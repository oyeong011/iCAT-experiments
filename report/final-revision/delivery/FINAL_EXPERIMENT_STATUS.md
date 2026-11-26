# 최종 실험 완료 현황 및 입력 자료 수신 상태 (`FINAL_EXPERIMENT_STATUS.md`)

- **작성 시각**: `2026-11-27 08:48:37 KST`
- **기준 커밋**: 승컴 `origin/main @ 4689c6797` / 고컴 `origin/report/data-validity-20261124 @ 67cf3f901` / 자원 계측 `origin/resource-overhead-20261114 @ c046de0d0`

## 1. 전체 리비전 핵심 실험 완료 현황 (**80/80 VALID, RUNNING 0건**)

| 배치 / 캠페인 | 호스트 | 워크로드 | 계획/유효 | 심사 대응 | 검증 주체 | 최종 상태 |
|---|---|---|---:|---|---|---|
| `revA-20261114` (`v4/random/v1/v2/arm47`) | 고컴 (Ryzen 3600XT) | `mixFYF 250k` (90m) | 13 / 13 | M2, M3 | 고컴·집컴 | **완료·검증 (arm47 n=1 분리)** |
| `revB-20261122` (`noelim/nosettle/v4/arm60`) | 고컴 (Ryzen 3600XT) | `mixFYF 250k` (90m) | 8 / 8 | M2 (참고) | 고컴·집컴 | **완료·교차배치 단서 (`revE`로 대체)** |
| `revC-20261124` (`v4/elim10/elim25/arm60/online`) | 고컴 (Ryzen 3600XT) | `mixFYF 250k` (90m) | 15 / 15 | M3-2, M6-1/2 | 고컴·집컴 | **완료·검증** |
| `revD-20261124` (`v4/nodrift/fullreset`) | 승컴 (i7-7700) | `mixFYF 250k` (90m) | 9 / 9 | M2-3/5 | 승컴·고컴·집컴 | **완료·3자 검증** |
| `abl-20261125` (`v4/nodiscount/bundle-off`) | 승컴 (i7-7700) | `mixFYF 250k` (90m) | 9 / 9 | M2-2/6 | 승컴·고컴·집컴 | **완료·3자 검증** |
| `revE-20261125` (`v4/noelim/drift12`) | 고컴 (Ryzen 3600XT) | `mixFYF 250k` (90m) | 9 / 9 | M2-1, M6-3 | 고컴·집컴 | **완료·검증** |
| `greedy-20261125` (`greedy-online VAR=8`) | 승컴 (i7-7700) | `mixFYF 250k` (90m) | 3 / 3 | M3-3 | 승컴·고컴·집컴 | **완료·3자 검증 (Honest Null)** |
| `batchG-20261126` (`bg-v4/greedygc/drift50`) | 승컴 (i7-7700) | `mixFYF 250k` (90m) | 9 / 9 | M3-5, M6-3 | 승컴·고컴·집컴 | **완료·3자 검증 (0/36 불일치)** |
| `arm47-20261127` (`Fixed Arm 47 n=3`) | 승컴 (i7-7700) | `mixFYF 250k` (90m) | 3 / 3 | Robustness | 승컴·집컴 | **완료·검증 (`1.98764±0.00027`)** |
| `m1-20261126` (`iCAT-v4` vs `SmartGC-EQ8`) | 고컴 (Ryzen 3600XT) | `mixY 10h` (20단계) | 2 / 2 (`n=1`) | M1, M5 | 고컴·집컴 | **완료·검증 (`rep2–3` 사용자 취소)** |
| **보조 검증 셋** (`resource-v124`, `3×60` 스윕, 레거시 Greedy 9종) | 승컴 | FIO-Fast 30m / 60-arm / x1 9종 | 246 / 246 | M5, M6-2, M3-5 | 집컴 | **완료·검증** |
| **제외된 무효 실행** (`SQLITE_FULL` 224+건, `mixG` 34건, `ENOSPC` 1건, 10월 `mixY` 이상치) | 양 호스트 | 구 `mixR`/전환/`mixY` | 0 / 260+ | M4-7 | 고컴·집컴 | **엄격 제외 (재사용 금지)** |

## 2. 고컴·승컴 신규 통합 입력 파일 수신 상태 (`0/5` 고컴, `0/5` 승컴)

| 소속 PC | 지시 입력 파일 | 원격 브랜치 | 수신 상태 | 경로 / 비고 |
|---|---|---|---|---|
| 고컴 | `iCAT_Complete_Experiment_Results.xlsx` | `origin/report/data-validity-20261124` (`67cf3f901`) | **미푸시 대기 (WAITING_PUSH)** | `아직 원격에 없음 — push 감지 즉시 교차검증 예정` |
| 고컴 | `EXPERIMENT_CATALOG.md` | `origin/report/data-validity-20261124` (`67cf3f901`) | **미푸시 대기 (WAITING_PUSH)** | `아직 원격에 없음 — push 감지 즉시 교차검증 예정` |
| 고컴 | `EXPERIMENT_RESULT_SUMMARY.md` | `origin/report/data-validity-20261124` (`67cf3f901`) | **미푸시 대기 (WAITING_PUSH)** | `아직 원격에 없음 — push 감지 즉시 교차검증 예정` |
| 고컴 | `FIGURE_CATALOG.md` | `origin/report/data-validity-20261124` (`67cf3f901`) | **미푸시 대기 (WAITING_PUSH)** | `아직 원격에 없음 — push 감지 즉시 교차검증 예정` |
| 고컴 | `DATA_PROVENANCE.csv` | `origin/report/data-validity-20261124` (`67cf3f901`) | **미푸시 대기 (WAITING_PUSH)** | `아직 원격에 없음 — push 감지 즉시 교차검증 예정` |
| 승컴 | `final_independent_validation.md` | `origin/main` (`4689c6797`) | **미푸시 대기 (WAITING_PUSH)** | `아직 원격에 없음 — push 감지 즉시 교차검증 예정` |
| 승컴 | `final_raw_data_validation.csv` | `origin/main` (`4689c6797`) | **미푸시 대기 (WAITING_PUSH)** | `아직 원격에 없음 — push 감지 즉시 교차검증 예정` |
| 승컴 | `final_statistical_validation.csv` | `origin/main` (`4689c6797`) | **미푸시 대기 (WAITING_PUSH)** | `아직 원격에 없음 — push 감지 즉시 교차검증 예정` |
| 승컴 | `final_robustness_validation.csv` | `origin/main` (`4689c6797`) | **미푸시 대기 (WAITING_PUSH)** | `아직 원격에 없음 — push 감지 즉시 교차검증 예정` |
| 승컴 | `final_m1_resource_validation.md` | `origin/main` (`4689c6797`) | **미푸시 대기 (WAITING_PUSH)** | `아직 원격에 없음 — push 감지 즉시 교차검증 예정` |

> **투명성 원칙:** 미푸시 상태인 고컴·승컴 신규 문서에 대해서는 "검증 완료"로 표시하지 않으며, 본 패키지의 모든 수치는 원시 로그(`result/`) 80/80 직접 재계산과 이미 push된 분석 커밋(`e452a2640`, `4689c6797`, `2a0900382`, `67cf3f901`, `30cf9b9fb`)을 기준으로 독립 확정했습니다. 두 PC의 신규 파일이 push되는 즉시 30분 정기 점검에서 자동 교차검증하여 본 디렉터리를 갱신합니다.
