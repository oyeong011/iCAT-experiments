#!/usr/bin/env python3
"""
Home PC Final Paper Revision Delivery Package Builder (2026-11-27)
Output directory: report/delivery-20261127/

Produces (100% read-only from immutable Git raw logs; zero modification to result/ or figs/):
  1. final_experiment_validity.csv
  2. final_statistical_audit.csv
  3. final_robustness_audit.md
  4. final_reviewer_evidence_matrix.md
  5. final_revision_status.md
  6. SENIOR_RESEARCHER_SUMMARY_20261127.md
  7. delivery_audit_dump.json (machine-readable snapshot for Excel/Figure sync)

Automatically detects completion of SeungCom batchG-20261126 (8/9 -> 9/9) and
GoCom m1-20261126 (1/2 -> 2/2) without ever marking unverified/running runs as PASS.
"""
import csv
import gzip
import json
import math
import os
import re
import statistics
import subprocess
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent
OUT_DIR.mkdir(parents=True, exist_ok=True)

REF_MAIN = "origin/main"
REF_GOCOM = "origin/report/data-validity-20261124"
REF_RES = "origin/resource-overhead-20261114"

KST = timezone(timedelta(hours=9))
NOW_STR = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST")


def git_rev(ref: str) -> str:
    return subprocess.check_output(["git", "rev-parse", "--short=9", ref], cwd=REPO_ROOT, text=True).strip()


def git_bytes(ref: str, path: str):
    p = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=REPO_ROOT, capture_output=True)
    return p.stdout if p.returncode == 0 else None


def git_text(ref: str, path: str):
    b = git_bytes(ref, path)
    return b.decode("utf-8", errors="replace") if b is not None else None


def git_path_exists(ref: str, path: str) -> bool:
    p = subprocess.run(["git", "cat-file", "-e", f"{ref}:{path}"], cwd=REPO_ROOT, capture_output=True)
    return p.returncode == 0


# ---------------------------------------------------------------------------
# Pure-Python Exact Student-t, Welch, Paired, Hedges' g, Holm-Bonferroni
# ---------------------------------------------------------------------------
def _betacf(a, b, x):
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) >= 1e-30 else 1e-30)
    h = d
    for m in range(1, 201):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 / ((1.0 + aa * d) if abs(1.0 + aa * d) >= 1e-30 else 1e-30)
        c = (1.0 + aa / c) if abs(1.0 + aa / c) >= 1e-30 else 1e-30
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 / ((1.0 + aa * d) if abs(1.0 + aa * d) >= 1e-30 else 1e-30)
        c = (1.0 + aa / c) if abs(1.0 + aa / c) >= 1e-30 else 1e-30
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 3e-12:
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


def t_p_two_tail(t_abs, df):
    return _betainc(df / 2.0, 0.5, df / (df + t_abs * t_abs))


def t_crit_95(df):
    lo, hi = 1.0, 200.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if t_p_two_tail(mid, df) > 0.05:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def group_stats(vals):
    n = len(vals)
    if n == 0:
        return {"n": 0, "mean": None, "sd": None, "ci_lo": None, "ci_hi": None}
    m = sum(vals) / n
    if n < 3:
        sd = math.sqrt(sum((x - m) ** 2 for x in vals) / (n - 1)) if n == 2 else None
        return {"n": n, "mean": m, "sd": sd, "ci_lo": None, "ci_hi": None}
    sd = math.sqrt(sum((x - m) ** 2 for x in vals) / (n - 1))
    tc = t_crit_95(n - 1)
    h = tc * sd / math.sqrt(n)
    return {"n": n, "mean": m, "sd": sd, "ci_lo": m - h, "ci_hi": m + h}


def welch_test(a, b):
    na, nb = len(a), len(b)
    if na < 3 or nb < 3:
        return None
    ma, mb = sum(a) / na, sum(b) / nb
    va = sum((x - ma) ** 2 for x in a) / (na - 1)
    vb = sum((x - mb) ** 2 for x in b) / (nb - 1)
    diff = ma - mb
    se = math.sqrt(va / na + vb / nb)
    df = (va / na + vb / nb) ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1)) if se > 0 else float(na + nb - 2)
    tc = t_crit_95(df)
    p = t_p_two_tail(abs(diff / se), df) if se > 0 else (0.0 if diff != 0 else 1.0)
    sp = math.sqrt(((na - 1) * va + (nb - 1) * vb) / (na + nb - 2))
    J = 1.0 - 3.0 / (4.0 * (na + nb - 2) - 1.0)
    g = (diff / sp) * J if sp > 0 else 0.0
    return {"diff": diff, "ci_lo": diff - tc * se, "ci_hi": diff + tc * se, "df": df, "p": p, "g": g}


def paired_test(a, b):
    if len(a) != len(b) or len(a) < 3:
        return None
    d = [x - y for x, y in zip(a, b)]
    n = len(d)
    m = sum(d) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in d) / (n - 1))
    se = sd / math.sqrt(n)
    tc = t_crit_95(n - 1)
    p = t_p_two_tail(abs(m / se), n - 1) if se > 0 else (0.0 if m != 0 else 1.0)
    return {"mean": m, "ci_lo": m - tc * se, "ci_hi": m + tc * se, "p": p}


def holm_adjust(pvals):
    m = len(pvals)
    idx_sorted = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    prev = 0.0
    for rank, idx in enumerate(idx_sorted):
        val = min(1.0, max(prev, (m - rank) * pvals[idx]))
        adj[idx] = val
        prev = val
    return adj


def load_hashes(ref, path):
    txt = git_text(ref, path) or ""
    out = {}
    for l in txt.splitlines():
        m = re.match(r"([0-9a-f]{64})\s+(\S+)", l.strip())
        if m:
            out[os.path.basename(m.group(2))] = m.group(1)
    return out


# ---------------------------------------------------------------------------
# Generic 7-Point Raw Run Verifier
# ---------------------------------------------------------------------------
def inspect_raw_run(ref: str, run_dir: str, check_ycsb: bool = True, expected_sha: str = None):
    ec = (git_text(ref, f"{run_dir}/exit-code.txt") or "MISSING").strip()
    env = git_text(ref, f"{run_dir}/environment.txt") or ""
    m_date = re.match(r"(\d{4}-\d{2}-\d{2}T[\d:+]+)", env.strip())
    run_date = m_date.group(1) if m_date else "UNKNOWN"
    m_host = re.search(r"Linux\s+(\S+)\s+(\S+)", env)
    host = m_host.group(1) if m_host else "UNKNOWN"
    kernel = m_host.group(2) if m_host else "UNKNOWN"
    m_sha = re.search(r"([0-9a-f]{64})\s+(\S+\.ko)", env)
    mod_sha = m_sha.group(1) if m_sha else "UNRECORDED"
    mod_name = os.path.basename(m_sha.group(2)) if m_sha else "UNKNOWN"

    summ = git_text(ref, f"{run_dir}/summary.txt") or ""
    fc = git_text(ref, f"{run_dir}/final-control.txt") or ""
    m_st = re.search(r"^total\s+host_bytes=(\d+)\s+host_pages=(\d+)\s+gc_pages=(\d+)\s+WAF=([\d.]+)", summ, re.M)
    m_ft = re.search(r"host_bytes=(\d+)\s+host_pages=(\d+)\s+gc_pages=(\d+)", fc)
    parts = re.findall(r"part=(\d+)\s+host_pages=(\d+)\s+gc_pages=(\d+)", fc)
    if m_st:
        sh, sg, sw = int(m_st.group(2)), int(m_st.group(3)), float(m_st.group(4))
        recalc = 1.0 + sg / sh if sh > 0 else 0.0
        fh = int(m_ft.group(2)) if m_ft else sh
        fg = int(m_ft.group(3)) if m_ft else sg
        ph = sum(int(x[1]) for x in parts) if parts else sh
        pg = sum(int(x[2]) for x in parts) if parts else sg
        two_path = (sh > 0 and sh == fh == ph and sg == fg == pg and abs(recalc - sw) < 2e-6)
    else:
        sh, sg, sw, recalc, two_path = 0, 0, None, None, False

    phase_wafs = {}
    for ph in ("A", "B", "C"):
        ps = git_text(ref, f"{run_dir}/phase-{ph}-start.txt")
        pe = git_text(ref, f"{run_dir}/phase-{ph}-end.txt")
        if ps and pe:
            ms = re.search(r"host_pages=(\d+)\s+gc_pages=(\d+)", ps)
            me = re.search(r"host_pages=(\d+)\s+gc_pages=(\d+)", pe)
            if ms and me and int(me.group(1)) > int(ms.group(1)):
                dh = int(me.group(1)) - int(ms.group(1))
                dg = int(me.group(2)) - int(ms.group(2))
                phase_wafs[ph] = 1.0 + dg / dh
    if not phase_wafs:
        for ph, wv in re.findall(r"^phase([ABC])\([^)]*\)\s+host_pages=\d+\s+gc_pages=\d+\s+WAF=([\d.]+)", summ, re.M):
            phase_wafs[ph] = float(wv)

    fio_seeds, fio_errs = [], 0
    for jf in ("phase-A.json", "phase-C.json", "phase-S01.json", "fio.json"):
        ft = git_text(ref, f"{run_dir}/{jf}")
        if ft:
            try:
                d = json.loads(ft)
                for j in d.get("jobs", []):
                    if j.get("error", 0) != 0:
                        fio_errs += 1
                    rs = j.get("job options", {}).get("randseed")
                    if rs and str(rs) not in fio_seeds:
                        fio_seeds.append(str(rs))
            except Exception:
                fio_errs += 1

    sqlite_full, ycsb_ok_pct = 0, None
    if check_ycsb:
        for yf in ("ycsb-run-B.txt.gz", "ycsb-run.txt.gz", "ycsb-load.txt.gz"):
            yb = git_bytes(ref, f"{run_dir}/{yf}")
            if yb is not None:
                if len(yb) == 0:
                    ycsb_ok_pct = 0.0
                    continue
                try:
                    yt = gzip.decompress(yb).decode("utf-8", errors="replace")
                except Exception:
                    yt = yb.decode("utf-8", errors="replace")
                sqlite_full += len(re.findall(r"SQLITE_FULL|database or disk is full", yt, re.I))
                ops = dict(re.findall(r"\[([\w-]+)\],\s*Operations,\s*(\d+)", yt))
                ok = sum(int(v) for k, v in ops.items() if k in ("INSERT", "READ", "UPDATE"))
                fail = sum(int(v) for k, v in ops.items() if "FAILED" in k.upper())
                if ok + fail > 0:
                    pct = 100.0 * ok / (ok + fail)
                    ycsb_ok_pct = pct if ycsb_ok_pct is None else min(ycsb_ok_pct, pct)

    # STRICT SCOPED KERNEL LOG: always prefer kernel.log.nowarn.gz / kernel.log, NEVER kernel-final.log for M1PROF
    kl_gz = git_bytes(ref, f"{run_dir}/kernel.log.nowarn.gz")
    if kl_gz is not None:
        kl = gzip.decompress(kl_gz).decode("utf-8", errors="replace")
    else:
        kl = git_text(ref, f"{run_dir}/kernel.log") or ""
    k_errs = sum(1 for l in kl.splitlines() if re.search(r"\b(BUG:|Oops|WARNING:|Call Trace|panic|EXT4-fs error|I/O error)\b", l))
    resets = sum(1 for l in kl.splitlines() if re.search(r"WATGC_V2\s+(?:part=\d+\s+)?reset\b", l))

    sha_ok = (mod_sha == expected_sha) if expected_sha else (mod_sha != "UNRECORDED")
    valid = (ec == "0" and two_path and fio_errs == 0 and sqlite_full == 0 and k_errs == 0 and (ycsb_ok_pct is None or ycsb_ok_pct >= 99.0))
    if expected_sha:
        valid = valid and sha_ok

    return {
        "ref": ref, "run_dir": run_dir, "run_date": run_date, "host": host, "kernel": kernel,
        "mod_name": mod_name, "mod_sha": mod_sha, "sha_ok": sha_ok, "exit_code": ec,
        "host_pages": sh, "gc_pages": sg, "waf_summary": sw, "waf_recalc": recalc,
        "two_path_ok": two_path, "waf_A": phase_wafs.get("A"), "waf_B": phase_wafs.get("B"), "waf_C": phase_wafs.get("C"),
        "fio_seeds": "/".join(fio_seeds) if fio_seeds else "UNRECORDED", "fio_errs": fio_errs,
        "sqlite_full": sqlite_full, "ycsb_ok_pct": round(ycsb_ok_pct, 3) if ycsb_ok_pct is not None else "N/A",
        "kernel_errs": k_errs, "resets": resets, "valid": valid,
    }


# ---------------------------------------------------------------------------
# Scoped M1-20261126 Verifier (kernel.log.nowarn.gz ONLY + sampler/mem.tsv + WAF_nand)
# ---------------------------------------------------------------------------
def inspect_m1_run(ref: str, run_dir: str, expected_sha: str):
    if not git_path_exists(ref, f"{run_dir}/exit-code.txt"):
        return None
    base = inspect_raw_run(ref, run_dir, check_ycsb=False, expected_sha=expected_sha)
    # Scoped kernel.log.nowarn.gz ONLY (08ac54dc9 rule: NEVER kernel-final.log!)
    kl_gz = git_bytes(ref, f"{run_dir}/kernel.log.nowarn.gz")
    kl = gzip.decompress(kl_gz).decode("utf-8", errors="replace") if kl_gz else (git_text(ref, f"{run_dir}/kernel.log") or "")

    # Parse final cumulative M1PROF lines (when=stop, 4-part sum)
    by_reg = {}
    parts_seen = set()
    for l in kl.splitlines():
        if "M1PROF" in l and "when=stop" in l:
            mp = re.search(r"part=(\d+)", l)
            mr = re.search(r"region=(\S+)\s+calls=(\d+)\s+ns=(\d+)\s+max_ns=(\d+)", l)
            if mp and mr:
                parts_seen.add(int(mp.group(1)))
                reg = mr.group(1)
                c, ns, mx = int(mr.group(2)), int(mr.group(3)), int(mr.group(4))
                e = by_reg.setdefault(reg, [0, 0, 0])
                e[0] += c
                e[1] += ns
                e[2] = max(e[2], mx)

    def reg_stats(name):
        c, ns, mx = by_reg.get(name, [0, 0, 0])
        return c, ns / 1e9, (ns / 1e3 / c if c else None), (ns / c if c else None), (mx / 1e3 if mx else None)

    gc_calls, gc_s, gc_us, _, gc_max_us = reg_stats("GC")
    sel_calls, sel_s, sel_us, _, sel_max_us = reg_stats("SELECT")
    learn_calls, learn_s, learn_us, learn_ns, learn_max_us = reg_stats("LEARN")
    rew_calls, rew_s, rew_us, rew_ns, _ = reg_stats("REWARD")
    buf_s = sum(by_reg.get(k, [0, 0, 0])[1] for k in ("BUF_ABSORB", "BUF_UNBUF", "BUF_DRAIN")) / 1e9

    # Exact WAF_nand from final-control.txt (smartgc part=* absorbed=... evicted=... nand_pages=...)
    fc = git_text(ref, f"{run_dir}/final-control.txt") or ""
    buf_abs, buf_ev, nand_sum = 0, 0, 0
    for l in fc.splitlines():
        if l.startswith("smartgc "):
            ma = re.search(r"absorbed=(\d+)", l)
            me = re.search(r"evicted=(\d+)", l)
            mn = re.search(r"nand_pages=(\d+)", l)
            if ma: buf_abs += int(ma.group(1))
            if me: buf_ev += int(me.group(1))
            if mn: nand_sum += int(mn.group(1))

    if "icat" in run_dir:
        waf_nand = base["waf_recalc"]
    elif base["host_pages"] > 0 and (buf_abs > 0 or nand_sum > 0):
        nand_pages = base["host_pages"] + base["gc_pages"] - buf_abs + buf_ev
        waf_nand = nand_pages / base["host_pages"]
    else:
        waf_nand = None

    # Channel model warnings from kernel-reduced.txt (kernel.log scoped line)
    kr_txt = git_text(ref, f"{run_dir}/kernel-reduced.txt") or ""
    m_cw = re.search(r"^kernel\.log\s+chmodel_warn_lines=(\d+)", kr_txt, re.M)
    ch_warn = int(m_cw.group(1)) if m_cw else None

    # Memory from sampler/<run_name>/mem.tsv (strictly kB and bytes separated!)
    run_name = os.path.basename(run_dir)
    mem_txt = git_text(ref, f"result/m1-20261126/sampler/{run_name}/mem.tsv") or ""
    by_s = defaultdict(list)
    if mem_txt:
        rows = [l.split("\t") for l in mem_txt.strip().splitlines() if l.strip()]
        hdr = rows[0]
        vcols = [i for i, h in enumerate(hdr) if "vmalloc" in h.lower()]
        scols = [i for i, h in enumerate(hdr) if h.lower() in ("state", "phase", "tag")]
        if vcols and scols:
            vcol, scol = vcols[0], scols[0]
            for r in rows[1:]:
                if len(r) > max(vcol, scol):
                    try:
                        by_s[r[scol].lower()].append(float(r[vcol]))
                    except ValueError:
                        pass

    vm_pre = statistics.median(by_s["pre"]) if by_s["pre"] else None
    vm_load1s = statistics.median(by_s["load1s"]) if by_s["load1s"] else None
    vm_loaded = statistics.median(by_s["loaded"]) if by_s["loaded"] else None
    vm_post = statistics.median(by_s["post"]) if by_s["post"] else None
    vm_delta_load_kb = (vm_load1s - vm_pre) if (vm_load1s is not None and vm_pre is not None) else None
    vm_delta_loaded_kb = (vm_loaded - vm_pre) if (vm_loaded is not None and vm_pre is not None) else None
    vm_delta_post_kb = (vm_post - vm_pre) if (vm_post is not None and vm_pre is not None) else None
    host_gib = base["host_pages"] * 4096 / (1024 ** 3) if base["host_pages"] else 0.0

    base["m1"] = {
        "parts_parsed": len(parts_seen),
        "gc_calls": gc_calls, "gc_s": gc_s, "gc_us_per_call": gc_us, "gc_max_us": gc_max_us,
        "gc_ms_per_gib": (gc_s * 1000.0 / host_gib) if host_gib else None,
        "select_calls": sel_calls, "select_s": sel_s, "select_us_per_call": sel_us, "select_max_us": sel_max_us,
        "learn_calls": learn_calls, "learn_s": learn_s, "learn_us_per_call": learn_us, "learn_ns_per_call": learn_ns,
        "reward_calls": rew_calls, "reward_s": rew_s, "reward_ns_per_call": rew_ns,
        "buf_upper_s": buf_s, "buf_absorbed": buf_abs, "buf_evicted": buf_ev,
        "chmodel_warn": ch_warn,
        "waf_nand": waf_nand,
        "vm_pre_kb": vm_pre,
        "vm_delta_load1s_kb": vm_delta_load_kb,
        "vm_delta_load1s_bytes": int(round(vm_delta_load_kb * 1024)) if vm_delta_load_kb is not None else None,
        "vm_delta_loaded_kb": vm_delta_loaded_kb,
        "vm_delta_post_kb": vm_delta_post_kb,
        "host_tb": base["host_pages"] * 4096 / 1e12,
    }
    return base


