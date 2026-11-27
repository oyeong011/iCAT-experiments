#!/usr/bin/env python3
"""11-28 승컴 C-group sensitivity (param-20261127: pf-c050, pf-c075 × 3) vs bg-v4 (C 0.25, batchG-20261126, different-batch control).
    python3 -I -B analysis/revision/param_cgroup.py
WAF of the new runs is recomputed from raw counters with final_validation.run (same code as every other batch);
bg-v4 rows come from final_raw_data_validation.csv (produced by that same function). Holm family = 2 contrasts x {total, C} = 4
(preregistration.md sec. 6). gamma group is on 고컴 and is never combined with this."""
import csv, re, statistics as st, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from final_validation import run, desc, welch, paired, holm, ROOT

B = ROOT / 'result/param-20261127'
OUT = ROOT / 'result/param-20261127-analysis'
OUT.mkdir(exist_ok=True)
reg = {l.split()[1].split('/')[-1]: l.split()[0] for l in open(B / 'modules.sha256') if l.strip()}
C_Q16 = {'bg-v4': 16384, 'pf-c050': 32768, 'pf-c075': 49152}
C_VAL = {'bg-v4': 0.25, 'pf-c050': 0.50, 'pf-c075': 0.75}

runs = []
for d in sorted((B / 'raw').glob('mixFYF-pf-c0*-rep?')):
    r = run('main', 'param-20261127', d, ROOT, {}, reg)
    init = [dict(re.findall(r'(\w+)=(\d+)', l)) for l in (d / 'kernel.log').read_text(errors='replace').splitlines() if 'WATGC_V2 init' in l][-4:]
    r['init_check'] = ''.join(sorted(i['part'] for i in init)) == '0123' and all(
        (int(i['revA_variant']), int(i['gamma_q16']), int(i['exploration_q16']), int(i['candidates'])) == (4, 65503, C_Q16[r['policy']], 45) for i in init)
    r['init_values'] = f"VARIANT {init[0]['revA_variant']} gamma_q16 {init[0]['gamma_q16']} exploration_q16 {init[0]['exploration_q16']} candidates {init[0]['candidates']} (4 parts)"
    runs.append(r)
for r in csv.DictReader(open(ROOT / 'result/final-validation-20261127/final_raw_data_validation.csv')):
    if r['batch'] == 'batchG-20261126' and r['policy'] == 'bg-v4' and r['role'] == 'main':
        for k in ('total_waf', 'A_waf', 'B_waf', 'C_waf', 'C5_waf', 'ycsb_ops_per_s'): r[k] = float(r[k])
        r['rep'] = int(r['rep']); r['valid'] = r['valid'] == 'True'; r['init_check'] = 'bg-v4 (기존 검증, VARIANT 4 / 65503 / 16384)'; runs.append(r)
assert all(r['valid'] for r in runs) and len(runs) == 9, [(r['run_id'], r['invalid_reason']) for r in runs if not r['valid']]
assert all(r['init_check'] for r in runs if r['policy'] != 'bg-v4')

# ---- learner metrics (same logic as seungcom_package.learner; copied because that module runs on import) ----
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
        rc = []
        for w, ts in rst.get(p, []):
            nxt = next(((w2, t2) for w2, t2 in sett.get(p, []) if w2 > w), None)
            rc.append((nxt[0] - w, nxt[1] - ts) if nxt else None)
        parts.append({'select': int(s['select']), 'eval_explore': int(s['eval_explore']), 'elim_events': int(s['elim']), 'reset': int(s['reset']),
                      'settle_events': len(sett.get(p, [])), 'active_final': int(s['active']),
                      'active_at_first_settle': int(samp[(p, fs[0])]['active']) if fs else None,
                      'first_settle_window': fs[0] if fs else None, 'first_settle_s': fs[1] - t0 if fs else None, 'reexplore': rc})
    return parts

mean = lambda xs: st.mean(xs) if xs else ''
LK = ('select', 'eval_explore', 'elim_events', 'reset', 'settle_events', 'active_at_first_settle', 'active_final', 'first_settle_window', 'first_settle_s')
for r in runs:
    ps = learner(r['raw_path']); assert len(ps) == 4, r['raw_path']
    rc = [x for q in ps for x in q['reexplore']]
    r.update({f'{k}_mean_per_part': mean([q[k] for q in ps if q[k] is not None]) for k in LK})
    r.update({'partitions_settled': sum(q['settle_events'] > 0 for q in ps), 'resets_total': len(rc), 'resets_censored': sum(x is None for x in rc),
              'reexplore_windows_mean': mean([x[0] for x in rc if x]), 'reexplore_s_mean': mean([x[1] for x in rc if x])})

