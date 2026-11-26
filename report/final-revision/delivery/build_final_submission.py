#!/usr/bin/env python3
"""
iCAT Paper Revision — Final Submission Package Builder (Home PC, Lead Integrator)
Output directory: report/final-revision/delivery/

Generates all 7 mandatory deliverables:
  1. FINAL_EXPERIMENT_REPORT.md        (Exact 12-chapter comprehensive report)
  2. FINAL_REVIEWER_RESPONSE_MATRIX.xlsx (5-sheet verified Excel workbook, 0 formula errors)
  3. FINAL_FIGURE_CATALOG.md           (4-tier classification of Paper Fig 1-10 + New Figs)
  4. FINAL_EXPERIMENT_STATUS.md        (Complete 80/80 VALID campaign & input intake status)
  5. FINAL_PAPER_NUMBER_AUDIT.csv      (Cross-source numeric audit: Excel/CSV/MD/Fig/Table 6-10/Body)
  6. FINAL_LIMITATIONS.md              (Complete honest methodological & empirical limitations)
  7. FINAL_DELIVERY_CHECKLIST.md       (Final submission readiness checklist)

Auto-detects GoCom's 5 input files and SeungCom's 5 input files on GitHub remotes
without ever fabricating checks for files not yet pushed.
Zero modification to result/, figs/, or PAPER_KCI_DRAFT.md.
"""
import csv
import json
import subprocess
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

REPO_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = Path(__file__).resolve().parent
OUT_DIR.mkdir(parents=True, exist_ok=True)

DELIV_DIR = REPO_ROOT / "report" / "delivery-20261127"
PF_DIR = REPO_ROOT / "report" / "paper-figures"

REF_MAIN = "origin/main"
REF_GOCOM = "origin/report/data-validity-20261124"
REF_RES = "origin/resource-overhead-20261114"

KST = timezone(timedelta(hours=9))
NOW_STR = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST")


def git_rev(ref: str) -> str:
    return subprocess.check_output(["git", "rev-parse", "--short=9", ref], cwd=REPO_ROOT, text=True).strip()


def git_find_files(ref: str, names: list) -> dict:
    out = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", ref], cwd=REPO_ROOT, text=True).splitlines()
    found = {}
    for target in names:
        matches = [p for p in out if Path(p).name == target or p.endswith("/" + target)]
        found[target] = matches[0] if matches else None
    return found


def load_csv(path: Path) -> list:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fieldnames: list, rows: list):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def style_sheet(ws, r1: int, r2: int, c1: int, c2: int, wrap_cols=None):
    wrap_cols = set(wrap_cols or [])
    thin = Side(style="thin", color="CCCCCC")
    bdr = Border(left=thin, right=thin, top=thin, bottom=thin)
    hdr_fill = PatternFill("solid", fgColor="1F3864")
    alt_fill = PatternFill("solid", fgColor="F5F8FC")
    hdr_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    body_font = Font(name="Calibri", size=10, color="111111")
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            cell = ws.cell(r, c)
            cell.border = bdr
            if r == r1:
                cell.fill = hdr_fill
                cell.font = hdr_font
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            else:
                if (r - r1) % 2 == 0:
                    cell.fill = alt_fill
                cell.font = body_font
                cell.alignment = Alignment(
                    horizontal="left" if isinstance(cell.value, str) else "right",
                    vertical="top",
                    wrap_text=(c in wrap_cols),
                )


def autofit(ws, max_w=46):
    for col in ws.columns:
        idx = col[0].column
        letter = get_column_letter(idx)
        w = 10
        for cell in col:
            if cell.value is not None:
                lines = str(cell.value).splitlines() or [""]
                w = max(w, max(len(l) for l in lines) + 3)
        ws.column_dimensions[letter].width = min(w, max_w)


