# iCAT 시스템 자원 오버헤드 측정 — 결과 보고서 (resource-v124-20261114)

- 기간: 2026-11-14 21:13 – 2026-11-15 05:43 KST. 계측 12회(정책 4개 × 3회) + 계측 없는 확인 4회. 실패 1회(21:12, 원인·증거 보존, 아래 6절).
- 브랜치 `resource-overhead-20261114`, 시작 커밋 `fb73280`. 환경·모듈 sha256·순서는 `experiment_manifest.json`, 방법은 `measurement_methodology.md`, 코드 감사는 `implementation_audit.md`에 있다.
- 숫자는 모두 FIO-Fast 1,800초 측정 구간, 파티션 4개 합, 정책당 n = 3의 평균 ± 표준편차다.

## 1. 핵심 결과

| | Fixed CAT-47 | iCAT v1 | iCAT v2 | iCAT v4 |
|---|---|---|---|---|
| 학습 전용 메모리 (sizeof, 4 파티션) | 0 B | 10,048 B | 10,048 B | 10,112 B |
| 모듈 text+data (계측 없는 빌드) | 76,469 B | 87,203 B (+10,734) | 87,203 B (+10,734) | 88,655 B (+12,186) |
| 정책 결정 수 / 30분 | 0 | 732 | 312 | 440.3 ± 2.5 |
| 결정 1회 평균 (보상 갱신 + 선택) | 미측정(결정 없음) | 4.28 ± 0.04 µs | 6.34 ± 0.04 µs | 6.18 ± 0.06 µs |
| 결정 1회 최대 | 미측정 | 23.6 ± 5.3 µs | 28.6 ± 6.8 µs | 26.5 ± 3.3 µs |
| 알고리즘 CPU / 30분 (observe + set_arm) | 0 | 3.20 ± 0.03 ms | 2.01 ± 0.01 ms | 2.78 ± 0.04 ms |
| 판단 기록 printk / 30분 | 0 | 4.44 ± 0.06 ms | 1.94 ± 0.06 ms | 2.85 ± 0.11 ms |
| GC당 학습 훅 비용 (iCAT − Fixed, 시계 비용 제외) | 0 | 13.4 ns | 11.6 ns | 9.4 ns |
| 학습 훅 전체 순비용 / 30분 (추정) | 0 | 30.6 ms | 26.2 ms | 20.2 ms |
| 위 순비용 / dispatcher CPU | 0 | 0.0017 % | 0.0015 % | 0.0011 % |
| WAF (계측 3회) | 1.770 ± 0.008 | 2.026 ± 0.001 | 2.005 ± 0.003 | 1.903 ± 0.001 |
| WAF (계측 없음 1회) | 1.775 | 2.024 | 2.007 | 1.902 |
| GC 복사 페이지 (호스트 18.0 M 페이지 기준) | 13.86 M | 18.48 M | 18.03 M | 16.25 M |

- "학습 훅 전체 순비용"은 (iCAT `on_gc` 합) − (GC 횟수 × Fixed의 GC당 `on_gc` 18.00 ± 0.13 ns)로 계산했다. Fixed의 `on_gc`는 빈 함수이므로 그 값이 시계 2회 읽기 비용이다. 이 순비용에는 결정 경로(알고리즘 + printk)와 모든 GC마다 실행되는 단계/창 검사가 들어간다.
- 계측 시계를 포함한 상한값(`on_gc` 합)은 v1 71.6 ms, v2 66.8 ms, v4 58.7 ms이고, Fixed는 35.8 ms다(전부 시계 비용). dispatcher CPU 대비 0.004 % 이하다.

## 2. 지시서 질문에 대한 답

**1) V4 학습 자료구조는 몇 바이트인가.** 파티션 하나에 `struct watgc_v2_tuner` 2,656 B다. 이 중 2,528 B가 학습 전용이고, 128 B(`param`, 현재 CAT 파라미터)는 고정 CAT도 쓴다. 내역은 다음과 같다.
- 후보별 보상 통계 960 B
- 후보별 가중치 480 B
- 탐색 968 B
- 구간·단계 관리 84 B
- 정착·변화 감지 17 B
- 후보 제거 비트맵 8 B
- 패딩 11 B

후보 배열은 60칸(40 B × 60)이다. v4는 그중 45칸만 쓰지만 배열 크기는 60으로 같다. 출처는 gdb `ptype /o`이고, 실행 중 모듈이 출력한 `sizeof`와 일치한다.

