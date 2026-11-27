#!/usr/bin/env python3
"""Build report/final-revision/iCAT_Revision_Final.xlsx (7 sheets, native Excel charts).

Read-only with respect to experiment data: every input is read with `git show <ref>:<path>`.
No experiment is run. All statistics are recomputed here from per-run WAF values and
compared with the values reported by GoCom / SeungCom (sheet Verification).

Inputs
  GoCom    c4bd5c463 (origin/report/data-validity-20261124)
           report/final-revision/gocom_revision_final/*.csv
  SeungCom e78fad59b (origin/main)
           result/final-validation-20261127/final_raw_data_validation.csv
           result/final-validation-20261127/final_statistical_validation.csv
"""
import csv, io, math, os, subprocess, sys
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference, Series
from openpyxl.chart.data_source import NumDataSource, NumRef
from openpyxl.chart.error_bar import ErrorBars
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.layout import Layout, ManualLayout
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.chart.text import RichText
from openpyxl.drawing.line import LineProperties
from openpyxl.drawing.text import CharacterProperties, Paragraph, ParagraphProperties, Font as DFont
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "iCAT_Revision_Final.xlsx")
GOCOM_REF, SEUNG_REF = "c4bd5c463", "e78fad59b"
GOCOM_DIR = "report/final-revision/gocom_revision_final/"
SEUNG_DIR = "result/final-validation-20261127/"
H1 = "Host 1 (GoCom, Ryzen 5 3600XT)"
H2 = "Host 2 (SeungCom, Core i7-7700)"
SKY, GREY, BLACK, GRID = "56B4E9", "D9D9D9", "000000", "D9D9D9"


def git_csv(ref, path):
    txt = subprocess.run(["git", "-C", REPO, "show", f"{ref}:{path}"], check=True,
                         capture_output=True).stdout.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(txt)))


# ---------- statistics (standard library only) ----------
def _betacf(a, b, x):
    qab, qap, qam = a + b, a + 1, a - 1
    c, d = 1.0, 1 - qab * x / qap
    d = 1 / (d if abs(d) > 1e-300 else 1e-300)
    h = d
    for m in range(1, 500):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d; d = 1 / (d if abs(d) > 1e-300 else 1e-300)
        c = 1 + aa / c; c = c if abs(c) > 1e-300 else 1e-300
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d; d = 1 / (d if abs(d) > 1e-300 else 1e-300)
        c = 1 + aa / c; c = c if abs(c) > 1e-300 else 1e-300
        de = d * c
        h *= de
        if abs(de - 1) < 1e-15:
            break
    return h


def _betai(a, b, x):
    if x <= 0: return 0.0
    if x >= 1: return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x))
    if x < (a + 1) / (a + b + 2):
        return bt * _betacf(a, b, x) / a
    return 1 - bt * _betacf(b, a, 1 - x) / b


def t_sf2(t, df):
    """two-sided p-value"""
    return _betai(df / 2, 0.5, df / (df + t * t))


def t_crit(df, alpha=0.05):
    lo, hi = 0.0, 1000.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if t_sf2(mid, df) > alpha: lo = mid
        else: hi = mid
    return (lo + hi) / 2


def desc(v):
    n = len(v); m = sum(v) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / (n - 1))
    hw = t_crit(n - 1) * sd / math.sqrt(n)
    return dict(n=n, mean=m, sd=sd, hw=hw, lo=m - hw, hi=m + hw, v=list(v))


def welch(treat, ctrl):
    a, b = desc(treat), desc(ctrl)
    va, vb = a["sd"] ** 2 / a["n"], b["sd"] ** 2 / b["n"]
    se = math.sqrt(va + vb)
    df = (va + vb) ** 2 / (va ** 2 / (a["n"] - 1) + vb ** 2 / (b["n"] - 1))
    d = a["mean"] - b["mean"]
    hw = t_crit(df) * se
    return dict(d=d, lo=d - hw, hi=d + hw, df=df, p=t_sf2(d / se, df))


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    out, run, m = [0] * len(ps), 0.0, len(ps)
    for k, i in enumerate(order):
        run = max(run, min(1.0, (m - k) * ps[i]))
        out[i] = run
    return out


# ---------- load per-run data ----------
RUN = {}   # group -> list of run dicts (rep order)
for r in git_csv(GOCOM_REF, GOCOM_DIR + "raw_data_gocom.csv"):
    if not r.get("group") or not r.get("rep"): continue
    RUN.setdefault(r["group"], []).append(dict(
        host=H1, batch=r["batch"], group=r["group"], rep=int(r["rep"]),
        host_pages=int(r["host_pages"]), gc_pages=int(r["gc_pages"]),
        waf=float(r["WAF total"]), A=float(r["WAF phase A"]), B=float(r["WAF phase B"]), C=float(r["WAF phase C"]),
        valid=r["valid (recheck)"], sha=r["module sha256"], seeds=r["FIO seeds"], iseed=r["icat_seed"],
        raw=r["raw dir"], src=f"{GOCOM_REF}:{GOCOM_DIR}raw_data_gocom.csv"))
for r in git_csv(SEUNG_REF, SEUNG_DIR + "final_raw_data_validation.csv"):
    if r["host"] != "승컴" or r["role"] != "main" or r["workload"] != "mixFYF" or r["valid"] != "True": continue
    RUN.setdefault(r["policy"], []).append(dict(
        host=H2, batch=r["batch"], group=r["policy"], rep=int(r["rep"]),
        host_pages=int(r["host_pages"]), gc_pages=int(r["gc_pages"]),
        waf=float(r["total_waf"]), A=float(r["A_waf"]), B=float(r["B_waf"]), C=float(r["C_waf"]),
        valid=r["valid"], sha=r["module_sha256"], seeds=r["fio_seeds_first_phase"], iseed=r["icat_seed"],
        raw=f'{r["raw_path"]} (raw-log commit {r["raw_log_commit"]})',
        src=f"{SEUNG_REF}:{SEUNG_DIR}final_raw_data_validation.csv"))
for g in RUN.values():
    g.sort(key=lambda x: x["rep"])

OFFB = "abl-off-elim-settle-drift-probe"
FAMILIES = {  # same-batch control -> treatments; Holm family = (total WAF, phase-C WAF) x treatments
    "revA-v4": ["revA-v1", "revA-v2", "revA-random"],
    "revC-v4": ["revC-elim10", "revC-elim25", "revC-arm60", "revC-online"],
    "revE-v4": ["revE-noelim", "revE-drift12"],
    "revD-v4": ["revD-nodrift", "revD-fullreset"],
    "abl-v4": ["abl-nodiscount", OFFB],
    "bg-v4": ["greedygc", "drift50"],
}
USED = ["revA-random", "revA-v4", "greedygc", "bg-v4", "abl-nodiscount", "abl-v4", "revA-v2", OFFB,
        "revE-noelim", "revE-v4", "revA-v1", "revD-nodrift", "revD-fullreset", "revD-v4",
        "revC-elim10", "revC-v4", "revC-elim25"]
