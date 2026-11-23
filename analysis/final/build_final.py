#!/usr/bin/env python3
"""Final integrated report tables/figures (2026-11-23). Reads existing result files only; runs nothing.

Inputs (all inside this repository):
  GoCom (oy-B550M-DS3H, Ryzen 5 3600XT):
    result/revA-20261114/{raw,results}      Random / V1 / V2 / V4 / arm47, mixFYF, n=3 (arm47 n=1)
    result/revB-20261122/raw                revB-v4 (n=1), noelim (n=3), nosettle (n=3), arm60 (n=1), mixFYF
    result/adapt-v7-mixY-20261122           v7 mixY transition analysis (from result/v7-20261011-icat2/mixY)
    result/gocom-sg-20261119/mixY-*         SmartGC / SmartGCQ / SG-Greedy / SG-ARM47, mixY, n=1
  SeungCom (oy-System-Product-Name, i7-7700):
    result/smartgc-20261119/report/compare.csv and the run dirs it names (SmartGC, SmartGC-EQ8, CAT-47, iCAT V4, mixY, n=1)
Outputs: result/final-20261123/{tables/*.csv, figures/*.png}
Every number is tagged in the CSVs with kind = measured | computed | estimated.
"""
import csv, json, math, re, statistics as st, subprocess, sys, datetime as dt
from pathlib import Path
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / 'result'
OUT = R / 'final-20261123'; TAB = OUT / 'tables'; FIG = OUT / 'figures'
TAB.mkdir(parents=True, exist_ok=True); FIG.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(R / 'revA-20261114'))
import analyze as A  # revA loader/validator (read-only use)

T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447}
GOCOM, SEUNG = 'GoCom (Ryzen 5 3600XT)', 'SeungCom (i7-7700)'
SEQ = 'F S V F V S F S V F V S F S V F V S F S'.split()


def wcsv(name, header, rows):
    with open(TAB / name, 'w', newline='') as f:
        w = csv.writer(f); w.writerow(header)
        for r in rows: w.writerow(['' if x is None else (f'{x:.6g}' if isinstance(x, float) else x) for x in r])


def mci(xs):
    m = st.mean(xs)
    if len(xs) < 2: return m, None, None, None
    sd = st.stdev(xs); h = T95[len(xs) - 1] * sd / math.sqrt(len(xs)); return m, sd, m - h, m + h


def welch(x, y):
    """mean(x)-mean(y), Welch 95% CI (t quantile by Welch-Satterthwaite df, scipy if available)."""
    d = st.mean(x) - st.mean(y); vx, vy = st.variance(x) / len(x), st.variance(y) / len(y); se = math.sqrt(vx + vy)
    df = (vx + vy) ** 2 / (vx ** 2 / (len(x) - 1) + vy ** 2 / (len(y) - 1))
    try:
        from scipy import stats; q = stats.t.ppf(.975, df); p = 2 * stats.t.sf(abs(d) / se, df)
    except ImportError:
        q = T95[max(1, min(6, round(df)))]; p = None
    return d, d - q * se, d + q * se, df, p


# ---------------------------------------------------------------- 1. mixFYF runs (revA + revB, GoCom)
def fyf_runs():
    out = []
    for camp in ('revA-20261114', 'revB-20261122'):
        for d in sorted((R / camp / 'raw').glob('mixFYF-*-rep[0-9]')):
            r = A.load(d); r['exit'] = int((d / 'exit-code.txt').read_text().strip())
            v = A.validate(r)
            fin = A.counters_at(r['samples'], 1e18) if r['samples'] else {}
            out.append(dict(campaign=camp, run=d.name, policy=r['policy'], rep=r['rep'], valid=v['valid'], reason=v['reason'],
                            waf=r['waf'], waf_A=r['waf_A'], waf_B=r['waf_B'], waf_C=r['waf_C'],
                            windows=fin.get('window'), selections=fin.get('select'), evaluations=fin.get('eval_explore'),
                            eliminations=fin.get('elim'), policy_updates=fin.get('best_change'), resets=fin.get('reset'),
                            learner_ms=(fin.get('learner_ns') or 0) / 1e6 if fin else None,
                            settled_lines=(d / 'kernel.log').read_text(errors='replace').count('WATGC_V2 settled'),
                            env=(d / 'environment.txt').read_text().splitlines()))
    return out


