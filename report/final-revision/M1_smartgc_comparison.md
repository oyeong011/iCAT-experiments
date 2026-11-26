# M1 기존 기법 비교: SmartGC 대 iCAT 최종본 (고컴 검증, 2026-11-25)

> **11-27 추가**: 구간 타이머 빌드로 다시 잰 자원 비용(GC·선택·학습 경과 시간, VmallocUsed 실측)은 `result/m1-20261126-final/m1_final_report.md`에 있다(고컴, 정책당 1회). 이 문서의 "CPU 시간과 GC 수행 시간 미측정" 서술은 그 보고로 대체된다. 커널 CPU 사용 시간은 여전히 측정 불가이다.

- 새 실험은 하지 않았다. 모든 측정값은 승컴 11월 mixY 10시간 원시 디렉터리에서 고컴이 다시 계산했다(`analysis/final_revision/m1_smartgc.py`).
  - 출력: `result/final-revision-analysis/m1_*.csv`
- 계산값의 근거는 `report/revision-20261123-gocom/resource_overhead_final.md` §3이다. 모듈 DWARF 정보에서 gdb `sizeof`로 직접 읽은 값이다.
- 표기:
  - **[측정]** 원시 카운터, fio json, filebench 출력에서 다시 계산한 값
  - **[계산]** sizeof와 할당식으로 구한 값
  - **[추정]** 다른 실험의 계수를 빌린 값
  - **미측정** 기존 로그에 없는 값

## 1. 비교 조건 (같은가)

| 조건 | SmartGC-EQ8 / SmartGC | CAT-47 (sg-arm47) | iCAT V4 | 같은가 |
|---|---|---|---|---|
| 호스트, 시기 | 승컴, 11월 | 승컴, 11월 | 승컴, 11월 | 같다 |
| 부하 | mixY 20단계 × 1,800 s (FIO test4 / test3 / Varmail) | 같음 | 같음 | 같다 (YCSB 없음) |
| 장치 | 8 GiB 에뮬레이터, 파티션 4개, 파티션당 line 8,192개, 페이지 524,288개 | 같음 | 같음 | 같다 |
| 소스 트리 | smartgc-src (line 72 B) | smartgc-src (line 72 B) | online-v4-src (line 48 B) | **다르다.** SmartGC와 CAT-47은 같은 트리, iCAT은 다른 트리다 |
| 반복 | n=1 | n=1 | n=1 | 통계를 낼 수 없다 |
| 후보 공간 | 희생 블록 단위 Q-learning (행동 2개) | 고정 arm 47 | arm 45개 | 정책 공간이 본질적으로 다르다 (비교 대상의 성격) |
| WAF 정의 | 1 + gc/host, 그리고 NAND 쓰기/host (GC 버퍼 때문) | 1 + gc/host (= NAND) | 1 + gc/host (= NAND) | SmartGC만 두 정의가 다르다. WAF_nand로 비교한다 |
| 채널 모델 경고 "Need to increase array size" | 있음 (커널 로그 줄 수 EQ8 234만, SmartGC 353만) | 있음 (259만) | 있음 (21만) | 네 run 모두에 있다. 이 경고가 뜬 요청에서는 채널 지연이 빠진다. 줄 수는 겹치는 스냅숏까지 센 값이라 상대 비교만 할 수 있다 |

## 2. 최종 비교표

| 항목 | SmartGC-EQ8 (대표) | SmartGC | CAT-47 | iCAT V4 | 종류 | 비교 가능? |
|---|---|---|---|---|---|---|
| WAF = 1 + gc/host | 4.4984 | 11.0723 | 3.2333 | **3.2107** | 측정 (고컴 재계산 = 승컴 `compare.csv`, 파티션 합 일치) | 가능 (n=1) |
| WAF_nand = NAND 쓰기/host | 4.492 | 11.018 | 3.233 | **3.211** | 측정 (승컴 `nand_pages`) | 가능 (n=1). 주 지표 |
| 10 h 동안 처리한 host 쓰기 | 6.08 TB | 4.27 TB | 7.93 TB | 8.41 TB | 측정 | 가능, 단 채널 경고 영향 (§1) |
| FIO 목표 IOPS 미달 job 수 / 42 | 3 | 13 | 0 | 0 | 측정 | 가능 |
| FIO clat p50 (job별 14단계 중앙값) | 11.9–12.1 µs | 298–1,438 µs | 12.0–13.3 µs | 12.2–13.0 µs | 측정 | **제한적** (§3) |
| FIO clat p99 (같은 방식) | 56–61 µs | 14.7–19.3 ms | 229–253 µs | 212–225 µs | 측정 | **제한적** (§3) |
| Varmail 평균 (6단계) | 54,567 ops/s, 0.95 ms/op | 27,009 ops/s, 2.30 ms/op | 86,413 ops/s, 0.58 ms/op | 93,414 ops/s, 0.57 ms/op | 측정 | 가능 (n=1) |
| 학습 상태 크기 (4 파티션) | 1,951,648 B | 같음 | 0 | **10,112 B** | 계산 (gdb sizeof) | 가능 |
| 위에 GC 버퍼 포함 | 2,343,936 B | 같음 | 0 | 10,112 B | 계산 | 가능 (정의를 밝힐 것) |
| 커널 VmallocUsed 증가 (실행 중 평균 − 로드 전) | 미측정 (로드 전 샘플 없음) | 37,606 kB | 35,595 kB | 34,741 kB | 측정, n=1 | 보조 근거만 (§4) |
| RSS | 없음 | 없음 | 없음 | 없음 | — | 커널 스레드라 RSS가 존재하지 않는다 |
| 학습 CPU 시간 | 미측정 | 미측정 | 0 | 미측정 (mixY). mixFYF에서 학습 결정 경과 시간 3.88 ms / 90분 [측정, ktime] | — | **불가** (§5) |
| dispatcher 스레드 사용률 | 99.9 % | 99.9 % | 99.9 % | 99.9 % | 측정 (schedstat) | 정책을 구분하지 못한다 (busy-poll) |
| GC 수행 시간 | 미측정 | 미측정 | 미측정 | 미측정 | — | **불가**. GC 시간 계측이 없다 |
| 학습 step 수 | 47,796 | 22,456,563 | — | 결정 횟수 (mixY) 미집계 | 측정 | 단위가 달라 비교하지 않는다 |

