#!/usr/bin/env python3
"""iCAT revision: complete experiment results workbook (GoCom, 2026-11-27). Read-only on every raw log; no new experiment.
    python3 -I analysis/final_revision/complete_results.py [SEUNGCOM_COMMIT]   (default 4689c6797 = origin/main 11-27 05:26)
SeungCom raw directories are taken with `git archive <commit>` into $ICAT_SC_CACHE (default: /tmp/icat-sc-<commit>), kernel-snapshots
excluded. Every WAF in the workbook is recomputed here from raw counters (summary.txt / final-control.txt / phase snapshots /
control-series.txt) and compared with the previously published value (databook v2, verify dirs, SeungCom analysis).
Outputs (refuses to overwrite):
  report/final-revision/iCAT_Complete_Experiment_Results.xlsx      17 sheets, native editable charts
  report/final-revision/complete-results/*.csv                      every table behind a sheet / chart
  report/final-revision/DATA_PROVENANCE.csv
Rules: host + batch on every row; no pooling across hosts or batches; n<3 -> no statistics; cross-batch contrasts labelled INDIRECT;
ktime = elapsed time (not CPU time); calculated memory != measured memory."""
import csv, gzip, hashlib, io, math, os, re, subprocess, statistics as st, sys, tarfile
from datetime import datetime
from pathlib import Path
from scipy import stats as sps

ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(Path(__file__).parent))
from xlsx_chart import Workbook

SC = sys.argv[1] if len(sys.argv) > 1 else '4689c6797'
OUTX = ROOT / 'report/final-revision/iCAT_Complete_Experiment_Results.xlsx'
OUTD = ROOT / 'report/final-revision/complete-results'
for p in (OUTX, ROOT / 'report/final-revision/DATA_PROVENANCE.csv'):
    if p.exists(): sys.exit(f'refusing to overwrite {p}')
if OUTD.exists() and any(OUTD.iterdir()): sys.exit(f'refusing to overwrite {OUTD}')
OUTD.mkdir(parents=True, exist_ok=True)
GIT = lambda *a: subprocess.run(['git', '-C', str(ROOT), *a], capture_output=True, text=True, check=True).stdout
SC_FULL = GIT('rev-parse', SC).strip(); HEAD = GIT('rev-parse', 'HEAD').strip()
CACHE = Path(os.environ.get('ICAT_SC_CACHE', f'/tmp/icat-sc-{SC_FULL[:9]}'))
SC_RAW = ['result/revD-20261124/raw', 'result/revision-additional-ablation/raw', 'result/greedy-20261125/raw', 'result/batchG-20261126/raw',
          'result/greedygc-20261126/raw', 'result/drift50-20261126/raw', 'result/arm47-20261127/raw']
if not (CACHE / 'DONE').exists():
    CACHE.mkdir(parents=True, exist_ok=True)
    data = subprocess.run(['git', '-C', str(ROOT), 'archive', SC_FULL, *SC_RAW], capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(data)) as t:
        t.extractall(CACHE, members=[m for m in t.getmembers() if '/kernel-snapshots' not in m.name], filter='data')
    (CACHE / 'DONE').write_text(SC_FULL)
scshow = lambda p: list(csv.DictReader(io.StringIO(GIT('show', f'{SC_FULL}:{p}'))))
rd = lambda p: list(csv.DictReader(open(ROOT / p)))
PROV = []   # (sheet/table, item, source, method)


def prov(table, item, source, method):
    PROV.append(dict(table=table, item=item, source=source, method=method))


# ------------------------------------------------------------------ groups ------------------------------------------------------------
L = lambda p: ROOT / p
C = lambda p: CACHE / p
GROUPS = [  # key, host, batch, label, raw base (Path), dir regex, design n, published raw path
    ('revA-v4', '고컴', 'revA-20261114', 'iCAT-v4', L('result/revA-20261114/raw'), r'mixFYF-revA-v4-rep\d$', 3),
    ('revA-v1', '고컴', 'revA-20261114', 'V1 (변화 감지 끔)', L('result/revA-20261114/raw'), r'mixFYF-revA-v1-rep\d$', 3),
    ('revA-v2', '고컴', 'revA-20261114', 'V2 (제거·정착 끔)', L('result/revA-20261114/raw'), r'mixFYF-revA-v2-rep\d$', 3),
    ('revA-random', '고컴', 'revA-20261114', 'Random Selection', L('result/revA-20261114/raw'), r'mixFYF-revA-random-rep\d$', 3),
    ('revA-arm47', '고컴', 'revA-20261114', '고정 Arm 47 (n=1, 단일 실행)', L('result/revA-20261114/raw'), r'mixFYF-arm47-rep\d$', 1),
    ('revB-v4', '고컴', 'revB-20261122', 'iCAT-v4 (n=1)', L('result/revB-20261122/raw'), r'mixFYF-revB-v4-rep\d$', 1),
    ('revB-noelim', '고컴', 'revB-20261122', 'NoElim (revB)', L('result/revB-20261122/raw'), r'mixFYF-revB-noelim-rep\d$', 3),
    ('revB-nosettle', '고컴', 'revB-20261122', 'NoSettle', L('result/revB-20261122/raw'), r'mixFYF-revB-nosettle-rep\d$', 3),
    ('revB-arm60', '고컴', 'revB-20261122', '60 arms (n=1)', L('result/revB-20261122/raw'), r'mixFYF-revB-arm60-rep\d$', 1),
    ('revC-v4', '고컴', 'revC-20261124', 'iCAT-v4', L('result/revC-20261124/raw'), r'mixFYF-revC-v4-rep\d$', 3),
    ('revC-elim10', '고컴', 'revC-20261124', '제거 문턱 10 %', L('result/revC-20261124/raw'), r'mixFYF-revC-elim10-rep\d$', 3),
    ('revC-elim25', '고컴', 'revC-20261124', '제거 문턱 25 %', L('result/revC-20261124/raw'), r'mixFYF-revC-elim25-rep\d$', 3),
    ('revC-arm60', '고컴', 'revC-20261124', '후보 60 arms', L('result/revC-20261124/raw'), r'mixFYF-revB-arm60-rep\d$', 3),
    ('revC-online', '고컴', 'revC-20261124', '원래 iCAT', L('result/revC-20261124/raw'), r'mixFYF-online-rep\d$', 3),
    ('revD-v4', '승컴', 'revD-20261124', 'iCAT-v4', C('result/revD-20261124/raw'), r'mixFYF-revD-v4-rep\d$', 3),
    ('revD-nodrift', '승컴', 'revD-20261124', 'NoDrift', C('result/revD-20261124/raw'), r'mixFYF-revD-nodrift-rep\d$', 3),
    ('revD-fullreset', '승컴', 'revD-20261124', 'FullReset', C('result/revD-20261124/raw'), r'mixFYF-revD-fullreset-rep\d$', 3),
    ('revE-v4', '고컴', 'revE-20261125', 'iCAT-v4', L('result/revE-20261125/raw'), r'mixFYF-revE-v4-rep\d$', 3),
    ('revE-noelim', '고컴', 'revE-20261125', 'NoElim (정착·감지 켬)', L('result/revE-20261125/raw'), r'mixFYF-revE-noelim-rep\d$', 3),
    ('revE-drift12', '고컴', 'revE-20261125', '감지 문턱 12.5 %', L('result/revE-20261125/raw'), r'mixFYF-revE-drift12-rep\d$', 3),
    ('abl-v4', '승컴', 'abl-20261125', 'iCAT-v4', C('result/revision-additional-ablation/raw'), r'mixFYF-abl-v4-rep\d$', 3),
    ('abl-nodiscount', '승컴', 'abl-20261125', 'NoDiscount', C('result/revision-additional-ablation/raw'), r'mixFYF-abl-nodiscount-rep\d$', 3),
    ('abl-offbundle', '승컴', 'abl-20261125', '묶음 끔 (제거+정착+감지+probe)', C('result/revision-additional-ablation/raw'), r'mixFYF-abl-off-elim-settle-drift-probe-rep\d$', 3),
    ('greedy', '승컴', 'greedy-20261125', 'Online Greedy', C('result/greedy-20261125/raw'), r'mixFYF-greedy-online-rep\d$', 3),
    ('bg-v4', '승컴', 'batchG-20261126', 'iCAT-v4', C('result/batchG-20261126/raw'), r'mixFYF-bg-v4-rep\d$', 3),
    ('greedygc', '승컴', 'batchG-20261126', 'Greedy GC (학습 없음)', C('result/greedygc-20261126/raw'), r'mixFYF-greedygc-rep\d$', 3),
    ('drift50', '승컴', 'batchG-20261126', '감지 문턱 50 %', C('result/drift50-20261126/raw'), r'mixFYF-drift50-rep\d$', 3),
    ('arm47', '승컴', 'arm47-20261127', '고정 Arm 47', C('result/arm47-20261127/raw'), r'mixFYF-arm47-rep\d$', 3),
]
GI = {g[0]: g for g in GROUPS}
pub = lambda d: str(d).replace(str(CACHE) + '/', f'origin/main@{SC_FULL[:9]}:').replace(str(ROOT) + '/', '')


# ------------------------------------------------------------- raw recomputation -------------------------------------------------------
def first(p): return p.read_text().splitlines()[0]
def cnt(t, k): return int(re.search(rf'\b{k}=(\d+)', t)[1])
def epoch(p): return datetime.fromisoformat(p.read_text().strip()).timestamp()


def series(d):
    out = []
    for l in (d / 'control-series.txt').read_text().splitlines():
        m = re.match(r'(\d+) .*?host_pages=(\d+) gc_pages=(\d+)', l)
        if m: out.append((int(m[1]), int(m[2]), int(m[3])))
    return out


def at(ser, t):   # first sample at or after t
    for s in ser:
        if s[0] >= t: return s
    return None


def recompute(key, d):
    g = GI[key]; rep = int(re.search(r'rep(\d)', d.name)[1]); bad = []
    r = dict(key=key, host=g[1], batch=g[2], policy=g[3], rep=rep, raw_dir=pub(d))
    r['exit'] = (d / 'exit-code.txt').read_text().strip() if (d / 'exit-code.txt').exists() else 'missing'
    if r['exit'] != '0': bad.append('exit')
    env = (d / 'environment.txt').read_text(errors='replace')
    ko = [s for s, p in re.findall(r'^([0-9a-f]{64})\s+(\S+)$', env, re.M) if p.endswith('.ko')]
    r['module_sha256'] = ko[0] if ko else ''
    r['hostname'] = (env.splitlines()[1].split() + ['', ''])[1] if len(env.splitlines()) > 1 else ''
    fs = sorted({int(x) for p in 'AC' if (d / f'phase-{p}.json').exists() for x in re.findall(r'"randseed"\s*:\s*"?(\d+)', (d / f'phase-{p}.json').read_text())})
    r['fio_seeds'] = ' '.join(map(str, fs)); r['fio_seeds_expected'] = fs == [20260910 + rep, 20261010 + rep, 20261110 + rep]
    kl = (d / 'kernel.log').read_text(errors='replace'); beg = [m.end() for m in re.finditer(r'mix-mixFYF-\S+ BEGIN', kl)]; own = kl[beg[-1]:] if beg else kl
    r['icat_seed'] = ' '.join(sorted(set(re.findall(r'WATGC_V2 init .*?icat_seed=(\d+)', own))))
    r['kernel_err'] = len(re.findall(r'BUG:|WARNING:|Oops|Call Trace', own))
    r['fio_err'] = sum(int(x) for p in 'AC' if (d / f'phase-{p}.json').exists() for x in re.findall(r'"error"\s*:\s*(\d+)', (d / f'phase-{p}.json').read_text()))
    yt = gzip.open(d / 'ycsb-run-B.txt.gz', 'rt', errors='replace').read() if (d / 'ycsb-run-B.txt.gz').exists() else ''
    ops = sum(int(x) for x in re.findall(r'^\[(?:READ|UPDATE)\], Operations, (\d+)', yt, re.M))
    ok = sum(int(x) for x in re.findall(r'^\[(?:READ|UPDATE)\], Return=OK, (\d+)', yt, re.M))
    tp = re.search(r'^\[OVERALL\], Throughput\(ops/sec\), ([\d.]+)', yt, re.M)
    r.update(ycsb_ops=ops, ycsb_ok=ok, ycsb_success=round(ok / ops, 6) if ops else '', ycsb_ops_per_s=float(tp[1]) if tp else '')
    r['sqlite_full'] = sum((gzip.open(f, 'rt', errors='replace').read() if f.suffix == '.gz' else f.read_text(errors='replace')).count('SQLITE_FULL') for f in d.glob('ycsb*'))
    for k, c in (('kernel_err', 'kernel error'), ('fio_err', 'fio error'), ('sqlite_full', 'SQLITE_FULL')):
        if r[k]: bad.append(c)
    if not ops or ok != ops: bad.append('YCSB')
    t = re.search(r'^total .*host_pages=(\d+) gc_pages=(\d+)', (d / 'summary.txt').read_text(), re.M)
    ps = re.findall(r'^part=\d host_pages=(\d+) gc_pages=(\d+)', (d / 'final-control.txt').read_text(), re.M)
    h, gp = int(t[1]), int(t[2]); r.update(host_pages=h, gc_pages=gp, waf=1 + gp / h)
    r['two_paths_equal'] = (h, gp) == (sum(int(x) for x, _ in ps), sum(int(y) for _, y in ps))
    if not r['two_paths_equal']: bad.append('WAF paths')
    r['started_zero'] = cnt(first(d / 'started.txt'), 'host_pages') == 0
    if not r['started_zero']: bad.append('counter not zero at start')
    for p in 'ABC':
        s0, s1 = first(d / f'phase-{p}-start.txt'), first(d / f'phase-{p}-end.txt')
        r[f'waf_{p}'] = 1 + (cnt(s1, 'gc_pages') - cnt(s0, 'gc_pages')) / (cnt(s1, 'host_pages') - cnt(s0, 'host_pages'))
    ser = series(d); c0 = epoch(d / 'phase-C-start.time'); a = at(ser, c0); b = at(ser, c0 + 300)
    r['waf_C5'] = 1 + (b[2] - a[2]) / (b[1] - a[1]) if a and b and b[1] > a[1] else ''
    r['valid_recomputed'] = not bad; r['invalid_reasons_recomputed'] = '; '.join(bad)
    r['_series'] = ser; r['_t0'] = epoch(d / 'phase-A-start.time'); r['_tB'] = epoch(d / 'phase-B-start.time'); r['_tC'] = c0
    return r


RUNS = []
for g in GROUPS:
    dirs = sorted(p for p in g[4].iterdir() if p.is_dir() and re.search(g[5], p.name))
    assert len(dirs) == g[6], (g[0], [p.name for p in dirs])
    RUNS += [recompute(g[0], d) for d in dirs]
by = lambda k: [r for r in RUNS if r['key'] == k]
print('recomputed runs:', len(RUNS), 'invalid:', [(r['key'], r['rep'], r['invalid_reasons_recomputed']) for r in RUNS if not r['valid_recomputed']])
prov('Raw Results / Run Validity', 'all mixFYF runs: WAF total/A/B/C, phase-C first-5-min WAF, validity checks', 'raw run directories (raw_dir column); SeungCom via git archive ' + SC_FULL[:9],
     'recomputed in complete_results.py: total = 1+gc/host from summary.txt "total" line, two paths = sum of final-control part lines; phase = start/end snapshots; C5 = control-series 30 s samples, first at/after C start to first at/after C start+300 s')

# ---- published values to compare (source validity + WAF) ----
PUBV = {}   # (key, rep) -> dict(valid, waf, waf_A, waf_B, waf_C, src)
F1KEY = {'revC-v4': 'revC:revC-v4', 'revC-elim10': 'revC:revC-elim10', 'revC-elim25': 'revC:revC-elim25', 'revC-arm60': 'revC:revB-arm60',
         'revC-online': 'revC:online', 'greedy': 'greedy'}
