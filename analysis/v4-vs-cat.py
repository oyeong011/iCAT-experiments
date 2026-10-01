#!/usr/bin/env python3
"""How much better is iCAT v4 than CAT? Every comparison at the same length and measurement method -> V4_VS_CAT.md"""
import re, statistics as st, datetime
from pathlib import Path
M = Path('/home/oy/iCAT/result/mix-20260911')
def tot(d):
    f = M / d / 'summary.txt'
    if not f.exists() or (M / d / 'SUSPECT.txt').exists(): return None
    m = re.search(r'^total .*WAF=([\d.]+)', f.read_text(), re.M); return float(m[1]) if m else None
def avg(ds):
    xs = [x for d in ds if (x := tot(d))]; return (st.mean(xs), len(xs)) if xs else (None, 0)
def curve(d, hrs):
    rows = []
    for l in (M / d / 'control-series.txt').read_text().splitlines():
        s = l.split()
        if len(s) > 5 and s[4].startswith('host_pages='):
            h, g = int(s[4].split('=')[1]), int(s[5].split('=')[1])
            if h > 0: rows.append((int(s[0]), h, g))
    r = min(rows, key=lambda r: abs(r[0] - rows[0][0] - hrs * 3600)); return 1 + r[2] / r[1]
def pct(v, b): return f'{(v / b - 1) * 100:+.1f}%' if v and b else '–'
def w(x, n=0): return '–' if x is None else f'{x:.3f}' + (f' ({n})' if n > 1 else '')
MIX = {'O': '거래 DB 흉내 → 메일 서버', 'F': '빠른 3영역 → 메일 서버', 'J': 'SQLite 수정 많음 → 읽기 위주', 'P': 'SQLite → 거래 DB 흉내',
       'K': '뜨거운 구역 512 → 128 MB', 'D': '빠른 → 느린 3영역', 'H': '느린 → 빠른 → SQLite', 'L': '빠른 ↔ 느린 60초 × 5',
       'C': '느린 → 빠른 3영역', 'Q': '빠른 → 5분 쉼 → 빠른', 'A': '빠른 3영역 → SQLite', 'B': 'SQLite → 빠른 3영역', 'G': '빠른 3영역 + SQLite 동시'}
o = []; p = o.append
p(f'# iCAT v4는 CAT보다 얼마나 좋은가\n\n> `python3 analysis/v4-vs-cat.py`로 원본 결과에서 자동 생성 ({datetime.datetime.now():%Y-%m-%d %H:%M}). '
  'WAF는 낮을수록 좋다. **음수(−)면 v4가 그만큼 좋다.** 모든 비교는 같은 길이·같은 측정 방식(명시 계측)끼리다. 괄호 = 반복 횟수(평균).\n')
p('비교 대상: **기본 CAT** = 37번(k7·100%·r7, 원저자 기본값) / **견고 CAT** = 50번(k10·50%·r16, 원저자 워크로드에서 최악 손해 최소) / '
  '**최적 CAT** = 47번(k10·25%·r16, 이 환경 대부분에서 1등) / **1등 고정** = 그 워크로드에서 측정한 고정 조합 중 1등 / Greedy / v1 = 원래 iCAT.\n')

