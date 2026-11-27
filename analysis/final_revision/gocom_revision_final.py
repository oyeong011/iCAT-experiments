#!/usr/bin/env python3
"""GoCom part of the "iCAT revision final results and Excel figures" task (2026-11-27).

Read-only. Inputs:
  - report/final-revision/complete-results/{raw_results_mixFYF,all_group_stats,all_contrasts,run_validity,adaptation_metrics}.csv
    (all recomputed from raw counters by analysis/final_revision/complete_results.py, commit 3fdb21258)
  - result/<batch>/raw/<run>/kernel.log  (learner counters, variant / gamma / C actually loaded)
  - result/revC-20261124-analysis/learner_runs.csv (existing elimination counts, cross-checked)
Outputs: report/final-revision/gocom_revision_final/*.csv. Refuses to overwrite.
Stats are recomputed here from per-rep values and asserted against the complete-results CSVs.
"""
import csv, math, re, statistics as st, sys
from pathlib import Path
from scipy import stats as ss

ROOT = Path(__file__).resolve().parents[2]
CR = ROOT / 'report/final-revision/complete-results'
OUT = ROOT / 'report/final-revision/gocom_revision_final'
if OUT.exists() and any(OUT.iterdir()):
    sys.exit(f'refusing to overwrite non-empty {OUT}')
OUT.mkdir(parents=True, exist_ok=True)

rd = lambda p: list(csv.DictReader(open(p, encoding='utf-8')))
RAW = rd(CR / 'raw_results_mixFYF.csv')
GS = {(r['그룹'], r['지표']): r for r in rd(CR / 'all_group_stats.csv')}
CT = {(r['대비 (정책 − 대조군)'], r['지표']): r for r in rd(CR / 'all_contrasts.csv')}
VAL = {(r['그룹'], r['rep']): r for r in rd(CR / 'run_validity.csv')}
ADP = {(r['그룹'], r['지표']): r for r in rd(CR / 'adaptation_metrics.csv')}
CHECKS = []   # (what, here, reference, source, ok)


def chk(what, here, ref, src, tol=1e-4):
    try: ok = abs(float(here) - float(ref)) <= tol
    except (TypeError, ValueError): ok = str(here) == str(ref)
    CHECKS.append(dict(item=what, this_script=here, reference=ref, reference_source=src, match=ok))


def runs(g): return sorted((r for r in RAW if r['그룹'] == g), key=lambda r: int(r['rep']))


MET = [('전체 WAF', 'waf'), ('단계 A', 'waf_A'), ('단계 B', 'waf_B'), ('단계 C', 'waf_C'), ('C 첫 5분', 'waf_C5')]


def desc(xs):
    n = len(xs); m = st.mean(xs)
    if n < 3: return dict(n=n, mean=m, sd='', ci_lo='', ci_hi='')
    sd = st.stdev(xs); h = ss.t.ppf(.975, n - 1) * sd / math.sqrt(n)
    return dict(n=n, mean=m, sd=sd, ci_lo=m - h, ci_hi=m + h)


def welch(a, b):
    va, vb = st.variance(a) / len(a), st.variance(b) / len(b); se = math.sqrt(va + vb)
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1)); d = st.mean(a) - st.mean(b)
    h = ss.t.ppf(.975, df) * se
    return dict(delta=d, lo=d - h, hi=d + h, df=df, p=2 * ss.t.sf(abs(d) / se, df))


def vals(g, col): return [float(r[col]) for r in runs(g)]


COLS = {'waf': '전체 WAF', 'waf_A': '단계 A', 'waf_B': '단계 B', 'waf_C': '단계 C', 'waf_C5': 'C 첫 5분'}
GS_KEY = {'waf': 'waf', 'waf_A': 'waf_A', 'waf_B': 'waf_B', 'waf_C': 'waf_C', 'waf_C5': 'waf_C5'}