checks = []   # (item, recomputed, reported, source, tolerance, match)


def chk(item, got, ref, src, tol):
    ok = abs(got - ref) <= tol
    checks.append((item, got, ref, src, tol, "MATCH" if ok else "MISMATCH"))


for g in set(USED) | {t for ts in FAMILIES.values() for t in ts}:
    assert g in RUN and len(RUN[g]) == 3, (g, len(RUN.get(g, [])))
    for r in RUN[g]:
        assert r["valid"] == "True", r
        chk(f"{g} rep{r['rep']}: WAF = 1 + gc_pages/host_pages", 1 + r["gc_pages"] / r["host_pages"], r["waf"],
            "per-run WAF column of the same source file", 1e-9)

D = {g: desc([r["waf"] for r in RUN[g]]) for g in RUN if len(RUN[g]) == 3}
CON = {}   # treatment -> contrast dict (+ holm, family size, control)
for ctrl, ts in FAMILIES.items():
    fam = [(t, m) for t in ts for m in ("waf", "C")]
    ws_ = [welch([r[m] for r in RUN[t]], [r[m] for r in RUN[ctrl]]) for t, m in fam]
    hp = holm([w["p"] for w in ws_])
    for (t, m), w, h in zip(fam, ws_, hp):
        if m == "waf":
            CON[t] = dict(w, holm=h, fam=len(fam), ctrl=ctrl,
                          pct=w["d"] / D[ctrl]["mean"] * 100,
                          pct_lo=w["lo"] / D[ctrl]["mean"] * 100, pct_hi=w["hi"] / D[ctrl]["mean"] * 100)

# ---------- verification against reported values ----------
def f(x):
    return float(str(x).replace("−", "-").replace("+", ""))

T4 = 6e-5
gb = {r["Experiment"]: r for r in git_csv(GOCOM_REF, GOCOM_DIR + "baseline_figure1_gocom.csv")}["Random Selection"]
src = f"GoCom {GOCOM_REF}: baseline_figure1_gocom.csv"
for k, g, key in [("Baseline mean WAF", "revA-random", "mean"), ("Baseline SD", "revA-random", "sd"),
                  ("Baseline 95% CI lo", "revA-random", "lo"), ("Baseline 95% CI hi", "revA-random", "hi"),
                  ("iCAT-v4 mean WAF (same batch)", "revA-v4", "mean"), ("iCAT-v4 SD", "revA-v4", "sd"),
                  ("iCAT-v4 95% CI lo", "revA-v4", "lo"), ("iCAT-v4 95% CI hi", "revA-v4", "hi")]:
    chk(f"{g} {k}", D[g][key], f(gb[k]), src, T4)
c = CON["revA-random"]
chk("revA-random − revA-v4 ΔWAF", c["d"], f(gb["ΔWAF (baseline − iCAT)"]), src, T4)
chk("revA-random − revA-v4 Welch CI lo", c["lo"], f(gb["Welch 95% CI lo"]), src, T4)
chk("revA-random − revA-v4 Welch CI hi", c["hi"], f(gb["Welch 95% CI hi"]), src, T4)
chk("revA-random − revA-v4 Welch df", c["df"], f(gb["Welch df"]), src, 6e-3)
assert gb["Holm p"] == "<0.0001" and c["holm"] < 1e-4 and int(gb["Holm family size"]) == c["fam"]
checks.append(("revA-random − revA-v4 Holm p (reported '<0.0001')", c["holm"], "<0.0001", src, "<1e-4", "MATCH"))
chk("Random: WAF reduction by iCAT (%)", c["d"] / D["revA-random"]["mean"] * 100,
    f(gb["Improvement (%) = (baseline − iCAT)/baseline ×100 [계산]"]), src, 6e-3)

src = f"GoCom {GOCOM_REF}: ablation_table_gocom.csv"
ga = {(r["batch"], r["Variant"]): r for r in git_csv(GOCOM_REF, GOCOM_DIR + "ablation_table_gocom.csv") if r.get("batch")}
for key, t in [(("revA-20261114", "NoDrift (revA V1)"), "revA-v1"),
               (("revA-20261114", "NoElim+NoSettle (revA V2)"), "revA-v2"),
               (("revE-20261125", "NoElim"), "revE-noelim")]:
    r, c = ga[key], CON[t]
    for k, v, tol in [("variant mean WAF", D[t]["mean"], T4), ("variant SD", D[t]["sd"], T4),
                      ("variant 95% CI lo", D[t]["lo"], T4), ("variant 95% CI hi", D[t]["hi"], T4),
                      ("control iCAT-v4 mean (same batch)", D[c["ctrl"]]["mean"], T4), ("control SD", D[c["ctrl"]]["sd"], T4),
                      ("ΔWAF", c["d"], T4), ("Welch 95% CI lo", c["lo"], T4), ("Welch 95% CI hi", c["hi"], T4),
                      ("ΔWAF (%) [계산]", c["pct"], 6e-3), ("Holm p", c["holm"], T4)]:
        chk(f"{t}: {k}", v, f(r[k]), src, tol)
    assert int(r["Holm family size"]) == c["fam"]

src = f"GoCom {GOCOM_REF}: param_elimination_threshold.csv"
ge = {r["group"]: r for r in git_csv(GOCOM_REF, GOCOM_DIR + "param_elimination_threshold.csv") if r.get("group")}
LC = {}
for r in git_csv(GOCOM_REF, GOCOM_DIR + "learner_counters_runs.csv"):
    if r.get("rep"): LC.setdefault(r["group"], []).append(r)
SHARE, ACTIVE = {}, {}
for t in ["revC-elim10", "revC-v4", "revC-elim25"]:
    rows = sorted(LC[t], key=lambda r: int(r["rep"])); assert len(rows) == 3
    for r in rows:
        parts = [int(x) for x in r["active_end_phaseA_per_part"].split()]
        chk(f"{t} rep{r['rep']}: eliminated share = 1 − mean(active per partition)/candidates",
            1 - sum(parts) / len(parts) / int(r["candidates"]), float(r["eliminated_share_end_phaseA"]),
            f"GoCom {GOCOM_REF}: learner_counters_runs.csv", 1e-12)
    SHARE[t] = desc([float(r["eliminated_share_end_phaseA"]) * 100 for r in rows])
    ACTIVE[t] = desc([float(r["active_end_phaseA_mean"]) for r in rows])
    r = ge[t]
    for k, key in [("mean WAF", "mean"), ("SD", "sd"), ("95% CI lo", "lo"), ("95% CI hi", "hi")]:
        chk(f"{t}: {k}", D[t][key], f(r[k]), src, T4)
    m, s = r["eliminated share end of phase A [실측, 1 − active/candidates]"].split(" ± ")
    chk(f"{t}: eliminated share mean (fraction)", SHARE[t]["mean"] / 100, f(m), src, 6e-4)
    chk(f"{t}: eliminated share SD (fraction)", SHARE[t]["sd"] / 100, f(s), src, 6e-4)
    m, s = r["active candidates end of phase A (mean of 4 parts)"].split(" ± ")
    chk(f"{t}: active candidates end of phase A (mean)", ACTIVE[t]["mean"], f(m), src, 6e-4)
    if t != "revC-v4":
        c = CON[t]
        chk(f"{t}: Δ vs same-batch 15%", c["d"], f(r["Δ vs same-batch default"]), src, T4)
        chk(f"{t}: Welch CI lo", c["lo"], f(r["Welch CI lo"]), src, T4)
        chk(f"{t}: Welch CI hi", c["hi"], f(r["Welch CI hi"]), src, T4)
        chk(f"{t}: Holm p", c["holm"], f(r["Holm p"]), src, T4)
