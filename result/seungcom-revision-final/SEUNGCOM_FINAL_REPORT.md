# 승컴 최종 리비전 보고 (2026-11-27)

새 실험은 하지 않았어요. 로그와 기존 결과 폴더(`final-revision-seungcom/`, `final-baseline-comparison/`)도 건드리지 않았어요.

- γ·C 민감도는 고컴 revF-20261127이 맡고 있어요 (각 1회). 승컴은 같은 실험을 중복해서 돌리지 않아요.
- 재생성 명령
  ```
  python3 -I -B analysis/revision/seungcom_package.py result/seungcom-revision-final
  python3 -I -B analysis/revision/seungcom_final.py
  ```
- WAF 통계의 출처는 `final-validation-20261127/final_statistical_validation.csv`예요. 원시 로그에서 다시 계산한 값이고, 고컴 Excel·집컴 자료와 불일치가 0이었어요.
- 소스는 `revD-src`이고, 마지막 변경 커밋은 `b62127da2`예요. 작업 트리는 깨끗하고 `sources.sha256` 검사를 통과했어요. 아래 행 번호는 이 리비전 기준이에요.

## 1. 확인한 실험 (승컴 i7-7700, mixFYF 90분, 각 3회, 모두 유효)

| 배치 | 정책 | 원시 경로 | 용도 |
|---|---|---|---|
| batchG-20261126 | bg-v4 | `result/batchG-20261126/raw/mixFYF-bg-v4-rep{1,2,3}` | Greedy GC의 대조군 |
| greedygc-20261126 | greedygc | `result/greedygc-20261126/raw/mixFYF-greedygc-rep{1,2,3}` | 기준선 (batchG 큐에서 번갈아 실행) |
| revD-20261124 | revD-v4, revD-nodrift, revD-fullreset | `result/revD-20261124/raw/mixFYF-<정책>-rep{1,2,3}` | Ablation |
| revision-additional-ablation | abl-v4, abl-nodiscount, abl-off-elim-settle-drift-probe | `result/revision-additional-ablation/raw/mixFYF-<정책>-rep{1,2,3}` | Ablation |
| drift50-20261126 | drift50 | `result/drift50-20261126/raw/mixFYF-drift50-rep{1,2,3}` | 파라미터 (batchG 큐) |

반복별 WAF, 모듈 sha, seed는 `raw_data.csv`에 있어요.

## 2. Baseline — Greedy GC (대조군은 bg-v4)

| Experiment | Baseline WAF [95 % CI] | iCAT WAF [95 % CI] | Improvement (%) | Holm p |
|---|---|---|---|---|
| Greedy GC | 2.6293 [2.6121, 2.6465] | 2.1105 [2.0497, 2.1712] | **19.73** | 0.00128 |

- Improvement = (Baseline − iCAT) / Baseline × 100이에요.
- 반복값
  - Greedy GC: 2.6337 / 2.6330 / 2.6214
  - bg-v4: 2.1288 / 2.0827 / 2.1199
- 같은 seed라서 쌍 검정도 했어요 (paired p 0.00092).
- Greedy GC의 FIO 쓰기 p99 지연은 더 낮았어요. 이 비교는 WAF만 본 것이에요.

## 3. Ablation (각자 자기 배치의 iCAT-v4로만 정규화)

| Variant | 같은 배치 V4 | WAF [95 % CI] | ΔWAF [95 % CI] | Δ % | Normalized | Holm p | 판정 |
|---|---|---|---|---|---|---|---|
| NoDrift | revD-v4 2.1386 | 2.2067 [2.0940, 2.3195] | +0.0681 [−0.0399, +0.1762] | +3.19 | 1.0319 | 0.234 | 차이 확인 못 함 |
| FullReset | revD-v4 2.1386 | 2.1982 [2.1477, 2.2488] | +0.0596 [+0.0160, +0.1033] | +2.79 | 1.0279 | 0.0721 | 보정 전 p .024, 보정 후 유의하지 않음 |
| NoDiscount | abl-v4 2.1390 | 2.1353 [2.0629, 2.2076] | −0.0038 [−0.0644, +0.0569] | −0.18 | 0.9982 | 1 | 차이 확인 못 함 |
| NoElim+NoSettle | abl-v4 2.1390 | 2.2632 [2.2460, 2.2803] | +0.1241 [+0.0730, +0.1753] | +5.80 | 1.0580 | **0.0277** | 유의 (V4가 낫다) |

- Holm 가족은 배치별로 2개 대비 × {전체, 단계 C} = 4예요.
- Normalized = 변형 WAF / 같은 배치 V4 WAF예요. 이 비율에는 CI가 없고, CI는 Δ에만 있어요.
- **NoElim+NoSettle**
  - abl 배치의 "묶음" 변형(VARIANT 2)이고, 고컴 revA V2와 같은 정책이에요.
  - 정착이 없으면 변화 감지와 probe도 정착 상태에서만 동작하므로 구조상 함께 꺼져요.
  - 그래서 이 행은 개별 기능이 아니라 네 기능을 묶어서 뺀 효과예요.

## 4. 소스코드 검증 (`feature_matrix.csv`, `run_config_check.csv`, `module_verification.csv`)

