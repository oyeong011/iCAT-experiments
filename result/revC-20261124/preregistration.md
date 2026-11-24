# revC-20261124 사전 등록 (고컴: E2 미완료분 · E6 1차 · E7)

- 작성: 2026-11-24, 본 실험 시작 전.
- 호스트: 고컴 oy-B550M-DS3H (AMD Ryzen 5 3600XT), 커널 7.0.0-31-generic.
- 지시: 사용자 11-24 "고컴도 독립적인 신규 실험을 진행한다". 이 지시가 이전의 "승컴과 동시 구동 금지"를 대체한다.
- 승컴과의 관계:
  - 승컴 E1(mixR, iCAT-v4 / NoDrift / FullReset)과 SmartGC는 중복하지 않는다.
  - 승컴 장비와 결과에는 손대지 않는다.
  - 고컴 결과는 승컴 결과와 합치지 않는다. 호스트, 부하, 시기가 다르다.

## 1. 실험과 변수

| 실험 | 질문 | 독립변수 | 비교군 | 대조군 |
|---|---|---|---|---|
| **E7** | 탐색 공간 45개 제한(k=2 제외)의 효과 | 후보 수 60 대 45 | revB-arm60 (ICAT_VARIANT 6, ARM_LO 0) | revC-v4 |
| **E2 미완료** | 원래 iCAT(온라인 기준선) 대비 iCAT-v4 | 학습기 구현 | online (`nvmev-online-mix-20260907.ko`, 원래 iCAT) | revC-v4 |
| **E6 1차** | 후보 제거 문턱 민감도 | `WATGC_V2_ELIM_Q16` = 10 % (6554), 15 % (기본 9830), 25 % (16384) | revC-elim10, revC-elim25 | revC-v4 (15 %) |

**통제변수 (revA·revB와 동일)**
- 부하: mixFYF = FIO-Fast 1800 s → YCSB-A(SQLite, 250k records, 1800 s) → FIO-Fast 1800 s
- 준비: Table-3 준비. 가상 장치 ext4 nodiscard, 6 GiB preset, 3 GiB randwrite(seed 20260907)
- seed: FIO hot/warm/cold = 20260910/20261010/20261110 + rep, icat_seed = 2026111400 + rep
- 장치: memmap 4G+8G, cpus=1,2, 4 FTL 파티션. 측정은 명시적 start/stop
- 러너: `runner-revC.sh`. `runner-revB.sh`와의 차이는 정책 목록, 경로, 표기뿐이다(diff 기록)
- 안전 장치: `safety-env.sh`. 가상 nvme1n1만 허용하고, `modules.sha256`에 있는 모듈만 insmod한다. 물리 SSD nvme0n1에는 쓰지 않는다

## 2. 모듈 (`modules.sha256`)

- revC-src = revB-src 사본이다. 차이는 두 가지뿐이다.
  - conv_ftl.h의 7개 파라미터를 `#ifndef`로 감쌌다.
  - Kbuild에 `ccflags-y += $(ICAT_EXTRA)` 한 줄을 넣었다.
- 빌드 명령: `make -C /lib/modules/$(uname -r)/build M=revC-src ICAT_VARIANT=4 ICAT_EXTRA=…`
- 기계어 비교(objdump, 주소 정규화):

| 모듈 | 대 revB-v4 |
|---|---|
| revC-v4 | 차이 0줄 (기계어 동일) |
| revC-elim10 | `imul $0x2666` → `$0x199a` 1줄 |
| revC-elim25 | `imul $0x2666` → `shl $0xe` 1줄 + 정렬 nop |

- revB-arm60, online-mix는 기존 모듈(해시 동일)을 그대로 쓴다.

## 3. 반복과 순서

- 정책마다 **n = 3** (rep 1..3)이다.
- rep 블록마다 5개 정책의 순서를 `random.Random(20261124 + rep)`로 섞었다(`queue-order.txt`). 시기 차이가 한 정책에 몰리지 않게 하기 위해서다.
- 본 실행 전 단기 실행(120 s): revC-v4, revC-elim10, revC-elim25, online.
  - 확인 항목: 로드, 초기 arm, WATGC/학습 로그, 커널 오류 없음, 정리 정상.
  - 단기 실행 결과는 합산하지 않는다.
- 하나라도 실패하면 큐가 멈춘다.
- 예상 시간: 단기 4 × 약 7.5분 + 본 실행 15 × 약 91.5분 = **약 23.4시간**.

## 4. 지표와 분석 (사전 고정)

**주 지표:** 전체 WAF = 1 + gc/host. 원시 카운터로 두 경로(summary, 파티션 합)를 재계산한다.

**보조 지표**
- 단계별 WAF(A/B/C)
- 판단 횟수와 재설정 횟수(커널 로그)
- YCSB 성공률. 실패 > 1 % 또는 SQLITE_FULL이 있으면 무효(`analysis/final_e1/validity.py`).

**통계**
- 정책별 평균 ± SD, 95 % t-CI (n=3, df=2)
- 대조군 revC-v4와의 차이: Welch 95 % CI
- 같은 rep(같은 seed)끼리 짝지은 차이: 95 % CI (df=2)

**판정**
- CI가 0을 포함하지 않으면 "차이 확인"이라고 한다.
- 포함하면 "구분되지 않음"이라고 한다.
- n=3에서 p값과 유의성 표현은 쓰지 않는다.

**배치 연결**
- revC-v4를 revA-v4(n=3, 2.128 ± 0.005)와 비교해 기록한다.
- 비교군과의 판정은 같은 배치의 revC-v4만 쓴다. revA·revB 값과 섞지 않는다.

**기존 결과 재사용**
- revB-arm60 rep1(2.128, 11-22)과 revA-random(n=3)은 보조 비교로만 인용한다.
- 같은 배치 통계에는 넣지 않는다.

## 5. 범위 밖 (이번 배치에서 하지 않음)

- E6 2차 후보: 판단 구간 64/256 GC, 정착 STABLE 6/24, probe 4/16/끔, drift 12.5 %/50 %, γ 반감기 ×¼/×4.
  - revC-src는 이 파라미터들도 덮어쓸 수 있다.
  - 이번 배치가 끝난 뒤 별도로 사전 등록한다.
- 승컴 E4는 mixR에서 n=2로 같은 파라미터 일부를 계획만 했다. 부하가 달라 고컴 결과는 중복이 아니다. 실행 전에 승컴과 범위를 맞춘다.
- SmartGC, E1: 하지 않는다.
