# 승컴 Revision 결과 교차검증 (고컴, 원시 로그와 코드 기준)

- 작성: 2026-11-23 23시대, 고컴. 대상은 승컴이 main `2f6ae2dec`까지 올린 문서다: `report/revision-20261123/`, `analysis/revision/*.py`.
- **방법:** 승컴 스크립트를 import하거나 복사하지 않았다. 고컴에서 새로 작성한 `analysis/revision_gocom/verify_seungcom.py`로 원시 파일(summary.txt, control-series.txt, kernel.log, phase-*.time)에서 다시 계산했다.
- 결과 파일: `result/revision-gocom-20261123/verify_R{1,2,3,4}_*.csv`
- 승컴 E1/E2 실험 결과는 아직 없다(큐 진행 중). 이 문서는 **기존 자료로 만든 승컴 분석**만 검증한다.

## 0. 요약

| 항목 | 판정 | 핵심 |
|---|---|---|
| Random vs V4: "Random 구현과 결과가 없다" | **사실과 다름 (고컴 자료 미반영)** | 고컴 revA에 매 판단 구간 45개 균등 무작위 정책(`ICAT_VARIANT=9`)이 있고, mixFYF n=3 결과가 있다. 고컴 자료가 main에 아직 올라가지 않아서 생긴 차이다 |
| Random 고정 기댓값 계산 | 재현됨 (차이 0.0008, 원인 확인) | mixC는 일치한다. mixA는 arm 47의 반복 run 묶는 방식 차이 |
| V1/V4 코드 차이 표 | **일치** | 줄 번호와 값 모두 확인 |
| 회복 시간 계산 | 재구현 결과 170/170 일치. 다만 **정의에 문제가 있다** | 단측 기준이라 170개 구간 중 **98개가 첫 창에서 바로 "회복"으로 판정**된다 (첫 창이 이미 기준 이하인 구간은 106개. 11-23 정정) |
| 누적 탐색 비용 계산 | 재구현 결과 일치. 다만 **v7 drift reset 수가 과다 집계됐다** | v6 shift-reset이 "WATGC_V2 reset" 줄도 함께 찍는다. 104회는 drift 39회와 shift 65회의 합이다 |
| 자료구조 크기 10,112 B, 9.4 ns/GC | 출처 확인됨 (정의 주의) | `resource_overhead_final.md` 참조 |

## 1. Random Selection vs V4

### 1.1 "구현 없음" 주장 (random_selection_audit.md §1)
- 승컴은 main과 origin/icat-2만 검색했다.
- 고컴 revA(`revA-src/conv_ftl.c:611–613`, 11-14)에는 다음 코드가 있다:
  ```c
  #if ICAT_VARIANT == 9
  	return watgc_v2_random_arm(t);   /* uniform over the 45 allowed arms; no elimination, settling or drift */
  ```
  - 난수는 xorshift64*이고, seed는 splitmix(icat_seed, 파티션)이다.
  - 판단 구간, burn-in, 로그 형식은 V4와 같다.
- 결과 (고컴 mixFYF, n=3): Random 2.324 ± 0.006, V4 2.128 ± 0.005. 차이는 **+0.196 [0.184, 0.208]**이다 (`ablation_validation.md`, `result/final-20261123/tables/random_vs_v4.csv`).
- 이 자료는 브랜치 `report/final-20261123`에만 있고 main에는 아직 없다. **승컴이 볼 수 없었던 것이 원인이다.**
- **영향:** 승컴의 E2(random45, mixR×3, 약 9시간)는 고컴 revA Random과 설계가 같다(매 구간 45개 균등 추첨). 부하만 다르다(mixR×3 대 mixFYF, 둘 다 FIO-Fast → YCSB-A → FIO-Fast). E2를 그대로 할지, 다른 부하에서 반복 확인하는 용도로만 둘지는 사용자 판단이 필요하다.

### 1.2 Random 고정 기댓값 재계산 (`verify_R1_random_fixed.csv`)

| 부하 | 고컴 재계산 (45개 평균 / 중앙값 / 최상) | 승컴 |
|---|---|---|
| mixA 1배 | 1.9554 / 1.9390 / 1.7201 (arm 32) | 1.9546 / 1.9390 / 1.7158 (arm 47) |
| mixC 1배 | 1.9496 / 1.9304 / 1.7509 (arm 47) | 1.9496 / 1.9304 / 1.7502 (arm 47) |

- mixA 차이의 원인: 승컴은 arm 47에 `mixA-fixed47-rep{1,2,3}`과 `mixA-arm47-rep1` 4회를 평균했다(1.7158). 고컴은 `armNN` run만 썼다(arm 47 = 1.7322 1회). 둘 다 정당한 선택이다.
- **추가로 확인한 점:** 같은 arm 47을 1배로 4회 돌린 값이 1.690–1.732(범위 2.5 %)다.
  - "V4가 고정 기댓값보다 2.3–2.8 % 낮다"(V4 n=1)는 단일 run 잡음과 비슷한 크기다.
  - 승컴의 "통계적으로 유의하다고 말할 수 없다"는 판정은 맞다.

