# 오염 데이터 잔존 검사 결과 (고컴, 2026-11-24)

- 검사기: `python3 -I analysis/final_e1/check_outputs.py [--paper]`
- 판정 방식:
  - 오염 워크로드 라벨이나 무효 run 이름이 **값과 함께** 있으면 HIT이다.
  - 다음은 통과시킨다.
    - 무효 표시가 있는 줄(flagged-ok)
    - 값이 없는 라벨 줄(label-only)
    - 유효 단계 행(valid-phase)
    - 검토를 마친 줄(allowed, `result/final-e1-validation/output_check_allow.txt`)
- 결과 파일:
  - `result/final-e1-validation/output_check_paper.csv` (논문 범위)
  - `output_check.csv` (전체)
  - `output_check_classified.csv` (HIT 분류)

## 1. 논문 범위 (`--paper`): **PASS, HIT 0**

| 파일 | 상태 |
|---|---|
| `PAPER_KCI_DRAFT.md` | flagged-ok 7: 표 3 무효 표시, 한계 7, 사용 금지 문단 |
| `PAPER_EXPERIMENTS_ONLY.md` | flagged-ok 7: 같은 내용 |
| `report/final-e1-validation/tables/table6_valid.md` | flagged-ok 1: 제외 사유 줄 |
| `report/final-e1-validation/tables/RESULTS_ALL.gated.md` (표 A1 원천) | label-only 8: 무효 워크로드 행이 모두 "–" |
| `report/final-e1-validation/figs/paper_fig_numbers.json` | 해당 없음 |

**한계:** 검사기는 라벨과 run 이름만 본다. 라벨 없이 쓴 오염 수치(예: "13종 중 4종", "3.0 %")는 원고를 직접 훑어 확인했다(`manuscript_revision_list.md` §1).

## 2. 저장소 전체: **FAIL, HIT 1,376**. 모두 논문 밖이다

| 분류 | 파일 | HIT | 원인 | 조치 |
|---|---|---|---|---|
| 과거 그림 데이터 | `figs/data/fig7_v4_trace.csv` | 1,181 | 9월 mixR B·C 단계와 mixJ trace 행. 생성 스크립트(`fig7-data.py`)는 이제 검사를 적용하지만, 커밋된 CSV는 예전 것이다 | 덮어쓰지 않음. 이 파일을 읽는 `fig7-plot.py`, `fig7-excel.py`가 행을 걸러낸다. 논문은 이 CSV를 쓰지 않는다 |
| 과거 그림 데이터 | `figs/data/fig14_30s.csv` 외 2개 | 158 | YCSB-A → YCSB-B(mixJ) 행. 생성 스크립트가 저장소에 없다 | 덮어쓰지 않음. 읽는 스크립트가 걸러낸다. 논문은 이 CSV를 쓰지 않는다 |
| 과거 보고서 | `RESULTS_ALL.md` 19, `V4_VS_CAT.md` 6, `WRITEUP_DRAFT.md` 6, `EXPERIMENTS_OVERVIEW.md` 5, `RESULTS_TABLE.md` 1 | 37 | 10월 이전에 만든 표와 초안 | 덮어쓰지 않음. 검사를 적용한 대체본은 `tables/RESULTS_ALL.gated.md`, `tables/V4_VS_CAT.gated.md` |

## 3. 판정

- **논문 원고는 오염 데이터 검사를 통과했다.**
- **그러나 논문 최종본이라고 판정하지 않는다.** 이유는 다음과 같다.
  1. 표 8·그림 10이 비어 있다(E1 재실험 대기). 원래 정책 구성으로는 복원할 수 없다.
  2. 표 A1을 본문에 싣지 않았다. 그림 번호도 불일치한다.
  3. 4.1절 예외 4종의 해석, 표 7 자리, 새 그림 경로는 저자가 결정해야 한다(`manuscript_revision_list.md` §3).
  4. 저장소 전체 검사는 FAIL이다. 과거 산출물을 논문 작성에 인용하면 오염 수치가 다시 들어갈 수 있다. 과거 산출물을 삭제하지 않는 대신, **원고를 고칠 때마다 `check_outputs.py --paper`를 다시 돌려야 한다.**
