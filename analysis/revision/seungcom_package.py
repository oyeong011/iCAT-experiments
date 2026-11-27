#!/usr/bin/env python3
"""11-27 승컴 package for the final revision Excel (집컴 builds iCAT_Revision_Final.xlsx).
    python3 -I -B analysis/revision/seungcom_package.py
Inputs (no new experiments):
  result/final-validation-20261127/final_statistical_validation.csv  (WAF stats recomputed from raw logs)
  result/final-validation-20261127/final_raw_data_validation.csv     (per-run WAF, validity, seeds)
  <run>/kernel.log                                                    (WATGC_V2 learner lines)
  scratchpad objdump comparison results are recorded by hand in module_verification.csv (see report).
Every variant is compared only with the iCAT-v4 of its own batch. Nothing is pooled across batches."""
import csv, re, statistics as st, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V = ROOT / 'result/final-validation-20261127'
OUT = ROOT / (sys.argv[1] if len(sys.argv) > 1 else 'result/final-revision-seungcom')
OUT.mkdir(exist_ok=True)
S = list(csv.DictReader(open(V / 'final_statistical_validation.csv')))
RAW = [r for r in csv.DictReader(open(V / 'final_raw_data_validation.csv')) if r['role'] == 'main']
D = {(r['batch'], r['policy']): r for r in S if r['kind'] == 'descriptive' and r['metric'] == 'total_waf'}
C = {r['treatment']: r for r in S if r['kind'] == 'contrast' and r['metric'] == 'total_waf' and not r['family'].startswith(('indirect', 'secondary', 'v4-repro'))}

def write(name, rows):
    with open(OUT / name, 'w', newline='') as f:
        w = csv.DictWriter(f, list(rows[0]), lineterminator='\n'); w.writeheader(); w.writerows(rows)

def sig(c):
    h = float(c['holm_p_family'])
    w = float(c['welch_p'])
    if h < 0.05: return f"유의 (Holm p {h:.2g})"
    return f"보정 전 p {w:.2g}, 보정 후 유의하지 않음 (Holm p {h:.2g})" if w < 0.05 else f"차이 확인 못 함 (Welch p {w:.2g}, Holm p {h:.2g})"

# ---- source-verified feature matrix (revD-src/conv_ftl.c, conv_ftl.h; sources.sha256 OK) ----
# columns: Discounting, Elimination, Settling, Drift detection, Partial reset, Probe
LOC = {'disc': 'conv_ftl.c:317-321,584-586 (watgc_v2_discount, GAMMA_Q16 conv_ftl.h:60-61)',
       'elim': 'conv_ftl.c:620-636 (ICAT_VARIANT != 2 && != 3; ELIM_Q16 conv_ftl.h:38-39)',
       'settle': 'conv_ftl.c:540-551 (ICAT_VARIANT != 2,5,9)', 'drift': 'conv_ftl.c:567-579 (ICAT_VARIANT != 1, gated on settled; DRIFT_Q16 conv_ftl.h:74-75)',
       'reset': 'conv_ftl.c:486-490 (VARIANT 7 -> WATGC_V2_ALLOWED, else watgc_v2_grow)', 'probe': 'conv_ftl.c:637-657 (only reached when settled)'}
