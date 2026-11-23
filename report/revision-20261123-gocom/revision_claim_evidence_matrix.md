# Revision 주장–근거 매트릭스 (고컴)

- 작성: 2026-11-23, 고컴.
- 코드 줄 번호는 `online-v4-src` 기준이다. revA/revB 변형은 `revA-src`, `revB-src` 기준이다.
- 원시 결과 경로는 저장소 루트 기준이다. 고컴 자료는 브랜치 `report/final-20261123`에 있다.
- 통계:
  - 평균 ± SD, 95 % CI는 t 분포다.
  - 두 집단 비교는 Welch 검정이다.
  - n=1에는 유의성을 부여하지 않는다.
- 판정:
  - **입증:** 같은 조건, n ≥ 3, CI가 0을 포함하지 않음
  - **일부 입증:** 한 부하만, 정의 문제, 또는 다른 기능과 함께 묶여 있음
  - **미입증:** CI가 0을 포함하거나, n=1이거나, 데이터가 없음

## 1. 집중 검증 항목

| 주장 | 코드 근거 | 실험 근거 (원시 결과) | 통계 근거 | 판정 | 추가 실험 (예상 시간) |
|---|---|---|---|---|---|
| **후보 제거가 WAF를 낮춘다** | h:34 `ELIM_Q16 9830` (15 %), c:581–598. 제거를 끈 변형: `revB-src/conv_ftl.c:616` (VARIANT 3) | `result/revA-20261114/raw/mixFYF-revA-v4-rep{1,2,3}`, `result/revB-20261122/raw/mixFYF-revB-noelim-rep{1,2,3}` | noelim − V4 = **+0.094 [+0.070, +0.118]** (V4 2.128 ± 0.005, noelim 2.223 ± 0.011). FIO-Fast 1 +0.033 [0.022, 0.045], FIO-Fast 2 +0.161 [0.125, 0.197] | **입증** (mixFYF, n=3. 다른 부하는 없음) | 다른 부하 반복은 선택 사항 |
| 후보 제거 효과 (정착 없음) | V2 대 nosettle (`revA-src:536,616`, `revB-src:536`) | `…/mixFYF-revA-v2-*`, `…/mixFYF-revB-nosettle-*` | +0.049 [−0.144, +0.241]. FIO-Fast 1에서만 +0.032 [0.001, 0.063] | 일부 입증 (첫 구간만) | — |
| **정착이 WAF를 낮춘다** | h:53–55, c:489–520. 끈 변형 `revB-src:536` (VARIANT 5). drift와 probe도 함께 꺼진다 | `…/mixFYF-revB-nosettle-rep{1,2,3}` | nosettle − V4 = +0.087 [−0.108, +0.282]. nosettle SD 0.079 (2.143–2.300). 제거가 꺼진 상태(V2 − noelim)에서는 +0.041 [0.018, 0.065] | **미입증** (V4 구성에서). 제거가 꺼진 조건에서만 일부 입증 | nosettle·V4 같은 배치 각 3회 추가 (약 9.2 h) |
| **45개 탐색 공간 제한** | h:33 `ARM_LO 15`. 끈 변형 `revB-src/conv_ftl.h` (VARIANT 6, ARM_LO 0) | `…/mixFYF-revB-arm60-rep1`. 승컴 `result/mix-20260911/t4-onlinev3k2-rep1-x18` (v3 + k=2 복원) | arm60 2.128 (n=1) = V4 2.128. v3k2: 1.848 → 1.905 (+3.1 %, n=1, FIO-Fast 3 h, 승컴) | **미입증** (두 결과 모두 n=1이고 방향도 엇갈림) | arm60 2회 추가 (약 3 h) |
| **변화 감지 효과** | h:58–59, c:534–545 | 고컴 `…/mixFYF-revA-v1-rep{1,2,3}` (drift만 끔, 동작은 v4nodrift와 같음). 승컴 E1 진행 중 `result/revision-20261123/mixR/` | revA-V1 − V4 = +0.079 [−0.050, +0.207]. FIO-Fast 2: V1 2.606 ± 0.108, V4 2.443 ± 0.012 | **미입증** (E1 대기) | 승컴 E1 (약 27 h 남음) |
| **재탐색 범위 (살아남은 후보 + 이웃)** | c:459 `watgc_v2_grow`. 비교 변형 fullreset c:459 `WATGC_V2_ALLOWED` | 승컴 E1 v4fullreset | 없음 | **미입증** | E1 |
| **워크로드 변화에 빠르게 반응한다** | v6/v7 shift-reset, V4 drift | 고컴 v7: `result/v7-20261011-icat2/mixY/mixY-onlinev7-rep1`, 분석 `result/adapt-v7-mixY-20261122/`. V4: `result/revA-20261114/results/workload_transition.csv` | v7: Varmail이 낀 전환 48/48 감지 (중앙값 7–30 s). F↔S 전환은 7/28만 감지. V4 (mixFYF): YCSB-A → FIO-Fast 전환 뒤 첫 reset 61.7–65.5 s (3/3). FIO-Fast → YCSB-A는 850–1,868 s | 일부 입증 (v7은 n=1. V4는 한 방향만) | 승컴 E1에서 V4 감지 시각 (E1에 포함) |
| **WAF 회복 시간** | — (분석 정의) | 고컴: `revA-20261114/results/waf_recovery.csv`, `adapt-v7-mixY-20261122/phase_summary.csv`. 승컴: `report/revision-20261123/recovery.csv` | V4 (자기 기준 ±5 %): 636 / 996 / 786 s. CAT-47 같은 구간 WAF × 1.05 기준으로는 모든 학습기가 미회복. v7: 19구간 중 18 회복. **승컴 단측 정의에서는 98/170 구간이 첫 창에서 바로 회복으로 판정** | 일부 입증 (정의가 통일되지 않음) | 새 실험은 필요 없음. 정의를 통일해 재계산 (1 h) |
| **탐색 CPU 오버헤드가 작다** | 계측 `revA-src/conv_ftl.c:737–745` (observe + set_arm) | `revA-20261114/results/resource/resource_summary.csv`, 승컴 `origin/resource-overhead-20261114:result/resource-v124-20261114/report/cpu_overhead_summary.csv` | 측정: V4 결정 경로 3.88 ± 0.11 ms / 90분, 1회 3.9 µs (최대 13.4). res-v4 (FIO-Fast 30분): 결정 2.78 ms, GC 훅 순비용 9.43 ± 0.12 ns/GC (차분), dispatcher 대비 0.0011 %. 추정: mixY 10 h 0.97 s | **입증** (iCAT 자체). SmartGC 대비 비교는 미입증 (SmartGC 미측정) | SmartGC 계측 빌드 (mixY 약 12 h) |
| **학습 메모리 오버헤드가 작다** | gdb `sizeof(struct watgc_v2_tuner)` = 2,656 B (online-v4 db93f822). SmartGC: `smartgc_cand` 32 B, `smartgc` 232 B, `line` 72 B (29b5f116b 소스를 고컴에서 빌드) | `resource_overhead_final.md`, 승컴 `result/smartgc-20261119/report/compare.csv` | 계산: iCAT 학습 전용 10,112 B (구조체 전체 10,624 B). SmartGC 학습 1,951,648 B (GC 버퍼 포함 2,343,936 B), 193배 (232배). 측정 (n=1): VmallocUsed 차이 SmartGC +2,010 kB, V4 −854 kB (CAT-47 대비) | **입증** (계산값 기준). 측정값은 방향만 맞음 (n=1) | 불필요 |

