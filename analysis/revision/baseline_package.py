#!/usr/bin/env python3
"""11-27 baseline comparison package (Random / Online Greedy / Greedy GC vs matched iCAT-v4), total WAF only.
    python3 -I -B analysis/revision/baseline_package.py
Reads ONLY result/final-validation-20261127/final_statistical_validation.csv (recomputed from raw logs, 0 mismatch vs 고컴/집컴).
No pooling across batches or hosts; Random and Greedy are never compared with each other."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'result/final-baseline-comparison'
OUT.mkdir(exist_ok=True)
S = list(csv.DictReader(open(ROOT / 'result/final-validation-20261127/final_statistical_validation.csv')))
D = {(r['batch'], r['policy']): r for r in S if r['kind'] == 'descriptive' and r['metric'] == 'total_waf'}
C = {(r['control'], r['treatment']): r for r in S if r['kind'] == 'contrast' and r['metric'] == 'total_waf'}

# (label, batch, policy, matched V4 key or None, direct?, graph label, interpretation, note)
ROWS = [
    ('iCAT-v4 (revA 대조군)', 'revA-20261114', 'revA-v4', None, '', 'iCAT-v4 (고컴 revA)', '',
     'Random의 같은 배치 대조군. 고컴 Ryzen 3600XT'),
    ('Random Selection', 'revA-20261114', 'revA-random', 'revA-20261114/revA-v4', 'yes', 'Random',
     'Random이 V4보다 WAF가 높다 (V4가 낫다)',
     '같은 배치·같은 seed 직접 비교. Holm 가족 = revA 3대비 × {전체, C} = 6 (전체만 3이면 Holm p 4.7e-6, 판정 같음)'),
    ('iCAT-v4 (revD 대조군)', 'revD-20261124', 'revD-v4', None, '', 'iCAT-v4 (승컴 revD)', '',
     'Online Greedy의 간접 비교 기준. 승컴 i7-7700'),
    ('Online Greedy', 'greedy-20261125', 'greedy-online', 'revD-20261124/revD-v4', 'no', 'Online Greedy',
     '차이를 확인하지 못했다 (간접 비교)',
     '다른 배치 (greedy-20261125 배치에 V4 없음). 같은 호스트·같은 부하. Holm 가족 없음. abl-v4 기준으로도 −0.009, p .63'),
    ('iCAT-v4 (batchG 대조군)', 'batchG-20261126', 'bg-v4', None, '', 'iCAT-v4 (승컴 batchG)', '',
     'Greedy GC의 같은 배치 대조군. 승컴 i7-7700'),
    ('Greedy GC', 'greedygc-20261126', 'greedygc', 'batchG-20261126/bg-v4', 'yes', 'Greedy GC',
     'Greedy GC가 V4보다 WAF가 높다 (V4가 낫다)',
     '같은 큐에서 번갈아 실행한 직접 비교, 같은 seed. Holm 가족 = batchG 2대비 × {전체, C} = 4. FIO 쓰기 p99 지연은 Greedy GC가 낮다 (단계 C −124 µs)'),
]

f3 = lambda x: f'{float(x):.3f}' if x not in ('', None) else ''
pfmt = lambda x: (f'{float(x):.2g}' if float(x) < 0.01 else f'{float(x):.3f}') if x not in ('', None) else ''
base, graph = [], []
for label, batch, pol, ctl, direct, glabel, interp, note in ROWS:
    d = D[(batch, pol)]
    row = {'policy': label, 'host': d['host'], 'batch': batch, 'n': d['n'], 'direct_comparison_to_v4': direct or '(대조군)',
           'mean_waf': f3(d['mean']), 'sd_waf': f3(d['sd']), 'ci95_lo': f3(d['ci95_lo']), 'ci95_hi': f3(d['ci95_hi']),
           'matched_v4': ctl or '', 'delta_vs_matched_v4': '', 'delta_pct': '', 'delta_ci95_lo': '', 'delta_ci95_hi': '',
           'p_value': '', 'holm_p': '', 'hedges_g': '', 'interpretation': interp or '기준', 'note': note}
    if ctl:
        c = C[(ctl, f'{batch}/{pol}')]
        v4 = float(D[tuple(ctl.split('/'))]['mean'])
        row.update(delta_vs_matched_v4=f'{float(c["diff"]):+.3f}', delta_pct=f'{100 * float(c["diff"]) / v4:+.1f}',
                   delta_ci95_lo=f3(c['ci95_lo']), delta_ci95_hi=f3(c['ci95_hi']), p_value=pfmt(c['welch_p']),
                   holm_p=pfmt(c['holm_p_family']) or '해당 없음 (간접)', hedges_g=f'{float(c["hedges_g"]):.2f}')
    base.append(row)
    graph.append({'graph': 'absolute_waf', 'label': glabel, 'host': d['host'], 'batch': batch, 'n': d['n'],
                  'value': row['mean_waf'], 'err_lo': row['ci95_lo'], 'err_hi': row['ci95_hi'], 'comparison': '', 'annotation': ''})
for r, g in zip(base, graph):
    if r['matched_v4']:
        sig = '' if r['direct_comparison_to_v4'] == 'no' else (', Holm p ' + r['holm_p'])
        graph.append({'graph': 'delta_vs_v4', 'label': g['label'], 'host': r['host'], 'batch': r['batch'], 'n': r['n'],
                      'value': r['delta_vs_matched_v4'], 'err_lo': r['delta_ci95_lo'], 'err_hi': r['delta_ci95_hi'],
                      'comparison': '직접 (같은 배치)' if r['direct_comparison_to_v4'] == 'yes' else '간접 (다른 배치)',
                      'annotation': f"{r['delta_vs_matched_v4']} ({r['delta_pct']} %), 95 % CI [{r['delta_ci95_lo']}, {r['delta_ci95_hi']}]{sig}"
                                    + ('' if r['direct_comparison_to_v4'] == 'yes' else ', 간접 비교·차이 확인 못 함')})

for name, rows in (('baseline_comparison.csv', base), ('graph_ready_values.csv', graph)):
    with open(OUT / name, 'w', newline='') as f:
        w = csv.DictWriter(f, list(rows[0]), lineterminator='\n'); w.writeheader(); w.writerows(rows)

# self-check: CIs of direct contrasts exclude 0, the indirect one contains it
assert all(float(r['delta_ci95_lo']) > 0 for r in base if r['direct_comparison_to_v4'] == 'yes')
assert all(float(r['delta_ci95_lo']) < 0 < float(r['delta_ci95_hi']) for r in base if r['direct_comparison_to_v4'] == 'no')
for r in base: print(*(r[k] for k in ('policy', 'host', 'mean_waf', 'ci95_lo', 'ci95_hi', 'delta_vs_matched_v4', 'delta_pct', 'delta_ci95_lo', 'delta_ci95_hi', 'p_value', 'holm_p', 'hedges_g')), sep=' | ')