inv = lambda k: {v: k2 for k2, v in F1KEY.items()}.get(k, k)
for r in rd('result/final-revision-analysis/m4/runs.csv'):
    PUBV[(inv(r['group']), int(r['rep']))] = dict(valid=r['valid'], reasons=r['reasons'], waf=r['waf'], waf_A=r['waf_A'], waf_B=r['waf_B'], waf_C=r['waf_C'], src='result/final-revision-analysis/m4/runs.csv')
for r in rd('result/revE-20261125-analysis/runs.csv'):
    PUBV[(r['policy'], int(r['rep']))] = dict(valid=r['valid'], reasons=r['reasons'], waf=r['waf'], waf_A=r['waf_A'], waf_B=r['waf_B'], waf_C=r['waf_C'], src='result/revE-20261125-analysis/runs.csv')
for vd in ('abl-20261125-verify', 'greedy-20261125-verify', 'batchG-20261126-verify', 'arm47-20261127-verify'):
    for r in rd(f'result/{vd}/runs.csv'):
        k = inv(r['group'])
        if k in GI and (k, int(r['rep'])) not in PUBV and GI[k][2].split('-')[0] in r['batch']:
            PUBV[(k, int(r['rep']))] = dict(valid=r['valid'], reasons=r['reasons'], waf=r['waf'], waf_A=r['waf_A'], waf_B=r['waf_B'], waf_C=r['waf_C'], src=f'result/{vd}/runs.csv')
for r in RUNS:
    p = PUBV.get((r['key'], r['rep']))
    r['valid_published'] = p['valid'] if p else 'not found'; r['published_source'] = p['src'] if p else ''
    r['max_abs_diff_vs_published'] = max(abs(r[m] - float(p[m])) for m in ('waf', 'waf_A', 'waf_B', 'waf_C')) if p else ''
    r['matches_published'] = bool(p) and r['max_abs_diff_vs_published'] < 1e-6 and str(r['valid_recomputed']) == p['valid']
print('runs not matching published:', [(r['key'], r['rep'], r['max_abs_diff_vs_published'], r['valid_published']) for r in RUNS if not r['matches_published']])


# ------------------------------------------------------------------ statistics -----------------------------------------------------------
METRICS = [('waf', '전체 WAF'), ('waf_A', '단계 A WAF (FIO)'), ('waf_B', '단계 B WAF (YCSB-A)'), ('waf_C', '단계 C WAF (FIO 복귀)'), ('waf_C5', '단계 C 첫 5분 WAF')]


def desc(v):
    n = len(v)
    if n < 3: return dict(n=n, mean=v[0] if n == 1 else st.mean(v), sd='', ci_lo='', ci_hi='', ci_half='', note='n<3: 단일 실행, 통계 없음' if n == 1 else 'n<3: 통계 없음')
    m, s = st.mean(v), st.stdev(v); h = sps.t.ppf(.975, n - 1) * s / n ** .5
    return dict(n=n, mean=m, sd=s, ci_lo=m - h, ci_hi=m + h, ci_half=h, note='')


STATS = {}
for g in GROUPS:
    rs = [r for r in by(g[0]) if r['valid_recomputed']]
    for m, _ in METRICS:
        v = [r[m] for r in rs if r[m] != '']
        STATS[(g[0], m)] = dict(key=g[0], host=g[1], batch=g[2], policy=g[3], metric=m, values=' / '.join(f'{x:.6f}' for x in v), **desc(v))


def welch(a, b):
    ma, mb, va, vb = st.mean(a), st.mean(b), st.variance(a), st.variance(b); na, nb = len(a), len(b)
    se = (va / na + vb / nb) ** .5; df = (va / na + vb / nb) ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    h = sps.t.ppf(.975, df) * se; p = 2 * sps.t.sf(abs((ma - mb) / se), df)
    sp = (((na - 1) * va + (nb - 1) * vb) / (na + nb - 2)) ** .5; g = (ma - mb) / sp * (1 - 3 / (4 * (na + nb) - 9))
    return dict(delta=ma - mb, ci_lo=ma - mb - h, ci_hi=ma - mb + h, df=df, p=p, hedges_g=g, rel_pct=100 * (ma - mb) / mb)


# (policy, control, kind, family) -- family = Holm family (primary contrasts of that batch x {waf, waf_C}); None = not in a family
CONTRASTS = [('revA-v1', 'revA-v4', 'direct', 'revA'), ('revA-v2', 'revA-v4', 'direct', 'revA'), ('revA-random', 'revA-v4', 'direct', 'revA'),
             ('revB-noelim', 'revB-v4', 'direct', None), ('revB-nosettle', 'revB-v4', 'direct', None), ('revB-arm60', 'revB-v4', 'direct', None),
             ('revC-elim10', 'revC-v4', 'direct', 'revC'), ('revC-elim25', 'revC-v4', 'direct', 'revC'), ('revC-arm60', 'revC-v4', 'direct', 'revC'),
             ('revC-online', 'revC-v4', 'direct', 'revC'), ('revD-nodrift', 'revD-v4', 'direct', 'revD'), ('revD-fullreset', 'revD-v4', 'direct', 'revD'),
             ('revE-noelim', 'revE-v4', 'direct', 'revE'), ('revE-drift12', 'revE-v4', 'direct', 'revE'),
             ('abl-nodiscount', 'abl-v4', 'direct', 'abl'), ('abl-offbundle', 'abl-v4', 'direct', 'abl'), ('abl-offbundle', 'abl-nodiscount', 'direct', None),
             ('greedygc', 'bg-v4', 'direct', 'batchG'), ('drift50', 'bg-v4', 'direct', 'batchG'),
             ('greedy', 'revD-v4', 'INDIRECT (같은 호스트, 다른 배치)', None), ('greedy', 'abl-v4', 'INDIRECT (같은 호스트, 다른 배치)', None),
             ('arm47', 'bg-v4', 'INDIRECT (같은 호스트, 다른 배치)', None)]
CON = []
for a, b, kind, fam in CONTRASTS:
    for m, ml in METRICS:
        va = [r[m] for r in by(a) if r['valid_recomputed'] and r[m] != '']; vb = [r[m] for r in by(b) if r['valid_recomputed'] and r[m] != '']
        row = dict(contrast=f'{a} − {b}', policy=GI[a][3], control=f'{GI[b][3]} ({b})', host=GI[a][1], batch=GI[a][2] if GI[a][2] == GI[b][2] else f'{GI[a][2]} vs {GI[b][2]}',
                   kind=kind, metric=m, n=f'{len(va)} vs {len(vb)}', family=fam if m in ('waf', 'waf_C') else None)
        if len(va) < 3 or len(vb) < 3:
            row.update(verdict='n<3: 통계 없음', delta=(st.mean(va) - st.mean(vb)) if va and vb else '')
        else:
            row.update(welch(va, vb)); lo, hi = row['ci_lo'], row['ci_hi']
            row['verdict'] = ('차이 있음' if lo > 0 or hi < 0 else '구분되지 않음') + ('' if kind == 'direct' else ' (간접 비교)')
        CON.append(row)
for fam in sorted({c['family'] for c in CON if c['family']}):
    rows = sorted([c for c in CON if c['family'] == fam], key=lambda c: c['p']); k = len(rows); run = 0
    for i, c in enumerate(rows):
        run = max(run, min(1, (k - i) * c['p'])); c['holm_p'] = run; c['holm_k'] = k
CK = {(c['contrast'], c['metric']): c for c in CON}
prov('Statistical Analysis', 'group mean/SD/t 95 % CI; Welch contrasts, Hedges g, Holm', 'Raw Results (this workbook)',
     'recomputed: t CI with n-1 df; Welch-Satterthwaite df; Hedges g = pooled-SD d x (1-3/(4(na+nb)-9)); Holm within batch family = primary contrasts x {total, phase C}')

# ---- cross-check against published statistics ----
XS = []
F1 = rd('report/paper-figures-20261127/F1_policy_waf_by_batch.csv')
for r in F1:
    k = inv(r['group'])
    if k in GI and (k, r['metric']) in STATS and r['mean'] not in ('', None):
        s = STATS[(k, r['metric'])]
        for f in ('mean', 'sd', 'ci95_lo', 'ci95_hi'):
            mine = s[{'ci95_lo': 'ci_lo', 'ci95_hi': 'ci_hi'}.get(f, f)]
            try: float(r[f])
            except (TypeError, ValueError): continue
            if mine == '': continue
            XS.append(dict(what=f'{k} {r["metric"]} {f}', published=float(r[f]), recomputed=mine, source='report/paper-figures-20261127/F1_policy_waf_by_batch.csv'))
for r in rd('result/batchG-20261126-verify/stats.csv') + rd('result/arm47-20261127-verify/stats.csv'):
    if r['group'] in GI and r['metric'] in ('waf', 'waf_A', 'waf_B', 'waf_C') and r['n_valid'] == '3' and GI[r['group']][2].split('-')[0] in r['batch']:
        for f in ('mean', 'sd', 'ci_lo', 'ci_hi'):
            XS.append(dict(what=f'{r["group"]} {r["metric"]} {f}', published=float(r[f]), recomputed=STATS[(r['group'], r['metric'])][f], source='result/*-verify/stats.csv (GoCom og_audit)'))
SCM = {'total_waf': 'waf', 'A_waf': 'waf_A', 'B_waf': 'waf_B', 'C_waf': 'waf_C', 'C_first5min_waf': 'waf_C5'}
for r in scshow('result/arm47-20261127-analysis/statistics.csv'):
    if r['metric'] in SCM:
        for f in ('mean', 'sd', 'ci_lo', 'ci_hi'):
            XS.append(dict(what=f'arm47 {SCM[r["metric"]]} {f}', published=float(r[f]), recomputed=STATS[('arm47', SCM[r['metric']])][f], source=f'SeungCom {SC_FULL[:9]}:result/arm47-20261127-analysis/statistics.csv'))
for r in scshow('result/batchG-20261126-analysis/statistics.csv'):
    k = {'bg-v4': 'bg-v4', 'greedygc': 'greedygc', 'drift50': 'drift50'}.get(r['policy'])
    if k and r['metric'] in SCM:
        for f in ('mean', 'sd'):
            XS.append(dict(what=f'{k} {SCM[r["metric"]]} {f}', published=float(r[f]), recomputed=STATS[(k, SCM[r['metric']])][f], source=f'SeungCom {SC_FULL[:9]}:result/batchG-20261126-analysis/statistics.csv'))
SMK = {'revD-v4': 'revD-v4', 'abl-v4': 'abl-v4', 'abl-nodiscount': 'abl-nodiscount', 'abl-off-elim-settle-drift-probe': 'abl-offbundle', 'greedy-online': 'greedy'}
SEC = scshow('result/secondary-metrics-20261126/statistics.csv')
for r in SEC:
    if r['metric'] == 'C_first5min_waf' and r['policy'] in SMK:
        for f in ('mean', 'sd'):
            XS.append(dict(what=f'{SMK[r["policy"]]} waf_C5 {f}', published=float(r[f]), recomputed=STATS[(SMK[r['policy']], 'waf_C5')][f], source=f'SeungCom {SC_FULL[:9]}:result/secondary-metrics-20261126/statistics.csv'))
# contrasts
for r in rd('report/paper-figures-20261127/F3_contrasts_same_batch.csv'):
    a, b = [inv(x.strip()) for x in r['contrast'].split(' - ')]; m = r['metric']; sgn = 1
    c = CK.get((f'{a} − {b}', m)) or CK.get((f'{b} − {a}', m))
    if not c or 'delta' not in c or r['delta'] in ('', None) or c.get('ci_lo', '') == '' or r.get('welch95_lo', '') in ('', None): continue
    if c['contrast'] != f'{a} − {b}': sgn = -1
    for f, g2 in (('delta', 'delta'), ('welch95_lo', 'ci_lo' if sgn > 0 else 'ci_hi'), ('welch95_hi', 'ci_hi' if sgn > 0 else 'ci_lo')):
        XS.append(dict(what=f'{r["contrast"]} {m} {f}', published=float(r[f]), recomputed=sgn * c[g2], source='report/paper-figures-20261127/F3_contrasts_same_batch.csv'))
for r in rd('result/batchG-20261126-verify/contrasts.csv') + rd('result/arm47-20261127-verify/contrasts.csv'):
    a, b = [x.strip() for x in r['contrast'].split(' - ')]; m = r['metric']
    c = CK.get((f'{a} − {b}', m)); sgn = 1
    if not c: c = CK.get((f'{b} − {a}', m)); sgn = -1
    if c and c.get('ci_lo', '') != '':
        XS.append(dict(what=f'{r["contrast"]} {m} delta', published=float(r['diff']), recomputed=sgn * c['delta'], source='result/*-verify/contrasts.csv'))
for r in scshow('result/batchG-20261126-analysis/contrasts.csv'):
    k = r['contrast'].split(' - '); m = SCM.get(r['metric'])
    c = CK.get((f'{k[0]} − {k[1]}', m)) if m else None
    if c and c.get('p', '') != '':
        XS.append(dict(what=f'{r["contrast"]} {m} p', published=float(r['p']), recomputed=c['p'], source='SeungCom batchG contrasts.csv'))
        if r['holm_p_4primary']: XS.append(dict(what=f'{r["contrast"]} {m} Holm', published=float(r['holm_p_4primary']), recomputed=c['holm_p'], source='SeungCom batchG contrasts.csv'))
for r in rd('report/paper-figures-20261127/T1_revC_contrasts_holm.csv'):
    a, b = [x.strip() for x in r['contrast'].split(' - ')]; m = {'total': 'waf', 'phase_C': 'waf_C', 'C': 'waf_C'}.get(r['metric'], r['metric'])
    a = {'revB-arm60': 'revC-arm60', 'online': 'revC-online'}.get(a, a); c = CK.get((f'{a} − {b}', m))
    if c and r.get('holm_p_sensitivity'):
        XS.append(dict(what=f'{r["contrast"]} {m} Welch p', published=float(r['welch_p']), recomputed=c['p'], source='report/paper-figures-20261127/T1_revC_contrasts_holm.csv'))
        XS.append(dict(what=f'{r["contrast"]} {m} Holm', published=float(r['holm_p_sensitivity']), recomputed=c['holm_p'], source='T1_revC_contrasts_holm.csv (family as published)'))
KNOWN_HOLM = [('revD-fullreset − revD-v4', 'waf', 0.072, 'result/revD-20261124-verify/verify.md'), ('revD-fullreset − revD-v4', 'waf_C', 0.060, 'same'),
              ('revE-noelim − revE-v4', 'waf', 0.091, 'report/final-revision/revE_final.md'), ('revE-drift12 − revE-v4', 'waf', 0.091, 'same'),
              ('abl-offbundle − abl-v4', 'waf', 0.028, 'result/abl-20261125-verify/verify.md (SeungCom value)')]
for c_, m, v, s in KNOWN_HOLM:
    XS.append(dict(what=f'{c_} {m} Holm', published=v, recomputed=CK[(c_, m)]['holm_p'], source=s, tol=0.0005))
for x in XS:
    tol = x.pop('tol', 1e-6 if 'Holm' not in x['what'] and ' p' not in x['what'] else 1e-4)
    x['abs_diff'] = abs(x['published'] - x['recomputed']); x['rel_diff'] = x['abs_diff'] / abs(x['published']) if x['published'] else ''
    x['tolerance'] = tol; x['match'] = x['abs_diff'] <= tol or (x['published'] and x['abs_diff'] / abs(x['published']) < 1e-6) or ('Holm' in x['what'] and round(x['recomputed'], 3) == round(x['published'], 3))
print('cross-check items:', len(XS), 'mismatches:', [(x['what'], x['published'], x['recomputed'], x['source']) for x in XS if not x['match']])


