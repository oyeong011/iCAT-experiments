#!/usr/bin/env python3
"""E1 원고 반영 제안서 (고컴, 2026-11-24). 원고를 수정하지 않는다.
Reads report/final-e1-validation/tables/table8_e1.md (made by table8_e1.py from validity-gated E1 runs only) and lists,
for each manuscript location, the current text and the proposed replacement. Numbers come only from table8_e1.md.
Output: report/final-e1-validation/e1_insert_proposal.md"""
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
t8 = (ROOT / 'report/final-e1-validation/tables/table8_e1.md').read_text() if (ROOT / 'report/final-e1-validation/tables/table8_e1.md').exists() else ''
ms = (ROOT / 'PAPER_KCI_DRAFT.md').read_text().split('\n')
ready = t8.startswith('**표 8 (재설계).**')


def where(prefix):
    return next((i + 1 for i, l in enumerate(ms) if l.startswith(prefix) or prefix in l), None)


rows = [
    ('6.2절 표 8 본문', where('**표 8.**'), '"대기" 칸 3행', '`tables/table8_e1.md`의 표와 Welch 보조 표로 교체'),
    ('6.2절 그림 10', where('**그림 10.**'), '캡션만 있음', '캡션 위에 `![그림 10](report/final-e1-validation/figs/paper/paper_fig10_e1_three_phase.png)` 추가'),
    ('6.2절 3단계 균등 전환 문단 끝', where('**3단계 균등 전환.**'), '실험 설계만 기술', '결과 문장 추가 (아래 초안, 수치는 표 8에서 자동)'),
    ('7장 "개선의 핵심"', where('**개선의 핵심.**'), '"…재측정 중이다(6.2절)"', 'E1 결과에 따라 "효과가 있었다/구분되지 않았다(표 8)"로 교체'),
    ('8장 한계 2', where('2. iCAT-v3와 iCAT-v4는 FIO-Fast와 3단계'), '설계 근거가 무효로 판정되었다는 문구', '유지 (재측정은 설계 이후의 확인 실험임을 명시)'),
    ('8장 한계 7', where('7. YCSB를 포함한 전환 워크로드 일부'), '"3단계 균등 전환은 레코드 수를 줄여 재측정 중이다"', '"…30만 레코드로 재측정하였다(표 8). 고정 조합은 재측정하지 않았다"'),
    ('부록 B 그림 10 행', where('| 그림 10 |'), '생성 대기', '"완성 (E1 n=3)"'),
]
L = ['# E1 결과 원고 반영 제안서 (자동 생성, 원고 미수정)', '',
     f'- 상태: **{"반영 가능 (세 정책 모두 유효 3회)" if ready else "대기 — 표 8 조건 미충족, 수치 없음"}**',
     '- 수치 출처: `report/final-e1-validation/tables/table8_e1.md` (`analysis/final_e1/table8_e1.py`). 다른 출처의 수치나 추정값은 쓰지 않는다.', '',
     '| 위치 | 원고 줄 | 현재 | 제안 |', '|---|---:|---|---|'] + [f'| {a} | {b} | {c} | {d} |' for a, b, c, d in rows]
if ready:
    comp = re.findall(r'^\| (NoDrift|FullReset) − iCAT-v4 \| ([^|]+) \| ([^|]+) \| ([^|]*) \|', t8, re.M)   # table rows already use U+2212
    L += ['', '## 결과 문장 초안 (저자 검토 필요)', '']
    for name, c3, tot, sig in comp:
        what = '변화 감지를 제거하면' if name == 'NoDrift' else '재설정 시 45개 전체를 복원하면'
        verdict = ('95% CI가 0을 포함하지 않았다' if '단계 3' in sig else '95% CI가 0을 포함하여 차이를 확인하지 못했다')
        L.append(f'- {what} 단계 3 WAF 차이는 {c3.strip()}, 전체 WAF 차이는 {tot.strip()}였다(각 3회, Welch). 단계 3 차이의 {verdict}.')
    L += ['', '## 표 8 (원고에 들어갈 내용)', '', t8]
else:
    L += ['', '표 8 조건이 충족되지 않아 결과 문장 초안과 수치를 만들지 않았다.', '', t8]
(ROOT / 'report/final-e1-validation/e1_insert_proposal.md').write_text('\n'.join(L) + '\n')
print('e1_insert_proposal:', 'READY' if ready else 'WAIT')
