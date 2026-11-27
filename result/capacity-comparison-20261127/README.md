# SSD 용량 8GB / 16GB 비교 — 기존 데이터 조사 결과 (2026-11-27, 승컴)

새 실험은 하지 않았어요. 기존 로그에서 값만 뽑았어요.

- 생성: `python3 -I -B analysis/revision/capacity_comparison.py`
- WAF는 `final-validation-20261127`에서 가져왔어요. 원시 로그에서 다시 계산한 값이에요.

## 핵심: 두 PC의 SSD 용량은 같았어요 (둘 다 8 GiB)

"고컴은 16GB, 승컴은 8GB"라고 알려져 있었는데, 실제 설정을 확인해 보니 **리비전 mixFYF 실험은 두 PC 모두 같은 8 GiB NVMeVirt**였어요.

| 항목 | 고컴 | 승컴 | 근거 |
|---|---|---|---|
| NVMeVirt 할당 | memmap_size=8192M (Storage 8191 MiB) | 같음 | runner의 insmod 줄, kernel.log `Storage:` |
| 커널 예약 | memmap=8G$4G | 같음 | environment.txt `/proc/cmdline` |
| NAND | 4 파티션 × 2 GiB = 8 GiB (chs=2, luns=4, lines=8192, 블록 64 KiB) | 같음 | kernel.log `Total Capacity` |
| 논리 용량 | 15,677,727 섹터 = 7,655 MiB | 같음 | device.txt |
| OP | 7 % (`OP_AREA_PERCENT 0.07`, 970 Pro 설정) | 같음 | revD-src/ssd_config.h:103 |
| **호스트 RAM (OS가 보는 양)** | **23 GiB** | **7.6 GiB** | environment.txt `free -h` |
| 호스트 RAM (물리, 추정) | 약 32 GB | 16 GB | 보이는 양 + 예약 8 GiB. dmidecode로는 확인하지 않았어요 |
| CPU | Ryzen 5 3600XT | i7-7700 | lscpu |
| 커널 | 7.0.0-31 | 같음 | uname |
| 부하 파일 | mix-test4.fio, YCSB workloada | sha 같음 | environment.txt sha256 |

- 소스·스크립트 전체에서 `memmap_size`는 55곳 모두 `8192M`이었어요. **16 GiB SSD로 돌린 실험은 찾지 못했어요.**
- "16GB / 8GB"는 SSD가 아니라 호스트 RAM의 차이로 보여요 (물리 약 32 GB / 16 GB, 또는 OS가 보는 23 / 7.6 GiB).
- 그래서 이 표로는 **SSD 용량 효과를 비교할 수 없어요.**
  - 두 PC의 차이는 CPU, 호스트 RAM, 배치예요.
  - V4끼리의 차이도 SSD 용량 효과가 아니라 호스트와 배치 차이예요.

## 정책별 WAF (mixFYF, `capacity_comparison.csv`)

| 정책 | 고컴 (배치: 평균 ± SD, n) | 승컴 (배치: 평균 ± SD, n) |
|---|---|---|
| iCAT-v4 | revA 2.128 ± 0.005 (3)<br>revB 2.152 (1)<br>revC 2.120 ± 0.029 (3)<br>revE 2.114 ± 0.026 (3) | revD 2.139 ± 0.008 (3)<br>abl 2.139 ± 0.023 (3)<br>batchG 2.110 ± 0.024 (3) |
| Random Selection | revA 2.324 ± 0.006 (3) | **미실행** |
| Greedy GC | **미실행** (고컴 sg-greedy는 mixY 부하라 제외) | greedygc 2.629 ± 0.007 (3) |
| Basic | 미실행 / 정책 미확정 | 미실행 / 정책 미확정 |
| Robust (CAT-Robust, arm 50) | 미실행 | 미실행 |
| CAT-Best (arm 47), 참고 | revA 1.987 (1) | arm47 1.988 ± 0.0003 (3) |

- **두 PC에서 모두 실행한 정책은 iCAT-v4와 arm 47뿐이에요.**
  - Random은 고컴에서만, Greedy GC는 승컴에서만 실행했어요.
  - Basic과 Robust는 리비전 mixFYF에서 어느 PC도 실행하지 않았어요. 실행하지 않은 정책의 수치는 만들지 않았어요.
  - Basic이 논문의 어느 정책(CAT-Default arm 37 등)을 가리키는지는 근거가 없어서 확정하지 않았어요.
- iCAT-v4는 배치마다 따로 적었고 합치지 않았어요. 평균 범위는 고컴 2.114–2.152, 승컴 2.110–2.139로 겹쳐요.
- 반복별 값, 원시 경로, 모듈 sha, 소스 커밋은 CSV에 있어요.
  - 소스 커밋은 고컴 revA/revB가 c06a372a5(dirty)이고, 나머지 배치는 미기록이라 모듈 sha256으로만 식별해요.

## 집컴 `Capacity_Comparison` 시트에 대한 권고

- 시트 제목을 "SSD 8GB vs 16GB"로 하지 않는 걸 권해요.
- 대신 "호스트별 결과 (SSD 8 GiB 동일, 호스트 RAM·CPU 다름)"으로 쓰고, 용량 효과로 해석하지 않는다고 적어 주세요.
- 진짜 SSD 용량 비교가 필요하면 16 GiB 설정으로 새 실험을 해야 해요. 이번 요청 범위 밖이라 하지 않았어요.
  - 한 PC에서 memmap_size만 바꿔야 해요.
  - 승컴은 OS가 보는 RAM이 7.6 GiB라 16 GiB를 예약하기 어려울 수 있어요.
