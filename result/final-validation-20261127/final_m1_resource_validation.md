# M1 자원 오버헤드 독립 검증 (승컴, 2026-11-27)

- 재계산 스크립트: `analysis/revision/m1_validation.py` (고컴·승컴 분석 코드를 가져오지 않음)
- 결과 표: `m1_recalc.csv` (166행, 게시값과 대조한 126행 모두 일치, 불일치 0)
- **이 문서의 모든 시간은 커널 `ktime_get_ns` 경과 시간이에요. CPU 시간이 아니에요.** `learner_ns`도 경과 시간이에요.

## 1. 자료 출처 3개 (서로 합치지 않음)

| 출처 | 호스트 | 부하 | 반복 | 계측 |
|---|---|---|---|---|
| A. `resource-v124-20261114` (`origin/resource-overhead-20261114`, 소스 HEAD `fb732800`) | 승컴 i7-7700 | mixY 첫 단계만 (FIO-Fast 1,800 s) | 정책당 n=3 (Fixed47, v1, v2, v4) | `RESOURCE` 줄 (ktime 구간 합), `/proc/meminfo`, schedstat |
| B. `revA-20261114` | 고컴 Ryzen 3600XT | mixFYF 90분 | n=3 | `learner_ns` (판단 구간별 누적 ktime) |
| C. `m1-20261126` | 고컴 Ryzen 3600XT | mixY 10 h | **정책당 n=1** (4회는 사용자 결정으로 취소) | `M1PROF` 줄 (ktime 구간), sampler `mem.tsv`, `stat.tsv` |

## 2. 항목별 구분

| 항목 | 상태 | 값 (재계산) | 근거 |
|---|---|---|---|
| 이론적 자료구조 크기 | **계산값** (원시 로그 아님) | iCAT 학습 상태 10,112 B, SmartGC 1,951,648 B | gdb sizeof × 개수. 아래 4번 주의 참고 |
| 실제 RSS | **해당 없음** | — | 커널 스레드라 프로세스 RSS가 없어요 |
| VmallocUsed 증가 (적재 후 − 전) | **실측, 일치** | C: iCAT-v4 34,848 kB, SmartGC-EQ8 37,752 kB, 차 2,904 kB (n=1). A: Fixed47 34,876, v1 34,868, v2 34,751, v4 34,756 kB (n=3 평균) | `mem.tsv`, `*.samples.txt` |
| 모듈 제거 후 잔여 | 실측, 일치 | C: 두 정책 모두 +16 kB | `mem.tsv` |
| 학습기 CPU 시간 | **미측정** | — | perf 없음, busy-poll이라 `/proc/stat` CPU1·CPU2가 모든 정책에서 100.0 % (재계산 확인) |
| 학습기 경과 시간 (ktime) | 실측, 일치 | A: v4 알고리즘(observe+set_arm) 2.78 ms / 30분. B: v4 3.78–3.99 ms / 90분. C: LEARN 4.29 s / 10 h (GC당 40.8 ns) | `RESOURCE`, `learner_ns`, `M1PROF` |
| GC 전체 경과 시간 | 실측, 일치 | C: iCAT-v4 98.4 µs/회 (10,354 s), SmartGC-EQ8 17.8 µs/회 (1,850 s) | `M1PROF region=GC` |
| GC 내부 알고리즘 (희생 블록 선택) | 실측, 일치 | C: iCAT-v4 SELECT 87.0 µs/회 (GC의 88.5 %), SmartGC-EQ8 1.0 µs/회 | `M1PROF region=SELECT` |
| 공통 NVMeVirt 비용 | **미측정** | — | 디스패처·I/O 경로에 계측이 없어요 |
| GC 공통 작업 (복사·소거) | 차감값 (측정 아님) | C: iCAT 11.3 µs/GC, SmartGC 16.7 µs/GC | GC − SELECT − LEARN(−REWARD). 계측 비용이 섞여 있어요 |
| 알고리즘 추가 비용 | 실측 합, 일치 | C: iCAT 9,167 s (선택이 거의 전부), SmartGC 586 s 이하 (버퍼 473 s는 상한) | 정책 구간 합 |

