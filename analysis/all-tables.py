#!/usr/bin/env python3
"""Every result table from the raw result files -> RESULTS_ALL.md.  python3 analysis/all-tables.py"""
import re, statistics as st, subprocess, datetime
from pathlib import Path
R = Path('/home/oy/iCAT/result'); M = R / 'mix-20260911'
out = []
p = out.append

def tot(d):
    f = M / d / 'summary.txt'
    if not f.exists(): return None
    m = re.search(r'^total .*WAF=([\d.]+)', f.read_text(), re.M)
    return float(m[1]) if m else None
def phases(d):
    f = M / d / 'summary.txt'
    if not f.exists(): return {}
    return {k: float(w) for k, w in re.findall(r'^phase([ABC])\(\S*\) host_pages=\d+ gc_pages=\d+ WAF=([\d.]+)', f.read_text(), re.M)}
def mean3(pat):
    xs = [x for r in (1, 2, 3) if (x := tot(pat.format(r=r))) is not None]
    return (st.mean(xs), len(xs)) if xs else (None, 0)
def f(x, n=None):
    if x is None: return '–'
    return f'{x:.3f}' + (f' ({n})' if n and n > 1 else '')
def sweep(path):
    t = Path(path).read_text()
    return {int(a): float(w) for a, w in re.findall(r'^\s*\d+\s+arm(\d\d)\s+\S+\s+([\d.]+)', t, re.M)}
def rank(W, v): return 1 + sum(1 for x in W.values() if x < v) if v else None
def nm(a): return f"k{[2,4,7,10][a//15]}·{[25,50,100,200,400][(a//3)%5]}%·r{[4,7,16][a%3]}"
def v4curve(d):
    rows = []
    for l in (M / d / 'control-series.txt').read_text().splitlines():
        s = l.split()
        if len(s) > 5 and s[4].startswith('host_pages='):
            h, g = int(s[4].split('=')[1]), int(s[5].split('=')[1])
            if h > 0: rows.append((int(s[0]), h, g))
    t0 = rows[0][0]
    return lambda hrs: (lambda r: 1 + r[2] / r[1])(min(rows, key=lambda r: abs(r[0] - t0 - hrs * 3600)))

MIX = {'A': '빠른 3영역 → SQLite', 'B': 'SQLite → 빠른 3영역', 'C': '느린 → 빠른 3영역', 'D': '빠른 → 느린 3영역',
       'F': '빠른 3영역 → 메일 서버', 'G': '빠른 3영역 + SQLite 동시', 'H': '느린 → 빠른 → SQLite', 'J': 'SQLite 수정 많음 → 읽기 위주',
       'K': '뜨거운 구역 512 → 128 MB', 'L': '빠른 ↔ 느린 60초 × 5', 'M': '초당 1만 → 5만 서서히', 'O': '거래 DB 흉내 → 메일 서버',
       'P': 'SQLite → 거래 DB 흉내', 'Q': '빠른 → 5분 쉼 → 빠른'}

p(f'# 전체 결과표\n\n> `python3 analysis/all-tables.py`로 원본 결과 파일에서 자동 생성 ({datetime.datetime.now():%Y-%m-%d %H:%M}). '
  'WAF는 낮을수록 좋다. 괄호 숫자는 반복 횟수(평균). –는 측정 안 함.\n')
p('정책: Greedy / 최악 CAT(10번 k2·200%·r7) / 기본 CAT(37번 k7·100%·r7, 원저자 기본값) / 최적 CAT(47번 k10·25%·r16) / 견고 CAT(50번 k10·50%·r16) / v1(원저자 iCAT) / v2·v3·v4(고친 iCAT).\n')

# 1. single workloads, x1 (GitHub method)
p('## 1. 단일 워크로드 (1배 길이, 원저자 계측 방식)\n')
p('| 워크로드 | Greedy | 최악 CAT | 기본 CAT | 최적 CAT | 견고 CAT | v1 |\n|---|---:|---:|---:|---:|---:|---:|')
s = subprocess.run(['python3', '/home/oy/iCAT/analysis/summary.py'], capture_output=True, text=True).stdout
NAMES = {'test2': 'hot/cold 2영역', 'test3': '느린 3영역', 'test4': '빠른 3영역', 'test5': 'hot 위치 이동',
         'sqlite-a': 'SQLite 읽기50/수정50', 'sqlite-b': 'SQLite 읽기95/수정5', 'oltp': '거래 DB 흉내', 'varmail': '메일 서버 (15만 파일)'}
for line in s.splitlines():
    c = line.split()
    if not c or c[0] not in ('fio(gh)', 'sqlite', 'filebench'): continue
    w = c[1]; cells = [x for x in line.split('  ') if x.strip()][2:]
    v = dict(zip(['gh-greedy', 'greedy', 'fixed10', 'gh-cat37', 'fixed37', 'fixed47', 'fixed50', 'gh-online', 'online', 'online-v2', 'onlinev2'], [x.strip() for x in cells]))
    p(f"| {NAMES.get(w, w)} | {v['gh-greedy']} | {v['fixed10']} | {v['gh-cat37']} | {v['fixed47']} | {v['fixed50']} | {v['gh-online']} |")