# ------------------------------------------------------------- other data sources --------------------------------------------------------
P2 = 'report/paper-figures-20261127/'
F5 = rd(P2 + 'F5_adaptation_summary.csv'); F6L = rd(P2 + 'F6_latency_stats.csv'); F6K = rd(P2 + 'F6_learner_elapsed_ktime.csv')
F7 = rd(P2 + 'F7_smartgc_waf.csv'); F4 = rd(P2 + 'F4_revC_E2E6E7_secondary.csv'); T2 = rd(P2 + 'T2_parameters.csv')
M1D = 'result/m1-20261126-final/'
M1W = rd(M1D + 'waf_and_integrity.csv'); M1K = rd(M1D + 'kernel_elapsed_time.csv'); M1M = rd(M1D + 'memory_comparison.csv')
M1T = rd(M1D + 'memory_theoretical.csv'); M1MM = rd(M1D + 'memory_measured.csv'); M1C = rd(M1D + 'common_vs_algorithm_cost.csv'); M1U = rd(M1D + 'userspace_cpu_time.csv')
# GoCom SmartGC mixY single runs (gocom-sg-20261119): WAF recomputed from summary/final-control
GSG = []
for d in sorted(L('result/gocom-sg-20261119').glob('mixY-*-rep1')):
    t = re.search(r'^total .*host_pages=(\d+) gc_pages=(\d+)', (d / 'summary.txt').read_text(), re.M) if (d / 'summary.txt').exists() else None
    ex = (d / 'exit-code.txt').read_text().strip() if (d / 'exit-code.txt').exists() else 'missing'
    sm = (d / 'summary.txt').read_text(errors='replace') if (d / 'summary.txt').exists() else ''
    nand = re.search(r'waf_nand=([\d.]+)', sm)
    GSG.append(dict(run=d.name, exit=ex, host_pages=int(t[1]) if t else '', gc_pages=int(t[2]) if t else '', waf_1_plus_gc_over_host=1 + int(t[2]) / int(t[1]) if t else '',
                    waf_nand_summary=float(nand[1]) if nand else '', raw_dir=pub(d)))
SC_SEC = SEC
# ---- time series (revA, GoCom, 5-min windows from phase A start) ----
BIN = 300; NB = 18
TS = {}
for k in ('revA-v4', 'revA-random', 'revA-v1', 'revA-v2'):
    per = []
    for r in by(k):
        ser, t0 = r['_series'], r['_t0']; w = []
        for i in range(NB):
            a, b = at(ser, t0 + i * BIN), at(ser, t0 + (i + 1) * BIN)
            w.append(1 + (b[2] - a[2]) / (b[1] - a[1]) if a and b and b[1] > a[1] else None)
        per.append(w)
    TS[k] = per
prov('Workload Adaptation', 'time-resolved WAF (5-min windows), revA GoCom n=3 per policy', 'control-series.txt of each revA run', 'recomputed: 1+Δgc/Δhost between first 30 s samples at/after A-start + 300 s·i')

# ===================================================================== WORKBOOK ===========================================================
wb = Workbook(); CSVS = {}
f4 = lambda x: '' if x in ('', None) else round(x, 4) if isinstance(x, float) else x


def csvdump(name, header, rows):
    CSVS[name] = (header, rows)


def intro(ws, title, items, r=0):
    ws.width(0, 26); ws.width(1, 110)
    ws.write(r, 0, title, 'title'); r += 2
    for k, v in items:
        ws.write(r, 0, k, 'bold'); ws.write(r, 1, v, 'wrap'); r += 1
    return r + 1


def table(ws, r, c, title, header, rows, name=None, note=None):
    ws.write(r, c, title, 'bold'); r += 1
    if note: ws.write(r, c, note, 'note'); r += 1
    a, b = ws.table(r, c, header, rows)
    if name: csvdump(name, header, rows)
    return a, b, r + len(rows) + 2


def gstat_rows(keys, metrics=('waf', 'waf_A', 'waf_B', 'waf_C')):
    out = []
    for k in keys:
        for m in metrics:
            s = STATS[(k, m)]
            out.append([GI[k][1], GI[k][2], k, GI[k][3], m, s['n'], s['values'], f4(s['mean']), f4(s['sd']), f4(s['ci_lo']), f4(s['ci_hi']), s['note']])
    return out


GH = ['호스트', '배치', '그룹', '정책', '지표', 'n', '개별 값 (rep1/2/3)', '평균', 'SD', '95% CI 하한', '95% CI 상한', '비고']
CH = ['대비 (정책 − 대조군)', '종류', '호스트', '배치', '지표', 'n', 'Δ', 'Welch 95% CI 하한', 'Welch 95% CI 상한', 'df', 'p (보정 전)', 'Holm p', 'Holm 대비 수', 'Hedges g', 'Δ %', '판정']


def con_rows(pairs, metrics=('waf', 'waf_A', 'waf_B', 'waf_C', 'waf_C5')):
    out = []
    for a, b in pairs:
        for m in metrics:
            c = CK[(f'{a} − {b}', m)]
            out.append([c['contrast'], c['kind'], c['host'], c['batch'], m, c['n'], f4(c.get('delta', '')), f4(c.get('ci_lo', '')), f4(c.get('ci_hi', '')),
                        f4(c.get('df', '')), f4(c.get('p', '')), f4(c.get('holm_p', '')), c.get('holm_k', ''), f4(c.get('hedges_g', '')), f4(c.get('rel_pct', '')), c['verdict']])
    return out


def run_rows(keys):
    return [[r['host'], r['batch'], r['key'], r['policy'], r['rep'], r['valid_recomputed'], f4(r['waf']), f4(r['waf_A']), f4(r['waf_B']), f4(r['waf_C']), f4(r['waf_C5']),
             r['raw_dir']] for k in keys for r in by(k)]


RH = ['호스트', '배치', '그룹', '정책', 'rep', '유효', '전체 WAF', 'A', 'B', 'C', 'C 첫 5분', '원시 경로']


def chart_table(ws, r, c, title, labels, cols, values, note=None):
    """values: list of rows (label, v1, v2, ...). returns (first_row, last_row, next_r)."""
    ws.write(r, c, title, 'bold'); r += 1
    if note: ws.write(r, c, note, 'note'); r += 1
    ws.row(r, c, cols, 'head')
    for i, row in enumerate(values): ws.row(r + 1 + i, c, [f4(x) if isinstance(x, float) else x for x in row])
    return r + 1, r + len(values), r + len(values) + 2


def bar_mean_ci(ws, r, c, keys, metric, title, ytitle, name, label=lambda k: f'{GI[k][3]} [{GI[k][1]} {GI[k][2]}]', ar=None, ac=8, ymin=None):
    vals = []
    for k in keys:
        s = STATS[(k, metric)]; lab = label(k) + (' (n=1 단일 실행)' if s['n'] == 1 else '')
        vals.append([lab, s['mean'], s['ci_half'] if s['ci_half'] != '' else '', s['n']])
    a, b, nr = chart_table(ws, r, c, f'[그래프 데이터] {title}', None, ['정책 [호스트 배치]', '평균', '95% CI 반폭', 'n'], vals)
    csvdump(name, ['label', 'mean', 'ci_half', 'n'], vals)
    ws.chart('bar', ar if ar is not None else r, ac, [dict(name='평균 ± 95% CI (n=3), n=1은 오차 막대 없음', cat=(a, c, b, c), val=(a, c + 1, b, c + 1), plus=(a, c + 2, b, c + 2), minus=(a, c + 2, b, c + 2))],
             title=title, y_title=ytitle, x_title='', legend=True, y_min=ymin, w=10, h=20)
    return nr


def delta_chart(ws, r, c, pairs, metric, title, name, ar=None, ac=8, h=22):
    vals = []
    for a, b in pairs:
        cc = CK[(f'{a} − {b}', metric)]
        if cc.get('ci_lo', '') == '': continue
        lab = f'{GI[a][3]} − {GI[b][3]} [{GI[a][1]} {cc["batch"]}]'
        d = cc['delta']; direct = cc['kind'] == 'direct'
        vals.append([lab, d if direct else '', d if not direct else '', cc['ci_hi'] - d, d - cc['ci_lo'], cc['verdict']])
    a0, b0, nr = chart_table(ws, r, c, f'[그래프 데이터] {title}', None, ['대비 [호스트 배치]', 'Δ 직접 (같은 배치)', 'Δ 간접 (다른 배치)', 'CI 위쪽 길이', 'CI 아래쪽 길이', '판정'], vals)
    csvdump(name, ['contrast', 'delta_direct', 'delta_indirect', 'ci_plus', 'ci_minus', 'verdict'], vals)
    ser = [dict(name='직접 비교 (같은 호스트·같은 배치) Δ ± Welch 95% CI', cat=(a0, c, b0, c), val=(a0, c + 1, b0, c + 1), plus=(a0, c + 3, b0, c + 3), minus=(a0, c + 4, b0, c + 4))]
    if any(v[2] != '' for v in vals):
        ser.append(dict(name='간접 비교 (다른 배치, 해석 주의) Δ ± Welch 95% CI', cat=(a0, c, b0, c), val=(a0, c + 2, b0, c + 2), plus=(a0, c + 3, b0, c + 3), minus=(a0, c + 4, b0, c + 4)))
    ws.chart('bar', ar if ar is not None else r, ac, ser, title=title, y_title=f'Δ {metric} (정책 − 같은 배치 V4). 0보다 크면 V4보다 WAF 높음(나쁨)', w=11, h=h, gap=60)
    return nr


S = lambda k, m='waf': STATS[(k, m)]
fmt = lambda c: f"{c['delta']:+.3f} [{c['ci_lo']:+.3f}, {c['ci_hi']:+.3f}]"
cc = lambda a, b, m='waf': CK[(f'{a} − {b}', m)]
hp = lambda x: '<0.0001' if x < 1e-4 else f'{x:.4f}'

# ---------------------------------------------------------------- 1. Executive Summary ----------------------------------------------------
ws = wb.sheet('Executive Summary')
r = intro(ws, 'iCAT 논문 리비전 — 전체 실험 결과 통합 (고컴, 2026-11-27)', [
    ('생성', f'analysis/final_revision/complete_results.py, report 브랜치 HEAD {HEAD[:9]}, 승컴 원시 자료 origin/main {SC_FULL[:9]} (git archive, 읽기 전용)'),
    ('원칙', 'WAF는 낮을수록 좋다. 모든 WAF는 원시 카운터에서 이 스크립트가 다시 계산했다. 호스트(고컴 AMD Ryzen 5 3600XT / 승컴 Intel i7-7700)와 배치가 다르면 합치지 않는다. '
            '판정은 같은 배치 대조군과의 Welch 95% CI(0 제외 = 차이 있음). n<3은 통계를 내지 않는다. 다른 배치 비교는 "간접"으로 표시한다.'),
    ('측정 구분', '실측 = 원시 로그 카운터/측정값. 계산 = 자료구조 크기(sizeof×개수) 등 이론값. 유도 = 실측값 간 차. ktime 경과 시간은 CPU 시간이 아니다.'),
    ('재계산 일치', f'run {len(RUNS)}개 재계산, 기존 게시값과 일치 {sum(r["matches_published"] for r in RUNS)}/{len(RUNS)}. 통계 대조 {len(XS)}항목 중 일치 {sum(x["match"] for x in XS)} (Statistical Analysis 시트).'),
])
ex = [
    ['M3 Random Selection', '고컴 revA', '3 vs 3', 'Random − V4, 전체 WAF', fmt(cc('revA-random', 'revA-v4')), hp(cc('revA-random', 'revA-v4')['holm_p']), cc('revA-random', 'revA-v4')['verdict'], 'V4가 무작위 선택보다 WAF 낮음'],
    ['M3 원래 iCAT', '고컴 revC', '3 vs 3', '원래 iCAT − V4', fmt(cc('revC-online', 'revC-v4')), hp(cc('revC-online', 'revC-v4')['holm_p']), cc('revC-online', 'revC-v4')['verdict'], 'V4 개선 확인'],
    ['M3 Online Greedy', '승컴 greedy vs revD', '3 vs 3', 'Greedy − revD-V4 (간접)', fmt(cc('greedy', 'revD-v4')), '-', cc('greedy', 'revD-v4')['verdict'], 'Greedy 대비 이득 주장 불가. 단계 C 첫 5분은 Greedy가 낮음 (Secondary Metrics)'],
    ['M3 Greedy GC', '승컴 batchG', '3 vs 3', 'Greedy GC − V4', fmt(cc('greedygc', 'bg-v4')), hp(cc('greedygc', 'bg-v4')['holm_p']), cc('greedygc', 'bg-v4')['verdict'], 'V4가 학습 없는 Greedy GC보다 WAF 낮음. FIO p99는 Greedy GC가 낮음(승컴 계산)'],
    ['M2 V2 (제거·정착 끔)', '고컴 revA', '3 vs 3', 'V2 − V4', fmt(cc('revA-v2', 'revA-v4')), hp(cc('revA-v2', 'revA-v4')['holm_p']), cc('revA-v2', 'revA-v4')['verdict'], ''],
    ['M2 V1 (감지 끔)', '고컴 revA', '3 vs 3', 'V1 − V4', fmt(cc('revA-v1', 'revA-v4')), hp(cc('revA-v1', 'revA-v4')['holm_p']), cc('revA-v1', 'revA-v4')['verdict'], ''],
    ['M2 NoDrift', '승컴 revD', '3 vs 3', 'NoDrift − V4', fmt(cc('revD-nodrift', 'revD-v4')), hp(cc('revD-nodrift', 'revD-v4')['holm_p']), cc('revD-nodrift', 'revD-v4')['verdict'], ''],
    ['M2 FullReset', '승컴 revD', '3 vs 3', 'FullReset − V4', fmt(cc('revD-fullreset', 'revD-v4')), hp(cc('revD-fullreset', 'revD-v4')['holm_p']), cc('revD-fullreset', 'revD-v4')['verdict'], 'Holm 후 경계'],
    ['M2 NoElim', '고컴 revE', '3 vs 3', 'NoElim − V4', fmt(cc('revE-noelim', 'revE-v4')), hp(cc('revE-noelim', 'revE-v4')['holm_p']), cc('revE-noelim', 'revE-v4')['verdict'], 'Holm 후 경계'],
    ['M2 NoDiscount', '승컴 abl', '3 vs 3', 'NoDiscount − V4', fmt(cc('abl-nodiscount', 'abl-v4')), hp(cc('abl-nodiscount', 'abl-v4')['holm_p']), cc('abl-nodiscount', 'abl-v4')['verdict'], ''],
    ['M2 묶음 끔', '승컴 abl', '3 vs 3', '묶음 끔 − V4', fmt(cc('abl-offbundle', 'abl-v4')), hp(cc('abl-offbundle', 'abl-v4')['holm_p']), cc('abl-offbundle', 'abl-v4')['verdict'], ''],
    ['M6 감지 12.5 %', '고컴 revE', '3 vs 3', '12.5 % − 25 %(V4)', fmt(cc('revE-drift12', 'revE-v4')), hp(cc('revE-drift12', 'revE-v4')['holm_p']), cc('revE-drift12', 'revE-v4')['verdict'], 'Holm 후 경계'],
    ['M6 감지 50 %', '승컴 batchG', '3 vs 3', '50 % − 25 %(V4)', fmt(cc('drift50', 'bg-v4')), hp(cc('drift50', 'bg-v4')['holm_p']), cc('drift50', 'bg-v4')['verdict'], ''],
    ['M6 제거 문턱 10/25 %', '고컴 revC', '3 vs 3', '10 % − 15 %, 25 % − 15 %', f"{fmt(cc('revC-elim10', 'revC-v4'))}; {fmt(cc('revC-elim25', 'revC-v4'))}", '-', '구분되지 않음', ''],
    ['M6 후보 60 arms', '고컴 revC', '3 vs 3', '60 − 45 arms', fmt(cc('revC-arm60', 'revC-v4')), '-', cc('revC-arm60', 'revC-v4')['verdict'], ''],
    ['Robustness Arm 47', '승컴 arm47', '3', '고정 Arm 47 전체 WAF', f"{S('arm47')['mean']:.5f} ± {S('arm47')['sd']:.5f} [{S('arm47')['ci_lo']:.5f}, {S('arm47')['ci_hi']:.5f}]", '-', '재현됨', f"고컴 n=1 {S('revA-arm47')['mean']:.5f}이 승컴 CI 안. 합산하지 않음"],
    ['M1 SmartGC (WAF_nand)', '고컴 m1-20261126', '1 vs 1', 'iCAT-v4 / SmartGC-EQ8', f"{float(M1W[0]['waf_nand']):.3f} / {float(M1W[1]['waf_nand']):.3f}", '-', 'n=1: 통계 없음', '방향만 보고'],
    ['M1 메모리', '고컴 m1-20261126', '1 vs 1', '학습 자료구조 (계산)', '10,112 B / 1,951,648 B', '-', '계산값', 'VmallocUsed 차 2,904 kB (실측) vs 계산 3,057.6 KiB'],
    ['M1 GC 경과 시간', '고컴 m1-20261126', '1 vs 1', 'GC 1회 평균 (ktime 경과, CPU 시간 아님)', '98.4 µs / 17.8 µs', '-', 'n=1', 'iCAT GC가 더 길다. iCAT이 빠르다고 주장하지 않는다'],
]
_, _, r = table(ws, r, 0, '핵심 결과 (Δ = 정책 − 대조군, WAF 낮을수록 좋음)', ['실험', '호스트·배치', 'n', '비교', 'Δ [Welch 95% CI] 또는 값', 'Holm p', '판정', '비고'], ex, 'executive_summary')
for i, w in enumerate([22, 18, 8, 26, 34, 9, 18, 50]): ws.width(i, w)
ws.width(1, 18)
unmet = [['M1 정책당 3회 반복', '미충족 (사용자 결정으로 정책당 1회, 4회 CANCELLED)'], ['M1 커널 안 CPU 시간', '측정 불가 (perf 없음, busy-poll). ktime 경과·사용자 공간 CPU로 대체'],
         ['M1 지연 p50/p95/p99 (GC 구간)', '계측이 호출별 값을 남기지 않음'], ['M3 Periodic Switching', '실행하지 않음'], ['M3 Greedy 대비 이득', '구분되지 않음 (간접 비교)'],
         ['M6 판단 구간·UCB 계수·수렴 조건·할인 계수 수준별', '측정하지 않음 (512 MiB 창 실험 미승인)'], ['감지 문턱 15 %', '실행한 적 없음. 측정 수준은 12.5 %(고컴 revE), 25 %(기본값), 50 %(승컴 batchG). 15 %는 제거 문턱의 기본값이다'],
         ['같은 배치 Arm 47 − V4', '미측정 (승컴 제안: V4 ×3, 약 4.7 h, 미승인)'], ['revB V4·60 arms', 'n=1 (revB 대비는 통계 없음. revC에서 n=3으로 다시 측정)'],
         ['집컴 독립 검증', 'M1 최종, 데이터북, batchG, arm47, 이 통합 Excel 모두 요청 전달 필요']]
