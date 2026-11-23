# CPU·메모리 오버헤드 최종 정리 (고컴 검증)

- 작성: 2026-11-23, 고컴. **새 실험은 하지 않았다.**
- 기존 측정값을 다시 확인했다. 자료구조 크기는 **모듈 바이너리의 DWARF 정보에서 gdb `sizeof`로 직접 읽었다.**
- 표기:
  - **[측정]** 실행 중 계측한 값
  - **[계산]** 코드와 sizeof로 식을 계산한 값
  - **[추정]** 다른 실험의 계수를 빌려 온 값

## 1. 요약

| 항목 | 값 | 종류 | 근거 |
|---|---|---|---|
| iCAT V4 학습 결정 경로 누적 시간 (mixFYF 90분, 4 파티션 합) | **3.88 ± 0.11 ms** (n=3) | 측정 | revA ktime 계측 |
| 1회 결정당 시간 | 평균 3.9 µs, 최대 13.4 µs | 측정 | 같은 계측, 991회 |
| 측정 구간 경과 시간(5,404 s) 대비 | 0.00007 % | 계산 | 3.88 ms ÷ 5,404 s |
| GC마다 호출되는 학습 훅(구간 누적·조건 검사) | **미측정** | — | 계측 범위 밖 (§2.1) |
| 위 훅을 계수 9.4 ns/GC로 환산 | 약 47 ms / 90분 | 추정 | GC 약 4.98 M회 × 9.4 ns. 9.4 ns = res-v4 계측의 GC당 on_gc 27.4 ns − CAT-47 18.0 ns (FIO-Fast 30분, n=3, `origin/resource-overhead-20261114` `result/resource-v124-20261114/report/cpu_overhead_summary.csv`). 측정값의 **차분**이므로 추정으로 분류 |
| iCAT V4 tuner 구조체 전체, online-v4 (승컴 mixY 실행 모듈) | 10,624 B = 2,656 B × 4 | 계산 (gdb sizeof) | `nvmev-online-v4.ko` db93f822 |
| 위에서 고정 CAT도 쓰는 128 B 파라미터 캐시를 뺀 학습 전용 | **10,112 B** = 2,528 B × 4 | 계산 | resource-v124 `data_structure_sizes.csv`와 일치 |
| 같은 항목, revA-v4 (계측 카운터 포함) | 10,848 B = 2,712 B × 4 | 계산 (gdb sizeof) | `nvmev-revA-v4.ko` 987d6204 |
| SmartGC 학습·정책 상태 | 1,951,648 B (학습) + 393,216 B (GC 버퍼) = **2,343,936 B** | 계산 (gdb sizeof + 할당식) | §3 |
| 커널 vmalloc 증가량 (실행 중 평균 − 로드 전) | SmartGC 37,606 / CAT-47 35,595 / iCAT V4 34,741 kB | 측정 (승컴, n=1) | `result/smartgc-20261119/report/compare.csv` |
| nvmev dispatcher 스레드 사용률 | 4개 정책 모두 99.9 % | 측정 (승컴 schedstat) | busy-poll이라 정책을 구분할 수 없다 |

## 2. CPU

### 2.1 무엇을 쟀나 (revA-src `conv_ftl.c:737–745`)

```c
t0 = ktime_get_ns();
if (evaluated != t->best_arm) t->n_eval_explore++;
next = watgc_v2_observe(ftl, host, gc_pages, sample);   /* 보상 갱신, 제거, 정착, drift, 다음 arm 선택 */
if (next != evaluated) { watgc_v2_set_arm(ftl, next); t->n_select++; }
t->learner_ns += ktime_get_ns() - t0;
```

- **포함:** 판단 구간이 끝날 때 한 번 실행되는 학습 결정 전체(observe + set_arm)
- **제외:**
  - GC마다 호출되는 `watgc_v2_on_gc`의 구간 누적·조건 검사(c:684–724)와 그 호출 인자 `ktime_get_ns()`(c:1719)
  - CAT 희생 블록 점수 계산. 이것은 학습기가 없는 CAT-47에도 똑같이 있다.
