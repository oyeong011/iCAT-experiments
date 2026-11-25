#!/usr/bin/env python3
"""revC-20261124 (고컴: E2 미완료 · E6 1차 · E7) analysis, exactly as pre-registered (result/revC-20261124/preregistration.md §4).
    python3 -I analysis/revision_gocom/revC_analyze.py [RAW_DIR]
RAW_DIR default /home/oy/iCAT/result/revC-20261124/raw (read-only). Smoke runs (-smoke120) are excluded.
Outputs (derived, new files): result/revC-20261124-analysis/{runs,stats,phases}.csv and report.md in the worktree."""
import csv, math, re, statistics as st, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'analysis/final_e1'))
import validity as V
RAW = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/home/oy/iCAT/result/revC-20261124/raw')
OUT = ROOT / 'result/revC-20261124-analysis'; OUT.mkdir(parents=True, exist_ok=True)
CTRL = 'revC-v4'
POL = [('revC-v4', '대조군 iCAT-v4 (제거 15 %, 45개)'), ('revB-arm60', 'E7: 후보 60개'), ('online', 'E2: 원래 iCAT'),
       ('revC-elim10', 'E6: 제거 문턱 10 %'), ('revC-elim25', 'E6: 제거 문턱 25 %')]
T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 8: 2.306}
from scipy import stats as _ss
tq = lambda df: float(_ss.t.ppf(.975, df))   # 11-25: exact t quantile for fractional Welch df (was nearest-integer table T95)
REVA_V4 = [r for r in (ROOT / 'result/revA-20261114/raw').glob('mixFYF-revA-v4-rep[0-9]') if r.is_dir()]


def cnt(p):
    m = re.search(r'host_pages=(\d+) gc_pages=(\d+)', p.read_text()); return int(m[1]), int(m[2])


def total(d):
    m = re.search(r'^total .*host_pages=(\d+) gc_pages=(\d+)', (d / 'summary.txt').read_text(), re.M); return int(m[1]), int(m[2])


def partsum(d):
    ps = re.findall(r'^part=\d host_pages=(\d+) gc_pages=(\d+)', (d / 'final-control.txt').read_text(), re.M)
    return sum(int(a) for a, _ in ps), sum(int(b) for _, b in ps)


def ci(v):
    m = st.mean(v)
    if len(v) < 2: return m, float('nan'), float('nan'), float('nan')
    s = st.stdev(v); h = tq(len(v) - 1) * s / math.sqrt(len(v)); return m, s, m - h, m + h


def welch(a, b):
    va, vb = st.variance(a) / len(a), st.variance(b) / len(b); se = math.sqrt(va + vb); d = st.mean(a) - st.mean(b)
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1)) if se else float('inf')
    q = tq(df) if se else 0
    sp = math.sqrt(((len(a) - 1) * st.variance(a) + (len(b) - 1) * st.variance(b)) / (len(a) + len(b) - 2))
    g = d / sp * (1 - 3 / (4 * (len(a) + len(b)) - 9)) if sp else float('nan')   # Hedges g (added 11-25 at user request; not pre-registered)
    return d, d - q * se, d + q * se, df, g


runs = []
for d in sorted(RAW.glob('mixFYF-*-rep[0-9]')):
    if not d.is_dir() or not (d / 'summary.txt').exists(): continue
    pol = re.match(r'mixFYF-(.+)-rep(\d)$', d.name)[1]; rep = int(d.name[-1])
    h, g = total(d); ph, pg = partsum(d)
    row = dict(policy=pol, rep=rep, exit=(d / 'exit-code.txt').read_text().strip() if (d / 'exit-code.txt').exists() else 'missing',
               valid=V.run_ok(d), reasons=' | '.join(V.reasons(d)), waf=1 + g / h, waf_partitions=1 + pg / ph, two_paths_equal=(h, g) == (ph, pg),
               resets=sum('WATGC_V2 reset' in l for f in [d / 'kernel-final.log'] if f.exists() for l in f.read_text(errors='replace').splitlines()),
               dir=str(d))
    for p in 'ABC':
        if (d / f'phase-{p}-start.txt').exists():
            (h0, g0), (h1, g1) = cnt(d / f'phase-{p}-start.txt'), cnt(d / f'phase-{p}-end.txt'); row[f'waf_{p}'] = 1 + (g1 - g0) / (h1 - h0)
    runs.append(row)
