# iCAT 논문 리비전 최종 제출 체크리스트 (`FINAL_DELIVERY_CHECKLIST.md`)

- **작성 시각**: `2026-11-27 09:19 KST`
- **최종 제출 준비 판정**: **CONDITIONAL READY (원시 80/80 검증·고컴 통합 Excel 17시트/15차트·622통계 QA 및 Chart 10 축 수정 완료; 저자 원고 패치 5건 수동 반영 및 승컴 신규 검증 5종 push 대기 남음)**

| # | 점검 항목 | 상태 | 근거 / 비고 |
|---|---|---|---|
| 1 | 전체 핵심 실험 누락 여부 (Random, SmartGC, Ablation, Greedy GC, Drift, Arm 47) | **PASS** | 10개 핵심 캠페인 **80/80 VALID** + 보조 셋 246/246 VALID (누락 0건, RUNNING 0건) |
| 2 | 오염·실패 run 배제 (`SQLITE_FULL`, `mixG`, `ENOSPC`, 10월 이상치) | **PASS** | 260+ 무효 run 100% 제외 확인 |
| 3 | 3대 핵심 주장 최종 판정 (입증 1 / 부분 입증 2 / 반증 명시) | **PASS** | `FINAL_REVIEWER_RESPONSE_MATRIX.xlsx!Core_3_Claims` 완료 |
| 4 | M1~M7 47개 세부 요구사항 전수 매핑 및 원 명칭 유지 | **PASS** | `FINAL_REVIEWER_RESPONSE_MATRIX.xlsx!M1_M7_47_Items` (14 완료 / 17 부분 / 7 실패 / 9 불필요 / 0 필요) |
| 5 | 기존 Figure 1~10 + 신규 Figure 4단계 최종 선정 | **PASS** | `FINAL_FIGURE_CATALOG.md` 완료 (구 그림 10·레거시 fig2·Periodic Switching 사용 금지) |
| 6 | 교차 수치 감사 (Excel · CSV · MD · Figure · 표 6~11 · 본문) | **PASS (수정안 제시)** | `FINAL_PAPER_NUMBER_AUDIT.csv` 19항목 완료 (표 6/7/9b/10/11 100% 일치; 원고 수정 5건 `PAPER_KCI_DRAFT_PATCH_PROPOSAL.md` 작성, 원고 직접 미수정) |
| 7 | `iCAT_Paper_Figures.xlsx` 및 최종 Figure 무결성 검증 | **PASS** | 21시트, 40/40 수치 일치, 0 오류 리터럴, 300 DPI PNG/PDF/SVG, `figs/` 0건 수정 |
| 8 | `FINAL_EXPERIMENT_REPORT.md` 12개 장 완비 | **PASS** | 1장~12장 전수 작성, 모든 수치 원시 로그 출처 연결 |
| 9 | 고컴 신규 통합 5종 파일 수신·교차검증 (`iCAT_Complete_Experiment_Results.xlsx` 등) | **PASS (Chart 10 수정본 제공)** | `origin/report/data-validity-20261124 @ 3fdb21258`: 17시트·78 mixFYF·2 M1·33대비·622통계 0불일치; 실제 Excel 육안 QA에서 `그림 10` 로그축 `crossesAt=1.0` 버그(`NA-18`) 발견 → `iCAT_Complete_Experiment_Results_Chart10Fixed.xlsx` (`CELL_DIFFS=0`)로 수정·재검증 완료 (`EXCEL_17SHEET_15CHART_QA.md`) |
| 10 | 승컴 신규 검증 5종 파일 수신·교차검증 (`final_independent_validation.md` 등) | **WAITING_PUSH (0/5, 미검증)** | `origin/main @ 4689c6797` 기준 미수신 (단, 승컴 기 push `batchG`·`arm47`·`secondary-metrics` 79/79 통계는 삼중 교차검증 0불일치 완료) |
| 11 | 투고 전 원고(`PAPER_KCI_DRAFT.md`) 최종 수동 반영 (NA-09~NA-13) | **ACTION REQUIRED (저자 반영)** | L405 GC 계측 오기, L297–307 미실행 300k 표 8·그림 10, 5건 `【결과 대기】` 태그, L262 그림 9 소수 2자리, 표 9 `WAF_nand` 각주 (`PAPER_KCI_DRAFT_PATCH_PROPOSAL.md`) |

## 최종 전달 산출물 경로 (`report/final-revision/delivery/`)
1. `report/final-revision/delivery/iCAT_Complete_Experiment_Results_Chart10Fixed.xlsx` (고컴 17시트·15차트 통합 Excel — `그림 10` 로그축 수정·실제 Excel 재검증 완료, 셀 값 100% 동일)
2. `report/final-revision/delivery/EXCEL_17SHEET_15CHART_QA.md` (17시트·15차트 OOXML+실제 Excel 육안 QA·622통계 대조·부정결과 누락 점검 보고서)
3. `report/final-revision/delivery/FINAL_EXPERIMENT_REPORT.md`
4. `report/final-revision/delivery/FINAL_REVIEWER_RESPONSE_MATRIX.xlsx`
5. `report/final-revision/delivery/FINAL_FIGURE_CATALOG.md`
6. `report/final-revision/delivery/FINAL_EXPERIMENT_STATUS.md`
7. `report/final-revision/delivery/FINAL_PAPER_NUMBER_AUDIT.csv`
8. `report/final-revision/delivery/FINAL_LIMITATIONS.md`
9. `report/final-revision/delivery/PAPER_KCI_DRAFT_PATCH_PROPOSAL.md`
10. `report/final-revision/delivery/FINAL_DELIVERY_CHECKLIST.md`
