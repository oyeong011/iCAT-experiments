#!/usr/bin/env python3
"""11-27 승컴 final: run-config check (kernel init lines) + runtime feature-off check (summary/sample/reset lines) + feature_matrix.csv.
    python3 -I -B analysis/revision/seungcom_package.py result/seungcom-revision-final   (WAF tables, learner metrics)
    python3 -I -B analysis/revision/seungcom_final.py                                     (this file)
Line numbers refer to revD-src @ b62127da2 (clean; sources.sha256 OK)."""
import csv, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'result/seungcom-revision-final'
RAW = [r for r in csv.DictReader(open(ROOT / 'result/final-validation-20261127/final_raw_data_validation.csv')) if r['role'] == 'main']

# policy -> (label, expected VARIANT, gamma_q16, exploration_q16, build flags)
EXP = {'revD-v4': ('iCAT-v4 (revD)', 4, 65503, 16384, 'ICAT_VARIANT=4'),
       'revD-nodrift': ('NoDrift', 1, 65503, 16384, 'ICAT_VARIANT=1'),
       'revD-fullreset': ('FullReset', 7, 65503, 16384, 'ICAT_VARIANT=7'),
       'abl-v4': ('iCAT-v4 (abl)', 4, 65503, 16384, 'ICAT_VARIANT=4'),
       'abl-nodiscount': ('NoDiscount', 4, 65536, 16384, 'ICAT_VARIANT=4 ICAT_EXTRA=-DWATGC_V2_GAMMA_Q16=65536ULL'),
       'abl-off-elim-settle-drift-probe': ('NoElim+NoSettle', 2, 65503, 16384, 'ICAT_VARIANT=2'),
       'bg-v4': ('iCAT-v4 (batchG)', 4, 65503, 16384, 'ICAT_VARIANT=4'),
       'drift50': ('drift50 (parameter)', 4, 65503, 16384, 'ICAT_VARIANT=4 ICAT_EXTRA=-DWATGC_V2_DRIFT_Q16=32768ULL')}

def kv(l): return dict(re.findall(r'(\w+)=(\d+)', l))

rows = []
for r in sorted((r for r in RAW if r['policy'] in EXP), key=lambda r: (r['batch'], r['policy'], r['rep'])):
    label, var, gq, cq, flags = EXP[r['policy']]
    kl = (ROOT / r['raw_path'] / 'kernel.log').read_text(errors='replace').splitlines()
    init = [kv(l) for l in kl if 'WATGC_V2 init' in l][-4:]          # measurement-start init (insmod init comes first)
    summ = [kv(l) for l in kl if 'WATGC_V2 summary' in l]
    samp = {(m['part'], m['window']): m for m in (kv(l) for l in kl if 'WATGC_V2 sample' in l)}
    resets = [kv(l) for l in kl if 'WATGC_V2 reset' in l]
    after = [int(samp[(x['part'], x['window'])]['active']) for x in resets if (x['part'], x['window']) in samp]
    cfg_ok = (len(init) == 4 and sorted(i['part'] for i in init) == list('0123') and
              all(int(i['revA_variant']) == var and int(i['gamma_q16']) == gq and int(i['exploration_q16']) == cq and int(i['candidates']) == 45 for i in init))
    S = lambda k: [int(s[k]) for s in summ]
    pol = r['policy']
    if pol == 'revD-nodrift':
        rt, rt_ok = f"reset={S('reset')}", sum(S('reset')) == 0
    elif pol == 'abl-off-elim-settle-drift-probe':
        rt = f"elim={S('elim')} active={S('active')} settled={S('settled')} reset={S('reset')}"
        rt_ok = sum(S('elim')) == 0 and set(S('active')) == {45} and sum(S('settled')) == 0 and sum(S('reset')) == 0
    elif pol == 'revD-fullreset':
        rt, rt_ok = f"resets={len(resets)}, active right after each reset={after}", bool(after) and set(after) == {45}
    elif pol == 'abl-nodiscount':
        rt, rt_ok = 'gamma_q16=65536 in init (discount is identity; no separate runtime counter)', cfg_ok
    elif pol == 'drift50':
        rt, rt_ok = f"resets={len(resets)}; drift threshold is not printed in init -> verified by objdump only (shl $0xf vs $0xe)", None
    else:
        rt, rt_ok = f"resets={len(resets)}, active right after each reset={after} (partial: < 45)", bool(after) and max(after) < 45
    rows.append({'run_id': r['run_id'], 'batch': r['batch'], 'policy': pol, 'label': label, 'rep': r['rep'], 'raw_path': r['raw_path'],
                 'module_sha256': r['module_sha256'], 'module_sha_matches_registered': r['module_sha_matches_registered'], 'build_flags': flags,
                 'init_lines_after_measure_start': len(init), 'init_variant': sorted({i['revA_variant'] for i in init}),
                 'init_gamma_q16': sorted({i['gamma_q16'] for i in init}), 'init_exploration_q16': sorted({i['exploration_q16'] for i in init}),
                 'expected': f'VARIANT={var} gamma_q16={gq} exploration_q16={cq}', 'config_ok': cfg_ok,
                 'runtime_evidence': rt, 'runtime_ok': '검증 불가 (objdump만)' if rt_ok is None else rt_ok,
                 'total_waf': r['total_waf'], 'valid': r['valid']})
