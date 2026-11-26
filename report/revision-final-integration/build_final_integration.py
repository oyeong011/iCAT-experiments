#!/usr/bin/env python3
"""
iCAT Final Revision Integration Builder (Home PC — Read-Only GitHub Verifier)
Builds:
1. Extends report/paper-figures/iCAT_Paper_Figures.xlsx with 9 new traceability sheets
   while keeping all 12 original sheets intact:
   - Ablation, Discount-free, NoElim, Online Greedy, Periodic Switching,
     Random Search, Greedy GC, Experiment Manifest, Data Validity
2. report/revision-final-integration/revision_progress.xlsx
3. report/revision-final-integration/evidence_matrix.xlsx
4. report/revision-final-integration/experiment_completion_matrix.csv
5. report/revision-final-integration/paper_figures/ (7 comparison figures x PNG 300dpi / PDF / SVG):
   - fig_discount_free_vs_v4
   - fig_noelim_vs_v4
   - fig_online_greedy_vs_v4
   - fig_periodic_switching_vs_v4
   - fig_random_search_vs_v4
   - fig_greedy_gc_vs_v4
   - fig_full_ablation

Strict rules:
- Zero NVMeVirt / FIO / YCSB / Filebench execution.
- Zero modification to raw logs or figs/.
- Never pool SeungCom (i7-7700) and GoCom (Ryzen 3600XT) data.
- Never display [ESTIMATED] or [THEORETICAL] values as [MEASURED].
- Never display statistical conclusions or CI bars when n < 3.
"""

import csv
import gzip
import json
import math
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import openpyxl
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

REPO_ROOT = Path(__file__).resolve().parents[2]
PF_DIR = REPO_ROOT / "report" / "paper-figures"
REAN_DIR = REPO_ROOT / "report" / "reanalysis-20261124"
OUT_DIR = Path(__file__).resolve().parent
FIG_DIR = OUT_DIR / "paper_figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

REF_MAIN = "origin/main"
REF_GOCOM = "origin/report/data-validity-20261124"
REF_RES = "origin/resource-overhead-20261114"

GENERATED_AT = datetime.now().strftime("%Y-%m-%d %H:%M:%S KST")

PALETTE = {
    "v4": "#0072B2",
    "random": "#D55E00",
    "v1": "#E69F00",
    "v2": "#CC79A7",
    "noelim": "#009E73",
    "nosettle": "#56B4E9",
    "fullreset": "#8E44AD",
    "greedy": "#B2182B",
    "online": "#D95F02",
    "neutral": "#555555",
    "pending_bg": "#F6F7F9",
    "pending_edge": "#B0B8C4",
    "est_bg": "#FFF9EB",
    "est_edge": "#D9A02B",
}