VAR = [  # key, batch, policy, label, x-axis label, flags, feature marks, removed, kept, code
    ('V4', 'revD-20261124', 'revD-v4', 'iCAT-v4 (revD 대조군)', '', 'ICAT_VARIANT=4', ('✓', '✓', '✓', '✓', '✓', '✓'), '—', '전부', ''),
    ('NoDrift', 'revD-20261124', 'revD-nodrift', 'NoDrift', 'w/o Drift Detection', 'ICAT_VARIANT=1', ('✓', '✓', '✓', '✗', 'N/A (리셋 없음)', '✓'),
     '변화 감지 블록을 건너뜀 → 리셋이 일어나지 않음', '할인, 후보 제거, 정착, probe', LOC['drift']),
    ('FullReset', 'revD-20261124', 'revD-fullreset', 'FullReset', 'Full Reset (instead of partial)', 'ICAT_VARIANT=7', ('✓', '✓', '✓', '✓', '✗ (45개 전부 복원)', '✓'),
     '리셋 때 후보를 살아남은 후보+이웃이 아니라 45개 전부로 복원', '할인, 후보 제거, 정착, 변화 감지, probe', LOC['reset']),
    ('V4', 'revision-additional-ablation', 'abl-v4', 'iCAT-v4 (abl 대조군)', '', 'ICAT_VARIANT=4', ('✓', '✓', '✓', '✓', '✓', '✓'), '—', '전부', ''),
    ('NoDiscount', 'revision-additional-ablation', 'abl-nodiscount', 'NoDiscount', 'w/o Discounting', 'ICAT_VARIANT=4 ICAT_EXTRA=-DWATGC_V2_GAMMA_Q16=65536ULL',
     ('✗ (γ=1)', '✓', '✓', '✓', '✓', '✓'), 'γ = 65536/65536 = 1 → watgc_v2_discount(v) = (v>>16)*65536 + ((v&0xFFFF)*65536>>16) = v (항등)', '나머지 전부', LOC['disc']),
    ('OffBundle', 'revision-additional-ablation', 'abl-off-elim-settle-drift-probe', 'NoElim+NoSettle', 'w/o Elimination & Settling',
     'ICAT_VARIANT=2', ('✓', '✗', '✗', '✗ (정착이 없어 발동 불가)', 'N/A (리셋 없음)', '✗ (정착이 없어 도달 불가)'),
     '후보 제거, 정착을 끔. 변화 감지와 probe는 정착 상태에서만 동작하므로 구조상 함께 꺼짐. 고컴 revA V2와 같은 정책 (VARIANT 2)', '할인, UCB 탐색', LOC['elim'] + '; ' + LOC['settle']),
]
abl = []
for key, b, p, label, xl, flags, marks, removed, kept, code in VAR:
    d = D[(b, p)]; c = C.get(f'{b}/{p}')
    v4 = D[(b, 'revD-v4' if b.startswith('revD') else 'abl-v4')]
    row = {'variant': label, 'x_axis_label': xl, 'batch': b, 'host': d['host'], 'build_flags': flags,
           **dict(zip(('discounting', 'elimination', 'settling', 'drift_detection', 'partial_reset', 'probe'), marks)),
           'removed_or_changed': removed, 'kept': kept, 'code_location': code, 'n': d['n'], 'mean_waf': f"{float(d['mean']):.4f}",
           'sd': f"{float(d['sd']):.4f}", 'ci95_lo': f"{float(d['ci95_lo']):.4f}", 'ci95_hi': f"{float(d['ci95_hi']):.4f}",
           'same_batch_v4_waf': f"{float(v4['mean']):.4f}", 'delta_waf': '', 'delta_ci95_lo': '', 'delta_ci95_hi': '', 'delta_pct': '',
           'normalized_waf': f"{float(d['mean']) / float(v4['mean']):.4f}", 'welch_p': '', 'paired_p': '', 'holm_p': '', 'holm_family': '', 'significance': '기준'}
    if c:
        row.update(delta_waf=f"{float(c['diff']):+.4f}", delta_ci95_lo=f"{float(c['ci95_lo']):+.4f}", delta_ci95_hi=f"{float(c['ci95_hi']):+.4f}",
                   delta_pct=f"{100 * float(c['diff']) / float(v4['mean']):+.2f}", welch_p=f"{float(c['welch_p']):.3g}", paired_p=f"{float(c['paired_p']):.3g}",
                   holm_p=f"{float(c['holm_p_family']):.3g}", holm_family=f"{c['family']} ({c['holm_family_size']}: 2대비 × {{전체, 단계 C}})", significance=sig(c))
    abl.append(row)
write('ablation_table.csv', abl)

# ---- baseline: Greedy GC vs same-batch iCAT-v4 (batchG) ----
g, v = D[('greedygc-20261126', 'greedygc')], D[('batchG-20261126', 'bg-v4')]; c = C['greedygc-20261126/greedygc']
reps = lambda b, p: ' / '.join(f"{float(r['total_waf']):.4f}" for r in sorted(RAW, key=lambda r: r['rep']) if r['batch'] == b and r['policy'] == p)
write('baseline_greedygc.csv', [{
    'experiment': 'Greedy GC', 'workload': 'mixFYF 90 min', 'host': '승컴 i7-7700', 'baseline_batch': 'greedygc-20261126', 'icat_batch': 'batchG-20261126 (같은 큐에서 번갈아 실행)',
    'n_each': 3, 'baseline_reps': reps('greedygc-20261126', 'greedygc'), 'icat_reps': reps('batchG-20261126', 'bg-v4'),
    'baseline_mean': f"{float(g['mean']):.4f}", 'baseline_sd': f"{float(g['sd']):.4f}", 'baseline_ci95': f"[{float(g['ci95_lo']):.4f}, {float(g['ci95_hi']):.4f}]",
    'icat_mean': f"{float(v['mean']):.4f}", 'icat_sd': f"{float(v['sd']):.4f}", 'icat_ci95': f"[{float(v['ci95_lo']):.4f}, {float(v['ci95_hi']):.4f}]",
    'improvement_pct': f"{100 * (float(g['mean']) - float(v['mean'])) / float(g['mean']):.2f}",
    'improvement_definition': '(Baseline − iCAT) / Baseline × 100 = iCAT의 WAF 감소율',
    'delta_waf_baseline_minus_icat': f"{float(c['diff']):.4f}", 'delta_ci95': f"[{float(c['ci95_lo']):.4f}, {float(c['ci95_hi']):.4f}]",
    'welch_p': f"{float(c['welch_p']):.3g}", 'paired_p': f"{float(c['paired_p']):.3g}", 'holm_p': f"{float(c['holm_p_family']):.3g}",
    'error_bar': '95 % CI (t, df=2)', 'note': 'FIO 쓰기 p99 지연은 Greedy GC가 더 낮다 (단계 C −124 µs, batchG conclusion.md). WAF만의 비교다.'}])

