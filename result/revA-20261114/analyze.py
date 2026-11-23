#!/usr/bin/env python3
"""revA-20261114 analysis: raw run dirs -> CSV tables, figures 7-9, experiment_manifest.json.

Definitions (pre-registered in preregistration.md):
  WAF = 1 + gc_pages / host_pages (FTL page counters, measurement start..stop).
  Valid observation windows = accepted learner windows (sum of 4 partitions).
  Candidate selections = arm changes applied after a decision.
  Candidate evaluations = accepted windows that evaluated a non-incumbent arm.
  Eliminations = candidate bits cleared online. Policy updates = incumbent (best arm) changes.
  Exploration CPU = cumulative ns inside the learner decision path (observe + set_arm), dispatcher thread.
  Windowed WAF w(t) = WAF of the trailing 300 s of control-series counters (30 s samples).
  Recovery after transition T into phase P (end E):
    self   : first t >= T+300 with |w/ref_self-1| <= 5% for every sample in [t, t+180]; ref_self = WAF of [E-600, E].
             Must occur before E-600, otherwise 'not_recovered'.
    ref47  : same, but criterion w <= 1.05 * (arm47 WAF of the same phase's [E-600, E]).
"""
import csv, json, math, re, statistics as st, sys, hashlib, subprocess, datetime
from pathlib import Path

C = Path('/home/oy/iCAT/result/revA-20261114')
import os
RAW, OUT = Path(os.environ.get('REVA_RAW', C / 'raw')), Path(os.environ.get('REVA_OUT', C / 'results'))
OUT.mkdir(exist_ok=True)
POL = ['revA-v4', 'revA-random', 'revA-v1', 'revA-v2', 'arm47']
LAB = {'revA-v4': 'iCAT V4', 'revA-random': 'Random', 'revA-v1': 'V1 (no drift/re-explore)',
       'revA-v2': 'V2 (no elim/settle)', 'arm47': 'CAT arm47 (fixed ref.)'}
T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262}
COUNTERS = ['select', 'eval_explore', 'elim', 'best_change', 'reset', 'discarded', 'learner_ns']


def field(line, key):
    m = re.search(rf'(?:^|\s){key}=(\S+)', line)
    return m and m[1]


def ts(p):
    return datetime.datetime.fromisoformat(Path(p).read_text().strip()).timestamp()


def load(d):
    m_ = re.match(r'^mix[A-Za-z]+-(.+)-rep(\d)', d.name)
    r = {'dir': str(d), 'policy': m_[1], 'rep': int(m_[2])}
    ex = (d / 'exit-code.txt')
    r['exit'] = int(ex.read_text()) if ex.exists() else None
    s = (d / 'summary.txt').read_text() if (d / 'summary.txt').exists() else ''
    m = re.search(r'^total .*WAF=([\d.]+)', s, re.M); r['waf'] = float(m[1]) if m else None
    for ph in 'ABC':
        m = re.search(rf'^phase{ph}\(\S+\) host_pages=(\d+) gc_pages=(\d+) WAF=([\d.]+)', s, re.M)
        r[f'waf_{ph}'] = float(m[3]) if m else None
        r[f't_{ph}0'] = ts(d / f'phase-{ph}-start.time') if (d / f'phase-{ph}-start.time').exists() else None
        r[f't_{ph}1'] = ts(d / f'phase-{ph}-end.time') if (d / f'phase-{ph}-end.time').exists() else None
    # 30 s counter series
    ser = []
    for l in (d / 'control-series.txt').read_text().splitlines():
        h, g = field(l, 'host_pages'), field(l, 'gc_pages')
        if h and g and field(l, 'active') == '1':
            ser.append((int(l.split()[0]), int(h), int(g)))
    r['series'] = ser
    # learner samples (kernel time) and phase markers
    samples, marks = [], {}
    kl = d / 'kernel.log'
    if kl.exists():
        for l in kl.read_text(errors='replace').splitlines():
            k = re.match(r'\[\s*([\d.]+)\]', l)
            if not k: continue
            kt = float(k[1])
            if 'WATGC_V2 sample' in l and 'revA' in l:
                samples.append(dict(kt=kt, part=int(field(l, 'part')), window=int(field(l, 'window')),
                                    evaluated=int(field(l, 'evaluated')), best=int(field(l, 'best')),
                                    host=int(field(l, 'host')), settled=int(field(l, 'settled')),
                                    active=int(field(l, 'active')), **{c: int(field(l, c)) for c in COUNTERS}))
            m = re.search(r'phase=([ABC]) START', l)
            if m and 'mix-mixFYF' in l: marks[m[1]] = kt
            if 'mix-mixFYF' in l and ' END' in l and (m := re.search(r'phase=([ABC]) END', l)): marks[m[1] + '_end'] = kt
    r['samples'], r['marks'] = samples, marks
    return r


