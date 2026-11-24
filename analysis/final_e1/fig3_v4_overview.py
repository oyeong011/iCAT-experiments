#!/usr/bin/env python3
"""그림 3. iCAT-v4 동작 개요 (GoCom, 2026-11-24).
Every box restates code in online-v4-src (conv_ftl.c md5 5737f84f…, conv_ftl.h md5 a8360a9b…); line numbers in brackets.
Nothing outside that code is drawn. Output: report/final-e1-validation/figs/paper/paper_fig03_v4_overview.{png,pdf,svg}"""
from pathlib import Path
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[2]; OUT = ROOT / 'report/final-e1-validation/figs/paper'; OUT.mkdir(parents=True, exist_ok=True)
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family': 'Noto Sans CJK JP', 'font.size': 9})
INK, INK2 = '#1d1d1f', '#52514e'
C = {'measure': '#8e8e93', 'search': '#eda100', 'elim': '#1baf7a', 'settle': '#2a78d6', 'drift': '#e34948'}

fig, ax = plt.subplots(figsize=(13, 7.4)); ax.set_xlim(0, 130); ax.set_ylim(0, 74); ax.axis('off')


def box(x, y, w, h, title, body, cat, ref):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.4,rounding_size=1.2', fc='white', ec=C[cat], lw=2))
    ax.add_patch(FancyBboxPatch((x, y + h - 4.2), w, 4.2, boxstyle='round,pad=0.4,rounding_size=1.2', fc=C[cat], ec=C[cat], lw=0))
    ax.text(x + 1, y + h - 2.1, title, color='white', fontsize=9.5, weight='bold', va='center')
    ax.text(x + 1, y + h - 5.6, body, color=INK, fontsize=8.3, va='top', linespacing=1.45)
    ax.text(x + w - 0.6, y + 0.9, ref, color=INK2, fontsize=7, ha='right', va='bottom')


