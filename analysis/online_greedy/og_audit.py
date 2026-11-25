#!/usr/bin/env python3
"""GoCom independent audit for the Online Greedy comparison (M3). Read-only on every raw directory. No new experiment.
    python3 -I analysis/online_greedy/og_audit.py  GROUP=HOST:BATCH:REGISTERED_SHA_FILE:GLOB  [GROUP=... ...]
  e.g. revA-random=고컴:revA-20261114:result/revA-20261114/modules.sha256:result/revA-20261114/raw/mixFYF-revA-random-rep[0-9]
Each group is one policy in one batch on one host. Statistics only for groups with 3 valid runs. Contrasts are computed only
between groups of the same host AND the same batch ("direct"); same host / different batch is "indirect (batch)"; different host is
never differenced (only each policy's own-host V4 delta is shown side by side).
Outputs: result/online-greedy-analysis/{runs.csv, arms.csv, stats.csv, contrasts.csv} and report/online-greedy-audit-data.md."""
import collections, csv, gzip, json, math, os, re, statistics as st, sys
from pathlib import Path
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'analysis/final_e1'))
import validity as V
OUT = ROOT / os.environ.get('OG_OUT', 'result/online-greedy-analysis'); OUT.mkdir(parents=True, exist_ok=True)   # OG_OUT / OG_REPORT: alternate outputs (M4 table)
WORK = {'b5edbcc77f269f500986eae375da8a94d4bf762d30f52a58d8ffd0d4901fa946': 'mix-test4.fio',
        'c0aff8a25402e3f8178b47db2cf0575ce9cacba4eeb4c4657e84cf748db8d92d': 'workloada'}
SAMPLE = re.compile(r'WATGC_V2 sample ns=\d+ part=(\d) .*?window=(\d+) .*?evaluated=(\d+) .*?host=(\d+) gc_pages=(\d+) .*?best=(\d+) next=(\d+)')
cnt = lambda t, k: int(re.search(rf'\b{k}=(\d+)', t)[1])
first = lambda p: p.read_text().splitlines()[0]

groups = []
for a in sys.argv[1:]:
    name, spec = a.split('=', 1); host, batch, reg, glob = spec.split(':', 3)
    groups.append((name, host, batch, Path(reg), sorted(p for p in Path('/').glob(glob.lstrip('/')) if p.is_dir()) if glob.startswith('/')
                   else sorted(p for p in ROOT.glob(glob) if p.is_dir())))