_, _, r = table(ws, r, 0, '미충족·한계 항목', ['항목', '상태'], unmet, 'unmet_items')
ALLK = [g[0] for g in GROUPS]
lab = lambda k: f"{GI[k][3]} [{GI[k][2].split('-')[0]}]" + (' (n=1 단일)' if S(k)['n'] == 1 else '')
vals = [[lab(k), S(k)['mean'] if GI[k][1] == '고컴' else '', S(k)['mean'] if GI[k][1] == '승컴' else '', S(k)['ci_half'], S(k)['n']] for k in ALLK]
a0, b0, r = chart_table(ws, r, 0, '[그래프 데이터] 그림 1. 정책별 전체 WAF (배치별, 평균 ± 95% CI). 배치가 다르면 막대끼리 직접 비교하지 않는다', None,
                        ['정책 [배치]', '고컴 평균', '승컴 평균', '95% CI 반폭', 'n'], vals)
csvdump('chart01_policy_total_waf', ['label', 'gocom_mean', 'seungcom_mean', 'ci_half', 'n'], vals)
ws.chart('bar', 2, 9, [dict(name='고컴 (AMD) 평균 ± 95% CI', cat=(a0, 0, b0, 0), val=(a0, 1, b0, 1), plus=(a0, 3, b0, 3)),
                       dict(name='승컴 (Intel) 평균 ± 95% CI', cat=(a0, 0, b0, 0), val=(a0, 2, b0, 2), plus=(a0, 3, b0, 3))],
         title='그림 1. 정책별 전체 WAF (mixFYF, 배치별 n=3; n=1은 오차 막대 없음). 같은 배치 안에서만 비교', y_title='전체 WAF (낮을수록 좋음)', w=16, h=26, y_min=1.8, gap=40)
vals = [[lab(k)] + [x for m in ('waf_A', 'waf_B', 'waf_C') for x in (S(k, m)['mean'], S(k, m)['ci_half'])] for k in ALLK]
a1, b1, r = chart_table(ws, r, 0, '[그래프 데이터] 그림 2. 단계 A/B/C WAF (평균 ± 95% CI)', None, ['정책 [배치]', 'A 평균', 'A CI 반폭', 'B 평균', 'B CI 반폭', 'C 평균', 'C CI 반폭'], vals)
csvdump('chart02_phase_waf', ['label', 'A_mean', 'A_ci_half', 'B_mean', 'B_ci_half', 'C_mean', 'C_ci_half'], vals)
ws.chart('bar', 30, 9, [dict(name=f'단계 {p} ({d})', cat=(a1, 0, b1, 0), val=(a1, 1 + 2 * i, b1, 1 + 2 * i), plus=(a1, 2 + 2 * i, b1, 2 + 2 * i))
                        for i, (p, d) in enumerate((('A', 'FIO'), ('B', 'YCSB-A'), ('C', 'FIO 복귀')))],
         title='그림 2. 단계별 WAF (mixFYF; A FIO → B YCSB-A → C FIO). 배치가 다르면 직접 비교하지 않는다', y_title='단계 WAF (낮을수록 좋음)', w=16, h=26, gap=40)
ws.write(r, 0, '시트 안내', 'bold'); r += 1
for i, s in enumerate(['Experiment Inventory', 'Random Selection', 'Ablation Study', 'Online Greedy', 'Greedy GC', 'Workload Adaptation', 'Drift Threshold', 'SmartGC Comparison',
                       'Memory Overhead', 'CPU and Timing', 'Arm 47 Robustness', 'Secondary Metrics', 'Statistical Analysis', 'Run Validity', 'Raw Results', 'Reviewer Evidence Matrix']):
    ws.write(r + i, 0, f'{i + 2}. {s}')

# ---------------------------------------------------------------- 2. Experiment Inventory --------------------------------------------
ws = wb.sheet('Experiment Inventory')
r = intro(ws, '실험 목록 (리비전 실험 + 원 논문 Figure 자료 + 저장소의 기타 결과 디렉터리)', [
    ('범위', 'report/data-validity-20261124 브랜치의 result/, report/ 와 승컴 origin/main의 result/ 를 조사했다. 리비전 비교에 쓰는 mixFYF 배치는 모두 아래 표에 있고 Raw Results 시트에 run 단위로 연결된다.'),
    ('누락 조사', '요청 목록 중 "drift15"는 존재하지 않는다(감지 문턱 측정 수준은 12.5/25/50 %). Periodic Switching, 판단 구간 민감도는 실행되지 않았다. 나머지는 모두 원시 로그를 찾았다.')])
inv_rows = []
EXPS = [('revA-20261114', '고컴', 'M2·M3', 'V4 / V1 / V2 / Random / 고정 Arm 47(n=1)', 'mixFYF 90분 (FIO→YCSB-A→FIO)', 'Random Selection, Ablation Study, Arm 47'),
        ('revB-20261122', '고컴', 'M2', 'V4(n=1) / NoElim / NoSettle / 60 arms(n=1)', 'mixFYF', 'Ablation Study (대조군 n=1 → 통계 없음)'),
        ('revC-20261124', '고컴', 'M3·M6', 'V4 / 제거 10 % / 25 % / 60 arms / 원래 iCAT', 'mixFYF', 'Ablation Study, Online Greedy(원래 iCAT)'),
        ('revD-20261124', '승컴', 'M2', 'V4 / NoDrift / FullReset', 'mixFYF', 'Ablation Study, Drift Threshold'),
        ('revE-20261125', '고컴', 'M2·M6', 'V4 / NoElim / 감지 12.5 %', 'mixFYF', 'Ablation Study, Drift Threshold'),
        ('abl-20261125', '승컴', 'M2', 'V4 / NoDiscount / 묶음 끔', 'mixFYF', 'Ablation Study'),
        ('greedy-20261125', '승컴', 'M3', 'Online Greedy (대조군 revD-v4, abl-v4: 다른 배치)', 'mixFYF', 'Online Greedy'),
        ('batchG-20261126', '승컴', 'M3·M6', 'V4 / Greedy GC / 감지 50 %', 'mixFYF', 'Greedy GC, Drift Threshold'),
        ('arm47-20261127', '승컴', 'Robustness', '고정 Arm 47 ×3', 'mixFYF', 'Arm 47 Robustness')]
for b, host, rv, pol, wl, sh in EXPS:
    rs = [r_ for r_ in RUNS if r_['batch'] == b]
    inv_rows.append([b, host, rv, pol, wl, len(rs), sum(r_['valid_recomputed'] for r_ in rs), sh, sorted({str(Path(r_['raw_dir']).parent) for r_ in rs})[0]])
inv_rows += [['smartgc-20261119 / gc-20261010', '승컴', 'M1', 'SmartGC-EQ8 / SmartGC / CAT-47 / iCAT-v4 (각 1)', 'mixY 20단계 10 h', 4, 4, 'SmartGC Comparison', 'result/smartgc-20261119/resume, result/gc-20261010'],
             ['gocom-sg-20261119', '고컴', 'M1 (보조)', 'SmartGC / SmartGC-Q / Greedy / Arm47 (각 1)', 'mixY', len(GSG), sum(g['exit'] == '0' for g in GSG), 'SmartGC Comparison', 'result/gocom-sg-20261119'],
             ['m1-20261126', '고컴', 'M1·M5', 'iCAT-v4 / SmartGC-EQ8 (구간 타이머 빌드, 각 1; 4회 CANCELLED)', 'mixY 20단계 10 h', 2, 2, 'Memory Overhead, CPU and Timing', '/home/oy/iCAT/result/m1-20261126/raw (요약 result/m1-20261126-final)'],
             ['bench (사용자 공간 sim)', '고컴', 'M1 CPU 대체', 'icat / smartgc-eq8, 각 seed 3', 'sim zones 60/30/10 % (mixY 아님)', 6, 6, 'CPU and Timing', 'analysis/bench_summary.tsv'],
             ['secondary-metrics-20261126', '승컴 (기존 로그 재분석)', 'M3·M6 보조', 'revD-v4, abl-*, greedy', '-', 15, 15, 'Secondary Metrics', f'origin/main {SC_FULL[:9]}:result/secondary-metrics-20261126']]
a, b, r = table(ws, r, 0, '리비전 실험 배치', ['배치', '호스트', '심사 의견', '정책', '부하', 'run 수', '유효 (재계산)', '시트', '원시 경로'], inv_rows, 'inventory_revision')
FIGS = [['그림 1', '60 조합 민감도 (FIO-Fast)', 'result/sweep-20260915/rank-test4.txt', '유효 (60/60)'],
        ['그림 2 / 표 4', '탐색 비용 (FIO-Fast 3 h)', 'result/mix-20260911/t4-*', '유효'],
        ['그림 3 / 표 5', '단일 워크로드 10 h, V4 개요', 't4-onlinev4-rep1-x60 등', '유효'],
        ['그림 4·5 (rank, v4 choices)', '단일 워크로드 순위/선택', 'figures.py fig9·fig10', '유효'],
        ['그림 6', 'iCAT-v3 구성 요소 제거', 't4-onlinev3*-rep1-x18', '유효 (각 n=1, 표기 유지)'],
        ['그림 7', '전환 13종 V4 vs CAT-Robust', 'mix{A..Q}-onlinev4/fixed50-*-x3', '일부 유효: 13종 중 8종. A,B,G,H,J 무효 (YCSB 실패)'],
        ['그림 8', '최상위 대비 손실', '같은 묶음', '11종 중 6종 유효 (C,D,F,K,O,P)'],
        ['그림 9', '견고성 6종', '같은 묶음', '검사 후 공통 집합 C,D,F,K,O,P'],
        ['그림 10 / 표 8', '3단계 균등 전환 (mixR 9월)', 'mixR-*-x3', '단계 1만 유효. 논문 사용 불가 → mixFYF 리비전 실험으로 대체'],
        ['표 6', '4종 × 고정 조합 6개', 'mix{O,F,J,P}-*-x3', 'J 행 무효']]
a, b, r = table(ws, r, 0, '원 논문 Figure 1~10 자료 (근거: report/final-e1-validation/paper_data_validity_matrix.md, 이 Excel은 수치를 다시 만들지 않고 상태만 연결)',
                ['논문 항목', '내용', '원시 자료', '데이터 상태'], FIGS, 'inventory_paper_figures')
loc = sorted(p.name for p in (ROOT / 'result').iterdir() if p.is_dir())
rem = sorted(set(l.split('/')[1] for l in GIT('ls-tree', '-d', '--name-only', SC_FULL, 'result/').split()) - set(loc))
used = {'revA-20261114', 'revB-20261122', 'revC-20261124', 'revE-20261125', 'gocom-sg-20261119', 'smartgc-20261119', 'gc-20261010', 'm1-20261126', 'm1-20261126-final',
        'm1-20261126-analysis', 'revD-20261124', 'revision-additional-ablation', 'greedy-20261125', 'batchG-20261126', 'greedygc-20261126', 'drift50-20261126', 'arm47-20261127',
        'secondary-metrics-20261126', 'revE-20261125-analysis', 'revC-20261124-analysis', 'final-revision-analysis', 'abl-20261125-verify', 'greedy-20261125-verify',
        'batchG-20261126-verify', 'arm47-20261127-verify', 'revD-20261124-verify', 'online-greedy-analysis', 'final-e1-validation'}
oth = [[d, '고컴 브랜치', '이 Excel에서 사용' if d in used else '리비전 이전 탐색·원 논문 자료 또는 보조 (이 Excel의 비교 통계에 쓰지 않음)'] for d in loc]
oth += [[d, f'승컴 origin/main {SC_FULL[:9]}', '이 Excel에서 사용' if d in used else '승컴 전용 (리비전 이전 탐색 또는 분석 산출물)'] for d in rem]
a, b, r = table(ws, r, 0, '저장소의 모든 result/ 디렉터리', ['디렉터리', '위치', '이 Excel에서의 사용'], oth, 'inventory_all_result_dirs')
for i, w in enumerate([30, 14, 14, 44, 26, 8, 10, 30, 60]): ws.width(i, w)


# ------------------------------------------------------------------ experiment sheet helper -------------------------------------------
def exp_intro(ws, title, why, hyp, rev, pols, cond, reps, result, meaning, can, cannot, limits, raw):
    return intro(ws, title, [('왜 진행했는가', why), ('검증 가설', hyp), ('심사 의견', rev), ('비교 정책', pols), ('실행 조건', cond), ('반복 횟수', reps),
                             ('결과', result), ('의미', meaning), ('논문에서 할 수 있는 주장', can), ('할 수 없는 주장', cannot), ('한계', limits), ('원시 데이터', raw)])


COND = 'NVMeVirt 8 GiB (MLC, OP 7 %, 4 파티션), mixFYF = FIO-Fast 1800 s → YCSB-A (SQLite 250k records) 1800 s → FIO-Fast 1800 s. FIO seed 20260910/20261010/20261110 + rep, icat_seed 2026111400 + rep.'

