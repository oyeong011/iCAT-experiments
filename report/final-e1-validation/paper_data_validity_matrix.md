# 논문 전체 실험별 데이터 유효성 매트릭스 (고컴)

- 작성: 2026-11-24, 고컴. 브랜치는 `report/data-validity-20261124`다(`report/final-20261123`에서 분기).
- 새 실험은 하지 않았다. 기존 결과 파일은 바꾸지 않았다.
- 대상: `PAPER_KCI_DRAFT.md`(= `PAPER_EXPERIMENTS_ONLY.md`)의 표와 그림, 그리고 Revision 대응에 쓰는 실험.
- 판정 근거: `analysis/final_e1/validity.py`
  - YCSB 실패율이 1 %를 넘으면 그 단계와 그 뒤 단계가 무효다.
  - exit code, `SUSPECT.txt`, 승컴 INVALID 파일도 반영한다.
- 원시 재검사: `result/final-e1-validation/{ycsb_validity_all, run_validity_ycsb, recheck_gocom_mixfyf, recheck_gocom_effects, recheck_smartgc_runs}.csv`
- 상태 범례:
  - **유효:** 원시 로그로 확인했다.
  - **무효:** YCSB 오염 또는 실행 실패다.
  - **일부 유효:** 앞 단계만 유효하다.
  - **검증 불가:** 원시 로그가 없다.
  - **대기:** 재실험 결과를 기다린다.

## 1. 논문 본문 표·그림

| 논문 항목 | 실험 / 원시 자료 | YCSB 사용 | 실행 성공 | 데이터 상태 | 생성 스크립트 (검사 적용) | 조치 |
|---|---|---|---|---|---|---|
| 표 1·2·3 (정책, 워크로드 정의) | — | 표 3에 YCSB 전환 6종 | — | 정의표 자체는 데이터가 아니다 | 수작업 | 표 3에서 무효 워크로드 6종(FIO-Fast → YCSB-A, YCSB-A → FIO-Fast, YCSB-A → YCSB-B, FIO-Slow → FIO-Fast → YCSB-A, FIO-Fast ∥ YCSB-A, 3단계 균등 전환)을 빼거나 "재측정"으로 표시 |
| 그림 1 (60 조합 민감도, FIO-Fast) | `sweep-20260915/rank-test4.txt` | 아니오 | 60/60 | **유효** (YCSB 없음) | `figures.py` fig1 | 없음 |
| 표 4, 그림 2 (탐색 비용, FIO-Fast 3 h) | `mix-20260911/t4-*` | 아니오 | 정상 | **유효** | `figures.py` fig3 | 없음 |
| 표 5, 그림 4·5 (단일 워크로드, 10 h) | `t4-onlinev4-rep1-x60` 등 | 아니오 | 정상 | **유효** | `figures.py` fig9·fig10, `v4-vs-cat.py` §1 | 없음 |
| 그림 6 (iCAT-v3 구성 요소 제거) | `t4-onlinev3*-rep1-x18` | 아니오 | 정상 | **유효** (각 n=1) | `figures.py` fig6 | n=1 표기 유지 |
| **그림 7** (전환 13종, v4 대 CAT-Robust) | `mix{A..Q}-onlinev4/fixed50-*-x3` | 6종이 YCSB | 정상 종료(exit 0)이나 YCSB 실패 | **일부 유효: 13종 중 8종 유효.** A, B, G(검증 불가), H, J 무효 | `figures.py` fig4 (검사 적용) | 본문 "4종 우수, 9종 열세"는 **유효 8종에서 3종 우수(−1.1 ~ −5.3 %), 5종 열세(+3.2 ~ +4.9 %)**로 바뀐다(계산값) |
| **표 6** (4종 × 고정 조합 6개) | `mix{O,F,J,P}-*-x3` | J, P가 YCSB | J 실패 | **J(YCSB-A → YCSB-B) 행 무효.** O, F, P 유효(P는 YCSB 실패 0 %) | 수작업 + `all-tables.py` | J 행을 빼야 한다. "4종 모두 1~2위" 문장을 수정 |
| **그림 8** (최상위 대비 손실) | 같은 묶음 | 일부 | — | 11종 중 유효 6종(C, D, F, K, O, P) | `figures.py` fig7 (검사 적용) | 재생성 |
| **그림 9** (견고성 6종) | 같은 묶음 | 일부 | — | 원래 집합에 무효 워크로드가 포함될 수 있다. 검사 후 공통 집합은 C, D, F, K, O, P | `figures.py` fig8 (검사 적용) | 재생성 후 평균·최댓값 문장 수정 |
| **표 8, 그림 10** (3단계 균등 전환, mixR) | 9월 `mixR-*-x3` 11개 | 단계 2 | YCSB READ 99.83 % 또는 UPDATE 9.98 % 실패, exit 0 | **단계 1(FIO)만 유효. 단계 2·3과 전체 WAF 무효** | `figures.py` fig5 ("[논문 사용 불가]" 표시), `v4-vs-cat.py` §4 | 표 8과 그림 10을 빼거나 재실험(300k, n=3)으로 교체. "단계 2에서 학습기가 우수, 단계 3 복귀" 문장 삭제 |
| 그림 6 (fig6_workload_waf) / fig14 (4개 응용 전환, 30초 WAF) | `mix{O,F,J,P}-*-rep1-x3` | J, P | J 실패 | **YCSB-A → YCSB-B 패널 무효.** 나머지 3개 유효 | `fig6-workloads.py`, `fig-four.py` (J 패널 자동 제외), `fig14-excel.py`, `fig6-workloads-excel.py` (J 행 제외) | 재생성. `figs/data/fig14_*.csv`, `fig6_lines_YCSB-A-to-YCSB-B.csv`는 오염 데이터 그대로 커밋돼 있다(덮어쓰지 않음) |
| 그림 7 trace (`fig7_v4_trace.csv`, v4 선택 과정) | O, F, J, P, mixR, 10 h | mixR, J | — | mixR은 A 단계만 유효, J는 무효 | `fig7-data.py`, `fig7-plot.py`, `fig7-excel.py` (검사 적용) | 재생성 |
| 표 A1 (1배 14종) | `mix*-rep{1,2,3}` 1배 | 6종 | — | A, B, G, H, J 무효(G는 검증 불가). 나머지 유효 | `all-tables.py` §4 (검사 적용, "–") | 표 A1 재생성 |
| 순위 표 "빠른 3영역 → SQLite", "SQLite 단일" (RESULTS_ALL §3) | `mixA-arm*-rep1`, `sweep-20260915/rank-sqlite-a.txt` | 예 | mixA 실패 | mixA **무효.** SQLite 단독 스윕은 ~~검증 불가~~ → **유효** (11-24 정정: YCSB 출력이 `result/sqlite/*.console.txt` 안에 있었고 87개 run 모두 실패 0 %, `recheck_sqlite_single.csv`) | `all-tables.py` §3 (mixA 열 "무효") | 논문에 쓰지 않는다 |

