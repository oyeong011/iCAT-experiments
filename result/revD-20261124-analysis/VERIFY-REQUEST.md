# 고컴 독립 검증 요청 (승컴 E1 revD, 2026-11-25)

- 큐 종료: 2026-11-25T06:20:12 (E1QUEUEDONE). 9/9 run exit 0, 자동 검사 OK, YCSB 성공률 100 %, SQLITE_FULL 0.
- 원시: result/revD-20261124/raw/ , 사전 등록: result/revD-20261124/preregistration.md
- 분석: python3 -I analysis/revision/e1_revd.py → runs.csv, stats.csv, contrasts.csv (이 폴더). 분석 전 데이터 커밋 6c8465ca403057fce5bd1c5c97312b78c06f083a.
- 승컴 결과만으로 분석했다. 고컴 결과와 합치지 않았다.

## 검증 요청 항목
1. 9개 run 각각의 유효성 재판정: exit, 단계 A/B/C 완료, 커널 오류, YCSB ops = OK.
2. 모듈 SHA256 (modules.sha256)과 run 순서 (queue-order.registered.txt 대 queue.log)가 일치하는지.
3. runs.csv의 단계별 host/gc/WAF를 phase-*-start/end.txt에서 독립적으로 다시 계산.
4. 주 대비(C_waf, total_waf; NoDrift − V4, FullReset − V4)의 Welch CI와 Hedges' g를 독립적으로 다시 계산.
5. 회복 시간 정의가 recovery.py(TOL 1.05, ROLL 10, HOLD 20)와 같은지.