runs = fyf_runs()
wcsv('fyf_runs.csv', ['campaign', 'run', 'policy', 'rep', 'valid', 'reason', 'WAF_total', 'WAF_FIO1', 'WAF_YCSBA', 'WAF_FIO2',
                      'valid_windows', 'selections', 'evaluations_nonincumbent', 'eliminations', 'policy_updates', 'drift_resets',
                      'learner_ktime_ms', 'settled_lines', 'kind', 'host', 'raw_dir'],
     [(x['campaign'], x['run'], x['policy'], x['rep'], x['valid'], x['reason'], x['waf'], x['waf_A'], x['waf_B'], x['waf_C'],
       x['windows'], x['selections'], x['evaluations'], x['eliminations'], x['policy_updates'], x['resets'], x['learner_ms'],
       x['settled_lines'], 'measured (FTL counters, learner ktime instrumentation)', GOCOM, f"result/{x['campaign']}/raw/{x['run']}")
      for x in runs])
by = {}
for x in runs:
    if x['valid']: by.setdefault(x['policy'], []).append(x)
W = lambda p, k='waf': [x[k] for x in by[p]]

LAB = {'revA-random': 'Random', 'revA-v4': 'iCAT V4', 'revA-v1': 'V1', 'revA-v2': 'V2 (no elim, no settle)',
       'revB-v4': 'V4 (revB bridge)', 'revB-noelim': 'no elimination', 'revB-nosettle': 'no settling',
       'revB-arm60': '60 arms', 'arm47': 'CAT-47 (fixed)'}
summ = []
for p in ['revA-random', 'revA-v4', 'revA-v1', 'revA-v2', 'revB-v4', 'revB-noelim', 'revB-nosettle', 'revB-arm60', 'arm47']:
    if p not in by: continue
    for k in ('waf', 'waf_A', 'waf_B', 'waf_C', 'windows', 'selections', 'evaluations', 'eliminations', 'policy_updates', 'resets', 'learner_ms'):
        xs = [v for v in W(p, k) if v is not None]
        if not xs: continue
        m, sd, lo, hi = mci(xs)
        summ.append((p, LAB[p], k, len(xs), m, sd, lo, hi, ';'.join(f'{v:.4f}' if isinstance(v, float) else str(v) for v in xs),
                     'measured' if k != 'learner_ms' else 'measured (ktime inside learner path, not process CPU)'))
wcsv('fyf_summary.csv', ['policy', 'label', 'metric', 'n', 'mean', 'sd', 'ci95_lo', 'ci95_hi', 'values', 'kind'], summ)

# Random vs V4
d, lo, hi, df, p = welch(W('revA-random'), W('revA-v4'))
rv = [('WAF total', *welch(W('revA-random'), W('revA-v4')))]
for k, n in (('waf_A', 'WAF FIO-Fast 1'), ('waf_B', 'WAF YCSB-A'), ('waf_C', 'WAF FIO-Fast 2'),
             ('selections', 'candidate selections'), ('evaluations', 'non-incumbent evaluations')):
    rv.append((n, *welch(W('revA-random', k), W('revA-v4', k))))
wcsv('random_vs_v4.csv', ['metric', 'Random_minus_V4', 'ci95_lo', 'ci95_hi', 'welch_df', 'p', 'kind'],
     [(*x, 'computed from measured runs (n=3 vs n=3)') for x in rv])

# 2x2 ablation (pre-registered contrasts; V4/V2 from revA, bridge failed -> V4 pooled sensitivity)
v4pool = W('revA-v4') + W('revB-v4')
con = [('elimination effect | settling on  (noelim - V4)', W('revB-noelim'), W('revA-v4')),
       ('elimination effect | settling on  (noelim - V4 pooled n=4)', W('revB-noelim'), v4pool),
       ('elimination effect | settling off (V2 - nosettle)', W('revA-v2'), W('revB-nosettle')),
       ('settling effect | elimination on  (nosettle - V4)', W('revB-nosettle'), W('revA-v4')),
       ('settling effect | elimination on  (nosettle - V4 pooled n=4)', W('revB-nosettle'), v4pool),
       ('settling effect | elimination off (V2 - noelim)', W('revA-v2'), W('revB-noelim')),
       ('both removed (V2 - V4)', W('revA-v2'), W('revA-v4')),
       ('V1 - V4 (revA)', W('revA-v1'), W('revA-v4'))]
abl = []
for name, x, y in con:
    d, lo, hi, df, p = welch(x, y)
    abl.append((name, len(x), len(y), d, lo, hi, df, p, 'distinguishable' if lo > 0 or hi < 0 else 'not distinguishable'))