# ---- per-run raw data (승컴 runs in this package) ----
SCOPE = {'revD-20261124', 'revision-additional-ablation', 'batchG-20261126', 'drift50-20261126', 'greedygc-20261126'}
write('raw_data.csv', [{k: r[k] for k in ('run_id', 'host', 'batch', 'policy', 'rep', 'raw_path', 'module_sha256', 'module_sha_matches_registered', 'fio_seeds_first_phase',
                                          'icat_seed', 'start', 'host_pages', 'gc_pages', 'total_waf', 'A_waf', 'B_waf', 'C_waf', 'C5_waf', 'ycsb_success', 'valid')}
                       for r in RAW if r['batch'] in SCOPE])

# ---- learner metrics from kernel.log (cumulative counters; measurement = after the last 4 init lines) ----
TS = r'^\[\s*([\d.]+)\]'
def learner(path):
    kl = (ROOT / path / 'kernel.log').read_text(errors='replace').splitlines()
    t0 = float(re.match(TS, [l for l in kl if 'WATGC_V2 init' in l][-1])[1])
    samp, sett, rst, summ = {}, {}, {}, {}
    for l in kl:
        if 'WATGC_V2 sample' in l:
            m = dict(re.findall(r'(\w+)=(\d+)', l)); samp[(m['part'], int(m['window']))] = m
        elif 'WATGC_V2 settled' in l:
            m = re.search(r'part=(\d) .*window=(\d+)', l); sett.setdefault(m[1], []).append((int(m[2]), float(re.match(TS, l)[1])))
        elif 'WATGC_V2 reset' in l:
            m = re.search(r'part=(\d) .*window=(\d+)', l); rst.setdefault(m[1], []).append((int(m[2]), float(re.match(TS, l)[1])))
        elif 'WATGC_V2 summary' in l:
            m = dict(re.findall(r'(\w+)=(\d+)', l)); summ[m['part']] = m
    parts = []
    for p in sorted(summ):
        s = summ[p]; fs = sett.get(p, [None])[0]
        pre = int(samp[(p, fs[0])]['eval_explore']) if fs else None
        re_cost = []
        for w, ts in rst.get(p, []):
            nxt = next(((w2, t2) for w2, t2 in sett.get(p, []) if w2 > w), None)
            re_cost.append((nxt[0] - w, nxt[1] - ts) if nxt else None)
        parts.append({'windows': int(s['windows']), 'select': int(s['select']), 'eval_explore': int(s['eval_explore']), 'eval_explore_pre_settle': pre,
                      'elim_events': int(s['elim']), 'best_change': int(s['best_change']), 'reset': int(s['reset']), 'settle_events': len(sett.get(p, [])),
                      'active_final': int(s['active']), 'active_at_first_settle': int(samp[(p, fs[0])]['active']) if fs else None,
                      'first_settle_window': fs[0] if fs else None, 'first_settle_s': fs[1] - t0 if fs else None, 'reexplore': re_cost})
    return parts

LP = [('revD-20261124', 'revD-v4'), ('revD-20261124', 'revD-nodrift'), ('revD-20261124', 'revD-fullreset'),
      ('revision-additional-ablation', 'abl-v4'), ('revision-additional-ablation', 'abl-nodiscount'), ('revision-additional-ablation', 'abl-off-elim-settle-drift-probe'),
      ('batchG-20261126', 'bg-v4'), ('drift50-20261126', 'drift50')]
