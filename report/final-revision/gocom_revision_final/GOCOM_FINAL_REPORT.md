# 고컴 완료 보고: iCAT 리비전 최종 결과 (기준선·Ablation·파라미터), 2026-11-27

- 새 실험은 하지 않았다. 원시 로그와 기존 결과는 읽기만 했다.
- 생성 스크립트: `analysis/final_revision/gocom_revision_final.py` (표준 라이브러리 + scipy, 읽기 전용)
  - 다시 실행하면 출력 디렉터리가 비어 있지 않아 거부된다 (덮어쓰기 방지).
  - 모든 평균, SD, CI, Welch 대비를 run별 값에서 다시 계산했다. 그 값을 통합 재계산 결과 `report/final-revision/complete-results/`(커밋 3fdb21258)와 대조했다. **검사 388건, 불일치 0건** (`verification_gocom.csv`).
- 최종 Excel(`iCAT_Revision_Final.xlsx`)은 집컴 담당이다. 고컴은 시트별로 들어갈 CSV를 만들었다 (§7).

## 0. 먼저 알릴 것

1. **참고 엑셀 `iCAT_기준선_Ablation_논문용.xlsx`를 찾지 못했다.** 이 PC 전체와 원격 브랜치 전부를 검색했지만 없었다. 그래서 그 파일의 수치는 대조하지 못했다. 파일을 올려 주면 대조하겠다.
2. **γ 0.90 / 0.95 / 0.99와 C 0.50 / 0.75는 실행한 적이 없다.**
   - 이 PC의 `result/`, `result_e1/`, `result_e2/` 전체와 승컴 리비전 배치 7개(origin/main 4689c6797)의 원시 커널 로그를 검사했다. `WATGC_V2 init` 줄 462,668개에서 값은 다음뿐이었다.
     - `gamma_q16`: 65503 (γ 0.9995) 또는 65536 (γ 1.0, 승컴 NoDiscount)
     - `exploration_q16`: 모든 run에서 16384 (C 0.25)
   - 따라서 `Discount_Factor`와 `Exploration_C` 시트는 "실행하지 않음"으로만 채울 수 있다. 민감도 그래프는 만들 수 없다.
3. **W1–W4 결과는 없다.** 리비전 실험은 모두 mixFYF 하나다. 지시대로 mixFYF를 W1–W4에 대입하지 않았다.
4. **revA V2와 승컴 abl "묶음 끔"은 같은 빌드 변형(`ICAT_VARIANT=2`)이다.**
   - Figure 2에서 같은 x 라벨 `w/o Elimination & Settling`으로 묶는다.
   - 호스트가 달라 두 값은 합치지 않고 따로 표시한다.

## 1. 확인한 실험 목록 (고컴)

| 배치 | 그룹 (최종 표기) | n | 모듈 sha256 앞 16자 | 원시 경로 |
|---|---|---|---|---|
| revA-20261114 | iCAT-v4, NoDrift (V1), NoElim+NoSettle (V2), Random Selection; Arm 47 n=1 | 3 / 3 / 3 / 3 / 1 | 987d62042df380e4, 50ee1c5910562b9f, c74e07148c2dfd5b, 7d88c9a869f18651, 9fde0ea49892b1c8 | `result/revA-20261114/raw/` |
| revB-20261122 | iCAT-v4 n=1, NoElim, NoSettle, Arms60 n=1 | 1 / 3 / 3 / 1 | 7599cbd68ae7b343, b1663b470a0a7616, 928896fbb6a994f6, b2a19db339e280ff | `result/revB-20261122/raw/` |
| revC-20261124 | iCAT-v4, Elim10, Elim25, Arms60, iCAT (원 구현) | 3 each | df2be25144d186ee, 186ee2c936507085, 606acc4161d0840c, b2a19db339e280ff, 44675657fa6d50cb | `result/revC-20261124/raw/` |
| revE-20261125 | iCAT-v4, NoElim, Drift12.5 | 3 each | df2be25144d186ee (revC-v4와 같은 파일), b1663b470a0a7616 (revB-noelim과 같은 파일), f6a02e980c748923 | `result/revE-20261125/raw/` |