for t, claim in [("revC-elim10", 80), ("revC-v4", 61), ("revC-elim25", 10)]:
    chk(f"{t}: eliminated share (%) rounds to the GoCom-reported {claim}%", round(SHARE[t]["mean"]), claim,
        "GoCom report §5.1 / task statement (80%, 61%, 10%)", 0)

src = f"SeungCom {SEUNG_REF}: final_statistical_validation.csv"
sv = git_csv(SEUNG_REF, SEUNG_DIR + "final_statistical_validation.csv")
sd_ = {r["policy"]: r for r in sv if r["kind"] == "descriptive" and r["metric"] == "total_waf" and r["host"] == "승컴"}
sc_ = {r["treatment"].split("/")[1]: r for r in sv if r["kind"] == "contrast" and r["metric"] == "total_waf"
       and r["host"] == "승컴" and r["holm_family_size"]}
for g in ["bg-v4", "greedygc", "abl-v4", "abl-nodiscount", OFFB, "revD-v4", "revD-nodrift", "revD-fullreset"]:
    r = sd_[g]
    for k, key in [("mean", "mean"), ("sd", "sd"), ("ci95_lo", "lo"), ("ci95_hi", "hi")]:
        chk(f"{g}: {k}", D[g][key], float(r[k]), src, 1e-6)
    if g in CON:
        r, c = sc_[g], CON[g]
        assert r["control"].split("/")[1] == c["ctrl"] and int(r["holm_family_size"]) == c["fam"]
        for k, key in [("diff", "d"), ("ci95_lo", "lo"), ("ci95_hi", "hi"), ("welch_df", "df"), ("welch_p", "p"),
                       ("holm_p_family", "holm")]:
            chk(f"{g} − {c['ctrl']}: {k}", c[key], float(r[k]), src, 1e-6)

bad = [c for c in checks if c[5] != "MATCH"]
for b in bad: print("MISMATCH", b)
assert not bad, f"{len(bad)} mismatches"

# ---------- workbook helpers ----------
wb = Workbook()
THIN, MED = Side(style="thin", color=BLACK), Side(style="medium", color=BLACK)
BASE = "Arial"


def cell(ws, r, c, v, fmt=None, bold=False, wrap=False, align=None, size=10, italic=False, color=None):
    x = ws.cell(row=r, column=c, value=v)
    x.font = Font(name=BASE, size=size, bold=bold, italic=italic, color=color)
    x.alignment = Alignment(wrap_text=wrap, horizontal=align, vertical="center")
    if fmt: x.number_format = fmt
    return x


def title(ws, text, sub=None):
    cell(ws, 1, 1, text, bold=True, size=13)
    if sub: cell(ws, 2, 1, sub, italic=True, size=9, color="404040")
    ws.sheet_view.showGridLines = False


def table(ws, r0, headers, rows, fmts=None, widths=None, wrap_head=True):
    """three-line table; returns first data row"""
    for j, h in enumerate(headers, 1):
        x = cell(ws, r0, j, h, bold=True, wrap=wrap_head, align="center")
        x.border = Border(top=MED, bottom=THIN)
    for i, row in enumerate(rows, 1):
        for j, v in enumerate(row, 1):
            x = cell(ws, r0 + i, j, v, fmt=(fmts or {}).get(j), wrap=isinstance(v, str) and "\n" in v,
                     align=None if (isinstance(v, str) and len(v) > 14 and j == 1) else "center")
            if i == len(rows): x.border = Border(bottom=MED)
    if widths:
        for j, w in enumerate(widths, 1): ws.column_dimensions[get_column_letter(j)].width = w
    return r0 + 1


def notes(ws, r, lines):
    for i, t in enumerate(lines):
        cell(ws, r + i, 1, t, size=9, color="404040")
    return r + len(lines)


def rich(size=10, bold=False, rot=None):
    cp = CharacterProperties(sz=size * 100, b=bold, solidFill=BLACK, latin=DFont(typeface=BASE))
    from openpyxl.chart.text import RichTextProperties
    bp = RichTextProperties(rot=rot) if rot is not None else RichTextProperties()
    return RichText(bodyPr=bp, p=[Paragraph(pPr=ParagraphProperties(defRPr=cp), endParaRPr=cp)])


def bar_chart(ytitle, xtitle, ymin, ymax, major, w, h, yfmt="0.0", legend=True):
    ch = BarChart(); ch.type = "col"; ch.grouping = "clustered"; ch.style = 2
    ch.width, ch.height = w, h
    ch.gapWidth = 80; ch.roundedCorners = False
    ch.y_axis.title, ch.x_axis.title = ytitle, xtitle
    ch.y_axis.scaling.min, ch.y_axis.scaling.max, ch.y_axis.majorUnit = ymin, ymax, major
    ch.y_axis.number_format = yfmt
    for ax in (ch.x_axis, ch.y_axis):
        ax.delete = False
        ax.spPr = GraphicalProperties(ln=LineProperties(solidFill=BLACK, w=9525))
        ax.txPr = rich(10)
        if ax.title is not None:
            ax.title.overlay = False
            for run in ax.title.tx.rich.p[0].r:
                run.rPr = CharacterProperties(sz=1100, b=False, solidFill=BLACK, latin=DFont(typeface=BASE))
    ch.x_axis.majorTickMark = "none"; ch.y_axis.majorTickMark = "out"
    ch.x_axis.tickLblPos = "low"
    ch.y_axis.majorGridlines.spPr = GraphicalProperties(ln=LineProperties(solidFill=GRID, w=6350))
    ch.plot_area.spPr = GraphicalProperties(solidFill="FFFFFF", ln=LineProperties(noFill=True))
    ch.graphical_properties = GraphicalProperties(solidFill="FFFFFF", ln=LineProperties(noFill=True))
    if legend:
        ch.legend.position = "t"; ch.legend.overlay = False; ch.legend.txPr = rich(10)
    else:
        ch.legend = None
    return ch