def wseries(ser, span=300):
    """trailing-span windowed WAF: list of (t, w)."""
    out = []
    for i, (t, h, g) in enumerate(ser):
        j = i
        while j > 0 and t - ser[j - 1][0] <= span: j -= 1
        if j < i and t - ser[j][0] >= span - 31 and h - ser[j][1] > 0:
            out.append((t, 1 + (g - ser[j][2]) / (h - ser[j][1])))
    return out


def interval_waf(ser, a, b):
    pa = min(ser, key=lambda x: abs(x[0] - a)); pb = min(ser, key=lambda x: abs(x[0] - b))
    return 1 + (pb[2] - pa[2]) / (pb[1] - pa[1]) if pb[1] > pa[1] else None


def recovery(w, T, E, ok):
    """first t>=T+300 where ok(w) holds for all samples in [t, t+180] and t < E-600."""
    pts = [(t, x) for t, x in w if T + 300 <= t <= E]
    for i, (t, _) in enumerate(pts):
        if t >= E - 600: break
        win = [x for tt, x in pts[i:] if tt <= t + 180]
        if len(win) >= 6 and all(ok(x) for x in win):
            return t - T
    return None


def counters_at(samples, kt):
    """sum over partitions of the latest cumulative counters at kernel time kt."""
    tot = {c: 0 for c in COUNTERS + ['window']}
    for p in range(4):
        last = [s for s in samples if s['part'] == p and s['kt'] <= kt]
        if last:
            for c in tot: tot[c] += last[-1][c]
    return tot


def mstat(xs):
    xs = [x for x in xs if x is not None]
    if not xs: return (None, None, None, 0)
    m = st.mean(xs)
    if len(xs) < 2: return (m, None, None, 1)
    sd = st.stdev(xs); h = T95[len(xs) - 1] * sd / math.sqrt(len(xs))
    return (m, sd, h, len(xs))


def fmt(x, n=4):
    return '' if x is None else (f'{x:.{n}f}' if isinstance(x, float) else str(x))


def main():
    runs = [load(d) for d in sorted(RAW.glob('mixFYF-*-rep[0-9]')) if d.is_dir()]
    ok = [r for r in runs if r['exit'] == 0 and r['waf']]
    ref = next((r for r in ok if r['policy'] == 'arm47'), None)
    ref_phase = {}
    if ref:
        for ph in 'BC':
            E = ref[f't_{ph}1']; ref_phase[ph] = interval_waf(ref['series'], E - 600, E)
    rows = []
    for r in ok:
        w = wseries(r['series'])
        row = dict(run=Path(r['dir']).name, policy=r['policy'], rep=r['rep'], waf_total=r['waf'],
                   waf_FIO1=r['waf_A'], waf_YCSBA=r['waf_B'], waf_FIO2=r['waf_C'])
        for ph, name in (('B', 'T1_FIO_to_YCSBA'), ('C', 'T2_YCSBA_to_FIO')):
            T, E = r[f't_{ph}0'], r[f't_{ph}1']
            rs = interval_waf(r['series'], E - 600, E)
            row[f'{name}_at'] = datetime.datetime.fromtimestamp(T).isoformat()
            row[f'{name}_at_s'] = round(T - r['t_A0'])
            row[f'{name}_ref_self_waf'] = rs
            sec = recovery(w, T, E, lambda x: abs(x / rs - 1) <= 0.05) if rs else None
            row[f'{name}_recovery_self_s'] = sec if sec is not None else 'not_recovered'
            if ph in ref_phase and ref_phase[ph]:
                lim = 1.05 * ref_phase[ph]
                sec = recovery(w, T, E, lambda x: x <= lim)
                row[f'{name}_recovery_ref47_s'] = sec if sec is not None else 'not_recovered'
                row[f'{name}_ref47_waf'] = ref_phase[ph]
        if r['samples']:
            mk = r['marks']
            fin = counters_at(r['samples'], 1e18)
            row.update(valid_windows=fin['window'], discarded_windows=fin['discarded'], selections=fin['select'],
                       evaluations_nonincumbent=fin['eval_explore'], eliminations=fin['elim'],
                       policy_updates=fin['best_change'], drift_resets=fin['reset'],
                       learner_cpu_ms=fin['learner_ns'] / 1e6)
            # exploratory windows: the logged best is after the update, so use eval_explore increments per sample.
            prev = {}; xh = 0; allh = 0
            for s in r['samples']:
                inc = s['eval_explore'] - prev.get(s['part'], 0); prev[s['part']] = s['eval_explore']
                allh += s['host']; xh += s['host'] if inc > 0 else 0
            row['explore_host_pages'] = xh; row['window_host_pages'] = allh
            row['explore_share_windows'] = fin['eval_explore'] / fin['window'] if fin['window'] else None
            for ph in 'ABC':
                a = counters_at(r['samples'], mk.get(ph, 0)); b = counters_at(r['samples'], mk.get(ph + '_end', 1e18))
                for c, nm in (('window', 'windows'), ('select', 'selections'), ('eval_explore', 'evaluations'),
                              ('elim', 'eliminations'), ('best_change', 'policy_updates'), ('reset', 'resets')):
                    row[f'{ph}_{nm}'] = b[c] - a[c]
                row[f'{ph}_learner_cpu_ms'] = (b['learner_ns'] - a['learner_ns']) / 1e6
            # first drift reset after each transition (detection latency, kernel clock)
            for ph in 'BC':
                T = mk.get(ph)
                first = None
                if T:
                    cur = {}
                    for s in r['samples']:
                        if s['kt'] < T: cur[s['part']] = s['reset']; continue
                        if s['reset'] > cur.get(s['part'], 0): first = s['kt']; break
                row[f'{ph}_first_reset_after_transition_s'] = round(first - T, 1) if first else 'none'
        rows.append((r, w, row))
    write_tables(rows, runs)
    figures(rows)
    manifest(runs, rows)
    resource(runs, rows)