# ------------------------------------------------------------------ source-verified feature matrix
SRC = 'revC-src/conv_ftl.c'   # revA-src / revB-src have the same line numbers for these blocks (diff checked)
LOC = dict(discount=f'{SRC}:578-582 (watgc_v2_discount on every arm each window; γ = WATGC_V2_GAMMA_Q16, conv_ftl.h:61)',
           elim=f'{SRC}:616-633 (skipped when ICAT_VARIANT 2 or 3; threshold WATGC_V2_ELIM_Q16, conv_ftl.h:39)',
           settle=f'{SRC}:536-550 (skipped when ICAT_VARIANT 2, 5, 9)',
           drift=f'{SRC}:563-574 (skipped when ICAT_VARIANT 1; runs only while settled; threshold WATGC_V2_DRIFT_Q16, conv_ftl.h:75)',
           probe=f'{SRC}:642-655 (runs only while settled)',
           reset=f'{SRC}:474-497 (reset_epoch: zero all arm statistics, active = survivors + 1-step neighbours via watgc_v2_grow)',
           random=f'{SRC}:611-614 (ICAT_VARIANT 9 returns a uniform random arm among 45)',
           arms=f'revC-src/conv_ftl.h:33-37 (ICAT_VARIANT 6 sets WATGC_V2_ARM_LO 0 -> 60 arms)',
           ucb=f'revC-src/conv_ftl.h:63 WATGC_V2_UCB_C_Q16 16384 = 0.25 WAF units; used at {SRC}:436')