- 따라서 3.88 ms는 **학습 결정 비용**이다. "학습기가 더하는 CPU 전체"의 하한일 뿐이다. 프로세스나 시스템의 CPU 사용량이 아니다.

### 2.2 변형별 측정값 [측정] (`result/revA-20261114/results/resource/resource_summary.csv`, revB는 같은 카운터)

| 변형 | 결정 횟수 | 누적 시간 | 1회 평균 | 1회 최대 |
|---|---|---|---|---|
| V4 | 991 | 3.88 ms | 3.92 µs | 13.4 µs |
| V1 | 1,000 | 3.68 ms | 3.68 µs | 12.7 µs |
| V2 | 924 | 9.04 ms | 9.78 µs | 17.3 µs |
| Random | 915 | 2.77 ms | 3.03 µs | 6.7 µs |
| noelim (revB) | 941 | 6.99 ms | — | — |
| nosettle (revB) | 1,029 | 3.33 ms | — | — |
| arm60 (revB, n=1) | 990 | 3.68 ms | — | — |

- 후보 제거를 끄면(noelim, V2) 결정 1회 비용이 약 2–2.5배다. 매 구간 모든 활성 후보에 대해 UCB를 계산하기 때문이다.
- 모든 변형에서 경과 시간 대비 0.0002 % 미만이다.

### 2.3 SmartGC

- 학습 CPU는 **미측정**이다. smartgc-src에 시간 측정 장치가 없다.
- 학습 step 수만 있다 [측정, 승컴]: SmartGC-EQ8 47,796회, SmartGC 22,456,563회 (mixY 10 h).
- step 수 × 시간 같은 환산은 하지 않는다. step당 비용을 측정한 적이 없다.

## 3. 메모리: 자료구조 크기와 커널 메모리 증가는 별도 지표다

### 3.1 자료구조 크기 [계산, gdb sizeof로 독립 확인]

| 모듈 | `struct watgc_v2_tuner` | `struct watgc_v2_arm` | `struct line` | `struct conv_ftl` |
|---|---|---|---|---|
| online-v4 (db93f822, 승컴 mixY V4) | **2,656** | 40 | 48 | 2,904 |
| revA-v4 (987d6204) | 2,712 | 40 | 48 | 2,960 |
| revB-noelim (b1663b47) | 2,712 | 40 | 48 | 2,960 |
| SmartGC 승컴 소스 29b5f116b를 고컴에서 크기 확인용으로만 빌드 (b4724ec7) | — | — | **72** | `struct smartgc` 232, `struct smartgc_cand` 32 |

- iCAT tuner 구조체 전체(arm 60개 × 40 B 포함)는 파티션 4개 합으로 10,624 B(online-v4)다.
  - 고정 CAT도 쓰는 128 B 파라미터 캐시를 빼면 학습 전용은 **10,112 B**다. 승컴 보고서 값과 정의가 일치한다 (`origin/resource-overhead-20261114`의 `data_structure_sizes.csv:90–93`, gdb 값 2,656 B도 같음).
  - 논문에는 "학습 전용 10,112 B (구조체 전체 10,624 B)"처럼 정의와 함께 쓴다.
  - revA-v4의 2,712 B는 revA에서 추가한 계측 카운터 56 B를 포함한다.
- SmartGC 크기는 승컴 표(`result/smartgc-20261119/smartgc_memory_sizes.csv`)의 sizeof(32, 232, 72)와 같다. 파티션당 개수는 line 8,192개, 페이지 524,288개다.

