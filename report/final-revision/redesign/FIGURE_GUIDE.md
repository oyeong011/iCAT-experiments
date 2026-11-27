# iCAT 논문 리비전 그래프 활용 가이드 (`FIGURE_GUIDE.md`)

- **작성 일시:** 2026-11-27 12:30 KST
- **연결 워크북:** `report/final-revision/redesign/iCAT_Revision_Results_Redesigned.xlsx` (11개 편집 가능 네이티브 Excel 차트, 실제 Microsoft Excel `Office16` 육안 검증 11/11 PASS)
- **고해상도 투고 파일(300 DPI PNG/PDF/SVG):** `report/paper-figures/figures/` (7종, 기존 생성본 무수정 유지)

---

## 1. 재설계 Excel 내 11개 차트 사용 안내 (논문 / 발표 / 리뷰어 답변별 매핑)

| 차트 ID | 시트 | 그래프 내용 | 비교 유형 / n | 추천 활용처 | 필수 캡션 주의 문구 |
|---|---|---|---|---|---|
| **Chart 01A** | `01_Main_Comparison_Baselines` | 주요 기준선 vs iCAT-v4 평균 WAF 절대값 | 직접 3종 + 간접 1종 (`n=3`) | **지도교수 보고 · 리뷰어 M3 총괄 답변 · 발표 슬라이드** | 호스트·배치가 다른 기준선끼리는 직접 통계 비교하지 않음; Online Greedy는 간접 비교 |
| **Chart 01B** | `01_Main_Comparison_Baselines` | V4 대비 Δ WAF (직접 파랑 vs 간접 주황) | 직접 3종(Holm) + 간접 2종 (`n=3`) | **논문 신규 핵심 요약 그림 · 리뷰어 M3 답변** | 양수 = V4 우위; Online Greedy(주황)는 다른 배치 간접 비교이며 0선 교차(구분 불가) |
| **Chart 02** | `02_Random_Selection_vs_V4` | Random Selection vs iCAT-v4 단계별 WAF | 같은 배치 직접 (`고컴 revA`, `n=3`) | **논문 §6.4 M3 그림** (`figure01_random` 보완) | 전체 −8.4%(Holm <.0001), 단계 C −13.0%; FIO p99 지연은 V4가 +15~20 µs 높음 |
| **Chart 03** | `03_Online_Greedy_vs_V4` | Online Greedy vs iCAT-v4 단계별 WAF | 다른 배치 간접 (`승컴`, `n=3`) | **리뷰어 M3 정직한 한계 답변 · 부록** | 전체 WAF 구분 안 됨(`−0.009`); 단계 C 첫 5분은 Greedy가 `−0.191` 유리(V4 불리) |
| **Chart 04** | `04_Greedy_GC_vs_V4` | Greedy GC vs iCAT-v4 단계별 WAF | 같은 배치 직접 (`승컴 batchG`, `n=3`) | **논문 §6.4 M3 핵심 그림** | 전체 −19.7%(Holm .0013), 단계 C −22.4%; 단 FIO p99는 Greedy가 유리(42 vs 166 µs) |
| **Chart 05** | `05_Ablation` | 기능별 12종 Ablation · 파라미터 Δ WAF | 전부 같은 배치 직접 (`n=3`) | **논문 §6.4 M2·M6 핵심 그림** (`figure02_ablation` 확장) | 묶음 OFF 양 호스트 유의(Holm ≤ .028); NoElim·FullReset·drift12는 Holm .060~.091 경계; NoDrift·NoDiscount 미입증 |
| **Chart 06A** | `06_Adaptation_and_Drift` | 변화 감지 문턱별 Δ WAF (`12.5/50%/끔` vs `25%`) | 같은 배치 직접 (`n=3`) | **논문 M6 민감도 · 리뷰어 답변** | **15% 변화 감지 문턱은 미실행**(15%는 제거 문턱 기본값); 12.5%는 고컴, 50%는 승컴 |
| **Chart 06B** | `06_Adaptation_and_Drift` | `[보조 분석]` 5분 창 WAF 전환 궤적 (`revA`) | 같은 배치 직접 (`고컴 revA`, `n=3`) | **기존 논문 Figure 10 교체 그림** (`figure03_adaptation` 대응) | 보조 분석 지표; 60분 FIO 재전환 후 V4 `2.57→2.36` 수렴 vs Random `2.77–2.85` 정체 |
| **Chart 07** | `07_Arm47_Robustness` | 고정 Arm 47 반복 재현성 (승컴 `n=3` vs 고컴 `n=1`) | 호스트 분리 (`n=3` + `n=1` 미합산) | **논문 Robustness 부록 · 리뷰어 답변** | `n=4` 합산 금지; Arm 47은 사후 최적(oracle)이며 "사전 최적"으로 기술 금지 |
| **Chart 08A** | `08_SmartGC_Resource` | iCAT vs SmartGC 메모리 비교 (KiB 로그 축) | 같은 호스트 (`고컴 m1`, `n=1`) | **논문 M1·M5 메모리 그림** (`figure07_resources` 보완) | 이론 계산값(`10,112 B` res-v124 / `10,336 B` m1)과 실측 `VmallocUsed` 엄격 구분; `n=1` |
| **Chart 08B** | `08_SmartGC_Resource` | GC 전체 · SELECT · LEARN · REWARD `ktime` 경과 시간 | 같은 호스트 (`고컴 m1`, `n=1`) | **논문 M1·M5 실행 시간 트레이드오프 그림** | **커널 CPU 시간이 아닌 `ktime` 경과 시간**; `LEARN` 11× 경량이나 `SELECT` 때문에 **GC 전체는 iCAT 5.5× 길음** |

---

## 2. 기존 논문 Figure 1~10 최종 처리 기준 (요약)

| 기존 그림 | 최종 판정 | 조치 및 대체 연결 |
|---|---|---|
| Figure 1~4 (개념도/알고리즘) | **유지** | 변경 불필요 |
| Figure 5 (정적 `3×60` sweep) | **유지** | 180/180 원시 검증 완료 |
| Figure 6 (고정 Arm 47 관련) | **유지 + 캡션 보완** | `Chart 07` (`arm47-20261127 n=3`, CV 0.013%) 재현 근거 추가 + oracle 범위 명시 |
| Figure 7, 8, 9 (기존 `mix` 비교) | **부분 유지·수정** | 유효 8종(`C/D/F/K/L/O/P/Q`) 범위 및 `n=1` 한계 명시; `mixA/B/G/H/J/R` (`mixG` 전체 포함) 제외; Figure 9 소수 2자리(`0.21% / 4.95% / 5.04%`) 병기 |
| **Figure 10** (`mixR 300k` 대기) | **교체 필수 (사용 금지)** | `SQLITE_FULL` 전량 무효 → **`Chart 06B`** 및 300 DPI `report/paper-figures/figures/figure03_adaptation.{png,pdf,svg}`로 교체 |

---

## 3. 그래프 편집·재사용 팁 (Excel 기준)
- 모든 차트는 같은 시트의 **바로 위 표 범위**를 직접 참조하므로, 라벨 다듬기나 축 글꼴 변경 시 Excel에서 즉시 반영된다.
- 차트 제목·축 제목·범례 모두 `overlay = False`로 설정했고, `Chart 08B` 로그 축은 `MinimumScale=0.01`, `CrossesAt=0.01`을 네이티브 적용하여 Microsoft Excel에서 겹침·역전 없이 바로 인쇄/PDF 내보내기가 가능하다.
