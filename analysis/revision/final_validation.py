#!/usr/bin/env python3
"""11-27 independent validation of every revision-era run, straight from raw logs (no existing analysis code imported).
    python3 -I -B analysis/revision/final_validation.py GOCOM_DIR
GOCOM_DIR = `git archive origin/report/data-validity-20261124 result/{revA-20261114,revB-20261122,revC-20261124,revE-20261125,
             gocom-sg-20261119,m1-20261126} | tar -x -C GOCOM_DIR`
Host is read from environment.txt (uname nodename), never from where the dir lives. Groups = (host, batch, policy); nothing is pooled
across hosts or batches. Stats only for n>=3 valid main reps (smoke dirs listed, never used).
Outputs result/final-validation-20261127/{final_raw_data_validation,final_statistical_validation,final_robustness_validation}.csv"""
import csv, gzip, json, math, re, statistics as st, subprocess, sys
from pathlib import Path
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'result/final-validation-20261127'
GO = Path(sys.argv[1]) if len(sys.argv) > 1 else None
GBR = 'origin/report/data-validity-20261124'
HOST = {'oy-System-Product-Name': '승컴', 'oy-B550M-DS3H': '고컴'}

# (location, batch dir, raw subdir, scope label)
BATCHES = [('main', 'revD-20261124', 'raw', 'revD (NoDrift/FullReset)'),
           ('main', 'revision-additional-ablation', 'raw', 'Ablation (NoDiscount/OffBundle)'),
           ('main', 'greedy-20261125', 'raw', 'Online Greedy'),
           ('main', 'batchG-20261126', 'raw', 'batchG V4'), ('main', 'drift50-20261126', 'raw', 'drift50'),
           ('main', 'greedygc-20261126', 'raw', 'Greedy GC'), ('main', 'arm47-20261127', 'raw', 'Arm 47'),
           ('main', 'smartgc-20261119', 'resume', 'SmartGC (승컴 mixY, 11-22 fresh rerun after 11-20 disk-full failure)'),
           ('main', 'gc-20261010', '.', 'SmartGC-EQ8 / sg-arm47 / SmartGC 1st attempt (승컴 mixY, 11-19~20; stored under gc-20261010 by the runner)'),
           ('gocom', 'revA-20261114', 'raw', 'revA (Random Selection/V1/V2/V4/Arm47)'),
           ('gocom', 'revB-20261122', 'raw', 'revB (NoElim/NoSettle/Arm60)'),
           ('gocom', 'revC-20261124', 'raw', 'revC (original iCAT "online"/Elim10/25/Arm60)'),
           ('gocom', 'revE-20261125', 'raw', 'revE (drift12/NoElim)'),
           ('gocom', 'gocom-sg-20261119', '.', 'SmartGC (고컴 mixY)'), ('gocom', 'm1-20261126', 'raw', 'M1 (mixY, sampler)')]
GC1010 = re.compile(r'mixY-(smartgc|smartgc-eq8|sg-arm47)-rep|t4-smartgc')   # gc-20261010 dir: only the Nov 19-20 SmartGC campaign runs written there
# source tree git SHA, only where the batch recorded one; otherwise the build identity is the module sha256 (+ sources.sha256 on 승컴)
SC = {'revA-20261114': 'c06a372a5e94 (HEAD at run, dirty tree: revA source-status.txt / cpu_measurements.csv git_commit)',
      'revB-20261122': 'c06a372a5 (HEAD at run, dirty tree: revB preregistration.md)'}
SC_RUN = {'smartgc-20261119/mixY-smartgc-rep1': '29b5f116b (HEAD at run start, smartgc-20261119/report/compare.csv)',
          'smartgc-20261119/mixY-onlinev4-rep1': '01df84464 (HEAD at run start, smartgc-20261119/report/compare.csv)'}
def src_commit(batch, name, base):
    if f'{batch}/{name}' in SC_RUN: return SC_RUN[f'{batch}/{name}']
    if batch in SC: return SC[batch]
    m = re.match(r'(?:mixY|t4)-(sg-arm47|smartgc-eq8|smartgc)-rep1', name)
    f = base / 'result/smartgc-20261119' / f'{m[1]}-rep1.commit.txt' if m and batch == 'gc-20261010' else None
    if f and f.exists(): return f.read_text().strip()[:9] + ' (HEAD at run start, smartgc-20261119/*.commit.txt)'
    if batch == 'm1-20261126': return 'c06a372a5 (run tree HEAD recorded at analysis time, m1-20261126-final/provenance.csv)'
    return '미기록 (build identity = module sha256' + ('; source files = sources.sha256)' if (base / 'result' / batch / 'sources.sha256').exists() else ')')

def rd(d, name):   # plain / .gz / .zst
    for suf, f in (('', lambda p: p.read_text(errors='replace')), ('.gz', lambda p: gzip.open(p, 'rt', errors='replace').read()),
                   ('.zst', lambda p: subprocess.run(['zstd', '-dcq', str(p)], capture_output=True, text=True, errors='replace').stdout)):
        if (d / (name + suf)).exists(): return f(d / (name + suf))
    return None

def ctr(d, name):   # (control host, gc), (sum part host, sum part gc)
    t = rd(d, name)
    if t is None: return None, None
    l = t.splitlines(); c = tuple(int(re.search(rf'\b{k}=(\d+)', l[0])[1]) for k in ('host_pages', 'gc_pages'))
    ps = re.findall(r'^part=\d host_pages=(\d+) gc_pages=(\d+)', t, re.M)
    return c, (sum(int(h) for h, _ in ps), sum(int(g) for _, g in ps))

def waf(h, g): return (h + g) / h if h else None

