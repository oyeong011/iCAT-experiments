# iCAT 논문 리비전 전체 Robustness 감사 및 독립 검증 보고서

- **작성 시각**: 2026-11-26 20:30 KST (집컴 독립 연구 감사)
- **최종 전달 마감**: **2026-11-27 (내일, 선임 연구원 전달)**
- **감사 기준 Git 커밋 (읽기 전용, 원시 로그 무수정)**:
  - 승컴 `origin/main`: **`e6edd2f03`** (`revD` 9/9, `abl` 9/9, `greedy` 3/3, `secondary-metrics`, `batchG` 6/9 VALID — `drift50 rep2`까지 검증)
  - 고컴 `origin/report/data-validity-20261124`: **`99f579da8`** (`revA` 13/13, `revB` 8/8, `revC` 15/15, `revE` 9/9, `m1-20261126` 1/2 `mixY-m1-icat-v4-rep1` + `sim` 12/12 + `smoke` 2/2 VALID)
  - 자원 계측 `origin/resource-overhead-20261114`: **`c046de0d0`** (`resource-v124` FIO-Fast 30분 n=3 분리 계측)
- **연계 CSV 증거 파일 (동일 디렉터리)**:
  - [figure_robustness.csv](file:///C:/Users/oyeon/orca/iCAT-experiments/report/final-robustness-20261126/figure_robustness.csv)
  - [fixed_arm47_audit.csv](file:///C:/Users/oyeon/orca/iCAT-experiments/report/final-robustness-20261126/fixed_arm47_audit.csv)
  - [experiment_validity.csv](file:///C:/Users/oyeon/orca/iCAT-experiments/report/final-robustness-20261126/experiment_validity.csv)
  - [statistical_audit.csv](file:///C:/Users/oyeon/orca/iCAT-experiments/report/final-robustness-20261126/statistical_audit.csv)
  - [reviewer_evidence_matrix.csv](file:///C:/Users/oyeon/orca/iCAT-experiments/report/final-robustness-20261126/reviewer_evidence_matrix.csv)

---

## 작업 A. 기존 논문 Figure 1~6 (및 7~10·레거시 Fig 2) 전체 Robustness 감사

`PAPER_KCI_DRAFT.md`와 `analysis/figures.py`의 원시 경로를 직접 대조한 결과입니다.

| 논문 그림 (파일명) | 원시 로그 / Git SHA | 독립 반복 `n` | 원시-그림 일치 | 핵심 위험 / 편차 | 분류 | 그대로 사용 가능 여부 |
|---|---|---:|---|---|---|---|
| **그림 1** (`fig1_sensitivity`) | `sweep-20260915/rank-test4.txt` + `gh-repro-20260914` | 조합별 `n=1` (10분), Greedy `n=3` (`2.186`) | **일치** | 60개 조합 거시 순위(`ρ=0.959`)·`k=2` 최하위군 안정; 단 1위(arm 31 `1.744`) vs 2위(arm 47 `1.746`, 0.1% 차)는 `n=1` | **`PARTIAL`** | **조건부 사용 가능** (동기·`k=2` 제외 근거용; 조합별 `n=1` 명시 + §6.4 `revC` 60 vs 45 `n=3` 연계) |
| **그림 2** (`fig3_time_use`) | `mix-20260911/t4-online{,v2,v3}-rep1-x18`, `t4-onlinev4-rep1-x60` | 정책별 **`n=1`** | **일치** | 저성능 비율 `21%→12%→4%` 전적으로 1회 확률적 실행에 의존 (단 `mixFYF n=3` `revC` 탐색비중으로 방향 보강됨) | **`FRAGILE`** | **통계 근거 불가** (`n=1` 단일 사례 명시 + `n=3` `revA/revC` 탐색비중 그래프 병기/대체 권장) |
| *(레거시 `fig2_learning_over_time`)* | 동일 4개 `t4-online*-rep1` + `fixed47/50` | 정책별 **`n=1`** | 경미 차이(`1.814` vs `1.8116`) | 이미 초안에서 제외됨 | **`FRAGILE`** | **미사용 유지** |
| **그림 3** (`paper_fig03_v4_overview`) | `online-v4-src/conv_ftl.c` 코드 대조 | N/A (구조도) | **일치** | 코드 흐름과 1:1 일치 | **`ROBUST`** | **그대로 사용 가능** (투고 시 내부 제목만 제거) |
| **그림 4** (`fig9_rank_over_time`) | `t4-online{,v3,v4}-rep1` + 15개 고정 조합 `rep1` | 정책별 **`n=1`** | **일치** | 계단 순위 그래프가 1회 실행의 작은 WAF 변동에 민감 ("8시간 후 5위"는 단일 실행 값) | **`FRAGILE`** | **단일 실행 예시로만 사용** ("단일 실행 사례" 명시, 확정적 수렴 시간 주장 금지) |
| **그림 5** (`fig10_v4_choices`) | `t4-onlinev4-rep1-x60/kernel.log` | **`n=1`** | **일치** | 메커니즘 시각화(정착 + 이웃 탐침)로는 타당하나 `1.5시간`은 단일 실행 값 | **`PARTIAL`** | **메커니즘 예시로 사용 가능** (`1회 실행` 단서 유지) |
| **그림 6** (`fig6_ablation`) | `t4-onlinev3{,probe,k2}-rep1-x18`, `t4-online-rep1-x18` | 정책별 **`n=1`** | **일치** (`1.848/1.875/1.884/1.905`) | **주의:** 제안 `v4`가 아닌 구 `v3`의 `n=1` 결과! 실제 `mixFYF n=3`(`revC`)에서 60 vs 45 전체 차이는 `+0.028 [−0.032, +0.089]`(CI 0 포함) | **`FRAGILE`** | **주 Ablation 근거 불가** → §6.4 **`n=3` `mixFYF` Ablation (`revA/revD/abl/revE`, 표 10·`fig_full_ablation`)**을 주 근거로 대체·승격 |
| **그림 7** (`fig4_mixes_v4_vs_robust`, 보너스) | `mix{O,F,P,K,D,L,C,Q}-*-x3` (5종 `SQLITE_FULL`/0B 제외) | `fixed50` **`n=1`**, `v4` `n=1~3` | **일치** | 8종 중 5종에서 `v4`가 열위, 1~5% 차이가 반복 편차(~2%)와 겹침 | **`FRAGILE`** | **탐색적 다중 부하 개요로만 사용** (통계적 우위 주장 금지) |
| **그림 8·9** (`fig7_mix_loss`, `fig8_robustness`, 보너스) | `mix{C,D,F,K,O,P}-*-x3` | 고정 조합 전원 **`n=1`** | **⚠️ 원고 L260 수치 불일치!** | **`PAPER_KCI_DRAFT.md` L260이 오염 제외 전 구 수치(`3.0%/6.5%/7.2%`)를 그대로 기재! 실제 유효 수치(`paper_fig_numbers.json`)는 `CAT-Best 0.21%`, `CAT-Robust 4.95%`, `iCAT-v4 5.04%`!** | **`FRAGILE`** | **원고 L260 즉시 정정 필수** (고정 `n=1` 탐색적 비교 명시; CAT-Best가 6종 중 5종 우위) |
| **그림 10** (`fig5_three_phase_mix`, 보너스) | `mixR-*-x3` | `n=1~2` | 오염 데이터 | Phase B/C **`SQLITE_FULL`** (YCSB 실패 최대 99.8%) | **`INVALID`** | **절대 사용 금지** → 유효 `mixFYF 250k n=3` (`figure03_adaptation.png`)로 완전 교체 |
| **신규 리비전 Figure (`report/paper-figures/` & `paper_figures/`)** | 66+ 검증 `mixFYF` run (`revA/C/D/abl/revE/greedy`) | 핵심 전 조건 **`n=3`** | **40/40 자동 검증 통과** | 호스트 엄격 분리, 95% t-CI·Welch·Paired·Holm 완비 | **`ROBUST`** | **논문 주 근거로 사용 확정** (내일 오전 `batchG`·`m1` 최종 반영) |

---

## 작업 B. 고정 Arm 47 (기존 WAF `1.987`) 재현성 감사

> **핵심 구분:** 동일 Arm 47 반복 = **재현성 검증** / 서로 다른 Arm(47 vs 50 vs 37 등) 비교 = **정책 일반화 검증**.

### 1. 문제의 WAF `1.987` 원시 추적 (`revA-20261114/raw/mixFYF-arm47-rep1`)
- **원시 경로**: `origin/report/data-validity-20261124:result/revA-20261114/raw/mixFYF-arm47-rep1`
- **실행 환경**: 고컴(`oy-B550M-DS3H`, 커널 `7.0.0-31-generic`), 실행 시각 `2026-11-14T20:36:09+09:00`
- **모듈 SHA256**: `9fde0ea49892b1c8fa31c5bfa453ca55f5f2525806964c427d3f640266b8ce7d` (`nvmev-arm47.ko` — 9월 승컴 `t4-fixed47`과 **완전 동일 모듈**)
- **워크로드·초기화·Seed**: `mixFYF 250k` (preset 6 GiB 순차 + prepare 3 GiB 무작위, FIO seed `20260911/20261011/20261111`, YCSB 100.0% OK, `SQLITE_FULL=0`)
- **실제 반복 횟수**: **`n = 1` (단 1회! `rep2`, `rep3` 없음)**
- **2경로 재계산 WAF**: **`1.987355`** (`host_pages=149,845,303`, `gc_pages=147,950,440`) — Phase A **`1.774412`**, Phase B **`1.026571`**, Phase C **`2.278243`**

### 2. 저장소 전체에서 이미 확보된 동일 Arm 47 `n=3` 자료 여부 ([fixed_arm47_audit.csv](file:///C:/Users/oyeon/orca/iCAT-experiments/report/final-robustness-20261126/fixed_arm47_audit.csv))

| 그룹 / 워크로드 | 호스트·시기 | `n` | 실행별 WAF | 평균 ± SD | `mixFYF 1.987` 비교 가능성 |
|---|---|---:|---|---|---|
| **`revA mixFYF 250k`** *(1.987 대상)* | 고컴 11-14 | **1** | `1.987355` | `1.9874` (`n=1` SD 없음) | 고컴 `revA-v4`(`2.1284 ± 0.0049`)와 동일 배치이나 **`n=1`이라 통계 검정 불가** |
| **`t4` FIO-Fast 10분** | 승컴 09-11 | **3** | `1.7739 / 1.7737 / 1.7736` | **`1.7738 ± 0.00017`** | 이미 `n=3` 존재 — FIO-Fast에서 Arm 47이 극도로 결정적(CV `0.01%`)임을 입증 |
| **`resource-v124` FIO-Fast 30분** | 승컴 11-14 | **3** | `1.7743 / 1.7610 / 1.7741` | **`1.7698 ± 0.0076`** | 이미 `n=3` 존재 — 11월 재측정에서도 Phase A 수준(`~1.774`) 일관 확인 |
| **`cat60` mixY 90분** | 승컴 10-11 | **3** | `2.1983 / 2.2048 / 2.2038` | **`2.2023 ± 0.0035`** | 이미 `n=3` 존재 — 다중 부하에서도 Arm 47 자체 재현성 매우 높음 |
| **`mixO` / `mixF` x1** vs **x3** | 승컴 09-11 | **3** (`x1`) / **1** (`x3`) | `mixO x1`: `1.912/1.731/1.910`<br>`mixF x1`: `2.354/2.396/2.382` | `mixO x1`: `1.851 ± 0.104`<br>`mixF x1`: `2.377 ± 0.021` | `x1`은 `n=3` 존재하나, 논문 표 6이 인용하는 `x3`은 `n=1`뿐 |
| **`mixY` 10시간 (교차 날짜/호스트)** | 승컴 10-10 vs 11-23 vs 고컴 11-19 | 각 **1** | `2.8641` / `2.7394`* / `3.2982` | 합산 불가 | **교차 월·호스트 `n=1` 비교 절대 불가** |

### 3. Arm 47 (`1.987`) 해석 및 추가 반복 필요성 판정
- **`mixFYF`에서 Arm 47(`1.987`)이 `iCAT-v4`(`2.128`)보다 낮은 구조적 이유:** `mixFYF` 전체 호스트 쓰기의 **96.1%**가 FIO-Fast(Phase A `72M` + Phase C `72M` vs Phase B `5.8M`)이며, Arm 47은 FIO-Fast의 오프라인 최상위 조합(60개 중 2위, 1위와 0.1% 차)으로서 초기 45개 탐색 비용과 Phase C 재탐색 비용을 전혀 지불하지 않음.
- **추가 반복 필요성:** 논문에서 `mixFYF`의 `arm47 = 1.987`을 **"오프라인 참고선(`n=1`, 통계 미부여)"**으로만 두고 정량 통계 주장을 하지 않는다면 **내일(11-27) 마감 전 추가 반복은 필수 아님**. 반대로 Arm 47 대비 탐색 오버헤드 `%`를 `95% CI`로 논문 주장에 포함하려면 `mixFYF`에서 동일 호스트 `n=3`이 필수(기존 `FIO-Fast`/`mixY` `n=3`은 워크로드가 달라 대체 불가 → 상세 계획은 [additional_experiments_required.md](file:///C:/Users/oyeon/orca/iCAT-experiments/report/final-robustness-20261126/additional_experiments_required.md) 참조).

---

## 작업 C. 신규 실험 독립 검증 요약 ([experiment_validity.csv](file:///C:/Users/oyeon/orca/iCAT-experiments/report/final-robustness-20261126/experiment_validity.csv))

총 **73개 완료 run**을 원시 로그에서 독립 검증하여 **73/73 VALID** 확인(2경로 WAF 일치, SHA256 일치, `exit=0`, FIO 오류 0, YCSB `100.0% OK` & `SQLITE_FULL=0`, 커널 오류 0).

### 1. M1 자원 오버헤드 비교표 (`m1-20261126` + `resource-v124` + `gdb sizeof`)

| 측정 계층 / 지표 | iCAT-v4 | SmartGC-EQ8 | 출처 / 검증 상태 |
|---|---:|---:|---|
| **이론적 학습 구조체 메모리 (4파티션, `gdb sizeof`)** | **`10,112 B`** (`9.88 KiB`) | **`1,951,648 B`** (`193.0×`, GC버퍼 포함 **`2,343,936 B` / `231.8×`**) | **VERIFIED EXACT** |
| **실제 커널 `VmallocUsed` 증가 (`load1s − pre` 중앙값)** | **`+34,848 kB`** (`10h 본 실행`, `pre 47,076 → 81,924 kB`) / smoke `+34,736 kB` | smoke **`+37,800 kB`** (`+3,064 kB` 더 큼); **10h 본 실행 진행 중** | **VERIFIED** (`m1-20261126/sampler/*/mem.tsv`) |
| **사용자 공간 `conv_ftl.c` CPU 벤치 (`zones` 합성, `n=3`, 모드 2)** | GC **`53.05 µs`** (`SELECT 48.91 µs`, `LEARN < 50 ns`, `windows=0`), 호스트 `1.55 s/GiB`, **WAF `7.16`** | GC **`7.59 µs`** (`SELECT 0.39 µs`, `LEARN step 285.5 µs × 1,540`, `260.5 ns/GC`), 호스트 `0.29 s/GiB`, **WAF_nand `9.19`** | **VERIFIED** (`4c1415c20`, 12/12 OK) — **불리한 CPU 결과 투명 보고** |
| **커널 `mixY` 10시간 본 실행 (`kernel.log` 단독 `M1PROF`, `n=1`)** | **`WAF 3.330464`** (`8.285 TB`, `chmodel_warn=0`)<br>`GC 98.37 µs` (`10,354 s`), `SELECT 87.05 µs` (`9,162 s`, **88.5%**), **`LEARN 40.80 ns` (`4.295 s`, `0.041%`)** | **실행 중 (`~11-27 01:00 KST` 완료 예정)**<br>*(참고: 정정된 smoke `kernel.log` 단독: `GC 5.34 µs`, `SELECT 1.15 µs`, `LEARN step 551 µs`, `REWARD 98 ns`, `BUF 36–54 ns`)* | iCAT **VALID (`n=1`)** / SmartGC **RUNNING** (`rep2·3` 사용자 취소 → `n=1` 통계 없음) |
| **iCAT 세부 경로 분리 (`resource-v124`, FIO-Fast 30분, `n=3`)** | 보상갱신 **`1.442 ms`**, 정책선택 **`1.273 ms`**, `set_arm` **`0.059 ms`**, `on_gc` 순비용 **`9.43 ns/GC`**, 에뮬 `do_gc` **`206.84 s`** (CAT-47 `255.98 s`) | N/A (`m1`에서 측정) | **VERIFIED** (`origin/resource-overhead-20261114`) |

### 2. M3 · M6 핵심 실험 결과표 (`mixFYF 250k`, 호스트 엄격 분리)

| 영역 | 호스트·배치 | 정책 | 유효 `n` | 전체 WAF 평균 ± SD [95% CI] | 동일 호스트 V4 대비 Welch Δ [95% CI] | Holm `p` | 판정 |
|---|---|---|---:|---|---|---:|---|
| **M3** | 고컴 `revA` | Random Selection | 3 | `2.3243 ± 0.0055` `[2.3106, 2.3381]` | **`+0.1959 [+0.1840, +0.2079]`** (`g=29.89`) | `<0.001` | **`ROBUST`** (V4 우위) |
| **M3** | 고컴 `revC` | 기존 iCAT (`online`) | 3 | `2.3951 ± 0.0029` `[2.3879, 2.4022]` | **`+0.2751 [+0.2030, +0.3472]`** (`g=10.53`) | `0.0141` | **`ROBUST`** (V4 우위) |
| **M3** | 승컴 `greedy` | Online Greedy (`VAR=8`) | 3 | `2.1300 ± 0.0198` `[2.0809, 2.1791]` | `−0.0086 [−0.0508, +0.0336]` (`vs revD-v4`) | `1.0000` | **정직한 Null** (0/2,513 규칙 불일치) |
| **M3** | 승컴 `batchG` | Greedy GC (`mixFYF`) | **2/3** | `2.6337 / 2.6330` *(실행 중)* | `n=2` 통계 보류 (`bg-v4` `2.1288 / 2.0827`) | 대기 | **진행 중** (`rep3` ~00:45 KST) |
| **M6** | 고컴 `revC` | ELIM 10% / 25% vs 15% | 3 / 3 / 3 | `2.1438` / `2.1707` vs `2.1200` | 10% `+0.0238 [−0.043, +0.091]`<br>25% `+0.0507 [−0.010, +0.111]` | `0.514` / `0.237` | **차이 미확인** (15% 최저 평균) |
| **M6** | 고컴 `revC` | 후보 60개 vs 45개 (`m5`) | 3 / 3 | `2.1482 ± 0.0215` vs `2.1200 ± 0.0294` | `+0.0282 [−0.0324, +0.0888]` | `0.514` | **차이 미확인** (`k=2` 제거 손실 없음) |
| **M6** | 고컴 `revE` | `drift12` (12.5%) vs 25% | 3 / 3 | `2.1855 ± 0.0267` vs `2.1135 ± 0.0261` | **`+0.0720 [+0.0121, +0.1319]`** (`g=2.18`) | `0.0907` | **사전등록 CI>0** (Phase B 조기 리셋 3/3) |
| **M6** | 승컴 `batchG` | `drift50` (50%) vs 25% | **2/3** | `2.1608 / 2.1016` *(실행 중)* | `n=2` 통계 보류 (`bg-v4` `2.1288 / 2.0827`) | 대기 | **진행 중** (`rep3` ~00:45 KST) |

---

## 작업 D & E. 통계 검증 및 3대 핵심 주장 대응 ([statistical_audit.csv](file:///C:/Users/oyeon/orca/iCAT-experiments/report/final-robustness-20261126/statistical_audit.csv), [reviewer_evidence_matrix.csv](file:///C:/Users/oyeon/orca/iCAT-experiments/report/final-robustness-20261126/reviewer_evidence_matrix.csv))

- **25개 `n=3` 대비 독립 재계산 결과:**
  - **`ROBUST` (Welch 95% CI 0 제외 + Holm `p < 0.05`, 6개):** `revA Random − V4` (`p=6e-6`), `revA V2 − V4` (`p=0.0003`), `revC Orig iCAT − V4` (`p=0.0141`), `abl OffBundle − V4` 전체·Phase C (`p=0.0277`), `revB* NoElim* − V4` (`p=0.0030`, 교차배치 단서).
  - **`CONFIRMED_PREREG` (Welch CI 0 제외, 4대비 Holm 경계 `p = 0.060–0.091`, 6개):** `revD FullReset − V4` 전체(`+0.0596`)·Phase C(`+0.1296`, 짝 CI>0), `revE Isolated NoElim − V4` 전체(`+0.0913`, 짝 CI>0)·Phase C(`+0.1548`), `revE Drift 12.5% − V4` 전체(`+0.0720`)·Phase C(`+0.1476`).
  - **`NO_DIFF_FOUND` (CI 0 포함, 13개):** `NoDrift` (2호스트), `NoDiscount γ=1.0`, `Online Greedy`, `ELIM 10%/25%`, `60-arm`, `NoSettle*`.
- **3대 핵심 주장 최종 판정:**
  1. **iCAT은 Random Selection보다 효과적인가?** → **입증 (`ROBUST`)** (`−8.4%`, `p<0.001`; 기존 iCAT 대비 `−11.5%`, `p=0.014`; Greedy GC 대비 레거시 9종 + `batchG` 오늘 밤 `n=3`). **단, Online Greedy 대비 우위(`−0.009`, `p=0.54`)와 오프라인 Arm 47(`1.987`) 대비 우위는 주장 불가.**
  2. **후보 제거·정착·변화 감지 기능이 실제 효과를 가지는가?** → **부분 입증:** 기능 묶음(`+5.8–6.4%`, 두 호스트 Holm `p≤0.028`), 단독 후보 제거(`+4.3%`, 동일배치 Welch·짝 CI>0, Holm `p=0.091`), 부분 복원(`+2.8%/+5.3%`, Welch CI>0, Holm `p=0.060–0.072`) 확인. **단독 변화 감지(`NoDrift`)는 방향성만 일치(CI 0 포함), 단독 정착(`NoSettle`)은 코드 종속+CI 0 포함, 할인 계수(`γ`)는 90분 내 효과 미확인(정직한 Null).**
  3. **정책 단위 학습은 SmartGC보다 자원 효율적인가?** → **이분화 필수:** 학습 **상태 메모리(`193×–232×` 절감, 실측 `VmallocUsed` ~3 MiB 절감)**와 **학습기 자체 결정 비용(`40.8 ns/GC`, 10시간 4.30초)**은 압도적으로 경량이나, **GC 1회 전체 CPU 경과 시간은 CAT 전 라인 스캔 때문에 iCAT(`53–98 µs`)이 SmartGC(`5.3–7.6 µs`)보다 훨씬 김** (WAF 절감과의 트레이드오프로 투명 서술 필수).