def add_series(ch, ws, name_ref, val_ref, cat_ref, err_ref, fill, labels=None, lblpos="inEnd", lblbox=False):
    s = Series(Reference(ws, range_string=val_ref), title_from_data=False)
    from openpyxl.chart.series import SeriesLabel
    from openpyxl.chart.data_source import StrRef
    s.tx = SeriesLabel(strRef=StrRef(f=name_ref))
    s.cat = None
    s.graphicalProperties = GraphicalProperties(solidFill=fill, ln=LineProperties(solidFill=BLACK, w=12700))
    s.invertIfNegative = False
    e = NumDataSource(numRef=NumRef(f=err_ref))
    s.errBars = ErrorBars(errDir="y", errBarType="both", errValType="cust", noEndCap=False, plus=e, minus=e,
                          spPr=GraphicalProperties(ln=LineProperties(solidFill=BLACK, w=12700)))
    if labels:
        s.dLbls = DataLabelList(); s.dLbls.showVal = True
        for k in ("showSerName", "showCatName", "showLegendKey", "showPercent"): setattr(s.dLbls, k, False)
        s.dLbls.numFmt = labels; s.dLbls.dLblPos = lblpos; s.dLbls.txPr = rich(9)
        if lblbox: s.dLbls.spPr = GraphicalProperties(solidFill="FFFFFF", ln=LineProperties(noFill=True))
    ch.series.append(s)
    ch.set_categories(Reference(ws, range_string=cat_ref))
    return s


def q(ws): return f"'{ws.title}'!"

# ---------- 1. Baseline_Data ----------
ws1 = wb.active; ws1.title = "Baseline_Data"
title(ws1, "Baseline comparison data: Random Selection, Greedy GC, and iCAT (total WAF, workload mixFYF)",
      "Each baseline is compared only with the iCAT-v4 control measured in the same batch on the same host. "
      "The two iCAT-v4 controls are not pooled, and Random Selection is not compared directly with Greedy GC.")
B = [("Random Selection vs. iCAT", H1, "revA-20261114", "Random Selection", "revA-random"),
     ("Random Selection vs. iCAT", H1, "revA-20261114", "iCAT (iCAT-v4, same batch)", "revA-v4"),
     ("Greedy GC vs. iCAT", H2, "batchG-20261126", "Greedy GC", "greedygc"),
     ("Greedy GC vs. iCAT", H2, "batchG-20261126", "iCAT (iCAT-v4, same batch)", "bg-v4")]
cell(ws1, 4, 1, "Table A. Per-policy total WAF (mean of n = 3 runs; CI = 95% confidence interval of the mean, t distribution, df = 2)", bold=True)
table(ws1, 5, ["Comparison group", "Host", "Batch", "Policy", "Run group", "n", "Mean WAF", "SD",
               "95% CI half-width", "95% CI lower", "95% CI upper", "Rep 1", "Rep 2", "Rep 3"],
      [[a, h, b, p, g, 3, D[g]["mean"], D[g]["sd"], D[g]["hw"], D[g]["lo"], D[g]["hi"], *D[g]["v"]] for a, h, b, p, g in B],
      fmts={j: "0.0000" for j in range(7, 15)}, widths=[30, 30, 17, 27, 13, 6, 11, 9, 12, 11, 11, 10, 10, 10])
cell(ws1, 11, 1, "Table B. Same-batch contrast (baseline − iCAT-v4), Welch t-test", bold=True)
table(ws1, 12, ["Comparison group", "Host", "Batch", "ΔWAF (baseline − iCAT)", "Welch 95% CI lower", "Welch 95% CI upper",
                "Welch df", "p (unadjusted)", "Holm-adjusted p", "Holm family size",
                "WAF reduction by iCAT (%)\n= (baseline − iCAT) / baseline × 100"],
      [[a, h, b, CON[g]["d"], CON[g]["lo"], CON[g]["hi"], CON[g]["df"], CON[g]["p"], CON[g]["holm"], CON[g]["fam"],
        CON[g]["d"] / D[g]["mean"] * 100]
       for a, h, b, g in [("Random Selection vs. iCAT", H1, "revA-20261114", "revA-random"),
                          ("Greedy GC vs. iCAT", H2, "batchG-20261126", "greedygc")]],
      fmts={4: "+0.0000", 5: "+0.0000", 6: "+0.0000", 7: "0.00", 8: "0.0E+00", 9: "0.0000", 11: "0.00"})
ws1.row_dimensions[12].height = 42
cell(ws1, 16, 1, "Table C. Chart source (Baseline_Figure reads these cells)", bold=True)
table(ws1, 17, ["X-axis group", "Baseline (Random Selection / Greedy GC)", "iCAT", "Baseline 95% CI half-width", "iCAT 95% CI half-width"],
      [["Random Selection vs. iCAT\n(Host 1)", D["revA-random"]["mean"], D["revA-v4"]["mean"], D["revA-random"]["hw"], D["revA-v4"]["hw"]],
       ["Greedy GC vs. iCAT\n(Host 2)", D["greedygc"]["mean"], D["bg-v4"]["mean"], D["greedygc"]["hw"], D["bg-v4"]["hw"]]],
      fmts={j: "0.0000" for j in range(2, 6)})
for r in (17, 18, 19): ws1.row_dimensions[r].height = 30
notes(ws1, 21, [
    "Error bars in the figure are 95% CIs of the mean (half-width = t(0.975, df = 2) × SD / √3 = 4.3027 × SD / √3). SD is listed separately and is not used as the error bar.",
    "Holm family = {total WAF, phase-C WAF} × treatments of the same batch (revA: 3 treatments → 6 tests; batchG: 2 treatments → 4 tests).",
    "WAF = 1 + GC page writes / host page writes over the measured interval (mixFYF: FIO 1800 s → YCSB-A 1800 s → FIO 1800 s).",
    f"Sources: GoCom {GOCOM_REF} ({GOCOM_DIR}raw_data_gocom.csv, baseline_figure1_gocom.csv); SeungCom {SEUNG_REF} ({SEUNG_DIR}final_raw_data_validation.csv, final_statistical_validation.csv)."])

# ---------- 2. Baseline_Figure ----------
ws2 = wb.create_sheet("Baseline_Figure")
title(ws2, "Figure. WAF of Random Selection, Greedy GC, and iCAT",
      "Bars: mean total WAF (n = 3). Error bars: 95% CI of the mean. Each group was measured on a different host; iCAT is the iCAT-v4 control of the same batch.")
ch = bar_chart("WAF (Write Amplification Factor)", None, 0, 3.0, 0.5, 15, 9.5)
ch.x_axis.title = None
d = q(ws1)
add_series(ch, ws1, d + "$B$17", d + "$B$18:$B$19", d + "$A$18:$A$19", d + "$D$18:$D$19", GREY, labels="0.00")
add_series(ch, ws1, d + "$C$17", d + "$C$18:$C$19", d + "$A$18:$A$19", d + "$E$18:$E$19", SKY, labels="0.00")
ws2.add_chart(ch, "A4")
notes(ws2, 25, ["Editable native Excel chart; data and error-bar ranges: Baseline_Data!A17:E19.",
                "Y axis starts at 0. Host 1 = GoCom (batch revA-20261114), Host 2 = SeungCom (batch batchG-20261126)."])

