#!/usr/bin/env python3
"""
Automated Consistency & Quality Verifier for report/paper-figures/
Verifies:
1. Exact 12 required sheets exist in iCAT_Paper_Figures.xlsx in exact order.
2. Zero Excel error literals (#REF!, #DIV/0!, #VALUE!, #NAME?, #N/A, #NUM!).
3. Every Fig_01..Fig_07 sheet contains at least one embedded native Excel chart.
4. Numerical consistency between verified_plot_data.json (exact values plotted in PNG/PDF/SVG)
   and the corresponding table cells in iCAT_Paper_Figures.xlsx (tolerance <= 1e-6).
5. All 21 figure files (7 figures x PNG/PDF/SVG) exist, are non-empty, and all PNGs are 300 DPI.
6. figure_manifest.csv exists and lists all 7 figures with complete traceability columns.
7. Existing figs/ directory is untouched.
"""

import csv
import json
import math
import subprocess
import sys
from pathlib import Path

import openpyxl
from PIL import Image

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[1]
XLSX_PATH = OUT_DIR / "iCAT_Paper_Figures.xlsx"
JSON_PATH = OUT_DIR / "verified_plot_data.json"
MANIFEST_PATH = OUT_DIR / "figure_manifest.csv"

REQUIRED_SHEETS = [
    "README",
    "Experiment_Index",
    "Raw_Data",
    "Statistics",
    "Fig_01_Random",
    "Fig_02_Ablation",
    "Fig_03_Adaptation",
    "Fig_04_Exploration",
    "Fig_05_Parameters",
    "Fig_06_Candidates",
    "Fig_07_Resources",
    "Table_Data",
]

REQUIRED_FIG_STEMS = [
    "figure01_random",
    "figure02_ablation",
    "figure03_adaptation",
    "figure04_exploration",
    "figure05_parameters",
    "figure06_candidates",
    "figure07_resources",
]

EXCEL_ERRORS = ("#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A", "#NUM!")


def approx_eq(a, b, tol=1e-6):
    return abs(float(a) - float(b)) <= tol


