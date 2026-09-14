# 믹스 워크로드 실험 계획 — 2026-09-07

상태: 계획/코드 리뷰. 이 문서는 새 실험 실행 또는 커널 수정 기록이 아니다.
검토 소스: GitHub meendragon/iCAT `7236149a01efad760aed084acf5b270f5a0408f6`.
현재 실행 중인 로컬 고정 CAT 실험과 별개이며, 기존 결과에 최신 온라인 코드의 이름을 붙이지 않는다.

## 목적

같은 가상 SSD에 여러 프로그램이 동시에 접근할 때, 온라인 CAT 파라미터 선택이 고정 CAT보다 유리한지 검증한다. 혼합 비율이 바뀐 뒤의 회복 비용까지 포함한다. 최신 코드는 상태별 Q-learning이 아닌 discounted UCB 계열 bandit으로 분류하며, Q-learning 우월성 실험으로 해석하지 않는다.

## 실행 전 통과 조건

1. Kbuild에 Greedy/고정 CAT/온라인 정책을 명시적으로 연결하고 실제 모듈 정책 로그와 SHA256을 확인한다. 현재 삼성 970 PRO는 이미 선택돼 있지만 학습 정책은 선택되지 않는다.
2. 온라인과 고정 CAT에서 Age 정의와 점수 계산을 통일한다. 최신 소스의 마지막 invalidation 기준 Age와 기존 실험의 생성 시각 기준 Age를 섞어 비교하지 않는다.
3. 온라인 action을 고정한 모드와 동일 파라미터 static CAT의 victim/counter 일치 테스트를 수행한다. 이를 위한 고정 action 인터페이스는 아직 준비되지 않았다.
4. 준비 이후 공통 측정 start/stop, 학습 시작·초기화 제어를 분리한다. cold-start 평가는 준비 중 학습을 금지한다. phase 전환에서는 학습 상태를 유지한다.
5. host/GC counter, Q16 WAF, partition 합계와 독립 장치 쓰기량을 검증한다. 학습에서 제외한 burn-in 쓰기도 전체 성능 비용에는 포함한다.
6. 새 가상 장치의 정체를 검증한 단일 장치 소유 runner를 사용한다. 기존 개별 runner들을 동시에 실행하면 각각 모듈을 재로드/포맷하므로 사용하지 않는다.
7. YCSB JDBC SQLite binding/드라이버와 Filebench 설치 및 짧은 실행을 검증한다. 현재 PATH 검사에서는 fio만 확인됐다. SQLite CLI 설치 여부만으로 JDBC 사용 가능 여부를 판단하지 않는다.

## 세 가지 구성안

모든 프로그램은 같은 NVMeVirt ext4에 서로 다른 경로를 사용한다. 아래 용량은 pilot 목표 상한이며 실제 DB/WAL/파일 생성량을 측정해 확정한다. 논리 용량 약 7.5 GiB에서 최소 1.5 GiB 여유 공간을 확보하고 ENOSPC는 실패로 처리한다.

| ID | 동시에 실행 | 공간 예산 초안 | 확인할 현상 |
|---|---|---|---|
| M1 | SQLite + YCSB-A, fio 순차 덮어쓰기 | DB/WAL 2 GiB, fio 2 GiB | 작은 DB 수정과 큰 순차 쓰기 혼합 |
| M2 | SQLite + YCSB-F, Filebench varmail | DB/WAL 2 GiB, fileset 2 GiB | read-modify-write와 파일 생성/수정/삭제 혼합 |
| M3 | SQLite + YCSB-A, fio 랜덤 덮어쓰기, Filebench varmail | DB/WAL 2 GiB, fio 1 GiB, fileset 1 GiB | 세 스트림 동시 실행과 구성 변화 |

YCSB-F는 workload 파일뿐 아니라 runner의 인수 검사와 binding 지원도 검증한다. 기존 400만 레코드 설정을 그대로 복사하지 않는다. 레코드 수는 실제 공간 측정으로 결정한다. fio는 크기 고정 파일을 덮어쓰며 무한 파일 증가를 금지한다.

## 실행 순서와 길이

