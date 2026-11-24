#!/usr/bin/env python3
"""Redesigned Table 8 / Figure 10 from the E1 rerun only (GoCom, 2026-11-24).

Source: result/final-e1-validation/e1_{runs,timeseries,resets}.csv written by e1_analyze.py.
Batch: result/revision-20261124/mixR, YCSB 300k records (label '.../rec300k'). No other batch is read.
Gate: a policy enters only with >= 3 runs whose every phase is valid (run_ok). Until ALL three policies
(onlinev4, onlinev4nodrift, onlinev4fullreset) have 3 valid runs, NO number and NO figure is produced:
only a status file. Nothing is estimated or extrapolated.
Outputs: report/final-e1-validation/tables/table8_e1.md, figs/paper/paper_fig10_e1_three_phase.{png,pdf,svg} (when ready)."""
import csv, math, re, statistics as st, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'result/final-e1-validation'; T = ROOT / 'report/final-e1-validation/tables'; FIG = ROOT / 'report/final-e1-validation/figs/paper'
BATCH = 'result/revision-20261124/mixR/rec300k'
POL = [('onlinev4', 'iCAT-v4'), ('onlinev4nodrift', 'NoDrift (변화 감지 끔)'), ('onlinev4fullreset', 'FullReset (45개 전체 재탐색)')]
T95 = {2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 8: 2.306, 10: 2.228}
tq = lambda df: T95[min(T95, key=lambda k: abs(k - df))]


def read(name):
    f = D / name
    return list(csv.DictReader(open(f))) if f.exists() and f.stat().st_size else []


runs = [r for r in read('e1_runs.csv') if r['batch'] == BATCH]
valid = {p: [r for r in runs if r['policy'] == p and r['run_ok'] == 'True'] for p, _ in POL}
ready = all(len(valid[p]) >= 3 for p, _ in POL)
status = ' / '.join(f'{lab.split(" ")[0]} 유효 {len(valid[p])}회 (전체 {sum(r["policy"] == p for r in runs)}회)' for p, lab in POL)

if not ready:
    (T / 'table8_e1.md').write_text(
        '# 표 8 · 그림 10 (재설계, E1 재실험 기준): **대기**\n\n'
        f'- 배치: `{BATCH}`\n- 현재: {status}\n'
        '- 조건: 세 정책 모두 유효 3회(모든 단계 유효, YCSB 실패 ≤ 1 %, SQLITE_FULL 없음).\n'
        '- 조건을 채우기 전에는 수치와 그림을 만들지 않는다. 추정값은 넣지 않는다.\n')
    print('WAIT:', status); sys.exit(0)


def ci(v):
    m = st.mean(v); s = st.stdev(v); h = tq(len(v) - 1) * s / math.sqrt(len(v)); return m, s, m - h, m + h


def welch(a, b):
    va, vb = st.variance(a) / len(a), st.variance(b) / len(b); se = math.sqrt(va + vb)
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1)); d = st.mean(a) - st.mean(b)
    return d, d - tq(df) * se, d + tq(df) * se


L = ['**표 8 (재설계).** 3단계 균등 전환(FIO-Fast → YCSB-A(300k 레코드) → FIO-Fast, 3배 길이)에서 변화 감지와 재탐색 범위를 바꾼 iCAT-v4 변형의 단계별 WAF '
     f'(각 정책 유효 {min(len(valid[p]) for p, _ in POL)}회 이상, 평균 ± 표준편차 [95 % CI]). 원자료 `{BATCH}`', '',
     '| 정책 | n | 단계 1 FIO-Fast | 단계 2 YCSB-A | 단계 3 FIO-Fast | 전체 | 단계 3 재탐색 (파티션 4개, 횟수 · 중앙 시점 s) | YCSB READ/UPDATE 최저 성공 % |',
     '|---|---:|---|---|---|---|---|---|']