# interaction: (noelim - V4) - (V2 - nosettle); SE from the four group variances
g = {k: W(k) for k in ('revB-noelim', 'revA-v4', 'revA-v2', 'revB-nosettle')}
inter = (st.mean(g['revB-noelim']) - st.mean(g['revA-v4'])) - (st.mean(g['revA-v2']) - st.mean(g['revB-nosettle']))
se = math.sqrt(sum(st.variance(v) / len(v) for v in g.values()))
abl.append(('interaction (elim effect with settling - without)', 12, '', inter, inter - 2.0 * se, inter + 2.0 * se, '', '',
            'approx. +-2 SE; not distinguishable' if abs(inter) < 2 * se else 'approx. +-2 SE'))
wcsv('ablation_2x2.csv', ['contrast', 'n_a', 'n_b', 'diff_WAF', 'ci95_lo', 'ci95_hi', 'welch_df', 'p', 'verdict'], abl)
b = by['revB-v4'][0]['waf']; ma, sa = st.mean(W('revA-v4')), st.stdev(W('revA-v4'))
wcsv('bridge_check.csv', ['revB_v4_WAF', 'revA_v4_mean', 'revA_v4_sd', 'diff', 'diff_pct', 'diff_in_sd', 'criterion', 'verdict'],
     [(b, ma, sa, b - ma, 100 * (b - ma) / ma, (b - ma) / sa, '|diff| <= 3 SD and <= 1 %',
       'FAIL (revA reuse withheld; V4 pooled n=4 reported as sensitivity)' if abs(b - ma) > 3 * sa or abs(b - ma) / ma > .01 else 'PASS')])

# --- figure: Random vs V4 and ablation
COL = {'revA-random': '#9e9e9e', 'revA-v4': '#1b9e77', 'revA-v1': '#66a61e', 'revA-v2': '#d95f02', 'revB-v4': '#1b9e77',
       'revB-noelim': '#7570b3', 'revB-nosettle': '#e7298a', 'revB-arm60': '#a6761d', 'arm47': '#666666'}
fig, ax = plt.subplots(1, 2, figsize=(12, 4.2), gridspec_kw=dict(width_ratios=[1, 1.6]))
for i, p in enumerate(['revA-random', 'revA-v4']):
    xs = W(p); m, sd, lo, hi = mci(xs)
    ax[0].bar(i, m, .6, color=COL[p], yerr=[[m - lo], [hi - m]], capsize=4)
    ax[0].scatter([i] * len(xs), xs, color='k', s=10, zorder=3)
    ax[0].text(i, hi + .005, f'{m:.3f}', ha='center', fontsize=9)
ax[0].set_xticks([0, 1], ['Random', 'iCAT V4']); ax[0].set_ylim(2.0, 2.4); ax[0].set_ylabel('WAF, mixFYF total (lower is better)')
ax[0].set_title('(a) Random selection vs iCAT V4 (n=3, 95% CI)', fontsize=10)
order = ['revA-v4', 'revB-v4', 'revB-noelim', 'revB-nosettle', 'revA-v2', 'revA-v1', 'revB-arm60']
for i, p in enumerate(order):
    xs = W(p); m, sd, lo, hi = mci(xs)
    ax[1].bar(i, m, .6, color=COL[p], alpha=.55 if p == 'revB-v4' else 1,
              yerr=None if lo is None else [[m - lo], [hi - m]], capsize=4, hatch='//' if len(xs) == 1 else None)
    ax[1].scatter([i] * len(xs), xs, color='k', s=10, zorder=3)
    ax[1].text(i, min((hi or m) + .006, 2.405), f'{m:.3f}\nn={len(xs)}', ha='center', fontsize=8, va='bottom' if (hi or m) < 2.39 else 'top', bbox=dict(fc='white', ec='none', pad=.5))
ax[1].set_xticks(range(len(order)), ['V4\n(revA)', 'V4\n(revB)', 'no\nelim', 'no\nsettle', 'V2\n(neither)', 'V1', '60\narms'], fontsize=8)
ax[1].set_ylim(2.0, 2.45); ax[1].set_title('(b) Ablation (hatched = n=1, no CI)', fontsize=10)
fig.tight_layout(); fig.savefig(FIG / 'fig1_random_ablation.png', dpi=160); plt.close(fig)

# ---------------------------------------------------------------- 2. mixY: SmartGC family vs CAT-47 vs iCAT (both hosts)
kv = lambda line: dict(t.split('=', 1) for t in line.split() if '=' in t)


