# m1-20261126 사전 등록: SmartGC 대 iCAT 자원 비용과 반복 실험 (고컴, 2026-11-26 00:20 작성, 실행 전)

## 배경과 목적

- 사용자 지시 "[긴급] M1 SmartGC 비교 실험 미완료 항목 실행" (2026-11-25 23:4x)
  1. 실제 메모리 사용량
  2. 알고리즘 자체의 CPU 사용량
  3. GC 실행 시간
  4. 정책 결정과 점수 갱신 비용
  5. 같은 워크로드와 같은 초기 조건
  6. 독립 반복 3회
- 이미 있는 결과(재사용하고 다시 돌리지 않음)
  - 승컴 smartgc-20261119: mixY SmartGC-EQ8, SmartGC, CAT-47, iCAT-v4 각 1회
  - 고컴 gc-20261010: mixY smartgc, smartgcq, sg-greedy, sg-arm47 각 1회 (11-19~21)
  - 계산 메모리: gdb sizeof
- 이미 있는 결과에 없는 것
  - GC와 학습 구간 계측. SmartGC 원본 빌드와 iCAT online-v4 빌드에는 구간 타이머가 없다. resource-v124 계측 빌드는 저장소에 없다.
  - 반복. 정책마다 n=1이다.
- 이 배치는 위 결과와 **합치지 않는다**. 호스트, 모듈 해시, 배치가 다르다.

## 측정 방법

### 1. 구간 타이머 빌드 (커널, 본 실행)

- 소스
  - SmartGC: `smartgc-src` (= 60174df07. 승컴 EQ8 빌드 헤더의 conv_ftl.c sha256 77cb7009…와 같다)
  - iCAT: `revC-src` (revC·revE iCAT-v4와 같은 소스. ICAT_VARIANT=4)
- 각 소스의 복사본에 `tools/m1prof_patch.py`를 적용했다. 원본 소스는 바꾸지 않았다.
  - 패치는 함수를 `<이름>__m1raw`로 바꾸고, 같은 이름의 래퍼가 시계를 두 번 읽는 구조다. GC 동작은 바꾸지 않는다.
  - diff: `build/m1-icat-vs-revC.diff`, `build/m1-smartgc-vs-60174df07.diff`
- 계측 구간 (파티션별 호출 수, 누적, 최대값)

| 구간 | SmartGC-EQ8 | iCAT-v4 |
|---|---|---|
| GC | do_gc 전체 (선택 + 복사 + 소거 + 보상/학습 훅) | do_gc 전체 |
| SELECT (희생 블록 결정) | select_victim_line (smartgc_step 포함) | select_victim_line (CAT 점수로 전체 line 스캔) |
| LEARN (점수·정책 갱신) | smartgc_step: Q 갱신과 모든 line의 상태 계산, 후보 정렬 | watgc_v2_on_gc: 판단 구간 집계, UCB 선택, 제거, 정착, 변화 감지 |
| REWARD | smartgc_on_erase (소거 보상 계산) | 해당 없음 |
| BUF_* | GC 버퍼 absorb, unbuffer, drain (쓰기 경로) | 해당 없음 |

- 시계는 `ktime_get_ns()`이다. **커널 ktime 경과 시간이고 CPU 사용 시간이 아니다.**
  - dispatcher 스레드는 CPU 1에 고정된 busy-poll kthread다. 구간 안에서 잠들지 않는다.
  - 따라서 경과 시간은 그 CPU에서 해당 코드가 실행된 시간에 인터럽트 시간을 더한 값이다.
- 카운터는 measurement "start"에서 0으로 돌리고, "stop"과 모듈 제거 때 `M1PROF` 줄로 출력한다.
- 계측 자체가 늘리는 경과 시간: 시계 읽기 1회당 수십 ns
  - GC당 2~3구간
  - SmartGC는 호스트 쓰기마다 BUF 구간이 1~2회 추가된다
- 동작이 같다는 확인 (사용자 공간 드라이버, 2 GiB × 3배 덮어쓰기, sim_seed=7)
  - 원본, 패치(계측 끔), 패치(계측 켬)의 host/gc 페이지 수가 같았다
  - iCAT 1,469,964 / 152,358, SmartGC-EQ8 1,469,964 / 454,393
  - 증거: `sim/equiv/`