# ---------- 3. Ablation_Table ----------
ws3 = wb.create_sheet("Ablation_Table")
title(ws3, "Ablation table: active features per variant and total WAF against the same-batch iCAT-v4",
      "Feature status follows the code and kernel logs verified by GoCom (feature_matrix.csv, learner_counters_runs.csv). "
      "The same variant measured on two hosts is listed as two rows and is never pooled.")
Y, N, NS, TRI = "✓", "✗", "✗*", "△"
AB = [  # variant, change (English), figure label, [Disc, Elim, Settle, Drift, Probe, PartialReset], host, batch, group
    ("NoDiscount", "Discounting removed (γ = 1.0)", "w/o Discounting\n(γ = 1)\nHost 2",
     [N, Y, Y, Y, Y, Y], H2, "abl-20261125", "abl-nodiscount"),
    ("NoElim+NoSettle", "Candidate elimination and settling removed; drift detection, probe and reset never run as a consequence",
     "w/o Elimination & Settling\n(Drift Det. & Probe inactive)\nHost 1", [Y, N, N, NS, NS, NS], H1, "revA-20261114", "revA-v2"),
    ("NoElim+NoSettle", "Candidate elimination and settling removed; drift detection, probe and reset never run as a consequence",
     "w/o Elimination & Settling\n(Drift Det. & Probe inactive)\nHost 2", [Y, N, N, NS, NS, NS], H2, "abl-20261125", OFFB),
    ("NoElim", "Candidate elimination removed", "w/o Elimination\nHost 1", [Y, N, Y, Y, Y, TRI], H1, "revE-20261125", "revE-noelim"),
    ("NoDrift", "Drift detection removed; no reset is triggered", "w/o Drift Detection\nHost 1",
     [Y, Y, Y, N, Y, NS], H1, "revA-20261114", "revA-v1"),
    ("NoDrift", "Drift detection removed; no reset is triggered", "w/o Drift Detection\nHost 2",
     [Y, Y, Y, N, Y, NS], H2, "revD-20261124", "revD-nodrift"),
    ("FullReset", "Partial reset replaced by full reset (all 45 candidates restored)", "Full Reset\n(instead of Partial Reset)\nHost 2",
     [Y, Y, Y, Y, Y, N], H2, "revD-20261124", "revD-fullreset"),
]
hdr = ["Variant", "Removed / changed feature", "Discounting", "Candidate\nElimination", "Settling", "Drift\nDetection", "Probe",
       "Partial\nReset", "Host", "Batch", "n\n(variant vs. iCAT-v4)", "Mean WAF", "SD", "95% CI lower\n(mean)", "95% CI upper\n(mean)",
       "Same-batch\niCAT-v4 WAF", "ΔWAF\n(variant − iCAT-v4)", "ΔWAF 95% CI\nlower (Welch)", "ΔWAF 95% CI\nupper (Welch)",
       "WAF change (%)", "Change 95% CI\nlower (%)", "Change 95% CI\nupper (%)", "p (unadjusted)", "Holm-adjusted p",
       "Holm family\nsize", "Significant\n(Holm p < 0.05)"]
rows = [["iCAT-v4", "— (reference; all features active, γ = 0.9995, C = 0.25)", Y, Y, Y, Y, Y, Y, "both hosts",
         "control of each batch", "", "see column P", "", "", "", "", "", "", "", "", "", "", "", "", "", "reference"]]
for v, chg, lab, fs, h, b, g in AB:
    c = CON[g]
    rows.append([v, chg, *fs, h, b, "3 vs. 3", D[g]["mean"], D[g]["sd"], D[g]["lo"], D[g]["hi"], D[c["ctrl"]]["mean"],
                 c["d"], c["lo"], c["hi"], c["pct"], c["pct_lo"], c["pct_hi"], c["p"], c["holm"], c["fam"],
                 "Yes" if c["holm"] < 0.05 else "No"])
fm = {j: "0.0000" for j in (12, 13, 14, 15, 16)}
fm.update({17: "+0.0000;-0.0000", 18: "+0.0000;-0.0000", 19: "+0.0000;-0.0000", 20: "+0.00;-0.00", 21: "+0.00;-0.00",
           22: "+0.00;-0.00", 23: "0.0000", 24: "0.0000"})
table(ws3, 4, hdr, rows, fmts=fm,
      widths=[18, 52, 12, 12, 10, 11, 9, 10, 30, 15, 13, 10, 9, 12, 12, 12, 13, 13, 13, 11, 13, 13, 11, 11, 9, 13])
ws3.row_dimensions[4].height = 44
for r in range(5, 13):
    ws3.cell(row=r, column=2).alignment = Alignment(wrap_text=True, vertical="center")
    ws3.row_dimensions[r].height = 30
    for c_ in range(3, 9): ws3.cell(row=r, column=c_).font = Font(name="Segoe UI Symbol", size=11, bold=True)
r = notes(ws3, 14, [
    "✓ active.   ✗ removed or changed in the build of this variant.   ✗* not removed in the code, but never executed because its precondition is removed.   △ executed, but with nothing to restore.",
    "NoElim+NoSettle (ICAT_VARIANT 2): elimination and settling are compiled out. Drift detection and probe run only in the settled state, so they are also inactive; no reset occurs (kernel logs: eliminations 0, resets 0, 45/45 candidates remain).",
    "NoDrift (ICAT_VARIANT 1): detection is compiled out, so partial reset is never triggered (kernel logs: resets 0).   NoElim (ICAT_VARIANT 3): resets occur (4 per run), but no candidate was eliminated, so there is nothing to restore.",
    "NoDiscount: same code as iCAT-v4 built with γ = 1.0 (WATGC_V2_GAMMA_Q16 = 65536); discounting is still computed but has no effect.   FullReset (ICAT_VARIANT 7): a reset restores all 45 candidates instead of survivors + neighbours.",
    "WAF change (%) = (variant − same-batch iCAT-v4) / same-batch iCAT-v4 × 100. Its CI is the Welch 95% CI of ΔWAF divided by the control mean (the uncertainty of the denominator is not propagated).",
    "Mean-WAF CI: t distribution, df = 2. Holm family = {total WAF, phase-C WAF} × treatments of the same batch. Significance criterion: Holm-adjusted p < 0.05.",
    "NoElim (Host 1, Holm p = 0.091) and FullReset (Host 2, Holm p = 0.072): the unadjusted Welch 95% CI of ΔWAF excludes 0, but the difference is not significant after Holm correction.",
    "Excluded: revB NoElim / NoSettle (same-batch iCAT-v4 has n = 1, no statistics). Parameter variants (Elim10/25, Drift12.5/50, Arms60) are not ablations."])