**2) 4 파티션 합계는.** 학습 전용 10,112 B(v4)와 10,048 B(v1, v2)다. 할당된 구조체 전체는 10,624 B와 10,560 B다. learner 코어에는 동적 할당이 없다. 튜너는 `struct conv_ftl` 안에 들어 있고 `conv_ftls` 배열과 함께 한 번에 할당된다.

**3) 추가 CPU는 얼마인가.** 30분 동안 결정 경로가 쓴 시간은 알고리즘 2.0–3.2 ms에 printk 1.9–4.4 ms를 더한 값이다. 모든 GC에 붙는 훅까지 포함한 순비용은 20–31 ms로, dispatcher CPU(1,794 s)의 0.0011–0.0017 %다.
- 지시서 8절의 (iCAT − Fixed)/Fixed %는 계산하지 않았다. Fixed의 학습 CPU가 0이라 정의되지 않는다.
- 간접 비용도 있다. iCAT은 같은 호스트 쓰기에서 GC 복사 페이지가 Fixed CAT-47보다 많다(v4 +17 %, v2 +30 %, v1 +33 %). 이 추가 복사에 든 CPU 시간은 분리하지 못했다(4절).

**4) 결정 1회당 평균 CPU는.** v1 4.28 µs, v2 6.34 µs, v4 6.18 µs이고, 최대는 24–29 µs다. 결정마다 printk 6.1–6.5 µs가 따로 더 든다. 결정은 GC 수천 번에 한 번꼴로 일어난다(v4는 30분 동안 440회).

**5) Fixed 대비 메모리 증가는.** 실측 가능한 차이는 코드 크기뿐이다: v1/v2 +10,734 B, v4 +12,186 B(text+data, 계측 없는 빌드).
- 런타임 데이터의 할당 차이는 v4 0 B, v1/v2 −64 B다. 고정 CAT 빌드도 같은 튜너 구조체(2,656 B × 4)를 할당하기 때문이다.
- 학습이 실제로 쓰는 상태는 10.1 kB다.
- insmod 후 VmallocUsed 증가는 정책 4개 모두 34.75–34.88 MB였다. 정책 간 차이(≤ 125 kB)는 실행 중 흔들림(σ ≈ 130–190 kB)보다 작아 측정 해상도 아래다.
- kthread에는 mm이 없어 VmRSS, VmHWM, PSS는 존재하지 않는다(N/A).

**6) V1, V2, V4의 차이는.**
- 메모리: v4만 64 B 더 많다(`active` 비트맵 8 B + `probe_idx` 4 B + 패딩). 코드는 v4가 1.4 kB 더 크다.
- 결정 횟수: v1 732, v2 312, v4 440. v2는 보상 창이 v1보다 커서 결정이 적고, v4는 창 조건이 다르다(감사 문서 참조).
- 결정 1회 비용: v1은 보상 갱신 위주(3.85 µs + 선택 0.41 µs)다. v2와 v4는 선택에 시간이 더 든다(v2 3.11 + 3.22 µs, v4 3.28 + 2.89 µs).
- 30분 총비용은 결정 횟수 차이 때문에 v1이 가장 크다.
- 어느 차이도 dispatcher CPU의 0.002 %를 넘지 않는다.

**7) 후보 수와 SSD 용량의 관계는.** 학습 상태 크기는 후보 칸 수(60)와 파티션 수(4)로만 정해지고 SSD 용량이나 블록 수와는 무관하다. 코드에서 튜너 크기는 컴파일 상수이고, 블록 수(`tt_lines` = 파티션당 8,192)에 비례하는 학습 자료구조는 없다. 결정 1회 비용은 후보 수에 선형이다(후보 배열 순회). 정책 결정 수는 GC 횟수가 아니라 보상 창 크기로 정해진다. 1 TB, 4 TB 장치에서 실측하지는 않았으므로, 용량 독립성은 코드 근거에 따른 결론이다.

**8) SmartGC와 비교할 수 있는가.** 실측 비교는 불가능하다(미측정). 원문 구현이 공개되지 않았고, 상태와 행동 정의, 항목 크기를 확인할 수 없다.
- `smartgc_theoretical_estimate.csv`에는 블록 수 계산만 넣었다(16 KiB 페이지, 블록당 384/768/1,536 페이지, 1/4/16 TB).
- 초안의 104 MB, 833 MB, 3.3 GB는 역산하면 블록당 약 19,044 B × 5,461 블록(1 Tb die), 그리고 그 8배와 32배다. 블록당 크기의 근거는 확인되지 않았다.
- 논문에 쓸 수 있는 문장은 "SmartGC류의 블록 단위 Q-table은 블록 수에 비례하고, iCAT 학습 상태는 용량과 무관한 상수(10 kB)"라는 구조적 비교까지다. 초안 수치를 인용하려면 원문 근거를 먼저 확보해야 한다.