ORDER = ['bg-v4', 'pf-c050', 'pf-c075']
by = {p: sorted((r for r in runs if r['policy'] == p), key=lambda r: r['rep']) for p in ORDER}
M = ['total_waf', 'A_waf', 'B_waf', 'C_waf', 'C5_waf']
LM = [f'{k}_mean_per_part' for k in LK] + ['partitions_settled', 'resets_total', 'resets_censored', 'reexplore_windows_mean', 'reexplore_s_mean']
f4 = lambda x: f'{x:.4f}' if isinstance(x, float) else x

raw_rows = [{'C': C_VAL[r['policy']], 'policy': r['policy'], 'batch': r['batch'], 'rep': r['rep'], 'raw_path': r['raw_path'], 'module': r['module'],
             'module_sha256': r['module_sha256'][:16], 'module_sha_matches_registered': r['module_sha_matches_registered'], 'icat_seed': r['icat_seed'],
             'fio_seeds_first_phase': r['fio_seeds_first_phase'], 'init_check': r['init_check'], 'init_values': r.get('init_values', ''), 'valid': r['valid'],
             **{m: f4(r[m]) for m in M + ['ycsb_ops_per_s']}, **{k: f4(r[k]) for k in LM}} for p in ORDER for r in by[p]]

summ = []
for p in ORDER:
    row = {'C': C_VAL[p], 'policy': p, 'batch': by[p][0]['batch'], 'role': '대조군 (다른 배치, 같은 호스트·모듈 계열·seed)' if p == 'bg-v4' else '신규'}
    for m in M:
        d = desc([r[m] for r in by[p]])
        row.update({f'{m}_reps': ' / '.join(f"{r[m]:.4f}" for r in by[p]), f'{m}_mean': f4(d['mean']), f'{m}_sd': f4(d['sd']),
                    f'{m}_ci95': f"[{d['ci95_lo']:.4f}, {d['ci95_hi']:.4f}]"})
    for k in LM:
        xs = [r[k] for r in by[p] if r[k] != '']
        row[k] = f'{st.mean(xs):.2f}' if xs else '해당 없음'
    summ.append(row)

con = []
for p in ('pf-c050', 'pf-c075'):
    for m in ('total_waf', 'C_waf'):
        a, b = [r[m] for r in by['bg-v4']], [r[m] for r in by[p]]
        w = welch(a, b); pr = paired({r['rep']: r[m] for r in by['bg-v4']}, {r['rep']: r[m] for r in by[p]})
        con.append({'treatment': f'C {C_VAL[p]} ({p})', 'control': 'C 0.25 (bg-v4, 다른 배치)', 'metric': m, 'control_mean': st.mean(a), 'treatment_mean': st.mean(b),
                    'diff': w['diff'], 'diff_pct_of_control': 100 * w['diff'] / st.mean(a), 'ci95_lo': w['ci95_lo'], 'ci95_hi': w['ci95_hi'],
                    'welch_df': w['welch_df'], 'welch_p': w['welch_p'], 'hedges_g': w['hedges_g'], 'paired_mean_same_seed': pr['paired_mean'],
                    'paired_p': pr['paired_p']})
for c, h in zip(con, holm([c['welch_p'] for c in con])):
    c['holm_p_family4'] = h
    c['reading'] = (f"유의 (Holm p {h:.2g})" if h < .05 else
                    f"보정 전 p {c['welch_p']:.2g}, 보정 후 유의하지 않음" if c['welch_p'] < .05 else f"차이 확인 못 함 (Welch p {c['welch_p']:.2g})")
    for k, x in c.items(): c[k] = f'{x:.4g}' if isinstance(x, float) and 'p' in k.split('_')[-1] else f4(x)

def write(name, rows):
    with open(OUT / name, 'w', newline='') as f:
        w = csv.DictWriter(f, list(rows[0]), lineterminator='\n'); w.writeheader(); w.writerows(rows)
write('cgroup_raw_by_run.csv', raw_rows)
write('cgroup_summary.csv', summ)
write('cgroup_contrasts.csv', con)
for s in summ: print(s['C'], s['total_waf_reps'], s['total_waf_mean'], s['total_waf_sd'], s['total_waf_ci95'], s['C_waf_mean'], s['active_at_first_settle_mean_per_part'], s['first_settle_s_mean_per_part'], s['resets_total'], s['reexplore_windows_mean'], s['elim_events_mean_per_part'], s['select_mean_per_part'])
for c in con: print(c['treatment'], c['metric'], c['diff'], c['ci95_lo'], c['ci95_hi'], c['welch_p'], c['paired_p'], c['holm_p_family4'], c['reading'])