def commits():   # raw-log commit = commit that added <run>/exit-code.txt
    m = {}
    for loc, br in (('main', 'HEAD'), ('gocom', GBR)):
        out = subprocess.run(['git', '-C', str(ROOT), 'log', br, '--diff-filter=A', '--name-only', '--format=@%h', '--', 'result/*exit-code.txt'],
                             capture_output=True, text=True).stdout
        c = None
        for l in out.splitlines():
            if l.startswith('@'): c = l[1:]
            elif l: m[(loc, l.rsplit('/', 1)[0])] = c          # log is newest first -> last write = oldest = adding commit
    return m

def run(loc, batch, d, base, cm, reg):
    rel = str(d.relative_to(base))
    env = rd(d, 'environment.txt') or ''
    node = (re.search(r'^Linux (\S+)', env, re.M) or [None, '?'])[1]
    mod = re.search(r'^([0-9a-f]{64})  \S*/(nvmev[^/\s]*\.ko)$', env, re.M)
    pre = re.match(r'(mixFYF|mixY|mix[A-Z]\d*|t4long|t4)-(.+?)-rep(\d)(.*)$', d.name)
    r = {'run_id': f'{batch}/{d.name}', 'host': HOST.get(node, node), 'nodename': node, 'batch': batch,
         'workload': pre[1] if pre else '?', 'policy': pre[2] if pre else d.name, 'rep': int(pre[3]) if pre else '',
         'role': ('other' if not pre else 'main' if not pre[4] else 'smoke' if 'smoke' in pre[4] else pre[4].lstrip('-')),
         'raw_path': (rel if loc == 'main' else f'{GBR}:{rel}'), 'raw_log_commit': cm.get((loc, rel), 'uncommitted'),
         'source_commit': src_commit(batch, d.name, base),
         'module': mod[2] if mod else '', 'module_sha256': mod[1] if mod else ''}
    r['module_sha_matches_registered'] = (reg.get(r['module']) == r['module_sha256']) if r['module'] in reg else 'no registry'
    r['ycsb_workload_sha256'] = (re.search(r'^([0-9a-f]{64})  \S*/workloads/sqlite/workloada$', env, re.M) or [None, ''])[1][:16]
    r['fio_job_sha256'] = (re.search(r'^([0-9a-f]{64})  \S*/workloads/(mix-test4\.fio)$', env, re.M) or [None, ''])[1][:16]
    # seeds
    js = sorted(d.glob('phase-*.json'))
    seeds, ferr, fdur = [], 0, []
    for j in js:
        try: J = json.load(open(j))
        except Exception: ferr += 1000; continue
        ferr += sum(x.get('error', 0) for x in J['jobs'])
        if j.stem in ('phase-A', 'phase-S01'): seeds = [x['job options'].get('randseed', '') for x in J['jobs']]
    for p in ('preset.json', 'prepare.json'):
        if (d / p).exists():
            try: ferr += sum(x.get('error', 0) for x in json.load(open(d / p))['jobs'])
            except Exception: ferr += 1000
    kl = rd(d, 'kernel.log') or ''
    r['fio_seeds_first_phase'] = '/'.join(seeds)
    r['icat_seed'] = (re.search(r'icat_seed=(\d+)', kl) or [None, 'none'])[1]
    # time / init
    t = sorted((p.name, p.read_text().strip()) for p in d.glob('phase-*-*.time'))
    from datetime import datetime as D
    ts = [D.fromisoformat(v).timestamp() for _, v in t]
    r['start'] = (env.splitlines() or [''])[0]
    r['measured_hours'] = round((max(ts) - min(ts)) / 3600, 3) if ts else ''
    phs = sorted({re.match(r'phase-(\w+?)-', n)[1] for n, _ in t})
    r['phases'] = '+'.join(phs)
    r['phase_minutes'] = '/'.join(f'{(D.fromisoformat((d / f"phase-{p}-end.time").read_text().strip()) - D.fromisoformat((d / f"phase-{p}-start.time").read_text().strip())).total_seconds() / 60:.1f}'
                                  for p in phs if (d / f'phase-{p}-end.time').exists())
    pc, _ = ctr(d, 'prepared.txt'); sc, _ = ctr(d, 'started.txt')
    r['init_counters_zero'] = bool(pc == (0, 0) and sc == (0, 0)) if pc and sc else False
    r['init_preset_ok'] = (d / 'preset.json').exists() and (d / 'mkfs.txt').exists()
    # YCSB
    y = rd(d, 'ycsb-run-B.txt') or rd(d, 'ycsb-run.txt') or ''
    ops = sum(map(int, re.findall(r'^\[(?:READ|UPDATE|INSERT|SCAN|READ-MODIFY-WRITE)\], Operations, (\d+)', y, re.M)))
    ok = sum(map(int, re.findall(r'^\[(?:READ|UPDATE|INSERT|SCAN|READ-MODIFY-WRITE)\], Return=OK, (\d+)', y, re.M)))
    r['ycsb_ops'], r['ycsb_ok'] = ops, ok
    r['ycsb_success'] = ok / ops if ops else ''
    r['sqlite_full'] = sum((rd(d, f) or '').count('SQLITE_FULL') for f in ('ycsb-run-B.txt', 'ycsb-run.txt', 'ycsb-load.txt'))
    r['fio_errors'] = ferr
    pol = sorted(set(re.findall(r'GC victim policy: (\S+)', kl))) + sorted({f'fixed-arm{a}' for a in re.findall(r'Fixed CAT init .*arm=(\d+)', kl)})
    r['kernel_policy'] = '+'.join(pol)
    r['fixed_arm_partitions'] = len(re.findall(r'Fixed CAT init ', kl))
    r['cpu_model'] = (re.search(r'(?:모델 이름|Model name):\s+(.+)', env) or [None, ''])[1].strip()
    r['kernel_cmdline_sha'] = __import__('hashlib').sha256(((env.splitlines() + ['', '', ''])[2]).encode()).hexdigest()[:12]
    r['kernel_errors'] = len(re.findall(r'BUG:|WARNING:|Oops|Call Trace|general protection', kl))
    r['kernel_log_present'] = bool(kl)
    # WAF
    c, p = ctr(d, 'stopped.txt')
    if c and sc:
        h, g = c[0] - sc[0], c[1] - sc[1]; r['host_pages'], r['gc_pages'] = h, g
        r['total_waf'] = waf(h, g); r['total_waf_partsum'] = waf(*p)
        r['waf_paths_agree_1e9'] = abs(r['total_waf'] - r['total_waf_partsum']) < 1e-9
    nand = re.findall(r'^smartgc part=\d .*nand_pages=(\d+)', rd(d, 'stopped.txt') or '', re.M)
    if nand and r.get('host_pages'): r['waf_nand'] = sum(map(int, nand)) / r['host_pages']   # SmartGC builds: NAND pages incl. GC-buffer flushes
    sm = rd(d, 'summary.txt') or ''
    m = re.search(r'^total .*WAF=([\d.]+)', sm, re.M); r['summary_waf'] = float(m[1]) if m else ''
    r['summary_vs_recalc_absdiff'] = abs(r['summary_waf'] - r['total_waf']) if m and r.get('total_waf') else ''
    for ph in 'ABC':
        a, _ = ctr(d, f'phase-{ph}-start.txt'); b, _ = ctr(d, f'phase-{ph}-end.txt')
        if r['workload'] == 'mixFYF' and a and b and b[0] > a[0]: r[f'{ph}_waf'] = waf(b[0] - a[0], b[1] - a[1])
    if r['workload'] == 'mixFYF' and (d / 'phase-C-start.time').exists() and (d / 'control-series.txt').exists():
        # C first 5 min: first control sample >= phase C start .. first sample >= start + 300 s (prereg abl-20261125 sec. 4)
        from datetime import datetime as D2
        t0 = D2.fromisoformat((d / 'phase-C-start.time').read_text().strip()).timestamp()
        pts = [(int(l.split()[0]), int(re.search(r'host_pages=(\d+)', l)[1]), int(re.search(r'gc_pages=(\d+)', l)[1])) for l in open(d / 'control-series.txt') if 'host_pages=' in l]
        a = next((x for x in pts if x[0] >= t0), None); b = next((x for x in pts if x[0] >= t0 + 300), None)
        if a and b and b[1] > a[1]: r['C5_waf'] = 1 + (b[2] - a[2]) / (b[1] - a[1])
    m = re.search(r'^\[OVERALL\], Throughput\(ops/sec\), ([\d.]+)', y, re.M)
    if m: r['ycsb_ops_per_s'] = float(m[1])
    ex = (rd(d, 'exit-code.txt') or '').strip()
    bad = []
    if ex != '0': bad.append(f'exit={ex or "missing"}')
    if r['workload'] == 'mixFYF' and r['phases'] != 'A+B+C': bad.append(f'phases={r["phases"]}')
    if r['workload'] == 'mixY' and len(phs) != 20: bad.append(f'{len(phs)}/20 phases')
    r['has_sqlite_phase'] = '(sqlite' in (rd(d, 'summary.txt') or '')
    if (r['workload'] == 'mixFYF' or (r['workload'] != 'mixY' and r['has_sqlite_phase'])) and (not ops or ok != ops): bad.append(f'ycsb {ok}/{ops}')
    if r['workload'] == 'mixY':   # mixY = FIO + filebench varmail (no YCSB): 6 varmail phases must reach IO Summary, no error lines
        fb = [p.read_text(errors='replace') for p in sorted(d.glob('filebench-S*.txt'))]
        r['filebench_done'] = sum('IO Summary' in x for x in fb)
        r['filebench_errors'] = sum(len(re.findall(r'(?im)^(?!.*region limits).*\b(error|failed)\b', x)) for x in fb)
        if r['filebench_done'] != 6 or r['filebench_errors']: bad.append(f'filebench {r["filebench_done"]}/6 err={r["filebench_errors"]}')
    if r['sqlite_full']: bad.append('SQLITE_FULL')
    if ferr: bad.append(f'fio_errors={ferr}')
    if not kl: bad.append('no kernel.log')
    elif r['kernel_errors']: bad.append(f'kernel_errors={r["kernel_errors"]}')
    if not r['init_counters_zero']: bad.append('init counters not zero')
    if not r.get('waf_paths_agree_1e9'): bad.append('WAF paths disagree')
    if r['summary_vs_recalc_absdiff'] == '' or r['summary_vs_recalc_absdiff'] > 5e-7: bad.append('summary WAF mismatch')
    if r['module_sha_matches_registered'] is False: bad.append('module sha != registered')
    r['valid'] = not bad; r['invalid_reason'] = '; '.join(bad)
    return r