| SmartGC 항목 | 4 파티션 합 (B) | 분류 |
|---|---|---|
| Q-table int64 × 10,000 상태 × 2 행동 | 640,000 | 학습 (용량과 무관) |
| 후보 목록 32 B × 8,192 line | 1,048,576 | 학습 (line 수에 비례) |
| 정렬 키 8 B × 8,192 | 262,144 | 학습 (line 수에 비례) |
| `struct smartgc` | 928 | 학습 상태와 통계 |
| **학습 소계** | **1,951,648** | — |
| drain 4 B × 8,192 + buffered 비트맵 524,288 bit | 393,216 | GC 버퍼 (학습이 아님) |
| **합계 (승컴 표 값)** | **2,343,936** | — |

- 학습 전용끼리 비교하면 SmartGC는 iCAT V4의 약 **193배**(1,951,648 ÷ 10,112)다.
  - 승컴 보고서의 "약 232배"(2,343,936 ÷ 10,112)는 학습이 아닌 GC 버퍼 393,216 B까지 분자에 넣은 값이다. 논문에는 193배를 쓰거나, 232배를 쓸 때 GC 버퍼 포함임을 밝힌다.
- 이와 별도로 smartgc-src 빌드는 line 구조체가 72 B로, iCAT 빌드의 48 B보다 크다. 24 B × 8,192 × 4 = 786,432 B만큼 더 쓴다. 학습 상태가 아니라 빌드 차이다.

### 3.2 커널 메모리 증가 [측정, 승컴, n=1]

| | SmartGC | CAT-47 | iCAT V4 |
|---|---|---|---|
| VmallocUsed 실행 중 평균 − 로드 전 | 37,606 kB | 35,595 kB | 34,741 kB |
| CAT-47과의 차이 | +2,010 kB | 0 | −854 kB |
| 같은 차이의 계산 예상 (3.1절) | +2,343,936 B + 786,432 B ≈ +3,057 kB | 0 | +10,112 B − 786,432 B ≈ −758 kB |

- 측정 차이와 계산 예상의 **방향은 같다.** 크기는 SmartGC에서 약 1,050 kB 어긋난다.
  - vmalloc과 vzalloc은 할당 시점에 물리 페이지를 잡는다. 그래서 "아직 쓰지 않은 페이지"로는 설명되지 않는다. 원인은 **확인 필요**다.
  - n=1이라 잡음 크기를 모른다.
- **결론:** 크기 비교는 sizeof(계산값)를 주 지표로 쓴다. VmallocUsed는 "에뮬레이터 자체가 약 35 MB를 쓰고, 정책 간 차이는 수 MB 이하"라는 보조 근거로만 쓴다.
- 고컴 revA에서는 VmallocUsed를 arm47 1회만 샘플링했다(최대 82,440 kB). 정책 비교에는 쓸 수 없다.
- 커널 스레드라 RSS는 없다.

## 4. 전체 실행 시간 대비 학습 비용

| 부하 | 경과 시간 | 학습 결정 시간 | 비율 | 종류 |
|---|---|---|---|---|
| mixFYF 90분, V4 | 5,404 s | 3.88 ms | 0.00007 % | 측정 / 계산 |
| mixFYF 90분, V4, GC 훅 포함 (9.4 ns/GC 적용) | 5,404 s | 약 51 ms | 약 0.001 % | 추정 |
| mixY 10 h, V4 (승컴) | 36,045 s (dispatcher CPU) | 0.97 s | 0.003 % | 추정 (9.4 ns/GC × 103 M GC) |

- 어느 경우든 학습 비용은 dispatcher 스레드 시간의 0.01 % 미만이다.
- 다만 0.97 s와 51 ms는 다른 부하(FIO-Fast 30분)에서 잰 차분 계수를 빌린 **추정값**이다. 논문에는 측정값(3.88 ms / 90분, 1회 3.9 µs)을 먼저 쓴다.

## 5. 남은 확인 사항

1. (해결) resource-v124-20261114는 `origin/resource-overhead-20261114`에 있다. 10,112 B와 9.4 ns의 정의를 위 표에 반영했다.
2. SmartGC VmallocUsed 측정 차이와 계산 예상이 어긋나는 원인 (n=1).
3. SmartGC step당 CPU 비용: 계측 빌드가 필요하다 (신규 실험).