## 2. Revision 대응 실험

| 항목 | 원시 자료 | YCSB | 실행 성공 | 데이터 상태 | 재확인 결과 (원시 로그) |
|---|---|---|---|---|---|
| **Random 대 V4** | 고컴 `revA-20261114/raw/mixFYF-revA-{random,v4}-rep{1,2,3}` | 예 (단계 B, 250k records) | 25/25 exit 0, 모든 단계에 종료 표시, fio error 0 | **유효.** YCSB 실패 0.000 %(READ와 UPDATE 모두) | Random − V4 = **+0.1959 [+0.1840, +0.2078]** (Welch, n=3:3). 앞서 보고한 값과 같다 |
| **Ablation: 후보 제거** | `revB-*/mixFYF-revB-noelim-*`, revA-V2 | 예 | 정상 | **유효** | noelim − V4 = **+0.0942 [+0.0714, +0.1169]**, V2 − V4 = +0.1355 [+0.1164, +0.1545] |
| Ablation: 정착 | `mixFYF-revB-nosettle-*` | 예 | 정상 | **유효** (데이터). 효과는 미입증 | nosettle − V4 = +0.0868 [−0.1099, +0.2835] |
| Ablation: drift (revA-V1) | `mixFYF-revA-v1-*` | 예 | 정상 | **유효** (데이터). 효과는 미입증 | V1 − V4 = +0.0787 [−0.0523, +0.2096] |
| arm60 | `mixFYF-revB-arm60-rep1` | 예 | 정상 | **유효**, n=1 | — |
| 각 run의 YCSB 연산 수 | 같은 25 run | — | — | 본 run 143.6–150.9 M 연산(1800 s 시간 기준). smoke120 4개는 7.0–8.6 M | 적재 250,000/250,000 |
| **SmartGC 비교 (mixY)** | 승컴 `smartgc-20261119/resume/mixY-{smartgc,onlinev4}-rep1`, `gc-20261010/mixY-{smartgc-eq8, sg-arm47}-rep1`. 고컴 `gocom-sg-20261119/mixY-*` | **아니오** (FIO와 Varmail만 있고 YCSB 출력이 0바이트) | 16/16 exit 0, 모든 단계 완료(fio json, filebench IO Summary) | **유효** (n=1씩) | WAF 두 경로가 일치한다. GC 버퍼가 있는 빌드는 NAND 식 host − absorbed + evicted + gc가 일치한다 |
| SmartGC 원래 실행 | `gc-20261010/mixY-smartgc-rep1` | 아니오 | **실패**: `exit-code.txt`가 비어 있고 summary 없음. 큐 로그에 호스트 디스크 `No space left on device` | **무효** (사용하지 않음) | 비교에는 처음부터 다시 실행한 `resume/mixY-smartgc-rep1`(11-22 시작, S01 카운터 0부터)을 쓴다 |
| SmartGC 지연 비교 | 같은 run | 아니오 | — | 데이터는 유효. channel_model 경고 구간에서는 SmartGC 지연이 과소 계산된다 | 기존 `chmodel_warning_impact.csv` 주의 사항 유지 |
| CAT-47 기준선 (mixY 10월/11월) | `gc-20261010/mixY-fixed47-rep1`, E0 | 아니오 | 정상 | 유효 (10-10 run은 이상치로 처리) | `cat47_baseline_audit.md` §5 |
| 자원 오버헤드 (CPU, 메모리) | revA resource, 승컴 resource-v124 (FIO-Fast) | 아니오 | 정상 | **유효** | — |
| v7 워크로드 변화 반응 (mixY) | `v7-20261011-icat2/mixY` | 아니오 | 정상 | **유효** (n=1) | — |
| 승컴 Random 고정 기댓값 | `mixA-arm*`, `mixC-arm*` 1배 | mixA 예 | mixA 실패 | **mixA 무효, mixC 유효** | 승컴 `random_selection_audit.md` §2와 고컴 `verify_R1_random_fixed.csv`의 mixA 행은 쓰지 않는다 |
| **E1 (변화 감지, 재탐색 범위)** | 11-23 `revision-20261123/mixR` | 예 (600k) | YCSB 실패 | **무효** (A 단계만 유효) | `e1_independent_check.md` §9 |
| E1 재실험 | `revision-20261124/mixR` | 예 (**300k**) | — | **대기** | `e1_analyze.py`가 자동 분석한다. 300k와 600k는 배치 라벨(`…/rec300k`, `…/rec600k`)로 분리되고, 한 배치에 두 값이 섞이면 중단한다 |

