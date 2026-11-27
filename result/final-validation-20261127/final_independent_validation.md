# iCAT 전체 실험 독립 검증 (승컴, 2026-11-27)

- 범위: 리비전 실험 전부 (Random Selection, revA–revE, Ablation, NoDiscount, NoElim, Online Greedy, Greedy GC, drift12, drift50, Arm 47, SmartGC, SmartGC-EQ8), 기존 논문 그림의 원천 (`mix-20260911`), M1 자원 비용
- 방법: 원시 로그에서 직접 다시 계산했어요. 고컴·집컴·기존 승컴 분석 코드는 가져오지 않았어요.
- 판정 용어는 **일치 / 불일치 / 미검증** 세 가지만 써요. "PASS" 표시는 하지 않아요.
- 새 실험은 돌리지 않았고, 원시 로그도 고치지 않았어요.

## 0. 먼저 알려야 할 발견

| # | 발견 | 근거 | 영향 |
|---|---|---|---|
| 1 | **SmartGC mixY 실행은 부하 조건이 같지 않았어요.** 30분짜리 단계가 최대 83.6분까지 늘었고, 전체 시간은 10 h가 아니라 최대 12.7 h였어요 | `final_robustness_validation.csv` "mixY 동일 조건": 승컴 SmartGC 7/20 단계 초과 (12.7 h), 고컴 SmartGC 7/20 (12.5 h), 고컴 SmartGCq 3/20 (11.1 h), SmartGC-EQ8 두 호스트 모두 2/20 (S04 32.5분, S07 31.7–31.8분). iCAT·CAT-47·Greedy는 20/20 단계 모두 약 30분 | SmartGC 계열 WAF는 다른 양의 쓰기에서 나온 값이에요. 고컴 Excel `SmartGC Comparison` B7의 "20단계 × 1800 s = 10 h"는 사실과 달라요 |
| 2 | **NoElim은 다른 배치 대조군과 비교할 때만 유의해요.** | 같은 배치 revE: NoElim − V4 = +0.091 [+0.030, +0.153], p .023, **Holm .091**. 다른 배치 revB NoElim − revA-V4: +0.094 [+0.070, +0.118], p .0015 (집컴 F7은 Holm .003으로 표기) | 직접 근거는 revE예요. revB−revA는 배치가 달라 "참고"로만 써야 해요. revB 안의 V4는 n=1이라 검정할 수 없어요 |
| 3 | **커널 CPU 시간은 어디서도 측정되지 않았어요.** 여러 문서가 ktime 경과 시간을 "CPU"라고 부르고 있어요 | `final_m1_resource_validation.md` 4절 | 표기를 "경과 시간 (ktime)"으로 바꿔야 해요 |
| 4 | **소스 코드 Git SHA는 대부분 기록되지 않았어요.** | `final_raw_data_validation.csv` `source_commit` 열 | 빌드 정체성은 모듈 sha256으로만 확인할 수 있어요 (아래 1.2) |

## 1. 원시 데이터 검증 (`final_raw_data_validation.csv`, 111개 실행 폴더)

### 1.1 유효성

