#!/usr/bin/env python3
"""11-27 cell-by-cell check of 고컴 report/final-revision/iCAT_Complete_Experiment_Results.xlsx against the independent raw-log
recomputation in result/final-validation-20261127/*.csv (made by final_validation.py / m1_validation.py; neither imports 고컴 code).
    uv run --no-project --with openpyxl python -I -B analysis/revision/excel_validation.py XLSX
Structured sheets (Raw Results, Run Validity, Statistical Analysis) are compared by row key (host, batch, group, rep / metric).
Every other numeric cell is looked up by value in the recomputed universe; a cell with no recomputed counterpart is 미검증, not 일치.
Output result/final-validation-20261127/excel_cell_validation.csv"""
import csv, math, re, sys
from pathlib import Path
import openpyxl

ROOT = Path(__file__).resolve().parents[2]
V = ROOT / 'result/final-validation-20261127'
XL = 'origin/report/data-validity-20261124@3fdb21258:report/final-revision/iCAT_Complete_Experiment_Results.xlsx'
wb = openpyxl.load_workbook(sys.argv[1], data_only=True)
rd = lambda n: list(csv.DictReader(open(V / n)))
runs, stat, m1 = rd('final_raw_data_validation.csv'), rd('final_statistical_validation.csv'), rd('m1_recalc.csv')
BATCH = {'abl-20261125': 'revision-additional-ablation'}
GROUP = {'revA-arm47': 'arm47', 'revC-arm60': 'revB-arm60', 'revC-online': 'online', 'abl-offbundle': 'abl-off-elim-settle-drift-probe', 'greedy': 'greedy-online'}
GB = {'drift50': 'drift50-20261126', 'greedygc': 'greedygc-20261126'}   # Excel files them under batchG-20261126
MET = {'waf': 'total_waf', 'waf_A': 'A_waf', 'waf_B': 'B_waf', 'waf_C': 'C_waf', 'waf_C5': 'C5_waf', 'ycsb_tput': 'ycsb_ops_per_s'}

def norm(b, g):
    g2 = GROUP.get(g, g); return GB.get(g2, BATCH.get(b, b)), g2

def num(x):
    try: return float(x)
    except (TypeError, ValueError): return None

def tol(x):   # half a unit of the last stored decimal (Excel keeps what 고컴 wrote; rounded cells get rounding tolerance)
    s = repr(float(x)); d = len(s.split('.')[1].rstrip('0')) if '.' in s and 'e' not in s else 0
    return max(1e-9, 1e-6 * abs(x)) if d >= 9 else 0.5 * 10 ** -d + 1e-12

R = {(r['batch'], r['policy'], r['rep']): r for r in runs if r['role'] == 'main'}   # smoke dirs share policy+rep: never key them here
D = {(r['batch'], r['policy'], r['metric']): r for r in stat if r['kind'] == 'descriptive'}
C = {(r['treatment'], r['control'], r['metric']): r for r in stat if r['kind'] == 'contrast'}
out = []
def add(sheet, cell, key, field, xv, rv, raw='', cause='', rec=''):
    a, b = num(xv), num(rv)
    if rv in ('', None): verdict = '미검증 (재계산 값 없음)'
    elif a is not None and b is not None: verdict = '일치' if abs(a - b) <= tol(a) else '불일치'
    else: verdict = '일치' if str(xv).strip().lower() == str(rv).strip().lower() else '불일치'
    out.append({'sheet': sheet, 'cell': cell, 'key': key, 'field': field, 'excel_value': xv, 'recalc_value': rv,
                'diff': abs(a - b) if a is not None and b is not None else '', 'verdict': verdict, 'raw_location': raw,
                'cause': cause if verdict == '불일치' else '', 'recommendation': rec if verdict == '불일치' else ''})

def tables(ws, first):
    """yield (header, [(row_idx, row)]) for every table whose header row starts with `first`."""
    rows = list(ws.iter_rows(values_only=True)); i = 0
    while i < len(rows):
        if rows[i] and rows[i][0] == first:
            h = [str(c) if c is not None else '' for c in rows[i]]; body = []; i += 1
            while i < len(rows) and rows[i] and rows[i][0] not in (None, '') and rows[i][0] != first and not str(rows[i][0])[0].isdigit() or (i < len(rows) and rows[i] and rows[i][0] in ('고컴', '승컴')):
                body.append((i + 1, rows[i])); i += 1
            yield h, body
        else: i += 1