assert all(x['config_ok'] for x in rows) and all(x['runtime_ok'] in (True, '검증 불가 (objdump만)') for x in rows), [x['run_id'] for x in rows if not x['config_ok'] or x['runtime_ok'] is False]
with open(OUT / 'run_config_check.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, list(rows[0]), lineterminator='\n'); w.writeheader(); w.writerows(rows)

L = 'revD-src/conv_ftl.c'
FM = [  # variant, batch, flags, discounting, elimination, settling, drift, partial reset, probe, code, runtime check, gocom note
    ('iCAT-v4', 'revD / abl / batchG', 'ICAT_VARIANT=4', '✓ γ=0.99949646', '✓ 15 %', '✓', '✓ 25 %', '✓', '✓', '—', 'init VARIANT=4 gamma_q16=65503 exploration_q16=16384; 리셋 직후 active < 45', ''),
    ('NoDrift', 'revD-20261124', 'ICAT_VARIANT=1', '✓', '✓', '✓', '✗', 'N/A (리셋 없음)', '✓',
     f'{L}:567 `ICAT_VARIANT != 1` → 감지 블록(567-579) 건너뜀', 'summary reset=0 (3 run × 4 파티션)', '고컴 revA V1과 같은 소스'),
    ('FullReset', 'revD-20261124', 'ICAT_VARIANT=7', '✓', '✓', '✓', '✓', '✗ 45개 전부 복원', '✓',
     f'{L}:486-490 reset_epoch에서 `active = WATGC_V2_ALLOWED` (45개)', 'reset 직후 sample active=45 (12/12 리셋)', ''),
    ('NoDiscount', 'revision-additional-ablation', 'ICAT_VARIANT=4 ICAT_EXTRA=-DWATGC_V2_GAMMA_Q16=65536ULL', '✗ γ=1 (항등)', '✓', '✓', '✓', '✓', '✓',
     f'{L}:317-321 watgc_v2_discount, 584-586 호출; conv_ftl.h:60-62 GAMMA_Q16', 'init gamma_q16=65536 (3 run × 4 파티션)', ''),
    ('NoElim+NoSettle', 'revision-additional-ablation', 'ICAT_VARIANT=2', '✓', '✗', '✗', '✗ (정착이 없어 구조상 꺼짐)', 'N/A (리셋 없음)', '✗ (정착이 없어 구조상 꺼짐)',
     f'{L}:620 제거 `!= 2`, 540 정착 `!= 2`; 감지 568과 probe 639-657은 settled일 때만', 'summary elim=0 active=45 settled=0 reset=0 (3 run × 4 파티션)', '고컴 revA V2와 같은 정책 (VARIANT 2)'),
    ('drift50 (Parameter Sensitivity)', 'drift50-20261126 (batchG 같은 큐)', 'ICAT_VARIANT=4 ICAT_EXTRA=-DWATGC_V2_DRIFT_Q16=32768ULL', '✓', '✓', '✓', '✓ 문턱 50 %', '✓', '✓',
     f'conv_ftl.h:74-76 DRIFT_Q16; 사용 {L}:572-573', 'init에 문턱이 찍히지 않음 → objdump로만 확인 (shl $0xf vs $0xe)', 'Ablation 아님'),
]
with open(OUT / 'feature_matrix.csv', 'w', newline='') as f:
    w = csv.writer(f, lineterminator='\n')
    w.writerow(['variant', 'batch', 'build_flags', 'discounting', 'elimination', 'settling', 'drift_detection', 'partial_reset', 'probe',
                'code_location (revD-src@b62127da2)', 'runtime_check (kernel log)', 'note', 'gocom_crosscheck'])
    for x in FM: w.writerow([*x, ''])
print(len(rows), 'runs: config 100% OK; runtime checks OK')