def write_csv(name, header, data):
    p = OUT / name
    with p.open('w', newline='') as f:
        wr = csv.writer(f); wr.writerow(header); [wr.writerow([fmt(x) for x in d]) for d in data]


def agg_rows(rows, pols, key):
    out = []
    for p in pols:
        xs = [row[key] for r, w, row in rows if row['policy'] == p and isinstance(row.get(key), (int, float))]
        m, sd, h, n = mstat(xs)
        out.append((p, key, n, m, sd, (m - h) if h is not None else None, (m + h) if h is not None else None, ';'.join(fmt(x) for x in xs)))
    return out


ENVTAG = None


def env_cols():
    return [ENVTAG['host'], ENVTAG['cpu'], ENVTAG['kernel'], ENVTAG['git_commit']]


def write_tables(rows, runs):
    global ENVTAG
    ENVTAG = env_info()
    E = ['host', 'cpu', 'kernel', 'git_commit']
    AH = ['policy', 'metric', 'n', 'mean', 'sd', 'ci95_lo', 'ci95_hi', 'values'] + E
    met = ['waf_total', 'waf_FIO1', 'waf_YCSBA', 'waf_FIO2']
    # random vs icat
    data = [a + tuple(env_cols()) for k in met + ['selections', 'evaluations_nonincumbent', 'valid_windows']
            for a in agg_rows(rows, ['revA-random', 'revA-v4'], k)]
    rv = [row for r, w, row in rows if row['policy'] in ('revA-random', 'revA-v4')]
    write_csv('random_vs_icat.csv', AH, data)
    write_csv('random_vs_icat_runs.csv', ['run', 'policy', 'rep', 'icat_seed', 'fio_seeds', 'waf_total', 'waf_FIO1', 'waf_YCSBA', 'waf_FIO2', 'selections', 'valid_windows'] + E,
              [(x['run'], x['policy'], x['rep'], 2026111400 + x['rep'], f"{20260910+x['rep']}/{20261010+x['rep']}/{20261110+x['rep']}", x['waf_total'], x['waf_FIO1'], x['waf_YCSBA'], x['waf_FIO2'], x.get('selections'), x.get('valid_windows')) + tuple(env_cols()) for x in rv])
    # ablation
    data = [a + tuple(env_cols()) for k in met + ['valid_windows', 'selections', 'evaluations_nonincumbent', 'eliminations', 'policy_updates', 'drift_resets', 'learner_cpu_ms']
            for a in agg_rows(rows, ['revA-v1', 'revA-v2', 'revA-v4'], k)]
    write_csv('ablation_v1_v2_v4.csv', AH, data)
    # per-run tables
    allr = [row for r, w, row in rows]
    tk = ['run', 'policy', 'rep', 'T1_FIO_to_YCSBA_at', 'T1_FIO_to_YCSBA_at_s', 'T2_YCSBA_to_FIO_at', 'T2_YCSBA_to_FIO_at_s',
          'waf_FIO1', 'waf_YCSBA', 'waf_FIO2', 'waf_total'] + [f'{p}_{n}' for p in 'ABC' for n in ('windows', 'selections', 'evaluations', 'eliminations', 'policy_updates', 'resets')] + \
         ['B_first_reset_after_transition_s', 'C_first_reset_after_transition_s']
    write_csv('workload_transition.csv', tk + E, [tuple(x.get(k) for k in tk) + tuple(env_cols()) for x in allr])
    ek = ['run', 'policy', 'rep', 'valid_windows', 'discarded_windows', 'selections', 'evaluations_nonincumbent', 'eliminations', 'policy_updates', 'drift_resets',
          'learner_cpu_ms', 'A_learner_cpu_ms', 'B_learner_cpu_ms', 'C_learner_cpu_ms', 'explore_share_windows', 'explore_host_pages', 'window_host_pages']
    write_csv('exploration_cost.csv', ek + E, [tuple(x.get(k) for k in ek) + tuple(env_cols()) for x in allr if x['policy'] != 'arm47'])
    rk = ['run', 'policy', 'rep', 'T1_FIO_to_YCSBA_at_s', 'T1_FIO_to_YCSBA_ref_self_waf', 'T1_FIO_to_YCSBA_recovery_self_s', 'T1_FIO_to_YCSBA_ref47_waf', 'T1_FIO_to_YCSBA_recovery_ref47_s',
          'T2_YCSBA_to_FIO_at_s', 'T2_YCSBA_to_FIO_ref_self_waf', 'T2_YCSBA_to_FIO_recovery_self_s', 'T2_YCSBA_to_FIO_ref47_waf', 'T2_YCSBA_to_FIO_recovery_ref47_s']
    write_csv('waf_recovery.csv', rk + E, [tuple(x.get(k) for k in rk) + tuple(env_cols()) for x in allr])
    # failed / incomplete runs
    write_csv('runs_status.csv', ['run', 'exit', 'waf'], [(Path(r['dir']).name, r['exit'], r['waf']) for r in runs])