Y, N = '✓', '✗'
# name, groups, variant, γ, C, elim, drift, arms, Disc, Elim, Settle, Drift, PartialReset, Probe, removed, kept, code, kind
FEAT = [
    ('iCAT-v4', 'revA-v4 revB-v4 revC-v4 revE-v4 (고컴); revD-v4 abl-v4 bg-v4 (승컴)', 4, '0.9995', '0.25', '15 %', '25 %', 45, Y, Y, Y, Y, Y, Y,
     '—', '전부', '—', '대조군'),
    ('NoDrift (revA V1)', 'revA-v1 (고컴); revD-nodrift (승컴)', 1, '0.9995', '0.25', '15 %', '— (감지 없음)', 45, Y, Y, Y, N, '— (재설정 없음)', Y,
     '변화 감지와 재설정', '할인, 제거, 정착, probe', LOC['drift'], 'Ablation'),
    ('NoElim+NoSettle (revA V2 = abl 묶음 끔)', 'revA-v2 (고컴); abl-off-elim-settle-drift-probe (승컴)', 2, '0.9995', '0.25', '— (제거 없음)', '— (정착 없어 미동작)', 45, Y, N, N,
     'N (구조상)', '— (재설정 없음)', 'N (구조상)', '후보 제거, 정착. 정착이 전제인 변화 감지·재설정·probe도 동작하지 않음', '할인 UCB (45개)',
     LOC['elim'] + '; ' + LOC['settle'], 'Ablation'),
    ('NoElim', 'revE-noelim, revB-noelim (고컴, 같은 모듈 b1663b47)', 3, '0.9995', '0.25', '— (제거 없음)', '25 %', 45, Y, N, Y, Y,
     '△ (제거된 후보가 없어 복원 대상 없음)', Y, '후보 제거', '할인, 정착, 변화 감지, 재설정, probe', LOC['elim'], 'Ablation'),
    ('NoSettle', 'revB-nosettle (고컴)', 5, '0.9995', '0.25', '15 %', '— (정착 없어 미동작)', 45, Y, Y, N, 'N (구조상)', '— (재설정 없음)', 'N (구조상)',
     '정착. 정착이 전제인 변화 감지·재설정·probe도 동작하지 않음', '할인, 후보 제거', LOC['settle'], 'Ablation (대조군 n=1, 통계 불가)'),
    ('FullReset', 'revD-fullreset (승컴)', 7, '0.9995', '0.25', '15 %', '25 %', 45, Y, Y, Y, Y, 'N (45개 전체 복원)', Y,
     '부분 복원 → 전체 복원', '나머지 전부', 'revD-src/conv_ftl.c reset_epoch #if ICAT_VARIANT == 7: active = WATGC_V2_ALLOWED (승컴 소스, 고컴 교차 확인)', 'Ablation'),
    ('NoDiscount', 'abl-nodiscount (승컴)', 4, '1.0 (Q16 65536)', '0.25', '15 %', '25 %', 45, 'N (γ = 1)', Y, Y, Y, Y, Y,
     '할인 (γ 0.9995 → 1)', '나머지 전부', 'ICAT_EXTRA=-DWATGC_V2_GAMMA_Q16=65536ULL (승컴 abl 사전 등록)', 'Ablation'),
    ('Random Selection', 'revA-random (고컴)', 9, '(계산되나 선택에 쓰지 않음)', '— (UCB 미사용)', '— (제거 없음)', '— (감지 없음)', 45, '—', N, N, N, '—', N,
     '학습 기반 선택 전체 (UCB, 제거, 정착, 감지)', '후보 45개, 판단 구간', LOC['random'], '기준선'),
    ('Elim10 / Elim25', 'revC-elim10, revC-elim25 (고컴)', 4, '0.9995', '0.25', '10 % / 25 %', '25 %', 45, Y, Y, Y, Y, Y, Y,
     '없음 (문턱만 변경)', '전부', 'ICAT_EXTRA=-DWATGC_V2_ELIM_Q16=6554ULL / 16384ULL (revC preregistration E6, objdump 1줄 차이)', 'Parameter Sensitivity'),
    ('Drift12.5', 'revE-drift12 (고컴)', 4, '0.9995', '0.25', '15 %', '12.5 %', 45, Y, Y, Y, Y, Y, Y,
     '없음 (문턱만 변경)', '전부', 'ICAT_EXTRA=-DWATGC_V2_DRIFT_Q16=8192ULL (revE build log, objdump 1줄 차이)', 'Parameter Sensitivity'),
    ('Drift50', 'drift50 (승컴)', 4, '0.9995', '0.25', '15 %', '50 %', 45, Y, Y, Y, Y, Y, Y,
     '없음 (문턱만 변경)', '전부', 'ICAT_EXTRA=-DWATGC_V2_DRIFT_Q16=32768ULL (승컴 result/drift50-20261126/preregistration.md:14)', 'Parameter Sensitivity'),
    ('Arms60', 'revC-arm60 (= revB-arm60 모듈, 고컴)', 6, '0.9995', '0.25', '15 %', '25 %', 60, Y, Y, Y, Y, Y, Y,
     '후보 축소 (k=2 제외) 해제', '전부', LOC['arms'], 'Parameter Sensitivity'),
]
with open(OUT / 'feature_matrix.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['Variant', 'run groups', 'ICAT_VARIANT', 'γ (discount)', 'C (UCB, WAF 단위)', 'Elimination threshold', 'Drift threshold', 'candidates',
                'Discounting', 'Elimination', 'Settling', 'Drift Detection', 'Partial Reset', 'Probe', '제거·변경한 기능', '유지한 기능', '변경 코드 위치', '분류'])
    for r in FEAT: w.writerow(r)
    w.writerow([]); w.writerow(['기호: ✓ 동작, ✗ 코드에서 끔, N (구조상) = 코드는 있으나 전제(정착)가 없어 실행되지 않음, — 해당 없음'])
    for k, v in LOC.items(): w.writerow([f'code:{k}', v])

# ------------------------------------------------------------------ kernel-log check of what was actually loaded + learner counters
TS = re.compile(r'^\[\s*(\d+\.\d+)\]')
INIT = re.compile(r'WATGC_V2 init .*?gamma_q16=(\d+) exploration_q16=(\d+) revA_variant=(\d+)')
SAMPLE = re.compile(r'WATGC_V2 sample ns=\d+ part=(\d+) .*?evaluated=(\d+) .*?best=(\d+) .*?settled=(\d) active=(\d+)')
SUMM = re.compile(r'WATGC_V2 summary ns=\d+ part=(\d+) .*?select=(\d+) eval_explore=(\d+) elim=(\d+) best_change=(\d+) reset=(\d+) learner_ns=(\d+) active=(\d+)')
GOCOM = ['revA-v4', 'revA-v1', 'revA-v2', 'revA-random', 'revB-v4', 'revB-noelim', 'revB-nosettle', 'revB-arm60',
         'revC-v4', 'revC-elim10', 'revC-elim25', 'revC-arm60', 'revE-v4', 'revE-noelim', 'revE-drift12']