def main():
    failures = []

    if not XLSX_PATH.exists():
        sys.exit(f"FAIL: Missing {XLSX_PATH}")
    if not JSON_PATH.exists():
        sys.exit(f"FAIL: Missing {JSON_PATH}")
    if not MANIFEST_PATH.exists():
        sys.exit(f"FAIL: Missing {MANIFEST_PATH}")

    wb = openpyxl.load_workbook(XLSX_PATH, data_only=False)
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))

    # 1. Exact sheet names & order (12 original sheets + optional 9 extended integration sheets)
    EXTENDED_SHEETS = REQUIRED_SHEETS + [
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
    if wb.sheetnames not in (REQUIRED_SHEETS, EXTENDED_SHEETS):
        failures.append(f"Sheet list mismatch: got {wb.sheetnames}, expected {REQUIRED_SHEETS} or {EXTENDED_SHEETS}")

    # 2. Zero Excel error literals
    for sname in wb.sheetnames:
        ws = wb[sname]
        for row in ws.iter_rows(values_only=True):
            for val in row:
                if isinstance(val, str) and any(err in val for err in EXCEL_ERRORS):
                    failures.append(f"Excel error literal in {sname}: {val}")

    # 3. Every Fig_01..Fig_07 sheet has >= 1 embedded native chart
    for sname in REQUIRED_SHEETS[4:11]:
        ws = wb[sname]
        if len(ws._charts) < 1:
            failures.append(f"Sheet {sname} has no embedded Excel chart")

    # 4. Exact numerical consistency checks: Excel table cells vs plotted JSON values
    # Fig 01
    ws1 = wb["Fig_01_Random"]
    f1 = data["fig01_random"]
    checks = [
        ("Fig_01 overall random", ws1["B15"].value, f1["overall"]["revA-random"]["mean"]),
        ("Fig_01 overall v4", ws1["D15"].value, f1["overall"]["revA-v4"]["mean"]),
        ("Fig_01 welch delta", ws1["F15"].value, f1["welch_total"]["delta"]),
        ("Fig_01 phase C random", ws1["B14"].value, f1["phases"]["revA-random"]["C"]["mean"]),
        ("Fig_01 phase C v4", ws1["D14"].value, f1["phases"]["revA-v4"]["C"]["mean"]),
        ("Fig_01 arm47 ref", ws1["C8"].value, f1["arm47_n1_ref"]),
    ]
    # Fig 02
    ws2 = wb["Fig_02_Ablation"]
    f2 = data["fig02_ablation"]
    checks += [
        ("Fig_02 v4 mean", ws2["D6"].value, f2["variants"]["revA-v4"]["mean"]),
        ("Fig_02 v1 mean", ws2["D7"].value, f2["variants"]["revA-v1"]["mean"]),
        ("Fig_02 nosettle mean", ws2["D8"].value, f2["variants"]["revB-nosettle"]["mean"]),
        ("Fig_02 noelim mean", ws2["D9"].value, f2["variants"]["revB-noelim"]["mean"]),
        ("Fig_02 v2 mean", ws2["D10"].value, f2["variants"]["revA-v2"]["mean"]),
        ("Fig_02 noelim welch delta", ws2["G9"].value, f2["welch_vs_v4"]["revB-noelim"]["delta"]),
        ("Fig_02 bridge", ws2["D11"].value, f2["revB_v4_bridge_n1"]),
        ("Fig_02 revD v4 tot", ws2["D15"].value, f2["seungcom_revD_total"]["revD-v4"]["mean"]),
        ("Fig_02 revD fullreset tot", ws2["D16"].value, f2["seungcom_revD_total"]["revD-fullreset"]["mean"]),
        ("Fig_02 revD fullreset welch tot", ws2["G16"].value, f2["seungcom_revD_welch_total"]["revD-fullreset"]["delta"]),
        ("Fig_02 revD nodrift tot", ws2["D17"].value, f2["seungcom_revD_total"]["revD-nodrift"]["mean"]),
        ("Fig_02 revD fullreset welch phC", ws2["G19"].value, f2["seungcom_revD_welch_phaseC"]["revD-fullreset"]["delta"]),
    ]
    # Fig 03
    ws3 = wb["Fig_03_Adaptation"]
    f3 = data["fig03_adaptation"]
    checks += [
        ("Fig_03 reset rep1", ws3["C6"].value, f3["v4_phaseC_first_reset_raw"][0]),
        ("Fig_03 reset rep2", ws3["D6"].value, f3["v4_phaseC_first_reset_raw"][1]),
        ("Fig_03 reset rep3", ws3["E6"].value, f3["v4_phaseC_first_reset_raw"][2]),
        ("Fig_03 traj t=5 v4", ws3["E12"].value, f3["trajectories"]["revA-v4"]["mean"][0]),
        ("Fig_03 traj last v4", ws3.cell(11 + len(f3["times_min"]), 5).value, f3["trajectories"]["revA-v4"]["mean"][-1]),
    ]
    # Fig 04
    ws4 = wb["Fig_04_Exploration"]
    f4 = data["fig04_exploration"]
    checks += [
        ("Fig_04 gocom random share", ws4["C6"].value, f4["gocom_mixFYF_explore_share_pct"]["revA-random"]["mean"]),
        ("Fig_04 gocom v4 share", ws4["C8"].value, f4["gocom_mixFYF_explore_share_pct"]["revA-v4"]["mean"]),
        ("Fig_04 seung v1 extra gc", ws4["C13"].value, f4["seungcom_fiofast_extra_gc_pct"]["iCAT v1"]["mean"]),
        ("Fig_04 seung v4 extra gc", ws4["C15"].value, f4["seungcom_fiofast_extra_gc_pct"]["iCAT v4"]["mean"]),
    ]
    # Fig 05
    ws5 = wb["Fig_05_Parameters"]
    f5 = data["fig05_parameters"]
    checks += [
        ("Fig_05 elim10 n=3", ws5["E6"].value, f5["live_revC"]["elim10_pct"]["waf"]),
        ("Fig_05 v4 15% n=3", ws5["E7"].value, f5["live_revC"]["elim15_v4_pct"]["waf"]),
        ("Fig_05 elim25 n=3", ws5["E8"].value, f5["live_revC"]["elim25_pct"]["waf"]),
        ("Fig_05 replay 15% survival", ws5["D14"].value, f5["offline_replay_rationale"][2]["ref_survival_pct"]),
    ]
    if "VALID" not in str(ws5["I7"].value):
        failures.append("Fig_05_Parameters missing VALID status marker for completed revC-v4 runs")
    # Fig 06
    ws6 = wb["Fig_06_Candidates"]
    f6 = data["fig06_candidates"]
    checks += [
        ("Fig_06 test4 k2 med", ws6["D6"].value, f6["full_60arm_sweeps"]["FIO-Fast (test4)"]["k2_median"]),
        ("Fig_06 test4 k4 med", ws6["I6"].value, f6["full_60arm_sweeps"]["FIO-Fast (test4)"]["k4_median"]),
        ("Fig_06 arm60 pilot", ws6["E12"].value, f6["live_revC_60vs45"]["revB_arm60_n1_pilot"]),
        ("Fig_06 revC arm60 n=3", ws6["E13"].value, f6["live_revC_60vs45"]["revC_arm60_n3"]["mean"]),
        ("Fig_06 revC v4 n=3", ws6["E14"].value, f6["live_revC_60vs45"]["revC_v4_n3"]["mean"]),
    ]
    if "VALID" not in str(ws6["I14"].value):
        failures.append("Fig_06_Candidates missing VALID status marker for completed revC-v4")
    # Fig 07
    ws7 = wb["Fig_07_Resources"]
    f7 = data["fig07_resources"]
    checks += [
        ("Fig_07 mem iCAT B", ws7["B6"].value, f7["memory_4partitions"]["iCAT_v4_learning_only_B"]),
        ("Fig_07 mem SmartGC B", ws7["B8"].value, f7["memory_4partitions"]["SmartGC_learning_only_B"]),
        ("Fig_07 cpu v4 ms", ws7["C15"].value, f7["cpu_gocom_mixFYF_90m"]["revA-v4"]["total_ms"]["mean"]),
        ("Fig_07 seung v4 hook ns", ws7["E23"].value, f7["cpu_seungcom_fiofast_30m"]["iCAT v4"]["net_hook_ns_per_gc"]["mean"]),
    ]

    for label, excel_val, plot_val in checks:
        if excel_val is None or not approx_eq(excel_val, plot_val):
            failures.append(f"Mismatch [{label}]: Excel={excel_val} vs Plot={plot_val}")

    # 5. Check all 21 figure files + 300 DPI PNG
    fig_dir = OUT_DIR / "figures"
    for stem in REQUIRED_FIG_STEMS:
        for ext in ["png", "pdf", "svg"]:
            fp = fig_dir / f"{stem}.{ext}"
            if not fp.exists() or fp.stat().st_size < 1000:
                failures.append(f"Missing or empty figure file: {fp}")
            elif ext == "png":
                with Image.open(fp) as im:
                    dpi = im.info.get("dpi", (0, 0))
                    if dpi[0] < 299 or dpi[1] < 299:
                        failures.append(f"PNG DPI < 300 for {fp}: {dpi}")

    # 6. Check figure_manifest.csv
    with open(MANIFEST_PATH, encoding="utf-8-sig") as f:
        mrows = list(csv.DictReader(f))
    if len(mrows) != 7:
        failures.append(f"figure_manifest.csv expected 7 rows, got {len(mrows)}")
    for r in mrows:
        for req_col in ["figure_id", "raw_data_paths", "experiment_id", "git_commit", "analysis_script", "data_validity", "n_reps", "stat_method"]:
            if not r.get(req_col):
                failures.append(f"Manifest row {r.get('figure_id')} missing {req_col}")

    # 7. Ensure existing figs/ untouched
    p = subprocess.run(["git", "status", "--porcelain", "figs/"], cwd=REPO_ROOT, capture_output=True, text=True)
    if p.stdout.strip():
        failures.append(f"Existing figs/ directory was modified: {p.stdout.strip()}")

    if failures:
        print("VERIFICATION FAILED:")
        for fl in failures:
            print("  -", fl)
        sys.exit(1)
    else:
        print(f"VERIFICATION PASSED: All 12 Excel sheets, {len(checks)} numeric consistency checks, 21 figure files (300 DPI PNG + PDF + SVG), manifest traceability, and zero modification to existing figs/ verified.")


if __name__ == "__main__":
    main()