COL = {'revA-v4': '#2a78d6', 'revA-random': '#eb6834', 'revA-v1': '#1baf7a', 'revA-v2': '#eda100', 'arm47': '#52514e'}


def figures(rows):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False, 'axes.edgecolor': '#8a8984',
                         'axes.labelcolor': '#0b0b0b', 'xtick.color': '#52514e', 'ytick.color': '#52514e', 'axes.grid': True,
                         'grid.color': '#e6e5e0', 'grid.linewidth': 0.6, 'figure.facecolor': '#fcfcfb', 'axes.facecolor': '#fcfcfb'})
    phases = [('waf_total', 'Total'), ('waf_FIO1', 'FIO-Fast 1'), ('waf_YCSBA', 'YCSB-A'), ('waf_FIO2', 'FIO-Fast 2')]

    def bars(ax, pols, title):
        n = len(pols); bw = 0.8 / n
        for i, p in enumerate(pols):
            for j, (k, _) in enumerate(phases):
                xs = [row[k] for r, w, row in rows if row['policy'] == p and row.get(k)]
                if not xs: continue
                m, sd, h, cnt = mstat(xs); x = j + (i - (n - 1) / 2) * bw
                ax.bar(x, m, bw * 0.92, color=COL[p], label=LAB[p] if j == 0 else None, zorder=2)
                if h: ax.errorbar(x, m, yerr=h, color='#0b0b0b', capsize=2, lw=0.9, zorder=3)
                ax.scatter([x] * len(xs), xs, s=9, color='#0b0b0b', zorder=4, linewidths=0)
                ax.text(x, m + (h or 0) + 0.03, f'{m:.3f}', ha='center', va='bottom', fontsize=6.5, color='#52514e', rotation=90)
        ax.set_xticks(range(len(phases)), [l for _, l in phases]); ax.set_ylabel('WAF (lower is better)')
        ax.set_ylim(1, None); ax.set_title(title, loc='left', fontsize=10); ax.legend(frameon=False, fontsize=8, loc='upper left')
        ax.grid(axis='x', visible=False)

    note = 'bars = mean, whisker = 95% CI (t), dots = individual reps'
    fig, ax = plt.subplots(figsize=(7, 4)); bars(ax, ['revA-v4', 'revA-random'], 'Figure 7. Random selection vs iCAT V4 (FIO-Fast → YCSB-A → FIO-Fast, 3×30 min)')
    fig.text(0.01, 0.01, note, fontsize=7, color='#52514e'); fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(OUT / 'figure7_random_comparison.png', dpi=200); plt.close(fig)
    fig, ax = plt.subplots(figsize=(7.5, 4)); bars(ax, ['revA-v1', 'revA-v2', 'revA-v4'], 'Figure 8. Ablation: V1 / V2 / V4')
    fig.text(0.01, 0.01, note + '. V1 = no drift detection/re-exploration; V2 = no elimination/settling', fontsize=7, color='#52514e')
    fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(OUT / 'figure8_ablation.png', dpi=200); plt.close(fig)
    # fig 9: windowed WAF over time since measurement start, mean over reps
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for p in POL:
        curves = []
        for r, w, row in rows:
            if row['policy'] != p or not w: continue
            t0 = r['t_A0']; curves.append({round((t - t0) / 60, 1): x for t, x in w})
        if not curves: continue
        import numpy as np   # runs sample on different clocks: interpolate each onto a common 30 s grid, mean where all reps cover
        lo = max(min(c) for c in curves); hi = min(max(c) for c in curves)
        grid = list(np.arange(math.ceil(lo * 2) / 2, hi, 0.5))
        ys = [st.mean(float(np.interp(g, sorted(c), [c[k] for k in sorted(c)])) for c in curves) for g in grid]
        ax.plot(grid, ys, color=COL[p], lw=2 if p != 'arm47' else 1.4, ls='-' if p != 'arm47' else '--', label=f'{LAB[p]} (n={len(curves)})')
    for xv, lab in ((30, 'FIO → YCSB-A'), (60, 'YCSB-A → FIO')):
        ax.axvline(xv, color='#8a8984', lw=0.9, ls=':'); ax.text(xv + 0.5, ax.get_ylim()[1], lab, fontsize=7, color='#52514e', va='top')
    ax.set_xlabel('minutes since measurement start (transitions nominal at 30 / 60 min)'); ax.set_ylabel('WAF, trailing 5-min window')
    ax.set_title('Figure 9. Adaptation across workload transitions (mean of reps)', loc='left', fontsize=10)
    ax.legend(frameon=False, fontsize=7.5, ncol=2, loc='upper left'); ax.grid(axis='x', visible=False)
    fig.tight_layout(); fig.savefig(OUT / 'figure9_adaptation.png', dpi=200); plt.close(fig)