EXPECT_VAR = {'v4': 4, 'v1': 1, 'v2': 2, 'random': 9, 'noelim': 3, 'nosettle': 5, 'arm60': 6, 'elim10': 4, 'elim25': 4, 'drift12': 4}
LC = []
for g in GOCOM:
    for r in runs(g):
        d = ROOT / r['원시 경로']; kl = (d / 'kernel.log').read_text(errors='replace').splitlines()
        beg = max(i for i, l in enumerate(kl) if re.search(r'mix-mixFYF-\S+ BEGIN', l)); kl = kl[beg:]
        aend = next(i for i, l in enumerate(kl) if re.search(r'phase=A END', l))
        inits = {m.groups() for l in kl if (m := INIT.search(l))}
        actA, settledA = {}, {}
        for l in kl[:aend]:
            if (m := SAMPLE.search(l)): actA[int(m[1])] = int(m[5]); settledA[int(m[1])] = int(m[4])
        summ = {}
        for l in kl:
            if (m := SUMM.search(l)): summ[int(m[1])] = list(map(int, m.groups()[1:]))
        exp = EXPECT_VAR[g.split('-', 1)[1]]
        cand = 60 if g.endswith('arm60') else 45
        row = dict(group=g, rep=r['rep'], raw_dir=r['원시 경로'],
                   loaded_variant=' '.join(sorted({x[2] for x in inits})), expected_variant=exp,
                   gamma_q16=' '.join(sorted({x[0] for x in inits})), exploration_q16=' '.join(sorted({x[1] for x in inits})),
                   variant_ok=inits and all(int(x[2]) == exp for x in inits) and all(x[0] == '65503' and x[1] == '16384' for x in inits),
                   candidates=cand,
                   active_end_phaseA_per_part=' '.join(str(actA.get(p, '')) for p in range(4)),
                   active_end_phaseA_mean=st.mean(actA.values()) if actA else '',
                   eliminated_share_end_phaseA=(1 - st.mean(actA.values()) / cand) if actA else '',
                   settled_parts_end_phaseA=sum(settledA.values()),
                   active_final_per_part=' '.join(str(summ[p][6]) for p in sorted(summ)),
                   elim_counter_sum=sum(v[2] for v in summ.values()), eval_explore_sum=sum(v[1] for v in summ.values()),
                   select_sum=sum(v[0] for v in summ.values()), best_change_sum=sum(v[3] for v in summ.values()),
                   reset_sum=sum(v[4] for v in summ.values()), learner_ms_ktime=sum(v[5] for v in summ.values()) / 1e6)
        LC.append(row)