mean = lambda xs: st.mean(xs) if xs else ''
lrun, lpol = [], []
for b, p in LP:
    runs = []
    for r in sorted((r for r in RAW if r['batch'] == b and r['policy'] == p), key=lambda r: r['rep']):
        ps = learner(r['raw_path'])
        assert len(ps) == 4, r['raw_path']
        rc = [x for q in ps for x in q['reexplore']]
        got = lambda k: [q[k] for q in ps if q[k] is not None]
        row = {'batch': b, 'policy': p, 'rep': r['rep'], 'partitions': 4, 'partitions_settled': sum(q['settle_events'] > 0 for q in ps),
               **{f'{k}_mean_per_part': mean(got(k)) for k in ('windows', 'select', 'eval_explore', 'eval_explore_pre_settle', 'elim_events', 'best_change',
                                                                'reset', 'settle_events', 'active_at_first_settle', 'active_final', 'first_settle_window', 'first_settle_s')},
               'resets_total': len(rc), 'resets_resettled': sum(x is not None for x in rc), 'resets_censored': sum(x is None for x in rc),
               'reexplore_windows_mean': mean([x[0] for x in rc if x]), 'reexplore_s_mean': mean([x[1] for x in rc if x])}
        runs.append(row); lrun.append(row)
    agg = {'batch': b, 'policy': p, 'n_runs': len(runs)}
    for k in runs[0]:
        if k.endswith(('_mean_per_part', '_mean')) or k in ('partitions_settled', 'resets_total', 'resets_resettled', 'resets_censored'):
            xs = [x[k] for x in runs if x[k] != '']
            agg[k] = f'{st.mean(xs):.2f}' if xs else '해당 없음'
            if len(xs) == 3 and k.endswith('_mean_per_part'): agg[k.replace('_mean_per_part', '_sd_between_runs')] = f'{st.stdev(xs):.2f}'
    lpol.append(agg)
for r in lrun:
    for k, x in r.items():
        if isinstance(x, float): r[k] = f'{x:.2f}'
write('learner_metrics_by_run.csv', lrun)
write('learner_metrics_by_policy.csv', lpol)

# ---- parameter sensitivity coverage (source constants across every tree; revision runs) ----
dr = C['drift50-20261126/drift50']
write('parameter_sensitivity.csv', [
    {'parameter': 'Discount factor γ', 'default': '0.99949646 (GAMMA_Q16 65503, conv_ftl.h:61)', 'tested_on_seungcom': 'γ = 1.0 (NoDiscount, abl 배치)',
     'requested_but_not_run': '0.90, 0.95, 0.99 — 승컴 미실험. 고컴 revF-20261127에서 각 1회 실행 중 (n=1, 통계 없음)', 'result': f"NoDiscount − V4 {float(C['revision-additional-ablation/abl-nodiscount']['diff']):+.4f}, Holm p 1 (차이 확인 못 함)",
     'note': 'γ=1 끝점 하나뿐이라 민감도 곡선이 아니다. 기본값은 0.99가 아니라 0.9995다'},
    {'parameter': 'Exploration coefficient C (UCB)', 'default': '0.25 WAF 단위 (UCB_C_Q16 16384, conv_ftl.h:63)', 'tested_on_seungcom': '없음',
     'requested_but_not_run': '0.50, 0.75 — 승컴 미실험 (승컴 소스는 16384 고정). 고컴 revF-20261127에서 각 1회 실행 중', 'result': '승컴 자료 없음 → 고컴 revF (n=1)',
     'note': 'C는 UCB 보너스의 크기(WAF 단위)이고, 무작위 선택 확률이 아니다'},
    {'parameter': 'Elimination threshold', 'default': '15 % (ELIM_Q16 9830, conv_ftl.h:39)', 'tested_on_seungcom': '15 %만 (모든 승컴 리비전 배치)',
     'requested_but_not_run': '10 %, 25 %는 고컴 revC-20261124에 있음', 'result': '승컴 자료 없음 → 고컴 revC 참조',
     'note': '문턱(평균이 best보다 몇 % 나쁘면 제거)과 실제 제거된 후보 비율은 다르다. 제거 비율은 learner_metrics의 active_at_first_settle로 본다'},
    {'parameter': 'Drift threshold', 'default': '25 % (DRIFT_Q16 16384, conv_ftl.h:75), 3구간 연속', 'tested_on_seungcom': '50 % (drift50, batchG 같은 큐)',
     'requested_but_not_run': '12.5 %는 고컴 revE-20261125', 'result': f"drift50 − V4 {float(dr['diff']):+.4f} [{float(dr['ci95_lo']):+.4f}, {float(dr['ci95_hi']):+.4f}], Holm p {float(dr['holm_p_family']):.2g} (차이 확인 못 함)",
     'note': 'Ablation이 아니라 Parameter Sensitivity. V4 리셋의 편차가 모두 50 %를 넘어서 25 %와 50 %가 다르게 동작할 기회가 거의 없었다'},
])
for r in abl: print(r['variant'][:22], r['mean_waf'], r['delta_waf'], r['delta_pct'], r['holm_p'], r['significance'])
for r in lpol: print(r['policy'][:16], r['partitions_settled'], r['first_settle_s_mean_per_part'], r['active_at_first_settle_mean_per_part'], r['resets_total'], r['resets_censored'], r['reexplore_windows_mean'], r['eval_explore_mean_per_part'])