cell(ws3, r + 1, 1, "Evidence for the feature status (GoCom verification)", bold=True)
ev = git_csv(GOCOM_REF, GOCOM_DIR + "feature_matrix.csv")
evd = {x["Variant"].split(" (")[0]: x for x in ev if x.get("ICAT_VARIANT")}


def logline(g):
    if g not in LC: return "Not in GoCom learner_counters_runs.csv (SeungCom runs). γ / C / variant confirmed from WATGC_V2 init lines of SeungCom kernel logs (GoCom report §0, §2.1)."
    rs = LC[g]
    return (f"{g}: active candidates at end of phase A = {min(float(x['active_end_phaseA_mean']) for x in rs):g}–"
            f"{max(float(x['active_end_phaseA_mean']) for x in rs):g} / 45; eliminations (sum) = "
            f"{min(int(x['elim_counter_sum']) for x in rs)}–{max(int(x['elim_counter_sum']) for x in rs)}; resets (sum) = "
            f"{min(int(x['reset_sum']) for x in rs)}–{max(int(x['reset_sum']) for x in rs)}; "
            f"loaded variant = {rs[0]['loaded_variant']}, gamma_q16 = {rs[0]['gamma_q16']}, exploration_q16 = {rs[0]['exploration_q16']}")


evrows = [["iCAT-v4", evd["iCAT-v4"]["ICAT_VARIANT"], evd["iCAT-v4"]["γ (discount)"], "all features active", logline("revA-v4")],
          ["NoDiscount", evd["NoDiscount"]["ICAT_VARIANT"], evd["NoDiscount"]["γ (discount)"], evd["NoDiscount"]["변경 코드 위치"], logline("abl-nodiscount")],
          ["NoElim+NoSettle", evd["NoElim+NoSettle"]["ICAT_VARIANT"], evd["NoElim+NoSettle"]["γ (discount)"], evd["NoElim+NoSettle"]["변경 코드 위치"], logline("revA-v2")],
          ["NoElim", evd["NoElim"]["ICAT_VARIANT"], evd["NoElim"]["γ (discount)"], evd["NoElim"]["변경 코드 위치"], logline("revE-noelim")],
          ["NoDrift", evd["NoDrift"]["ICAT_VARIANT"], evd["NoDrift"]["γ (discount)"], evd["NoDrift"]["변경 코드 위치"], logline("revA-v1")],
          ["FullReset", evd["FullReset"]["ICAT_VARIANT"], evd["FullReset"]["γ (discount)"], evd["FullReset"]["변경 코드 위치"], logline("revD-fullreset")]]
r0 = r + 2
for j, h in enumerate(["Variant", "Code evidence (GoCom feature_matrix.csv)", "ICAT_VARIANT", "γ", "Kernel-log evidence (GoCom learner_counters_runs.csv)"], 1):
    cell(ws3, r0, j if j < 3 else j + 0, h, bold=True).border = Border(top=MED, bottom=THIN)
for i, (v, var, gam, code, log) in enumerate(evrows, 1):
    cell(ws3, r0 + i, 1, v); cell(ws3, r0 + i, 2, code, wrap=True, size=9); cell(ws3, r0 + i, 3, var, align="center")
    cell(ws3, r0 + i, 4, gam, align="center"); cell(ws3, r0 + i, 5, log, size=9)
    ws3.row_dimensions[r0 + i].height = 40

# ---------- 4. Ablation_Figure ----------
ws4 = wb.create_sheet("Ablation_Figure")
title(ws4, "Figure. WAF change of each ablation variant relative to the iCAT-v4 of the same batch",
      "Bars: (variant − iCAT-v4) / iCAT-v4 × 100. Error bars: Welch 95% CI of ΔWAF as % of the control mean. "
      "Filled: Holm-adjusted p < 0.05; white: not significant. Host 1 and Host 2 results are separate bars (not pooled).")
SIG, NSG = "Significant (Holm-adjusted p < 0.05)", "Not significant (Holm-adjusted p ≥ 0.05)"
prow = []
for v, chg, lab, fs, h, b, g in AB:
    c = CON[g]; s = c["holm"] < 0.05; hw = (c["pct_hi"] - c["pct_lo"]) / 2
    prow.append([lab, c["pct"] if s else None, None if s else c["pct"], hw if s else None, None if s else hw,
                 v, h.split(" (")[0], c["pct"], c["pct_lo"], c["pct_hi"], c["holm"]])
P0 = 32
table(ws4, P0, ["Bar label", SIG, NSG, "CI half-width (significant)", "CI half-width (not significant)", "Variant", "Host",
                "WAF change (%)", "95% CI lower (%)", "95% CI upper (%)", "Holm-adjusted p"], prow,
      fmts={2: "+0.00;-0.00", 3: "+0.00;-0.00", 4: "0.00", 5: "0.00", 8: "+0.00;-0.00", 9: "+0.00;-0.00", 10: "+0.00;-0.00", 11: "0.0000"},
      widths=[34, 16, 16, 14, 14, 18, 9, 12, 12, 12, 12])
ws4.row_dimensions[P0].height = 44
for i in range(1, 8):
    ws4.row_dimensions[P0 + i].height = 42
    ws4.cell(row=P0 + i, column=1).alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
ch = bar_chart("WAF change vs. same-batch iCAT-v4 (%)", None, -4, 12, 2, 29, 12, yfmt="0")
ch.x_axis.title = None; ch.overlap = 100; ch.gapWidth = 60
d = q(ws4); a, z = P0 + 1, P0 + 7
add_series(ch, ws4, f"{d}$B${P0}", f"{d}$B${a}:$B${z}", f"{d}$A${a}:$A${z}", f"{d}$D${a}:$D${z}", SKY)
add_series(ch, ws4, f"{d}$C${P0}", f"{d}$C${a}:$C${z}", f"{d}$A${a}:$A${z}", f"{d}$E${a}:$E${z}", "FFFFFF")
ws4.add_chart(ch, "A4")
cell(ws4, P0 - 1, 1, "Chart source (values copied from Ablation_Table)", bold=True)
notes(ws4, P0 + 9, [
    "Editable native Excel chart; two overlapping series (significant / not significant) so that the fill encodes the Holm-adjusted test result.",
    "'w/o Elimination & Settling' also has drift detection and probe inactive, because both run only in the settled state (see Ablation_Table).",
    "NoElim (Host 1) and FullReset (Host 2) have CIs that exclude 0 before correction but Holm-adjusted p ≥ 0.05; they are drawn as not significant.",
    "Each bar is normalised by the iCAT-v4 of its own batch; bars from different hosts/batches are shown side by side and must not be averaged."])

