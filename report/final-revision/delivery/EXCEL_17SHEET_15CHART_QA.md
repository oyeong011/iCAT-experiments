# 고컴 통합 Excel (`3fdb21258`) 17시트·15그래프 독립 QA 및 최종 제출 판정

- **감사 주체:** 집컴 (독립 연구 감사·최종 통합 담당)
- **감사 일시:** 2026-11-27 09:18 KST
- **감사 대상:** `origin/report/data-validity-20261124 @ 3fdb21258`
  - `report/final-revision/iCAT_Complete_Experiment_Results.xlsx` (고컴 원본, 17시트, 15차트)
  - `report/final-revision/EXPERIMENT_CATALOG.md`
  - `report/final-revision/EXPERIMENT_RESULT_SUMMARY.md`
  - `report/final-revision/FIGURE_CATALOG.md`
  - `report/final-revision/DATA_PROVENANCE.csv` (136행)
  - `report/final-revision/complete-results/crosscheck_published.csv` (622행) / `crosscheck_mismatch.csv` / `unmet_items.csv` (10행)
- **실제 Microsoft Excel 렌더링 검증 환경:** Windows `Office16\EXCEL.EXE` COM 자동화 (17시트 열기, 수식 오류 검사, 15차트 전수 PNG 내보내기 및 육안 검증 완료)
- **저자 즉시 사용용 수정본:** [`iCAT_Complete_Experiment_Results_Chart10Fixed.xlsx`](./iCAT_Complete_Experiment_Results_Chart10Fixed.xlsx)
  - 고컴 `3fdb21258` 원본과 **17개 시트 전체 셀 값 100% 동일 (`CELL_DIFFS = 0`)**
  - 실제 Excel 육안 검사에서 발견한 **차트 12 (`CPU and Timing` 시트 `그림 10`) 로그 Y축 교차점 버그 (`NA-18`)만 단독 수정** (`MinimumScale=0.01`, `CrossesAt=0.01`, `TickLabelPosition=low`), 수정 후 실제 Excel PNG 재렌더링 PASS 확인.

---

## 1. 17개 시트 구조·수식·내용(목적/가설/결과/해석/심사연결) 전수 감사

| # | 시트명 | 행×열 | 수식/오류 | 목적·가설 | 결과·통계 | 해석·한계 | 심사 연결 | 판정 |
|---:|---|---:|---:|:---:|:---:|:---:|:---:|:---:|
| 1 | `Executive Summary` | 121×8 | 0 / 0 | 요약 시트 | O (28그룹 + M1) | O (할 수 있는/없는 주장) | O (M1–M7) | **PASS** |
| 2 | `Experiment Inventory` | 110×9 | 0 / 0 | 인벤토리 | O (전체 배치+Fig1–10) | O (미실행 목록) | O | **PASS** |
| 3 | `Random Selection` | 49×16 | 0 / 0 | O | O (revA n=3) | O | O (M3) | **PASS** |
| 4 | `Ablation Study` | 189×16 | 0 / 0 | O | O (revA–E, abl) | O (revB n=1 제외 명시) | O (M2·M6) | **PASS** |
| 5 | `Online Greedy` | 58×16 | 0 / 0 | O | O (greedy, revC-online) | O (**부정적 결과 명시**) | O (M3) | **PASS** |
| 6 | `Greedy GC` | 49×16 | 0 / 0 | O | O (batchG n=3) | O | O (M3) | **PASS** |
| 7 | `Workload Adaptation` | 164×10 | 0 / 0 | O | O (revA 5분창, mixY 20단계) | O | O (M6) | **PASS** |
| 8 | `Drift Threshold` | 81×16 | 0 / 0 | O | O (12.5/25/50%/끔) | O (**15% 미실행 명시**) | O (M6) | **PASS** |
| 9 | `SmartGC Comparison` | 42×10 | 0 / 0 | O | O (승컴/고컴 m1 n=1) | O (호스트·빌드 분리) | O (M1) | **PASS** |
| 10 | `Memory Overhead` | 73×16 | 0 / 0 | O | O (계산 vs 실측) | O (`VmallocUsed` 한계) | O (M1·M5) | **PASS** |
| 11 | `CPU and Timing` | 84×12 | 0 / 0 | O | O (`M1PROF`, sim CPU) | O (**GC 5.5× 불리 명시**) | O (M1·M5) | **PASS** (차트 수정본 적용) |
| 12 | `Arm 47 Robustness` | 55×16 | 0 / 0 | O | O (승컴 n=3 + 고컴 n=1) | O (합산 금지·oracle 명시) | O (Robustness) | **PASS** |
| 13 | `Secondary Metrics` | 240×16 | 0 / 0 | O | O (탐색비중·재정착·지연) | O (Greedy C5 불리 명시) | O (M5·M6) | **PASS** |
| 14 | `Statistical Analysis` | 890×16 | 0 / 0 | 통계 총괄 | O (전체 그룹·대비·Holm) | — | — | **PASS** |
| 15 | `Run Validity` | 112×24 | 0 / 0 | 유효성 표 | O (78 mixFYF+M1+smoke) | O (CANCELLED 구분) | O (M4) | **PASS** |
| 16 | `Raw Results` | 98×16 | 0 / 0 | 원시 표 | O (mixFYF 78 + mixY) | — | — | **PASS** |
| 17 | `Reviewer Evidence Matrix` | 14×6 | 0 / 0 | 심사 대응 | O (M1–M7 + Robustness) | O (충족/부분충족 명시) | O | **PASS** |