col = lambda h, name: h.index(name) if name in h else None
L = openpyxl.utils.get_column_letter
done = set()
# 1 Raw Results (mixFYF table)
ws = wb['Raw Results']
for h, body in tables(ws, '호스트'):
    for i, r in body:
        if r[0] not in ('고컴', '승컴'): continue
        b, g = norm(r[1], r[2]); x = R.get((b, g, str(r[4])))
        key = f'{r[0]} {r[1]}/{r[2]} rep{r[4]}'
        if not x: add('Raw Results', f'A{i}', key, '(run)', 'present', '', cause='run not found in recomputation'); continue
        if x['host'] != r[0]: add('Raw Results', f'A{i}', key, 'host', r[0], x['host'], x['raw_path'])
        for name, f in (('host_pages', 'host_pages'), ('gc_pages', 'gc_pages'), ('전체 WAF', 'total_waf'), ('단계 A', 'A_waf'), ('단계 B', 'B_waf'), ('단계 C', 'C_waf'),
                        ('C 첫 5분', 'C5_waf'), ('YCSB ops/s', 'ycsb_ops_per_s'), ('유효', 'valid')):
            j = col(h, name)
            if j is not None: add('Raw Results', f'{L(j + 1)}{i}', key, name, r[j], x[f], x['raw_path'], 'Excel value differs from raw counters', 'recompute from stopped.txt / phase-*-end.txt')
            if j is not None: done.add(('Raw Results', i, j))
        j = col(h, '모듈 sha256')
        if j is not None: add('Raw Results', f'{L(j + 1)}{i}', key, 'module sha256 prefix', str(r[j])[:16], x['module_sha256'][:16], x['raw_path']); done.add(('Raw Results', i, j))
# mixY rows of Raw Results (출처, run, exit, host_pages, gc_pages, WAF)
for h, body in tables(ws, '출처'):
    for i, r in body:
        p = str(r[1]).rstrip('/')   # full path when given; m1 rows give only the run name -> match within the m1 batch
        cand = [v for v in runs if v['workload'] == 'mixY' and v['role'] == 'main' and (v['raw_path'].split(':', 1)[-1] == p or (v['batch'] == 'm1-20261126' and v['raw_path'].endswith('/' + p)))]
        x = cand[0] if len(cand) == 1 else None
        if not x: add('Raw Results', f'B{i}', str(r[1]), '(run)', 'present', '', cause='ambiguous or missing run'); continue
        for j, f in ((3, 'host_pages'), (4, 'gc_pages'), (5, 'total_waf')): add('Raw Results', f'{L(j + 1)}{i}', str(r[1]), f, r[j], x[f], x['raw_path']); done.add(('Raw Results', i, j))
# 2 Run Validity
ws = wb['Run Validity']
for h, body in tables(ws, '호스트'):
    for i, r in body:
        if r[0] not in ('고컴', '승컴') or str(r[2]).startswith('mixFYF-'): continue   # smoke rows are listed by full dir name
        b, g = norm(r[1], r[2]); x = R.get((b, g, str(r[3])))
        key = f'{r[0]} {r[1]}/{r[2]} rep{r[3]}'
        if not x: add('Run Validity', f'A{i}', key, '(run)', 'present', '', cause='run not found in recomputation'); continue
        for name, f in (('exit', None), ('icat_seed', 'icat_seed'), ('커널 오류', 'kernel_errors'), ('FIO 오류', 'fio_errors'), ('YCSB ops', 'ycsb_ops'),
                        ('YCSB OK', 'ycsb_ok'), ('SQLITE_FULL', 'sqlite_full'), ('두 경로 일치', 'waf_paths_agree_1e9'), ('시작 카운터 0', 'init_counters_zero'), ('유효 (재검사)', 'valid')):
            j = col(h, name)
            if j is None: continue
            rv = '0' if f is None and x['valid'] == 'True' else (x[f] if f else '')
            add('Run Validity', f'{L(j + 1)}{i}', key, name, r[j], rv, x['raw_path']); done.add(('Run Validity', i, j))
        j = col(h, 'FIO seed')
        if j is not None: add('Run Validity', f'{L(j + 1)}{i}', key, 'FIO seed', str(r[j]).replace(' ', '/'), x['fio_seeds_first_phase'], x['raw_path']); done.add(('Run Validity', i, j))
        j = col(h, '모듈 sha256')
        if j is not None: add('Run Validity', f'{L(j + 1)}{i}', key, 'module sha256 prefix', str(r[j])[:16], x['module_sha256'][:16], x['raw_path']); done.add(('Run Validity', i, j))
# 3 Statistical Analysis: group stats + contrasts
ws = wb['Statistical Analysis']
for h, body in tables(ws, '호스트'):
    for i, r in body:
        if r[0] not in ('고컴', '승컴') or r[4] not in MET: continue
        b, g = norm(r[1], r[2]); x = D.get((b, g, MET[r[4]])); key = f'{r[0]} {r[1]}/{r[2]} {r[4]}'
        for name, f in (('n', 'n'), ('평균', 'mean'), ('SD', 'sd'), ('95% CI 하한', 'ci95_lo'), ('95% CI 상한', 'ci95_hi')):
            j = col(h, name)
            if j is not None and r[j] is not None: add('Statistical Analysis', f'{L(j + 1)}{i}', key, name, r[j], x[f] if x else '', f'{b}/{g}'); done.add(('Statistical Analysis', i, j))