# ---------------------------------------------------------------- 3. Random Selection ----------------------------------------------------
ws = wb.sheet('Random Selection'); c1 = cc('revA-random', 'revA-v4'); c1C = cc('revA-random', 'revA-v4', 'waf_C')
r = exp_intro(ws, '3. Random Selection vs iCAT-v4 (M3)', '학습 없이 매 판단 구간마다 후보를 무작위로 고르는 기준선보다 iCAT 학습기가 나은지 확인한다.',
              'iCAT-v4의 WAF가 Random Selection보다 낮다.', 'M3 (온라인 기준선과 비교)', 'iCAT-v4 vs Random Selection (같은 45 arms 후보, 같은 판단 구간)', '고컴 revA-20261114. ' + COND,
              '정책당 3회 (같은 배치)', f"전체 WAF: V4 {S('revA-v4')['mean']:.4f} ± {S('revA-v4')['sd']:.4f}, Random {S('revA-random')['mean']:.4f} ± {S('revA-random')['sd']:.4f}. Random − V4 = {fmt(c1)} ({c1['rel_pct']:+.1f} %), Holm p = {hp(c1['holm_p'])}. 단계 C: {fmt(c1C)}.",
              '학습된 선택이 무작위 선택보다 WAF를 낮춘다. 모든 단계에서 같은 방향이다.', f"같은 배치 3회 반복에서 iCAT-v4의 WAF가 Random Selection보다 {abs(c1['rel_pct']):.1f} % 낮았다 (Welch 95 % CI가 0 제외, Holm 보정 후에도 유의).",
              '다른 호스트·워크로드에서도 같다는 주장. 지연이 개선된다는 주장 (FIO p99는 V4가 15–20 µs 높음, Secondary Metrics).', '한 호스트(고컴), 한 부하(mixFYF), n=3.', 'result/revA-20261114/raw/mixFYF-revA-{v4,random}-rep{1,2,3}')
a, b, r = table(ws, r, 0, '개별 실행', RH, run_rows(['revA-v4', 'revA-random']))
a, b, r = table(ws, r, 0, '기술 통계 (t 95 % CI)', GH, gstat_rows(['revA-v4', 'revA-random']))
a, b, r = table(ws, r, 0, '대비 (Welch)', CH, con_rows([('revA-random', 'revA-v4')]))
rr = r
ws.write(rr, 0, '[그래프 데이터] Random vs iCAT: 단계별 평균 WAF ± 95% CI (고컴 revA, 각 n=3). WAF는 낮을수록 좋다', 'bold'); rr += 1
ws.row(rr, 0, ['단계', 'iCAT-v4 평균', 'iCAT-v4 CI 반폭', 'Random 평균', 'Random CI 반폭'], 'head')
ph = []
for i, (m, ml) in enumerate(METRICS[:4]):
    ph.append([ml, S('revA-v4', m)['mean'], S('revA-v4', m)['ci_half'], S('revA-random', m)['mean'], S('revA-random', m)['ci_half']])
    ws.row(rr + 1 + i, 0, [ml] + [f4(x) for x in ph[-1][1:]])
csvdump('chart03_random_vs_icat', ['phase', 'v4_mean', 'v4_ci_half', 'random_mean', 'random_ci_half'], ph)
ws.chart('bar', 2, 3, [dict(name='iCAT-v4 (n=3)', cat=(rr + 1, 0, rr + 4, 0), val=(rr + 1, 1, rr + 4, 1), plus=(rr + 1, 2, rr + 4, 2)),
                       dict(name='Random Selection (n=3)', cat=(rr + 1, 0, rr + 4, 0), val=(rr + 1, 3, rr + 4, 3), plus=(rr + 1, 4, rr + 4, 4))],
         title='그림 3. Random Selection vs iCAT-v4 (고컴 revA, 같은 배치)', y_title='WAF (낮을수록 좋음), 오차 막대 = 95% CI', w=9, h=22)
prov('Random Selection', 'all values', 'Raw Results rows revA-v4 / revA-random', 'recomputed (this script)')

# ---------------------------------------------------------------- 4. Ablation Study -----------------------------------------------------
ws = wb.sheet('Ablation Study')
ABL = [('revA-v1', 'revA-v4'), ('revA-v2', 'revA-v4'), ('revB-noelim', 'revB-v4'), ('revB-nosettle', 'revB-v4'), ('revB-arm60', 'revB-v4'), ('revC-elim10', 'revC-v4'),
       ('revC-elim25', 'revC-v4'), ('revC-arm60', 'revC-v4'), ('revD-nodrift', 'revD-v4'), ('revD-fullreset', 'revD-v4'), ('revE-noelim', 'revE-v4'),
       ('revE-drift12', 'revE-v4'), ('abl-nodiscount', 'abl-v4'), ('abl-offbundle', 'abl-v4'), ('abl-offbundle', 'abl-nodiscount')]
r = exp_intro(ws, '4. 구성 요소 제거 실험 (M2, 일부 M6)', 'iCAT-v4의 각 구성 요소(변화 감지, 실행 중 후보 제거, 수렴 후 정착, 할인, 부분 재설정)가 WAF에 기여하는지 확인한다.',
              '구성 요소를 끄면 같은 배치 V4보다 WAF가 높아진다.', 'M2 (구성 요소 제거), M6 (파라미터 근거)',
              'V1 감지 끔, V2 제거·정착 끔, NoElim, NoSettle, NoDrift, FullReset, NoDiscount, 묶음 끔(제거+정착+감지+probe), 제거 문턱 10/25 %, 후보 60 arms, 감지 12.5 %',
              '배치마다 같은 배치 V4 대조군. revA·revC·revE 고컴, revD·abl 승컴. ' + COND, '정책당 3회. revB의 V4와 60 arms는 n=1이라 revB 대비는 통계 없음',
              f"차이 있음: V2 {fmt(cc('revA-v2', 'revA-v4'))}, FullReset {fmt(cc('revD-fullreset', 'revD-v4'))}, NoElim(revE) {fmt(cc('revE-noelim', 'revE-v4'))}, 묶음 끔 {fmt(cc('abl-offbundle', 'abl-v4'))}. "
              f"구분되지 않음: V1 {fmt(cc('revA-v1', 'revA-v4'))}, NoDrift {fmt(cc('revD-nodrift', 'revD-v4'))}, NoDiscount {fmt(cc('abl-nodiscount', 'abl-v4'))}, 제거 10/25 %, 60 arms.",
              '후보 제거·정착(묶음)이 WAF 이득의 주요 원천이다. 변화 감지 단독 효과와 할인은 이 부하에서 확인되지 않았다.',
              '제거와 정착을 함께 끄면 WAF가 높아진다(같은 배치 n=3). 실행 중 제거만 꺼도 높아진다(Holm 후 경계). 묶음 끔 +0.124.',
              '변화 감지가 WAF를 낮춘다는 주장 (두 호스트 모두 구분되지 않음). 할인이 효과가 있다는 주장. 서로 다른 배치의 효과 크기를 합친 값.',
              '배치마다 V4 값이 0.03 정도 다르다 → 배치 간 Δ를 직접 비교하지 않는다. revB 대비는 대조군 n=1.', 'Raw Results 시트의 raw_dir (revA/B/C/E 고컴, revD/abl 승컴 origin/main)')
a, b, r = table(ws, r, 0, '대비 (정책 − 같은 배치 V4; 마지막 줄은 묶음 끔 − NoDiscount)', CH, con_rows(ABL), 'ablation_contrasts')
a, b, r = table(ws, r, 0, '기술 통계', GH, gstat_rows(sorted({x for p in ABL for x in p}, key=lambda k: [g[0] for g in GROUPS].index(k))))
r = delta_chart(ws, r, 0, [p for p in ABL if p[1] != 'abl-nodiscount'], 'waf', '그림 4. 구성 요소 제거: Δ 전체 WAF vs 같은 배치 V4 (Welch 95% CI, n=3; revB는 n<3이라 제외)', 'chart04_ablation_delta', ar=2, ac=3, h=26)

# ---------------------------------------------------------------- 5. Online Greedy -----------------------------------------------------
ws = wb.sheet('Online Greedy'); g1 = cc('greedy', 'revD-v4'); g2 = cc('greedy', 'abl-v4'); g5 = cc('greedy', 'revD-v4', 'waf_C5'); on = cc('revC-online', 'revC-v4')
r = exp_intro(ws, '5. Online Greedy와 원래 iCAT (M3)', '탐색 없이 매 창 관측 최솟값 arm을 고르는 Online Greedy, 그리고 리비전 전 원래 iCAT 구현과 비교해 iCAT-v4의 탐색·제거 구조가 필요한지 본다.',
              'iCAT-v4의 WAF가 Online Greedy와 원래 iCAT보다 낮다.', 'M3', 'iCAT-v4 vs Online Greedy (승컴), iCAT-v4 vs 원래 iCAT (고컴 revC, 같은 배치)',
              'Online Greedy: 승컴 greedy-20261125 (V4 대조군 없음 → revD-v4, abl-v4와 간접 비교). 원래 iCAT: 고컴 revC 같은 배치. ' + COND, '정책당 3회',
              f"Greedy − revD-V4 = {fmt(g1)} (간접), Greedy − abl-V4 = {fmt(g2)} (간접): 구분되지 않음. 단계 C 첫 5분 WAF는 Greedy가 낮다: {fmt(g5)} (V4에 불리). 원래 iCAT − V4 = {fmt(on)} ({on['rel_pct']:+.1f} %, 같은 배치).",
              'V4는 원래 iCAT보다 확실히 낫지만, 단순 Online Greedy보다 낫다는 근거는 없다. 전환 직후에는 Greedy가 더 빨리 낮은 WAF에 도달한다.',
              f"iCAT-v4가 원래 iCAT보다 WAF {abs(on['rel_pct']):.1f} % 낮다. Online Greedy와는 WAF가 구분되지 않는다(그대로 보고).", 'Online Greedy보다 낫다는 주장. 전환 적응이 Greedy보다 빠르다는 주장.',
              'Greedy와 V4는 다른 배치 → 간접 비교, 배치 효과 ±0.03 가능.', 'origin/main result/greedy-20261125/raw, result/revD-20261124/raw, result/revision-additional-ablation/raw; result/revC-20261124/raw/mixFYF-online-*')
a, b, r = table(ws, r, 0, '개별 실행', RH, run_rows(['greedy', 'revD-v4', 'abl-v4', 'revC-online', 'revC-v4']))
a, b, r = table(ws, r, 0, '대비', CH, con_rows([('greedy', 'revD-v4'), ('greedy', 'abl-v4'), ('revC-online', 'revC-v4')]), 'online_greedy_contrasts')
r = bar_mean_ci(ws, r, 0, ['revD-v4', 'abl-v4', 'greedy', 'revC-v4', 'revC-online'], 'waf', '그림 5. Online Greedy·원래 iCAT vs iCAT-v4: 전체 WAF (승컴 3개는 서로 다른 배치 = 간접; 고컴 revC 2개는 같은 배치)',
                'WAF (낮을수록 좋음), 오차 막대 = 95% CI', 'chart05_online_greedy', ar=2, ac=3, ymin=1.8)

# ---------------------------------------------------------------- 6. Greedy GC -----------------------------------------------------------
ws = wb.sheet('Greedy GC'); gg = cc('greedygc', 'bg-v4'); ggC = cc('greedygc', 'bg-v4', 'waf_C')
r = exp_intro(ws, '6. Greedy GC (학습 없는 기존 정책) vs iCAT-v4 (M3, batchG)', '학습이 전혀 없는 표준 Greedy GC(유효 페이지 최소 블록 선택) 대비 이득을 같은 배치에서 확인한다.',
              'iCAT-v4의 WAF가 Greedy GC보다 낮다.', 'M3', 'iCAT-v4 (bg-v4) vs Greedy GC (greedygc)', '승컴 batchG-20261126, 같은 배치. ' + COND, '정책당 3회',
              f"Greedy GC − V4 = {fmt(gg)} ({gg['rel_pct']:+.1f} %), Holm p = {gg['holm_p']:.4f}. 단계 C {fmt(ggC)}, Holm {ggC['holm_p']:.4f}.",
              'CAT 기반 선택 + 학습이 학습 없는 Greedy GC보다 WAF를 크게 낮춘다.', f"같은 배치 3회에서 iCAT-v4의 WAF가 Greedy GC보다 낮다 (Greedy GC가 {gg['rel_pct']:.1f} % 높음, Holm 보정 후 유의).",
              'WAF 감소가 지연 개선으로 이어진다는 주장: 승컴 계산에서 Greedy GC의 FIO 쓰기 p99가 더 낮았다 (고컴 미재계산). Arm 47 − V4 차이와 합쳐 해석하는 것.', '승컴 한 호스트. 지연은 승컴 값만 있음.',
              'origin/main result/batchG-20261126/raw, result/greedygc-20261126/raw')
a, b, r = table(ws, r, 0, '개별 실행', RH, run_rows(['bg-v4', 'greedygc']))
a, b, r = table(ws, r, 0, '기술 통계', GH, gstat_rows(['bg-v4', 'greedygc']))
a, b, r = table(ws, r, 0, '대비', CH, con_rows([('greedygc', 'bg-v4')]), 'greedygc_contrasts')
rr = r; ws.write(rr, 0, '[그래프 데이터] 단계별 평균 WAF ± 95% CI (승컴 batchG, n=3)', 'bold'); rr += 1
ws.row(rr, 0, ['단계', 'iCAT-v4 평균', 'CI 반폭', 'Greedy GC 평균', 'CI 반폭'], 'head'); ph = []
for i, (m, ml) in enumerate(METRICS[:4]):
    ph.append([ml, S('bg-v4', m)['mean'], S('bg-v4', m)['ci_half'], S('greedygc', m)['mean'], S('greedygc', m)['ci_half']]); ws.row(rr + 1 + i, 0, [ml] + [f4(x) for x in ph[-1][1:]])
csvdump('chart06_greedygc', ['phase', 'v4_mean', 'v4_ci_half', 'greedygc_mean', 'greedygc_ci_half'], ph)
ws.chart('bar', 2, 3, [dict(name='iCAT-v4 (n=3)', cat=(rr + 1, 0, rr + 4, 0), val=(rr + 1, 1, rr + 4, 1), plus=(rr + 1, 2, rr + 4, 2)),
                       dict(name='Greedy GC (n=3)', cat=(rr + 1, 0, rr + 4, 0), val=(rr + 1, 3, rr + 4, 3), plus=(rr + 1, 4, rr + 4, 4))],
         title='그림 6. Greedy GC vs iCAT-v4 (승컴 batchG, 같은 배치)', y_title='WAF (낮을수록 좋음), 오차 막대 = 95% CI', w=9, h=22)

# ---------------------------------------------------------------- 7. Workload Adaptation -------------------------------------------------
ws = wb.sheet('Workload Adaptation')
tsm = lambda k, i: st.mean([w[i] for w in TS[k] if w[i] is not None])
TSTXT = (f"단계 C(60–85분)에서 모든 정책의 5분 창 WAF가 단계 A보다 높다. V4는 단계 C 동안 {tsm('revA-v4', 12):.2f} → {tsm('revA-v4', 16):.2f}로 낮아지고, "
         f"Random은 {min(tsm('revA-random', i) for i in range(12, 17)):.2f}–{max(tsm('revA-random', i) for i in range(12, 17)):.2f}에 머문다. "
         f"V1(감지 끔)은 {tsm('revA-v1', 12):.2f} → {tsm('revA-v1', 16):.2f}, V2(제거·정착 끔)는 {tsm('revA-v2', 12):.2f} → {tsm('revA-v2', 16):.2f}. 단계 B(YCSB)는 모든 정책이 약 1.0이다. "
         "마지막 창(85–90분)은 단계 C 종료 뒤 표본이 없어 비워 두었다.")