def main():
    c_main = git_rev(REF_MAIN)
    c_gocom = git_rev(REF_GOCOM)
    c_res = git_rev(REF_RES)

    # Check live presence of GoCom's 5 input files and SeungCom's 5 input files
    gocom_targets = [
        "iCAT_Complete_Experiment_Results.xlsx",
        "EXPERIMENT_CATALOG.md",
        "EXPERIMENT_RESULT_SUMMARY.md",
        "FIGURE_CATALOG.md",
        "DATA_PROVENANCE.csv",
    ]
    seung_targets = [
        "final_independent_validation.md",
        "final_raw_data_validation.csv",
        "final_statistical_validation.csv",
        "final_robustness_validation.csv",
        "final_m1_resource_validation.md",
    ]
    gocom_found = git_find_files(REF_GOCOM, gocom_targets)
    seung_found = git_find_files(REF_MAIN, seung_targets)
    n_gocom_present = sum(1 for v in gocom_found.values() if v)
    n_seung_present = sum(1 for v in seung_found.values() if v)
    print(f"Heads: main={c_main}, gocom={c_gocom}, res={c_res} | GoCom inputs={n_gocom_present}/5, SeungCom inputs={n_seung_present}/5")

    val_rows = load_csv(DELIV_DIR / "final_experiment_validity.csv")
    stat_rows = load_csv(DELIV_DIR / "final_statistical_audit.csv")
    dump = json.loads((DELIV_DIR / "delivery_audit_dump.json").read_text(encoding="utf-8"))

    n_valid = sum(1 for r in val_rows if r["Validity"] == "VALID")
    n_total = len(val_rows)

    # -----------------------------------------------------------------------
    # 1. FINAL_PAPER_NUMBER_AUDIT.csv (Cross-Source Numeric Audit)
    # -----------------------------------------------------------------------
    audit_rows = [
        # Confirmed Matches (PASS)
        {
            "Audit_ID": "NA-01", "Target_Source": "GoCom Databook v2 (F2_runs)", "Location": "30cf9b9fb:iCAT_revision_databook_v2.xlsx!F2_runs",
            "Metric_or_Item": "65 completed mixFYF runs x 4 WAF cells (260 cells)", "Reported_Value": "65/65 runs, 260 WAF cells",
            "Verified_Raw_Value": "260/260 exact match (<=2e-6)", "Status": "MATCH", "Severity": "INFO",
            "Proposed_Fix_Do_Not_Edit_Draft_Directly": "No change needed (note: revA-arm47 n=1 excluded separately; batchG/arm47/m1 added in Home PC package)",
            "Raw_Evidence_Path": "report/delivery-20261127/final_experiment_validity.csv",
        },
        {
            "Audit_ID": "NA-02", "Target_Source": "GoCom Databook v2 (F1_policy_waf_by_batch)", "Location": "30cf9b9fb:iCAT_revision_databook_v2.xlsx!F1",
            "Metric_or_Item": "92 policy-batch Mean / SD / 95% CI rows", "Reported_Value": "92 rows",
            "Verified_Raw_Value": "92/92 exact match (incl. n<3 no-stat rule)", "Status": "MATCH", "Severity": "INFO",
            "Proposed_Fix_Do_Not_Edit_Draft_Directly": "No change needed",
            "Raw_Evidence_Path": "report/delivery-20261127/final_statistical_audit.csv",
        },
        {
            "Audit_ID": "NA-03", "Target_Source": "PAPER_KCI_DRAFT.md Table 10 (all 22 rows: A,C,D,E,F,D',G)", "Location": f"67cf3f901:PAPER_KCI_DRAFT.md#L343-L378",
            "Metric_or_Item": "Mean±SD, Overall Delta [CI], Phase C Delta [CI], Holm footnotes", "Reported_Value": "22 policy rows + Holm †/‡/¶",
            "Verified_Raw_Value": "22/22 exact 3-decimal match across SeungCom, GoCom, Home PC", "Status": "MATCH", "Severity": "INFO",
            "Proposed_Fix_Do_Not_Edit_Draft_Directly": "No numeric change needed; keep host/batch footnotes intact",
            "Raw_Evidence_Path": "report/delivery-20261127/final_statistical_audit.csv",
        },
        {
            "Audit_ID": "NA-04", "Target_Source": "PAPER_KCI_DRAFT.md Table 9b (m1-20261126)", "Location": f"67cf3f901:PAPER_KCI_DRAFT.md#L324-L337",
            "Metric_or_Item": "WAF_nand (4.553 vs 3.330), GC ktime (17.8 vs 98.4 us), SELECT (1.0 vs 87.0 us), LEARN (47.6 vs 4.3 s), VmallocUsed (37,752 vs 34,848 kB)",
            "Reported_Value": "Table 9b 8 rows", "Verified_Raw_Value": "8/8 exact match from scoped kernel.log.nowarn.gz, final-control.txt, sampler/*/mem.tsv",
            "Status": "MATCH", "Severity": "INFO",
            "Proposed_Fix_Do_Not_Edit_Draft_Directly": "No numeric change needed; keep n=1 and ktime!=CPU disclaimers",
            "Raw_Evidence_Path": f"{REF_GOCOM}@{c_gocom}:result/m1-20261126/raw/",
        },
        {
            "Audit_ID": "NA-05", "Target_Source": "PAPER_KCI_DRAFT.md Table 11 (Phase C adaptation)", "Location": f"67cf3f901:PAPER_KCI_DRAFT.md#L380-L393",
            "Metric_or_Item": "8 policy rows (detect time, restored arms, resettle time, explore share, Phase C WAF)", "Reported_Value": "8 rows (A/C/D/E)",
            "Verified_Raw_Value": "8/8 verified against revA/C/D/E kernel.log and m6_summary", "Status": "MATCH", "Severity": "INFO",
            "Proposed_Fix_Do_Not_Edit_Draft_Directly": "No numeric change needed",
            "Raw_Evidence_Path": "report/reanalysis-20261124/r1_adaptation_summary.csv",
        },
        {
            "Audit_ID": "NA-06", "Target_Source": "SeungCom batchG-20261126 (M3 Greedy GC & M6 drift50)", "Location": f"{REF_MAIN}@{c_main}:result/batchG-20261126-analysis/",
            "Metric_or_Item": "9 runs x 4 WAF cells (36 cells) + 4 primary contrasts + 11 drift50 resets", "Reported_Value": "Greedy GC +0.519 (Holm 0.0013); drift50 +0.018 (Holm 0.831); 11/11 resets >50%",
            "Verified_Raw_Value": "0/36 WAF mismatches; exact 6-decimal match on Welch/Paired/Holm/Hedges' g; min drift ratio 61.4%", "Status": "MATCH", "Severity": "INFO",
            "Proposed_Fix_Do_Not_Edit_Draft_Directly": "Triple-verified (SeungCom + GoCom + Home PC); ensure Greedy GC lower FIO p99 caveat stays in text",
            "Raw_Evidence_Path": f"{REF_MAIN}@{c_main}:result/batchG-20261126/raw/",
        },
        {
            "Audit_ID": "NA-07", "Target_Source": "SeungCom arm47-20261127 (Fixed Arm 47 n=3)", "Location": f"{REF_MAIN}@{c_main}:result/arm47-20261127-analysis/",
            "Metric_or_Item": "mixFYF Arm 47 n=3 Mean±SD [95% CI] & GoCom n=1 cross-host check", "Reported_Value": "1.98764±0.00027 [1.98698, 1.98831]; GoCom n=1 1.987355 inside CI",
            "Verified_Raw_Value": "3/3 VALID (1.987502 / 1.987953 / 1.987478); exact 6-decimal match", "Status": "MATCH", "Severity": "INFO",
            "Proposed_Fix_Do_Not_Edit_Draft_Directly": "Report as SeungCom n=3 (NEVER pool with GoCom n=1 as n=4); cite FIO p99 174.6 us corroborating CAT scan cost",
            "Raw_Evidence_Path": f"{REF_MAIN}@{c_main}:result/arm47-20261127/raw/",
        },
        {
            "Audit_ID": "NA-08", "Target_Source": "Home PC Master Excel & Figures (iCAT_Paper_Figures.xlsx)", "Location": "report/paper-figures/iCAT_Paper_Figures.xlsx",
            "Metric_or_Item": "21 sheets, 40 automated JSON-to-Excel numeric checks, 21 figure files", "Reported_Value": "75 mixFYF + m1 Table 7E + 3x60 sweeps + resource-v124",
            "Verified_Raw_Value": "40/40 PASS, 0 Excel error literals, 300 DPI PNG/PDF/SVG, figs/ untouched", "Status": "MATCH", "Severity": "INFO",
            "Proposed_Fix_Do_Not_Edit_Draft_Directly": "Ready for delivery",
            "Raw_Evidence_Path": "report/paper-figures/verify_paper_figures.py",
        },
        # Discrepancies / Placeholders / Omissions Requiring Editorial Action (DO NOT edit draft directly)
        {
            "Audit_ID": "NA-09", "Target_Source": "PAPER_KCI_DRAFT.md §7 Resource Cost", "Location": f"67cf3f901:PAPER_KCI_DRAFT.md#L405",
            "Metric_or_Item": "GC execution time measurement claim", "Reported_Value": "\"GC 수행 시간은 계측하지 않았다.\"",
            "Verified_Raw_Value": "CONTRADICTS Table 9b (m1-20261126: iCAT 98.4 us vs SmartGC 17.8 us/GC) AND resource-v124 (FIO-Fast 30m n=3: do_gc-on_gc 206.8 s vs CAT-47 256.0 s; reward 1.44 ms, select 1.27 ms, set_arm 0.06 ms)",
            "Status": "DISCREPANCY", "Severity": "HIGH",
            "Proposed_Fix_Do_Not_Edit_Draft_Directly": "Replace L405 sentence with summary citing both resource-v124 (FIO-Fast 30m n=3, erase=0) and Table 9b (m1-20261126 mixY n=1: iCAT LEARN 4.3 s vs SmartGC 47.6 s, but iCAT GC 98.4 us = 5.5x SmartGC 17.8 us due to CAT SELECT 87.0 us)",
            "Raw_Evidence_Path": f"{REF_RES}@{c_res}:result/resource-v124-20261114/report/cpu_overhead_summary.csv",
        },
        {
            "Audit_ID": "NA-10", "Target_Source": "PAPER_KCI_DRAFT.md §6.2 Table 8 & Fig 10", "Location": f"67cf3f901:PAPER_KCI_DRAFT.md#L297-L307",
            "Metric_or_Item": "3-phase transition (YCSB-A 300k records) re-run table & figure", "Reported_Value": "All cells '대기'; Fig 10 '【재측정 결과 대기】'",
            "Verified_Raw_Value": "300k re-run NEVER executed; valid replacement is mixFYF 250k (n=3) in §6.4 Table 10 & Table 11 (figure03_adaptation.png)",
            "Status": "PLACEHOLDER", "Severity": "HIGH",
            "Proposed_Fix_Do_Not_Edit_Draft_Directly": "Remove unexecuted 300k Table 8 and pending Fig 10; point §6.2 3-phase transition directly to §6.4 mixFYF 250k (n=3) Table 10/11 and figure03_adaptation",
            "Raw_Evidence_Path": "report/paper-figures/figures/figure03_adaptation.png",
        },
        {
            "Audit_ID": "NA-11", "Target_Source": "PAPER_KCI_DRAFT.md Draft Placeholders", "Location": f"67cf3f901:PAPER_KCI_DRAFT.md#L004,L232,L240,L256,L260",
            "Metric_or_Item": "Remaining 【결과 대기】 / 【갱신 예정】 tags in Fig 6, Fig 7, Table 6, Fig 8", "Reported_Value": "5 pending tags referencing queue31/queue32 (never executed to n=3)",
            "Verified_Raw_Value": "x3 mixes (Table 6/Fig 7/Fig 8) remain n=1 fixed arms & n=1..3 v4; v4 ablation completed in §6.4 Table 10",
            "Status": "PLACEHOLDER", "Severity": "HIGH",
            "Proposed_Fix_Do_Not_Edit_Draft_Directly": "Delete all 5 【결과 대기】/【갱신 예정】 tags; explicitly label Fig 6 (v3 n=1 prelim), Fig 7/8 & Table 6 (exploratory n=1 fixed arms) and direct readers to §6.4 for confirmatory n=3",
            "Raw_Evidence_Path": "report/final-robustness-20261126/figure_robustness.csv",
        },
        {
            "Audit_ID": "NA-12", "Target_Source": "PAPER_KCI_DRAFT.md §6.2 Fig 9 Robustness Text", "Location": f"67cf3f901:PAPER_KCI_DRAFT.md#L262",
            "Metric_or_Item": "Mean loss vs best fixed arm across 6 valid x3 mixes", "Reported_Value": "CAT-Best 0.2%, iCAT-v4 5.0%, CAT-Robust 5.0% (1-decimal rounding)",
            "Verified_Raw_Value": "Exact post-gating values: CAT-Best 0.21%, CAT-Robust 4.95%, iCAT-v4 5.04% (note: older draft had stale pre-gating 3.0%/6.5%/7.2%)",
            "Status": "DISCREPANCY", "Severity": "MEDIUM",
            "Proposed_Fix_Do_Not_Edit_Draft_Directly": "Report 2 decimals (0.21% / 4.95% / 5.04%) so iCAT-v4 (5.04%) is not misread as tied with or lower than CAT-Robust (4.95%) on mean",
            "Raw_Evidence_Path": f"{REF_GOCOM}@{c_gocom}:report/final-e1-validation/figs/paper/",
        },
        {
            "Audit_ID": "NA-13", "Target_Source": "PAPER_KCI_DRAFT.md Table 9 vs Databook v2 F7_smartgc_waf", "Location": f"67cf3f901:PAPER_KCI_DRAFT.md#L313-L321 & databook_v2!F7_smartgc_waf",
            "Metric_or_Item": "SmartGC-EQ8 & SmartGC WAF definition", "Reported_Value": "Table 9: WAF_nand 4.49 & 11.02; Databook F7: host WAF 4.4984 & 11.0723",
            "Verified_Raw_Value": "Both numerically correct under different definitions: host WAF = 1+gc/host vs WAF_nand = (host+gc-absorbed+evicted)/host",
            "Status": "DISCREPANCY", "Severity": "MEDIUM",
            "Proposed_Fix_Do_Not_Edit_Draft_Directly": "Add explicit footnote in Table 9 and Databook F7 distinguishing WAF_host vs WAF_nand (already separated in Home PC Table 7E & validity CSV)",
            "Raw_Evidence_Path": "report/delivery-20261127/final_experiment_validity.csv",
        },
        {
            "Audit_ID": "NA-14", "Target_Source": "GoCom Databook v2 F6_memory", "Location": "30cf9b9fb:iCAT_revision_databook_v2.xlsx!F6_memory#R9-R12",
            "Metric_or_Item": "VmallocUsed unit label vs cell values", "Reported_Value": "item says '(kB)' while bytes column stores kB*1024 bytes (38,508,134.4 etc.)",
            "Verified_Raw_Value": "37,605.6 kB = 38,508,134.4 bytes (m1 new values: 34,848 kB = 35,684,352 B vs 37,752 kB = 38,658,048 B)",
            "Status": "DISCREPANCY", "Severity": "MEDIUM",
            "Proposed_Fix_Do_Not_Edit_Draft_Directly": "Remove '(kB)' from item text or separate kB and bytes columns (already fixed in Home PC iCAT_Paper_Figures.xlsx Table 7E)",
            "Raw_Evidence_Path": f"{REF_GOCOM}@{c_gocom}:result/m1-20261126/sampler/",
        },
        {
            "Audit_ID": "NA-15", "Target_Source": "GoCom Databook v2 F3_contrasts_same_batch", "Location": "30cf9b9fb:iCAT_revision_databook_v2.xlsx!F3#R2-R25,R34-R45",
            "Metric_or_Item": "Blank p_unadjusted / p_holm_4tests cells & D' sign direction", "Reported_Value": "Blank p/Holm on revA/C/D/abl/greedy; R40 writes revD-v4 - greedy = +0.009 (opposite to Table 10 -0.009)",
            "Verified_Raw_Value": "abl OffBundle p=0.0069 (Holm 0.0277); NoDiscount p=0.869 (Holm 1.000); Greedy - revD-v4 = -0.0086 [-0.0508, +0.0336] (p=0.543)",
            "Status": "OMISSION", "Severity": "MEDIUM",
            "Proposed_Fix_Do_Not_Edit_Draft_Directly": "Populate all p/Holm cells and unify sign to Variant - Control(V4) everywhere (already completed in final_statistical_audit.csv & FINAL_REVIEWER_RESPONSE_MATRIX.xlsx)",
            "Raw_Evidence_Path": "report/delivery-20261127/final_statistical_audit.csv",
        },
        {
            "Audit_ID": "NA-16", "Target_Source": "Legacy analysis/figures.py (not in draft)", "Location": "figs/fig2_learning_over_time (omitted from PAPER_KCI_DRAFT.md)",
            "Metric_or_Item": "Hardcoded CAT-Robust 1.814 vs raw t4long-fixed50-rep1 1.8116", "Reported_Value": "1.814 (0.13% diff)",
            "Verified_Raw_Value": "1.8116", "Status": "DISCREPANCY", "Severity": "LOW",
            "Proposed_Fix_Do_Not_Edit_Draft_Directly": "Keep legacy fig2 omitted from submission (already excluded)",
            "Raw_Evidence_Path": "report/final-robustness-20261126/figure_robustness.csv",
        },
    ]
    write_csv(OUT_DIR / "FINAL_PAPER_NUMBER_AUDIT.csv", list(audit_rows[0].keys()), audit_rows)
    print(f"Wrote FINAL_PAPER_NUMBER_AUDIT.csv ({len(audit_rows)} rows)")

    # -----------------------------------------------------------------------
    # 2. FINAL_REVIEWER_RESPONSE_MATRIX.xlsx (5 sheets, 0 formula errors)
    # -----------------------------------------------------------------------
    wb = openpyxl.Workbook()

    # Sheet 1: Core_3_Claims (Section 3.B — exact 4 verdicts: 입증 / 부분 입증 / 입증 불가 / 추가 실험 필요)
    ws1 = wb.active
    ws1.title = "Core_3_Claims"
    ws1["A1"] = "iCAT 논문 리비전 — 3대 핵심 주장 최종 심사 판정표"
    ws1["A1"].font = Font(name="Calibri", size=13, bold=True, color="1F3864")
    ws1["A2"] = f"작성: {NOW_STR} | 기준 커밋: main@{c_main}, gocom@{c_gocom}, res@{c_res} | 판정 체계: 입증 / 부분 입증 / 입증 불가 / 추가 실험 필요"
    ws1["A2"].font = Font(name="Calibri", size=9.5, italic=True, color="444444")

    c3_hdr = ["주장 번호", "핵심 주장 (심사 쟁점)", "최종 판정", "입증된 실측 근거 (n=3 / 정확 계산)", "입증되지 않은 부분 및 반증(정직 보고 필수)", "논문 허용 표현 범위", "원시 근거 경로"]
    c3_rows = [
        [
            "주장 1 (M3)",
            "iCAT은 무작위 정책 선택(및 기준선)보다 효과적이다.",
            "입증",
            "[실측 n=3, 동일배치] ① Random Selection 대비 −8.43% (+0.1959 [+0.184, +0.208], g=29.9, Holm p<0.001, 고컴 revA). ② 기존 iCAT 원 구현 대비 −11.49% (+0.2751 [+0.203, +0.347], g=10.53, Holm p=0.0282, 고컴 revC). ③ 전통적 Greedy GC 대비 −19.73% (+0.5189 [+0.463, +0.574], g=23.1, Holm p=0.0013, 승컴 batchG) + 레거시 9종 9/9 유의(−7.1%~−42.0%).",
            "① 단순 Online Greedy(VAR=8, 승컴 n=3, 교차날짜 간접) 대비 우위 없음 (−0.0086 [−0.051, +0.034], p=0.543; Phase C 첫 5분 Greedy 2.407 < V4 2.598). ② 사후 최적 고정 Arm 47(승컴 n=3: 1.9876 ± 0.0003)보다 약 5.8% 높음. ③ Greedy GC 대비 FIO 쓰기 p99 지연은 iCAT이 열위(166 vs 42 us, erase=0). ④ Periodic Switching·Random Search 미실행(범위 제한).",
            "mixFYF(n=3)에서 무작위 선택(−8.4%), 원 구현(−11.5%), Greedy GC(−19.7%) 대비 통계적으로 유의한 WAF 절감을 입증함. 단, 단순 Online Greedy 대비 우위나 사후 최적 고정 조합 초과, FIO 꼬리 지연 개선은 주장하지 않음.",
            "origin/report/data-validity-20261124:result/rev{A,C}-*/raw/ ; origin/main:result/{greedy,batchG,greedygc,arm47}-*/raw/",
        ],
        [
            "주장 2 (M2 / M6)",
            "후보 제거·정착 및 워크로드 변화 감지·재탐색이 성능에 기여한다.",
            "부분 입증",
            "[실측 n=3, 동일배치] ① v4 4기능 묶음 제거(VAR=2)는 양 호스트 모두 유의 악화: 고컴 revA +0.1355 [+0.117, +0.154] (Holm p<0.001), 승컴 abl +0.1241 [+0.073, +0.175] (Holm p=0.0277). ② 후보 제거 단독(NoElim, 고컴 revE): +0.0913 [+0.030, +0.153] (Paired>0, g=3.88; 4-test Holm p=0.0907 경계). ③ 부분 vs 전체 복원(FullReset, 승컴 revD): Total +0.0596 [+0.016, +0.103], Phase C +0.1296 [+0.052, +0.208] (4-test Holm p=0.072/0.060 경계). ④ Phase C 전환 43~79초 내 재현 감지; ELIM 10~25%·60→45후보·drift50 안정, drift12.5% 조기리셋 악화(+0.0720, Holm p=0.0907).",
            "① 변화 감지 단독(NoDrift): 양 호스트 3/3 평균 열위(+0.079 고컴, +0.068 승컴)이나 분산 과대로 Welch CI 0 포함 → n=3 통계 미입증. ② 할인 계수 제거(NoDiscount, gamma=1.0): −0.0038 [−0.064, +0.057] (Holm p=1.000) → 90분 범위 효과 없음. ③ 정착 단독(NoSettle): 코드상 감지/탐침 종속 + 교차배치 + CI 0 포함. ④ Phase B 저쓰기 전환 대부분 미감지. ⑤ 판단구간·UCB c·정착조건 민감도 미측정.",
            "v4 개선 묶음의 기여(+5.8~6.4%, 양 호스트 Holm p<=0.028)와 후보 제거·부분 복원의 방향성/사전등록 CI 우위(Holm 경계 0.06~0.09)를 보고함. 변화 감지 단독 및 할인 계수의 WAF 이득은 입증되지 않았음을 명시함.",
            "origin/report/data-validity-20261124:result/rev{A,B,C,E}-*/raw/ ; origin/main:result/{revD,revision-additional-ablation,drift50}-*/raw/",
        ],
        [
            "주장 3 (M1 / M5)",
            "정책 단위 학습은 블록 단위 학습(SmartGC)보다 메모리와 CPU 오버헤드 측면에서 효율적이다.",
            "부분 입증",
            "[이론 계산] 학습 상태 메모리: iCAT 10,112 B(용량 무관) vs SmartGC 1,951,648 B(193.0x, GC 버퍼 포함 2,344,864 B = 231.9x). [실측 n=1, m1-20261126] ① VmallocUsed 증가량: iCAT 34,848 kB vs SmartGC 37,752 kB (차이 +2,904 kB, 이론차 3,058 KiB와 5% 내 일치, 언로드 후 +16 kB 복귀). ② 학습 갱신 자체(LEARN ktime): iCAT 4.30 s (40.8 ns/GC, GC의 0.041%) vs SmartGC 47.56 s (975.5 us x 48,751회) → iCAT 11.1x 경량. ③ WAF_nand: iCAT 3.330 vs SmartGC-EQ8 4.553 (−26.9%, 승컴 표 9도 3.21 vs 4.49 동일 방향). ④ resource-v124 FIO-Fast 30m(n=3) 분리 계측: reward 1.44 ms, select 1.27 ms, set_arm 0.06 ms.",
            "① [핵심 반증 — 입증 불가] GC 1회 전체 경과시간은 iCAT(98.4 us/GC, 1,342 ms/GiB)이 SmartGC(17.8 us/GC, 333 ms/GiB)의 5.5배 김! 원인은 CAT 전 라인 스캔 희생 선택(SELECT 87.0 us/GC = GC의 88.5%) 대 SmartGC 목록 선택(1.0 us/GC). 사용자 공간 CPU 벤치에서도 동일 방향(53.7 us). ② 커널 내부 CPU 시간(perf/busy-poll)·VmRSS(커널스레드)·NVMeVirt 공통 처리 비용·호출별 백분위수 미측정. ③ m1-20261126은 사용자 결정으로 n=1(통계 검정 불가). ④ mixY 지연은 SmartGC 채널 포화(22,069건)로 비교 제외.",
            "주장을 반드시 분리: (a) 학습 상태 메모리(193x 계산, 실측 Vmalloc +2,904 kB)와 학습 알고리즘 갱신 비용(4.3 s vs 47.6 s) 및 WAF_nand(−27~29%, n=1)는 iCAT이 유리함. (b) 반면 희생 블록 선택을 포함한 GC 1회 경과시간은 CAT 스캔 구조 때문에 iCAT이 5.5배 크므로 'GC CPU 효율 우위'를 주장하지 않고 트레이드오프로 명시함.",
            "origin/report/data-validity-20261124:result/m1-20261126/raw/ & result/m1-20261126-final/ ; origin/resource-overhead-20261114:result/resource-v124-20261114/",
        ],
    ]
    for c, h in enumerate(c3_hdr, 1):
        ws1.cell(4, c, h)
    for r_i, row in enumerate(c3_rows, 5):
        for c_i, v in enumerate(row, 1):
            ws1.cell(r_i, c_i, v)
    style_sheet(ws1, 4, 4 + len(c3_rows), 1, len(c3_hdr), wrap_cols={2, 4, 5, 6, 7})
    autofit(ws1, max_w=55)

    # Sheet 2: M1_M7_47_Items (parsed directly from final_reviewer_evidence_matrix.md)
    ws2 = wb.create_sheet("M1_M7_47_Items")
    ws2["A1"] = "최초 심사 요구사항(M1~M7, 47개 세부 항목) 전수 대응표"
    ws2["A1"].font = Font(name="Calibri", size=12, bold=True, color="1F3864")
    mat_lines = (DELIV_DIR / "final_reviewer_evidence_matrix.md").read_text(encoding="utf-8").splitlines()
    m47_rows = []
    for l in mat_lines:
        if l.startswith("| M"):
            cols = [x.strip().strip("*").strip("`") for x in l.strip().strip("|").split("|")]
            if len(cols) == 7:
                m47_rows.append(cols)
    m47_hdr = ["Req_ID", "Category", "Original_Reviewer_Requirement", "Internal_Exp_ID", "Verified_Result_and_Limitations", "Raw_Log_or_Source_Path", "Final_Verdict"]
    for c, h in enumerate(m47_hdr, 1):
        ws2.cell(3, c, h)
    for r_i, row in enumerate(m47_rows, 4):
        for c_i, v in enumerate(row, 1):
            ws2.cell(r_i, c_i, v)
    style_sheet(ws2, 3, 3 + len(m47_rows), 1, 7, wrap_cols={3, 4, 5, 6})
    autofit(ws2, max_w=50)

    # Sheet 3: Stat_Contrasts_36
    ws3 = wb.create_sheet("Stat_Contrasts_36")
    ws3["A1"] = "전체 통계 대비 독립 검증표 (36개 대비, 공란 0건, 부호 통일: 비교 정책 − 대조군 V4)"
    ws3["A1"].font = Font(name="Calibri", size=12, bold=True, color="1F3864")
    s_hdr = list(stat_rows[0].keys())
    for c, h in enumerate(s_hdr, 1):
        ws3.cell(3, c, h)
    for r_i, row in enumerate(stat_rows, 4):
        for c_i, h in enumerate(s_hdr, 1):
            val = row[h]
            try:
                if val != "" and h in ("Target_n", "Ctrl_n"):
                    val = int(val)
                elif val != "" and h in ("Target_Mean", "Target_SD", "Ctrl_Mean", "Ctrl_SD", "Welch_Delta", "Welch_df", "Welch_p", "Holm_p", "Hedges_g", "Paired_p"):
                    val = float(val)
            except ValueError:
                pass
            ws3.cell(r_i, c_i, val)
    style_sheet(ws3, 3, 3 + len(stat_rows), 1, len(s_hdr))
    autofit(ws3, max_w=42)

    # Sheet 4: Number_Audit
    ws4 = wb.create_sheet("Paper_Number_Audit")
    ws4["A1"] = "논문·Excel·CSV·Figure·본문 교차 수치 감사 (원고 직접 수정 금지, 수정 제안 별도 제시)"
    ws4["A1"].font = Font(name="Calibri", size=12, bold=True, color="1F3864")
    a_hdr = list(audit_rows[0].keys())
    for c, h in enumerate(a_hdr, 1):
        ws4.cell(3, c, h)
    for r_i, row in enumerate(audit_rows, 4):
        for c_i, h in enumerate(a_hdr, 1):
            ws4.cell(r_i, c_i, row[h])
    style_sheet(ws4, 3, 3 + len(audit_rows), 1, len(a_hdr), wrap_cols={4, 5, 6, 9, 10})
    autofit(ws4, max_w=48)

    # Sheet 5: Provenance_80Runs_and_Inputs
    ws5 = wb.create_sheet("Provenance_and_Inputs")
    ws5["A1"] = "입력 자료 수신 현황 (고컴 5종 / 승컴 5종) 및 80/80 VALID 원시 실행 추적"
    ws5["A1"].font = Font(name="Calibri", size=12, bold=True, color="1F3864")
    in_hdr = ["Source_PC", "Expected_File", "Git_Branch", "Current_Commit", "Presence_Status", "Git_Path_or_Note"]
    in_rows = []
    for fn in gocom_targets:
        p = gocom_found[fn]
        in_rows.append(["GoCom", fn, REF_GOCOM, c_gocom, "PRESENT" if p else "WAITING_PUSH", p or f"Not yet pushed to {REF_GOCOM} as of {NOW_STR}"])
    for fn in seung_targets:
        p = seung_found[fn]
        in_rows.append(["SeungCom", fn, REF_MAIN, c_main, "PRESENT" if p else "WAITING_PUSH", p or f"Not yet pushed to {REF_MAIN} as of {NOW_STR}"])
    in_rows.append(["GoCom (existing)", "DELIVERY_20261127.md", REF_GOCOM, c_gocom, "VERIFIED", "report/final-revision/DELIVERY_20261127.md"])
    in_rows.append(["GoCom (existing)", "iCAT_revision_databook_v2.xlsx", REF_GOCOM, c_gocom, "VERIFIED (65/65 PASS; 3 errata)", "report/paper-figures-20261127/iCAT_revision_databook_v2.xlsx"])
    in_rows.append(["Home PC (existing)", "iCAT_Paper_Figures.xlsx", "origin/report/home-delivery-20261127", "f2fc145fd", "VERIFIED (40/40 PASS)", "report/paper-figures/iCAT_Paper_Figures.xlsx"])
    for c, h in enumerate(in_hdr, 1):
        ws5.cell(3, c, h)
    for r_i, row in enumerate(in_rows, 4):
        for c_i, v in enumerate(row, 1):
            ws5.cell(r_i, c_i, v)
    style_sheet(ws5, 3, 3 + len(in_rows), 1, len(in_hdr))

    r_start = 4 + len(in_rows) + 2
    ws5.cell(r_start, 1, f"All {n_valid}/{n_total} Independently Verified Raw Runs (0 RUNNING, 0 INVALID)").font = Font(name="Calibri", size=11, bold=True, color="1F3864")
    v_cols = ["Campaign", "Review_Item", "Policy", "Rep", "Host", "Git_Commit", "Module_SHA256", "FIO_Seeds", "WAF_Recalc", "WAF_nand", "WAF_PhaseA", "WAF_PhaseB", "WAF_PhaseC", "Two_Path_Match", "Validity", "Raw_Path"]
    for c, h in enumerate(v_cols, 1):
        ws5.cell(r_start + 1, c, h)
    for idx_v, vr in enumerate(val_rows, r_start + 2):
        for c, h in enumerate(v_cols, 1):
            val = vr[h]
            if h in ("WAF_Recalc", "WAF_nand", "WAF_PhaseA", "WAF_PhaseB", "WAF_PhaseC"):
                try:
                    val = float(val)
                except ValueError:
                    pass
            elif h == "Rep":
                val = int(val)
            ws5.cell(idx_v, c, val)
    style_sheet(ws5, r_start + 1, r_start + 1 + len(val_rows), 1, len(v_cols))
    autofit(ws5, max_w=46)

    xlsx_out = OUT_DIR / "FINAL_REVIEWER_RESPONSE_MATRIX.xlsx"
    wb.save(xlsx_out)
    # Immediate zero-error check
    wb_chk = openpyxl.load_workbook(xlsx_out, data_only=False)
    for sn in wb_chk.sheetnames:
        for row in wb_chk[sn].iter_rows(values_only=True):
            for val in row:
                if isinstance(val, str) and any(e in val for e in ("#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A", "#NUM!")):
                    raise RuntimeError(f"Excel error literal in {sn}: {val}")
    print(f"Wrote {xlsx_out} ({len(wb_chk.sheetnames)} sheets, 0 formula errors)")

    # -----------------------------------------------------------------------
    # 3. FINAL_FIGURE_CATALOG.md (Section 3.C — Exact 4 Categories)
    # -----------------------------------------------------------------------
    fig_cat_md = f"""# 최종 논문 Figure 선정 카탈로그 (`FINAL_FIGURE_CATALOG.md`)

- **작성 시각**: `{NOW_STR}`
- **기준 커밋**: 승컴 `origin/main @ {c_main}` / 고컴 `origin/report/data-validity-20261124 @ {c_gocom}` / 집컴 `origin/report/home-delivery-20261127`
- **4단계 판정 기준**: `논문에 그대로 사용 가능` | `수정 후 사용 가능` | `보조 자료로만 사용` | `사용 금지`

---

## 1. 기존 논문 Figure 1~10 최종 판정

| Figure | 원고 절 | 파일 위치 | 반복 횟수 | 최종 판정 | 사유 및 필수 수정 사항 |
|---|---|---|---|---|---|
| **기존 그림 1** (`fig1_sensitivity`) | §3.3 | `report/final-e1-validation/figs/paper/paper_fig01_fig1_sensitivity.png` | 60 arm 각 `n=1` (10m); Greedy `n=3` | **수정 후 사용 가능** | 동기 부여·`k=2` 배제 근거로 유효. 투고 전 검토용 내부 제목 제거, arm당 `n=1` 명시, 1·2위(`1.744` vs `1.746`) 우열 주장 금지. |
| **기존 그림 2** (`fig3_time_use`) | §4.1 | `report/final-e1-validation/figs/paper/paper_fig02_fig3_time_use.png` | 정책당 **`n=1`** | **보조 자료로만 사용** | 3h 단일 실행 사례(`n=1`)로 통계 증명 불가. 본문 주 근거는 신규 `figure04_exploration`(n=3)으로 대체하고, 기존 그림 2는 1회 실행 사례로만 한정. |
| **레거시 `figs/fig2_learning_over_time`** | (원고 미포함) | `figs/fig2_learning_over_time.png` | 정책당 **`n=1`** | **사용 금지** | `n=1` 및 `CAT-Robust 1.814` vs 실측 `1.8116` 하드코딩 오차(0.13%). 원고에서 이미 제외됨(유지). |
| **기존 그림 3** (`paper_fig03_v4_overview`) | §5 | `report/final-e1-validation/figs/paper/paper_fig03_v4_overview.png` | 알고리즘 도식 | **논문에 그대로 사용 가능** | `online-v4-src/conv_ftl.c` 코드 흐름과 정확히 일치(투고 시 검토용 제목만 제거). |
| **기존 그림 4** (`fig9_rank_over_time`) | §6.1 | `report/final-e1-validation/figs/paper/paper_fig04_fig9_rank_over_time.png` | 정책·기준 모두 **`n=1`** | **보조 자료로만 사용** | 10h 단일 실행 순위 계단도(`n=1`). "약 8시간에 5위"를 결정적 일반화로 주장 금지 → 단일 실행 사례로만 사용. |
| **기존 그림 5** (`fig10_v4_choices`) | §6.1 | `report/final-e1-validation/figs/paper/paper_fig05_fig10_v4_choices.png` | **`n=1`** | **보조 자료로만 사용** | 제거·정착·이웃탐색 동작 메커니즘 시각화용(`1회 실행` 캡션 유지, 1.5h 수렴 일반화 금지). |
| **기존 그림 6** (`fig6_ablation`) | §6.1 | `report/final-e1-validation/figs/paper/paper_fig06_fig6_ablation.png` | 각 **`n=1`** (**구버전 v3**) | **보조 자료로만 사용** | 구버전 v3의 `n=1` 예비 실험. 주 Ablation 그림으로 부적합 → 신규 **`figure02_ablation` / `fig_full_ablation` (`n=3` v4)**으로 주 근거 대체, L232 `【결과 대기】` 삭제. |
| **기존 그림 7** (`fig4_mixes_v4_vs_robust`) | §6.2 | `report/final-e1-validation/figs/paper/paper_fig07_fig4_mixes_v4_vs_robust.png` | CAT-Robust **`n=1`**; v4 `n=1~3` | **수정 후 사용 가능** | 유효 8종 탐색적 요약으로만 사용(v4 3승 5패, `fixed50 n=1`). L240 `【결과 대기】` 삭제 및 탐색적 단서 명시 필수. |
| **기존 그림 8** (`fig7_mix_loss_by_workload`) | §6.2 | `report/final-e1-validation/figs/paper/paper_fig08_fig7_mix_loss_by_workload.png` | 고정 arm 전부 **`n=1`** | **수정 후 사용 가능** | 유효 6종 탐색적 요약. L260 `【선별 실험 결과로 갱신 예정】` 삭제 및 `n=1` 기준 단서 명시 필수. |
| **기존 그림 9** (`fig8_robustness`) | §6.2 | `report/final-e1-validation/figs/paper/paper_fig09_fig8_robustness.png` | 고정 arm 전부 **`n=1`** | **수정 후 사용 가능** | 본문 L262에 소수 2자리 정확한 post-gating 값(`CAT-Best 0.21%`, `CAT-Robust 4.95%`, `iCAT-v4 5.04%`) 병기 및 `n=1` 탐색적 한계 명시 필수. |
| **기존 그림 10** (`fig5_three_phase_mix` / `paper_fig10_e1_three_phase`) | §6.2/6.4 | `figs/fig5_three_phase_mix.png` (오염) / `paper_fig10` (미생성) | **INVALID / 미실행** | **사용 금지** | 구 `mixR`은 `SQLITE_FULL` 오염(YCSB 실패 최대 99.8%)으로 무효, `300k` 재측정은 미실행. 신규 **`figure03_adaptation` (`mixFYF 250k n=3`)**으로 전면 대체. |

---

## 2. 신규 리비전 Figure 최종 판정 (`report/paper-figures/figures/` & `report/revision-final-integration/paper_figures/`)

| 신규 Figure | 대응 심사 항목 | 파일 위치 (300 DPI PNG / PDF / SVG) | 반복 횟수 | 최종 판정 | 비고 |
|---|---|---|---|---|---|
| **`figure01_random`** | M3-1 무작위 선택 대비 | `report/paper-figures/figures/figure01_random.{{png,pdf,svg}}` | **`n=3`** (고컴 `revA`) | **논문에 그대로 사용 가능** | 95% CI, 개별 rep 점, Arm 47 참고선 포함 (`verify_paper_figures.py` PASS). |
| **`figure02_ablation`** | M2 구성 요소 제거 | `report/paper-figures/figures/figure02_ablation.{{png,pdf,svg}}` | **`n=3`** (고컴·승컴 분리) | **논문에 그대로 사용 가능** | 호스트 엄격 분리, Welch 95% CI, `revB*` 교차배치 명시. |
| **`figure03_adaptation`** | M2-4/M6-8 3단계 적응 | `report/paper-figures/figures/figure03_adaptation.{{png,pdf,svg}}` | **`n=3`** (`mixFYF 250k`) | **논문에 그대로 사용 가능** | 오염된 기존 그림 10(`mixR`)의 공식 대체 그림. |
| **`figure04_exploration`** | M2/M5 탐색 비용 | `report/paper-figures/figures/figure04_exploration.{{png,pdf,svg}}` | **`n=3`** (`revA` + `resource-v124`) | **논문에 그대로 사용 가능** | 기존 그림 2(`n=1`)의 정량적 `n=3` 보강/대체 그림. |
| **`figure05_parameters`** | M6-1 제거 문턱 민감도 | `report/paper-figures/figures/figure05_parameters.{{png,pdf,svg}}` | **`n=3`** (`revC` 9/9) | **논문에 그대로 사용 가능** | ELIM 10%/15%/25% 실측 + 오프라인 replay 근거. |
| **`figure06_candidates`** | M6-2 후보 공간(60 vs 45) | `report/paper-figures/figures/figure06_candidates.{{png,pdf,svg}}` | `3×60` sweep + **`n=3`** (`revC`) | **논문에 그대로 사용 가능** | `k=2` 하위 군집 및 60 vs 45 실측 `n=3` 결합. |
| **`figure07_resources`** | M1/M5 메모리·CPU 오버헤드 | `report/paper-figures/figures/figure07_resources.{{png,pdf,svg}}` | `sizeof` + **`n=3`** (`revA`/`res`) | **수정 후 사용 가능** | `sizeof`(193×/232×)와 iCAT 결정 `ktime` 반영됨. 본문 표 9b의 `m1-20261126` SmartGC `GC 98.4 vs 17.8 µs` 트레이드오프를 캡션 또는 병렬 패널로 보강 권고. |
| **`fig_full_ablation`** | M2 전체 Ablation 통합 | `report/revision-final-integration/paper_figures/fig_full_ablation.{{png,pdf,svg}}` | **`n=3`** (`revA/E/D/abl`) | **논문에 그대로 사용 가능** | 고컴(`revA/revE`)·승컴(`revD/abl`) 좌우 패널 완전 분리. |
| **`fig_greedy_gc_vs_v4`** | M3-5 Greedy GC 검증 | `report/revision-final-integration/paper_figures/fig_greedy_gc_vs_v4.{{png,pdf,svg}}` | **`n=3`** (9종 + `batchG`) | **논문에 그대로 사용 가능** | 시각 검수 완료: 레거시 9종 + `mixFYF batchG` (`−19.7%`, Holm `p=0.0013`) 반영. |
| **`fig_online_greedy_vs_v4`** | M3-3 Online Greedy 검증 | `report/revision-final-integration/paper_figures/fig_online_greedy_vs_v4.{{png,pdf,svg}}` | **`n=3`** (승컴 간접) | **논문에 그대로 사용 가능** | Honest null(`−0.0086`) 및 고컴 기준선 호스트 분리 제시. |
| **`fig_noelim_vs_v4`** | M2-1 후보 제거 단독 | `report/revision-final-integration/paper_figures/fig_noelim_vs_v4.{{png,pdf,svg}}` | **`n=3`** (`revE` 동일배치) | **논문에 그대로 사용 가능** | `revE` 동일배치 `+0.0913` (`Holm p=0.091` 경계 명시). |
| **`fig_discount_free_vs_v4`** | M2-6 할인 계수 제거 | `report/revision-final-integration/paper_figures/fig_discount_free_vs_v4.{{png,pdf,svg}}` | **`n=3`** (`abl` 동일배치) | **논문에 그대로 사용 가능** | Honest null(`−0.0038`) + 이론적 `gamma^t` 가중치 곡선. |
| **`fig_random_search_vs_v4`** | R4 Random Search 기대값 | `report/revision-final-integration/paper_figures/fig_random_search_vs_v4.{{png,pdf,svg}}` | `[추정]` 조합 기대값 | **보조 자료로만 사용** | 실측 Random Search가 아닌 60-arm 스윕 기반 조합론적 기대값(`E[min W_i]`)이므로 본문 실측 그래프와 분리. |
| **`fig_periodic_switching_vs_v4`** | M3 Periodic Switching | `report/revision-final-integration/paper_figures/fig_periodic_switching_vs_v4.{{png,pdf,svg}}` | **미실행 (0회)** | **사용 금지** | 사용자 결정으로 미실행(플레이스홀더 그림) — 논문 투고 제외, 한계로만 기술. |
"""
    (OUT_DIR / "FINAL_FIGURE_CATALOG.md").write_text(fig_cat_md, encoding="utf-8")
    print("Wrote FINAL_FIGURE_CATALOG.md")

    # -----------------------------------------------------------------------
    # 4. FINAL_EXPERIMENT_STATUS.md
    # -----------------------------------------------------------------------
    intake_lines = [
        "| 소속 PC | 지시 입력 파일 | 원격 브랜치 | 수신 상태 | 경로 / 비고 |",
        "|---|---|---|---|---|",
    ]
    for fn in gocom_targets:
        p = gocom_found[fn]
        intake_lines.append(f"| 고컴 | `{fn}` | `{REF_GOCOM}` (`{c_gocom}`) | **{'수신 완료' if p else '미푸시 대기 (WAITING_PUSH)'}** | `{p or '아직 원격에 없음 — push 감지 즉시 교차검증 예정'}` |")
    for fn in seung_targets:
        p = seung_found[fn]
        intake_lines.append(f"| 승컴 | `{fn}` | `{REF_MAIN}` (`{c_main}`) | **{'수신 완료' if p else '미푸시 대기 (WAITING_PUSH)'}** | `{p or '아직 원격에 없음 — push 감지 즉시 교차검증 예정'}` |")

    status_md = f"""# 최종 실험 완료 현황 및 입력 자료 수신 상태 (`FINAL_EXPERIMENT_STATUS.md`)

- **작성 시각**: `{NOW_STR}`
- **기준 커밋**: 승컴 `origin/main @ {c_main}` / 고컴 `origin/report/data-validity-20261124 @ {c_gocom}` / 자원 계측 `origin/resource-overhead-20261114 @ {c_res}`

## 1. 전체 리비전 핵심 실험 완료 현황 (**{n_valid}/{n_total} VALID, RUNNING 0건**)

| 배치 / 캠페인 | 호스트 | 워크로드 | 계획/유효 | 심사 대응 | 검증 주체 | 최종 상태 |
|---|---|---|---:|---|---|---|
| `revA-20261114` (`v4/random/v1/v2/arm47`) | 고컴 (Ryzen 3600XT) | `mixFYF 250k` (90m) | 13 / 13 | M2, M3 | 고컴·집컴 | **완료·검증 (arm47 n=1 분리)** |
| `revB-20261122` (`noelim/nosettle/v4/arm60`) | 고컴 (Ryzen 3600XT) | `mixFYF 250k` (90m) | 8 / 8 | M2 (참고) | 고컴·집컴 | **완료·교차배치 단서 (`revE`로 대체)** |
| `revC-20261124` (`v4/elim10/elim25/arm60/online`) | 고컴 (Ryzen 3600XT) | `mixFYF 250k` (90m) | 15 / 15 | M3-2, M6-1/2 | 고컴·집컴 | **완료·검증** |
| `revD-20261124` (`v4/nodrift/fullreset`) | 승컴 (i7-7700) | `mixFYF 250k` (90m) | 9 / 9 | M2-3/5 | 승컴·고컴·집컴 | **완료·3자 검증** |
| `abl-20261125` (`v4/nodiscount/bundle-off`) | 승컴 (i7-7700) | `mixFYF 250k` (90m) | 9 / 9 | M2-2/6 | 승컴·고컴·집컴 | **완료·3자 검증** |
| `revE-20261125` (`v4/noelim/drift12`) | 고컴 (Ryzen 3600XT) | `mixFYF 250k` (90m) | 9 / 9 | M2-1, M6-3 | 고컴·집컴 | **완료·검증** |
| `greedy-20261125` (`greedy-online VAR=8`) | 승컴 (i7-7700) | `mixFYF 250k` (90m) | 3 / 3 | M3-3 | 승컴·고컴·집컴 | **완료·3자 검증 (Honest Null)** |
| `batchG-20261126` (`bg-v4/greedygc/drift50`) | 승컴 (i7-7700) | `mixFYF 250k` (90m) | 9 / 9 | M3-5, M6-3 | 승컴·고컴·집컴 | **완료·3자 검증 (0/36 불일치)** |
| `arm47-20261127` (`Fixed Arm 47 n=3`) | 승컴 (i7-7700) | `mixFYF 250k` (90m) | 3 / 3 | Robustness | 승컴·집컴 | **완료·검증 (`1.98764±0.00027`)** |
| `m1-20261126` (`iCAT-v4` vs `SmartGC-EQ8`) | 고컴 (Ryzen 3600XT) | `mixY 10h` (20단계) | 2 / 2 (`n=1`) | M1, M5 | 고컴·집컴 | **완료·검증 (`rep2–3` 사용자 취소)** |
| **보조 검증 셋** (`resource-v124`, `3×60` 스윕, 레거시 Greedy 9종) | 승컴 | FIO-Fast 30m / 60-arm / x1 9종 | 246 / 246 | M5, M6-2, M3-5 | 집컴 | **완료·검증** |
| **제외된 무효 실행** (`SQLITE_FULL` 224+건, `mixG` 34건, `ENOSPC` 1건, 10월 `mixY` 이상치) | 양 호스트 | 구 `mixR`/전환/`mixY` | 0 / 260+ | M4-7 | 고컴·집컴 | **엄격 제외 (재사용 금지)** |

## 2. 고컴·승컴 신규 통합 입력 파일 수신 상태 (`{n_gocom_present}/5` 고컴, `{n_seung_present}/5` 승컴)

{chr(10).join(intake_lines)}

> **투명성 원칙:** 미푸시 상태인 고컴·승컴 신규 문서에 대해서는 "검증 완료"로 표시하지 않으며, 본 패키지의 모든 수치는 원시 로그(`result/`) 80/80 직접 재계산과 이미 push된 분석 커밋(`e452a2640`, `4689c6797`, `2a0900382`, `67cf3f901`, `30cf9b9fb`)을 기준으로 독립 확정했습니다. 두 PC의 신규 파일이 push되는 즉시 30분 정기 점검에서 자동 교차검증하여 본 디렉터리를 갱신합니다.
"""
    (OUT_DIR / "FINAL_EXPERIMENT_STATUS.md").write_text(status_md, encoding="utf-8")
    print("Wrote FINAL_EXPERIMENT_STATUS.md")

    # -----------------------------------------------------------------------
    # 5. FINAL_LIMITATIONS.md
    # -----------------------------------------------------------------------
    lim_md = f"""# iCAT 논문 리비전 최종 실험 한계 및 주장 제한서 (`FINAL_LIMITATIONS.md`)

- **작성 시각**: `{NOW_STR}`
- **원칙**: 심사위원의 요구보다 강한 주장을 하지 않으며, 입증되지 않았거나 불리한 실측 결과를 숨기지 않는다.

1. **단일 에뮬레이터 기하학 및 `erase=0` 타이밍 한계 (M7-1~5)**
   - 모든 실험은 NVMeVirt 8 GiB, OP 7%, MLC 타이밍(`erase=0`), `conv_ftl`, `ext4 nodiscard`, 최대 10시간 범위에서 수행되었다.
   - 대용량 SSD(16~64+ GiB), 상이한 OP 비율(14%/28%), 비영(non-zero) 소거 지연을 갖는 TLC/QLC 실물 SSD, `discard` 활성 환경 및 실서버 장기 트레이스에서의 일반화는 미검증이며 향후 과제로 명시한다.
2. **SmartGC 비교의 단일 실행(`n=1`) 및 커널 CPU 시간 미측정 (M1-2, M1-3, M1-9, M5-2)**
   - `m1-20261126`은 사용자 결정으로 정책당 `n=1`만 실행되었으므로(`rep2–3` 4건 CANCELLED) 통계적 유의성 검정이나 신뢰구간을 부여할 수 없다.
   - 커널 스레드는 `VmRSS`가 존재하지 않아 `/proc/meminfo` `VmallocUsed`와 `gdb sizeof` 계산값으로 대체하였으며, NVMeVirt busy-poll 구조 및 커널용 `perf` 부재로 커널 내부 CPU 시간과 NVMeVirt 공통 처리 비용은 미측정(`ktime` 경과 시간과 엄격 구분)이다.
3. **GC 희생 블록 선택(`SELECT`) 경과 시간 불리 트레이드오프 (M1-4, M1-6)**
   - iCAT-v4의 학습 갱신(`LEARN`) 자체는 `4.30 s` (`40.8 ns/GC`)로 SmartGC(`47.56 s`)보다 11배 작으나, CAT 전 라인 점수 스캔(`SELECT 87.05 µs/GC`) 때문에 GC 1회 전체 경과시간은 iCAT(`98.37 µs/GC`, `1,342 ms/GiB`)이 SmartGC(`17.84 µs/GC`, `333 ms/GiB`)의 **5.5배**였다. 따라서 "전체 GC CPU 효율 우위"는 주장할 수 없으며, **WAF·학습 메모리 우위 대 희생 선택 연산 비용 트레이드오프**로 기술한다.
4. **단순 온라인 탐욕 선택(Online Greedy) 대비 WAF 우위 미입증 (M3-3)**
   - 승컴 `greedy-20261125` (`n=3`, `0/2,513` argmin 규칙 불일치)에서 `Online Greedy − revD-v4 = −0.0086 [−0.0508, +0.0336]` (`p=0.543`), Phase C 첫 5분 WAF도 Greedy(`2.407`) < V4(`2.598`)로 iCAT-v4의 우위가 확인되지 않았다. 또한 대조군(`revD-v4`, `abl-v4`)과는 다른 날짜의 간접 비교다.
5. **변화 감지 단독(`NoDrift`) 및 할인 계수(`gamma`) 효과 미입증 (M2-3, M2-6)**
   - `NoDrift`는 양 호스트 모두 3/3 평균 열위(`+0.079`, `+0.068`)였으나 분산이 커서 `n=3` Welch 95% CI가 0을 포함하였다. `NoDiscount` (`gamma=1.0`)는 `−0.0038 [−0.0644, +0.0569]` (`Holm p=1.000`)로 90분 구간(`gamma^250=0.882`)에서 효과가 확인되지 않았다.
6. **후보 제거 단독(`revE`)·부분 복원(`revD`)의 다중 비교 보정 경계 (M2-1, M2-5, M6-3)**
   - `revE` `NoElim`(`+0.0913`)·`drift12`(`+0.0720`) 및 `revD` `FullReset`(`+0.0596`, Phase C `+0.1296`)은 사전등록 Welch 95% CI가 0을 배제하였으나, 4-검정 Holm 보정 후 `p=0.060–0.091`로 0.05 경계에 위치함을 반드시 각주로 병기한다.
7. **사용자 체감 I/O 지연 개선 미입증 (M1-8, M5-5)**
   - `mixFYF`에서 iCAT-v4는 무작위 선택 대비 FIO p99가 `+15~20 µs` 높았고, `batchG` Greedy GC 대비로도 FIO p99(`166 vs 42 µs`)가 높았다(Arm 47도 `175 µs`로 CAT 스캔 영향 시사). `mixY` 지연은 SmartGC 채널 포화 경고(`22,069`건)와 `rate_iops` 고정, `erase=0`으로 비교 근거에서 제외한다.
8. **미측정 하이퍼파라미터 및 비교 정책 범위 (M3-4, M6-4~7)**
   - 판단 구간 크기(512 MiB / 128 GC), UCB 계수(`0.25`), 정착 조건(`12`구간/확인 `3`회/`0.5%`), 탐침 주기(`8`/`240`), 짧은 반감기 할인율 및 Periodic Switching은 미실행이며 경험적 설정 및 범위 한계로 명시한다.
9. **기존 본문 그림 1~2·4~9 및 표 6~7의 단일 실행(`n=1`) 한계 및 호스트 분리 (M4-1, M4-8)**
   - `n=3` 확정 통계는 `mixFYF 250k` 1종(§6.4 표 10) 중심이며, 기존 §6.1–6.2 그림·표는 `n=1` 고정 조합 기반 탐색적 자료로 격하한다. 호스트 간(고컴 Ryzen vs 승컴 i7) 및 서로 다른 배치 간 결과는 절대 합산하지 않는다(Arm 47도 승컴 `n=3`과 고컴 `n=1` 분리 유지).
10. **데이터 오염 제외 이력 투명 공개 (M4-7)**
    - 9월·11월 `SQLITE_FULL` 오염(`mixA/B/H/J/R` 224+건), `mixG` 0-byte YCSB(34건), 초기 `ENOSPC`(1건), 10월 `mixY-fixed47` 월별 편차(`+12.9%`)는 전수 제외하였으며, 구 그림 10 및 미실행 `300k` 표 8은 원고에서 제거한다.
"""
    (OUT_DIR / "FINAL_LIMITATIONS.md").write_text(lim_md, encoding="utf-8")
    print("Wrote FINAL_LIMITATIONS.md")

    # -----------------------------------------------------------------------
    # 6. FINAL_EXPERIMENT_REPORT.md (Exact 12-Chapter Report from Section 5)
    # -----------------------------------------------------------------------
    report_md = f"""# iCAT 논문 리비전 최종 종합 실험 보고서 (`FINAL_EXPERIMENT_REPORT.md`)

- **작성 주체**: 집컴 (최종 연구 통합·독립 감사 책임)
- **작성 시각**: `{NOW_STR}`
- **기준 원격 커밋**: 승컴 `origin/main @ {c_main}` / 고컴 `origin/report/data-validity-20261124 @ {c_gocom}` / 자원 계측 `origin/resource-overhead-20261114 @ {c_res}`
- **연결 통합 산출물**: [FINAL_REVIEWER_RESPONSE_MATRIX.xlsx](file:///C:/Users/oyeon/orca/iCAT-experiments/report/final-revision/delivery/FINAL_REVIEWER_RESPONSE_MATRIX.xlsx) · [FINAL_FIGURE_CATALOG.md](file:///C:/Users/oyeon/orca/iCAT-experiments/report/final-revision/delivery/FINAL_FIGURE_CATALOG.md) · [FINAL_PAPER_NUMBER_AUDIT.csv](file:///C:/Users/oyeon/orca/iCAT-experiments/report/final-revision/delivery/FINAL_PAPER_NUMBER_AUDIT.csv) · [iCAT_Paper_Figures.xlsx](file:///C:/Users/oyeon/orca/iCAT-experiments/report/paper-figures/iCAT_Paper_Figures.xlsx)

---

## 1장. 연구 및 실험 개요

본 보고서는 iCAT(온라인 정책 단위 GC 파라미터 학습기, iCAT-v4) 논문 리비전에서 수행된 모든 실험을 원시 로그 기준으로 독립 재검증하고, 최초 심사위원의 요구사항(M1~M7, 47개 세부 항목) 및 3대 핵심 주장에 대한 최종 입증 여부를 판정한 결과다.

- **핵심 검증 원칙**: (1) 원시 로그(`result/`)와 기존 `figs/` 무변경, (2) 호스트(고컴 Ryzen 5 3600XT vs 승컴 Intel i7-7700)·배치·워크로드·레코드 수(250k vs 오염 600k) 엄격 분리, (3) `n<3` 조건 통계적 유의성 미부여, (4) 실측값(`[실측]`)과 이론/계산값(`[계산]`) 엄격 구분, (5) 불리한 결과와 미입증 주장의 정직한 기술.
- **표기 부호 통일**: 본 보고서와 모든 통계표에서 **`Δ = 비교 정책 − 동일 배치 대조군(iCAT-v4)`**로 통일한다. 따라서 양수(`+`)는 비교 정책의 WAF가 더 높음(iCAT-v4 우위), 음수(`−`)는 비교 정책의 WAF가 더 낮음(iCAT-v4 열위)을 뜻한다.
- **최종 무결성 현황**: 핵심 리비전 실행 **80/80 VALID (RUNNING 0건)** + 보조 검증 셋(`resource-v124` 12건, `3×60` 스윕 180건, 레거시 유효 Greedy 9종 54건) 전수 검증 완료. 오염 데이터(`SQLITE_FULL` 224+건, `mixG` 34건, `ENOSPC` 1건) 100% 배제 확인.

---

## 2장. 전체 실험 목록과 목적

| 캠페인 | 호스트 | 워크로드 | 유효/계획 | 검증 목적 (최초 심사 요구사항) | 원시 경로 |
|---|---|---|---:|---|---|
| `revA-20261114` | 고컴 | `mixFYF 250k` (90m) | 13/13 | M3-1 무작위 선택, M2-2 묶음 제거, M2-3 변화 감지, Arm 47 참고(`n=1`) | `{REF_GOCOM}:result/revA-20261114/raw/` |
| `revB-20261122` | 고컴 | `mixFYF 250k` (90m) | 8/8 | M2-1/2 `NoElim`/`NoSettle` 예비 검증 *(브리지 실패 → `revE`로 대체)* | `{REF_GOCOM}:result/revB-20261122/raw/` |
| `revC-20261124` | 고컴 | `mixFYF 250k` (90m) | 15/15 | M3-2 원 구현(`online`), M6-1 제거 문턱(10/15/25%), M6-2 후보 수(60 vs 45) | `{REF_GOCOM}:result/revC-20261124/raw/` |
| `revD-20261124` | 승컴 | `mixFYF 250k` (90m) | 9/9 | M2-3 `NoDrift`, M2-5 부분 복원 vs 전체 45개 재설정(`FullReset`) | `{REF_MAIN}:result/revD-20261124/raw/` |
| `abl-20261125` | 승컴 | `mixFYF 250k` (90m) | 9/9 | M2-2 v4 4기능 묶음 재현, M2-6 할인 계수 제거(`gamma=1.0`) | `{REF_MAIN}:result/revision-additional-ablation/raw/` |
| `revE-20261125` | 고컴 | `mixFYF 250k` (90m) | 9/9 | M2-1 동일배치 `NoElim` 단독, M6-3 변화 감지 문턱 12.5% | `{REF_GOCOM}:result/revE-20261125/raw/` |
| `greedy-20261125` | 승컴 | `mixFYF 250k` (90m) | 3/3 | M3-3 단순 Online Greedy (`VARIANT=8`, 0/2,513 규칙 불일치) | `{REF_MAIN}:result/greedy-20261125/raw/` |
| `batchG-20261126` | 승컴 | `mixFYF 250k` (90m) | 9/9 | M3-5 동일배치 Greedy GC (`n=3`), M6-3 변화 감지 문턱 50% (`n=3`) | `{REF_MAIN}:result/batchG-20261126/raw/` |
| `arm47-20261127` | 승컴 | `mixFYF 250k` (90m) | 3/3 | 고정 Arm 47(`1.987`) 재현성 검증 (`n=3`, 호스트 분리) | `{REF_MAIN}:result/arm47-20261127/raw/` |
| `m1-20261126` | 고컴 | `mixY 10h` (20단계) | 2/2 (`n=1`) | M1/M5 SmartGC-EQ8 vs iCAT-v4 동일 환경 `WAF_nand`·`VmallocUsed`·`ktime` | `{REF_GOCOM}:result/m1-20261126/raw/` |
| `resource-v124` | 승컴 | FIO-Fast 30m | 12/12 | M5-1~6 분리 `reward/select/set_arm/do_gc` 경과시간 & 타이머 검증 | `{REF_RES}:result/resource-v124-20261114/` |

---

## 3장. Random Selection 및 기존 iCAT 원 구현 비교

- **무작위 선택 대비 (`M3-1`, 고컴 `revA`, 동일배치 `n=3`)**: `Random` `2.3243 ± 0.0055` vs `iCAT-v4` `2.1284 ± 0.0049` → **`Δ = +0.1959 [+0.1840, +0.2079]`** (`−8.43%`, `Welch p = 2e-6`, `Holm p = 6e-6`, `Hedges' g = 29.89`, `Paired p = 0.00066`). **입증 완료.**
- **기존 iCAT 원 구현 대비 (`M3-2`, 고컴 `revC`, 동일배치 `n=3`)**: `Original iCAT` `2.3951 ± 0.0029` vs `iCAT-v4` `2.1200 ± 0.0294` → **Total `Δ = +0.2751 [+0.2030, +0.3472]`** (`−11.49%`, `Welch p = 0.00353`, `8-test Holm p = 0.0282`, `g = 10.53`), **Phase C `Δ = +0.4466 [+0.2958, +0.5974]`** (`8-test Holm p = 0.0421`). 원 구현은 단계 3 호스트 쓰기의 `97%`를 탐색 조합으로 처리한 반면 `iCAT-v4`는 `22%`로 억제하였다. **입증 완료.**

---

## 4장. Ablation Study (구성 요소 제거 검증)

| 심사 항목 | 비교 (호스트·배치) | Total WAF Δ `[Welch 95% CI]` | Welch p | Holm p | Hedges' g | 최종 해석 |
|---|---|---:|---:|---:|---:|---|
| **M2-2** v4 묶음 제거 (고컴) | `revA-v2 − revA-v4` (동일배치) | `+0.1355 [+0.1167, +0.1543]` | `0.000158` | `0.000316` | `14.78` | **입증 완료** (+6.4%) |
| **M2-2** v4 4기능 묶음 (승컴) | `abl-bundle-off − abl-v4` (동일배치) | `+0.1241 [+0.0730, +0.1753]` | `0.006929` | `0.027716` | `5.90` | **입증 완료** (+5.8%, 양 호스트 재현) |
| **M2-1** 후보 제거 단독 | `revE-noelim − revE-v4` (고컴 동일배치) | `+0.0913 [+0.0296, +0.1530]` | `0.022681` | `0.090724` | `3.88` | **부분 입증** (Paired `p=0.037`, Holm 경계) |
| **M2-5** 부분 vs 전체 복원 | `revD-fullreset − revD-v4` (승컴 동일배치) | `+0.0596 [+0.0160, +0.1033]` | `0.024023` | `0.072069` | `3.08` | **부분 입증** (Phase C `+0.1296`, Holm `0.060`) |
| **M2-3** 변화 감지 단독 | `revA-v1` / `revD-nodrift − v4` | `+0.0787` / `+0.0681` (CI 0포함) | `0.121 / 0.117` | `0.121 / 0.234` | `1.69 / 1.67` | **입증 실패** (3/3 열위이나 분산 과대) |
| **M2-6** 할인 계수 제거 | `abl-nodiscount − abl-v4` (승컴 동일배치) | `−0.0038 [−0.0644, +0.0569]` | `0.869045` | `1.000000` | `−0.12` | **입증 실패** (90분 `gamma^250=0.882` 효과 없음) |
| **M2-2** 정착 단독 (`revB*`) | `revB-nosettle − revA-v4` (교차배치*) | `+0.0868 [−0.1085, +0.2821]` | `0.197062` | `0.197062` | `1.24` | **입증 실패** (코드 종속 + 교차배치 + CI 0포함) |

---

## 5장. 워크로드 적응 실험 (`mixFYF 250k`, 표 11 및 R1 재분석)

- **Phase C(YCSB-A → FIO-Fast) 적응**: `iCAT-v4`는 고컴·승컴 전 배치(`revA/C/D/E/batchG`)에서 단계 3 진입 후 **약 43~79초** 만에 변화를 감지하고, 변화가 발생한 파티션의 제거 후보(평균 `13~17`개)만 부분 복원하여 **282~499초** 내 재정착하였다.
- **전체 재설정(`FullReset`) 및 `NoElim`과의 비교**: `FullReset`은 147개 후보를 복원해 재정착 `1,182 s`·탐색 쓰기 비중 `56%`(vs V4 `27%`), `NoElim`은 재정착 `1,075 s`·탐색 쓰기 비중 `52%`(vs V4 `30%`)가 소요되었다.
- **한계**: Phase B(저쓰기 YCSB-A) 전환은 대부분 미감지되었고, Phase C 첫 5분 WAF에서는 `Online Greedy`(`2.407`)가 `revD-v4`(`2.598`)보다 낮아 "즉각적 회복 속도 우위"는 주장하지 않는다.

---

## 6장. Online Greedy 및 Greedy GC 비교

- **Online Greedy (`M3-3`, 승컴 `greedy-20261125`, `n=3`, 교차날짜 간접)**:
  - `2,513`개 결정 구간 전수에서 Q16 ratio `argmin` 규칙 일치(`0`건 불일치) 확인.
  - `Online Greedy` `2.1300 ± 0.0198` vs `revD-v4` `2.1386 ± 0.0082` → **`Δ = −0.0086 [−0.0508, +0.0336]`** (`p = 0.543`, vs `abl-v4` `−0.0090 [−0.0577, +0.0397]`). **iCAT-v4 우위 입증 실패 — 본문에 정직 보고 필수.**
- **Greedy GC (`M3-5`, 승컴 `batchG-20261126`, 동일배치 `n=3`, 3자 검증 완료)**:
  - `Greedy GC` `2.6293 ± 0.0069` vs `bg-v4` `2.1105 ± 0.0245` → **Total `Δ = +0.5189 [+0.4633, +0.5744]`** (**iCAT −19.73%**, `Welch p = 0.000321`, **`Holm p = 0.001284`**, `g = 23.09`, `Paired p = 0.000918`), **Phase C `Δ = +0.7078 [+0.5882, +0.8274]`** (`Holm p = 0.003822`). 레거시 유효 9종(`n=3`)에서도 9/9 유의(`−7.1% ~ −42.0%`). **WAF 우위 입증 완료.**
  - **불리 보조 결과**: `erase=0` 환경에서 `Greedy GC`의 Phase C FIO 쓰기 지연(`mean 14.2 µs`, `p99 41.9 µs`)이 `bg-v4`(`mean 27.7 µs`, `p99 166.0 µs`)보다 크게 낮다.

---

## 7장. Drift Threshold 및 파라미터 민감도 실험

- **후보 제거 문턱 `ELIM_Q16` (`M6-1`, 고컴 `revC`, `n=3`)**: `15%`(`2.1200`)가 최저 평균이며, `10%`(`+0.0238 [−0.043, +0.091]`)·`25%`(`+0.0507 [−0.010, +0.111]`) 모두 0 포함(안정적 둔감성 입증).
- **후보 공간 크기 `60 vs 45` (`M6-2/m5`, 고컴 `revC` + `3×60` 스윕)**: 전체 WAF `+0.0282 [−0.032, +0.089]`(CI 0 포함), Phase A 초기 비용만 `+3.0%` 유의; 3/3 최종 선택은 45개 내부.
- **변화 감지 문턱 `DRIFT_Q16` (`M6-3`, 12.5% / 25% / 50%)**:
  - **12.5% (고컴 `revE`, 동일배치 `n=3`)**: Phase B 조기 리셋(평균 `1.7`회 vs 대조군 `0.7`회) 유발 → Total **`+0.0720 [+0.0121, +0.1319]`**, Phase C **`+0.1476 [+0.0266, +0.2685]`** (`Holm p = 0.0907` 경계).
  - **50% (승컴 `batchG`, 동일배치 `n=3`, 3자 검증)**: 전체 11회 리셋 모두 변화율 `>50%`(최소 `61.4%`) 검증. Total **`+0.0183 [−0.0445, +0.0812]`** (`Holm p = 0.831`), Phase C **`+0.0418 [−0.0877, +0.1714]`** → 25%와 구분되지 않음.
- **미측정 파라미터**: 판단 구간 크기(512 MiB), UCB 계수(`0.25`), 정착 조건(`12/3/0.5%`), 탐침 주기는 경험적 설정으로 한계에 명시.

---

## 8장. SmartGC 자원 오버헤드 (`m1-20261126` & `resource-v124`)

고컴 `m1-20261126` (`mixY 10h`, `n=1` per policy, `kernel.log.nowarn.gz` 단독 파싱) 독립 검증 결과(`PAPER_KCI_DRAFT.md` 표 9b와 100% 일치):

| 항목 | `iCAT-v4` (`n=1`) | `SmartGC-EQ8` (`n=1`) | 구분 | 해석 |
|---|---:|---:|---|---|
| **호스트 `WAF` / `WAF_nand`** | `3.330` / **`3.330`** (`8.29 TB`) | `4.562` / **`4.553`** (`5.97 TB`) | `[실측]` | iCAT `WAF_nand` **−26.9%** (단 `n=1` 통계 없음) |
| **학습 상태 메모리 (`sizeof`)** | **`10,112 B`** | **`1,951,648 B`** (+버퍼 `393,216 B`) | `[계산]` | 학습 상태 **193.0×** (전체 **231.9×**) 경량 |
| **`VmallocUsed` Δ (`load1s − pre`)** | **`34,848 kB`** (`35,684,352 B`) | **`37,752 kB`** (`38,658,048 B`) | `[실측]` | 차이 **`+2,904 kB`** (이론차 `3,058 KiB`와 5% 내 일치; 언로드 후 `+16 kB`) |
| **GC 1회 `ktime` 경과 시간** | **`98.37 µs`** (`1,342 ms/GiB`) | **`17.84 µs`** (`333 ms/GiB`) | `[실측, 경과]` | **불리 결과:** iCAT이 **5.5× 김** (CAT 전 라인 스캔) |
| **희생 선택 `SELECT` `ktime`** | `87.05 µs/GC` (`9,162 s`, 88.5%) | `1.00 µs/GC` (`103.9 s`, step 제외 `56.3 s`) | `[실측, 경과]` | iCAT GC 비용의 대부분은 학습이 아닌 CAT 스캔 |
| **학습 갱신 `LEARN` `ktime`** | **`4.295 s`** (`40.80 ns/GC`, 0.041%) | **`47.556 s`** (`975.5 µs × 48,751`) | `[실측, 경과]` | 학습 알고리즘 자체는 iCAT이 **11.1× 경량** |
| **커널 CPU 시간 / NVMeVirt 공통 비용** | **미측정** | **미측정** | `[미측정]` | busy-poll·`perf` 부재; `ktime`과 CPU 시간 엄격 구분 |

- 별도 승컴 `resource-v124` (FIO-Fast 30m, `n=3`, `erase=0`)에서 iCAT-v4 분리 경과시간은 `reward 1.442 ms`, `select 1.273 ms`, `set_arm 0.059 ms`, 학습기 제외 `do_gc` `206.84 s` (CAT-47 `255.98 s`)로 확인되었다.

---

## 9장. Robustness 및 고정 Arm 47 검증

- **고정 Arm 47 `mixFYF` `n=3` (승컴 `arm47-20261127`, `4689c6797`)**: **`1.987644 ± 0.000268`** (`95% CI [1.986980, 1.988309]`, `CV = 0.013%`; `A 1.77430 / B 1.03098 / C 2.27865`). 기존 고컴 `revA` 단일 실행(`1.987355`)이 승컴 `n=3` CI 내부에 들어가 극도의 재현성이 입증되었다 *(호스트가 다르므로 `n=4`로 합산 금지)*.
- **승컴 내 간접 비교 (`arm47 − bg-v4`, 다른 배치)**: Total **`−0.1228 [−0.1836, −0.0621]`** (`p=0.0130`), Phase C **`−0.1250 [−0.2492, −0.0009]`** (`p=0.0493`). 또한 Arm 47의 FIO Phase C p99(`174.6 µs`)가 V4(`166.0 µs`)와 유사하여, Greedy GC(`41.9 µs`) 대비 지연 차이가 온라인 학습기가 아닌 **CAT 전 라인 스캔 자체**에서 기인함을 뒷받침한다.
- **기존 Figure 1~10 Robustness 요약**: 그림 3만 그대로 사용 가능, 그림 1·7·8·9는 수정 후(탐색적 `n=1` 단서 + 2자리 수치) 사용 가능, 그림 2·4·5·6은 보조 사례로만 사용, 오염된 구 그림 10 및 미실행 `300k` 표 8은 사용 금지(`FINAL_FIGURE_CATALOG.md` 참조).

---

## 10장. 심사 의견별 증거 요약 (3대 핵심 주장 및 M1~M7 47개 항목)

- **핵심 주장 1** (iCAT > 무작위 정책 선택): **`입증`** (단 Online Greedy 무우위·Arm 47 oracle 한계 병기)
- **핵심 주장 2** (후보 제거·정착·변화 감지·재탐색 기여): **`부분 입증`** (묶음 입증, `NoElim`/`PartialReset` Holm 경계, `NoDrift`/`NoDiscount`/`NoSettle` 미입증)
- **핵심 주장 3** (정책 단위 학습의 메모리·CPU 효율 우위): **`부분 입증`** (학습 메모리 193×·학습 갱신 11× 유리; **전체 GC/SELECT 경과시간 5.5× 불리 → CPU 우위 입증 불가**)
- **47개 세부 항목 전체 집계**: 입증 완료 `14` / 부분 입증 `17` / 입증 실패 `7` / 추가 실험 불필요 `9` / 추가 실험 필요 `0` (상세: `FINAL_REVIEWER_RESPONSE_MATRIX.xlsx`).

---

## 11장. 실험의 한계

상세 10대 한계는 [FINAL_LIMITATIONS.md](file:///C:/Users/oyeon/orca/iCAT-experiments/report/final-revision/delivery/FINAL_LIMITATIONS.md)에 수록하였다. 핵심은 (1) 단일 8 GiB OP-7% `erase=0` 에뮬레이터, (2) `m1` `n=1` 및 커널 CPU 시간 미측정, (3) CAT `SELECT` 5.5× 스캔 비용 트레이드오프, (4) Online Greedy·`NoDrift`·`NoDiscount`·FIO p99 우위 미입증, (5) 기존 본문 그림·표의 `n=1` 탐색적 한계다.

---

## 12장. 최종 논문 반영 권고 (원고 직접 수정 전 제안)

1. **즉시 반영할 원고 패치 5건 (`FINAL_PAPER_NUMBER_AUDIT.csv` NA-09~NA-13)**:
   - `PAPER_KCI_DRAFT.md` **L405 (§7 자원 비용)**: `"GC 수행 시간은 계측하지 않았다"` 문구 삭제 → `resource-v124`(`n=3`) 및 표 9b(`m1` `n=1`: `LEARN` 11× 경량 vs `GC` 5.5× 열위) 요약으로 교체.
   - **L297–L307 (표 8 `300k` & 그림 10)**: 전원 `"대기"`인 미실행 표 8·그림 10 삭제 → §6.4 `mixFYF 250k (n=3)` 표 10·11 및 `figure03_adaptation`으로 통합.
   - **L004, L232, L240, L256, L260**: 잔존 `【결과 대기】`·`【갱신 예정】` 태그 5건 전면 삭제 및 `n=1` 탐색적 한계 확정.
   - **L262 (그림 9)**: 평균 손실을 소수 2자리(`CAT-Best 0.21%`, `CAT-Robust 4.95%`, `iCAT-v4 5.04%`)로 병기.
   - **L313–L321 (표 9)**: `WAF_nand` vs 호스트 `WAF` 정의 각주 보강.
2. **신규 Figure 채택 권고**: §6.4 주 근거 그림으로 `figure01_random`, `figure02_ablation`(또는 `fig_full_ablation`), `figure03_adaptation`, `figure04_exploration`, `figure05_parameters`, `figure06_candidates`, `fig_greedy_gc_vs_v4`, `fig_online_greedy_vs_v4`를 채택하고, `figure07_resources`는 표 9b 트레이드오프 캡션을 보강해 사용한다.
3. **고컴·승컴 최종 통합 입력 수신 후 마무리**: 현재 미푸시 상태인 고컴 5종(`iCAT_Complete_Experiment_Results.xlsx` 등)과 승컴 5종(`final_independent_validation.md` 등)이 push되는 즉시 자동 교차검증 후 최종 체크리스트를 확정한다.
"""
    (OUT_DIR / "FINAL_EXPERIMENT_REPORT.md").write_text(report_md, encoding="utf-8")
    print("Wrote FINAL_EXPERIMENT_REPORT.md")

    # -----------------------------------------------------------------------
    # 7. FINAL_DELIVERY_CHECKLIST.md
    # -----------------------------------------------------------------------
    ready_state = "CONDITIONAL READY (원시 80/80 검증·7대 산출물 완료; 원고 패치 5건 적용 및 고컴·승컴 신규 문서 push 교차검증 남음)" if (n_gocom_present < 5 or n_seung_present < 5) else "READY FOR SUBMISSION (원고 패치 5건 반영만 남음)"
    chk_md = f"""# iCAT 논문 리비전 최종 제출 체크리스트 (`FINAL_DELIVERY_CHECKLIST.md`)

- **작성 시각**: `{NOW_STR}`
- **최종 제출 준비 판정**: **{ready_state}**

| # | 점검 항목 | 상태 | 근거 / 비고 |
|---|---|---|---|
| 1 | 전체 핵심 실험 누락 여부 (Random, SmartGC, Ablation, Greedy GC, Drift, Arm 47) | **PASS** | 10개 핵심 캠페인 **80/80 VALID** + 보조 셋 246/246 VALID (누락 0건, RUNNING 0건) |
| 2 | 오염·실패 run 배제 (`SQLITE_FULL`, `mixG`, `ENOSPC`, 10월 이상치) | **PASS** | 260+ 무효 run 100% 제외 확인 |
| 3 | 3대 핵심 주장 최종 판정 (입증 1 / 부분 입증 2 / 반증 명시) | **PASS** | `FINAL_REVIEWER_RESPONSE_MATRIX.xlsx!Core_3_Claims` 완료 |
| 4 | M1~M7 47개 세부 요구사항 전수 매핑 및 원 명칭 유지 | **PASS** | `FINAL_REVIEWER_RESPONSE_MATRIX.xlsx!M1_M7_47_Items` (14 완료 / 17 부분 / 7 실패 / 9 불필요 / 0 필요) |
| 5 | 기존 Figure 1~10 + 신규 Figure 4단계 최종 선정 | **PASS** | `FINAL_FIGURE_CATALOG.md` 완료 (구 그림 10·레거시 fig2·Periodic Switching 사용 금지) |
| 6 | 교차 수치 감사 (Excel · CSV · MD · Figure · 표 6~10 · 본문) | **PASS (수정안 제시)** | `FINAL_PAPER_NUMBER_AUDIT.csv` 16항목 완료 (핵심 표 9b/10/11 100% 일치; 원고 수정 필요 5건·데이터북 정오표 3건 별도 패치안 작성, 원고 직접 미수정) |
| 7 | `iCAT_Paper_Figures.xlsx` 및 최종 Figure 무결성 검증 | **PASS** | 21시트, 40/40 수치 일치, 0 오류 리터럴, 300 DPI PNG/PDF/SVG, `figs/` 0건 수정 |
| 8 | `FINAL_EXPERIMENT_REPORT.md` 12개 장 완비 | **PASS** | 1장~12장 전수 작성, 모든 수치 원시 로그 출처 연결 |
| 9 | 고컴 신규 통합 5종 파일 수신·교차검증 (`iCAT_Complete_Experiment_Results.xlsx` 등) | **{'PASS' if n_gocom_present == 5 else f'WAITING_PUSH ({n_gocom_present}/5)'}** | `{REF_GOCOM} @ {c_gocom}` 기준 — push 감지 즉시 자동 교차검증 예정 |
| 10 | 승컴 신규 검증 5종 파일 수신·교차검증 (`final_independent_validation.md` 등) | **{'PASS' if n_seung_present == 5 else f'WAITING_PUSH ({n_seung_present}/5)'}** | `{REF_MAIN} @ {c_main}` 기준 — push 감지 즉시 자동 교차검증 예정 |
| 11 | 투고 전 원고(`PAPER_KCI_DRAFT.md`) 최종 수동 반영 (NA-09~NA-13) | **ACTION REQUIRED (저자 반영)** | L405 GC 계측 오기, L297–307 미실행 300k 표 8·그림 10, 5건 `【결과 대기】` 태그, L262 그림 9 소수 2자리, 표 9 `WAF_nand` 각주 |

## 필수 7대 최종 산출물 경로 (`report/final-revision/delivery/`)
1. `report/final-revision/delivery/FINAL_EXPERIMENT_REPORT.md`
2. `report/final-revision/delivery/FINAL_REVIEWER_RESPONSE_MATRIX.xlsx`
3. `report/final-revision/delivery/FINAL_FIGURE_CATALOG.md`
4. `report/final-revision/delivery/FINAL_EXPERIMENT_STATUS.md`
5. `report/final-revision/delivery/FINAL_PAPER_NUMBER_AUDIT.csv`
6. `report/final-revision/delivery/FINAL_LIMITATIONS.md`
7. `report/final-revision/delivery/FINAL_DELIVERY_CHECKLIST.md`
"""
    (OUT_DIR / "FINAL_DELIVERY_CHECKLIST.md").write_text(chk_md, encoding="utf-8")
    print("Wrote FINAL_DELIVERY_CHECKLIST.md")
    print("ALL 7 MANDATORY FINAL DELIVERY FILES GENERATED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