| Variant | 빌드 플래그 | 꺼진 기능과 근거 (revD-src/conv_ftl.c) | 커널 로그 확인 |
|---|---|---|---|
| NoDrift | `ICAT_VARIANT=1` | 567행 `ICAT_VARIANT != 1` → 감지 블록 567–579 건너뜀 | summary `reset=0` (3 run × 4 파티션) |
| FullReset | `ICAT_VARIANT=7` | 486–490행 `reset_epoch`에서 `active = WATGC_V2_ALLOWED` (45개 전부) | 리셋 직후 sample `active=45` (12/12). V4는 4–31 |
| NoDiscount | `ICAT_EXTRA=-DWATGC_V2_GAMMA_Q16=65536ULL` | 317–321행 discount가 γ=65536/65536=1에서 항등 (584–586행에서 호출) | init `gamma_q16=65536` |
| NoElim+NoSettle | `ICAT_VARIANT=2` | 620행 제거 `!= 2`, 540행 정착 `!= 2`. 감지(568행)와 probe(639–657행)는 settled일 때만 동작 | summary `elim=0 active=45 settled=0 reset=0` |
| drift50 (파라미터) | `ICAT_EXTRA=-DWATGC_V2_DRIFT_Q16=32768ULL` | conv_ftl.h:74–76 (572–573행에서 사용) | init에 문턱이 찍히지 않아요. objdump로만 확인했어요 |

- **init 줄 확인:** 측정 시작 init 줄 4개의 `revA_variant`, `gamma_q16`, `exploration_q16`, `candidates`가 24개 run 모두 등록값과 같아요.
  - 모든 run에서 C는 `exploration_q16=16384`(0.25)예요.
- **실행 모듈:** 기록된 플래그로 다시 빌드한 기계어가 실행 모듈과 7/7 같았어요 (차이 0줄).
  - 음성 대조로 검사 감도를 확인했어요. 상수 하나만 달라도 2–48줄, 분기가 다르면 404–3,023줄 차이가 났어요.
- **헤더:** `ICAT_VARIANT` 분기는 헤더에 6(후보 범위)과 9(난수 상태)뿐이에요. 1, 2, 7은 위의 `.c` 분기에서만 동작이 달라져요.
- `feature_matrix.csv`의 `gocom_crosscheck` 열은 고컴이 채울 칸으로 비워 뒀어요.

## 5. 검증한 수치

- WAF (전체, 단계 A/B/C, 단계 C 첫 5분)는 원시 카운터에서 다시 계산했어요.
  - 요약값과의 차이는 ≤ 4.9e-7이에요.
  - 고컴 Excel·집컴 자료와 불일치는 0이에요.
- 학습기 지표 (`learner_metrics_*.csv`)
  - 선택 변경 횟수가 기존 ablation 보고서와 같아요 (abl-v4 569, 묶음 867).
  - 첫 정착 전까지는 V4, NoDrift, FullReset, drift50이 똑같은 코드로 돌아요. 그래서 첫 정착 시간과 그때 남은 후보 수의 차이는 실행 간 잡음이에요.

## 6. 누락

| 항목 | 상태 |
|---|---|
| γ 0.99 / 0.95 / 0.90 | 승컴 자료 없음. 고컴 revF에서 각 1회 실행 중 |
| C 0.50 / 0.75 | 승컴 자료 없음 (승컴 소스는 C 0.25로 고정). 고컴 revF에서 실행 중 |
| γ 자료 | 승컴에는 NoDiscount(γ = 1.0) 하나뿐이에요. 기본값은 0.99가 아니라 0.9995예요 |
| 후보 제거 문턱 10 / 25 % | 고컴 revC |
| 변화 감지 12.5 % | 고컴 revE |
| W1~W4별 Greedy GC vs iCAT-v4 | 없음. mixFYF 하나뿐이고, 다른 부하에 대입하지 않았어요 |

## 7. 비교할 수 없는 실험

| 비교 | 이유 |
|---|---|
| Random vs Greedy GC | 호스트(고컴/승컴)와 배치가 달라요 |
| 서로 다른 배치의 V4 섞기 | 금지 조건이에요. 각 변형은 자기 배치의 V4로만 정규화했어요 |
| Online Greedy | 같은 배치에 V4가 없어서 간접 비교만 돼요 |
| 고컴 revF 결과와 승컴 결과 합치기 | 호스트가 달라요. revF는 n=1이라 통계도 내지 않아요 |
| 커널 CPU 시간 | 측정한 적이 없어요. ktime 경과 시간만 있어요 |

## 8. 작업 2 — 고컴 revF 독립 검증 (대기 중)

- 고컴이 `result/revF-20261127/raw`에 6개 run을 push하면 승컴이 검증해요.
  1. WAF 5종 (전체, 단계 A/B/C, 단계 C 첫 5분)을 원시 카운터에서 다시 계산해요.
  2. 커널 init 줄의 γ, C, VARIANT가 사전 등록과 같은지 확인해요.
- n=1이라 판정은 하지 않고, 값이 일치하는지만 보고해요.

## 갱신 (2026-11-28)

- `parameter_sensitivity.csv`의 C 행("승컴 미실험")은 이제 맞지 않아요.
- 승컴 C 0.50/0.75 × 3 결과는 `result/param-20261127-analysis/`에 있어요. 이 파일은 덮어쓰지 않았어요.
