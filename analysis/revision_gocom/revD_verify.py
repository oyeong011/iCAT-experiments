#!/usr/bin/env python3
"""GoCom independent verification of SeungCom E1 revD-20261124 (VERIFY-REQUEST.md items 1-5). Read-only on the revD files.
    python3 -I analysis/revision_gocom/revD_verify.py <revD campaign dir> <revD analysis dir> <recovery.py>
The revD files are an export of origin/main (git archive), not the run tree. Nothing here reuses e1_revd.py code:
validity, WAF, statistics and the recovery time are re-implemented from the definitions in revD preregistration.md.
Outputs: result/revD-20261124-verify/{verify_runs.csv, verify_contrasts.csv, verify.md} in the report worktree.
GoCom results are NOT merged into any of these numbers."""
import csv, gzip, math, re, statistics as st, sys
from datetime import datetime
from pathlib import Path
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'analysis/final_e1'))
import validity as V
CAMP, ANA, RECPY = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
OUT = ROOT / 'result/revD-20261124-verify'; OUT.mkdir(parents=True, exist_ok=True)
POL = ['revD-v4', 'revD-nodrift', 'revD-fullreset']
L = ['# 승컴 revD E1 고컴 독립 검증 (자동 생성)', '', f'- 대상: `{CAMP}` (origin/main 내보내기), 승컴 분석 `{ANA}`.',
     '- e1_revd.py 코드를 쓰지 않고 사전 등록 정의로 다시 구현했다. 고컴 결과는 섞지 않았다.', '']
cnt = lambda t, k: int(re.search(rf'\b{k}=(\d+)', t)[1])
first = lambda p: p.read_text().splitlines()[0]
iso = lambda s: datetime.fromisoformat(s.strip()).timestamp()

# ---- item 2: module hashes, run order ----
reg = {l.split()[1].split('/')[-1]: l.split()[0] for l in (CAMP / 'modules.sha256').read_text().splitlines() if l.strip()}
order_reg = [tuple(l.split()) for l in (CAMP / 'queue-order.registered.txt').read_text().splitlines() if l.strip()]
order_run = re.findall(r'\bstart (revD-\w+) rep(\d)', (CAMP / 'queue.log').read_text())
L += ['## 2. 모듈 해시와 실행 순서', f'- 사전 등록 순서 {len(order_reg)}개, queue.log 시작 기록 {len(order_run)}개, 일치: **{order_reg == order_run}**']