### 2. CPU 사용 시간 (사용자 공간, 같은 C 코드)

- **커널 안에서 구간 CPU 시간을 직접 잴 수 없는 이유**
  1. 이 커널(7.0.0-31)에 맞는 perf가 설치되어 있지 않다 ("perf not found for kernel 7.0.0-31").
  2. nvmev 스레드는 busy-poll이라 schedstat과 /proc/stat 사용률이 모든 정책에서 약 100 %다. 정책을 구분하지 못한다.
  3. 커널 태스크 CPU 시간(`sum_exec_runtime`)은 tick이나 문맥 교환 때만 갱신된다. µs 단위 구간에는 쓸 수 없다.
- **대체 방법**: `bench-sim.sh`
  - 같은 계측 소스(`conv_ftl.c`, `ssd.c`, `pqueue.c`)를 사용자 공간 드라이버(`sim/sim.c`)로 실행한다. 이 드라이버는 NVMe 쓰기/읽기 명령을 FTL에 직접 넣는다.
  - 모드 1은 `CLOCK_THREAD_CPUTIME_ID`, 즉 스레드 CPU 시간이다.
    - 1회 읽기 비용이 약 1 µs라 긴 구간(GC, SELECT, iCAT LEARN 합계)에만 쓴다.
  - 모드 2는 `CLOCK_MONOTONIC`이다. CPU 11에 고정한 단일 스레드에서 I/O와 대기 없이 잰다.
    - 1회 비용은 약 40 ns다. 짧은 구간에 쓴다.
    - 모드 1의 긴 구간 값과 비교해 둘이 같은 값을 주는지 확인한다.
  - 조건: 8 GiB, 파티션 4개, 6배 덮어쓰기, zones 부하(60/30/10 %), seed 1·2·3, 정책 2개 × 모드 2개
  - 별도로 프로세스 전체 CPU 시간(getrusage user/sys)도 기록한다.
- 한계
  - 가짜 시계와 지연 0 채널 모델을 쓰므로 이 드라이버의 WAF는 측정값이 아니다.
  - 사용자 공간 -O2 빌드다. 커널 빌드와 컴파일 옵션이 다르다.
  - 부하가 mixY가 아니다. 그래서 호출당 비용만 쓰고, 실행 전체 비용은 커널 실행의 호출 수 × 호출당 비용으로 **[추정]**한다.

### 3. 실제 메모리

- `/proc/vmallocinfo`는 root 전용이고 sudo 허용 목록에 없다. 그래서 쓰지 못한다.
- 대신 `sampler.sh`로 다음을 기록한다.
  - `/proc/meminfo`의 VmallocUsed, Slab, SUnreclaim
    - 모듈 적재 전 60 s 동안 1 s 간격
    - 적재 직후 60 s 동안 1 s 간격 (mkfs와 I/O 이전 구간 포함)
    - 실행 중 60 s 간격
    - 제거 후 60 s
  - `/sys/module/nvmev/coresize`
- 판정 지표: **적재 직후 VmallocUsed − 적재 전 VmallocUsed** [측정]
  - 정책 간 차이를 sizeof 계산값과 비교한다.
  - 시스템 전체 값이라 다른 할당의 잡음이 섞인다. 그래서 run 3회의 평균 ± SD로 보고한다.

## 실행 조건

- 부하: mixY. `MIXY_SEQ="F S V F V S F S V F V S F S V F V S F S"`, `PH_SECS=1800`. 20단계, 10시간.
  - 승컴 smartgc-20261119, 고컴 gc-20261010과 같은 부하 정의다.
- 러너: `runner-m1.sh`
  - 바탕은 고컴 `result/sg-20261119/mix-gc-20261010.local.sh`다. 11-19 고컴 mixY 4회에 쓴 사본이다.
  - 차이 4줄 (`build/runner-m1-vs-sg20261119-local.diff`)
    1. 정책 이름 2개 추가
    2. mixY 반복별 디렉터리
    3. insmod 전에 모듈 sha256 등록 확인
    4. `MOD_ARGS` 추가