| 호스트 | 배치 | 본 실행 | 유효 | smoke 등 |
|---|---|---|---|---|
| 승컴 | revD-20261124 (NoDrift/FullReset) | 9 | 9 | 4 |
| 승컴 | revision-additional-ablation (NoDiscount/OffBundle) | 9 | 9 | 3 |
| 승컴 | greedy-20261125 (Online Greedy) | 3 | 3 | 1 |
| 승컴 | batchG-20261126 / drift50 / greedygc | 9 | 9 | 3 |
| 승컴 | arm47-20261127 | 3 | 3 | 1 |
| 승컴 | smartgc-20261119/resume (SmartGC 재실행, iCAT V4) | 2 | 2 | 0 |
| 승컴 | gc-20261010 폴더 안의 11-19~20 SmartGC 캠페인 (EQ8, sg-arm47, SmartGC 1차) | 3 | **2** | 2 |
| 고컴 | revA-20261114 (Random, V1, V2, V4, Arm 47) | 13 | 13 | 2 |
| 고컴 | revB-20261122 (NoElim, NoSettle, Arm60, V4 n=1) | 8 | 8 | 3 |
| 고컴 | revC-20261124 (원래 iCAT "online", Elim10/25, Arm60) | 15 | 15 | 0 |
| 고컴 | revE-20261125 (drift12, NoElim) | 9 | 9 | 0 |
| 고컴 | gocom-sg-20261119 (SmartGC, SmartGCq, sg-arm47, sg-greedy) | 4 | 4 | 1 |
| 고컴 | m1-20261126 (iCAT-v4, SmartGC-EQ8, mixY) | 2 | 2 | 2 |
| **합계** | | **89** | **88** | 22 |

- 무효 1건: 승컴 `gc-20261010/mixY-smartgc-rep1` (11-20 1차 시도)
  - 디스크가 가득 차서 13/20 단계에서 멈췄어요 (`smartgc-20261119/queue-fail-diag.txt`).
  - 11-22 `smartgc-20261119/resume/mixY-smartgc-rep1`에서 처음부터 다시 돌렸어요. 이어서 돌린 것이 아니에요. 새 insmod를 했고, 시작 카운터가 0이며, environment 시작 시각이 11-22 18:51이에요.
- 유효 88건 공통 결과
  - exit 0, FIO 오류 0, 커널 오류 0 (BUG, WARNING, Oops, Call Trace), SQLITE_FULL 0이에요.
  - YCSB 성공률은 100 %예요 (mixFYF와 sqlite 단계가 있는 부하).
  - mixY는 varmail 6단계가 모두 "IO Summary"에 도달했어요.
  - 시작 카운터 0, preset·mkfs가 있어요.
  - 두 경로 WAF(전체 줄, 파티션 합)가 1e-9 이내로 같아요.
  - summary.txt 값과의 차이는 최대 4.9e-7이에요 (소수 6자리 반올림).
- 호스트는 폴더 위치가 아니라 `environment.txt`의 nodename으로 정했어요.
  - 승컴 = oy-System-Product-Name, i7-7700
  - 고컴 = oy-B550M-DS3H, Ryzen 5 3600XT

### 1.2 Git SHA와 모듈 SHA256

| 항목 | 결과 |
|---|---|
| 모듈 sha256 = 등록값 | 106 폴더 일치. 고컴 `gocom-sg-20261119` 5개는 등록 해시 파일이 없어 **미검증**이에요 |
| 소스 Git SHA | revA, revB = `c06a372a5` (로컬 변경 있는 작업 트리). SmartGC 캠페인 = 실행 시작 시 HEAD (`*.commit.txt`, `report/compare.csv`). m1 = 분석 시점 HEAD `c06a372a5`. **나머지 배치는 미기록**이에요. 승컴 배치는 `sources.sha256`(소스 파일 해시)가 있어요 |
| 원시 로그 커밋 | 모든 폴더에 있어요 (`raw_log_commit` 열). 이 값은 로그를 올린 커밋이지 소스 버전이 아니에요 |

### 1.3 seed와 초기화

- FIO seed는 모든 mixFYF 실행에서 20260910/20261010/20261110 + rep 규칙을 따랐어요.
- icat_seed는 2026111400 + rep이에요. Arm 47과 Greedy GC는 해당 없어요.
- 같은 배치 안에서는 같은 rep끼리 seed가 같았어요. 그래서 짝 비교(paired)는 같은 배치 대비에만 붙였어요.

## 2. 통계 검증 (`final_statistical_validation.csv`)

- 방법
  - 평균, SD, t 95 % CI (df = n−1)
  - Welch t 검정, Hedges g
  - 같은 배치·같은 seed 짝 비교 (paired t, df 2)
  - Holm 보정: 배치별로 (대비 수 × 전체·단계 C)