- 모든 run은 run 검사를 다시 통과했다 (`complete-results/run_validity.csv`).
  - 검사 항목: exit 0, 커널·FIO 오류 0, YCSB 실패 0, SQLITE_FULL 0, WAF 두 경로 일치, 시작 카운터 0, FIO seed 규칙.
- 코드 버전
  - 소스 트리: `revA-src`, `revB-src`, `revC-src`. 이 브랜치(`report/data-validity-20261124`)에 있다.
  - 각 run의 실제 모듈은 위 sha256으로 고정했다. 배치별 `modules.sha256`과 run별 `environment.txt`에 기록되어 있다.
- 부하: mixFYF = FIO-Fast 1800 s → YCSB-A (SQLite 25만 레코드) 1800 s → FIO-Fast 1800 s.
  - 측정 방식: 구간 지정 계측. WAF = 1 + GC 쓰기 / 호스트 쓰기, 원시 카운터에서 계산했다.

## 2. 변형별 기능: 소스코드 + 실제 실행 로그로 검증

### 2.1 소스코드 근거 (`feature_matrix.csv`)

- 위치는 `revC-src/conv_ftl.c` 기준이다. `revA-src`와 `revB-src`도 이 블록들의 행 번호가 같다 (diff로 확인).
- revA-src에는 VARIANT 3·5 분기가 없다. revA에서는 VARIANT 1·2·4·9만 썼다.

| 기능 | 코드 | 꺼지는 VARIANT |
|---|---|---|
| Discounting | 578–582: 매 판단 구간 모든 arm 통계에 γ를 곱한다 (`conv_ftl.h:61`) | 없음. γ 값만 바꿀 수 있다 (NoDiscount: γ = 1) |
| Elimination | 616–633: 최상위 대비 평균 WAF가 문턱(`ELIM_Q16`, 기본 15 %)을 넘는 후보를 제거한다 | 2, 3 (Random 9는 611행에서 먼저 반환) |
| Settling | 536–550 | 2, 5, 9 |
| Drift Detection | 563–574: 정착 상태에서만 실행한다. 문턱 `DRIFT_Q16`, 기본 25 % | 1. 정착이 없는 2·5·9에서는 구조상 실행되지 않는다 |
| Partial Reset | 474–497: 모든 arm 통계를 0으로 하고, 후보 = 남은 후보 + 1단계 이웃 | 감지가 없으면 일어나지 않는다. 승컴 VARIANT 7(FullReset)은 45개 전체 복원 |
| Probe | 642–655: 정착 상태에서만 실행한다 | 정착이 없으면 구조상 꺼진다 |

| Variant | Discounting | Elimination | Settling | Drift Detection | Partial Reset | Probe | 분류 |
|---|---|---|---|---|---|---|---|
| iCAT-v4 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 대조군 |
| NoDiscount (승컴) | ✗ (γ = 1) | ✓ | ✓ | ✓ | ✓ | ✓ | Ablation |
| NoElim+NoSettle (revA V2, abl 묶음 끔) | ✓ | ✗ | ✗ | ✗ (구조상) | — | ✗ (구조상) | Ablation |
| NoElim | ✓ | ✗ | ✓ | ✓ | △ 재설정은 일어나지만 복원할 제거 후보가 없다 | ✓ | Ablation |
| NoDrift (revA V1, revD) | ✓ | ✓ | ✓ | ✗ | — (재설정 없음) | ✓ | Ablation |
| FullReset (승컴) | ✓ | ✓ | ✓ | ✓ | ✗ (전체 복원) | ✓ | Ablation |
| NoSettle (revB, 대조군 n=1) | ✓ | ✓ | ✗ | ✗ (구조상) | — | ✗ (구조상) | Ablation, 통계 불가 |
| Elim10 / Elim25, Drift12.5, Drift50, Arms60 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Parameter Sensitivity (값만 변경) |