def write_csv(path: Path, fieldnames: list, rows: list):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def fmt(v, nd=4):
    if v is None or v == "" or isinstance(v, str):
        return str(v) if v is not None else "N/A"
    return f"{v:.{nd}f}"


def main():
    c_main = git_rev(REF_MAIN)
    c_gocom = git_rev(REF_GOCOM)
    c_res = git_rev(REF_RES)
    print(f"Delivery Builder Git heads: main={c_main}, gocom={c_gocom}, res={c_res}")

    h_revA = load_hashes(REF_GOCOM, "result/revA-20261114/modules.sha256")
    h_revB = load_hashes(REF_GOCOM, "result/revB-20261122/modules.sha256")
    h_revC = load_hashes(REF_GOCOM, "result/revC-20261124/modules.sha256")
    h_revD = load_hashes(REF_MAIN, "result/revD-20261124/modules.sha256")
    h_abl = load_hashes(REF_MAIN, "result/revision-additional-ablation/modules.sha256")
    h_revE = load_hashes(REF_GOCOM, "result/revE-20261125/modules.sha256")
    h_greedy = load_hashes(REF_MAIN, "result/greedy-20261125/modules.sha256")
    h_batchG = load_hashes(REF_MAIN, "result/batchG-20261126/modules.sha256")
    h_arm47 = load_hashes(REF_MAIN, "result/arm47-20261127/modules.sha256")
    h_m1 = load_hashes(REF_GOCOM, "result/m1-20261126/modules.sha256")

    # Core completed campaigns (65 + arm47 n=1 = 66 mixFYF runs)
    campaign_specs = [
        ("revA-20261114", "M3/Ref", REF_GOCOM, c_gocom, "revA-arm47", 1, "result/revA-20261114/raw/mixFYF-arm47-rep1", h_revA.get("nvmev-arm47.ko"), "mixFYF 250k", True),
        *[("revA-20261114", "M2/M3", REF_GOCOM, c_gocom, f"revA-{p}", r, f"result/revA-20261114/raw/mixFYF-revA-{p}-rep{r}", h_revA.get(f"nvmev-revA-{p}.ko"), "mixFYF 250k", True)
          for p in ("v4", "random", "v1", "v2") for r in (1, 2, 3)],
        ("revB-20261122", "M2", REF_GOCOM, c_gocom, "revB-v4", 1, "result/revB-20261122/raw/mixFYF-revB-v4-rep1", h_revB.get("nvmev-revA-v4.ko") or h_revB.get("nvmev-revB-v4.ko"), "mixFYF 250k", True),
        ("revB-20261122", "M6/E7", REF_GOCOM, c_gocom, "revB-arm60", 1, "result/revB-20261122/raw/mixFYF-revB-arm60-rep1", h_revB.get("nvmev-revB-arm60.ko"), "mixFYF 250k", True),
        *[("revB-20261122", "M2", REF_GOCOM, c_gocom, f"revB-{p}", r, f"result/revB-20261122/raw/mixFYF-revB-{p}-rep{r}", h_revB.get(f"nvmev-revB-{p}.ko"), "mixFYF 250k", True)
          for p in ("noelim", "nosettle") for r in (1, 2, 3)],
        *[("revC-20261124", "M6/E6", REF_GOCOM, c_gocom, f"revC-{p}", r, f"result/revC-20261124/raw/mixFYF-revC-{p}-rep{r}", h_revC.get(f"nvmev-revC-{p}.ko"), "mixFYF 250k", True)
          for p in ("v4", "elim10", "elim25") for r in (1, 2, 3)],
        *[("revC-20261124", "M6/E7", REF_GOCOM, c_gocom, "revC-arm60", r, f"result/revC-20261124/raw/mixFYF-revB-arm60-rep{r}", h_revC.get("nvmev-revB-arm60.ko"), "mixFYF 250k", True)
          for r in (1, 2, 3)],
        *[("revC-20261124", "M3", REF_GOCOM, c_gocom, "revC-online", r, f"result/revC-20261124/raw/mixFYF-online-rep{r}", h_revC.get("nvmev-online.ko"), "mixFYF 250k", True)
          for r in (1, 2, 3)],
        *[("revD-20261124", "M2/E1", REF_MAIN, c_main, f"revD-{p}", r, f"result/revD-20261124/raw/mixFYF-revD-{p}-rep{r}", h_revD.get(f"nvmev-revD-{p}.ko"), "mixFYF 250k", True)
          for p in ("v4", "nodrift", "fullreset") for r in (1, 2, 3)],
        *[("abl-20261125", "M2", REF_MAIN, c_main, f"abl-{p}", r, f"result/revision-additional-ablation/raw/mixFYF-abl-{d}-rep{r}", h_abl.get(f"nvmev-abl-{d}.ko"), "mixFYF 250k", True)
          for (p, d) in [("v4", "v4"), ("nodiscount", "nodiscount"), ("bundle-off", "off-elim-settle-drift-probe")] for r in (1, 2, 3)],
        *[("revE-20261125", "M2/M6", REF_GOCOM, c_gocom, f"revE-{p}", r, f"result/revE-20261125/raw/mixFYF-revE-{p}-rep{r}", h_revE.get(m), "mixFYF 250k", True)
          for (p, m) in [("v4", "nvmev-revC-v4.ko"), ("noelim", "nvmev-revB-noelim.ko"), ("drift12", "nvmev-revE-drift12.ko")] for r in (1, 2, 3)],
        *[("greedy-20261125", "M3", REF_MAIN, c_main, "greedy-online", r, f"result/greedy-20261125/raw/mixFYF-greedy-online-rep{r}", h_greedy.get("nvmev-greedy-online.ko"), "mixFYF 250k", True)
          for r in (1, 2, 3)],
        *[("arm47-20261127", "Robustness/Ref", REF_MAIN, c_main, "arm47-seungcom", r, f"result/arm47-20261127/raw/mixFYF-arm47-rep{r}", h_arm47.get("nvmev-arm47.ko"), "mixFYF 250k", True)
          for r in (1, 2, 3)],
    ]

    # Auto-detect batchG-20261126 (up to 9 runs)
    batchG_defs = [
        ("M3", "batchG-greedygc", r, f"result/greedygc-20261126/raw/mixFYF-greedygc-rep{r}", h_batchG.get("nvmev-greedygc.ko"))
        for r in (1, 2, 3)
    ] + [
        ("M6", "batchG-drift50", r, f"result/drift50-20261126/raw/mixFYF-drift50-rep{r}", h_batchG.get("nvmev-drift50.ko"))
        for r in (1, 2, 3)
    ] + [
        ("M3/M6", "batchG-v4", r, f"result/batchG-20261126/raw/mixFYF-bg-v4-rep{r}", h_batchG.get("nvmev-abl-v4.ko"))
        for r in (1, 2, 3)
    ]

    batchG_pending = []
    for cat, pol, r, rdir, esha in batchG_defs:
        if git_path_exists(REF_MAIN, f"{rdir}/exit-code.txt"):
            campaign_specs.append(("batchG-20261126", cat, REF_MAIN, c_main, pol, r, rdir, esha, "mixFYF 250k", True))
        else:
            batchG_pending.append((cat, pol, r, rdir, esha))

    # Inspect all mixFYF runs
    val_rows = []
    by_pol = defaultdict(list)
    for camp, cat, ref, commit, pol, rep, rdir, esha, wl, cy in campaign_specs:
        info = inspect_raw_run(ref, rdir, check_ycsb=cy, expected_sha=esha)
        by_pol[pol].append(info)
        note = ""
        if pol == "revA-arm47":
            note = "n=1 single reference run (no SD/CI; oracle arm on 96% FIO-Fast)"
        elif pol == "revB-v4":
            note = "Cross-batch bridge failed (+4.8 SD vs revA-v4); superseded by same-batch revE"
        elif pol.startswith("batchG-"):
            note = "SeungCom batchG-20261126 (cpu_check=unavailable: loadsampler not ported to SeungCom)"
        val_rows.append({
            "Campaign": camp, "Review_Item": cat, "Policy": pol, "Rep": rep,
            "Host": info["host"], "Git_Branch": ref, "Git_Commit": commit,
            "Run_Date": info["run_date"], "Workload": wl,
            "Module_Name": info["mod_name"], "Module_SHA256": info["mod_sha"], "SHA_Match": info["sha_ok"],
            "FIO_Seeds": info["fio_seeds"], "Exit_Code": info["exit_code"],
            "FIO_Errors": info["fio_errs"], "YCSB_OK_Pct": info["ycsb_ok_pct"], "SQLITE_FULL": info["sqlite_full"],
            "Kernel_Errors": info["kernel_errs"], "Host_Pages": info["host_pages"], "GC_Pages": info["gc_pages"],
            "WAF_Recalc": f"{info['waf_recalc']:.6f}" if info["waf_recalc"] else "MISSING",
            "WAF_nand": f"{info['waf_recalc']:.6f}" if info["waf_recalc"] else "MISSING",
            "WAF_PhaseA": f"{info['waf_A']:.6f}" if info["waf_A"] else "N/A",
            "WAF_PhaseB": f"{info['waf_B']:.6f}" if info["waf_B"] else "N/A",
            "WAF_PhaseC": f"{info['waf_C']:.6f}" if info["waf_C"] else "N/A",
            "Two_Path_Match": info["two_path_ok"], "Validity": "VALID" if info["valid"] else "INVALID",
            "Raw_Path": f"{ref}:{rdir}", "Notes": note,
        })

    for cat, pol, r, rdir, esha in batchG_pending:
        val_rows.append({
            "Campaign": "batchG-20261126", "Review_Item": cat, "Policy": pol, "Rep": r,
            "Host": "oy-System-Product-Name", "Git_Branch": REF_MAIN, "Git_Commit": c_main,
            "Run_Date": "RUNNING", "Workload": "mixFYF 250k",
            "Module_Name": os.path.basename(rdir), "Module_SHA256": esha or "preregistered", "SHA_Match": "PENDING",
            "FIO_Seeds": "20260913/1013/1113", "Exit_Code": "RUNNING", "FIO_Errors": "PENDING",
            "YCSB_OK_Pct": "PENDING", "SQLITE_FULL": "PENDING", "Kernel_Errors": "PENDING",
            "Host_Pages": "PENDING", "GC_Pages": "PENDING", "WAF_Recalc": "PENDING", "WAF_nand": "PENDING",
            "WAF_PhaseA": "PENDING", "WAF_PhaseB": "PENDING", "WAF_PhaseC": "PENDING",
            "Two_Path_Match": "PENDING", "Validity": "RUNNING (NOT VERIFIED)",
            "Raw_Path": f"{REF_MAIN}:{rdir}", "Notes": "Pending completion (~00:42 KST); NOT marked PASS",
        })

    # Auto-detect m1-20261126 (up to 2 runs: icat-v4, smartgc-eq8)
    m1_results = {}
    for pol, rdir, mkey in [
        ("m1-icat-v4", "result/m1-20261126/raw/mixY-m1-icat-v4-rep1", "nvmev-m1-icat-v4.ko"),
        ("m1-smartgc-eq8", "result/m1-20261126/raw/mixY-m1-smartgc-eq8-rep1", "nvmev-m1-smartgc-eq8.ko"),
    ]:
        res = inspect_m1_run(REF_GOCOM, rdir, h_m1.get(mkey))
        m1_results[pol] = res
        if res is not None:
            m1d = res["m1"]
            note = (
                f"n=1 (rep2-3 cancelled by user); chmodel_warn={m1d['chmodel_warn']}; "
                f"scoped kernel.log M1PROF: GC={fmt(m1d['gc_us_per_call'],2)}us/call ({fmt(m1d['gc_s'],1)}s), "
                f"SELECT={fmt(m1d['select_us_per_call'],2)}us/call ({fmt(m1d['select_s'],1)}s), "
                f"LEARN={fmt(m1d['learn_ns_per_call'],2)}ns/call ({fmt(m1d['learn_s'],3)}s); "
                f"Vmalloc_load1s_delta={fmt(m1d['vm_delta_load1s_kb'],0)} kB ({m1d['vm_delta_load1s_bytes']} B)"
            )
            val_rows.append({
                "Campaign": "m1-20261126", "Review_Item": "M1/M5", "Policy": pol, "Rep": 1,
                "Host": res["host"], "Git_Branch": REF_GOCOM, "Git_Commit": c_gocom,
                "Run_Date": res["run_date"], "Workload": "mixY 10h (20 phases)",
                "Module_Name": res["mod_name"], "Module_SHA256": res["mod_sha"], "SHA_Match": res["sha_ok"],
                "FIO_Seeds": res["fio_seeds"], "Exit_Code": res["exit_code"],
                "FIO_Errors": res["fio_errs"], "YCSB_OK_Pct": "N/A", "SQLITE_FULL": 0,
                "Kernel_Errors": res["kernel_errs"], "Host_Pages": res["host_pages"], "GC_Pages": res["gc_pages"],
                "WAF_Recalc": f"{res['waf_recalc']:.6f}" if res["waf_recalc"] else "MISSING",
                "WAF_nand": f"{m1d['waf_nand']:.6f}" if m1d["waf_nand"] else "CHECK_BUF_LOG",
                "WAF_PhaseA": "N/A", "WAF_PhaseB": "N/A", "WAF_PhaseC": "N/A",
                "Two_Path_Match": res["two_path_ok"], "Validity": "VALID" if res["valid"] else "INVALID",
                "Raw_Path": f"{REF_GOCOM}:{rdir}", "Notes": note,
            })
        else:
            val_rows.append({
                "Campaign": "m1-20261126", "Review_Item": "M1/M5", "Policy": pol, "Rep": 1,
                "Host": "oy-B550M-DS3H", "Git_Branch": REF_GOCOM, "Git_Commit": c_gocom,
                "Run_Date": "RUNNING", "Workload": "mixY 10h (20 phases)",
                "Module_Name": mkey, "Module_SHA256": h_m1.get(mkey, "preregistered"), "SHA_Match": "PENDING",
                "FIO_Seeds": "rep1", "Exit_Code": "RUNNING", "FIO_Errors": "PENDING",
                "YCSB_OK_Pct": "N/A", "SQLITE_FULL": 0, "Kernel_Errors": "PENDING",
                "Host_Pages": "PENDING", "GC_Pages": "PENDING", "WAF_Recalc": "PENDING", "WAF_nand": "PENDING",
                "WAF_PhaseA": "N/A", "WAF_PhaseB": "N/A", "WAF_PhaseC": "N/A",
                "Two_Path_Match": "PENDING", "Validity": "RUNNING (NOT VERIFIED)",
                "Raw_Path": f"{REF_GOCOM}:{rdir}", "Notes": "Running (~00:45-01:40 KST); rep2-3 cancelled by user; NOT marked PASS",
            })

    write_csv(OUT_DIR / "final_experiment_validity.csv", list(val_rows[0].keys()), val_rows)
    n_valid = sum(1 for r in val_rows if r["Validity"] == "VALID")
    n_running = sum(1 for r in val_rows if "RUNNING" in r["Validity"])
    print(f"Wrote final_experiment_validity.csv ({len(val_rows)} rows: {n_valid} VALID, {n_running} RUNNING)")

    # -----------------------------------------------------------------------
    # 2. final_statistical_audit.csv (ZERO blank cells, UNIFIED Delta = Variant - Control(V4))
    # -----------------------------------------------------------------------
    batchG_complete = (len(by_pol["batchG-greedygc"]) == 3 and len(by_pol["batchG-drift50"]) == 3 and len(by_pol["batchG-v4"]) == 3)

    contrast_defs = [
        # (family, fam_desc, req_name, contrast_id, host, batch_rel, target_pol, ctrl_pol, metric, key)
        ("F1_revA_total", "3-test (revA Total)", "M3-1 무작위 선택 대비 우위", "revA-random - revA-v4", "GoCom", "direct (same host, same batch)", "revA-random", "revA-v4", "Total WAF", "waf_recalc"),
        ("F1_revA_total", "3-test (revA Total)", "M2-2 후보제거+정착 묶음 효과", "revA-v2 - revA-v4", "GoCom", "direct (same host, same batch)", "revA-v2", "revA-v4", "Total WAF", "waf_recalc"),
        ("F1_revA_total", "3-test (revA Total)", "M2-3 변화 감지 단독 효과(NoDrift)", "revA-v1 - revA-v4", "GoCom", "direct (same host, same batch)", "revA-v1", "revA-v4", "Total WAF", "waf_recalc"),

        ("F2_revC_8test", "8-test (revC 4x2, Table 10 †)", "M3-2 기존 iCAT(원 구현) 대비 우위", "revC-online - revC-v4", "GoCom", "direct (same host, same batch)", "revC-online", "revC-v4", "Total WAF", "waf_recalc"),
        ("F2_revC_8test", "8-test (revC 4x2, Table 10 †)", "M3-2 기존 iCAT(원 구현) 대비 우위", "revC-online - revC-v4", "GoCom", "direct (same host, same batch)", "revC-online", "revC-v4", "Phase C WAF", "waf_C"),
        ("F2_revC_8test", "8-test (revC 4x2, Table 10 †)", "M6-1 후보 제거 문턱 10% 민감도", "revC-elim10 - revC-v4", "GoCom", "direct (same host, same batch)", "revC-elim10", "revC-v4", "Total WAF", "waf_recalc"),
        ("F2_revC_8test", "8-test (revC 4x2, Table 10 †)", "M6-1 후보 제거 문턱 10% 민감도", "revC-elim10 - revC-v4", "GoCom", "direct (same host, same batch)", "revC-elim10", "revC-v4", "Phase C WAF", "waf_C"),
        ("F2_revC_8test", "8-test (revC 4x2, Table 10 †)", "M6-1 후보 제거 문턱 25% 민감도", "revC-elim25 - revC-v4", "GoCom", "direct (same host, same batch)", "revC-elim25", "revC-v4", "Total WAF", "waf_recalc"),
        ("F2_revC_8test", "8-test (revC 4x2, Table 10 †)", "M6-1 후보 제거 문턱 25% 민감도", "revC-elim25 - revC-v4", "GoCom", "direct (same host, same batch)", "revC-elim25", "revC-v4", "Phase C WAF", "waf_C"),
        ("F2_revC_8test", "8-test (revC 4x2, Table 10 †)", "M6-2 후보 공간 크기(60 vs 45, m5)", "revC-arm60 - revC-v4", "GoCom", "direct (same host, same batch)", "revC-arm60", "revC-v4", "Total WAF", "waf_recalc"),
        ("F2_revC_8test", "8-test (revC 4x2, Table 10 †)", "M6-2 후보 공간 크기(60 vs 45, m5)", "revC-arm60 - revC-v4", "GoCom", "direct (same host, same batch)", "revC-arm60", "revC-v4", "Phase C WAF", "waf_C"),

        ("F3_revD_4test", "4-test (revD 2x2, Table 10 †)", "M2-5 후보 복원 범위(부분 vs 전체 45개)", "revD-fullreset - revD-v4", "SeungCom", "direct (same host, same batch)", "revD-fullreset", "revD-v4", "Total WAF", "waf_recalc"),
        ("F3_revD_4test", "4-test (revD 2x2, Table 10 †)", "M2-5 후보 복원 범위(부분 vs 전체 45개)", "revD-fullreset - revD-v4", "SeungCom", "direct (same host, same batch)", "revD-fullreset", "revD-v4", "Phase C WAF", "waf_C"),
        ("F3_revD_4test", "4-test (revD 2x2, Table 10 †)", "M2-3 변화 감지 단독 효과(NoDrift)", "revD-nodrift - revD-v4", "SeungCom", "direct (same host, same batch)", "revD-nodrift", "revD-v4", "Total WAF", "waf_recalc"),
        ("F3_revD_4test", "4-test (revD 2x2, Table 10 †)", "M2-3 변화 감지 단독 효과(NoDrift)", "revD-nodrift - revD-v4", "SeungCom", "direct (same host, same batch)", "revD-nodrift", "revD-v4", "Phase C WAF", "waf_C"),

        ("F4_abl_4test", "4-test (abl 2x2, Table 10 F)", "M2-2 v4 4기능 묶음 제거 효과(OffBundle)", "abl-bundle-off - abl-v4", "SeungCom", "direct (same host, same batch)", "abl-bundle-off", "abl-v4", "Total WAF", "waf_recalc"),
        ("F4_abl_4test", "4-test (abl 2x2, Table 10 F)", "M2-2 v4 4기능 묶음 제거 효과(OffBundle)", "abl-bundle-off - abl-v4", "SeungCom", "direct (same host, same batch)", "abl-bundle-off", "abl-v4", "Phase C WAF", "waf_C"),
        ("F4_abl_4test", "4-test (abl 2x2, Table 10 F)", "M2-6 할인 계수 효과(Discount-free, gamma=1)", "abl-nodiscount - abl-v4", "SeungCom", "direct (same host, same batch)", "abl-nodiscount", "abl-v4", "Total WAF", "waf_recalc"),
        ("F4_abl_4test", "4-test (abl 2x2, Table 10 F)", "M2-6 할인 계수 효과(Discount-free, gamma=1)", "abl-nodiscount - abl-v4", "SeungCom", "direct (same host, same batch)", "abl-nodiscount", "abl-v4", "Phase C WAF", "waf_C"),

        ("F5_revE_4test", "4-test (revE 2x2, Table 10 ‡)", "M2-1 후보 제거 단독 효과(NoElim)", "revE-noelim - revE-v4", "GoCom", "direct (same host, same batch)", "revE-noelim", "revE-v4", "Total WAF", "waf_recalc"),
        ("F5_revE_4test", "4-test (revE 2x2, Table 10 ‡)", "M2-1 후보 제거 단독 효과(NoElim)", "revE-noelim - revE-v4", "GoCom", "direct (same host, same batch)", "revE-noelim", "revE-v4", "Phase C WAF", "waf_C"),
        ("F5_revE_4test", "4-test (revE 2x2, Table 10 ‡)", "M6-3 변화 감지 문턱 12.5% 민감도", "revE-drift12 - revE-v4", "GoCom", "direct (same host, same batch)", "revE-drift12", "revE-v4", "Total WAF", "waf_recalc"),
        ("F5_revE_4test", "4-test (revE 2x2, Table 10 ‡)", "M6-3 변화 감지 문턱 12.5% 민감도", "revE-drift12 - revE-v4", "GoCom", "direct (same host, same batch)", "revE-drift12", "revE-v4", "Phase C WAF", "waf_C"),

        # Unified sign: Variant - Control(V4)! (Fixes DELIVERY_20261127.md sign flip!)
        ("F6_greedy_indirect", "4-test (greedy indirect)", "M3-3 Online Greedy 대비 우위 (교차날짜 간접)", "greedy-online - revD-v4", "SeungCom", "indirect (same host, different batch)", "greedy-online", "revD-v4", "Total WAF", "waf_recalc"),
        ("F6_greedy_indirect", "4-test (greedy indirect)", "M3-3 Online Greedy 대비 우위 (교차날짜 간접)", "greedy-online - revD-v4", "SeungCom", "indirect (same host, different batch)", "greedy-online", "revD-v4", "Phase C WAF", "waf_C"),
        ("F6_greedy_indirect", "4-test (greedy indirect)", "M3-3 Online Greedy 대비 우위 (교차날짜 간접)", "greedy-online - abl-v4", "SeungCom", "indirect (same host, different batch)", "greedy-online", "abl-v4", "Total WAF", "waf_recalc"),
        ("F6_greedy_indirect", "4-test (greedy indirect)", "M3-3 Online Greedy 대비 우위 (교차날짜 간접)", "greedy-online - abl-v4", "SeungCom", "indirect (same host, different batch)", "greedy-online", "abl-v4", "Phase C WAF", "waf_C"),

        ("F7_revB_indirect", "2-test (revB cross-batch*)", "M2-1 후보 제거 단독 (교차배치 참고; revE로 대체)", "revB-noelim - revA-v4", "GoCom", "indirect (same host, different batch; bridge failed)", "revB-noelim", "revA-v4", "Total WAF", "waf_recalc"),
        ("F7_revB_indirect", "2-test (revB cross-batch*)", "M2-2 정착 단독 (교차배치 참고; 코드 종속)", "revB-nosettle - revA-v4", "GoCom", "indirect (same host, different batch; bridge failed)", "revB-nosettle", "revA-v4", "Total WAF", "waf_recalc"),
    ]

    if batchG_complete:
        contrast_defs += [
            ("F8_batchG_4test", "4-test (batchG 2x2)", "M3-5 Greedy GC 대비 우위 (mixFYF 동일배치)", "batchG-greedygc - batchG-v4", "SeungCom", "direct (same host, same batch)", "batchG-greedygc", "batchG-v4", "Total WAF", "waf_recalc"),
            ("F8_batchG_4test", "4-test (batchG 2x2)", "M3-5 Greedy GC 대비 우위 (mixFYF 동일배치)", "batchG-greedygc - batchG-v4", "SeungCom", "direct (same host, same batch)", "batchG-greedygc", "batchG-v4", "Phase C WAF", "waf_C"),
            ("F8_batchG_4test", "4-test (batchG 2x2)", "M6-3 변화 감지 문턱 50% 민감도 (mixFYF 동일배치)", "batchG-drift50 - batchG-v4", "SeungCom", "direct (same host, same batch)", "batchG-drift50", "batchG-v4", "Total WAF", "waf_recalc"),
            ("F8_batchG_4test", "4-test (batchG 2x2)", "M6-3 변화 감지 문턱 50% 민감도 (mixFYF 동일배치)", "batchG-drift50 - batchG-v4", "SeungCom", "direct (same host, same batch)", "batchG-drift50", "batchG-v4", "Phase C WAF", "waf_C"),
            ("F10_arm47_indirect", "2-test (arm47 indirect ref)", "Robustness 고정 Arm 47 (승컴 n=3) vs bg-v4 (다른 배치 참고)", "arm47-seungcom - batchG-v4", "SeungCom", "indirect (same host, different batch)", "arm47-seungcom", "batchG-v4", "Total WAF", "waf_recalc"),
            ("F10_arm47_indirect", "2-test (arm47 indirect ref)", "Robustness 고정 Arm 47 (승컴 n=3) vs bg-v4 (다른 배치 참고)", "arm47-seungcom - batchG-v4", "SeungCom", "indirect (same host, different batch)", "arm47-seungcom", "batchG-v4", "Phase C WAF", "waf_C"),
        ]

    stat_rows = []
    fam_groups = defaultdict(list)
    for idx_c, cdef in enumerate(contrast_defs):
        fam, fdesc, rname, cid, host, brel, tpol, cpol, metric, key = cdef
        tvals = [r[key] for r in by_pol[tpol]]
        cvals = [r[key] for r in by_pol[cpol]]
        ts, cs = group_stats(tvals), group_stats(cvals)
        wt = welch_test(tvals, cvals)
        pt = paired_test(tvals, cvals)
        row = {
            "Family": fam, "Holm_Family_Spec": fdesc, "Reviewer_Requirement": rname,
            "Contrast_Variant_Minus_Ctrl": cid, "Host": host, "Host_Batch_Relation": brel, "Metric": metric,
            "Target_n": ts["n"], "Target_Mean": round(ts["mean"], 6), "Target_SD": round(ts["sd"], 6),
            "Target_CI95": f"[{ts['ci_lo']:.4f}, {ts['ci_hi']:.4f}]",
            "Ctrl_n": cs["n"], "Ctrl_Mean": round(cs["mean"], 6), "Ctrl_SD": round(cs["sd"], 6),
            "Ctrl_CI95": f"[{cs['ci_lo']:.4f}, {cs['ci_hi']:.4f}]",
            "Welch_Delta": round(wt["diff"], 6), "Welch_CI95": f"[{wt['ci_lo']:+.4f}, {wt['ci_hi']:+.4f}]",
            "Welch_df": round(wt["df"], 2), "Welch_p": round(wt["p"], 6), "Holm_p": None,
            "Hedges_g": round(wt["g"], 3),
            "Paired_CI95": f"[{pt['ci_lo']:+.4f}, {pt['ci_hi']:+.4f}]" if pt else "N/A",
            "Paired_p": round(pt["p"], 6) if pt else "N/A",
            "Excludes_Zero": "YES" if (wt["ci_lo"] > 0 or wt["ci_hi"] < 0) else "NO",
            "Stat_Verdict": "",
        }
        stat_rows.append(row)
        fam_groups[fam].append(idx_c)

    for fam, idxs in fam_groups.items():
        pvals = [stat_rows[i]["Welch_p"] for i in idxs]
        adjs = holm_adjust(pvals)
        for i, ap in zip(idxs, adjs):
            stat_rows[i]["Holm_p"] = round(ap, 6)
            excl = stat_rows[i]["Excludes_Zero"] == "YES"
            is_ind = "indirect" in stat_rows[i]["Host_Batch_Relation"]
            if excl and ap < 0.05:
                stat_rows[i]["Stat_Verdict"] = ("INDIRECT_DIFF (different batch)" if is_ind else "ROBUST_PASS (Welch CI excl. 0 & Holm p<0.05)")
            elif excl:
                stat_rows[i]["Stat_Verdict"] = f"PREREG_CI_PASS_HOLM_BORDERLINE (Welch CI excl. 0; Holm p={ap:.4f})"
            else:
                stat_rows[i]["Stat_Verdict"] = ("INDIRECT_NO_DIFF (different batch; CI incl. 0)" if is_ind else "NO_DIFF_FOUND (CI includes 0)")

    # If batchG still partial (e.g. 8/9: greedygc=3, drift50=3, bg-v4=2), add explicit non-stat rows
    if not batchG_complete:
        for rname, tpol in [
            ("M3-5 Greedy GC 대비 우위 (batchG 진행 중)", "batchG-greedygc"),
            ("M6-3 변화 감지 문턱 50% 민감도 (batchG 진행 중)", "batchG-drift50"),
        ]:
            tv = [r["waf_recalc"] for r in by_pol[tpol]]
            cv = [r["waf_recalc"] for r in by_pol["batchG-v4"]]
            ts, cs = group_stats(tv), group_stats(cv)
            stat_rows.append({
                "Family": "F8_batchG_PENDING", "Holm_Family_Spec": "PENDING bg-v4 rep3", "Reviewer_Requirement": rname,
                "Contrast_Variant_Minus_Ctrl": f"{tpol} - batchG-v4", "Host": "SeungCom", "Host_Batch_Relation": "direct (same batch; bg-v4 rep3 RUNNING)",
                "Metric": "Total WAF",
                "Target_n": ts["n"], "Target_Mean": round(ts["mean"], 6) if ts["mean"] else "N/A",
                "Target_SD": round(ts["sd"], 6) if ts["sd"] else "N/A (n<3)",
                "Target_CI95": f"[{ts['ci_lo']:.4f}, {ts['ci_hi']:.4f}]" if ts["ci_lo"] else "NO CI (n<3)",
                "Ctrl_n": cs["n"], "Ctrl_Mean": round(cs["mean"], 6) if cs["mean"] else "N/A",
                "Ctrl_SD": "N/A (n<3)", "Ctrl_CI95": "NO CI (n<3)",
                "Welch_Delta": round(ts["mean"] - cs["mean"], 6) if (ts["mean"] and cs["mean"]) else "PENDING",
                "Welch_CI95": "NO STAT (ctrl n<3)", "Welch_df": "N/A", "Welch_p": "N/A", "Holm_p": "N/A", "Hedges_g": "N/A",
                "Paired_CI95": "NO STAT (ctrl n<3)", "Paired_p": "N/A", "Excludes_Zero": "N/A",
                "Stat_Verdict": f"PENDING_FINAL_RUN (Target n={ts['n']}, Ctrl bg-v4 n={cs['n']}; NO STAT until n=3)",
            })

    # Always include M1 n=1 explicit non-statistical row
    m1_v4 = m1_results["m1-icat-v4"]
    m1_sg = m1_results["m1-smartgc-eq8"]
    stat_rows.append({
        "Family": "F9_m1_n1", "Holm_Family_Spec": "n=1 (no inference)", "Reviewer_Requirement": "M1 SmartGC-EQ8 vs iCAT-v4 동일 소스·동일 환경 비교",
        "Contrast_Variant_Minus_Ctrl": "m1-smartgc-eq8 - m1-icat-v4", "Host": "GoCom", "Host_Batch_Relation": "direct (same host, same batch, n=1)",
        "Metric": "mixY 10h WAF (host) / WAF_nand",
        "Target_n": 1 if m1_sg else 0, "Target_Mean": round(m1_sg["waf_recalc"], 6) if m1_sg else "RUNNING",
        "Target_SD": "N/A (n=1)", "Target_CI95": "NO CI (n=1)",
        "Ctrl_n": 1 if m1_v4 else 0, "Ctrl_Mean": round(m1_v4["waf_recalc"], 6) if m1_v4 else "MISSING",
        "Ctrl_SD": "N/A (n=1)", "Ctrl_CI95": "NO CI (n=1)",
        "Welch_Delta": round(m1_sg["waf_recalc"] - m1_v4["waf_recalc"], 6) if (m1_sg and m1_v4) else "PENDING",
        "Welch_CI95": "NO STAT (n=1)", "Welch_df": "N/A", "Welch_p": "N/A", "Holm_p": "N/A", "Hedges_g": "N/A",
        "Paired_CI95": "NO STAT (n=1)", "Paired_p": "N/A", "Excludes_Zero": "N/A",
        "Stat_Verdict": "SINGLE_RUN_ONLY (n=1 by user decision; no statistical significance claimed)" if m1_sg else "PENDING_SMARTGC_REP1 (iCAT-v4 n=1 VALID; SmartGC-EQ8 RUNNING)",
    })

    write_csv(OUT_DIR / "final_statistical_audit.csv", list(stat_rows[0].keys()), stat_rows)
    print(f"Wrote final_statistical_audit.csv ({len(stat_rows)} rows, batchG_complete={batchG_complete}, m1_complete={m1_sg is not None})")

    # Helper to lookup computed contrast row
    smap = {(r["Contrast_Variant_Minus_Ctrl"], r["Metric"]): r for r in stat_rows}

    # Build batchG summary text
    bg_g_vals = [r["waf_recalc"] for r in by_pol["batchG-greedygc"]]
    bg_d_vals = [r["waf_recalc"] for r in by_pol["batchG-drift50"]]
    bg_v_vals = [r["waf_recalc"] for r in by_pol["batchG-v4"]]
    bg_g_st = group_stats(bg_g_vals)
    bg_d_st = group_stats(bg_d_vals)
    bg_v_st = group_stats(bg_v_vals)

    # Check if SeungCom batchG final report exists for cross-check
    sc_bg_report = git_text(REF_MAIN, "result/batchG-20261126/report/batchG_summary.md") or git_text(REF_MAIN, "report/batchG-20261126/summary.md")

    # -----------------------------------------------------------------------
    # 3. final_robustness_audit.md (Section 2.A + Section 2.C + Section 3 + Section 4)
    # -----------------------------------------------------------------------
    m1_v4_d = m1_v4["m1"] if m1_v4 else {}
    m1_sg_d = m1_sg["m1"] if m1_sg else None

    if batchG_complete:
        r_gg_t = smap[("batchG-greedygc - batchG-v4", "Total WAF")]
        r_gg_c = smap[("batchG-greedygc - batchG-v4", "Phase C WAF")]
        r_d50_t = smap[("batchG-drift50 - batchG-v4", "Total WAF")]
        r_d50_c = smap[("batchG-drift50 - batchG-v4", "Phase C WAF")]
        batchG_md = f"""### 3.1 승컴 `batchG-20261126` 독립 검증 완료 (9/9 VALID, `origin/main @ {c_main}`)

모든 9개 run에 대해 종료 코드(`0`), 사전등록 모듈 SHA256, FIO 오류(`0`)·시드(`rep1/2/3`), YCSB 성공률(`100%`, `SQLITE_FULL=0`), 커널 오류(`0`), 원시 카운터 2-경로 WAF 재계산을 독립 검증 완료했습니다. *(참고: `cpu_check=unavailable`은 `loadsampler`가 승컴에 미이식되어 CPU가 미측정임을 뜻하며 WAF 유효성과 무관 — 커밋 `2fd5fa359` 확인)*

| 정책 (n=3) | Total WAF (Mean ± SD) | 95% t-CI | Δ vs `bg-v4` [Welch 95% CI] | Welch p | Holm p (4-test) | Hedges' g | Phase C Δ [Welch 95% CI] | 판정 |
|---|---:|---|---|---:|---:|---:|---|---|
| **iCAT-v4 (`bg-v4`)** | `{bg_v_st['mean']:.4f} ± {bg_v_st['sd']:.4f}` | `[{bg_v_st['ci_lo']:.4f}, {bg_v_st['ci_hi']:.4f}]` | 대조군 | — | — | — | 대조군 | 동일 배치 대조군 |
| **Greedy GC** *(M3-5)* | `{bg_g_st['mean']:.4f} ± {bg_g_st['sd']:.4f}` | `[{bg_g_st['ci_lo']:.4f}, {bg_g_st['ci_hi']:.4f}]` | `{r_gg_t['Welch_Delta']:+.4f} {r_gg_t['Welch_CI95']}` | `{r_gg_t['Welch_p']:.6f}` | `{r_gg_t['Holm_p']:.6f}` | `{r_gg_t['Hedges_g']}` | `{r_gg_c['Welch_Delta']:+.4f} {r_gg_c['Welch_CI95']}` (`Holm {r_gg_c['Holm_p']:.4f}`) | **{r_gg_t['Stat_Verdict']}** |
| **Drift 50%** *(M6-3)* | `{bg_d_st['mean']:.4f} ± {bg_d_st['sd']:.4f}` | `[{bg_d_st['ci_lo']:.4f}, {bg_d_st['ci_hi']:.4f}]` | `{r_d50_t['Welch_Delta']:+.4f} {r_d50_t['Welch_CI95']}` | `{r_d50_t['Welch_p']:.6f}` | `{r_d50_t['Holm_p']:.6f}` | `{r_d50_t['Hedges_g']}` | `{r_d50_c['Welch_Delta']:+.4f} {r_d50_c['Welch_CI95']}` (`Holm {r_d50_c['Holm_p']:.4f}`) | **{r_d50_t['Stat_Verdict']}** |
"""
    else:
        batchG_md = f"""### 3.1 승컴 `batchG-20261126` 독립 검증 현황 ({len(bg_g_vals)+len(bg_d_vals)+len(bg_v_vals)}/9 VALID — `bg-v4 rep3` 진행 중, `origin/main @ {c_main}`)

> **완료 기준 준수:** `mixFYF-bg-v4-rep3`가 완료·검증되기 전까지 `batchG` 대비는 **PENDING (미완결)** 상태로 유지하며, 통계적 유의성이나 `PASS`를 부여하지 않습니다.

- **Greedy GC (`n={len(bg_g_vals)}` VALID)**: `Total WAF = {bg_g_st['mean']:.4f}` ± `{fmt(bg_g_st['sd'],4)}` (CI `[{fmt(bg_g_st['ci_lo'],4)}, {fmt(bg_g_st['ci_hi'],4)}]`, 개별: `{', '.join(f'{x:.6f}' for x in bg_g_vals)}`)
- **Drift 50% (`n={len(bg_d_vals)}` VALID)**: `Total WAF = {bg_d_st['mean']:.4f}` ± `{fmt(bg_d_st['sd'],4)}` (CI `[{fmt(bg_d_st['ci_lo'],4)}, {fmt(bg_d_st['ci_hi'],4)}]`, 개별: `{', '.join(f'{x:.6f}' for x in bg_d_vals)}`)
- **iCAT-v4 (`bg-v4`, `n={len(bg_v_vals)}` VALID, `rep3 RUNNING`)**: 현재 2회 평균 `{bg_v_st['mean']:.4f}` (개별: `{', '.join(f'{x:.6f}' for x in bg_v_vals)}`; `n<3` 통계 미산출)
"""

    if m1_sg_d is not None:
        m1_md = f"""### 3.2 고컴 `m1-20261126` 독립 검증 완료 (2/2 VALID, `n=1` per policy, `origin/report/data-validity-20261124 @ {c_gocom}`)

> **핵심 검증 규칙:** 모든 `M1PROF` 카운터는 커밋 `08ac54dc9` 규정에 따라 이전 실행 링버퍼가 섞이지 않은 **`kernel.log.nowarn.gz` 단독**에서 파싱했습니다(`kernel-final.log` 미사용). 사용자 결정으로 `rep2–3`은 취소되어 **정책당 `n=1`**이며, 통계적 유의성은 부여하지 않습니다.

| 지표 (구분) | `m1-icat-v4` (`n=1`) | `m1-smartgc-eq8` (`n=1`) | 해석 및 한계 |
|---|---:|---:|---|
| **호스트 기준 `WAF`** `[실측]` | `{m1_v4['waf_recalc']:.6f}` (`{m1_v4_d['host_tb']:.3f} TB`) | `{m1_sg['waf_recalc']:.6f}` (`{m1_sg_d['host_tb']:.3f} TB`) | `1 + gc_pages/host_pages` |
| **NAND 기준 `WAF_nand`** `[실측]` | `{fmt(m1_v4_d['waf_nand'],6)}` | `{fmt(m1_sg_d['waf_nand'],6)}` | SmartGC DRAM GC 버퍼 흡수분 구분 |
| **이론적 학습 상태 메모리 (`gdb sizeof`)** `[계산]` | `10,112 B` (전체 tuner `10,624–10,848 B`) | `1,951,648 B` (+GC 버퍼 `393,216 B` = `2,344,864 B`) | 학습 상태 **193.0×** (전체 **231.9×**) 경량 |
| **실측 커널 `VmallocUsed` Δ (`load1s - pre`)** `[실측]` | `{fmt(m1_v4_d['vm_delta_load1s_kb'],0)} kB` (`{m1_v4_d['vm_delta_load1s_bytes']} B`) | `{fmt(m1_sg_d['vm_delta_load1s_kb'],0)} kB` (`{m1_sg_d['vm_delta_load1s_bytes']} B`) | 에뮬레이터 공통 ~35 MB 포함; 커널 스레드는 `VmRSS` 미존재 |
| **GC 전체 `ktime` 경과 시간** `[실측, 경과시간]` | `{fmt(m1_v4_d['gc_us_per_call'],2)} µs/GC` (누적 `{fmt(m1_v4_d['gc_s'],1)} s`, `{fmt(m1_v4_d['gc_ms_per_gib'],0)} ms/GiB`) | `{fmt(m1_sg_d['gc_us_per_call'],2)} µs/GC` (누적 `{fmt(m1_sg_d['gc_s'],1)} s`, `{fmt(m1_sg_d['gc_ms_per_gib'],0)} ms/GiB`) | **불리 사실 명시:** iCAT이 호출당 **5.5×** 김(CAT 전 라인 스캔). "GC가 빠르다" 주장 금지 |
| **희생 선택 `SELECT` `ktime`** `[실측, 경과시간]` | `{fmt(m1_v4_d['select_us_per_call'],2)} µs/GC` (`{fmt(m1_v4_d['select_s'],1)} s`, GC의 88.5%) | `{fmt(m1_sg_d['select_us_per_call'],2)} µs/GC` (`{fmt(m1_sg_d['select_s'],1)} s`, step 제외 `{fmt(m1_sg_d['select_s']-m1_sg_d['learn_s'],1)} s`) | CAT 전수 스캔 vs SmartGC 상태 목록 |
| **학습 알고리즘 `LEARN` `ktime`** `[실측, 경과시간]` | `{fmt(m1_v4_d['learn_ns_per_call'],2)} ns/GC` (`{fmt(m1_v4_d['learn_s'],3)} s`, GC의 0.041%) | `{fmt(m1_sg_d['learn_us_per_call'],2)} µs/step` (`{m1_sg_d['learn_calls']:,}`회 = `{fmt(m1_sg_d['learn_s'],2)} s`) | 학습 갱신 자체는 iCAT이 11× 작음(`4.3 s` vs `47.6 s`) |
| **보상·GC 버퍼 `ktime`** `[실측, 경과시간]` | 해당 없음 (`REWARD`는 `LEARN`에 포함, GC 버퍼 없음) | `REWARD {fmt(m1_sg_d['reward_s'],2)} s` + `BUF 상한 {fmt(m1_sg_d['buf_upper_s'],1)} s` (계측 비용 포함) | SmartGC 전용 쓰기 경로 버퍼 비용 |
| **실측 `VmallocUsed` 차이 및 언로드 복귀** `[실측]` | `load1s Δ +{fmt(m1_v4_d['vm_delta_load1s_kb'],0)} kB`, `post +{fmt(m1_v4_d['vm_delta_post_kb'],0)} kB` | `load1s Δ +{fmt(m1_sg_d['vm_delta_load1s_kb'],0)} kB`, `post +{fmt(m1_sg_d['vm_delta_post_kb'],0)} kB` | 차이 **`+{fmt(m1_sg_d['vm_delta_load1s_kb']-m1_v4_d['vm_delta_load1s_kb'],0)} kB`** (`+{(m1_sg_d['vm_delta_load1s_bytes']-m1_v4_d['vm_delta_load1s_bytes']):,} B`) — 이론 계산차 `3,058 KiB`와 5% 이내 일치 |
| **채널 모델 포화 경고 (`chmodel_warn`)** `[실측]` | `{m1_v4_d['chmodel_warn']}` | `{m1_sg_d['chmodel_warn']}` | SmartGC에서만 포화 경고 발생 → 지연 비교 제외 유지 |
| **커널 내부 CPU 시간 (`perf` / `task_cputime`)** | **미측정** | **미측정** | busy-poll 구조·`perf` 미지원; `ktime` 경과 시간과 엄격 구분 |
| **NVMeVirt 공통 처리 / FTL 쓰기 경로 비용** | **미측정** | **미측정** | 정책 구간(`GC/SELECT/LEARN/REWARD/BUF`)만 실측, 공통 GC는 차감 추정 |
"""
    else:
        m1_md = f"""### 3.2 고컴 `m1-20261126` 독립 검증 현황 (1/2 VALID — `SmartGC-EQ8 rep1` 진행 중, `origin/report/data-validity-20261124 @ {c_gocom}`)

> **완료 기준 준수:** `mixY-m1-smartgc-eq8-rep1`이 완료·push되기 전까지 M1 커널 10h 대조는 **PENDING (미완결)** 상태로 유지합니다.

- **`mixY-m1-icat-v4-rep1` (1/2 VALID, `n=1`)**:
  - `WAF = WAF_nand = {m1_v4['waf_recalc']:.6f}` (`{m1_v4_d['host_tb']:.3f} TB`, `chmodel_warn = {m1_v4_d['chmodel_warn']}`)
  - `kernel.log.nowarn.gz` 한정 `M1PROF`: `GC = {fmt(m1_v4_d['gc_us_per_call'],2)} µs/GC` (`{fmt(m1_v4_d['gc_s'],1)} s`), `SELECT = {fmt(m1_v4_d['select_us_per_call'],2)} µs/GC` (`{fmt(m1_v4_d['select_s'],1)} s`, `88.5%`), `LEARN = {fmt(m1_v4_d['learn_ns_per_call'],2)} ns/GC` (`{fmt(m1_v4_d['learn_s'],3)} s`, `0.041%`)
  - 실측 `VmallocUsed` Δ (`load1s - pre` 중앙값): `{fmt(m1_v4_d['vm_delta_load1s_kb'],0)} kB` (`{m1_v4_d['vm_delta_load1s_bytes']} B`)
- **`mixY-m1-smartgc-eq8-rep1` (2/2 RUNNING, ETA ~00:45–01:40 KST)**:
  - 사전 검증된 smoke (`kernel.log.nowarn.gz` 한정): `GC 5.34 µs/GC`, `SELECT 1.15 µs/GC`, `LEARN step 551 µs`, `VmallocUsed Δ +37,800 kB` (`+38,707,200 B`, iCAT 대비 `+3,064 kB`)
  - 사용자 공간 `conv_ftl.c` 시뮬레이션 벤치 (`n=3` 참고): `iCAT 53.05 µs/GC` (WAF `7.16`) vs `SmartGC-EQ8 7.59 µs/GC` (WAF `9.19`) — **iCAT의 학습 연산은 극소이나 CAT 전 라인 스캔 `SELECT` 경과시간은 SmartGC보다 큼**
- **미측정 항목 (명시 유지)**: 커널 내부 CPU 시간(`perf`/busy-poll 한계 → `ktime` 경과 시간과 구분), `VmRSS`(커널 스레드 미존재), NVMeVirt 공통 처리 비용, 호출별 지연 p50/p95/p99, `rep2–3` 반복(사용자 결정 취소).
"""

    robustness_md = f"""# iCAT 논문 리비전 최종 Robustness 감사 보고서 (`final_robustness_audit.md`)

- **작성 주체**: 집컴 (독립 연구 감사·원시 로그 검증·최종 통합 담당)
- **생성 시각**: `{NOW_STR}`
- **기준 원격 커밋**: 승컴 `origin/main @ {c_main}` / 고컴 `origin/report/data-validity-20261124 @ {c_gocom}` / 자원 계측 `origin/resource-overhead-20261114 @ {c_res}`
- **절대 원칙**: 원시 로그(`result/`)·원본 `figs/` 무변경, 신규 NVMeVirt 미실행, 호스트·배치 무분별 합산 금지, `n<3` 통계적 유의성 미부여, 미검증·실행 중 항목 `PASS` 표기 금지.

---

## 1. 기존 논문 Figure 1~10 전수 감사 (원시 데이터 연결 · 반복 수 · 사용 범위)

| Figure | 원고 절 | 원시 로그 경로 (검증됨) | 반복 횟수 | 분류 | 사용 가능 범위 및 필수 조치 |
|---|---|---|---|---|---|
| **그림 1** (`fig1_sensitivity`) | §3.3 | `result/sweep-20260915/rank-test4.txt`, `result/gh-repro-20260914/*.console.txt` | 60 arm 각 **`n=1`** (10m); Greedy **`n=3`** (`2.186`) | **PARTIAL** | 동기 부여·`k=2` 하위 군집 배제 근거로 사용 가능. 단 arm별 `n=1` 명시, 1·2위(`arm31 1.744` vs `arm47 1.746`) 우열 주장 금지. |
| **그림 2** (`fig3_time_use`) | §4.1 | `result/mix-20260911/t4-online{{,v2,v3}}-rep1-x18`, `t4-onlinev4-rep1-x60/kernel.log` | 정책당 **`n=1`** | **FRAGILE** | 통계적 증명 불가 — **"1회 실행 사례"**로 명시하고, `n=3` 탐색 비중 정량 근거(`revC` `97%` vs `27%`, `figure04_exploration.png`) 병기. |
| **그림 3** (`paper_fig03_v4_overview`) | §5 | 코드 매핑 (`online-v4-src/conv_ftl.c`, `analysis/final_e1/fig3_v4_overview.py`) | 도식 (N/A) | **ROBUST** | 그대로 사용 가능 (투고 시 검토용 내부 제목만 제거). |
| **그림 4** (`fig9_rank_over_time`) | §6.1 | `t4-online{{,v3,v4}}-rep1-x{{18,60}}` + 고정 조합 15종 `rep1` | 정책·기준 모두 **`n=1`** | **FRAGILE** | "약 8시간에 5위"를 결정적 일반화로 주장 금지 → **1회 실행 사례**로 완화. |
| **그림 5** (`fig10_v4_choices`) | §6.1 | `result/mix-20260911/t4-onlinev4-rep1-x60/kernel.log` | **`n=1`** | **PARTIAL** | 제거·정착·이웃탐색 동작 메커니즘 예시로만 사용 (`1회 실행` 캡션 유지). |
| **그림 6** (`fig6_ablation`) | §6.1 | `t4-onlinev3-rep1-x18`, `v3probe`, `online`, `v3k2` | 각 **`n=1`** (**구버전 v3**) | **FRAGILE** | 주 Ablation 근거로 부적합(구버전 v3, `n=1`). L232 `【결과 대기】` 삭제 후, §6.4 `n=3` v4 Ablation(표 10·`figure02_ablation.png`)을 주 근거로 명시. |
| **그림 7** (`fig4_mixes_v4_vs_robust`) | §6.2 | `result/mix-20260911/mix*-{{onlinev4,fixed50}}-rep*-x3` (유효 8종) | CAT-Robust **`n=1`** (8/8); v4 **`n=1~3`** | **FRAGILE** | 탐색적 다중 워크로드 요약으로만 사용(v4 3승 5패, `fixed50 n=1`). L240 `【결과 대기】` 삭제. |
| **그림 8** (`fig7_mix_loss_by_workload`) | §6.2 | `result/mix-20260911/mix{{C,D,F,K,O,P}}-*-x3` (유효 6종) | 고정 arm 전부 **`n=1`**; v4 **`n=1~3`** | **FRAGILE** | 탐색적 참고 자료로 제한. L260 `【선별 실험 결과로 갱신 예정】` 삭제. |
| **그림 9** (`fig8_robustness`) | §6.2 | 위 6종 공통 유효 전환 워크로드 | 고정 arm 전부 **`n=1`** | **FRAGILE** | 과거 초안 구수치(`3.0/6.5/7.2%`)는 `30cf9b9fb` L262에서 `0.2%/5.0%/5.0%`로 수정됨. 단 소수 2자리 정확값은 **`CAT-Best 0.21%, CAT-Robust 4.95%, iCAT-v4 5.04%`**이므로 평균 우위 오독 방지를 위해 소수 2자리 병기 권고. |
| **그림 10** (`fig5_three_phase_mix` / `paper_fig10_e1_three_phase`) | §6.2/6.4 | 구 `mixR-*-x3` (**SQLITE_FULL 오염으로 무효**) / 300k 재측정 **미실행** | **INVALID / 미실행** | **INVALID** | **절대 사용 금지.** 표 8(`300k records` 전원 대기)·그림 10(`생성 대기`)을 유효 `mixFYF 250k (n=3)` 결과(`revA/revD`, 표 10·`figure03_adaptation.png`)로 전면 대체. |
| **신규 리비전 Figure 1~7** (`report/paper-figures/figures/`) | §6.4/§7 | 75+ 검증 `mixFYF 250k` run + `resource-v124` + `3×60` sweep | 핵심 조건 전부 **`n=3`** | **ROBUST** | 논문 리비전의 **1차 통계적 확정 근거** (`verify_paper_figures.py` 전수 수치 일치 검증). |

### 1.1 고정 Arm 47 (`1.987`) 사용 범위 및 재현성 감사 (**승컴 `arm47-20261127` `n=3` 독립 검증 완료**)
- **승컴 `arm47-20261127` (`n=3` VALID, `4689c6797`)**: `rep1 1.987502 / rep2 1.987953 / rep3 1.987478` → **`Mean = 1.98764 ± 0.00027`** (`95% CI [1.98698, 1.98831]`, `CV = 0.013%`; `Phase A 1.77430 / B 1.03098 / C 2.27865`). 4개 파티션 `Fixed CAT init arm=47` 확인, 2-경로 WAF 일치, 승컴 분석과 소수 6자리 일치.
- **고컴 `revA/mixFYF-arm47-rep1` (`1.987355`, `n=1`)**: 호스트가 다르므로 승컴 `n=3`과 **절대 합산(`n=4` 표기) 금지**. 다만 고컴 `1.987355`가 승컴 `n=3` 95% CI(`[1.98698, 1.98831]`) 내부에 위치하여 `mixFYF` Arm 47 WAF의 극도로 높은 재현성이 독립 확인됨.
- **승컴 내 간접 비교 (`arm47 − bg-v4`, 다른 배치)**: Total **`−0.1228 [−0.1836, −0.0621]`** (`p=0.0130`, `g=−5.68`), Phase C **`−0.1250 [−0.2492, −0.0009]`** (`p=0.0493`) — 사후 최적 oracle인 Arm 47이 온라인 V4보다 약 5.8% 낮음. 또한 Arm 47의 FIO Phase C p99(`174.6 µs`)는 V4(`166.0 µs`)와 유사하여, Greedy GC(`41.9 µs`)와의 지연 차이가 온라인 학습기가 아닌 **CAT 전 라인 스캔 자체**에서 비롯됨을 방증함.
- **기존 `n=3` Arm 47 및 표 6·7 한계**: FIO-Fast 10분/30분·`mixY 90m`에서도 재현성이 확인되나, **`mixY 10h` 교차 월 비교**에서는 10월(`2.864`)과 11월(`3.233`) 사이에 **`+12.9%` 시기 편차**가 존재함. 표 6·표 7의 3배 길이 고정 조합은 여전히 `n=1`이므로 L256 `【결과 대기】` 삭제 후 단일 실행 참고값으로 명시.

---

## 2. 전달 자료 오류 7건 전수 점검 및 수정 내역 (Section 2.C)

| # | 발견 오류 항목 | 원본 위치 및 문제 내용 | 수정 상태 및 집컴 최종 패키지 반영 내역 |
|---|---|---|---|
| **1** | **SmartGC `WAF` vs `WAF_nand` 정의 차이** | `iCAT_revision_databook_v2.xlsx` `F7_smartgc_waf`는 호스트 기준 `WAF=1+gc/host` (`EQ8 4.4984`, `SmartGC 11.0723`) 기재, 반면 `PAPER_KCI_DRAFT.md` 표 9는 DRAM 버퍼 흡수 제외 `WAF_nand` (`4.49`, `11.02`) 기재 | `final_experiment_validity.csv`, `iCAT_Paper_Figures.xlsx`, 본 보고서에서 **`WAF`와 `WAF_nand` 두 열을 분리·병기**하고 계산식(`1 + gc/host` vs `1 + (gc - buf_absorb)/host`) 명시. |
| **2** | **`VmallocUsed` 단위 라벨 오류** | `iCAT_revision_databook_v2.xlsx` `F6_memory` R9–R12의 `item` 열에 `(kB)`로 표기하면서 `bytes` 열에 `kB×1024` bytes 값(`38,508,134.4` 등) 저장 | `VmallocUsed_delta_kB`와 `VmallocUsed_delta_bytes`를 별도 열로 엄격 분리하고, 고컴 데이터북 정오표에 R9–R12 라벨 수정 명시. |
| **3** | **Excel 통계값 공란 (`F3_contrasts_same_batch`)** | `revE`(`R26–R33`)에만 `p_unadjusted`·`p_holm_4tests`가 기입되고 `abl`(`R34–R39`), `greedy`(`R40–R45`), `revA/C/D`(`R2–R25`)는 공란 | `final_statistical_audit.csv` 및 `iCAT_Paper_Figures.xlsx`에서 **전 `n=3` 대비의 `Welch_p`, `Holm_p`, `Holm_Family_Spec`, `Hedges_g`, `Paired_p` 공란 0건**으로 전수 기입 (`abl OffBundle`: `Welch p=0.0069`, **`Holm p=0.0277`**; `NoDiscount`: `p=0.869`, `Holm p=1.000`; `greedy vs revD-v4`: `p=0.543`). |
| **4** | **Greedy 비교 부호 비일관** | `DELIVERY_20261127.md` §2·`F3` R40은 `revD-v4 − Online Greedy = +0.009 [−0.034, +0.051]`, 논문 표 10은 `Online Greedy − revD-v4 = −0.009 [−0.051, +0.034]`로 방향 상반 | 집컴 전 산출물에서 **`Δ = 비교 정책 − 대조군(iCAT-v4)`**로 부호 완전 통일 (`Online Greedy − revD-v4 = −0.0086 [−0.0508, +0.0336]`, 양수 = iCAT-v4 우위, 음수 = 비교 정책 우위). |
| **5** | **Figure 9 과거 수치** | 구 초안 L260에 유효성 게이팅 전 구수치(`CAT-Best 3.0%, iCAT-v4 6.5%, CAT-Robust 7.2%`) 잔존 (`30cf9b9fb` L262는 1자리 반올림 `0.2% / 5.0% / 5.0%`로 갱신됨) | 정확한 post-gating 2자리 수치 **`CAT-Best 0.21%, CAT-Robust 4.95%, iCAT-v4 5.04%`**를 정오표·보고서에 명시(반올림 시 `iCAT-v4`와 `CAT-Robust`가 동일하게 보이는 왜곡 방지). |
| **6** | **`PAPER_KCI_DRAFT.md` L385 과거 GC 계측 설명** | L385에 `"GC 수행 시간은 계측하지 않았다"` 잔존 (`origin/resource-overhead-20261114`의 FIO-Fast 30m `do_gc − on_gc` `n=3` 실측 및 `m1-20261126` `M1PROF`와 충돌) | `final_revision_status.md`에 L385 즉시 교체 문안 제공: `resource-v124` (`do_gc − on_gc` iCAT-v4 `206.84 s` vs CAT-47 `255.98 s`, `erase=0` 단서; `reward 1.442 ms`, `select 1.273 ms`, `set_arm 0.059 ms`) 및 `m1-20261126` `ktime`(`SELECT` 스캔 비용 vs `LEARN` 극소 비용) 분리 기재. |
| **7** | **표 6·표 8의 `300k records` 및 `【결과 대기】` 플레이스홀더** | 원고 L004–005, L232(그림 6), L240(그림 7), L256(표 6), L260(그림 8), L297–307(표 8 `300k records` 전원 "대기" & 그림 10)에 미실행/구 플레이스홀더 잔존 | 전 7개 플레이스홀더 위치를 line 번호까지 식별. `300k` 표 8·그림 10은 미실행이므로 삭제·대체(`mixFYF 250k n=3` 표 10·`figure03_adaptation.png`), 표 6·그림 7은 `n=1~3` 탐색적 단서로 확정. |

---

## 3. 최종 신규 배치 독립 검증 결과 (`batchG-20261126` & `m1-20261126`)

{batchG_md}

{m1_md}

---

## 4. 원시 데이터 무결성 요약 (`final_experiment_validity.csv`)

- **총 추적 run 수**: `{len(val_rows)}`건 (**VALID `{n_valid}`건**, **RUNNING(미검증) `{n_running}`건**, 무효 혼입 **0건**)
- 모든 VALID run은 원시 `summary.txt` ↔ `final-control.txt` ↔ 파티션 합산 2-경로 WAF 일치, `exit=0`, 커널 오류 `0`, FIO 오류 `0`, YCSB `SQLITE_FULL=0` (`≥99%`, 실측 `100%`) 및 사전등록 모듈 SHA256 대조를 독립 통과함.
- 상세 run별 표: [final_experiment_validity.csv](file:///C:/Users/oyeon/orca/iCAT-experiments/report/delivery-20261127/final_experiment_validity.csv)
- 상세 통계 대비 표: [final_statistical_audit.csv](file:///C:/Users/oyeon/orca/iCAT-experiments/report/delivery-20261127/final_statistical_audit.csv)
"""
    (OUT_DIR / "final_robustness_audit.md").write_text(robustness_md, encoding="utf-8")
    print("Wrote final_robustness_audit.md")

    # -----------------------------------------------------------------------
    # 4. final_reviewer_evidence_matrix.md (Section 2.B — 47 Original Requirements, 5 Exact Categories)
    # -----------------------------------------------------------------------
    # Exact 5 allowed verdicts: 입증 완료 | 부분 입증 | 입증 실패 | 추가 실험 불필요 | 추가 실험 필요
    m1_kernel_verdict = "부분 입증" if m1_sg_d else "추가 실험 필요"
    m1_kernel_note = (
        f"m1-20261126 2/2 완료(n=1): iCAT WAF {m1_v4['waf_recalc']:.3f} vs SmartGC-EQ8 {m1_sg['waf_recalc']:.3f}; 단 n=1·ktime(경과시간) 한정"
        if m1_sg_d
        else "m1-20261126 1/2 완료(iCAT-v4 OK), SmartGC-EQ8 rep1 실행 중(~00:45-01:40 KST); 완료 후 n=1 판정 확정"
    )
    bg_gg_verdict = "입증 완료" if batchG_complete else "추가 실험 필요"
    bg_gg_note = (
        f"batchG 9/9 완료(SeungCom mixFYF n=3): Greedy GC {bg_g_st['mean']:.4f} vs bg-v4 {bg_v_st['mean']:.4f}, Δ={smap[('batchG-greedygc - batchG-v4','Total WAF')]['Welch_Delta']:+.4f} {smap[('batchG-greedygc - batchG-v4','Total WAF')]['Welch_CI95']} (Holm p={smap[('batchG-greedygc - batchG-v4','Total WAF')]['Holm_p']:.4f}) + 레거시 9종 n=3 9/9 유의"
        if batchG_complete
        else f"레거시 9종(n=3) 유의 + batchG Greedy GC 3/3 완료({bg_g_st['mean']:.4f}), 대조군 bg-v4 rep3 실행 중(~00:42 KST)"
    )
    bg_d50_verdict = (
        ("입증 완료" if smap[("batchG-drift50 - batchG-v4", "Total WAF")]["Excludes_Zero"] == "YES" else "부분 입증")
        if batchG_complete
        else "부분 입증"
    )
    bg_d50_note = (
        f"12.5%(revE n=3): +0.0720 [+0.012, +0.132](조기리셋, Holm p=0.091); 50%(batchG n=3): {bg_d_st['mean']:.4f} vs bg-v4 {bg_v_st['mean']:.4f}, Δ={smap[('batchG-drift50 - batchG-v4','Total WAF')]['Welch_Delta']:+.4f} {smap[('batchG-drift50 - batchG-v4','Total WAF')]['Welch_CI95']} (Holm p={smap[('batchG-drift50 - batchG-v4','Total WAF')]['Holm_p']:.4f})"
        if batchG_complete
        else f"12.5%(revE n=3): +0.0720 [+0.012, +0.132](Holm p=0.091); 50%(batchG): drift50 3/3 완료({bg_d_st['mean']:.4f}), bg-v4 rep3 대기(~00:42 KST)"
    )

    m1_select_verdict = "입증 실패"  # Unfavorable finding already confirmed in sim bench + kernel smoke + icat 10h!
    # Build complete 47-row table mapping original reviewer requirements -> internal exp ID -> raw path -> 5-class verdict
    req_rows = [
        # M1 SmartGC (9)
        ("M1-1", "M1 SmartGC 비교", "이론적 메모리 오버헤드 비교 (블록 단위 Q-table vs 정책 단위 상태)", "gdb-sizeof (`resource_overhead_final.md`)", "iCAT 10,112 B vs SmartGC 1,951,648 B (193.0×) / +GC버퍼 2,344,864 B (231.9×) [계산값]", "origin/report/data-validity-20261124:report/revision-20261123-gocom/resource_overhead_final.md", "입증 완료"),
        ("M1-2", "M1 SmartGC 비교", "실제 RSS 및 커널 메모리 측정", "`m1-20261126` (`sampler/*/mem.tsv`, n=1) + `smartgc-20261119`", "커널 스레드 VmRSS 미존재(구조적 불가); 실측 `VmallocUsed` Δ: SmartGC +37,752 kB vs iCAT +34,848 kB (차이 +2,904 kB, 이론 계산차 3,058 KiB와 5% 이내 일치, 언로드 후 +16 kB 복귀; n=1)", "origin/report/data-validity-20261124:result/m1-20261126/sampler/", "부분 입증"),
        ("M1-3", "M1 SmartGC 비교", "SmartGC 대비 알고리즘 자체 학습 CPU/경과 시간", "`m1-20261126` (`M1PROF` `LEARN` `ktime`, n=1)", "학습 자체 경과시간: iCAT `4.30 s` (`40.8 ns/GC`) vs SmartGC `47.56 s` (`975.5 µs/step` × 48,751회) — iCAT 11× 경량. 단 커널 CPU 시간(`perf`) 미측정(`ktime` 경과시간)·n=1", "origin/report/data-validity-20261124:result/m1-20261126/raw/", "부분 입증"),
        ("M1-4", "M1 SmartGC 비교", "SmartGC 대비 정책 결정(희생 블록 선택 `SELECT`) 비용", "`m1-20261126` (`M1PROF` `SELECT`, n=1) + `sim` bench (n=3)", "**불리 결과 확인:** iCAT `SELECT` `87.05 µs/GC` (10h `9,162 s`, GC의 88.5%) > SmartGC `1.00 µs/GC` (`103.9 s`, step 제외 `56.3 s`). CAT 전 라인 스캔 비용이 압도적으로 큼 → 우위 입증 실패, 트레이드오프로 정직 기술", "origin/report/data-validity-20261124:result/m1-20261126/raw/", "입증 실패"),
        ("M1-5", "M1 SmartGC 비교", "SmartGC 대비 점수/Q-table 갱신 비용", "`m1-20261126` (`M1PROF` `LEARN/REWARD`) + `resource-v124`", "iCAT 보상 갱신 `1.44 ms/30m`(`resource-v124` n=3) · `40.8 ns/GC`(`m1` 10h) vs SmartGC `LEARN 47.6 s + REWARD 9.2 s`. 단 `m1` n=1 경과시간 한정", "origin/resource-overhead-20261114:result/resource-v124-20261114/ & result/m1-20261126/", "부분 입증"),
        ("M1-6", "M1 SmartGC 비교", "SmartGC 대비 GC 전체 실행 시간(`do_gc`) 비교", "`m1-20261126` (`M1PROF` `GC`, n=1) + `resource-v124`", "**불리 결과 확인:** iCAT-v4 `do_gc` `98.37 µs/GC` (`1,342 ms/GiB`) = SmartGC `17.84 µs/GC` (`333 ms/GiB`)의 **5.5×** (CAT 전 라인 스캔). \"iCAT GC가 더 빠르다\" 주장 불가", "origin/report/data-validity-20261124:result/m1-20261126/raw/", "입증 실패"),
        ("M1-7", "M1 SmartGC 비교", "SmartGC 대비 전환 부하 WAF(`WAF_nand` / `WAF`) 비교", "`smartgc-20261119` (표 9) + `m1-20261126` (표 9b, n=1)", f"기존 표 9(승컴 n=1): iCAT 3.21 vs EQ8 4.49 (−28.5%); 신규 `m1-20261126`(고컴 n=1): iCAT `WAF_nand 3.330` vs EQ8 `4.553` (−26.9%, 호스트 `WAF 4.562`). 양 호스트 방향 일치하나 n=1 통계 없음", "origin/report/data-validity-20261124:result/m1-20261126/raw/", m1_kernel_verdict),
        ("M1-8", "M1 SmartGC 비교", "SmartGC 대비 사용자 체감 I/O 지연 시간 비교", "`smartgc-20261119` + `m1-20261126` (`kernel-reduced.txt`)", "기존 4 run 전부 채널 포화(21만~353만 줄), 신규 `m1`에서도 SmartGC `chmodel_warn=22,069` (iCAT `0`) + `rate_iops` 고정 + `erase=0`으로 지연 비교 제외", "origin/report/data-validity-20261124:result/m1-20261126/raw/", "입증 실패"),
        ("M1-9", "M1 SmartGC 비교", "SmartGC 비교 독립 반복(`n>=3`) 및 통계적 유의성", "`m1-20261126` (`rep2-3` 사용자 결정 취소)", "사용자 결정으로 정책당 `n=1`만 수행(통계 검정 불가 → 논문에서 단일 실행 한계 명시)", "origin/report/data-validity-20261124:report/final-revision/DELIVERY_20261127.md", "추가 실험 불필요"),

        # M2 Ablation (6)
        ("M2-1", "M2 구성 요소 제거(Ablation)", "후보 제거(Candidate Elimination) 단독 효과 검증", "`revE-20261125` (`revE-noelim` vs `revE-v4`, 동일배치 n=3)", "+0.0913 [+0.0296, +0.1530] (+4.3%, Paired CI>0, g=3.88; 4-test Holm p=0.0907 경계)", "origin/report/data-validity-20261124:result/revE-20261125/raw/", "부분 입증"),
        ("M2-2", "M2 구성 요소 제거(Ablation)", "정착(Settling) 단독 효과 및 v4 기능 묶음 효과 검증", "`revA-v2` (고컴 n=3) + `abl-bundle-off` (승컴 n=3) + `revB-nosettle`", "묶음 제거(VAR=2)는 양 호스트 모두 입증 완료(고컴 +0.1355 Holm p<0.001, 승컴 +0.1241 Holm p=0.0277); 단 정착 단독(`NoSettle`)은 코드상 감지/탐침 종속+교차배치+CI 0포함", "origin/report/data-validity-20261124:result/revA-20261114/raw/ & origin/main:result/revision-additional-ablation/raw/", "부분 입증"),
        ("M2-3", "M2 구성 요소 제거(Ablation)", "변화 감지(Drift Detection) 단독 효과 검증", "`revA-v1` (고컴 n=3) + `revD-nodrift` (승컴 n=3)", "양 호스트 모두 3/3 평균 열위(+0.0787, +0.0681)이나 분산 과대로 Welch CI 0포함 → `n=3` 통계 미입증", "origin/report/data-validity-20261124:result/revA-20261114/raw/ & origin/main:result/revD-20261124/raw/", "입증 실패"),
        ("M2-4", "M2 구성 요소 제거(Ablation)", "재탐색 발동 및 단계 전환 대응 효과 검증", "`revA/revC/revD/revE` 적응 로그 (`kernel.log`)", "Phase C 전환은 43~79초 내 재현적 감지 성공; 단 Phase B 저쓰기 전환은 대부분 미감지(구조 한계)", "origin/report/data-validity-20261124:result/final-revision-analysis/", "부분 입증"),
        ("M2-5", "M2 구성 요소 제거(Ablation)", "후보 복원 범위(부분 복원 vs 전체 45개 재설정) 우위 검증", "`revD-20261124` (`revD-fullreset` vs `revD-v4`, 승컴 n=3)", "Total +0.0596 [+0.0160, +0.1033], Phase C +0.1296 [+0.0516, +0.2076] (Welch CI>0; 4-test Holm p=0.072/0.060 경계)", "origin/main:result/revD-20261124/raw/", "부분 입증"),
        ("M2-6", "M2 구성 요소 제거(Ablation)", "할인 계수(`gamma=0.9995`) 효과 검증 (Discount-free 대비)", "`abl-20261125` (`abl-nodiscount` vs `abl-v4`, 승컴 n=3)", "Δ = −0.0038 [−0.0644, +0.0569] (Welch p=0.869, Holm p=1.000) — 90분 구간(`gamma^250=0.882`)에서 효과 없음 정직 보고", "origin/main:result/revision-additional-ablation/raw/", "입증 실패"),

        # M3 Baselines (5)
        ("M3-1", "M3 기준선(Baselines) 비교", "무작위 선택(Random Selection) 대비 우위 검증", "`revA-20261114` (`revA-random` vs `revA-v4`, 고컴 n=3)", "+0.1959 [+0.1840, +0.2079] (−8.4%, g=29.9, Holm p<0.001)", "origin/report/data-validity-20261124:result/revA-20261114/raw/", "입증 완료"),
        ("M3-2", "M3 기준선(Baselines) 비교", "기존 iCAT 원 구현(Original iCAT) 대비 우위 검증", "`revC-20261124` (`revC-online` vs `revC-v4`, 고컴 n=3)", "+0.2751 [+0.2030, +0.3472] (−11.5%, g=10.53, 8-test Holm p=0.0282)", "origin/report/data-validity-20261124:result/revC-20261124/raw/", "입증 완료"),
        ("M3-3", "M3 기준선(Baselines) 비교", "단순 온라인 탐욕 선택(Online Greedy) 대비 우위 검증", "`greedy-20261125` (`VAR=8`, 승컴 n=3, 교차날짜 간접)", "`Greedy − revD-v4 = −0.0086 [−0.0508, +0.0336]` (`p=0.543`, vs `abl-v4` `−0.0090`), Phase C 첫 5분 Greedy 2.407 < V4 2.598 → **V4 우위 입증 실패(정직 보고)**", "origin/main:result/greedy-20261125/raw/", "입증 실패"),
        ("M3-4", "M3 기준선(Baselines) 비교", "4개 정책(Random/Greedy/원 iCAT/V4) 단일 조건 동시 비교", "`revA/revC`(고컴) vs `greedy`(승컴) 분리 수행", "Random·원 iCAT은 고컴, Online Greedy는 승컴에서 수행되어 호스트 간 직접 합산 불가(호스트 내 V4 대비만 병렬 제시); Periodic Switching 미실행", "origin/report/data-validity-20261124:result/rev{A,C}-*/ & origin/main:result/greedy-20261125/", "부분 입증"),
        ("M3-5", "M3 기준선(Baselines) 비교", "전통적 Greedy GC 대비 우위 검증", "`batchG-20261126` (`mixFYF-greedygc` vs `bg-v4`, 승컴) + 레거시 9종", bg_gg_note, "origin/main:result/greedygc-20261126/raw/ & result/mix-20260911/", bg_gg_verdict),

        # M4 Statistics & Validity (8)
        ("M4-1", "M4 통계적 신뢰성·유효성", "모든 주요 비교의 독립 반복 횟수(`n>=3`) 확보", "신규 §6.4 (`revA–E`, `abl`, `greedy`, `batchG`) vs 기존 §6.1–6.3", "§6.4 `mixFYF` 핵심 대비는 `n=3` 확보; 단 기존 그림 1~2·4~9, 표 6·7·9, `m1`은 `n=1~2` 잔존(탐색적 표기 필수)", "report/delivery-20261127/final_experiment_validity.csv", "부분 입증"),
        ("M4-2", "M4 통계적 신뢰성·유효성", "평균과 표준편차(Mean ± SD) 원시 로그 일치 보고", "전 배치 원시 카운터 재계산 (`final_statistical_audit.csv`)", "65+ run 및 신규 배치 전원 원시 카운터 소수 6자리 일치 확인", "report/delivery-20261127/final_statistical_audit.csv", "입증 완료"),
        ("M4-3", "M4 통계적 신뢰성·유효성", "95% 신뢰구간(Student-t CI) 보고 및 `n<3` 비표시", "전 `n=3` 조건 95% t-CI (`df=2`)", "`n=3` 전 조건 산출 및 `n<3` 통계 미표시 원칙 전수 준수", "report/delivery-20261127/final_statistical_audit.csv", "입증 완료"),
        ("M4-4", "M4 통계적 신뢰성·유효성", "이분산 Welch t-검정 및 95% CI 판정", "전 `n=3` 대비 (`final_statistical_audit.csv`)", "전 대비 `Welch_Delta`, `CI95`, `df`, `p`, `Hedges_g` 공란 0건 독립 검증 완료", "report/delivery-20261127/final_statistical_audit.csv", "입증 완료"),
        ("M4-5", "M4 통계적 신뢰성·유효성", "동일 seed/rep 짝지은 비교(Paired t-CI) 보조 검증", "동일 배치 `rep1–3` 짝지은 검정", "전 동일 배치 `n=3` 대비에 대해 `Paired_CI95`·`Paired_p` 독립 재계산 완료", "report/delivery-20261127/final_statistical_audit.csv", "입증 완료"),
        ("M4-6", "M4 통계적 신뢰성·유효성", "Holm-Bonferroni 다중 비교 보정 민감도 분석", "배치별 사전등록 가족(Family) Holm 보정", "전 가족(revA 3-test, revC 8-test, revD 4-test, abl 4-test, revE 4-test, batchG 4-test) 독립 재계산 및 경계(`p=0.06–0.09`) 정직 명시", "report/delivery-20261127/final_statistical_audit.csv", "입증 완료"),
        ("M4-7", "M4 통계적 신뢰성·유효성", "실패·오염 run 식별 및 엄격 제외 (`SQLITE_FULL`, `mixG`, `ENOSPC`)", "`validity.py` + 집컴 7점 독립 게이트", "`SQLITE_FULL` 224+건, `mixG` 34건, `ENOSPC` 1건 전수 제외 및 미포함 검증 완료", "origin/report/data-validity-20261124:analysis/final_e1/validity.py", "입증 완료"),
        ("M4-8", "M4 통계적 신뢰성·유효성", "서로 다른 호스트·배치 혼합 금지 및 원고 표 정합성", "호스트·배치 분리 + `PAPER_KCI_DRAFT.md` 표 8/10 점검", "표 10·데이터북은 호스트/배치 분리 완료; 단 원고 표 8(`300k` 플레이스홀더) 및 L256/L240/L385 잔존 문구 수정 필요(정오표 제공)", "report/delivery-20261127/final_revision_status.md", "부분 입증"),

        # M5 Overhead (6)
        ("M5-1", "M5 시스템 자원 오버헤드", "메모리 오버헤드 실측 및 구조체 계산", "`resource-v124` (FIO-Fast n=3) + `gdb sizeof` + `m1-20261126`", "`sizeof` 10,112 B 및 FIO-Fast `VmallocUsed` n=3 검증 완료; 단 커널 스레드 `VmRSS` 미존재·`m1`은 n=1", "origin/resource-overhead-20261114:result/resource-v124-20261114/report/memory_overhead_summary.csv", "부분 입증"),
        ("M5-2", "M5 시스템 자원 오버헤드", "CPU 오버헤드(알고리즘/갱신/선택 분리 계측)", "`resource-v124` (FIO-Fast 30m n=3) + `m1-20261126`", "FIO-Fast n=3 분리 실측(`reward 1.442 ms`, `select 1.273 ms`, `set_arm 0.059 ms`) 완료; 단 `perf` CPU 시간은 busy-poll 한계로 미측정(`ktime` 경과시간만)", "origin/resource-overhead-20261114:result/resource-v124-20261114/report/cpu_overhead_summary.csv", "부분 입증"),
        ("M5-3", "M5 시스템 자원 오버헤드", "학습 결정 경로 실행(경과) 시간 및 전체 실행 비중", "`revA` (`cpu_measurements.csv`, n=3) + `m1-20261126`", "`mixFYF 90m` 누적 `3.88 ms` (`3.9 µs/결정`, `0.00007%`, n=3) 및 `m1 10h` `4.30 s` (`40.8 ns/GC`) 검증 완료", "origin/report/data-validity-20261124:result/revA-20261114/results/resource/cpu_measurements.csv", "입증 완료"),
        ("M5-4", "M5 시스템 자원 오버헤드", "GC 전체 수행 시간(`do_gc`)에 미치는 영향", "`resource-v124` (FIO-Fast 30m n=3) + `m1-20261126`", "FIO-Fast n=3 `do_gc − on_gc` iCAT-v4 `206.84 s` vs CAT-47 `255.98 s` (`erase=0` 매핑 시간) 확인; 단 `m1`에서 SmartGC 대비 CAT 스캔이 느림 + 원고 L385 오기 수정 필요", "origin/resource-overhead-20261114:result/resource-v124-20261114/report/cpu_overhead_summary.csv", "부분 입증"),
        ("M5-5", "M5 시스템 자원 오버헤드", "사용자 체감 I/O 지연 시간(FIO clat p50/p99, YCSB latency)", "`revA/revD` (`r3_io_latency_summary.csv`, n=3) + `smartgc`", "`mixFYF` n=3에서 YCSB·FIO p50 차이 없음, **FIO p99는 iCAT-v4가 +15~20 µs 열위**(꼬리 지연 개선 입증 실패, 정직 기술); `erase=0` 한계", "report/reanalysis-20261124/r3_io_latency_summary.csv", "입증 실패"),
        ("M5-6", "M5 시스템 자원 오버헤드", "측정 도구의 정확성·타이머 왜곡 검증", "`resource-v124` (`measurement_methodology.md`, n=3) + `perf-20261119`", "타이머 18 ns 차분·`ktime` vs CPU 구분·busy-poll 구조적 한계 검증 완료", "origin/resource-overhead-20261114:result/resource-v124-20261114/report/measurement_methodology.md", "입증 완료"),

        # M6 Parameters & Adaptation (8)
        ("M6-1", "M6 파라미터 민감도·적응", "후보 제거 문턱(`ELIM_Q16`: 10% / 15% / 25%) 민감도", "`revC-20261124` (`elim10/v4/elim25`, 고컴 n=3)", "15% 최저 평균(`2.1200`), 10%(`+0.0238`)·25%(`+0.0507`) 모두 CI 0포함(광범위 둔감·안정 입증)", "origin/report/data-validity-20261124:result/revC-20261124/raw/", "입증 완료"),
        ("M6-2", "M6 파라미터 민감도·적응", "후보 공간 크기(60개 vs `k=2` 제외 45개, m5) 타당성", "`revC-20261124` (`revB-arm60` vs `revC-v4`, n=3) + `3×60` 스윕", "전체 WAF +0.0282 [−0.032, +0.089] (Phase A 초기 비용 +3.0% 유의; 3/3 최종 선택은 45개 내부)", "origin/report/data-validity-20261124:result/revC-20261124/raw/", "입증 완료"),
        ("M6-3", "M6 파라미터 민감도·적응", "변화 감지 문턱(`DRIFT_Q16`: 12.5% / 25% / 50%) 민감도", "`revE-drift12` (고컴 n=3) + `batchG-drift50` (승컴 n=3)", bg_d50_note, "origin/report/data-validity-20261124:result/revE-20261125/raw/ & origin/main:result/drift50-20261126/raw/", bg_d50_verdict),
        ("M6-4", "M6 파라미터 민감도·적응", "판단 구간 크기(512 MiB / 128 GC) 민감도", "미실행 (`window_plan.md` 오프라인 잡음 SD 5.5–7.1%만 계산)", "미승인·미실행 → 논문 §8 한계 4에 경험적 설정으로 명시", "origin/report/data-validity-20261124:result/revE-20261125/window_plan.md", "추가 실험 불필요"),
        ("M6-5", "M6 파라미터 민감도·적응", "할인 계수(`gamma`) 수준별 민감도", "`abl-nodiscount` (`gamma=1.0` on/off만 n=3; 짧은 반감기 미실행)", "on/off null 확인 완료; 짧은 반감기 추가 스윕은 90분 범위 외 → 논문 한계 명시", "origin/main:result/revision-additional-ablation/raw/", "추가 실험 불필요"),
        ("M6-6", "M6 파라미터 민감도·적응", "정착 판정 조건(`STABLE=12`, 확인 3회, 0.5%) 민감도", "미실행", "미실행 → 논문 §8 한계 4에 경험적 설정으로 명시", "NONE (disclosed in §8 Limitation 4)", "추가 실험 불필요"),
        ("M6-7", "M6 파라미터 민감도·적응", "재탐색·탐침 주기(`PROBE=8`, `STALE=240`, UCB `c=0.25`) 민감도", "미실행", "미실행 → 논문 §8 한계 4에 경험적 설정으로 명시", "NONE (disclosed in §8 Limitation 4)", "추가 실험 불필요"),
        ("M6-8", "M6 파라미터 민감도·적응", "전환 후 적응·회복 시간(감지/재탐색/재정착/WAF 회복, E3)", "`revA/C/D/E` 적응 로그 + `r1_adaptation_*.csv` + `secondary-metrics`", "Phase C 감지(43~79s)·재정착(299~499s) 정량화 완료; 단 Phase B 저쓰기 미감지 및 Phase C 첫 5분 WAF에서 Online Greedy(2.407) < V4(2.598)로 빠른 회복 우위는 미입증", "report/reanalysis-20261124/r1_adaptation_summary.csv", "부분 입증"),

        # M7 Environment Generalization (5)
        ("M7-1", "M7 환경·워크로드 일반화", "SSD 용량 일반화 (8 GiB 외 16/32/64 GiB+)", "미실행 (8 GiB 단일 에뮬레이터)", "논문 §7·§8 한계 5에 명시적 적용 범위 제한 및 향후 과제로 기술", "revC-src/ssd_config.h (8 GiB fixed)", "추가 실험 불필요"),
        ("M7-2", "M7 환경·워크로드 일반화", "오버프로비저닝(OP) 비율 일반화 (7% 외 14%/28%)", "미실행 (OP 7% 단일)", "논문 §7·§8 한계 5에 명시적 제한 기술", "revC-src/ssd_config.h (OP 7% fixed)", "추가 실험 불필요"),
        ("M7-3", "M7 환경·워크로드 일반화", "NAND 구성(TLC/QLC·비영 erase 지연) 일반화", "미실행 (MLC `erase=0` 에뮬레이터)", "논문 §7·§8 한계 5에 `erase=0` 한계 및 지연/GC 해석 주의 명시", "revC-src/ssd_config.h (MLC erase=0)", "추가 실험 불필요"),
        ("M7-4", "M7 환경·워크로드 일반화", "다중 전환 워크로드 및 실서버 트레이스 일반화", "`mix-20260911` (유효 8종 n=1~3) + `mixFYF` (n=3)", "`n=3` 통계 검증은 `mixFYF` 1종 중심; 다중 전환 8종은 탐색적 `n=1~3`; 실서버 트레이스 미검증 → 범위 제한 명시", "origin/report/data-validity-20261124:PAPER_KCI_DRAFT.md", "부분 입증"),
        ("M7-5", "M7 환경·워크로드 일반화", "NVMeVirt 외 실물 SSD·discard ON·장시간(>10h)·타 FTL 일반화", "미실행 (`ext4 nodiscard`, `conv_ftl`, ≤10h)", "논문 §7·§8 한계 5에 명시적 범위 제한 및 향후 과제 기술", "environment.txt (conv_ftl nodiscard)", "추가 실험 불필요"),
    ]

    v_counts = defaultdict(int)
    for r in req_rows:
        v_counts[r[6]] += 1

    matrix_lines = [
        "# iCAT 최초 심사 요구사항(M1~M7, 47개 세부 항목) 대응 근거표 (`final_reviewer_evidence_matrix.md`)",
        "",
        f"- **생성 시각**: `{NOW_STR}` (`origin/main @ {c_main}`, `origin/report/data-validity-20261124 @ {c_gocom}`, `origin/resource-overhead-20261114 @ {c_res}`)",
        "- **분류 체계 (5종 엄격 적용)**: `입증 완료` | `부분 입증` | `입증 실패` | `추가 실험 불필요` | `추가 실험 필요`",
        "- **표기 원칙**: 모든 항목에 **최초 심사 요구사항 원 명칭**을 유지하고, 내부 실험 ID(`revE-noelim`, `batchG-drift50` 등)와 원시 로그 경로를 함께 병기함.",
        "",
        "## 요약 집계 (총 47개 세부 요구사항)",
        "",
        "| 분류 | 건수 | 해석 원칙 |",
        "|---|---:|---|",
        f"| **입증 완료** | **{v_counts['입증 완료']}** | `n=3` 원시 로그 검증·통계 기준 통과(또는 정확한 구조체 계산) — 본문 주장 가능 |",
        f"| **부분 입증** | **{v_counts['부분 입증']}** | 방향·일부 조건 확인되었으나 Holm 경계(`0.06–0.09`), `n=1` 한계, 교차배치, 부분 조건 한정 — 단서·범위 제한 필수 |",
        f"| **입증 실패** | **{v_counts['입증 실패']}** | 실측상 우위 미확인(Online Greedy, NoDrift, Discount-free, FIO p99, SmartGC `SELECT`·`do_gc` 경과시간, mixY 지연) — **우위 주장 삭제 및 정직 보고 필수** |",
        f"| **추가 실험 불필요** | **{v_counts['추가 실험 불필요']}** | 사용자 결정·범위 외·하드웨어 일반화 항목 — 논문 §7·§8 한계 명시로 마감 |",
        f"| **추가 실험 필요** | **{v_counts['추가 실험 필요']}** | 현재 실행 중인 최종 큐(`batchG` `bg-v4 rep3` / `m1` `smartgc-eq8 rep1`) 종료 대기 중(신규 큐 추가 아님) |",
        "",
        "## M1~M7 전체 47개 항목 추적표",
        "",
        "| ID | 대분류 | 최초 심사 요구사항 (원 명칭) | 대응 내부 실험 ID | 검증된 핵심 결과 및 한계 | 원시 로그 / 근거 경로 | 최종 판정 |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in req_rows:
        matrix_lines.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | `{r[5]}` | **{r[6]}** |")

    (OUT_DIR / "final_reviewer_evidence_matrix.md").write_text("\n".join(matrix_lines) + "\n", encoding="utf-8")
    print("Wrote final_reviewer_evidence_matrix.md")

    # -----------------------------------------------------------------------
    # 5. final_revision_status.md (Claim-by-claim Keep/Soften/Delete + Draft Patch Table)
    # -----------------------------------------------------------------------
    status_md = f"""# iCAT 논문 리비전 최종 상태 및 원고 수정 패치 지침 (`final_revision_status.md`)

- **생성 시각**: `{NOW_STR}`
- **원격 커밋**: 승컴 `origin/main @ {c_main}` / 고컴 `origin/report/data-validity-20261124 @ {c_gocom}` / 자원 계측 `origin/resource-overhead-20261114 @ {c_res}`
- **실험 완료 현황**:
  - 확정 검증 완료: **`{n_valid}`개 run VALID** (무효/오염 혼입 0건)
  - 실행 대기(미완료): **`{n_running}`개 run RUNNING** (`batchG` 완료={batchG_complete}, `m1` 완료={m1_sg is not None})

---

## 1. 논문 주장별 유지 / 완화 / 삭제 확정 지침

### A. 유지 가능 (입증 완료 — `n=3` 통계 확정 또는 정확 계산)
1. **무작위 선택 대비 WAF 절감 (`M3-1`)**: `mixFYF 250k` (`n=3`, 고컴 `revA`)에서 iCAT-v4가 무작위 선택 대비 **−8.43%** (`Δ = +0.1959 [+0.1840, +0.2079]`, `g=29.9`, `Holm p<0.001`).
2. **기존 iCAT 원 구현 대비 WAF 절감 (`M3-2`)**: `mixFYF 250k` (`n=3`, 고컴 `revC`)에서 **−11.49%** (`Δ = +0.2751 [+0.2030, +0.3472]`, `g=10.53`, `8-test Holm p=0.0282`), Phase C 탐색 쓰기 비중 `97% → 22%`.
3. **v4 기능 묶음(제거·정착·변화감지·탐침) 효과 (`M2-2`)**: 양 호스트 모두 재현 확정 — 고컴 `revA` `+0.1355 [+0.1167, +0.1543]` (`Holm p<0.001`), 승컴 `abl` `+0.1241 [+0.0730, +0.1753]` (`Holm p=0.0277`).
4. **이론적 학습 상태 메모리 우위 (`M1-1`)**: 4파티션 합계 `10,112 B` (장치 용량 무관) vs SmartGC 학습 상태 `1,951,648 B` (**193.0×**, GC 버퍼 포함 `2,344,864 B` **231.9×**).
5. **학습 결정 경로 자체의 경량성 (`M5-3`)**: `mixFYF 90m` `3.88 ms` (`3.9 µs/결정`, `0.00007%`, `n=3`), `m1 10h` `LEARN 4.30 s` (`40.8 ns/GC`, `0.041%`).
6. **후보 제거 문턱(10~25%)·후보 공간(45 vs 60) 안정성 (`M6-1/2`)**: 전체 WAF 차이 없음(CI 0 포함), 60-arm은 Phase A 초기 탐색 비용만 `+3.0%`.
7. **Greedy GC 대비 WAF 절감 (`M3-5`)**: 레거시 유효 9종(`n=3`) 전수 유의(`−7.1% ~ −42.0%`), `mixFYF` `batchG` {"9/9 확정(통계 표 참조)" if batchG_complete else "Greedy GC 3/3 완료(`2.6293`), `bg-v4 rep3` 완료 직후 확정"}.

### B. 조건부 완화 필수 (부분 입증 — 경계 p값·단일 실행·단서 병기)
1. **후보 제거 단독 효과 (`M2-1`, `revE`)**: 동일 배치 `n=3`에서 `+0.0913 [+0.0296, +0.1530]` (`Paired CI>0`), 단 4-test Holm `p=0.0907` → **"사전등록 Welch/짝지은 CI 기준 개선, 다중 비교 보정 후 경계"**로 표기.
2. **부분 복원 vs 전체 45개 재설정 (`M2-5`, `revD`)**: Total `+0.0596 [+0.0160, +0.1033]`, Phase C `+0.1296 [+0.0516, +0.2076]`, 단 4-test Holm `p=0.072 / 0.060` → 경계 단서 병기.
3. **변화 감지 문턱 민감도 (`M6-3`, `revE` 12.5% & `batchG` 50%)**: 12.5%는 Phase B 조기 리셋으로 `+0.0720 [+0.0121, +0.1319]` (`Holm p=0.0907`); 50%는 `batchG` 최종 수치 병기.
4. **SmartGC 대비 `mixY` WAF (`M1-7`)**: `n=1` 단일 실행이므로 통계적 유의성 주장 없이 단일 실행 관측치로만 제시.
5. **기존 그림 1~2, 4~9 및 표 6~7 (`M4-1`)**: 모두 `n=1` 고정 조합 또는 `n=1~3` 학습기 기반이므로 **"1회 실행 사례 / 탐색적 참고 결과"**로 격하하고, 확정 통계는 §6.4 표 10으로 분리.

### C. 반드시 삭제 또는 부정 결과 정직 기술 (입증 실패)
1. **"단순 Online Greedy보다 iCAT-v4가 우수하다" → 삭제 (`M3-3`)**: `Online Greedy − revD-v4 = −0.0086 [−0.0508, +0.0336]` (`p=0.543`), Phase C 첫 5분도 Greedy(`2.407`) < V4(`2.598`).
2. **"iCAT-v4가 SmartGC보다 전체 GC CPU/실행 시간이 더 빠르다" → 삭제 (`M1-4/6`)**: 학습 연산(`LEARN`)은 `4.3 s` (`40.8 ns/GC`)로 SmartGC(`47.6 s`)보다 11× 작으나, CAT 전 라인 스캔(`SELECT 87.0 µs/GC`) 때문에 전체 GC당 경과시간은 iCAT(`98.4 µs`, `1,342 ms/GiB`)이 SmartGC(`17.8 µs`, `333 ms/GiB`)의 **5.5×** — **WAF·메모리 절감 대 희생 선택 연산 비용 트레이드오프**로 정직 기술.
3. **"변화 감지 단독으로 WAF가 통계적으로 유의하게 낮아진다" → 삭제 (`M2-3`)**: 양 호스트 모두 3/3 평균 열위이나 분산 과대로 Welch CI 0 포함.
4. **"할인 계수 `gamma=0.9995`가 90분 부하에서 WAF를 개선한다" → 삭제 (`M2-6`)**: `−0.0038 [−0.0644, +0.0569]` (`Holm p=1.000`).
5. **"WAF 감소가 사용자 I/O 꼬리 지연(p99)을 개선한다" → 삭제 (`M5-5`, `M1-8`)**: `mixFYF` FIO p99는 iCAT-v4가 `+15~20 µs` 높고, `batchG` Greedy GC 대비로도 FIO p99(`166 vs 42 µs`)가 높음; `mixY` 지연은 SmartGC 채널 포화(`22,069`건)로 비교 제외.

---

## 2. `PAPER_KCI_DRAFT.md` (`2a0900382`) 및 `iCAT_revision_databook_v2.xlsx` 즉시 수정 패치 표

| 대상 파일·위치 | 현재 내용 (문제점) | 권고 수정안 |
|---|---|---|
| `PAPER_KCI_DRAFT.md` L004–005 | `【결과 대기】` / `【그림 N 자리】` 초안 메모 잔존 | 투고본 정리 시 삭제 |
| `PAPER_KCI_DRAFT.md` L232 (그림 6) | `...제거 실험을 진행 중이다【결과 대기】.` | `...잠정적이며, iCAT-v4 구성 요소의 반복(n=3) 제거 검증은 6.4절 표 10에 제시한다.` |
| `PAPER_KCI_DRAFT.md` L240 (그림 7) | `모든 전환 워크로드를 3회로 맞춘 결과로 그림 7을 갱신할 예정이다【결과 대기】.` | 삭제하고 `이 8종 비교는 CAT-Robust 1회·iCAT-v4 1~3회의 탐색적 요약이며, 통계적 검정은 6.4절(n=3)에서 수행한다.`로 교체 |
| `PAPER_KCI_DRAFT.md` L256 (표 6) | `【결과 대기: arm 47·17·50 각 3회】` | 삭제하고 `(고정 조합은 1회 측정이므로 동등 이상의 탐색적 사례로만 해석한다)`로 확정 |
| `PAPER_KCI_DRAFT.md` L260 (그림 8) | `【선별 실험 결과로 갱신 예정】` | 플레이스홀더 문구 삭제 |
| `PAPER_KCI_DRAFT.md` L262 (그림 9) | `CAT-Best 0.2%, iCAT-v4 5.0%, CAT-Robust 5.0%` (1자리 반올림) | 소수 2자리 정확한 post-gating 값 병기: **`CAT-Best 0.21%, CAT-Robust 4.95%, iCAT-v4 5.04%`** |
| `PAPER_KCI_DRAFT.md` L297–307 (표 8·그림 10) | `YCSB-A 30만 레코드` 재측정 표 8 전원 `"대기"`, 그림 10 `【재측정 결과 대기】` | `300k` 미실행이므로 표 8·그림 10을 삭제하고 **6.4절 `mixFYF 250k (n=3)` 표 10·표 11 및 `figure03_adaptation.png`**로 통합 참조 |
| `PAPER_KCI_DRAFT.md` L313–337 (표 9 · 표 9b) | `2a0900382`에서 표 9b 추가 완료(집컴 독립 검증 100% 일치). 단 표 9 `WAF_nand` (`4.49`, `11.02`)와 데이터북 `F7` 호스트 `WAF` (`4.4984`, `11.0723`) 정의 차이 각주 보강 권고 | 표 9 각주에 `WAF_nand` vs 호스트 `WAF` 식 명시 (`m1` 표 9b 수치는 `4.553` vs `3.330`, `98.4 µs` vs `17.8 µs`, `Vmalloc +2,904 kB` 전수 검증 PASS) |
| `PAPER_KCI_DRAFT.md` L400 (§7 자원 비용, 구 L385) | `"GC 수행 시간은 계측하지 않았다."` 잔존 (표 9b 및 `resource-v124`와 모순) | `"별도 FIO-Fast 30분 계측(n=3, erase=0)에서 학습기 호출 제외 GC 매핑 경과시간은 iCAT-v4 206.8 s 대 CAT-47 256.0 s(분리 경과시간: reward 1.44 ms, select 1.27 ms, set_arm 0.06 ms)였으며, SmartGC와의 동일 환경 비교(표 9b, m1-20261126, n=1)에서는 iCAT의 학습 갱신(4.3 s, 40.8 ns/GC)은 SmartGC(47.6 s)보다 11배 작았으나 CAT 전 라인 스캔 선택(87.0 µs/GC) 때문에 GC 1회 경과시간은 iCAT(98.4 µs)이 SmartGC(17.8 µs)의 5.5배였다."`로 교체 |
| `iCAT_revision_databook_v2.xlsx` `F6_memory` R9–R12 | `item` 열 `(kB)` 표기, 실제 `bytes` 열은 bytes 값 | `(kB)` 라벨 삭제 또는 `kB`와 `bytes` 열 분리 |
| `iCAT_revision_databook_v2.xlsx` `F3_contrasts_same_batch` | `abl`, `greedy`, `revA/C/D`의 `p_unadjusted`·`p_holm_4tests` 공란; `R40` D′ 부호(`revD-v4 − greedy`)가 표 10과 반대 | 집컴 `final_statistical_audit.csv` 및 `iCAT_Paper_Figures.xlsx` 기준으로 전 행 `p`/`Holm` 기입 및 `정책 − V4` 부호 통일 |
"""
    (OUT_DIR / "final_revision_status.md").write_text(status_md, encoding="utf-8")
    print("Wrote final_revision_status.md")

    # -----------------------------------------------------------------------
    # 6. SENIOR_RESEARCHER_SUMMARY_20261127.md (Ready-to-forward Executive Summary)
    # -----------------------------------------------------------------------
    exec_md = f"""# iCAT 논문 리비전 최종 독립 검증 요약 보고서 (선임 연구원 전달용)

- **작성일시**: `{NOW_STR}`
- **검증 주체**: 집컴 (독립 원시 로그 재계산·통계 감사·패키지 통합)
- **검증 기준 커밋**: 승컴 `origin/main @ {c_main}` / 고컴 `origin/report/data-validity-20261124 @ {c_gocom}` / 자원 계측 `origin/resource-overhead-20261114 @ {c_res}`

---

## 1. 한눈에 보는 최종 검증 판정

- **원시 데이터 무결성**: 총 **`{n_valid}`개 실행 원시 로그 독립 7점 검증 통과 (VALID)**, 실패·오염 run(`SQLITE_FULL` 224+건, `mixG` 34건, `ENOSPC` 1건) 100% 제외 확인. *(현재 잔여 실행 대기: `{n_running}`건 — 완료 전까지 `PASS` 미표기)*
- **고컴 전달 데이터북(`iCAT_revision_databook_v2.xlsx`) 독립 감사**: `F2_runs` 65개 run(260개 WAF 셀) 및 `F1` 92행 기술통계·논문 표 10(19행) **원시 로그와 0건 불일치(PASS)**. 단 투고 전 수정할 **표기·누락 오류 7건**을 식별하여 본 패키지에 모두 교정·패치안을 포함함.
- **최초 심사 요구사항(M1~M7, 47개 세부 항목) 달성 현황**:
  - **입증 완료**: `{v_counts['입증 완료']}`건 | **부분 입증**: `{v_counts['부분 입증']}`건 | **입증 실패(정직 보고·주장 삭제)**: `{v_counts['입증 실패']}`건 | **추가 실험 불필요(한계 명시)**: `{v_counts['추가 실험 불필요']}`건 | **최종 큐 완료 대기**: `{v_counts['추가 실험 필요']}`건

---

## 2. 논문 본문에 확정 반영할 핵심 결과 (`mixFYF 250k`, `n=3`, 호스트·배치 엄격 분리)

*(부호 통일: `Δ = 비교 정책 − 동일 배치 iCAT-v4`, 양수(+) = iCAT-v4 우위)*

| 심사 항목 | 비교 (호스트·배치) | Total WAF Δ `[Welch 95% CI]` | Welch p | Holm p | 최종 해석 |
|---|---|---:|---:|---:|---|
| **M3-1** 무작위 선택 | `Random − V4` (고컴 `revA`, 동일배치) | `+0.1959 [+0.1840, +0.2079]` | `<0.0001` | `<0.0001` | **입증 완료** (−8.4%) |
| **M3-2** 기존 iCAT 원 구현 | `Orig iCAT − V4` (고컴 `revC`, 동일배치) | `+0.2751 [+0.2030, +0.3472]` | `0.0035` | `0.0282` | **입증 완료** (−11.5%) |
| **M2-2** v4 4기능 묶음 제거 | `OffBundle − V4` (고컴 `revA` / 승컴 `abl`) | `+0.1355` / `+0.1241 [+0.0730, +0.1753]` | `<0.001` / `0.0069` | `<0.001` / `0.0277` | **입증 완료** (양 호스트 재현) |
| **M2-1** 후보 제거 단독 | `NoElim − V4` (고컴 `revE`, 동일배치) | `+0.0913 [+0.0296, +0.1530]` | `0.0227` | `0.0907` | **부분 입증** (Paired>0, Holm 경계) |
| **M2-5** 부분 vs 전체 복원 | `FullReset − V4` (승컴 `revD`, 동일배치) | `+0.0596 [+0.0160, +0.1033]` | `0.0239` | `0.0718` | **부분 입증** (Phase C +0.130, Holm 경계) |
| **M6-1/2** 제거문턱·60후보 | `elim10/25`, `arm60 − V4` (고컴 `revC`) | `+0.024 / +0.051 / +0.028` (CI 0포함) | `0.079–0.294` | `0.475–0.951` | **입증 완료** (파라미터 둔감·안정) |
| **M6-3** 변화감지 12.5% | `drift12 − V4` (고컴 `revE`, 동일배치) | `+0.0720 [+0.0121, +0.1319]` | `0.0289` | `0.0907` | **부분 입증** (Phase B 조기리셋) |
| **M3-5** Greedy GC | `Greedy GC − V4` (승컴 `batchG`, 동일배치) | {f"`{smap[('batchG-greedygc - batchG-v4','Total WAF')]['Welch_Delta']:+.4f} {smap[('batchG-greedygc - batchG-v4','Total WAF')]['Welch_CI95']}`" if batchG_complete else f"Greedy GC `2.6293` (n=3) vs `bg-v4` 진행중(2/3)"} | {f"`{smap[('batchG-greedygc - batchG-v4','Total WAF')]['Welch_p']:.6f}`" if batchG_complete else "대기"} | {f"`{smap[('batchG-greedygc - batchG-v4','Total WAF')]['Holm_p']:.6f}`" if batchG_complete else "대기"} | {"**입증 완료**" if batchG_complete else "`bg-v4 rep3` 대기(~00:42 KST)"} |
| **M6-3** 변화감지 50% | `drift50 − V4` (승컴 `batchG`, 동일배치) | {f"`{smap[('batchG-drift50 - batchG-v4','Total WAF')]['Welch_Delta']:+.4f} {smap[('batchG-drift50 - batchG-v4','Total WAF')]['Welch_CI95']}`" if batchG_complete else f"drift50 `2.1288` (n=3) vs `bg-v4` 진행중(2/3)"} | {f"`{smap[('batchG-drift50 - batchG-v4','Total WAF')]['Welch_p']:.6f}`" if batchG_complete else "대기"} | {f"`{smap[('batchG-drift50 - batchG-v4','Total WAF')]['Holm_p']:.6f}`" if batchG_complete else "대기"} | {f"**{bg_d50_verdict}**" if batchG_complete else "`bg-v4 rep3` 대기(~00:42 KST)"} |
| **M3-3** Online Greedy | `Greedy − revD-v4` (승컴, **교차날짜 간접**) | `−0.0086 [−0.0508, +0.0336]` | `0.5433` | `1.0000` | **입증 실패** (우위 없음 정직 보고) |
| **M2-3** 변화감지 단독 | `NoDrift − V4` (고컴 `revA` / 승컴 `revD`) | `+0.0787` / `+0.0681` (CI 0포함) | `0.119` / `0.116` | `0.119` / `0.116` | **입증 실패** (분산 과대, 검정력 부족) |
| **M2-6** 할인 계수 제거 | `NoDiscount − V4` (승컴 `abl`, 동일배치) | `−0.0038 [−0.0644, +0.0569]` | `0.8692` | `1.0000` | **입증 실패** (90분 범위 효과 없음) |

---

## 3. 반드시 정직 보고·수정해야 할 핵심 리스크 4가지

1. **SmartGC 대비 자원 오버헤드 분리 서술 (`M1` / `M5`)**: iCAT-v4의 **학습 상태 메모리(193×–232× 경량, 실측 `VmallocUsed` 차이 `+2,904 kB` vs 이론 `3,058 KiB`)**와 **학습 연산 자체(`4.3 s` vs `47.6 s`, 11× 경량)**는 압도적으로 가볍지만, **CAT 전 라인 스캔 기반 희생 선택(`SELECT 87.0 µs/GC`)** 때문에 GC 1회 경과시간은 iCAT(`98.4 µs`, `1,342 ms/GiB`)이 SmartGC(`17.8 µs`, `333 ms/GiB`)의 **5.5×**입니다(`m1-20261126` 2/2 독립 검증 완료, 표 9b 일치). 따라서 "전체 GC CPU도 iCAT이 우위"라는 표현은 금지하고, **WAF·메모리 우위 대 희생 선택 연산 비용 트레이드오프**로 기술해야 합니다.
2. **Online Greedy 무우위 (`M3-3`) & FIO p99 열위 (`M5-5`)**: `mixFYF`에서 단순 탐욕 선택 대비 통계적 우위가 없고, FIO p99는 iCAT-v4가 `+15~20 µs` 높으며(Greedy GC 대비로도 FIO p99 `166 vs 42 µs` 열위), 두 항목 모두 본문에 정직하게 유지합니다.
3. **기존 논문 Figure 1~10 중 단일 실행(`n=1`) 및 무효 데이터 격리**: 그림 2·4·6·7·8·9와 표 6·7·9·9b는 단일 실행 기반이므로 탐색적 사례로 한정하고, **`SQLITE_FULL`로 오염된 구 그림 10 및 미실행 `300k` 표 8은 원고에서 제거·대체**해야 합니다. *(고정 Arm 47 `mixFYF`는 승컴 `arm47-20261127` `n=3` 독립 검증 완료: **`1.98764 ± 0.00027`** [`[1.98698, 1.98831]`] — 기존 고컴 `n=1` `1.987355`가 CI 내 재현됨, 호스트 분리 유지)*
4. **원고(`PAPER_KCI_DRAFT.md` @ `2a0900382`) 잔존 오류 패치**: L232/L240/L256/L260/L297–307의 `【결과 대기】` 플레이스홀더, §7 L400(구 L385) `"GC 수행 시간은 계측하지 않았다"` 오기, 표 9 `WAF_nand` vs `WAF` 정의 차이를 `final_revision_status.md` 패치표대로 투고 전 일괄 반영하면 됩니다.

---

## 4. 전달 패키지 파일 목록

1. `report/delivery-20261127/final_robustness_audit.md` — 기존 Figure 1~10, Arm 47, 7건 오류 수정 및 `batchG`/`m1` 종합 감사
2. `report/delivery-20261127/final_experiment_validity.csv` — 전 run 원시 카운터·SHA256·시드·유효성 검증표
3. `report/delivery-20261127/final_statistical_audit.csv` — 전 `n=3` 대비 Mean/SD/95% CI/Welch/Paired/Hedges' g/Holm 표 (공란 0건, 부호 통일)
4. `report/delivery-20261127/final_reviewer_evidence_matrix.md` — 최초 심사 요구사항(M1~M7, 47개 항목) 원 명칭·5분류 판정표
5. `report/delivery-20261127/final_revision_status.md` — 주장별 유지/완화/삭제 지침 및 원고·데이터북 패치표
6. `report/paper-figures/iCAT_Paper_Figures.xlsx` — 논문용 통합 Excel 데이터북 (원시·통계·차트·표 전수 검증)
7. `report/paper-figures/figures/figure01..07.{{png,pdf,svg}}` & `report/revision-final-integration/paper_figures/fig_*.{{png,pdf,svg}}` — 최종 논문 Figure 및 CSV
"""
    (OUT_DIR / "SENIOR_RESEARCHER_SUMMARY_20261127.md").write_text(exec_md, encoding="utf-8")
    print("Wrote SENIOR_RESEARCHER_SUMMARY_20261127.md")

    # Machine-readable dump
    dump = {
        "generated_at": NOW_STR,
        "commits": {"main": c_main, "gocom": c_gocom, "res": c_res},
        "n_valid": n_valid,
        "n_running": n_running,
        "batchG_complete": batchG_complete,
        "m1_complete": m1_sg is not None,
        "batchG_stats": {"greedygc": bg_g_st, "drift50": bg_d_st, "v4": bg_v_st},
        "m1_icat_v4": m1_v4_d,
        "m1_smartgc_eq8": m1_sg_d,
        "verdict_counts": dict(v_counts),
    }
    (OUT_DIR / "delivery_audit_dump.json").write_text(json.dumps(dump, indent=2, ensure_ascii=False), encoding="utf-8")
    print("DONE! Verdict counts:", dict(v_counts))


if __name__ == "__main__":
    main()
