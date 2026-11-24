#!/usr/bin/env python3
"""Paper tables from validity-gated data (GoCom, 2026-11-24). Writes report/final-e1-validation/tables/*.
  table6_valid.{md,csv}  : Table 6 rows whose runs pass validity.py (iCAT-v4 x3 mean (n), 6 fixed arms)
  table8_status.md       : Table 8 / Fig 10 (3-phase equal-write, mixR) -> banned until a valid E1 rerun exists
  sec41_order_check.csv  : the 4.1 claim "CAT-Best, CAT-Robust < CAT-Default < iCAT < Greedy" checked on the gated 1x tables
Inputs: raw result dirs (Table 6), report/final-e1-validation/tables/RESULTS_ALL.gated.md (4.1 check)."""
import csv, re, statistics as st, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import validity as V
ROOT = V.ROOT; M = ROOT / 'result/mix-20260911'; T = ROOT / 'report/final-e1-validation/tables'; T.mkdir(parents=True, exist_ok=True)


def tot(d):
    d = M / d; f = d / 'summary.txt'
    if not f.exists() or not V.run_ok(d): return None
    return float(re.search(r'^total .*WAF=([\d.]+)', f.read_text(), re.M)[1])


# ---- Table 6
ROWS = [('O', 'OLTP → Varmail'), ('F', 'FIO-Fast → Varmail'), ('J', 'YCSB-A → YCSB-B'), ('P', 'YCSB-A → OLTP')]
ARMS = [('fixed47', 'arm 47 (Best)'), ('arm17', 'arm 17'), ('fixed50', 'arm 50 (Robust)'), ('arm46', 'arm 46'), ('arm31', 'arm 31'), ('fixed37', 'arm 37 (Default)')]
out, md = [], ['| 전환 워크로드 | iCAT-v4 (n) | ' + ' | '.join(a for _, a in ARMS) + ' | iCAT-v4 순위 |', '|---|---:|' + '---:|' * len(ARMS) + '---|']
excluded = []
for k, name in ROWS:
    v = [x for r in (1, 2, 3) if (x := tot(f'mix{k}-onlinev4-rep{r}-x3'))]
    f = {p: tot(f'mix{k}-{p}-rep1-x3') for p, _ in ARMS}
    if not v or any(x is None for x in f.values()):
        excluded.append(name); continue
    m = st.mean(v); allv = sorted([m] + list(f.values())); rank = allv.index(m) + 1
    best = min(f.values())
    cells = [f'**{x:.3f}**' if x == best and x < m else f'{x:.3f}' for x in f.values()]
    md.append(f'| {name} | ' + (f'**{m:.3f}**' if m < best else f'{m:.3f}') + f' ({len(v)}) | ' + ' | '.join(cells) + f' | {rank}/{len(ARMS) + 1} |')
    out.append(dict(workload=name, v4_mean=f'{m:.4f}', v4_n=len(v), v4_runs=' '.join(f'{x:.4f}' for x in v), **{a: f'{x:.4f}' for a, x in f.items()}, v4_rank=f'{rank}/{len(ARMS) + 1}'))
(T / 'table6_valid.md').write_text('**표 6 (유효성 검사 적용).** 전환 워크로드 ' + f'{len(out)}종에서 iCAT-v4와 고정 조합 6개의 WAF (3배 길이; iCAT-v4는 2~3회 평균, 고정 조합 1회)\n\n'
                                   + '\n'.join(md) + f"\n\n제외: {', '.join(excluded) or '없음'} (YCSB SQLITE_FULL 오염, `analysis/final_e1/validity.py`).\n")
