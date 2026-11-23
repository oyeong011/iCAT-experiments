# revB-20261122 사전 등록 (고컴, Ablation 보강: 2×2 요인 + 탐색 공간)

작성: 2026-11-22, 본 실험 시작 전. 호스트 고컴 oy-B550M-DS3H (AMD Ryzen 5 3600XT, 23 GiB), 커널 7.0.0-31-generic. iCAT 작업 트리 HEAD c06a372a5 (로컬 변경 있음). 승컴(i7-7700, oy-System-Product-Name)의 결과는 이 캠페인에 합치지 않는다.

## 목적

revA(2026-11-14)의 V2는 "후보 제거 + 정착"을 함께 제거해서 두 기능의 기여를 따로 볼 수 없다. 또 V4의 "탐색 공간 제한(45 arm)" 효과는 같은 장비·같은 계측으로 측정된 적이 없다. 이번 캠페인은 이 두 가지만 보강한다.

| 변형 | 후보 제거 | 정착 | 변화 감지/재탐색 | 이웃 probe | 탐색 공간 |
|---|---|---|---|---|---|
| V4 (revA-v4 ×3, revB-v4 ×1) | O | O | O (정착 상태에서만) | O (정착 상태에서만) | 45 |
| revB-noelim (ICAT_VARIANT=3) | X | O | O | O | 45 |
| revB-nosettle (ICAT_VARIANT=5) | O | X | X (정착이 전제) | X (정착이 전제) | 45 |
| V2 (revA-v2 ×3) | X | X | X | X | 45 |
| revB-arm60 (ICAT_VARIANT=6) | O | O | O | O | 60 (k=2 포함) |

2×2 요인: (제거, 정착) = V4(1,1), noelim(0,1), nosettle(1,0), V2(0,0). V4와 V2는 revA의 같은 호스트·러너·seed 결과(n=3)를 재사용한다. 8일 간격의 재현성 확인용으로 revB-v4 1회를 같이 돌린다. revB-v4가 revA-v4 3회 범위에서 크게 벗어나면(±3 SD 또는 ±1% 초과) revA 재사용을 보류하고 기록한다.

정착을 끄면 V4 구조상 drift 검사와 probe도 동작하지 않는다. 그래서 nosettle은 "정착 및 정착에 딸린 기능 전체 제거"로 해석하며, 정착만의 순수 효과라고 주장하지 않는다.

## 코드

- revB-src = revA-src 사본 + 3줄 분기(inputs/revB-vs-revA.diff). 기존 V4/V1/V2/Random 경로는 바뀌지 않는다.
- 모듈 SHA256은 modules.sha256 참조. 빌드: `make -C /lib/modules/7.0.0-31-generic/build M=/home/oy/iCAT/revB-src ICAT_VARIANT=<3|5|6|4> modules`.
- 러너 runner-revB.sh = runner-revA.sh에서 정책 이름, 경로, 일지 표기만 변경(차이는 7줄). safety-env.sh는 revA와 같고, 허용 모듈 목록만 revB로 바꿨다.

## 워크로드·조건 (revA와 동일)

- mixFYF: FIO-Fast 1800 s → YCSB-A(SQLite, 250k records, 구간 합계 1800 s) → FIO-Fast 1800 s.
- Table-3 준비: 가상장치 ext4 nodiscard, 6 GiB preset, 3 GiB randwrite(seed 20260907).
- seed: FIO hot/warm/cold = 20260910/20261010/20261110 + rep, icat_seed = 2026111400 + rep.
- 장치 설정: memmap 4G+8G, cpus=1,2, 4 FTL partitions. 측정은 명시적 start/stop.

## 순서

queue-order.txt를 그대로 따른다. revB-v4 rep1을 먼저 돌리고, 이후 rep 1..3 블록마다 3개 변형의 순서를 Random(20261122+rep)으로 섞었다. 모두 10회, 회당 약 95분.

본 실행 전에 새 모듈 3개(noelim, nosettle, arm60)를 각각 120 s 단기 실행으로 확인한다. 확인 항목은 로드, 초기 arm 37, WATGC sample 4개 파티션, active 수(noelim/nosettle 45, arm60 60), 커널 오류 없음, 정리 정상이다. 단기 실행 결과는 본 결과에 합산하지 않는다.

## 지표와 판정

지표는 revA analyze.py와 같다. WAF = 1+gc/host, 구간별 WAF, 유효 관측 구간, 선택/평가/제거/정책 갱신/reset 횟수, 학습기 ktime, 회복 시간.

통계는 n=3, t 분포 95% CI를 쓴다. 기여도 계산식은 다음과 같다. 제거 효과 = WAF(noelim) − WAF(V4)와 WAF(V2) − WAF(nosettle). 정착 효과 = WAF(nosettle) − WAF(V4)와 WAF(V2) − WAF(noelim). 상호작용 = 두 값의 차이. n=3이므로 CI가 겹치면 "구분 불가"로 보고한다.

실패 처리는 revA와 같다. exit≠0, FIO 바이트 불일치, YCSB 오류, 커널 오류가 있는 run은 통계에서 제외하고 원본은 보존한다.

## 변경 2026-11-22T19:50 (본 실행 1회차 진행 중, 결과를 보기 전)

사용자 지시("최대한 실험을 빨리 종료")에 따라 revB-arm60 rep2와 rep3를 뺐다. 나머지 순서와 조건은 같다(queue-order-v2.txt, queue2.sh). 2×2 요인(noelim, nosettle)은 n=3을 유지한다. arm60은 n=1이므로 탐색 공간 효과는 단일 관측으로만 보고하고, 통계적 우열은 주장하지 않는다. 총 10회 → 8회, 예상 종료 시각은 11-23 11:30경에서 08:10경으로 앞당겨진다.
