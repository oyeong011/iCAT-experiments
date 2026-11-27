# 메인 기준선 비교 그림 캡션 및 설명 (`BASELINE_CAPTION.md`)

- **대상 그림:** `report/final-revision/main-baseline-final/baseline_comparison.{png,pdf,svg}` 및 `iCAT_Main_Baseline_Comparison.xlsx`
- **수치 출처 (삼중 검증 일치):**
  - 승컴 `origin/main @ e78fad59b`: `result/final-baseline-comparison/graph_main_3bars.csv`
  - 고컴 `origin/report/data-validity-20261124 @ 61dfd99e8`: `report/final-revision/redesign_support/BASELINE_FIGURE_REVIEW.md`

---

## 1. 논문 본문용 국문 캡션 (권장 최종본)

> **그림 X. Baseline Comparison: Random Selection, iCAT-v4, and Greedy GC.** mixFYF 90분 워크로드에서 각 정책의 전체 WAF 평균과 95% 신뢰구간(각 정책 `n=3`). **배치 A**(호스트 1, Ryzen 5 3600XT)에서 `iCAT-v4` (`2.128`, 95% CI `[2.116, 2.141]`)는 같은 배치의 `Random Selection` (`2.324`, 95% CI `[2.311, 2.338]`) 대비 전체 WAF를 **8.4% 감소**시켰다(`Δ = +0.196`, 95% CI `[+0.184, +0.208]`, 배치 A 6-검정 Holm `p < 0.0001` [`9.4×10⁻⁶`]). **배치 G**(호스트 2, Intel i7-7700)에서 `iCAT-v4` (`2.110`, 95% CI `[2.050, 2.171]`)는 같은 배치의 `Greedy GC` (`2.629`, 95% CI `[2.612, 2.647]`) 대비 전체 WAF를 **19.7% 감소**시켰다(`Δ = +0.519`, 95% CI `[+0.463, +0.574]`, 배치 G 4-검정 Holm `p = 0.0013`). 두 배치의 `iCAT-v4` 대조군은 호스트와 배치가 다르므로 하나로 합치지 않고 각각 별도 막대로 표시하였으며, `Random Selection`과 `Greedy GC` 간 직접적인 통계 비교는 수행하지 않았다. **본 그림은 무작위 정책 선택과 전통적인 Greedy GC를 각각 동일 배치 iCAT-v4와 비교한다. Online Greedy 대비 iCAT-v4의 우위는 별도로 입증되지 않았으며, 해당 결과는 표 10에 보고한다.** *(참고: FIO 쓰기 p99 지연은 같은 배치에서 Greedy GC(`41.9 µs`)가 iCAT-v4(`166.0 µs`)보다 낮았고, 배치 A 단계 3에서도 iCAT-v4가 Random Selection보다 `15–20 µs` 높았다.)*

---

## 2. 논문 본문용 영문 캡션 (영문 초록·발표·리뷰 답변용)

> **Figure X. Baseline Comparison: Random Selection, iCAT-v4, and Greedy GC.** Mean total WAF with 95% CIs (`n = 3` per policy, 90-minute `mixFYF` workload) across two separate same-batch experiments. In **Batch A** (Host 1, Ryzen 5 3600XT), `iCAT-v4` (`2.128`) reduces total WAF by **8.4%** compared with same-batch `Random Selection` (`2.324`; `Δ = +0.196`, 95% CI `[+0.184, +0.208]`, batch-specific 6-test Holm `p < 0.0001`). In **Batch G** (Host 2, Intel i7-7700), `iCAT-v4` (`2.110`) reduces total WAF by **19.7%** compared with same-batch `Greedy GC` (`2.629`; `Δ = +0.519`, 95% CI `[+0.463, +0.574]`, batch-specific 4-test Holm `p = 0.0013`). The two `iCAT-v4` bars represent separate host/batch controls and are not pooled; no direct statistical comparison is made between `Random Selection` and `Greedy GC`. This figure compares random policy selection and conventional Greedy GC against their respective same-batch `iCAT-v4` controls; superiority of `iCAT-v4` over `Online Greedy` is not established (`Δ = −0.009 [−0.051, +0.034]`, indirect comparison) and is reported separately in Table 10.

---

## 3. 고컴 검토(`61dfd99e8`) 및 승컴 숫자 패키지(`e78fad59b`) 반영 체크리스트

| 점검 항목 | 반영 결과 |
|---|---|
| `iCAT-v4` 단일 0-막대 합산 문제 해소 | 배치 A `iCAT-v4 (2.128)`와 배치 G `iCAT-v4 (2.110)`를 **동일 파랑(`#1F5AA6`) 2개 막대로 분리 배치**, 합산 금지 |
| Random vs Greedy GC 시각·통계 분리 | 두 배치 사이에 점선 구분선·배경 음영을 두고, 괄호는 각 배치 내부(`Random–V4`, `Greedy GC–V4`)에만 연결; 서로 직접 비교 미수행 명시 |
| `Holm p` 배치별 가족 명시 | 배치 A 6-검정 가족 (`<0.0001`, `9.4×10⁻⁶`), 배치 G 4-검정 가족 (`0.0013`) 별도 표기 |
| CI 부호 표기 통일 (`[+0.184, +0.208]`) | 고컴 검토 권고대로 하한·상한 부호 병기 (`[+0.184, +0.208]`, `[+0.463, +0.574]`) |
| Online Greedy 투명 공개 (체리피킹 방지) | 필수 원문 문구 그대로 포함; 표 10 및 부록에서 삭제하지 않고 유지 |
| 지연 트레이드오프 공정 병기 | Greedy GC(`41.9 vs 166.0 µs`)와 Random(`+15–20 µs`) 양쪽 모두에 대해 지연 우위 미주장 병기 |