# ---- 1. single workload
p('## 1. 단일 워크로드: 빠른 3영역 쓰기\n')
p('| 실행 길이 | v4 | 기본 CAT | 견고 CAT | 최적 CAT | Greedy | v1 | v4 − 기본 | v4 − 견고 | v4 − 최적 | v4 − Greedy | v4 − v1 |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
d37, d50, d47, dg = tot('t4-fixed37-rep1'), tot('t4long-fixed50-rep1'), tot('t4-fixed47-rep1-x18'), tot('t4long-greedy-rep1')
for lab, hrs, v1 in [('1시간', 1, tot('t4long-online-rep1')), ('3시간', 3, tot('t4-online-rep1-x18')), ('10시간', 10, None)]:
    v4 = curve('t4-onlinev4-rep1-x60', hrs)
    p(f'| {lab} | {v4:.3f} | {w(d37)} | {w(d50)} | {w(d47)} | {w(dg)} | {w(v1)} | {pct(v4, d37)} | {pct(v4, d50)} | {pct(v4, d47)} | {pct(v4, dg)} | {pct(v4, v1)} |')
p('\n고정 조합과 Greedy는 실행 길이에 따라 값이 거의 변하지 않는다(47번 10분 1.774, 3시간 1.772). 기본 CAT은 10분, 견고·Greedy는 1시간, 최적은 3시간 값. '
  'v4의 1·3시간 값은 10시간 실행의 해당 시점 누적 WAF. 같은 방식으로 잰 고정 조합 60개 사이에서 v4(10시간)는 **5위**.\n')

# ---- 2. transition workloads x3
p('## 2. 전환 워크로드 13종 (3배 길이, 30~90분)\n')
p('| 전환 워크로드 | v4 | 기본 CAT | 견고 CAT | 최적 CAT | 1등 고정 (번호) | v4 − 기본 | v4 − 견고 | v4 − 최적 | v4 − 1등 고정 |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
ARMS = ['fixed47', 'fixed50', 'fixed37'] + [f'arm{a:02d}' for a in (46, 31, 32, 17, 16, 15, 30, 34, 35, 45, 49, 53, 56)]
cnt = {'기본': [0, 0], '견고': [0, 0], '최적': [0, 0], '1등': [0, 0]}
for k, n in MIX.items():
    v4, nv = avg([f'mix{k}-onlinev4-rep{r}-x3' for r in (1, 2, 3)])
    f3 = {a: x for a in ARMS if (x := tot(f'mix{k}-{a}-rep1-x3'))}
    b37, b50, b47 = f3.get('fixed37'), f3.get('fixed50'), f3.get('fixed47')
    best = min(f3, key=f3.get) if f3 else None
    for key, b in [('기본', b37), ('견고', b50), ('최적', b47), ('1등', f3.get(best) if len(f3) >= 3 else None)]:
        if v4 and b: cnt[key][0] += v4 < b; cnt[key][1] += 1
    bl = f'{f3[best]:.3f} ({best.replace("fixed", "").replace("arm", "")}번, {len(f3)}개 중)' if len(f3) >= 3 else '–'
    p(f'| {n} | {w(v4, nv)} | {w(b37)} | {w(b50)} | {w(b47)} | {bl} | {pct(v4, b37)} | {pct(v4, b50)} | {pct(v4, b47)} | {pct(v4, f3[best]) if len(f3) >= 3 else "–"} |')
p('\n**v4가 이긴 횟수 (같은 길이에서 잰 경우만)**: ' + ', '.join(f'{k} CAT {a}/{b}' if k != '1등' else f'1등 고정 {a}/{b}' for k, (a, b) in cnt.items()) + '\n')
p('–: 그 길이에서 측정하지 않음(1배 길이 값은 길이에 따라 작업 내용이 달라져 섞지 않음). 1등 고정은 3개 이상 측정한 워크로드만.\n')

# ---- 3. transition workloads x6
p('## 3. 전환 워크로드 4종 (6배 길이, 약 2시간)\n')
p('| 전환 워크로드 | v4 | 견고 CAT | 최적 CAT | v1 | v3 | v4 − 견고 | v4 − 최적 | v4 − v1 |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|')
for k in 'ACDK':
    v4 = tot(f'mix{k}-onlinev4-rep1-x6'); b50, n50 = avg([f'mix{k}-fixed50-rep{r}-x6' for r in (1, 2, 3)]); b47, _ = avg([f'mix{k}-fixed47-rep{r}-x6' for r in (1, 2, 3)])
    v1 = tot(f'mix{k}-online-rep1-x6'); v3 = tot(f'mix{k}-onlinev3-rep1-x6')
    p(f'| {MIX[k]} | {w(v4)} | {w(b50)} | {w(b47)} | {w(v1)} | {w(v3)} | {pct(v4, b50)} | {pct(v4, b47)} | {pct(v4, v1)} |')

# ---- 4. three-phase
p('\n## 4. 3구간 전환: 빠른 3영역 → SQLite → 빠른 3영역 (구간별 쓰기량 동일, 약 2.3시간)\n')
v4, nv = avg([f'mixR-onlinev4-rep{r}-x3' for r in (1, 2)])
rows = [('기본 CAT', avg(['mixR-fixed37-rep1-x3'])), ('견고 CAT', avg([f'mixR-fixed50-rep{r}-x3' for r in (1, 2)])), ('최적 CAT', avg(['mixR-fixed47-rep1-x3'])),
        ('17번 (SQLite 구간 1등)', avg(['mixR-arm17-rep1-x3'])), ('32번', avg(['mixR-arm32-rep1-x3'])), ('Greedy', avg(['mixR-greedy-rep1-x3'])), ('v1', avg(['mixR-online-rep1-x3'])), ('v3', avg(['mixR-onlinev3-rep1-x3']))]
p(f'v4 = {w(v4, nv)}\n\n| 비교 대상 | WAF | v4 − 비교 대상 |\n|---|---:|---:|')
for lab, (b, n) in rows: p(f'| {lab} | {w(b, n)} | {pct(v4, b)} |')

# ---- 5. summary
p('\n## 5. 요약 (2026-10-01 기준, 위 표가 갱신되면 다시 확인)\n')
p('| 비교 대상 | 결과 |\n|---|---|')
p('| 기본 CAT (원저자 기본값) | **v4가 모든 경우에 좋음.** 단일 워크로드 1시간 −5.2%, 10시간 −8.4%. 전환 워크로드 4/4 (−4.3 ~ −18.3%), 3구간 전환 −13.7% |')
p('| 견고 CAT (원저자 워크로드 기준) | 전환 워크로드 4/13에서 v4가 좋음(−1.1 ~ −5.3%, 견고 CAT이 맞지 않는 구간이 있는 경우), 9/13에서 나쁨(+3.2 ~ +11.5%). 단일 워크로드 10시간 −0.2%, 3구간 전환 +0.3%로 비슷 |')
p('| 최적 CAT (47번) | 전환 워크로드 3/6에서 v4가 좋음(거래 DB → 메일 −2.7%, SQLite 수정 → 읽기 −3.4%, SQLite → 거래 DB −0.7%), 나머지는 나쁨(최대 +15.2%). 단일 워크로드 10시간 +2.0% |')
p('| 워크로드별 1등 고정 조합 | 워크로드 하나가 계속되면 원리상 넘을 수 없음. 전환 워크로드 4종 중 1종(거래 DB → 메일, −2.7%)에서 v4가 1등 |')
p('| Greedy, v1 | v4가 모든 경우에 좋음 (Greedy 대비 −17 ~ −34%, v1 대비 −2.5 ~ −9.1%) |')
Path('/home/oy/iCAT/V4_VS_CAT.md').write_text('\n'.join(o) + '\n'); print('\n'.join(o))