# 2. fast 3-region by length
p('\n## 2. 빠른 3영역 쓰기, 실행 길이별 (명시 계측)\n')
c = v4curve('t4-onlinev4-rep1-x60')
L = [('10분', 't4-{p}-rep{r}', 0.167), ('30분', 't4-{p}-rep{r}-x3', 0.5), ('1시간', 't4long-{p}-rep{r}', 1), ('3시간', 't4-{p}-rep{r}-x18', 3), ('10시간', 't4-{p}-rep{r}-x60', 10)]
p('| 길이 | 최적 CAT | 견고 CAT | Greedy | v1 | v2 | v3 | v4 |\n|---|---:|---:|---:|---:|---:|---:|---:|')
for lab, pat, hrs in L:
    row = [mean3(pat.replace('{p}', q)) for q in ('fixed47', 'fixed50', 'greedy', 'online', 'onlinev2', 'onlinev3')]
    v4 = f(c(hrs)) + (' *' if hrs < 10 else '') if hrs >= 1 else '–'
    p(f'| {lab} | ' + ' | '.join(f(*x) for x in row) + f' | {v4} |')
p('\n\\* v4 1시간·3시간 값은 10시간 실행의 해당 시점 누적 WAF(30초 카운터). v2 10분은 순회 도중 종료(무의미).\n')

# 3. rank among 60 arms
p('## 3. 60개 고정 조합 중 순위 (61자리 중)\n')
T = sweep(R / 'sweep-20260915/rank-test4.txt'); SQ = sweep(R / 'sweep-20260915/rank-sqlite-a.txt')
MA = {a: tot(f'mixA-arm{a:02d}-rep1') for a in range(60)}; MC = {a: tot(f'mixC-arm{a:02d}-rep1') for a in range(60)}
g = lambda k: mean3(k)[0]
rows = [('최적 CAT (47)', T[47], MA[47], MC[47], SQ[47]), ('견고 CAT (50)', T[50], MA[50], MC[50], SQ[50]),
        ('기본 CAT (37)', T[37], MA[37], MC[37], SQ[37]), ('Greedy', 2.186, g('mixA-greedy-rep{r}'), g('mixC-greedy-rep{r}'), 1.503),
        ('v1 (1배)', 2.001, g('mixA-online-rep{r}'), g('mixC-online-rep{r}'), 1.342),
        ('v1 (3시간 / 3배 / 3배)', 1.884, tot('mixA-online-rep1-x3'), tot('mixC-online-rep1-x3'), None),
        ('v1 (– / 6배 / 6배)', None, tot('mixA-online-rep1-x6'), tot('mixC-online-rep1-x6'), None),
        ('v3 (3시간)', 1.848, None, None, None),
        ('v4 (10시간 / 3배 / 3배)', c(10), tot('mixA-onlinev4-rep1-x3'), tot('mixC-onlinev4-rep1-x3'), None),
        ('v4 (– / 6배 / 6배)', None, tot('mixA-onlinev4-rep1-x6'), tot('mixC-onlinev4-rep1-x6'), None)]
p('| 정책 | 빠른 3영역 단일 | 빠른 3영역 → SQLite | 느린 → 빠른 3영역 | SQLite 단일 |\n|---|---|---|---|---|')
for lab, *vs in rows:
    p(f'| {lab} | ' + ' | '.join(f'{rank(W, v)}등 ({v:.3f})' if v else '–' for W, v in zip((T, MA, MC, SQ), vs)) + ' |')
p(f'\n각 실험의 1등: 빠른 3영역 {nm(min(T, key=T.get))} {min(T.values()):.3f} / 빠른→SQLite {nm(min(MA, key=MA.get))} {min(MA.values()):.3f} / '
  f'느린→빠른 {nm(min(MC, key=MC.get))} {min(MC.values()):.3f} / SQLite {nm(min(SQ, key=SQ.get))} {min(SQ.values()):.3f}. 고정 조합 값은 1배 길이(길이에 거의 무관: 47번 빠른 3영역 10분 1.774, 3시간 1.772).\n')

# 4. mixes x1
p('## 4. 믹스 14종, 1배 길이 (10~30분, 3회 평균)\n')
p('| 믹스 | Greedy | 최악 CAT | 기본 CAT | 최적 CAT | 견고 CAT | v1 | v4 (1회) |\n|---|---:|---:|---:|---:|---:|---:|---:|')
for k, n in MIX.items():
    vals = [mean3(f'mix{k}-{q}-rep{{r}}') for q in ('greedy', 'fixed10', 'fixed37', 'fixed47', 'fixed50', 'online')]
    p(f'| {n} | ' + ' | '.join(f(*x) for x in vals) + f" | {f(tot(f'mix{k}-onlinev4-rep1'))} |")