def read_kernel(d):
    for n in ('kernel.log', 'kernel.log.zst'):
        f = d / n
        if f.exists() and f.stat().st_size:
            if n.endswith('.zst'):
                return subprocess.run(['zstdcat', str(f)], capture_output=True, text=True, errors='replace').stdout
            return f.read_text(errors='replace')
    return ''


def mixy(label, host, d, sha=None):
    r = dict(label=label, host=host, dir=str(d.relative_to(ROOT)), exit=(d / 'exit-code.txt').read_text().strip())
    s = (d / 'summary.txt').read_text()
    tot = kv(next(l for l in s.splitlines() if l.startswith('total')))
    r['host_pages'], r['gc_pages'], r['host_TB'] = int(tot['host_pages']), int(tot['gc_pages']), int(tot['host_bytes']) / 1e12
    r['WAF'] = 1 + r['gc_pages'] / r['host_pages']
    fc = (d / 'final-control.txt').read_text().splitlines()
    sg = [kv(l) for l in fc if l.startswith('smartgc part=')]
    r['nand_pages'] = sum(int(x['nand_pages']) for x in sg) if sg else r['host_pages'] + r['gc_pages']
    r['WAF_nand'] = r['nand_pages'] / r['host_pages']
    r['gc_count'] = sum(int(kv(l)['gc_count']) for l in fc if l.startswith('part='))
    r['steps'] = sum(int(x['steps']) for x in sg) if sg else None
    r['phase_waf'] = [float(m) for m in re.findall(r'^phaseS\d\d\(\w+\).*WAF=([\d.]+)', s, re.M)]
    t0 = dt.datetime.fromisoformat((d / 'phase-S01-start.time').read_text().strip())
    t1 = dt.datetime.fromisoformat((d / 'phase-S20-end.time').read_text().strip())
    r['measured_wall_h'] = (t1 - t0).total_seconds() / 3600
    # per-phase performance + chmodel warnings logged in kernel.log
    kl = read_kernel(d); marks = {}; warn_t = []
    for l in kl.splitlines():
        m = re.match(r'\[\s*([\d.]+)\]', l)
        if not m: continue
        if 'Need to increase array size' in l: warn_t.append(float(m[1])); continue
        p = re.search(r' phase=(S\d\d) (START|END)', l)
        if p and 'mix-mixY' in l: marks[(p[1], p[2])] = float(m[1])
    warn_t.sort()
    import bisect
    s01 = dt.datetime.fromisoformat((d / 'phase-S01-start.time').read_text().strip()).timestamp()
    off = marks[('S01', 'START')] - s01 if ('S01', 'START') in marks else None
    r['warn_lines_in_log'] = len(warn_t); r['markers_found'] = sum(1 for k in marks if k[1] == 'START')
    ph = []
    for i in range(1, 21):
        s_ = f'S{i:02d}'; w = SEQ[i - 1]
        a = dt.datetime.fromisoformat((d / f'phase-{s_}-start.time').read_text().strip())
        e = dt.datetime.fromisoformat((d / f'phase-{s_}-end.time').read_text().strip())
        row = dict(phase=s_, workload=w, wall_s=(e - a).total_seconds(), waf=r['phase_waf'][i - 1] if len(r['phase_waf']) >= i else None)
        # phase window in kernel time = wall time + offset (offset from the S01 START marker; markers of later
        # phases can be missing when the warning flood overruns the kernel ring buffer)
        ka, ke = a.timestamp() + off, e.timestamp() + off
        row['warn_lines'] = bisect.bisect_left(warn_t, ke) - bisect.bisect_left(warn_t, ka) if off is not None else None
        row['marker_found'] = (s_, 'START') in marks
        j = d / f'phase-{s_}.json'
        if w in 'FS' and j.exists():
            jj = json.loads(j.read_text()); jobs = [x['write'] for x in jj['jobs']]
            N = sum(x['clat_ns']['N'] for x in jobs)
            row['MBps'] = sum(x['io_bytes'] for x in jobs) / 1e6 / (max(x['runtime'] for x in jobs) / 1e3)
            row['clat_mean_us'] = sum(x['clat_ns']['mean'] * x['clat_ns']['N'] for x in jobs) / N / 1e3
            row['clat_p99_us'] = max(x['clat_ns']['percentile']['99.000000'] for x in jobs) / 1e3
            row['clat_p999_us'] = max(x['clat_ns']['percentile'].get('99.900000', 0) for x in jobs) / 1e3
            row['fio_runtime_s'] = max(x['runtime'] for x in jobs) / 1e3
        fb = d / f'filebench-{s_}.txt'
        if w == 'V' and fb.exists():
            m = re.search(r'IO Summary: +\d+ ops ([\d.]+) ops/s .*? ([\d.]+)mb/s +([\d.]+)ms/op', fb.read_text())
            if m: row['ops_s'], row['MBps'], row['ms_op'] = float(m[1]), float(m[2]), float(m[3])
        ph.append(row)
    r['phases'] = ph; r['warn_total'] = sum(x['warn_lines'] or 0 for x in ph)
    r['kernel_log_lines'] = kl.count('\n')
    return r