def env_info():
    sh = lambda c: subprocess.run(c, shell=True, capture_output=True, text=True).stdout.strip()
    return dict(host=sh('hostname'), cpu=sh("LANG=C lscpu | sed -n 's/^Model name: *//p'"), kernel=sh('uname -r'),
                git_commit=sh('git -C /home/oy/iCAT rev-parse HEAD'))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest() if Path(p).exists() else None


def manifest(runs, rows):
    sh = lambda c: subprocess.run(c, shell=True, capture_output=True, text=True).stdout.strip()
    m = dict(campaign='revA-20261114', generated=datetime.datetime.now().astimezone().isoformat(),
             environment=dict(**env_info(), cpu_cores=sh('nproc'), ram_bytes=sh("LANG=C free -b | awk '/Mem:/{print $2}'"),
                              os=sh('. /etc/os-release; echo $PRETTY_NAME'), cmdline=sh('cat /proc/cmdline'),
                              physical_ssd=sh("lsblk -d -n -o MODEL,SIZE /dev/nvme0n1"), virtual_ssd='NVMeVirt CSL_Virt 7.5 GiB, memmap 8G@4G, SAMSUNG_970PRO base, 4 FTL partitions, cpus=1,2',
                              nvmevirt_upstream=sh('git -C /home/oy/nvmevirt rev-parse HEAD'), nvmevirt_fork_source='revA-src (online-v4-src + revA instrumentation)',
                              git_worktree_dirty=bool(sh('git -C /home/oy/iCAT status --porcelain')),
                              tools=dict(fio=sh('fio --version'), java=sh('java -version 2>&1 | head -1'), sqlite=sh('sqlite3 --version').split()[0])),
             config=dict(workload='FIO-Fast(test4) 1800 s -> YCSB-A sqlite 250k records (load+run) 1800 s -> FIO-Fast 1800 s',
                         prep='ext4 nodiscard, 6 GiB sequential preset + 3 GiB randwrite seed 20260907, explicit start/stop',
                         fio_seeds='hot/warm/cold = 20260910+rep / 20261010+rep / 20261110+rep',
                         icat_seed='2026111400+rep (used only by revA-random; xorshift64* per partition seeded by splitmix(seed ^ (part+1)*phi))',
                         variants={'revA-v4': 'full iCAT-v4', 'revA-v1': 'no drift detection / re-exploration', 'revA-v2': 'no elimination, no settling (UCB throughout; drift check inactive because it requires settling)',
                                   'revA-random': 'uniform random over 45 arms each window', 'arm47': 'fixed CAT k10/25%/r16 reference'},
                         name_warning='revA-v1/revA-v2 are NOT the paper iCAT-v1 (original) / iCAT-v2 (3x window)'),
             files=dict(runner=sha(C / 'runner-revA.sh'), safety_env=sha(C / 'safety-env.sh'), source_diff=sha(C / 'inputs/revA-vs-online-v4.diff'),
                        modules={l.split()[1]: l.split()[0] for l in (C / 'modules.sha256').read_text().splitlines()}),
             run_order=(C / 'runs.tsv').read_text().splitlines() if (C / 'runs.tsv').exists() else [],
             runs=[dict(run=Path(r['dir']).name, policy=r['policy'], rep=r['rep'], exit=r['exit'], waf=r['waf']) for r in runs],
             outputs=sorted(p.name for p in OUT.iterdir()))
    (OUT / 'experiment_manifest.json').write_text(json.dumps(m, indent=1, ensure_ascii=False))