## 3. 차단 장치

1. **데이터 접근 단계** (스크립트 안에서 `validity.py` 호출):
   - `figures.py`, `v4-vs-cat.py`, `fig7-data.py`, `all-tables.py`, `fig6-workloads.py`, `fig-four.py`: run 디렉터리 단위로 검사한다.
   - `fig14-excel.py`, `fig6-workloads-excel.py`, `fig7-plot.py`, `fig7-excel.py`: 커밋된 데이터 CSV를 워크로드 라벨과 단계로 걸러낸다.
   - 경로를 바꾼 사본을 scratchpad에서 실행해 확인했다. `/home/oy/iCAT`의 figs와 md는 덮어쓰지 않았다.
   - 엑셀 스크립트 두 개는 고컴에 openpyxl이 없어 실행하지 못했다. 필터만 따로 시험했다(fig14_30s 897행 → 744행, YCSB-A → YCSB-B 제거).
2. **산출물 단계** `python3 -I analysis/final_e1/check_outputs.py`:
   - 논문 초안, 결과 md, `figs/data/*.csv`·`*.xlsx`, final 보고서를 검사한다.
   - 오염 라벨이나 무효 run 이름이 값과 함께 있으면 **HIT**이고, 종료 코드는 1이다.
   - 무효 표시가 있는 줄, 값 없는 라벨 줄, 유효 단계 행, 검토를 마친 허용 줄(`output_check_allow.txt`)은 통과시킨다.
   - **PDF를 만들기 전에 이 검사가 PASS여야 한다.**
3. **현재 상태 (11-24 14:30):** FAIL, HIT 1,382건 (값 없는 라벨 줄을 label-only로 분류한 뒤 기준).
   - 논문 초안 8건과 같은 내용의 `PAPER_EXPERIMENTS_ONLY.md` 8건
   - RESULTS_ALL 22건, V4_VS_CAT 7건 등
   - 커밋된 fig14와 fig7 데이터 CSV
   - 재생성한 RESULTS_ALL(scratchpad)은 **PASS**(HIT 0)다. 즉 스크립트로 다시 만들면 오염 값은 빠진다.
   - 남은 HIT은 원고 문장과 커밋된 옛 산출물이다. 사람이 고쳐야 한다.

## 4. 제출 전 필수 수정 (원고)

1. 그림 7 본문 수치: 4/13 → 3/8 우수(유효 워크로드만).
2. 표 6: YCSB-A → YCSB-B 행 삭제. "4종 모두 1~2위" 수정.
3. 표 8, 그림 10(3단계 균등 전환): 삭제하거나 300k 재실험(n=3)으로 교체. 단계 2·3 관련 서술 삭제.
4. 그림 8·9: 검사를 적용해 재생성하고 견고성 수치 문장을 수정.
5. 표 3: 무효 워크로드 6종의 처리(삭제 또는 재측정 표시).
6. 표 A1: 재생성.
7. 그림 6/fig14: YCSB-A → YCSB-B 패널 제거 후 재생성.
8. V4_VS_CAT §5 고정 요약 문장 재작성.
9. 재생성 후 `check_outputs.py`가 PASS인지 확인.

## 5. 갱신 (11-24 오후 2차)

- 원고 수정을 반영했다(`manuscript_revision_list.md`).
  - 그림 7·8·9는 `report/final-e1-validation/figs/`에서 재생성했다.
  - 표 6은 3행으로 줄였다.
  - 표 8·그림 10은 "사용 금지" 문단으로 바꿨다.
- 논문 범위 검사(`check_outputs.py --paper`): **PASS**(HIT 0).
- 저장소 전체 검사: FAIL(HIT 1,376). 모두 논문에 들어가지 않는 과거 산출물이다(`residual_check.md`).