# ---------- 5. Elimination_Threshold ----------
ws5 = wb.create_sheet("Elimination_Threshold")
title(ws5, "Elimination threshold (10%, 15%, 25%): total WAF and candidates actually eliminated",
      "All three settings were measured in the same batch on Host 1 (revC-20261124, n = 3 each). "
      "The threshold is a rule parameter; the eliminated share is the measured outcome at the end of phase A.")
ET = [("10%", "revC-elim10"), ("15% (default)", "revC-v4"), ("25%", "revC-elim25")]
rows = []
for lab, g in ET:
    c = CON.get(g)
    rows.append([lab, g, 3, D[g]["mean"], D[g]["sd"], D[g]["hw"], D[g]["lo"], D[g]["hi"],
                 c["d"] if c else "reference", c["lo"] if c else "", c["hi"] if c else "", c["holm"] if c else "",
                 ACTIVE[g]["mean"], SHARE[g]["mean"], SHARE[g]["sd"], SHARE[g]["hw"], *SHARE[g]["v"]])
E0 = 4
fm = {j: "0.0000" for j in (4, 5, 6, 7, 8, 12)}
fm.update({9: "+0.0000;-0.0000", 10: "+0.0000;-0.0000", 11: "+0.0000;-0.0000", 13: "0.00"})
fm.update({j: "0.0" for j in range(14, 20)})
table(ws5, E0, ["Elimination threshold", "Run group", "n", "Mean WAF", "SD", "WAF 95% CI\nhalf-width", "WAF 95% CI\nlower",
                "WAF 95% CI\nupper", "ΔWAF vs. 15%", "Welch 95% CI\nlower", "Welch 95% CI\nupper", "Holm-adjusted p\n(family of 8)",
                "Active candidates at\nend of phase A (of 45)", "Candidates eliminated at\nend of phase A (%)", "SD (%)",
                "95% CI\nhalf-width (%)", "Rep 1 (%)", "Rep 2 (%)", "Rep 3 (%)"], rows, fmts=fm,
      widths=[20, 13, 5, 10, 9, 12, 12, 12, 13, 12, 12, 14, 18, 20, 8, 12, 9, 9, 9])
ws5.row_dimensions[E0].height = 44
d = q(ws5); a, z = E0 + 1, E0 + 3
ch = bar_chart("WAF (Write Amplification Factor)", "Elimination threshold", 0, 2.5, 0.5, 12, 9, legend=False)
add_series(ch, ws5, f"{d}$D${E0}", f"{d}$D${a}:$D${z}", f"{d}$A${a}:$A${z}", f"{d}$F${a}:$F${z}", SKY, labels="0.00")
ws5.add_chart(ch, "A10")
ch = bar_chart("Eliminated candidates (%)", "Elimination threshold", 0, 100, 20, 12, 9, yfmt="0", legend=False)
add_series(ch, ws5, f"{d}$N${E0}", f"{d}$N${a}:$N${z}", f"{d}$A${a}:$A${z}", f"{d}$P${a}:$P${z}", SKY, labels="0", lblpos="inBase", lblbox=True)
ws5.add_chart(ch, "H10")
cell(ws5, 9, 1, "(a) Mean total WAF per threshold (error bars: 95% CI)", bold=True)
cell(ws5, 9, 8, "(b) Candidates actually eliminated per threshold (error bars: 95% CI)", bold=True)
notes(ws5, 30, [
    "Threshold ≠ eliminated share. The threshold removes a candidate whose mean WAF exceeds the best candidate's by more than the given percentage; "
    "the measured share of the 45 candidates eliminated at the end of phase A was 80% (threshold 10%), 61% (15%) and 10% (25%).",
    "Eliminated share = 1 − (active candidates at end of phase A, mean of 4 partitions) / 45, per run; then mean, SD and 95% CI (t, df = 2) over 3 runs.",
    "Total WAF: neither 10% nor 25% is distinguishable from 15% (Welch 95% CIs of ΔWAF include 0; Holm-adjusted p = 0.95 and 0.47). No threshold can be claimed optimal.",
    "Holm family: revC batch, {total WAF, phase-C WAF} × {Elim10, Elim25, Arms60, original iCAT} = 8 tests.",
    f"Sources: GoCom {GOCOM_REF} ({GOCOM_DIR}param_elimination_threshold.csv, learner_counters_runs.csv, raw_data_gocom.csv)."])

# ---------- 6. Raw_Data ----------
ws6 = wb.create_sheet("Raw_Data")
title(ws6, "Per-run raw data used in this workbook (51 runs, all valid, workload mixFYF)",
      "WAF = 1 + gc_pages / host_pages. Elimination columns are filled only for the threshold runs (revC).")
USE = {"revA-random": "Baseline", "greedygc": "Baseline", "bg-v4": "Baseline", "revA-v4": "Baseline, Ablation",
       "abl-nodiscount": "Ablation", "abl-v4": "Ablation", "revA-v2": "Ablation", OFFB: "Ablation", "revE-noelim": "Ablation",
       "revE-v4": "Ablation", "revA-v1": "Ablation", "revD-nodrift": "Ablation", "revD-fullreset": "Ablation", "revD-v4": "Ablation",
       "revC-elim10": "Elimination_Threshold", "revC-v4": "Elimination_Threshold", "revC-elim25": "Elimination_Threshold"}
NAME = {"revA-random": "Random Selection", "greedygc": "Greedy GC", "abl-nodiscount": "NoDiscount", "revA-v2": "NoElim+NoSettle",
        OFFB: "NoElim+NoSettle", "revE-noelim": "NoElim", "revA-v1": "NoDrift", "revD-nodrift": "NoDrift",
        "revD-fullreset": "FullReset", "revC-elim10": "iCAT-v4, elimination threshold 10%",
        "revC-elim25": "iCAT-v4, elimination threshold 25%"}
rows = []
for g in USED:
    for r in RUN[g]:
        lc = next((x for x in LC.get(g, []) if int(x["rep"]) == r["rep"]), None) if g.startswith("revC") else None
        rows.append([USE[g], r["host"], r["batch"], g, NAME.get(g, "iCAT-v4"), r["rep"], r["host_pages"], r["gc_pages"], r["waf"],
                     r["A"], r["B"], r["C"], lc["active_end_phaseA_per_part"] if lc else "",
                     float(lc["eliminated_share_end_phaseA"]) * 100 if lc else "", r["valid"], r["sha"], r["seeds"], r["iseed"],
                     r["raw"], r["src"]])
table(ws6, 4, ["Used in", "Host", "Batch", "Run group", "Policy / variant", "Rep", "host_pages", "gc_pages", "Total WAF", "WAF phase A",
               "WAF phase B", "WAF phase C", "Active candidates at end of\nphase A (4 partitions)", "Eliminated share at\nend of phase A (%)",
               "Valid", "Module SHA256", "FIO seeds (A / B / C)", "iCAT seed", "Raw log directory", "Source file (commit:path)"], rows,
      fmts={7: "#,##0", 8: "#,##0", 9: "0.000000", 10: "0.000000", 11: "0.000000", 12: "0.000000", 14: "0.00"},
      widths=[22, 30, 17, 32, 32, 5, 13, 13, 11, 11, 11, 11, 22, 17, 7, 66, 28, 12, 70, 80])