with open(OUT / 'learner_counters_runs.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(LC[0])); w.writeheader(); w.writerows(LC)
for row in LC: CHECKS.append(dict(item=f"{row['group']} rep{row['rep']} kernel init variant/γ/C", this_script=f"{row['loaded_variant']}/{row['gamma_q16']}/{row['exploration_q16']}",
                                  reference=f"{row['expected_variant']}/65503/16384", reference_source='preregistration + conv_ftl.h', match=bool(row['variant_ok'])))
# cross-check against existing revC learner analysis (elim counter = elim_events_counter)
for r in rd(ROOT / 'result/revC-20261124-analysis/learner_runs.csv'):
    if r['smoke'] != 'False': continue
    g = {'revC-v4': 'revC-v4', 'revC-elim10': 'revC-elim10', 'revC-elim25': 'revC-elim25', 'revB-arm60': 'revC-arm60'}.get(r['policy'])
    x = next((y for y in LC if y['group'] == g and y['rep'] == r['rep']), None)
    if x:
        chk(f'{g} rep{r["rep"]} elim counter', x['elim_counter_sum'], r['elim_events_counter'], 'result/revC-20261124-analysis/learner_runs.csv', 0)
        chk(f'{g} rep{r["rep"]} final active', x['active_final_per_part'], r['final_active'], 'result/revC-20261124-analysis/learner_runs.csv')

# ------------------------------------------------------------------ group stats + contrasts (recomputed, asserted)
def gstat(g):
    out = {}
    for col in COLS:
        xs = vals(g, COLS[col]); d = desc(xs); out[col] = (xs, d)
        ref = GS.get((g, GS_KEY[col]))
        if ref and d['sd'] != '':
            chk(f'{g} {col} mean', d['mean'], ref['평균'], 'complete-results/all_group_stats.csv')
            chk(f'{g} {col} CI lo', d['ci_lo'], ref['95% CI 하한'], 'complete-results/all_group_stats.csv')
    return out


def contrast(g, c, col='waf'):
    a, b = vals(g, COLS[col]), vals(c, COLS[col])
    if len(a) < 3 or len(b) < 3: return None
    w = welch(a, b); ref = CT.get((f'{g} − {c}', col))
    holm = ''
    if ref:
        chk(f'{g} − {c} {col} Δ', w['delta'], ref['Δ'], 'complete-results/all_contrasts.csv')
        chk(f'{g} − {c} {col} CI lo', w['lo'], ref['Welch 95% CI 하한'], 'complete-results/all_contrasts.csv')
        chk(f'{g} − {c} {col} CI hi', w['hi'], ref['Welch 95% CI 상한'], 'complete-results/all_contrasts.csv')
        holm = ref['Holm p']; w['holm_k'] = ref['Holm 대비 수']
    w['holm'] = holm
    return w


fmt = lambda x, k=4: '' if x in ('', None) else f'{x:.{k}f}'
hp = lambda s: '' if s in ('', None) else ('<0.0001' if float(s) < 1e-4 else f'{float(s):.4f}')


def verdict(w):
    if w is None: return '통계 없음 (n<3)'
    sig = w['lo'] > 0 or w['hi'] < 0
    if not sig: return '구분되지 않음 (CI가 0 포함)'
    if w['holm'] != '' and float(w['holm']) >= 0.05: return f'차이 있음 (보정 전 CI 기준), Holm 후 경계 (p = {hp(w["holm"])})'
    return '차이 있음'


# Raw_Data
with open(OUT / 'raw_data_gocom.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['host', 'batch', 'group', 'policy', 'rep', 'host_pages', 'gc_pages', 'WAF total', 'WAF phase A', 'WAF phase B', 'WAF phase C', 'WAF C first 5 min',
                'valid (recheck)', 'module sha256', 'FIO seeds', 'icat_seed', 'raw dir'])
    for g in GOCOM + ['revA-arm47', 'revC-online']:
        for r in runs(g):
            v = VAL[(g, r['rep'])]
            w.writerow([r['호스트'], r['배치'], g, r['정책'], r['rep'], r['host_pages'], r['gc_pages'], r['전체 WAF'], r['단계 A'], r['단계 B'], r['단계 C'], r['C 첫 5분'],
                        r['유효'], r['모듈 sha256'], v['FIO seed'], v['icat_seed'], r['원시 경로']])

# Baseline (Figure 1, GoCom part): Random vs same-batch iCAT-v4; original iCAT vs same-batch iCAT-v4 (extra)
BASE = [('Random Selection', 'revA-random', 'revA-v4', 'revA-20261114'), ('iCAT (원 구현) [추가]', 'revC-online', 'revC-v4', 'revC-20261124')]
with open(OUT / 'baseline_figure1_gocom.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['Experiment', 'batch (host)', 'n', 'Baseline mean WAF', 'Baseline SD', 'Baseline 95% CI lo', 'Baseline 95% CI hi',
                'iCAT-v4 mean WAF (same batch)', 'iCAT-v4 SD', 'iCAT-v4 95% CI lo', 'iCAT-v4 95% CI hi',
                'ΔWAF (baseline − iCAT)', 'Welch 95% CI lo', 'Welch 95% CI hi', 'Welch df', 'p (unadj.)', 'Holm p', 'Holm family size',
                'Improvement (%) = (baseline − iCAT)/baseline ×100 [계산]', 'ΔWAF (%) = (baseline − iCAT)/iCAT ×100 [계산]', 'Normalized WAF = baseline/iCAT [계산]', 'verdict'])
    for name, g, c, b in BASE:
        sg, sc = gstat(g), gstat(c); dg, dc = sg['waf'][1], sc['waf'][1]; ww = contrast(g, c)
        w.writerow([name, f'{b} (고컴, Ryzen 5 3600XT)', '3 vs 3', fmt(dg['mean']), fmt(dg['sd']), fmt(dg['ci_lo']), fmt(dg['ci_hi']),
                    fmt(dc['mean']), fmt(dc['sd']), fmt(dc['ci_lo']), fmt(dc['ci_hi']), fmt(ww['delta']), fmt(ww['lo']), fmt(ww['hi']), fmt(ww['df'], 2),
                    f"{ww['p']:.2e}", hp(ww['holm']), ww.get('holm_k', ''),
                    fmt((dg['mean'] - dc['mean']) / dg['mean'] * 100, 2), fmt((dg['mean'] - dc['mean']) / dc['mean'] * 100, 2), fmt(dg['mean'] / dc['mean']), verdict(ww)])
    w.writerow([]); w.writerow(['오차 막대: 95 % CI (t 분포, df = 2). SD 열을 따로 둔다. Greedy GC 행은 승컴 batchG 담당이라 이 파일에 없다.'])
    w.writerow(['Improvement (%)는 평균의 비로 계산한 점추정값이며 CI가 없다. 판정은 ΔWAF의 Welch CI로 한다.'])