# ---------------- stats (independent implementation)
def desc(x):
    n = len(x); m = st.mean(x) if x else ''
    if n < 3: return {'n': n, 'mean': m, 'sd': '', 'ci95_lo': '', 'ci95_hi': '', 'note': 'n<3: no SD/CI/test'}
    s = st.stdev(x); h = stats.t.ppf(.975, n - 1) * s / n ** .5
    return {'n': n, 'mean': m, 'sd': s, 'ci95_lo': m - h, 'ci95_hi': m + h, 'ci95_halfwidth': h, 'cv_pct': 100 * s / m, 'note': ''}

def welch(a, b):   # b - a
    na, nb, va, vb = len(a), len(b), st.variance(a), st.variance(b)
    se = math.sqrt(va / na + vb / nb); d = st.mean(b) - st.mean(a)
    df = (va / na + vb / nb) ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    sp = math.sqrt(((na - 1) * va + (nb - 1) * vb) / (na + nb - 2)); J = 1 - 3 / (4 * (na + nb) - 9)
    h = stats.t.ppf(.975, df) * se
    return {'diff': d, 'ci95_lo': d - h, 'ci95_hi': d + h, 'welch_df': df, 'welch_p': 2 * stats.t.sf(abs(d / se), df), 'hedges_g': J * d / sp}

