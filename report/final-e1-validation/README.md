# E1 재실험 대비 데이터 유효성 검증 (고컴)

- 작성: 2026-11-24 12시대, 고컴. 원시 파일과 스크립트만 썼다. NVMeVirt 실험은 하지 않았고 승컴 작업에도 접근하지 않았다.
- 기준 자료:
  - 승컴 `result/revision-20261123/mixR/INVALID-20261124.txt` (64c5459ed)
  - 고컴이 YCSB 원시 출력 2,012개 파일을 직접 다시 검사한 결과
- 판정 규칙(`analysis/final_e1/validity.py`):
  - YCSB 연산 중 하나라도 실패가 1 %를 넘으면 그 YCSB 단계는 무효다. 그 뒤의 모든 단계도 무효다. 장치 상태가 이미 달라졌기 때문이다.
  - 실패 YCSB 단계보다 **앞선** 단계는 유효하다.
  - INVALID 파일에 오른 단계, exit code ≠ 0, `SUSPECT.txt`가 있는 run도 제외한다.

## 1. 오염의 실체 (측정값, 원시 로그)

| 형태 | 해당 run (예) | YCSB 결과 | 처리량 |
|---|---|---|---|
| READ 실패 | 11-23 v4 rep1·rep2, fullreset rep1, nodrift rep2, 9월 v4 rep1 | READ 21.0 M 중 성공 약 35 k (**실패 99.83 %**). UPDATE는 성공 | 약 12.9–14.7 k ops/s |
| UPDATE 실패 | 11-23 nodrift rep1, 9월 v4 rep2 | READ 100 % 성공, UPDATE **9.98 % 실패** | 약 8.7–8.9 k ops/s |

- 두 형태 모두 첫 오류는 `SQLITE_FULL`("database or disk is full")이다. 이후 `statement is not executing`이 이어진다.
- 무효 run 262개(11-24 12시 병합 기준) 가운데 226개에서 `SQLITE_FULL`을 확인했다. 나머지 36개는 다음과 같다.
  - mixG 34개: YCSB 출력이 비어 있다.
  - exit≠0 run 1개
  - 11-23 nodrift smoke 1개: 승컴 INVALID 파일의 "이 디렉터리의 모든 mixR run"에 해당한다. YCSB 실패는 0 %다.
- 승컴이 밝힌 원인: 6 GiB `test.dat`를 남긴 채 600k-record DB와 WAL(약 0.94 GB)을 넣을 공간이 없었다.
  - 고컴은 이 원인을 따로 재현하지 않았다. 다만 오류 코드는 원인 설명과 맞는다.
- **러너는 이런 run에도 exit=0을 기록했다.**
- **고컴 자체 정정:** 고컴이 앞서 "YCSB 속도가 빠른 무리와 느린 무리로 나뉘고 원인은 미확인"이라고 쓴 현상이 바로 이 두 오염 형태였다(`e1_independent_check.md` §6.3).

## 2. 영향 범위 (`result/final-e1-validation/run_validity_ycsb.csv`, YCSB 단계가 있는 run 364개)

| 결과 묶음 | 부하 | 유효 | 무효 | 검증 불가 | 유효하게 남는 단계 |
|---|---|---|---|---|---|
| mix-20260911 (9월) | **mixR**×3 | 0 | 11 | — | A (FIO) |
| | **mixA** 1배/×3/×6 | 0 | 91 (+exit≠0 2) | — | A (FIO) |
| | **mixB** | 0 | 37 | — | 없음 (YCSB가 A) |
| | **mixH** | 0 | 35 | — | A, B (FIO) |
| | **mixJ** | 0 | 41 (+exit≠0 1) | — | 없음 |
| | **mixG** | 0 | — | 34 | 없음 (YCSB 출력 파일이 0바이트라 검증할 수 없다) |
| | long-fixed47, long-online | 0 | 2 | — | — |
| | mixP, mixT, main-*, t4 | 52 | 0 | — | 전부 |
| revision-20261123 (11-23 E1) | mixR×3 (+smoke) | 0 | 5 + smoke 1 (INVALID 파일과 일치) | — | A |
| inherit-20261006 | mixV, mixW2 | 6 | 2 | — | — |
| **고컴 revA / revB** (mixFYF) | | **25** | 0 | — | 전부. 고컴 Random/V4, 제거·정착 결과는 영향이 없다 |
| mixT 10시간, v6-mixT, screen | | 6 | 0 | — | 전부 |

- 실패율은 8.2–99.8 %다. 1 % 기준의 경계에 걸린 run은 없다(`result/final-e1-validation/ycsb_validity_all.csv`).
- 무효는 9월 12일부터 11월 24일 사이 run이다. 대부분이 9월 실행이다(병합 전 집계로 218/260).
- 고컴이 찾은 무효 단계 목록은 `result/final-e1-validation/gocom_detected_invalid.txt`다. 형식은 `<run> <무효 단계>`다.
  - 승컴 INVALID 파일은 11-23 mixR만 다룬다. **9월 mixA·B·H·J·R과 mixG도 같은 기준으로 무효 표시가 필요하다.** 승컴에 전달할 것.