with open(OUT / 'baseline_data_gocom.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['group', 'policy', 'batch', 'metric', 'n', 'rep1', 'rep2', 'rep3', 'mean', 'SD', '95% CI lo', '95% CI hi'])
    for g in ('revA-v4', 'revA-random', 'revC-v4', 'revC-online'):
        sg = gstat(g)
        for col, (xs, d) in sg.items():
            w.writerow([g, runs(g)[0]['정책'], runs(g)[0]['배치'], COLS[col], d['n'], *[fmt(x, 5) for x in xs], fmt(d['mean'], 5), fmt(d['sd'], 5), fmt(d['ci_lo'], 5), fmt(d['ci_hi'], 5)])
    for col in ('waf_A', 'waf_B', 'waf_C', 'waf_C5'):
        for g, c in (('revA-random', 'revA-v4'), ('revC-online', 'revC-v4')):
            ww = contrast(g, c, col)
            w.writerow([f'{g} − {c}', 'Δ', '', COLS[col], '3 vs 3', '', '', '', fmt(ww['delta'], 5), '', fmt(ww['lo'], 5), fmt(ww['hi'], 5)])

# Ablation table (GoCom batches only; SeungCom rows come from SeungCom)
ABL = [('w/o Drift Detection', 'NoDrift (revA V1)', 'revA-v1', 'revA-v4'),
       ('w/o Elimination & Settling', 'NoElim+NoSettle (revA V2)', 'revA-v2', 'revA-v4'),
       ('w/o Elimination', 'NoElim', 'revE-noelim', 'revE-v4'),
       ('w/o Elimination (cross-check, control n=1)', 'NoElim (revB)', 'revB-noelim', 'revB-v4'),
       ('w/o Settling (control n=1)', 'NoSettle', 'revB-nosettle', 'revB-v4')]
FM = {r[0].split(' (')[0]: r for r in FEAT}
with open(OUT / 'ablation_table_gocom.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['X label (제안)', 'Variant', 'batch', 'Discounting', 'Elimination', 'Settling', 'Drift Detection', 'Partial Reset', 'Probe',
                '제거·변경한 기능', '유지한 기능', '변경 코드 위치', 'n (variant vs control)', 'variant mean WAF', 'variant SD', 'variant 95% CI lo', 'variant 95% CI hi',
                'control iCAT-v4 mean (same batch)', 'control SD', 'ΔWAF', 'Welch 95% CI lo', 'Welch 95% CI hi', 'ΔWAF (%) [계산]', 'Normalized WAF [계산]',
                'Holm p', 'Holm family size', 'verdict', 'ΔWAF phase C', 'phase C CI lo', 'phase C CI hi'])
    for lab, name, g, c in ABL:
        fm = FM[name.split(' (')[0]]
        sg, sc = gstat(g), gstat(c); dg, dc = sg['waf'][1], sc['waf'][1]
        ww = contrast(g, c); wc = contrast(g, c, 'waf_C')
        w.writerow([lab, name, runs(g)[0]['배치'], *fm[8:14], fm[14], fm[15], fm[16], f"{dg['n']} vs {dc['n']}", fmt(dg['mean']), fmt(dg['sd']), fmt(dg['ci_lo']), fmt(dg['ci_hi']),
                    fmt(dc['mean']), fmt(dc['sd']), fmt(dg['mean'] - dc['mean']), fmt(ww['lo']) if ww else '', fmt(ww['hi']) if ww else '',
                    fmt((dg['mean'] - dc['mean']) / dc['mean'] * 100, 2), fmt(dg['mean'] / dc['mean']),
                    hp(ww['holm']) if ww else '', ww.get('holm_k', '') if ww else '', verdict(ww),
                    fmt(wc['delta']) if wc else fmt(sg['waf_C'][1]['mean'] - sc['waf_C'][1]['mean']), fmt(wc['lo']) if wc else '', fmt(wc['hi']) if wc else ''])
    w.writerow([]); w.writerow(['revB 행은 대조군 iCAT-v4가 1회라 CI·판정이 없다. 논문 Figure 2에 넣지 않는다. FullReset, NoDiscount, 승컴 NoDrift/NoElim+NoSettle은 승컴 담당.'])