## 3. 원시 로그 재계산과 게시값 대조

| 출처 | 대조 항목 | 결과 |
|---|---|---|
| A (승컴 resource-v124) | 알고리즘 ms, on_gc ms, GC당 on_gc ns, GC 횟수 × 정책 4개 | 16/16 일치 |
| B (고컴 revA `cpu_measurements.csv`) | `learner_total_ms`, 판단 횟수 × run 13개 | 26/26 일치 |
| C (고컴 m1 `kernel_elapsed_time.csv`, `memory.csv`) | 구간별 호출 수, 누적, 호출당, GC당, GiB당, 파티션 최소·최대, 최대 1회, VmallocUsed | 84/84 일치 |
| 고컴 Excel `CPU and Timing`, `Memory Overhead` 시트 | 위 값들 | 측정값 칸은 모두 일치. 이론값 29칸은 미검증 (sizeof 계산값) |

- `learner_ns`는 **파티션별 누적값**이에요. 전체 학습 시간은 파티션마다 마지막 값을 더해서 구해요. 표본 줄을 모두 더하면 약 100배 큰 값이 나와요. 승컴·고컴 기존 분석은 둘 다 마지막 값을 써서 맞아요.

## 4. 고쳐야 할 표기

| 위치 | 현재 표기 | 문제 | 수정 권고 |
|---|---|---|---|
| `origin/resource-overhead-20261114:result/resource-v124-20261114/report/cpu_overhead_summary.csv`, `cpu_time.csv` | "알고리즘 CPU [ms]", "학습 훅 순비용 / dispatcher CPU [%]" | 값은 ktime 경과 시간이에요 | "알고리즘 경과 시간 (ktime) [ms]"로 바꾸기. 근거(schedstat 99.9 %)는 각주로 |
| 고컴 `revA-20261114/analyze.py` 열 `learner_cpu_ms`, 그림 `results/resource/figure8_learner_cpu.png` | "learner CPU" | `learner_ns`는 경과 시간이에요 | "learner elapsed (ktime)"로 바꾸기 |
| 집컴 `report/paper-figures/figure_manifest.csv` figure07 | "CPU: n=3 per policy", "Mean ± 95 % CI for CPU" | 커널 CPU 시간은 측정된 적이 없어요 | "ktime 경과 시간, n=3"으로 바꾸기 |
| 승컴 `result/revD-20261124/preregistration.md` 지표 8 | "탐색 CPU 경과 시간" | CPU와 경과 시간이 섞여 있어요 | "탐색 경과 시간 (ktime)" |
| 고컴 Excel `Memory Overhead` B9, `Executive Summary` E27, m1 보고서 | "iCAT 10,112 B" (m1 비교 문맥) | 10,112 B = (tuner 2,656 B − param 128 B) × 4로, **resource-v124 빌드** 값이에요. m1 빌드의 tuner는 2,712 B예요 (`m1-20261126-final/memory_theoretical.csv`). 같은 규칙이면 (2,712 − 128) × 4 = 10,336 B예요 | 어느 빌드의 값인지 적거나, m1 빌드 값으로 바꾸기. 결론(약 1/190)은 그대로예요 |
| 고컴 Excel `CPU and Timing` | ktime을 "CPU 시간 아님"으로 명시 | 문제 없음 | 유지 |

## 5. 결론

- 측정한 값(VmallocUsed, ktime 구간)은 원시 로그와 모두 일치해요.
- **CPU 시간은 어느 PC에서도 측정되지 않았어요.** 논문에는 "경과 시간 (ktime)"으로만 써야 해요.
- 학습 상태 메모리는 iCAT이 작아요 (계산값). 반면 GC 경과 시간은 iCAT이 SmartGC-EQ8보다 5.5배 길어요 (n=1). 둘 다 그대로 보고해야 해요.
- C는 정책당 1회라서 신뢰구간과 유의성 검정이 없어요.