### 1.3 고컴 Random/V4 WAF를 두 경로로 계산 (`verify_R2_waf_two_paths.csv`)
- 경로 1: summary.txt 합계. 경로 2: control-series.txt의 30초 카운터, A 시작부터 C 끝까지.
- 13회 모두 차이가 0.003 이하다. 30초 샘플 경계 때문이다.
- Random − V4 차이는 경로 1에서 0.1959, 경로 2에서 0.1946이다.
- 이것은 **같은 카운터를 두 방식으로 읽은 계산 일치**다. 독립 계측 검증은 아니다.

## 2. V1/V4 코드 차이 (v1_ablation_audit.md §1)

| 항목 | 승컴 표 | 고컴 확인 (`online-mix-src` / `online-v4-src` conv_ftl.h) |
|---|---|---|
| 후보 수 | 60 / 45 | h:32 ARM_N 60 / h:33 ARM_LO 15 → 45 ✔ |
| 판단 구간 | 64 GC + 256 MiB / 128 GC + 512 MiB | h:41–42 / h:43–44 ✔ |
| 초기 순회 | 3회 / 1회 | h:50 MIN_VISITS 3 / h:52 1 ✔ |
| drift | 12.5 %, 3구간 / 25 %, 3구간 | h:56–57 8192 / h:58–59 16384 ✔ |
| 재방문 240, probe 8 | 같음 | h:55, h:54 / h:57, h:56 ✔ |
| 후보 제거 | 없음 / 15 % | — / h:34 9830 ✔ |

- **결론 일치:** 논문의 V1(online-mix)과 V4는 6가지가 동시에 다르다. 그래서 V1 대 V4로 변화 감지 효과를 말할 수 없다.
- **고컴이 덧붙일 것:**
  - 고컴 revA의 "V1"은 논문 V1이 아니다. V4에서 drift 검사 블록 하나만 끈 변형이다 (`revA-src/conv_ftl.c:563`, `ICAT_VARIANT != 1 &&`).
  - revA-src와 online-v4-src의 conv_ftl.c 차이는 변형 분기, 계측 카운터, 난수 함수뿐이다 (diff 87줄, 정책 로직 변경 없음).
  - 따라서 **revA-V1은 승컴 E1의 v4nodrift와 같은 질문에 답하는 기존 결과다** (mixFYF, n=3).
    - V1(감지 없음) 2.207 ± 0.052, V4 2.128 ± 0.005
    - 차이 +0.079 [−0.050, +0.207]로 **구분 불가**다
    - 전환 후 FIO-Fast 2만 보면 V1 2.606 ± 0.108, V4 2.443 ± 0.012다
  - 승컴 E1이 mixR×3에서 같은 결론을 낼지는 별도 부하의 반복 확인이 된다. 중복 여부는 사용자 판단이 필요하다.

## 3. WAF 회복 시간 계산식 (analysis/revision/recovery.py)

- **재구현 일치:** 승컴 정의를 그대로 고컴 코드로 다시 짰고, 170개 구간 모두 30초(1샘플) 안에서 일치했다 (`verify_R3_recovery.csv`). 승컴 정의는 다음과 같다:
  - 5분 이동창 WAF ≤ 1.05 × (구간 후반부 WAF)
  - 이 조건이 이후 10분 동안 유지되어야 한다
- **정의상 문제 (단측 기준):**
  - 170개 구간 중 106개는 첫 이동창(구간 시작 +300 s)부터 이미 기준 이하다. 그중 **98개는 이후 10분 유지 조건까지 만족해 첫 창에서 바로 회복으로 판정**된다. 그래서 회복 시간이 최솟값(약 300 s)으로 나온다.
  - 정정 (11-23 23:3x): 처음에는 106을 "첫 창에서 바로 통과"한 수로 적었다. 유지 조건까지 넣은 정확한 수는 98이다. 승컴 `recovery.csv`의 `first_window` 열(98개)과 고컴 재계산이 일치한다.
  - WAF가 구간 안에서 **올라가는** 경우(GC가 아직 덜 쌓인 FIO 구간 초반 등)에는 "회복"이 아니라 "아직 나빠지지 않음"을 재게 된다.
- 고컴 정의는 양측 ±5 %이고, 기준은 마지막 600 s다(revA, adapt-v7). 같은 구간에 적용하면 149/170에서 값이 정해진다. 두 정의의 값은 같은 축으로 비교할 수 없다.
- **권장:**
  1. 논문에는 단측 판정이 즉시 통과한 구간을 "회복 측정 대상 아님"으로 따로 표시한다. 또는 두 컴퓨터가 한 가지 정의(양측)로 통일한다.
  2. 기준을 "구간 후반부"로 잡으면 탐색 대상 구간과 기준 구간이 겹친다. 승컴 문서에 이 한계를 적는다.