SGR = R / 'smartgc-20261119'; GC = R / 'gc-20261010'; GO = R / 'gocom-sg-20261119'
MY = [('SmartGC-EQ8', SEUNG, GC / 'mixY-smartgc-eq8-rep1'), ('SmartGC', SEUNG, SGR / 'resume/mixY-smartgc-rep1'),
      ('CAT-47', SEUNG, GC / 'mixY-sg-arm47-rep1'), ('iCAT V4', SEUNG, SGR / 'resume/mixY-onlinev4-rep1'),
      ('SmartGC', GOCOM, GO / 'mixY-smartgc-rep1'), ('SmartGCQ (Q0=2000)', GOCOM, GO / 'mixY-smartgcq-rep1'),
      ('SG-Greedy', GOCOM, GO / 'mixY-sg-greedy-rep1'), ('SG-ARM47 (CAT-47)', GOCOM, GO / 'mixY-sg-arm47-rep1'),
      ('iCAT v7', GOCOM, R / 'v7-20261011-icat2/mixY/mixY-onlinev7-rep1')]
my = [mixy(*x) for x in MY]
# SeungCom CPU / memory columns come from its own compare.csv (measured by its 30 s sampler; not re-derived here)
sc = {row['label']: row for row in csv.DictReader(open(SGR / 'report/compare.csv'))}
wcsv('mixY_compare.csv', ['host', 'policy', 'n', 'exit', 'WAF', 'WAF_nand', 'host_TB_total', 'gc_count', 'smartgc_steps',
                          'measured_wall_h_S01_to_S20', 'chmodel_warn_lines_in_phases', 'chmodel_warn_lines_whole_log', 'phase_markers_found', 'dispatcher_util', 'vmalloc_delta_kB', 'raw_dir'],
     [(r['host'], r['label'], 1, r['exit'], r['WAF'], r['WAF_nand'], r['host_TB'], r['gc_count'], r['steps'], r['measured_wall_h'],
       r['warn_total'], r['warn_lines_in_log'], r['markers_found'], sc.get(r['label'], {}).get('disp_util', '') if r['host'] == SEUNG else 'not sampled',
       sc.get(r['label'], {}).get('VmallocUsed_delta_kB', '') if r['host'] == SEUNG else 'not sampled', r['dir']) for r in my])
rows = []
for r in my:
    for x in r['phases']:
        rows.append((r['host'], r['label'], x['phase'], x['workload'], x['wall_s'], x['waf'], x['warn_lines'], x.get('MBps'),
                     x.get('clat_mean_us'), x.get('clat_p99_us'), x.get('clat_p999_us'), x.get('fio_runtime_s'), x.get('ops_s'), x.get('ms_op')))
wcsv('mixY_phase_perf.csv', ['host', 'policy', 'phase', 'workload', 'phase_wall_s', 'phase_WAF', 'chmodel_warn_lines_logged',
                             'MBps', 'fio_clat_mean_us', 'fio_clat_p99_us_maxjob', 'fio_clat_p999_us_maxjob', 'fio_runtime_s',
                             'varmail_ops_s', 'varmail_ms_op'], rows)

# --- figure: mixY WAF / host TB (both hosts) and per-phase WAF
CM = {'SmartGC-EQ8': '#d95f02', 'SmartGC': '#e7298a', 'CAT-47': '#7570b3', 'iCAT V4': '#1b9e77', 'SmartGCQ (Q0=2000)': '#e6ab02',
      'SG-Greedy': '#a6761d', 'SG-ARM47 (CAT-47)': '#7570b3', 'iCAT v7': '#1b9e77'}
