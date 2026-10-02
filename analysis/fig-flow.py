#!/usr/bin/env python3
"""그림: iCAT-v4 후보 제거·정착·이웃 탐침 흐름도 + 47번/22번 이웃 예시 -> figs/fig11_v4_flow.(png|pdf)
상수는 online-v4-src/conv_ftl.h, 예시 수치는 FIO-Fast 10시간 실행(t4-onlinev4-rep1-x60) 파티션 0의 커널 로그."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, Rectangle
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
SURF, INK, INK2, GRID, V4 = '#fcfcfb', '#0b0b0b', '#52514e', '#e4e3df', '#2a78d6'
plt.rcParams.update({'font.family': 'Noto Sans CJK JP', 'font.size': 9.5, 'figure.facecolor': SURF})
fig = plt.figure(figsize=(13, 7.0))
ax = fig.add_axes([0.01, 0.0, 0.56, 0.92]); ax.set_xlim(0, 10); ax.set_ylim(2.2, 10); ax.axis('off')
def box(x, y, w, h, title, body, ex=None, lw=2.6):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.12', fc='white', ec=INK, lw=lw))
    ax.text(x + 0.15, y + h - 0.16, title, va='top', fontsize=10.5, weight='bold', color=INK)
    ax.text(x + 0.15, y + h - 0.55, body, va='top', fontsize=8.6, color=INK2, linespacing=1.45)
    if ex: ax.text(x + w - 0.12, y + 0.1, ex, va='bottom', ha='right', fontsize=8, color=V4, linespacing=1.35)
def arrow(x1, y1, x2, y2, label=None, rad=0):
    ax.annotate('', (x2, y2), (x1, y1), arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.6, connectionstyle=f'arc3,rad={rad}'))
    if label: ax.text((x1 + x2) / 2 + 0.08, (y1 + y2) / 2, label, fontsize=8, color=INK2, va='center')
W = 4.6
box(0.2, 8.55, W, 1.3, '① 시작', '후보 45개 (k=2인 0~14번 제외)\n첫 조합 37번 (k=7, 100%, 7)')
box(0.2, 6.75, W, 1.5, '② 전수 순회', '후보마다 1창씩 측정 (방문 수 최소 우선)\n창 = GC 128회 이상 & 호스트 쓰기 512 MiB 이상\n조합 교체 직후 1창은 버림(번인)', '예: 창 1~45')
box(0.2, 4.75, W, 1.7, '③ 후보 제거 (매 창)', '조건: 모든 후보 1회 이상 측정됨\n최선 평균 WAF보다 15% 넘게 나쁘면 제외\n(현재 사용 중·최선 조합은 제외 안 함)\n할인 평균 γ=0.9995', '예: 창 45에서 45개 → 20개')
box(0.2, 2.75, W, 1.7, '④ 탐색 (UCB)', '남은 후보 중 (평균 WAF − 보너스) 최소 선택\n보너스 = 0.25·√(2 ln N / n_i)\n240창 동안 안 본 후보는 강제 재측정', '예: 창 46~73')
box(5.2, 2.75, W, 1.7, '⑤ 정착 판정', '최선 조합이 12창 연속 유지\n+ 최선 조합 직접 사용 3회\n최선 교체는 0.5% 넘게 좋을 때만\n(교체되면 정착 해제 → ④로)', '예: 창 74 정착(31번)\n→ 창 76 해제')
box(5.2, 4.75, W, 1.7, '⑥ 활용 + 이웃 탐침', '최선 조합 계속 사용\n8창마다 이웃 1개 시험\n(k·s·r 중 하나만 한 칸 이동)\n시험한 이웃은 후보로 복귀', '예: 창 330 최종 정착(46번)\n이후 46번 사용 78%')
box(5.2, 6.75, W, 1.5, '⑦ 변화 감지', '최선 조합의 창 WAF가 정착 기준값과\n25% 넘게 다른 창이 3회 연속', '예: 이 실행에서는 0회')
box(5.2, 8.55, W, 1.3, '⑧ 부분 재설정', '측정 기록 초기화\n후보 = 생존 후보 + 그 이웃 → ②로')
arrow(2.5, 8.55, 2.5, 8.25); arrow(2.5, 6.75, 2.5, 6.45); arrow(2.5, 4.75, 2.5, 4.45)
arrow(4.8, 3.6, 5.2, 3.6, ''); ax.text(4.83, 3.75, '', fontsize=8)
arrow(6.4, 4.45, 6.4, 4.75); ax.text(6.5, 4.58, '조건 충족', fontsize=8, color=INK2, va='center')
arrow(8.4, 4.75, 8.4, 4.45, rad=0); ax.text(8.5, 4.58, '최선 교체', fontsize=8, color=INK2, va='center')
arrow(7.5, 6.45, 7.5, 6.75); arrow(7.5, 8.25, 7.5, 8.55); ax.text(7.6, 8.4, '감지', fontsize=8, color=INK2, va='center')
arrow(5.2, 9.2, 4.8, 7.5, rad=0.25)
ax.text(5.6, 2.45, '③ 후보 제거는 ④·⑥ 상태에서도 매 창 적용', fontsize=8, color=INK2)
ax.set_title('그림 11. iCAT-v4의 후보 제거·정착·이웃 탐침 과정 (상수: conv_ftl.h, 예시: FIO-Fast 10시간 실행 파티션 0)', loc='left', fontsize=10.5, color=INK)
# right: neighbour grid
bx = fig.add_axes([0.6, 0.08, 0.39, 0.62]); bx.set_xlim(-0.6, 15.6); bx.set_ylim(-1.6, 6.2); bx.axis('off'); bx.set_aspect('equal')
ks, sc, ra = [2, 4, 7, 10], [25, 50, 100, 200, 400], [4, 7, 16]
hl = {47: ('기준', INK), 32: ('이웃', V4), 46: ('이웃', V4), 50: ('이웃', V4), 22: ('기준', INK), 19: ('이웃', V4), 21: ('이웃', V4), 23: ('이웃', V4), 25: ('이웃', V4), 37: ('이웃', V4), 7: ('제외', INK2)}
for ki, k in enumerate(ks):
    ox = ki * 4
    bx.text(ox + 1.5, 5.75, f'k = {k}' + (' (후보 아님)' if k == 2 else ''), ha='center', fontsize=9, color=INK)
    for si in range(5):
        for ri in range(3):
            a = (ki * 5 + si) * 3 + ri; y = 4 - si
            role = hl.get(a, (None, None))[0]
            fc = '#efeeea' if k == 2 else ('white' if role is None else ('#dbe8f8' if role == '이웃' else '#ffffff'))
            lw = 2.6 if role == '기준' else (1.8 if role == '이웃' else 0.6)
            ec = INK if role == '기준' else (V4 if role == '이웃' else '#b9b8b3')
            bx.add_patch(Rectangle((ox + ri, y), 0.92, 0.92, fc=fc, ec=ec, lw=lw, ls='--' if a == 7 else '-'))
            bx.text(ox + ri + 0.46, y + 0.46, a, ha='center', va='center', fontsize=8, color=INK if k != 2 else '#9a9994', weight='bold' if role == '기준' else 'normal')
    for ri in range(3): bx.text(ox + ri + 0.46, -0.35, ra[ri], ha='center', fontsize=7.5, color=INK2)
for si in range(5): bx.text(-0.15, 4 - si + 0.46, f'{sc[si]}%', ha='right', va='center', fontsize=7.5, color=INK2)
bx.text(7.5, -0.95, '가로: 나이 비율 r (4·7·16)   세로: 임계 배율 s   조합 번호 = 15·k단계 + 3·s단계 + r단계', ha='center', fontsize=7.8, color=INK2)
fig.text(0.6, 0.83, '이웃 = k·s·r 중 하나만 한 칸 이동 (최대 6개)', fontsize=10, weight='bold', color=INK)
fig.text(0.6, 0.805, '47번 (10, 25%, 16) → 이웃 32·46·50 (격자 끝이라 3개)\n22번 (4, 100%, 7) → 이웃 19·21·23·25·37 (k=2 쪽 7번은 후보가 아니라 제외)', fontsize=8.6, color=INK2, va='top', linespacing=1.6)
for ext in ('png', 'pdf'): fig.savefig(f'/home/oy/iCAT/figs/fig11_v4_flow.{ext}', dpi=170, bbox_inches='tight', pad_inches=0.15)