- **수치 교차검증:** 집컴 80개 VALID run 독립 재계산 대조 결과 **mixFYF 78/78 (312/312 WAF 셀 + host/gc pages) 불일치 0건**, **M1 2/2 (WAF_nand, gc_count, chmodel_warn, VmallocUsed, M1PROF 10개 구간) 불일치 0건**, **직접·동일호스트 대비 33/33 불일치 0건**.
- **실제 Excel 열기 검사:** 복구 경고 0건, 수식 오류(`#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`, `#N/A`, `#NUM!`) 0건.

---

## 2. 15개 Excel 차트 OOXML + 실제 Excel 육안 전수 검사

| # | 시트 | 차트 제목 (요약) | 형태 | 축·단위 | 범례 | 오차 막대 | 데이터 범위 | 원본 Excel 육안 | 수정본 상태 |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | `Executive Summary` | 그림 1. 정책별 전체 WAF (28그룹) | 세로 막대 | Y: 전체 WAF (min=1.8) | 하단 2계열(고컴/승컴) | Custom ±95% CI (`D45:D72`, n=1 없음) | `A45:C72` | **PASS** | PASS |
| 2 | `Executive Summary` | 그림 2. 단계별 WAF (A/B/C) | 묶음 막대 | Y: 단계 WAF | 하단 3계열(A/B/C) | Custom ±95% CI (`C/E/G76:103`) | `A76:G103` | **PASS** | PASS |
| 3 | `Random Selection` | 그림 3. Random vs iCAT-v4 | 묶음 막대 | Y: WAF, 95% CI | 하단 2계열 | Custom ±95% CI (`C/E46:49`) | `A46:E49` | **PASS** | PASS |
| 4 | `Ablation Study` | 그림 4. 구성 요소 제거 Δ WAF | 세로 막대 | Y: Δ WAF (정책−V4) | 하단 1계열 | Custom Welch CI (`D/E179:189`) | `A179:E189` | **PASS** | PASS |
| 5 | `Online Greedy` | 그림 5. Online Greedy·원래 iCAT vs V4 | 세로 막대 | Y: WAF (min=1.8) | 하단 1계열 | Custom ±95% CI (`C54:58`) | `A54:C58` | **PASS** | PASS |
| 6 | `Greedy GC` | 그림 6. Greedy GC vs iCAT-v4 | 묶음 막대 | Y: WAF, 95% CI | 하단 2계열 | Custom ±95% CI (`C/E46:49`) | `A46:E49` | **PASS** | PASS |
| 7 | `Workload Adaptation` | 그림 7a. 5분 창 WAF 시계열 (revA) | 산점선 | X: 0–90분, Y: 5분 창 WAF | 하단 4계열 | 없음 (n=3 평균, SD 열 별도) | `A18:F35` | **PASS** | PASS |
| 8 | `Workload Adaptation` | 그림 7b. mixY 20단계 WAF | 선 | X: S01F–S20S, Y: 로그10 | 하단 4계열 | 없음 (n=1) | `A39:E58` | **PASS** | PASS |
| 9 | `Drift Threshold` | 그림 8. 감지 문턱 12.5/50%/끔 Δ | 세로 막대 | Y: Δ WAF (정책−V4) | 하단 1계열 | Custom Welch CI (`D/E78:81`) | `A78:E81` | **PASS** | PASS |
| 10 | `SmartGC Comparison` | 참고 그림. mixY 정책별 WAF (n=1) | 세로 막대 | Y: WAF | 하단 1계열 | 없음 (n=1 명시) | `A37:B42` | **PASS** | PASS |
| 11 | `Memory Overhead` | 그림 9. 메모리 비교 (계산 vs 실측) | 묶음 막대 | Y: KiB (로그10) | 하단 2계열 | 없음 (n=1) | `A71:C73` | **PASS** (전 값 ≥9.88 KiB) | PASS |
| 12 | `CPU and Timing` | 그림 10. 학습 비용과 GC 실행 시간 | 묶음 막대 | Y: µs per GC (로그10) | 하단 2계열 | 없음 (n=1) | `A81:C84` | **FAIL (`NA-18`)**: `crosses=autoZero` → Excel 기본 교차선 `y=1.0`으로 `<1 µs` 막대(`LEARN`, `REWARD`)가 아래로 거꾸로 매달리고 `SmartGC SELECT=1.00 µs`가 선으로 사라짐 | **PASS (수정 완료)**: `min=0.01`, `crossesAt=0.01` 적용 후 4개 항목 7개 막대 모두 정상 상향 렌더링 확인 |
| 13 | `Arm 47 Robustness` | 그림 11. 고정 Arm 47 반복 재현성 | 점+오차막대 | Y: 전체 WAF (`1.985–1.990`) | 하단 1계열 | Custom ±95% CI (`C51:55`) | `A51:C55` | **PASS** | PASS |
| 14 | `Secondary Metrics` | 그림 12a. 탐색 창 host 쓰기 비중 | 세로 막대 | Y: 비중 (0–1) | 하단 1계열 | Custom ±95% CI (`C214:227`) | `A214:C227` | **PASS** | PASS |
| 15 | `Secondary Metrics` | 그림 12b. 단계 C 재정착 시간 | 세로 막대 | Y: 초 (낮을수록 빠름) | 하단 1계열 | Custom ±95% CI (`C231:240`) | `A231:C240` | **PASS (주의)** *(주1)* | PASS (주의) |