fig, ax = plt.subplots(1, 2, figsize=(13, 4.4))
SHORT = {'SmartGC-EQ8': 'SmartGC\n-EQ8', 'SmartGCQ (Q0=2000)': 'SmartGCQ\n(Q0=2000)', 'SG-Greedy': 'SG-\nGreedy', 'SG-ARM47 (CAT-47)': 'SG-ARM47\n(CAT-47)'}
lab = [f"{SHORT.get(r['label'], r['label'])}\n[{'S' if r['host'] == SEUNG else 'G'}]" for r in my]
for i, r in enumerate(my):
    ax[0].bar(i, r['WAF_nand'], .65, color=CM[r['label']], hatch=None if r['host'] == SEUNG else '..', edgecolor='k', lw=.4)
    ax[0].text(i, r['WAF_nand'] + .15, f"{r['WAF_nand']:.2f}", ha='center', fontsize=8)
    ax[1].bar(i, r['host_TB'], .65, color=CM[r['label']], hatch=None if r['host'] == SEUNG else '..', edgecolor='k', lw=.4)
    ax[1].text(i, r['host_TB'] + .1, f"{r['host_TB']:.2f}", ha='center', fontsize=8)
for a in ax: a.set_xticks(range(len(my)), lab, fontsize=7); a.axvline(3.5, color='k', lw=.6, ls=':')
ax[0].set_ylabel('WAF_nand = NAND programs / host pages'); ax[0].set_title('(a) mixY write amplification (n=1 each)', fontsize=10)
ax[1].set_ylabel('host data written, S01-S20 (TB)'); ax[1].set_title('(b) host writes (FIO size-bounded, Varmail 1800 s)', fontsize=10)
fig.text(.01, .01, '[S] = SeungCom i7-7700, [G] = GoCom Ryzen 3600XT (dotted). Hosts are not pooled.', fontsize=7)
fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(FIG / 'fig2_mixY_waf_throughput.png', dpi=160); plt.close(fig)

# --- figure: chmodel warnings vs latency / throughput per phase
fig, ax = plt.subplots(1, 3, figsize=(14, 4))
for r in my:
    if not r['warn_total']: continue
    xs = [(x['warn_lines'], x) for x in r['phases'] if x['warn_lines'] is not None]
    mk = 'o' if r['host'] == SEUNG else 's'
    f = [(w, x) for w, x in xs if x['workload'] in 'FS' and x.get('clat_p99_us')]
    v = [(w, x) for w, x in xs if x['workload'] == 'V' and x.get('ops_s')]
    nm = f"{r['label']} [{'S' if r['host'] == SEUNG else 'G'}]"
    ax[0].scatter([w + 1 for w, _ in f], [x['clat_p99_us'] / 1e3 for _, x in f], marker=mk, label=nm, color=CM[r['label']])
    ax[1].scatter([w + 1 for w, _ in f], [x['wall_s'] for _, x in f], marker=mk, label=nm, color=CM[r['label']])
    ax[2].scatter([w + 1 for w, _ in v], [x['ops_s'] for _, x in v], marker=mk, label=nm, color=CM[r['label']])
for r in my:  # no-warning references as horizontal bands
    if r['warn_total']: continue
    f = [x for x in r['phases'] if x['workload'] in 'FS' and x.get('clat_p99_us')]
    v = [x for x in r['phases'] if x['workload'] == 'V' and x.get('ops_s')]
    if f: ax[0].axhline(max(x['clat_p99_us'] for x in f) / 1e3, color=CM[r['label']], lw=.6, ls='--')
    if v: ax[2].axhline(st.mean(x['ops_s'] for x in v), color=CM[r['label']], lw=.6, ls='--')
for a, t, y in zip(ax, ['(a) FIO p99 completion latency', '(b) FIO phase wall time', '(c) Varmail throughput'],
                   ['p99 clat, slowest job (ms)', 'phase wall time (s)', 'ops/s']):
    a.set_xscale('log'); a.set_xlabel('chmodel warning lines logged in phase (+1)'); a.set_title(t, fontsize=10); a.set_ylabel(y)
ax[0].set_yscale('log'); ax[0].legend(fontsize=7)
fig.text(.01, .01, 'dashed = warning-free runs (iCAT V4, CAT-47, SG-Greedy): max FIO p99 / mean Varmail ops/s. Counts are lines logged in kernel.log (lower bound).', fontsize=7)
fig.tight_layout(rect=(0, .04, 1, 1)); fig.savefig(FIG / 'fig3_chmodel_warnings.png', dpi=160); plt.close(fig)