### 2.2 실행 로그로 확인한 실제 동작 (`learner_counters_runs.csv`, 고컴 41개 run)

- 커널 로그의 `WATGC_V2 init` 줄에 찍힌 VARIANT, γ, C가 41개 run 모두 사전 등록과 같다.
- 각 기능이 꺼진 변형에서는 로그상으로도 그 기능이 일어나지 않았다.

| 변형 | 단계 A 끝 남은 후보 (4 파티션 평균) | 종료 시 남은 후보 | 제거 카운터 합 | 재설정 합 | 해석 |
|---|---|---|---|---|---|
| iCAT-v4 (revA·C·E) | 17.5–22 / 45 | 2–8 | 185–202 | 4 | 정상 동작 |
| NoDrift (V1) | 18–22 | 1–5 | 191–199 | **0** | 감지와 재설정이 일어나지 않았다 |
| NoElim+NoSettle (V2) | **45** | 45 | **0** | **0** | 제거와 재설정이 일어나지 않았다 |
| NoElim (revB, revE) | **45** | 45 | **0** | 4 | 제거는 없고 감지·재설정은 동작했다 |
| NoSettle (revB) | 18–22 | **1** | 176 | **0** | 제거는 계속되고, probe 재편입과 재설정이 없다 |
| Random Selection | 45 | 45 | 0 | 0 | 학습 기능이 모두 동작하지 않았다 |

## 3. Figure 1: Random Selection (고컴 부분)

- 파일: `baseline_figure1_gocom.csv` (요약), `baseline_data_gocom.csv` (rep별 값과 단계별 대비)
- 오차 막대: **95 % CI** (t 분포, df = 2). SD는 별도 열에 있다.
- 같은 배치(revA, 고컴)의 iCAT-v4를 대조군으로 썼다.
- Greedy GC 행은 승컴 batchG 담당이다. 그 대조군은 승컴 batchG의 iCAT-v4다. 두 iCAT-v4를 합치거나 바꿔 쓰면 안 된다.

| Experiment | Baseline WAF (mean ± SD) | iCAT-v4 WAF, 같은 배치 | ΔWAF [Welch 95 % CI] | Holm p | Improvement (%) | 판정 |
|---|---|---|---|---|---|---|
| Random Selection (revA) | 2.3243 ± 0.0055 | 2.1284 ± 0.0049 | +0.1959 [+0.1840, +0.2079] | <0.0001 (6개 대비) | 8.43 | 차이 있음 |
| (추가) iCAT 원 구현 (revC) | 2.3951 ± 0.0029 | 2.1200 ± 0.0294 | +0.2751 [+0.2030, +0.3472] | 0.0282 (8개 대비) | 11.49 | 차이 있음 |

- Improvement (%) = (Baseline − iCAT) / Baseline × 100. 평균의 비로 계산한 점추정값이고 CI는 없다.
  - 다른 정의도 같이 적었다: ΔWAF (%) = (Baseline − iCAT) / iCAT × 100 → Random 9.20 %.
  - 논문에서는 하나만 쓰고 정의를 밝힌다.
- 단계별 대비(A, B, C, C 첫 5분)는 `baseline_data_gocom.csv`에 있다.
- 같은 배치에서 단계 C의 FIO p99 지연은 iCAT-v4가 Random보다 15–20 µs 높았다. 지연 개선은 주장하지 않는다.

## 4. Table 1 / Figure 2: Ablation (고컴 배치)

- 파일: `ablation_table_gocom.csv`
- ΔWAF (%) = (Variant − 같은 배치 iCAT-v4) / iCAT-v4 × 100
- Normalized WAF = Variant / 같은 배치 iCAT-v4