def paired(pa, pb):
    dd = [pb[k] - pa[k] for k in sorted(pa)]; n = len(dd); m, s = st.mean(dd), st.stdev(dd); h = stats.t.ppf(.975, n - 1) * s / n ** .5
    return {'paired_n': n, 'paired_mean': m, 'paired_ci95_lo': m - h, 'paired_ci95_hi': m + h,
            'paired_p': 2 * stats.t.sf(abs(m / (s / n ** .5)), n - 1) if s else ''}

def holm(ps):
    o = sorted(range(len(ps)), key=ps.__getitem__); adj, run = [0] * len(ps), 0
    for r, i in enumerate(o): run = max(run, min(1, (len(ps) - r) * ps[i])); adj[i] = run
    return adj

# (family, batch_a, policy_a [control], batch_b, policy_b, kind)
CON = [('revA', 'revA-20261114', 'revA-v4', 'revA-20261114', p, 'direct') for p in ('revA-random', 'revA-v1', 'revA-v2')] + \
      [('revC', 'revC-20261124', 'revC-v4', 'revC-20261124', p, 'direct') for p in ('online', 'revB-arm60', 'revC-elim10', 'revC-elim25')] + \
      [('revE', 'revE-20261125', 'revE-v4', 'revE-20261125', p, 'direct') for p in ('revE-drift12', 'revE-noelim')] + \
      [('revD', 'revD-20261124', 'revD-v4', 'revD-20261124', p, 'direct') for p in ('revD-nodrift', 'revD-fullreset')] + \
      [('abl', 'revision-additional-ablation', 'abl-v4', 'revision-additional-ablation', p, 'direct') for p in ('abl-nodiscount', 'abl-off-elim-settle-drift-probe')] + \
      [('secondary', 'revision-additional-ablation', 'abl-nodiscount', 'revision-additional-ablation', 'abl-off-elim-settle-drift-probe', 'direct (secondary, not in Holm)')] + \
      [('revB', 'revB-20261122', 'revB-v4', 'revB-20261122', p, 'direct') for p in ('revB-noelim', 'revB-nosettle', 'revB-arm60')] + \
      [('batchG', 'batchG-20261126', 'bg-v4', 'greedygc-20261126', 'greedygc', 'direct (same queue, interleaved)'),
       ('batchG', 'batchG-20261126', 'bg-v4', 'drift50-20261126', 'drift50', 'direct (same queue, interleaved)')] + \
      [('indirect', 'revD-20261124', 'revD-v4', 'greedy-20261125', 'greedy-online', 'indirect (different batch)'),
       ('indirect', 'revision-additional-ablation', 'abl-v4', 'greedy-20261125', 'greedy-online', 'indirect (different batch)'),
       ('indirect', 'batchG-20261126', 'bg-v4', 'arm47-20261127', 'arm47', 'indirect (different batch)'),
       ('indirect', 'revB-20261122', 'revB-noelim', 'revE-20261125', 'revE-noelim', 'batch reproducibility'),
       ('indirect', 'revA-20261114', 'revA-v4', 'revB-20261122', 'revB-noelim', 'indirect (different batch)'),
       ('indirect', 'revA-20261114', 'revA-v4', 'revB-20261122', 'revB-nosettle', 'indirect (different batch)')] + \
      [('v4-repro', a, pa, b, pb, 'batch reproducibility') for (a, pa), (b, pb) in
       [(('revD-20261124', 'revD-v4'), ('revision-additional-ablation', 'abl-v4')), (('revD-20261124', 'revD-v4'), ('batchG-20261126', 'bg-v4')),
        (('revision-additional-ablation', 'abl-v4'), ('batchG-20261126', 'bg-v4')), (('revA-20261114', 'revA-v4'), ('revC-20261124', 'revC-v4')),
        (('revA-20261114', 'revA-v4'), ('revE-20261125', 'revE-v4')), (('revC-20261124', 'revC-v4'), ('revE-20261125', 'revE-v4'))]]
METRICS = ['total_waf', 'A_waf', 'B_waf', 'C_waf', 'C5_waf', 'ycsb_ops_per_s']

def write(name, rows):
    with open(OUT / name, 'w', newline='') as f:
        w = csv.DictWriter(f, list(dict.fromkeys(k for r in rows for k in r)), lineterminator='\n'); w.writeheader(); w.writerows(rows)

