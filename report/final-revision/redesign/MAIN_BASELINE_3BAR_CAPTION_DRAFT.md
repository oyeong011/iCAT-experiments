# 메인 Baseline 3-막대 그래프 논문 캡션 초안 (`MAIN_BASELINE_3BAR_CAPTION_DRAFT.md`)

- **대상 그래프:** `report/final-revision/redesign/iCAT_Revision_Results_Redesigned_v2.xlsx` → `01_Main_Comparison_Baselines` 메인 3-막대 차트
- **근거 수치 출처:** `report/final-revision/redesign/MAIN_BASELINE_3BAR_SOURCES.csv` (`origin/main@69d7d5556:result/final-baseline-comparison/baseline_comparison.csv` 및 `final_statistical_validation.csv`)

---

## 1. 국문 논문 본문용 캡션 초안 (KCI 본문 권장)

> **그림 X.** 같은 배치 `iCAT-v4` 대비 기준선 정책별 전체 WAF 차이 (`ΔWAF vs matched iCAT-v4`, 낮을수록 우수; 각 대비 `n=3`, 오차 막대는 Welch 95% 신뢰구간). `Random Selection` (`+0.196`, 95% CI `[0.184, 0.208]`, Holm `p = 9.4×10⁻⁶`)은 호스트 1(Ryzen 5 3600XT, 배치 A)에서 같은 배치로 실행한 `iCAT-v4` (`2.128`) 대비 직접 비교 결과이며, `Greedy GC` (`+0.519`, 95% CI `[0.463, 0.574]`, Holm `p = 0.0013`)는 호스트 2(i7-7700, 배치 G)에서 같은 배치로 실행한 `iCAT-v4` (`2.110`) 대비 직접 비교 결과이다. `iCAT-v4`는 각 배치의 기준선(`ΔWAF = 0`)을 나타낸다. **주의:** `Random Selection`과 `Greedy GC`는 서로 다른 호스트와 배치에서 측정되었으므로 두 기준선 간의 직접 비교를 의미하지 않는다. 동시 대조군 없이 다른 배치와 간접 비교된 `Online Greedy` (`ΔWAF = −0.009`, 95% CI `[−0.051, +0.034]`, 구분되지 않음)는 본 그림에서 제외하고 부록(표/그림 별도)에 제시한다.

---

## 2. 국문 요약 캡션 (지면 제약 시 축약본)

> **그림 X.** 같은 배치 `iCAT-v4` 기준선(`Δ = 0`) 대비 `Random Selection` (`+0.196 [0.184, 0.208]`, Holm `p = 9.4×10⁻⁶`, 배치 A 직접 비교)과 `Greedy GC` (`+0.519 [0.463, 0.574]`, Holm `p = 0.0013`, 배치 G 직접 비교)의 전체 WAF 차이 (`n=3`, Welch 95% CI). 두 기준선은 각자 짝지어진 같은 배치 `iCAT-v4` (`2.128` 및 `2.110`) 대비 차이이며, 서로 다른 호스트·배치이므로 `Random Selection`과 `Greedy GC`를 직접 비교하지 않는다. 간접 비교인 `Online Greedy`는 부록에 별도 수록한다.

---

## 3. 영문 캡션 초안 (영문 초록 / 발표 / 리뷰어 답변용)

> **Figure X.** Total WAF difference relative to each baseline's same-batch matched `iCAT-v4` control (`ΔWAF vs matched iCAT-v4`, lower is better; `n = 3` per policy, error bars show Welch 95% CIs). `Random Selection` (`+0.196`, 95% CI `[0.184, 0.208]`, Holm `p = 9.4e-6`) is directly compared against same-batch `iCAT-v4` (`2.128`) on Host 1 (Batch A), and `Greedy GC` (`+0.519`, 95% CI `[0.463, 0.574]`, Holm `p = 0.0013`) is directly compared against same-batch `iCAT-v4` (`2.110`) on Host 2 (Batch G); `iCAT-v4` denotes the zero-difference baseline (`Δ = 0`). **Note:** `Random Selection` and `Greedy GC` were measured on different hosts and batches and are **not** directly compared against each other. `Online Greedy` (indirect cross-batch comparison, `Δ = −0.009 [−0.051, +0.034]`, indistinguishable from `iCAT-v4`) is excluded from this main figure and reported separately in the appendix.

---

## 4. 본문 인용 시 함께 지켜야 할 3가지 규칙
1. **직접 vs 간접 혼동 금지:** 본 그림의 두 막대는 모두 **같은 배치 직접 비교(`direct`)**이며, 간접 비교(`Online Greedy`)를 본 그림의 결론에 섞어 쓰지 않는다.
2. **기준선 간 우열 서술 금지:** "`Greedy GC`가 `Random Selection`보다 WAF가 더 나쁘다"처럼 두 기준선을 직접 비교하는 문장을 쓰지 않는다(호스트·배치 상이).
3. **지연 트레이드오프 병기:** 본문에서 `Greedy GC` 대비 WAF 절감(`−19.7%`)을 언급할 때, FIO 쓰기 p99 지연은 `Greedy GC` (`41.9 µs`)가 `iCAT-v4` (`166.0 µs`)보다 낮음을 반드시 병기한다.