- *(주1) 차트 15 (`그림 12b`)*: `revD-v4`의 n=3 대칭 t-95% CI 하한이 음수(`−400 s`)로 내려가면서 Excel 자동 Y최솟값이 `−600`으로 설정됨. 통계 계산 자체는 정확하며 X축 라벨도 하단(`tickLblPos=low`)에 겹침 없이 출력됨. 다만 논문 인용 시 `n=3` 소표본 대칭 CI 특성임을 주석으로 명시 권장.

---

## 3. 고컴 622개 통계 교차검증 & 승컴 독립 검증 대조

1. **고컴 `crosscheck_published.csv` (622/622 PASS, `crosscheck_mismatch.csv` = 0건):**
   - **617 / 622건:** `|차| = 0.0` (완전 일치)
   - **5 / 622건:** 마크다운 보고서의 소수점 3자리 반올림 표시 차이만 존재 (`±0.0005` 허용 범위 내 일치):
     - `revD-fullreset − revD-v4` waf Holm (`0.072` vs `0.07207`), waf_C Holm (`0.06` vs `0.06038`)
     - `revE-noelim − revE-v4` waf Holm (`0.091` vs `0.09072`), `revE-drift12 − revE-v4` waf Holm (`0.091` vs `0.09072`)
     - `abl-offbundle − abl-v4` waf Holm (`0.028` vs `0.02771`)
2. **승컴 기(旣) push 분석 결과 (`origin/main @ 4689c6797`) 삼중 교차검증:**
   - 622개 중 **79개 항목**이 승컴 `4689c6797` CSV (`arm47` 20개, `batchG` 30개, `secondary-metrics` 10개, `batchG contrasts` 19개)와 직접 대조되었으며 **79/79건 오차 0.0 완전 일치**.
   - 집컴 독립 재계산(`final_experiment_validity.csv`, `final_statistical_audit.csv`)과도 **승컴 33개 run + 고컴 47개 run(총 80/80) 불일치 0건**.
3. **승컴 신규 5종 파일 (`final_independent_validation.md` 외 4종) 수신 상태 — 미검증 명시:**
   - 2026-11-27 09:15 KST `git fetch --all` 기준 `origin/main` HEAD는 여전히 `4689c6797`이며, 승컴의 신규 5종 파일(`final_independent_validation.md`, `final_raw_data_validation.csv`, `final_statistical_validation.csv`, `final_robustness_validation.csv`, `final_m1_resource_validation.md`)은 **아직 push되지 않음 (`WAITING_PUSH / 미검증`)**.
   - 원칙에 따라 해당 5종 파일은 검증 완료로 표시하지 않으며, push 확인 즉시 30분 정기 점검 또는 즉시 대조로 추가 검증한다.

---

## 4. 필수 누락 방지 3대 부정·미실행 항목 점검 (요구사항 8번)