## 3. 그림·표 스크립트 조사 (figures.py, v4-vs-cat.py, fig7-data.py)

| 스크립트 | 오염 자료 참조 | 조치 |
|---|---|---|
| `analysis/figures.py` | 그림 5: `mixR-{fixed47, fixed50×2, online, onlinev3, onlinev4×2}-rep*-x3`의 단계 A/B/C와 전체 WAF. 그림 4·7: `mix{A,B,G,H,J}-*-x3` 전체 WAF | `tot()`는 모든 단계가 유효한 run만 반환한다. `phases()`는 유효 단계만 반환한다. `curve()`는 무효 run이면 중단한다. 그림 5는 유효 단계만 그리고, 빠진 단계가 있으면 제목을 "[논문 사용 불가]"로 바꾼다 |
| `analysis/v4-vs-cat.py` | §2 전환 13종 중 mixA, B, G, H, J. §3 ×6 mixA. §4 3구간(mixR) 전부. §5 요약 문장은 10-01에 고정된 오염 수치(3구간 −13.7 %, 견고 CAT 4/13 등) | `tot()`에 유효성 검사를 넣었다. 해당 칸은 "–"가 된다. §5 앞에 경고 문단을 넣었다 |
| `analysis/fig7-data.py` | `mixR-onlinev4-rep1-x3`(B·C 단계 trace와 reset 사건), `mixJ-onlinev4-rep1-x3` 전체 | 유효 단계의 행만 쓴다. mixJ는 건너뛴다 |

**검사 방법:** 원본 스크립트는 `/home/oy/iCAT/figs`, `/home/oy/iCAT/V4_VS_CAT.md`에 바로 쓴다. 그래서 경로만 바꾼 사본을 scratchpad에서 실행했다. 기존 그림과 표는 덮어쓰지 않았다.

| 검사 | 수정 전 | 수정 후 |
|---|---|---|
| V4_VS_CAT §4 (mixR) | v4 2.079(n=2)와 비교 대상 8행(2.024–3.164) | 모두 "–" |
| V4_VS_CAT §2 | 13종 중 5종(mixA, B, G, H, J)에 값 | 이 5종은 "–" |
| fig7 trace 행 수 | mixR 1,478행, mixJ 143행 | mixR 440행(A 단계만), mixJ 0행 |
| figures.py | 그림 10개 | 그림 10개 생성(오류 없음). 그림 5는 1구간만 남고 "[논문 사용 불가]" 표시 |

**이 세 스크립트 밖에서 논문 수치에 영향이 있는 곳 (수정은 하지 않았다. 확인 필요):**
- `figs/data/fig14_lines_YCSB-A-to-YCSB-B.csv`, `fig6_lines_YCSB-A-to-YCSB-B.csv`: mixJ다. 무효다.
- `analysis/all-tables.py` §7(mixR)과 mixA 1배 arm 스윕(`MA`): 무효다.
- 승컴 `report/revision-20261123/random_selection_audit.md`와 고컴 `verify_R1_random_fixed.csv`의 mixA 기댓값: 무효다. mixC는 FIO만 있어서 유효하다.
- 승컴 `report/revision-20261123/recovery.csv`, `exploration_counts.csv`의 mixR·mixA 행.

## 4. 유효한 단계만 따로 분류

- `result/final-e1-validation/phase_prefix_valid.csv`: 전체로는 무효인 run에서 YCSB 실패 **앞의** 단계만 모았다. 180행이다.
  - mixA 단계 A 91개
  - mixH 단계 A·B 각 35개
  - mixR 단계 A 17개
  - 기타 2개
- `result/final-e1-validation/e1_phaseA.csv`: E1 정책(v4, nodrift, fullreset)의 mixR 단계 A다.
  - 11-23 배치 v4는 1.9027과 1.8961, nodrift는 1.9040과 1.9055, fullreset은 1.8948이다.
  - 단계 A는 정책 사이에 차이가 거의 없다. 단계 A에서는 reset이 없고, 세 모듈의 동작은 drift 조건 외에는 같다.

## 5. 재실험 결과 자동 검증 준비 상태

**재실험 사양 (승컴 `script/revision-rerun-20261124.sh`):**
- 경로는 `result/revision-20261124/mixR`이다. 사전 검증 run은 `result/revision-20261124/validation`이다.
- 검증이 통과해야 시작한다. 첫 실패에서 큐를 멈춘다.
- 순서는 rep 1..3 × (v4, nodrift, fullreset)이다.
- **YCSB 적재가 300,000 records다.** 이전은 600,000이었다.
  - 그래서 재실험의 B·C 단계는 9월이나 11-23 run과 **부하가 다르다.** 비교는 재실험 배치 안에서만 한다.
  - 단계 A(FIO)는 같은 부하다.
- 런너 변경(7dd5e9d9a): 적재 전에 남은 공간을 검사한다(record당 2 KB).

**자동 검증 (`python3 -I analysis/final_e1/e1_analyze.py`, 약 20초):**

