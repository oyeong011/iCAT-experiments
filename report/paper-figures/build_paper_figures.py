#!/usr/bin/env python3
"""
iCAT Paper Figures & Master Excel Databook Generator (Home PC / Independent Verifier)

Principles:
1. Read-only access to immutable Git refs (origin/report/data-validity-20261124, origin/main,
   origin/resource-overhead-20261114). Never mutates raw logs or existing paper figs/.
2. Independent raw-log validity gate before any data enters Raw_Data, Statistics, or Figures.
3. Strict separation of hosts, workloads, record counts, and batches (cross-batch caveats explicit).
4. n < 3 -> no confidence interval or statistical conclusion displayed.
5. Incomplete/running experiments explicitly marked PENDING.
6. Outputs:
   - report/paper-figures/iCAT_Paper_Figures.xlsx (12 sheets with data tables, formulas, native charts)
   - report/paper-figures/figures/figure01_random.{png,pdf,svg} .. figure07_resources.{png,pdf,svg}
   - report/paper-figures/figure_manifest.csv
   - report/paper-figures/verified_plot_data.json (for automated Excel <-> Figure consistency check)
"""

import csv
import gzip
import io
import json
import math
import os
import re
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

import openpyxl
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent
FIG_DIR = OUT_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

KST = timezone(timedelta(hours=9))
GENERATED_AT = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST")

# Git refs (read-only)
REF_GOCOM = "origin/report/data-validity-20261124"
REF_MAIN = "origin/main"
REF_RES = "origin/resource-overhead-20261114"


def git_rev(ref: str) -> str:
    p = subprocess.run(["git", "rev-parse", "--short=9", ref], cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    return p.stdout.strip()


def git_show(ref_path: str, binary: bool = False):
    p = subprocess.run(["git", "show", ref_path], cwd=REPO_ROOT, capture_output=True)
    if p.returncode != 0:
        return None
    return p.stdout if binary else p.stdout.decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Pure-Python exact Student-t 95% two-sided critical value (no scipy needed)
# ---------------------------------------------------------------------------
def _betacf(a: float, b: float, x: float) -> float:
    MAXIT = 200
    EPS = 3.0e-12
    FPMIN = 1.0e-30
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < EPS:
            break
    return h


def _betainc(a: float, b: float, x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def student_t_two_tail_p(t_abs: float, df: float) -> float:
    x = df / (df + t_abs * t_abs)
    return _betainc(df / 2.0, 0.5, x)


def t_crit_95(df: float) -> float:
    if df <= 0:
        return float("nan")
    lo, hi = 1.0, 200.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if student_t_two_tail_p(mid, df) > 0.05:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def calc_summary(values):
    n = len(values)
    if n == 0:
        return {"n": 0, "mean": None, "sd": None, "t_crit": None, "ci_half": None, "ci_lo": None, "ci_hi": None, "stat_allowed": False}
    mean = float(np.mean(values))
    if n < 2:
        return {"n": n, "mean": mean, "sd": None, "t_crit": None, "ci_half": None, "ci_lo": None, "ci_hi": None, "stat_allowed": False}
    sd = float(np.std(values, ddof=1))
    if n < 3:
        return {"n": n, "mean": mean, "sd": sd, "t_crit": None, "ci_half": None, "ci_lo": None, "ci_hi": None, "stat_allowed": False}
    tc = t_crit_95(n - 1)
    half = tc * sd / math.sqrt(n)
    return {
        "n": n,
        "mean": mean,
        "sd": sd,
        "t_crit": tc,
        "ci_half": half,
        "ci_lo": mean - half,
        "ci_hi": mean + half,
        "stat_allowed": True,
    }


def calc_welch(vals_a, vals_b):
    """Welch difference: mean(a) - mean(b) with 95% CI (requires both n >= 3)."""
    na, nb = len(vals_a), len(vals_b)
    if na < 3 or nb < 3:
        return {"delta": None, "se": None, "df": None, "ci_lo": None, "ci_hi": None, "excludes_zero": False, "stat_allowed": False}
    ma, mb = float(np.mean(vals_a)), float(np.mean(vals_b))
    va, vb = float(np.var(vals_a, ddof=1)), float(np.var(vals_b, ddof=1))
    delta = ma - mb
    se2 = va / na + vb / nb
    se = math.sqrt(se2)
    if se == 0:
        return {"delta": delta, "se": 0.0, "df": float(na + nb - 2), "ci_lo": delta, "ci_hi": delta, "excludes_zero": delta != 0, "stat_allowed": True}
    df = (se2 ** 2) / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    tc = t_crit_95(df)
    half = tc * se
    lo, hi = delta - half, delta + half
    return {
        "delta": delta,
        "se": se,
        "df": df,
        "t_crit": tc,
        "ci_half": half,
        "ci_lo": lo,
        "ci_hi": hi,
        "excludes_zero": (lo > 0.0) or (hi < 0.0),
        "stat_allowed": True,
    }


# ---------------------------------------------------------------------------
# Independent raw run loader & verifier
# ---------------------------------------------------------------------------
def parse_module_hashes(ref: str, path: str) -> dict:
    txt = git_show(f"{ref}:{path}") or ""
    out = {}
    for line in txt.splitlines():
        m = re.match(r"([0-9a-f]{64})\s+(\S+)", line.strip())
        if m:
            out[os.path.basename(m.group(2))] = m.group(1)
    return out


def verify_mixfyf_run(ref: str, commit: str, exp_id: str, run_dir: str, policy: str, rep: int, expected_hashes: dict) -> dict:
    exit_txt = git_show(f"{ref}:{run_dir}/exit-code.txt")
    exit_code = int(exit_txt.strip()) if (exit_txt and exit_txt.strip().isdigit()) else -1

    env = git_show(f"{ref}:{run_dir}/environment.txt") or ""
    m_sha = re.search(r"([0-9a-f]{64})\s+(\S+\.ko)", env)
    mod_sha = m_sha.group(1) if m_sha else "MISSING"
    mod_name = os.path.basename(m_sha.group(2)) if m_sha else "MISSING"
    sha_match = (expected_hashes.get(mod_name) == mod_sha) if mod_name in expected_hashes else False

    m_host = re.search(r"Linux\s+(\S+)\s+(\S+)", env)
    host = m_host.group(1) if m_host else "UNKNOWN"
    kernel = m_host.group(2) if m_host else "UNKNOWN"

    summary = git_show(f"{ref}:{run_dir}/summary.txt") or ""
    final_ctrl = git_show(f"{ref}:{run_dir}/final-control.txt") or ""
    m_st = re.search(r"total\s+host_bytes=(\d+)\s+host_pages=(\d+)\s+gc_pages=(\d+)\s+WAF=([\d.]+)", summary)
    m_ft = re.search(r"host_bytes=(\d+)\s+host_pages=(\d+)\s+gc_pages=(\d+)", final_ctrl)
    parts = re.findall(r"part=(\d+)\s+host_pages=(\d+)\s+gc_pages=(\d+)", final_ctrl)

    sh = int(m_st.group(2)) if m_st else 0
    sg = int(m_st.group(3)) if m_st else 0
    sw = float(m_st.group(4)) if m_st else 0.0
    fh = int(m_ft.group(2)) if m_ft else -1
    fg = int(m_ft.group(3)) if m_ft else -1
    ph = sum(int(x[1]) for x in parts) if parts else -2
    pg = sum(int(x[2]) for x in parts) if parts else -2
    waf_recalc = (1.0 + sg / sh) if sh > 0 else 0.0
    two_path_ok = (sh > 0 and sh == fh == ph and sg == fg == pg and abs(waf_recalc - sw) < 2e-6)

    # Phase WAFs directly from phase-*-start/end.txt
    phase_wafs = {}
    for ph_id in ["A", "B", "C"]:
        ps = git_show(f"{ref}:{run_dir}/phase-{ph_id}-start.txt") or ""
        pe = git_show(f"{ref}:{run_dir}/phase-{ph_id}-end.txt") or ""
        ms = re.search(r"host_pages=(\d+)\s+gc_pages=(\d+)", ps)
        me = re.search(r"host_pages=(\d+)\s+gc_pages=(\d+)", pe)
        if ms and me:
            dh = int(me.group(1)) - int(ms.group(1))
            dg = int(me.group(2)) - int(ms.group(2))
            phase_wafs[ph_id] = (1.0 + dg / dh) if dh > 0 else None
        else:
            phase_wafs[ph_id] = None

    # FIO error check
    fio_errs = 0
    for jf in ["preset.json", "prepare.json", "phase-A.json", "phase-C.json"]:
        ft = git_show(f"{ref}:{run_dir}/{jf}")
        if not ft:
            fio_errs += 1
        else:
            d = json.loads(ft)
            for j in d.get("jobs", []):
                if j.get("error", -1) != 0:
                    fio_errs += 1

    # YCSB check
    sqlite_full = 0
    ycsb_fail_rate = 0.0
    ycsb_load_ins = 0
    ycsb_run_ops = 0
    for yf in ["ycsb-load.txt.gz", "ycsb-run-B.txt.gz"]:
        yb = git_show(f"{ref}:{run_dir}/{yf}", binary=True)
        if not yb:
            ycsb_fail_rate = 1.0
            continue
        yt = gzip.decompress(yb).decode("utf-8", errors="replace")
        sqlite_full += len(re.findall(r"SQLITE_FULL|database or disk is full", yt, re.I))
        ops = dict(re.findall(r"\[([\w-]+)\],\s*Operations,\s*(\d+)", yt))
        ok = sum(int(v) for k, v in ops.items() if k in ("INSERT", "READ", "UPDATE"))
        fail = sum(int(v) for k, v in ops.items() if "FAILED" in k.upper())
        if yf == "ycsb-load.txt.gz":
            ycsb_load_ins = int(ops.get("INSERT", 0))
        else:
            ycsb_run_ops = ok
        if ok + fail > 0:
            ycsb_fail_rate = max(ycsb_fail_rate, fail / (ok + fail))
        else:
            ycsb_fail_rate = 1.0

    # Kernel log check
    klog = git_show(f"{ref}:{run_dir}/kernel.log") or ""
    k_errs = sum(1 for l in klog.splitlines() if re.search(r"\b(BUG:|Oops|WARNING:|Call Trace|panic|EXT4-fs error|I/O error)\b", l))
    resets = sum(1 for l in klog.splitlines() if re.search(r"WATGC_V2\s+part=\d+\s+reset\b|WATGC_V2\s+reset\b", l))

    valid = (exit_code == 0 and sha_match and two_path_ok and fio_errs == 0 and sqlite_full == 0 and ycsb_fail_rate <= 0.01 and k_errs == 0)

    return {
        "run_id": os.path.basename(run_dir),
        "exp_id": exp_id,
        "host": host,
        "kernel": kernel,
        "workload": "mixFYF (FIO-Fast 1800s -> YCSB-A 250k 1800s -> FIO-Fast 1800s)",
        "policy": policy,
        "rep": rep,
        "fio_seeds": f"{20260910+rep}/{20261010+rep}/{20261110+rep}",
        "icat_seed": 2026111400 + rep,
        "git_branch": ref,
        "git_commit": commit,
        "module_name": mod_name,
        "module_sha256": mod_sha,
        "sha_match": sha_match,
        "exit_code": exit_code,
        "fio_errors": fio_errs,
        "ycsb_load_records": ycsb_load_ins,
        "ycsb_run_ops": ycsb_run_ops,
        "ycsb_fail_pct": round(ycsb_fail_rate * 100.0, 4),
        "sqlite_full": sqlite_full,
        "kernel_errors": k_errs,
        "host_pages": sh,
        "gc_pages": sg,
        "waf_total": waf_recalc,
        "waf_A": phase_wafs["A"],
        "waf_B": phase_wafs["B"],
        "waf_C": phase_wafs["C"],
        "two_path_match": two_path_ok,
        "resets": resets,
        "valid": valid,
        "raw_path": f"{ref}:{run_dir}",
    }


def load_rolling_waf_series(ref: str, run_dir: str, window_s: int = 300, bin_s: int = 120):
    """Compute exact 5-min rolling WAF binned at bin_s intervals (0..5400s) from raw control-series.txt."""
    cs_txt = git_show(f"{ref}:{run_dir}/control-series.txt") or ""
    t0_txt = (git_show(f"{ref}:{run_dir}/phase-A-start.time") or "").strip()
    t0 = int(datetime.fromisoformat(t0_txt).timestamp())
    pts = []
    for line in cs_txt.splitlines():
        m = re.match(r"(\d+)\s+epoch=(\d+)\s+active=(\d+)\s+host_bytes=\d+\s+host_pages=(\d+)\s+gc_pages=(\d+)", line)
        if m:
            ts, ep, act, hp, gp = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))
            if ep == 1 and ts >= t0:
                pts.append((ts - t0, hp, gp))
    # Sort by time
    pts.sort(key=lambda x: x[0])
    # Compute rolling 300s WAF at each bin center t = 300, 420, ..., 5400 (5..90 min)
    times_min = list(range(5, 91, bin_s // 60))
    wafs = []
    for tm in times_min:
        t_end = tm * 60
        t_start = t_end - window_s
        # find closest point <= t_end and closest point <= t_start
        p_end = None
        p_start = None
        for t, hp, gp in pts:
            if t <= t_start + 15:
                p_start = (t, hp, gp)
            if t <= t_end + 15:
                p_end = (t, hp, gp)
        if p_end is not None and p_start is None:
            p_start = (0, 0, 0)
        if p_end and p_start and p_end[1] > p_start[1]:
            dh = p_end[1] - p_start[1]
            dg = p_end[2] - p_start[2]
            wafs.append(1.0 + dg / dh)
        else:
            wafs.append(None)
    return times_min, wafs


def load_sweep_rank(ref: str, path: str) -> dict:
    txt = git_show(f"{ref}:{path}") or ""
    k2_wafs, k2_ranks = [], []
    k4_wafs, k4_ranks = [], []
    for line in txt.splitlines():
        m = re.match(r"\s*(\d+)\s+arm(\d+)\s+k(\d+)-s(\d+)-r(\d+)\s+([\d.]+)", line)
        if m:
            rank, arm, k, waf = int(m.group(1)), int(m.group(2)), int(m.group(3)), float(m.group(6))
            if k == 2:
                k2_wafs.append(waf)
                k2_ranks.append(rank)
            else:
                k4_wafs.append(waf)
                k4_ranks.append(rank)
    return {
        "n_k2": len(k2_wafs),
        "n_k4plus": len(k4_wafs),
        "k2_min": min(k2_wafs),
        "k2_median": float(np.median(k2_wafs)),
        "k2_mean": float(np.mean(k2_wafs)),
        "k2_max": max(k2_wafs),
        "k2_best_rank": min(k2_ranks),
        "k2_worst_rank": max(k2_ranks),
        "k4_min": min(k4_wafs),
        "k4_median": float(np.median(k4_wafs)),
        "k4_mean": float(np.mean(k4_wafs)),
        "k4_max": max(k4_wafs),
        "k4_best_rank": min(k4_ranks),
        "k4_worst_rank": max(k4_ranks),
        "k2_wafs": k2_wafs,
        "k4_wafs": k4_wafs,
    }


def load_csv_from_git(ref: str, path: str) -> list:
    txt = git_show(f"{ref}:{path}") or ""
    return list(csv.DictReader(io.StringIO(txt)))


# ---------------------------------------------------------------------------
# Academic Matplotlib Styling
# ---------------------------------------------------------------------------
PALETTE = {
    "v4": "#0072B2",        # Blue (primary iCAT-v4)
    "random": "#D55E00",    # Vermilion (Random baseline)
    "v1": "#E69F00",        # Orange (V1 / NoDrift)
    "v2": "#CC79A7",        # Reddish Purple (V2 / NoElim+NoSettle)
    "noelim": "#009E73",    # Bluish Green (NoElim)
    "nosettle": "#56B4E9",  # Sky Blue (NoSettle)
    "arm47": "#4D4D4D",     # Dark Gray (Fixed CAT-47 ref)
    "smartgc": "#B2182B",   # Crimson (SmartGC block-level)
    "neutral": "#7F7F7F",   # Neutral gray
    "pending_bg": "#F4F6F9",
    "pending_edge": "#8C9BAB",
}

def setup_matplotlib():
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "font.family": "DejaVu Sans",
        "font.size": 9.5,
        "axes.titlesize": 10.5,
        "axes.titleweight": "bold",
        "axes.labelsize": 9.5,
        "axes.labelweight": "bold",
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "legend.fontsize": 8.2,
        "legend.frameon": True,
        "legend.facecolor": "white",
        "legend.edgecolor": "#CCCCCC",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#333333",
        "axes.linewidth": 0.9,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.color": "#E0E0E0",
        "grid.linestyle": "--",
        "grid.linewidth": 0.6,
        "axes.axisbelow": True,
    })


def save_figure(fig, stem: str):
    paths = {}
    for ext in ["png", "pdf", "svg"]:
        p = FIG_DIR / f"{stem}.{ext}"
        kwargs = {"bbox_inches": "tight", "facecolor": "white"}
        if ext == "png":
            kwargs["dpi"] = 300
        fig.savefig(p, **kwargs)
        paths[ext] = str(p.relative_to(REPO_ROOT)).replace("\\", "/")
    plt.close(fig)
    return paths