def main():
    OUT.mkdir(exist_ok=True); cm = commits(); runs = []
    for loc, b, sub, label in BATCHES:
        base = ROOT if loc == 'main' else GO
        bd = base / 'result' / b
        rb = bd.parent / 'batchG-20261126' if b in ('drift50-20261126', 'greedygc-20261126') else bd   # batchG registers all three modules
        reg = {Path(l.split()[1]).name: l.split()[0] for l in (rb / 'modules.sha256').read_text().splitlines() if l.strip()} if (rb / 'modules.sha256').exists() else {}
        if b in ('gc-20261010', 'smartgc-20261119'):   # SmartGC campaign registers per run (*.module.sha256) + report/compare.csv
            sg = ROOT / 'result/smartgc-20261119'
            reg.update({Path(l.split()[1]).name: l.split()[0] for f in sg.glob('*.module.sha256') for l in f.read_text().splitlines() if l.strip()})
            reg.update({f'nvmev-{r["policy"]}.ko'.replace('nvmev-onlinev4', 'nvmev-online-v4'): r['sha256'] for r in csv.DictReader(open(sg / 'report/compare.csv'))})
        for d in sorted((bd / sub).glob('*')):
            if not (d / 'exit-code.txt').exists() and not (d / 'environment.txt').exists(): continue
            if b == 'gc-20261010' and not GC1010.search(d.name): continue
            r = run(loc, b, d, base, cm, reg); r['scope'] = label; runs.append(r)
    write('final_raw_data_validation.csv', runs)
    key = lambda r: (r['host'], r['batch'], r['policy'])
    grp = {}
    for r in runs:
        if r['role'] == 'main' and r['valid']: grp.setdefault(key(r), []).append(r)
    srows = []
    for (h, b, p), rs in grp.items():
        for k in METRICS:
            x = [r[k] for r in sorted(rs, key=lambda r: r['rep']) if isinstance(r.get(k), float)]
            if x: srows.append({'kind': 'descriptive', 'host': h, 'batch': b, 'policy': p, 'metric': k,
                                'values_by_rep': ' / '.join(f'{v:.6f}' for v in x), **desc(x)})
    hb = {(b, p): h for h, b, p in grp}
    for fam, ba, pa, bb, pb, kind in CON:
        ha, hbb = hb.get((ba, pa)), hb.get((bb, pb))
        for k in METRICS:
            A = {r['rep']: r[k] for r in grp.get((ha, ba, pa), []) if isinstance(r.get(k), float)}
            B = {r['rep']: r[k] for r in grp.get((hbb, bb, pb), []) if isinstance(r.get(k), float)}
            c = {'kind': 'contrast', 'family': fam, 'comparison': kind, 'host': ha if ha == hbb else f'{ha} vs {hbb}',
                 'control': f'{ba}/{pa}', 'treatment': f'{bb}/{pb}', 'metric': k, 'n_control': len(A), 'n_treatment': len(B)}
            if ha != hbb: c['note'] = 'different hosts: not compared'
            elif len(A) < 3 or len(B) < 3:
                c['note'] = 'n<3: no test'
                if A and B: c['diff'] = st.mean(B.values()) - st.mean(A.values())   # difference of means only, no CI/p
            else:
                c.update(welch(list(A.values()), list(B.values())))
                sa = {r['rep']: r['fio_seeds_first_phase'] for r in grp[(ha, ba, pa)]}; sb = {r['rep']: r['fio_seeds_first_phase'] for r in grp[(hbb, bb, pb)]}
                same = set(A) == set(B) and all(sa[i] == sb[i] for i in A)
                c['same_seed_pairs'] = same
                if same and kind.startswith('direct'): c.update(paired(A, B))
                else: c['paired_note'] = '해당 없음 (다른 배치)' if not kind.startswith('direct') else '해당 없음 (seed 불일치)'
            srows.append(c)
    for fam in {c['family'] for c in srows if c['kind'] == 'contrast'}:
        cs = [c for c in srows if c.get('family') == fam and 'welch_p' in c and c['metric'] in ('total_waf', 'C_waf')]   # Holm: total + phase C only
        if fam in ('revA', 'revC', 'revE', 'revD', 'abl', 'batchG'):
            for c, a in zip(cs, holm([c['welch_p'] for c in cs])): c['holm_p_family'] = a; c['holm_family_size'] = len(cs)
            ct = [c for c in cs if c['metric'] == 'total_waf']   # alt. family (total WAF only) for batches without a pre-registered family
            for c, a in zip(ct, holm([c['welch_p'] for c in ct])): c['holm_p_total_only'] = a
    write('final_statistical_validation.csv', srows)
    write('final_robustness_validation.csv', robustness(runs, grp, srows))
    write('crosscheck_jibcom_delivery.csv', crosscheck_delivery(runs) + crosscheck_stats(srows))
    if not __import__('os').environ.get('SKIP_PRE'): write('final_prerevision_figure_validation.csv', prerevision(cm))
    print(f'runs={len(runs)} main={sum(r["role"] == "main" for r in runs)} valid_main={sum(r["role"] == "main" and r["valid"] for r in runs)}')
    for r in runs:
        if r['role'] == 'main' and not r['valid']: print('INVALID', r['host'], r['run_id'], r['invalid_reason'])
    return runs, srows

# (figure, claim in 집컴 figure_manifest.csv @ origin/report/home-delivery-20261127, host, batch, policy, claimed n)
FIG = [('figure01_random', 'Random n=3', '고컴', 'revA-20261114', 'revA-random', 3), ('figure01_random', 'iCAT-v4 n=3', '고컴', 'revA-20261114', 'revA-v4', 3),
       ('figure01_random', 'CAT-47 ref n=1', '고컴', 'revA-20261114', 'arm47', 1),
       ('figure02_ablation', 'v1 n=3', '고컴', 'revA-20261114', 'revA-v1', 3), ('figure02_ablation', 'v2 n=3', '고컴', 'revA-20261114', 'revA-v2', 3),
       ('figure02_ablation', 'NoElim n=3 (control = revA-v4, other batch)', '고컴', 'revB-20261122', 'revB-noelim', 3),
       ('figure02_ablation', 'NoSettle n=3 (control = revA-v4, other batch)', '고컴', 'revB-20261122', 'revB-nosettle', 3),
       ('figure02_ablation', 'revD v4 n=3', '승컴', 'revD-20261124', 'revD-v4', 3), ('figure02_ablation', 'NoDrift n=3', '승컴', 'revD-20261124', 'revD-nodrift', 3),
       ('figure02_ablation', 'FullReset n=3', '승컴', 'revD-20261124', 'revD-fullreset', 3),
       ('figure05_parameters', 'elim10 n=3', '고컴', 'revC-20261124', 'revC-elim10', 3), ('figure05_parameters', 'elim15 (v4) n=3', '고컴', 'revC-20261124', 'revC-v4', 3),
       ('figure05_parameters', 'elim25 n=3', '고컴', 'revC-20261124', 'revC-elim25', 3), ('figure06_candidates', '60-arm n=3', '고컴', 'revC-20261124', 'revB-arm60', 3)]