rows, arms = [], []
for name, host, batch, reg, dirs in groups:
    regs = {l.split()[0] for l in reg.read_text().splitlines() if l.strip()} if reg.exists() else set()
    for d in dirs:
        rep = int(re.search(r'rep(\d)', d.name)[1]); bad = []
        env = (d / 'environment.txt').read_text(errors='replace') if (d / 'environment.txt').exists() else ''
        el = env.splitlines()
        shas = dict(re.findall(r'^([0-9a-f]{64})\s+(\S+)$', env, re.M))
        ko = [s for s, p in shas.items() if p.endswith('.ko')]
        r = dict(group=name, host=host, batch=batch, rep=rep, dir=str(d), raw_exists=(d / 'summary.txt').exists(),
                 exit=(d / 'exit-code.txt').read_text().strip() if (d / 'exit-code.txt').exists() else 'missing',
                 module_sha=ko[0] if ko else '', module_registered=bool(ko) and ko[0] in regs,
                 workload_ok=sorted(WORK[s] for s in shas if s in WORK) == ['mix-test4.fio', 'workloada'],
                 hostname=el[1].split()[1] if len(el) > 1 else '', kernel=el[1].split()[2] if len(el) > 1 else '',
                 boot=el[2] if len(el) > 2 else '', start=el[0] if el else '',
                 cpu=next((l.split(':', 1)[1].strip() for l in el if re.match(r'^(모델 이름|Model name)', l)), ''),
                 mem=next((l.split()[1] for l in el if re.match(r'^(메모리|Mem):', l)), ''))
        if r['exit'] != '0': bad.append('exit')
        if not r['module_registered']: bad.append('module not registered')
        if not r['workload_ok']: bad.append('workload hash')
        # seeds: FIO randseed in phase A/C json, icat_seed in the kernel init line of THIS run
        fs = sorted({int(x) for p in 'AC' if (d / f'phase-{p}.json').exists() for x in re.findall(r'"randseed"\s*:\s*"?(\d+)', (d / f'phase-{p}.json').read_text())})
        exp = [20260910 + rep, 20261010 + rep, 20261110 + rep]
        kl = (d / 'kernel.log').read_text(errors='replace') if (d / 'kernel.log').exists() else ''
        beg = [m.end() for m in re.finditer(r'mix-mixFYF-\S+ BEGIN', kl)]; own = kl[beg[-1]:] if beg else kl
        isd = sorted(set(re.findall(r'WATGC_V2 init .*?icat_seed=(\d+)', own)))
        r.update(fio_seeds=' '.join(map(str, fs)), fio_seeds_ok=fs == exp, icat_seed=' '.join(isd),
                 icat_seed_ok=isd == [str(2026111400 + rep)], fresh_init_parts=len(re.findall(r'WATGC_V2 init ', own)))
        if not r['fio_seeds_ok']: bad.append('fio seed')
        r['kernel_err'] = len(re.findall(r'BUG:|WARNING:|Oops|Call Trace', own))
        if r['kernel_err']: bad.append('kernel error')
        r['fio_err'] = sum(int(x) for p in 'AC' if (d / f'phase-{p}.json').exists() for x in re.findall(r'"error"\s*:\s*(\d+)', (d / f'phase-{p}.json').read_text()))
        if r['fio_err']: bad.append('fio error')
        yt = gzip.open(d / 'ycsb-run-B.txt.gz', 'rt', errors='replace').read() if (d / 'ycsb-run-B.txt.gz').exists() else ''
        ops = sum(int(x) for x in re.findall(r'^\[(?:READ|UPDATE)\], Operations, (\d+)', yt, re.M))
        ok = sum(int(x) for x in re.findall(r'^\[(?:READ|UPDATE)\], Return=OK, (\d+)', yt, re.M))
        sf = sum((gzip.open(f, 'rt', errors='replace').read() if f.suffix == '.gz' else f.read_text(errors='replace')).count('SQLITE_FULL') for f in d.glob('ycsb*'))
        r.update(ycsb_ops=ops, ycsb_ok=ok, ycsb_success=ok / ops if ops else 0, sqlite_full=sf, validity_gate=V.run_ok(d))
        if not ops or ok != ops or sf or not r['validity_gate']: bad.append('YCSB')
        # WAF from raw counters: summary total, partition sum, and phase start/end snapshots
        t = re.search(r'^total .*host_pages=(\d+) gc_pages=(\d+)', (d / 'summary.txt').read_text(), re.M)
        ps = re.findall(r'^part=\d host_pages=(\d+) gc_pages=(\d+)', (d / 'final-control.txt').read_text(), re.M)
        h, g = int(t[1]), int(t[2]); r['waf'] = 1 + g / h
        r['two_paths_equal'] = (h, g) == (sum(int(x) for x, _ in ps), sum(int(y) for _, y in ps))
        r['started_zero'] = cnt(first(d / 'started.txt'), 'host_pages') == 0 if (d / 'started.txt').exists() else None
        if not r['two_paths_equal']: bad.append('WAF paths')
        for p in 'ABC':
            s0, s1 = first(d / f'phase-{p}-start.txt'), first(d / f'phase-{p}-end.txt')
            r[f'waf_{p}'] = 1 + (cnt(s1, 'gc_pages') - cnt(s0, 'gc_pages')) / (cnt(s1, 'host_pages') - cnt(s0, 'host_pages'))
        # learner log: per-arm selections, policy changes, exploration cost (windows whose evaluated arm != best)
        # exploration cost, two definitions:
        #  (a) 'not-best' share: windows whose evaluated arm != the logged best= (NOT meaningful for greedy-online: there best= comes from
        #      the unchanged update_best with its 0.5 % tolerance, not from the greedy argmin -> reported as n/a for that policy)
        #  (b) initial coverage cost: per partition, windows up to and including the window in which the 45th distinct arm is first seen;
        #      host share and WAF of those windows. Same definition for every policy.
        ev = collections.Counter(); changes = 0; eh = eg = ah = 0; win = 0; seen = collections.defaultdict(set); cov = {}; ih = ig = 0
        for m in SAMPLE.finditer(own):
            part, w, e, hh, gg, b, nx = map(int, m.groups()); win += 1; ev[e] += 1; ah += hh
            if e != b: eh += hh; eg += gg
            if nx != e: changes += 1
            if part not in cov:
                seen[part].add(e); ih += hh; ig += gg
                if len(seen[part]) == 45: cov[part] = w
        greedy = 'greedy' in name and 'v4' not in name
        r.update(windows=win, distinct_arms=len(ev), policy_changes=changes,
                 explore_host_share='' if greedy else (eh / ah if ah else ''), explore_gc_pages='' if greedy else eg,
                 coverage_windows=' '.join(str(cov.get(p_, 'none')) for p_ in range(4)), init_host_share=ih / ah if ah else '',
                 init_waf=1 + ig / ih if ih else '')
        for a_, n_ in sorted(ev.items()): arms.append(dict(group=name, host=host, batch=batch, rep=rep, arm=a_, selections=n_))
        r['valid'] = not bad; r['reasons'] = '; '.join(bad)
        rows.append(r)

def w(name, rr):
    if not rr: return
    with open(OUT / name, 'w', newline='') as f:
        x = csv.DictWriter(f, list(dict.fromkeys(k for r in rr for k in r))); x.writeheader(); x.writerows(rr)
w('runs.csv', rows); w('arms.csv', arms)