res = read('e1_resets.csv')
for p, lab in POL:
    v = valid[p]; cells = []
    for k in ('waf_A', 'waf_B', 'waf_C', 'waf_total'):
        m, s, lo, hi = ci([float(r[k]) for r in v]); cells.append(f'{m:.3f} ± {s:.3f} [{lo:.3f}, {hi:.3f}]')
    rr = [x for x in res if x['batch'] == BATCH and x['policy'] == p and x['phase'] == 'C' and int(x['rep']) in {int(r['rep']) for r in v}]
    rs = f"{len(rr) / len(v):.1f}회/run · {st.median(float(x['s_after_phase_start']) for x in rr):.0f}" if rr else '0회'
    ysucc = min(min(float(r.get('ycsb_read_success_pct') or 100), float(r.get('ycsb_update_success_pct') or 100)) for r in v)
    L.append(f'| {lab} | {len(v)} | ' + ' | '.join(cells) + f' | {rs} | {ysucc:.3f} |')
L += ['', '| 비교 (Welch 95 % CI) | 단계 3 WAF 차이 | 전체 WAF 차이 | CI가 0을 포함하지 않음 |', '|---|---|---|---|']
base = valid['onlinev4']
for p, lab in POL[1:]:
    out = []
    for k in ('waf_C', 'waf_total'):
        d, lo, hi = welch([float(r[k]) for r in valid[p]], [float(r[k]) for r in base]); out.append((d, lo, hi))
    L.append(f'| {lab.split(" ")[0]} − iCAT-v4 | {out[0][0]:+.3f} [{out[0][1]:+.3f}, {out[0][2]:+.3f}] | {out[1][0]:+.3f} [{out[1][1]:+.3f}, {out[1][2]:+.3f}] | '
             + ', '.join(n for n, o in (('단계 3', out[0]), ('전체', out[1])) if o[1] > 0 or o[2] < 0) + ' |')
(T / 'table8_e1.md').write_text('\n'.join(L) + '\n')

# Figure 10 (redesigned): (a) per-phase WAF mean with 95 % CI, (b) phase-3 5-minute WAF, mean of valid runs with min-max band
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib import font_manager
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family': 'Noto Sans CJK JP', 'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
COL = {'onlinev4': '#2a78d6', 'onlinev4nodrift': '#eb6834', 'onlinev4fullreset': '#1baf7a'}
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 3.8), gridspec_kw={'width_ratios': [1, 1.3]})
for j, (p, lab) in enumerate(POL):
    xs, ys, es = [], [], []
    for i, k in enumerate(('waf_A', 'waf_B', 'waf_C')):
        m, s, lo, hi = ci([float(r[k]) for r in valid[p]]); xs.append(i + (j - 1) * 0.26); ys.append(m); es.append(hi - m)
    a1.bar(xs, ys, width=0.24, yerr=es, capsize=3, color=COL[p], label=lab)
a1.set_xticks(range(3)); a1.set_xticklabels(['단계 1 FIO-Fast', '단계 2 YCSB-A', '단계 3 FIO-Fast']); a1.set_ylabel('단계 WAF (95 % CI)')
a1.legend(frameon=False, fontsize=8)
ts = [x for x in read('e1_timeseries.csv') if x['batch'] == BATCH and x['phase'] == 'C']
for p, lab in POL:
    reps = {int(r['rep']) for r in valid[p]}; by = {}
    for x in ts:
        if x['policy'] == p and int(x['rep']) in reps: by.setdefault(round(float(x['minute_to'])), []).append(float(x['waf']))
    mins = sorted(k for k, v in by.items() if len(v) == len(reps))
    a2.plot(mins, [st.mean(by[k]) for k in mins], color=COL[p], lw=2, label=lab)
    a2.fill_between(mins, [min(by[k]) for k in mins], [max(by[k]) for k in mins], color=COL[p], alpha=0.15, lw=0)
a2.set_xlabel('단계 3 시작 후 시간 (분)'); a2.set_ylabel('5분 구간 WAF (선 = 평균, 띠 = 최소~최대)')
fig.suptitle('그림 10. 3단계 균등 전환(재측정, YCSB 300k): 변화 감지와 재탐색 범위에 따른 단계별 WAF', x=0.01, ha='left', fontsize=11)
fig.tight_layout(); FIG.mkdir(parents=True, exist_ok=True)
for e in ('png', 'pdf', 'svg'): fig.savefig(FIG / f'paper_fig10_e1_three_phase.{e}', dpi=200, bbox_inches='tight')
print('\n'.join(L))