def robustness(runs, grp, srows):
    out = []
    def add(check, item, result, verdict, detail=''): out.append({'check': check, 'item': item, 'result': result, 'verdict': verdict, 'detail': detail})
    # 1 Random Selection spread
    for k in METRICS:
        x = [r[k] for r in grp.get(('고컴', 'revA-20261114', 'revA-random'), []) if isinstance(r.get(k), float)]
        if x: add('Random Selection 반복 간 편차', f'고컴 revA-random {k}', ' / '.join(f'{v:.4f}' for v in x),
                  'OK' if len(x) == 3 else 'n<3', f'SD {st.stdev(x):.4f}, CV {100 * st.stdev(x) / st.mean(x):.2f} %, range {max(x) - min(x):.4f}')
    # 2 figure repetition claims vs valid main reps found in raw logs
    for f, claim, h, b, p, n in FIG:
        got = len(grp.get((h, b, p), []))
        add('Figure 반복 횟수 (집컴 manifest 주장 vs 원시)', f'{f}: {claim}', f'valid main reps = {got}', 'MATCH' if got == n else 'MISMATCH', f'{h} {b}/{p}')
    # 3 Arm 47
    a = sorted(grp.get(('승컴', 'arm47-20261127', 'arm47'), []), key=lambda r: r['rep']); g = grp.get(('고컴', 'revA-20261114', 'arm47'), [])
    add('Arm 47 독립 반복', '승컴 arm47-20261127 valid main reps', len(a), 'OK' if len(a) == 3 else 'FAIL')
    add('Arm 47 독립 반복', 'seeds differ between reps', ' | '.join(r['fio_seeds_first_phase'] for r in a), 'OK' if len({r['fio_seeds_first_phase'] for r in a}) == len(a) else 'FAIL')
    add('Arm 47 독립 반복', 'Fixed CAT arm=47 on all 4 partitions, every run', [r['fixed_arm_partitions'] for r in a + g],
        'OK' if all(r['fixed_arm_partitions'] % 4 == 0 and r['fixed_arm_partitions'] and r['kernel_policy'].split('+')[-1] == 'fixed-arm47'
                    and r['kernel_policy'].count('fixed-arm') == 1 for r in a + g) else 'FAIL', 'init printed at insmod and again at measurement start = 8 lines, all arm=47')
    add('Arm 47 독립 반복', 'same module as 고컴 n=1', {r['module_sha256'][:16] for r in a + g}, 'OK' if len({r['module_sha256'] for r in a + g}) == 1 else 'FAIL')
    if len(a) == 3 and g:
        d = desc([r['total_waf'] for r in a])
        add('Arm 47 독립 반복', '고컴 n=1 inside 승컴 n=3 95% CI (not pooled)', f'{g[0]["total_waf"]:.6f} in [{d["ci95_lo"]:.6f}, {d["ci95_hi"]:.6f}]',
            'OK' if d['ci95_lo'] <= g[0]['total_waf'] <= d['ci95_hi'] else 'OUTSIDE', 'different hosts (Intel vs AMD): reported side by side, never n=4')
    # 4 drift50 detection behaviour (independent of drift-check.py)
    for r in sorted(grp.get(('승컴', 'drift50-20261126', 'drift50'), []), key=lambda r: r['rep']):
        kl = rd(ROOT / r['raw_path'], 'kernel.log')
        dev = [abs(int(s_) - int(f_)) / int(f_) for f_, s_ in re.findall(r'WATGC_V2 reset .*reason=waf-drift reference_q16=(\d+) sample_q16=(\d+)', kl)]
        add('drift50 변화 감지 동작', f'drift50 rep{r["rep"]}', f'resets={len(dev)} min_dev={min(dev):.3f}' if dev else 'resets=0',
            'OK' if all(x > .5 for x in dev) else 'FAIL', 'every waf-drift reset must exceed 50 % deviation (DRIFT_Q16=32768)')
    for b, p in (('batchG-20261126', 'bg-v4'), ('revE-20261125', 'revE-drift12')):
        for r in sorted(grp.get(('승컴' if b.startswith('batch') else '고컴', b, p), []), key=lambda r: r['rep']):
            kl = rd(ROOT / r['raw_path'], 'kernel.log') if r['host'] == '승컴' else rd(GO / r['raw_path'].split(':', 1)[1], 'kernel.log')
            dev = [abs(int(s_) - int(f_)) / int(f_) for f_, s_ in re.findall(r'WATGC_V2 reset .*reason=waf-drift reference_q16=(\d+) sample_q16=(\d+)', kl)]
            thr = .125 if 'drift12' in p else .25
            add('drift50 변화 감지 동작 (비교 기준)', f'{p} rep{r["rep"]}', f'resets={len(dev)} min_dev={min(dev):.3f} n_dev_25_50={sum(.25 < x <= .5 for x in dev)}' if dev else 'resets=0',
                'OK' if all(x > thr for x in dev) else 'FAIL', f'threshold {thr:.3f}')
    # 5 Greedy GC vs iCAT same conditions (rep-paired)
    gg = {r['rep']: r for r in grp.get(('승컴', 'greedygc-20261126', 'greedygc'), [])}; bv = {r['rep']: r for r in grp.get(('승컴', 'batchG-20261126', 'bg-v4'), [])}
    for rep in sorted(set(gg) & set(bv)):
        A, B = bv[rep], gg[rep]
        same = {k: A[k] == B[k] for k in ('host', 'cpu_model', 'kernel_cmdline_sha', 'fio_job_sha256', 'fio_seeds_first_phase', 'ycsb_workload_sha256', 'workload', 'phases', 'init_counters_zero', 'init_preset_ok')}
        add('Greedy GC 대 iCAT 동일 조건', f'rep{rep} bg-v4 vs greedygc', ', '.join(k for k, v in same.items() if not v) or 'all identical',
            'OK' if all(same.values()) else 'DIFF', f'module {A["module"]} vs {B["module"]}; kernel policy {A["kernel_policy"]} vs {B["kernel_policy"]}; phase min {A["phase_minutes"]} vs {B["phase_minutes"]}; YCSB ops (time-limited, outcome) {A["ycsb_ops"]} vs {B["ycsb_ops"]}')
    # 5b mixY SmartGC comparisons: phases are 1800 s time-limited; overrun = device could not finish the step on time
    for (h, b, p), rs in sorted(grp.items()):
        for r in rs:
            if r['workload'] != 'mixY': continue
            pm = [float(x) for x in r['phase_minutes'].split('/')]; over = [f'S{i + 1:02d}={m:.1f}' for i, m in enumerate(pm) if m > 31]
            add('mixY 동일 조건 (단계 시간)', f'{h} {r["run_id"]}', f'{len(over)}/20 phases > 31 min', 'OK' if not over else 'OVERRUN',
                (', '.join(over) + f'; total {r["measured_hours"]} h vs 10 h nominal') if over else 'all 20 phases ~30 min')
    # 6 host / batch mixing
    for (h, b, p), rs in grp.items():
        nodes = {r['nodename'] for r in rs}
        if len(nodes) != 1: add('호스트·배치 혼합', f'{b}/{p}', nodes, 'MIXED')
    add('호스트·배치 혼합', 'every descriptive group = one host x one batch x one policy', f'{len(grp)} groups', 'OK' if all(len({r["nodename"] for r in rs}) == 1 for rs in grp.values()) else 'MIXED')
    for c in srows:
        if c['kind'] == 'contrast' and not c['comparison'].startswith('direct') and 'welch_p' in c:
            add('호스트·배치 혼합', f'{c["treatment"]} - {c["control"]} {c["metric"]}', c['comparison'], 'INDIRECT (label required)', 'same host, different batch: never pooled; reported as reference only')
    add('호스트·배치 혼합', '집컴 figure02: revB NoElim/NoSettle vs revA-v4', 'control from another batch (revB has only n=1 V4)', 'INDIRECT (label required)',
        'revE-noelim - revE-v4 (same batch, n=3) exists and is the direct NoElim test')
    return out