| X 라벨 (제안) | Variant | 배치 | Variant WAF | 같은 배치 iCAT-v4 | ΔWAF [95 % CI] | ΔWAF (%) | Normalized | Holm p | 판정 |
|---|---|---|---|---|---|---|---|---|---|
| w/o Drift Detection | NoDrift (V1) | revA | 2.2071 ± 0.0525 | 2.1284 ± 0.0049 | +0.0787 [−0.0501, +0.2074] | 3.70 | 1.0370 | 0.2375 | 구분되지 않음 |
| w/o Elimination & Settling | NoElim+NoSettle (V2) | revA | 2.2639 ± 0.0091 | 2.1284 ± 0.0049 | +0.1355 [+0.1167, +0.1543] | 6.37 | 1.0637 | 0.0005 | 차이 있음 |
| w/o Elimination | NoElim | revE | 2.2048 ± 0.0052 | 2.1135 ± 0.0261 | +0.0913 [+0.0296, +0.1530] | 4.32 | 1.0432 | 0.0907 | 보정 전 CI로는 차이 있음, Holm 보정 후 경계 |
| (Figure 제외) | NoElim (revB) | revB | 2.2226 ± 0.0113 | 2.1520 (n=1) | +0.0706 | 3.28 | — | — | 대조군 n=1, 통계 불가 |
| (Figure 제외) | NoSettle | revB | 2.2152 ± 0.0790 | 2.1520 (n=1) | +0.0632 | 2.94 | — | — | 대조군 n=1, 통계 불가 |

- X 라벨 검증 결과
  - `w/o Elimination & Settling`은 실제로 변화 감지, 재설정, probe도 꺼진 상태다 (§2). 라벨 아래나 캡션에 "(drift detection and probe inactive as a consequence)"를 붙인다.
  - `w/o Drift Detection`과 `w/o Elimination`은 이름 그대로다.
- 승컴 담당인 FullReset, NoDiscount, 승컴의 NoDrift와 NoElim+NoSettle은 이 표에 없다. 집컴이 합칠 때 배치마다 자기 iCAT-v4로 정규화해야 한다.
- Drift12.5, Elim10/25, Arms60은 Ablation 표가 아니라 §5 파라미터 민감도에 넣는다.

## 5. 파라미터 민감도

### 5.1 후보 제거 문턱 (`param_elimination_threshold.csv`, revC 같은 배치)

| 문턱 | 전체 WAF | Δ vs 15 % [95 % CI] | Holm p | 단계 A 끝 남은 후보 / 45 | 단계 A 끝 제거된 비율 (실측) | 제거 카운터 | 학습 ktime (ms) |
|---|---|---|---|---|---|---|---|
| 10 % | 2.1438 ± 0.0081 | +0.0238 [−0.0433, +0.0909] | 0.951 | 8.8 ± 1.3 | 0.80 ± 0.03 | 214 ± 10 | 2.94 ± 0.15 |
| 15 % (기본) | 2.1200 ± 0.0294 | — | — | 17.8 ± 0.3 | 0.61 ± 0.01 | 194 ± 9 | 3.86 ± 0.18 |
| 25 % | 2.1707 ± 0.0212 | +0.0507 [−0.0098, +0.1112] | 0.475 | 40.5 ± 2.6 | 0.10 ± 0.06 | 186 ± 1 | 5.77 ± 0.17 |
| off (NoElim, revE 배치) | 2.2048 ± 0.0052 | revE 대조 +0.0913 [+0.0296, +0.1530] | 0.091 | 45 | 0 | 0 | 6.68 ± 0.16 |

- **문턱과 실제 제거 비율은 다르다.** 문턱 10 %에서 후보의 80 %가 제거되었고, 25 %에서는 10 %만 제거되었다. 이 열의 이름을 "제거 문턱"과 섞지 않는다.
- 제거 카운터는 커널 summary의 n_elim 합계다. probe가 이웃을 다시 넣었다가 재제거하는 경우도 센다.
  - 기존 revC 보고서의 "제거 횟수 45/30/23"은 남은 후보 수가 줄어든 판단 구간의 수다. 정의가 다르고, 둘 다 원시 로그에서 다시 계산된다. 이번 대조에서 n_elim 값과 최종 후보 수는 기존 `learner_runs.csv`와 일치했다.