# per-policy summary of warnings vs perf
wrows = []
for r in my:
    f = [x for x in r['phases'] if x['workload'] in 'FS' and x.get('clat_p99_us')]
    v = [x for x in r['phases'] if x['workload'] == 'V' and x.get('ops_s')]
    fw = [x for x in f if x['warn_lines']]; fn = [x for x in f if not x['warn_lines']]
    wrows.append((r['host'], r['label'], r['warn_total'], sum(1 for x in r['phases'] if x['warn_lines']),
                  st.mean(x['clat_p99_us'] for x in fw) / 1e3 if fw else None, st.mean(x['clat_p99_us'] for x in fn) / 1e3 if fn else None,
                  max(x['wall_s'] for x in f) if f else None, st.mean(x['wall_s'] for x in f) if f else None,
                  st.mean(x['ops_s'] for x in v) if v else None, st.mean(x['ms_op'] for x in v) if v else None))
wcsv('chmodel_warning_impact.csv', ['host', 'policy', 'warn_lines_logged_total', 'phases_with_warnings', 'FIO_p99_ms_mean_phases_with_warn',
                                    'FIO_p99_ms_mean_phases_without_warn', 'FIO_phase_wall_max_s', 'FIO_phase_wall_mean_s',
                                    'Varmail_ops_s_mean', 'Varmail_ms_op_mean'], wrows)

# ---------------------------------------------------------------- 3. memory: sizeof vs VmallocUsed (separate metrics)
ds = list(csv.DictReader(open(R / 'revA-20261114/results/resource/data_structure_sizes.csv')))
mem = [(GOCOM, x['policy'], 'computed (sizeof x partitions)', 'learner_state_in_use_B', x['learner_state_in_use_B'], 'result/revA-20261114/results/resource/data_structure_sizes.csv') for x in ds]
mem += [(GOCOM, x['policy'], 'measured (module size)', 'module_static_total_B', x['module_static_total_B'], 'size(1) of .ko sections') for x in ds]
for x in csv.DictReader(open(SGR / 'report/memory_calculated.csv')):
    mem.append((SEUNG, x['policy'], 'computed (code + sizeof)', 'learner_or_policy_state_B', x['bytes_4_partitions'], x['basis']))
for lab_, row in sc.items():
    mem.append((SEUNG, lab_, 'measured (/proc/meminfo, run mean - before load, n=1)', 'VmallocUsed_delta_kB', row['VmallocUsed_delta_kB'], row['dir']))
    mem.append((SEUNG, lab_, 'measured (/proc/modules)', 'coresize_B', row['coresize'], row['dir']))
wcsv('memory_metrics.csv', ['host', 'policy', 'kind', 'metric', 'value', 'source'], mem)

# ---------------------------------------------------------------- 4. CPU: measured vs estimated
cpu = []
for x in csv.DictReader(open(R / 'revA-20261114/results/resource/resource_summary.csv')):
    cpu.append((GOCOM, x['policy'], 'measured: ktime_get_ns() around learner path, summed', 'learner_total_ms (mixFYF 90 min)',
                x['learner_total_ms_mean'], x['learner_total_ms_sd'], x['n_valid']))
    cpu.append((GOCOM, x['policy'], 'computed: learner_total / measured wall', 'learner_share_of_wall_pct', x['learner_share_of_wall_pct_mean'], '', x['n_valid']))
for p in ('revB-v4', 'revB-noelim', 'revB-nosettle', 'revB-arm60'):
    xs = W(p, 'learner_ms'); m, sd, *_ = mci(xs)
    cpu.append((GOCOM, p, 'measured: ktime_get_ns() around learner path, summed', 'learner_total_ms (mixFYF 90 min)', m, sd, len(xs)))
for lab_, row in sc.items():
    cpu.append((SEUNG, lab_, 'measured: schedstat run time of nvmev_dispatcher / wall', 'dispatcher_util', row['disp_util'], '', 1))
    cpu.append((SEUNG, lab_, 'estimated (iCAT V4 only): gc_count x 9.4 ns/GC from resource-v124 (source not in repo)' if lab_ == 'iCAT V4'
                else 'not measured (no learner timer in smartgc-src / no learner)', 'learner_cpu_s (mixY 10 h)', row['learn_cpu_s'], '', 1))
wcsv('cpu_metrics.csv', ['host', 'policy', 'kind', 'metric', 'value', 'sd', 'n'], cpu)