DELIV = 'origin/report/home-delivery-20261127:report/delivery-20261127/final_experiment_validity.csv'
def crosscheck_delivery(runs):
    """집컴 per-run table vs this recomputation; key = raw path (main path or branch:path)."""
    import io
    txt = subprocess.run(['git', '-C', str(ROOT), 'show', DELIV], capture_output=True, text=True).stdout.lstrip('\ufeff')
    by = {r['raw_path'].split(':', 1)[-1]: r for r in runs}
    out = []
    F = [('Host_Pages', 'host_pages', 0), ('GC_Pages', 'gc_pages', 0), ('WAF_Recalc', 'total_waf', 5e-7), ('WAF_PhaseA', 'A_waf', 5e-7),
         ('WAF_PhaseB', 'B_waf', 5e-7), ('WAF_PhaseC', 'C_waf', 5e-7), ('Module_SHA256', 'module_sha256', None), ('FIO_Seeds', 'fio_seeds_first_phase', None)]
    for e in csv.DictReader(io.StringIO(txt)):
        rp = e['Raw_Path'].split(':', 1)[-1]; r = by.get(rp)
        if not r: out.append({'excel_or_table': DELIV, 'row_key': rp, 'field': '(run)', 'table_value': 'present', 'recalc_value': 'not in this validation scope', 'agree': ''}); continue
        for tf, rf, tol in F:
            tv, rv = e.get(tf, ''), r.get(rf, '')
            if tv in ('', None) and rv in ('', None): continue
            num = lambda x: isinstance(x, (int, float)) or re.fullmatch(r'-?[\d.]+(e-?\d+)?', str(x)) is not None
            if tol is None: ok, dd = str(tv) == str(rv), ''
            elif num(tv) and num(rv): dd = abs(float(tv) - float(rv)); ok = dd <= tol
            else: ok, dd = (str(tv).upper() in ('N/A', 'NA', '') and rv in ('', None)), ''   # table N/A where recalc has no value
            out.append({'excel_or_table': DELIV, 'row_key': rp, 'raw_location': r['raw_path'], 'field': tf, 'table_value': tv, 'recalc_value': rv, 'abs_diff': dd, 'agree': ok,
                        'cause': '' if ok else 'value differs from raw-log recomputation', 'recommendation': '' if ok else 'replace with recalc_value after checking the cell formula'})
        vt = e['Validity'].upper().startswith('VALID'); out.append({'excel_or_table': DELIV, 'row_key': rp, 'raw_location': r['raw_path'], 'field': 'Validity',
                                                                     'table_value': e['Validity'], 'recalc_value': r['valid'], 'agree': vt == r['valid']})
    return out

STATS = 'origin/report/home-delivery-20261127:report/delivery-20261127/final_statistical_audit.csv'
SMAP = {'revA-random': 'revA-20261114/revA-random', 'revA-v1': 'revA-20261114/revA-v1', 'revA-v2': 'revA-20261114/revA-v2', 'revA-v4': 'revA-20261114/revA-v4',
        'revC-online': 'revC-20261124/online', 'revC-elim10': 'revC-20261124/revC-elim10', 'revC-elim25': 'revC-20261124/revC-elim25',
        'revC-arm60': 'revC-20261124/revB-arm60', 'revC-v4': 'revC-20261124/revC-v4', 'revD-fullreset': 'revD-20261124/revD-fullreset',
        'revD-nodrift': 'revD-20261124/revD-nodrift', 'revD-v4': 'revD-20261124/revD-v4', 'abl-bundle-off': 'revision-additional-ablation/abl-off-elim-settle-drift-probe',
        'abl-nodiscount': 'revision-additional-ablation/abl-nodiscount', 'abl-v4': 'revision-additional-ablation/abl-v4',
        'revE-noelim': 'revE-20261125/revE-noelim', 'revE-drift12': 'revE-20261125/revE-drift12', 'revE-v4': 'revE-20261125/revE-v4',
        'greedy-online': 'greedy-20261125/greedy-online', 'revB-noelim': 'revB-20261122/revB-noelim', 'revB-nosettle': 'revB-20261122/revB-nosettle',
        'batchG-greedygc': 'greedygc-20261126/greedygc', 'batchG-drift50': 'drift50-20261126/drift50', 'batchG-v4': 'batchG-20261126/bg-v4',
        'arm47-seungcom': 'arm47-20261127/arm47'}