p('\nv4 1배는 첫 순회(약 15분)가 실행 대부분을 차지해 평가용이 아님(참고값).\n')

# 5. mixes x3
p('## 5. 믹스, 3배 길이 (30~90분, 1회)\n')
p('| 믹스 | 최적 CAT | 견고 CAT | v1 | v2 | **v4** | v4 − 견고 |\n|---|---:|---:|---:|---:|---:|---:|')
for k, n in MIX.items():
    v = [tot(f'mix{k}-{q}-rep1-x3') for q in ('fixed47', 'fixed50', 'online', 'onlinev2', 'onlinev4')]
    if not any(v): continue
    d = f'{(v[4] / v[1] - 1) * 100:+.1f}%' if v[4] and v[1] else '–'
    p(f'| {n} | ' + ' | '.join(f(x) for x in v) + f' | {d} |')
p('\n파일벤치가 들어간 믹스(메일 서버, 거래 DB 흉내)는 3배 길이에서 파일벤치 구간을 900초로 늘림.\n')

# 6. mixes x6
p('## 6. 믹스, 6배 길이 (약 2시간, 1회; v2는 3회 평균)\n')
p('| 믹스 | 최적 CAT | 견고 CAT | v1 | v2 | v3 | v4 |\n|---|---:|---:|---:|---:|---:|---:|')
for k in 'ACDK':
    v = [mean3(f'mix{k}-{q}-rep{{r}}-x6') for q in ('fixed47', 'fixed50', 'online', 'onlinev2', 'onlinev3', 'onlinev4')]
    p(f'| {MIX[k]} | ' + ' | '.join(f(*x) for x in v) + ' |')

# 7. mixR
p('\n## 7. 새 믹스: 빠른 3영역 → SQLite → 빠른 3영역 (구간별 쓰기량 같게, 3배 길이 약 2.3시간)\n')
p('| 정책 | 빠른 (앞) | SQLite | 빠른 (뒤) | 전체 |\n|---|---:|---:|---:|---:|')
for lab, q in [('최적 CAT (47)', 'fixed47'), ('32번 (k7·25%·r16)', 'arm32'), ('견고 CAT (50)', 'fixed50'), ('17번 (k4·25%·r16)', 'arm17'),
               ('기본 CAT (37)', 'fixed37'), ('Greedy', 'greedy'), ('v1', 'online'), ('v3', 'onlinev3'), ('v4', 'onlinev4')]:
    for r in (1, 2):
        d = f'mixR-{q}-rep{r}-x3'; ph = phases(d)
        if ph: p(f"| {lab}{' (2회차)' if r == 2 else ''} | {f(ph.get('A'))} | {f(ph.get('B'))} | {f(ph.get('C'))} | {f(tot(d))} |")

# 8. slow
p('\n## 8. 아주 느린 3영역 쓰기 (빠른 3영역의 1/16 속도, 20분, 원저자 계측 방식)\n')
SL = sweep(R / 'sweep-slow16-20260921/rank-slow16.txt')
p('| 순위 | 조합 | WAF |\n|---|---|---:|')
for i, (a, w) in enumerate(sorted(SL.items(), key=lambda x: x[1])):
    tag = {47: ' ← 최적 CAT', 50: ' ← 견고 CAT', 37: ' ← 기본 CAT'}.get(a, '')
    p(f'| {i + 1} | {a}번 ({nm(a)}){tag} | {w:.3f} |')
gw = re.search(r'WAF=([\d.]+)', subprocess.run(f"grep -h 'GC stats' $(grep -h '^\\[RESULT\\]' {R}/sweep-slow16-20260921/slow16-greedy.console.txt | awk '{{print $2}}') | tail -1", shell=True, capture_output=True, text=True).stdout)
p(f'| – | Greedy | {gw[1] if gw else "–"} |\n\n{len(SL)}개 조합만 측정(핵심 15개 + k=2 6개).\n')

# 9. oltp recheck
p('## 9. 거래 DB 흉내 재측정 (5분, 3회)\n')
p('| 조합 | 60조합 sweep (1회) | 1회 | 2회 | 3회 | 평균 |\n|---|---:|---:|---:|---:|---:|')
OL = sweep(R / 'sweep-20260915/rank-oltp.txt')
for a in (46, 47, 49, 50):
    xs = []
    for r in (1, 2, 3):
        m = re.search(r'^\[WAF\] module=\S+ WAF=([\d.]+)', (R / f'filebench/oltp-arm{a}-rep{r}.console.txt').read_text(), re.M)
        xs.append(float(m[1]) if m else None)
    p(f'| {a}번 ({nm(a)}) | {OL[a]:.3f} | ' + ' | '.join(f(x) for x in xs) + f' | {f(st.mean([x for x in xs if x]))} |')

Path('/home/oy/iCAT/RESULTS_ALL.md').write_text('\n'.join(out) + '\n')
print('\n'.join(out))