r = exp_intro(ws, '7. 워크로드 전환에 따른 WAF 변화', '부하가 바뀔 때(FIO → YCSB-A → FIO, mixY 20단계) 정책의 WAF가 어떻게 변하고 다시 낮아지는지 시간 축으로 본다.',
              '전환 뒤 iCAT-v4가 무작위·제거 실험보다 낮은 WAF로 돌아온다.', 'M6 (적응 성능)', 'revA: iCAT-v4, Random, V1, V2 (고컴, 각 n=3, 5분 창 평균). mixY: SmartGC-EQ8, SmartGC, CAT-47, iCAT-v4 (승컴, 각 n=1)',
              'mixFYF 90분 (A 0–30분 FIO, B 30–60분 YCSB-A, C 60–90분 FIO). mixY 20단계 × 1800 s (F=FIO-Fast, S=FIO-Slow, V=Varmail).', 'revA 정책당 3회 (시간 창별 평균 ± SD). mixY 정책당 1회 (단일 실행, 통계 없음)',
              TSTXT,
              '시간 해상도 WAF는 단계 평균만으로 보이지 않는 전환 비용을 보여준다.', '전환 후 V4의 단계 평균 WAF가 Random보다 낮다 (Random Selection 시트). 감지 시각·재수렴 시간 (적응 지표 표, n=3).',
              '5분 창 하나하나의 차이에 대한 통계적 주장 (창마다 검정하지 않았다). mixY 정책 간 통계적 우열 (n=1).', 'mixY는 승컴 n=1. revA 시간 축은 고컴 한 배치.',
              'result/revA-20261114/raw/*/control-series.txt; result/smartgc-20261119/resume, result/gc-20261010 (F7_smartgc_waf.csv)')
TSK = ['revA-v4', 'revA-random', 'revA-v1', 'revA-v2']
ws.write(r, 0, '[그래프 데이터] 5분 창 WAF, rep 3회 평균 (고컴 revA). 창 시작 = 단계 A 시작 기준 분', 'bold'); r += 1
ws.row(r, 0, ['창 시작 (분)', '단계'] + [GI[k][3] + ' 평균' for k in TSK] + [GI[k][3] + ' SD' for k in TSK], 'head'); a0 = r + 1; tsrows = []
for i in range(NB):
    means = []; sds = []
    for k in TSK:
        v = [w[i] for w in TS[k] if w[i] is not None]; means.append(st.mean(v) if v else ''); sds.append(st.stdev(v) if len(v) > 2 else '')
    row = [i * 5, 'A (FIO)' if i < 6 else 'B (YCSB-A)' if i < 12 else 'C (FIO)'] + means + sds; tsrows.append(row)
    ws.row(r + 1 + i, 0, [f4(x) if isinstance(x, float) else x for x in row])
b0 = a0 + NB - 1; r = b0 + 2
csvdump('chart07_waf_timeseries_revA', ['minute', 'phase'] + [k + '_mean' for k in TSK] + [k + '_sd' for k in TSK], tsrows)
ws.chart('scatter', 2, 3, [dict(name=GI[k][3] + ' (n=3 평균)', cat=(a0, 0, b0, 0), val=(a0, 2 + j, b0, 2 + j)) for j, k in enumerate(TSK)],
         title='그림 7a. 워크로드 전환에 따른 5분 창 WAF (고컴 revA, n=3 평균). A 0–30분 FIO / B 30–60분 YCSB-A / C 60–90분 FIO',
         x_title='단계 A 시작 후 시간 (분)', y_title='5분 창 WAF (낮을수록 좋음)', w=11, h=22, x_min=0, x_max=90)
PH = ['S01F', 'S02S', 'S03V', 'S04F', 'S05V', 'S06S', 'S07F', 'S08S', 'S09V', 'S10F', 'S11V', 'S12S', 'S13F', 'S14S', 'S15V', 'S16F', 'S17V', 'S18S', 'S19F', 'S20S']
ws.write(r, 0, '[그래프 데이터] mixY 단계별 WAF (승컴, 각 n=1 단일 실행) — F7_smartgc_waf.csv (고컴 재계산, 두 경로 일치)', 'bold'); r += 1
ws.row(r, 0, ['단계'] + [x['policy'] + ' (n=1)' for x in F7], 'head'); a1 = r + 1; yrows = []
for i, p in enumerate(PH):
    row = [p] + [float(x[p]) if x.get(p) else '' for x in F7]; yrows.append(row); ws.row(a1 + i, 0, [f4(v) if isinstance(v, float) else v for v in row])
b1 = a1 + len(PH) - 1; r = b1 + 2
csvdump('chart07b_mixY_phase_waf', ['phase'] + [x['policy'] for x in F7], yrows)
ws.chart('line', 26, 3, [dict(name=x['policy'] + ' (n=1)', cat=(a1, 0, b1, 0), val=(a1, 1 + j, b1, 1 + j)) for j, x in enumerate(F7)],
         title='그림 7b. mixY 20단계 단계별 WAF (승컴, 정책당 n=1 단일 실행; F=FIO-Fast, S=FIO-Slow, V=Varmail)', x_title='단계', y_title='단계 WAF (낮을수록 좋음, 로그 축)', w=11, h=22, log_y=True)
prov('Workload Adaptation', 'mixY per-phase WAF', 'report/paper-figures-20261127/F7_smartgc_waf.csv (databook, GoCom recomputation of SeungCom runs)', 'copied')
AD = [x for x in F5 if x['metric'] in ('C_detect_s', 'C_recovery_s', 'C_resettle_from_reset_s_max', 'C_explore_host_share', 'B_detect_s', 'first_settle_s_latest_part', 'C_restored_arms')]
a, b, r = table(ws, r, 0, '적응 지표 (고컴 revA·revC·revE, 커널 로그; 출처 F5_adaptation_summary.csv, 고컴 계산)', ['그룹', '호스트', '배치', '지표', 'n', '개별 값', '평균', 'SD'],
                [[x['group'], x['host'], x['batch'], x['metric'], x['n_valid'], x['values'], x['mean'], x['sd']] for x in AD], 'adaptation_metrics')
prov('Workload Adaptation', 'adaptation metrics', 'report/paper-figures-20261127/F5_adaptation_summary.csv', 'copied (GoCom kernel-log analysis, verified 11-25/26)')

# ---------------------------------------------------------------- 8. Drift Threshold ---------------------------------------------------
ws = wb.sheet('Drift Threshold'); d12 = cc('revE-drift12', 'revE-v4'); d50 = cc('drift50', 'bg-v4')
r = exp_intro(ws, '8. 변화 감지 문턱 (M6)', '변화 감지 문턱(기본 25 %)의 근거를 위해 더 민감한 12.5 %, 덜 민감한 50 %, 감지 끔과 비교한다.',
              '기본값 25 %가 12.5 %나 50 %보다 나쁘지 않다.', 'M6 (파라미터 근거)', '12.5 % (고컴 revE), 50 % (승컴 batchG), 감지 끔 (고컴 revA V1, 승컴 revD NoDrift). 모두 같은 배치 V4(25 %) 대비',
              '각 배치 안에서만 V4와 비교. 서로 다른 호스트·배치의 Δ는 합치지 않는다. ' + COND, '정책당 3회',
              f"12.5 %: {fmt(d12)} (Holm {d12['holm_p']:.3f}, 경계). 50 %: {fmt(d50)} (구분되지 않음). 감지 끔: revA {fmt(cc('revA-v1', 'revA-v4'))}, revD {fmt(cc('revD-nodrift', 'revD-v4'))} (둘 다 구분되지 않음).",
              '문턱을 12.5 %로 낮추면 불필요한 재설정이 늘어 WAF가 높아질 수 있다. 50 %와 25 %는 구분되지 않는다.', '측정한 세 수준 중 25 %가 가장 나쁘지 않았다. 12.5 %는 보정 전 CI 기준 더 나빴다(Holm 후 경계).',
              '25 %가 최적값이라는 주장. 15 % 수준의 결과 (측정하지 않음).', '수준마다 다른 호스트·배치. 12.5 %는 고컴, 50 %는 승컴.', 'result/revE-20261125/raw, origin/main result/drift50-20261126/raw')
a, b, r = table(ws, r, 0, '대비 (같은 배치 V4 = 25 %)', CH, con_rows([('revE-drift12', 'revE-v4'), ('drift50', 'bg-v4'), ('revA-v1', 'revA-v4'), ('revD-nodrift', 'revD-v4')]), 'drift_contrasts')
a, b, r = table(ws, r, 0, '기술 통계', GH, gstat_rows(['revE-v4', 'revE-drift12', 'bg-v4', 'drift50', 'revA-v4', 'revA-v1', 'revD-v4', 'revD-nodrift']))
ws.write(r, 0, '참고: 요청 목록의 "12.5/15/50"에서 15 %는 감지 문턱으로 실행된 적이 없다. 15 %는 후보 제거 문턱(WATGC_V2_ELIM_Q16)의 기본값이며 Ablation Study의 revC 제거 문턱 10/15/25 %에 있다.', 'warn'); r += 2
r = delta_chart(ws, r, 0, [('revE-drift12', 'revE-v4'), ('drift50', 'bg-v4'), ('revA-v1', 'revA-v4'), ('revD-nodrift', 'revD-v4')], 'waf',
                '그림 8. 감지 문턱 12.5 % / 50 % / 끔 − 같은 배치 25 % (Δ 전체 WAF ± Welch 95% CI)', 'chart08_drift_delta', ar=2, ac=3)

# ---------------------------------------------------------------- 9. SmartGC Comparison ------------------------------------------------
ws = wb.sheet('SmartGC Comparison')
r = exp_intro(ws, '9. SmartGC 비교 (M1)', '심사위원이 요청한 기존 학습 기반 GC(SmartGC)와 같은 부하에서 비교한다. 원저자 코드가 없어 논문 기술대로 재구현했다 (EQ8 = 논문 식 8 GC 버퍼 포함).',
              'iCAT-v4의 WAF_nand가 SmartGC보다 낮다.', 'M1', 'iCAT-v4, SmartGC-EQ8, SmartGC (순위 목록), CAT-47; 고컴 보조 SmartGC/SmartGC-Q/Greedy/Arm47',
              'mixY 20단계 × 1800 s = 10 h (FIO-Fast / FIO-Slow / Varmail, YCSB 없음). 승컴 smartgc-20261119·gc-20261010, 고컴 gocom-sg-20261119, 고컴 m1-20261126(구간 타이머 빌드)', '정책당 1회 (모든 호스트). 통계 없음',
              f"승컴: iCAT-v4 WAF {float(F7[3]['waf']):.3f}, SmartGC-EQ8 {float(F7[0]['waf']):.3f} (EQ8은 1+gc/host; WAF_nand는 M1 표). 고컴 m1: WAF_nand {float(M1W[0]['waf_nand']):.3f} vs {float(M1W[1]['waf_nand']):.3f}.",
              '두 호스트, 두 빌드에서 방향이 같다 (iCAT이 낮음).', 'iCAT-v4의 WAF가 SmartGC 재구현보다 낮은 방향이 두 호스트의 단일 실행에서 일관되었다.',
              '통계적 우열 (n=1). 원저자 SmartGC보다 낫다는 주장 (재구현). 지연 비교 (SmartGC-EQ8에 채널 모델 포화 경고 22,069줄).', 'n=1, 재구현, mixY만.',
              'result/smartgc-20261119/resume, result/gc-20261010/mixY-*, result/gocom-sg-20261119, /home/oy/iCAT/result/m1-20261126/raw')
a, b, r = table(ws, r, 0, '승컴 mixY (F7_smartgc_waf.csv, 고컴 재계산 일치)', ['정책', '원시 경로', '모듈 sha256 앞 16자', 'exit', 'host_pages', 'gc_pages', 'WAF (1+gc/host)', '두 경로 일치', '비고'],
                [[x['policy'], x['run_dir'], x['module_sha256'], x['exit'], int(x['host_pages']), int(x['gc_pages']), f4(float(x['waf'])), x['partition_sum_equal'], 'n=1 단일 실행'] for x in F7], 'smartgc_seungcom')
a, b, r = table(ws, r, 0, '고컴 gocom-sg-20261119 mixY (이 스크립트 재계산)', ['run', 'exit', 'host_pages', 'gc_pages', 'WAF (1+gc/host)', 'WAF_nand (summary)', '원시 경로'],
                [[g['run'], g['exit'], g['host_pages'], g['gc_pages'], f4(g['waf_1_plus_gc_over_host']), g['waf_nand_summary'], g['raw_dir']] for g in GSG], 'smartgc_gocom_sg')
a, b, r = table(ws, r, 0, '고컴 m1-20261126 (구간 타이머 빌드)', ['run', '정책', 'exit', 'host TB', 'WAF_nand', 'gc_count', 'FIO 오류 단계', '커널 오류', 'chmodel 경고 줄', 'YCSB'],
                [[x['run'], x['policy'], x['exit'], x['host_TB'], f4(float(x['waf_nand'])), x['gc_count'], x['fio_phases_with_error'], x['kernel_errors'], x['chmodel_warn_lines'], x['ycsb']] for x in M1W], 'smartgc_m1')
vals = [[f"{x['policy']} [승컴 n=1]", float(x['waf'])] for x in F7] + [[f"{x['policy']} [고컴 m1 n=1, WAF_nand]", float(x['waf_nand'])] for x in M1W]
a0, b0, r = chart_table(ws, r, 0, '[그래프 데이터] mixY 정책별 WAF (모두 n=1 단일 실행, 호스트별 표시)', None, ['정책 [호스트]', 'WAF'], vals)
csvdump('chart_smartgc_waf', ['label', 'waf'], vals)
ws.chart('bar', 2, 3, [dict(name='WAF (n=1 단일 실행, 오차 막대 없음)', cat=(a0, 0, b0, 0), val=(a0, 1, b0, 1))], title='참고 그림. mixY 정책별 WAF (n=1, 호스트·빌드별)',
         y_title='WAF (낮을수록 좋음)', w=10, h=20)

# ---------------------------------------------------------------- 10. Memory Overhead ---------------------------------------------------
ws = wb.sheet('Memory Overhead')
icl = 10112; sgl = sum(int(x['bytes']) for x in M1T if x['policy'] == 'SmartGC-EQ8' and x['item'] in ('Q table', 'cand', 'sort_key')) + 232 * 4
r = exp_intro(ws, '10. 메모리 오버헤드 (M1·M5)', 'iCAT 학습 상태와 SmartGC 학습 구조의 메모리를 같은 조건에서 계산·측정한다.', 'iCAT의 학습 상태가 SmartGC보다 훨씬 작다.', 'M1, M5',
              'iCAT-v4 vs SmartGC-EQ8 (고컴 m1-20261126)', 'VmallocUsed (/proc/meminfo, 시스템 전체) 적재 전 60 s, 적재 후 60 s 중앙값 차; 자료구조 크기는 빌드된 .ko의 gdb sizeof × 할당식', '정책당 1회',
              f"학습 자료구조 (계산): iCAT {icl:,} B vs SmartGC {sgl:,} B (약 1/{sgl / icl:.0f}). VmallocUsed 증가 (실측): {float(M1M[0]['vmalloc_delta_load_kB_measured']):,.0f} kB vs {float(M1M[1]['vmalloc_delta_load_kB_measured']):,.0f} kB, 차 {float(M1M[2]['vmalloc_delta_load_kB_measured']):,.0f} kB (계산 차 {float(M1M[2]['theoretical_conv_ftl_vmalloc_kB_calculated']):,.1f} KiB).",
              'FTL 공통 자료구조(매핑 테이블 등 32 MiB)가 대부분이고, 정책별 차이는 학습 구조와 line 구조체 크기에서 나온다.', '학습 상태 메모리가 SmartGC 재구현의 약 1/193이다 (계산). 정책 간 vmalloc 차이 실측이 계산과 맞는다.',
              'VmallocUsed를 모듈 전용 메모리라고 하는 것 (시스템 전체 값). RSS(사용자 공간 시뮬레이터)를 커널 모듈 메모리라고 하는 것. n=1 차이의 통계적 유의성.', 'n=1. /proc/vmallocinfo는 root 권한이 없어 쓰지 못했다.',
              'result/m1-20261126-final/{memory_measured,memory_theoretical,memory_comparison}.csv')