def crosscheck_stats(srows):
    import io
    txt = subprocess.run(['git', '-C', str(ROOT), 'show', STATS], capture_output=True, text=True).stdout.lstrip('\ufeff')
    mine = {(c['treatment'], c['control'], c['metric']): c for c in srows if c['kind'] == 'contrast'}
    out = []
    for e in csv.DictReader(io.StringIO(txt)):
        t, _, c = e['Contrast_Variant_Minus_Ctrl'].partition(' - '); k = {'Total WAF': 'total_waf', 'Phase C WAF': 'C_waf'}.get(e['Metric'])
        m = mine.get((SMAP.get(t), SMAP.get(c), k))
        key = f"{e['Family']}: {e['Contrast_Variant_Minus_Ctrl']} {e['Metric']}"
        if not m or 'diff' not in m:
            out.append({'excel_or_table': STATS, 'row_key': key, 'field': '(contrast)', 'table_value': e['Stat_Verdict'], 'recalc_value': 'n=1 or not recomputed', 'agree': ''}); continue
        for tf, mf, tol in (('Welch_Delta', 'diff', 5e-6), ('Welch_df', 'welch_df', 5e-3), ('Welch_p', 'welch_p', 5e-6), ('Hedges_g', 'hedges_g', 5e-3),
                            ('Paired_p', 'paired_p', 5e-6), ('Holm_p', 'holm_p_family', 5e-6)):
            tv, rv = e.get(tf, ''), m.get(mf, '')
            if tv in ('', 'N/A') or rv == '': continue
            dd = abs(float(tv) - float(rv)); ok = dd <= max(tol, 5e-4 * abs(float(tv))) if tf != 'Holm_p' else dd <= 5e-6
            cause = rec = ''
            if tf == 'Holm_p' and not ok and m.get('holm_p_total_only', '') != '' and abs(float(tv) - m['holm_p_total_only']) <= 5e-6:
                ok, rv, dd = 'family definition', m['holm_p_total_only'], abs(float(tv) - m['holm_p_total_only'])
                cause = f"Holm family: 집컴 {e['Holm_Family_Spec']} (total WAF only); this check {m['holm_family_size']} tests (total+C). revA prereg defines no family"
                rec = 'state the family in the table caption; verdict (reject or not at .05) is the same under both families'
            out.append({'excel_or_table': STATS, 'row_key': key, 'raw_location': f"{m['control']} | {m['treatment']}", 'field': tf, 'table_value': tv, 'recalc_value': rv,
                        'abs_diff': dd, 'agree': ok, 'cause': cause, 'recommendation': rec})
        lo, hi = [float(x) for x in re.findall(r'[-+]?\d+\.\d+', e['Welch_CI95'])]
        out.append({'excel_or_table': STATS, 'row_key': key, 'raw_location': f"{m['control']} | {m['treatment']}", 'field': 'Welch_CI95', 'table_value': e['Welch_CI95'], 'recalc_value': f"[{m['ci95_lo']:+.4f}, {m['ci95_hi']:+.4f}]",
                    'agree': abs(lo - m['ci95_lo']) <= 6e-5 and abs(hi - m['ci95_hi']) <= 6e-5})
    return out

def prerevision(cm):
    """Sep-era sources of the pre-revision paper figures (mix-20260911, 승컴): valid reps per (workload, policy, length suffix),
    and the 9-workload Online(original iCAT) vs Greedy claim recomputed from raw."""
    rs = [run('main', 'mix-20260911', d, ROOT, cm, {}) for d in sorted((ROOT / 'result/mix-20260911').glob('*-rep*')) if d.is_dir() and (d / 'summary.txt').exists()]
    g = {}
    for r in rs: g.setdefault((r['workload'], r['policy'], r['role']), []).append(r)
    out = [{'kind': 'group', 'workload': w, 'policy': p, 'length_or_role': role, 'dirs': len(x), 'valid': sum(r['valid'] for r in x),
            'invalid_reasons': ' | '.join(sorted({r['invalid_reason'] for r in x if not r['valid']})),
            'total_waf_valid': ' / '.join(f'{r["total_waf"]:.4f}' for r in sorted(x, key=lambda r: r['rep']) if r['valid'] and r.get('total_waf')),
            'host': '+'.join(sorted({r['host'] for r in x}))} for (w, p, role), x in sorted(g.items())]
    for w in ('mixC', 'mixD', 'mixF', 'mixK', 'mixL', 'mixM', 'mixO', 'mixP', 'mixQ'):
        A = [r['total_waf'] for r in g.get((w, 'greedy', 'main'), []) if r['valid']]; B = [r['total_waf'] for r in g.get((w, 'online', 'main'), []) if r['valid']]
        row = {'kind': '9-workload claim: online - greedy', 'workload': w, 'policy': 'online(original iCAT) - greedy', 'n_greedy_valid': len(A), 'n_online_valid': len(B)}
        if len(A) >= 3 and len(B) >= 3: row.update(welch(A, B)); row['pct'] = 100 * (st.mean(B) - st.mean(A)) / st.mean(A)
        else: row['note'] = 'n<3: no test'
        out.append(row)
    return out

if __name__ == '__main__':
    main()