ws6.row_dimensions[4].height = 32
ws6.freeze_panes = "A5"

# ---------- 7. Verification ----------
ws7 = wb.create_sheet("Verification")
title(ws7, "Verification: sources, recomputation checks, unverified parameters",
      "No new experiment was run. Every statistic in this workbook was recomputed from per-run values and compared with the values reported by GoCom and SeungCom.")
r = 4
cell(ws7, r, 1, "A. Sources", bold=True)
srcs = [["GoCom validated data", "github.com/oyeong011/iCAT-experiments", "report/data-validity-20261124", GOCOM_REF, GOCOM_DIR,
         "GOCOM_FINAL_REPORT.md; raw_data_gocom.csv, baseline_figure1_gocom.csv, ablation_table_gocom.csv, feature_matrix.csv, learner_counters_runs.csv, param_elimination_threshold.csv, param_discount_factor.csv, param_exploration_C.csv"],
        ["SeungCom final results", "github.com/oyeong011/iCAT-experiments", "main", SEUNG_REF, SEUNG_DIR,
         "final_raw_data_validation.csv (per-run counters), final_statistical_validation.csv (descriptives, Welch contrasts, Holm)"],
        ["SeungCom raw kernel/FIO logs", "github.com/oyeong011/iCAT-experiments", "main", "4689c6797",
         "result/revD-20261124, result/revision-additional-ablation, result/batchG-20261126, result/greedygc-20261126", "raw/ directories listed per run in Raw_Data"],
        ["GoCom raw kernel/FIO logs", "github.com/oyeong011/iCAT-experiments", "report/data-validity-20261124", GOCOM_REF,
         "result/revA-20261114, result/revC-20261124, result/revE-20261125", "raw/ directories listed per run in Raw_Data"]]
table(ws7, r + 1, ["Item", "Repository", "Branch", "Commit", "Path", "Files"], srcs, widths=[58, 22, 22, 40, 12, 12])
for i in range(len(srcs)):
    for j in (1, 5, 6): ws7.cell(row=r + 2 + i, column=j).alignment = Alignment(horizontal="left", vertical="center")
r += len(srcs) + 3
cell(ws7, r, 1, "B. Parameters without sensitivity experiments (unverified; no figure produced)", bold=True)
unv = [["Discount factor γ", "0.9995 (WATGC_V2_GAMMA_Q16 = 65503)", "γ = 0.9995 (all iCAT-v4 runs) and γ = 1.0 (NoDiscount, SeungCom abl batch) only",
        "Not executed: any other γ (e.g. 0.90, 0.95, 0.99)", "Unverified. NoDiscount vs. iCAT-v4 is an ablation (Ablation_Table), not a sensitivity curve."],
       ["Exploration coefficient C (UCB bonus, WAF units)", "0.25 (WATGC_V2_UCB_C_Q16 = 16384)", "C = 0.25 in every run",
        "Not executed: any other C (e.g. 0.50, 0.75)", "Unverified. No sensitivity data exist."]]
table(ws7, r + 1, ["Parameter", "Default actually used", "Values actually measured", "Sensitivity experiment", "Status"], unv)
for i in range(2):
    for j in range(1, 6): ws7.cell(row=r + 2 + i, column=j).alignment = Alignment(horizontal="left", vertical="center")
r = notes(ws7, r + 4, ["Basis: GoCom scan of 462,668 'WATGC_V2 init' kernel-log lines on both hosts (GOCOM_FINAL_REPORT.md §0, §5.2): gamma_q16 ∈ {65503, 65536}, exploration_q16 = 16384 only."]) + 1
cell(ws7, r, 1, "C. Method and limits", bold=True)
r = notes(ws7, r + 1, [
    "Descriptives: mean, sample SD (n − 1), 95% CI of the mean = mean ± t(0.975, n − 1) × SD / √n. Error bars are CIs, never SDs.",
    "Contrasts: Welch t-test (unequal variances, Welch–Satterthwaite df) against the iCAT-v4 control of the same batch; Holm correction within each batch family ({total WAF, phase-C WAF} × treatments).",
    "No pooling: the same variant on two hosts (NoElim+NoSettle, NoDrift) and the iCAT-v4 controls of different batches are kept separate.",
    "Random Selection (Host 1) and Greedy GC (Host 2) were measured on different hosts; each is interpreted only against its own iCAT-v4 control.",
    "n = 3 per group, single workload (mixFYF). GoCom reference values are published to 4 decimals (tolerance 6e-5); SeungCom values to full precision (tolerance 1e-6).",
    "Kernel-log learner counters are available for Host 1 runs only (learner_counters_runs.csv); the feature status of the Host 2 variants rests on GoCom's source cross-check and init-line scan."]) + 1
nm = sum(1 for c in checks if c[5] == "MATCH")
cell(ws7, r, 1, f"D. Recomputation checks: {len(checks)} checks, {nm} match, {len(checks) - nm} mismatch", bold=True)
table(ws7, r + 1, ["Item", "Recomputed here", "Reported", "Reference source", "Tolerance", "Result"],
      [list(c) for c in checks], fmts={2: "0.000000", 3: "0.000000"})
for i in range(len(checks)):
    for j in (1, 4): ws7.cell(row=r + 2 + i, column=j).alignment = Alignment(horizontal="left", vertical="center")
ws7.column_dimensions["D"].width = 62

wb.save(OUT)
# openpyxl writes data-label <c:numFmt> without sourceLinked="0", so Excel ignores the format; patch the chart XML.
import re, shutil, zipfile
tmp = OUT + ".tmp"
with zipfile.ZipFile(OUT) as zi, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zo:
    for it in zi.infolist():
        data = zi.read(it.filename)
        if it.filename.startswith("xl/charts/chart"):
            data = re.sub(rb'(<dLbls>\s*<numFmt formatCode="[^"]*")\s*/>', rb'\g<1> sourceLinked="0"/>', data)
        zo.writestr(it, data)
shutil.move(tmp, OUT)
print(f"saved {OUT}; checks {len(checks)}, mismatches {len(checks) - nm}")
for g in USED: print(f"{g:34s} {D[g]['mean']:.4f} sd {D[g]['sd']:.4f} ci [{D[g]['lo']:.4f}, {D[g]['hi']:.4f}]")
for t, c in CON.items(): print(f"{t:34s} d {c['d']:+.4f} [{c['lo']:+.4f}, {c['hi']:+.4f}] pct {c['pct']:+.2f} holm {c['holm']:.4f}/{c['fam']}")
for t in SHARE: print(t, f"share {SHARE[t]['mean']:.1f}% ± CI {SHARE[t]['hw']:.1f}")
