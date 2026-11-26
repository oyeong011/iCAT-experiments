# 최초 심사 의견 M2 · M3 요구사항별 충족 판정 매트릭스 (`reviewer_response_matrix.md`)

- **기준 시각:** 2026-11-25 10:23 KST
- **판정 기준:**
  - **PASS:** 동일 호스트·동일 배치 실측(`n ≥ 3`, 95% CI, 원시 로그 독립 검증 통과)으로 요구사항 입증 완료.
  - **PARTIAL:** 일부 조건 입증 또는 교차 배치·추정 모델·레거시 워크로드·`n=2` 진행 중으로 제한적 입증 상태(추가 실행 또는 표현 절제 필요).
  - **FAIL:** 실측 데이터 `n = 0` (미착수 또는 전면 무효)으로 현재 시점 입증 불가.

---

## 1. 심사 의견 M2 (구성 요소별 기여도 — Ablation) 세부 판정

| ID | M2 세부 요구사항 | 현재 확보 근거 (`[측정]`/`[계산]` 구분) | 최종 판정 | PASS 전환 조건 / 논문 반영 전략 |
|---|---|---|---|---|
| **M2-1** | **후보 제거 (Elimination)** 단독 기여도 (`NoElim vs V4`) | `[측정]` 고컴 `revB-noelim` vs `revA-v4` (`n=3`): **`+0.0942 [+0.070, +0.118]`** (CI > 0). 단, `revB-v4` 브리지(`2.1520`)가 `revA-v4` 대비 `+4.8 SD` 이탈해 교차 배치 주의 필요. 승컴 동일 배치 `NoElim` `0/3`. | **PARTIAL** | **승컴 동일 배치 `NoElim` `n=3` 완료 시 PASS 전환** |
| **M2-2** | **정착 (Settlement)** 기여도 (`NoSettle / V2 vs V4`) | `[측정]` 고컴 동일 배치 `V2(NoElim+NoSettle) − V4 = +0.1355 [+0.117, +0.154]` (**결합 효과 확정**). 단독 `revB-nosettle* − V4 = +0.0868 [-0.108, +0.282]` (CI에 0 포함, 미확정). | **PARTIAL** | "제거+정착 결합 기여도 확정, 정착 단독은 높은 분산으로 미확정"으로 정직 기술 |
| **M2-3** | **변화 감지 (Drift Detection)** 기여도 (`NoDrift vs V4`) | `[측정]` 승컴 `revD` (`n=3`, 동일 배치): 3/3 rep 모두 `NoDrift > V4` (전체 `+0.0681`, Phase C `+0.1411`, `g=1.67`, Phase C SD **6.7배 축소** `0.0944 → 0.0141`), 그러나 Welch 95% CI가 0 포함(`[-0.040, +0.176]` / `[-0.087, +0.369]`). 고컴 `revA-v1` 역시 CI에 0 포함. | **PARTIAL** | "3/3 일관 개선 및 Phase C 분산 6.7배 축소, 그러나 `n=3`의 NoDrift 고분산으로 유의성 미확정"으로 절제 기술 |
| **M2-4** | **부분 재탐색 vs 전체 재탐색** (`FullReset vs V4`) | `[측정]` 승컴 `revD` (`n=3`, 동일 배치): Phase C **`+0.1296 [+0.052, +0.208]`** (`g=3.78`, 짝 CI > 0), 전체 **`+0.0596 [+0.016, +0.103]`** (`g=3.08`), 첫 5분 `+0.2712`, 파티션 재탐색 창 수 3.2배 절감(`67` vs `215`). (민감도: 4-대비 Holm 보정 시 `p=0.060 / 0.072` 병기.) | **PASS** | 사전 등록 기준 충족 확정 + Holm 민감도 투명 병기 |
| **M2-5** | **할인 계수 ($\gamma$)** 기여도 (`Discount-free vs V4`) | `[계산]` $\gamma = 65503/65536$, 90분 말기 $\gamma^{250} = 0.8817$ (이론적 감쇠만 계산). **`[측정]` 승컴 `Discount-free (γ=1.0)` `0/3` 미착수.** | **FAIL** | **승컴 `Discount-free MAB` `n=3` 완료 시 PASS/확정 평가 전환** |
| **M2 종합** | **M2 전체 요구사항 충족 여부** | 1 PASS (`FullReset`), 3 PARTIAL (`NoElim*`, `Settle`, `Drift`), 1 FAIL (`Discount-free`) | **PARTIAL** | **승컴 `Discount-free` + 동일 배치 `NoElim` 6 run 완료가 핵심 관문** |