## 4. 누적 탐색 비용 계산식 (analysis/revision/exploration.py)

| run | 항목 | 승컴 | 고컴 재계산 |
|---|---|---|---|
| iCAT V4 mixY 11월 | 판단 구간 / arm 전환 / 사용한 arm / reset / settled | 10,564 / 3,198 / 45 / 11 / 31 | 10,564 / 3,198 / 45 / 11 / 31 ✔ |
| iCAT v7 mixY 10월 (승컴 run) | 판단 구간 / arm 전환 | 97,359 / 27,793 | 97,359 / 27,793 ✔ |
| 같은 run | drift_resets | **104** | WATGC_V2 reset 줄 104 중 **65줄은 shift-reset이 함께 찍은 줄**이다. drift 경로만 세면 **39** |

- 근거 (같은 log, 5 µs 간격으로 두 줄이 찍힘):
  ```
  [2707689.886290] WATGC_V6 shift-reset part=0 window=579 arm=18 ...
  [2707689.886295] WATGC_V2 reset part=0 epoch=1 window=579 arm=18 reason=waf-drift ...
  ```
  - shift-reset 경로도 `reason=waf-drift`로 찍힌다. 그래서 reason 필드로도 두 경로를 구분할 수 없다.
- **권장:**
  - `exploration_counts.csv`의 v7 `drift_resets`를 "전체 reset 104 (shift 65 + drift 39)"로 고친다.
  - 고컴 adapt-v7 분석(고컴 v7 run, reset 109 = shift 80 + 나머지 29)도 같은 방식으로 표기했다.
- `arm_switches`(연속 구간 arm이 바뀐 횟수)와 `windows`(sample 줄 수)는 정의대로 계산됐다.

## 5. 고컴이 승컴에 전달할 사항

1. 고컴 revA와 revB 원본·분석이 **브랜치 `report/final-20261123`**에 있다. 아직 push하지 않았다. push하면 승컴이 E1/E2 중복 여부를 판단할 수 있다.
2. E2 random45 ≈ 고컴 revA-Random (n=3, mixFYF). E1 v4nodrift ≈ 고컴 revA-V1 (n=3, mixFYF).
3. 회복 시간 정의를 두 컴퓨터가 통일할 필요가 있다 (§3).
4. v7 drift reset 집계를 고쳐야 한다 (§4).
5. 10,112 B는 "학습 전용"이다(tuner 2,656 B − 고정 CAT도 쓰는 128 B, × 4). SmartGC "232배"는 GC 버퍼를 포함한 값이고, 학습 전용끼리는 193배다.

## 6. 추가 검증 (11-23 23시대): 승컴 490ff4021의 양측 회복 정의

- 승컴은 `recovery.py`에 양측 기준(`recovery2_s`)과 `first_window` 표시를 추가했다.
  - 양측 기준: |WAF/기준 − 1| ≤ 5 %
  - 기준: 구간 후반부 WAF
  - 5분 이동창, 10분 유지
- 고컴의 양측 정의(revA, adapt-v7)와 같은 170개 구간에서 비교했다. 125개는 30초 안에서 일치하고, 45개는 다르다.
  - 고컴 정의: 기준은 마지막 600 s WAF, 최근 300 s WAF, 180 s 유지, 구간 끝 600 s 전까지만 찾는다
  - 다른 이유는 기준 구간과 유지 시간이 다르기 때문이다. 계산 오류가 아니다.
- `first_window` 98개는 고컴 재계산과 정확히 같다 (단측과 양측 모두 98).
- **권장:** 논문에는 한 가지 정의만 쓴다. 승컴 정의(후반부 기준, 10분 유지)를 쓸 경우, 고컴 revA와 adapt-v7 회복 값을 그 정의로 다시 계산해야 한다. 새 실험은 필요 없고 약 1시간이 걸린다.

## 무효 고지 (2026-11-24, 고컴)

> **[2026-11-24 무효 고지, 고컴]** 이 문서가 인용한 YCSB 포함 run(9월·11-23 mixR, 9월 mixA)은 YCSB `SQLITE_FULL` 오염으로 YCSB 단계와 그 뒤 단계, 전체 WAF가 무효다. 근거: `report/final-e1-validation/README.md`, 승컴 `result/revision-20261123/mixR/INVALID-20261124.txt`. 아래 원문은 기록으로 남겨 두고 수정하지 않는다.

- 이 문서에서 영향받는 부분: mixA 1배 Random 고정 기댓값 대조(§1 표의 mixA 행, mixA 차이 원인 설명). mixC 행은 유효하다(FIO만 있음).
