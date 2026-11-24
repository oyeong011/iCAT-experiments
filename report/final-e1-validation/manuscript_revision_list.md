# 원고 수정 목록 (고컴, 2026-11-24)

- 대상: `PAPER_KCI_DRAFT.md`, `PAPER_EXPERIMENTS_ONLY.md`(실험 부분 사본). 두 파일을 같은 문장으로 고쳤다.
- 브랜치: `report/data-validity-20261124`. 원래 문장은 git 이력(`ff065d0be` 이전)에 남아 있다.
- 원칙:
  - 수치는 유효성 검사(`analysis/final_e1/validity.py`)를 적용한 재계산값으로만 바꿨다.
  - 재계산 근거가 없는 수치는 바꾸지 않고 "사용 금지" 또는 "재확인 필요"로 표시했다.
- 새 그림과 표는 `report/final-e1-validation/figs`, `tables`에 있다. 기존 `figs/`와 결과 md는 덮어쓰지 않았다.

## 1. 적용한 수정

| # | 위치 | 원래 | 수정 | 근거 (계산값) |
|---|---|---|---|---|
| 1 | 요약(국문·영문) | 1배 길이에서 단일·전환 **전체**에서 iCAT이 기본 파라미터보다 WAF 높음 | 유효 **17종 중 14종** | `tables/sec41_order_check.csv`: Default < iCAT가 성립하지 않는 3종(SQLite 95/5 단독, OLTP → Varmail, YCSB-A → OLTP) |
| 2 | 요약·결론 | 전환 워크로드에서 기본 파라미터보다 **모든 경우** 낮음 | **비교한 3종 모두** 낮음 | 3배 길이 CAT-Default 측정은 유효 3종(F −18.3 %, O −16.5 %, P −4.3 %). 3단계 균등 전환과 YCSB-A → YCSB-B는 무효 |
| 3 | 표 3 | YCSB 전환 6종의 길이 표기 | "결과 무효: YCSB 오류, 제외" / "검증 불가, 제외" / "단계 2·3 결과 무효, 재측정 중" | `result/final-e1-validation/run_validity_ycsb.csv` |
| 4 | 3.2절 끝 | 3배 비교 대상 13종 | 13종 중 YCSB 오류 5종 제외, **8종** 사용 | 같은 파일 |
| 5 | 4.1절 | 1배 단일 9종·전환 14종, **모든 경우** 순서 성립 | 유효 단일 8종·전환 9종 중 **13종** 성립, 예외 4종 명시 | `sec41_order_check.csv`. 예외 4종은 오염과 무관한 원래 데이터다(아래 §3-1) |
| 6 | 4.1절 | 3단계 균등 전환(2.288) 대 CAT-Default(2.410) | 삭제 | mixR 전체 WAF 무효 |
| 7 | 6.2절 그림 7 문단 | 13종 중 4종 우수(1.1~5.3 %), 9종 열세(3.2~11.5 %). 열세 9종은 fio와 YCSB-A 단계 | **8종 중 3종 우수(1.1~5.3 %), 5종 열세(3.2~4.9 %)**. 열세 5종은 fio 단계로만 구성 | `figs/paper_fig_numbers.json` `fig4_v4_vs_robust_pct` |
| 8 | 그림 7 | `figs/fig4_mixes_v4_vs_robust.png` (13종) | `report/final-e1-validation/figs/fig4_mixes_v4_vs_robust.png` (8종) | 검사 적용 후 재생성 |
| 9 | 표 6 | 4행(YCSB-A → YCSB-B 포함) | **3행.** O, F, P 값은 원래와 같다 | `tables/table6_valid.md` |
| 10 | 표 6 뒤 문장 | 4종 모두 1~2위, 나머지 3종 | 3종 모두 1~2위, 나머지 2종 | 표 6 |
| 11 | 그림 8 | 원래 파일 | 유효 6종으로 재생성 | `paper_fig_numbers.json` `fig7_loss_pct` |
| 12 | 견고성 문단 | 평균 CAT-Best 3.0 / v4 6.5 / Robust 7.2 %, 최댓값 v4 15.2 / CAT-Best 17.0(YCSB-A → YCSB-B) / Robust 20.2 %. "v4 최댓값이 CAT-Best보다 작다" | **평균 0.2 / 5.0 / 5.0 %, 최댓값 CAT-Best 1.3 / v4 15.2 / Robust 20.2 %.** CAT-Best가 평균과 최댓값 모두 최소 | `fig8_mean_pct`, `fig8_max_pct` (공통 6종: FIO-Slow → FIO-Fast, OLTP → Varmail, FIO-Fast → Varmail, YCSB-A → OLTP, hot 512 → 128 MB, FIO-Fast → FIO-Slow) |
| 13 | 그림 9 | 원래 파일 | 재생성. 제목을 데이터에서 계산하게 바꿨다(원래 제목 "최댓값은 iCAT-v4가 최소"는 검사 후 틀림) | 같은 JSON |
| 14 | 표 8, 그림 10, 3단계 균등 전환 문단 전체 | 7개 정책 단계별 WAF와 해석 | **"사용 금지" 문단으로 대체** | `tables/table8_status.md`: 11개 run 모두 단계 2·3 무효 |
| 15 | 7장 "개선의 핵심" | 이웃 탐색·부분 초기화가 복귀 시 특히 효과적(6.2절) | 근거가 무효이며 재측정 중 | 3단계 균등 전환 무효 |
| 16 | 8장 한계 1 | 구간 지정 계측 반복 차이 0.1 %(3단계 arm 50: 2.074, 2.073) | 이 근거는 무효이며 재확인 필요 | mixR 전체 WAF 무효 |
| 17 | 8장 한계 2 | 3단계 균등 전환 결과를 참고해 설계 | 그 결과가 이후 무효로 판정되었다는 문구 추가 | — |
| 18 | 8장 한계 3 | 고정 조합 2~6개 | 유효 6종 기준 2~7개 | `fig7_loss_pct` |
| 19 | 8장 한계 7 (신규) | — | YCSB SQLITE_FULL 오염, 제외 범위, mixG 검증 불가, 재측정 중 | `README.md` §1–§2 |
| 20 | 부록 A 표 A1 | RESULTS_ALL.md 4장 | `tables/RESULTS_ALL.gated.md` 1·4장 (오염 5종은 "–") | — |
| 21 | 부록 B | 그림 7–10 경로와 상태 | 새 경로, 그림 10 "사용 금지" | — |