- iCAT V4 대 SmartGC-EQ8 [측정, n=1]:
  - WAF_nand가 28.5 % 낮다 (3.211 대 4.492)
  - host 쓰기를 38.5 % 더 처리했다
- iCAT V4 대 CAT-47 [측정, n=1]:
  - WAF가 0.7 % 낮다
  - n=1이라 차이를 주장하지 않는다
  - 이 CAT-47은 smartgc-src 빌드라 iCAT과 소스 트리가 다르다
- SmartGC 대표는 결과를 보기 전(11-19 EXPERIMENT_LOG)에 정한 규칙으로 EQ8로 정했다.

## 3. 지연 시간: 왜 "제한적"인가

1. **FIO는 `rate_iops`로 처리량을 고정했다** (hot 24,000, warm 12,000, cold 4,000).
   - 목표를 맞춘 정책끼리는 지연만 비교할 수 있다.
   - SmartGC는 13개 job, EQ8은 3개 job이 목표에 못 미쳤다. 이 경우 지연과 처리량이 함께 변한다.
2. **채널 모델 경고가 네 run 모두에서 떴다.** 경고가 뜬 요청에서는 채널 지연이 빠진다.
   - 그래서 지연 분포가 실제 SSD보다 낮게 잡혔을 수 있다. 정책마다 경고 빈도가 다르다.
   - SmartGC-EQ8의 p99(약 60 µs)가 CAT·iCAT(약 220 µs)보다 낮은 것은 이 효과일 가능성이 있다. **원인은 확인하지 않았다.**
3. n=1이다.

- 따라서 논문에는 "SmartGC(원 논문식)는 목표 IOPS를 채우지 못하고 p99가 수십 ms"까지만 쓴다.
- "EQ8의 p99가 낮다"를 iCAT의 약점으로 해석하지 않고, 지연이 iCAT의 장점이라고 주장하지도 않는다.

## 4. 메모리: 자료구조별 근거

| 정책 | 자료구조 | 개수 (4 파티션) | 크기 | 용량과의 관계 |
|---|---|---|---|---|
| iCAT V4 | `struct watgc_v2_tuner` (arm 60개 × 40 B 포함) | 4 | 2,656 B × 4 = 10,624 B. 고정 CAT도 쓰는 128 B 파라미터 캐시를 빼면 **10,112 B** | 용량과 무관하다 (arm 수에 비례) |
| SmartGC | Q-table int64 × 10,000 상태 × 2 행동 | 4 | 640,000 B | 무관 (상태 이산화 수에 비례) |
| SmartGC | 후보 목록 `struct smartgc_cand` 32 B | 8,192 × 4 | 1,048,576 B | line 수에 비례 |
| SmartGC | 정렬 키 8 B | 8,192 × 4 | 262,144 B | line 수에 비례 |
| SmartGC | `struct smartgc` 232 B | 4 | 928 B | 무관 |
| SmartGC | GC 버퍼: drain 4 B × line + 페이지 비트맵 | 8,192 × 4, 524,288 bit × 4 | 393,216 B | 용량에 비례 (학습 상태가 아님) |
| 빌드 차이 | `struct line` 72 B (smartgc-src) 대 48 B (online-v4-src) | 8,192 × 4 | +786,432 B | 학습 상태가 아님 |

