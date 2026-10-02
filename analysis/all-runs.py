#!/usr/bin/env python3
"""Every measured run, one row each -> ALL_RUNS.csv (Excel) and ALL_RUNS.md.  python3 analysis/all-runs.py"""
import re, csv, datetime
from pathlib import Path
R = Path('/home/oy/iCAT/result')
WL = {'t4': '빠른 3영역', 't4long': '빠른 3영역', 'main': '빠른 3영역 → SQLite (초기 설계)', 'long': '빠른 3영역 → SQLite (초기 설계, 긴)', 'smoke': '시험 실행',
      'mixA': '빠른 3영역 → SQLite', 'mixB': 'SQLite → 빠른 3영역', 'mixC': '느린 → 빠른 3영역', 'mixD': '빠른 → 느린 3영역',
      'mixF': '빠른 3영역 → 메일 서버', 'mixG': '빠른 3영역 + SQLite 동시', 'mixH': '느린 → 빠른 → SQLite', 'mixJ': 'SQLite 수정 많음 → 읽기 위주',
      'mixK': '뜨거운 구역 512 → 128 MB', 'mixL': '빠른 ↔ 느린 60초 × 5', 'mixM': '초당 1만 → 5만 서서히', 'mixO': '거래 DB 흉내 → 메일 서버',
      'mixP': 'SQLite → 거래 DB 흉내', 'mixQ': '빠른 → 5분 쉼 → 빠른', 'mixR': '빠른 3영역 → SQLite → 빠른 3영역 (쓰기량 균등)'}
POL = {'greedy': 'Greedy', 'online': 'iCAT v1', 'onlinev2': 'iCAT v2', 'onlinev3': 'iCAT v3', 'onlinev4': 'iCAT v4',
       'onlinev3k2': 'v3 + k=2 되돌림', 'onlinev3probe': 'v3 + 탐색 되돌림', 'fixed10': '고정 10번 (최악)', 'fixed37': '고정 37번 (기본)',
       'fixed47': '고정 47번 (최적)', 'fixed50': '고정 50번 (견고)'}
def pol(p):
    m = re.fullmatch(r'arm(\d\d)', p)
    return f'고정 {int(m[1])}번' if m else POL.get(p, p)
rows = []
# explicit-window runs (mix-20260911 runner)
for f in sorted((R / 'mix-20260911').glob('*/summary.txt')):
    d = f.parent.name
    m = re.fullmatch(r'(t4long|t4|mix[A-Z]|main|long|smoke)-(.+?)(?:-rep(\d))?(-x\d+)?(-smoke)?(-\w*broken)?', d)
    if not m: continue
    s = f.read_text()
    tot = re.search(r'^total .*WAF=([\d.]+)', s, re.M)
    if not tot: continue
    ph = dict(re.findall(r'^phase([ABC])\(\S*\) host_pages=\d+ gc_pages=\d+ WAF=([\d.]+)', s, re.M))
    status = '정상'
    if m[6]: status = '무효 (' + m[6].strip('-') + ')'
    elif m[5] or m[1] == 'smoke': status = '시험 실행'
    elif (f.parent / 'SUSPECT.txt').exists(): status = '의심 (도구 손상 직후)'
    rows.append({'측정 방식': '명시 계측', '워크로드': WL.get(m[1], m[1]), '정책': pol(m[2]), '길이': {'t4long': '6배 (1시간)', 'long': '6배'}.get(m[1], (m[4] or '-x1').strip('-').replace('x', '') + '배'),
                 '반복': m[3] or '1', 'WAF 전체': tot[1], **{f'구간 {k}': f"{float(ph[k]):.3f}" if k in ph else '' for k in 'ABC'}, '상태': status, '폴더': f'result/mix-20260911/{d}'})
# original-author-method sweeps (one WAF per run)
GC = re.compile(r'GC stats: .*?host_pages=(\d+) gc_pages=(\d+)')
def gh(console):
    t = console.read_text(errors='replace')
    w = re.search(r'^\[WAF\] module=\S+ WAF=([\d.]+)', t, re.M)
    if w: return w[1]
    r = re.search(r'^\[RESULT\] (\S+)', t, re.M)
    if r and Path(r[1]).exists():
        g = GC.findall(Path(r[1]).read_text(errors='replace'))
        if g: return f'{1 + int(g[-1][1]) / int(g[-1][0]):.4f}'
    return None
for pat, wl in [('sweep-20260915/test4-*.console.txt', '빠른 3영역'), ('sweep-slow16-20260921/slow16-*.console.txt', '아주 느린 3영역'),
                ('sweep-varmail-20260928/varmail-*.console.txt', '메일 서버 (15만 파일)'), ('sqlite/a-arm*.console.txt', 'SQLite 읽기50/수정50'),
                ('filebench/oltp-arm*.console.txt', '거래 DB 흉내')]:
    for c in sorted(R.glob(pat)):
        m = re.search(r'(arm\d\d|gh-greedy)(?:-rep(\d))?', c.name)
        if not m or (w := gh(c)) is None: continue
        rows.append({'측정 방식': '원저자 방식', '워크로드': wl, '정책': pol(m[1]) if m[1] != 'gh-greedy' else 'Greedy', '길이': '1배', '반복': m[2] or '1',
                     'WAF 전체': w, '구간 A': '', '구간 B': '', '구간 C': '', '상태': '정상', '폴더': str(c.relative_to(R.parent))})
cols = list(rows[0])
with open('/home/oy/iCAT/ALL_RUNS.csv', 'w', newline='', encoding='utf-8-sig') as fh:
    wr = csv.DictWriter(fh, cols); wr.writeheader(); wr.writerows(rows)
md = [f'# 모든 측정값 ({len(rows)}개 실행)\n', f'> `python3 analysis/all-runs.py`로 원본 결과 폴더에서 자동 생성 ({datetime.datetime.now():%Y-%m-%d %H:%M}). '
      '엑셀용은 `ALL_RUNS.csv`. WAF는 낮을수록 좋다. 길이는 기본 길이 대비 배수(빠른 3영역 1배 = 10분). '
      '명시 계측과 원저자 방식은 같은 조합에서 1.5~3% 차이가 나므로 섞어 비교하지 않는다.\n']
for wl in dict.fromkeys(r['워크로드'] for r in rows):
    sub = sorted([r for r in rows if r['워크로드'] == wl], key=lambda r: (r['측정 방식'], r['길이'], float(r['WAF 전체'])))
    md.append(f'\n## {wl} ({len(sub)}개)\n\n| 측정 방식 | 길이 | 정책 | 반복 | WAF 전체 | 구간 A | 구간 B | 구간 C | 상태 |\n|---|---|---|---|---:|---:|---:|---:|---|')
    for r in sub: md.append(f"| {r['측정 방식']} | {r['길이']} | {r['정책']} | {r['반복']} | {float(r['WAF 전체']):.3f} | {r['구간 A']} | {r['구간 B']} | {r['구간 C']} | {r['상태']} |")
Path('/home/oy/iCAT/ALL_RUNS.md').write_text('\n'.join(md) + '\n')
print(len(rows), 'runs')
