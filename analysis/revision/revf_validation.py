#!/usr/bin/env python3
"""고컴 revF-20261127 (γ / C sensitivity, n=1 each) independent re-check on 승컴. NO verdicts (n=1).
    git archive origin/report/data-validity-20261124 result/revF-20261127 | tar -x -C DIR
    python3 -I -B analysis/revision/revf_validation.py DIR
Recomputes total / A / B / C / C5 WAF from raw counters (final_validation.run) and checks the kernel init lines
(revA_variant, gamma_q16, exploration_q16, candidates) of the measurement-start init against the preregistration."""
import csv, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from final_validation import run, rd, ROOT   # same raw-counter code used for every other batch

BASE = Path(sys.argv[1])
B = BASE / 'result/revF-20261127'
OUT = ROOT / 'result/revF-20261127-validation'
OUT.mkdir(exist_ok=True)
# preregistration.md sec. 1 (origin/report/data-validity-20261124@89def8940)
PRE = {'revF-v4': (4, 65503, 16384), 'revF-g99': (4, 64881, 16384), 'revF-g95': (4, 62259, 16384), 'revF-g90': (4, 58982, 16384),
       'revF-c050': (4, 65503, 32768), 'revF-c075': (4, 65503, 49152)}
reg = {l.split()[1].split('/')[-1]: l.split()[0] for l in open(B / 'modules.sha256') if l.strip()}
rows = []
for d in sorted((B / 'raw').glob('mixFYF-revF-*-rep*')):
    r = run('gocom', 'revF-20261127', d, BASE, {}, reg)
    if r['role'] != 'main': continue
    init = [dict(re.findall(r'(\w+)=(\d+)', l)) for l in (rd(d, 'kernel.log') or '').splitlines() if 'WATGC_V2 init' in l][-4:]
    var, gq, cq = PRE[r['policy']]
    r['init_parts'] = ''.join(sorted(i['part'] for i in init))
    r['init_variant'] = '/'.join(sorted({i['revA_variant'] for i in init}))
    r['init_gamma_q16'] = '/'.join(sorted({i['gamma_q16'] for i in init}))
    r['init_exploration_q16'] = '/'.join(sorted({i['exploration_q16'] for i in init}))
    r['prereg'] = f'VARIANT={var} gamma_q16={gq} exploration_q16={cq}'
    r['init_matches_prereg'] = (r['init_parts'] == '0123' and all(
        (int(i['revA_variant']), int(i['gamma_q16']), int(i['exploration_q16']), int(i['candidates'])) == (var, gq, cq, 45) for i in init))
    rows.append(r)
ctl = next((r for r in rows if r['policy'] == 'revF-v4'), None)
for r in rows:   # simple difference and ratio vs the same-batch control, NO verdict (n=1)
    for m in ('total_waf', 'C_waf', 'C5_waf'):
        if ctl and r.get(m) and ctl.get(m): r[f'{m}_minus_ctl'] = r[m] - ctl[m]; r[f'{m}_ratio_ctl'] = r[m] / ctl[m]
keys = ['run_id', 'policy', 'rep', 'host', 'raw_path', 'module', 'module_sha256', 'module_sha_matches_registered', 'prereg', 'init_parts', 'init_variant',
        'init_gamma_q16', 'init_exploration_q16', 'init_matches_prereg', 'fio_seeds_first_phase', 'icat_seed', 'phases', 'phase_minutes', 'init_counters_zero',
        'ycsb_success', 'sqlite_full', 'fio_errors', 'kernel_errors', 'host_pages', 'gc_pages', 'total_waf', 'total_waf_partsum', 'waf_paths_agree_1e9',
        'summary_waf', 'summary_vs_recalc_absdiff', 'A_waf', 'B_waf', 'C_waf', 'C5_waf', 'total_waf_minus_ctl', 'total_waf_ratio_ctl',
        'C_waf_minus_ctl', 'C_waf_ratio_ctl', 'C5_waf_minus_ctl', 'C5_waf_ratio_ctl', 'valid', 'invalid_reason']
with open(OUT / 'revf_recalc.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, keys, extrasaction='ignore', lineterminator='\n'); w.writeheader(); w.writerows(rows)
print(f'{len(rows)} main runs (expected 6)')
for r in rows: print(r['policy'], r['init_matches_prereg'], r['module_sha_matches_registered'], r['valid'], r['invalid_reason'],
                    *(f"{r.get(m, float('nan')):.4f}" for m in ('total_waf', 'A_waf', 'B_waf', 'C_waf', 'C5_waf')))