- 장치: NVMeVirt 8 GiB (memmap 4G+8192M, cpus=1,2). 물리 nvme0n1에는 쓰지 않는다.
  - 러너는 CSL_Virt 모델인 컨트롤러만 쓴다.
- 같은 초기 조건
  - 매 run마다 모듈을 새로 적재하고 mkfs를 한다.
  - Table-3 준비 단계는 같다 (6 GiB FIO 파일, prepare randseed 20260907).
  - FIO seed: 20260910+rep, 20261010+rep, 20261110+rep
- 학습기 seed
  - SmartGC: `smartgc_seed=rep`. rep1은 승컴 EQ8과 같은 seed 1이다.
  - iCAT: `icat_seed=2026111400+rep`. V4는 무작위 선택을 쓰지 않는다. revC·revE와 같은 규칙이다.
- 모듈 (`modules.sha256`)

| 모듈 | 빌드 옵션 | sha256 |
|---|---|---|
| `buildoutput/nvmev-m1-icat-v4.ko` | ICAT_VARIANT=4 | 23d0561f8202da64125e3fa575c1ef3dfa350bee598dc964e0ffa325e0e27148 |
| `buildoutput/nvmev-m1-smartgc-eq8.ko` | NVMEVIRT_GC_POLICY=SMARTGC SMARTGC_EQ8=1 (Q 초기값 0) | d609dcdddfe5aa18132ececd5f2c897774f1cc2521a8fe844214c667f96b2fdc |

- 실행 순서 (`queue-order.registered.txt`): 반복 블록마다 `random.Random(20261126)`으로 섞었다.
  - rep1: iCAT → SmartGC
  - rep2: iCAT → SmartGC
  - rep3: SmartGC → iCAT
- 시작 조건
  - revE 큐가 "main queue finished"로 **정상 종료한 뒤**에 시작한다. 장치가 비어 있어야 한다.
  - revE를 중단하거나 바꾸지 않는다. 승컴에는 관여하지 않는다.
- 단기 실행: 정책마다 1회. SMOKE=1, MIXY_SEQ="F V S", PH_SECS=120. 결과에 합치지 않는다.

## 판정 규칙 (결과를 보기 전에 정함)

- **유효 run**
  - exit 0
  - 모듈 해시 등록값 일치
  - 전체 WAF와 파티션 합 WAF 일치
  - 파티션 4개의 M1PROF stop 줄이 있음
  - 커널 BUG/Oops/Call Trace/soft lockup/hung task 0건
  - FIO job 오류 0건
  - 모든 Filebench 단계에 IO Summary가 있음
  - 20단계 모두 있음
  - CPU 1·2 사용률 ≥ 95 %
- **실패 run**
  - 원인을 기록하고 통계에서 뺀다. 실패 run도 보고한다(실패 수와 원인).
  - SmartGC가 FIO timeout으로 실패하는 것도 정책의 결과로 보고한다. 큐는 이어서 진행한다.
  - 장치가 정리되지 않았거나 커널 오류가 나면 큐를 멈춘다.
- **주 지표**
  - WAF_nand = (host − absorbed + evicted + gc) / host. iCAT은 1 + gc/host와 같다.
  - Welch 95 % CI로 판정한다 (유효 n=3 대 3). n<3이면 통계를 내지 않는다.
- **자원 지표**
  - 커널 구간 경과 시간 [측정, ktime]: 호출당 평균(ns), 실행당 합계(s), 호스트 GiB당(ms), GC 1회당(ns)
  - 사용자 공간 CPU 시간 [측정, 스레드 CPU 시간/고정 코어 monotonic]: 호출당
  - 메모리 [측정 VmallocUsed 증가량, 계산 sizeof]
- **보조 지표** (판정하지 않고 보고만 한다)
  - 처리한 호스트 쓰기
  - FIO 목표 IOPS 미달 job 수
  - Varmail ops/s
  - 채널 모델 경고 줄 수
- 승컴 n=1 결과와 고컴 11-19 n=1 결과는 이 배치와 합치지 않는다. 방향이 같은지만 별도로 적는다.
- 쓰지 않는 표현
  - "CPU 사용률"
  - ktime을 "CPU 시간"이라고 부르는 것
  - n=1끼리 내린 통계 판정
