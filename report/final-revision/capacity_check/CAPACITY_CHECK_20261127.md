# 고컴 NVMeVirt 용량 검증 (2026-11-27, 읽기 전용)

- 새 실험은 하지 않았다. 원시 로그, 소스, 시스템 정보를 읽기만 했다.
- 측정 당시 고컴에서는 revF 큐가 실행 중이었다. 조회는 CPU 8, nice 19로 가볍게 했고, 큐와 모듈에는 손대지 않았다.

## 결론

- **고컴에서 16 GB SSD로 실험한 기록은 없다.** 고컴의 NVMeVirt 할당은 모든 run에서 **8 GiB**이고, 승컴과 같다.
  - 고컴 run 커널 로그 779개가 모두 `Storage: 0x100100000-0x300000000 (8191 MiB)`, `ns 0/1: size 7655 MiB`다.
  - 승컴 리비전 run 45개도 같은 값이다.
  - "16 GB"에 해당하는 것은 **승컴 호스트의 물리 RAM**(16 GB)이다. 고컴 호스트 RAM은 32 GB다. SSD 용량과는 관계없다.
- 따라서 "16 GB 환경의 iCAT, Random, Greedy GC, Basic, Robust 결과"는 **모두 미실행**이다.
- **기존 결과로는 용량을 늘린 환경에서 iCAT 성능을 검증할 수 없다.** 검증하려면 새 실험이 필요하다 (§4). 승인 없이 시작하지 않았다.

## 1. 확인 항목

| 항목 | 고컴 | 승컴 | 값 종류와 출처 |
|---|---|---|---|
| CPU | AMD Ryzen 5 3600XT (6코어 12스레드) | Intel i7-7700 (4코어 8스레드) | 실측. run별 `environment.txt` lscpu |
| 호스트 물리 RAM | **32 GiB** (펌웨어 메모리 지도 System RAM 합계 31.95 GiB) | **16 GB** | 고컴: 실측, `/sys/firmware/memmap`. 승컴: 문서 기록 (`EXPERIMENTS_OVERVIEW.md:27`, EXPERIMENT_LOG 1638행 "16 GiB 중 8 GiB 예약") |
| OS가 쓰는 RAM | 24 GiB online (`lsmem`), `free` 23 GiB | `free` 7.6 GiB | 실측 (승컴은 run `environment.txt`) |
| NVMeVirt 예약 | 커널 인자 `memmap=8G$4G` → 0x1_0000_0000–0x2_FFFF_FFFF, 8 GiB (`lsmem`에서 빠진 구간) | 같은 커널 인자 | 실측. `/proc/cmdline`, 승컴 run `environment.txt` |
| NVMeVirt 할당 (insmod) | `memmap_start=4G memmap_size=8192M` | 같음 | 러너 인자 (리비전 러너 전체 170곳, 다른 값 없음) |
| NVMeVirt가 인식한 저장 영역 | 8191 MiB | 8191 MiB | 실측. 커널 로그 `Storage:` 줄. 고컴 779 run, 승컴 45 run 모두 같음 |
| 호스트가 인식한 논리 용량 | **7655 MiB** (`/dev/nvme1n1`, namespace 1개) | 7655 MiB | 실측. 커널 로그 `ns 0/1: size` |
| NAND 구성 | MLC, 채널 8 × LUN 2 × plane 1, flash page 32 KiB, FTL 파티션 4개, 파티션당 line 8,192개 (커널 로그 `chs=2 luns=4 lines=8192`는 파티션 기준) | 같음 (같은 `ssd_config.h`) | 소스 `revC-src/ssd_config.h:71–80`, 커널 로그 |
| 지연 모델 | 읽기 36 ± 6 µs, 프로그램 185 µs, erase 0 | 같음 | `ssd_config.h:92–96` |
| Over-provisioning | 7 % (`OP_AREA_PERCENT 0.07`). 8191 MiB 대비 논리 7655 MiB는 93.5 % | 같음 | 소스, 로그로 계산 |
| GC 시작 조건 | 빈 line 2개 이하 | 같음 | `conv_ftl.c:1182` |

## 2. 워크로드 크기와 쓰기량 (mixFYF, 두 호스트 공통)

| 항목 | 값 | 비고 |
|---|---|---|
| 준비 쓰기 | 6 GiB 순차 + 3 GiB 4 KiB 랜덤 (seed 20260907) | 러너 |
| FIO-Fast 작업 영역 | hot 512 MiB (24k IOPS) + warm 1.5 GiB (12k) + cold 4 GiB (4k) = **6 GiB** | `workloads/mix-test4.fio`. 논리 용량 7655 MiB의 약 80 % (계산) |
| YCSB-A | SQLite 25만 레코드 load + run 1800 s | 러너 |
| 호스트 쓰기량 (iCAT-v4, revE rep1 예) | 전체 571 GiB. 단계 A 275 GiB, 단계 B 22 GiB, 단계 C 275 GiB | 실측. `summary.txt` host_pages × 4 KiB. 논리 용량의 약 76배 |

- 작업 영역이 논리 용량의 약 80 %다. 그래서 이 설정의 WAF는 용량 대비 사용률에 크게 좌우된다.
- 같은 FIO 설정을 16 GB SSD에 돌리면 사용률이 약 40 %로 떨어진다. 그러면 WAF와 GC 압력이 전혀 다른 실험이 된다 (§4).

## 3. 정책별 결과 정리 요청에 대한 답

