# 잔여 리비전 실험 및 실행 계획 현황 (`remaining_experiments.md`)

- **기준 시각:** 2026-11-25 10:23 KST
- **집컴 원칙:** 승컴·고컴의 큐를 제어하거나 NVMeVirt 실험을 실행하지 않으며, 30분 주기 GitHub 모니터링(`task-56`)으로 완료 즉시 독립 검증·통합한다.

---

## 1. 현재 진행 중 / 잔여 필수 실험 목록

| 우선순위 | 담당 호스트 | 실험 항목 | 대응 심사 의견 | 현재 상태 | 잔여 Run | 예상 소요 | 비고 / 대조군 연결 |
|---:|---|---|---|---|---:|---:|---|
| **1 (실행 중)** | 고컴 | `revC-20261124` 잔여 3건 (`v4`, `arm60`, `online` rep3) | M3-2, M6(E6), m5(E7) | **RUNNING (12/15)** | 3 | ~4.6 h | 약 **14:00 KST** 전체 완료 예상. 완료 즉시 `revC-v4` `n=3` 확정 및 E2/E6/E7 Welch·짝 CI 산출 |
| **2 (승컴 대기)** | 승컴 | **Discount-free MAB ($\gamma=1.0$)** (`mixFYF`, `n=3`) | **M2-5 (현재 FAIL)** | **NOT STARTED (0/3)** | 3 | ~4.6 h | 승컴 `revD-v4` (`2.1386 ± 0.0082`, `n=3`)와 동일 호스트 비교 (배치 간격 짧아 시점 편차 최소, 필요 시 브리지 `v4` 1 run 확인) |
| **3 (승컴 대기)** | 승컴 | **동일 배치 NoElim** (`mixFYF`, `n=3`) | **M2-1 (현재 PARTIAL)** | **NOT STARTED (0/3)** | 3 | ~4.6 h | 고컴 `revB-noelim`의 배치 이탈(`+4.8 SD`) 우려를 승컴 `revD-v4`와 동일 호스트로 해소 |
| **4 (고컴 대기)** | 고컴 | **Online Greedy** (`mixFYF`, `n=3`) | **M3-3 (현재 FAIL)** | **NOT STARTED (0/3)** | 3 | ~4.6 h | `revC` 종료 직후 착수 시 `revC-v4` (`n=3`)와 연속 배치 비교 가능 |
| **5 (고컴 대기)** | 고컴 | **Periodic Switching (Round-Robin)** (`mixFYF`, `n=3`) | **M3-4 (현재 FAIL)** | **NOT STARTED (0/3)** | 3 | ~4.6 h | `revC` 종료 직후 연속 배치 비교 |

- **총 잔여 필수 실행:** **15 run** (승컴 6 run ≈ 9.2h, 고컴 9 run ≈ 13.8h — 양 장비 병렬 가동 시 약 14시간 내 전부 완료 가능).
- **중복 검증:** 승컴(M2: Discount-free, NoElim)과 고컴(M3: revC 잔여 + Online Greedy, Periodic Switching) 간 중복 실행 **0건**.

---

## 2. 선택적 보강 / 비실행 확정 항목

| 항목 | 현재 상태 | 권장 조치 |
|---|---|---|
| **`mixFYF` Greedy GC (`n=3`)** | NOT RUN (레거시 9종 `x1` `n=3` vs `online`만 유효) | **선택 사항 (4.6 h):** 레거시 9종(`−7.1% ~ −42.0%`)으로 M3-6을 방어할 수 있으나, 본문 `mixFYF` 표에 `Greedy GC` 행을 직접 넣고 싶다면 고컴/승컴 중 한 곳에서 3 run 추가 고려 |
| **라이브 NVMeVirt Random Search** | NOT RUN (오프라인 모델 `[추정]` 2종 확보) | **비권장:** 오프라인 모델(`[추정]`)로 충분하며, 온라인 Random Selection(`revA-Random`, −8.43%) + `Online Greedy` + `Periodic Switching` 실측으로 M3 기준선 요건 충족 |
| **E6 2차 (변화 감지 문턱 12.5%/50% 등)** | NOT RUN | `revC` E6 1차(`elim10/15/25`) 결과 확인 후 결정 |
| **E8 (실물 SSD / 용량·OP 일반화)** | NOT RUN | **실행하지 않음** — 논문 8장 한계로 명시 |

---

## 3. 완료 후 최종 통합 및 `main` 병합 게이트

1. 고컴 `revC` 15/15 완료 시 (`~14:00 KST`):
   - `revC-v4` `n=3` 기준 `revA-v4` 대비 배치 편차 최종 판정 → 승컴 `NoElim` 설계와 교차 검토.
   - `iCAT_Paper_Figures.xlsx` (`Fig_01`, `Fig_05`, `Fig_06`) 및 `evidence_matrix.xlsx` 자동 갱신.
2. 승컴 `Discount-free` + `NoElim` (6 run) 및 고컴 `Online Greedy` + `Periodic Switching` (6 run) 완료 시:
   - 집컴에서 전 건 7개 항목 독립 검증 후 `iCAT_Paper_Figures.xlsx` 21개 시트, `paper_figures/` 7종, `evidence_matrix.xlsx` M2/M3 최종 PASS/PARTIAL/FAIL 재판정.
3. 원고(`PAPER_KCI_DRAFT.md` 표 8 `mixFYF` 250k 정렬 및 본문 미참조 표·그림 수정) 일관성 최종 검증 후 **사용자 승인 하에 `main` 병합**.