| 요구 항목 | 출력 |
|---|---|
| 실행별 유효성 (exit, INVALID 목록, YCSB 실패율, 모듈, seed, 두 경로 WAF 일치) | `e1_runs.csv`, `e1_status.md` |
| 정책별 평균·SD·95 % CI (유효 값만, 배치별) | `e1_stats.csv` |
| v4 대비 Welch 95 % CI | `e1_stats.csv`의 `welch_*` 열. `claim_allowed=yes`는 양쪽 n ≥ 3이고 CI가 0을 포함하지 않을 때만이다 |
| 두 번째 FIO 단계(C) WAF | `e1_runs.csv` `waf_C`, `e1_stats.csv` `metric=waf_C` |
| 시간별 WAF | `e1_timeseries.csv` (5분 구간, 단계별) |
| 재탐색 횟수와 시점 | `e1_resets.csv` (이 run의 dmesg만 읽는다. 단계, 단계 시작 뒤 초) |
| YCSB 성공률과 처리량 | `e1_runs.csv` `ycsb_*` (적재 수, 연산별 성공 %, ops/s) |

- 모든 출력 경로는 `result/final-e1-validation/`이고, 요약은 `report/final-e1-validation/e1_status.md`다.
- 이미 있는 run 7개로 시험했다.
  - 오염된 B·C 단계와 전체 WAF는 모두 "제외"로 나온다.
  - 통계에는 단계 A만 들어간다.
- 고컴은 감시 작업으로 `result/revision-20261124/`에 새 run이 push되면 바로 분석을 돌린다.

## 6. 고컴 기존 문서에 대한 영향

- `report/revision-20261123-gocom/e1_independent_check.md` §2–§8:
  - **B·C 단계, 전체 WAF, C 단계 reset, 회복 시간, 정책 비교가 모두 무효다.**
  - 유효한 것은 모듈·seed·실행 겹침 검사와 단계 A WAF뿐이다.
  - 원문은 두고 무효 고지를 덧붙였다.
- `revision_evidence_check.md`의 mixA Random 기댓값, `duplication_check_E1_E2.md`의 mixR YCSB 수치에도 무효 고지를 덧붙였다.
- 고컴 revA·revB(mixFYF), mixY(v7, SmartGC, CAT-47), E0 결과는 유효하다.
  - mixFYF의 YCSB는 실패 0 %다.
  - mixY에는 YCSB가 없다.

## 7. 추가 점검 (11-24 오후, 브랜치 `report/data-validity-20261124`)

- 논문 전체 매트릭스: `paper_data_validity_matrix.md`
- 추가로 검사를 넣은 스크립트:
  - `all-tables.py`
  - `fig6-workloads.py`, `fig-four.py`
  - `fig14-excel.py`, `fig6-workloads-excel.py`
  - `fig7-plot.py`, `fig7-excel.py`
- 산출물 차단 검사: `analysis/final_e1/check_outputs.py`. 현재 FAIL이며, 원고와 커밋된 옛 산출물에 오염 값이 있다.
- 원시 재확인: `analysis/final_e1/recheck_valid_sets.py`
  - 고컴 mixFYF 25 run: YCSB 실패 0 %, 효과 수치 재현.
  - SmartGC 비교 16 run: YCSB 없음, 모두 완료. 원래 SmartGC 실행은 호스트 디스크가 가득 차서 실패했다.
- E1 재실험의 300k와 600k 분리: 배치 라벨에 실제 적재 레코드 수를 넣었다. 한 배치에 다른 레코드 수가 섞이면 통계를 내지 않고 중단한다.

## 8. 최종 산출물 색인 (11-24 오후 2차)

| 요구 | 파일 |
|---|---|
| 1. 수정된 논문용 그림 | `figs/fig4_mixes_v4_vs_robust.*`(그림 7), `figs/fig7_mix_loss_by_workload.*`(그림 8), `figs/fig8_robustness.*`(그림 9), 수치는 `figs/paper_fig_numbers.json`. 나머지 그림은 같은 실행에서 재생성했고 값은 원래와 같다. `fig5_three_phase_mix`는 "[논문 사용 불가]" |
| 2. 수정된 논문용 표 | `tables/table6_valid.{md,csv}`, `tables/table8_status.md`(사용 금지), `tables/RESULTS_ALL.gated.md`(표 A1 원천), `tables/V4_VS_CAT.gated.md`, `tables/sec41_order_check.csv` |
| 3. 원고 수정 목록 | `manuscript_revision_list.md` (적용 21건, 남은 저자 판단 6건) |
| 4. 오염 데이터 잔존 검사 | `residual_check.md`. 논문 범위 PASS(0), 저장소 전체 FAIL(1,376, 모두 논문 밖) |
| 5. 유효 / 사용 불가 주장 | `claims_and_pending.md` §1·§2 |
| 6. E1 미완료 실험 | `claims_and_pending.md` §3 |
| 생성 스크립트 | `analysis/final_e1/paper_tables.py`, `check_outputs.py`(`--paper`), `classify_hits.py`. 그림은 `analysis/figures.py`(검사 적용, 제목을 데이터에서 계산) |