a, b, r = table(ws, r, 0, '자료구조 크기 (계산)', ['정책', '항목', '식', 'bytes', 'kB', '정책 고유', '종류'], [[x['policy'], x['item'], x['formula'], int(x['bytes']), float(x['kB']), x['policy_specific'], x['kind']] for x in M1T], 'memory_theoretical')
a, b, r = table(ws, r, 0, '측정값 (VmallocUsed, Slab, SUnreclaim; 시스템 전체)', list(M1MM[0].keys()), [list(x.values()) for x in M1MM], 'memory_measured')
a, b, r = table(ws, r, 0, '측정 vs 계산 비교', list(M1M[0].keys()), [list(x.values()) for x in M1M], 'memory_comparison')
vals = [['학습 자료구조 (계산)', icl / 1024, sgl / 1024], ['conv_ftl.c vmalloc 합계 (계산)', float(M1T[4]['kB']), float([x for x in M1T if x['policy'] == 'SmartGC-EQ8' and x['item'].startswith('TOTAL')][0]['kB'])],
        ['VmallocUsed 증가 (실측, 시스템 전체)', float(M1M[0]['vmalloc_delta_load_kB_measured']), float(M1M[1]['vmalloc_delta_load_kB_measured'])]]
a0, b0, r = chart_table(ws, r, 0, '[그래프 데이터] 메모리 (KiB/kB, n=1 단일 실행)', None, ['항목', 'iCAT-v4', 'SmartGC-EQ8'], vals)
csvdump('chart09_memory', ['item', 'icat_kib', 'smartgc_kib'], vals)
ws.chart('bar', 2, 3, [dict(name='iCAT-v4 (n=1)', cat=(a0, 0, b0, 0), val=(a0, 1, b0, 1)), dict(name='SmartGC-EQ8 (n=1)', cat=(a0, 0, b0, 0), val=(a0, 2, b0, 2))],
         title='그림 9. iCAT vs SmartGC 메모리 (고컴 m1, n=1). 계산값과 실측값을 구분', y_title='KiB (로그 축)', log_y=True, w=10, h=22)
prov('Memory Overhead', 'all', 'result/m1-20261126-final/*.csv (GoCom M1 final, b1af7f526)', 'copied; learning-structure sum recomputed from memory_theoretical.csv + struct smartgc 232 B x 4')

# ---------------------------------------------------------------- 11. CPU and Timing --------------------------------------------------
ws = wb.sheet('CPU and Timing')
kt = {(x['policy'], x['region']): x for x in M1K}
r = exp_intro(ws, '11. CPU·시간 비용 (M1·M5)', 'GC 실행, 희생 블록 선택, 학습 갱신 비용을 정책별로 분리한다.', 'iCAT의 학습 갱신 비용이 작다. (GC 전체 시간이 짧다는 가설은 세우지 않는다.)', 'M1, M5',
              'iCAT-v4 vs SmartGC-EQ8', '커널 구간 타이머 (ktime_get_ns 경과 시간, CPU 시간 아님), mixY 10 h, 고컴 m1-20261126. 사용자 공간 시뮬레이터 CPU 시간(CLOCK_THREAD_CPUTIME_ID)은 다른 부하(sim zones)',
              '커널: 정책당 1회. 사용자 공간: seed 3개',
              f"GC 1회 평균 경과: iCAT {float(kt[('iCAT-v4', 'GC')]['mean_ns_per_call']) / 1000:.1f} µs vs SmartGC {float(kt[('SmartGC-EQ8', 'GC')]['mean_ns_per_call']) / 1000:.1f} µs. 희생 블록 선택: {float(kt[('iCAT-v4', 'SELECT')]['mean_ns_per_call']) / 1000:.1f} µs vs {float(kt[('SmartGC-EQ8', 'SELECT')]['mean_ns_per_call']) / 1000:.1f} µs. "
              f"학습 갱신 GC당: {float(kt[('iCAT-v4', 'LEARN')]['ns_per_gc']):.1f} ns vs {float(kt[('SmartGC-EQ8', 'LEARN')]['ns_per_gc']):.1f} ns.",
              'iCAT의 GC 경과 시간은 SmartGC보다 길고, 대부분 전체 line 점수 검사(희생 블록 선택)다. 학습 갱신 자체는 GC 경과의 0.04 %다.',
              '학습 갱신 비용이 GC당 약 41 ns(ktime 경과)로 작다. 학습 구조 메모리 절감과 GC 실행 비용은 별개로 보고한다.',
              'iCAT의 GC 전체 경과 시간이 SmartGC보다 짧다는 주장. ktime 값을 CPU 사용 시간이라고 하는 것. 커널 CPU 시간 실측값 (측정 불가).',
              '커널 CPU 시간 측정 불가 (perf 없음, nvmev kthread busy-poll). p50/p95/p99 없음. n=1. 타이머 오버헤드 약 40.7 ns/구간은 사용자 공간 추정값.',
              'result/m1-20261126-final/{kernel_elapsed_time,common_vs_algorithm_cost,userspace_cpu_time}.csv, analysis/bench_summary.tsv')
a, b, r = table(ws, r, 0, '커널 구간 경과 시간 (ktime, CPU 시간 아님; n=1)', ['정책', '구간', '호출 수', '합계 (s)', '호출당 평균 (ns)', '파티션 평균 최소', '최대', 'GC당 (ns)', 'host GiB당 (ms)', '최대 1회 (ns)', 'p50/p95/p99'],
                [[x['policy'], x['region'], int(x['calls']), float(x['total_s']), float(x['mean_ns_per_call']), float(x['partition_mean_min_ns']), float(x['partition_mean_max_ns']),
                  float(x['ns_per_gc']), float(x['ms_per_host_GiB']), int(x['max_single_call_ns']), '측정 불가 (호출별 값 없음)'] for x in M1K], 'kernel_elapsed')
a, b, r = table(ws, r, 0, '공통 비용 vs 알고리즘 비용 (ktime 경과; 유도값 포함)', ['정책', '분류', '합계 (s)', 'host GiB당 (ms)', 'GC당 (ns)', '유도식', '종류', '비고'],
                [[x['policy'], x['category'], x['total_s'], x['ms_per_host_GiB'], x['ns_per_gc'], x['derivation'], x['kind'], x['note']] for x in M1C], 'common_vs_algorithm')
a, b, r = table(ws, r, 0, '사용자 공간 시뮬레이터 (다른 부하: sim zones, mixY 아님)', ['정책', 'clock mode', 'clock', '구간', 'seed', '호출 수', '호출당 (ns)', '보정 후 (ns)', 'seed SD', 'user s', 'sys s', 'maxrss kB (사용자 공간 프로세스, 모듈 메모리 아님)'],
                [[x['policy'], x['clock_mode'], x['clock'], x['region'], x['seed'], x['calls'], x['ns_per_call_raw'], x['ns_per_call_minus_calib'], x['sd_over_seeds'], x['user_s'], x['sys_s'], x['sim_process_maxrss_kB']] for x in M1U], 'userspace_cpu')
vals = [['GC 전체', float(kt[('iCAT-v4', 'GC')]['ns_per_gc']) / 1000, float(kt[('SmartGC-EQ8', 'GC')]['ns_per_gc']) / 1000],
        ['희생 블록 선택 (SELECT)', float(kt[('iCAT-v4', 'SELECT')]['ns_per_gc']) / 1000, float(kt[('SmartGC-EQ8', 'SELECT')]['ns_per_gc']) / 1000],
        ['학습 갱신 (LEARN)', float(kt[('iCAT-v4', 'LEARN')]['ns_per_gc']) / 1000, float(kt[('SmartGC-EQ8', 'LEARN')]['ns_per_gc']) / 1000],
        ['보상 (REWARD, SmartGC만)', '', float(kt[('SmartGC-EQ8', 'REWARD')]['ns_per_gc']) / 1000]]
a0, b0, r = chart_table(ws, r, 0, '[그래프 데이터] GC 1회당 경과 시간 µs (ktime 경과, CPU 시간 아님; n=1)', None, ['구간', 'iCAT-v4', 'SmartGC-EQ8'], vals)
csvdump('chart10_timing', ['region', 'icat_us_per_gc', 'smartgc_us_per_gc'], vals)
ws.chart('bar', 2, 3, [dict(name='iCAT-v4 (n=1)', cat=(a0, 0, b0, 0), val=(a0, 1, b0, 1)), dict(name='SmartGC-EQ8 (n=1)', cat=(a0, 0, b0, 0), val=(a0, 2, b0, 2))],
         title='그림 10. 학습 비용과 GC 실행 시간 (GC 1회당, ktime 경과 µs, 고컴 m1 n=1). iCAT GC가 더 길다', y_title='µs per GC (로그 축)', log_y=True, w=10, h=22)
prov('CPU and Timing', 'all', 'result/m1-20261126-final/*.csv', 'copied (GoCom M1 final; M1PROF cross-checked stop vs remove and vs gc_count)')

# ---------------------------------------------------------------- 12. Arm 47 Robustness -------------------------------------------------
ws = wb.sheet('Arm 47 Robustness'); a47 = S('arm47'); ar = cc('arm47', 'bg-v4')
r = exp_intro(ws, '12. 고정 Arm 47 반복 재현성 (Robustness)', '사후에 고른 최적 고정 arm(47)의 기존 결과가 n=1(고컴)뿐이라, 다른 seed와 다른 호스트에서 재현되는지 확인한다.',
              '고정 Arm 47의 mixFYF WAF가 seed와 호스트에 관계없이 재현된다.', 'Robustness (M4 반복 요구 관련)', '고정 Arm 47 (승컴 ×3), 참고: 고컴 revA n=1, 승컴 batchG V4 (다른 배치)',
              '승컴 arm47-20261127, 모듈 sha256 9fde0ea4… (고컴 실행과 같은 파일). ' + COND, '승컴 3회 + 고컴 기존 1회 (합산하지 않음)',
              f"승컴 n=3 전체 WAF {a47['mean']:.5f} ± {a47['sd']:.5f}, 95% CI [{a47['ci_lo']:.5f}, {a47['ci_hi']:.5f}] (CV {100 * a47['sd'] / a47['mean']:.3f} %). 고컴 n=1 {S('revA-arm47')['mean']:.5f}는 CI 안. "
              f"참고 Arm 47 − 승컴 V4(다른 배치) = {fmt(ar)}.", 'WAF는 seed·호스트에 거의 무관하다. 지연·처리량은 호스트에 따라 크게 다르다.',
              '고정 Arm 47의 WAF 1.9876 ± 0.0003 (n=3)은 기존 n=1 결과를 재현한다.', 'Arm 47을 실행 전에 알 수 있었다는 주장 (사후 oracle). 승컴 n=3과 고컴 n=1을 합친 n=4. V4와의 같은 배치 비교 (간접뿐).',
              '같은 배치 V4가 없다. 지연은 호스트 간 비교 불가.', 'origin/main result/arm47-20261127/raw/mixFYF-arm47-rep{1,2,3}; result/revA-20261114/raw/mixFYF-arm47-rep1')
a, b, r = table(ws, r, 0, '개별 실행', RH, run_rows(['arm47', 'revA-arm47']))
a, b, r = table(ws, r, 0, '기술 통계', GH, gstat_rows(['arm47', 'revA-arm47', 'bg-v4'], ('waf', 'waf_A', 'waf_B', 'waf_C', 'waf_C5')))
a, b, r = table(ws, r, 0, '참고 대비 (간접)', CH, con_rows([('arm47', 'bg-v4')]))
vals = [[f'승컴 rep{x["rep"]}', x['waf'], ''] for x in by('arm47')] + [['승컴 평균 ± 95% CI (n=3)', a47['mean'], a47['ci_half']], ['고컴 revA n=1 (단일 실행, 다른 호스트)', S('revA-arm47')['mean'], '']]
a0, b0, r = chart_table(ws, r, 0, '[그래프 데이터] 고정 Arm 47 전체 WAF', None, ['실행', '전체 WAF', '95% CI 반폭'], vals)
csvdump('chart11_arm47', ['run', 'waf', 'ci_half'], vals)
ws.chart('line', 2, 3, [dict(name='전체 WAF (점), 평균은 95% CI 막대', cat=(a0, 0, b0, 0), val=(a0, 1, b0, 1), plus=(a0, 2, b0, 2), line=False)],
         title='그림 11. 고정 Arm 47 반복 재현성 (승컴 n=3 + 고컴 n=1 참고, 합산하지 않음)', y_title='전체 WAF (낮을수록 좋음; 축 범위 확대)', y_min=1.985, y_max=1.990, w=10, h=22)

# ---------------------------------------------------------------- 13. Secondary Metrics -------------------------------------------------
ws = wb.sheet('Secondary Metrics')
r = exp_intro(ws, '13. 보조 지표 (단계 C 첫 5분 WAF, 탐색 비용, 적응 시간, 지연)', '전체 WAF 외에 전환 직후 비용, 탐색 비용, 적응 시간, 지연을 함께 보고해 불리한 결과를 숨기지 않는다.',
              '(사전 등록 보조 지표, 가설 검정 아님)', 'M3, M5, M6', '모든 mixFYF 그룹 (단계 C 첫 5분 WAF는 이 스크립트가 재계산). 탐색·적응: 고컴 og_audit / F5, 승컴 secondary-metrics. 지연: 고컴 revA·revC (F6)',
              COND, '정책당 3회', f"단계 C 첫 5분 WAF: Greedy − revD-V4 = {fmt(g5)} (Greedy가 낮음, V4에 불리, 간접). 탐색 host 비중·적응 시간은 아래 표.",
              '전환 직후에는 탐색 없는 Greedy가 유리하다. V4의 이득은 단계 후반·전체에서 나온다.', '보조 지표를 그대로 보고한다 (불리한 결과 포함).', '보조 지표에 근거한 우열 주장 (다중 비교 보정 없음, 탐색적).',
              '지연은 호스트마다 크게 달라 같은 호스트·배치 안에서만 본다.', 'control-series.txt, kernel.log, phase-*.json')
a, b, r = table(ws, r, 0, '단계 C 첫 5분 WAF (이 스크립트 재계산; 승컴 secondary-metrics와 대조는 Statistical Analysis)', GH, gstat_rows([g[0] for g in GROUPS], ('waf_C5',)), 'secondary_C5')
a, b, r = table(ws, r, 0, '단계 C 첫 5분 WAF 대비', CH, con_rows([p for p in [(x[0], x[1]) for x in CONTRASTS]], ('waf_C5',)))
OGA = []
for src in ('result/final-revision-analysis/m4/runs.csv', 'result/abl-20261125-verify/runs.csv', 'result/greedy-20261125-verify/runs.csv', 'result/batchG-20261126-verify/runs.csv', 'result/arm47-20261127-verify/runs.csv'):
    for x in rd(src):
        k = inv(x['group'])
        if k in GI and GI[k][2].split('-')[0] in x['batch'] and x.get('explore_host_share', '') not in ('', None):
            OGA.append((k, float(x['explore_host_share']), x.get('init_host_share', ''), src))
seen = set(); ex_rows = []; exv = {}
for k, v, ih, src in OGA:
    if (k, v) in seen: continue
    seen.add((k, v)); exv.setdefault(k, []).append(v)
for k in [g[0] for g in GROUPS if g[0] in exv]:
    d_ = desc(exv[k]); ex_rows.append([GI[k][1], GI[k][2], k, GI[k][3], d_['n'], ' / '.join(f'{x:.4f}' for x in exv[k]), f4(d_['mean']), f4(d_['sd']), f4(d_['ci_lo']), f4(d_['ci_hi'])])