for h, body in tables(ws, '대비 (정책 − 대조군)'):
    for i, r in body:
        if r[4] not in MET: continue
        t, _, c = str(r[0]).partition(' − '); bt = r[3]
        tb, tg = norm(bt, t); cb, cg = norm(bt, c)
        if t == 'arm47': tb = 'arm47-20261127'
        x = C.get((f'{tb}/{tg}', f'{cb}/{cg}', MET[r[4]])) or next((v for (tt, cc, m), v in C.items() if tt.endswith('/' + tg) and cc.endswith('/' + cg) and m == MET[r[4]]), None)
        key = f'{r[0]} {r[3]} {r[4]}'
        for name, f in (('Δ', 'diff'), ('Welch 95% CI 하한', 'ci95_lo'), ('Welch 95% CI 상한', 'ci95_hi'), ('df', 'welch_df'), ('p (보정 전)', 'welch_p'), ('Hedges g', 'hedges_g'), ('Holm p', 'holm_p_family')):
            j = col(h, name)
            if j is None or r[j] in (None, ''): continue
            rv = x.get(f, '') if x else ''
            if name == 'Holm p' and x and rv != '' and num(r[j]) is not None and abs(num(r[j]) - num(rv)) > tol(num(r[j])) and x.get('holm_p_total_only'):
                rv = x['holm_p_total_only'] if abs(num(r[j]) - num(x['holm_p_total_only'])) <= tol(num(r[j])) else rv
            add('Statistical Analysis', f'{L(j + 1)}{i}', key, name, r[j], rv, x and f"{x['control']} | {x['treatment']}", 'Holm family or value differs', 'state the Holm family in the caption')
            done.add(('Statistical Analysis', i, j))
# 4 every other numeric cell: value lookup in the recomputed universe
U = []
for r in runs:
    for f in ('host_pages', 'gc_pages', 'total_waf', 'A_waf', 'B_waf', 'C_waf', 'C5_waf', 'ycsb_ops_per_s', 'waf_nand'):
        if num(r.get(f)) is not None: U.append((num(r[f]), f'run {r["run_id"]} {f}'))
for r in stat:
    for f in ('mean', 'sd', 'ci95_lo', 'ci95_hi', 'ci95_halfwidth', 'cv_pct', 'diff', 'welch_df', 'welch_p', 'hedges_g', 'holm_p_family', 'holm_p_total_only', 'paired_mean', 'paired_p', 'paired_ci95_lo', 'paired_ci95_hi'):
        if num(r.get(f)) is not None: U.append((num(r[f]), f'{r.get("batch", "")}{r.get("treatment", "")}/{r.get("policy", "")} {r.get("control", "")} {r["metric"]} {f}'))
    if r['kind'] == 'contrast' and num(r.get('ci95_lo')) is not None:   # CI half width; sign-reversed contrast (control - treatment)
        U.append(((num(r['ci95_hi']) - num(r['ci95_lo'])) / 2, f'{r["treatment"]} - {r["control"]} {r["metric"]} CI half width'))
        for f in ('diff', 'ci95_lo', 'ci95_hi', 'hedges_g'): U.append((-num(r[f]), f'{r["control"]} - {r["treatment"]} {r["metric"]} {f} (reversed)'))
    if r['kind'] == 'contrast' and num(r.get('diff')) is not None:   # Δ % = 100 diff / control mean
        cm = next((num(d['mean']) for d in stat if d['kind'] == 'descriptive' and f"{d['batch']}/{d['policy']}" == r['control'] and d['metric'] == r['metric']), None)
        if cm: U.append((100 * num(r['diff']) / cm, f'{r["treatment"]} - {r["control"]} {r["metric"]} pct'))
for r in m1:
    if num(r['recalc']) is not None: U.append((num(r['recalc']), f'{r["source"]} {r["run"]} {r["item"]}'))
U.sort()
import bisect
keys = [u[0] for u in U]
for ws in wb.worksheets:
    for row in ws.iter_rows():
        for c in row:
            v = c.value
            if (ws.title, c.row, c.column - 1) in done or not isinstance(v, (int, float)) or isinstance(v, bool): continue
            if isinstance(v, int) and abs(v) < 1000 or (isinstance(v, float) and v.is_integer() and abs(v) < 1000): continue   # counts / reps / labels
            t = tol(float(v)); k = bisect.bisect_left(keys, v - t); hit = U[k] if k < len(U) and abs(U[k][0] - v) <= t else None
            ctx = ' | '.join(str(x.value)[:25] for x in row[:3] if x.value is not None)
            out.append({'sheet': ws.title, 'cell': c.coordinate, 'key': ctx, 'field': 'value lookup', 'excel_value': v, 'recalc_value': hit[0] if hit else '',
                        'diff': abs(hit[0] - v) if hit else '', 'verdict': '일치 (값 대조)' if hit else '미검증 (재계산 대상 밖 또는 불일치 후보)',
                        'raw_location': hit[1] if hit else '', 'cause': '', 'recommendation': ''})
with open(V / 'excel_cell_validation.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, list(out[0]), lineterminator='\n'); w.writeheader(); w.writerows(out)
from collections import Counter
print(Counter((o['sheet'], o['verdict']) for o in out))
for o in out:
    if o['verdict'] == '불일치': print('MISMATCH', o['sheet'], o['cell'], o['key'], o['field'], o['excel_value'], o['recalc_value'])