**9) 결과가 논문 주장을 뒷받침하는가.**
- 직접 비용이 작다는 주장(메모리 10 kB 상수, CPU 0.002 % 미만)은 뒷받침된다. 3회 반복의 표준편차가 1–2 % 이내로 작다.
- 이 실험에서 iCAT의 WAF는 Fixed CAT-47보다 나빴다(v4 +7.5 %, v2 +13.3 %, v1 +14.5 %). Fixed CAT-47은 이 부하에서 오프라인으로 고른 최적 arm이라 사실상 상한(oracle) 기준이다.
- 따라서 "iCAT은 자원을 거의 쓰지 않는다"는 직접 비용에 한해서만 맞다. 학습 중 덜 좋은 arm을 쓴 대가로 GC 복사가 17–33 % 늘었다. 이 간접 비용을 논문에서 빼면 과장이 된다.

## 3. 논문 삽입용 표와 해석 문단

**Table X. Resource overhead of the iCAT learner (FIO-Fast, 30 min, 4 partitions, mean ± std, n = 3).**

| Metric | Fixed CAT-47 | iCAT v1 | iCAT v2 | iCAT v4 |
|---|---|---|---|---|
| Learner state (bytes) | 0 | 10,048 | 10,048 | 10,112 |
| Module code + data, delta vs. Fixed (bytes) | — | +10,734 | +10,734 | +12,186 |
| Decisions per 30 min | 0 | 732 | 312 | 440 ± 3 |
| CPU per decision, mean / max (µs) | — | 4.28 / 23.6 | 6.34 / 28.6 | 6.18 / 26.5 |
| Learner hook CPU per GC (ns) | 0 | 13.4 | 11.6 | 9.4 |
| Learner CPU per 30 min (ms) | 0 | 30.6 | 26.2 | 20.2 |
| Share of FTL dispatcher CPU (%) | 0 | 0.0017 | 0.0015 | 0.0011 |
| WAF | 1.770 ± 0.008 | 2.026 ± 0.001 | 2.005 ± 0.003 | 1.903 ± 0.001 |

해석 문단(국문). iCAT 학습기는 파티션당 2.5 kB, 4 파티션 합 약 10 kB의 고정 크기 상태만 쓴다. 이 크기는 후보 수에만 비례하고 SSD 용량과는 무관하다. 학습은 GC 경로 안에서 동기적으로 실행되며, 30분 FIO-Fast 부하에서 GC당 9–13 ns, 결정 1회당 평균 4–6 µs가 들었다. 이는 FTL dispatcher CPU 시간의 0.002 % 미만이다. 계측이 GC 동작을 바꾸지 않았음은 계측 빌드와 비계측 빌드의 WAF 차이가 0.3 % 이내인 것으로 확인했다. 다만 학습 과정에서 최적이 아닌 파라미터를 거치므로, 오프라인 최적 고정 설정(CAT-47)보다 GC 복사가 17 %(v4) 늘었다. iCAT의 실질적 비용은 연산이나 메모리가 아니라 이 탐색 비용이다.

Interpretation (English). The iCAT learner keeps a fixed-size state of about 2.5 kB per partition (≈10 kB for four partitions). The size depends only on the number of candidate configurations, not on SSD capacity. Learning runs synchronously inside the GC path. Under a 30-minute FIO-Fast workload it costs 9–13 ns per GC and 4–6 µs per decision on average, which is below 0.002 % of the FTL dispatcher's CPU time. Instrumented and uninstrumented builds differ in WAF by under 0.3 %, so the measurement did not perturb GC behaviour. The learner does visit sub-optimal configurations, and this raises GC page copies by 17 % (v4) over the offline-best fixed configuration (CAT-47). The practical cost of iCAT is therefore exploration, not computation or memory.

## 4. 한계

