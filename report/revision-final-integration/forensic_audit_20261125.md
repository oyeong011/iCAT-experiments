# 긴급 전수조사 보고서: iCAT 논문 최초 심사 요구사항 충족 여부 및 미실행 실험 발굴

- **작성 시각**: 2026-11-25 23:55 KST (집컴 독립 감사)
- **검증 기준 Git 커밋 (읽기 전용 원시 로그 직접 대조)**:
  - 승컴 `origin/main`: **`282f3fa07`** (`abl-20261125` 8/9 완료, `revD` 9/9 완료, `greedy-20261125` 승인·대기)
  - 고컴 `origin/report/data-validity-20261124`: **`6b87a8079`** (`revE-20261125` 6/9 완료: `revE-v4-rep2=2.0958` 방금 검증 완료, `revC` 15/15 완료, `revA`/`revB` 완료)
  - 자원 계측 `origin/resource-overhead-20261114`: **`c046de0d0`** (`resource-v124-20261114` FIO-Fast 30분 n=3 완료)
- **출처 투명성 명시**: 최초 심사위원 원문 파일 자체는 Git 저장소에 별도 보관되어 있지 않으므로(`research-alignment-audit.md` 확인), 저장소의 최초 대응 문서(`revision_gap_audit.md`, `revision_response_table.md`, `research-alignment-audit.md`, `additional_experiment_plan.md`, `M1~M7` 보고서)와 사용자 지시의 M1~M7 / E1~E8 요구사항을 문장·지표 단위로 **47개 세부 요구사항**으로 분리하여 전수 대조하였다.
- **사용자 제외 확정 항목**: `Random Search`와 `Periodic Switching`은 사용자 결정으로 제외되었으므로 미실행 추가 실험 제안(§B, §E)에서 제외하였다.
- **기계 판독 추적표**: [forensic_requirement_matrix.csv](file:///C:/Users/oyeon/orca/iCAT-experiments/report/revision-final-integration/forensic_requirement_matrix.csv)

---

## 판정 기준 정의 (엄격 적용)

| 판정 | 정의 |
|---|---|
| `COMPLETE` | 필요한 실험, 지표 측정, 원시 로그 독립 검증, 통계 분석(n≥3, CI/Welch), 논문 반영 조건이 모두 충족됨 (단, 단일 워크로드·호스트 범위는 명시) |
| `PARTIAL` | 일부 지표·일부 배치·진행 중(n<3) 또는 교차 배치 단서만 확보됨 (**절대 COMPLETE로 처리하지 않음**) |
| `NOT EXECUTED` | 필요한 실험 또는 계측 빌드를 아예 실행하지 않음 |
| `INVALID` | 실행했으나 `SQLITE_FULL`, `ENOSPC`, 채널 포화 지연 누락, 0바이트 로그 등으로 무효 |
| `INSUFFICIENT` | 실행했으나 반복 횟수(`n=1~2`), 검정력, 또는 측정 지표가 부족해 통계적 결론 불가 |
| `ANALYSIS ONLY` | 신규 실험 없이 기존 로그 재분석 또는 코드 `sizeof`/수식 계산으로만 근거 확보 |
| `PAPER LIMITATION` | 추가 실험 없이 논문 한계(§7·§8)로 명시하기로 결정 |

---

## A. 최초 심사 요구사항 전체 목록 (M1~M7, 47개 세부 요구사항 전수 추적)

### M1. SmartGC 비교 (블록 단위 RL GC vs 정책 단위 iCAT) — 9개 세부 지표

| ID | 요구 지표 | 비교 대상 / 조건 | 필요 n | 실행 ID / 원시 경로 | 유효성 | 통계 | 논문 반영 | 최종 판정 |
|---|---|---|---:|---|---|---|---|---|
| **M1-1** | **이론적 메모리** | SmartGC vs iCAT-v4 (4파티션, 8 GiB) | 정확 계산 | `gdb sizeof` (`nvmev-online-v4.ko`, `smartgc-src`) / `report/revision-20261123-gocom/resource_overhead_final.md` | VALID (`10,112 B` vs `1,951,648 B` [193×] / `2,343,936 B` [232×]) | 정확 계산 | 반영 (§6.3, 표 9) | **`ANALYSIS ONLY`** (계산 완료) |
| **M1-2** | **실제 RSS / 커널 메모리** | SmartGC-EQ8 vs iCAT-v4 (커널 스레드) | n≥3 (측정 시) | `result/smartgc-20261119/report/compare.csv` | **커널 스레드라 RSS 없음**; 보조 `VmallocUsed_delta`는 **대표 모델 `SmartGC-EQ8`에서 로드 전 샘플 누락(`미측정`)**, 비대표 SmartGC만 `n=1` (`37,606 kB`) | 없음 (n=0/1) | 부분 반영 (§6.3) | **`INSUFFICIENT`** (RSS는 `PAPER LIMITATION`, EQ8 Vmalloc은 누락) |
| **M1-3** | **알고리즘 자체 CPU 시간** | SmartGC-EQ8 vs iCAT-v4 | n≥3 | `smartgc-src/conv_ftl.c` (계측 코드 없음); `compare.csv` `learn_cpu_s=미측정` | **SmartGC 미측정**; iCAT-v4 `0.9687 s`도 mixY 실측이 아닌 FIO-Fast 계수 **추정값** | 없음 | 미측정 명시 | **`NOT EXECUTED`** |
| **M1-4** | **정책 결정 비용** | `smartgc_select`/`step` vs `watgc_v2_choose` | n≥3 | `smartgc-src` 미계측 (step 수 `47,796` / `22,456,563`만 존재) | **미측정** (step 수→시간 환산 불가) | 없음 | 미측정 명시 | **`NOT EXECUTED`** |
| **M1-5** | **점수/Q-table 갱신 비용** | SmartGC Q-table update vs iCAT reward update | n≥3 | `smartgc-src` 미계측 (`res-v4`는 FIO-Fast 30분에서만 iCAT `1.442 ms` 측정) | **SmartGC 미측정** | 없음 | 미측정 명시 | **`NOT EXECUTED`** |
| **M1-6** | **GC 실행 시간 (`do_gc`)** | SmartGC vs iCAT-v4 (동일 트리) | n≥3 | `mixY` 4개 run 전부 `do_gc` 시간 계측 없음; 게다가 `smartgc-src`(`line 72 B`) vs `online-v4-src`(`line 48 B`) **소스 트리 불일치** | **미측정** + 에뮬레이터 `erase=0` | 없음 | 미측정 명시 | **`NOT EXECUTED`** |
| **M1-7** | **WAF (`WAF_nand`)** | SmartGC-EQ8 / SmartGC / CAT-47 / iCAT-v4 (`mixY` 10h) | n≥3 | `result/gc-20261010/mixY-smartgc-eq8-rep1`, `result/smartgc-20261119/resume/mixY-onlinev4-rep1` | 원시 카운터 일치 (`3.211` vs `4.492`, `-28.5%`), 단 **소스 트리 다름** + **`n=1`** (`gc-20261010/mixY-smartgc-rep1` ENOSPC 무효 제외) | **없음 (`n=1`)** | 반영 (§6.3 표 9, n=1 단서) | **`INSUFFICIENT`** |
| **M1-8** | **지연 시간 (I/O latency)** | SmartGC-EQ8 vs iCAT-v4 (`mixY`) | n≥3 | `result/final-revision-analysis/m1_latency_{fio,varmail}.csv` | **4개 run 모두 NVMeVirt 채널 모델 포화 경고 `"Need to increase array size"` 수십~수백만 줄 발생**(EQ8 234만, SmartGC 353만, CAT-47 259만, V4 21만) → 채널 지연 누락 + `rate_iops` 고정 + `erase=0` + `n=1` | 없음 (`n=1`) | 비교 제외 명시 (§6.3) | **`INVALID`** (채널 포화 지연 오염) |
| **M1-9** | **독립 반복 및 통계 검증** | SmartGC vs iCAT-v4 (`n≥3`, SD/CI/Welch) | n≥3 | 없음 (전부 `n=1`) | 반복 0건 | **없음** | n=1 단서만 | **`NOT EXECUTED`** |

---

### M2. iCAT 메커니즘별 독립 기여 검증 (Ablation) — 6개 세부 항목

| ID | 메커니즘 | 비교 대상 / 조건 | 필요 n | 실행 ID / 원시 경로 | 유효성 | 통계 | 논문 반영 | 최종 판정 |
|---|---|---|---:|---|---|---|---|---|
| **M2-1** | **후보 제거 단독 효과 (`NoElim`)** | `ICAT_VARIANT=3` (정착·감지 켬, 제거만 끔) vs `V4` (`mixFYF`) | n≥3 | ① `revB-noelim` vs `revA-v4` (교차 배치, `revB-v4` 브리지 `+4.8 SD` 실패)<br>② **고컴 `revE-20261125` 진행 중 (6/9 VALID)**: `revE-v4` `2.1011/2.0958` (2/3), `revE-noelim` `2.2087/2.2067` (2/3) | `revB` 교차배치 단서; `revE` 6/9 모두 VALID (~11-26 04:10 완료) | `revE` 아직 n=2 (통계 대기) | 표 10 `【결과 대기】` | **`PARTIAL`** (고컴 `revE` 완료 시 `COMPLETE` 전환 예정) |
| **M2-2** | **정착 단독 효과 (`NoSettle`)** | `ICAT_VARIANT=5` (정착 끔) vs `V4`; 및 묶음 `VARIANT=2` (`revA-v2`, 승컴 `abl-off-elim-settle-drift-probe`) | n≥3 | ① `revB-nosettle` (`2.2152 ± 0.0790`) vs `revA-v4` (`2.1284`, 교차 배치, Welch CI `[−0.108, +0.282]` 0 포함)<br>② 코드 구조상 정착을 끄면 **변화감지·재탐색·probe도 동시 비활성**(`conv_ftl.c:567,639`)<br>③ 묶음 `VARIANT=2`: 고컴 `revA-v2` (`+0.1355 CI>0`), 승컴 `abl` (`+0.1241 [+0.073, +0.175]` 완료) | 묶음(`VARIANT=2`)은 2호스트 모두 VALID; **단독 정착은 코드 구조상 완전 분리 불가 + 동일 배치 n=3 없음 + CI 0 포함** | 묶음: CI>0<br>단독: CI 0 포함 | 표 10에 묶음만 반영, 단독 미반영 | **`PARTIAL`** (단독 정착은 **`INSUFFICIENT / NOT EXECUTED`**) |
| **M2-3** | **변화 감지 단독 효과 (`NoDrift`)** | `NoDrift` (`revA-v1`, `revD-nodrift`) vs `V4` (`mixFYF`) | n≥3 | 고컴 `revA-v1` (n=3), 승컴 `revD-nodrift` (n=3, 3자 검증 일치) | 100% VALID (`resets=0` 확인) | **두 호스트 모두 Welch CI 0 포함**: 고컴 `+0.079 [−0.050, +0.207]`, 승컴 `+0.068 [−0.040, +0.176]` (Phase C `+0.141 [−0.087, +0.369]`; 3/3 열위·SD 6.7× 증가이나 n=3 검정력 부족) | 반영 (§6.4 표 10, "구분 안 됨" 명시) | **`INSUFFICIENT`** (실험 완료·유효하나 통계적 입증 미달) |
| **M2-4** | **재탐색 효과 (전환 후 재탐색)** | 전환 후 리셋·재탐색 발동 및 WAF/적응 영향 (`revA`, `revC`, `revD`) | n≥3 | `revA-v4`, `revC-v4`, `revD-v4` vs `NoDrift`/`FullReset` | Phase C 43–74 s 감지·재탐색 3배치 재현; **단 Phase B(FIO→YCSB)는 저쓰기(~10창/30분)로 대부분 미감지(0–2파티션, 10–16분 지연)** | `FullReset` 대비 CI>0 (Holm 경계), `NoDrift` 대비 CI 0 포함 | 반영 (§6.4 표 11) | **`PARTIAL`** |
| **M2-5** | **후보 복원 범위 (부분 복원 vs 전체 45개 복원)** | `revD-fullreset` vs `revD-v4` (승컴 `mixFYF`, 동일 배치) | n≥3 | `origin/main:result/revD-20261124/raw/` (9/9, 승컴·고컴·집컴 3자 검증 일치) | 100% VALID (복원 후보 147 vs 13개, 재탐색 창 3.2×, 탐색 비중 0.56 vs 0.27) | 사전 등록 Welch CI>0: 전체 `+0.060 [+0.016, +0.103]` (`g=3.08`), Phase C `+0.130 [+0.052, +0.208]` (`g=3.78`); **단 Holm 4대비 보정 시 `p=0.060/0.072`** | 표 10 반영 (**단 표 8은 아직 대기 상태**) | **`COMPLETE`** (Holm 민감도 단서·단일 부하 명시 조건) |
| **M2-6** | **할인 계수 효과 (`γ=1.0` vs `0.9995`)** | `abl-nodiscount` (`GAMMA_Q16=65536`) vs `abl-v4` (승컴 `mixFYF`, 동일 배치) | n≥3 | 승컴 **`abl-20261125` 진행 중 (8/9 VALID)**: `abl-v4` `2.1390 ± 0.0228` (3/3 완료), `abl-nodiscount` `2.1278 / 2.1106` (**2/3**, 마지막 `rep3` ~00:50 KST) + R2 이론 계산 (`γ^250=0.882`) | 8/9 VALID; `rep3` 1회 남음 | 아직 n=2 (완료 직후 산출) | 미반영 (표 10에 행 자체 누락!) | **`PARTIAL`** (~00:50 KST 완료 시 `COMPLETE` 전환 예정) |

---

### M3. 온라인 정책 선택 비교 (Baseline) — 5개 세부 항목 *(Random Search·Periodic Switching은 사용자 제외 결정)*

| ID | 비교 대상 | 비교 조건 | 필요 n | 실행 ID / 원시 경로 | 유효성 | 통계 | 논문 반영 | 최종 판정 |
|---|---|---|---:|---|---|---|---|---|
| **M3-1** | **Random Selection vs V4** | 고컴 `revA` `mixFYF` 동일 배치 | n≥3 | `result/revA-20261114/raw/mixFYF-revA-{random,v4}-rep{1..3}` | 6/6 VALID | **`+0.1959 [+0.1840, +0.2078]`** (`−8.43%`, `g=29.9`, Welch·짝 CI>0) | 반영 (§6.4 표 10) | **`COMPLETE`** (단일 부하·호스트) |
| **M3-2** | **기존 iCAT(`online`) vs V4** | 고컴 `revC` `mixFYF` 동일 배치 | n≥3 | `result/revC-20261124/raw/mixFYF-{online,revC-v4}-rep{1..3}` | 6/6 VALID | **`+0.2751 [+0.2030, +0.3472]`** (`−11.49%`, `g=10.53`, Welch·짝 CI>0) | 반영 (§6.4 표 10·11) | **`COMPLETE`** (단일 부하·호스트) |
| **M3-3** | **Online Greedy (`VARIANT=8`) vs V4** | 승컴 `greedy-20261125` `mixFYF` (n=3) | n≥3 | `origin/main:result/greedy-20261125/` (빌드·사전등록·승인 완료, **`abl` 종료 직후 ~00:50 자동 시작 대기**) | **0/3 미실행**; 또한 **주의**: ① 승컴 실행이라 고컴 `Random`/`원래 iCAT`과 직접 합산 불가, ② `abl-v4 − revD-v4` CI가 `[−0.0493, +0.0502]`로 사전 기준 `[−0.02, +0.02]` 초과 → `revD-v4` 재사용 시 교차 날짜(2일 차) 단서 발생 | 없음 (0/3) | 표 10 `【결과 대기】` | **`NOT EXECUTED`** (승인·자동 대기 중) |
| **M3-4** | **4개 정책(Random / Greedy / 원래 iCAT / V4) 동일 조건 비교** | 단일 호스트·동일 배치 비교 성립 여부 | n≥3 | Random·원래 iCAT은 **고컴**, Online Greedy는 **승컴**으로 분리 실행 설계 | 호스트 불일치(Ryzen vs i7, YCSB 1.45억 vs 1.15억 ops) → 4개 정책 직접 통합 불가, 호스트 내 `V4` 대비 Δ만 병렬 비교 가능 | 직접 비교 불가 | 표 10에 호스트 분리 표기 | **`PARTIAL`** (구조적 호스트 분리) |
| **M3-5** | **Greedy GC vs iCAT** | `mixFYF` 250k 및 레거시 `x1` 9종 | n≥3 | 레거시 승컴 `mix-20260911` 유효 9종 (`mixC/D/F/K/L/M/O/P/Q`, `online` 대비 n=3×9, 9/9 CI>0 `−7.1~−42.0%`); **`mixFYF` 250k에는 Greedy GC 0회**; `v4` 동일 길이 `x1`은 `mixC/D` n=1뿐 | 레거시 9종 VALID (16개 SQLITE_FULL/mixG 제외), `mixFYF` 0회 | 레거시 `online`: 9/9 CI>0; `v4` n=3: 없음 | 부록 표 A1만 (`mixFYF` 없음) | **`PARTIAL`** (`mixFYF` 기준 `NOT EXECUTED`) |

---

### M4. 통계적 신뢰성 — 8개 세부 항목

| ID | 요구 항목 | 확인 내용 | 원시·분석 근거 | 논문 반영 | 최종 판정 |
|---|---|---|---|---|---|
| **M4-1** | **독립 반복 횟수 (`n≥3`)** | `mixFYF` 핵심 4배치(`revA/B/C/D`) 44회는 n=3 확보(단 `revB` V4·Arm60은 n=1). **그러나 본문 `표 6·표 7`(전환 6~7종 고정 arm 3배 n=1, v4 4종 n=1·2종 n=2), `표 9`(SmartGC n=1), `표 A1`(단일 5종 n=1)은 미반복!** | `M4_statistics_final.md`, `PAPER_KCI_DRAFT.md` 표 6·7·9·A1 | 본문에 `【결과 대기: arm 47·17·50 각 3회】` 잔존 | **`PARTIAL`** |
| **M4-2** | **평균과 표준편차 (SD)** | `revA/B/C/D` 44회 전부 원시 재계산 일치 (`1e-9` 이내) | `result/final-revision-analysis/m4/stats.csv`, 집컴 `iCAT_Paper_Figures.xlsx` | §6.4 표 10 반영 (표 8 대기) | **`COMPLETE`** (`mixFYF` 한정, 전체 논문 기준 `PARTIAL`) |
| **M4-3** | **95% 신뢰구간 (t-CI)** | `n≥3` 전 조건에 `df=n-1` t-CI 산출, `n<3` CI 미표시 원칙 준수 | `m4/stats.csv`, `iCAT_Paper_Figures.xlsx` | §6.4 반영 | **`COMPLETE`** (`mixFYF` 한정) |
| **M4-4** | **Welch 검정 (95% CI)** | 동일 배치 전 대비에 Welch 95% CI 산출·3자 검증 일치 | `m4/contrasts.csv`, `revD-20261124-verify/verify.md` | §6.4 표 10 반영 | **`COMPLETE`** (`mixFYF` 한정) |
| **M4-5** | **짝지은 비교 (같은 seed/rep)** | `revC`, `revD`, `revE`, `abl` 모두 동일 seed 대응 t-CI 산출 설계 및 계산 완료 | `revC_E2_E6_E7_final.md`, `verify.md` | §6.4 각주·보조표 반영 | **`COMPLETE`** |
| **M4-6** | **Holm 다중 비교 보정** | `revD` 4대비(`0.0604/0.0721/0.2342/0.2342`) 및 `revC` 4대비 민감도 산출 완료. `abl`·`revE` 사전 등록에 Holm 포함 | `T1_revC_contrasts_holm.csv`, `verify.md` | §6.4 각주 반영 | **`COMPLETE`** |
| **M4-7** | **실패한 run 처리 및 제외** | `SQLITE_FULL` 224+ run(`mixA/B/H/J/R`, 11-23 `mixR`), `mixG` 34 run(0B 로그), `mixY-smartgc` ENOSPC 1 run 전부 식별·제외 및 `Data Validity` 시트 기록 | `analysis/final_e1/validity.py`, `iCAT_Paper_Figures.xlsx` | §8 한계 7 반영 | **`COMPLETE`** |
| **M4-8** | **서로 다른 배치·호스트 혼합 금지** | `revA/revC/revD`는 엄격 분리됨. 단, 기존 `revB-noelim/nosettle` 교차 배치 잔존(`revE`로 해소 중), 승컴 `greedy`는 `revD-v4`(이틀 전 배치)를 주 대조군으로 사용 예정(교차 날짜 단서 필요), **원고 표 8은 아직 "30만 레코드"로 `revD`(250k)와 불일치** | `M4_statistics_final.md`, `PAPER_KCI_DRAFT.md` 표 8 | 표 8·10 불일치 잔존 | **`PARTIAL`** |

---

### M5. 시스템 오버헤드 — 6개 세부 항목

| ID | 요구 지표 | 확보된 증거 vs 누락된 증거 | 원시 경로 | 논문 반영 | 최종 판정 |
|---|---|---|---|---|---|
| **M5-1** | **메모리 오버헤드** | `gdb sizeof` 4파티션 정확 계산 완료(iCAT `10,112 B` vs SmartGC `1,951,648 B`), `resource-v124` `VmallocUsed`/`Slab`/`coresize` 측정 완료. 커널 스레드라 RSS 없음(`PAPER LIMITATION`), SmartGC-EQ8 `VmallocUsed_before` 누락 | `origin/resource-overhead-20261114:result/resource-v124-20261114/report/memory_overhead_summary.csv`, `resource_overhead_final.md` | §6.3, §7 반영 | **`PARTIAL`** (이론 크기 `ANALYSIS ONLY` 완료, 실측 RSS 불가·EQ8 Vmalloc 누락) |
| **M5-2** | **CPU 오버헤드** | ① `revA` mixFYF 90분 결정 경로 ktime `3.88 ± 0.11 ms` (`0.00007%`), ② `resource-v124` FIO-Fast 30분(n=3)에서 **보상갱신(`1.442 ms`)·정책선택(`1.273 ms`)·`set_arm`(`0.059 ms`)·`on_gc` 훅 순비용(`9.43 ns/GC`, `20.20 ms`)** 분리 실측 완료!<br>**누락**: ① `ktime`은 wall-clock 경과 시간이며 프로세스 CPU 시간(`task_cputime`/perf)이 아님(busy-poll `99.9%`), ② 전환 부하(`mixFYF`) 재탐색 구간 분리 계측 미실행, ③ **SmartGC CPU 전면 미측정** | `origin/resource-overhead-20261114:...cpu_overhead_summary.csv`, `revA/results/resource/cpu_measurements.csv` | §7 반영 (**단 고컴 `M5_resource_comparison.md`가 `resource-v124`의 분리 측정값을 누락하고 "분리 불가·GC시간 미측정"으로 오기!**) | **`PARTIAL`** |
| **M5-3** | **실행 시간 (벽시계·결정 경로)** | `mixFYF` 90분(5,404 s) 및 `FIO-Fast` 30분(1,800 s) 구간별 경과 시간·결정당 평균/최대 시간(`3.92 µs` / `13.4 µs`) 실측 완료 | `revA`, `resource-v124` | §7 반영 | **`COMPLETE`** (iCAT 한정; SmartGC는 `NOT EXECUTED`) |
| **M5-4** | **GC 실행 시간 (`do_gc`)** | `resource-v124` FIO-Fast 30분(n=3)에서 `do_gc - on_gc` 실측 존재(CAT-47 `255.98 s`, iCAT v4 `206.84 s`, v1 `196.89 s`, v2 `200.32 s` — **단 에뮬레이터 `erase=0`·데이터 미복사 매핑 시간**). **`mixFYF` 및 `SmartGC`에서는 전면 미측정!** | `origin/resource-overhead-20261114:...cpu_overhead_summary.csv` | 미반영 (고컴 M5 보고서가 "미측정"으로 누락) | **`PARTIAL`** (`mixFYF`/SmartGC `NOT EXECUTED`, 실SSD GC 시간은 `PAPER LIMITATION`) |
| **M5-5** | **지연 시간 (I/O latency)** | 고컴 `revA` mixFYF(n=3) FIO clat p50/p99 및 YCSB READ/UPDATE 평균·p99·처리량 실측 완료(**불리한 결과 확인**: Phase C FIO p99에서 V4 `122.0 µs` > Random `102.6 µs`, `+19.5 [+15.1, +23.8] µs`). 단 `erase=0` 에뮬레이터 한계, `mixY` SmartGC 지연은 채널 포화로 `INVALID` | `result/final-revision-analysis/latency_comparison.csv`, `report/reanalysis-20261124/r3_io_latency_summary.csv` | §7 반영 | **`PARTIAL`** (에뮬레이터 한계·SmartGC 지연 무효) |
| **M5-6** | **측정 도구의 정확성 검증** | `res-v4` 타이머 오버헤드(`18.00 ns/GC` CAT-47 차분) 정량화 완료, `ktime` vs CPU 시간 구분 명시, `schedstat` busy-poll 한계 검증 완료, 계측 vs 비계측(`perf-20261119`) 비교 존재 | `origin/resource-overhead-20261114:result/resource-v124-20261114/report/measurement_methodology.md`, `perf-20261119` | §7에 `ktime` 단서 반영 | **`COMPLETE`** (단 `perf`/`task_cputime` 미적용 한계 명시) |

---

### M6. 파라미터 민감도 및 적응 성능 — 8개 세부 항목

| ID | 항목 | 코드 기본값 | 측정 수준 / 근거 | 원시 경로 | 통계 | 논문 반영 | 최종 판정 |
|---|---|---|---|---|---|---|---|
| **M6-1** | **후보 제거 문턱 (`ELIM_Q16`)** | 15% | `10% / 15% / 25%` (`revC`, n=3) + 오프라인 24스윕 재생 | `result/revC-20261124/raw/` | 완료 (10% `+0.024 [−0.043, +0.091]`, 25% `+0.051 [−0.010, +0.111]`, CI 0 포함, 15% 최저 평균 `2.1200`) | 반영 (§6.4 표 10) | **`COMPLETE`** |
| **M6-2** | **후보 공간 크기 (`ARM_LO`, m5)** | 45개 (`k=2` 제외) | 3×60 전체 스윕(`test4/oltp/sqlite-a`) + `revC` 60 vs 45 (n=3) | `result/sweep-20260915/`, `result/revC-20261124/raw/` | 완료 (`+0.0282 [−0.0324, +0.0888]`, CI 0 포함, k=2 제거 손실 없음) | 반영 (§6.4 표 10) | **`COMPLETE`** |
| **M6-3** | **변화 감지 문턱 (`DRIFT_Q16`)** | 25% | ① `12.5%` (`revE-drift12`): **진행 중 (2/3 VALID: `2.1624 / 2.2148`, Phase B 조기 리셋 실측 확인, 3/3 ~01:05 KST)**<br>② **`50%` (상향 민감도)**: **미실행** | `result/revE-20261125/raw/` | 아직 n=2 (`revE` 완료 시 12.5% vs 25% 확정) | 표 10 `【결과 대기】` | **`PARTIAL`** (12.5% 진행 중, 50% `NOT EXECUTED`) |
| **M6-4** | **판단 구간 크기 (`WINDOW_HOST/GC`)** | 512 MiB / 128 GC | 계획서만 존재 (`result/revE-20261125/window_plan.md`, 미승인) + 오프라인 창 잡음 SD 5.5–7.1% 계산 | 없음 (미실행) | 없음 | 한계 4에 "미측정 경험적 설정" 명시 | **`NOT EXECUTED`** |
| **M6-5** | **할인 계수 (`GAMMA_Q16`)** | 0.9995 (반감기 1,376창) | `γ=1.0` on/off (`abl-nodiscount`) 진행 중(2/3, ~00:50 KST); **반감기 축소 민감도(예: ×1/4, ×1/16)는 미실행** | `result/revision-additional-ablation/raw/` | 아직 n=2 (수준별 민감도는 없음) | 한계 4·5에 명시 | **`PARTIAL`** (on/off 진행 중, 수준별 민감도 `NOT EXECUTED`) |
| **M6-6** | **정착 조건 (`STABLE=12 / 확인=3 / 0.5%`)** | 12 / 3 / 0.5% | 수준별 민감도 실행 0건 (오직 `NoSettle` off만 `revB` 교차배치로 시도) | 없음 | 없음 | 한계 4에 "미측정 경험적 설정" 명시 | **`NOT EXECUTED`** |
| **M6-7** | **재탐색/탐침 주기 (`PROBE=8`, `STALE=240`, `DRIFT_WIN=3`, `UCB c=0.25`)** | 8 / 240 / 3 / 0.25 | 실행 0건 (9월 `v4noprobe` 1회 무효/미반복 외 없음) | 없음 | 없음 | 한계 4에 "미측정 경험적 설정" 명시 | **`NOT EXECUTED`** |
| **M6-8** | **적응 및 회복 시간 (E3)** | 감지·재탐색·재정착·회복 | `revA`, `revC`, `revD` 파티션 단위 실측 완료: Phase C 감지 61–63 s (3배치 재현), 재정착 V4 340–500 s vs FullReset 1,182 s. **한계**: ① Phase B 저쓰기 전환은 대부분 미감지(0–2파티션, 10–16분), ② 사전 정의 회복 시간은 자기 후반 WAF 기준이라 `NoDrift`가 333 s로 가장 짧게 나오는 역설 → "더 빠른 적응/회복" 통계적 우위 미입증 | `result/final-revision-analysis/adaptation_*.csv`, `report/reanalysis-20261124/r1_adaptation_*.csv` | 기술 통계 완료, 우위 CI 미달 | 반영 (§6.4 표 11) | **`PARTIAL`** |

---

### M7. 환경 일반화 — 5개 세부 항목

| ID | 항목 | 현재 검증 범위 | 미검증 범위 | 논문 반영 | 최종 판정 |
|---|---|---|---|---|---|
| **M7-1** | **SSD 용량** | 8 GiB 단일 구성 | 16/32/64 GiB+, 실제 대용량 SSD | §7, §8 한계 5 명시 | **`PAPER LIMITATION`** (`NOT EXECUTED`) |
| **M7-2** | **오버프로비저닝 (OP)** | OP 7% 단일 구성 | OP 14% / 20% / 28% | §7, §8 한계 5 명시 | **`PAPER LIMITATION`** (`NOT EXECUTED`) |
| **M7-3** | **NAND 구성** | MLC 타이밍, **erase 지연 0**, 4파티션 | TLC/QLC, 비영 erase 지연, 실물 NAND | §7, §8 한계 5 명시 | **`PAPER LIMITATION`** (`NOT EXECUTED`) |
| **M7-4** | **워크로드 일반화** | `n=3` 통계 검증은 **`mixFYF` 1종** 중심 (단일 8종·전환 6~7종은 대부분 n=1~2, SQLite 전환 5종은 무효 제외) | 실제 서버/클라우드 트레이스, 다수 전환 워크로드 n=3 | §7, §8 한계 2·5·7 명시 | **`PARTIAL`** (실서버 트레이스는 `PAPER LIMITATION`) |
| **M7-5** | **NVMeVirt 설정** | conventional page-mapping FTL, ext4 `nodiscard`, 최대 10시간 | discard 활성, ZNS/다른 FTL, 장시간(>10h), 물리 SSD | §7, §8 한계 5 명시 | **`PAPER LIMITATION`** (`NOT EXECUTED`) |

---

## B. 아직 실행하지 않은 실험 목록 *(Random Search·Periodic Switching 제외)*

| 우선순위 | 심사 요구사항 | 필요한 실험 | 기존 결과 재사용 가능 여부 | 담당 컴퓨터 | 예상 시간 |
|---|---|---|---|---|---|
| **P0 (자동 대기 중)** | **M3-3**: Online Greedy vs V4 | `greedy-20261125` (`ICAT_VARIANT=8`, `mixFYF` n=3) — 이미 빌드·승인 완료, `abl` 종료(~00:50) 직후 자동 시작 | 주 대조군 `revD-v4`(n=3, 11-24) 재사용 예정(보조 `abl-v4`). **단 브리지 CI `[−0.049, +0.050]`이 `±0.02` 초과하므로 엄격 동일배치 원하면 `greedy-v4` 3회 추가(+4.6h) 필요** | **승컴** | **4.7 h** (Greedy 3회)<br>*(동일배치 V4 추가 시 9.4 h)* |
| **P1 (핵심 누락)** | **M1-3/4/5/6 & M5-2/4**: SmartGC 알고리즘 CPU·정책결정·Q-table갱신·`do_gc` 시간 실측 비교 | **SmartGC-EQ8 vs iCAT-v4 `ktime` 계측 비교** (`smartgc_step`/`smartgc_select`/Q-table 갱신/`do_gc`에 `ktime_get_ns()` 삽입, `mixFYF` 90분 또는 `FIO-Fast` 30분에서 **동일 조건 n=3** 측정 — `mixY` 10h 3회는 60시간 이상이라 비현실적) | 불가 (`smartgc-src`에 시간 계측 코드 전무; `mixY`는 소스 트리 불일치 + 채널 포화 + n=1) | **고컴** (`revE` 종료 후) | **~5.0 h** (FIO-Fast 30분 × 2정책 × n=3 + 빌드/smoke) 또는 **~9.5 h** (`mixFYF` 90분 × 2정책 × n=3) |
| **P1 (핵심 누락)** | **M1-7/9**: SmartGC vs iCAT-v4 WAF 통계 반복 (`n=3`) | 위 P1을 **`mixFYF` 90분(n=3)**으로 통합 실행하면 **M1 CPU/결정/갱신/GC시간 + M1 WAF n=3 통계 + M1 Vmalloc_delta(EQ8)**를 한 번에 해결 가능! | 기존 `mixY` 10h n=1은 장시간 보조 참고값으로 유지(합산 불가) | **고컴** (`revE` 종료 후) | **~9.5 h** (P1 통합 실행 시) |
| **P2 (권장)** | **M6-4**: 판단 구간 크기 민감도 (`WINDOW_HOST_PAGES/GC`) | 고컴 `result/revE-20261125/window_plan.md` 실행 (`256 MiB/64 GC` & `1 GiB/256 GC`, `MAX_WINDOW_NS=600s`, `mixFYF` n=3) | `revE-v4`(n=3) + 브리지 1회 재사용 가능(최소안 7 run) | **고컴** | **11.0 h** (최소안) / **14.0 h** (엄격안) / **6.2 h** (1 GiB 단독) |
| **P2 (선택)** | **M4-1**: 본문 `표 6·그림 7` 전환 워크로드 고정 조합 반복 보강 | `PAPER_KCI_DRAFT.md`에 명시된 `【결과 대기: arm 47·17·50 각 3회】` (특히 `OLTP→Varmail` 1종만이라도 n=3 확보, 또는 본문에서 자리표시자 제거 후 n=1 탐색적 비교로 정정) | 기존 `OLTP→Varmail` iCAT-v4 n=3 존재; 고정 arm 47/17/50은 n=1뿐 | 승컴 또는 고컴 | **~4–6 h** (또는 원고 정정 시 **0 h**) |
| **P3 (선택)** | **M5-2/4**: `mixFYF` 전환 부하 재탐색 구간 `res-v4` 분리 CPU/GC 계측 (11-23 계획 E3) | `res-v4` (`observe`/`choose`/`set_arm`/`on_gc`/`do_gc` 분리 계측 빌드) `mixFYF` 1~3회 | FIO-Fast 30분 `resource-v124` (n=3)은 이미 존재하므로, 전환 부하 실측 필요 시에만 | 승컴 | **1.6 h** (n=1) / **4.7 h** (n=3) |
| **P3 (선택)** | **M6-3**: 변화 감지 문턱 상향 수준 (`50%`) | `WATGC_V2_DRIFT_Q16=32768ULL` (`mixFYF` n=3) | `revE-v4` 및 `revE-drift12`(12.5%)와 비교 | 고컴 | **4.7 h** |
| **P3 (선택)** | **M2-2**: 정착 단독(`NoSettle`, `VARIANT=5`) 동일 배치 재실행 | `revE` 직후 `nosettle` vs `v4` n=3 — 단 코드 구조상 감지·probe도 함께 꺼지므로 완전한 단독 분리는 불가 | `revB-nosettle`은 교차배치 + SD 0.079로 CI 0 포함 | 고컴 | **4.7–9.4 h** (구조적 한계로 효용 낮음) |
| **P4 (선택/보류)** | **M3-5**: `mixFYF` 250k Greedy GC 기준선 | `nvmev-greedy` `mixFYF` n=3 | 레거시 9종(`x1` n=3) 존재하나 `mixFYF`·`iCAT-v4` 동일조건 n=3은 0건 | 승컴 또는 고컴 | **4.7 h** |
| **제외 (한계 명시)** | **M6-5/6/7**: γ 수준별, 정착 조건, `c=0.25`, `PROBE=8`, `STALE=240` & **M7-1~5**: 실SSD/용량/OP/NAND | 다수 조합(수십 시간 소요) 또는 에뮬레이터 구조 한계 | — | 미실행 | **0 h** (논문 한계 명시) |

---

## C. 일부만 수행한 실험 목록 (완료된 지표 vs 누락된 지표)

1. **M1 SmartGC 비교 (`result/smartgc-20261119/`, `result/gc-20261010/`)**
   - **완료**: 이론적 메모리(`gdb sizeof` 193×/232×), `mixY` 10h WAF (`n=1`, `-28.5%`), Varmail 처리량 (`n=1`).
   - **누락**: **① SmartGC 알고리즘 CPU / 정책결정 / Q-table 갱신 / `do_gc` 시간 전면 미측정**, **② 독립 반복 `n=3` 및 통계(SD/CI/Welch) 전무**, **③ 대표 모델 `SmartGC-EQ8`의 커널 `VmallocUsed_before` 누락**, **④ FIO 지연은 채널 모델 포화 경고(21만~353만 줄)로 오염**, **⑤ `SmartGC`(`smartgc-src`)와 `iCAT-v4`(`online-v4-src`)의 소스 트리 불일치**.
2. **M2-1/2/3/6 iCAT 메커니즘 Ablation (`revA/revB/revD/abl/revE`)**
   - **완료**: `FullReset` vs `V4` (`revD` n=3, CI>0, 단 Holm 경계), 묶음 `VARIANT=2` (`revA`·`abl` 2호스트 모두 n=3 CI>0).
   - **진행 중**: 단독 `NoElim` (`revE` 6/9 완료, `rep3` 3회 남음 ~04:10), `Discount-free` (`abl` 8/9 완료, `rep3` 1회 남음 ~00:50).
   - **누락**: **① `NoSettle` 단독 효과**(동일 배치 없음 + 코드상 감지·probe 종속 + CI 0 포함), **② `NoDrift` 통계적 우위**(2호스트 모두 3/3 열위이나 분산 커서 n=3에서 CI 0 포함).
3. **M3 온라인 정책 선택 (`revA`, `revC`, `greedy-20261125`)**
   - **완료**: 고컴 `Random Selection` vs `V4` (n=3 PASS), 고컴 `원래 iCAT` vs `V4` (n=3 PASS), 레거시 9종 `Greedy GC` vs `iCAT-online` (n=3 PASS).
   - **누락**: **① `Online Greedy` 아직 0/3 (승컴 ~00:50 자동 시작 대기)**, **② `Random`/`원래 iCAT`(고컴)과 `Online Greedy`(승컴)의 단일 호스트 직접 비교 불가**, **③ 승컴 `greedy`의 동일 배치 `V4` 대조군 미포함(`abl-v4 − revD-v4` 브리지 CI `±0.050` > `±0.02` 기준 초과)**, **④ `mixFYF` Greedy GC 0회**.
4. **M4 통계적 신뢰성 (`revA/B/C/D` vs 본문 표 6·7·8·9·A1)**
   - **완료**: `mixFYF` 44회 원시 재계산·Welch CI·짝 CI·Holm 보정·실패 run(`SQLITE_FULL`) 제외.
   - **누락**: **① 본문 `표 6·표 7`(고정 arm 3배 전부 n=1, v4 대부분 n=1~2), `표 9`(SmartGC n=1), `표 A1`(5종 n=1) 반복 부재**, **② `PAPER_KCI_DRAFT.md`에 `【결과 대기】` 등 미완성 자리표시자 15곳 잔존(특히 표 8 "30만 레코드" 불일치, 표 10에 `abl` 행 누락)**.
5. **M5 시스템 오버헤드 (`revA`, `resource-v124`)**
   - **완료**: 메모리 `sizeof` (10,112 B), `revA` mixFYF 결정경로 `ktime` (`3.88 ms`), `resource-v124` FIO-Fast 30분 분리 계측(보상갱신 `1.442 ms`, 선택 `1.273 ms`, `set_arm` `0.059 ms`, `on_gc` 순비용 `9.43 ns/GC`, 에뮬레이터 `do_gc` `206.8 s`), `revA` FIO/YCSB 지연 (`n=3`, FIO p99 `+19.5 µs` 불리 확인).
   - **누락**: **① SmartGC CPU/결정/갱신/GC시간**, **② `mixFYF` 전환 구간 재탐색 분리 CPU·`do_gc` 시간**, **③ 실제 스레드 CPU 시간(`task_cputime`/perf) 및 실SSD GC 시간(erase=0)**.
6. **M6 파라미터 민감도 및 적응 성능 (`revC`, `revD`, `revE`, `abl`)**
   - **완료**: 제거 문턱 10/15/25% (`revC` n=3), 후보 60 vs 45 (`revC` n=3), 복원 범위 (`revD` n=3), Phase C 감지·재정착 시간 실측.
   - **진행 중**: 감지 문턱 12.5% (`revE-drift12` 2/3).
   - **누락**: **① 판단 구간 512 MiB 민감도(미승인·미실행)**, **② 감지 문턱 50%**, **③ 할인율 수준별 민감도(반감기 축소)**, **④ 정착 조건·UCB `c`·`PROBE`·`STALE` 민감도**, **⑤ Phase B 저쓰기 전환 감지(대부분 미감지) 및 회복 시간 통계 우위**.

---

## D. 잘못 완료 처리한 항목 (기존 보고서 vs 실제 증거 불일치)

| # | 항목 | 기존 보고서의 잘못된 완료 표시 | 실제 독립 감사에서 발견된 증거 결함 | 올바른 판정 |
|---|---|---|---|---|
| **D1** | **M1 SmartGC 비교** | 고컴 `review_evidence_and_status.md`: `실험 완료 ✔ (n=1) / 데이터 검증 ✔ / 논문 반영 ✔` | ① **CPU·정책결정·Q-table갱신·`do_gc` 시간 4개 지표 전면 미측정**, ② **독립 반복 `n=3` 및 통계 0건(`n=1`)**, ③ **대표 `EQ8`의 `VmallocUsed_before` 누락**, ④ **지연은 채널 모델 포화 경고(21만~353만 줄)로 오염**, ⑤ **`smartgc-src` vs `online-v4-src` 소스 트리 불일치** | **`PARTIAL / INSUFFICIENT`** (`CPU·반복`은 `NOT EXECUTED`, 지연은 `INVALID`) |
| **D2** | **M5 시스템 오버헤드 (고컴 보고서 누락 + 과대 완료)** | 고컴 `review_evidence_and_status.md`: `실험 완료 ✔ / 데이터 검증 ✔ / 논문 반영 ✔`<br>고컴 `M5_resource_comparison.md` §7: `"GC 수행 시간 미측정, 선택과 갱신 시간 분리 불가"` | ① **이중 오류 발견**: 승컴 `origin/resource-overhead-20261114:result/resource-v124-20261114/report/cpu_overhead_summary.csv`에 **보상갱신(`1.442 ms`)·정책선택(`1.273 ms`)·`set_arm`(`0.059 ms`)·에뮬레이터 `do_gc`(`206.84 s`)**이 이미 n=3으로 분리 실측되어 있는데 고컴 M5 보고서가 이를 누락함! ② 반대로 **SmartGC CPU/GC시간 및 `mixFYF` 전환 구간 분리 계측은 실제 미실행**인데 전체 M5를 `✔`로 완료 처리함 | **`PARTIAL`** (기존 `resource-v124` 분리값 반영 + SmartGC/mixFYF 누락 명시 필요) |
| **D3** | **M4 통계적 신뢰성** | 고컴 `review_evidence_and_status.md`: `실험 완료 ✔ / 데이터 검증 ✔ 44/44 / 논문 반영 ✔` | `mixFYF` 44회만 완료일 뿐, **논문 본문 `PAPER_KCI_DRAFT.md`에는 `표 8`("YCSB-A 30만 레코드", 전부 "대기")·`그림 10`(대기)·`표 6·7`(고정 arm 3배 n=1, `【결과 대기: arm 47·17·50 각 3회】`)·`표 9`(SmartGC n=1)·`표 A1`(5종 n=1) 등 미완성·미반복·불일치 자리표시자 15곳이 그대로 남아 있음** | **`PARTIAL`** |
| **D4** | **M2 후보 제거 (`revB-noelim`)** | 고컴 `revision_claim_evidence_matrix.md` (11-23): `후보 제거가 WAF를 낮춘다 → 입증` | `revB-noelim` vs `revA-v4`는 날짜가 다른 **교차 배치**이며, 같은 배치 연결용 `revB-v4`(n=1, `2.1520`)가 `revA-v4` 대비 `+4.8 SD`로 브리지 불합격 → 이후 `revE`로 재실험 중이므로 현재 시점은 미완료 | **`PARTIAL`** (`revE` 완료 대기) |
| **D5** | **M3 Online Greedy 대조군 재사용 전제** | 승컴 `greedy-20261125` 승인 전제: `abl-v4 − revD-v4` CI가 `[−0.02, +0.02]` 이내일 때만 `V4` 재사용 | 방금 완료된 `abl-v4` (`2.1390 ± 0.0228`, n=3) vs `revD-v4` (`2.1386 ± 0.0082`, n=3)의 실제 Welch 95% CI는 **`[−0.0493, +0.0502]`** (`|Δ|=0.0004`이나 폭이 `±0.02` 초과). `ba507d385`에 따라 `greedy`는 자동 시작되지만, 동일 배치 대조 기준은 미충족 상태이므로 보고 시 교차 날짜 단서 또는 `greedy-v4` 3회 보강 결정 필요 | **`NOT EXECUTED (CAUTION)`** |
| **D6** | **집컴 기존 `evidence_matrix.xlsx`의 `M4(CORE) PASS`** | 집컴 14:01 갱신: `M4 (CORE) PASS`, `M6 E6 ELIM PASS`, `m5/E7 PASS` | `revC` 15/15 한정으로는 정확하나, 논문 전체 M4(표 6·7·8·9·A1) 및 M6 전체(판단구간·감지문턱·정착·할인) 기준으로 혼동 여지가 있으므로 본 전수조사 기준으로 엄격 하향 정정함 | **`PARTIAL`** (세부 `M6-1/M6-2`만 `COMPLETE`) |

---

## E. 추가 실험 실행 계획 (충돌 방지 3컴퓨터 분산, 사용자 승인 후 실행)

### 현재 실행 중 / 자동 연계 큐 (절대 중단·변경 금지)

| 컴퓨터 | 현재 실행 중 | 자동 후속 대기 | 종료 예상 |
|---|---|---|---|
| **승컴** | `abl-20261125` **8/9 완료** (마지막 9/9 `abl-nodiscount rep3` 진행 중) | `greedy-20261125` (`greedy-online` n=3, ~4.7h) 자동 시작 | `abl` **~11-26 00:50**, `greedy` **~11-26 05:30 KST** |
| **고컴** | `revE-20261125` **6/9 완료** (`revE-drift12 rep3`, `revE-v4 rep3`, `revE-noelim rep3` 3회 남음) | 없음 (04:10 KST 이후 유휴!) | **`revE` ~11-26 04:10 KST** |

### 오늘 승인·실행 검토 대상 추가 실험 (장치 충돌 0건)

| 단계 | 담당 컴퓨터 | 실행 항목 | 해결되는 심사 요구사항 | 선행 조건 | 예상 시간 | 권장 여부 |
|---|---|---|---|---|---|---|
| **안 1 (최우선 권장)** | **고컴** | **SmartGC-EQ8 vs iCAT-v4 `ktime` 계측 + 반복 비교** (`smartgc-src`와 동일 베이스에 `smartgc_step`/`select`/Q-update/`do_gc` `ktime` 삽입 + `mixFYF` 90분 n=3, 또는 `FIO-Fast` 30분 n=3) | **M1-3/4/5/6 (SmartGC CPU·결정·갱신·GC시간)** + **M1-7/9 (WAF n=3 통계)** + **M1-2 (EQ8 Vmalloc_delta)** + **M5-2/4** — 현재 가장 큰 미실행 구멍 일괄 해소! | 고컴 `revE` 종료 (~11-26 04:10 KST) | **~5.0 h** (FIO-Fast 30m n=3) 또는 **~9.5 h** (`mixFYF` 90m n=3) | **강력 권장** (SmartGC `PARTIAL→COMPLETE` 핵심) |
| **안 2 (권장)** | **승컴** | **Option 2A**: `greedy-20261125` 종료 직후 `greedy-v4` 3회 보강 (교차 날짜 단서 제거, `abl-v4 − revD-v4` CI `±0.050` 보완)<br>**Option 2B**: `res-v4` `mixFYF` 1~3회 (전환 부하 재탐색 분리 CPU/GC 실측) | **M3-3 / M4-8** (완벽한 동일 배치 `Greedy vs V4`)<br>**M5-2/4** (전환 부하 분리 CPU) | 승컴 `greedy` 종료 (~11-26 05:30 KST) | 2A: **4.7 h** / 2B: **1.6–4.7 h** | **선택 권장** (2A는 동일배치 엄격성 확보, 생략 시 교차날짜 명시) |
| **안 3 (시간 여유 시)** | **고컴** | **M6-4 판단 구간 민감도** (`window_plan.md`: 256 MiB / 1 GiB, `MAX_WINDOW_NS=600s`, `revE-v4` 재사용 최소안) | **M6-4** (판단 구간 512 MiB 실측 검증) | 고컴 안 1 종료 후 (또는 안 1 대신) | **11.0 h** (최소안) / **6.2 h** (1 GiB 단독) | **선택** (미실행 시 한계 4 유지 가능) |
| **안 4 (집컴 무비용 즉시 작업)** | **집컴** | ① `abl`(00:50)·`revE`(04:10)·`greedy`(05:30) 완료 즉시 7개 항목 독립 검증<br>② `resource-v124` 분리 측정값(보상갱신/선택/GC시간) M5 통합 반영<br>③ `iCAT_Paper_Figures.xlsx`·Figure 일괄 갱신<br>④ `PAPER_KCI_DRAFT.md` **15개 `【...】` 자리표시자·표 8 불일치·표 10 누락·참고문헌 [12]·MB/MiB 통일** 전수 수정안 작성 | **M4-8, M5-2/4, 원고 일관성** | 각 캠페인 완료 커밋 도착 | **~1 h** (NVMeVirt 미사용) | **필수 (즉시 자동 수행)** |

---

## F. 최종 리비전 완료율 (최초 심사 요구사항 47개 세부 항목 기준)

### 1. 현재 시점 (2026-11-25 23:55 KST, 진행 중 캠페인 미완료 기준)

| 대분류 | 세부 항목 수 | `COMPLETE` | `ANALYSIS ONLY` | `PARTIAL` | `INSUFFICIENT` | `INVALID` | `NOT EXECUTED` | `PAPER LIMITATION` | 엄격 충족률 (`COMPLETE`만) | 실질 대응률 (`COMPLETE`+`ANALYSIS`+`LIMITATION` 합의분) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **M1 SmartGC** | 9 | 0 | 1 | 0 | 2 | 1 | 5 | 0 | **0.0%** (0/9) | **11.1%** (1/9) |
| **M2 메커니즘** | 6 | 1 | 0 | 4 | 1 | 0 | 0 | 0 | **16.7%** (1/6) | **16.7%** (1/6) |
| **M3 온라인 선택** | 5 | 2 | 0 | 2 | 0 | 0 | 1 | 0 | **40.0%** (2/5) | **40.0%** (2/5) |
| **M4 통계 신뢰성** | 8 | 6 | 0 | 2 | 0 | 0 | 0 | 0 | **75.0%** (6/8) | **75.0%** (6/8) |
| **M5 시스템 오버헤드** | 6 | 2 | 0 | 4 | 0 | 0 | 0 | 0 | **33.3%** (2/6) | **33.3%** (2/6) |
| **M6 파라미터·적응** | 8 | 2 | 0 | 3 | 0 | 0 | 3 | 0 | **25.0%** (2/8) | **25.0%** (2/8) |
| **M7 환경 일반화** | 5 | 0 | 0 | 1 | 0 | 0 | 0 | 4 | **0.0%** (0/5) | **80.0%** (4/5 한계 명시) |
| **전체 합계** | **47** | **13** | **1** | **16** | **3** | **1** | **9** | **4** | **27.7%** (13/47) | **38.3%** (18/47) |

### 2. 시나리오별 예상 충족률 변화 (47개 세부 항목 기준)

| 시나리오 | 예상 `COMPLETE` | 예상 실질 대응률 (`COMPLETE`+`ANALYSIS`+`LIMITATION`) | 핵심 해소 항목 |
|---|---:|---:|---|
| **현재 (23:55 KST)** | **13 / 47 (27.7%)** | **18 / 47 (38.3%)** | `revA/revC/revD` 완료 |
| **현재 큐 자동 종료 후 (내일 05:30 KST: `abl` + `revE` + `greedy` 완료)** | **16 / 47 (34.0%)** | **21 / 47 (44.7%)** *(미실행 파라미터 3종 한계 명시 시 **51.1%**)* | M2-1(단독 `NoElim`), M2-6(`Discount-free`), M3-3(`Online Greedy`), M6-3(`drift12`) 해소 |
| **+ 고컴 안 1 (SmartGC `ktime` 계측 + n=3 반복, ~9.5 h) + 집컴 원고·M5 정리 완료 시** | **24 / 47 (51.1%)** | **33 / 47 (70.2%)** *(한계 명시 항목 포함 시 핵심 심사 요구사항 대응 완료)* | **M1 SmartGC 6개 구멍 + M5-2/4 + M4 원고 정합성 일괄 해소!** |
| **+ 고컴 안 3 (`window_plan` 판단구간, ~11 h) + 승컴 안 2A (`greedy-v4`, ~4.7 h) 추가 시** | **26 / 47 (55.3%)** | **36 / 47 (76.6%)** | M6-4 판단구간 + M3-3 완벽 동일배치 추가 해소 |

---

## 결론: 오늘 가장 시급한 의사결정 3가지

1. **최우선 누락 발굴**: 기존 보고서가 `✔`로 완료 처리한 **M1 SmartGC**는 실제로는 **9개 지표 중 5개가 `NOT EXECUTED`, 2개가 `INSUFFICIENT`, 1개가 `INVALID`**입니다. 내일 새벽 고컴 `revE` 종료(~04:10 KST) 직후 **안 1 (SmartGC-EQ8 vs iCAT-v4 `ktime` 계측 + n=3 반복)**을 실행할지 여부가 이번 리비전 완성도를 가르는 가장 큰 분기점입니다.
2. **M5 오기 정정**: 승컴 `resource-overhead-20261114` 브랜치에 이미 **보상갱신·정책선택·`set_arm`·에뮬레이터 `do_gc` 시간(n=3)**이 분리 실측되어 있는데 고컴 M5 보고서가 이를 누락하고 "미측정/분리 불가"로 적었습니다. 집컴에서 원시 CSV 기준으로 즉시 통합 정정할 수 있습니다.
3. **논문 원고 미완성 잔존**: `PAPER_KCI_DRAFT.md`에 **`【결과 대기】` 등 15개 자리표시자**, `표 8`의 구버전("30만 레코드") 불일치, `표 10`의 `abl` 행 누락이 남아 있으므로, 내일 새벽 `abl`/`revE`/`greedy` 완료 직후 집컴에서 전수 대조·정합성 검증을 완료해야 합니다.


---

## G. 사후 갱신 및 정정 기록 (2026-11-26 06:10 KST — `abl`/`revE`/`greedy` 완료 및 `m1-20261126` 착수 반영)

> 본 섹션은 `AGENTS.md` 정정 원칙에 따라 위 2026-11-25 23:55 KST 원본 감사 기록을 보존한 채, 이후 완료되어 3자(승컴·고컴·집컴) 독립 원시 로그 검증을 통과한 3개 캠페인(`abl-20261125`, `revE-20261125`, `greedy-20261125`)과 신규 착수 캠페인(`m1-20261126`)의 상태 변화를 반영한다.
> - 기준 커밋: 승컴 `origin/main` **`84af5fac6`**, 고컴 `origin/report/data-validity-20261124` **`f2635f103`**, 자원 `origin/resource-overhead-20261114` **`c046de0d0`**

### 1. 판정 변경 항목 (3개 항목 `COMPLETE` 승격 + `M6-3`·`M1` 진척)

| ID | 기존 판정 (11-25 23:55) | 갱신 판정 (11-26 06:10) | 독립 검증 완료 근거 |
|---|---|---|---|
| **M2-1** (후보 제거 단독 `NoElim`) | `PARTIAL` | **`COMPLETE`** | 고컴 `revE-20261125` 9/9 VALID! 동일 배치 단독 `revE-noelim` (`VARIANT=3`, `2.2048 ± 0.0052`) − `revE-v4` (`2.1135 ± 0.0261`) = **`+0.0913 [+0.0296, +0.1530]`** (`g=+3.88`, 짝 CI `[+0.0139, +0.1687] > 0`, Phase C `+0.1548 [+0.0300, +0.2795]`). `revB` 교차배치 단서 영구 해소(4대비 Holm `p=0.0907` 민감도 명시). |
| **M2-6** (할인 계수 `γ=1.0`) | `PARTIAL` | **`COMPLETE`** | 승컴 `abl-20261125` 9/9 VALID(3자 검증 일치)! 동일 배치 `abl-nodiscount` (`2.1353 ± 0.0291`) − `abl-v4` (`2.1390 ± 0.0228`) = **`−0.0038 [−0.0644, +0.0569]`** (`Holm p=1.000`, Phase C `−0.0099`). 정직한 null 결과(이론 R2 `γ^250=0.882`와 일치), 표 10 배치 F 반영 완료. 동 배치 묶음 끔(`OffBundle`)도 `+0.1241 [+0.0730, +0.1753]` (`Holm p=0.0277`) 확인. |
| **M3-3** (Online Greedy `VARIANT=8`) | `NOT EXECUTED` | **`COMPLETE`** | 승컴 `greedy-20261125` 3/3 VALID(3자 검증 일치)! 집컴 독립 Q16 비율 argmin 검증 **0 / 2,513창 불일치**, `2.1300 ± 0.0198`. `Greedy − revD-v4` = **`−0.0086 [−0.0508, +0.0336]`** (`p=0.54`, Phase C `+0.0167 [−0.0535, +0.0870]`), 보조 `abl-v4` 대비 `−0.0090 [−0.0577, +0.0397]`. **iCAT에 불리한 정직한 null 결과** — "V4가 단순 Greedy보다 낫다"는 주장은 `mixFYF`에서 기각되며 표 10 행 D'에 투명 반영됨(교차 날짜 각주 § 포함). |
| **M6-3** (감지 문턱 `12.5%` / `50%`) | `PARTIAL` | **`PARTIAL`** (12.5% 완료) | 고컴 `revE-drift12` (`12.5%`, `2.1855 ± 0.0267`) − `revE-v4` = **`+0.0720 [+0.0121, +0.1319]`** (`g=+2.18`, Phase C `+0.1476 [+0.0266, +0.2685]`, 3/3 Phase B 조기 리셋 확인, 4대비 Holm `p=0.0907`). 상향 `50%`는 미실행. |
| **M1-2~M1-9** (SmartGC 비교) | 미실행/부족 | **고컴 `m1-20261126` 실행 중** (판정 유지) | 고컴에서 `SmartGC-EQ8` vs `iCAT-v4` `ktime` 계측 + `VmallocUsed` + `mixY 10h` **n=3 (6회 ≈ 60h)** 본 큐 착수! 사용자 공간 `conv_ftl.c` 시뮬 벤치 12/12 OK(불리한 결과: iCAT `53.0 µs/GC` vs SmartGC `7.6 µs/GC` — CAT 전 라인 스캔 비용, 단 WAF는 iCAT `7.16` < SmartGC `9.19`), 커널 `mixY` smoke 2/2 OK, 본 실행 1/6 진행 중(~14:40 KST). **본 실행 6/6 완료 전까지 판정 조기 승격 금지.** |

### 2. 갱신된 47개 세부 요구사항 충족률 (2026-11-26 06:10 KST)
- **`COMPLETE`**: **16 / 47 (34.0%)** *(기존 13 → +3: M2-1, M2-6, M3-3)*
- **`ANALYSIS ONLY`**: **1 / 47 (2.1%)**
- **`PARTIAL`**: **14 / 47 (29.8%)** *(기존 16 → -2)*
- **`INSUFFICIENT`**: **3 / 47 (6.4%)**
- **`INVALID`**: **1 / 47 (2.1%)**
- **`NOT EXECUTED`**: **8 / 47 (17.0%)** *(기존 9 → -1; 단 이 중 M1-3/4/5/6/9 5건은 현재 고컴 `m1-20261126`에서 실행 중)*
- **`PAPER LIMITATION`**: **4 / 47 (8.5%)**
- **실질 대응률 (`COMPLETE + ANALYSIS ONLY + PAPER LIMITATION`)**: **21 / 47 (44.7%)** *(고컴 `m1-20261126` 6/6 완료 시 M1 6~7건이 추가 승격 예정)*
