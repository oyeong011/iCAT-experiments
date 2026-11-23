# revA-20261114 사전 등록 (컴퓨터 A, 알고리즘 성능 및 Ablation)

작성: 2026-11-14, 본 실험 시작 전. 호스트 oy-B550M-DS3H (AMD Ryzen 5 3600XT 6C/12T, 23 GiB RAM), 커널 7.0.0-31-generic, iCAT HEAD c06a372a5e940f911734946f1ffd574d2bdd7ca8 (작업 트리 로컬 변경 있음: source-status.txt).

## 비교군 (모두 같은 소스 revA-src에서 ICAT_VARIANT로 분기)

| 이름 | 정의 | 코드 차이 |
|---|---|---|
| revA-v4 | 전체 iCAT-v4 | online-v4와 동일 동작 + 계측 카운터 |
| revA-v1 | 워크로드 변화 감지·재탐색 제거 | drift 검사 블록 비활성 → reset_epoch 호출 없음 |
| revA-v2 | 후보 제거·정착 미적용 | 15% 제거 블록 비활성, settled 진입 금지 → 전 구간 UCB 탐색. V4의 drift 검사는 정착 상태에서만 동작하므로 V2에서는 결과적으로 drift 재탐색도 없음 |
| revA-random | 45개 후보 균등 무작위 | 매 판단 구간 xorshift64*로 arm 15..59 중 하나; 제거·정착·drift 없음. 판단 구간/burn-in은 V4와 동일 |
| arm47 | 고정 CAT k10/25%/r16 (CAT-Best) | 회복 기준 참조용 1회 |

주의: revA-v1/revA-v2는 논문의 iCAT-v1(원본 iCAT)·iCAT-v2(판단 구간 3배)와 다르다.

## 워크로드와 일정

FIO-Fast(test4, 24k/12k/4k IOPS, 1800 s 분량) → YCSB-A(SQLite, 250k records load + run (600k 스모크에서 SQLITE_FULL로 변경), 구간 합계 1800 s) → FIO-Fast(1800 s). 전환 시점 명목 +1800 s, +3600 s. 실제 시각은 phase-*-start.time과 커널 marker로 기록.
준비: 가상장치 ext4 nodiscard, 6 GiB 순차 preset, 3 GiB randwrite(seed 20260907), measurement start/stop.
Seeds: FIO hot/warm/cold = 20260910+rep / 20261010+rep / 20261110+rep (같은 rep의 정책끼리 동일), icat_seed = 2026111400+rep.

## 반복과 순서

arm47 rep1, 이후 rep 1..3 블록마다 4개 학습기 순서를 Random(20261114+rep)으로 섞음 (queue-order.txt). 총 13회, 회당 약 95분.

## 지표 정의

analyze.py 머리말 참조. 요약: WAF = 1+gc/host; 유효 관측 구간 = 4 파티션 accepted window 합; 후보 선택 = 적용된 arm 변경; 후보 평가 = 현 incumbent가 아닌 arm을 평가한 accepted window; 후보 제거 = 온라인 제거 bit 수; 정책 갱신 = incumbent 변경; 누적 탐색 CPU = observe+set_arm 구간 ktime 합(디스패처 스레드 벽시계 ns, 독립 CPU 계측 아님).
WAF 회복: 30 s 카운터의 trailing 300 s WAF. 전환 T 이후 (a) self: 해당 구간 마지막 600 s WAF 대비 ±5% 이내를 180 s 연속 유지하는 최초 시점, (b) ref47: arm47 같은 구간 마지막 600 s WAF ×1.05 이하를 180 s 유지하는 최초 시점. 둘 다 구간 종료 600 s 전까지 미충족이면 not_recovered.
통계: 평균, 표본 표준편차, t 분포 95% CI (n=3, t=4.303). n=3이므로 CI가 넓으며 우열 판정은 CI 비중첩 여부와 개별 값을 함께 본다.

## 실패 처리

exit≠0, 바이트 불일치, 샘플 누락 run은 통계에서 제외하고 runs_status.csv에 남긴다. 원본 삭제·덮어쓰기 금지(러너가 기존 디렉터리 존재 시 거부). 장치 정리 실패 시 큐 중단.