- **간접 비용의 CPU는 미측정이다.** `do_gc` 시간(`dogc` − `ongc`)은 측정했다: Fixed 256.0 s, v1 196.9 s, v2 200.3 s, v4 206.8 s. GC 1회당으로는 128.5 µs, 86.4 µs, 88.8 µs, 96.6 µs다. iCAT은 복사 페이지가 많은데도 GC 시간이 더 짧았다. 이 시간은 선택된 arm(k, scale)에 따라 달라지는 victim 탐색 비용을 포함하므로, 학습 비용의 증거로도 반증으로도 쓰지 않는다. dispatcher 전체 CPU는 바쁜 대기로 99.86–99.90 %에 포화되어 정책 간 차이를 보여 주지 못한다.
- 부하는 FIO-Fast 1종, 장치는 8 GiB 에뮬레이터 1종이다. 용량 독립성은 코드 근거이고 실측이 아니다.
- 계측 없는 확인 실행은 정책당 1회다.
- 시계 비용을 Fixed의 GC당 값(18.00 ns)으로 빼는 방식은 iCAT 빌드의 시계 비용도 같다고 가정한다. 같은 `ktime_get_ns`, 같은 CPU 고정이므로 타당하다고 보지만 직접 검증하지는 않았다.
- perf와 `/proc/vmallocinfo`는 sudo 권한이 없어 쓰지 못했다.

## 5. 추가 실험 제안

1. 다른 부하(FIO-Slow, varmail 등)에서 결정 수와 GC 복사 증가율을 확인한다.
2. 더 큰 에뮬레이터 용량으로 학습 상태와 결정 비용이 용량과 무관한지 실측한다.
3. Fixed CAT-47 대신 기본 CAT 설정(비-oracle)을 기준으로 간접 비용을 다시 잰다.

## 6. 실행 중 문제와 처리

- **21:12 첫 실행 실패.** `mix-gc-20261010.sh`의 mixY 요약 단계가 2단계 이상을 가정해 `PN[S02]: unbound variable`로 끝났다. 규칙 6에 따라 중단했다. 증거는 `failed-21h12-*`로 보존했다. 스크립트를 고친 뒤(단계가 1개면 B를 A의 끝 상태로 채움) 21:13에 다시 시작했다.
- **카운터 파일 오염(분석 단계에서 발견).** 러너가 만든 `*.resource.txt`는 dmesg 버퍼 전체에서 잘라 앞선 실행들의 블록까지 섞여 있었다(계측 없는 `online` 실행 파일에도 RESOURCE 줄이 있었음). 첫 분석은 이를 합산해 GC 횟수가 회차마다 2–5배씩 달랐다. 각 실행의 `kernel.log`(그 실행 marker 이후)에는 정확히 한 블록만 있고 `sizeof_tuner`도 빌드와 일치하므로, 분석은 `kernel.log`만 읽도록 고쳤다. 오염된 파일은 기록용으로 그대로 남겼다. 실험 데이터 자체는 영향을 받지 않았다.

## 7. 원본 코드와 계측 코드의 차이

- `online-mix-src` → `res-v1-src`, `online-v2-src` → `res-v2-src`: `conv_ftl.c`만 바뀌었다(+74/−13줄). `online-v4-src` → `res-v4-src`: `conv_ftl.c` +62/−1줄. 나머지 차이는 빌드 산출물(.o, .cmd)이다.
- 추가된 코드는 모두 `#ifdef RES_INSTR` 안에 있다.
  - 파티션별 카운터 배열과 `res_add()`
  - 7개 지점(dogc, ongc, observe, update, select, log, setarm)의 `ktime_get_ns` 쌍
  - rmmod 때 RESOURCE 줄 출력
- 고정 CAT 빌드에는 `#ifdef CONV_FIXED_ARM`으로 arm 47을 설치하는 줄 2개가 더 있다.
- `RES_INSTR` 없이 빌드하면 `.text`의 sha256이 원본 모듈과 같다(v1 badea139…, v2 2002cfa0…, v4 380dfe28…). 알고리즘 변경은 없다.
- 계측 영향: WAF 차이는 Fixed −0.26 %, v1 +0.09 %, v2 −0.08 %, v4 +0.06 %(계측 3회 평균 대 비계측 1회)로, 모두 0.3 % 이내다.

## 8. 산출물

`resource_raw.csv`, `cpu_measurements.csv`, `memory_measurements.csv`, `data_structure_sizes.csv`, `resource_summary.csv`, `cpu_overhead_summary.csv`, `memory_overhead_summary.csv`, `cpu_time.csv`, `smartgc_theoretical_estimate.csv`, `figure10_memory_overhead.png`, `figure11_cpu_overhead.png`, `figure12_learning_cost.png`, `experiment_manifest.json`, `implementation_audit.md`, `measurement_methodology.md`, 이 문서. 재생성: `python3 analysis/resource/analyze.py`.