## 2. 그 밖의 주장

| 주장 | 코드 근거 | 실험 근거 | 통계 | 판정 | 추가 실험 |
|---|---|---|---|---|---|
| Random 선택보다 낫다 | `revA-src/conv_ftl.c:611–613` | `…/mixFYF-revA-random-rep{1,2,3}` | Random − V4 = +0.196 [0.184, 0.208]. 같은 rep끼리 +0.196 [0.174, 0.218]. 8.43 % 개선 | **입증** (mixFYF, n=3) | 불필요 (E2 생략 타당) |
| V1(논문)보다 낫다 | online-mix 대 online-v4, 6가지 차이 | 승컴 resource-v124 FIO-Fast 30분 n=3 | V1 2.026 ± 0.001, V4 1.903 ± 0.001 | 입증 (전체 개선만. 기능별 기여는 분리 안 됨) | — |
| SmartGC보다 WAF가 낮다 (mixY) | — | `result/smartgc-20261119/resume/mixY-onlinev4-rep1`, `result/gc-20261010/mixY-smartgc-eq8-rep1` | WAF_nand 3.211 대 4.492 (−28.5 %). 각 n=1. 원시 카운터 재계산 일치 | 일부 입증 (n=1이지만 차이 크기가 큼) | 반복 (회당 10–12 h) |
| CAT-47(고정 최적)과 비슷하거나 낫다 | — | 같은 배치 `result/gc-20261010/mixY-sg-arm47-rep1` | 3.211 대 3.233 (−0.7 %), n=1. 10월 기준선 2.864는 10-10 run 하나만 다른 이상치다(E0와 10월 다른 run 5개, `cat47_baseline_audit.md` §5) | **미입증** | 반복 |
| SmartGC보다 지연과 처리량이 좋다 | channel_model.c:74 경고 | `result/final-20261123/tables/chmodel_warning_impact.csv` | FIO p99 0.24 ms 대 21.6 ms. FIO 구간이 최대 4,167 s로 늘어남 | 일부 입증 (n=1. 경고 구간에서는 SmartGC 지연이 과소 계산됨) | — |

## 3. 요약

- **입증:** 후보 제거 효과, Random 대비 우위, 학습 CPU와 메모리가 작다는 것 (iCAT 자체)
- **일부 입증:** 워크로드 변화 반응, 회복 시간(정의 통일 필요), SmartGC 대비 WAF(n=1)
- **미입증:**
  - 정착 효과 (V4 구성에서)
  - 45개 제한 효과
  - 변화 감지 효과, 재탐색 범위 효과 (E1 대기)
  - CAT-47 대비 우위
  - 파라미터 민감도
- 제출 전 필수 조치와 데이터 부족 항목은 `revision_independent_audit.md` §3에 정리했다.