- n<3이면 평균 차이만 적고 CI나 검정은 하지 않았어요 (revB의 V4 n=1, mixY n=1 전부).

| 대비 (같은 배치) | 호스트 | 전체 WAF Δ [95 % CI] | p | Holm | 단계 C Δ | Holm | 판단 |
|---|---|---|---|---|---|---|---|
| Random − V4 (revA) | 고컴 | +0.196 [+0.184, +0.208] | <.001 | <.001 | +0.366 | <.001 | 차이 있음 |
| V1 − V4 (revA) | 고컴 | +0.079 [−0.050, +0.207] | .121 | .237 | +0.163 | .237 | 구분 안 됨 |
| V2 − V4 (revA) | 고컴 | +0.136 [+0.117, +0.154] | <.001 | <.001 | +0.249 | <.001 | 차이 있음 |
| 원래 iCAT − V4 (revC) | 고컴 | +0.275 [+0.203, +0.347] | .004 | .028 | +0.447 | .042 | 차이 있음 |
| Elim10 / Elim25 / Arm60 − V4 (revC) | 고컴 | +0.024 / +0.051 / +0.028 (CI 모두 0 포함) | ≥ .079 | ≥ .47 | | | 구분 안 됨 |
| NoDrift − V4 (revD) | 승컴 | +0.068 [−0.040, +0.176] | .117 | .234 | +0.141 | .234 | 구분 안 됨 |
| FullReset − V4 (revD) | 승컴 | +0.060 [+0.016, +0.103] | .024 | .072 | +0.130 | .060 | Welch CI는 0 제외, Holm 후 유의하지 않음 |
| NoElim − V4 (revE) | 고컴 | +0.091 [+0.030, +0.153] | .023 | .091 | +0.155 | .091 | Welch CI는 0 제외, Holm 후 유의하지 않음 |
| drift12 − V4 (revE) | 고컴 | +0.072 [+0.012, +0.132] | .029 | .091 | +0.148 | .091 | Welch CI는 0 제외, Holm 후 유의하지 않음 |
| NoDiscount − V4 (abl) | 승컴 | −0.004 [−0.064, +0.057] | .869 | 1 | −0.010 | 1 | 구분 안 됨 |
| OffBundle − V4 (abl) | 승컴 | +0.124 [+0.073, +0.175] | .007 | .028 | +0.217 | .028 | 차이 있음 |
| Greedy GC − V4 (batchG) | 승컴 | +0.519 [+0.463, +0.574] | <.001 | .001 | +0.708 | .004 | 차이 있음 (V4가 WAF 낮음) |
| drift50 − V4 (batchG) | 승컴 | +0.018 [−0.045, +0.081] | .459 | .831 | +0.042 | .831 | 구분 안 됨 |

| 대비 (다른 배치, 참고만) | 호스트 | 전체 WAF Δ [95 % CI] | p |
|---|---|---|---|
| Online Greedy − revD-V4 | 승컴 | −0.009 [−0.051, +0.034] | .543 |
| Online Greedy − abl-V4 | 승컴 | −0.009 [−0.058, +0.040] | .632 |
| Arm 47 − batchG-V4 | 승컴 | −0.123 [−0.184, −0.062] | .013 |
| revB NoElim − revA-V4 | 고컴 | +0.094 [+0.070, +0.118] | .0015 |
| revB NoSettle − revA-V4 | 고컴 | +0.087 [−0.109, +0.282] | .197 |

- 사전 등록과의 관계
  - revD는 Welch CI가 주 판정이에요. revE는 Holm을 "민감도 분석"으로 등록했어요. 그래서 FullReset, NoElim, drift12를 "Welch CI 기준 차이"로 쓰는 것은 등록과 맞아요. 다만 Holm 값을 함께 적어야 해요.
  - revA는 Holm 가족을 등록하지 않았어요. 전체 WAF만 묶으면 3개, 단계 C까지 묶으면 6개예요. 어느 쪽이든 V2와 Random은 유의하고 V1은 유의하지 않아요.
