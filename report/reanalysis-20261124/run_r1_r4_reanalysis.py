#!/usr/bin/env python3
"""
Home PC Zero-Cost Reanalysis Suite (R1-R4) + revB/revC Environment Comparison
Strictly read-only against immutable Git refs. Zero NVMeVirt execution.
Zero modification to existing raw logs or result files.

Outputs under report/reanalysis-20261124/:
  - r1_adaptation_runs.csv / r1_adaptation_summary.csv
  - r2_discount_gamma.csv
  - r3_io_latency_runs.csv / r3_io_latency_summary.csv
  - r4_random_search_expectation.csv
  - revB_vs_revC_env_audit.csv
  - reanalysis_summary.json
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

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent
OUT_DIR.mkdir(parents=True, exist_ok=True)

SCRIPT_REL = "report/reanalysis-20261124/run_r1_r4_reanalysis.py"
REF_GOCOM = "origin/report/data-validity-20261124"
REF_MAIN = "origin/main"
REF_RES = "origin/resource-overhead-20261114"
KST = timezone(timedelta(hours=9))
GENERATED_AT = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST")

# Pre-registered constants verbatim from analysis/revision/recovery.py
TOL, ROLL, HOLD = 1.05, 10, 20

# Exact gamma from revA-src/conv_ftl.h
WATGC_V2_GAMMA_Q16 = 65503
GAMMA = WATGC_V2_GAMMA_Q16 / 65536.0
HALF_LIFE_WINDOWS = math.log(0.5) / math.log(GAMMA)


def git_rev(ref: str) -> str:
    return subprocess.run(["git", "rev-parse", "--short=9", ref], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.strip()


def git_show(ref_path: str, binary: bool = False):
    p = subprocess.run(["git", "show", ref_path], cwd=REPO_ROOT, capture_output=True)
    if p.returncode != 0:
        return None
    return p.stdout if binary else p.stdout.decode("utf-8", errors="replace")


# Pure-Python exact Student-t 95% critical value
def _betacf(a, b, x):
    MAXIT, EPS, FPMIN = 200, 3e-12, 1e-30
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (FPMIN if abs(d) < FPMIN else d)
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (FPMIN if abs(d) < FPMIN else d)
        c = 1.0 + aa / c
        c = FPMIN if abs(c) < FPMIN else c
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (FPMIN if abs(d) < FPMIN else d)
        c = 1.0 + aa / c
        c = FPMIN if abs(c) < FPMIN else c
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < EPS:
            break
    return h


def _betainc(a, b, x):
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def t_crit_95(df: float) -> float:
    lo, hi = 1.0, 200.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        p = _betainc(df / 2.0, 0.5, df / (df + mid * mid))
        if p > 0.05:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def stat_summary(vals):
    vals = [float(v) for v in vals if v is not None]
    n = len(vals)
    if n == 0:
        return {"n": 0, "mean": None, "sd": None, "ci_lo": None, "ci_hi": None}
    m = float(np.mean(vals))
    if n < 3:
        sd = float(np.std(vals, ddof=1)) if n == 2 else None
        return {"n": n, "mean": m, "sd": sd, "ci_lo": None, "ci_hi": None}
    sd = float(np.std(vals, ddof=1))
    h = t_crit_95(n - 1) * sd / math.sqrt(n)
    return {"n": n, "mean": m, "sd": sd, "ci_lo": m - h, "ci_hi": m + h}


def welch_diff(a, b):
    """a - b Welch 95% CI (requires both n >= 3)."""
    a = [float(x) for x in a if x is not None]
    b = [float(x) for x in b if x is not None]
    if len(a) < 3 or len(b) < 3:
        return None
    ma, mb = float(np.mean(a)), float(np.mean(b))
    va, vb = float(np.var(a, ddof=1)), float(np.var(b, ddof=1))
    se2 = va / len(a) + vb / len(b)
    d = ma - mb
    if se2 == 0:
        return {"delta": d, "ci_lo": d, "ci_hi": d, "excludes_zero": d != 0}
    df = (se2 ** 2) / ((va / len(a)) ** 2 / (len(a) - 1) + (vb / len(b)) ** 2 / (len(b) - 1))
    h = t_crit_95(df) * math.sqrt(se2)
    return {"delta": d, "ci_lo": d - h, "ci_hi": d + h, "excludes_zero": (d - h > 0) or (d + h < 0)}


def write_csv(path: Path, rows: list):
    if not rows:
        return
    keys = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


# ---------------------------------------------------------------------------
# Pre-registered recovery() verbatim from analysis/revision/recovery.py
# ---------------------------------------------------------------------------
def compute_recovery(series_pts, t0, t1):
    pts = [x for x in series_pts if t0 <= x[0] <= t1]
    if len(pts) < ROLL + HOLD + 2:
        return None, (None, False, None, False), None
    waf = lambda a, b: 1.0 + (b[2] - a[2]) / max(b[1] - a[1], 1)
    half = [x for x in pts if x[0] >= (t0 + t1) / 2.0]
    ref = waf(half[0], half[-1])
    roll = [(pts[i][0], waf(pts[i - ROLL], pts[i])) for i in range(ROLL, len(pts))]

    def first(ok):
        for i, (t, w) in enumerate(roll):
            if i + HOLD < len(roll) and all(ok(x[1]) for x in roll[i:i + HOLD + 1]):
                return t - t0, (i == 0)
        return None, False

    one, f1 = first(lambda w: w <= ref * TOL)
    two, f2 = first(lambda w: abs(w / ref - 1.0) <= TOL - 1.0)
    return ref, (one, f1, two, f2), waf(pts[0], pts[-1])


def parse_series_git(ref: str, run_dir: str):
    txt = git_show(f"{ref}:{run_dir}/control-series.txt") or ""
    out = []
    for l in txt.splitlines():
        m = re.match(r"(\d+) .*host_pages=(\d+) gc_pages=(\d+)", l)
        if m:
            out.append((int(m[1]), int(m[2]), int(m[3])))
    return out


def parse_phase_times_git(ref: str, run_dir: str):
    out = {}
    for p in ["A", "B", "C"]:
        ts = git_show(f"{ref}:{run_dir}/phase-{p}-start.time")
        te = git_show(f"{ref}:{run_dir}/phase-{p}-end.time")
        if ts and te:
            out[p] = (datetime.fromisoformat(ts.strip()).timestamp(), datetime.fromisoformat(te.strip()).timestamp())
    return out


def parse_kernel_events_git(ref: str, run_dir: str):
    """Separate detection, re-exploration, and settlement times strictly using kernel.log clock."""
    kl = git_show(f"{ref}:{run_dir}/kernel.log") or ""
    start = {}
    end = {}
    ev = []
    for l in kl.splitlines():
        ms = re.match(r"\[\s*([\d.]+)\].*phase=(\w+) START", l)
        if ms:
            start[ms[2]] = float(ms[1])
            continue
        me = re.match(r"\[\s*([\d.]+)\].*phase=(\w+) END", l)
        if me:
            end[me[2]] = float(me[1])
            continue
        mv = re.match(r"\[\s*([\d.]+)\] NVMeVirt: WATGC_V\d (reset|shift-reset|settled|sample) .*part=(\d)", l)
        if mv:
            ev.append((float(mv[1]), mv[2], int(mv[3])))

    names = sorted(start, key=start.get)
    res = {}
    for j, p in enumerate(names):
        t0 = start[p]
        t1 = end.get(p, start[names[j + 1]] if j + 1 < len(names) else 1e18)
        e = [x for x in ev if t0 <= x[0] <= t1]
        resets = [x for x in e if x[1] in ("reset", "shift-reset")]
        settled = [x for x in e if x[1] == "settled"]
        samples = [x for x in e if x[1] == "sample"]

        # Partition-level counts
        win_by_part = {pt: sum(1 for x in samples if x[2] == pt) for pt in range(4)}

        # 1. Detection time: phase START -> earliest reset
        detect_s = (min(x[0] for x in resets) - t0) if resets else None
        detect_parts = sorted(set(x[2] for x in resets))

        # 2. Re-exploration duration: reset -> first settled AFTER reset (both earliest across all parts & per-part mean)
        reexplore_s = None
        explore_windows = None
        reexplore_per_part = []
        settle_after_reset_from_start_s = None
        if resets:
            r0 = min(x[0] for x in resets)
            st_after = [x[0] for x in settled if x[0] > r0]
            if st_after:
                first_st = min(st_after)
                reexplore_s = first_st - r0
                settle_after_reset_from_start_s = first_st - t0
                explore_windows = sum(1 for x in samples if r0 < x[0] <= first_st)
            else:
                explore_windows = sum(1 for x in samples if x[0] > r0)
            for pt in detect_parts:
                r_pt = min(x[0] for x in resets if x[2] == pt)
                st_pt = [x[0] for x in settled if x[2] == pt and x[0] > r_pt]
                if st_pt:
                    reexplore_per_part.append(min(st_pt) - r_pt)

        # 3. Settlement time from phase START (initial settlement in Phase A; post-reset in Phase C if reset occurred)
        first_settle_from_start_s = (min(x[0] for x in settled) - t0) if settled else None
        settle_per_part_from_start = []
        for pt in range(4):
            st_pt = [x[0] for x in settled if x[2] == pt]
            if st_pt:
                settle_per_part_from_start.append(min(st_pt) - t0)

        res[p] = {
            "resets_count": len(resets),
            "reset_parts": len(detect_parts),
            "detect_s": detect_s,
            "reexplore_earliest_s": reexplore_s,
            "reexplore_part_mean_s": float(np.mean(reexplore_per_part)) if reexplore_per_part else None,
            "reexplore_parts_settled": len(reexplore_per_part),
            "explore_windows_post_reset": explore_windows,
            "settle_from_start_earliest_s": settle_after_reset_from_start_s if resets else first_settle_from_start_s,
            "settle_from_start_part_mean_s": float(np.mean(settle_per_part_from_start)) if (not resets and settle_per_part_from_start) else None,
            "settled_events_count": len(settled),
            "windows_total_4parts": len(samples),
            "windows_per_part_max": max(win_by_part.values()) if win_by_part else 0,
            "windows_per_part_mean": float(np.mean(list(win_by_part.values()))) if win_by_part else 0.0,
        }
    return res


def parse_fio_latency_git(ref: str, run_dir: str, phase_file: str):
    """Extract per-job and IOPS-weighted mean clat (us) from FIO json."""
    txt = git_show(f"{ref}:{run_dir}/{phase_file}")
    if not txt:
        return None
    d = json.loads(txt)
    out = {}
    tot_io = 0
    weighted_mean_ns = 0.0
    for j in d.get("jobs", []):
        name = j["jobname"]
        w = j["write"]
        ios = w.get("total_ios", 0)
        mean_ns = w["clat_ns"]["mean"]
        pct = w["clat_ns"].get("percentile", {})
        tot_io += ios
        weighted_mean_ns += mean_ns * ios
        out[name] = {
            "iops": w["iops"],
            "mean_us": mean_ns / 1000.0,
            "p50_us": pct.get("50.000000", 0) / 1000.0,
            "p95_us": pct.get("95.000000", 0) / 1000.0,
            "p99_us": pct.get("99.000000", 0) / 1000.0,
            "p999_us": pct.get("99.900000", 0) / 1000.0,
        }
    out["weighted_mean_us"] = (weighted_mean_ns / tot_io / 1000.0) if tot_io > 0 else None
    out["total_iops"] = sum(v["iops"] for k, v in out.items() if isinstance(v, dict))
    return out


def parse_ycsb_latency_git(ref: str, run_dir: str):
    yb = git_show(f"{ref}:{run_dir}/ycsb-run-B.txt.gz", binary=True)
    if not yb:
        return None
    yt = gzip.decompress(yb).decode("utf-8", errors="replace")
    def get_val(sec, key):
        m = re.search(rf"\[{re.escape(sec)}\],\s*{re.escape(key)},\s*([\d.]+)", yt)
        return float(m[1]) if m else None
    return {
        "throughput_ops_s": get_val("OVERALL", "Throughput(ops/sec)"),
        "read_ops": get_val("READ", "Operations"),
        "read_avg_us": get_val("READ", "AverageLatency(us)"),
        "read_p95_us": get_val("READ", "95thPercentileLatency(us)"),
        "read_p99_us": get_val("READ", "99thPercentileLatency(us)"),
        "update_ops": get_val("UPDATE", "Operations"),
        "update_avg_us": get_val("UPDATE", "AverageLatency(us)"),
        "update_p95_us": get_val("UPDATE", "95thPercentileLatency(us)"),
        "update_p99_us": get_val("UPDATE", "99thPercentileLatency(us)"),
    }


def exact_k_random_search_stats(sorted_wafs: list, k: int):
    """Exact expectation and SD of min(k draws without replacement) from sorted_wafs."""
    N = len(sorted_wafs)
    if k > N or k < 1:
        return None
    denom = math.comb(N, k)
    probs = []
    for idx in range(N - k + 1):
        # idx is 0-based; rank r = idx + 1; remaining items strictly worse = N - (idx + 1)
        p = math.comb(N - idx - 1, k - 1) / denom
        probs.append((sorted_wafs[idx], p))
    mean = sum(w * p for w, p in probs)
    var = sum(((w - mean) ** 2) * p for w, p in probs)
    return {"k": k, "N": N, "expected_best_waf": mean, "sd_best_waf": math.sqrt(max(var, 0.0)), "prob_top3": sum(p for _, p in probs[:min(3, len(probs))])}


def main():
    commit_gocom = git_rev(REF_GOCOM)
    commit_main = git_rev(REF_MAIN)
    commit_res = git_rev(REF_RES)

    # All 22 independently validated GoCom mixFYF runs
    valid_runs = [
        ("revA-20261114", "arm47", 1, "result/revA-20261114/raw/mixFYF-arm47-rep1"),
        ("revA-20261114", "revA-v4", 1, "result/revA-20261114/raw/mixFYF-revA-v4-rep1"),
        ("revA-20261114", "revA-v4", 2, "result/revA-20261114/raw/mixFYF-revA-v4-rep2"),
        ("revA-20261114", "revA-v4", 3, "result/revA-20261114/raw/mixFYF-revA-v4-rep3"),
        ("revA-20261114", "revA-random", 1, "result/revA-20261114/raw/mixFYF-revA-random-rep1"),
        ("revA-20261114", "revA-random", 2, "result/revA-20261114/raw/mixFYF-revA-random-rep2"),
        ("revA-20261114", "revA-random", 3, "result/revA-20261114/raw/mixFYF-revA-random-rep3"),
        ("revA-20261114", "revA-v1", 1, "result/revA-20261114/raw/mixFYF-revA-v1-rep1"),
        ("revA-20261114", "revA-v1", 2, "result/revA-20261114/raw/mixFYF-revA-v1-rep2"),
        ("revA-20261114", "revA-v1", 3, "result/revA-20261114/raw/mixFYF-revA-v1-rep3"),
        ("revA-20261114", "revA-v2", 1, "result/revA-20261114/raw/mixFYF-revA-v2-rep1"),
        ("revA-20261114", "revA-v2", 2, "result/revA-20261114/raw/mixFYF-revA-v2-rep2"),
        ("revA-20261114", "revA-v2", 3, "result/revA-20261114/raw/mixFYF-revA-v2-rep3"),
        ("revB-20261122", "revB-v4", 1, "result/revB-20261122/raw/mixFYF-revB-v4-rep1"),
        ("revB-20261122", "revB-arm60", 1, "result/revB-20261122/raw/mixFYF-revB-arm60-rep1"),
        ("revB-20261122", "revB-noelim", 1, "result/revB-20261122/raw/mixFYF-revB-noelim-rep1"),
        ("revB-20261122", "revB-noelim", 2, "result/revB-20261122/raw/mixFYF-revB-noelim-rep2"),
        ("revB-20261122", "revB-noelim", 3, "result/revB-20261122/raw/mixFYF-revB-noelim-rep3"),
        ("revB-20261122", "revB-nosettle", 1, "result/revB-20261122/raw/mixFYF-revB-nosettle-rep1"),
        ("revB-20261122", "revB-nosettle", 2, "result/revB-20261122/raw/mixFYF-revB-nosettle-rep2"),
        ("revB-20261122", "revB-nosettle", 3, "result/revB-20261122/raw/mixFYF-revB-nosettle-rep3"),
        ("revC-20261124", "revC-elim10", 1, "result/revC-20261124/raw/mixFYF-revC-elim10-rep1"),
    ]

    # =========================================================================
    # R1: E3 Adaptation Speed (Detection / Re-exploration / Settlement / WAF Recovery)
    # R2: Discount Factor gamma^n Theoretical Weight Calculation
    # R3: I/O Latency Analysis (FIO clat Phase A, YCSB-A Phase B, FIO clat Phase C)
    # =========================================================================
    r1_rows = []
    r2_rows = []
    r3_rows = []
    env_rows = []

    for exp_id, pol, rep, rdir in valid_runs:
        run_id = os.path.basename(rdir)
        s_pts = parse_series_git(REF_GOCOM, rdir)
        p_times = parse_phase_times_git(REF_GOCOM, rdir)
        k_ev = parse_kernel_events_git(REF_GOCOM, rdir)

        # R1 per phase
        for ph in ["A", "B", "C"]:
            t0, t1 = p_times[ph]
            ref_waf, (rec1, f1, rec2, f2), pwaf = compute_recovery(s_pts, t0, t1)
            ev = k_ev.get(ph, {})
            r1_rows.append({
                "exp_id": exp_id,
                "run_id": run_id,
                "policy": pol,
                "rep": rep,
                "phase": ph,
                "phase_duration_s": round(t1 - t0, 1),
                "phase_waf": round(pwaf, 6) if pwaf else None,
                "ref_waf_2nd_half": round(ref_waf, 6) if ref_waf else None,
                "resets_count": ev.get("resets_count", 0),
                "reset_parts": ev.get("reset_parts", 0),
                "detection_time_s": round(ev["detect_s"], 2) if ev.get("detect_s") is not None else None,
                "reexplore_earliest_s": round(ev["reexplore_earliest_s"], 2) if ev.get("reexplore_earliest_s") is not None else None,
                "reexplore_part_mean_s": round(ev["reexplore_part_mean_s"], 2) if ev.get("reexplore_part_mean_s") is not None else None,
                "reexplore_parts_settled": ev.get("reexplore_parts_settled", 0),
                "explore_windows_post_reset": ev.get("explore_windows_post_reset"),
                "settle_from_phase_start_s": round(ev["settle_from_start_earliest_s"], 2) if ev.get("settle_from_start_earliest_s") is not None else None,
                "waf_recovery_1sided_s": round(rec1, 1) if rec1 is not None else None,
                "recovery_1sided_first_win": f1,
                "waf_recovery_2sided_s": round(rec2, 1) if rec2 is not None else None,
                "recovery_2sided_first_win": f2,
                "git_branch": REF_GOCOM,
                "git_commit": commit_gocom,
                "raw_data_path": f"{REF_GOCOM}:{rdir}",
                "analysis_script": SCRIPT_REL,
            })

        # R2: per-partition final valid window count from final-control.txt
        fc = git_show(f"{REF_GOCOM}:{rdir}/final-control.txt") or ""
        part_wins = [int(m) for m in re.findall(r"windows=(\d+)", fc)]
        if part_wins and max(part_wins) > 0:
            w_max = max(part_wins)
            w_mean = float(np.mean(part_wins))
            w_phaseA = k_ev.get("A", {}).get("windows_per_part_max", 0)
            w_phaseC = k_ev.get("C", {}).get("windows_per_part_max", 0)
            eff_n_full = (1.0 - (GAMMA ** w_max)) / (1.0 - GAMMA)
            r2_rows.append({
                "exp_id": exp_id,
                "run_id": run_id,
                "workload": "mixFYF (90 min)",
                "policy": pol,
                "rep": rep,
                "gamma_q16": WATGC_V2_GAMMA_Q16,
                "gamma": round(GAMMA, 8),
                "half_life_windows": round(HALF_LIFE_WINDOWS, 2),
                "phaseA_max_windows_per_part": w_phaseA,
                "weight_oldest_after_phaseA": round(GAMMA ** w_phaseA, 6),
                "total_mean_windows_per_part": round(w_mean, 2),
                "total_max_windows_per_part": w_max,
                "weight_oldest_after_full_run": round(GAMMA ** w_max, 6),
                "effective_window_ratio_pct": round(eff_n_full / w_max * 100.0, 2),
                "actual_perf_ablation_status": "UNMEASURED (no gamma=1 ablation build)",
                "git_branch": REF_GOCOM,
                "git_commit": commit_gocom,
                "raw_data_path": f"{REF_GOCOM}:{rdir}/final-control.txt",
                "analysis_script": SCRIPT_REL,
            })

        # R3: FIO Phase A, YCSB-A Phase B, FIO Phase C (strictly separated)
        fioA = parse_fio_latency_git(REF_GOCOM, rdir, "phase-A.json")
        fioC = parse_fio_latency_git(REF_GOCOM, rdir, "phase-C.json")
        ycsbB = parse_ycsb_latency_git(REF_GOCOM, rdir)
        r3_rows.append({
            "exp_id": exp_id,
            "run_id": run_id,
            "policy": pol,
            "rep": rep,
            # Phase A FIO-Fast 1
            "fioA_total_iops": round(fioA["total_iops"], 1),
            "fioA_weighted_clat_mean_us": round(fioA["weighted_mean_us"], 3),
            "fioA_hot_p50_us": round(fioA["hot"]["p50_us"], 3),
            "fioA_hot_p99_us": round(fioA["hot"]["p99_us"], 3),
            "fioA_warm_p99_us": round(fioA["warm"]["p99_us"], 3),
            "fioA_cold_p99_us": round(fioA["cold"]["p99_us"], 3),
            # Phase B YCSB-A 250k
            "ycsbB_throughput_ops_s": round(ycsbB["throughput_ops_s"], 1),
            "ycsbB_read_avg_us": round(ycsbB["read_avg_us"], 3),
            "ycsbB_read_p95_us": round(ycsbB["read_p95_us"], 3),
            "ycsbB_read_p99_us": round(ycsbB["read_p99_us"], 3),
            "ycsbB_update_avg_us": round(ycsbB["update_avg_us"], 3),
            "ycsbB_update_p95_us": round(ycsbB["update_p95_us"], 3),
            "ycsbB_update_p99_us": round(ycsbB["update_p99_us"], 3),
            # Phase C FIO-Fast 2
            "fioC_total_iops": round(fioC["total_iops"], 1),
            "fioC_weighted_clat_mean_us": round(fioC["weighted_mean_us"], 3),
            "fioC_hot_p50_us": round(fioC["hot"]["p50_us"], 3),
            "fioC_hot_p99_us": round(fioC["hot"]["p99_us"], 3),
            "fioC_warm_p99_us": round(fioC["warm"]["p99_us"], 3),
            "fioC_cold_p99_us": round(fioC["cold"]["p99_us"], 3),
            "git_branch": REF_GOCOM,
            "git_commit": commit_gocom,
            "raw_data_path": f"{REF_GOCOM}:{rdir}/{{phase-A.json,ycsb-run-B.txt.gz,phase-C.json}}",
            "analysis_script": SCRIPT_REL,
        })

        # Environment comparison across revA, revB, revC
        env_txt = git_show(f"{REF_GOCOM}:{rdir}/environment.txt") or ""
        first_line = env_txt.splitlines()[0].strip() if env_txt else ""
        m_kern = re.search(r"Linux\s+(\S+)\s+(\S+)", env_txt)
        m_sha = re.search(r"([0-9a-f]{64})\s+(\S+\.ko)", env_txt)
        m_cmd = re.search(r"BOOT_IMAGE=.*", env_txt)
        env_rows.append({
            "exp_id": exp_id,
            "run_id": run_id,
            "policy": pol,
            "rep": rep,
            "started_at": first_line,
            "host": m_kern[1] if m_kern else "UNKNOWN",
            "kernel": m_kern[2] if m_kern else "UNKNOWN",
            "module_sha256": m_sha[1][:16] + "..." if m_sha else "MISSING",
            "boot_cmdline_has_isolcpus": "isolcpus" in (m_cmd[0] if m_cmd else ""),
            "git_commit": commit_gocom,
            "raw_data_path": f"{REF_GOCOM}:{rdir}/environment.txt",
        })

    # Add valid 10-hour mixY runs to R2 for long-run contrast!
    mixy_specs = [
        (REF_MAIN, commit_main, "smartgc-20261119", "onlinev4 (mixY 10h, SeungCom)", "result/smartgc-20261119/resume/mixY-onlinev4-rep1"),
        (REF_GOCOM, commit_gocom, "v7-20261011-icat2", "onlinev7 (mixY 10h, icat-2)", "result/v7-20261011-icat2/mixY/mixY-onlinev7-rep1"),
    ]
    for ref_m, com_m, exp_m, pol_m, rdir_m in mixy_specs:
        fc = git_show(f"{ref_m}:{rdir_m}/final-control.txt")
        if fc:
            part_wins = [int(m) for m in re.findall(r"windows=(\d+)", fc)]
            if part_wins and max(part_wins) > 0:
                w_max = max(part_wins)
                w_mean = float(np.mean(part_wins))
                eff_n_full = (1.0 - (GAMMA ** w_max)) / (1.0 - GAMMA)
                r2_rows.append({
                    "exp_id": exp_m,
                    "run_id": os.path.basename(rdir_m),
                    "workload": "mixY (10 hours, 20x1800s)",
                    "policy": pol_m,
                    "rep": 1,
                    "gamma_q16": WATGC_V2_GAMMA_Q16,
                    "gamma": round(GAMMA, 8),
                    "half_life_windows": round(HALF_LIFE_WINDOWS, 2),
                    "phaseA_max_windows_per_part": "N/A",
                    "weight_oldest_after_phaseA": "N/A",
                    "total_mean_windows_per_part": round(w_mean, 2),
                    "total_max_windows_per_part": w_max,
                    "weight_oldest_after_full_run": round(GAMMA ** w_max, 6),
                    "effective_window_ratio_pct": round(eff_n_full / w_max * 100.0, 2),
                    "actual_perf_ablation_status": "UNMEASURED (note: resets clear arm history on drift)",
                    "git_branch": ref_m,
                    "git_commit": com_m,
                    "raw_data_path": f"{ref_m}:{rdir_m}/final-control.txt",
                    "analysis_script": SCRIPT_REL,
                })

    # R1 policy-level summary (Phase A & Phase C)
    r1_sum_rows = []
    pol_order = ["revA-v4", "revA-v1", "revA-v2", "revA-random", "arm47", "revB-noelim", "revB-nosettle", "revB-v4", "revB-arm60", "revC-elim10"]
    for ph in ["A", "C"]:
        for pol in pol_order:
            sub = [r for r in r1_rows if r["policy"] == pol and r["phase"] == ph]
            if not sub:
                continue
            det = stat_summary([r["detection_time_s"] for r in sub])
            reex = stat_summary([r["reexplore_earliest_s"] for r in sub])
            st_s = stat_summary([r["settle_from_phase_start_s"] for r in sub])
            rec1 = stat_summary([r["waf_recovery_1sided_s"] for r in sub])
            rec2 = stat_summary([r["waf_recovery_2sided_s"] for r in sub])
            r1_sum_rows.append({
                "phase": ph,
                "policy": pol,
                "n_runs": len(sub),
                "resets_per_run_mean": round(float(np.mean([r["resets_count"] for r in sub])), 2),
                "detect_n": det["n"],
                "detect_mean_s": round(det["mean"], 2) if det["mean"] is not None else "N/A",
                "detect_ci95": f"[{det['ci_lo']:.2f}, {det['ci_hi']:.2f}]" if det["ci_lo"] is not None else "N/A (n<3)",
                "reexplore_n": reex["n"],
                "reexplore_mean_s": round(reex["mean"], 2) if reex["mean"] is not None else "N/A",
                "reexplore_ci95": f"[{reex['ci_lo']:.2f}, {reex['ci_hi']:.2f}]" if reex["ci_lo"] is not None else "N/A (n<3)",
                "settle_from_start_n": st_s["n"],
                "settle_from_start_mean_s": round(st_s["mean"], 2) if st_s["mean"] is not None else "N/A",
                "settle_from_start_ci95": f"[{st_s['ci_lo']:.2f}, {st_s['ci_hi']:.2f}]" if st_s["ci_lo"] is not None else "N/A (n<3)",
                "waf_rec_1sided_n": rec1["n"],
                "waf_rec_1sided_mean_s": round(rec1["mean"], 1) if rec1["mean"] is not None else "None",
                "waf_rec_1sided_first_win_cnt": sum(1 for r in sub if r["recovery_1sided_first_win"]),
                "waf_rec_2sided_n": rec2["n"],
                "waf_rec_2sided_mean_s": round(rec2["mean"], 1) if rec2["mean"] is not None else "None",
                "waf_rec_2sided_first_win_cnt": sum(1 for r in sub if r["recovery_2sided_first_win"]),
                "analysis_script": SCRIPT_REL,
            })

    # R3 policy-level summary + Welch vs revA-v4 (strictly per workload!)
    r3_sum_rows = []
    r3_metrics = [
        ("Phase A: FIO-Fast 1", "fioA_weighted_clat_mean_us", "us"),
        ("Phase A: FIO-Fast 1", "fioA_hot_p99_us", "us"),
        ("Phase B: YCSB-A 250k", "ycsbB_throughput_ops_s", "ops/s"),
        ("Phase B: YCSB-A 250k", "ycsbB_read_avg_us", "us"),
        ("Phase B: YCSB-A 250k", "ycsbB_read_p99_us", "us"),
        ("Phase B: YCSB-A 250k", "ycsbB_update_avg_us", "us"),
        ("Phase B: YCSB-A 250k", "ycsbB_update_p99_us", "us"),
        ("Phase C: FIO-Fast 2", "fioC_weighted_clat_mean_us", "us"),
        ("Phase C: FIO-Fast 2", "fioC_hot_p99_us", "us"),
        ("Phase C: FIO-Fast 2", "fioC_warm_p99_us", "us"),
        ("Phase C: FIO-Fast 2", "fioC_cold_p99_us", "us"),
    ]
    v4_r3 = [r for r in r3_rows if r["policy"] == "revA-v4"]
    for wl_name, mkey, unit in r3_metrics:
        v4_vals = [r[mkey] for r in v4_r3]
        for pol in pol_order:
            sub = [r for r in r3_rows if r["policy"] == pol]
            vals = [r[mkey] for r in sub]
            st = stat_summary(vals)
            wd = welch_diff(vals, v4_vals) if pol != "revA-v4" else None
            r3_sum_rows.append({
                "workload_phase": wl_name,
                "metric": mkey,
                "unit": unit,
                "policy": pol,
                "n": st["n"],
                "mean": round(st["mean"], 3) if st["mean"] is not None else "N/A",
                "sd": round(st["sd"], 3) if st["sd"] is not None else "N/A",
                "ci95": f"[{st['ci_lo']:.3f}, {st['ci_hi']:.3f}]" if st["ci_lo"] is not None else "N/A (n<3)",
                "welch_delta_vs_v4": round(wd["delta"], 3) if wd else ("0.000 (ctrl)" if pol == "revA-v4" else "N/A (n<3)"),
                "welch_ci95": f"[{wd['ci_lo']:+.3f}, {wd['ci_hi']:+.3f}]" if wd else "N/A",
                "ci_excludes_zero": ("YES" if wd["excludes_zero"] else "NO") if wd else "N/A",
                "analysis_script": SCRIPT_REL,
            })

    # =========================================================================
    # R4: Exact Analytical Expectation of k-Trial Random Search on 3 Valid 60/60 Sweeps
    # =========================================================================
    r4_rows = []
    sweep_specs = [
        ("FIO-Fast (test4)", "result/sweep-20260915/rank-test4.txt"),
        ("OLTP", "result/sweep-20260915/rank-oltp.txt"),
        ("SQLite-A (87/87 valid)", "result/sweep-20260915/rank-sqlite-a.txt"),
    ]
    for wname, spath in sweep_specs:
        txt = git_show(f"{REF_MAIN}:{spath}") or ""
        arms_all = []
        arms_k4 = []
        arm37_waf = None
        arm50_waf = None
        for line in txt.splitlines():
            m = re.match(r"\s*(\d+)\s+arm(\d+)\s+k(\d+)-s(\d+)-r(\d+)\s+([\d.]+)", line)
            if m:
                arm_id, k_val, waf = int(m[2]), int(m[3]), float(m[6])
                arms_all.append(waf)
                if k_val >= 4:
                    arms_k4.append(waf)
                if arm_id == 37:
                    arm37_waf = waf
                if arm_id == 50:
                    arm50_waf = waf
        arms_all.sort()
        arms_k4.sort()
        for space_lbl, wlist in [("Full 60-arm space", arms_all), ("Reduced 45-arm space (excl. k=2)", arms_k4)]:
            opt_waf = wlist[0]
            for k_trials in [1, 2, 3, 5, 10, 15, 20, 30, 45, 60]:
                if k_trials > len(wlist):
                    continue
                st_k = exact_k_random_search_stats(wlist, k_trials)
                gap_pct = (st_k["expected_best_waf"] / opt_waf - 1.0) * 100.0
                r4_rows.append({
                    "workload": wname,
                    "candidate_space": space_lbl,
                    "N_candidates": len(wlist),
                    "k_random_trials": k_trials,
                    "expected_best_waf": round(st_k["expected_best_waf"], 6),
                    "sd_best_waf": round(st_k["sd_best_waf"], 6),
                    "optimal_arm_waf": round(opt_waf, 6),
                    "gap_vs_optimal_pct": round(gap_pct, 3),
                    "prob_finding_top3_pct": round(st_k["prob_top3"] * 100.0, 2),
                    "cat37_default_waf": arm37_waf,
                    "cat50_robust_waf": arm50_waf,
                    "method_caveat": "Static single-workload exact combinatorics E[min W_i]; NOT an online NVMeVirt Random Search execution (excludes switching/exploration cost)",
                    "git_branch": REF_MAIN,
                    "git_commit": commit_main,
                    "raw_data_path": f"{REF_MAIN}:{spath}",
                    "analysis_script": SCRIPT_REL,
                })

    write_csv(OUT_DIR / "r1_adaptation_runs.csv", r1_rows)
    write_csv(OUT_DIR / "r1_adaptation_summary.csv", r1_sum_rows)
    write_csv(OUT_DIR / "r2_discount_gamma.csv", r2_rows)
    write_csv(OUT_DIR / "r3_io_latency_runs.csv", r3_rows)
    write_csv(OUT_DIR / "r3_io_latency_summary.csv", r3_sum_rows)
    write_csv(OUT_DIR / "r4_random_search_expectation.csv", r4_rows)
    write_csv(OUT_DIR / "revB_vs_revC_env_audit.csv", env_rows)

    # Print crisp key findings summary to stdout for immediate verification
    print(f"=== R1-R4 ZERO-COST REANALYSIS COMPLETE ({GENERATED_AT}) ===")
    print(f"Commits: GoCom={commit_gocom}, Main={commit_main}, Res={commit_res}")
    print("\n--- R1 (E3 Adaptation, Phase A & C summary) ---")
    for r in r1_sum_rows:
        if r["policy"] in ("revA-v4", "revA-v1", "revA-v2", "revA-random", "revB-noelim", "revB-nosettle", "revC-elim10", "arm47"):
            print(f"  Ph {r['phase']} | {r['policy']:13s} (n={r['n_runs']}) | resets={r['resets_per_run_mean']:4.1f} | detect={str(r['detect_mean_s']):>6s}s | reexp={str(r['reexplore_mean_s']):>6s}s | settle={str(r['settle_from_start_mean_s']):>6s}s | rec1={str(r['waf_rec_1sided_mean_s']):>6s}s(fw={r['waf_rec_1sided_first_win_cnt']}) | rec2={str(r['waf_rec_2sided_mean_s']):>6s}s(fw={r['waf_rec_2sided_first_win_cnt']})")
    print("\n--- R2 (Discount factor gamma=0.99949646, half-life=1376.22 windows) ---")
    for r in r2_rows:
        if r["policy"] in ("revA-v4", "revA-v2", "revB-noelim", "revC-elim10") and r["rep"] == 1 or "mixY" in r["workload"]:
            print(f"  {r['workload']:26s} | {r['policy']:30s} | max_win={r['total_max_windows_per_part']:4d} | oldest_wt={r['weight_oldest_after_full_run']:.4f} | eff_ratio={r['effective_window_ratio_pct']:.2f}%")
    print("\n--- R3 (I/O Latency, key metrics vs revA-v4, n=3) ---")
    for r in r3_sum_rows:
        if r["policy"] in ("revA-v4", "revA-random", "revA-v1", "revA-v2", "revB-noelim", "revB-nosettle", "revC-elim10") and r["metric"] in ("fioA_weighted_clat_mean_us", "fioA_hot_p99_us", "ycsbB_throughput_ops_s", "ycsbB_read_avg_us", "ycsbB_update_avg_us", "fioC_weighted_clat_mean_us", "fioC_hot_p99_us"):
            print(f"  {r['metric']:26s} | {r['policy']:13s} (n={r['n']}) | mean={str(r['mean']):>9s} | delta_vs_v4={str(r['welch_delta_vs_v4']):>12s} | CI={r['welch_ci95']} | sig={r['ci_excludes_zero']}")
    print("\n--- R4 (Static k-trial Random Search expectation, 60 vs 45 space) ---")
    for r in r4_rows:
        if r["k_random_trials"] in (1, 3, 5, 10, 20, 45):
            print(f"  {r['workload']:22s} | {r['candidate_space']:32s} | k={r['k_random_trials']:2d} | E[best]={r['expected_best_waf']:.4f} (±{r['sd_best_waf']:.4f}) | gap={r['gap_vs_optimal_pct']:+.2f}% | P(top3)={r['prob_finding_top3_pct']:5.1f}%")


if __name__ == "__main__":
    main()