| 정책 | 16 GB SSD 결과 | 참고: 실제로 있는 8 GiB mixFYF 결과 |
|---|---|---|
| iCAT (iCAT-v4) | **미실행** | 고컴 revA·revC·revE, 승컴 revD·abl·batchG (각 n=3, 배치별) |
| Random Selection | **미실행** | 고컴 revA n=3 |
| Greedy GC | **미실행** | 승컴 batchG n=3 |
| Basic (CAT-Default, arm 37) | **미실행** | mixFYF에는 없음 |
| Robust (CAT-Robust, arm 50) | **미실행** | mixFYF에는 없음 |

- 반복별 WAF, 평균, SD, CI는 8 GiB 결과에 대해 이미 정리되어 있다. 위치: `report/final-revision/complete-results/raw_results_mixFYF.csv`, `all_group_stats.csv`, `report/final-revision/gocom_revision_final/`.
- 16 GB 결과가 없으므로 이 문서에서는 새 표를 만들지 않았다.

## 4. 고컴과 승컴의 차이, 그리고 용량 확장 검증에 필요한 것

- **두 호스트의 SSD 설정은 같다**: 8 GiB, 같은 `ssd_config.h`, OP 7 %, 같은 워크로드와 seed.
- 다른 것은 호스트 하드웨어다: CPU (AMD 6코어 vs Intel 4코어), 물리 RAM (32 GB vs 16 GB). 그래서 고컴과 승컴 결과의 차이는 **용량 효과가 아니다.** 호스트와 배치의 차이다.
- 기존 자료에는 SSD 용량이 다른 비교가 하나도 없다. 용량 효과는 기존 결과로 판단할 수 없다.
- 용량 확장 실험을 하려면 고컴에서만 가능하다.
  - 승컴은 RAM이 16 GB라 16 GiB 예약이 불가능하다.
  - 고컴도 커널 인자를 `memmap=16G$4G`로 바꾸고 **재부팅**해야 한다. 그러면 OS가 쓸 수 있는 RAM은 약 16 GiB로 줄어든다.
- 실험 전에 정해야 할 것
  1. 워크로드를 용량에 맞춰 키울지 (FIO 작업 영역 12 GiB, 준비 쓰기 2배) 그대로 둘지
     - 키우면 사용률을 같게 둔 "용량 확장" 비교가 된다.
     - 그대로 두면 "사용률 감소" 비교가 된다.
  2. 같은 배치에서 8 GiB iCAT-v4 대조군을 다시 돌릴지. 재부팅을 사이에 두므로 배치가 나뉜다.
  3. 반복 수와 정책 (iCAT-v4, Random, Greedy GC, CAT-Default, CAT-Robust)
- 시간 추정 (계산): mixFYF 1회 약 1.55 h. 16 GiB에서 워크로드를 키우면 쓰기량이 2배라 약 3 h로 추정한다. 정책 5개 × 3회면 약 45 h다.

## 5. 근거 파일

- 커널 로그 검사 대상: 이 PC의 `result/`, `result_e1/`, `result_e2/` 아래 kernel.log 782개.
  - 용량 줄이 있는 779개가 모두 8191 MiB / 7655 MiB다. 나머지 3개는 용량 줄이 없는 로그다.
  - 승컴: origin/main 4689c6797의 리비전 7개 배치 kernel.log 45개.
- 메모리: `/proc/cmdline`, `lsmem`, `/sys/firmware/memmap`. 측정 시각 2026-11-27 16:40경.

## 6. `capacity_comparison.csv` (집컴 `Capacity_Comparison` 시트용)

- 파일: `report/final-revision/capacity_check/capacity_comparison.csv`
  - 수치 출처는 `complete-results/raw_results_mixFYF.csv`다 (원시 카운터 재계산, 커밋 3fdb21258). 평균, SD, 95 % CI(t, df = 2)는 rep별 값에서 다시 계산했다.
- 열: 실제 용량, 요청 라벨, 호스트, CPU, 물리 RAM, NVMeVirt 할당, SSD 설정, 워크로드, 정책, 배치, n, rep1–3 WAF, 평균, SD, CI, 모듈 sha256, 원시 경로, 상태
- "고컴 16 GB, 승컴 8 GB"라는 전제는 실제 설정과 다르다. 두 호스트 모두 SSD는 8 GiB다. 그래서 CSV에는 다음과 같이 적었다.
  - 측정 행은 모두 `ssd_capacity_actual = 8 GiB`다.
  - 16 GiB 행은 5개 정책 모두 `NOT RUN`이다. 수치는 넣지 않았다.
- 양쪽에서 공통으로 실행한 정책 (mixFYF, 요청한 5개 중): **iCAT-v4뿐**이다.
  - 고컴: revA, revC, revE. 승컴: revD, abl, batchG. 배치마다 따로 적었고 합치지 않았다.
  - Random Selection은 고컴만, Greedy GC는 승컴만 실행했다.
  - Basic(arm 37)과 Robust(arm 50)는 어느 쪽도 mixFYF에서 실행하지 않았다.
  - 참고: 고정 Arm 47(CAT-Best)은 양쪽에 있다 (고컴 n=1, 승컴 n=3). 요청 목록에 없어 CSV에 넣지 않았다.
- 이 CSV의 고컴과 승컴 차이는 **용량 효과가 아니다.** SSD 설정과 워크로드는 같고, 호스트(CPU, RAM)와 배치가 다르다.
  - 예: iCAT-v4 배치 평균 범위는 고컴 2.113–2.128, 승컴 2.110–2.139로 겹친다.