# ---------------- resource overhead (added 2026-11-14, second request) ----------------
FIO_EXPECTED_IOS = (58982400000 + 29491200000 + 9830400000) * 3 // 4096   # per FIO-Fast phase (1800 s payload)
ORDER = ['arm47', 'revA-v1', 'revA-v2', 'revA-random', 'revA-v4']


def validate(r):
    """workload/device validity checks for one run dir -> dict."""
    import gzip
    d = Path(r['dir']); v = dict(run=d.name, policy=r['policy'], rep=r['rep'], runner_exit=r['exit'])
    for ph in 'AC':
        j = d / f'phase-{ph}.json'
        if j.exists():
            jj = json.loads(j.read_text())
            v[f'fio_{ph}_errors'] = sum(x['error'] for x in jj['jobs'])
            v[f'fio_{ph}_ios_done'] = sum(x['write']['total_ios'] for x in jj['jobs'])
        else:
            v[f'fio_{ph}_errors'] = v[f'fio_{ph}_ios_done'] = None
        v[f'fio_{ph}_ios_expected'] = FIO_EXPECTED_IOS
    txt = ''
    for f in sorted(d.glob('ycsb-run-B.txt*')):
        txt = (gzip.open(f, 'rt', errors='replace') if f.suffix == '.gz' else f.open(errors='replace')).read()
    ok = {k: int(n) for k, n in re.findall(r'^\[(READ|UPDATE)\], Return=OK, (\d+)', txt, re.M)}
    er = {k: int(n) for k, n in re.findall(r'^\[(READ|UPDATE)\], Return=ERROR, (\d+)', txt, re.M)}
    v.update(ycsb_read_ok=ok.get('READ'), ycsb_update_ok=ok.get('UPDATE'), ycsb_errors=sum(er.values()),
             sqlite_full=txt.count('SQLITE_FULL'), ycsb_expected='time-bounded (no fixed op count)')
    kl = (d / 'kernel.log').read_text(errors='replace') if (d / 'kernel.log').exists() else ''
    v['kernel_error_lines'] = len(re.findall(r'(?im)^.*(nvmev|nvmevirt).*(error|fail|bug|warn|assert).*$', kl))
    v['valid'] = bool(r['exit'] == 0 and r['waf'] and v['ycsb_errors'] == 0 and v['sqlite_full'] == 0
                      and v['fio_A_errors'] == 0 and v['fio_C_errors'] == 0 and v['kernel_error_lines'] == 0
                      and v['fio_A_ios_done'] == FIO_EXPECTED_IOS and v['fio_C_ios_done'] == FIO_EXPECTED_IOS)
    v['reason'] = '' if v['valid'] else ';'.join(k for k, bad in [
        ('runner_exit', r['exit'] != 0), ('ycsb_errors', v['ycsb_errors']), ('sqlite_full', v['sqlite_full']),
        ('fio_errors', (v['fio_A_errors'] or 0) + (v['fio_C_errors'] or 0)), ('kernel_errors', v['kernel_error_lines']),
        ('fio_ios_mismatch', v['fio_A_ios_done'] != FIO_EXPECTED_IOS or v['fio_C_ios_done'] != FIO_EXPECTED_IOS)] if bad)
    return v


def per_call(samples, lo=-1.0, hi=1e18):
    """per learner call ns = delta of cumulative learner_ns between consecutive samples of a partition."""
    prev, out = {}, []
    for s in samples:
        p = s['part']
        if p in prev and lo <= s['kt'] < hi: out.append(s['learner_ns'] - prev[p])
        elif p not in prev and lo <= s['kt'] < hi: out.append(s['learner_ns'])   # first call of the partition
        prev[p] = s['learner_ns']
    return out


def msd(xs):
    xs = [x for x in xs if isinstance(x, (int, float))]
    return (st.mean(xs) if xs else None, st.stdev(xs) if len(xs) > 1 else None, len(xs))