# Parameter sensitivity
ADPK = [('first_settle_s_latest_part', '첫 정착 시간 (단계 A 시작부터, 가장 늦은 파티션, s)'), ('C_detect_s', '단계 C 첫 감지 (s)'),
        ('C_restored_arms', '단계 C 재설정 때 복원된 후보 수'), ('C_resettle_from_reset_s_max', '단계 C 재정착 (재설정부터, 최대, s)'),
        ('C_explore_host_share', '단계 C 탐색 조합이 처리한 host 쓰기 비중')]


def param_file(fname, rows, note):
    with open(OUT / fname, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['setting', 'group', 'batch', 'status', 'n', 'mean WAF', 'SD', '95% CI lo', '95% CI hi', 'Δ vs same-batch default', 'Welch CI lo', 'Welch CI hi', 'Holm p', 'verdict',
                    'active candidates end of phase A (mean of 4 parts)', 'eliminated share end of phase A [실측, 1 − active/candidates]', 'elim counter (sum 4 parts)',
                    'eval_explore (sum)', 'resets (sum)', 'learner ktime ms'] + [a[1] for a in ADPK])
        for setting, g, c, status in rows:
            if g is None: w.writerow([setting, '', '', status]); continue
            d = gstat(g)['waf'][1]; ww = contrast(g, c) if c else None; lc = [x for x in LC if x['group'] == g]
            m = lambda k: fmt(st.mean(float(x[k]) for x in lc), 3) if lc and all(x[k] != '' for x in lc) else ''
            sd = lambda k: fmt(st.stdev(float(x[k]) for x in lc), 3) if len(lc) > 2 and all(x[k] != '' for x in lc) else ''
            adp = [(ADP.get((g, k)) or {}) for k, _ in ADPK]
            w.writerow([setting, g, runs(g)[0]['배치'], status, d['n'], fmt(d['mean']), fmt(d['sd']), fmt(d['ci_lo']), fmt(d['ci_hi']),
                        fmt(ww['delta']) if ww else '(기본값)', fmt(ww['lo']) if ww else '', fmt(ww['hi']) if ww else '', hp(ww['holm']) if ww else '', verdict(ww) if ww else '대조군',
                        f"{m('active_end_phaseA_mean')} ± {sd('active_end_phaseA_mean')}", f"{m('eliminated_share_end_phaseA')} ± {sd('eliminated_share_end_phaseA')}",
                        f"{m('elim_counter_sum')} ± {sd('elim_counter_sum')}", f"{m('eval_explore_sum')} ± {sd('eval_explore_sum')}", f"{m('reset_sum')} ± {sd('reset_sum')}",
                        f"{m('learner_ms_ktime')} ± {sd('learner_ms_ktime')}"]
                       + [f"{float(a['평균']):.3f} ± {float(a['SD']):.3f}" if a.get('SD') else (a.get('개별 값', '') + ' (통계 없음)' if a else '') for a in adp])
        w.writerow([])
        for line in note: w.writerow([line])