# ---- item 1 + 3: per-run validity and WAF ----
theirs = {(r['policy'], int(r['rep'])): r for r in csv.DictReader(open(ANA / 'runs.csv'))}
rows = []
for d in sorted((CAMP / 'raw').glob('mixFYF-revD-*-rep[0-9]')):
    pol, rep = re.match(r'mixFYF-(revD-\w+)-rep(\d)$', d.name).groups(); rep = int(rep)
    env = (d / 'environment.txt').read_text(errors='replace')
    ko = re.search(r'^([0-9a-f]{64})\s+\S*?([^/\s]+\.ko)$', env, re.M)
    r = dict(policy=pol, rep=rep, exit=(d / 'exit-code.txt').read_text().strip() if (d / 'exit-code.txt').exists() else 'missing',
             module_ok=bool(ko) and reg.get(ko[2]) == ko[1] and ko[2] == f'nvmev-{pol}.ko')
    bad = [] if r['exit'] == '0' else ['exit']
    for p in 'ABC':
        s, e = d / f'phase-{p}-start.txt', d / f'phase-{p}-end.txt'
        if not (s.exists() and e.exists()): bad.append(f'phase {p}'); continue
        h = cnt(first(e), 'host_pages') - cnt(first(s), 'host_pages'); g = cnt(first(e), 'gc_pages') - cnt(first(s), 'gc_pages')
        r[f'{p}_waf'] = 1 + g / h; r[f'{p}_host'] = h
    tot = re.search(r'^total .*host_pages=(\d+) gc_pages=(\d+)', (d / 'summary.txt').read_text(), re.M)
    ps = re.findall(r'^part=\d host_pages=(\d+) gc_pages=(\d+)', (d / 'final-control.txt').read_text(), re.M)
    h1, g1 = int(tot[1]), int(tot[2]); h2, g2 = sum(int(a) for a, _ in ps), sum(int(b) for _, b in ps)
    r['total_waf'] = 1 + g1 / h1; r['two_paths_equal'] = (h1, g1) == (h2, g2)
    if not r['two_paths_equal']: bad.append('WAF paths differ')
    kl = (d / 'kernel.log').read_text(errors='replace')
    beg = [m.start() for m in re.finditer(r'mix-mixFYF-' + re.escape(pol) + r'-\S* BEGIN', kl)]
    own = kl[beg[-1]:] if beg else kl
    r['kernel_err'] = len(re.findall(r'BUG:|WARNING:|Oops|Call Trace', own))
    if r['kernel_err']: bad.append('kernel error')
    yt = gzip.open(d / 'ycsb-run-B.txt.gz', 'rt', errors='replace').read() if (d / 'ycsb-run-B.txt.gz').exists() else ''
    ops = sum(int(x) for x in re.findall(r'^\[(?:READ|UPDATE)\], Operations, (\d+)', yt, re.M))
    okk = sum(int(x) for x in re.findall(r'^\[(?:READ|UPDATE)\], Return=OK, (\d+)', yt, re.M))
    notok = sum(int(x) for x in re.findall(r'^\[(?:READ|UPDATE)\], Return=(?!OK)\w+, (\d+)', yt, re.M))
    sf = sum((gzip.open(f, 'rt', errors='replace').read() if f.suffix == '.gz' else f.read_text(errors='replace')).count('SQLITE_FULL')
             for f in d.glob('ycsb*'))
    r.update(ycsb_ops=ops, ycsb_ok=okk, ycsb_notok=notok, sqlite_full=sf, gate_run_ok=V.run_ok(d))
    if not ops or okk != ops or notok or sf: bad.append('YCSB')
    if not r['gate_run_ok']: bad.append('validity.py')
    if not r['module_ok']: bad.append('module hash')
    # item 5: recovery, own implementation of the pre-registered definition (30 s samples, 5 min window, 10 min hold, 1.05)
    s = [tuple(int(x) for x in m.groups()) for l in (d / 'control-series.txt').read_text().splitlines()
         for m in [re.match(r'(\d+) .*host_pages=(\d+) gc_pages=(\d+)', l)] if m]
    t0, t1 = iso((d / 'phase-C-start.time').read_text()), iso((d / 'phase-C-end.time').read_text())
    pts = [x for x in s if t0 <= x[0] <= t1]
    w = lambda a, b: 1 + (b[2] - a[2]) / max(b[1] - a[1], 1)
    half = [x for x in pts if x[0] >= (t0 + t1) / 2]; ref = w(half[0], half[-1])
    roll = [(pts[i][0], w(pts[i - 10], pts[i])) for i in range(10, len(pts))]
    rec = next((roll[i][0] - t0 for i in range(len(roll)) if i + 20 < len(roll) and all(v <= ref * 1.05 for _, v in roll[i:i + 21])), None)
    r['C_recovery_s'] = rec
    t = theirs.get((pol, rep), {})
    r['their_valid'] = t.get('valid')
    for k in ('A_waf', 'B_waf', 'C_waf', 'total_waf', 'C_recovery_s'):
        a, b = r.get(k), t.get(k)
        r[f'match_{k}'] = (a is None and b in ('', None)) or (a is not None and b not in ('', None) and abs(a - float(b)) < 1e-9)
    r['valid'] = not bad; r['reasons'] = '; '.join(bad)
    rows.append(r)
with open(OUT / 'verify_runs.csv', 'w', newline='') as f:
    w_ = csv.DictWriter(f, list(dict.fromkeys(k for r in rows for k in r))); w_.writeheader(); w_.writerows(rows)
L += [f'- 모듈 해시 일치(정책 이름까지): {sum(r["module_ok"] for r in rows)}/{len(rows)}', '',
      '## 1·3·5. run 유효성, 단계별 WAF 재계산, 회복 시간 재계산',
      '| run | exit | 커널 오류 | YCSB OK/전체 (비OK, SQLITE_FULL) | validity.py | A / B / C / 전체 WAF | 승컴 값과 일치 (A,B,C,전체,회복) | 회복 s | 판정 |', '|---|---|---|---|---|---|---|---|---|']