a, b, r = table(ws, r, 0, '탐색 비용: 전체 run에서 탐색 창(evaluated ≠ best)이 차지한 host 쓰기 비중 (고컴 og_audit 계산; Greedy의 best는 정의가 다름)', ['호스트', '배치', '그룹', '정책', 'n', '개별 값', '평균', 'SD', 'CI 하한', 'CI 상한'], ex_rows, 'explore_host_share')
prov('Secondary Metrics', 'explore_host_share', 'result/final-revision-analysis/m4/runs.csv, result/*-verify/runs.csv', 'copied (GoCom og_audit kernel-log parse)')
a, b, r = table(ws, r, 0, f'승컴 secondary-metrics-20261126 (승컴 계산; 단계 C 첫 5분 WAF만 고컴 재계산 대조)', list(SC_SEC[0].keys()), [list(x.values()) for x in SC_SEC], 'seungcom_secondary')
prov('Secondary Metrics', 'SeungCom secondary metrics', f'origin/main {SC_FULL[:9]}:result/secondary-metrics-20261126/statistics.csv', 'copied; C_first5min_waf independently recomputed (match in Statistical Analysis)')
LAT = [x for x in F6L if x['metric'] in ('C_hot_p99_us', 'C_warm_p99_us', 'C_cold_p99_us', 'B_ycsb_ops_per_s', 'B_update_p99_us')]
a, b, r = table(ws, r, 0, '지연·처리량 (고컴 revA·revC, F6_latency_stats.csv; 같은 배치 안에서만 비교)', ['그룹', '지표', 'n', '개별 값', '평균', 'SD', 'CI 하한', 'CI 상한'],
                [[x['group'], x['metric'], x['n'], x['values'], x['mean'], x['sd'], x['ci_lo'], x['ci_hi']] for x in LAT], 'latency')
prov('Secondary Metrics', 'latency', 'report/paper-figures-20261127/F6_latency_stats.csv', 'copied (GoCom, from FIO json / YCSB output)')
# chart 12: explore cost (host share) and adaptation time (C_resettle / recovery)
ex_keys = [k for k in ['revA-v4', 'revA-v1', 'revC-v4', 'revC-elim10', 'revC-elim25', 'revC-arm60', 'revD-v4', 'revD-nodrift', 'revD-fullreset', 'abl-v4', 'abl-nodiscount', 'abl-offbundle', 'bg-v4', 'drift50'] if k in exv]
vals = [[f'{GI[k][3]} [{GI[k][1]} {GI[k][2]}]', st.mean(exv[k]), desc(exv[k])['ci_half']] for k in ex_keys]
a0, b0, r = chart_table(ws, r, 0, '[그래프 데이터] 그림 12a 탐색 비용 (탐색 창 host 비중, n=3 평균 ± 95% CI)', None, ['그룹 [호스트 배치]', '탐색 host 비중', 'CI 반폭'], vals)
csvdump('chart12a_explore_share', ['group', 'explore_host_share', 'ci_half'], vals)
ws.chart('bar', 2, 3, [dict(name='탐색 host 비중 (n=3) ± 95% CI', cat=(a0, 0, b0, 0), val=(a0, 1, b0, 1), plus=(a0, 2, b0, 2))],
         title='그림 12a. 탐색 비용: 탐색 창이 차지한 host 쓰기 비중 (배치별, 합산하지 않음)', y_title='비중 (0–1, 낮을수록 탐색 적음)', w=11, h=22)
adk = [(x['group'], x['host'], x['batch'], x) for x in F5 if x['metric'] == 'C_resettle_from_reset_s_max']
vals = []
for g_, h_, b_, x in adk:
    try:
        v = [float(t) for t in x['values'].split(' / ')]
    except ValueError:
        continue
    d_ = desc(v); vals.append([f'{g_} [{h_} {b_}]', d_['mean'], d_['ci_half'], x['values']])
a0, b0, r = chart_table(ws, r, 0, '[그래프 데이터] 그림 12b 적응 시간: 단계 C 재설정 → 재정착 최대 시간 (s, 파티션 최대; n=3; 출처 F5, 고컴 분석, revD는 승컴 원시)', None, ['그룹 [호스트 배치]', '평균 (s)', 'CI 반폭', '개별 값'], vals)
csvdump('chart12b_adaptation_time', ['group', 'mean_s', 'ci_half', 'values'], vals)
ws.chart('bar', 26, 3, [dict(name='단계 C 재정착 시간 (s), n=3 ± 95% CI', cat=(a0, 0, b0, 0), val=(a0, 1, b0, 1), plus=(a0, 2, b0, 2))],
         title='그림 12b. 적응 시간: 단계 C 재설정 후 재정착까지 (배치별, 호스트는 라벨; 재설정 없는 정책은 측정 불가로 제외)', y_title='초 (낮을수록 빠름)', w=11, h=22)

# ---------------------------------------------------------------- 14. Statistical Analysis -----------------------------------------------
ws = wb.sheet('Statistical Analysis')
r = intro(ws, '14. 통계 (독립 재계산과 기존 값 대조)', [('방법', 't 95 % CI (df = n−1). Welch t (Satterthwaite df), 판정 = Welch 95 % CI가 0 제외. Hedges g (n=3 대 3, 크기 참고용). Holm: 배치별 사전 지정 주 대비 × {전체, 단계 C}.'),
                                                       ('Holm 계열', 'revA 6 (V1, V2, Random), revC 8 (elim10, elim25, 60 arms, 원래 iCAT), revD 4, revE 4, abl 4 (NoDiscount, 묶음 끔), batchG 4. revB(대조군 n=1)·간접 비교는 계열 밖.'),
                                                       ('대조', f'기존 게시값 {len(XS)}항목과 비교. 일치 {sum(x["match"] for x in XS)}, 불일치 {sum(not x["match"] for x in XS)} (불일치 원인은 아래 "불일치 조사").')])
a, b, r = table(ws, r, 0, '그룹 통계 (모든 그룹 × 지표)', GH, gstat_rows([g[0] for g in GROUPS], [m for m, _ in METRICS]), 'all_group_stats')
a, b, r = table(ws, r, 0, '모든 대비', CH, con_rows([(x[0], x[1]) for x in CONTRASTS]), 'all_contrasts')
a, b, r = table(ws, r, 0, '기존 게시값과 대조', ['항목', '게시값', '재계산', '|차|', '상대 차', '허용', '일치', '출처'],
                [[x['what'], x['published'], x['recomputed'], x['abs_diff'], x['rel_diff'], x['tolerance'], x['match'], x['source']] for x in XS], 'crosscheck_published')
MIS = [x for x in XS if not x['match']]
a, b, r = table(ws, r, 0, '불일치 조사', ['항목', '게시값', '재계산', '출처', '원인'], [[x['what'], x['published'], x['recomputed'], x['source'], ''] for x in MIS] or [['없음', '', '', '', '']], 'crosscheck_mismatch')
MIS_ROW = a

# ---------------------------------------------------------------- 15. Run Validity / 16. Raw Results ------------------------------------
ws = wb.sheet('Run Validity')
r = intro(ws, '15. run 유효성 (이 스크립트 재검사 + 기존 판정 대조)', [('기준', 'exit 0, 커널 오류 0 (BUG/WARNING/Oops/Call Trace, 해당 run 구간), FIO 오류 0, YCSB READ+UPDATE 모두 OK, SQLITE_FULL 0, WAF 두 경로 일치, 시작 카운터 0.'),
                                                       ('제외', '무효 run을 임의로 제외하지 않는다. smoke120 run은 사전 등록상 통계 대상이 아니라서 목록에만 둔다 (원시 경로 존재). M1 4회 CANCELLED는 실패·무효가 아니라 취소다.')])
VH = ['호스트', '배치', '그룹', 'rep', 'exit', '모듈 sha256', 'hostname', 'FIO seed', 'seed 규칙 일치', 'icat_seed', '커널 오류', 'FIO 오류', 'YCSB ops', 'YCSB OK', 'YCSB 성공률', 'SQLITE_FULL',
      '두 경로 일치', '시작 카운터 0', '유효 (재검사)', '사유', '유효 (기존 판정)', '기존 판정 출처', 'WAF 최대 |차|', '기존 값과 일치']
a, b, r = table(ws, r, 0, 'run별 검사', VH, [[x['host'], x['batch'], x['key'], x['rep'], x['exit'], x['module_sha256'][:16], x['hostname'], x['fio_seeds'], x['fio_seeds_expected'], x['icat_seed'],
                                              x['kernel_err'], x['fio_err'], x['ycsb_ops'], x['ycsb_ok'], x['ycsb_success'], x['sqlite_full'], x['two_paths_equal'], x['started_zero'],
                                              x['valid_recomputed'], x['invalid_reasons_recomputed'], x['valid_published'], x['published_source'], x['max_abs_diff_vs_published'], x['matches_published']] for x in RUNS], 'run_validity')
sm = []
for g in GROUPS:
    for p in sorted(g[4].iterdir()):
        if p.is_dir() and re.search(g[5].replace(r'rep\d$', r'rep\d-smoke'), p.name): sm.append([g[1], g[2], p.name, pub(p), 'smoke (사전 등록상 통계 제외)'])
a, b, r = table(ws, r, 0, 'smoke run (통계 대상 아님, 원시 존재)', ['호스트', '배치', 'run', '경로', '처리'], sm, 'smoke_runs')
a, b, r = table(ws, r, 0, 'M1 (mixY) run', list(M1W[0].keys()), [list(x.values()) for x in M1W])
ws.write(r, 0, 'M1 CANCELLED 4회: mixY-m1-{icat-v4,smartgc-eq8}-rep{2,3} — 사용자 결정으로 취소 (실패·무효 아님). /home/oy/iCAT/result/m1-20261126/CANCELLED-RUNS.txt', 'note')

ws = wb.sheet('Raw Results')
r = intro(ws, '16. 원시 결과 (run 단위, 이 스크립트가 원시 카운터에서 계산)', [('열', 'host_pages/gc_pages = summary.txt total 줄. WAF = 1 + gc/host. 단계 WAF = 단계 시작/끝 스냅샷. C 첫 5분 = control-series 30 s 표본.'),
                                                                     ('경로', 'origin/main@<sha>: 는 승컴 원시 자료 (git archive로 읽음). 나머지는 이 브랜치 경로.')])
RW = ['호스트', '배치', '그룹', '정책', 'rep', 'host_pages', 'gc_pages', '전체 WAF', '단계 A', '단계 B', '단계 C', 'C 첫 5분', 'YCSB ops/s', '유효', '모듈 sha256', '원시 경로']
a, b, r = table(ws, r, 0, 'mixFYF run', RW, [[x['host'], x['batch'], x['key'], x['policy'], x['rep'], x['host_pages'], x['gc_pages'], x['waf'], x['waf_A'], x['waf_B'], x['waf_C'], x['waf_C5'],
                                              x['ycsb_ops_per_s'], x['valid_recomputed'], x['module_sha256'], x['raw_dir']] for x in RUNS], 'raw_results_mixFYF')
a, b, r = table(ws, r, 0, 'mixY run (SmartGC 비교, n=1)', ['출처', 'run', 'exit', 'host_pages', 'gc_pages', 'WAF'],
                [['F7 (승컴)', x['run_dir'], x['exit'], int(x['host_pages']), int(x['gc_pages']), float(x['waf'])] for x in F7] + [['gocom-sg (고컴)', g['raw_dir'], g['exit'], g['host_pages'], g['gc_pages'], g['waf_1_plus_gc_over_host']] for g in GSG]
                + [['m1 (고컴)', x['run'], x['exit'], int(x['host_pages']), int(x['gc_pages']), float(x['waf_1_plus_gc_over_host'])] for x in M1W], 'raw_results_mixY')

# ---------------------------------------------------------------- 17. Reviewer Evidence Matrix -----------------------------------------
ws = wb.sheet('Reviewer Evidence Matrix')
r = intro(ws, '17. 심사 의견별 근거', [('출처', 'report/final-revision/review_evidence_and_status.md (11-27 갱신)을 이 Excel 시트와 연결했다.')])
REV = [['M1', '기존 학습 기반 GC(SmartGC)와 비교', 'SmartGC Comparison, Memory Overhead, CPU and Timing', '정책당 1회 (반복 미충족)', 'WAF 방향 일관(두 호스트), 메모리 충족, CPU 부분 충족(커널 CPU 측정 불가), GC 비용 iCAT이 더 큼', '부분 충족'],
       ['M2', '구성 요소 제거', 'Ablation Study', '3 (revB 일부 n=1)', 'V2·FullReset·NoElim·묶음 끔은 차이, V1·NoDrift·NoDiscount는 구분되지 않음', '충족 (불리한 결과 포함 보고)'],
       ['M3', '온라인 기준선 비교', 'Random Selection, Online Greedy, Greedy GC', '3', 'Random·원래 iCAT·Greedy GC 대비 차이. Online Greedy와 구분되지 않음(간접). Periodic 미실행', '부분 충족'],
       ['M4', '반복과 통계 검증', 'Statistical Analysis, Run Validity, Raw Results', f'{len(RUNS)} run', f'재계산 {sum(x["matches_published"] for x in RUNS)}/{len(RUNS)} 일치, 통계 대조 {sum(x["match"] for x in XS)}/{len(XS)}', '충족'],
       ['M5', '자원 효율', 'Memory Overhead, CPU and Timing, Secondary Metrics', '1 (M1), 3 (revA 지연)', 'ktime 경과와 CPU 시간 구분. 지연은 같은 배치 안에서만', '부분 충족'],
       ['M6', '적응 성능, 파라미터 근거', 'Workload Adaptation, Drift Threshold, Ablation Study, Secondary Metrics', '3', '감지 12.5/25/50 %, 제거 10/15/25 %, 후보 45/60. 판단 구간 등 4개 미측정', '부분 충족'],
       ['M7', '환경 일반화', '(실험 없음) M7_scope_and_limitations.md', '-', '단일 에뮬레이터 구성 명시', '범위 명시'],
       ['Robustness', '최적 고정 arm 재현성', 'Arm 47 Robustness', '3 + 1', 'Arm 47 WAF 재현 (CV 0.013 %)', '충족 (승컴, 집컴 검증 전)']]
a, b, r = table(ws, r, 0, '심사 의견 → 시트 → 결과', ['심사 의견', '요구', '근거 시트', '반복', '결과 요약', '판정'], REV, 'reviewer_matrix')
for i, w in enumerate([12, 30, 44, 18, 70, 20]): ws.width(i, w)

for s in wb.sheets:
    if s.name not in ('Executive Summary', 'Experiment Inventory', 'Reviewer Evidence Matrix'):
        s.width(0, 26); s.width(1, 22)
        for i in range(2, 16): s.widths.setdefault(i, 14)
        s.width(1, 110 if s.name not in ('Raw Results', 'Run Validity', 'Statistical Analysis') else 22)

nchart = wb.save(OUTX)
for name, (h, rows) in CSVS.items():
    with open(OUTD / f'{name}.csv', 'w', newline='') as f:
        w = csv.writer(f); w.writerow(h); w.writerows(rows)
for name, (h, rows) in CSVS.items():
    prov('complete-results CSV', name, f'report/final-revision/complete-results/{name}.csv', 'written from the same in-memory table as the sheet / chart')
with open(ROOT / 'report/final-revision/DATA_PROVENANCE.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, ['table', 'item', 'source', 'method']); w.writeheader(); w.writerows(PROV)
    for x in RUNS: w.writerow(dict(table='Raw Results', item=f"{x['key']} rep{x['rep']}", source=x['raw_dir'], method=f"recomputed; published value source: {x['published_source']}; match={x['matches_published']}"))
print('xlsx', OUTX, 'sheets', len(wb.sheets), 'charts', nchart, 'csv', len(CSVS))