def resource(runs, rows):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    R = OUT / 'resource'; R.mkdir(exist_ok=True)
    E = ['host', 'cpu', 'kernel', 'git_commit']
    val = [validate(r) for r in runs]
    vk = list(val[0].keys()) if val else []
    write_csv('resource/runs_status.csv', vk + E, [tuple(v[k] for k in vk) + tuple(env_cols()) for v in val])
    good = {v['run'] for v in val if v['valid']}
    static = {l.split('\t')[0].replace('nvmev-', '').replace('.ko', ''): l.split('\t')
              for l in (C / 'inputs/module_static_sizes.tsv').read_text().splitlines()[1:]}
    # data structure sizes
    ds = []
    for p in ORDER:
        t = static[p]; tun, arm, parts = int(t[5]), int(t[6]), int(t[9])
        used = 0 if p == 'arm47' else tun * parts
        ds.append((p, t[1], int(t[2]), int(t[3]), int(t[4]), int(t[2]) + int(t[3]) + int(t[4]), tun, arm, 60, arm * 60, parts,
                   tun * parts, used, 'tuner struct is embedded in every build (CAT build uses only its 128 B param cache); learner logic differs only by code paths'))
    write_csv('resource/data_structure_sizes.csv', ['policy', 'module_sha256', 'text_B', 'data_B', 'bss_B', 'module_static_total_B',
              'sizeof_tuner_per_partition_B', 'sizeof_arm_stat_B', 'arm_slots', 'arm_table_B', 'partitions', 'tuner_allocated_total_B',
              'learner_state_in_use_B', 'note'] + E, [d + tuple(env_cols()) for d in ds])
    # cpu per run
    cpu = []
    for r, w, row in rows:
        if row['run'] not in good: continue
        dur = (r['t_C1'] - r['t_A0']) * 1e9
        mk = r['marks']
        allc = per_call(r['samples'], mk.get('A', -1), mk.get('C_end', 1e18))   # measured interval only (prep excluded), like SmartGC stats
        prepc = per_call(r['samples'], -1, mk.get('A', -1))
        ac = per_call(r['samples'], mk.get('A', -1), mk.get('A_end', 1e18))
        tot = sum(allc)
        cpu.append(dict(run=row['run'], policy=row['policy'], rep=row['rep'], learner_calls=len(allc), learner_total_ms=tot / 1e6,
                        learner_mean_us=(tot / len(allc) / 1e3) if allc else None, learner_max_us=(max(allc) / 1e3) if allc else None,
                        learner_p99_us=(sorted(allc)[int(0.99 * (len(allc) - 1))] / 1e3) if allc else None,
                        fio1_calls=len(ac), fio1_total_ms=sum(ac) / 1e6, measured_wall_s=dur / 1e9,
                        prep_calls=len(prepc), prep_total_ms=sum(prepc) / 1e6,
                        learner_share_of_wall_pct=100 * tot / dur if dur else None,
                        waf_total=row['waf_total'], waf_FIO1=row['waf_FIO1'], waf_YCSBA=row['waf_YCSBA'], waf_FIO2=row['waf_FIO2']))
    ck = ['run', 'policy', 'rep', 'learner_calls', 'learner_total_ms', 'learner_mean_us', 'learner_max_us', 'learner_p99_us',
          'fio1_calls', 'fio1_total_ms', 'prep_calls', 'prep_total_ms', 'measured_wall_s', 'learner_share_of_wall_pct', 'waf_total', 'waf_FIO1', 'waf_YCSBA', 'waf_FIO2']
    write_csv('resource/cpu_measurements.csv', ck + E, [tuple(c[k] for k in ck) + tuple(env_cols()) for c in cpu])
    # memory per run (system-wide; cannot resolve KB-level policy differences)
    mem = []
    ms = []
    mf = C / 'memsampler.tsv'
    if mf.exists():
        ms = [l.split('\t') for l in mf.read_text().splitlines()[1:]]
    for r, w, row in rows:
        if row['run'] not in good: continue
        ser = [l for l in (Path(r['dir']) / 'control-series.txt').read_text().splitlines() if 'memavail_mb=' in l]
        av = [int(field(l, 'memavail_mb')) for l in ser]
        t0, t1 = r['t_A0'], r['t_C1']
        inrun = [x for x in ms if t0 <= int(x[0]) <= t1 and x[1] == '1']
        mem.append(dict(run=row['run'], policy=row['policy'], rep=row['rep'],
                        memavail_first_mb=av[0] if av else None, memavail_last_mb=av[-1] if av else None,
                        memavail_min_mb=min(av) if av else None, module_coresize_B=inrun[0][2] if inrun else 'not_sampled',
                        slab_max_kB=max(int(x[4]) for x in inrun) if inrun else 'not_sampled',
                        vmalloc_max_kB=max(int(x[6]) for x in inrun) if inrun else 'not_sampled',
                        RSS='N/A (learner runs in kernel threads; RSS=0)', VmHWM='N/A (kernel thread)'))
    mk_ = list(mem[0].keys()) if mem else ['run']
    write_csv('resource/memory_measurements.csv', mk_ + E, [tuple(m[k] for k in mk_) + tuple(env_cols()) for m in mem])
    # summary per policy
    summ = []
    for p in ORDER:
        cs = [c for c in cpu if c['policy'] == p]; t = static[p]
        row = [p, len(cs), len([v for v in val if v['policy'] == p and not v['valid']])]
        for k in ['waf_total', 'waf_FIO1', 'learner_calls', 'learner_total_ms', 'learner_mean_us', 'learner_max_us', 'learner_share_of_wall_pct']:
            m, sd, n = msd([c[k] for c in cs]); row += [m, sd]
        row += [int(t[2]) + int(t[3]) + int(t[4]), 0 if p == 'arm47' else int(t[5]) * int(t[9])]
        summ.append(row)
    hk = ['policy', 'n_valid', 'n_failed'] + [f'{k}_{s}' for k in ['waf_total', 'waf_FIO1', 'learner_calls', 'learner_total_ms', 'learner_mean_us', 'learner_max_us', 'learner_share_of_wall_pct'] for s in ('mean', 'sd')] + ['module_static_B', 'learner_state_in_use_B']
    write_csv('resource/resource_summary.csv', hk + E, [tuple(r_) + tuple(env_cols()) for r_ in summ])
    # figures
    names = {'arm47': 'CAT-47 (fixed)', 'revA-v1': 'V1', 'revA-v2': 'V2', 'revA-random': 'Random', 'revA-v4': 'V4'}
    cols = {'arm47': '#52514e', 'revA-v1': '#1baf7a', 'revA-v2': '#eda100', 'revA-random': '#eb6834', 'revA-v4': '#2a78d6'}

    def barfig(fname, title, ylabel, vals, note):
        fig, ax = plt.subplots(figsize=(7, 3.8))
        for i, (p, m, sd, n, pts) in enumerate(vals):
            if m is None: continue
            ax.bar(i, m, 0.6, color=cols[p], zorder=2)
            if sd: ax.errorbar(i, m, yerr=sd, color='#0b0b0b', capsize=3, lw=0.9, zorder=3)
            if pts: ax.scatter([i] * len(pts), pts, s=10, color='#0b0b0b', zorder=4, linewidths=0)
            ax.text(i, m + (sd or 0), f'{m:,.3g}' if m < 1000 else f'{m:,.0f}', ha='center', va='bottom', fontsize=8, color='#52514e')
        ax.set_xticks(range(len(vals)), [f'{names[p]}\nn={n}' for p, *_ , n, _ in [(v[0], v[1], v[2], v[3], v[4]) for v in vals]])
        ax.set_ylabel(ylabel); ax.set_title(title, loc='left', fontsize=10); ax.grid(axis='x', visible=False)
        fig.text(0.01, 0.01, note, fontsize=7, color='#52514e'); fig.tight_layout(rect=(0, 0.04, 1, 1)); fig.savefig(R / fname, dpi=200); plt.close(fig)

    nvalid = {p: len([c for c in cpu if c['policy'] == p]) for p in ORDER}
    barfig('figure7_memory.png', 'Figure 7. Learner state memory per policy (4 FTL partitions)', 'bytes',
           [(p, (0 if p == 'arm47' else int(static[p][5]) * 4), None, nvalid[p], None) for p in ORDER],
           'sizeof(struct watgc_v2_tuner) x 4 from module DWARF; static, identical across runs. RSS/VmHWM not applicable (kernel threads).')
    barfig('figure8_learner_cpu.png', 'Figure 8. Cumulative learner-code time per run', 'ms (ktime inside observe+set_arm)',
           [(p, *msd([c['learner_total_ms'] for c in cpu if c['policy'] == p])[:2], nvalid[p], [c['learner_total_ms'] for c in cpu if c['policy'] == p]) for p in ORDER],
           'Not process CPU usage: wall ns inside the learner code path on the NVMeVirt dispatcher thread. Bars = mean, whisker = SD, dots = runs.')
    barfig('figure9_waf.png', 'Figure 9. WAF per policy (FIO-Fast → YCSB-A → FIO-Fast, 3×30 min)', 'WAF (lower is better)',
           [(p, *msd([c['waf_total'] for c in cpu if c['policy'] == p])[:2], nvalid[p], [c['waf_total'] for c in cpu if c['policy'] == p]) for p in ORDER],
           'Bars = mean, whisker = SD, dots = runs. CAT-47 is a single reference run.')


if __name__ == '__main__':
    main()