param_file('param_elimination_threshold.csv',
           [('10 %', 'revC-elim10', 'revC-v4', '측정 (revC, n=3)'), ('15 % (기본)', 'revC-v4', None, '측정 (revC 대조군, n=3)'),
            ('25 %', 'revC-elim25', 'revC-v4', '측정 (revC, n=3)'), ('off (제거 없음)', 'revE-noelim', 'revE-v4', '측정 (revE, 다른 배치. 같은 배치 대조군은 revE-v4)')],
           ['문턱(threshold)은 "최상위 대비 평균 WAF가 몇 % 넘게 나쁘면 제거"하는 기준이다. 실제로 제거된 후보 비율과 다르다.',
            'eliminated share = 1 − (단계 A 끝 active 후보 수 / 후보 수). probe가 이웃을 다시 후보로 넣으므로 제거 누적 횟수(elim counter)와 다르다.',
            'elim counter는 커널 summary의 n_elim 합계(probe로 재편입된 arm의 재제거 포함)다. 기존 revC 보고서의 "제거 횟수 45/30/23"은 active가 줄어든 판단 구간의 수로, 정의가 다르다.',
            '측정한 문턱은 10, 15, 25 %와 off뿐이다. 그 외 값은 실행하지 않았다.'])
param_file('param_discount_factor.csv',
           [('γ = 0.9995 (기본)', 'revA-v4', None, '측정 (모든 iCAT-v4 대조군)'), ('γ = 0.90', None, None, '실행하지 않음'), ('γ = 0.95', None, None, '실행하지 않음'),
            ('γ = 0.99', None, None, '실행하지 않음'), ('γ = 1.0 (할인 없음)', None, None, '승컴 abl-nodiscount n=3 (승컴 담당): Δ −0.004 [−0.064, +0.057], 구분되지 않음')],
           ['커널 로그 검사 (이 PC의 result, result_e1, result_e2 전체 + 승컴 리비전 배치 7개): WATGC_V2 init 줄 462,668개 중 gamma_q16은 65503 (0.9995) 또는 65536 (1.0, NoDiscount)뿐이다.',
            'γ 0.90 / 0.95 / 0.99는 어떤 배치에서도 실행하지 않았다. 민감도 그래프를 만들 수 없다.'])
param_file('param_exploration_C.csv',
           [('C = 0.25 (기본)', 'revA-v4', None, '측정 (모든 iCAT-v4 대조군)'), ('C = 0.50', None, None, '실행하지 않음'), ('C = 0.75', None, None, '실행하지 않음')],
           ['C는 UCB 보너스 항의 계수다 (WAF 단위, conv_ftl.c:436). 무작위 선택 확률이 아니다.',
            '커널 로그 전수 검사: exploration_q16은 모든 run에서 16384 (0.25)뿐이다. C 민감도 실험은 없다.'])
param_file('param_other_gocom.csv',
           [('Drift 25 % (기본)', 'revE-v4', None, '측정 (revE 대조군)'), ('Drift 12.5 %', 'revE-drift12', 'revE-v4', '측정 (revE, n=3)'),
            ('Drift 50 %', None, None, '승컴 batchG drift50 (승컴 담당): Δ +0.018 [−0.045, +0.081], 구분되지 않음. 다른 호스트라 이 표의 12.5 %와 한 곡선으로 잇지 않는다'),
            ('45 arms (기본)', 'revC-v4', None, '측정 (revC 대조군)'), ('60 arms', 'revC-arm60', 'revC-v4', '측정 (revC, n=3)')],
           ['Drift 문턱과 후보 수는 기능을 없애지 않고 값만 바꾼 실험이다. Ablation이 아니라 Parameter Sensitivity로 분류한다.',
            '변화 감지 15 %는 실행하지 않았다.'])

with open(OUT / 'verification_gocom.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['item', 'this_script', 'reference', 'reference_source', 'match']); w.writeheader(); w.writerows(CHECKS)
bad = [c for c in CHECKS if not c['match']]
print(f'checks {len(CHECKS)}, mismatches {len(bad)}')
for c in bad[:20]: print('MISMATCH', c)
print('files:', sorted(p.name for p in OUT.iterdir()))