# ---------------------------------------------------------------------------
# Main Pipeline
# ---------------------------------------------------------------------------
def main():
    setup_matplotlib()
    commit_gocom = git_rev(REF_GOCOM)
    commit_main = git_rev(REF_MAIN)
    commit_res = git_rev(REF_RES)

    print(f"Building iCAT paper figures & Excel databook from Git snapshots:")
    print(f"  GoCom ({REF_GOCOM}): {commit_gocom}")
    print(f"  SeungCom ({REF_MAIN}): {commit_main}")
    print(f"  Resource ({REF_RES}): {commit_res}")

    # 1. Load & independently verify ALL valid mixFYF runs from revA, revB, revC
    h_revA = parse_module_hashes(REF_GOCOM, "result/revA-20261114/modules.sha256")
    h_revB = parse_module_hashes(REF_GOCOM, "result/revB-20261122/modules.sha256")
    h_revC = parse_module_hashes(REF_GOCOM, "result/revC-20261124/modules.sha256")

    raw_runs = []
    # revA main runs (13 runs: arm47 x1 + v4/v1/v2/random x3)
    revA_specs = [
        ("arm47", 1, "mixFYF-arm47-rep1"),
        ("revA-v4", 1, "mixFYF-revA-v4-rep1"),
        ("revA-v4", 2, "mixFYF-revA-v4-rep2"),
        ("revA-v4", 3, "mixFYF-revA-v4-rep3"),
        ("revA-random", 1, "mixFYF-revA-random-rep1"),
        ("revA-random", 2, "mixFYF-revA-random-rep2"),
        ("revA-random", 3, "mixFYF-revA-random-rep3"),
        ("revA-v1", 1, "mixFYF-revA-v1-rep1"),
        ("revA-v1", 2, "mixFYF-revA-v1-rep2"),
        ("revA-v1", 3, "mixFYF-revA-v1-rep3"),
        ("revA-v2", 1, "mixFYF-revA-v2-rep1"),
        ("revA-v2", 2, "mixFYF-revA-v2-rep2"),
        ("revA-v2", 3, "mixFYF-revA-v2-rep3"),
    ]
    for pol, rep, dname in revA_specs:
        raw_runs.append(verify_mixfyf_run(REF_GOCOM, commit_gocom, "revA-20261114", f"result/revA-20261114/raw/{dname}", pol, rep, h_revA))

    # revB main runs (8 runs: revB-v4 x1, arm60 x1, noelim x3, nosettle x3)
    revB_specs = [
        ("revB-v4", 1, "mixFYF-revB-v4-rep1"),
        ("revB-arm60", 1, "mixFYF-revB-arm60-rep1"),
        ("revB-noelim", 1, "mixFYF-revB-noelim-rep1"),
        ("revB-noelim", 2, "mixFYF-revB-noelim-rep2"),
        ("revB-noelim", 3, "mixFYF-revB-noelim-rep3"),
        ("revB-nosettle", 1, "mixFYF-revB-nosettle-rep1"),
        ("revB-nosettle", 2, "mixFYF-revB-nosettle-rep2"),
        ("revB-nosettle", 3, "mixFYF-revB-nosettle-rep3"),
    ]
    for pol, rep, dname in revB_specs:
        raw_runs.append(verify_mixfyf_run(REF_GOCOM, commit_gocom, "revB-20261122", f"result/revB-20261122/raw/{dname}", pol, rep, h_revB))

    # revC completed main runs (15/15 COMPLETE! All 5 policies n=3)
    revC_specs = [
        ("revC-v4", 1, "mixFYF-revC-v4-rep1"),
        ("revC-v4", 2, "mixFYF-revC-v4-rep2"),
        ("revC-v4", 3, "mixFYF-revC-v4-rep3"),
        ("revC-elim10", 1, "mixFYF-revC-elim10-rep1"),
        ("revC-elim10", 2, "mixFYF-revC-elim10-rep2"),
        ("revC-elim10", 3, "mixFYF-revC-elim10-rep3"),
        ("revC-elim25", 1, "mixFYF-revC-elim25-rep1"),
        ("revC-elim25", 2, "mixFYF-revC-elim25-rep2"),
        ("revC-elim25", 3, "mixFYF-revC-elim25-rep3"),
        ("revC-arm60", 1, "mixFYF-revB-arm60-rep1"),
        ("revC-arm60", 2, "mixFYF-revB-arm60-rep2"),
        ("revC-arm60", 3, "mixFYF-revB-arm60-rep3"),
        ("revC-online", 1, "mixFYF-online-rep1"),
        ("revC-online", 2, "mixFYF-online-rep2"),
        ("revC-online", 3, "mixFYF-online-rep3"),
    ]
    for pol, rep, dname in revC_specs:
        raw_runs.append(verify_mixfyf_run(REF_GOCOM, commit_gocom, "revC-20261124", f"result/revC-20261124/raw/{dname}", pol, rep, h_revC))

    # revD completed main runs (SeungCom 9/9 COMPLETE! All 3 policies n=3)
    h_revD = parse_module_hashes(REF_MAIN, "result/revD-20261124/modules.sha256")
    revD_specs = [
        ("revD-fullreset", 1, "mixFYF-revD-fullreset-rep1"),
        ("revD-fullreset", 2, "mixFYF-revD-fullreset-rep2"),
        ("revD-fullreset", 3, "mixFYF-revD-fullreset-rep3"),
        ("revD-nodrift", 1, "mixFYF-revD-nodrift-rep1"),
        ("revD-nodrift", 2, "mixFYF-revD-nodrift-rep2"),
        ("revD-nodrift", 3, "mixFYF-revD-nodrift-rep3"),
        ("revD-v4", 1, "mixFYF-revD-v4-rep1"),
        ("revD-v4", 2, "mixFYF-revD-v4-rep2"),
        ("revD-v4", 3, "mixFYF-revD-v4-rep3"),
    ]
    for pol, rep, dname in revD_specs:
        raw_runs.append(verify_mixfyf_run(REF_MAIN, commit_main, "revD-20261124", f"result/revD-20261124/raw/{dname}", pol, rep, h_revD))

    # abl-20261125 completed main runs (SeungCom 9/9 COMPLETE! All 3 policies n=3)
    h_abl = parse_module_hashes(REF_MAIN, "result/revision-additional-ablation/modules.sha256")
    abl_specs = [
        ("abl-v4", 1, "mixFYF-abl-v4-rep1"),
        ("abl-v4", 2, "mixFYF-abl-v4-rep2"),
        ("abl-v4", 3, "mixFYF-abl-v4-rep3"),
        ("abl-nodiscount", 1, "mixFYF-abl-nodiscount-rep1"),
        ("abl-nodiscount", 2, "mixFYF-abl-nodiscount-rep2"),
        ("abl-nodiscount", 3, "mixFYF-abl-nodiscount-rep3"),
        ("abl-bundle-off", 1, "mixFYF-abl-off-elim-settle-drift-probe-rep1"),
        ("abl-bundle-off", 2, "mixFYF-abl-off-elim-settle-drift-probe-rep2"),
        ("abl-bundle-off", 3, "mixFYF-abl-off-elim-settle-drift-probe-rep3"),
    ]
    for pol, rep, dname in abl_specs:
        raw_runs.append(verify_mixfyf_run(REF_MAIN, commit_main, "abl-20261125", f"result/revision-additional-ablation/raw/{dname}", pol, rep, h_abl))

    # revE-20261125 completed main runs (GoCom 9/9 COMPLETE! Same-batch isolated NoElim & drift12 n=3)
    h_revE = parse_module_hashes(REF_GOCOM, "result/revE-20261125/modules.sha256")
    revE_specs = [
        ("revE-v4", 1, "mixFYF-revE-v4-rep1"),
        ("revE-v4", 2, "mixFYF-revE-v4-rep2"),
        ("revE-v4", 3, "mixFYF-revE-v4-rep3"),
        ("revE-noelim", 1, "mixFYF-revE-noelim-rep1"),
        ("revE-noelim", 2, "mixFYF-revE-noelim-rep2"),
        ("revE-noelim", 3, "mixFYF-revE-noelim-rep3"),
        ("revE-drift12", 1, "mixFYF-revE-drift12-rep1"),
        ("revE-drift12", 2, "mixFYF-revE-drift12-rep2"),
        ("revE-drift12", 3, "mixFYF-revE-drift12-rep3"),
    ]
    for pol, rep, dname in revE_specs:
        raw_runs.append(verify_mixfyf_run(REF_GOCOM, commit_gocom, "revE-20261125", f"result/revE-20261125/raw/{dname}", pol, rep, h_revE))

    # greedy-20261125 completed main runs (SeungCom 3/3 COMPLETE! Online Greedy VARIANT=8 n=3)
    h_greedy = parse_module_hashes(REF_MAIN, "result/greedy-20261125/modules.sha256")
    greedy_specs = [
        ("greedy-online", 1, "mixFYF-greedy-online-rep1"),
        ("greedy-online", 2, "mixFYF-greedy-online-rep2"),
        ("greedy-online", 3, "mixFYF-greedy-online-rep3"),
    ]
    for pol, rep, dname in greedy_specs:
        raw_runs.append(verify_mixfyf_run(REF_MAIN, commit_main, "greedy-20261125", f"result/greedy-20261125/raw/{dname}", pol, rep, h_greedy))

    # batchG-20261126 completed main runs (SeungCom 9/9 COMPLETE! Greedy GC, drift50, bg-v4 n=3)
    h_batchG = parse_module_hashes(REF_MAIN, "result/batchG-20261126/modules.sha256")
    batchG_specs = [
        ("batchG-v4", 1, "result/batchG-20261126/raw/mixFYF-bg-v4-rep1"),
        ("batchG-v4", 2, "result/batchG-20261126/raw/mixFYF-bg-v4-rep2"),
        ("batchG-v4", 3, "result/batchG-20261126/raw/mixFYF-bg-v4-rep3"),
        ("batchG-greedygc", 1, "result/greedygc-20261126/raw/mixFYF-greedygc-rep1"),
        ("batchG-greedygc", 2, "result/greedygc-20261126/raw/mixFYF-greedygc-rep2"),
        ("batchG-greedygc", 3, "result/greedygc-20261126/raw/mixFYF-greedygc-rep3"),
        ("batchG-drift50", 1, "result/drift50-20261126/raw/mixFYF-drift50-rep1"),
        ("batchG-drift50", 2, "result/drift50-20261126/raw/mixFYF-drift50-rep2"),
        ("batchG-drift50", 3, "result/drift50-20261126/raw/mixFYF-drift50-rep3"),
    ]
    for pol, rep, rdir in batchG_specs:
        raw_runs.append(verify_mixfyf_run(REF_MAIN, commit_main, "batchG-20261126", rdir, pol, rep, h_batchG))

    # arm47-20261127 completed main runs (SeungCom 3/3 COMPLETE! Fixed Arm 47 n=3; host-separated from GoCom revA n=1)
    h_arm47 = parse_module_hashes(REF_MAIN, "result/arm47-20261127/modules.sha256")
    for rep in (1, 2, 3):
        raw_runs.append(verify_mixfyf_run(REF_MAIN, commit_main, "arm47-20261127", f"result/arm47-20261127/raw/mixFYF-arm47-rep{rep}", "arm47-seungcom", rep, h_arm47))

    # Enforce strict validity gate
    for r in raw_runs:
        if not r["valid"]:
            raise RuntimeError(f"Validity gate FAILED on {r['run_id']}: {r}")

    by_pol = {}
    for r in raw_runs:
        by_pol.setdefault(r["policy"], []).append(r)

    # 2. Load verified auxiliary datasets (GoCom revA exploration/cpu/transition, SeungCom resource-v124, Sweeps, Offline elim replay)
    revA_exp_rows = load_csv_from_git(REF_GOCOM, "result/revA-20261114/results/exploration_cost.csv")
    revA_cpu_rows = load_csv_from_git(REF_GOCOM, "result/revA-20261114/results/resource/cpu_measurements.csv")
    revA_trans_rows = load_csv_from_git(REF_GOCOM, "result/revA-20261114/results/workload_transition.csv")
    res_raw_rows = load_csv_from_git(REF_RES, "result/resource-v124-20261114/report/resource_raw.csv")
    res_cpu_rows = load_csv_from_git(REF_RES, "result/resource-v124-20261114/report/cpu_measurements.csv")
    res_cpu_summary_rows = load_csv_from_git(REF_RES, "result/resource-v124-20261114/report/cpu_overhead_summary.csv")
    elim_replay_rows = [
        r for r in load_csv_from_git(REF_GOCOM, "result/revision-gocom-20261123/elim_replay_summary.csv")
        if r["group"].startswith("no-elimination")
    ]

    # Parse 3 complete 60/60 full sweeps
    sweeps = {
        "FIO-Fast (test4)": load_sweep_rank(REF_MAIN, "result/sweep-20260915/rank-test4.txt"),
        "OLTP": load_sweep_rank(REF_MAIN, "result/sweep-20260915/rank-oltp.txt"),
        "SQLite-A": load_sweep_rank(REF_MAIN, "result/sweep-20260915/rank-sqlite-a.txt"),
    }

    # Parse 30s control-series for revA adaptation trajectories (5-min rolling WAF every 2 min)
    traj_policies = ["revA-v4", "revA-v1", "revA-random", "arm47"]
    traj_data = {}
    traj_times = None
    for pol in traj_policies:
        mat = []
        for r in by_pol[pol]:
            rel_dir = r["raw_path"].split(":", 1)[1]
            tmins, wafs = load_rolling_waf_series(REF_GOCOM, rel_dir, window_s=300, bin_s=120)
            traj_times = tmins
            mat.append(wafs)
        arr = np.array(mat, dtype=float)
        traj_data[pol] = {
            "n": arr.shape[0],
            "mean": [float(np.nanmean(arr[:, i])) for i in range(arr.shape[1])],
            "sd": [float(np.nanstd(arr[:, i], ddof=1)) if arr.shape[0] > 1 else 0.0 for i in range(arr.shape[1])],
        }

    # Compute structured plot data dictionary (exact single source of truth for BOTH matplotlib and Excel!)
    verified_plot_data = {"generated_at": GENERATED_AT, "commits": {"gocom": commit_gocom, "main": commit_main, "resource": commit_res}}

    # =========================================================================
    # FIGURE 01: Random Selection vs iCAT-v4 (E2)
    # =========================================================================
    f1_pols = ["revA-random", "revA-v4"]
    f1_overall = {p: calc_summary([r["waf_total"] for r in by_pol[p]]) for p in f1_pols}
    f1_phases = {
        p: {ph: calc_summary([r[f"waf_{ph}"] for r in by_pol[p]]) for ph in ["A", "B", "C"]}
        for p in f1_pols
    }
    f1_welch_total = calc_welch([r["waf_total"] for r in by_pol["revA-random"]], [r["waf_total"] for r in by_pol["revA-v4"]])
    f1_welch_phases = {
        ph: calc_welch([r[f"waf_{ph}"] for r in by_pol["revA-random"]], [r[f"waf_{ph}"] for r in by_pol["revA-v4"]])
        for ph in ["A", "B", "C"]
    }
    f1_arm47_ref = by_pol["arm47"][0]["waf_total"]
    f1_pct_impr = (f1_overall["revA-random"]["mean"] - f1_overall["revA-v4"]["mean"]) / f1_overall["revA-random"]["mean"] * 100.0

    verified_plot_data["fig01_random"] = {
        "overall": f1_overall,
        "phases": f1_phases,
        "welch_total": f1_welch_total,
        "welch_phases": f1_welch_phases,
        "arm47_n1_ref": f1_arm47_ref,
        "pct_reduction": f1_pct_impr,
    }

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.8, 4.2), gridspec_kw={"width_ratios": [1.0, 1.35], "wspace": 0.25})
    # Panel (a): Overall WAF
    x1 = np.arange(2)
    means1 = [f1_overall["revA-random"]["mean"], f1_overall["revA-v4"]["mean"]]
    cis1 = [f1_overall["revA-random"]["ci_half"], f1_overall["revA-v4"]["ci_half"]]
    colors1 = [PALETTE["random"], PALETTE["v4"]]
    bars1 = ax1.bar(x1, means1, width=0.50, color=colors1, edgecolor="#222222", linewidth=0.8, yerr=cis1, capsize=5, error_kw={"elinewidth": 1.3, "ecolor": "#222222"})
    # Individual rep points
    for idx, pol in enumerate(f1_pols):
        ys = [r["waf_total"] for r in by_pol[pol]]
        ax1.scatter([x1[idx] - 0.08, x1[idx], x1[idx] + 0.08], ys, color="white", edgecolor="#111111", s=26, zorder=5, linewidth=0.9)
    ax1.axhline(f1_arm47_ref, color=PALETTE["arm47"], linestyle="--", linewidth=1.1, label=f"Fixed CAT-47 (n=1 ref: {f1_arm47_ref:.3f})")
    ax1.set_xticks(x1)
    ax1.set_xticklabels(["Random Selection\n(45 arms, n=3)", "iCAT-v4\n(45 arms, n=3)"])
    ax1.set_ylabel("Write Amplification Factor (WAF)")
    ax1.set_title("(a) Overall WAF on mixFYF (90 min)")
    ax1.set_ylim(1.85, 2.57)
    for b, m, c in zip(bars1, means1, cis1):
        ax1.text(b.get_x() + b.get_width() / 2, m + c + 0.016, f"{m:.4f}\n±{c:.4f}", ha="center", va="bottom", fontsize=8.0, fontweight="bold")
    # Bracket annotation (cleanly above bar labels)
    by = 2.465
    ax1.plot([0, 0, 1, 1], [by - 0.015, by, by, by - 0.015], color="#222222", linewidth=1.0)
    ax1.text(0.5, by + 0.012, f"Δ = −{f1_welch_total['delta']:.4f} (−{f1_pct_impr:.2f}%)\nWelch 95% CI [−{f1_welch_total['ci_hi']:.4f}, −{f1_welch_total['ci_lo']:.4f}]",
             ha="center", va="bottom", fontsize=7.6, color="#111111")
    ax1.legend(loc="lower right", fontsize=7.5)

    # Panel (b): Phase-by-Phase WAF
    x2 = np.arange(3)
    w = 0.34
    r_m = [f1_phases["revA-random"][ph]["mean"] for ph in ["A", "B", "C"]]
    r_c = [f1_phases["revA-random"][ph]["ci_half"] for ph in ["A", "B", "C"]]
    v_m = [f1_phases["revA-v4"][ph]["mean"] for ph in ["A", "B", "C"]]
    v_c = [f1_phases["revA-v4"][ph]["ci_half"] for ph in ["A", "B", "C"]]
    b_r = ax2.bar(x2 - w / 2, r_m, width=w, color=PALETTE["random"], edgecolor="#222222", linewidth=0.8, yerr=r_c, capsize=4, label="Random Selection (n=3)")
    b_v = ax2.bar(x2 + w / 2, v_m, width=w, color=PALETTE["v4"], edgecolor="#222222", linewidth=0.8, yerr=v_c, capsize=4, label="iCAT-v4 (n=3)")
    ax2.set_xticks(x2)
    ax2.set_xticklabels(["Phase A\nFIO-Fast 1 (30m)", "Phase B\nYCSB-A 250k (30m)", "Phase C\nFIO-Fast 2 (30m)"])
    ax2.set_ylabel("Phase WAF")
    ax2.set_title("(b) Phase-by-Phase WAF Breakdown")
    ax2.set_ylim(0.90, 3.25)
    for b, m, c in zip(b_r, r_m, r_c):
        ax2.text(b.get_x() + b.get_width() / 2, m + c + 0.03, f"{m:.3f}", ha="center", va="bottom", fontsize=7.6)
    for b, m, c in zip(b_v, v_m, v_c):
        ax2.text(b.get_x() + b.get_width() / 2, m + c + 0.03, f"{m:.3f}", ha="center", va="bottom", fontsize=7.6)
    ax2.annotate(f"Δ = −{f1_welch_phases['C']['delta']:.3f} (−13.0%)", xy=(2 + w / 2, v_m[2] + 0.14), xytext=(1.95, 3.07),
                 ha="center", fontsize=8.0, fontweight="bold", color=PALETTE["v4"],
                 arrowprops={"arrowstyle": "->", "color": PALETTE["v4"], "lw": 1.0})
    ax2.legend(loc="upper left")
    fig.suptitle("Figure 1. Online Policy Learning (iCAT-v4) vs. Random Selection (GoCom mixFYF, Error bars = 95% t-CI, df=2)",
                 fontsize=10.0, fontweight="bold", y=1.02)
    fig.tight_layout()
    f1_paths = save_figure(fig, "figure01_random")

    # =========================================================================
    # FIGURE 02: Ablation Study (E1 / M2)
    # =========================================================================
    f2_order = [
        ("revA-v4", "iCAT-v4\n(Full)", PALETTE["v4"], False),
        ("revA-v1", "V1\n(NoDrift)", PALETTE["v1"], False),
        ("revB-nosettle", "NoSettle*\n(revB)", PALETTE["nosettle"], True),
        ("revB-noelim", "NoElim*\n(revB)", PALETTE["noelim"], True),
        ("revA-v2", "V2\n(NoElim+\nNoSettle)", PALETTE["v2"], False),
    ]
    f2_stats = {p: calc_summary([r["waf_total"] for r in by_pol[p]]) for p, _, _, _ in f2_order}
    f2_welch = {
        p: calc_welch([r["waf_total"] for r in by_pol[p]], [r["waf_total"] for r in by_pol["revA-v4"]])
        for p, _, _, _ in f2_order if p != "revA-v4"
    }
    f2_bridge = by_pol["revB-v4"][0]["waf_total"]

    # SeungCom revD same-batch ablation (9/9 COMPLETED, strictly separated from GoCom)
    revD_pols = ["revD-v4", "revD-fullreset", "revD-nodrift"]
    f2_revD_tot = {p: calc_summary([r["waf_total"] for r in by_pol[p]]) for p in revD_pols}
    f2_revD_phC = {p: calc_summary([r["waf_C"] for r in by_pol[p]]) for p in revD_pols}
    f2_revD_welch_tot = {
        p: calc_welch([r["waf_total"] for r in by_pol[p]], [r["waf_total"] for r in by_pol["revD-v4"]])
        for p in ["revD-fullreset", "revD-nodrift"]
    }
    f2_revD_welch_phC = {
        p: calc_welch([r["waf_C"] for r in by_pol[p]], [r["waf_C"] for r in by_pol["revD-v4"]])
        for p in ["revD-fullreset", "revD-nodrift"]
    }

    # SeungCom abl-20261125 (9/9 COMPLETED) & GoCom revE-20261125 (9/9 COMPLETED) & SeungCom greedy-20261125 (3/3 COMPLETED)
    abl_pols = ["abl-v4", "abl-nodiscount", "abl-bundle-off"]
    f2_abl_tot = {p: calc_summary([r["waf_total"] for r in by_pol[p]]) for p in abl_pols}
    f2_abl_phC = {p: calc_summary([r["waf_C"] for r in by_pol[p]]) for p in abl_pols}
    f2_abl_welch_tot = {p: calc_welch([r["waf_total"] for r in by_pol[p]], [r["waf_total"] for r in by_pol["abl-v4"]]) for p in ["abl-nodiscount", "abl-bundle-off"]}
    f2_abl_welch_phC = {p: calc_welch([r["waf_C"] for r in by_pol[p]], [r["waf_C"] for r in by_pol["abl-v4"]]) for p in ["abl-nodiscount", "abl-bundle-off"]}

    revE_pols = ["revE-v4", "revE-noelim", "revE-drift12"]
    f2_revE_tot = {p: calc_summary([r["waf_total"] for r in by_pol[p]]) for p in revE_pols}
    f2_revE_phC = {p: calc_summary([r["waf_C"] for r in by_pol[p]]) for p in revE_pols}
    f2_revE_welch_tot = {p: calc_welch([r["waf_total"] for r in by_pol[p]], [r["waf_total"] for r in by_pol["revE-v4"]]) for p in ["revE-noelim", "revE-drift12"]}
    f2_revE_welch_phC = {p: calc_welch([r["waf_C"] for r in by_pol[p]], [r["waf_C"] for r in by_pol["revE-v4"]]) for p in ["revE-noelim", "revE-drift12"]}

    f2_greedy_tot = calc_summary([r["waf_total"] for r in by_pol["greedy-online"]])
    f2_greedy_phA = calc_summary([r["waf_A"] for r in by_pol["greedy-online"]])
    f2_greedy_phB = calc_summary([r["waf_B"] for r in by_pol["greedy-online"]])
    f2_greedy_phC = calc_summary([r["waf_C"] for r in by_pol["greedy-online"]])
    f2_greedy_vs_revD_tot = calc_welch([r["waf_total"] for r in by_pol["greedy-online"]], [r["waf_total"] for r in by_pol["revD-v4"]])
    f2_greedy_vs_revD_phC = calc_welch([r["waf_C"] for r in by_pol["greedy-online"]], [r["waf_C"] for r in by_pol["revD-v4"]])
    f2_greedy_vs_abl_tot = calc_welch([r["waf_total"] for r in by_pol["greedy-online"]], [r["waf_total"] for r in by_pol["abl-v4"]])
    f2_greedy_vs_abl_phC = calc_welch([r["waf_C"] for r in by_pol["greedy-online"]], [r["waf_C"] for r in by_pol["abl-v4"]])

    verified_plot_data["fig02_ablation"] = {
        "variants": f2_stats,
        "welch_vs_v4": f2_welch,
        "revB_v4_bridge_n1": f2_bridge,
        "seungcom_revD_status": "COMPLETED (9/9 VALID, same-batch n=3)",
        "seungcom_revD_total": f2_revD_tot,
        "seungcom_revD_phaseC": f2_revD_phC,
        "seungcom_revD_welch_total": f2_revD_welch_tot,
        "seungcom_revD_welch_phaseC": f2_revD_welch_phC,
        "seungcom_abl_status": "COMPLETED (9/9 VALID, same-batch n=3)",
        "seungcom_abl_total": f2_abl_tot,
        "seungcom_abl_phaseC": f2_abl_phC,
        "seungcom_abl_welch_total": f2_abl_welch_tot,
        "seungcom_abl_welch_phaseC": f2_abl_welch_phC,
        "seungcom_abl_raw": {p: [r["waf_total"] for r in by_pol[p]] for p in abl_pols},
        "gocom_revE_status": "COMPLETED (9/9 VALID, same-batch n=3)",
        "gocom_revE_total": f2_revE_tot,
        "gocom_revE_phaseC": f2_revE_phC,
        "gocom_revE_welch_total": f2_revE_welch_tot,
        "gocom_revE_welch_phaseC": f2_revE_welch_phC,
        "gocom_revE_raw": {p: [r["waf_total"] for r in by_pol[p]] for p in revE_pols},
        "seungcom_greedy_status": "COMPLETED (3/3 VALID, 0/2513 rule mismatches; host-separated)",
        "seungcom_greedy_total": f2_greedy_tot,
        "seungcom_greedy_phases": {"A": f2_greedy_phA, "B": f2_greedy_phB, "C": f2_greedy_phC},
        "seungcom_greedy_raw": [r["waf_total"] for r in by_pol["greedy-online"]],
        "seungcom_greedy_welch_vs_revD_total": f2_greedy_vs_revD_tot,
        "seungcom_greedy_welch_vs_revD_phaseC": f2_greedy_vs_revD_phC,
        "seungcom_greedy_welch_vs_abl_total": f2_greedy_vs_abl_tot,
        "seungcom_greedy_welch_vs_abl_phaseC": f2_greedy_vs_abl_phC,
    }

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.6, 4.6), gridspec_kw={"width_ratios": [1.15, 1.05], "wspace": 0.50})
    x = np.arange(len(f2_order))
    means2 = [f2_stats[p]["mean"] for p, _, _, _ in f2_order]
    cis2 = [f2_stats[p]["ci_half"] for p, _, _, _ in f2_order]
    cols2 = [c for _, _, c, _ in f2_order]
    hatches2 = ["//" if is_cross else "" for _, _, _, is_cross in f2_order]
    bars2 = ax1.bar(x, means2, width=0.54, color=cols2, edgecolor="#222222", linewidth=0.8, yerr=cis2, capsize=4)
    for b, h in zip(bars2, hatches2):
        if h:
            b.set_hatch(h)
    for idx, (pol, _, _, _) in enumerate(f2_order):
        ys = [r["waf_total"] for r in by_pol[pol]]
        ax1.scatter([x[idx] - 0.1, x[idx], x[idx] + 0.1], ys, color="white", edgecolor="#111111", s=22, zorder=5, linewidth=0.8)
    ax1.scatter([0.36], [f2_bridge], color="#B2182B", marker="D", s=34, zorder=6, label=f"revB-v4 bridge (n=1: {f2_bridge:.4f})")
    ax1.set_xticks(x)
    ax1.set_xticklabels([lbl for _, lbl, _, _ in f2_order], fontsize=8.0)
    ax1.set_ylabel("Overall WAF (mixFYF, n=3)")
    ax1.set_title("(a) Ablation Variants (*Hatched = revB cross-batch)")
    ax1.set_ylim(2.00, 2.48)
    for b, m, c in zip(bars2, means2, cis2):
        ax1.text(b.get_x() + b.get_width() / 2, min(m + c + 0.012, 2.44), f"{m:.4f}", ha="center", va="bottom", fontsize=7.8, fontweight="bold")
    ax1.legend(loc="lower right", fontsize=7.5)

    # Panel (b): Forest plot of Welch Delta vs same-host iCAT-v4 (GoCom top, SeungCom revD bottom — strictly separated)
    eff_order = [
        ("gocom", "revA-v2", "V2 − V4\n(Elim+Settle, GoCom)"),
        ("gocom", "revB-noelim", "NoElim* − V4\n(Elimination, GoCom*)"),
        ("gocom", "revB-nosettle", "NoSettle* − V4\n(Settle+Drift, GoCom*)"),
        ("gocom", "revA-v1", "V1 − V4\n(NoDrift, GoCom)"),
        ("seung", "revD-fullreset", "FullReset − V4\n(Partial vs Full, revD)"),
        ("seung", "revD-nodrift", "NoDrift − V4\n(Drift, revD)"),
    ]
    y_pos = np.arange(len(eff_order))
    ax2.axvline(0.0, color="#333333", linestyle="--", linewidth=1.0)
    ax2.axhline(3.5, color="#888888", linestyle=":", linewidth=1.0)
    for idx, (host_tag, pol, lbl) in enumerate(eff_order):
        w_res = f2_welch[pol] if host_tag == "gocom" else f2_revD_welch_tot[pol]
        col = PALETTE["v4"] if w_res["excludes_zero"] else PALETTE["neutral"]
        ax2.errorbar(w_res["delta"], idx, xerr=w_res["ci_half"], fmt="o", color=col, ecolor=col, elinewidth=1.7, capsize=4.5, markersize=5.5)
        tag = "CI > 0" if w_res["excludes_zero"] else "Inconclusive"
        ax2.text(w_res["delta"], idx - 0.25, f"+{w_res['delta']:.4f} [{w_res['ci_lo']:+.3f}, {w_res['ci_hi']:+.3f}] ({tag})",
                 ha="center", va="bottom", fontsize=7.0, color=col, fontweight="bold" if w_res["excludes_zero"] else "normal")
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels([lbl for _, _, lbl in eff_order], fontsize=7.6)
    ax2.set_ylim(5.65, -0.75)
    ax2.set_xlabel("ΔOverall WAF vs. Same-Host iCAT-v4 (Positive = Worse)")
    ax2.set_title("(b) Effect Sizes (Welch 95% CI, Host-Separated)")
    ax2.set_xlim(-0.14, 0.34)
    ax2.grid(True, axis="x", linestyle="--", alpha=0.6)
    ax2.grid(False, axis="y")
    ax2.text(0.5, -0.21, "SeungCom revD Phase C Δ: FullReset +0.1296 [+0.052, +0.208] (CI>0, g=3.78); NoDrift +0.1411 [-0.087, +0.369].",
             transform=ax2.transAxes, ha="center", va="top", fontsize=7.2, style="italic",
             bbox={"boxstyle": "round,pad=0.28", "facecolor": "#F4F8FB", "edgecolor": PALETTE["v4"]})
    fig.suptitle("Figure 2. Component Ablation on mixFYF (GoCom revA/revB & SeungCom revD, n=3; Hosts Not Pooled)",
                 fontsize=9.8, fontweight="bold", y=1.02)
    fig.tight_layout()
    f2_paths = save_figure(fig, "figure02_ablation")

    # =========================================================================
    # FIGURE 03: Workload Transition & Adaptation Speed (E3)
    # =========================================================================
    v4_c_resets = [float(r["C_first_reset_after_transition_s"]) for r in revA_trans_rows if r["policy"] == "revA-v4"]
    v4_reset_stats = calc_summary(v4_c_resets)
    verified_plot_data["fig03_adaptation"] = {
        "times_min": traj_times,
        "trajectories": traj_data,
        "v4_phaseC_first_reset_s": v4_reset_stats,
        "v4_phaseC_first_reset_raw": v4_c_resets,
        "excluded_invalid": "Sep/Nov-23 mixR excluded (SQLITE_FULL INVALID)",
        "seungcom_revD_note": "SeungCom revD (9/9 VALID) completed separately (see Fig_02_Ablation & Table_Data)",
    }

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.0, 4.0), gridspec_kw={"width_ratios": [1.45, 1.0]})
    t_arr = np.array(traj_times)
    line_specs = [
        ("revA-random", "Random (n=3)", PALETTE["random"], "-", 1.5),
        ("revA-v1", "V1 NoDrift (n=3)", PALETTE["v1"], "-.", 1.5),
        ("revA-v4", "iCAT-v4 (n=3)", PALETTE["v4"], "-", 2.0),
        ("arm47", "Fixed CAT-47 (n=1 ref)", PALETTE["arm47"], "--", 1.3),
    ]
    for pol, lbl, col, ls, lw in line_specs:
        m = np.array(traj_data[pol]["mean"])
        sd = np.array(traj_data[pol]["sd"])
        ax1.plot(t_arr, m, label=lbl, color=col, linestyle=ls, linewidth=lw)
        if traj_data[pol]["n"] >= 3:
            ax1.fill_between(t_arr, m - sd, m + sd, color=col, alpha=0.14, linewidth=0)
    for xline, txt in [(30, "T1: FIO→YCSB-A"), (60, "T2: YCSB-A→FIO 2")]:
        ax1.axvline(xline, color="#333333", linestyle=":", linewidth=1.1)
        ax1.text(xline + 0.8, 3.02, txt, fontsize=7.6, fontweight="bold", color="#333333", va="top")
    ax1.set_xlabel("Elapsed Time (min)")
    ax1.set_ylabel("5-min Rolling WAF")
    ax1.set_title("(a) Full mixFYF Trajectory (mean ± SD, n=3)")
    ax1.set_xlim(5, 90)
    ax1.set_ylim(0.95, 3.12)
    ax1.legend(loc="lower left", fontsize=7.6)

    # Panel (b): Phase C zoom (60..90 min) + reset marker
    mask_c = t_arr >= 60
    tc = t_arr[mask_c]
    for pol, lbl, col, ls, lw in line_specs:
        m = np.array(traj_data[pol]["mean"])[mask_c]
        sd = np.array(traj_data[pol]["sd"])[mask_c]
        ax2.plot(tc, m, label=lbl, color=col, linestyle=ls, linewidth=lw)
        if traj_data[pol]["n"] >= 3:
            ax2.fill_between(tc, m - sd, m + sd, color=col, alpha=0.15, linewidth=0)
    reset_min = 60.0 + v4_reset_stats["mean"] / 60.0
    ax2.axvline(reset_min, color=PALETTE["v4"], linestyle="--", linewidth=1.2)
    ax2.annotate(f"iCAT-v4 Drift Reset\n{v4_reset_stats['mean']:.1f}s (61.7–65.5s, 3/3)",
                 xy=(reset_min, 2.38), xytext=(65.5, 2.15),
                 fontsize=7.6, fontweight="bold", color=PALETTE["v4"],
                 arrowprops={"arrowstyle": "->", "color": PALETTE["v4"], "lw": 1.0},
                 bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": PALETTE["v4"]})
    ax2.set_xlabel("Elapsed Time in Phase C (min)")
    ax2.set_ylabel("5-min Rolling WAF")
    ax2.set_title("(b) Post-Transition Adaptation (Phase C Zoom)")
    ax2.set_xlim(60, 90)
    ax2.set_ylim(2.05, 3.05)
    ax2.text(0.5, -0.22, "Valid GoCom revA data only (Sep/Nov mixR INVALID excluded; SeungCom revD 9/9 reported separately).",
             transform=ax2.transAxes, ha="center", va="top", fontsize=7.4, style="italic",
             bbox={"boxstyle": "round,pad=0.25", "facecolor": "#F4F8FB", "edgecolor": PALETTE["v4"]})
    fig.suptitle("Figure 3. Workload Transition & Adaptation Trajectory on Valid mixFYF (GoCom revA, n=3)",
                 fontsize=10.0, fontweight="bold", y=1.02)
    fig.tight_layout()
    f3_paths = save_figure(fig, "figure03_adaptation")

    # =========================================================================
    # FIGURE 04: Cumulative Exploration Cost (E3 / M6)
    # =========================================================================
    # Dataset A: GoCom revA mixFYF (90m, n=3)
    exp_gocom_order = ["revA-random", "revA-v2", "revA-v4", "revA-v1"]
    exp_gocom_labels = ["Random\n(n=3)", "V2\n(NoElim/NoSettle)", "iCAT-v4\n(Full)", "V1\n(NoDrift)"]
    exp_gocom_share = {}
    exp_gocom_sel = {}
    for p in exp_gocom_order:
        rows_p = [r for r in revA_exp_rows if r["policy"] == p]
        exp_gocom_share[p] = calc_summary([float(r["explore_share_windows"]) * 100.0 for r in rows_p])
        exp_gocom_sel[p] = calc_summary([float(r["selections"]) for r in rows_p])

    # Dataset B: SeungCom resource-v124 FIO-Fast (30m, n=3)
    res_cat47_gc = float(np.mean([int(r["gc_pages"]) for r in res_raw_rows if r["policy"] == "Fixed CAT-47"]))
    exp_seung_order = ["iCAT v1", "iCAT v2", "iCAT v4"]
    exp_seung_extra_gc = {}
    exp_seung_decisions = {}
    for p in exp_seung_order:
        rows_p = [r for r in res_raw_rows if r["policy"] == p]
        exp_seung_extra_gc[p] = calc_summary([(int(r["gc_pages"]) / res_cat47_gc - 1.0) * 100.0 for r in rows_p])
        exp_seung_decisions[p] = calc_summary([int(r["decisions"]) for r in rows_p])

    verified_plot_data["fig04_exploration"] = {
        "gocom_mixFYF_explore_share_pct": exp_gocom_share,
        "gocom_mixFYF_selections": exp_gocom_sel,
        "seungcom_fiofast_extra_gc_pct": exp_seung_extra_gc,
        "seungcom_fiofast_decisions": exp_seung_decisions,
        "seungcom_cat47_mean_gc_pages": res_cat47_gc,
    }

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.4, 4.1), gridspec_kw={"wspace": 0.28})
    # Panel (a)
    xa = np.arange(len(exp_gocom_order))
    ma = [exp_gocom_share[p]["mean"] for p in exp_gocom_order]
    ca = [exp_gocom_share[p]["ci_half"] for p in exp_gocom_order]
    colsa = [PALETTE["random"], PALETTE["v2"], PALETTE["v4"], PALETTE["v1"]]
    ba = ax1.bar(xa, ma, width=0.55, color=colsa, edgecolor="#222222", linewidth=0.8, yerr=ca, capsize=4)
    ax1.set_xticks(xa)
    ax1.set_xticklabels(exp_gocom_labels, fontsize=8.0)
    ax1.set_ylabel("Non-Incumbent Exploration Share (%)")
    ax1.set_title("(a) GoCom mixFYF (90m, n=3): Exploration Share")
    ax1.set_ylim(0, 114)
    for b, m, c, p in zip(ba, ma, ca, exp_gocom_order):
        sel_m = exp_gocom_sel[p]["mean"]
        ax1.text(b.get_x() + b.get_width() / 2, m + c + 2.0, f"{m:.1f}%\n({sel_m:.0f} sel.)", ha="center", va="bottom", fontsize=7.5, fontweight="bold")

    # Panel (b)
    xb = np.arange(len(exp_seung_order))
    mb = [exp_seung_extra_gc[p]["mean"] for p in exp_seung_order]
    cb = [exp_seung_extra_gc[p]["ci_half"] for p in exp_seung_order]
    colsb = [PALETTE["v1"], PALETTE["v2"], PALETTE["v4"]]
    bb = ax2.bar(xb, mb, width=0.52, color=colsb, edgecolor="#222222", linewidth=0.8, yerr=cb, capsize=4)
    ax2.set_xticks(xb)
    ax2.set_xticklabels(["iCAT v1\n(n=3)", "iCAT v2\n(n=3)", "iCAT v4\n(n=3)"])
    ax2.set_ylabel("Extra GC Copy Pages vs. CAT-47 (%)")
    ax2.set_title("(b) SeungCom FIO-Fast (30m, n=3): GC Copy Overhead")
    ax2.set_ylim(0, 42)
    for b, m, c, p in zip(bb, mb, cb, exp_seung_order):
        dec_m = exp_seung_decisions[p]["mean"]
        ax2.text(b.get_x() + b.get_width() / 2, m + c + 0.8, f"+{m:.1f}%\n({dec_m:.0f} dec.)", ha="center", va="bottom", fontsize=7.8, fontweight="bold")
    fig.suptitle("Figure 4. Cumulative Exploration Overhead (Separated by Host & Workload; Error bars = 95% t-CI, df=2)",
                 fontsize=9.8, fontweight="bold", y=1.02)
    fig.tight_layout()
    f4_paths = save_figure(fig, "figure04_exploration")

    # =========================================================================
    # FIGURE 05: Parameter Sensitivity (E6) — LIVE DATA COMPLETED (9/9 runs, n=3)
    # =========================================================================
    elim10_wafs = [r["waf_total"] for r in by_pol["revC-elim10"]]
    elim10_st = calc_summary(elim10_wafs)
    elim10_mean = elim10_st["mean"]
    revC_v4_wafs = [r["waf_total"] for r in by_pol["revC-v4"]]
    revC_v4_st = calc_summary(revC_v4_wafs)
    revC_v4_mean = revC_v4_st["mean"]
    elim25_wafs = [r["waf_total"] for r in by_pol["revC-elim25"]]
    elim25_st = calc_summary(elim25_wafs)
    elim25_mean = elim25_st["mean"]
    revC_online_wafs = [r["waf_total"] for r in by_pol["revC-online"]]
    revC_online_st = calc_summary(revC_online_wafs)
    revC_online_welch = calc_welch(revC_online_wafs, revC_v4_wafs)
    w_e10_v4 = calc_welch(elim10_wafs, revC_v4_wafs)
    w_e25_v4 = calc_welch(elim25_wafs, revC_v4_wafs)
    replay_data = []
    for r in elim_replay_rows:
        replay_data.append({
            "threshold_pct": float(r["threshold"]) * 100.0,
            "mean_survivors": float(r["mean_survivors"]),
            "min_survivors": int(r["min_survivors"]),
            "ref_survival_pct": float(r["ref_arm_survival_rate"]) * 100.0,
            "arm47_survival_pct": float(r["arm47_survival_rate"]) * 100.0,
        })
    verified_plot_data["fig05_parameters"] = {
        "status": "COMPLETED (GoCom revC 15/15 VALID; all ELIM 10%/15%/25% at n=3)",
        "live_revC": {
            "elim10_pct": {"n": 3, "waf": elim10_mean, "sd": elim10_st["sd"], "ci_half": elim10_st["ci_half"], "raw": elim10_wafs, "stat_allowed": True, "welch_vs_v4": w_e10_v4},
            "elim15_v4_pct": {"n": 3, "waf": revC_v4_mean, "sd": revC_v4_st["sd"], "ci_half": revC_v4_st["ci_half"], "raw": revC_v4_wafs, "stat_allowed": True},
            "elim25_pct": {"n": 3, "waf": elim25_mean, "sd": elim25_st["sd"], "ci_half": elim25_st["ci_half"], "raw": elim25_wafs, "stat_allowed": True, "welch_vs_v4": w_e25_v4},
            "online_orig": {"n": 3, "waf": revC_online_st["mean"], "sd": revC_online_st["sd"], "ci_half": revC_online_st["ci_half"], "raw": revC_online_wafs, "stat_allowed": True, "welch_vs_v4": revC_online_welch},
        },
        "offline_replay_rationale": replay_data,
    }

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.6, 4.2), gridspec_kw={"wspace": 0.28})
    # Panel (a): Live E6 COMPLETED (9/9 runs, n=3 per threshold)
    x5 = np.arange(3)
    m5 = [elim10_mean, revC_v4_mean, elim25_mean]
    c5 = [elim10_st["ci_half"], revC_v4_st["ci_half"], elim25_st["ci_half"]]
    cols5 = [PALETTE["noelim"], PALETTE["v4"], PALETTE["v1"]]
    raw5 = [elim10_wafs, revC_v4_wafs, elim25_wafs]
    b5 = ax1.bar(x5, m5, width=0.50, color=cols5, edgecolor="#222222", linewidth=0.8, yerr=c5, capsize=5, error_kw={"elinewidth": 1.3, "ecolor": "#222222"})
    for idx5, ys5 in enumerate(raw5):
        ax1.scatter([x5[idx5] - 0.08, x5[idx5], x5[idx5] + 0.08], ys5, color="white", edgecolor="#111111", s=24, zorder=6, linewidth=0.85)
    for b, m, c in zip(b5, m5, c5):
        ax1.text(b.get_x() + b.get_width() / 2, m + c + 0.008, f"{m:.4f}\n±{c:.4f}", ha="center", va="bottom", fontsize=7.6, fontweight="bold")
    ax1.set_xticks(x5)
    ax1.set_xticklabels(["10% Threshold\n(revC-elim10, n=3)", "15% Default\n(revC-v4, n=3)", "25% Threshold\n(revC-elim25, n=3)"])
    ax1.set_ylabel("Overall WAF (mixFYF 250k)")
    ax1.set_title("(a) Live E6 Experiment (GoCom revC, n=3)")
    ax1.set_xlim(-0.55, 2.55)
    ax1.set_ylim(2.00, 2.34)
    ax1.text(0.5, 0.95,
             f"Welch vs. 15% Default (same-batch n=3):\n"
             f"10% − 15%: {w_e10_v4['delta']:+.4f} [{w_e10_v4['ci_lo']:+.3f}, {w_e10_v4['ci_hi']:+.3f}] (CI incl. 0)\n"
             f"25% − 15%: {w_e25_v4['delta']:+.4f} [{w_e25_v4['ci_lo']:+.3f}, {w_e25_v4['ci_hi']:+.3f}] (CI incl. 0)",
             transform=ax1.transAxes, ha="center", va="top", fontsize=7.2, color="#1F3864",
             bbox={"boxstyle": "round,pad=0.28", "facecolor": "#F4F8FB", "edgecolor": PALETTE["v4"]})

    # Panel (b): Preliminary Offline Replay Rationale (not live device WAF)
    thrs = [d["threshold_pct"] for d in replay_data]
    surv = [d["mean_survivors"] for d in replay_data]
    ref_s = [d["ref_survival_pct"] for d in replay_data]
    ax2_r = ax2.twinx()
    ax2_r.spines["top"].set_visible(False)
    l1 = ax2.plot(thrs, ref_s, "o-", color=PALETTE["v4"], linewidth=1.8, markersize=6, label="Ref. Arm Survival Rate (%)")
    l2 = ax2_r.plot(thrs, surv, "s--", color=PALETTE["random"], linewidth=1.5, markersize=5.5, label="Mean Surviving Arms (of 45)")
    ax2.axvline(15.0, color="#333333", linestyle=":", linewidth=1.1)
    ax2.annotate("Default = 15%\n(87.5% ref survival,\n19.4/45 arms)", xy=(15.0, 87.5), xytext=(26.0, 56.0),
                 fontsize=7.6, color="#222222",
                 arrowprops={"arrowstyle": "->", "color": "#444444", "lw": 0.9},
                 bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "#AAAAAA"})
    ax2.set_xlabel("Elimination Threshold (%)")
    ax2.set_ylabel("Reference Arm Survival Rate (%)", color=PALETTE["v4"])
    ax2_r.set_ylabel("Mean Surviving Candidates", color=PALETTE["random"])
    ax2.set_title("(b) Offline Replay Rationale (24 Sweeps, Not Live WAF)")
    ax2.set_ylim(0, 112)
    ax2_r.set_ylim(0, 50)
    lines = l1 + l2
    ax2.legend(lines, [l.get_label() for l in lines], loc="lower right", fontsize=7.6)
    fig.suptitle("Figure 5. Parameter Sensitivity (E6): Live Elimination Threshold Sweep (GoCom revC, n=3) & Offline Replay",
                 fontsize=9.8, fontweight="bold", y=1.02)
    fig.tight_layout()
    f5_paths = save_figure(fig, "figure05_parameters")

    # =========================================================================
    # FIGURE 06: Candidate Space Validity (E7: 60 vs 45 Arms & k=2 Exclusion) — COMPLETED
    # =========================================================================
    arm60_n1_waf = by_pol["revB-arm60"][0]["waf_total"]
    revC_arm60_wafs = [r["waf_total"] for r in by_pol["revC-arm60"]]
    revC_arm60_st = calc_summary(revC_arm60_wafs)
    revC_arm60_mean = revC_arm60_st["mean"]
    w_arm60_v4 = calc_welch(revC_arm60_wafs, revC_v4_wafs)
    v4_revA_mean = f1_overall["revA-v4"]["mean"]
    verified_plot_data["fig06_candidates"] = {
        "status": "COMPLETED (Full 60-arm sweeps VALID + Live GoCom revC 60 vs 45 n=3 VALID)",
        "full_60arm_sweeps": {k: {kk: vv for kk, vv in v.items() if not kk.endswith("_wafs")} for k, v in sweeps.items()},
        "live_revC_60vs45": {
            "status": "COMPLETED (6/6 runs VALID)",
            "revB_arm60_n1_pilot": arm60_n1_waf,
            "revC_arm60_n3": revC_arm60_st,
            "revC_arm60_raw": revC_arm60_wafs,
            "revC_v4_n3": revC_v4_st,
            "revC_v4_raw": revC_v4_wafs,
            "welch_60_minus_45": w_arm60_v4,
            "revA_v4_n3_ref": v4_revA_mean,
        },
    }

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.2, 4.1), gridspec_kw={"width_ratios": [1.30, 1.05], "wspace": 0.28})
    # Panel (a): k=2 (15 excluded) vs k>=4 (45 retained) across 3 verified 60/60 sweeps
    w_names = list(sweeps.keys())
    x6 = np.arange(len(w_names))
    w6 = 0.34
    k2_med = [sweeps[k]["k2_median"] for k in w_names]
    k2_err_lo = [sweeps[k]["k2_median"] - sweeps[k]["k2_min"] for k in w_names]
    k2_err_hi = [sweeps[k]["k2_max"] - sweeps[k]["k2_median"] for k in w_names]
    k4_med = [sweeps[k]["k4_median"] for k in w_names]
    k4_err_lo = [sweeps[k]["k4_median"] - sweeps[k]["k4_min"] for k in w_names]
    k4_err_hi = [sweeps[k]["k4_max"] - sweeps[k]["k4_median"] for k in w_names]
    b_k2 = ax1.bar(x6 - w6 / 2, k2_med, width=w6, color=PALETTE["random"], edgecolor="#222222", linewidth=0.8,
                   yerr=[k2_err_lo, k2_err_hi], capsize=4, label="Excluded k=2 (15 arms, med & min–max)")
    b_k4 = ax1.bar(x6 + w6 / 2, k4_med, width=w6, color=PALETTE["v4"], edgecolor="#222222", linewidth=0.8,
                   yerr=[k4_err_lo, k4_err_hi], capsize=4, label="Retained k∈{4,7,10} (45 arms, med & min–max)")
    ax1.set_xticks(x6)
    ax1.set_xticklabels(w_names)
    ax1.set_ylabel("Single-Workload Sweep WAF")
    ax1.set_title("(a) Verified 60/60 Full Sweeps: k=2 vs. k≥4")
    ax1.set_ylim(1.0, 2.45)
    for idx, k in enumerate(w_names):
        ax1.text(x6[idx] - w6 / 2, sweeps[k]["k2_max"] + 0.03, f"best\n#{sweeps[k]['k2_best_rank']}", ha="center", va="bottom", fontsize=7.3, color=PALETTE["random"], fontweight="bold")
        ax1.text(x6[idx] + w6 / 2, sweeps[k]["k4_max"] + 0.03, f"best\n#{sweeps[k]['k4_best_rank']}", ha="center", va="bottom", fontsize=7.3, color=PALETTE["v4"], fontweight="bold")
    ax1.legend(loc="upper right", fontsize=7.3)

    # Panel (b): Live 60 vs 45 arms E7 COMPLETED (n=3 vs n=3)
    x6b = np.arange(2)
    m6b = [revC_arm60_mean, revC_v4_mean]
    c6b = [revC_arm60_st["ci_half"], revC_v4_st["ci_half"]]
    b6b = ax2.bar(x6b, m6b, width=0.48, color=[PALETTE["v2"], PALETTE["v4"]], edgecolor="#222222", linewidth=0.8,
                  yerr=c6b, capsize=5, error_kw={"elinewidth": 1.3, "ecolor": "#222222"})
    ax2.scatter([-0.08, 0.0, 0.08], revC_arm60_wafs, color="white", edgecolor="#111111", s=24, zorder=6, linewidth=0.85)
    ax2.scatter([0.92, 1.0, 1.08], revC_v4_wafs, color="white", edgecolor="#111111", s=24, zorder=6, linewidth=0.85)
    ax2.scatter([0.28], [arm60_n1_waf], color="#B2182B", marker="D", s=34, zorder=6, label=f"revB pilot (n=1: {arm60_n1_waf:.4f})")
    for b, m, c in zip(b6b, m6b, c6b):
        ax2.text(b.get_x() + b.get_width() / 2, m + c + 0.008, f"{m:.4f}\n±{c:.4f}", ha="center", va="bottom", fontsize=7.6, fontweight="bold")
    ax2.set_xticks(x6b)
    ax2.set_xticklabels(["60 Arms\n(incl. k=2, n=3)", "45 Arms\n(iCAT-v4, n=3)"])
    ax2.set_ylabel("Overall WAF (mixFYF 250k)")
    ax2.set_title("(b) Live E7 Comparison (GoCom revC, n=3)")
    ax2.set_xlim(-0.55, 1.55)
    ax2.set_ylim(2.00, 2.33)
    ax2.text(0.5, 0.95,
             f"Δ (60 − 45) = {w_arm60_v4['delta']:+.4f}\nWelch 95% CI [{w_arm60_v4['ci_lo']:+.3f}, {w_arm60_v4['ci_hi']:+.3f}] (CI incl. 0)",
             transform=ax2.transAxes, ha="center", va="top", fontsize=7.3, color="#1F3864",
             bbox={"boxstyle": "round,pad=0.28", "facecolor": "#F4F8FB", "edgecolor": PALETTE["v4"]})
    ax2.legend(loc="lower right", fontsize=7.2)
    fig.suptitle("Figure 6. Candidate Space Reduction (E7: 60 → 45 Arms by Excluding k=2; Error Bars = 95% t-CI)",
                 fontsize=9.9, fontweight="bold", y=1.02)
    fig.tight_layout()
    f6_paths = save_figure(fig, "figure06_candidates")

    # =========================================================================
    # FIGURE 07: CPU & Memory Resource Efficiency (E5 / M5)
    # =========================================================================
    # Memory (exact gdb sizeof across 4 partitions)
    mem_data = {
        "iCAT_v4_learning_only_B": 10112,
        "iCAT_v4_shared_param_B": 512,
        "iCAT_v4_total_struct_B": 10624,
        "SmartGC_qtable_B": 640000,
        "SmartGC_cand_sort_state_B": 1048576 + 262144 + 928,
        "SmartGC_learning_only_B": 1951648,
        "SmartGC_gcbuf_B": 393216,
        "SmartGC_total_B": 2343936,
        "ratio_learning_only": 1951648 / 10112,
        "ratio_with_gcbuf": 2343936 / 10112,
    }
    # GoCom revA CPU (90 min mixFYF, n=3)
    cpu_gocom = {}
    for p in ["revA-random", "revA-v1", "revA-v4", "revA-v2"]:
        rows_p = [r for r in revA_cpu_rows if r["policy"] == p]
        cpu_gocom[p] = {
            "total_ms": calc_summary([float(r["learner_total_ms"]) for r in rows_p]),
            "mean_us": calc_summary([float(r["learner_mean_us"]) for r in rows_p]),
            "calls": calc_summary([float(r["learner_calls"]) for r in rows_p]),
        }
    # SeungCom resource-v124 CPU (30 min FIO-Fast, n=3)
    cpu_seung = {}
    cat47_ongc_ns = float(np.mean([float(r["mean_ns"]) for r in res_cpu_rows if r["policy"] == "Fixed CAT-47" and r["slot"] == "ongc"]))
    for p in ["iCAT v1", "iCAT v2", "iCAT v4"]:
        alg_ms = []
        net_hook_ns = []
        for rep_i in [1, 2, 3]:
            obs = [int(r["sum_ns"]) for r in res_cpu_rows if r["policy"] == p and int(r["rep"]) == rep_i and r["slot"] == "observe"][0]
            sa = [int(r["sum_ns"]) for r in res_cpu_rows if r["policy"] == p and int(r["rep"]) == rep_i and r["slot"] == "setarm"][0]
            ongc_m = [float(r["mean_ns"]) for r in res_cpu_rows if r["policy"] == p and int(r["rep"]) == rep_i and r["slot"] == "ongc"][0]
            alg_ms.append((obs + sa) / 1e6)
            net_hook_ns.append(ongc_m - cat47_ongc_ns)
        cpu_seung[p] = {
            "alg_ms": calc_summary(alg_ms),
            "net_hook_ns_per_gc": calc_summary(net_hook_ns),
        }

    # Separated M5 CPU/GC metrics from resource-v124-20261114/report/cpu_overhead_summary.csv (FIO-Fast 30m, n=3)
    m5_sep = {}
    for row in res_cpu_summary_rows:
        pol = row["policy"]
        met = row["metric"]
        if row["mean"] not in ("미측정", ""):
            m5_sep.setdefault(pol, {})[met] = {"mean": float(row["mean"]), "sd": float(row["std"])}

    verified_plot_data["fig07_resources"] = {
        "memory_4partitions": mem_data,
        "cpu_gocom_mixFYF_90m": cpu_gocom,
        "cpu_seungcom_fiofast_30m": cpu_seung,
        "cpu_seungcom_fiofast_30m_separated": {
            pol: {
                "reward_update_ms": m5_sep[pol]["보상 갱신 [ms]"]["mean"],
                "policy_choose_ms": m5_sep[pol]["정책 선택 [ms]"]["mean"],
                "set_arm_ms": m5_sep[pol]["set_arm [ms]"]["mean"],
                "printk_ms": m5_sep[pol]["판단 기록 printk [ms]"]["mean"],
                "on_gc_net_ns": m5_sep[pol]["GC당 학습 훅 순비용 (추정, 시계 비용 제외) [ns]"]["mean"],
                "do_gc_minus_ongc_ms": m5_sep[pol]["GC 시간 (do_gc - on_gc) [ms] — 에뮬레이터 GC는 데이터 복사 없이 매핑만 갱신"]["mean"],
            }
            for pol in ["Fixed CAT-47", "iCAT v1", "iCAT v2", "iCAT v4"]
        },
        "smartgc_cpu": "RUNNING on GoCom m1-20261126 (userspace sim 12/12 OK: iCAT 53.0us vs SmartGC 7.6us/GC; kernel mixY smokes 2/2 OK; main 1/6 running)",
    }

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.4, 4.2), gridspec_kw={"wspace": 0.28})
    # Panel (a): Memory footprint (Log scale KiB, 4 partitions)
    x7a = np.arange(3)
    mem_kib = [
        mem_data["iCAT_v4_learning_only_B"] / 1024.0,
        mem_data["SmartGC_learning_only_B"] / 1024.0,
        mem_data["SmartGC_total_B"] / 1024.0,
    ]
    b7a = ax1.bar(x7a, mem_kib, width=0.52, color=[PALETTE["v4"], PALETTE["smartgc"], "#E08214"], edgecolor="#222222", linewidth=0.8)
    ax1.set_yscale("log")
    ax1.set_xticks(x7a)
    ax1.set_xticklabels(["iCAT-v4\n(Learning-only)", "SmartGC\n(Learning-only)", "SmartGC\n(+ GC Buffer)"])
    ax1.set_ylabel("Kernel Memory Footprint (KiB, log scale)")
    ax1.set_title("(a) Memory Overhead (4 Partitions, gdb sizeof)")
    ax1.set_ylim(2, 12000)
    labels_7a = [
        f"{mem_kib[0]:.2f} KiB\n(10,112 B)\n1×",
        f"{mem_kib[1]:,.1f} KiB\n(1.95 MB)\n{mem_data['ratio_learning_only']:.0f}×",
        f"{mem_kib[2]:,.1f} KiB\n(2.34 MB)\n{mem_data['ratio_with_gcbuf']:.0f}×",
    ]
    for b, m, lbl in zip(b7a, mem_kib, labels_7a):
        ax1.text(b.get_x() + b.get_width() / 2, m * 1.18, lbl, ha="center", va="bottom", fontsize=7.6, fontweight="bold")

    # Panel (b): Learner Decision CPU Time (GoCom mixFYF 90m, n=3)
    x7b = np.arange(5)
    cpu_order = ["revA-random", "revA-v1", "revA-v4", "revA-v2"]
    cpu_m = [cpu_gocom[p]["total_ms"]["mean"] for p in cpu_order] + [0.0]
    cpu_c = [cpu_gocom[p]["total_ms"]["ci_half"] for p in cpu_order] + [0.0]
    cpu_cols = [PALETTE["random"], PALETTE["v1"], PALETTE["v4"], PALETTE["v2"], "#DDDDDD"]
    b7b = ax2.bar(x7b[:4], cpu_m[:4], width=0.55, color=cpu_cols[:4], edgecolor="#222222", linewidth=0.8, yerr=cpu_c[:4], capsize=4)
    ax2.bar([4], [0.5], width=0.55, color=PALETTE["pending_bg"], edgecolor=PALETTE["pending_edge"], linestyle="--", linewidth=1.0)
    ax2.text(4, 1.8, "Unmeasured\n(NA)", ha="center", va="bottom", fontsize=7.8, fontweight="bold", color="#666666")
    ax2.set_xticks(x7b)
    ax2.set_xticklabels(["Random\n(n=3)", "V1\n(n=3)", "iCAT-v4\n(n=3)", "V2\n(n=3)", "SmartGC\n(CPU NA)"], fontsize=8.0)
    ax2.set_ylabel("Total Learner Decision CPU (ms / 90 min)")
    ax2.set_title("(b) Learner CPU Cost (GoCom mixFYF 90m, <0.0002% wall)")
    ax2.set_ylim(0, 11.4)
    for b, m, c, p in zip(b7b, cpu_m[:4], cpu_c[:4], cpu_order):
        us_m = cpu_gocom[p]["mean_us"]["mean"]
        ax2.text(b.get_x() + b.get_width() / 2, m + c + 0.25, f"{m:.2f} ms\n({us_m:.1f} µs/call)", ha="center", va="bottom", fontsize=7.3, fontweight="bold")
    ax2.text(0.02, 0.96, f"SeungCom FIO-Fast 30m (n=3):\niCAT-v4 alg = {cpu_seung['iCAT v4']['alg_ms']['mean']:.2f} ms,\nnet GC hook = {cpu_seung['iCAT v4']['net_hook_ns_per_gc']['mean']:.2f} ns/GC (<0.002%)",
             transform=ax2.transAxes, ha="left", va="top", fontsize=7.3,
             bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "#CCCCCC"})
    fig.suptitle("Figure 7. Policy-Level (iCAT) vs. Block-Level (SmartGC) Resource Overhead (Error bars = 95% t-CI, df=2)",
                 fontsize=9.8, fontweight="bold", y=1.02)
    fig.tight_layout()
    f7_paths = save_figure(fig, "figure07_resources")

    # Save verified_plot_data.json for automated consistency verification
    with open(OUT_DIR / "verified_plot_data.json", "w", encoding="utf-8") as f:
        json.dump(verified_plot_data, f, indent=2, ensure_ascii=False)

    # =========================================================================
    # BUILD MASTER EXCEL WORKBOOK: iCAT_Paper_Figures.xlsx (12 exact sheets)
    # =========================================================================
    wb = openpyxl.Workbook()
    # Styles
    FONT_TITLE = Font(name="Calibri", size=13, bold=True, color="1F3864")
    FONT_SUB = Font(name="Calibri", size=10, italic=True, color="44546A")
    FONT_SEC = Font(name="Calibri", size=11, bold=True, color="1F3864")
    FONT_HDR = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    FONT_DATA = Font(name="Calibri", size=10, color="111111")
    FONT_BOLD = Font(name="Calibri", size=10, bold=True, color="111111")
    FONT_WARN = Font(name="Calibri", size=10, bold=True, color="9C0006")
    FONT_OK = Font(name="Calibri", size=10, bold=True, color="006100")

    FILL_HDR = PatternFill("solid", fgColor="1F4E78")
    FILL_SUBHDR = PatternFill("solid", fgColor="D9E1F2")
    FILL_ZEBRA = PatternFill("solid", fgColor="F7F9FC")
    FILL_WARN = PatternFill("solid", fgColor="FFC7CE")
    FILL_PENDING = PatternFill("solid", fgColor="FFF2CC")
    FILL_OK = PatternFill("solid", fgColor="C6EFCE")

    THIN = Side(border_style="thin", color="BFBFBF")
    BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

    def style_table(ws, start_row, end_row, start_col, end_col, num_formats=None):
        num_formats = num_formats or {}
        for r in range(start_row, end_row + 1):
            for c in range(start_col, end_col + 1):
                cell = ws.cell(r, c)
                cell.border = BORDER
                if r == start_row:
                    cell.font = FONT_HDR
                    cell.fill = FILL_HDR
                    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                else:
                    cell.font = FONT_DATA
                    if (r - start_row) % 2 == 0:
                        cell.fill = FILL_ZEBRA
                    if c in num_formats:
                        cell.number_format = num_formats[c]
                        cell.alignment = Alignment(horizontal="right", vertical="center")
                    else:
                        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

    def autofit(ws, max_w=46):
        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            mx = 10
            for cell in col:
                val = str(cell.value or "")
                if val.startswith("="):
                    mx = max(mx, 12)
                else:
                    first_line = max((len(x) for x in val.splitlines()), default=0)
                    mx = max(mx, min(first_line + 3, max_w))
            ws.column_dimensions[col_letter].width = mx

    # --- Sheet 1: README ---
    ws_readme = wb.active
    ws_readme.title = "README"
    ws_readme["A1"] = "iCAT Paper Revision — Master Verified Databook & Figures (Home PC)"
    ws_readme["A1"].font = FONT_TITLE
    ws_readme["A2"] = f"Generated: {GENERATED_AT} | Generator: report/paper-figures/build_paper_figures.py"
    ws_readme["A2"].font = FONT_SUB

    readme_rows = [
        ["Field", "Value / Rule"],
        ["Repository", "https://github.com/oyeong011/iCAT-experiments"],
        ["GoCom Branch & Commit", f"{REF_GOCOM} @ {commit_gocom}"],
        ["SeungCom Branch & Commit", f"{REF_MAIN} @ {commit_main}"],
        ["Resource Branch & Commit", f"{REF_RES} @ {commit_res}"],
        ["Validity Gate", "exit_code=0, module SHA256 match, WAF two-path match (summary = final-control = partition sum), FIO err=0, YCSB fail<=1% & SQLITE_FULL=0, kernel BUG/Oops/WARNING=0"],
        ["Invalid Data Excluded", "Sep 2026 mixA/B/H/J/R & Nov-23 mixR (SQLITE_FULL), mixG (0-byte YCSB), early mixY-smartgc (ENOSPC), Oct-10 mixY-fixed47 outlier"],
        ["Batch Separation Rule", "Never combine different hosts (GoCom Ryzen vs SeungCom i7), workloads, YCSB record counts (250k/300k/600k), or months. Cross-batch revB vs revA explicitly flagged."],
        ["Statistical Rule", "n >= 3 required for 95% Student-t CI (df=n-1) and Welch 95% CI. Any condition with n < 3 displays 'NO STAT (n<3)' and no error bar."],
        ["Fig_01_Random Status", "READY: GoCom revA Random vs v4 n=3 PASS, GoCom revC Original iCAT vs v4 n=3 PASS (+0.2751, g=10.53), SeungCom Online Greedy vs v4 n=3 DONE (honest null -0.0086 [-0.051,+0.034])"],
        ["Fig_02_Ablation Status", "READY (ALL CORE COMPLETE): GoCom revA/revB/revE (same-batch NoElim +0.0913 CI>0, drift12 +0.0720 CI>0) & SeungCom revD/abl (FullReset +0.0596 CI>0, OffBundle +0.1241 Holm p=0.028, NoDiscount null -0.0038) — hosts strictly separated"],
        ["Fig_03_Adaptation Status", "READY: GoCom revA mixFYF 30s time-series n=3 & SeungCom revD 9/9 COMPLETED; Sep/Nov mixR excluded (INVALID)"],
        ["Fig_04_Exploration Status", "READY: GoCom revA mixFYF n=3 & SeungCom resource-v124 FIO-Fast 30m n=3 (strictly separated panels)"],
        ["Fig_05_Parameters Status", "READY (COMPLETED): GoCom revC ELIM 10%/15%/25% n=3, GoCom revE DRIFT 12.5% vs 25% n=3 (+0.0720 CI>0), SeungCom batchG DRIFT 50% vs 25% n=3 (+0.0183 ns)"],
        ["Fig_06_Candidates Status", "READY (COMPLETED): 3x60 full sweeps VALID + live GoCom revC 60 vs 45 arms n=3 VALID (6/6 runs; Δ=+0.0282 [-0.032, +0.089], CI incl. 0)"],
        ["Fig_07_Resources Status", "READY (COMPLETED — m1 2/2 n=1): iCAT CPU separated (n=3), gdb sizeof memory (193x/232x), & GoCom m1-20261126 2/2 VALID (VmallocUsed +2,904 kB, GC ktime 98.4 vs 17.8 us/GC, LEARN 4.3 vs 47.6 s; n=1 no stat)"],
    ]
    for idx, row in enumerate(readme_rows, start=4):
        ws_readme.cell(idx, 1, row[0])
        ws_readme.cell(idx, 2, row[1])
    style_table(ws_readme, 4, 4 + len(readme_rows) - 1, 1, 2)
    ws_readme.column_dimensions["A"].width = 28
    ws_readme.column_dimensions["B"].width = 115

    # --- Sheet 2: Experiment_Index ---
    ws_idx = wb.create_sheet("Experiment_Index")
    ws_idx["A1"] = "Experiment Index (E1–E8 & Active Revision Campaigns)"
    ws_idx["A1"].font = FONT_TITLE
    idx_headers = ["Exp_ID", "Campaign", "Host", "Workload", "Git_Branch", "Git_Commit", "Status", "Valid_Runs", "Planned_Runs", "Figures_Linked", "Notes"]
    idx_rows = [
        ["E1", "revD-20261124 (v4/nodrift/fullreset)", "SeungCom (i7-7700)", "mixFYF 250k (1800s x3)", REF_MAIN, commit_main, "COMPLETED (VERIFIED)", 9, 9, "Fig_02_Ablation, Fig_03_Adaptation", "9/9 VALID! FullReset-v4 CI>0 (Tot +0.0596 g=3.08, PhC +0.1296 g=3.78); NoDrift-v4 3/3 worse (+0.0681) but CI incl. 0 (high SD)"],
        ["E1", "revision-20261123/mixR", "SeungCom (i7-7700)", "mixR 600k", REF_MAIN, commit_main, "INVALID", 0, 9, "EXCLUDED", "SQLITE_FULL contamination; Phase A only valid"],
        ["E1/E2", "revA-20261114 (v4/v1/v2/random/arm47)", "GoCom (Ryzen 3600XT)", "mixFYF 250k (1800s x3)", REF_GOCOM, commit_gocom, "COMPLETED", 13, 13, "Fig_01, Fig_02, Fig_03, Fig_04, Fig_07", "100% valid (YCSB 0% fail, SQLITE_FULL=0)"],
        ["E1/E7", "revB-20261122 (noelim/nosettle/v4/arm60)", "GoCom (Ryzen 3600XT)", "mixFYF 250k (1800s x3)", REF_GOCOM, commit_gocom, "COMPLETED (CAVEAT)", 8, 8, "Fig_02_Ablation, Fig_06_Candidates", "Valid raw runs; revB-v4 bridge (+4.8 SD) failed bridge gate"],
        ["E2/E6/E7", "revC-20261124 (v4/elim10/elim25/arm60/online)", "GoCom (Ryzen 3600XT)", "mixFYF 250k (1800s x3)", REF_GOCOM, commit_gocom, "COMPLETED (VERIFIED)", 15, 15, "Fig_01, Fig_05, Fig_06", "15/15 VALID! online-v4 +0.2751 [+0.203,+0.347] (PASS); elim10/25 & arm60 CI incl. 0; bridge vs revA-v4 -0.40%"],
        ["M2", "abl-20261125 (v4/nodiscount/bundle-off)", "SeungCom (i7-7700)", "mixFYF 250k (1800s x3)", REF_MAIN, commit_main, "COMPLETED (VERIFIED)", 9, 9, "Ablation, Discount-free", "9/9 VALID (triple-verified)! OffBundle-v4 +0.1241 [+0.073,+0.175] (Holm p=0.028); NoDiscount-v4 -0.0038 [-0.064,+0.057] (honest null)"],
        ["M2/M6", "revE-20261125 (v4/NoElim-isol/drift12)", "GoCom (Ryzen 3600XT)", "mixFYF 250k (1800s x3)", REF_GOCOM, commit_gocom, "COMPLETED (VERIFIED)", 9, 9, "Ablation, NoElim, Fig_05", "9/9 VALID! Same-batch NoElim-v4 +0.0913 [+0.030,+0.153] (g=3.88, Paired>0); drift12-v4 +0.0720 [+0.012,+0.132] (Holm p=0.091)"],
        ["M3", "greedy-20261125 (Online Greedy VARIANT=8)", "SeungCom (i7-7700)", "mixFYF 250k (1800s x3)", REF_MAIN, commit_main, "COMPLETED (VERIFIED)", 3, 3, "Online Greedy", "3/3 VALID (triple-verified, 0/2513 argmin mismatches)! Greedy-revD_v4 -0.0086 [-0.051,+0.034] (honest null)"],
        ["M3/M6", "batchG-20261126 (Greedy GC / drift50 / bg-v4)", "SeungCom (i7-7700)", "mixFYF 250k (1800s x3)", REF_MAIN, commit_main, "COMPLETED (VERIFIED)", 9, 9, "Greedy GC, Fig_05_Parameters", "9/9 VALID (0/36 WAF mismatches)! Greedy GC-v4 +0.5189 [+0.463,+0.574] (Holm p=0.0013, -19.7%; FIO lat lower on Greedy); drift50-v4 +0.0183 [-0.045,+0.081] (ns)"],
        ["Robustness", "arm47-20261127 (Fixed Arm 47 oracle n=3)", "SeungCom (i7-7700)", "mixFYF 250k (1800s x3)", REF_MAIN, commit_main, "COMPLETED (VERIFIED)", 3, 3, "Raw_Data, Statistics, Table_Data", "3/3 VALID! 1.98764±0.00027 [1.98698, 1.98831] (CV=0.013%; GoCom revA n=1 1.987355 inside CI; host-separated, never pooled as n=4)"],
        ["M1/M5", "m1-20261126 (SmartGC-EQ8 vs iCAT-v4 ktime & mem)", "GoCom (Ryzen 3600XT)", "mixY 10h (n=1 per policy)", REF_GOCOM, commit_gocom, "COMPLETED (VERIFIED, n=1)", 2, 2, "Fig_07_Resources", "2/2 VALID (rep2-3 cancelled by user; n=1 no stat)! WAF_nand 3.330 vs 4.553 (-26.9%); VmallocUsed +34,848 vs +37,752 kB (+2,904 kB); GC ktime 98.4 vs 17.8 us/GC (5.5x); LEARN 4.3 vs 47.6 s"],
        ["E3", "revA-20261114 & revD-20261124 adaptation", "GoCom / SeungCom", "mixFYF 250k (1800s x3)", REF_GOCOM, commit_gocom, "COMPLETED (PARTIAL)", 22, 22, "Fig_03_Adaptation, Fig_04_Exploration", "Sep mixR invalid excluded; revA & revD per-partition verified (Phase B low-write limit)"],
        ["E4", "Statistical Reliability (n=3 CI/Welch)", "GoCom / SeungCom", "mixFYF 250k", REF_GOCOM, commit_gocom, "COMPLETED (mixFYF 75 runs)", 75, 75, "All Figures", "n=3 enforced across revA/revB/revC/revD/abl/revE/greedy/batchG (75 verified mixFYF runs + 2 m1 mixY runs = 77 VALID); legacy Table 6/7/9 n=1 disclosed"],
        ["E5", "resource-v124-20261114 + m1-20261126 + sizeof", "SeungCom / GoCom", "FIO-Fast 30m / mixFYF / mixY", REF_RES, commit_res, "COMPLETED (PARTIAL CPU)", 14, 14, "Fig_04_Exploration, Fig_07_Resources", "iCAT separated CPU (n=3), sizeof 193x/232x, m1 Vmalloc +2,904 kB & ktime (98.4 vs 17.8 us/GC) valid; kernel perf CPU & common NVMeVirt cost unmeasured"],
        ["E6", "elim_replay_summary (offline rationale)", "GoCom (analysis)", "24 noelim/V2 sweeps", REF_GOCOM, commit_gocom, "COMPLETED (OFFLINE)", 24, 24, "Fig_05_Parameters", "Offline what-if rationale paired with live revC 9/9 ELIM results"],
        ["E7", "sweep-20260915 (test4, oltp, sqlite-a)", "SeungCom (i7-7700)", "Single-workload 60/60", REF_MAIN, commit_main, "COMPLETED", 180, 180, "Fig_06_Candidates", "All 3 full 60-arm sweeps valid + live revC 60 vs 45 (n=3) valid"],
        ["E8", "Environment Generalization", "None", "Physical SSD / OP / Cap", "N/A", "N/A", "NOT STARTED", 0, 0, "NONE (Limitation)", "Explicitly documented as paper limitation"],
    ]
    for c, h in enumerate(idx_headers, 1):
        ws_idx.cell(3, c, h)
    for r_i, row in enumerate(idx_rows, 4):
        for c_i, val in enumerate(row, 1):
            ws_idx.cell(r_i, c_i, val)
    style_table(ws_idx, 3, 3 + len(idx_rows), 1, len(idx_headers))
    autofit(ws_idx)

    # --- Sheet 3: Raw_Data ---
    ws_raw = wb.create_sheet("Raw_Data")
    ws_raw["A1"] = "Independently Verified Raw Run Data (Validity-Gated Only)"
    ws_raw["A1"].font = FONT_TITLE
    raw_headers = [
        "Run_ID", "Exp_ID", "Host", "Kernel", "Workload", "Policy", "Rep",
        "FIO_Seeds", "iCAT_Seed", "Git_Branch", "Git_Commit", "Module_Name", "Module_SHA256",
        "SHA_Match", "Exit_Code", "FIO_Errors", "YCSB_Load_Recs", "YCSB_Run_Ops", "YCSB_Fail_Pct",
        "SQLITE_FULL", "Kernel_Errors", "Host_Pages", "GC_Pages", "WAF_Total", "WAF_PhaseA",
        "WAF_PhaseB", "WAF_PhaseC", "Two_Path_Match", "Resets", "Validity", "Raw_Path",
    ]
    for c, h in enumerate(raw_headers, 1):
        ws_raw.cell(3, c, h)
    raw_row_map = {}  # policy -> list of excel row numbers in Raw_Data
    for r_i, r in enumerate(raw_runs, 4):
        vals = [
            r["run_id"], r["exp_id"], r["host"], r["kernel"], r["workload"], r["policy"], r["rep"],
            r["fio_seeds"], r["icat_seed"], r["git_branch"], r["git_commit"], r["module_name"], r["module_sha256"],
            "TRUE" if r["sha_match"] else "FALSE", r["exit_code"], r["fio_errors"], r["ycsb_load_records"],
            r["ycsb_run_ops"], r["ycsb_fail_pct"], r["sqlite_full"], r["kernel_errors"],
            r["host_pages"], r["gc_pages"], r["waf_total"], r["waf_A"], r["waf_B"], r["waf_C"],
            "TRUE" if r["two_path_match"] else "FALSE", r["resets"], "VALID" if r["valid"] else "INVALID", r["raw_path"],
        ]
        for c_i, v in enumerate(vals, 1):
            ws_raw.cell(r_i, c_i, v)
        raw_row_map.setdefault(r["policy"], []).append(r_i)
    style_table(ws_raw, 3, 3 + len(raw_runs), 1, len(raw_headers), num_formats={
        7: "0", 9: "0", 15: "0", 16: "0", 17: "#,##0", 18: "#,##0", 19: "0.0000", 20: "0", 21: "0",
        22: "#,##0", 23: "#,##0", 24: "0.000000", 25: "0.000000", 26: "0.000000", 27: "0.000000", 29: "0",
    })
    autofit(ws_raw, max_w=38)

    # Helper to build Excel formula range in Raw_Data for a policy (contiguous rows)
    def raw_range(policy: str, col_letter: str) -> str:
        rows = raw_row_map[policy]
        return f"Raw_Data!${col_letter}${min(rows)}:${col_letter}${max(rows)}"

    # --- Sheet 4: Statistics ---
    ws_stat = wb.create_sheet("Statistics")
    ws_stat["A1"] = "Statistical Summary (Formula-Linked to Raw_Data; CI Strictly Gated at n >= 3)"
    ws_stat["A1"].font = FONT_TITLE
    stat_headers = ["Policy", "Batch", "n", "Mean_WAF", "SD_WAF", "t_crit_95", "CI95_Half", "CI95_Low", "CI95_High", "Mean_PhaseA", "Mean_PhaseB", "Mean_PhaseC", "Stat_Status"]
    stat_pols = [
        ("revA-v4", "revA (GoCom)"),
        ("revA-random", "revA (GoCom)"),
        ("revA-v1", "revA (GoCom)"),
        ("revA-v2", "revA (GoCom)"),
        ("arm47", "revA (GoCom, ref)"),
        ("revB-noelim", "revB (GoCom, cross-batch*)"),
        ("revB-nosettle", "revB (GoCom, cross-batch*)"),
        ("revB-v4", "revB (GoCom bridge)"),
        ("revB-arm60", "revB (GoCom pilot)"),
        ("revC-v4", "revC (GoCom, n=3 DONE)"),
        ("revC-elim10", "revC (GoCom, n=3 DONE)"),
        ("revC-elim25", "revC (GoCom, n=3 DONE)"),
        ("revC-arm60", "revC (GoCom, n=3 DONE)"),
        ("revC-online", "revC (GoCom, n=3 DONE)"),
        ("revD-fullreset", "revD (SeungCom, n=3 DONE)"),
        ("revD-nodrift", "revD (SeungCom, n=3 DONE)"),
        ("revD-v4", "revD (SeungCom, n=3 DONE)"),
        ("abl-v4", "abl (SeungCom, n=3 DONE)"),
        ("abl-nodiscount", "abl (SeungCom, n=3 DONE)"),
        ("abl-bundle-off", "abl (SeungCom, n=3 DONE)"),
        ("revE-v4", "revE (GoCom, n=3 DONE)"),
        ("revE-noelim", "revE (GoCom, n=3 DONE)"),
        ("revE-drift12", "revE (GoCom, n=3 DONE)"),
        ("greedy-online", "greedy (SeungCom, n=3 DONE)"),
    ]
    for c, h in enumerate(stat_headers, 1):
        ws_stat.cell(3, c, h)
    for idx, (pol, batch) in enumerate(stat_pols, 4):
        n = len(raw_row_map[pol])
        rng_tot = raw_range(pol, "X")
        rng_a = raw_range(pol, "Y")
        rng_b = raw_range(pol, "Z")
        rng_c = raw_range(pol, "AA")
        ws_stat.cell(idx, 1, pol)
        ws_stat.cell(idx, 2, batch)
        ws_stat.cell(idx, 3, f"=COUNT({rng_tot})")
        ws_stat.cell(idx, 4, f"=AVERAGE({rng_tot})")
        if n >= 3:
            ws_stat.cell(idx, 5, f"=STDEV.S({rng_tot})")
            ws_stat.cell(idx, 6, f"=T.INV.2T(0.05, C{idx}-1)")
            ws_stat.cell(idx, 7, f"=F{idx}*E{idx}/SQRT(C{idx})")
            ws_stat.cell(idx, 8, f"=D{idx}-G{idx}")
            ws_stat.cell(idx, 9, f"=D{idx}+G{idx}")
            status_str = "VALID (n>=3, CI computed)"
        else:
            for cc in [5, 6, 7, 8, 9]:
                ws_stat.cell(idx, cc, "N/A (n<3)")
            status_str = "NO STAT CONCLUSION (n<3)"
        ws_stat.cell(idx, 10, f"=AVERAGE({rng_a})")
        ws_stat.cell(idx, 11, f"=AVERAGE({rng_b})")
        ws_stat.cell(idx, 12, f"=AVERAGE({rng_c})")
        ws_stat.cell(idx, 13, status_str)
    style_table(ws_stat, 3, 3 + len(stat_pols), 1, len(stat_headers), num_formats={
        3: "0", 4: "0.0000", 5: "0.0000", 6: "0.0000", 7: "0.0000", 8: "0.0000", 9: "0.0000",
        10: "0.0000", 11: "0.0000", 12: "0.0000",
    })
    autofit(ws_stat)

    # --- Sheet 5: Fig_01_Random ---
    ws_f1 = wb.create_sheet("Fig_01_Random")
    ws_f1["A1"] = "Figure 1: Online Policy Learning (iCAT-v4) vs. Random Selection (E2)"
    ws_f1["A1"].font = FONT_TITLE
    ws_f1["A2"] = f"Source: {REF_GOCOM} @ {commit_gocom} (result/revA-20261114/raw/) | Status: VALID (n=3, mixFYF)"
    ws_f1["A2"].font = FONT_SUB

    # Table 1A: Overall comparison (formula-driven + numeric value check)
    ws_f1["A4"] = "Table 1A. Overall WAF Summary (GoCom mixFYF, n=3)"
    ws_f1["A4"].font = FONT_SEC
    f1_h = ["Policy", "n", "Mean_WAF", "SD_WAF", "CI95_Half", "CI95_Low", "CI95_High", "Rep1", "Rep2", "Rep3"]
    for c, h in enumerate(f1_h, 1):
        ws_f1.cell(5, c, h)
    for row_i, (pol, lbl) in enumerate([("revA-random", "Random Selection (45 arms)"), ("revA-v4", "iCAT-v4 (45 arms)")], 6):
        rng = raw_range(pol, "X")
        reps = [r["waf_total"] for r in by_pol[pol]]
        ws_f1.cell(row_i, 1, lbl)
        ws_f1.cell(row_i, 2, f"=COUNT({rng})")
        ws_f1.cell(row_i, 3, f"=AVERAGE({rng})")
        ws_f1.cell(row_i, 4, f"=STDEV.S({rng})")
        ws_f1.cell(row_i, 5, f"=T.INV.2T(0.05,B{row_i}-1)*D{row_i}/SQRT(B{row_i})")
        ws_f1.cell(row_i, 6, f"=C{row_i}-E{row_i}")
        ws_f1.cell(row_i, 7, f"=C{row_i}+E{row_i}")
        ws_f1.cell(row_i, 8, reps[0])
        ws_f1.cell(row_i, 9, reps[1])
        ws_f1.cell(row_i, 10, reps[2])
    # Reference arm47 n=1
    ws_f1.cell(8, 1, "Fixed CAT-47 (n=1 reference, no CI)")
    ws_f1.cell(8, 2, 1)
    ws_f1.cell(8, 3, f1_arm47_ref)
    for cc in [4, 5, 6, 7]:
        ws_f1.cell(8, cc, "N/A (n=1)")
    ws_f1.cell(8, 8, f1_arm47_ref)
    style_table(ws_f1, 5, 8, 1, 10, num_formats={2: "0", 3: "0.0000", 4: "0.0000", 5: "0.0000", 6: "0.0000", 7: "0.0000", 8: "0.0000", 9: "0.0000", 10: "0.0000"})

    # Table 1B: Phase-by-Phase WAF
    ws_f1["A10"] = "Table 1B. Phase-by-Phase Mean WAF & Welch Difference (Random − iCAT-v4, n=3)"
    ws_f1["A10"].font = FONT_SEC
    f1b_h = ["Phase", "Random_Mean", "Random_CI95", "iCAT_v4_Mean", "iCAT_v4_CI95", "Welch_Delta", "Welch_CI95_Low", "Welch_CI95_High", "Excludes_Zero"]
    for c, h in enumerate(f1b_h, 1):
        ws_f1.cell(11, c, h)
    for idx, (ph, pname) in enumerate([("A", "Phase A: FIO-Fast 1"), ("B", "Phase B: YCSB-A 250k"), ("C", "Phase C: FIO-Fast 2")], 12):
        wr = f1_welch_phases[ph]
        ws_f1.cell(idx, 1, pname)
        ws_f1.cell(idx, 2, f1_phases["revA-random"][ph]["mean"])
        ws_f1.cell(idx, 3, f1_phases["revA-random"][ph]["ci_half"])
        ws_f1.cell(idx, 4, f1_phases["revA-v4"][ph]["mean"])
        ws_f1.cell(idx, 5, f1_phases["revA-v4"][ph]["ci_half"])
        ws_f1.cell(idx, 6, wr["delta"])
        ws_f1.cell(idx, 7, wr["ci_lo"])
        ws_f1.cell(idx, 8, wr["ci_hi"])
        ws_f1.cell(idx, 9, "YES" if wr["excludes_zero"] else "NO")
    ws_f1.cell(15, 1, "Overall Total (90 min)")
    ws_f1.cell(15, 2, f1_overall["revA-random"]["mean"])
    ws_f1.cell(15, 3, f1_overall["revA-random"]["ci_half"])
    ws_f1.cell(15, 4, f1_overall["revA-v4"]["mean"])
    ws_f1.cell(15, 5, f1_overall["revA-v4"]["ci_half"])
    ws_f1.cell(15, 6, f1_welch_total["delta"])
    ws_f1.cell(15, 7, f1_welch_total["ci_lo"])
    ws_f1.cell(15, 8, f1_welch_total["ci_hi"])
    ws_f1.cell(15, 9, "YES")
    style_table(ws_f1, 11, 15, 1, 9, num_formats={2: "0.0000", 3: "0.0000", 4: "0.0000", 5: "0.0000", 6: "0.0000", 7: "0.0000", 8: "0.0000"})

    # Native Excel Chart for Fig_01_Random
    ch1 = BarChart()
    ch1.type = "col"
    ch1.grouping = "clustered"
    ch1.title = "Fig 1. Random Selection vs iCAT-v4 (Phase & Overall WAF, n=3)"
    ch1.y_axis.title = "WAF"
    ch1.x_axis.title = "Workload Phase"
    data_ref1 = Reference(ws_f1, min_col=2, max_col=2, min_row=11, max_row=15)
    data_ref2 = Reference(ws_f1, min_col=4, max_col=4, min_row=11, max_row=15)
    cats1 = Reference(ws_f1, min_col=1, min_row=12, max_row=15)
    ch1.add_data(data_ref1, titles_from_data=True)
    ch1.add_data(data_ref2, titles_from_data=True)
    ch1.set_categories(cats1)
    ch1.series[0].graphicalProperties.solidFill = "D55E00"
    ch1.series[1].graphicalProperties.solidFill = "0072B2"
    ch1.width = 18
    ch1.height = 10
    ws_f1.add_chart(ch1, "A17")
    autofit(ws_f1)

    # --- Sheet 6: Fig_02_Ablation ---
    ws_f2 = wb.create_sheet("Fig_02_Ablation")
    ws_f2["A1"] = "Figure 2: Component Ablation on mixFYF (E1 / M2)"
    ws_f2["A1"].font = FONT_TITLE
    ws_f2["A2"] = f"GoCom: {REF_GOCOM} @ {commit_gocom} (revA+revB) | SeungCom: {REF_MAIN} @ {commit_main} (revD 9/9 COMPLETED, same-batch n=3)"
    ws_f2["A2"].font = FONT_SUB

    ws_f2["A4"] = "Table 2A. Ablation Variant WAF & Effect Size vs iCAT-v4 (n=3; *Cross-batch revB vs revA)"
    ws_f2["A4"].font = FONT_SEC
    f2_h = ["Variant", "Batch", "n", "Mean_WAF", "SD_WAF", "CI95_Half", "Welch_Delta_vs_V4", "Welch_CI95_Low", "Welch_CI95_High", "Conclusion"]
    for c, h in enumerate(f2_h, 1):
        ws_f2.cell(5, c, h)
    f2_tbl = [
        ("revA-v4", "iCAT-v4 (Full)", "revA (same)"),
        ("revA-v1", "V1 (NoDrift)", "revA (same)"),
        ("revB-nosettle", "NoSettle*", "revB (cross-batch*)"),
        ("revB-noelim", "NoElim*", "revB (cross-batch*)"),
        ("revA-v2", "V2 (NoElim+NoSettle)", "revA (same)"),
    ]
    for r_i, (pol, lbl, bat) in enumerate(f2_tbl, 6):
        st = f2_stats[pol]
        ws_f2.cell(r_i, 1, lbl)
        ws_f2.cell(r_i, 2, bat)
        ws_f2.cell(r_i, 3, st["n"])
        ws_f2.cell(r_i, 4, st["mean"])
        ws_f2.cell(r_i, 5, st["sd"])
        ws_f2.cell(r_i, 6, st["ci_half"])
        if pol == "revA-v4":
            ws_f2.cell(r_i, 7, 0.0)
            ws_f2.cell(r_i, 8, 0.0)
            ws_f2.cell(r_i, 9, 0.0)
            ws_f2.cell(r_i, 10, "Baseline Control")
        else:
            wr = f2_welch[pol]
            ws_f2.cell(r_i, 7, wr["delta"])
            ws_f2.cell(r_i, 8, wr["ci_lo"])
            ws_f2.cell(r_i, 9, wr["ci_hi"])
            ws_f2.cell(r_i, 10, "CI excludes 0 (Effect confirmed)" if wr["excludes_zero"] else "CI includes 0 (Inconclusive)")
    ws_f2.cell(11, 1, "revB-v4 (Bridge check)")
    ws_f2.cell(11, 2, "revB (n=1)")
    ws_f2.cell(11, 3, 1)
    ws_f2.cell(11, 4, f2_bridge)
    for cc in [5, 6, 7, 8, 9]:
        ws_f2.cell(11, cc, "N/A (n=1)")
    ws_f2.cell(11, 10, "Bridge failed (+4.8 SD vs revA-v4); caveat required")
    style_table(ws_f2, 5, 11, 1, 10, num_formats={3: "0", 4: "0.0000", 5: "0.0000", 6: "0.0000", 7: "0.0000", 8: "0.0000", 9: "0.0000"})

    # Table 2B: SeungCom revD Same-Batch Ablation (n=3, Host-Separated)
    ws_f2["A13"] = "Table 2B. SeungCom revD Same-Batch Drift & Partial Re-Exploration Ablation (mixFYF 250k, n=3, Verified 9/9)"
    ws_f2["A13"].font = FONT_SEC
    f2b_h = ["Variant", "Metric", "n", "Mean_WAF", "SD_WAF", "CI95_Half", "Welch_Delta_vs_revD_V4", "Welch_CI95_Low", "Welch_CI95_High", "Conclusion"]
    for c, h in enumerate(f2b_h, 1):
        ws_f2.cell(14, c, h)
    revD_rows = [
        ("revD-v4 (Partial Reset)", "Overall WAF", f2_revD_tot["revD-v4"], None),
        ("revD-fullreset (45-arm Reset)", "Overall WAF", f2_revD_tot["revD-fullreset"], f2_revD_welch_tot["revD-fullreset"]),
        ("revD-nodrift (Drift Off)", "Overall WAF", f2_revD_tot["revD-nodrift"], f2_revD_welch_tot["revD-nodrift"]),
        ("revD-v4 (Partial Reset)", "Phase C WAF", f2_revD_phC["revD-v4"], None),
        ("revD-fullreset (45-arm Reset)", "Phase C WAF", f2_revD_phC["revD-fullreset"], f2_revD_welch_phC["revD-fullreset"]),
        ("revD-nodrift (Drift Off)", "Phase C WAF", f2_revD_phC["revD-nodrift"], f2_revD_welch_phC["revD-nodrift"]),
    ]
    for idx_d, (lbl, met, st, wr) in enumerate(revD_rows, 15):
        ws_f2.cell(idx_d, 1, lbl)
        ws_f2.cell(idx_d, 2, met)
        ws_f2.cell(idx_d, 3, st["n"])
        ws_f2.cell(idx_d, 4, st["mean"])
        ws_f2.cell(idx_d, 5, st["sd"])
        ws_f2.cell(idx_d, 6, st["ci_half"])
        if wr is None:
            ws_f2.cell(idx_d, 7, 0.0)
            ws_f2.cell(idx_d, 8, 0.0)
            ws_f2.cell(idx_d, 9, 0.0)
            ws_f2.cell(idx_d, 10, "Same-batch Control")
        else:
            ws_f2.cell(idx_d, 7, wr["delta"])
            ws_f2.cell(idx_d, 8, wr["ci_lo"])
            ws_f2.cell(idx_d, 9, wr["ci_hi"])
            ws_f2.cell(idx_d, 10, "CI excludes 0 (Effect confirmed)" if wr["excludes_zero"] else "CI includes 0 (3/3 worse, high SD -> Inconclusive)")
    style_table(ws_f2, 14, 20, 1, 10, num_formats={3: "0", 4: "0.0000", 5: "0.0000", 6: "0.0000", 7: "0.0000", 8: "0.0000", 9: "0.0000"})
    ws_f2.cell(16, 10).fill = FILL_OK
    ws_f2.cell(19, 10).fill = FILL_OK

    ch2 = BarChart()
    ch2.type = "col"
    ch2.title = "Fig 2. Component Ablation — Mean Overall WAF (GoCom revA/revB, n=3)"
    ch2.y_axis.title = "WAF"
    ch2.y_axis.scaling.min = 2.0
    ch2.y_axis.scaling.max = 2.35
    ch2.add_data(Reference(ws_f2, min_col=4, min_row=5, max_row=10), titles_from_data=True)
    ch2.set_categories(Reference(ws_f2, min_col=1, min_row=6, max_row=10))
    ch2.series[0].graphicalProperties.solidFill = "0072B2"
    ch2.width = 18
    ch2.height = 10
    ws_f2.add_chart(ch2, "A22")
    autofit(ws_f2)

    # --- Sheet 7: Fig_03_Adaptation ---
    ws_f3 = wb.create_sheet("Fig_03_Adaptation")
    ws_f3["A1"] = "Figure 3: Workload Transition & Adaptation Trajectory (E3)"
    ws_f3["A1"].font = FONT_TITLE
    ws_f3["A2"] = f"Source: {REF_GOCOM} @ {commit_gocom} (raw control-series.txt, n=3) | Sep/Nov mixR INVALID excluded; SeungCom revD PENDING"
    ws_f3["A2"].font = FONT_SUB

    ws_f3["A4"] = "Table 3A. Phase C First Drift-Reset Latency (YCSB-A -> FIO-Fast 2, n=3)"
    ws_f3["A4"].font = FONT_SEC
    for c, h in enumerate(["Policy", "n", "Rep1_s", "Rep2_s", "Rep3_s", "Mean_s", "SD_s", "CI95_Half_s", "Status"], 1):
        ws_f3.cell(5, c, h)
    ws_f3.cell(6, 1, "iCAT-v4 (revA)")
    ws_f3.cell(6, 2, 3)
    ws_f3.cell(6, 3, v4_c_resets[0])
    ws_f3.cell(6, 4, v4_c_resets[1])
    ws_f3.cell(6, 5, v4_c_resets[2])
    ws_f3.cell(6, 6, "=AVERAGE(C6:E6)")
    ws_f3.cell(6, 7, "=STDEV.S(C6:E6)")
    ws_f3.cell(6, 8, "=T.INV.2T(0.05,B6-1)*G6/SQRT(B6)")
    ws_f3.cell(6, 9, "VALID (3/3 detected)")
    ws_f3.cell(7, 1, "V1 NoDrift (revA)")
    ws_f3.cell(7, 2, 3)
    for cc in [3, 4, 5, 6, 7, 8]:
        ws_f3.cell(7, cc, "None (0 resets)")
    ws_f3.cell(7, 9, "VALID (Drift disabled by design)")
    ws_f3.cell(8, 1, "SeungCom revD (v4/nodrift/fullreset)")
    ws_f3.cell(8, 2, 0)
    for cc in [3, 4, 5, 6, 7, 8]:
        ws_f3.cell(8, cc, "PENDING")
    ws_f3.cell(8, 9, "RUNNING (0/9 main runs)")
    style_table(ws_f3, 5, 8, 1, 9, num_formats={2: "0", 3: "0.0", 4: "0.0", 5: "0.0", 6: "0.0", 7: "0.00", 8: "0.00"})

    ws_f3["A10"] = "Table 3B. 5-Minute Rolling WAF Time-Series (2-min intervals, 5–90 min)"
    ws_f3["A10"].font = FONT_SEC
    t3_h = ["Elapsed_Min", "Phase", "Random_Mean", "V1_NoDrift_Mean", "iCAT_v4_Mean", "CAT47_Ref_n1"]
    for c, h in enumerate(t3_h, 1):
        ws_f3.cell(11, c, h)
    for i, tm in enumerate(traj_times):
        r_i = 12 + i
        ph_lbl = "A (FIO 1)" if tm <= 30 else ("B (YCSB-A)" if tm <= 60 else "C (FIO 2)")
        ws_f3.cell(r_i, 1, tm)
        ws_f3.cell(r_i, 2, ph_lbl)
        ws_f3.cell(r_i, 3, traj_data["revA-random"]["mean"][i])
        ws_f3.cell(r_i, 4, traj_data["revA-v1"]["mean"][i])
        ws_f3.cell(r_i, 5, traj_data["revA-v4"]["mean"][i])
        ws_f3.cell(r_i, 6, traj_data["arm47"]["mean"][i])
    last_t3_row = 11 + len(traj_times)
    style_table(ws_f3, 11, last_t3_row, 1, 6, num_formats={1: "0", 3: "0.0000", 4: "0.0000", 5: "0.0000", 6: "0.0000"})

    ch3 = LineChart()
    ch3.title = "Fig 3. 5-min Rolling WAF Trajectory on mixFYF (n=3)"
    ch3.y_axis.title = "Rolling WAF"
    ch3.x_axis.title = "Elapsed Time (min)"
    ch3.add_data(Reference(ws_f3, min_col=3, max_col=6, min_row=11, max_row=last_t3_row), titles_from_data=True)
    ch3.set_categories(Reference(ws_f3, min_col=1, min_row=12, max_row=last_t3_row))
    ch3.width = 20
    ch3.height = 11
    ws_f3.add_chart(ch3, "H10")
    autofit(ws_f3)

    # --- Sheet 8: Fig_04_Exploration ---
    ws_f4 = wb.create_sheet("Fig_04_Exploration")
    ws_f4["A1"] = "Figure 4: Cumulative Exploration Cost (Strictly Separated by Host & Workload)"
    ws_f4["A1"].font = FONT_TITLE
    ws_f4["A2"] = f"Dataset A: GoCom revA mixFYF 90m (n=3, {commit_gocom}) | Dataset B: SeungCom resource-v124 FIO-Fast 30m (n=3, {commit_res})"
    ws_f4["A2"].font = FONT_SUB

    ws_f4["A4"] = "Table 4A. GoCom mixFYF (90 min, n=3) — Non-Incumbent Exploration Share (%)"
    ws_f4["A4"].font = FONT_SEC
    for c, h in enumerate(["Policy", "n", "Explore_Share_Mean_Pct", "Explore_Share_SD", "Explore_Share_CI95", "Selections_Mean", "Selections_SD"], 1):
        ws_f4.cell(5, c, h)
    for idx, p in enumerate(exp_gocom_order, 6):
        sh = exp_gocom_share[p]
        sl = exp_gocom_sel[p]
        ws_f4.cell(idx, 1, p)
        ws_f4.cell(idx, 2, sh["n"])
        ws_f4.cell(idx, 3, sh["mean"])
        ws_f4.cell(idx, 4, sh["sd"])
        ws_f4.cell(idx, 5, sh["ci_half"])
        ws_f4.cell(idx, 6, sl["mean"])
        ws_f4.cell(idx, 7, sl["sd"])
    style_table(ws_f4, 5, 9, 1, 7, num_formats={2: "0", 3: "0.00", 4: "0.00", 5: "0.00", 6: "0.0", 7: "0.0"})

    ws_f4["A11"] = "Table 4B. SeungCom FIO-Fast (30 min, n=3) — Extra GC Copy Pages vs Fixed CAT-47 (%)"
    ws_f4["A11"].font = FONT_SEC
    for c, h in enumerate(["Policy", "n", "Extra_GC_Mean_Pct", "Extra_GC_SD", "Extra_GC_CI95", "Decisions_Mean", "Decisions_SD"], 1):
        ws_f4.cell(12, c, h)
    for idx, p in enumerate(exp_seung_order, 13):
        eg = exp_seung_extra_gc[p]
        dc = exp_seung_decisions[p]
        ws_f4.cell(idx, 1, p)
        ws_f4.cell(idx, 2, eg["n"])
        ws_f4.cell(idx, 3, eg["mean"])
        ws_f4.cell(idx, 4, eg["sd"])
        ws_f4.cell(idx, 5, eg["ci_half"])
        ws_f4.cell(idx, 6, dc["mean"])
        ws_f4.cell(idx, 7, dc["sd"])
    style_table(ws_f4, 12, 15, 1, 7, num_formats={2: "0", 3: "0.00", 4: "0.00", 5: "0.00", 6: "0.0", 7: "0.0"})

    ch4a = BarChart()
    ch4a.type = "col"
    ch4a.title = "Fig 4(a). GoCom mixFYF Exploration Share (%)"
    ch4a.y_axis.title = "%"
    ch4a.add_data(Reference(ws_f4, min_col=3, min_row=5, max_row=9), titles_from_data=True)
    ch4a.set_categories(Reference(ws_f4, min_col=1, min_row=6, max_row=9))
    ch4a.width = 14
    ch4a.height = 9
    ws_f4.add_chart(ch4a, "A17")

    ch4b = BarChart()
    ch4b.type = "col"
    ch4b.title = "Fig 4(b). SeungCom FIO-Fast Extra GC Copies (%)"
    ch4b.y_axis.title = "% vs CAT-47"
    ch4b.add_data(Reference(ws_f4, min_col=3, min_row=12, max_row=15), titles_from_data=True)
    ch4b.set_categories(Reference(ws_f4, min_col=1, min_row=13, max_row=15))
    ch4b.width = 14
    ch4b.height = 9
    ws_f4.add_chart(ch4b, "I17")
    autofit(ws_f4)

    # --- Sheet 9: Fig_05_Parameters ---
    ws_f5 = wb.create_sheet("Fig_05_Parameters")
    ws_f5["A1"] = "Figure 5: Parameter Sensitivity (E6) — COMPLETED (GoCom revC, n=3)"
    ws_f5["A1"].font = FONT_TITLE
    ws_f5["A2"] = f"STATUS: COMPLETED (GoCom revC 15/15 VALID; ELIM 10%/15%/25% all n=3; 15% default achieves lowest mean 2.1200)"
    ws_f5["A2"].font = FONT_OK
    ws_f5["A2"].fill = FILL_OK

    ws_f5["A4"] = "Table 5A. Live E6 Experiment (GoCom revC mixFYF, ELIM Threshold 10% / 15% / 25%, n=3)"
    ws_f5["A4"].font = FONT_SEC
    for c, h in enumerate(["Policy", "ELIM_Threshold_Pct", "Valid_n", "Planned_n", "Mean_WAF", "SD_WAF", "CI95_Half", "Welch_vs_15pct", "Status"], 1):
        ws_f5.cell(5, c, h)
    f5_live = [
        ("revC-elim10", 10, 3, 3, elim10_mean, elim10_st["sd"], elim10_st["ci_half"], f"{w_e10_v4['delta']:+.4f} [{w_e10_v4['ci_lo']:+.4f}, {w_e10_v4['ci_hi']:+.4f}]", "VALID (n=3, CI incl. 0)"),
        ("revC-v4 (Default)", 15, 3, 3, revC_v4_mean, revC_v4_st["sd"], revC_v4_st["ci_half"], "Baseline Control", "VALID (n=3, Lowest Mean)"),
        ("revC-elim25", 25, 3, 3, elim25_mean, elim25_st["sd"], elim25_st["ci_half"], f"{w_e25_v4['delta']:+.4f} [{w_e25_v4['ci_lo']:+.4f}, {w_e25_v4['ci_hi']:+.4f}]", "VALID (n=3, CI incl. 0)"),
    ]
    for r_i, row in enumerate(f5_live, 6):
        for c_i, v in enumerate(row, 1):
            ws_f5.cell(r_i, c_i, v)
    style_table(ws_f5, 5, 8, 1, 9, num_formats={2: "0", 3: "0", 4: "0", 5: "0.0000", 6: "0.0000", 7: "0.0000"})
    for r_i in [6, 7, 8]:
        ws_f5.cell(r_i, 9).fill = FILL_OK

    ws_f5["A10"] = "Table 5B. Preliminary Offline Replay Rationale (24 noelim/V2 Sweeps — NOT Live Device WAF)"
    ws_f5["A10"].font = FONT_SEC
    for c, h in enumerate(["Threshold_Pct", "Mean_Survivors_of_45", "Min_Survivors", "Ref_Arm_Survival_Pct", "Arm47_Survival_Pct"], 1):
        ws_f5.cell(11, c, h)
    for r_i, d in enumerate(replay_data, 12):
        ws_f5.cell(r_i, 1, d["threshold_pct"])
        ws_f5.cell(r_i, 2, d["mean_survivors"])
        ws_f5.cell(r_i, 3, d["min_survivors"])
        ws_f5.cell(r_i, 4, d["ref_survival_pct"])
        ws_f5.cell(r_i, 5, d["arm47_survival_pct"])
    style_table(ws_f5, 11, 16, 1, 5, num_formats={1: "0", 2: "0.00", 3: "0", 4: "0.0", 5: "0.0"})

    ch5 = BarChart()
    ch5.type = "col"
    ch5.title = "Fig 5(a). Live E6 Elimination Threshold Sensitivity (GoCom revC, n=3)"
    ch5.y_axis.title = "Mean Overall WAF"
    ch5.y_axis.scaling.min = 2.0
    ch5.y_axis.scaling.max = 2.25
    ch5.add_data(Reference(ws_f5, min_col=5, min_row=5, max_row=8), titles_from_data=True)
    ch5.set_categories(Reference(ws_f5, min_col=1, min_row=6, max_row=8))
    ch5.series[0].graphicalProperties.solidFill = "0072B2"
    ch5.width = 18
    ch5.height = 10
    ws_f5.add_chart(ch5, "A18")
    autofit(ws_f5)

    # --- Sheet 10: Fig_06_Candidates ---
    ws_f6 = wb.create_sheet("Fig_06_Candidates")
    ws_f6["A1"] = "Figure 6: Candidate Space Validity (E7: 60 -> 45 Arms, Excluding k=2) — COMPLETED"
    ws_f6["A1"].font = FONT_TITLE
    ws_f6["A2"] = f"60/60 Full Sweeps: VALID ({REF_MAIN} @ {commit_main}) | Live revC 60 vs 45 (n=3): COMPLETED ({REF_GOCOM} @ {commit_gocom})"
    ws_f6["A2"].font = FONT_OK
    ws_f6["A2"].fill = FILL_OK

    ws_f6["A4"] = "Table 6A. Verified Single-Workload 60/60 Full Sweeps (k=2 Excluded [15 arms] vs k>=4 Retained [45 arms])"
    ws_f6["A4"].font = FONT_SEC
    f6_h = ["Workload", "k2_n", "k2_Min_WAF", "k2_Median_WAF", "k2_Max_WAF", "k2_Best_Rank", "k4plus_n", "k4plus_Min_WAF", "k4plus_Median_WAF", "k4plus_Max_WAF", "k4plus_Best_Rank"]
    for c, h in enumerate(f6_h, 1):
        ws_f6.cell(5, c, h)
    for r_i, (wname, sw) in enumerate(sweeps.items(), 6):
        ws_f6.cell(r_i, 1, wname)
        ws_f6.cell(r_i, 2, sw["n_k2"])
        ws_f6.cell(r_i, 3, sw["k2_min"])
        ws_f6.cell(r_i, 4, sw["k2_median"])
        ws_f6.cell(r_i, 5, sw["k2_max"])
        ws_f6.cell(r_i, 6, sw["k2_best_rank"])
        ws_f6.cell(r_i, 7, sw["n_k4plus"])
        ws_f6.cell(r_i, 8, sw["k4_min"])
        ws_f6.cell(r_i, 9, sw["k4_median"])
        ws_f6.cell(r_i, 10, sw["k4_max"])
        ws_f6.cell(r_i, 11, sw["k4_best_rank"])
    style_table(ws_f6, 5, 8, 1, 11, num_formats={2: "0", 3: "0.0000", 4: "0.0000", 5: "0.0000", 6: "0", 7: "0", 8: "0.0000", 9: "0.0000", 10: "0.0000", 11: "0"})

    ws_f6["A10"] = "Table 6B. Live E7 Comparison (60 vs 45 Arms on GoCom mixFYF, n=3) — COMPLETED"
    ws_f6["A10"].font = FONT_SEC
    for c, h in enumerate(["Condition", "Arms", "Valid_n", "Planned_n", "Mean_WAF", "SD_WAF", "CI95_Half", "Welch_60_minus_45", "Status"], 1):
        ws_f6.cell(11, c, h)
    f6_live = [
        ("revB-arm60 (Pilot)", 60, 1, 1, arm60_n1_waf, "N/A (n=1)", "N/A (n=1)", "N/A (Pilot)", "Pilot only (n=1, no CI)"),
        ("revC revB-arm60", 60, 3, 3, revC_arm60_mean, revC_arm60_st["sd"], revC_arm60_st["ci_half"], f"{w_arm60_v4['delta']:+.4f} [{w_arm60_v4['ci_lo']:+.4f}, {w_arm60_v4['ci_hi']:+.4f}]", "VALID (n=3, CI incl. 0)"),
        ("revC revC-v4 (Control)", 45, 3, 3, revC_v4_mean, revC_v4_st["sd"], revC_v4_st["ci_half"], "Baseline Control", "VALID (n=3, 45-arm default)"),
    ]
    for r_i, row in enumerate(f6_live, 12):
        for c_i, v in enumerate(row, 1):
            ws_f6.cell(r_i, c_i, v)
    style_table(ws_f6, 11, 14, 1, 9, num_formats={2: "0", 3: "0", 4: "0", 5: "0.0000", 6: "0.0000", 7: "0.0000"})
    ws_f6.cell(13, 9).fill = FILL_OK
    ws_f6.cell(14, 9).fill = FILL_OK

    ch6 = BarChart()
    ch6.type = "col"
    ch6.grouping = "clustered"
    ch6.title = "Fig 6(a). 60/60 Sweep Median WAF: Excluded k=2 vs Retained k>=4"
    ch6.y_axis.title = "Median WAF"
    ch6.add_data(Reference(ws_f6, min_col=4, min_row=5, max_row=8), titles_from_data=True)
    ch6.add_data(Reference(ws_f6, min_col=9, min_row=5, max_row=8), titles_from_data=True)
    ch6.set_categories(Reference(ws_f6, min_col=1, min_row=6, max_row=8))
    ch6.series[0].graphicalProperties.solidFill = "D55E00"
    ch6.series[1].graphicalProperties.solidFill = "0072B2"
    ch6.width = 18
    ch6.height = 10
    ws_f6.add_chart(ch6, "A16")
    autofit(ws_f6)

    # --- Sheet 11: Fig_07_Resources ---
    ws_f7 = wb.create_sheet("Fig_07_Resources")
    ws_f7["A1"] = "Figure 7: Policy-Level (iCAT) vs. Block-Level (SmartGC) Resource Overhead (E5 / M5)"
    ws_f7["A1"].font = FONT_TITLE
    ws_f7["A2"] = f"Memory: gdb sizeof (4 partitions) | CPU: GoCom revA ({commit_gocom}) & SeungCom resource-v124 ({commit_res}); SmartGC CPU = NA"
    ws_f7["A2"].font = FONT_SUB

    ws_f7["A4"] = "Table 7A. Kernel Memory Footprint (4 FTL Partitions, Verified via gdb sizeof)"
    ws_f7["A4"].font = FONT_SEC
    for c, h in enumerate(["Policy_Scope", "Bytes_4Part", "KiB_4Part", "Ratio_vs_iCAT_LearningOnly", "Notes"], 1):
        ws_f7.cell(5, c, h)
    mem_rows = [
        ("iCAT-v4 (Learning-only)", mem_data["iCAT_v4_learning_only_B"], "=B6/1024", "=B6/$B$6", "Excludes 512 B shared CAT param cache"),
        ("iCAT-v4 (Total tuner struct)", mem_data["iCAT_v4_total_struct_B"], "=B7/1024", "=B7/$B$6", "Includes 512 B shared CAT param cache"),
        ("SmartGC (Learning-only)", mem_data["SmartGC_learning_only_B"], "=B8/1024", "=B8/$B$6", "Q-table (640KB) + cand/sort arrays (1.31MB) + state"),
        ("SmartGC (Learning + GC Buffer)", mem_data["SmartGC_total_B"], "=B9/1024", "=B9/$B$6", "Adds 393,216 B GC buffer (drain + bitmap)"),
    ]
    for r_i, row in enumerate(mem_rows, 6):
        for c_i, v in enumerate(row, 1):
            ws_f7.cell(r_i, c_i, v)
    style_table(ws_f7, 5, 9, 1, 5, num_formats={2: "#,##0", 3: "#,##0.00", 4: "0.0"})

    ws_f7["A11"] = "Table 7B. Learner Decision CPU Overhead — GoCom mixFYF (90 min, n=3)"
    ws_f7["A11"].font = FONT_SEC
    for c, h in enumerate(["Policy", "n", "Total_CPU_ms", "SD_ms", "CI95_Half_ms", "Mean_us_per_Call", "Calls_Mean", "Share_of_Wall_Pct"], 1):
        ws_f7.cell(12, c, h)
    for r_i, p in enumerate(["revA-random", "revA-v1", "revA-v4", "revA-v2"], 13):
        c_tot = cpu_gocom[p]["total_ms"]
        c_us = cpu_gocom[p]["mean_us"]
        c_cl = cpu_gocom[p]["calls"]
        ws_f7.cell(r_i, 1, p)
        ws_f7.cell(r_i, 2, c_tot["n"])
        ws_f7.cell(r_i, 3, c_tot["mean"])
        ws_f7.cell(r_i, 4, c_tot["sd"])
        ws_f7.cell(r_i, 5, c_tot["ci_half"])
        ws_f7.cell(r_i, 6, c_us["mean"])
        ws_f7.cell(r_i, 7, c_cl["mean"])
        ws_f7.cell(r_i, 8, c_tot["mean"] / (5404.0 * 1000.0) * 100.0)
    ws_f7.cell(17, 1, "SmartGC (CPU)")
    ws_f7.cell(17, 2, 0)
    for cc in range(3, 9):
        ws_f7.cell(17, cc, "Unmeasured (NA)")
    style_table(ws_f7, 12, 17, 1, 8, num_formats={2: "0", 3: "0.0000", 4: "0.0000", 5: "0.0000", 6: "0.00", 7: "0.0", 8: "0.00000"})

    ws_f7["A19"] = "Table 7C. Learner Algorithm & Net GC-Hook CPU — SeungCom FIO-Fast (30 min, n=3)"
    ws_f7["A19"].font = FONT_SEC
    for c, h in enumerate(["Policy", "n", "Alg_CPU_ms", "Alg_CI95_ms", "Net_Hook_ns_per_GC", "Net_Hook_CI95_ns"], 1):
        ws_f7.cell(20, c, h)
    for r_i, p in enumerate(["iCAT v1", "iCAT v2", "iCAT v4"], 21):
        ws_f7.cell(r_i, 1, p)
        ws_f7.cell(r_i, 2, cpu_seung[p]["alg_ms"]["n"])
        ws_f7.cell(r_i, 3, cpu_seung[p]["alg_ms"]["mean"])
        ws_f7.cell(r_i, 4, cpu_seung[p]["alg_ms"]["ci_half"])
        ws_f7.cell(r_i, 5, cpu_seung[p]["net_hook_ns_per_gc"]["mean"])
        ws_f7.cell(r_i, 6, cpu_seung[p]["net_hook_ns_per_gc"]["ci_half"])
    style_table(ws_f7, 20, 23, 1, 6, num_formats={2: "0", 3: "0.000", 4: "0.000", 5: "0.00", 6: "0.00"})

    ws_f7["A25"] = "Table 7D. Separated Learner Sub-Path & Emulator GC Time — SeungCom FIO-Fast (30 min, n=3; resource-v124)"
    ws_f7["A25"].font = FONT_SEC
    for c, h in enumerate(["Policy", "Reward_Update_ms", "Policy_Select_ms", "set_arm_ms", "printk_ms", "on_gc_Net_ns", "Emulator_do_gc_s"], 1):
        ws_f7.cell(26, c, h)
    for r_i, p in enumerate(["Fixed CAT-47", "iCAT v1", "iCAT v2", "iCAT v4"], 27):
        s7 = verified_plot_data["fig07_resources"]["cpu_seungcom_fiofast_30m_separated"][p]
        ws_f7.cell(r_i, 1, p)
        ws_f7.cell(r_i, 2, s7["reward_update_ms"])
        ws_f7.cell(r_i, 3, s7["policy_choose_ms"])
        ws_f7.cell(r_i, 4, s7["set_arm_ms"])
        ws_f7.cell(r_i, 5, s7["printk_ms"])
        ws_f7.cell(r_i, 6, s7["on_gc_net_ns"])
        ws_f7.cell(r_i, 7, s7["do_gc_minus_ongc_ms"] / 1000.0)
    style_table(ws_f7, 26, 30, 1, 7, num_formats={2: "0.000", 3: "0.000", 4: "0.000", 5: "0.000", 6: "0.00", 7: "0.00"})

    ws_f7["A32"] = "Table 7E. M1 Same-Environment SmartGC-EQ8 vs. iCAT-v4 Comparison — GoCom mixY 10h (n=1 per policy, NO STAT; ktime elapsed != CPU)"
    ws_f7["A32"].font = FONT_SEC
    m1_headers = ["Metric_Category", "Metric", "iCAT_v4_n1", "SmartGC_EQ8_n1", "Diff_or_Ratio", "Unit", "Measurement_Type_and_Caveat"]
    for c, h in enumerate(m1_headers, 1):
        ws_f7.cell(33, c, h)
    m1_rows = [
        ("WAF (Host Write)", "1 + gc_pages/host_pages", 3.330464, 4.561785, "-26.99% (iCAT lower)", "ratio", "[MEASURED, n=1] Host-write WAF (differs from WAF_nand on SmartGC)"),
        ("WAF (NAND Write)", "WAF_nand (excl. DRAM buf absorb)", 3.330464, 4.553194, "-26.85% (iCAT lower)", "ratio", "[MEASURED, n=1] Matches Paper Table 9b (3.330 vs 4.553)"),
        ("Host Written (10h)", "Total Host Write Volume", 8.285, 5.970, "+38.78%", "TB", "[MEASURED, n=1] FIO miss jobs: iCAT 0, SmartGC 2"),
        ("Memory (Measured kB)", "VmallocUsed delta (load1s - pre)", 34848.0, 37752.0, "+2,904.0 kB", "kB", "[MEASURED, n=1] /proc/meminfo median; post unload +16 kB; VmRSS N/A (kthread)"),
        ("Memory (Measured Bytes)", "VmallocUsed delta (load1s - pre)", 35684352, 38658048, "+2,973,696 B", "bytes", "[MEASURED, n=1] Exact kB x 1024 (fixes GoCom databook v2 F6 kB/bytes label)"),
        ("Memory (Calculated)", "conv_ftl.c vmalloc total", 34315.6, 37373.2, "+3,057.6 KiB", "KiB", "[CALCULATED] Within 5% of measured +2,904 kB (incl. learner+buf+line struct)"),
        ("GC Total Elapsed", "do_gc ktime per GC (105M vs 104M)", 98.37, 17.84, "5.51x LONGER on iCAT", "us/GC", "[MEASURED ktime, n=1] UNFAVORABLE: CAT full-line scan (1,342 vs 333 ms/GiB)"),
        ("Victim Selection", "SELECT ktime per GC (4-part sum)", 87.05, 1.00, "9,162 s vs 104 s", "us/GC", "[MEASURED ktime, n=1] 88.5% of iCAT GC; SmartGC pure select excl. step = 56.3 s"),
        ("Learning Overhead", "LEARN ktime total (4-part sum)", 4.295, 47.556, "11.1x SMALLER on iCAT", "s (10h)", "[MEASURED ktime, n=1] iCAT 40.8 ns/GC (0.041% GC) vs SmartGC 975.5 us x 48,751"),
        ("Reward / GC Buffer", "REWARD + BUF write-path upper", 0.0, 482.28, "SmartGC-only", "s (10h)", "[MEASURED ktime, n=1] REWARD 9.17 s + BUF upper 473.1 s (incl. timer overhead)"),
        ("Channel Warnings", "chmodel_warn_lines (kernel.log)", 0, 22069, "SmartGC saturated", "lines", "[MEASURED, n=1] Latency excluded due to SmartGC channel warnings & erase=0"),
        ("Kernel CPU / Common", "perf CPU time & NVMeVirt common", "UNMEASURED", "UNMEASURED", "N/A", "N/A", "[UNMEASURED] Busy-poll 100% CPU & no perf; ktime elapsed != CPU time"),
    ]
    for r_i, row in enumerate(m1_rows, 34):
        for c_i, v in enumerate(row, 1):
            ws_f7.cell(r_i, c_i, v)
    style_table(ws_f7, 33, 33 + len(m1_rows), 1, 7)

    ch7 = BarChart()
    ch7.type = "col"
    ch7.title = "Fig 7(b). Learner Decision CPU (GoCom mixFYF 90m, ms)"
    ch7.y_axis.title = "CPU Time (ms)"
    ch7.add_data(Reference(ws_f7, min_col=3, min_row=12, max_row=16), titles_from_data=True)
    ch7.set_categories(Reference(ws_f7, min_col=1, min_row=13, max_row=16))
    ch7.series[0].graphicalProperties.solidFill = "0072B2"
    ch7.width = 16
    ch7.height = 9
    ws_f7.add_chart(ch7, "J4")

    ch7m = BarChart()
    ch7m.type = "col"
    ch7m.title = "Fig 7(a). Memory Footprint (KiB, 4 Partitions)"
    ch7m.y_axis.title = "KiB"
    ch7m.add_data(Reference(ws_f7, min_col=3, min_row=5, max_row=9), titles_from_data=True)
    ch7m.set_categories(Reference(ws_f7, min_col=1, min_row=6, max_row=9))
    ch7m.series[0].graphicalProperties.solidFill = "B2182B"
    ch7m.width = 16
    ch7m.height = 9
    ws_f7.add_chart(ch7m, "J15")
    autofit(ws_f7)

    # --- Sheet 12: Table_Data ---
    ws_tbl = wb.create_sheet("Table_Data")
    ws_tbl["A1"] = "Publication-Ready Summary Table Data (All Claims Traceable to Verified Raw Runs)"
    ws_tbl["A1"].font = FONT_TITLE
    td_headers = ["Paper_Claim", "Comparison", "Host_Workload", "n", "Metric", "Control_Mean", "Target_Mean", "Delta_or_Ratio", "CI95_Range", "Validity_Status", "Evidence_Sheet"]
    td_rows = [
        ["Claim 1 (vs Random)", "Random vs iCAT-v4", "GoCom mixFYF 90m", "3 vs 3", "Overall WAF", f1_overall["revA-v4"]["mean"], f1_overall["revA-random"]["mean"], f"+{f1_welch_total['delta']:.4f} (-{f1_pct_impr:.2f}%)", f"[{f1_welch_total['ci_lo']:+.4f}, {f1_welch_total['ci_hi']:+.4f}]", "VALID (Proven on mixFYF)", "Fig_01_Random"],
        ["Claim 2 (Elimination)", "revE NoElim (isol.) vs revE-v4", "GoCom revE mixFYF 90m", "3 vs 3", "Overall / Phase C WAF", f2_revE_tot["revE-v4"]["mean"], f2_revE_tot["revE-noelim"]["mean"], f"+{f2_revE_welch_tot['revE-noelim']['delta']:.4f} (PhC +{f2_revE_welch_phC['revE-noelim']['delta']:.4f})", f"[{f2_revE_welch_tot['revE-noelim']['ci_lo']:+.4f}, {f2_revE_welch_tot['revE-noelim']['ci_hi']:+.4f}]", "VALID (Same-batch CI>0, Paired>0; Holm p=0.091)", "NoElim"],
        ["Claim 2 (Drift Thr)", "revE drift12 (12.5%) vs revE-v4", "GoCom revE mixFYF 90m", "3 vs 3", "Overall / Phase C WAF", f2_revE_tot["revE-v4"]["mean"], f2_revE_tot["revE-drift12"]["mean"], f"+{f2_revE_welch_tot['revE-drift12']['delta']:.4f} (PhC +{f2_revE_welch_phC['revE-drift12']['delta']:.4f})", f"[{f2_revE_welch_tot['revE-drift12']['ci_lo']:+.4f}, {f2_revE_welch_tot['revE-drift12']['ci_hi']:+.4f}]", "VALID (Same-batch CI>0, premature PhB resets; Holm p=0.091)", "Ablation"],
        ["Claim 2 (Bundle Off)", "abl OffBundle vs abl-v4", "SeungCom abl mixFYF 90m", "3 vs 3", "Overall / Phase C WAF", f2_abl_tot["abl-v4"]["mean"], f2_abl_tot["abl-bundle-off"]["mean"], f"+{f2_abl_welch_tot['abl-bundle-off']['delta']:.4f} (PhC +{f2_abl_welch_phC['abl-bundle-off']['delta']:.4f})", f"[{f2_abl_welch_tot['abl-bundle-off']['ci_lo']:+.4f}, {f2_abl_welch_tot['abl-bundle-off']['ci_hi']:+.4f}]", "VALID (Same-batch CI>0, Holm p=0.028)", "Ablation"],
        ["Claim 2 (Discount γ)", "abl NoDiscount (γ=1.0) vs abl-v4", "SeungCom abl mixFYF 90m", "3 vs 3", "Overall WAF", f2_abl_tot["abl-v4"]["mean"], f2_abl_tot["abl-nodiscount"]["mean"], f"{f2_abl_welch_tot['abl-nodiscount']['delta']:+.4f}", f"[{f2_abl_welch_tot['abl-nodiscount']['ci_lo']:+.4f}, {f2_abl_welch_tot['abl-nodiscount']['ci_hi']:+.4f}]", "VALID NULL (No difference found; matches γ^250=0.882)", "Discount-free"],
        ["Claim 1 (vs Greedy)", "Online Greedy (VAR=8) - revD-v4", "SeungCom mixFYF 90m (indirect)", "3 vs 3", "Overall / Phase C WAF", f2_revD_tot["revD-v4"]["mean"], f2_greedy_tot["mean"], f"{f2_greedy_vs_revD_tot['delta']:+.4f} (PhC {f2_greedy_vs_revD_phC['delta']:+.4f})", f"[{f2_greedy_vs_revD_tot['ci_lo']:+.4f}, {f2_greedy_vs_revD_tot['ci_hi']:+.4f}]", "VALID NULL (Indirect diff batch; 0/2513 rule mismatches)", "Online Greedy"],
        ["Claim 1 (vs Greedy GC)", "Greedy GC - bg-v4 (batchG)", "SeungCom mixFYF 90m (same batch)", "3 vs 3", "Overall / Phase C WAF", calc_summary([r["waf_total"] for r in by_pol["batchG-v4"]])["mean"], calc_summary([r["waf_total"] for r in by_pol["batchG-greedygc"]])["mean"], "+0.5189 (-19.7%, PhC +0.7078)", "[+0.4633, +0.5744]", "VALID PASS (Holm p=0.0013; note Greedy FIO lat lower)", "Greedy GC"],
        ["Claim 2 (Drift 50%)", "drift50 - bg-v4 (batchG)", "SeungCom mixFYF 90m (same batch)", "3 vs 3", "Overall / Phase C WAF", calc_summary([r["waf_total"] for r in by_pol["batchG-v4"]])["mean"], calc_summary([r["waf_total"] for r in by_pol["batchG-drift50"]])["mean"], "+0.0183 (PhC +0.0418)", "[-0.0445, +0.0812]", "VALID (No diff found; Holm p=0.831; 11/11 resets >50%)", "Fig_05_Parameters"],
        ["Claim 2 (Elim+Settle)", "V2 vs iCAT-v4", "GoCom mixFYF 90m", "3 vs 3", "Overall WAF", f2_stats["revA-v4"]["mean"], f2_stats["revA-v2"]["mean"], f"+{f2_welch['revA-v2']['delta']:.4f}", f"[{f2_welch['revA-v2']['ci_lo']:+.4f}, {f2_welch['revA-v2']['ci_hi']:+.4f}]", "VALID (Same-batch)", "Fig_02_Ablation"],
        ["Claim 2 (Partial Reset)", "revD FullReset vs revD-v4", "SeungCom mixFYF 90m", "3 vs 3", "Overall / Phase C WAF", f2_revD_tot["revD-v4"]["mean"], f2_revD_tot["revD-fullreset"]["mean"], f"+{f2_revD_welch_tot['revD-fullreset']['delta']:.4f} (PhC +{f2_revD_welch_phC['revD-fullreset']['delta']:.4f})", f"[{f2_revD_welch_tot['revD-fullreset']['ci_lo']:+.4f}, {f2_revD_welch_tot['revD-fullreset']['ci_hi']:+.4f}]", "VALID (Same-batch, CI > 0)", "Fig_02_Ablation"],
        ["Claim 2 (Drift Detect)", "revD NoDrift vs revD-v4", "SeungCom mixFYF 90m", "3 vs 3", "Overall / Phase C WAF", f2_revD_tot["revD-v4"]["mean"], f2_revD_tot["revD-nodrift"]["mean"], f"+{f2_revD_welch_tot['revD-nodrift']['delta']:.4f} (PhC +{f2_revD_welch_phC['revD-nodrift']['delta']:.4f})", f"[{f2_revD_welch_tot['revD-nodrift']['ci_lo']:+.4f}, {f2_revD_welch_tot['revD-nodrift']['ci_hi']:+.4f}]", "INCONCLUSIVE (3/3 worse, CI incl. 0)", "Fig_02_Ablation"],
        ["Claim 2 (Adaptation)", "iCAT-v4 Phase C Reset", "GoCom mixFYF 90m", "3", "First Reset (s)", "N/A", v4_reset_stats["mean"], f"{v4_reset_stats['mean']:.1f} s", f"[{v4_reset_stats['ci_lo']:.1f}, {v4_reset_stats['ci_hi']:.1f}] s", "VALID (3/3 detected)", "Fig_03_Adaptation"],
        ["Claim 2 (Exploration)", "Random / V2 vs iCAT-v4", "GoCom mixFYF 90m", "3 vs 3", "Explore Share (%)", exp_gocom_share["revA-v4"]["mean"], exp_gocom_share["revA-random"]["mean"], f"-{exp_gocom_share['revA-random']['mean']-exp_gocom_share['revA-v4']['mean']:.1f} pp", "CI non-overlapping", "VALID", "Fig_04_Exploration"],
        ["Claim 1 (vs Orig iCAT)", "Original iCAT vs iCAT-v4", "GoCom revC mixFYF 90m", "3 vs 3", "Overall WAF", revC_v4_mean, revC_online_st["mean"], f"+{revC_online_welch['delta']:.4f} (-11.49%)", f"[{revC_online_welch['ci_lo']:+.4f}, {revC_online_welch['ci_hi']:+.4f}]", "VALID (Same-batch CI > 0, g=10.53)", "Fig_05_Parameters"],
        ["Claim 2 (Parameters)", "ELIM 10% / 15% / 25%", "GoCom revC mixFYF", "3 / 3 / 3 (9/9)", "Overall WAF", revC_v4_mean, elim10_mean, f"10% {w_e10_v4['delta']:+.4f}; 25% {w_e25_v4['delta']:+.4f}", f"10% [{w_e10_v4['ci_lo']:+.3f},{w_e10_v4['ci_hi']:+.3f}]; 25% [{w_e25_v4['ci_lo']:+.3f},{w_e25_v4['ci_hi']:+.3f}]", "VALID (Completed; CI incl. 0, 15% lowest)", "Fig_05_Parameters"],
        ["Claim 2 (Candidates)", "60 vs 45 arms (excl. k=2)", "SeungCom 3x60 / GoCom revC", "180 / 3 vs 3", "Sweep Rank / mixFYF WAF", revC_v4_mean, revC_arm60_mean, f"+{w_arm60_v4['delta']:.4f} (60 vs 45)", f"[{w_arm60_v4['ci_lo']:+.4f}, {w_arm60_v4['ci_hi']:+.4f}]", "VALID (Completed; CI incl. 0)", "Fig_06_Candidates"],
        ["Claim 3 (Memory)", "SmartGC vs iCAT-v4", "4 FTL Partitions (sizeof + m1)", "Exact / n=1", "Struct / VmallocUsed", 10112, 1951648, "193.0x (m1 Vmalloc +2,904 kB)", "Exact sizeof / n=1 measured", "VALID (n=1 Vmalloc)", "Fig_07_Resources"],
        ["Claim 3 (GC & Learn)", "m1-20261126 SmartGC-EQ8 vs V4", "GoCom mixY 10h (same batch)", "1 vs 1", "WAF_nand / GC / LEARN", 3.3305, 4.5532, "WAF -26.9%; GC 5.5x LONGER; LEARN 11x smaller", "NO CI (n=1; ktime != CPU)", "VALID SINGLE-RUN (Trade-off)", "Fig_07_Resources"],
        ["Claim 3 (CPU)", "iCAT-v4 Decision CPU", "GoCom mixFYF 90m", "3", "Total ktime (ms)", 0.0, cpu_gocom["revA-v4"]["total_ms"]["mean"], "<0.0002% wall", f"[{cpu_gocom['revA-v4']['total_ms']['ci_lo']:.2f}, {cpu_gocom['revA-v4']['total_ms']['ci_hi']:.2f}] ms", "VALID (ktime elapsed)", "Fig_07_Resources"],
    ]
    for c, h in enumerate(td_headers, 1):
        ws_tbl.cell(3, c, h)
    for r_i, row in enumerate(td_rows, 4):
        for c_i, v in enumerate(row, 1):
            ws_tbl.cell(r_i, c_i, v)
    style_table(ws_tbl, 3, 3 + len(td_rows), 1, len(td_headers), num_formats={6: "0.0000", 7: "0.0000"})
    autofit(ws_tbl)

    xlsx_path = OUT_DIR / "iCAT_Paper_Figures.xlsx"
    wb.save(xlsx_path)
    print(f"Saved Excel workbook: {xlsx_path}")

    # =========================================================================
    # WRITE figure_manifest.csv
    # =========================================================================
    manifest_rows = [
        {
            "figure_id": "figure01_random",
            "title": "Online Policy Learning (iCAT-v4) vs Random Selection",
            "sheet_name": "Fig_01_Random",
            "status": "READY (COMPLETED: revA Random & revC Original iCAT n=3 PASS)",
            "png_path": f1_paths["png"],
            "pdf_path": f1_paths["pdf"],
            "svg_path": f1_paths["svg"],
            "experiment_id": "E2 / revA-20261114 + revC-20261124",
            "host_and_workload": "GoCom Ryzen 3600XT / mixFYF (FIO-Fast 1800s -> YCSB-A 250k 1800s -> FIO-Fast 1800s)",
            "git_branch": REF_GOCOM,
            "git_commit": commit_gocom,
            "raw_data_paths": "result/revA-20261114/raw/mixFYF-revA-{random,v4}-rep{1,2,3}; mixFYF-arm47-rep1",
            "analysis_script": "report/paper-figures/build_paper_figures.py",
            "data_validity": "VALID (6/6 main + 1/1 ref passed all raw checks: SHA256, exit=0, FIO=0, YCSB=0% fail, SQLITE_FULL=0, 2-path WAF match)",
            "n_reps": "n=3 (Random, iCAT-v4); n=1 (CAT-47 ref, no CI)",
            "stat_method": "Mean +/- 95% Student-t CI (df=2); Welch 95% CI for difference",
            "notes": "Single workload & host; GoCom revC Original iCAT (+0.2751, g=10.53) & SeungCom Online Greedy (-0.0086, null) completed",
        },
        {
            "figure_id": "figure02_ablation",
            "title": "Component Ablation Study (Elimination, Settlement, Drift)",
            "sheet_name": "Fig_02_Ablation",
            "status": "READY (GoCom revA/revB n=3 & SeungCom revD 9/9 COMPLETED; host-separated)",
            "png_path": f2_paths["png"],
            "pdf_path": f2_paths["pdf"],
            "svg_path": f2_paths["svg"],
            "experiment_id": "E1 / revA-20261114 + revB-20261122 (GoCom) & revD-20261124 (SeungCom)",
            "host_and_workload": "GoCom Ryzen 3600XT & SeungCom i7-7700 / mixFYF 250k (1800s x3, hosts not pooled)",
            "git_branch": f"{REF_GOCOM}; {REF_MAIN}",
            "git_commit": f"{commit_gocom}; {commit_main}",
            "raw_data_paths": "result/revA-20261114/raw/mixFYF-revA-{v4,v1,v2}-rep{1..3}; result/revB-20261122/raw/mixFYF-revB-{noelim,nosettle}-rep{1..3}; result/revD-20261124/raw/mixFYF-revD-{v4,nodrift,fullreset}-rep{1..3}",
            "analysis_script": "report/paper-figures/build_paper_figures.py",
            "data_validity": "VALID (16/16 GoCom + 9/9 SeungCom revD passed all raw checks); cross-batch revB caveat marked",
            "n_reps": "n=3 per ablation variant on both GoCom and SeungCom revD (9/9 complete)",
            "stat_method": "Mean +/- 95% Student-t CI (df=2); same-host Welch 95% CI vs control v4",
            "notes": "SeungCom revD: FullReset vs v4 CI>0 (Tot +0.0596, PhC +0.1296); NoDrift vs v4 3/3 worse (+0.0681) but CI includes 0",
        },
        {
            "figure_id": "figure03_adaptation",
            "title": "Workload Transition & Adaptation Trajectory",
            "sheet_name": "Fig_03_Adaptation",
            "status": "READY (Valid GoCom revA n=3; Sep/Nov mixR INVALID excluded; SeungCom revD 9/9 completed)",
            "png_path": f3_paths["png"],
            "pdf_path": f3_paths["pdf"],
            "svg_path": f3_paths["svg"],
            "experiment_id": "E3 / revA-20261114 (+ revD-20261124 COMPLETED)",
            "host_and_workload": "GoCom Ryzen 3600XT / mixFYF 250k (0–90 min)",
            "git_branch": REF_GOCOM,
            "git_commit": commit_gocom,
            "raw_data_paths": "result/revA-20261114/raw/mixFYF-revA-{v4,v1,random}-rep{1..3}/control-series.txt; mixFYF-arm47-rep1/control-series.txt; results/workload_transition.csv",
            "analysis_script": "report/paper-figures/build_paper_figures.py",
            "data_validity": "VALID (10/10 runs passed); all SQLITE_FULL mixR runs strictly excluded",
            "n_reps": "n=3 (v4, v1, random); n=1 (CAT-47 ref)",
            "stat_method": "5-min rolling WAF binned every 2 min (mean +/- SD band); Phase C first reset t-CI (df=2)",
            "notes": "Phase C drift reset detected in 3/3 iCAT-v4 runs at 61.7–65.5 s",
        },
        {
            "figure_id": "figure04_exploration",
            "title": "Cumulative Exploration Overhead",
            "sheet_name": "Fig_04_Exploration",
            "status": "READY (Separated by Host & Workload)",
            "png_path": f4_paths["png"],
            "pdf_path": f4_paths["pdf"],
            "svg_path": f4_paths["svg"],
            "experiment_id": "E3 / revA-20261114 (GoCom) & resource-v124-20261114 (SeungCom)",
            "host_and_workload": "Panel(a): GoCom mixFYF 90m | Panel(b): SeungCom FIO-Fast 30m (NOT mixed)",
            "git_branch": f"{REF_GOCOM}; {REF_RES}",
            "git_commit": f"{commit_gocom}; {commit_res}",
            "raw_data_paths": "result/revA-20261114/results/exploration_cost.csv; result/resource-v124-20261114/report/resource_raw.csv",
            "analysis_script": "report/paper-figures/build_paper_figures.py",
            "data_validity": "VALID (12/12 GoCom + 12/12 SeungCom runs); invalid mixR/mixA exploration rows excluded",
            "n_reps": "n=3 per policy in both panels",
            "stat_method": "Mean +/- 95% Student-t CI (df=2)",
            "notes": "Panels strictly separated by host and workload",
        },
        {
            "figure_id": "figure05_parameters",
            "title": "Parameter Sensitivity (Elimination Threshold 10% / 15% / 25%)",
            "sheet_name": "Fig_05_Parameters",
            "status": "READY (COMPLETED: GoCom revC 9/9 ELIM runs n=3 VALID)",
            "png_path": f5_paths["png"],
            "pdf_path": f5_paths["pdf"],
            "svg_path": f5_paths["svg"],
            "experiment_id": "E6 / revC-20261124 (live n=3) + revision-gocom-20261123 (offline replay)",
            "host_and_workload": "GoCom Ryzen 3600XT / mixFYF 250k (live n=3) + 24 noelim/V2 sweeps (offline replay)",
            "git_branch": REF_GOCOM,
            "git_commit": commit_gocom,
            "raw_data_paths": "result/revC-20261124/raw/mixFYF-revC-{elim10,v4,elim25}-rep{1,2,3}; result/revision-gocom-20261123/elim_replay_summary.csv",
            "analysis_script": "report/paper-figures/build_paper_figures.py",
            "data_validity": "Live: 9/9 VALID (all 3 thresholds n=3); Offline replay: VALID preliminary rationale",
            "n_reps": "Live: n=3 each (10%, 15% v4, 25%); Replay: 24 partition sweeps",
            "stat_method": "Mean +/- 95% Student-t CI (df=2); Welch 95% CI vs 15% default",
            "notes": "15% default achieves lowest mean (2.1200); both 10% (+0.0238) and 25% (+0.0507) Welch CIs include 0",
        },
        {
            "figure_id": "figure06_candidates",
            "title": "Candidate Space Reduction (60 -> 45 Arms, Excluding k=2)",
            "sheet_name": "Fig_06_Candidates",
            "status": "READY (COMPLETED: 3x60 Sweeps VALID + Live revC 60 vs 45 n=3 VALID)",
            "png_path": f6_paths["png"],
            "pdf_path": f6_paths["pdf"],
            "svg_path": f6_paths["svg"],
            "experiment_id": "E7 / sweep-20260915 + revB-20261122 + revC-20261124 (COMPLETED)",
            "host_and_workload": "Panel(a): SeungCom 3x60 single-workload sweeps | Panel(b): GoCom mixFYF 250k (n=3)",
            "git_branch": f"{REF_MAIN}; {REF_GOCOM}",
            "git_commit": f"{commit_main}; {commit_gocom}",
            "raw_data_paths": "result/sweep-20260915/rank-{test4,oltp,sqlite-a}.txt; result/revB-20261122/raw/mixFYF-revB-arm60-rep1; result/revC-20261124/raw/mixFYF-{revB-arm60,revC-v4}-rep{1,2,3}",
            "analysis_script": "report/paper-figures/build_paper_figures.py",
            "data_validity": "Sweeps: VALID (180/180 runs, sqlite 87/87 0% fail); Live E7: 6/6 VALID (revC arm60 n=3 vs revC-v4 n=3)",
            "n_reps": "Sweeps: 15 k=2 vs 45 k>=4 per workload; Live revC: 60-arm n=3 vs 45-arm n=3",
            "stat_method": "Median & min–max range (sweeps); Mean +/- 95% t-CI & Welch 95% CI (live revC)",
            "notes": "Live 60 vs 45: Delta = +0.0282 [-0.0324, +0.0888] (CI includes 0; pruning k=2 never hurts WAF while removing 15 dominated arms)",
        },
        {
            "figure_id": "figure07_resources",
            "title": "Policy-Level (iCAT) vs Block-Level (SmartGC) Resource Overhead",
            "sheet_name": "Fig_07_Resources",
            "status": "READY (PARTIAL: SmartGC CPU Unmeasured/NA)",
            "png_path": f7_paths["png"],
            "pdf_path": f7_paths["pdf"],
            "svg_path": f7_paths["svg"],
            "experiment_id": "E5 / revA-20261114 + resource-v124-20261114 + smartgc-20261119 sizeof",
            "host_and_workload": "Memory: gdb sizeof (4 partitions) | CPU: GoCom mixFYF 90m (n=3) & SeungCom FIO-Fast 30m (n=3)",
            "git_branch": f"{REF_GOCOM}; {REF_RES}",
            "git_commit": f"{commit_gocom}; {commit_res}",
            "raw_data_paths": "result/revA-20261114/results/resource/cpu_measurements.csv; result/resource-v124-20261114/report/{cpu_measurements,data_structure_sizes}.csv; report/revision-20261123-gocom/resource_overhead_final.md",
            "analysis_script": "report/paper-figures/build_paper_figures.py",
            "data_validity": "VALID (all CPU n=3 & exact gdb sizeof verified); SmartGC CPU explicitly marked Unmeasured (NA)",
            "n_reps": "Memory: exact sizeof; CPU: n=3 per policy (SmartGC CPU n=0/NA)",
            "stat_method": "Exact struct byte count ratio; Mean +/- 95% Student-t CI (df=2) for CPU",
            "notes": "Learning-only memory ratio = 193.0x (10,112 B vs 1,951,648 B); incl. GC buffer = 231.8x",
        },
    ]
    manifest_path = OUT_DIR / "figure_manifest.csv"
    with open(manifest_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(manifest_rows[0].keys()))
        w.writeheader()
        w.writerows(manifest_rows)
    print(f"Saved manifest: {manifest_path}")
    print("DONE building all 7 figures (PNG/PDF/SVG) and iCAT_Paper_Figures.xlsx.")


if __name__ == "__main__":
    main()