| 필수 확인 항목 | 고컴 Excel 반영 위치 | 고컴 문서 반영 위치 | 집컴 전달 패키지 반영 위치 | 판정 |
|---|---|---|---|---|
| **15% 변화 감지 미실행** | `Drift Threshold` (`R12`, `R74`), `Experiment Inventory`, `unmet_items.csv` | `EXPERIMENT_CATALOG.md §4`, `FIGURE_CATALOG.md` (그림 8) *(주의: `EXPERIMENT_RESULT_SUMMARY.md`에는 15% 문구 미포함)* | `FINAL_LIMITATIONS.md`, `FINAL_EXPERIMENT_REPORT.md`, `FINAL_EXPERIMENT_STATUS.md`, `FINAL_REVIEWER_RESPONSE_MATRIX.xlsx` | **누락 없음** (고컴 요약 MD 1곳 보완 권고) |
| **Online Greedy 부정적 결과** | 10개 시트 (`Executive Summary`, `Online Greedy`, `Secondary Metrics`, `Reviewer Evidence Matrix` 등): 전체 WAF `−0.0086 [−0.0508, +0.0336]` 구분 불가(간접), **단계 C 첫 5분 `−0.191 [−0.289, −0.093]` V4에 불리** | `EXPERIMENT_CATALOG.md`, `EXPERIMENT_RESULT_SUMMARY.md §2·3·5`, `FIGURE_CATALOG.md` | `FINAL_EXPERIMENT_REPORT.md`, `FINAL_LIMITATIONS.md`, `FINAL_REVIEWER_RESPONSE_MATRIX.xlsx` | **누락 없음** |
| **SmartGC 대비 GC 실행 시간 불리함** | `Executive Summary`, `CPU and Timing`, `Reviewer Evidence Matrix`: **`iCAT GC 98.37 µs vs SmartGC-EQ8 17.84 µs` (5.5× 더 길음)**, `SELECT 87.05 vs 1.00 µs`, 커널 CPU 시간 미측정 구분 | `EXPERIMENT_RESULT_SUMMARY.md §4·5` | `FINAL_EXPERIMENT_REPORT.md`, `FINAL_LIMITATIONS.md`, `FINAL_REVIEWER_RESPONSE_MATRIX.xlsx` | **누락 없음** |

---

## 5. 기존 논문 Figure 1~10 교체 최종 판정 & 표 6~11·본문 일치 판정

- **Figure 1~10 최종 판정** (상세 근거: [`FINAL_FIGURE_CATALOG.md`](./FINAL_FIGURE_CATALOG.md)):
  - **그대로 유지 (5개):** Figure 1, 2, 3, 4 (개념도/알고리즘), Figure 5 (정적 FIO/YCSB 3×60 sweep, 180/180 원시 검증).
  - **유지 + 캡션/범위 명시 보완 (1개):** Figure 6 (Arm 47 반복 재현성 `arm47-20261127 n=3` `1.9876 ± 0.0003` 확보, 단 단일 실행 원래 조건 및 oracle 성격 명시).
  - **부분 유지·수정 필요 (3개):** Figure 7, 8, 9 (YCSB 오염 워크로드 제외 범위 명시 + Figure 9 소수점 1자리 반올림 오해 해소 `CAT-Best 0.21% / CAT-Robust 4.95% / iCAT-v4 5.04%`).
  - **반드시 교체/제거 (1개):** **Figure 10** (`300k` 1단계만 유효, `【재측정 결과 대기】`) → 리비전 `mixFYF 250k n=3` 기반 **`figure03_adaptation`** (`report/paper-figures/png/figure03_adaptation.png` 및 통합 Excel `Workload Adaptation` `그림 7a`)로 교체.
  - **신규 추가 권장 (논문용 300 DPI 파일 이미 생성 완료):** `report/paper-figures/{png,pdf,svg}/figure01_random_comparison` ~ `figure07_resource_overhead` (7종, 40/40 검증 PASS).
- **표 6~11 및 `PAPER_KCI_DRAFT.md` (`67cf3f901`) 대조 결과** (상세 패치: [`PAPER_KCI_DRAFT_PATCH_PROPOSAL.md`](./PAPER_KCI_DRAFT_PATCH_PROPOSAL.md), [`FINAL_PAPER_NUMBER_AUDIT.csv`](./FINAL_PAPER_NUMBER_AUDIT.csv)):
  - **표 6 (21/21 셀), 표 7 (`mixD/L/Q`), 표 9b (8/8 셀), 표 10 (22/22 셀), 표 11 (8/8 셀):** 원시 로그 및 통합 Excel과 **100% 일치**.
  - **표 8 (`300k` 8행 전체 `"대기"`):** 미실행 구(舊) 표 → **제거 후 §6.4 `mixFYF 250k n=3` 표 10·11로 대체**.
  - **본문 수정 필수 5건:** ① `L405` 구(舊) 문구 `"GC 수행 시간은 계측하지 않았다"` 수정(표 9b·`resource-v124`와 모순), ② `L297–L307` 표 8·그림 10 대기 항목 교체, ③ `L004/L232/L240/L256/L260` `【결과 대기】` 태그 5건 제거, ④ `L262` 그림 9 소수점 2자리 병기, ⑤ `L313` 표 9 `WAF_nand` vs 호스트 `WAF` 각주 추가.