for r in rows:
    m = ''.join('O' if r[f'match_{k}'] else 'X' for k in ('A_waf', 'B_waf', 'C_waf', 'total_waf', 'C_recovery_s'))
    L.append(f"| {r['policy']} rep{r['rep']} | {r['exit']} | {r['kernel_err']} | {r['ycsb_ok']:,}/{r['ycsb_ops']:,} ({r['ycsb_notok']}, {r['sqlite_full']}) | {r['gate_run_ok']} | "
             f"{r.get('A_waf', 0):.4f} / {r.get('B_waf', 0):.4f} / {r.get('C_waf', 0):.4f} / {r['total_waf']:.4f} | {m} | {r['C_recovery_s']} | {'유효' if r['valid'] else '무효: ' + r['reasons']} |")

# ---- item 4: contrasts ----
rc = RECPY.read_text()
L += ['', f"- recovery.py 상수: `{re.search(r'^TOL, ROLL, HOLD = .*$', rc, re.M)[0]}` (사전 등록: 1.05, 5분=10표본, 10분=20표본)"]
val = {p: {r['rep']: r for r in rows if r['policy'] == p and r['valid']} for p in POL}
th = {(r['contrast'], r['metric']): r for r in csv.DictReader(open(ANA / 'contrasts.csv'))}
cts = []
L += ['', '## 4. 주 대비 재계산 (Welch 95 % CI, Hedges g, 같은 rep 짝 비교는 참고)',
      '| 대비 | 지표 | Δ 평균 | Welch 95 % CI | df | Hedges g | 승컴 값과 일치 | 짝 Δ 95 % CI (참고, 사전 등록 외) |', '|---|---|---|---|---|---|---|---|']
for p in POL[1:]:
    for k in ('C_waf', 'total_waf'):
        a = [val['revD-v4'][i][k] for i in sorted(val['revD-v4'])]; b = [val[p][i][k] for i in sorted(val[p])]
        if len(a) < 3 or len(b) < 3: L.append(f'| {p} − v4 | {k} | n<3: 통계 없음 | | | | | |'); continue
        va, vb = st.variance(a) / 3, st.variance(b) / 3; d = st.mean(b) - st.mean(a)
        df = (va + vb) ** 2 / (va ** 2 / 2 + vb ** 2 / 2); h = stats.t.ppf(.975, df) * math.sqrt(va + vb)
        sp = math.sqrt((st.variance(a) + st.variance(b)) / 2); g = d / sp * (1 - 3 / (4 * 6 - 9))
        reps = sorted(set(val[p]) & set(val['revD-v4'])); dd = [val[p][i][k] - val['revD-v4'][i][k] for i in reps]
        ph = stats.t.ppf(.975, len(dd) - 1) * st.stdev(dd) / math.sqrt(len(dd))
        t = th.get((f'{p} - revD-v4', k), {})
        same = all(abs(x - float(t.get(c, 'nan'))) < 1e-9 for x, c in ((d, 'diff'), (d - h, 'ci_lo'), (d + h, 'ci_hi'), (df, 'welch_df'), (g, 'hedges_g')))
        cts.append(dict(contrast=f'{p} - revD-v4', metric=k, diff=d, ci_lo=d - h, ci_hi=d + h, df=df, hedges_g=g, matches_seungcom=same,
                        paired=st.mean(dd), paired_lo=st.mean(dd) - ph, paired_hi=st.mean(dd) + ph))
        L.append(f'| {p} − v4 | {k} | {d:+.4f} | [{d - h:+.4f}, {d + h:+.4f}] | {df:.2f} | {g:.2f} | {same} | {st.mean(dd):+.4f} [{st.mean(dd) - ph:+.4f}, {st.mean(dd) + ph:+.4f}] |')
with open(OUT / 'verify_contrasts.csv', 'w', newline='') as f:
    w_ = csv.DictWriter(f, list(cts[0]) if cts else ['contrast']); w_.writeheader(); w_.writerows(cts)
L += ['', '- Hedges g = (평균 차 / 합동 SD) × (1 − 3/(4(n₁+n₂) − 9)). n=3 대 3에서 g는 불안정하므로 크기 참고용이다.']
(OUT / 'verify.md').write_text('\n'.join(L).replace(' -0.', ' −0.').replace('[-', '[−') + '\n'); print('\n'.join(L))
