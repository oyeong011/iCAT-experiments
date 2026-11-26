# 최종 논문 Figure 선정 카탈로그 (`FINAL_FIGURE_CATALOG.md`)

- **작성 시각**: `2026-11-27 08:48:37 KST`
- **기준 커밋**: 승컴 `origin/main @ 4689c6797` / 고컴 `origin/report/data-validity-20261124 @ 67cf3f901` / 집컴 `origin/report/home-delivery-20261127`
- **4단계 판정 기준**: `논문에 그대로 사용 가능` | `수정 후 사용 가능` | `보조 자료로만 사용` | `사용 금지`

---

## 1. 기존 논문 Figure 1~10 최종 판정

| Figure | 원고 절 | 파일 위치 | 반복 횟수 | 최종 판정 | 사유 및 필수 수정 사항 |
|---|---|---|---|---|---|
| **기존 그림 1** (`fig1_sensitivity`) | §3.3 | `report/final-e1-validation/figs/paper/paper_fig01_fig1_sensitivity.png` | 60 arm 각 `n=1` (10m); Greedy `n=3` | **수정 후 사용 가능** | 동기 부여·`k=2` 배제 근거로 유효. 투고 전 검토용 내부 제목 제거, arm당 `n=1` 명시, 1·2위(`1.744` vs `1.746`) 우열 주장 금지. |
| **기존 그림 2** (`fig3_time_use`) | §4.1 | `report/final-e1-validation/figs/paper/paper_fig02_fig3_time_use.png` | 정책당 **`n=1`** | **보조 자료로만 사용** | 3h 단일 실행 사례(`n=1`)로 통계 증명 불가. 본문 주 근거는 신규 `figure04_exploration`(n=3)으로 대체하고, 기존 그림 2는 1회 실행 사례로만 한정. |
| **레거시 `figs/fig2_learning_over_time`** | (원고 미포함) | `figs/fig2_learning_over_time.png` | 정책당 **`n=1`** | **사용 금지** | `n=1` 및 `CAT-Robust 1.814` vs 실측 `1.8116` 하드코딩 오차(0.13%). 원고에서 이미 제외됨(유지). |
| **기존 그림 3** (`paper_fig03_v4_overview`) | §5 | `report/final-e1-validation/figs/paper/paper_fig03_v4_overview.png` | 알고리즘 도식 | **논문에 그대로 사용 가능** | `online-v4-src/conv_ftl.c` 코드 흐름과 정확히 일치(투고 시 검토용 제목만 제거). |
| **기존 그림 4** (`fig9_rank_over_time`) | §6.1 | `report/final-e1-validation/figs/paper/paper_fig04_fig9_rank_over_time.png` | 정책·기준 모두 **`n=1`** | **보조 자료로만 사용** | 10h 단일 실행 순위 계단도(`n=1`). "약 8시간에 5위"를 결정적 일반화로 주장 금지 → 단일 실행 사례로만 사용. |
| **기존 그림 5** (`fig10_v4_choices`) | §6.1 | `report/final-e1-validation/figs/paper/paper_fig05_fig10_v4_choices.png` | **`n=1`** | **보조 자료로만 사용** | 제거·정착·이웃탐색 동작 메커니즘 시각화용(`1회 실행` 캡션 유지, 1.5h 수렴 일반화 금지). |
| **기존 그림 6** (`fig6_ablation`) | §6.1 | `report/final-e1-validation/figs/paper/paper_fig06_fig6_ablation.png` | 각 **`n=1`** (**구버전 v3**) | **보조 자료로만 사용** | 구버전 v3의 `n=1` 예비 실험. 주 Ablation 그림으로 부적합 → 신규 **`figure02_ablation` / `fig_full_ablation` (`n=3` v4)**으로 주 근거 대체, L232 `【결과 대기】` 삭제. |
| **기존 그림 7** (`fig4_mixes_v4_vs_robust`) | §6.2 | `report/final-e1-validation/figs/paper/paper_fig07_fig4_mixes_v4_vs_robust.png` | CAT-Robust **`n=1`**; v4 `n=1~3` | **수정 후 사용 가능** | 유효 8종 탐색적 요약으로만 사용(v4 3승 5패, `fixed50 n=1`). L240 `【결과 대기】` 삭제 및 탐색적 단서 명시 필수. |
| **기존 그림 8** (`fig7_mix_loss_by_workload`) | §6.2 | `report/final-e1-validation/figs/paper/paper_fig08_fig7_mix_loss_by_workload.png` | 고정 arm 전부 **`n=1`** | **수정 후 사용 가능** | 유효 6종 탐색적 요약. L260 `【선별 실험 결과로 갱신 예정】` 삭제 및 `n=1` 기준 단서 명시 필수. |
| **기존 그림 9** (`fig8_robustness`) | §6.2 | `report/final-e1-validation/figs/paper/paper_fig09_fig8_robustness.png` | 고정 arm 전부 **`n=1`** | **수정 후 사용 가능** | 본문 L262에 소수 2자리 정확한 post-gating 값(`CAT-Best 0.21%`, `CAT-Robust 4.95%`, `iCAT-v4 5.04%`) 병기 및 `n=1` 탐색적 한계 명시 필수. |
| **기존 그림 10** (`fig5_three_phase_mix` / `paper_fig10_e1_three_phase`) | §6.2/6.4 | `figs/fig5_three_phase_mix.png` (오염) / `paper_fig10` (미생성) | **INVALID / 미실행** | **사용 금지** | 구 `mixR`은 `SQLITE_FULL` 오염(YCSB 실패 최대 99.8%)으로 무효, `300k` 재측정은 미실행. 신규 **`figure03_adaptation` (`mixFYF 250k n=3`)**으로 전면 대체. |