def arrow(x1, y1, x2, y2, text='', col=INK2, rad=0.0, tx=None, ty=None):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>', mutation_scale=11, color=col, lw=1.4,
                                 connectionstyle=f'arc3,rad={rad}'))
    if text:
        ax.text(tx if tx is not None else (x1 + x2) / 2, ty if ty is not None else (y1 + y2) / 2, text, fontsize=7.8, color=col,
                ha='center', va='center', bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none'))


# row 1: measurement pipeline (per partition, driven by GC completions)
box(1, 58, 24, 13, '측정 ① 워밍업', '파티션마다 GC 100회 동안\n학습하지 않음', 'measure', 'c:649')
box(28, 58, 28, 13, '측정 ② 번인 (조합 변경 직후)', 'GC 32회 + 호스트 128 MiB가\n지날 때까지 표본에서 제외', 'measure', 'c:660, h:41–42')
box(59, 58, 42, 13, '측정 ③ 판단 구간', 'GC 128회 이상 + 호스트 512 MiB 이상\n표본 WAF = 1 + GC 쓰기 / 호스트 쓰기\nGC 8,192회 또는 300 s 안에 못 채우면 폐기', 'measure', 'c:663–676, h:43–47')
box(104, 58, 25, 13, '시작 상태', '후보 45개 (60개 중 k=2인\narm 0–14 제외)\n첫 조합 arm 37', 'measure', 'h:33, h:35, c:630')
arrow(25.5, 64.5, 27.5, 64.5); arrow(56.5, 64.5, 58.5, 64.5)

# row 2: per-window update, in code order
box(1, 30, 30, 23, '변화 감지 (정착 상태, 최상위 사용 중)', '표본 WAF가 정착 시 기준 WAF와\n25 % 넘게 다른 구간이\n3구간 연속이면 → 재설정\n\n재설정: 통계 초기화,\n후보 = 남은 후보 + 1단계 이웃,\n정착 해제', 'drift', 'c:534–545, 448–470, h:58–59')
box(35, 30, 27, 23, '관측 누적', '모든 조합의 누적값에\n할인 γ = 0.99950 / 구간\n(반감기 약 1,376 구간)\n후 이번 조합에 표본 추가', 'measure', 'c:548–565, h:50')
box(66, 30, 30, 23, '최상위 갱신 · 정착 판정', '평균 WAF가 가장 낮은 후보 = 최상위\n(현 최상위보다 0.5 % 이내 개선이면 유지)\n\n정착: 모든 후보 1회 이상 사용\n+ 최상위 12구간 유지\n+ 최상위로 3회 확인', 'settle', 'c:472–520, h:53–55')
box(100, 30, 29, 23, '후보 제거', '모든 후보를 1회 이상 쓴 뒤,\n평균 WAF가 최상위보다\n15 % 넘게 높은 후보를 제외\n(최상위·현재 조합은 제외 안 함)', 'elim', 'c:581–598, h:34')
arrow(31.5, 41.5, 34.5, 41.5); arrow(62.5, 41.5, 65.5, 41.5); arrow(96.5, 41.5, 99.5, 41.5)
arrow(80, 57.4, 16, 53.8, '판단 구간마다 (파티션별)', tx=48, ty=55.6)

# row 3: next-arm choice
ax.text(114.5, 26.6, '정착 상태?', fontsize=8.5, color=INK, ha='center', va='center', bbox=dict(boxstyle='round,pad=0.35', fc='#f3f3f1', ec=INK2, lw=1))
arrow(114.5, 29.6, 114.5, 27.9)
box(1, 2, 56, 19, '다음 조합: 탐색 (정착 전)', '1) 아직 쓰지 않은 후보 (첫 순회)\n2) 240구간 이상 쓰지 않은 후보\n3) 할인 UCB: 평균 WAF − 0.25·√(2 ln N / n)이 가장 작은 후보\n   (N, n = 할인된 전체·조합별 관측 수)', 'search', 'c:398–445, h:51, h:57')
box(61, 2, 68, 19, '다음 조합: 정착 후', '최상위 조합을 계속 사용\n최상위 사용 8구간마다 이웃 탐침 1회: 최상위와 k · 임계배율 · 나이비율 중\n하나만 한 단계 다른 조합을 후보로 되돌리고 1구간 사용 (제거된 조합도 다시 후보)', 'settle', 'c:599–618, 147–161, h:56')
arrow(108.5, 26.6, 40, 21.4, '아니오', rad=0.04, tx=75, ty=24.6)
arrow(114.5, 25.3, 114.5, 21.4, '예', tx=117, ty=23.3)
arrow(16, 29.6, 16, 21.4, '재설정 후 다시 탐색', col=C['drift'], tx=16, ty=25.5)
ax.text(65, 4.3, '→ 고른 조합이 바뀌면 ② 번인부터, 같으면 ③ 다음 판단 구간 (c:702–706)', fontsize=7.8, color=INK2, va='center')
ax.text(4, 4.3, '→ 고른 조합이 바뀌면 ② 번인부터, 같으면 ③ 다음 판단 구간 (c:702–706)', fontsize=7.8, color=INK2, va='center')

ax.text(0.5, 73.6, '그림 3. iCAT-v4 동작 개요: 측정 → (변화 감지) → 관측 누적 → 최상위 갱신·정착 → 후보 제거 → 다음 조합 선택. 모든 상태는 FTL 파티션(4개)마다 독립',
        fontsize=10.5, color=INK, va='top')
for i, (k, lab) in enumerate([('search', '탐색'), ('elim', '후보 제거'), ('settle', '정착·이웃 탐침'), ('drift', '변화 감지·재설정'), ('measure', '측정·누적')]):
    ax.add_patch(FancyBboxPatch((58 + i * 14.5, -1.6), 1.6, 1.2, boxstyle='square,pad=0', fc=C[k], ec='none', clip_on=False))
    ax.text(60.2 + i * 14.5, -1.0, lab, fontsize=7.8, color=INK2, va='center')
ax.text(0.5, -1.0, '괄호 안: online-v4-src 근거 (c: conv_ftl.c 줄, h: conv_ftl.h 줄)', fontsize=7.5, color=INK2, va='center')
for e in ('png', 'pdf', 'svg'):
    fig.savefig(OUT / f'paper_fig03_v4_overview.{e}', dpi=200, bbox_inches='tight')
print('wrote', OUT / 'paper_fig03_v4_overview.png')