## 2. 수치를 바꾸지 않고 유지한 것 (재확인 결과 유효)

- 표 1·2, 그림 1, 표 4, 그림 2, 표 5, 그림 4·5·6: FIO만 쓰는 단일 워크로드이고 YCSB가 없다.
- 표 6의 O, F, P 행 값(1.859 / 2.352 / 1.127 등): 검사 후 재계산값과 같다.
- 7장 "CAT-Best(arm 47)는 FIO-Fast, YCSB-A, Varmail에서 모두 상위": SQLite 단독 실행 87개(`result/sqlite/*.console.txt`)의 YCSB 실패가 0 %다(`recheck_sqlite_single.csv`). 앞서 "검증 불가"로 적은 것을 정정한다(아래 §4).
- 7장 "Varmail이 포함된 전환 워크로드에서 CAT-Robust보다 낮은 WAF", "OLTP → Varmail에서 측정 고정 조합보다 낮음": 둘 다 유효 데이터다.

## 3. 남은 원고 작업 (고컴이 하지 않음, 저자 판단 필요)

1. **4.1절 예외 4종의 해석:**
   - 오염과 무관하게 원래 데이터에서도 "모든 경우 순서 성립"은 사실이 아니었다(Varmail 단독 iCAT 4.927 > Greedy 4.762, SQLite 95/5 단독 iCAT 1.104 < Default 1.113 등).
   - 고컴은 계산된 사실만 적었다. 해석 문장은 저자가 정한다.
2. **표 A1 본문 삽입:** 원고는 아직 표를 싣지 않고 경로만 가리킨다.
3. **그림 파일 안의 번호:** `figures.py`가 그리는 제목 번호(그림 4, 7, 8)와 원고 번호(그림 7, 8, 9)가 다르다. 원래부터 있던 문제다.
4. **표 7 자리(【결과 대기】: 전환 11종 선별):**
   - 근거 자료(`RESULTS_ALL` §10)에 오염 워크로드(FIO-Fast → YCSB-A, YCSB-A → FIO-Fast, FIO-Slow → FIO-Fast → YCSB-A, YCSB-A → YCSB-B)가 들어 있다.
   - 채울 때 반드시 `validity.py`를 적용해야 한다.
5. **새 그림 경로 정리:** 그림 7·8·9가 `report/final-e1-validation/figs/`를 가리킨다. 투고본을 만들 때 `figs/`로 옮길지 결정이 필요하다. 옮기면 기존 파일을 덮어쓰게 되므로 사용자 승인이 필요하다.
6. **표 8·그림 10:** E1 재실험(300k)은 v4, nodrift, fullreset만 다룬다. 원래 표 8의 정책(CAT-Best, CAT-Robust, arm 17, iCAT, iCAT-v3, CAT-Default)은 재측정 계획에 없다. 원래 형태로는 복원할 수 없으므로 표 설계를 바꿔야 한다.

## 4. 고컴 이전 보고의 정정

- `paper_data_validity_matrix.md`에서 "SQLite 단독 스윕은 검증 불가(원시 YCSB 로그 없음)"라고 썼다. 실제로는 YCSB 출력이 `result/sqlite/*.console.txt` 안에 있었다. 고컴 스캔이 `ycsb-*.txt` 파일 이름만 찾아서 놓쳤다.
- 87개 run 모두 YCSB 실패 0 %다. 판정을 **유효**로 정정한다(매트릭스에도 반영).
