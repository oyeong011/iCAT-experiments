# 메인 Baseline 3-막대 시트 설명서 (`MAIN_BASELINE_3BAR_SHEET_GUIDE.md`)

- **대상 파일:** `report/final-revision/redesign/iCAT_Revision_Results_Redesigned_v2.xlsx` (기존 `v1` 무수정 보존)
- **대상 시트:** `01_Main_Comparison_Baselines`
- **데이터 출처:** `origin/main@69d7d5556:result/final-baseline-comparison/baseline_comparison.csv` 및 `result/final-validation-20261127/final_statistical_validation.csv` (신규 계산 없음, 검증 완료 수치만 재사용)

---

## 1. 시트 재구성 의도 (논문 본문 최적화)
- 기존 `v1`의 2개 통합 그래프(절대값 + 직접/간접 혼합 5막대)는 전체 맥락 파악에는 유리하지만, 논문 본문 메인 그림으로 바로 옮기기에는 간접 비교(`Online Greedy`)와 구버전(`원래 iCAT`)이 함께 섞여 시선이 분산되는 문제가 있었다.
- `v2`의 `01_Main_Comparison_Baselines`는 **논문 본문 메인 그림 1개 + 바로 아래 요약표 1개** 구조로 압축했다:
  1. **비교 대상 정확히 3개:** `Random Selection` (`+0.196`), `iCAT-v4` (`0`, 기준선), `Greedy GC` (`+0.519`).
  2. **지표:** 절대 WAF 대신 **`ΔWAF vs matched iCAT-v4 (lower is better)`**를 메인으로 채택해, 서로 다른 호스트·배치의 기준선을 합산하지 않고도 각자의 같은 배치 대조군 대비 WAF 절감 효과를 직관적으로 보여준다.
  3. **Online Greedy 분리:** 동시 대조군이 없는 간접 비교이며 WAF 차이가 구분되지 않는 `Online Greedy` (`Δ −0.009 [−0.051, +0.034]`, `p=0.543`)는 메인 그림에서 제외하고, 시트 `03_Online_Greedy_vs_V4`(보조/부록 후보)로만 남겼다.

---

## 2. 시트 레이아웃 및 구성 요소

| 구역 | 행 범위 | 내용 |
|---|---|---|
| **통합 5칸 요약표** | `A4:E6` | `무슨 실험인지 / 왜 했는지 / 핵심 결과 / 논문에서 할 수 있는 주장 / 한계` |
| **메인 3-막대 그래프** | `A8` (약 23행) | `Random Selection (+0.196)` · `iCAT-v4 (0)` · `Greedy GC (+0.519)` 세로 막대그래프 + Welch 95% CI 오차 막대 (`y축: ΔWAF vs matched iCAT-v4 (lower is better)`) |
| **작은 요약표 (그래프 바로 아래)** | `A33:E36` | `policy / mean_waf / delta_vs_v4 / ci95 / comparison_type` 5열 표 (아래 재수록) + 짝 대조군 상세 주석(`A37:E37`) |
| **하단 필수 주석 · 캡션 블록** | `A39:E47` | 핵심 해석 문장, 짝 대조군 설명, **Random vs Greedy GC 직접 비교 금지 주의**, Online Greedy 제외 사유, 출처/n/직접 비교/Holm 메타, 논문 캡션 초안 |

---

## 3. 시트 내 요약표 (원본 수치)

| policy | mean_waf | delta_vs_v4 | ci95 | comparison_type |
|---|---:|---:|:---:|:---:|
| Random Selection | 2.324 | +0.196 | [0.184, 0.208] | direct |
| iCAT-v4 (matched to Random) | 2.128 | 0 | baseline | direct |
| Greedy GC | 2.629 | +0.519 | [0.463, 0.574] | direct |

- *주석:* `Greedy GC`의 `+0.519`는 같은 배치인 승컴 `batchG-20261126`의 `iCAT-v4` (`mean WAF 2.110`, `SD 0.024`, `95% CI [2.050, 2.171]`, `direct`) 대비 차이이다 (`2.629 − 2.110 = +0.519`).
- *Holm 보정:* `Random Selection` `Holm p = 9.4e-06` (`6`-검정 가족), `Greedy GC` `Holm p = 0.0013` (`4`-검정 가족).
- *트레이드오프 명시:* `Greedy GC`는 WAF에서 불리하지만 FIO 쓰기 p99 지연(`41.9 µs`)은 `iCAT-v4` (`166.0 µs`)보다 낮다(시트 `04_Greedy_GC_vs_V4` 참조).