1. 계측/장치 보호 테스트 → 각 도구 단독 smoke → 혼합 5~10분 smoke. 이는 기능 검증이며 학습 성능 결과가 아니다.
2. 동일한 데이터 생성 및 preconditioning 절차 후 flush. 공통 카운터를 시작하고 동시에 부하를 시작한다.
3. stationary pilot: M1~M3 각각 혼합 강도를 고정해 1시간 실행한다. 모든 partition의 유효 window 수와 action 방문 수를 기록한다. 탐색이 끝나지 않으면 미수렴으로 보고한다.
4. adaptation 본 실험: A(DB 위주) → B(파일 쓰기 위주) → A. 총 요청 압력을 가능하면 유지하고 스트림별 목표 rate를 바꾼다. 70:30 등의 수치는 우선 요청 부하 목표이지 NAND 쓰기 비율이 아니다. 실제 stream 처리량과 장치 총 쓰기를 함께 보고한다.
5. phase 길이는 pilot 후 고정한다. 모든 정책/seed에 같은 일정 적용. learner가 수렴할 때까지 run마다 임의 연장하지 않는다. 미수렴도 결과로 남긴다.

현재 learner는 60 actions × 최소 3회 방문 = partition당 최소 180 유효 관측이 필요하다. 관측당 최소 256 MiB이며 action 변경 시 128 MiB burn-in이 추가된다. 4 partitions가 모두 coverage에 도달하려면 측정만 최소 180 GiB, burn-in 포함 대략 270 GiB 수준의 host 쓰기가 필요할 수 있다. 4 KiB × 10,000 IOPS 기준 후자는 약 2시간이며 GC 조건·준비·추가 안정성 조건은 별도다. 따라서 10~30분 실행을 수렴 검증으로 간주하지 않는다.

## 비교군과 반복

- Greedy, 동일 구현의 기본 고정 CAT, 개발용 데이터에서 고른 global static CAT, 현재 온라인 UCB tuner.
- offline best는 동일 Age/동일 workload/동일 초기화로 다시 계산한다. phase별 독립 실행 최적값은 연속 실행의 실현 가능한 oracle이라고 단정하지 않는다.
- Q-learning을 별도 구현한다면 그때 동일 action/관측/예산의 bandit 비교를 추가한다.
- pilot 3 matched workload seeds, 최종 5 이상. 정책 순서는 균형 배치하고 모든 실패 기록을 보존한다.
- 3 mixes × 4 policies × 3 seeds = 36회가 stationary pilot 규모다. phase 실험은 별도 36회이며 smoke/oracle 비용은 제외한다. 확정 시간은 pilot 관측 후 산출한다.

## 결과와 판정

- 주 지표: 공통 측정 구간 전체 WAF = 1 + GC pages / host pages. 앱 요청량을 분모로 쓰지 않는다.
- 시간축: 측정 window WAF, cumulative WAF, partition별 action/visits, accepted/discarded windows, phase marker.
- 적응 비용: 전환 이후 추가 GC pages, WAF 회복 시간과 host-write volume. 회복 기준은 기준선 근처 허용 범위와 연속 window 수로 사전 확정한다.
- 앱별 처리량 및 지원되는 latency percentile을 따로 기록한다. 서로 다른 앱의 p99를 평균 내지 않는다.
- 평균/개별 seed/95% CI 보고. 온라인이 지거나 회복하지 못한 경우도 같은 표에 포함한다.
- source SHA, module SHA256, kernel/도구/binding 버전, 실제 장치·용량, Age/GC 설정, CPU 배치, cache/DB durability 설정, workload hash, seed, 시작/종료 및 실패 원인을 EXPERIMENT_LOG.md에 남긴다.
- 실제 SSD 수명/latency 또는 Q-learning 효과에 대한 결론은 이 에뮬레이터 실험만으로 내리지 않는다.

## 중단 기준

잘못된 장치, 계측 불일치, 프로세스 실패, 공간 부족, 로그 손실은 해당 run 실패 및 후속 batch 중단 사유다. 학습 성능 저하/미수렴 자체는 실험 실패가 아니라 보고할 결과다. 진행 중인 기존 CAT batch는 수정하거나 중단하지 않는다.
