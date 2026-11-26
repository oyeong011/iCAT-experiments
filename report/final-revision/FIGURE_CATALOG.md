# 그래프 목록 (고컴, 2026-11-27)

- 모든 그래프는 `iCAT_Complete_Experiment_Results.xlsx` 안의 Excel 기본 차트로, 편집할 수 있다.
  - 차트는 같은 시트의 "[그래프 데이터]" 표 범위를 참조한다. 표를 고치면 그래프도 바뀐다.
  - 같은 값이 `report/final-revision/complete-results/<CSV>`에도 있다.
- 공통 규칙
  - WAF는 낮을수록 좋다. 이 문구를 축 제목에 적었다.
  - n=3이면 평균 ± 95 % CI를 그렸다. t 분포, df = 2다.
  - n=1이면 "단일 실행"으로 표시하고 오차 막대를 그리지 않았다.
  - 다른 배치끼리의 간접 비교는 별도 계열 색과 "(간접)" 라벨로 구분했다.
  - 호스트와 배치는 라벨에 적었다.
- 색: dataviz 기준 팔레트를 고정 순서로 썼다 (#2A78D6, #EB6834, #1BAF7A, #EDA100, …).
- `check_complete_xlsx.py` 검사 결과는 PASS다.
  - 차트 참조 86개의 캐시 값이 셀 값과 같다.
  - 차트 CSV의 수치 621개가 모두 Excel 안에 있다.
- **미확인**: 이 PC에는 Excel이나 LibreOffice가 없어서 파일을 열어 화면으로 보지는 못했다. OOXML 구조와 수치만 검사했다.

| # | 시트 | 그래프 | 형태 | 자료 (CSV) | n | 값 종류 |
|---|---|---|---|---|---|---|
| 1 | Executive Summary | 정책별 전체 WAF (28개 그룹, 고컴과 승컴을 다른 색으로) | 막대 + 95 % CI | `chart01_policy_total_waf.csv` | 3 (n=1 표시 3개) | 실측 (원시 카운터 재계산) |
| 2 | Executive Summary | 단계 A/B/C WAF | 묶음 막대 + CI | `chart02_phase_waf.csv` | 3 / 1 | 실측 |
| 3 | Random Selection | Random vs iCAT-v4, 단계별 | 묶음 막대 + CI | `chart03_random_vs_icat.csv` | 3 | 실측, 고컴 revA |
| 4 | Ablation Study | 구성 요소 제거 Δ (같은 배치 V4 대비) | 막대 Δ + Welch CI | `chart04_ablation_delta.csv` | 3 (revB 제외) | 실측 Δ |
| 5 | Online Greedy | revD-v4, abl-v4, Greedy (승컴, 간접), revC-v4, 원래 iCAT (고컴, 같은 배치) | 막대 + CI | `chart05_online_greedy.csv` | 3 | 실측 |
| 6 | Greedy GC | Greedy GC vs iCAT-v4, 단계별 | 묶음 막대 + CI | `chart06_greedygc.csv` | 3 | 실측, 승컴 batchG |
| 7a | Workload Adaptation | 5분 창 WAF 시간 변화 (V4, Random, V1, V2) | 산점선 | `chart07_waf_timeseries_revA.csv` (SD 열 포함) | 3 (창별 평균) | 실측, control-series 30 s |
| 7b | Workload Adaptation | mixY 20단계 단계별 WAF (로그 축) | 선 | `chart07b_mixY_phase_waf.csv` | 1 | 실측, 승컴 |
| 8 | Drift Threshold | 감지 12.5 %, 50 %, 끔 − 같은 배치 25 % | 막대 Δ + CI | `chart08_drift_delta.csv` | 3 | 실측 Δ. 15 %는 측정하지 않음 |
| 참고 | SmartGC Comparison | mixY 정책별 WAF (호스트·빌드별) | 막대 | `chart_smartgc_waf.csv` | 1 | 실측 |
| 9 | Memory Overhead | 학습 자료구조(계산), vmalloc 합계(계산), VmallocUsed 증가(실측) | 묶음 막대, 로그 축 | `chart09_memory.csv` | 1 | 계산과 실측을 항목 이름에 구분 |
| 10 | CPU and Timing | GC 1회당 GC 전체, SELECT, LEARN, REWARD | 묶음 막대, 로그 축 | `chart10_timing.csv` | 1 | ktime 경과 시간 (CPU 시간 아님) |
| 11 | Arm 47 Robustness | 승컴 rep1–3, 평균 ± CI, 고컴 n=1 | 점 + CI (y축 1.985–1.990 확대) | `chart11_arm47.csv` | 3 + 1 (합산 안 함) | 실측 |
| 12a | Secondary Metrics | 탐색 창 host 비중 | 막대 + CI | `chart12a_explore_share.csv` | 3 | 커널 로그 (고컴 og_audit) |
| 12b | Secondary Metrics | 단계 C 재설정 → 재정착 시간 | 막대 + CI | `chart12b_adaptation_time.csv` | 3 | 커널 로그 (F5). 재설정이 없는 정책은 측정 불가로 제외 |

## 원 논문 Figure 1~10

- 기존 그림 파일은 `report/final-e1-validation/figs/`와 `figs/paper/`에 있다. 이번 작업에서 다시 그리지 않았다.
- 데이터 상태는 Excel의 Experiment Inventory 시트와 `paper_data_validity_matrix.md`에 있다.
  - 그림 7·8·9는 유효한 워크로드 일부만 쓸 수 있다.
  - 그림 10은 단계 1만 유효해서 논문에 쓸 수 없다.
- 논문용 PDF/PNG 그림을 리비전 결과로 새로 그리는 일은 하지 않았다. 남은 일이다.