# ---------------------------------------------------------------------------
# Git & Statistical Helpers
# ---------------------------------------------------------------------------
def git_rev(ref: str) -> str:
    return subprocess.run(
        ["git", "rev-parse", "--short=9", ref], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def git_show(spec: str, binary: bool = False):
    p = subprocess.run(["git", "show", spec], cwd=REPO_ROOT, capture_output=True)
    if p.returncode != 0:
        return None
    return p.stdout if binary else p.stdout.decode("utf-8", errors="replace")


def student_t_crit_95(df: float) -> float:
    if df <= 0:
        return float("nan")
    def t_cdf(t_val, v):
        c = math.gamma((v + 1.0) / 2.0) / (math.sqrt(v * math.pi) * math.gamma(v / 2.0))
        n = 2000
        h = t_val / n
        s = 0.0
        for i in range(n + 1):
            x = i * h
            w = 1.0 if (i == 0 or i == n) else (4.0 if i % 2 == 1 else 2.0)
            s += w * ((1.0 + (x * x) / v) ** (-(v + 1.0) / 2.0))
        return 0.5 + c * s * h / 3.0

    lo, hi = 1.9, 14.0
    for _ in range(55):
        mid = 0.5 * (lo + hi)
        if t_cdf(mid, df) < 0.975:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def calc_summary(vals):
    n = len(vals)
    if n == 0:
        return {"n": 0, "mean": None, "sd": None, "ci_half": None, "ci_lo": None, "ci_hi": None}
    mean = float(np.mean(vals))
    if n < 3:
        return {"n": n, "mean": mean, "sd": None, "ci_half": None, "ci_lo": None, "ci_hi": None}
    sd = float(np.std(vals, ddof=1))
    tc = student_t_crit_95(n - 1)
    ci_h = tc * sd / math.sqrt(n)
    return {"n": n, "mean": mean, "sd": sd, "ci_half": ci_h, "ci_lo": mean - ci_h, "ci_hi": mean + ci_h}


def calc_welch(a, b):
    if len(a) < 3 or len(b) < 3:
        return None
    ma, mb = float(np.mean(a)), float(np.mean(b))
    va, vb = float(np.var(a, ddof=1)), float(np.var(b, ddof=1))
    na, nb = len(a), len(b)
    se = math.sqrt(va / na + vb / nb)
    df = (va / na + vb / nb) ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    tc = student_t_crit_95(df)
    delta = ma - mb
    ci_h = tc * se
    sp = math.sqrt(((na - 1) * va + (nb - 1) * vb) / (na + nb - 2))
    J = 1.0 - 3.0 / (4.0 * (na + nb - 2) - 1.0)
    g = (delta / sp) * J if sp > 0 else 0.0
    return {
        "delta": delta, "ci_half": ci_h, "ci_lo": delta - ci_h, "ci_hi": delta + ci_h,
        "df": df, "hedges_g": g, "excludes_zero": (delta - ci_h > 0) or (delta + ci_h < 0),
    }


# ---------------------------------------------------------------------------
# Matplotlib Styling
# ---------------------------------------------------------------------------
def setup_matplotlib():
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "font.family": "DejaVu Sans",
        "font.size": 9.3,
        "axes.titlesize": 10.2,
        "axes.titleweight": "bold",
        "axes.labelsize": 9.3,
        "axes.labelweight": "bold",
        "xtick.labelsize": 8.3,
        "ytick.labelsize": 8.3,
        "legend.fontsize": 7.8,
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


def save_fig(fig, stem: str):
    out = {}
    for ext in ["png", "pdf", "svg"]:
        p = FIG_DIR / f"{stem}.{ext}"
        kw = {"bbox_inches": "tight", "facecolor": "white"}
        if ext == "png":
            kw["dpi"] = 300
        fig.savefig(p, **kw)
        out[ext] = str(p.relative_to(REPO_ROOT)).replace("\\", "/")
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Independent Verification of Existing Greedy GC Runs (47 total -> 9 valid mix sets + mixY + 16 invalid)
# ---------------------------------------------------------------------------
def verify_legacy_run(ref: str, run_dir: str):
    summ = git_show(f"{ref}:{run_dir}/summary.txt") or ""
    fc = git_show(f"{ref}:{run_dir}/final-control.txt") or ""
    ec_raw = (git_show(f"{ref}:{run_dir}/exit-code.txt") or "-1").strip()
    ec = int(ec_raw) if re.match(r"^-?\d+$", ec_raw) else -1
    env = git_show(f"{ref}:{run_dir}/environment.txt") or ""
    m_sha = re.search(r"([0-9a-f]{64})\s+(\S+\.ko)", env)
    mod_sha = m_sha.group(1) if m_sha else "UNRECORDED"
    mod_name = os.path.basename(m_sha.group(2)) if m_sha else "UNKNOWN"
    m_host = re.search(r"Linux\s+(\S+)\s+(\S+)", env)
    host = m_host.group(1) if m_host else "UNKNOWN"

    m_st = re.search(r"total\s+host_bytes=(\d+)\s+host_pages=(\d+)\s+gc_pages=(\d+)\s+WAF=([\d.]+)", summ)
    m_ft = re.search(r"host_bytes=(\d+)\s+host_pages=(\d+)\s+gc_pages=(\d+)", fc)
    parts = re.findall(r"part=(\d+)\s+host_pages=(\d+)\s+gc_pages=(\d+)", fc)
    if m_st:
        sh, sg, sw = int(m_st.group(2)), int(m_st.group(3)), float(m_st.group(4))
        w_recalc = 1.0 + sg / sh
        fh = int(m_ft.group(2)) if m_ft else sh
        fg = int(m_ft.group(3)) if m_ft else sg
        ph = sum(int(x[1]) for x in parts) if parts else sh
        pg = sum(int(x[2]) for x in parts) if parts else sg
        two_path = (sh == fh == ph and sg == fg == pg and abs(w_recalc - sw) < 2e-6)
    else:
        sh, sg, sw, w_recalc, two_path = 0, 0, 0.0, 0.0, False

    kl = git_show(f"{ref}:{run_dir}/kernel.log") or ""
    k_errs = sum(1 for l in kl.splitlines() if re.search(r"\b(BUG:|Oops|WARNING:|Call Trace|panic|EXT4-fs error|I/O error)\b", l))

    return {
        "run_dir": run_dir, "host": host, "mod_name": mod_name, "mod_sha": mod_sha,
        "exit_code": ec, "host_pages": sh, "gc_pages": sg,
        "waf_summary": sw, "waf_recalc": w_recalc, "two_path_ok": two_path,
        "kernel_errors": k_errs, "valid": (ec == 0 and two_path and k_errs == 0),
    }


def load_greedy_verification(ref_gocom: str):
    valid_workloads = ["mixC", "mixD", "mixF", "mixK", "mixL", "mixM", "mixO", "mixP", "mixQ"]
    greedy_summary = []
    greedy_raw_rows = []
    for wl in valid_workloads:
        g_runs = [verify_legacy_run(ref_gocom, f"result/mix-20260911/{wl}-greedy-rep{i}") for i in [1, 2, 3]]
        o_runs = [verify_legacy_run(ref_gocom, f"result/mix-20260911/{wl}-online-rep{i}") for i in [1, 2, 3]]
        # Same-length x1 v4 only exists on mixC and mixD (n=1)
        v4_x1 = None
        if wl in ("mixC", "mixD"):
            v4_x1 = verify_legacy_run(ref_gocom, f"result/mix-20260911/{wl}-onlinev4-rep1")
        for r in g_runs:
            greedy_raw_rows.append({"workload": wl, "policy": "Greedy GC (x1)", "valid_note": "VALID (non-SQLite or YCSB 0% fail)", **r})
        for r in o_runs:
            greedy_raw_rows.append({"workload": wl, "policy": "iCAT-online (x1)", "valid_note": "VALID (same-length baseline)", **r})
        if v4_x1:
            greedy_raw_rows.append({"workload": wl, "policy": "iCAT-v4 (x1, n=1)", "valid_note": "VALID (n=1 exploratory, no CI)", **v4_x1})

        gs = calc_summary([r["waf_recalc"] for r in g_runs])
        os_ = calc_summary([r["waf_recalc"] for r in o_runs])
        w_go = calc_welch([r["waf_recalc"] for r in g_runs], [r["waf_recalc"] for r in o_runs])
        greedy_summary.append({
            "workload": wl,
            "greedy": gs,
            "online": os_,
            "welch_greedy_minus_online": w_go,
            "pct_reduction_online_vs_greedy": (gs["mean"] - os_["mean"]) / gs["mean"] * 100.0,
            "v4_x1_n1": v4_x1["waf_recalc"] if v4_x1 else None,
            "all_two_path_ok": all(r["two_path_ok"] and r["valid"] for r in g_runs + o_runs),
        })

    # Also verify mixY single-run Greedy on GoCom & v4 on SeungCom (host-separated!)
    mixy_gocom_greedy = verify_legacy_run(ref_gocom, "result/gocom-sg-20261119/mixY-sg-greedy-rep1")
    mixy_gocom_arm47 = verify_legacy_run(ref_gocom, "result/gocom-sg-20261119/mixY-sg-arm47-rep1")
    mixy_seung_v4 = verify_legacy_run(ref_gocom, "result/smartgc-20261119/resume/mixY-onlinev4-rep1")
    greedy_raw_rows.append({"workload": "mixY (GoCom)", "policy": "Greedy GC (n=1)", "valid_note": "VALID (GoCom n=1, no CI; do NOT pool with SeungCom)", **mixy_gocom_greedy})
    greedy_raw_rows.append({"workload": "mixY (GoCom)", "policy": "CAT-47 (n=1)", "valid_note": "VALID (GoCom n=1 same-host ref)", **mixy_gocom_arm47})
    greedy_raw_rows.append({"workload": "mixY (SeungCom)", "policy": "iCAT-v4 (n=1)", "valid_note": "VALID (SeungCom n=1; different host from mixY-sg-greedy)", **mixy_seung_v4})

    return greedy_summary, greedy_raw_rows, {
        "mixy_gocom_greedy": mixy_gocom_greedy,
        "mixy_gocom_arm47": mixy_gocom_arm47,
        "mixy_seung_v4": mixy_seung_v4,
    }


def load_random_search_data(ref_main: str):
    # 1. SeungCom 20261125 mixFYF Monte Carlo Random Search estimates (from GoCom revA-random windows)
    rs_txt = (git_show(f"{ref_main}:result/revision-20261125-analysis/random_search.csv") or "").lstrip("\ufeff")
    seung_rs = list(csv.DictReader(rs_txt.splitlines()))
    # 2. Home PC R4 exact combinatorics on 3x60 single-workload sweeps
    with open(REAN_DIR / "r4_random_search_expectation.csv", encoding="utf-8-sig") as f:
        r4_rows = list(csv.DictReader(f))
    return seung_rs, r4_rows


def load_gamma_data():
    with open(REAN_DIR / "r2_discount_gamma.csv", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# Build 7 Comparison Figures in report/revision-final-integration/paper_figures/
# ---------------------------------------------------------------------------
def build_comparison_figures(vdata, greedy_summary, mixy_refs, seung_rs, r4_rows, gamma_rows):
    fig_manifest = {}

    # 1. Discount-free vs V4 (COMPLETED: SeungCom abl-20261125 same-batch n=3 + Theoretical gamma^n panel)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.8, 4.3), gridspec_kw={"wspace": 0.30})
    revD_v4 = vdata["fig02_ablation"]["seungcom_revD_total"]["revD-v4"]
    abl_v4 = vdata["fig02_ablation"]["seungcom_abl_total"]["abl-v4"]
    abl_nd = vdata["fig02_ablation"]["seungcom_abl_total"]["abl-nodiscount"]
    abl_nd_w = vdata["fig02_ablation"]["seungcom_abl_welch_total"]["abl-nodiscount"]
    abl_raw = vdata["fig02_ablation"]["seungcom_abl_raw"]
    b_df = ax1.bar([0, 1], [abl_v4["mean"], abl_nd["mean"]], width=0.46,
                   color=[PALETTE["v4"], PALETTE["nosettle"]], edgecolor="#222222",
                   yerr=[abl_v4["ci_half"], abl_nd["ci_half"]], capsize=5)
    ax1.scatter([-0.08, 0.0, 0.08], abl_raw["abl-v4"], color="white", edgecolor="#111111", s=24, zorder=6, linewidth=0.85)
    ax1.scatter([0.92, 1.0, 1.08], abl_raw["abl-nodiscount"], color="white", edgecolor="#111111", s=24, zorder=6, linewidth=0.85)
    ax1.text(0, abl_v4["mean"] + abl_v4["ci_half"] + 0.010,
             f"{abl_v4['mean']:.4f} ± {abl_v4['sd']:.4f}\n(CI ±{abl_v4['ci_half']:.4f}, n=3)",
             ha="center", va="bottom", fontsize=7.5, fontweight="bold")
    ax1.text(1, abl_nd["mean"] + abl_nd["ci_half"] + 0.010,
             f"{abl_nd['mean']:.4f} ± {abl_nd['sd']:.4f}\n(CI ±{abl_nd['ci_half']:.4f}, n=3)",
             ha="center", va="bottom", fontsize=7.5, fontweight="bold")
    ax1.set_xticks([0, 1])
    ax1.set_xticklabels(["iCAT-v4 (γ=0.9995)\nSeungCom abl (n=3)", "Discount-free (γ=1.0)\nSeungCom abl (n=3)"])
    ax1.set_ylabel("Overall WAF (mixFYF 250k)")
    ax1.set_title("(a) Live Same-Batch Comparison (COMPLETED, n=3)")
    ax1.set_xlim(-0.55, 1.55)
    ax1.set_ylim(2.00, 2.34)
    ax1.text(0.5, 0.95,
             f"Welch Δ (NoDiscount − V4) = {abl_nd_w['delta']:+.4f} [{abl_nd_w['ci_lo']:+.3f}, {abl_nd_w['ci_hi']:+.3f}]\n"
             f"Honest null: No difference found (Holm p = 1.000; PhC −0.010)",
             transform=ax1.transAxes, ha="center", va="top", fontsize=7.3, fontweight="bold", color="#1F3864",
             bbox={"boxstyle": "round,pad=0.28", "facecolor": "#F4F8FB", "edgecolor": PALETTE["v4"]})

    # Panel (b): Theoretical weight decay gamma^n (strictly labeled THEORETICAL)
    gamma = 65503.0 / 65536.0
    ns = np.arange(0, 301, 5)
    ax2.set_facecolor(PALETTE["est_bg"])
    ax2.plot(ns, gamma ** ns, color=PALETTE["v4"], linewidth=2.0, label="γ = 65503/65536 ≈ 0.999496")
    ax2.axhline(1.0, color="#666666", linestyle="--", linewidth=1.2, label="Discount-free (γ = 1.0)")
    ax2.axvline(250, color=PALETTE["random"], linestyle=":", linewidth=1.2)
    ax2.annotate(f"End of 90m mixFYF\n(~250 windows/part)\nγ^250 = {gamma**250:.4f}",
                 xy=(250, gamma ** 250), xytext=(115, 0.895),
                 fontsize=7.6, fontweight="bold", color=PALETTE["random"],
                 arrowprops={"arrowstyle": "->", "color": PALETTE["random"], "lw": 1.0},
                 bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": PALETTE["random"]})
    ax2.set_xlabel("Elapsed Windows per Partition (n)")
    ax2.set_ylabel("Oldest Observation Weight (γ^n)")
    ax2.set_title("(b) [THEORETICAL] Discount Weight Decay (Explains Null)")
    ax2.set_ylim(0.84, 1.02)
    ax2.legend(loc="lower left", fontsize=7.6)
    fig.suptitle("Discount-free MAB (γ=1.0) vs. iCAT-v4 (γ=0.9995): Live Same-Batch Null & Theoretical Decay",
                 fontsize=9.8, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig_manifest["fig_discount_free_vs_v4"] = save_fig(fig, "fig_discount_free_vs_v4")

    # 2. NoElim vs V4 (GoCom revB* cross-batch + GoCom revE SAME-BATCH COMPLETED!)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.8, 4.3), gridspec_kw={"wspace": 0.30})
    v4_gc = vdata["fig02_ablation"]["variants"]["revA-v4"]
    ne_gc = vdata["fig02_ablation"]["variants"]["revB-noelim"]
    br_gc = vdata["fig02_ablation"]["revB_v4_bridge_n1"]
    revE_v4 = vdata["fig02_ablation"]["gocom_revE_total"]["revE-v4"]
    revE_ne = vdata["fig02_ablation"]["gocom_revE_total"]["revE-noelim"]
    revE_ne_w = vdata["fig02_ablation"]["gocom_revE_welch_total"]["revE-noelim"]
    revE_raw = vdata["fig02_ablation"]["gocom_revE_raw"]

    b1 = ax1.bar([0, 1], [v4_gc["mean"], ne_gc["mean"]], width=0.46,
                 color=[PALETTE["v4"], PALETTE["noelim"]], edgecolor="#222222",
                 yerr=[v4_gc["ci_half"], ne_gc["ci_half"]], capsize=5)
    b1[1].set_hatch("//")
    ax1.scatter([0.28], [br_gc], color="#B2182B", marker="D", s=42, zorder=6, label=f"revB-v4 bridge (n=1: {br_gc:.4f})")
    ax1.text(0, v4_gc["mean"] + v4_gc["ci_half"] + 0.010, f"{v4_gc['mean']:.4f} ± {v4_gc['sd']:.4f}\n(CI ±{v4_gc['ci_half']:.4f}, n=3)", ha="center", va="bottom", fontsize=7.4, fontweight="bold")
    ax1.text(1, ne_gc["mean"] + ne_gc["ci_half"] + 0.010, f"{ne_gc['mean']:.4f} ± {ne_gc['sd']:.4f}\n(CI ±{ne_gc['ci_half']:.4f}, n=3)", ha="center", va="bottom", fontsize=7.4, fontweight="bold")
    ax1.set_xticks([0, 1])
    ax1.set_xticklabels(["iCAT-v4\nGoCom revA (n=3)", "NoElim*\nGoCom revB (n=3)"])
    ax1.set_ylabel("Overall WAF (mixFYF 250k)")
    ax1.set_title("(a) Prior Cross-Batch* (Δ=+0.0942 [+0.070, +0.118])")
    ax1.set_ylim(2.00, 2.38)
    ax1.legend(loc="lower right", fontsize=7.3)

    b2 = ax2.bar([0, 1], [revE_v4["mean"], revE_ne["mean"]], width=0.46,
                 color=[PALETTE["v4"], PALETTE["noelim"]], edgecolor="#222222",
                 yerr=[revE_v4["ci_half"], revE_ne["ci_half"]], capsize=5)
    ax2.scatter([-0.08, 0.0, 0.08], revE_raw["revE-v4"], color="white", edgecolor="#111111", s=24, zorder=6, linewidth=0.85)
    ax2.scatter([0.92, 1.0, 1.08], revE_raw["revE-noelim"], color="white", edgecolor="#111111", s=24, zorder=6, linewidth=0.85)
    ax2.text(0, revE_v4["mean"] + revE_v4["ci_half"] + 0.008, f"{revE_v4['mean']:.4f} ± {revE_v4['sd']:.4f}\n(CI ±{revE_v4['ci_half']:.4f}, n=3)", ha="center", va="bottom", fontsize=7.4, fontweight="bold")
    ax2.text(1, revE_ne["mean"] + revE_ne["ci_half"] + 0.008, f"{revE_ne['mean']:.4f} ± {revE_ne['sd']:.4f}\n(CI ±{revE_ne['ci_half']:.4f}, n=3)", ha="center", va="bottom", fontsize=7.4, fontweight="bold")
    ax2.set_xticks([0, 1])
    ax2.set_xticklabels(["iCAT-v4 (Control)\nGoCom revE (n=3)", "Isolated NoElim (VAR=3)\nGoCom revE (n=3)"])
    ax2.set_ylabel("Overall WAF (mixFYF 250k)")
    ax2.set_title("(b) GoCom revE Same-Batch Verification (COMPLETED)")
    ax2.set_xlim(-0.55, 1.55)
    ax2.set_ylim(2.00, 2.40)
    ax2.text(0.51, 0.96,
             f"Same-Batch Δ = {revE_ne_w['delta']:+.4f} [{revE_ne_w['ci_lo']:+.3f}, {revE_ne_w['ci_hi']:+.3f}] (Welch & Paired CI>0)\n"
             f"PhC Δ = +0.1548 [+0.030, +0.280] (g=3.88; Holm p=0.091)",
             transform=ax2.transAxes, ha="center", va="top", fontsize=6.8, fontweight="bold", color="#1F3864",
             bbox={"boxstyle": "round,pad=0.24", "facecolor": "#F4F8FB", "edgecolor": PALETTE["noelim"]})
    fig.suptitle("Candidate Elimination (Isolated NoElim vs. iCAT-v4): Cross-Batch* & Same-Batch Confirmation",
                 fontsize=9.8, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig_manifest["fig_noelim_vs_v4"] = save_fig(fig, "fig_noelim_vs_v4")

    # 3. Online Greedy vs V4 (COMPLETED: Strictly Host-Separated — Panel A SeungCom, Panel B GoCom Baselines)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.2, 4.3), gridspec_kw={"width_ratios": [1.05, 1.15], "wspace": 0.28})
    revA_rand = vdata["fig01_random"]["overall"]["revA-random"]
    revC_v4 = vdata["fig05_parameters"]["live_revC"]["elim15_v4_pct"]
    revC_onl = vdata["fig05_parameters"]["live_revC"]["online_orig"]
    gr_st = vdata["fig02_ablation"]["seungcom_greedy_total"]
    gr_raw = vdata["fig02_ablation"]["seungcom_greedy_raw"]
    gr_w_revD = vdata["fig02_ablation"]["seungcom_greedy_welch_vs_revD_total"]
    gr_w_abl = vdata["fig02_ablation"]["seungcom_greedy_welch_vs_abl_total"]

    # Panel (a): SeungCom (i7-7700) — Online Greedy vs revD-v4 (primary) & abl-v4 (secondary)
    xs_g = np.arange(3)
    ms_g = [revD_v4["mean"], abl_v4["mean"], gr_st["mean"]]
    cs_g = [revD_v4["ci_half"], abl_v4["ci_half"], gr_st["ci_half"]]
    cols_g = [PALETTE["v4"], "#4A90C2", PALETTE["greedy"]]
    bs_g = ax1.bar(xs_g, ms_g, width=0.50, color=cols_g, edgecolor="#222222", yerr=cs_g, capsize=4.5)
    ax1.scatter([1.92, 2.0, 2.08], gr_raw, color="white", edgecolor="#111111", s=24, zorder=6, linewidth=0.85)
    for b, m, c in zip(bs_g, ms_g, cs_g):
        ax1.text(b.get_x() + b.get_width() / 2, m + c + 0.009, f"{m:.4f}\n±{c:.4f}", ha="center", va="bottom", fontsize=7.4, fontweight="bold")
    ax1.set_xticks(xs_g)
    ax1.set_xticklabels(["iCAT-v4\nrevD (Primary, n=3)", "iCAT-v4\nabl (Sec., n=3)", "Online Greedy\nVAR=8 (n=3)"], fontsize=7.9)
    ax1.set_ylabel("Overall WAF (mixFYF 250k)")
    ax1.set_title("(a) SeungCom (i7-7700): Online Greedy vs. iCAT-v4")
    ax1.set_ylim(2.00, 2.38)
    ax1.text(0.52, 0.96,
             f"Greedy − revD-v4: {gr_w_revD['delta']:+.4f} [{gr_w_revD['ci_lo']:+.3f}, {gr_w_revD['ci_hi']:+.3f}] (p=0.54)\n"
             f"Honest null (0/2,513 rule mismatches; PhC +0.017)",
             transform=ax1.transAxes, ha="center", va="top", fontsize=6.7, fontweight="bold", color="#7A1C1C",
             bbox={"boxstyle": "round,pad=0.24", "facecolor": "#FFF5F5", "edgecolor": PALETTE["greedy"]})

    # Panel (b): GoCom (Ryzen 3600XT) — Random Selection & Original iCAT vs Same-Batch V4 (NOT pooled with SeungCom)
    xg_b = np.arange(4)
    mg_b = [v4_gc["mean"], revA_rand["mean"], revC_v4["waf"], revC_onl["waf"]]
    cg_b = [v4_gc["ci_half"], revA_rand["ci_half"], revC_v4["ci_half"], revC_onl["ci_half"]]
    cols_gb = [PALETTE["v4"], PALETTE["random"], "#2B8CBE", PALETTE["online"]]
    bg_b = ax2.bar(xg_b, mg_b, width=0.52, color=cols_gb, edgecolor="#222222", yerr=cg_b, capsize=4.5)
    ax2.axvline(1.5, color="#888888", linestyle=":", linewidth=1.0)
    for b, m, c in zip(bg_b, mg_b, cg_b):
        ax2.text(b.get_x() + b.get_width() / 2, m + c + 0.012, f"{m:.4f}\n±{c:.4f}", ha="center", va="bottom", fontsize=7.3, fontweight="bold")
    ax2.set_xticks(xg_b)
    ax2.set_xticklabels(["iCAT-v4\nrevA (n=3)", "Random Sel.\nrevA (n=3)", "iCAT-v4\nrevC (n=3)", "Original iCAT\nrevC (n=3)"], fontsize=7.7)
    ax2.set_ylabel("Overall WAF (mixFYF 250k)")
    ax2.set_title("(b) GoCom (Ryzen 3600XT): Random & Original iCAT (Not Pooled)")
    ax2.set_ylim(2.00, 2.58)
    ax2.text(0.5, 0.95,
             "GoCom Same-Batch Baselines (Both Welch & Paired CI > 0):\n"
             "Random − V4 = +0.1959 (−8.4%); Orig iCAT − V4 = +0.2751 (−11.5%)",
             transform=ax2.transAxes, ha="center", va="top", fontsize=7.1, fontweight="bold", color="#1F3864",
             bbox={"boxstyle": "round,pad=0.26", "facecolor": "#F4F8FB", "edgecolor": PALETTE["v4"]})
    fig.suptitle("Online Policy Selection Baselines vs. iCAT-v4 (Strictly Host-Separated; Error Bars = 95% t-CI, n=3)",
                 fontsize=9.8, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig_manifest["fig_online_greedy_vs_v4"] = save_fig(fig, "fig_online_greedy_vs_v4")

    # 4. Periodic Switching vs V4 (EXCLUDED BY USER DECISION — Scope Limitation)
    fig, ax = plt.subplots(figsize=(7.6, 4.0))
    ax.set_facecolor(PALETTE["pending_bg"])
    ax.bar([0, 2], [v4_gc["mean"], revA_rand["mean"]], width=0.46,
           color=[PALETTE["v4"], PALETTE["random"]], edgecolor="#222222",
           yerr=[v4_gc["ci_half"], revA_rand["ci_half"]], capsize=5)
    ax.text(0, v4_gc["mean"] + v4_gc["ci_half"] + 0.015, f"{v4_gc['mean']:.4f} ± {v4_gc['sd']:.4f}\n(CI ±{v4_gc['ci_half']:.4f}, n=3)", ha="center", va="bottom", fontsize=7.6, fontweight="bold")
    ax.text(2, revA_rand["mean"] + revA_rand["ci_half"] + 0.015, f"{revA_rand['mean']:.4f} ± {revA_rand['sd']:.4f}\n(CI ±{revA_rand['ci_half']:.4f}, n=3)", ha="center", va="bottom", fontsize=7.6, fontweight="bold")
    ax.text(1, 2.22, "Periodic Switching (Round-Robin)\nEXCLUDED BY USER DECISION\n(Not Scheduled; 0/3)",
            ha="center", va="center", fontsize=8.1, color="#555555",
            bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": PALETTE["pending_edge"], "linestyle": "--"})
    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(["iCAT-v4\nGoCom revA (n=3)", "Periodic Switching\n(Excluded / 0/3)", "Random Selection\nGoCom revA (n=3)"])
    ax.set_ylabel("Overall WAF (mixFYF 250k)")
    ax.set_title("Periodic Switching vs. iCAT-v4 — EXCLUDED (Scope Limitation)")
    ax.set_xlim(-0.55, 2.55)
    ax.set_ylim(2.00, 2.48)
    ax.text(0.5, 0.93, "STATUS: EXCLUDED BY USER DECISION (Scope Limitation)\nDocumented in Limitations; Random & Online Greedy & Original iCAT evaluated instead",
            transform=ax.transAxes, ha="center", va="top", fontsize=7.6, fontweight="bold", color="#555555",
            bbox={"boxstyle": "round,pad=0.28", "facecolor": "#F4F6F9", "edgecolor": "#8C9BAB"})
    fig.tight_layout()
    fig_manifest["fig_periodic_switching_vs_v4"] = save_fig(fig, "fig_periodic_switching_vs_v4")

    # 5. Random Search vs V4 (STRICT separation of [MEASURED] vs [ESTIMATED])
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.8, 4.2), gridspec_kw={"wspace": 0.28})
    # Panel (a): GoCom mixFYF Measured iCAT-v4 & Random vs [ESTIMATED] Monte Carlo Random Search (k=1..45)
    ks_mc, vals_mc, p10_mc, p90_mc = [], [], [], []
    for r in seung_rs:
        m = re.search(r"Random Search k=(\d+)", r["what"])
        if m:
            ks_mc.append(int(m.group(1)))
            vals_mc.append(float(r["value"]))
            mp = re.search(r"p10=([\d.]+)\s+p90=([\d.]+)", r["values"])
            p10_mc.append(float(mp.group(1)) if mp else float(r["value"]))
            p90_mc.append(float(mp.group(2)) if mp else float(r["value"]))
    ax1.set_facecolor(PALETTE["est_bg"])
    ax1.plot(ks_mc, vals_mc, "o--", color="#B86B00", linewidth=1.8, markersize=5.5, label="[ESTIMATED] Random Search (k×1 win, MC 20k)")
    ax1.fill_between(ks_mc, p10_mc, p90_mc, color="#E69F00", alpha=0.16, label="[ESTIMATED] p10–p90 range")
    ax1.axhline(v4_gc["mean"], color=PALETTE["v4"], linewidth=2.0, label=f"[MEASURED] iCAT-v4: {v4_gc['mean']:.4f} ± {v4_gc['sd']:.4f} (n=3)")
    ax1.axhspan(v4_gc["ci_lo"], v4_gc["ci_hi"], color=PALETTE["v4"], alpha=0.15)
    ax1.axhline(revA_rand["mean"], color=PALETTE["random"], linestyle="-.", linewidth=1.6, label=f"[MEASURED] Random Sel.: {revA_rand['mean']:.4f} ± {revA_rand['sd']:.4f} (n=3)")
    ax1.set_xlabel("Random Search Trial Budget k (of 45 arms)")
    ax1.set_ylabel("Overall WAF (mixFYF 250k)")
    ax1.set_title("(a) mixFYF: [MEASURED] V4 vs. [ESTIMATED] Random Search")
    ax1.set_ylim(2.02, 2.46)
    ax1.legend(loc="upper right", fontsize=7.1)
    ax1.text(0.02, 0.04, "Note: MC estimator bias on arm47 = +0.0846 (model only, NOT live NVMeVirt).",
             transform=ax1.transAxes, fontsize=7.0, style="italic", color="#555555")

    # Panel (b): SeungCom 3x60 single-workload exact combinatorics [ESTIMATED] E[min W_i] (45-arm space)
    ax2.set_facecolor(PALETTE["est_bg"])
    wls_r4 = [("FIO-Fast (test4)", PALETTE["v4"], "o-"), ("OLTP", PALETTE["noelim"], "s-"), ("SQLite-A (87/87 valid)", PALETTE["v2"], "^-")]
    for wname, col, fmt in wls_r4:
        sub = [r for r in r4_rows if r["workload"] == wname and int(r["N_candidates"]) == 45]
        ks = [int(r["k_random_trials"]) for r in sub]
        gaps = [float(r["gap_vs_optimal_pct"]) for r in sub]
        short = wname.split(" (")[0]
        ax2.plot(ks, gaps, fmt, color=col, linewidth=1.7, markersize=5, label=f"{short} (45-arm exact E[min])")
    ax2.set_xlabel("Random Trials k (Single-Workload Static Sweep)")
    ax2.set_ylabel("Expected WAF Gap vs. Optimal (%)")
    ax2.set_title("(b) [ESTIMATED] Exact Combinatorics on 3×60 Sweeps")
    ax2.set_ylim(-0.5, 20.5)
    ax2.legend(loc="upper right", fontsize=7.4)
    ax2.text(0.5, -0.19, "Static offline E[min W_i]; excludes online switching & drift cost.",
             transform=ax2.transAxes, ha="center", va="top", fontsize=7.0, style="italic", color="#555555")
    fig.suptitle("Random Search vs. iCAT-v4: Strictly Separating [MEASURED] Runs from [ESTIMATED] Models",
                 fontsize=9.8, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig_manifest["fig_random_search_vs_v4"] = save_fig(fig, "fig_random_search_vs_v4")

    # 6. Greedy GC vs iCAT (9 valid SeungCom x1 workloads n=3 vs n=3 + mixFYF/mixY note)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.2, 4.3), gridspec_kw={"width_ratios": [1.85, 1.0], "wspace": 0.25})
    wls = [g["workload"] for g in greedy_summary]
    xg = np.arange(len(wls))
    wg = 0.36
    gm = [g["greedy"]["mean"] for g in greedy_summary]
    gci = [g["greedy"]["ci_half"] for g in greedy_summary]
    om = [g["online"]["mean"] for g in greedy_summary]
    oci = [g["online"]["ci_half"] for g in greedy_summary]
    ax1.bar(xg - wg / 2, gm, width=wg, color=PALETTE["greedy"], edgecolor="#222222", yerr=gci, capsize=3, label="Greedy GC (x1, n=3, 95% CI)")
    ax1.bar(xg + wg / 2, om, width=wg, color=PALETTE["online"], edgecolor="#222222", yerr=oci, capsize=3, label="iCAT-online (x1, n=3, 95% CI)")
    # Overlay mixC/mixD v4 x1 n=1 (no CI)
    for idx_w, g in enumerate(greedy_summary):
        if g["v4_x1_n1"] is not None:
            ax1.scatter([xg[idx_w] + wg / 2], [g["v4_x1_n1"]], color=PALETTE["v4"], marker="D", edgecolor="white", s=45, zorder=6,
                        label="iCAT-v4 (x1, n=1, no CI)" if idx_w == 0 else None)
    ax1.set_xticks(xg)
    ax1.set_xticklabels(wls)
    ax1.set_ylabel("Overall WAF (SeungCom Sep 2026)")
    ax1.set_title("(a) 9 Valid Non-Contaminated Workloads (n=3 vs n=3, Welch CI>0 in 9/9)")
    ax1.set_ylim(0.8, 4.15)
    ax1.legend(loc="upper right", fontsize=7.4)

    # Panel (b): Revision mixFYF batchG-20261126 (SeungCom n=3 COMPLETED!) + mixY (GoCom n=1)
    bg_gg_m, bg_gg_ci = 2.629343, 0.017200
    bg_v4_m, bg_v4_ci = 2.110472, 0.060602
    ax2.bar([0, 1], [bg_gg_m, bg_v4_m], yerr=[bg_gg_ci, bg_v4_ci], capsize=3.5,
            width=0.46, color=[PALETTE["greedy"], PALETTE["v4"]], edgecolor="#222222")
    ax2.bar([2.1, 3.0], [mixy_refs["mixy_gocom_greedy"]["waf_recalc"], mixy_refs["mixy_gocom_arm47"]["waf_recalc"]],
            width=0.44, color=[PALETTE["greedy"], "#777777"], edgecolor="#222222", alpha=0.82)
    ax2.axvline(1.55, color="#888888", linestyle=":", linewidth=1.0)
    ax2.text(0, bg_gg_m + bg_gg_ci + 0.12, f"{bg_gg_m:.3f}\n(n=3)", ha="center", va="bottom", fontsize=7.2, fontweight="bold")
    ax2.text(1, bg_v4_m + bg_v4_ci + 0.12, f"{bg_v4_m:.3f}\n(n=3)", ha="center", va="bottom", fontsize=7.2, fontweight="bold")
    ax2.text(0.5, 4.35, "batchG (n=3):\nΔ=+0.519 [+0.463,+0.574]\nHolm p=0.0013 (−19.7%)",
             ha="center", va="center", fontsize=6.7, color="#1F3864", fontweight="bold",
             bbox={"boxstyle": "round,pad=0.22", "facecolor": "#F4F8FB", "edgecolor": PALETTE["v4"]})
    ax2.text(2.1, mixy_refs["mixy_gocom_greedy"]["waf_recalc"] + 0.14, f"{mixy_refs['mixy_gocom_greedy']['waf_recalc']:.3f}\n(n=1)", ha="center", va="bottom", fontsize=7.0, fontweight="bold")
    ax2.text(3.0, mixy_refs["mixy_gocom_arm47"]["waf_recalc"] + 0.14, f"{mixy_refs['mixy_gocom_arm47']['waf_recalc']:.3f}\n(n=1)", ha="center", va="bottom", fontsize=7.0, fontweight="bold")
    ax2.set_xticks([0, 1, 2.1, 3.0])
    ax2.set_xticklabels(["mixFYF\nGreedy\n(SC n=3)", "mixFYF\nV4\n(SC n=3)", "mixY\nGreedy\n(GC n=1)", "mixY\nCAT-47\n(GC n=1)"], fontsize=7.0)
    ax2.set_ylabel("Overall WAF")
    ax2.set_title("(b) mixFYF batchG (n=3 PASS) & mixY (n=1)")
    ax2.set_xlim(-0.55, 3.55)
    ax2.set_ylim(0, 7.2)
    fig.suptitle("Greedy GC Verification: 9 Legacy Workloads (−7.1% to −42.0%) & mixFYF batchG (−19.7%, Holm p=0.0013)",
                 fontsize=9.6, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig_manifest["fig_greedy_gc_vs_v4"] = save_fig(fig, "fig_greedy_gc_vs_v4")

    # 7. Full Ablation Comparison (ALL COMPLETED: GoCom revA/revB*/revE n=3 & SeungCom revD/abl n=3)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.2, 4.6), gridspec_kw={"width_ratios": [1.22, 1.15], "wspace": 0.24})
    revE_tot = vdata["fig02_ablation"]["gocom_revE_total"]
    gc_bars = [
        ("revA-v4", "v4\n(revA)", PALETTE["v4"], False, vdata["fig02_ablation"]["variants"]["revA-v4"]),
        ("revA-v1", "NoDrift\n(revA)", PALETTE["v1"], False, vdata["fig02_ablation"]["variants"]["revA-v1"]),
        ("revA-v2", "V2 Off\n(revA)", PALETTE["v2"], False, vdata["fig02_ablation"]["variants"]["revA-v2"]),
        ("revE-v4", "v4\n(revE)", "#2B8CBE", False, revE_tot["revE-v4"]),
        ("revE-noelim", "NoElim\n(revE)", PALETTE["noelim"], False, revE_tot["revE-noelim"]),
        ("revE-drift12", "Drift12\n(revE)", "#E67E22", False, revE_tot["revE-drift12"]),
    ]
    x_a = np.arange(len(gc_bars))
    ma = [d["mean"] for _, _, _, _, d in gc_bars]
    ca = [d["ci_half"] for _, _, _, _, d in gc_bars]
    ba = ax1.bar(x_a, ma, width=0.56, color=[c for _, _, c, _, _ in gc_bars], edgecolor="#222222", yerr=ca, capsize=3.5)
    ax1.axvline(2.5, color="#888888", linestyle=":", linewidth=1.0)
    for bar, m, c in zip(ba, ma, ca):
        ax1.text(bar.get_x() + bar.get_width() / 2, min(m + c + 0.008, 2.43), f"{m:.3f}", ha="center", va="bottom", fontsize=7.4, fontweight="bold")
    ax1.set_xticks(x_a)
    ax1.set_xticklabels([l for _, l, _, _, _ in gc_bars], fontsize=7.6)
    ax1.set_ylabel("Overall WAF (mixFYF 250k, n=3)")
    ax1.set_title("(a) GoCom (Ryzen 3600XT): revA & Same-Batch revE (n=3)")
    ax1.set_ylim(2.00, 2.50)
    ax1.text(0.51, 0.96, "revE Same-Batch: NoElim +0.0913 [+0.030,+0.153]\nDrift12 +0.0720 [+0.012,+0.132] (Holm p=0.091)",
             transform=ax1.transAxes, ha="center", va="top", fontsize=6.8, color="#1F3864", fontweight="bold",
             bbox={"boxstyle": "round,pad=0.22", "facecolor": "#F4F8FB", "edgecolor": PALETTE["noelim"]})

    # Panel (b): SeungCom revD (9/9) & abl-20261125 (9/9) — ALL COMPLETED
    abl_tot = vdata["fig02_ablation"]["seungcom_abl_total"]
    sc_bars = [
        ("revD-v4", "v4\n(revD)", PALETTE["v4"], vdata["fig02_ablation"]["seungcom_revD_total"]["revD-v4"]),
        ("revD-fullreset", "FullReset\n(revD)", PALETTE["fullreset"], vdata["fig02_ablation"]["seungcom_revD_total"]["revD-fullreset"]),
        ("revD-nodrift", "NoDrift\n(revD)", PALETTE["v1"], vdata["fig02_ablation"]["seungcom_revD_total"]["revD-nodrift"]),
        ("abl-v4", "v4\n(abl)", "#2B8CBE", abl_tot["abl-v4"]),
        ("abl-nodiscount", "γ=1.0\n(abl)", PALETTE["nosettle"], abl_tot["abl-nodiscount"]),
        ("abl-bundle-off", "OffBundle\n(abl)", PALETTE["v2"], abl_tot["abl-bundle-off"]),
    ]
    x_b = np.arange(len(sc_bars))
    mb = [d["mean"] for _, _, _, d in sc_bars]
    cb = [d["ci_half"] for _, _, _, d in sc_bars]
    bb = ax2.bar(x_b, mb, width=0.56, color=[c for _, _, c, _ in sc_bars], edgecolor="#222222", yerr=cb, capsize=3.5)
    ax2.axvline(2.5, color="#888888", linestyle=":", linewidth=1.0)
    for bar, m, c in zip(bb, mb, cb):
        ax2.text(bar.get_x() + bar.get_width() / 2, min(m + c + 0.008, 2.43), f"{m:.3f}", ha="center", va="bottom", fontsize=7.4, fontweight="bold")
    ax2.set_xticks(x_b)
    ax2.set_xticklabels([l for _, l, _, _ in sc_bars], fontsize=7.6)
    ax2.set_ylabel("Overall WAF (mixFYF 250k, n=3)")
    ax2.set_title("(b) SeungCom (i7-7700): revD & Same-Batch abl (n=3)")
    ax2.set_ylim(2.00, 2.50)
    ax2.text(0.51, 0.96, "revD FullReset +0.060 (CI>0) | abl OffBundle +0.124 (Holm p=0.028)\nabl γ=1.0 Honest Null (−0.004, Holm p=1.000)",
             transform=ax2.transAxes, ha="center", va="top", fontsize=6.8, color="#1F3864", fontweight="bold",
             bbox={"boxstyle": "round,pad=0.22", "facecolor": "#F4F8FB", "edgecolor": PALETTE["v4"]})
    fig.suptitle("Full Component Ablation Summary — ALL COMPLETED (Strictly Host-Separated; 95% Student-t CI, n=3)",
                 fontsize=9.8, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig_manifest["fig_full_ablation"] = save_fig(fig, "fig_full_ablation")

    return fig_manifest


# ---------------------------------------------------------------------------
# Excel Styling Helper
# ---------------------------------------------------------------------------
FONT_TITLE = Font(name="Calibri", size=13, bold=True, color="1F3864")
FONT_SUB = Font(name="Calibri", size=10, italic=True, color="44546A")
FONT_SEC = Font(name="Calibri", size=11, bold=True, color="1F3864")
FONT_HDR = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
FONT_DATA = Font(name="Calibri", size=10, color="111111")
FILL_HDR = PatternFill("solid", fgColor="1F4E78")
FILL_ZEBRA = PatternFill("solid", fgColor="F7F9FC")
FILL_OK = PatternFill("solid", fgColor="C6EFCE")
FILL_WARN = PatternFill("solid", fgColor="FFF2CC")
FILL_FAIL = PatternFill("solid", fgColor="FFC7CE")
THIN = Side(border_style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def style_table(ws, r1, r2, c1, c2, num_fmt=None):
    num_fmt = num_fmt or {}
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            cell = ws.cell(r, c)
            cell.border = BORDER
            if r == r1:
                cell.font = FONT_HDR
                cell.fill = FILL_HDR
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            else:
                cell.font = FONT_DATA
                if (r - r1) % 2 == 0:
                    cell.fill = FILL_ZEBRA
                if c in num_fmt:
                    cell.number_format = num_fmt[c]
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                else:
                    cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)


def autofit(ws, max_w=48):
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        mx = 10
        for cell in col:
            val = str(cell.value or "")
            if val.startswith("="):
                mx = max(mx, 12)
            else:
                fl = max((len(x) for x in val.splitlines()), default=0)
                mx = max(mx, min(fl + 3, max_w))
        ws.column_dimensions[col_letter].width = mx


def write_sheet_table(ws, start_row, headers, rows, num_fmt=None):
    for c, h in enumerate(headers, 1):
        ws.cell(start_row, c, h)
    for ri, row in enumerate(rows, start_row + 1):
        for ci, val in enumerate(row, 1):
            ws.cell(ri, ci, val)
    style_table(ws, start_row, start_row + len(rows), 1, len(headers), num_fmt=num_fmt)
    return start_row + len(rows)


# ---------------------------------------------------------------------------
# 1. Extend report/paper-figures/iCAT_Paper_Figures.xlsx with 9 New Sheets
# ---------------------------------------------------------------------------
NEW_SHEETS = [
    "Ablation",
    "Discount-free",
    "NoElim",
    "Online Greedy",
    "Periodic Switching",
    "Random Search",
    "Greedy GC",
    "Experiment Manifest",
    "Data Validity",
]


def extend_master_paper_excel(vdata, greedy_summary, greedy_raw_rows, seung_rs, r4_rows, gamma_rows, commits, comp_rows):
    xlsx_path = PF_DIR / "iCAT_Paper_Figures.xlsx"
    wb = openpyxl.load_workbook(xlsx_path)

    # Remove any prior versions of the 9 new sheets so re-runs are idempotent while preserving the 12 original sheets!
    for s in NEW_SHEETS:
        if s in wb.sheetnames:
            del wb[s]

    # --- Sheet A: Ablation ---
    ws = wb.create_sheet("Ablation")
    ws["A1"] = "Unified Component Ablation Summary (Strictly Host-Separated; Raw-Log Linked)"
    ws["A1"].font = FONT_TITLE
    ws["A2"] = f"Generated: {GENERATED_AT} | GoCom: {REF_GOCOM}@{commits['gocom']} | SeungCom: {REF_MAIN}@{commits['main']}"
    ws["A2"].font = FONT_SUB
    ab_rows = []
    for p, lbl, batch in [
        ("revA-v4", "iCAT-v4 (Control)", "GoCom revA"),
        ("revA-v1", "V1 (NoDrift)", "GoCom revA"),
        ("revB-nosettle", "NoSettle*", "GoCom revB*"),
        ("revB-noelim", "NoElim*", "GoCom revB*"),
        ("revA-v2", "V2 (NoElim+NoSettle)", "GoCom revA"),
    ]:
        st = vdata["fig02_ablation"]["variants"][p]
        wr = vdata["fig02_ablation"]["welch_vs_v4"].get(p)
        ab_rows.append([
            "GoCom (Ryzen 3600XT)", batch, lbl, st["n"], st["mean"], st["sd"], st["ci_half"],
            0.0 if wr is None else wr["delta"],
            "Baseline" if wr is None else f"[{wr['ci_lo']:+.4f}, {wr['ci_hi']:+.4f}]",
            "Baseline" if wr is None else ("CONFIRMED (CI>0)" if wr["excludes_zero"] else "INCONCLUSIVE"),
            f"{REF_GOCOM}:result/{'revA-20261114' if p.startswith('revA') else 'revB-20261122'}/raw/mixFYF-{p}-rep{{1..3}}",
        ])
    for p, lbl in [("revD-v4", "iCAT-v4 (Control)"), ("revD-fullreset", "FullReset (45-arm)"), ("revD-nodrift", "NoDrift (Drift Off)")]:
        st = vdata["fig02_ablation"]["seungcom_revD_total"][p]
        wr = vdata["fig02_ablation"]["seungcom_revD_welch_total"].get(p)
        ab_rows.append([
            "SeungCom (i7-7700)", "SeungCom revD (same-batch)", lbl, st["n"], st["mean"], st["sd"], st["ci_half"],
            0.0 if wr is None else wr["delta"],
            "Baseline" if wr is None else f"[{wr['ci_lo']:+.4f}, {wr['ci_hi']:+.4f}]",
            "Baseline" if wr is None else ("CONFIRMED (Pre-reg CI>0; Holm p=0.072)" if wr["excludes_zero"] else "INCONCLUSIVE (3/3 worse, high SD)"),
            f"{REF_MAIN}:result/revD-20261124/raw/mixFYF-{p}-rep{{1..3}}",
        ])
    for p, lbl in [("revE-v4", "iCAT-v4 (Control)"), ("revE-noelim", "Isolated NoElim (VARIANT=3)"), ("revE-drift12", "Drift Threshold 12.5%")]:
        st = vdata["fig02_ablation"]["gocom_revE_total"][p]
        wr = vdata["fig02_ablation"]["gocom_revE_welch_total"].get(p)
        ab_rows.append([
            "GoCom (Ryzen 3600XT)", "GoCom revE (same-batch)", lbl, st["n"], st["mean"], st["sd"], st["ci_half"],
            0.0 if wr is None else wr["delta"],
            "Baseline" if wr is None else f"[{wr['ci_lo']:+.4f}, {wr['ci_hi']:+.4f}]",
            "Baseline" if wr is None else "CONFIRMED (Welch CI>0; 4-contrast Holm p=0.091)",
            f"{REF_GOCOM}:result/revE-20261125/raw/mixFYF-{p}-rep{{1..3}}",
        ])
    for p, lbl in [("abl-v4", "iCAT-v4 (Control)"), ("abl-nodiscount", "Discount-free MAB (γ=1.0)"), ("abl-bundle-off", "Bundle Off (VARIANT=2)")]:
        st = vdata["fig02_ablation"]["seungcom_abl_total"][p]
        wr = vdata["fig02_ablation"]["seungcom_abl_welch_total"].get(p)
        v_txt = "Baseline" if wr is None else ("CONFIRMED (Welch CI>0, Holm p=0.028)" if wr["excludes_zero"] else "HONEST NULL (No difference found; Holm p=1.000)")
        raw_nm = "abl-off-elim-settle-drift-probe" if p == "abl-bundle-off" else p
        ab_rows.append([
            "SeungCom (i7-7700)", "SeungCom abl (same-batch)", lbl, st["n"], st["mean"], st["sd"], st["ci_half"],
            0.0 if wr is None else wr["delta"],
            "Baseline" if wr is None else f"[{wr['ci_lo']:+.4f}, {wr['ci_hi']:+.4f}]",
            v_txt,
            f"{REF_MAIN}:result/revision-additional-ablation/raw/mixFYF-{raw_nm}-rep{{1..3}}",
        ])
    write_sheet_table(ws, 4, ["Host", "Batch", "Policy", "n", "Mean_WAF", "SD_WAF", "CI95_Half", "Welch_Delta_vs_SameHost_V4", "Welch_CI95", "Verdict", "Raw_Log_Link"], ab_rows, num_fmt={4: "0", 5: "0.0000", 6: "0.0000", 7: "0.0000", 8: "0.0000"})
    autofit(ws)

    # --- Sheet B: Discount-free ---
    ws = wb.create_sheet("Discount-free")
    ws["A1"] = "Discount-free MAB (γ = 1.0) vs. iCAT-v4 (γ = 65503/65536) — COMPLETED (n=3)"
    ws["A1"].font = FONT_TITLE
    ws["A2"] = "Live NVMeVirt SeungCom abl-20261125 COMPLETED (9/9 VALID, triple-verified): Honest Null Δ=−0.0038 [−0.0644, +0.0569] | Theoretical γ^n Strictly Separated Below"
    ws["A2"].font = FONT_SUB
    rv4 = vdata["fig02_ablation"]["seungcom_revD_total"]["revD-v4"]
    abl_v4 = vdata["fig02_ablation"]["seungcom_abl_total"]["abl-v4"]
    abl_nd = vdata["fig02_ablation"]["seungcom_abl_total"]["abl-nodiscount"]
    abl_nd_w = vdata["fig02_ablation"]["seungcom_abl_welch_total"]["abl-nodiscount"]
    df_live = [
        ["[MEASURED]", "SeungCom (i7-7700)", "abl-v4 (γ=0.999496, same-batch)", 3, 3, abl_v4["mean"], abl_v4["sd"], abl_v4["ci_half"], "VALID (Control, PhC 2.4670)", f"{REF_MAIN}@{commits['main']}:result/revision-additional-ablation/raw/mixFYF-abl-v4-rep{{1..3}}"],
        ["[MEASURED]", "SeungCom (i7-7700)", "abl-nodiscount (γ=1.0, same-batch)", 3, 3, abl_nd["mean"], abl_nd["sd"], abl_nd["ci_half"], f"VALID NULL (Δ={abl_nd_w['delta']:+.4f} [{abl_nd_w['ci_lo']:+.4f},{abl_nd_w['ci_hi']:+.4f}], Holm p=1.000)", f"{REF_MAIN}@{commits['main']}:result/revision-additional-ablation/raw/mixFYF-abl-nodiscount-rep{{1..3}}"],
        ["[MEASURED]", "SeungCom (i7-7700)", "revD-v4 (Historical ref)", 3, 3, rv4["mean"], rv4["sd"], rv4["ci_half"], "VALID (Prior day ref; bridge Δ=+0.0004)", f"{REF_MAIN}@{commits['main']}:result/revD-20261124/raw/mixFYF-revD-v4-rep{{1..3}}"],
    ]
    r_end = write_sheet_table(ws, 4, ["Data_Type", "Host", "Policy", "Valid_n", "Target_n", "Mean_WAF", "SD_WAF", "CI95_Half", "Status", "Raw_Log_Link"], df_live, num_fmt={4: "0", 5: "0", 6: "0.0000", 7: "0.0000", 8: "0.0000"})
    ws.cell(r_end + 2, 1, "Table B2. [THEORETICAL CALCULATION — NOT MEASURED WAF] Discount Weight Decay γ^n over Observed mixFYF Windows").font = FONT_SEC
    g_rows = [
        ["[THEORETICAL]", r["policy"], r["rep"], int(r["total_max_windows_per_part"]), float(r["gamma"]), float(r["weight_oldest_after_full_run"]), float(r["effective_window_ratio_pct"]), "report/reanalysis-20261124/r2_discount_gamma.csv"]
        for r in gamma_rows[:12]
    ]
    write_sheet_table(ws, r_end + 3, ["Data_Type", "Policy", "Rep", "Max_Windows", "Gamma", "Oldest_Weight_gamma_n", "Eff_Sample_Ratio_Pct", "Source_Script_CSV"], g_rows, num_fmt={4: "0", 5: "0.000000", 6: "0.0000", 7: "0.00"})
    autofit(ws)

    # --- Sheet C: NoElim ---
    ws = wb.create_sheet("NoElim")
    ws["A1"] = "Candidate Elimination Ablation (Isolated NoElim vs. iCAT-v4) — COMPLETED (Same-Batch GoCom revE, n=3)"
    ws["A1"].font = FONT_TITLE
    ws["A2"] = "GoCom revE-20261125 same-batch isolated NoElim (VARIANT=3, n=3) CONFIRMED: +0.0913 [+0.0296, +0.1530] (Paired CI>0; resolves revB cross-batch caveat!)"
    ws["A2"].font = FONT_SUB
    ne_gc = vdata["fig02_ablation"]["variants"]["revB-noelim"]
    v4_gc = vdata["fig02_ablation"]["variants"]["revA-v4"]
    w_ne = vdata["fig02_ablation"]["welch_vs_v4"]["revB-noelim"]
    re_v4 = vdata["fig02_ablation"]["gocom_revE_total"]["revE-v4"]
    re_ne = vdata["fig02_ablation"]["gocom_revE_total"]["revE-noelim"]
    re_ne_w = vdata["fig02_ablation"]["gocom_revE_welch_total"]["revE-noelim"]
    ne_rows = [
        ["GoCom (Ryzen 3600XT)", "revE-20261125", "revE-v4 (Same-Batch Control)", 3, re_v4["mean"], re_v4["sd"], re_v4["ci_half"], 0.0, "Baseline", "VALID (Same-batch control)", f"{REF_GOCOM}:result/revE-20261125/raw/mixFYF-revE-v4-rep{{1..3}}"],
        ["GoCom (Ryzen 3600XT)", "revE-20261125", "revE-noelim (Isolated VARIANT=3)", 3, re_ne["mean"], re_ne["sd"], re_ne["ci_half"], re_ne_w["delta"], f"[{re_ne_w['ci_lo']:+.4f}, {re_ne_w['ci_hi']:+.4f}]", "CONFIRMED (Welch & Paired CI>0; Holm p=0.091)", f"{REF_GOCOM}:result/revE-20261125/raw/mixFYF-revE-noelim-rep{{1..3}}"],
        ["GoCom (Ryzen 3600XT)", "revA-20261114", "revA-v4 (Prior Control)", 3, v4_gc["mean"], v4_gc["sd"], v4_gc["ci_half"], 0.0, "Baseline", "VALID (Historical ref)", f"{REF_GOCOM}:result/revA-20261114/raw/mixFYF-revA-v4-rep{{1..3}}"],
        ["GoCom (Ryzen 3600XT)", "revB-20261122", "revB-noelim*", 3, ne_gc["mean"], ne_gc["sd"], ne_gc["ci_half"], w_ne["delta"], f"[{w_ne['ci_lo']:+.4f}, {w_ne['ci_hi']:+.4f}]", "VALID (Prior cross-batch*)", f"{REF_GOCOM}:result/revB-20261122/raw/mixFYF-revB-noelim-rep{{1..3}}"],
        ["GoCom (Ryzen 3600XT)", "revB-20261122", "revB-v4 (Bridge)", 1, vdata["fig02_ablation"]["revB_v4_bridge_n1"], "N/A (n=1)", "N/A (n=1)", "N/A", "Bridge +4.8 SD vs revA-v4", "CAVEAT (Resolved by revE)", f"{REF_GOCOM}:result/revB-20261122/raw/mixFYF-revB-v4-rep1"],
    ]
    write_sheet_table(ws, 4, ["Host", "Campaign", "Policy", "n", "Mean_WAF", "SD_WAF", "CI95_Half", "Welch_Delta", "Welch_CI95", "Status", "Raw_Log_Link"], ne_rows, num_fmt={4: "0", 5: "0.0000", 6: "0.0000", 7: "0.0000", 8: "0.0000"})
    autofit(ws)

    # --- Sheet D: Online Greedy ---
    ws = wb.create_sheet("Online Greedy")
    ws["A1"] = "Online Greedy Policy Selection (ICAT_VARIANT=8) vs. iCAT-v4 — COMPLETED (SeungCom n=3)"
    ws["A1"].font = FONT_TITLE
    ws["A2"] = "Triple-verified (SeungCom+GoCom+Home): 3/3 VALID, 0/2,513 argmin rule mismatches. Honest null: Greedy − revD-v4 = −0.0086 [−0.0508, +0.0336] (p=0.54)."
    ws["A2"].font = FONT_SUB
    revC_v4_st = vdata["fig05_parameters"]["live_revC"]["elim15_v4_pct"]
    gr_st = vdata["fig02_ablation"]["seungcom_greedy_total"]
    gr_w_revD = vdata["fig02_ablation"]["seungcom_greedy_welch_vs_revD_total"]
    gr_w_abl = vdata["fig02_ablation"]["seungcom_greedy_welch_vs_abl_total"]
    og_rows = [
        ["SeungCom (i7-7700)", "greedy-20261125", "Online Greedy (VARIANT=8)", 3, 3, gr_st["mean"], gr_st["sd"], gr_st["ci_half"], f"VALID NULL vs revD ({gr_w_revD['delta']:+.4f} [{gr_w_revD['ci_lo']:+.4f},{gr_w_revD['ci_hi']:+.4f}]); 0/2513 rule mismatches", f"{REF_MAIN}@{commits['main']}:result/greedy-20261125/raw/mixFYF-greedy-online-rep{{1..3}}"],
        ["SeungCom (i7-7700)", "revD-20261124", "revD-v4 (Primary Control)", 3, 3, rv4["mean"], rv4["sd"], rv4["ci_half"], "VALID (Primary control, different day)", f"{REF_MAIN}@{commits['main']}:result/revD-20261124/raw/mixFYF-revD-v4-rep{{1..3}}"],
        ["SeungCom (i7-7700)", "abl-20261125", "abl-v4 (Secondary Control)", 3, 3, abl_v4["mean"], abl_v4["sd"], abl_v4["ci_half"], f"VALID (Greedy − abl-v4: {gr_w_abl['delta']:+.4f} [{gr_w_abl['ci_lo']:+.4f},{gr_w_abl['ci_hi']:+.4f}])", f"{REF_MAIN}@{commits['main']}:result/revision-additional-ablation/raw/mixFYF-abl-v4-rep{{1..3}}"],
        ["GoCom (Ryzen 3600XT)", "revC-20261124", "revC-v4 (Different Host Ref)", 3, 3, revC_v4_st["waf"], revC_v4_st["sd"], revC_v4_st["ci_half"], "VALID (Different host — do NOT pool with SeungCom)", f"{REF_GOCOM}@{commits['gocom']}:result/revC-20261124/raw/mixFYF-revC-v4-rep{{1..3}}"],
    ]
    write_sheet_table(ws, 4, ["Host", "Campaign", "Policy", "Valid_n", "Target_n", "Mean_WAF", "SD_WAF", "CI95_Half", "Status", "Raw_Log_Link"], og_rows, num_fmt={4: "0", 5: "0", 6: "0.0000", 7: "0.0000", 8: "0.0000"})
    autofit(ws)

    # --- Sheet E: Periodic Switching ---
    ws = wb.create_sheet("Periodic Switching")
    ws["A1"] = "Periodic Switching (Round-Robin) vs. iCAT-v4 — EXCLUDED BY USER DECISION (Scope Limitation)"
    ws["A1"].font = FONT_TITLE
    ws["A2"] = "User explicitly excluded Periodic Switching & Random Search from additional NVMeVirt experiments. Documented as scope limitation."
    ws["A2"].font = FONT_SUB
    ps_rows = [
        ["GoCom (Ryzen 3600XT)", "revA-20261114", "revA-v4 (Ref)", 3, 3, v4_gc["mean"], v4_gc["sd"], v4_gc["ci_half"], "VALID (Historical ref)", f"{REF_GOCOM}:result/revA-20261114/raw/mixFYF-revA-v4-rep{{1..3}}"],
        ["GoCom (Ryzen 3600XT)", "revA-20261114", "revA-random (Ref)", 3, 3, vdata["fig01_random"]["overall"]["revA-random"]["mean"], vdata["fig01_random"]["overall"]["revA-random"]["sd"], vdata["fig01_random"]["overall"]["revA-random"]["ci_half"], "VALID (Random ref)", f"{REF_GOCOM}:result/revA-20261114/raw/mixFYF-revA-random-rep{{1..3}}"],
        ["Excluded", "User Decision", "Periodic Switching", 0, 0, "EXCLUDED", "EXCLUDED", "EXCLUDED", "EXCLUDED BY USER DECISION (Scope Limitation)", "N/A"],
    ]
    write_sheet_table(ws, 4, ["Host", "Campaign", "Policy", "Valid_n", "Target_n", "Mean_WAF", "SD_WAF", "CI95_Half", "Status", "Raw_Log_Link"], ps_rows, num_fmt={4: "0", 5: "0", 6: "0.0000", 7: "0.0000", 8: "0.0000"})
    autofit(ws)

    # --- Sheet F: Random Search ---
    ws = wb.create_sheet("Random Search")
    ws["A1"] = "Random Search Re-Verification (Strictly Separating [MEASURED] vs. [ESTIMATED])"
    ws["A1"].font = FONT_TITLE
    ws["A2"] = "CRITICAL: Zero live NVMeVirt Random Search executions exist. All Random Search values below are [ESTIMATED] models from verified logs/sweeps."
    ws["A2"].font = FONT_SUB
    rs_t1 = [[r["kind"], r["host"], r["what"], r["n"], float(r["value"]), r["values"], r["source"]] for r in seung_rs]
    r_end = write_sheet_table(ws, 4, ["Data_Type", "Host", "Metric_or_Model", "n_or_Trials", "Value", "Range_or_Reps", "Source_Path"], rs_t1, num_fmt={5: "0.0000"})
    ws.cell(r_end + 2, 1, "Table F2. [ESTIMATED] Exact Combinatorial Random Search E[min W_i] on 3 Verified 60/60 Sweeps (45-arm space, excl. k=2)").font = FONT_SEC
    rs_t2 = [
        ["[ESTIMATED]", r["workload"], int(r["k_random_trials"]), float(r["expected_best_waf"]), float(r["sd_best_waf"]), float(r["optimal_arm_waf"]), float(r["gap_vs_optimal_pct"]), r["raw_data_path"]]
        for r in r4_rows if int(r["N_candidates"]) == 45 and int(r["k_random_trials"]) in (1, 2, 3, 5, 10, 20, 45)
    ]
    write_sheet_table(ws, r_end + 3, ["Data_Type", "Workload", "k_Trials", "Expected_Best_WAF", "SD_Best_WAF", "Optimal_WAF", "Gap_vs_Optimal_Pct", "Raw_Sweep_Path"], rs_t2, num_fmt={3: "0", 4: "0.0000", 5: "0.0000", 6: "0.0000", 7: "0.00"})
    autofit(ws)

    # --- Sheet G: Greedy GC ---
    ws = wb.create_sheet("Greedy GC")
    ws["A1"] = "Existing Greedy GC Re-Verification (47 Runs Audited: 9 Valid Workloads n=3 vs n=3, 16 Invalid Excluded)"
    ws["A1"].font = FONT_TITLE
    ws["A2"] = f"Source: {REF_GOCOM}@{commits['gocom']}:result/mix-20260911/ & {REF_MAIN}@{commits['main']}:result/batchG-20261126/ (mixFYF Greedy GC 3/3 COMPLETED!)"
    ws["A2"].font = FONT_SUB
    gg_rows = []
    for g in greedy_summary:
        w = g["welch_greedy_minus_online"]
        gg_rows.append([
            "SeungCom (i7-7700)", g["workload"], "x1 (valid)",
            g["greedy"]["n"], g["greedy"]["mean"], g["greedy"]["sd"], g["greedy"]["ci_half"],
            g["online"]["n"], g["online"]["mean"], g["online"]["sd"], g["online"]["ci_half"],
            w["delta"], f"[{w['ci_lo']:+.4f}, {w['ci_hi']:+.4f}]", -g["pct_reduction_online_vs_greedy"],
            g["v4_x1_n1"] if g["v4_x1_n1"] is not None else "N/A (x3 only)",
            "VALID (2-path OK)" if g["all_two_path_ok"] else "CHECK",
            f"{REF_GOCOM}:result/mix-20260911/{g['workload']}-{{greedy,online}}-rep{{1..3}}",
        ])
    gg_rows.append(["GoCom (Ryzen 3600XT)", "mixY", "90m", 1, 6.181213, "N/A (n=1)", "N/A (n=1)", 1, 3.298178, "N/A (n=1)", "N/A (n=1)", "N/A (n=1)", "CAT-47 ref only", "N/A", "Host-separated", "VALID (n=1, no CI)", f"{REF_GOCOM}:result/gocom-sg-20261119/mixY-sg-greedy-rep1"])
    gg_rows.append(["SeungCom (i7-7700)", "mixFYF 250k (batchG)", "90m", 3, 2.629343, 0.006924, 0.017200, 3, 2.110472, 0.024395, 0.060602, 0.518871, "[+0.4633, +0.5744]", -19.73, "bg-v4 same-batch n=3", "VALID PASS (Holm p=0.0013; FIO lat lower on Greedy)", f"{REF_MAIN}@{commits['main']}:result/greedygc-20261126/raw/mixFYF-greedygc-rep{{1..3}}"])
    write_sheet_table(ws, 4, [
        "Host", "Workload", "Length", "Greedy_n", "Greedy_Mean", "Greedy_SD", "Greedy_CI95",
        "iCAT_Online_n", "iCAT_Online_Mean", "iCAT_Online_SD", "iCAT_Online_CI95",
        "Welch_Delta", "Welch_CI95", "Online_vs_Greedy_Pct", "iCAT_v4_x1_n1", "Validity", "Raw_Log_Link",
    ], gg_rows, num_fmt={4: "0", 5: "0.0000", 6: "0.0000", 7: "0.0000", 8: "0", 9: "0.0000", 10: "0.0000", 11: "0.0000", 12: "0.0000", 14: "0.00"})
    autofit(ws)

    # --- Sheet H: Experiment Manifest ---
    ws = wb.create_sheet("Experiment Manifest")
    ws["A1"] = "Complete Revision Experiment Manifest (Host, Branch, Commit, SHA256, Workload, Seed, Reps, Validity)"
    ws["A1"].font = FONT_TITLE
    ws["A2"] = f"Synchronized: {GENERATED_AT}"
    ws["A2"].font = FONT_SUB
    write_sheet_table(ws, 4, list(comp_rows[0].keys()), [[r[k] for k in comp_rows[0].keys()] for r in comp_rows])
    autofit(ws)

    # --- Sheet I: Data Validity ---
    ws = wb.create_sheet("Data Validity")
    ws["A1"] = "Independent Data Validity Audit Ledger (Valid vs. Invalid / Excluded Datasets)"
    ws["A1"].font = FONT_TITLE
    ws["A2"] = "Every dataset audited for exit=0, module SHA256, two-path WAF match, FIO err=0, YCSB fail<=1%, SQLITE_FULL=0, kernel errors=0."
    ws["A2"].font = FONT_SUB
    dv_rows = [
        ["revA-20261114 (mixFYF)", "GoCom", REF_GOCOM, commits["gocom"], 13, 13, 0, "VALID", "100% YCSB OK, SQLITE_FULL=0, 2-path WAF exact", "Paper main (E1/E2/E3/E4/E5)"],
        ["revB-20261122 (mixFYF)", "GoCom", REF_GOCOM, commits["gocom"], 8, 8, 0, "VALID (CAVEAT)", "Raw valid; revB-v4 bridge (+4.8 SD) requires cross-batch caveat", "Paper ablation (flag *)"],
        ["revC-20261124 (mixFYF)", "GoCom", REF_GOCOM, commits["gocom"], 15, 15, 0, "VALID (15/15 DONE)", "15/15 valid (all 5 policies n=3, 2-path exact, loadsampler OK); bridge vs revA-v4 = -0.40%", "Paper main (E2/E6/E7)"],
        ["revD-20261124 (mixFYF)", "SeungCom", REF_MAIN, commits["main"], 9, 9, 0, "VALID (9/9 DONE)", "9/9 valid, queue order exact, 3-path WAF exact; triple-verified (SeungCom+GoCom+Home)", "Paper main E1 (completed)"],
        ["resource-v124-20261114", "SeungCom", REF_RES, commits["res"], 12, 12, 0, "VALID", "FIO-Fast 30m n=3 CPU & GC overhead valid", "Paper E5/Fig 4 & 7"],
        ["sweep-20260915 (3x60)", "SeungCom", REF_MAIN, commits["main"], 180, 180, 0, "VALID", "test4, oltp, sqlite-a (87/87 0% fail) valid", "Paper E7/Fig 6 & R4"],
        ["mix-20260911 (mixC/D/F/K/L/M/O/P/Q)", "SeungCom", REF_GOCOM, commits["gocom"], 54, 54, 0, "VALID", "9 non-SQLite/valid-YCSB workloads: Greedy (27) + Online (27) 2-path exact", "Greedy GC re-verification"],
        ["mix-20260911 (mixA/B/H/J/R) & 11-23 mixR", "SeungCom", REF_MAIN, commits["main"], 224, 0, 224, "INVALID (EXCLUDED)", "SQLITE_FULL (8.2–99.8% YCSB fail, exit=0 disguised)", "STRICTLY EXCLUDED"],
        ["mix-20260911 (mixG-*)", "SeungCom", REF_MAIN, commits["main"], 34, 0, 34, "INVALID / UNVERIFIABLE", "0-byte YCSB output logs", "STRICTLY EXCLUDED"],
        ["gc-20261010/mixY-smartgc-rep1", "SeungCom", REF_MAIN, commits["main"], 1, 0, 1, "INVALID (EXCLUDED)", "ENOSPC (No space left on device), empty exit-code", "Use smartgc-20261119/resume"],
        ["gc-20261010/mixY-fixed47-rep1", "SeungCom", REF_MAIN, commits["main"], 1, 1, 0, "OUTLIER (DO NOT MIX)", "Oct-10 WAF 2.864 vs Nov same-module 3.233", "Single reference only"],
        ["abl-20261125 (v4/nodiscount/bundle-off)", "SeungCom", REF_MAIN, commits["main"], 9, 9, 0, "VALID (9/9 DONE)", "Triple-verified! OffBundle +0.1241 (Holm p=0.028); NoDiscount −0.0038 (honest null)", "Paper main M2 (Table 10 row F)"],
        ["revE-20261125 (v4/NoElim-isol/drift12)", "GoCom", REF_GOCOM, commits["gocom"], 9, 9, 0, "VALID (9/9 DONE)", "Same-batch NoElim +0.0913 (Welch/Paired CI>0); drift12 +0.0720 (premature PhB resets; Holm p=0.091)", "Paper main M2/M6 (Table 10 row E)"],
        ["greedy-20261125 (Online Greedy VARIANT=8)", "SeungCom", REF_MAIN, commits["main"], 3, 3, 0, "VALID (3/3 DONE)", "Triple-verified, 0/2,513 argmin rule mismatches; honest null −0.0086 [−0.051, +0.034]", "Paper main M3 (Table 10 row D')"],
        ["m1-20261126 (SmartGC-EQ8 vs iCAT-v4 ktime)", "GoCom", REF_GOCOM, commits["gocom"], 14, 14, 0, "RUNNING (SIM 12/12 + SMOKES 2/2 OK)", "Sim 12/12 OK (iCAT 53.0us vs SmartGC 7.6us/GC, WAF 7.16 vs 9.19); kernel smokes 2/2 OK; main 1/6 running", "Monitoring every 30m (~11-28)"],
    ]
    write_sheet_table(ws, 4, ["Dataset", "Host", "Branch", "Commit", "Audited_Runs", "Valid_Runs", "Invalid_Runs", "Validity_Status", "Audit_Details", "Usage_Policy"], dv_rows, num_fmt={5: "0", 6: "0", 7: "0"})
    for r_i in range(5, 5 + len(dv_rows)):
        st_txt = str(ws.cell(r_i, 8).value)
        if "INVALID" in st_txt:
            ws.cell(r_i, 8).fill = FILL_FAIL
        elif "VALID" in st_txt and "CAVEAT" not in st_txt:
            ws.cell(r_i, 8).fill = FILL_OK
        else:
            ws.cell(r_i, 8).fill = FILL_WARN
    autofit(ws)

    wb.save(xlsx_path)
    print(f"Extended master Excel workbook ({len(wb.sheetnames)} sheets): {xlsx_path}")


# ---------------------------------------------------------------------------
# 2. Build report/revision-final-integration/{revision_progress.xlsx, evidence_matrix.xlsx, experiment_completion_matrix.csv}
# ---------------------------------------------------------------------------
def build_integration_workbooks(vdata, greedy_summary, commits, comp_rows):
    # A. experiment_completion_matrix.csv
    csv_path = OUT_DIR / "experiment_completion_matrix.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(comp_rows[0].keys()))
        w.writeheader()
        w.writerows(comp_rows)

    # B. revision_progress.xlsx
    wb_p = openpyxl.Workbook()
    ws = wb_p.active
    ws.title = "Progress_Overview"
    ws["A1"] = "iCAT Additional Revision Integration — Live Progress Tracker"
    ws["A1"].font = FONT_TITLE
    ws["A2"] = f"Updated: {GENERATED_AT} | SeungCom ({REF_MAIN}@{commits['main']}) | GoCom ({REF_GOCOM}@{commits['gocom']})"
    ws["A2"].font = FONT_SUB
    write_sheet_table(ws, 4, list(comp_rows[0].keys()), [[r[k] for k in comp_rows[0].keys()] for r in comp_rows])
    for r_i in range(5, 5 + len(comp_rows)):
        st_v = str(ws.cell(r_i, 10).value)
        if st_v.startswith("COMPLETED"):
            ws.cell(r_i, 10).fill = FILL_OK
        elif st_v.startswith("RUNNING") or st_v.startswith("PARTIAL"):
            ws.cell(r_i, 10).fill = FILL_WARN
        else:
            ws.cell(r_i, 10).fill = FILL_FAIL
    autofit(ws)

    ws_q = wb_p.create_sheet("Host_Queues")
    ws_q["A1"] = "Per-Host Experiment Queue & Remaining Workload Estimate"
    ws_q["A1"].font = FONT_TITLE
    q_rows = [
        ["SeungCom (i7-7700)", "revD-20261124 (E1: v4/nodrift/fullreset)", 9, 9, 0, 0.0, "COMPLETED (9/9 VALID)", "2026-11-25 06:20 KST"],
        ["SeungCom (i7-7700)", "abl-20261125 (v4/nodiscount/off-elim-settle-drift-probe)", 9, 9, 0, 0.0, "COMPLETED (9/9 VALID, triple-verified)", "2026-11-26 00:52 KST"],
        ["SeungCom (i7-7700)", "greedy-20261125 (Online Greedy VARIANT=8, n=3)", 3, 3, 0, 0.0, "COMPLETED (3/3 VALID, triple-verified)", "2026-11-26 05:34 KST"],
        ["GoCom (Ryzen 3600XT)", "revC-20261124 (v4/elim10/elim25/arm60/online)", 15, 15, 0, 0.0, "COMPLETED (15/15 VALID)", "2026-11-25 14:00 KST"],
        ["GoCom (Ryzen 3600XT)", "revE-20261125 (v4/NoElim-isol/drift12, n=3)", 9, 9, 0, 0.0, "COMPLETED (9/9 VALID)", "2026-11-26 04:08 KST"],
        ["GoCom (Ryzen 3600XT)", "m1-20261126 (SmartGC-EQ8 vs iCAT-v4 ktime + n=3, 6x10h mixY)", 0, 6, 6, 60.0, "RUNNING (sim 12/12 + smokes 2/2 OK; main 1/6 started 04:39)", "~2026-11-28 16:00 KST"],
        ["Excluded", "Periodic Switching & Random Search", 0, 0, 0, 0.0, "EXCLUDED BY USER DECISION", "Scope limitation"],
    ]
    write_sheet_table(ws_q, 4, ["Host", "Campaign", "Completed", "Planned", "Remaining", "Est_Hours_Left", "Status", "ETA"], q_rows, num_fmt={3: "0", 4: "0", 5: "0", 6: "0.0"})
    autofit(ws_q)
    wb_p.save(OUT_DIR / "revision_progress.xlsx")

    # C. evidence_matrix.xlsx (Reviewer M2 & M3 PASS/PARTIAL/FAIL + M1/M4-M7/m5/m6)
    wb_e = openpyxl.Workbook()
    ws_e = wb_e.active
    ws_e.title = "M2_M3_Verdict"
    ws_e["A1"] = "Reviewer M2 & M3 Requirement-Level Evidence Matrix (PASS / PARTIAL / FAIL)"
    ws_e["A1"].font = FONT_TITLE
    ws_e["A2"] = f"As of {GENERATED_AT} | Strict Rule: [ESTIMATED] != [MEASURED]; n<3 != statistical confirmation"
    ws_e["A2"].font = FONT_SUB
    ev_rows = [
        ["M2-1", "M2 (Ablation)", "Candidate Elimination contribution (Isolated NoElim vs V4)", "GoCom revE-20261125 (same-batch n=3) & revB*", "[MEASURED] Same-batch GoCom revE-noelim (VARIANT=3) − revE-v4 = +0.0913 [+0.0296, +0.1530] (Paired [+0.0139,+0.1687]>0, g=3.88, PhC +0.1548); 4-contrast Holm p=0.091 disclosed", "PASS", "COMPLETE (resolves revB cross-batch caveat; disclose Holm sensitivity)"],
        ["M2-2", "M2 (Ablation)", "Settlement contribution (NoSettle / Bundle Off vs V4)", "GoCom revA-v2/revB-nosettle & SeungCom abl-bundle-off (n=3)", "[MEASURED] Bundle Off confirmed on BOTH hosts: GoCom revA-v2 +0.1355 CI>0 & SeungCom abl +0.1241 [+0.073,+0.175] (Holm p=0.028); Isolated NoSettle* CI incl. 0 & coupled in code", "PARTIAL", "Report bundle confirmed on 2 hosts & isolated settlement inconclusive"],
        ["M2-3", "M2 (Ablation)", "Drift detection contribution (NoDrift vs V4)", "SeungCom revD (9/9) & GoCom revA-v1 (n=3)", "[MEASURED] revD 3/3 worse (+0.0681 Tot, +0.1411 PhC, SD 6.7x lower), but Welch CI includes 0 ([-0.040, +0.176]); revA-v1 also CI incl. 0", "PARTIAL", "Honest reporting: 3/3 directional + variance reduction, CI inconclusive at n=3"],
        ["M2-4", "M2 (Ablation)", "Partial re-exploration vs FullReset (FullReset vs V4)", "SeungCom revD (9/9, same-batch n=3)", "[MEASURED] PhC +0.1296 [+0.052, +0.208] (g=3.78, Paired CI>0), Tot +0.0596 [+0.016, +0.103] (g=3.08); Holm sensitivity p=0.060/0.072; triple-verified", "PASS", "Pre-registered Welch CI > 0 confirmed; disclose Holm sensitivity"],
        ["M2-5", "M2 (Ablation)", "Discount factor γ contribution (Discount-free vs V4)", "SeungCom abl-20261125 (9/9 COMPLETED) & R2 theoretical", "[MEASURED] Same-batch abl-nodiscount (γ=1.0) − abl-v4 = −0.0038 [−0.0644, +0.0569] (Holm p=1.000; PhC −0.0099) — honest null matching [THEORETICAL] γ^250=0.882", "PASS", "COMPLETE (honest null finding transparently reported in Table 10 row F)"],
        ["M3-1", "M3 (Baselines)", "Online Random Selection vs V4", "GoCom revA (n=3)", "[MEASURED] revA-Random − revA-v4 = +0.1959 [+0.1840, +0.2078] (-8.43%, Welch & Paired CI>0)", "PASS", "Single host/workload scope noted"],
        ["M3-2", "M3 (Baselines)", "Original iCAT (online) vs V4", "GoCom revC (15/15 COMPLETED, n=3)", "[MEASURED] revC-online (2.3951 ± 0.0029) − revC-v4 (2.1200 ± 0.0294) = +0.2751 [+0.2030, +0.3472] (Paired [+0.1994, +0.3508], g=+10.53)", "PASS", "CONFIRMED (same-batch n=3 Welch & Paired CI > 0)"],
        ["M3-3", "M3 (Baselines)", "Online Greedy (argmin no-UCB, VARIANT=8) vs V4", "SeungCom greedy-20261125 (3/3 COMPLETED, triple-verified)", "[MEASURED] Greedy (2.1300 ± 0.0198, 0/2,513 rule mismatches) − revD-v4 = −0.0086 [−0.0508, +0.0336] (vs abl-v4 −0.0090 [−0.058,+0.040]) — honest null; cannot claim V4 beats Greedy on mixFYF", "PASS", "COMPLETE (honest null finding reported in Table 10 row D'; cross-day caveat noted)"],
        ["M3-4", "M3 (Baselines)", "Periodic Switching (Round-Robin) vs V4", "Excluded by user decision (0/3)", "EXCLUDED BY USER DECISION (not scheduled)", "PARTIAL", "Documented as scope limitation"],
        ["M3-5", "M3 (Baselines)", "Random Search (try k then fix) vs V4", "Excluded by user decision; Offline MC & R4 exact sweep", "[ESTIMATED] mixFYF MC k=1..45: 2.306–2.214 vs V4 2.128 (est bias +0.085); 3x60 sweeps +12.5–17.4% at k=1; live NVMeVirt excluded by user", "PARTIAL", "Strictly label [ESTIMATED]"],
        ["M3-6", "M3 (Baselines)", "Greedy GC baseline vs iCAT", "SeungCom mixC/D/F/K/L/M/O/P/Q (n=3x9); mixY (n=1)", "[MEASURED] 9 valid legacy workloads n=3 vs n=3: iCAT-online beats Greedy by -7.1% to -42.0% (Welch CI>0 in 9/9); mixFYF Greedy NOT RUN", "PARTIAL", "Strong legacy n=3 proof vs iCAT-online; note mixFYF Greedy absent"],
        ["M2-OVERALL", "M2 Summary", "Overall M2 Component Contribution Verdict", "All M2 sub-items (revA/revB/revD/abl/revE)", "3 PASS (Isolated NoElim, Partial FullReset, Discount-free honest null), 2 PARTIAL (Bundle PASS / isolated NoSettle & NoDrift CI incl. 0)", "PASS", "All planned M2 experiments completed & triple-verified"],
        ["M3-OVERALL", "M3 Summary", "Overall M3 Baseline Comparison Verdict", "All M3 sub-items (revA/revC/greedy)", "3 PASS (Random Sel. +, Original iCAT +, Online Greedy honest null), 3 PARTIAL (Periodic/Random Search user-excluded, Greedy GC legacy)", "PASS", "All approved M3 experiments completed & triple-verified"],
    ]
    write_sheet_table(ws_e, 4, ["Req_ID", "Reviewer_Item", "Requirement", "Data_Source", "Verified_Evidence_Summary", "Verdict", "Action_to_PASS"], ev_rows)
    for r_i in range(5, 5 + len(ev_rows)):
        v = str(ws_e.cell(r_i, 6).value)
        ws_e.cell(r_i, 6).fill = FILL_OK if v == "PASS" else (FILL_WARN if v == "PARTIAL" else FILL_FAIL)
    autofit(ws_e)

    ws_o = wb_e.create_sheet("Other_Review_Items")
    ws_o["A1"] = "Status of Remaining Reviewer Items (M1, M4, M5, M6/m6, m5, M7)"
    ws_o["A1"].font = FONT_TITLE
    o_rows = [
        ["M1", "SmartGC Comparison (CPU/Mem/WAF/n=3)", "RUNNING (m1-20261126)", "GoCom m1-20261126 running (sim 12/12 OK: iCAT 53.0us vs SmartGC 7.6us/GC, WAF 7.16 vs 9.19; kernel smokes 2/2 OK; main 6x10h mixY 1/6 started 04:39)"],
        ["M4", "Statistical Reliability (E4)", "PARTIAL (mixFYF 66/66 PASS)", "revA/B/C/D/abl/revE/greedy (66 runs) all n=3 + Welch/Paired/Holm; legacy Table 6/7/9 n=1 & draft placeholders remain"],
        ["M5", "CPU, Memory & I/O Efficiency (E5)", "PARTIAL (m1 RUNNING)", "Memory 193x (sizeof), iCAT separated CPU (reward 1.44ms, choose 1.27ms, set_arm 0.059ms, on_gc net 9.43ns, do_gc 206.8s) integrated; SmartGC ktime running in m1-20261126"],
        ["M6/m6", "Adaptation Speed (E3) & Parameters (E6)", "PARTIAL (ELIM/DRIFT12 PASS)", "E6 ELIM 10%/15%/25% (revC n=3) & DRIFT 12.5% vs 25% (revE n=3: +0.0720 CI>0, premature PhB resets) COMPLETED; window/50%/settle/probe unexecuted (limitations)"],
        ["m5", "Candidate Space 60->45 (E7)", "PASS", "3x60 full sweeps valid (k=2 worst) + live revC 60 vs 45 COMPLETED (n=3 vs n=3: Δ=+0.0282 [-0.032, +0.089], CI incl. 0)"],
        ["M7", "Environment Generalization (E8)", "PAPER LIMITATION", "Single NVMeVirt 8GiB/OP 7%/erase=0 setup only; explicitly disclosed in Limitations section"],
    ]
    write_sheet_table(ws_o, 4, ["Item", "Topic", "Verdict", "Current_Evidence_and_Status"], o_rows)
    autofit(ws_o)
    wb_e.save(OUT_DIR / "evidence_matrix.xlsx")
    print(f"Saved integration workbooks & CSV in {OUT_DIR}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    setup_matplotlib()
    commits = {
        "main": git_rev(REF_MAIN),
        "gocom": git_rev(REF_GOCOM),
        "res": git_rev(REF_RES),
    }
    vdata = json.loads((PF_DIR / "verified_plot_data.json").read_text(encoding="utf-8"))
    greedy_summary, greedy_raw_rows, mixy_refs = load_greedy_verification(REF_GOCOM)
    seung_rs, r4_rows = load_random_search_data(REF_MAIN)
    gamma_rows = load_gamma_data()

    # Build unified completion matrix rows
    comp_rows = [
        {"exp_id": "E1-revD-v4", "host": "SeungCom (i7-7700)", "branch": REF_MAIN, "commit": commits["main"], "module_sha256": "b3577505...5ff32d6", "workload": "mixFYF 250k (1800s x3)", "seeds": "20260911-13", "valid_n": 3, "target_n": 3, "status": "COMPLETED (VALID)", "mean_waf": f"{vdata['fig02_ablation']['seungcom_revD_total']['revD-v4']['mean']:.4f}", "sd_or_note": f"SD {vdata['fig02_ablation']['seungcom_revD_total']['revD-v4']['sd']:.4f}", "data_type": "[MEASURED]"},
        {"exp_id": "E1-revD-nodrift", "host": "SeungCom (i7-7700)", "branch": REF_MAIN, "commit": commits["main"], "module_sha256": "4c267cd5...9dac86", "workload": "mixFYF 250k (1800s x3)", "seeds": "20260911-13", "valid_n": 3, "target_n": 3, "status": "COMPLETED (VALID)", "mean_waf": f"{vdata['fig02_ablation']['seungcom_revD_total']['revD-nodrift']['mean']:.4f}", "sd_or_note": f"SD {vdata['fig02_ablation']['seungcom_revD_total']['revD-nodrift']['sd']:.4f}", "data_type": "[MEASURED]"},
        {"exp_id": "E1-revD-fullreset", "host": "SeungCom (i7-7700)", "branch": REF_MAIN, "commit": commits["main"], "module_sha256": "5a34cb84...efbe9a2", "workload": "mixFYF 250k (1800s x3)", "seeds": "20260911-13", "valid_n": 3, "target_n": 3, "status": "COMPLETED (VALID)", "mean_waf": f"{vdata['fig02_ablation']['seungcom_revD_total']['revD-fullreset']['mean']:.4f}", "sd_or_note": f"SD {vdata['fig02_ablation']['seungcom_revD_total']['revD-fullreset']['sd']:.4f}", "data_type": "[MEASURED]"},
        {"exp_id": "M2-abl-v4", "host": "SeungCom (i7-7700)", "branch": REF_MAIN, "commit": commits["main"], "module_sha256": "b3577505...5ff32d6", "workload": "mixFYF 250k (1800s x3)", "seeds": "20260911-13", "valid_n": 3, "target_n": 3, "status": "COMPLETED (VALID)", "mean_waf": f"{vdata['fig02_ablation']['seungcom_abl_total']['abl-v4']['mean']:.4f}", "sd_or_note": f"SD {vdata['fig02_ablation']['seungcom_abl_total']['abl-v4']['sd']:.4f} (triple-verified)", "data_type": "[MEASURED]"},
        {"exp_id": "M2-Discount-free", "host": "SeungCom (i7-7700)", "branch": REF_MAIN, "commit": commits["main"], "module_sha256": "b26b914c...82241", "workload": "mixFYF 250k (1800s x3)", "seeds": "20260911-13", "valid_n": 3, "target_n": 3, "status": "COMPLETED (VALID NULL)", "mean_waf": f"{vdata['fig02_ablation']['seungcom_abl_total']['abl-nodiscount']['mean']:.4f}", "sd_or_note": f"SD {vdata['fig02_ablation']['seungcom_abl_total']['abl-nodiscount']['sd']:.4f} (Welch −0.0038, Holm p=1.000)", "data_type": "[MEASURED]"},
        {"exp_id": "M2-Bundle-Off (VARIANT=2)", "host": "SeungCom (i7-7700)", "branch": REF_MAIN, "commit": commits["main"], "module_sha256": "b35924ab...547140", "workload": "mixFYF 250k (1800s x3)", "seeds": "20260911-13", "valid_n": 3, "target_n": 3, "status": "COMPLETED (VALID)", "mean_waf": f"{vdata['fig02_ablation']['seungcom_abl_total']['abl-bundle-off']['mean']:.4f}", "sd_or_note": f"SD {vdata['fig02_ablation']['seungcom_abl_total']['abl-bundle-off']['sd']:.4f} (Welch +0.1241, Holm p=0.028)", "data_type": "[MEASURED]"},
        {"exp_id": "E1/E2-revA (v4/v1/v2/rand)", "host": "GoCom (Ryzen 3600XT)", "branch": REF_GOCOM, "commit": commits["gocom"], "module_sha256": "modules.sha256 (verified)", "workload": "mixFYF 250k (1800s x3)", "seeds": "20260911-13", "valid_n": 13, "target_n": 13, "status": "COMPLETED (VALID)", "mean_waf": "v4 2.1284 / rand 2.3243", "sd_or_note": "Welch +0.1959 CI>0", "data_type": "[MEASURED]"},
        {"exp_id": "E1/E7-revB (noelim/nosettle)", "host": "GoCom (Ryzen 3600XT)", "branch": REF_GOCOM, "commit": commits["gocom"], "module_sha256": "modules.sha256 (verified)", "workload": "mixFYF 250k (1800s x3)", "seeds": "20260911-13", "valid_n": 8, "target_n": 8, "status": "COMPLETED (CAVEAT*)", "mean_waf": "noelim 2.2226 / nosettle 2.2152", "sd_or_note": "Bridge +4.8 SD (resolved by revE)", "data_type": "[MEASURED]"},
        {"exp_id": "E6-revC-elim10", "host": "GoCom (Ryzen 3600XT)", "branch": REF_GOCOM, "commit": commits["gocom"], "module_sha256": "186ee2c9...00c6043", "workload": "mixFYF 250k (1800s x3)", "seeds": "20260911-13", "valid_n": 3, "target_n": 3, "status": "COMPLETED (VALID)", "mean_waf": f"{vdata['fig05_parameters']['live_revC']['elim10_pct']['waf']:.4f}", "sd_or_note": f"SD {vdata['fig05_parameters']['live_revC']['elim10_pct']['sd']:.4f} (Welch +0.0238, CI incl. 0)", "data_type": "[MEASURED]"},
        {"exp_id": "E6-revC-elim25", "host": "GoCom (Ryzen 3600XT)", "branch": REF_GOCOM, "commit": commits["gocom"], "module_sha256": "606acc41...df4c1597", "workload": "mixFYF 250k (1800s x3)", "seeds": "20260911-13", "valid_n": 3, "target_n": 3, "status": "COMPLETED (VALID)", "mean_waf": f"{vdata['fig05_parameters']['live_revC']['elim25_pct']['waf']:.4f}", "sd_or_note": f"SD {vdata['fig05_parameters']['live_revC']['elim25_pct']['sd']:.4f} (Welch +0.0507, CI incl. 0)", "data_type": "[MEASURED]"},
        {"exp_id": "E6/E7-revC-v4", "host": "GoCom (Ryzen 3600XT)", "branch": REF_GOCOM, "commit": commits["gocom"], "module_sha256": "df2be251...4224d7", "workload": "mixFYF 250k (1800s x3)", "seeds": "20260911-13", "valid_n": 3, "target_n": 3, "status": "COMPLETED (VALID)", "mean_waf": f"{vdata['fig05_parameters']['live_revC']['elim15_v4_pct']['waf']:.4f}", "sd_or_note": f"SD {vdata['fig05_parameters']['live_revC']['elim15_v4_pct']['sd']:.4f} (Bridge vs revA -0.40%)", "data_type": "[MEASURED]"},
        {"exp_id": "E7-revC-arm60", "host": "GoCom (Ryzen 3600XT)", "branch": REF_GOCOM, "commit": commits["gocom"], "module_sha256": "b2a19db3...81e6d", "workload": "mixFYF 250k (1800s x3)", "seeds": "20260911-13", "valid_n": 3, "target_n": 3, "status": "COMPLETED (VALID)", "mean_waf": f"{vdata['fig06_candidates']['live_revC_60vs45']['revC_arm60_n3']['mean']:.4f}", "sd_or_note": f"SD {vdata['fig06_candidates']['live_revC_60vs45']['revC_arm60_n3']['sd']:.4f} (Welch +0.0282, CI incl. 0)", "data_type": "[MEASURED]"},
        {"exp_id": "E2-revC-online", "host": "GoCom (Ryzen 3600XT)", "branch": REF_GOCOM, "commit": commits["gocom"], "module_sha256": "44675657...2529a9e5", "workload": "mixFYF 250k (1800s x3)", "seeds": "20260911-13", "valid_n": 3, "target_n": 3, "status": "COMPLETED (VALID)", "mean_waf": f"{vdata['fig05_parameters']['live_revC']['online_orig']['waf']:.4f}", "sd_or_note": f"SD {vdata['fig05_parameters']['live_revC']['online_orig']['sd']:.4f} (Welch +0.2751 CI>0, g=10.53)", "data_type": "[MEASURED]"},
        {"exp_id": "M2-revE-v4", "host": "GoCom (Ryzen 3600XT)", "branch": REF_GOCOM, "commit": commits["gocom"], "module_sha256": "df2be251...4224d7", "workload": "mixFYF 250k (1800s x3)", "seeds": "20260911-13", "valid_n": 3, "target_n": 3, "status": "COMPLETED (VALID)", "mean_waf": f"{vdata['fig02_ablation']['gocom_revE_total']['revE-v4']['mean']:.4f}", "sd_or_note": f"SD {vdata['fig02_ablation']['gocom_revE_total']['revE-v4']['sd']:.4f} (Bridge vs revA -0.70%)", "data_type": "[MEASURED]"},
        {"exp_id": "M2-revE-NoElim-isol (VARIANT=3)", "host": "GoCom (Ryzen 3600XT)", "branch": REF_GOCOM, "commit": commits["gocom"], "module_sha256": "b1663b47...29fa7", "workload": "mixFYF 250k (1800s x3)", "seeds": "20260911-13", "valid_n": 3, "target_n": 3, "status": "COMPLETED (VALID)", "mean_waf": f"{vdata['fig02_ablation']['gocom_revE_total']['revE-noelim']['mean']:.4f}", "sd_or_note": f"SD {vdata['fig02_ablation']['gocom_revE_total']['revE-noelim']['sd']:.4f} (Welch +0.0913 CI>0, Paired>0; Holm p=0.091)", "data_type": "[MEASURED]"},
        {"exp_id": "M6-revE-drift12 (12.5%)", "host": "GoCom (Ryzen 3600XT)", "branch": REF_GOCOM, "commit": commits["gocom"], "module_sha256": "f6a02e98...726361", "workload": "mixFYF 250k (1800s x3)", "seeds": "20260911-13", "valid_n": 3, "target_n": 3, "status": "COMPLETED (VALID)", "mean_waf": f"{vdata['fig02_ablation']['gocom_revE_total']['revE-drift12']['mean']:.4f}", "sd_or_note": f"SD {vdata['fig02_ablation']['gocom_revE_total']['revE-drift12']['sd']:.4f} (Welch +0.0720 CI>0, premature PhB resets)", "data_type": "[MEASURED]"},
        {"exp_id": "M3-Online-Greedy (VARIANT=8)", "host": "SeungCom (i7-7700)", "branch": REF_MAIN, "commit": commits["main"], "module_sha256": "4df03c90...7262eec", "workload": "mixFYF 250k (1800s x3)", "seeds": "20260911-13", "valid_n": 3, "target_n": 3, "status": "COMPLETED (VALID NULL)", "mean_waf": f"{vdata['fig02_ablation']['seungcom_greedy_total']['mean']:.4f}", "sd_or_note": f"SD {vdata['fig02_ablation']['seungcom_greedy_total']['sd']:.4f} (0/2513 mismatches; vs revD-v4 −0.0086 null)", "data_type": "[MEASURED]"},
        {"exp_id": "M1/M5-m1-20261126 (SmartGC vs V4)", "host": "GoCom (Ryzen 3600XT)", "branch": REF_GOCOM, "commit": commits["gocom"], "module_sha256": "23d0561f / d609dcdd", "workload": "mixY 10h (n=3) + zones sim", "seeds": "rep1-3", "valid_n": 0, "target_n": 6, "status": "RUNNING (SIM 12/12 + SMOKES 2/2 OK)", "mean_waf": "PENDING (1/6 running)", "sd_or_note": "Sim: iCAT 53.0us vs SmartGC 7.6us/GC (WAF 7.16 vs 9.19)", "data_type": "[RUNNING]"},
        {"exp_id": "M3-Periodic-Switching", "host": "Excluded", "branch": "N/A", "commit": "N/A", "module_sha256": "N/A", "workload": "mixFYF 250k", "seeds": "N/A", "valid_n": 0, "target_n": 0, "status": "EXCLUDED (USER DECISION)", "mean_waf": "N/A", "sd_or_note": "Explicitly excluded by user", "data_type": "[EXCLUDED]"},
        {"exp_id": "M3-Random-Search", "host": "Offline Model (Excluded live)", "branch": REF_MAIN, "commit": commits["main"], "module_sha256": "N/A (Model)", "workload": "mixFYF MC + 3x60 Sweeps", "seeds": "20261125 / Exact", "valid_n": 0, "target_n": 0, "status": "PARTIAL (MODEL ONLY / EXCLUDED LIVE)", "mean_waf": "MC 2.214-2.306", "sd_or_note": "NOT live NVMeVirt (excluded by user)", "data_type": "[ESTIMATED]"},
        {"exp_id": "M3-Greedy-GC-Legacy", "host": "SeungCom (i7-7700)", "branch": REF_GOCOM, "commit": commits["gocom"], "module_sha256": "nvmev-greedy-m.ko", "workload": "9 valid mixC/D/F/K/L/M/O/P/Q (x1)", "seeds": "Sep-2026 rep1-3", "valid_n": 27, "target_n": 27, "status": "COMPLETED (VALID LEGACY)", "mean_waf": "-7.1% to -42.0% vs online", "sd_or_note": "9/9 Welch CI>0; mixFYF 0/3", "data_type": "[MEASURED]"},
    ]

    fig_manifest = build_comparison_figures(vdata, greedy_summary, mixy_refs, seung_rs, r4_rows, gamma_rows)
    extend_master_paper_excel(vdata, greedy_summary, greedy_raw_rows, seung_rs, r4_rows, gamma_rows, commits, comp_rows)
    build_integration_workbooks(vdata, greedy_summary, commits, comp_rows)

    # Save JSON summary of greedy verification & manifest for automated audit
    (OUT_DIR / "integration_audit_summary.json").write_text(
        json.dumps({
            "generated_at": GENERATED_AT,
            "commits": commits,
            "figures": fig_manifest,
            "greedy_valid_workloads": [
                {
                    "workload": g["workload"],
                    "greedy_mean": round(g["greedy"]["mean"], 6),
                    "greedy_sd": round(g["greedy"]["sd"], 6),
                    "greedy_ci": round(g["greedy"]["ci_half"], 6),
                    "online_mean": round(g["online"]["mean"], 6),
                    "online_sd": round(g["online"]["sd"], 6),
                    "online_ci": round(g["online"]["ci_half"], 6),
                    "pct_reduction": round(g["pct_reduction_online_vs_greedy"], 2),
                    "welch_excludes_zero": g["welch_greedy_minus_online"]["excludes_zero"],
                    "v4_x1_n1": round(g["v4_x1_n1"], 6) if g["v4_x1_n1"] else None,
                }
                for g in greedy_summary
            ],
        }, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print("ALL FINAL INTEGRATION ARTIFACTS BUILT SUCCESSFULLY.")


if __name__ == "__main__":
    main()
