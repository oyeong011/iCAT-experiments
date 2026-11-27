# iCAT 논문 리비전 최종 종합 실험 보고서 (`FINAL_EXPERIMENT_REPORT.md`)

- **작성 주체**: 집컴 (최종 연구 통합·독립 감사 책임)
- **작성 시각**: `2026-11-27 09:11:23 KST`
- **기준 원격 커밋**: 승컴 `origin/main @ 4689c6797` / 고컴 `origin/report/data-validity-20261124 @ 3fdb21258` / 자원 계측 `origin/resource-overhead-20261114 @ c046de0d0`
- **연결 통합 산출물**: [FINAL_REVIEWER_RESPONSE_MATRIX.xlsx](file:///C:/Users/oyeon/orca/iCAT-experiments/report/final-revision/delivery/FINAL_REVIEWER_RESPONSE_MATRIX.xlsx) · [FINAL_FIGURE_CATALOG.md](file:///C:/Users/oyeon/orca/iCAT-experiments/report/final-revision/delivery/FINAL_FIGURE_CATALOG.md) · [FINAL_PAPER_NUMBER_AUDIT.csv](file:///C:/Users/oyeon/orca/iCAT-experiments/report/final-revision/delivery/FINAL_PAPER_NUMBER_AUDIT.csv) · [iCAT_Paper_Figures.xlsx](file:///C:/Users/oyeon/orca/iCAT-experiments/report/paper-figures/iCAT_Paper_Figures.xlsx)

---

## 1장. 연구 및 실험 개요

본 보고서는 iCAT(온라인 정책 단위 GC 파라미터 학습기, iCAT-v4) 논문 리비전에서 수행된 모든 실험을 원시 로그 기준으로 독립 재검증하고, 최초 심사위원의 요구사항(M1~M7, 47개 세부 항목) 및 3대 핵심 주장에 대한 최종 입증 여부를 판정한 결과다.

- **핵심 검증 원칙**: (1) 원시 로그(`result/`)와 기존 `figs/` 무변경, (2) 호스트(고컴 Ryzen 5 3600XT vs 승컴 Intel i7-7700)·배치·워크로드·레코드 수(250k vs 오염 600k) 엄격 분리, (3) `n<3` 조건 통계적 유의성 미부여, (4) 실측값(`[실측]`)과 이론/계산값(`[계산]`) 엄격 구분, (5) 불리한 결과와 미입증 주장의 정직한 기술.
- **표기 부호 통일**: 본 보고서와 모든 통계표에서 **`Δ = 비교 정책 − 동일 배치 대조군(iCAT-v4)`**로 통일한다. 따라서 양수(`+`)는 비교 정책의 WAF가 더 높음(iCAT-v4 우위), 음수(`−`)는 비교 정책의 WAF가 더 낮음(iCAT-v4 열위)을 뜻한다.
- **최종 무결성 현황**: 핵심 리비전 실행 **80/80 VALID (RUNNING 0건)** + 보조 검증 셋(`resource-v124` 12건, `3×60` 스윕 180건, 레거시 유효 Greedy 9종 54건) 전수 검증 완료. 오염 데이터(`SQLITE_FULL` 224+건, `mixG` 34건, `ENOSPC` 1건) 100% 배제 확인.

---

## 2장. 전체 실험 목록과 목적

| 캠페인 | 호스트 | 워크로드 | 유효/계획 | 검증 목적 (최초 심사 요구사항) | 원시 경로 |
|---|---|---|---:|---|---|
| `revA-20261114` | 고컴 | `mixFYF 250k` (90m) | 13/13 | M3-1 무작위 선택, M2-2 묶음 제거, M2-3 변화 감지, Arm 47 참고(`n=1`) | `origin/report/data-validity-20261124:result/revA-20261114/raw/` |
| `revB-20261122` | 고컴 | `mixFYF 250k` (90m) | 8/8 | M2-1/2 `NoElim`/`NoSettle` 예비 검증 *(브리지 실패 → `revE`로 대체)* | `origin/report/data-validity-20261124:result/revB-20261122/raw/` |
| `revC-20261124` | 고컴 | `mixFYF 250k` (90m) | 15/15 | M3-2 원 구현(`online`), M6-1 제거 문턱(10/15/25%), M6-2 후보 수(60 vs 45) | `origin/report/data-validity-20261124:result/revC-20261124/raw/` |
| `revD-20261124` | 승컴 | `mixFYF 250k` (90m) | 9/9 | M2-3 `NoDrift`, M2-5 부분 복원 vs 전체 45개 재설정(`FullReset`) | `origin/main:result/revD-20261124/raw/` |
| `abl-20261125` | 승컴 | `mixFYF 250k` (90m) | 9/9 | M2-2 v4 4기능 묶음 재현, M2-6 할인 계수 제거(`gamma=1.0`) | `origin/main:result/revision-additional-ablation/raw/` |
| `revE-20261125` | 고컴 | `mixFYF 250k` (90m) | 9/9 | M2-1 동일배치 `NoElim` 단독, M6-3 변화 감지 문턱 12.5% | `origin/report/data-validity-20261124:result/revE-20261125/raw/` |
| `greedy-20261125` | 승컴 | `mixFYF 250k` (90m) | 3/3 | M3-3 단순 Online Greedy (`VARIANT=8`, 0/2,513 규칙 불일치) | `origin/main:result/greedy-20261125/raw/` |
| `batchG-20261126` | 승컴 | `mixFYF 250k` (90m) | 9/9 | M3-5 동일배치 Greedy GC (`n=3`), M6-3 변화 감지 문턱 50% (`n=3`) | `origin/main:result/batchG-20261126/raw/` |
| `arm47-20261127` | 승컴 | `mixFYF 250k` (90m) | 3/3 | 고정 Arm 47(`1.987`) 재현성 검증 (`n=3`, 호스트 분리) | `origin/main:result/arm47-20261127/raw/` |
| `m1-20261126` | 고컴 | `mixY 10h` (20단계) | 2/2 (`n=1`) | M1/M5 SmartGC-EQ8 vs iCAT-v4 동일 환경 `WAF_nand`·`VmallocUsed`·`ktime` | `origin/report/data-validity-20261124:result/m1-20261126/raw/` |
| `resource-v124` | 승컴 | FIO-Fast 30m | 12/12 | M5-1~6 분리 `reward/select/set_arm/do_gc` 경과시간 & 타이머 검증 | `origin/resource-overhead-20261114:result/resource-v124-20261114/` |

---

## 3장. Random Selection 및 기존 iCAT 원 구현 비교

- **무작위 선택 대비 (`M3-1`, 고컴 `revA`, 동일배치 `n=3`)**: `Random` `2.3243 ± 0.0055` vs `iCAT-v4` `2.1284 ± 0.0049` → **`Δ = +0.1959 [+0.1840, +0.2079]`** (`−8.43%`, `Welch p = 2e-6`, `Holm p = 6e-6`, `Hedges' g = 29.89`, `Paired p = 0.00066`). **입증 완료.**
- **기존 iCAT 원 구현 대비 (`M3-2`, 고컴 `revC`, 동일배치 `n=3`)**: `Original iCAT` `2.3951 ± 0.0029` vs `iCAT-v4` `2.1200 ± 0.0294` → **Total `Δ = +0.2751 [+0.2030, +0.3472]`** (`−11.49%`, `Welch p = 0.00353`, `8-test Holm p = 0.0282`, `g = 10.53`), **Phase C `Δ = +0.4466 [+0.2958, +0.5974]`** (`8-test Holm p = 0.0421`). 원 구현은 단계 3 호스트 쓰기의 `97%`를 탐색 조합으로 처리한 반면 `iCAT-v4`는 `22%`로 억제하였다. **입증 완료.**

---

## 4장. Ablation Study (구성 요소 제거 검증)

| 심사 항목 | 비교 (호스트·배치) | Total WAF Δ `[Welch 95% CI]` | Welch p | Holm p | Hedges' g | 최종 해석 |
|---|---|---:|---:|---:|---:|---|
| **M2-2** v4 묶음 제거 (고컴) | `revA-v2 − revA-v4` (동일배치) | `+0.1355 [+0.1167, +0.1543]` | `0.000158` | `0.000316` | `14.78` | **입증 완료** (+6.4%) |
| **M2-2** v4 4기능 묶음 (승컴) | `abl-bundle-off − abl-v4` (동일배치) | `+0.1241 [+0.0730, +0.1753]` | `0.006929` | `0.027716` | `5.90` | **입증 완료** (+5.8%, 양 호스트 재현) |
| **M2-1** 후보 제거 단독 | `revE-noelim − revE-v4` (고컴 동일배치) | `+0.0913 [+0.0296, +0.1530]` | `0.022681` | `0.090724` | `3.88` | **부분 입증** (Paired `p=0.037`, Holm 경계) |
| **M2-5** 부분 vs 전체 복원 | `revD-fullreset − revD-v4` (승컴 동일배치) | `+0.0596 [+0.0160, +0.1033]` | `0.024023` | `0.072069` | `3.08` | **부분 입증** (Phase C `+0.1296`, Holm `0.060`) |
| **M2-3** 변화 감지 단독 | `revA-v1` / `revD-nodrift − v4` | `+0.0787` / `+0.0681` (CI 0포함) | `0.121 / 0.117` | `0.121 / 0.234` | `1.69 / 1.67` | **입증 실패** (3/3 열위이나 분산 과대) |
| **M2-6** 할인 계수 제거 | `abl-nodiscount − abl-v4` (승컴 동일배치) | `−0.0038 [−0.0644, +0.0569]` | `0.869045` | `1.000000` | `−0.12` | **입증 실패** (90분 `gamma^250=0.882` 효과 없음) |
| **M2-2** 정착 단독 (`revB*`) | `revB-nosettle − revA-v4` (교차배치*) | `+0.0868 [−0.1085, +0.2821]` | `0.197062` | `0.197062` | `1.24` | **입증 실패** (코드 종속 + 교차배치 + CI 0포함) |

---

## 5장. 워크로드 적응 실험 (`mixFYF 250k`, 표 11 및 R1 재분석)

- **Phase C(YCSB-A → FIO-Fast) 적응**: `iCAT-v4`는 고컴·승컴 전 배치(`revA/C/D/E/batchG`)에서 단계 3 진입 후 **약 43~79초** 만에 변화를 감지하고, 변화가 발생한 파티션의 제거 후보(평균 `13~17`개)만 부분 복원하여 **282~499초** 내 재정착하였다.
- **전체 재설정(`FullReset`) 및 `NoElim`과의 비교**: `FullReset`은 147개 후보를 복원해 재정착 `1,182 s`·탐색 쓰기 비중 `56%`(vs V4 `27%`), `NoElim`은 재정착 `1,075 s`·탐색 쓰기 비중 `52%`(vs V4 `30%`)가 소요되었다.
- **한계**: Phase B(저쓰기 YCSB-A) 전환은 대부분 미감지되었고, Phase C 첫 5분 WAF에서는 `Online Greedy`(`2.407`)가 `revD-v4`(`2.598`)보다 낮아 "즉각적 회복 속도 우위"는 주장하지 않는다.

---

## 6장. Online Greedy 및 Greedy GC 비교

- **Online Greedy (`M3-3`, 승컴 `greedy-20261125`, `n=3`, 교차날짜 간접)**:
  - `2,513`개 결정 구간 전수에서 Q16 ratio `argmin` 규칙 일치(`0`건 불일치) 확인.
  - `Online Greedy` `2.1300 ± 0.0198` vs `revD-v4` `2.1386 ± 0.0082` → **`Δ = −0.0086 [−0.0508, +0.0336]`** (`p = 0.543`, vs `abl-v4` `−0.0090 [−0.0577, +0.0397]`). **iCAT-v4 우위 입증 실패 — 본문에 정직 보고 필수.**
- **Greedy GC (`M3-5`, 승컴 `batchG-20261126`, 동일배치 `n=3`, 3자 검증 완료)**:
  - `Greedy GC` `2.6293 ± 0.0069` vs `bg-v4` `2.1105 ± 0.0245` → **Total `Δ = +0.5189 [+0.4633, +0.5744]`** (**iCAT −19.73%**, `Welch p = 0.000321`, **`Holm p = 0.001284`**, `g = 23.09`, `Paired p = 0.000918`), **Phase C `Δ = +0.7078 [+0.5882, +0.8274]`** (`Holm p = 0.003822`). 레거시 유효 9종(`n=3`)에서도 9/9 유의(`−7.1% ~ −42.0%`). **WAF 우위 입증 완료.**
  - **불리 보조 결과**: `erase=0` 환경에서 `Greedy GC`의 Phase C FIO 쓰기 지연(`mean 14.2 µs`, `p99 41.9 µs`)이 `bg-v4`(`mean 27.7 µs`, `p99 166.0 µs`)보다 크게 낮다.

---

## 7장. Drift Threshold 및 파라미터 민감도 실험

- **후보 제거 문턱 `ELIM_Q16` (`M6-1`, 고컴 `revC`, `n=3`)**: `15%`(`2.1200`)가 최저 평균이며, `10%`(`+0.0238 [−0.043, +0.091]`)·`25%`(`+0.0507 [−0.010, +0.111]`) 모두 0 포함(안정적 둔감성 입증).
- **후보 공간 크기 `60 vs 45` (`M6-2/m5`, 고컴 `revC` + `3×60` 스윕)**: 전체 WAF `+0.0282 [−0.032, +0.089]`(CI 0 포함), Phase A 초기 비용만 `+3.0%` 유의; 3/3 최종 선택은 45개 내부.
- **변화 감지 문턱 `DRIFT_Q16` (`M6-3`, 12.5% / 25% / 50%)**:
  - **12.5% (고컴 `revE`, 동일배치 `n=3`)**: Phase B 조기 리셋(평균 `1.7`회 vs 대조군 `0.7`회) 유발 → Total **`+0.0720 [+0.0121, +0.1319]`**, Phase C **`+0.1476 [+0.0266, +0.2685]`** (`Holm p = 0.0907` 경계).
  - **50% (승컴 `batchG`, 동일배치 `n=3`, 3자 검증)**: 전체 11회 리셋 모두 변화율 `>50%`(최소 `61.4%`) 검증. Total **`+0.0183 [−0.0445, +0.0812]`** (`Holm p = 0.831`), Phase C **`+0.0418 [−0.0877, +0.1714]`** → 25%와 구분되지 않음.
- **미측정 파라미터**: 판단 구간 크기(512 MiB), UCB 계수(`0.25`), 정착 조건(`12/3/0.5%`), 탐침 주기는 경험적 설정으로 한계에 명시.

---

## 8장. SmartGC 자원 오버헤드 (`m1-20261126` & `resource-v124`)

고컴 `m1-20261126` (`mixY 10h`, `n=1` per policy, `kernel.log.nowarn.gz` 단독 파싱) 독립 검증 결과(`PAPER_KCI_DRAFT.md` 표 9b와 100% 일치):

| 항목 | `iCAT-v4` (`n=1`) | `SmartGC-EQ8` (`n=1`) | 구분 | 해석 |
|---|---:|---:|---|---|
| **호스트 `WAF` / `WAF_nand`** | `3.330` / **`3.330`** (`8.29 TB`) | `4.562` / **`4.553`** (`5.97 TB`) | `[실측]` | iCAT `WAF_nand` **−26.9%** (단 `n=1` 통계 없음) |
| **학습 상태 메모리 (`sizeof`)** | **`10,112 B`** | **`1,951,648 B`** (+버퍼 `393,216 B`) | `[계산]` | 학습 상태 **193.0×** (전체 **231.9×**) 경량 |
| **`VmallocUsed` Δ (`load1s − pre`)** | **`34,848 kB`** (`35,684,352 B`) | **`37,752 kB`** (`38,658,048 B`) | `[실측]` | 차이 **`+2,904 kB`** (이론차 `3,058 KiB`와 5% 내 일치; 언로드 후 `+16 kB`) |
| **GC 1회 `ktime` 경과 시간** | **`98.37 µs`** (`1,342 ms/GiB`) | **`17.84 µs`** (`333 ms/GiB`) | `[실측, 경과]` | **불리 결과:** iCAT이 **5.5× 김** (CAT 전 라인 스캔) |
| **희생 선택 `SELECT` `ktime`** | `87.05 µs/GC` (`9,162 s`, 88.5%) | `1.00 µs/GC` (`103.9 s`, step 제외 `56.3 s`) | `[실측, 경과]` | iCAT GC 비용의 대부분은 학습이 아닌 CAT 스캔 |
| **학습 갱신 `LEARN` `ktime`** | **`4.295 s`** (`40.80 ns/GC`, 0.041%) | **`47.556 s`** (`975.5 µs × 48,751`) | `[실측, 경과]` | 학습 알고리즘 자체는 iCAT이 **11.1× 경량** |
| **커널 CPU 시간 / NVMeVirt 공통 비용** | **미측정** | **미측정** | `[미측정]` | busy-poll·`perf` 부재; `ktime`과 CPU 시간 엄격 구분 |

- 별도 승컴 `resource-v124` (FIO-Fast 30m, `n=3`, `erase=0`)에서 iCAT-v4 분리 경과시간은 `reward 1.442 ms`, `select 1.273 ms`, `set_arm 0.059 ms`, 학습기 제외 `do_gc` `206.84 s` (CAT-47 `255.98 s`)로 확인되었다.

---

## 9장. Robustness 및 고정 Arm 47 검증

- **고정 Arm 47 `mixFYF` `n=3` (승컴 `arm47-20261127`, `4689c6797`)**: **`1.987644 ± 0.000268`** (`95% CI [1.986980, 1.988309]`, `CV = 0.013%`; `A 1.77430 / B 1.03098 / C 2.27865`). 기존 고컴 `revA` 단일 실행(`1.987355`)이 승컴 `n=3` CI 내부에 들어가 극도의 재현성이 입증되었다 *(호스트가 다르므로 `n=4`로 합산 금지)*.
- **승컴 내 간접 비교 (`arm47 − bg-v4`, 다른 배치)**: Total **`−0.1228 [−0.1836, −0.0621]`** (`p=0.0130`), Phase C **`−0.1250 [−0.2492, −0.0009]`** (`p=0.0493`). 또한 Arm 47의 FIO Phase C p99(`174.6 µs`)가 V4(`166.0 µs`)와 유사하여, Greedy GC(`41.9 µs`) 대비 지연 차이가 온라인 학습기가 아닌 **CAT 전 라인 스캔 자체**에서 기인함을 뒷받침한다.
- **기존 Figure 1~10 Robustness 요약**: 그림 3만 그대로 사용 가능, 그림 1·7·8·9는 수정 후(탐색적 `n=1` 단서 + 2자리 수치) 사용 가능, 그림 2·4·5·6은 보조 사례로만 사용, 오염된 구 그림 10 및 미실행 `300k` 표 8은 사용 금지(`FINAL_FIGURE_CATALOG.md` 참조).

---

## 10장. 심사 의견별 증거 요약 (3대 핵심 주장 및 M1~M7 47개 항목)

- **핵심 주장 1** (iCAT > 무작위 정책 선택): **`입증`** (단 Online Greedy 무우위·Arm 47 oracle 한계 병기)
- **핵심 주장 2** (후보 제거·정착·변화 감지·재탐색 기여): **`부분 입증`** (묶음 입증, `NoElim`/`PartialReset` Holm 경계, `NoDrift`/`NoDiscount`/`NoSettle` 미입증)
- **핵심 주장 3** (정책 단위 학습의 메모리·CPU 효율 우위): **`부분 입증`** (학습 메모리 193×·학습 갱신 11× 유리; **전체 GC/SELECT 경과시간 5.5× 불리 → CPU 우위 입증 불가**)
- **47개 세부 항목 전체 집계**: 입증 완료 `14` / 부분 입증 `17` / 입증 실패 `7` / 추가 실험 불필요 `9` / 추가 실험 필요 `0` (상세: `FINAL_REVIEWER_RESPONSE_MATRIX.xlsx`).

---

## 11장. 실험의 한계

상세 10대 한계는 [FINAL_LIMITATIONS.md](file:///C:/Users/oyeon/orca/iCAT-experiments/report/final-revision/delivery/FINAL_LIMITATIONS.md)에 수록하였다. 핵심은 (1) 단일 8 GiB OP-7% `erase=0` 에뮬레이터, (2) `m1` `n=1` 및 커널 CPU 시간 미측정, (3) CAT `SELECT` 5.5× 스캔 비용 트레이드오프, (4) Online Greedy·`NoDrift`·`NoDiscount`·FIO p99 우위 미입증, (5) 기존 본문 그림·표의 `n=1` 탐색적 한계다.

---

## 12장. 최종 논문 반영 권고 (원고 직접 수정 전 제안)

1. **즉시 반영할 원고 패치 5건 (`FINAL_PAPER_NUMBER_AUDIT.csv` NA-09~NA-13)**:
   - `PAPER_KCI_DRAFT.md` **L405 (§7 자원 비용)**: `"GC 수행 시간은 계측하지 않았다"` 문구 삭제 → `resource-v124`(`n=3`) 및 표 9b(`m1` `n=1`: `LEARN` 11× 경량 vs `GC` 5.5× 열위) 요약으로 교체.
   - **L297–L307 (표 8 `300k` & 그림 10)**: 전원 `"대기"`인 미실행 표 8·그림 10 삭제 → §6.4 `mixFYF 250k (n=3)` 표 10·11 및 `figure03_adaptation`으로 통합.
   - **L004, L232, L240, L256, L260**: 잔존 `【결과 대기】`·`【갱신 예정】` 태그 5건 전면 삭제 및 `n=1` 탐색적 한계 확정.
   - **L262 (그림 9)**: 평균 손실을 소수 2자리(`CAT-Best 0.21%`, `CAT-Robust 4.95%`, `iCAT-v4 5.04%`)로 병기.
   - **L313–L321 (표 9)**: `WAF_nand` vs 호스트 `WAF` 정의 각주 보강.
2. **신규 Figure 채택 권고**: §6.4 주 근거 그림으로 `figure01_random`, `figure02_ablation`(또는 `fig_full_ablation`), `figure03_adaptation`, `figure04_exploration`, `figure05_parameters`, `figure06_candidates`, `fig_greedy_gc_vs_v4`, `fig_online_greedy_vs_v4`를 채택하고, `figure07_resources`는 표 9b 트레이드오프 캡션을 보강해 사용한다.
3. **고컴·승컴 최종 통합 입력 수신 후 마무리**: 현재 미푸시 상태인 고컴 5종(`iCAT_Complete_Experiment_Results.xlsx` 등)과 승컴 5종(`final_independent_validation.md` 등)이 push되는 즉시 자동 교차검증 후 최종 체크리스트를 확정한다.