with open(T / 'table6_valid.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)

# ---- Table 8 / Fig 10
rr = sorted(p for p in M.glob('mixR-*-x3') if p.is_dir())
lines = ['# 표 8 · 그림 10 (3단계 균등 전환) 사용 금지', '',
         f'- 원자료 `result/mix-20260911/mixR-*-x3` {len(rr)}개 run 중 단계 2·3이 유효한 run: {sum(1 for p in rr if {"B", "C"} <= V.usable_phases(p))}개.',
         '- 단계 1(FIO-Fast)만 유효하다. 단계 2(YCSB-A)와 단계 3, 전체 WAF는 YCSB SQLITE_FULL 오염으로 무효다.',
         '- E1 재실험(`result/revision-20261124/mixR`, YCSB 300k records)에서 정책별로 유효한 3회가 모이기 전에는 표 8과 그림 10을 논문에 싣지 않는다.',
         '- 재실험은 YCSB 레코드 수가 600k → 300k로 바뀌었다. 그래서 원래 표 8의 정책(CAT-Best, CAT-Robust, arm 17, iCAT, iCAT-v3, CAT-Default)과는 같은 조건이 아니다. 재실험은 v4 / nodrift / fullreset만 다룬다.', '',
         '| run | 유효 단계 | 판정 |', '|---|---|---|']
lines += [f"| {p.name} | {''.join(sorted(V.usable_phases(p))) or '-'} | 무효(단계 2·3·전체): {'; '.join(V.reasons(p))[:80]} |" for p in rr]
(T / 'table8_status.md').write_text('\n'.join(lines) + '\n')

# ---- 4.1 ordering claim on the gated 1x tables
g = (T / 'RESULTS_ALL.gated.md').read_text()
def table(sec):
    blk = g.split(sec, 1)[1].split('\n## ', 1)[0]
    rows = [l for l in blk.splitlines() if l.startswith('| ') and not l.startswith('| 워크로드') and not l.startswith('| 믹스')]
    return [[c.strip() for c in l.strip('|').split('|')] for l in rows]
num = lambda c: float(re.match(r'[\d.]+', c)[0]) if re.match(r'[\d.]+', c) else None
chk = []
for sec, kind in (('## 1. 단일 워크로드', 'single'), ('## 4. 믹스 14종', 'mix-1x')):
    for r in table(sec):
        name, greedy, worst, dflt, best, robust, v1 = r[:7]
        vals = dict(greedy=num(greedy), default=num(dflt), best=num(best), robust=num(robust), icat=num(v1))
        if any(x is None for x in vals.values()):
            chk.append(dict(kind=kind, workload=name, status='EXCLUDED (invalid data)', **{k: '' for k in vals})); continue
        ok1 = max(vals['best'], vals['robust']) < vals['default']; ok2 = vals['default'] < vals['icat']; ok3 = vals['icat'] < vals['greedy']
        chk.append(dict(kind=kind, workload=name, status='holds' if ok1 and ok2 and ok3 else
                        'VIOLATED: ' + ', '.join(x for x, o in (('Best/Robust<Default', ok1), ('Default<iCAT', ok2), ('iCAT<Greedy', ok3)) if not o),
                        **{k: f'{x:.3f}' for k, x in vals.items()}))
with open(T / 'sec41_order_check.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(chk[0])); w.writeheader(); w.writerows(chk)
print(open(T / 'table6_valid.md').read())
for c in chk: print(c['kind'], c['workload'], c['status'])

# ---- Table A1: gated RESULTS_ALL §1 (single) and §4 (transition, 1x) with the manuscript's workload names
NAMES = {'거래 DB 흉내': 'OLTP', '메일 서버 (15만 파일)': 'Varmail', 'hot/cold 2영역': 'FIO-HotCold', '느린 3영역': 'FIO-Slow', '빠른 3영역': 'FIO-Fast',
         'hot 위치 이동': 'FIO-Shift', 'SQLite 읽기50/수정50': 'YCSB-A', 'SQLite 읽기95/수정5': 'YCSB-B',
         '빠른 3영역 → SQLite': 'FIO-Fast → YCSB-A', 'SQLite → 빠른 3영역': 'YCSB-A → FIO-Fast', '느린 → 빠른 3영역': 'FIO-Slow → FIO-Fast',
         '빠른 → 느린 3영역': 'FIO-Fast → FIO-Slow', '빠른 3영역 → 메일 서버': 'FIO-Fast → Varmail', '빠른 3영역 + SQLite 동시': 'FIO-Fast ∥ YCSB-A',
         '느린 → 빠른 → SQLite': 'FIO-Slow → FIO-Fast → YCSB-A', 'SQLite 수정 많음 → 읽기 위주': 'YCSB-A → YCSB-B',
         '뜨거운 구역 512 → 128 MB': 'FIO-Fast (hot 512 → 128 MB)', '빠른 ↔ 느린 60초 × 5': 'FIO-Fast ↔ FIO-Slow (60 s × 5)',
         '초당 1만 → 5만 서서히': '점진적 부하 증가', '거래 DB 흉내 → 메일 서버': 'OLTP → Varmail', 'SQLite → 거래 DB 흉내': 'YCSB-A → OLTP',
         '빠른 → 5분 쉼 → 빠른': 'FIO-Fast → 유휴 → FIO-Fast'}
fmt = lambda c: re.sub(r'\s*\((\d+)\)$', r' (\1)', re.sub(r'\((\d+)\)$', r' (\1)', c.strip()))
A1 = ['**표 A1.** 1배 길이 결과 요약 (평균, 괄호는 반복 횟수; 원저자 계측 방식). 생성: `analysis/all-tables.py`(유효성 검사 적용) → `report/final-e1-validation/tables/RESULTS_ALL.gated.md` §1·§4', '',
      '(a) 단일 워크로드', '', '| 워크로드 | Greedy | 최악 CAT (arm 10) | CAT-Default | CAT-Best | CAT-Robust | iCAT |', '|---|---:|---:|---:|---:|---:|---:|']
for r in table('## 1. 단일 워크로드'):
    A1.append(f'| {NAMES.get(r[0], r[0])} | ' + ' | '.join(fmt(c) for c in r[1:7]) + ' |')
A1 += ['', '(b) 전환 워크로드 (iCAT-v4는 1회, 첫 순회가 실행 대부분을 차지해 참고값)', '',
       '| 전환 워크로드 | Greedy | 최악 CAT (arm 10) | CAT-Default | CAT-Best | CAT-Robust | iCAT | iCAT-v4 |', '|---|---:|---:|---:|---:|---:|---:|---:|']
for r in table('## 4. 믹스 14종'):
    if all(c.strip() == '–' for c in r[1:]):
        A1.append(f'| {NAMES.get(r[0], r[0])} | ' + ('검증 불가 (YCSB 출력 없음, 한계 7)' if '동시' in r[0] else '무효 (YCSB 오류, 한계 7)') + ' | | | | | | |')
    else:
        A1.append(f'| {NAMES.get(r[0], r[0])} | ' + ' | '.join(fmt(c) for c in r[1:8]) + ' |')
(T / 'tableA1.md').write_text('\n'.join(A1) + '\n')
print('\n'.join(A1))

# ---- Table 7 candidates: 1x screen of 16 fixed arms (valid workloads only) + 3x confirmation (gated §11)
ARMS16 = ['fixed47', 'fixed50', 'fixed37'] + [f'arm{a:02d}' for a in (46, 31, 32, 17, 16, 15, 30, 34, 35, 45, 49, 53, 56)]
anum = lambda a: int(re.sub(r'\D', '', a))
SCREEN = [('B', 'YCSB-A → FIO-Fast'), ('D', 'FIO-Fast → FIO-Slow'), ('F', 'FIO-Fast → Varmail'), ('G', 'FIO-Fast ∥ YCSB-A'),
          ('H', 'FIO-Slow → FIO-Fast → YCSB-A'), ('J', 'YCSB-A → YCSB-B'), ('K', 'FIO-Fast (hot 512 → 128 MB)'),
          ('L', 'FIO-Fast ↔ FIO-Slow (60 s × 5)'), ('O', 'OLTP → Varmail'), ('P', 'YCSB-A → OLTP'), ('Q', 'FIO-Fast → 유휴 → FIO-Fast')]
loss, rows7, excl7 = {}, [], []
for k, name in SCREEN:
    w = {a: st.mean(xs) for a in ARMS16 if (xs := [x for r in (1, 2, 3) if (x := tot(f'mix{k}-{a}-rep{r}')) is not None])}   # mean of valid reps, as RESULTS_ALL §10
    if len(w) < len(ARMS16):
        excl7.append(f'{name} ({len(w)}/16 유효)'); continue
    best = min(w.values()); loss[name] = {a: (x / best - 1) * 100 for a, x in w.items()}
    top = sorted(w, key=w.get)[:3]; rk = {a: sorted(w, key=w.get).index(a) + 1 for a in w}
    x3 = {a: x for a in ARMS16 if (x := tot(f'mix{k}-{a}-rep1-x3')) is not None}
    v4 = [x for r in (1, 2, 3) if (x := tot(f'mix{k}-onlinev4-rep{r}-x3'))]
    b3 = min(x3, key=x3.get) if x3 else None
    rows7.append(f"| {name} | {', '.join(f'arm {anum(a)} {w[a]:.3f}' for a in top)} | {rk['fixed47']} / {rk['fixed50']} / {rk['fixed37']} | "
                 + (f"{len(x3)}개: arm {anum(b3)} {x3[b3]:.3f}" if len(x3) >= 2 else (f'3배 확인 없음 (arm {anum(b3)}만 측정)' if x3 else '3배 확인 없음')) + ' | '
                 + (f"{st.mean(v4):.3f} ({len(v4)})" + (f", 측정 최상위 대비 {(st.mean(v4) / x3[b3] - 1) * 100:+.1f} %" if len(x3) >= 2 else '') if v4 else '–') + ' |')
agg = {a: (st.mean(loss[n][a] for n in loss), max(loss[n][a] for n in loss)) for a in ARMS16}
order = sorted(agg, key=lambda a: agg[a][0])
T7 = ['**표 7 후보 (유효 데이터만).** 전환 워크로드에서 고정 조합 16개를 1배 길이로 선별한 결과와 3배 길이 확인 (고정 조합 각 1회, iCAT-v4 1~3회)', '',
      '| 전환 워크로드 | 1배 선별 상위 3 (16개 중) | arm 47 / 50 / 37의 1배 순위 | 3배 확인 (측정 조합 수: 최상위) | iCAT-v4 3배 (n) |', '|---|---|---|---|---|'] + rows7 + [
      '', f'제외 (YCSB 오류 또는 검증 불가): {", ".join(excl7)}.', '',
      f'**유효 {len(loss)}종 전체에서 1배 손실(워크로드별 16개 중 최상위 대비 WAF 증가율)의 평균이 작은 순:**', '',
      '| 고정 조합 | 평균 손실 % | 최대 손실 % |', '|---|---:|---:|'] + [f'| arm {anum(a)} | {agg[a][0]:.1f} | {agg[a][1]:.1f} |' for a in order[:6]] + [
      '', f'최대 손실이 가장 작은 조합: arm {anum(min(agg, key=lambda a: agg[a][1]))} ({min(v[1] for v in agg.values()):.1f} %).']
(T / 'table7_valid.md').write_text('\n'.join(T7) + '\n')
print('\n'.join(T7))