---

## 2. 심사 의견 M3 (기준선 대비 우위 — Baselines) 세부 판정

| ID | M3 세부 요구사항 | 현재 확보 근거 (`[측정]`/`[추정]` 구분) | 최종 판정 | PASS 전환 조건 / 논문 반영 전략 |
|---|---|---|---|---|
| **M3-1** | **Online Random Selection** 대비 우위 | `[측정]` 고컴 `revA-Random` vs `revA-v4` (`n=3`, 동일 배치 `mixFYF`): **`+0.1959 [+0.1840, +0.2078]`** (**−8.43%**, Welch·짝 CI 모두 0 미포함). | **PASS** | 단일 호스트·단일 전환 부하 범위 명시 |
| **M3-2** | **원논문 iCAT (`online`)** 대비 우위 | `[측정]` 고컴 `revC`: 현재 `n=2/3` (`online 2.3938` vs `revC-v4 2.1139`, 약 −11.7% 예비 격차; `n < 3` 통계 보류). | **PARTIAL** | **금일(~14:00 KST) `revC` 15/15 완료 시 PASS 전환 예상** |
| **M3-3** | **Online Greedy (ε-greedy / argmin)** 대비 우위 | **`[측정]` 고컴 `Online Greedy` `0/3` 미착수.** | **FAIL** | **고컴 `Online Greedy` `n=3` 완료 시 PASS/평가 전환** |
| **M3-4** | **Periodic Switching (Round-Robin)** 대비 우위 | **`[측정]` 고컴 `Periodic Switching` `0/3` 미착수.** | **FAIL** | **고컴 `Periodic Switching` `n=3` 완료 시 PASS/평가 전환** |
| **M3-5** | **Random Search (k개 시험 후 고정)** 대비 우위 | **`[추정]`** 모델 2종만 확보 (실측 0건): ① 승컴 MC 20k(`mixFYF` `k=1..45`: `2.306–2.214`, 추정기 편향 `+0.085`), ② 집컴 R4 3×60 sweep 정확 조합론(`k=1` 격차 `+12.5~17.4%`). | **PARTIAL** | 반드시 `[추정]`으로 명시하고 실측과 분리 보고 |
| **M3-6** | **Greedy GC** 대비 우위 | `[측정]` 승컴 2026-09 비오염 9개 워크로드(`mixC/D/F/K/L/M/O/P/Q`, `n=3` vs `n=3`): `iCAT-online`이 9/9 전부에서 **−7.1% ~ −42.0%** 유의 개선 (Welch CI > 0). 단, `mixFYF` Greedy GC는 `0/3` 미실행, `mixC/D` `v4 x1`은 `n=1`. | **PARTIAL** | 레거시 9종 `n=3` 입증 활용 + `mixFYF` Greedy 부재 명시 (또는 선택적 3 run 추가) |
| **M3 종합** | **M3 전체 요구사항 충족 여부** | 1 PASS (`Random Sel.`), 3 PARTIAL (`Original iCAT 2/3`, `Random Search [추정]`, `Greedy GC 레거시`), 2 FAIL (`Online Greedy`, `Periodic Switching`) | **PARTIAL** | **`revC` 15/15 + 고컴 `Online Greedy` & `Periodic Switching` 6 run 완료가 핵심 관문** |

---

## 3. 기타 심사 의견(M4~M7, m5, m6) 요약

- **M4 (통계적 신뢰성):** **PARTIAL** — `revA`, `revB`, `revD`, `resource-v124` `n=3` 완료; `revC` 12/15 진행 중; 레거시 `n=1`은 탐색적 결과로 제한.
- **M5 (자원 효율성):** **PARTIAL** — 메모리 193배(`gdb sizeof`), iCAT 학습 CPU `<0.0002%`, R3 호스트 I/O 지연 분리 분석 완료; SmartGC CPU 미측정은 한계 명시.
- **M6 / m6 (적응 속도 & 파라미터 민감도):** **PARTIAL** — E3 파티션별 감지/재정착/회복 완료(Phase B 저쓰기 감지 지연 한계 명시); E6 `elim10`·`elim25` `n=3` 완료, `revC-v4-rep3` 완료 시 1차 민감도 완료.
- **m5 (후보 공간 60→45):** **PARTIAL** — 3×60 sweep 완료, 라이브 `revC` `arm60` & `v4` 2/3 진행 중(금일 완료).
- **M7 (환경 일반화):** **FAIL (논문 한계 명시)** — 단일 NVMeVirt 8 GiB / OP 7% 환경; 8장 한계로 명시.
