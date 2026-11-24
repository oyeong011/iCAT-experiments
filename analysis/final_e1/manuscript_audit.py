#!/usr/bin/env python3
"""Manuscript consistency audit (GoCom, 2026-11-24): figure/table numbering, captions, image links, in-text references,
unit and statistics notation. Read-only on the manuscript; writes report/final-e1-validation/manuscript_audit.md.
    python3 -I analysis/final_e1/manuscript_audit.py [PAPER_KCI_DRAFT.md]"""
import re, sys, collections
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
fn = ROOT / (sys.argv[1] if len(sys.argv) > 1 else 'PAPER_KCI_DRAFT.md')
L = fn.read_text().split('\n')
body_end = next((i for i, l in enumerate(L) if l.startswith('### 부록 B')), len(L))   # appendix B is a maintenance table
issues, notes = [], []

cap = collections.defaultdict(list)   # ('표'|'그림', id) -> caption line numbers
for i, l in enumerate(L[:body_end], 1):
    m = re.match(r'^\*\*(표|그림) ([0-9]+|A[0-9]+)\.\*\*', l)
    if m: cap[(m[1], m[2])].append(i)
imgs = [(i, m[1], m[2]) for i, l in enumerate(L[:body_end], 1) for m in [re.match(r'^!\[그림 (\d+)\]\(([^)]+)\)', l)] if m]

# 1. numbering: consecutive, unique, caption order
for kind in ('표', '그림'):
    nums = sorted(int(k[1]) for k in cap if k[0] == kind and k[1].isdigit())
    exp = list(range(1, max(nums) + 1)) if nums else []
    if nums != exp: issues.append(f'{kind} 번호가 연속이 아님: 있음 {nums}, 없음 {sorted(set(exp) - set(nums))}')
    for k, v in cap.items():
        if k[0] == kind and len(v) > 1: issues.append(f'{kind} {k[1]} 캡션이 {len(v)}개 (줄 {v})')
    order = [int(k[1]) for k, v in sorted(cap.items(), key=lambda kv: kv[1][0]) if k[0] == kind and k[1].isdigit()]
    if order != sorted(order): issues.append(f'{kind} 캡션 등장 순서가 번호 순서와 다름: {order}')

# 2. images: number matches the next caption, file exists, file name carries the same paper number
for i, n, path in imgs:
    nxt = next(((k, ln) for k, v in cap.items() for ln in v if k[0] == '그림' and ln > i), None)
    nxt = min(((k, ln) for k, v in cap.items() for ln in v if k[0] == '그림' and ln > i), key=lambda x: x[1], default=None)
    if not nxt or nxt[0][1] != n: issues.append(f'줄 {i}: 그림 {n} 이미지 다음 캡션 번호가 다름 ({nxt})')
    if not (ROOT / path).exists(): issues.append(f'줄 {i}: 그림 {n} 파일 없음: {path}')
    m = re.search(r'paper_fig(\d\d)_', path)
    if not m or int(m[1]) != int(n): issues.append(f'줄 {i}: 그림 {n} 파일명 번호 불일치: {path}')
figcaps = {k[1] for k in cap if k[0] == '그림'}
for n in sorted(figcaps, key=int):
    if not any(x[1] == n for x in imgs):
        notes.append(f'그림 {n}: 이미지 링크 없음 (캡션만 있음)')

# 3. in-text references: target exists; first reference before or near the caption
refs = collections.defaultdict(list)
for i, l in enumerate(L[:body_end], 1):
    if l.startswith('![') or re.match(r'^\*\*(표|그림) ', l): continue
    for m in re.finditer(r'(표|그림) ?([0-9]+|A[0-9]+)(?![0-9])', l):
        refs[(m[1], m[2])].append(i)
for k, v in sorted(refs.items()):
    if k not in cap: issues.append(f'{k[0]} {k[1]} 참조(줄 {v[:5]})의 캡션이 없음')
for k, v in cap.items():
    if k not in refs: notes.append(f'{k[0]} {k[1]}: 본문 참조 없음 (캡션 줄 {v[0]})')
    elif min(refs[k]) > v[0] + 40: notes.append(f'{k[0]} {k[1]}: 첫 본문 참조(줄 {min(refs[k])})가 캡션(줄 {v[0]})보다 40줄 넘게 뒤')

# 4. units and statistics notation (counts; mixed styles are reported, not rewritten)
txt = '\n'.join(L[:body_end])
pat = {'백분율 붙여쓰기 "5%"': r'\d%', '백분율 띄어쓰기 "5 %"': r'\d %(?!p)', '%p': r'%p',
       '"n=3"': r'\bn=\d', '"n = 3"': r'\bn = \d', '"±"': '±', '"95% CI"': r'95% ?CI', '"95 % CI"': r'95 % CI',
       'MiB': r'\bMiB\b', 'MB': r'\bMB\b', 'GiB': r'\bGiB\b', 'GB': r'\bGB\b',
       '"초"(시간)': r'\d+초', '" s"(시간)': r'\d+ s\b', '"분"': r'\d+분', '"시간"': r'\d+(\.\d+)?시간',
       '음수 "−"(U+2212)': '−', '음수 "-"(하이픈+숫자)': r'(?<![\w.])-\d'}
cnt = {k: len(re.findall(v, txt)) for k, v in pat.items()}
mix = []
if cnt['백분율 붙여쓰기 "5%"'] and cnt['백분율 띄어쓰기 "5 %"']: mix.append('백분율 띄어쓰기 혼용')
if cnt['"n=3"'] and cnt['"n = 3"']: mix.append('n 표기 혼용')
if cnt['"95% CI"'] and cnt['"95 % CI"']: mix.append('CI 표기 혼용')
if cnt['MiB'] and cnt['MB']: mix.append('MiB/MB 혼용 (용량 단위: 의도 확인 필요)')
if cnt['"초"(시간)'] and cnt['" s"(시간)']: mix.append('초/s 혼용')
if cnt['음수 "−"(U+2212)'] and cnt['음수 "-"(하이픈+숫자)']: mix.append('음수 기호 혼용(− 와 -)')
lines_mix = {}
for key, rx in (('백분율 띄어쓰기', r'\d %(?!p)'), ('음수 하이픈', r'(?<![\w.])-\d'), ('" s"', r'\d+ s\b'), ('MB', r'\bMB\b')):
    lines_mix[key] = [i for i, l in enumerate(L[:body_end], 1) if re.search(rx, l)][:12]

out = [f'# 원고 점검: `{fn.name}` (자동 생성, `analysis/final_e1/manuscript_audit.py`)', '',
       f'- 캡션: 표 {sorted((k[1] for k in cap if k[0] == "표"), key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else x))}, 그림 {sorted((k[1] for k in cap if k[0] == "그림"), key=int)}',
       f'- 이미지 링크: {len(imgs)}개', '', '## 문제 (수정 필요)', ''] + ([f'- {x}' for x in issues] or ['- 없음']) + [
       '', '## 참고', ''] + ([f'- {x}' for x in notes] or ['- 없음']) + [
       '', '## 단위·통계 표기 (본문, 부록 B 제외)', '', '| 표기 | 개수 |', '|---|---:|'] + [f'| {k} | {v} |' for k, v in cnt.items()] + [
       '', '혼용: ' + (', '.join(mix) or '없음'), ''] + [f'- {k} 줄: {v}' for k, v in lines_mix.items() if v]
o = ROOT / 'report/final-e1-validation/manuscript_audit.md'; o.write_text('\n'.join(out) + '\n'); print('\n'.join(out))