- 같은 파일에 첫 정착 시간, 단계 C 감지·복원 후보·재정착 시간, 탐색 쓰기 비중이 있다. 출처는 `complete-results/adaptation_metrics.csv`다.
- 결론
  - 10–25 %에서 전체 WAF는 구분되지 않았다. 최적 문턱을 주장할 수 없다.
  - 문턱이 높을수록 남은 후보가 많고, 학습 시간이 늘고, 단계 C 복원 후보가 늘었다. 메커니즘은 예상 방향으로 움직였다.

### 5.2 할인율 γ, 탐색 계수 C

- γ 0.90 / 0.95 / 0.99: **실행하지 않음.**
  - 측정한 값은 γ 0.9995(기본)와 γ 1.0(승컴 NoDiscount)뿐이다.
  - NoDiscount 결과(Δ −0.004 [−0.064, +0.057], 구분되지 않음)는 승컴 담당이다.
- C 0.50 / 0.75: **실행하지 않음.** 모든 run이 C = 0.25다.
  - C는 UCB 보너스 항의 계수다 (WAF 단위, `conv_ftl.c:436`). 무작위 선택 확률이 아니다.

### 5.3 그 밖의 파라미터 (`param_other_gocom.csv`)

| 설정 | 배치 | Δ vs 같은 배치 기본값 [95 % CI] | Holm p | 판정 |
|---|---|---|---|---|
| Drift 12.5 % (기본 25 %) | revE | +0.0720 [+0.0121, +0.1319] | 0.091 | 보정 전 CI로는 차이 있음, Holm 보정 후 경계 |
| Arms60 (기본 45) | revC | +0.0282 [−0.0324, +0.0888] | 0.951 | 구분되지 않음 |

- Drift 50 %는 승컴 batchG 결과다. 다른 호스트이므로 12.5 %와 한 곡선으로 잇지 않는다.
- 변화 감지 15 %는 실행하지 않았다.

## 6. 비교할 수 없는 실험과 이유

| 실험 | 이유 |
|---|---|
| revB NoElim, NoSettle | 같은 배치 iCAT-v4가 1회뿐이다. 통계와 Figure에 쓰지 않는다 |
| revA Arm 47 (n=1) | 1회 실행이다. 승컴 3회와 호스트가 달라 합치지 않는다 |
| Random Selection vs Greedy GC | 호스트, 배치, 대조군이 다르다. 각각 자기 배치 iCAT-v4와의 차이로만 읽는다 |
| Drift 12.5 % vs Drift 50 % | 호스트와 배치가 다르다 |
| 배치 사이의 iCAT-v4 절대값 | 같은 정책도 배치 사이에서 0.5–1 % 움직였다 (revA 2.128, revC 2.120, revE 2.113). 공통 대조군으로 쓰지 않는다 |
| γ·C 민감도, W1–W4 | 데이터가 없다 |

## 7. 집컴 Excel 시트별 입력 파일

| 시트 | 고컴 파일 |
|---|---|
| Baseline_Data | `baseline_data_gocom.csv`, `baseline_figure1_gocom.csv` |
| Ablation_Table | `ablation_table_gocom.csv`, `feature_matrix.csv` (승컴 변형 포함, 고컴 교차 확인) |
| Discount_Factor | `param_discount_factor.csv` (실행하지 않음) |
| Exploration_C | `param_exploration_C.csv` (실행하지 않음) |
| Elimination_Threshold | `param_elimination_threshold.csv` |
| (Parameter, 기타) | `param_other_gocom.csv` |
| Raw_Data | `raw_data_gocom.csv` (고컴 run별 WAF, 모듈 sha256, seed, 원시 경로) |
| Verification | `verification_gocom.csv` (388건), `learner_counters_runs.csv` |

- GitHub 경로: `oyeong011/iCAT-experiments`, 브랜치 `report/data-validity-20261124`, 디렉터리 `report/final-revision/gocom_revision_final/`
- 원 논문 Figure 스타일(하늘색 iCAT, 검은 테두리)은 집컴 Excel에서 정한다. 원 논문 그림의 정확한 색 코드는 이 저장소에서 찾지 못했다.