- V4 배치 간 재현성 (다른 배치끼리 비교, 합치지 않음): 승컴 3배치, 고컴 3배치 모두 |Δ| ≤ 0.029이고 CI는 0을 포함해요.

## 3. Robustness 검증 (`final_robustness_validation.csv`)

| 항목 | 결과 | 판정 |
|---|---|---|
| Random Selection 반복 간 편차 | 전체 WAF 2.3265 / 2.3285 / 2.3180, SD 0.0055, CV 0.24 % (단계 A·B·C의 CV 0.22–0.46 %) | 일치 (n=3, 매우 작음) |
| Arm 47 독립 3회 | 승컴 3/3 유효, rep마다 seed 다름, 4개 파티션 모두 arm=47, 모듈 고컴과 같은 파일. 1.98764 ± 0.00027, 고컴 n=1 1.987355는 95 % CI [1.98698, 1.98831] 안 | 일치 (호스트가 달라 n=4로 합치지 않음) |
| drift50 변화 감지 동작 | 3회 모두 waf-drift 리셋이 50 % 문턱을 넘었어요 (리셋 4/4/3회, 최소 편차 0.614). 비교 기준: batchG V4의 리셋 12건 중 편차 25–50 % 구간은 **0건** → 이 부하에서는 25 %와 50 % 문턱이 다르게 동작할 기회가 거의 없었어요. revE drift12는 25–50 % 구간 리셋이 1–3건 | 일치 (동작 정상) |
| Greedy GC 대 iCAT 같은 조건 | rep별로 호스트, CPU, 커널 cmdline, FIO job, YCSB workload, seed, 단계 구성, 초기화가 모두 같아요. 다른 것은 모듈뿐 (단계 시간 30.0–30.3분) | 일치 |
| 호스트·배치 혼합 | 39개 그룹 모두 호스트 1개 × 배치 1개예요. 다른 배치 대비 21개는 "간접"으로 표시했어요 | 일치 (혼합 없음) |
| mixY 단계 시간 | 0절 발견 1 참고 | **불일치** (SmartGC 계열) |
| 리비전 그림 반복 횟수 (집컴 `figure_manifest.csv` 주장 14개) | 14/14 원시 유효 반복 수와 같아요 | 일치 |
| 기존 논문 그림 원천 (`mix-20260911`) | 4절 참고 | 4절 |

## 4. 기존 논문 그림의 반복 횟수 (`final_prerevision_figure_validation.csv`)

PRE_REVISION_SECTION

## 5. 다른 PC 결과와의 대조

### 5.1 고컴 Excel `report/final-revision/iCAT_Complete_Experiment_Results.xlsx` (`origin/report/data-validity-20261124@3fdb21258`, 17개 시트)

- 표: `excel_cell_validation.csv`. 칸마다 시트, 셀, Excel 값, 재계산 값, 차이, 원시 로그 위치를 적었어요.

| 대조 방식 | 칸 수 | 일치 | 불일치 | 미검증 |
|---|---|---|---|---|
| 행 키로 대조 (Raw Results, Run Validity, Statistical Analysis의 run·그룹·대비) | 3,016 | 3,016 | **0** | 0 |
| 값으로 대조 (나머지 시트의 숫자 칸) | 4,500 | 4,214 | 0 | 286 |

- 미검증 286칸은 모두 이번 재계산에 없는 지표예요. 불일치가 아니라 "확인하지 않음"이에요.
  - Workload Adaptation 시계열 구간값 148칸
  - Secondary Metrics 99칸 (탐색 비용 비중, 적응 시간, 지연 p99)
  - Memory Overhead 이론값 29칸 (sizeof 계산)
  - Statistical Analysis 9칸 (고컴 자체 대조표의 |차| 같은 메타값)
  - CPU and Timing 1칸 (µs 단위 환산 1개)