- **학습 상태끼리 비교하면 SmartGC는 iCAT V4의 약 193배다** [계산] (1,951,648 ÷ 10,112). GC 버퍼까지 넣으면 약 232배다.
- 원 논문이 적은 "블록마다 20 KB Q-table"을 그대로 따르면 [계산] 32,768 line × 20 KB = 640 MiB다. 이 구현은 그렇게 하지 않고 파티션당 Q-table 하나를 썼다(`smartgc-src/SMARTGC.md` "직접 정한 것" 1).
  - 그래서 메모리 비교는 **이 재구현 기준**이다. 논문에는 원 논문식 크기와 재구현 크기를 함께 적는다.
- **관리 블록 수:**
  - iCAT은 블록별 학습 상태가 없다. 파티션별 tuner가 arm 60개 통계를 가진다.
  - SmartGC는 line(슈퍼블록) 8,192개 × 4개를 상태 계산과 후보 목록에서 관리한다.
- **측정값과 대조** [측정, n=1, VmallocUsed]:
  - SmartGC − CAT-47 = +2,010 kB, 계산 예상 +2,289 kB (배열만)
  - iCAT − CAT-47 = −854 kB, 계산 예상 약 −758 kB
  - 방향은 같다. 크기 차이의 원인은 확인하지 못했다.
  - 에뮬레이터 자체가 약 35 MB를 공통으로 쓰므로 **보조 근거로만** 쓴다.

## 5. CPU: 비교할 수 없는 이유

- SmartGC의 smartgc-src에는 함수 단위 시간 측정 장치가 없다. 학습 step 수만 있다.
- iCAT의 `learner_ns`는 **커널 ktime으로 잰 경과 시간**이다. 프로세스 CPU 시간이 아니다.
  - 범위는 판단 구간이 끝날 때 한 번 실행되는 결정 경로다. GC마다 도는 훅은 포함하지 않는다.
- nvmev 스레드는 busy-poll이라 schedstat 사용률이 모든 정책에서 약 100 %다.
- → **SmartGC와 iCAT의 CPU 비교는 기존 자료로 할 수 없다.**
  - 할 수 있는 말: "iCAT의 학습 결정 경로 경과 시간은 mixFYF 90분 동안 3.88 ms, 1회 3.9 µs다 [측정, ktime]."
  - SmartGC에 같은 계측을 넣으려면 새 빌드와 새 실행이 필요하다. 이번 작업 범위 밖이다.

## 6. 논문 M1 답변 초안

> We re-implemented SmartGC (Zhao et al., HPCC 2025) from the paper. The authors' code is not public. We ran it on the same NVMeVirt configuration and the same 10-hour, 20-phase mixed workload (FIO/Varmail) as iCAT. All policies ran on the same host in the same month, with one run per policy.
>
> **WAF.** We use NAND writes per host write, because SmartGC buffers some writes. iCAT achieved 3.21. SmartGC achieved 4.49 with per-block action selection (Eq. 8) and 11.02 with ranked victim lists. iCAT processed 38.5 % more host data in the same time.
>
> **Memory.** iCAT keeps 10,112 B of learner state for four partitions, independent of device capacity. Our SmartGC implementation keeps 1.95 MB, about 193× more. Most of it grows with the number of blocks. The original paper's per-block 20 KB Q-table would need about 640 MiB for our device.
>
> **Limitations.** Each policy was run once, so we do not claim statistical significance. CPU cost could not be compared: SmartGC has no timing instrumentation, and the emulator threads busy-poll at about 100 % CPU for every policy. iCAT's learner decision path took 3.88 ms (kernel ktime, elapsed time) over a 90-minute run. Latency comparisons are limited by fixed-rate FIO jobs and by emulator channel-model saturation, which occurred in all runs.

**한국어 요지**
- 같은 장비, 같은 달, 같은 부하에서 1회씩 비교했다.
- WAF_nand: iCAT 3.21 대 SmartGC-EQ8 4.49
- 학습 메모리: 10 KB 대 1.95 MB
- CPU와 GC 시간은 측정하지 못했다(이유 명시). 지연 비교는 제한적이다.

## 7. 남는 한계 (기존 로그로 검증할 수 없는 항목)

| 항목 | 이유 | 필요한 것 |
|---|---|---|
| 반복 (n≥3) | 정책별 1회 | 새 실행 (정책당 10 h) |
| SmartGC 학습 CPU | 계측 없음 | 계측 빌드와 새 실행 |
| GC 수행 시간 | 모든 빌드에 GC 시간 계측 없음 | 계측 빌드 |
| CAT-47과 iCAT의 소스 트리 차이 | sg-arm47은 smartgc-src 빌드 | iCAT도 smartgc-src 트리에서 빌드하거나, CAT 비교는 같은 트리 결과(고컴 mixFYF arm47)로 한다 |
| VmallocUsed 측정과 계산의 차이 (SmartGC 약 1 MB) | n=1, 원인 미확인 | — |