with open(OUT / 'runs.csv', 'w', newline='') as f:
    keys = list(dict.fromkeys(k for r in runs for k in r)); w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(runs)

ok = {p: {r['rep']: r for r in runs if r['policy'] == p and r['valid'] and r['exit'] == '0'} for p, _ in POL}
stats, L = [], ['# revC-20261124 결과 (자동 생성, 사전 등록 §4 방식)', '',
                f'- 원자료: `{RAW}` (smoke 제외). 유효성: exit 0 + `validity.py`(YCSB 실패 ≤ 1 %, SQLITE_FULL 없음).',
                '- 통계: 평균 ± SD, 95 % t-CI. 대조군과의 차이는 Welch 95 % CI와 같은 rep끼리의 짝 비교 95 % CI. CI가 0을 포함하지 않을 때만 "차이 확인". n<3이면 통계 없음.',
                '- Hedges g(합동 SD, 소표본 보정)는 11-25 사용자 요청으로 추가한 것으로 사전 등록 지표가 아니다. n=3 대 3에서는 크기 참고용이다.', '',
                '| 정책 | 유효 n | 전체 WAF 평균 ± SD [95 % CI] | 단계 A / B / C 평균 | 대조군 대비 Welch Δ [95 % CI] | 같은 rep끼리 짝 Δ [95 % CI] | 판정 |', '|---|---:|---|---|---|---|---|']
base = ok[CTRL]
for p, lab in POL:
    v = [ok[p][k]['waf'] for k in sorted(ok[p])]; n = len(v)
    row = dict(policy=p, label=lab, n=n)
    if n == 0:
        L.append(f'| {lab} | 0 | 대기 | | | | |'); stats.append(row); continue
    m, s, lo, hi = ci(v); ph = ' / '.join(f"{st.mean(ok[p][k][f'waf_{x}'] for k in ok[p]):.3f}" for x in 'ABC')
    row.update(mean=m, sd=s, ci_lo=lo, ci_hi=hi)
    cell = f'{m:.4f} ± {s:.4f} [{lo:.4f}, {hi:.4f}]' if n >= 3 else f'{m:.4f} (n<3: 통계 없음)'
    wel = pair = verdict = ''
    if p != CTRL and n >= 3 and len(base) >= 3:
        d, dlo, dhi, df, hg = welch(v, [base[k]['waf'] for k in sorted(base)])
        reps = sorted(set(ok[p]) & set(base)); diffs = [ok[p][k]['waf'] - base[k]['waf'] for k in reps]
        pm, ps_, plo, phi = ci(diffs)
        wel = f'{d:+.4f} [{dlo:+.4f}, {dhi:+.4f}] (g={hg:+.2f})'; pair = f'{pm:+.4f} [{plo:+.4f}, {phi:+.4f}] (n={len(reps)})'
        verdict = '차이 확인' if (dlo > 0 or dhi < 0) else '구분되지 않음'
        row.update(welch=d, welch_lo=dlo, welch_hi=dhi, welch_df=df, hedges_g=hg, paired=pm, paired_lo=plo, paired_hi=phi, verdict=verdict)
    L.append(f'| {lab} | {n} | {cell} | {ph} | {wel} | {pair} | {verdict} |'.replace('-0.', '−0.').replace(' -', ' −'))
    stats.append(row)
with open(OUT / 'stats.csv', 'w', newline='') as f:
    keys = list(dict.fromkeys(k for r in stats for k in r)); w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(stats)
ra = [1 + g / h for d in REVA_V4 for h, g in [total(d)]]
if ra and len(base) >= 1:
    bm = st.mean(base[k]['waf'] for k in base)
    L += ['', f'- 배치 연결 (기록용, 판정에 쓰지 않음): revA-v4 {st.mean(ra):.4f} ± {st.stdev(ra):.4f} (n={len(ra)}), revC-v4 {bm:.4f} (n={len(base)}), 차이 {(bm / st.mean(ra) - 1) * 100:+.2f} %.']
inv = [r for r in runs if not (r['valid'] and r['exit'] == '0')]
L += ['', f'- 무효 또는 실패 run: {len(inv)}개' + ''.join(f"\n  - {r['policy']} rep{r['rep']}: exit {r['exit']}; {r['reasons']}" for r in inv)]
L += [f'- WAF 두 경로(summary 대 파티션 합) 불일치: {sum(not r["two_paths_equal"] for r in runs)}개']
(OUT / 'report.md').write_text('\n'.join(L) + '\n'); print('\n'.join(L))