---

## 2. 신규 리비전 Figure 최종 판정 (`report/paper-figures/figures/` & `report/revision-final-integration/paper_figures/`)

| 신규 Figure | 대응 심사 항목 | 파일 위치 (300 DPI PNG / PDF / SVG) | 반복 횟수 | 최종 판정 | 비고 |
|---|---|---|---|---|---|
| **`figure01_random`** | M3-1 무작위 선택 대비 | `report/paper-figures/figures/figure01_random.{png,pdf,svg}` | **`n=3`** (고컴 `revA`) | **논문에 그대로 사용 가능** | 95% CI, 개별 rep 점, Arm 47 참고선 포함 (`verify_paper_figures.py` PASS). |
| **`figure02_ablation`** | M2 구성 요소 제거 | `report/paper-figures/figures/figure02_ablation.{png,pdf,svg}` | **`n=3`** (고컴·승컴 분리) | **논문에 그대로 사용 가능** | 호스트 엄격 분리, Welch 95% CI, `revB*` 교차배치 명시. |
| **`figure03_adaptation`** | M2-4/M6-8 3단계 적응 | `report/paper-figures/figures/figure03_adaptation.{png,pdf,svg}` | **`n=3`** (`mixFYF 250k`) | **논문에 그대로 사용 가능** | 오염된 기존 그림 10(`mixR`)의 공식 대체 그림. |
| **`figure04_exploration`** | M2/M5 탐색 비용 | `report/paper-figures/figures/figure04_exploration.{png,pdf,svg}` | **`n=3`** (`revA` + `resource-v124`) | **논문에 그대로 사용 가능** | 기존 그림 2(`n=1`)의 정량적 `n=3` 보강/대체 그림. |
| **`figure05_parameters`** | M6-1 제거 문턱 민감도 | `report/paper-figures/figures/figure05_parameters.{png,pdf,svg}` | **`n=3`** (`revC` 9/9) | **논문에 그대로 사용 가능** | ELIM 10%/15%/25% 실측 + 오프라인 replay 근거. |
| **`figure06_candidates`** | M6-2 후보 공간(60 vs 45) | `report/paper-figures/figures/figure06_candidates.{png,pdf,svg}` | `3×60` sweep + **`n=3`** (`revC`) | **논문에 그대로 사용 가능** | `k=2` 하위 군집 및 60 vs 45 실측 `n=3` 결합. |
| **`figure07_resources`** | M1/M5 메모리·CPU 오버헤드 | `report/paper-figures/figures/figure07_resources.{png,pdf,svg}` | `sizeof` + **`n=3`** (`revA`/`res`) | **수정 후 사용 가능** | `sizeof`(193×/232×)와 iCAT 결정 `ktime` 반영됨. 본문 표 9b의 `m1-20261126` SmartGC `GC 98.4 vs 17.8 µs` 트레이드오프를 캡션 또는 병렬 패널로 보강 권고. |
| **`fig_full_ablation`** | M2 전체 Ablation 통합 | `report/revision-final-integration/paper_figures/fig_full_ablation.{png,pdf,svg}` | **`n=3`** (`revA/E/D/abl`) | **논문에 그대로 사용 가능** | 고컴(`revA/revE`)·승컴(`revD/abl`) 좌우 패널 완전 분리. |
| **`fig_greedy_gc_vs_v4`** | M3-5 Greedy GC 검증 | `report/revision-final-integration/paper_figures/fig_greedy_gc_vs_v4.{png,pdf,svg}` | **`n=3`** (9종 + `batchG`) | **논문에 그대로 사용 가능** | 시각 검수 완료: 레거시 9종 + `mixFYF batchG` (`−19.7%`, Holm `p=0.0013`) 반영. |
| **`fig_online_greedy_vs_v4`** | M3-3 Online Greedy 검증 | `report/revision-final-integration/paper_figures/fig_online_greedy_vs_v4.{png,pdf,svg}` | **`n=3`** (승컴 간접) | **논문에 그대로 사용 가능** | Honest null(`−0.0086`) 및 고컴 기준선 호스트 분리 제시. |
| **`fig_noelim_vs_v4`** | M2-1 후보 제거 단독 | `report/revision-final-integration/paper_figures/fig_noelim_vs_v4.{png,pdf,svg}` | **`n=3`** (`revE` 동일배치) | **논문에 그대로 사용 가능** | `revE` 동일배치 `+0.0913` (`Holm p=0.091` 경계 명시). |
| **`fig_discount_free_vs_v4`** | M2-6 할인 계수 제거 | `report/revision-final-integration/paper_figures/fig_discount_free_vs_v4.{png,pdf,svg}` | **`n=3`** (`abl` 동일배치) | **논문에 그대로 사용 가능** | Honest null(`−0.0038`) + 이론적 `gamma^t` 가중치 곡선. |
| **`fig_random_search_vs_v4`** | R4 Random Search 기대값 | `report/revision-final-integration/paper_figures/fig_random_search_vs_v4.{png,pdf,svg}` | `[추정]` 조합 기대값 | **보조 자료로만 사용** | 실측 Random Search가 아닌 60-arm 스윕 기반 조합론적 기대값(`E[min W_i]`)이므로 본문 실측 그래프와 분리. |
| **`fig_periodic_switching_vs_v4`** | M3 Periodic Switching | `report/revision-final-integration/paper_figures/fig_periodic_switching_vs_v4.{png,pdf,svg}` | **미실행 (0회)** | **사용 금지** | 사용자 결정으로 미실행(플레이스홀더 그림) — 논문 투고 제외, 한계로만 기술. |