# ---------------------------------------------------------------- 5. exploration cost (mixFYF) + window definitions
ec = []
for p in ['revA-random', 'revA-v1', 'revA-v2', 'revA-v4', 'revB-v4', 'revB-noelim', 'revB-nosettle', 'revB-arm60']:
    row = [p, LAB[p], len(by[p])]
    for k in ('windows', 'selections', 'evaluations', 'eliminations', 'policy_updates', 'resets', 'learner_ms'):
        row.append(st.mean(W(p, k)))
    row.append(st.mean(W(p, 'evaluations')) / st.mean(W(p, 'windows')))
    ec.append(tuple(row))
wcsv('exploration_cost.csv', ['policy', 'label', 'n', 'valid_windows', 'selections', 'evaluations_nonincumbent', 'eliminations',
                              'policy_updates', 'drift_resets', 'learner_ktime_ms', 'explore_share_of_windows'], ec)

# --- figure: v7 mixY adaptation (from adapt-v7-mixY-20261122 outputs)
te = list(csv.DictReader(open(R / 'adapt-v7-mixY-20261122/transition_events.csv')))
ps = list(csv.DictReader(open(R / 'adapt-v7-mixY-20261122/phase_summary.csv')))
fig, ax = plt.subplots(1, 2, figsize=(12, 4))
types = sorted({x['transition'] for x in te})
for i, t in enumerate(types):
    for j, k in enumerate(('detect_s', 'cover_s_derived', 'settle_s')):
        v = [float(x[k]) for x in te if x['transition'] == t and x[k] not in ('none', '')]
        ax[0].scatter([i + (j - 1) * .22] * len(v), v, s=12, color=['#1b9e77', '#7570b3', '#d95f02'][j], label=k if i == 0 else None)
    nd = sum(1 for x in te if x['transition'] == t and x['detect_s'] == 'none')
    ax[0].text(i, 1900, f'undetected\n{nd}/{sum(1 for x in te if x["transition"] == t)}', ha='center', fontsize=7)
ax[0].set_xticks(range(len(types)), [t.replace('->', '\n->') for t in types], fontsize=7); ax[0].set_yscale('log'); ax[0].set_ylim(1, 4000)
ax[0].set_ylabel('seconds after phase start'); ax[0].legend(fontsize=7, loc='lower right'); ax[0].set_title('(a) iCAT v7 per-partition reaction (GoCom mixY, n=1)', fontsize=10)
rc = [(x['phase'], x['workload'], x['recovery_s']) for x in ps[1:]]
ax[1].bar(range(len(rc)), [float(v) if v != 'not_recovered' else 0 for _, _, v in rc],
          color=[{'FIO-Fast': '#1b9e77', 'FIO-Slow': '#7570b3', 'Varmail': '#d95f02'}[w] for _, w, _ in rc])
for i, (_, _, v) in enumerate(rc):
    if v == 'not_recovered': ax[1].text(i, 30, 'n.r.', ha='center', fontsize=7, rotation=90)
ax[1].set_xticks(range(len(rc)), [p for p, _, _ in rc], fontsize=7, rotation=90)
from matplotlib.patches import Patch
ax[1].legend(handles=[Patch(color=c, label=l) for l, c in (('FIO-Fast', '#1b9e77'), ('FIO-Slow', '#7570b3'), ('Varmail', '#d95f02'))], fontsize=7, loc='upper left')
ax[1].set_ylabel('WAF recovery time (s)'); ax[1].set_title('(b) device WAF recovery per phase (+-5% of last-600 s WAF, 180 s)', fontsize=10)
fig.tight_layout(); fig.savefig(FIG / 'fig4_v7_adaptation.png', dpi=160); plt.close(fig)

# ---------------------------------------------------------------- manifest
man = dict(generated=dt.datetime.now().isoformat(timespec='seconds'),
           git_head=subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip(),
           fyf_runs=[dict(run=x['run'], campaign=x['campaign'], valid=x['valid'], waf=x['waf'],
                          module_sha256=next((l.split()[0] for l in x['env'] if l.endswith('.ko')), None)) for x in runs],
           mixY_runs=[dict(host=r['host'], policy=r['label'], dir=r['dir'], exit=r['exit'], WAF=r['WAF'], WAF_nand=r['WAF_nand'],
                           module_sha256=next((l.split()[0] for l in (ROOT / r['dir'] / 'environment.txt').read_text().splitlines() if l.endswith('.ko')), None))
                      for r in my])
(OUT / 'manifest.json').write_text(json.dumps(man, indent=1, ensure_ascii=False))
print('ok', len(runs), 'fyf runs,', len(my), 'mixY runs')