def ci(v):
    m, s = st.mean(v), st.stdev(v); h = stats.t.ppf(.975, len(v) - 1) * s / math.sqrt(len(v)); return m, s, m - h, m + h

def welch(a, b):   # b - a
    va, vb = st.variance(a) / len(a), st.variance(b) / len(b); d = st.mean(b) - st.mean(a)
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1)); h = stats.t.ppf(.975, df) * math.sqrt(va + vb)
    sp = math.sqrt(((len(a) - 1) * st.variance(a) + (len(b) - 1) * st.variance(b)) / (len(a) + len(b) - 2))
    return d, d - h, d + h, df, d / sp * (1 - 3 / (4 * (len(a) + len(b)) - 9))

G = {g[0]: g for g in groups}
val = {g: [r for r in rows if r['group'] == g and r['valid']] for g in G}
srows, crows = [], []
for g, rr in val.items():
    for k in ('waf', 'waf_A', 'waf_B', 'waf_C', 'distinct_arms', 'policy_changes', 'explore_host_share', 'init_host_share', 'init_waf'):
        v = [r[k] for r in rr if r.get(k, '') != '']
        srows.append(dict(group=g, host=G[g][1], batch=G[g][2], metric=k, n_valid=len(v), values=' / '.join(f'{x:.4f}' for x in v),
                          **(dict(zip(('mean', 'sd', 'ci_lo', 'ci_hi'), ci(v))) if len(v) >= 3 else dict(mean='n<3: 통계 없음'))))
names = list(G)
for i, a in enumerate(names):
    for b in names[i + 1:]:
        ha, hb = G[a][1], G[b][1]
        kind = 'direct (same host, same batch)' if (ha, G[a][2]) == (hb, G[b][2]) else 'indirect (same host, different batch)' if ha == hb else None
        if kind is None: continue
        for k in ('waf', 'waf_C'):
            x, y = [r[k] for r in val[a]], [r[k] for r in val[b]]
            crows.append(dict(contrast=f'{b} - {a}', kind=kind, metric=k, **(dict(zip(('diff', 'ci_lo', 'ci_hi', 'welch_df', 'hedges_g'), welch(x, y)))
                                                                            if len(x) >= 3 and len(y) >= 3 else dict(diff='n<3: 통계 없음'))))
w('stats.csv', srows); w('contrasts.csv', crows)
L = ['# Online Greedy 비교: 기존 결과 독립 감사 데이터 (자동 생성)', '', '| 그룹 | 호스트 | 배치 | rep | 원시 | exit | 모듈 등록 | 부하 해시 | FIO seed | icat_seed | YCSB OK/전체 | SQLITE_FULL | 커널 오류 | WAF 두 경로 | 전체 WAF | A / B / C | 서로 다른 arm | 정책 변경 | 판정 |',
     '|' + '---|' * 19]
for r in rows:
    L.append(f"| {r['group']} | {r['host']} | {r['batch']} | {r['rep']} | {r['raw_exists']} | {r['exit']} | {r['module_registered']} | {r['workload_ok']} | {r['fio_seeds_ok']} | {r['icat_seed'] or '-'} | "
             f"{r['ycsb_ok']:,}/{r['ycsb_ops']:,} | {r['sqlite_full']} | {r['kernel_err']} | {r['two_paths_equal']} | {r['waf']:.4f} | {r['waf_A']:.3f} / {r['waf_B']:.3f} / {r['waf_C']:.3f} | "
             f"{r['distinct_arms']} | {r['policy_changes']} | {'유효' if r['valid'] else '무효: ' + r['reasons']} |")
L += ['', '| 그룹 | 지표 | 유효 n | 값 | 평균 ± SD [95 % CI] |', '|---|---|---|---|---|']
for s in srows:
    L.append(f"| {s['group']} | {s['metric']} | {s['n_valid']} | {s['values']} | " + (f"{s['mean']:.4f} ± {s['sd']:.4f} [{s['ci_lo']:.4f}, {s['ci_hi']:.4f}]" if s['n_valid'] >= 3 else s['mean']) + ' |')
L += ['', '| 대비 | 종류 | 지표 | Δ | Welch 95 % CI | df | Hedges g |', '|---|---|---|---|---|---|---|']
for c in crows:
    L.append(f"| {c['contrast']} | {c['kind']} | {c['metric']} | " + (f"{c['diff']:+.4f} | [{c['ci_lo']:+.4f}, {c['ci_hi']:+.4f}] | {c['welch_df']:.2f} | {c['hedges_g']:+.2f} |" if c.get('welch_df') else f"{c['diff']} | | | |"))
L += ['', '- 서로 다른 호스트 사이의 차이는 계산하지 않는다. Hedges g는 n=3 대 3에서 크기 참고용이다.']
(ROOT / 'report').mkdir(exist_ok=True); (ROOT / os.environ.get('OG_REPORT', 'report/online-greedy-audit-data.md')).write_text('\n'.join(L).replace('[-', '[−').replace(' -0.', ' −0.') + '\n'); print('\n'.join(L))