- 숫자 말고 고쳐야 할 서술 (불일치)

| Excel 위치 | Excel 내용 | 원시 로그 | 원인 | 수정 권고 |
|---|---|---|---|---|
| `SmartGC Comparison` B7 | "mixY 20단계 × 1800 s = 10 h" | SmartGC 단계가 최대 83.6분, 전체 11.1–12.7 h (`phase-S*-start/end.time`) | SmartGC가 FIO 단계를 제시간에 끝내지 못함 | SmartGC 계열은 실제 시간을 적고 "같은 부하가 아님"을 한계에 추가 |
| `Memory Overhead` B9, `Executive Summary` E27 | iCAT 학습 자료구조 10,112 B (m1 비교) | m1 빌드 tuner 2,712 B. 10,112 B는 resource-v124 빌드 (2,656 − 128) × 4 | 다른 빌드의 계산값을 함께 씀 | 출처 빌드 명시, 또는 m1 빌드 값 10,336 B 사용 |
| `SmartGC Comparison` 24행 머리글 | 6번째 열 "WAF_nand (summary)" | 그 열에는 경로가 들어 있어요 | 열 이름 오류 | 열 이름을 "원시 경로"로 |
| `Ablation Study`, `Drift Threshold`의 "차이 있음" | FullReset, NoElim(revE), drift12 | Holm .060–.091 | 판정이 보정 전 Welch CI 기준 | 판정 옆에 "Holm 후 유의하지 않음" 병기 |

- 칭찬할 점: Excel은 ktime을 "CPU 시간 아님"으로 명시했어요. revC의 "online"을 "원래 iCAT"으로 바르게 구분했어요. Online Greedy 비교는 "간접"으로 표시했어요.

### 5.2 집컴 전달 패키지 (`origin/report/home-delivery-20261127`)

- `final_experiment_validity.csv` 80개 실행 × 8개 필드 (host·gc pages, 전체·단계 WAF, 모듈 sha, seed, 유효성): **모두 일치**
- `final_statistical_audit.csv` 35개 대비 × Δ, CI, df, p, g, paired p: **모두 일치**
  - Holm 2칸은 가족 정의만 달라요 (revA 3개 vs 6개). 집컴 정의로 다시 계산하면 같아요.
- 집컴 F7 (revB NoElim/NoSettle − revA-V4)에 Holm을 붙인 것은 다른 배치 대비예요. 주 근거로 쓰면 안 돼요 (0절 발견 2).

## 6. 결론

| 질문 | 답 |
|---|---|
| 고컴 Excel 숫자가 원시 로그와 맞는가 | 대조한 7,230칸 모두 일치해요. 불일치 0이에요. 286칸은 미검증이에요 (재계산하지 않은 지표) |
| 무효 실행이 통계에 들어갔는가 | 아니요. 무효 1건(SmartGC 1차 시도)은 어느 표에도 없어요 |
| 호스트·배치를 섞었는가 | 아니요. 다른 배치 대비는 모두 "간접"으로 표시돼 있어요 |
| n=1에 CI나 유의성을 붙였는가 | 아니요 (Excel, 집컴, 이 검증 모두) |
| 논문 전에 고쳐야 할 것 | SmartGC 단계 시간 초과 명시, 10,112 B 출처, "CPU" 표기, NoElim 근거를 revE로 한정, Holm 병기 |

## 7. 재현

```
# 고컴 원시 로그
git archive origin/report/data-validity-20261124 result/{revA-20261114,revB-20261122,revC-20261124,revE-20261125,gocom-sg-20261119,m1-20261126,m1-20261126-final,m1-20261126-analysis} | tar -x -C G
git archive origin/resource-overhead-20261114 result/resource-v124-20261114 | tar -x -C G
python3 -I -B analysis/revision/final_validation.py G
python3 -I -B analysis/revision/m1_validation.py G
uv run --no-project --with openpyxl python -I -B analysis/revision/excel_validation.py <xlsx>
```
