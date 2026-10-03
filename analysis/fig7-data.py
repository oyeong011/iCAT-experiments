#!/usr/bin/env python3
"""그림 7 데이터: v4 학습기의 판단 구간별 기록 -> figs/data/fig7_v4_trace.csv
원천: 각 실행의 kernel-snapshots/*.log + kernel*.log (BEGIN 표식 뒤, 중복 제거; analysis/v4-log.py)
경과(분)은 측정 시작(Measurement: command=start) 기준 = fig14_30s.csv와 같은 시간축."""
import re, csv, importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location('v4log', '/home/oy/iCAT/analysis/v4-log.py'); v4log = importlib.util.module_from_spec(spec); spec.loader.exec_module(v4log)
M = Path('/home/oy/iCAT/result/mix-20260911')
K, S, R = [2, 4, 7, 10], [25, 50, 100, 200, 400], [4, 7, 16]
dec = lambda a: (K[a // 15], S[(a // 3) % 5], R[a % 3])
RUNS = [('mixO-onlinev4-rep1-x3', 'OLTP → Varmail', 'OLTP', 'Varmail'), ('mixF-onlinev4-rep1-x3', 'FIO-Fast → Varmail', 'FIO-Fast', 'Varmail'),
        ('mixJ-onlinev4-rep1-x3', 'YCSB-A → YCSB-B', 'YCSB-A', 'YCSB-B'), ('mixP-onlinev4-rep1-x3', 'YCSB-A → OLTP', 'YCSB-A', 'OLTP'),
        # runs where the change detector fired and the learner re-explored (10-03)
        ('mixF-onlinev4-rep2-x3', 'FIO-Fast → Varmail (2회차)', 'FIO-Fast', 'Varmail'), ('mixR-onlinev4-rep1-x3', 'FIO-Fast → YCSB-A → FIO-Fast', 'FIO-Fast', 'YCSB-A')]
ts = lambda l: float(re.match(r'\[\s*(\d+\.\d+)\]', l)[1])
with open('/home/oy/iCAT/figs/data/fig7_v4_trace.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['워크로드', '파티션', '세대(재설정마다 +1)', '판단구간 번호', '경과(분)', '구간', '이번 구간에 쓴 조합', 'k', '임계배율(%)', '나이비율', '구간 WAF',
                '추정 최선 조합', '다음 조합', '정착(1=예)', '남은 후보 수', '사건'])
    for d, wl, a, b in RUNS:
        L = v4log.lines(str(M / d)); t0 = next(ts(l) for l in L if 'Measurement: command=start' in l)
        PH = [(ts(l), l.split('phase=')[1][0]) for l in L if 'phase=' in l and ' START' in l]; prev = {}
        NAME = {'A': a, 'B': b, 'C': a}   # 3-phase run: C repeats A's workload
        for l in L:
            if 'WATGC_V2 reset' in l:
                w.writerow([wl, re.search(r'part=(\d)', l)[1], '', re.search(r'window=(\d+)', l)[1], round((ts(l) - t0) / 60, 2)] + [''] * 10 + ['재설정(변화 감지)']); continue
            m = re.search(r'part=(\d) epoch=(\d+) window=(\d+) .*?evaluated=(\d+) .*?waf_q16=(\d+) best=(\d+) next=(\d+) settled=(\d) active=(\d+)', l)
            if not m: continue
            p, ep, win, ev, q, best, nx, st_, act = m.groups(); ev, best, nx, act, st_ = int(ev), int(best), int(nx), int(act), int(st_)
            pr = prev.get(p, {}); e = []
            if pr and act < pr['act']: e.append(f'후보 제거 {pr["act"]}→{act}')
            if pr and act > pr['act']: e.append(f'후보 복귀 {pr["act"]}→{act}')
            if pr and st_ and not pr['st']: e.append('정착')
            if pr and not st_ and pr['st']: e.append('정착 해제')
            if st_ and nx != best: e.append(f'이웃 탐침→{nx}')
            prev[p] = {'act': act, 'st': st_}
            ph = [x for t_, x in PH if t_ <= ts(l)][-1:] or ['A']
            w.writerow([wl, p, ep, win, round((ts(l) - t0) / 60, 2), f'{ph[0]}({NAME[ph[0]]})', ev, *dec(ev),
                        f'{int(q) / 65536:.4f}', best, nx, st_, act, '; '.join(e)])
