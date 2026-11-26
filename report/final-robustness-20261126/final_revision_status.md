# 최종 리비전 현황 및 11월 27일 선임 연구원 전달 패키지 체크리스트

- **작성 시각**: 2026-11-26 20:30 KST (집컴 통합 관리·독립 검증)
- **전달 마감**: **2026-11-27 (내일)**
- **기준 커밋**: 승컴 `origin/main` **`e6edd2f03`**, 고컴 `origin/report/data-validity-20261124` **`99f579da8`**, 자원 `origin/resource-overhead-20261114` **`c046de0d0`**

---

## 1. 내일(11월 27일) 전달할 최종 산출물 8종 순차 현황

| # | 요구 산출물 | 현재 파일 경로 (집컴 생성·검증 완료) | 현재 상태 (20:30 KST) | 내일 오전 최종 갱신 사항 |
|---|---|---|---|---|
| **1** | **실험별 원시 데이터 및 유효성 검증표** | [experiment_validity.csv](file:///C:/Users/oyeon/orca/iCAT-experiments/report/final-robustness-20261126/experiment_validity.csv) (73개 VALID run + 2개 실행 중) | **1차 전달 가능 (READY)** | `batchG` rep3 (3건) + `m1-smartgc` (1건) 추가 검증 반영 (~02:00 KST) |
| **2** | **정책별 성능 비교 Excel** | [iCAT_Paper_Figures.xlsx](file:///C:/Users/oyeon/orca/iCAT-experiments/report/paper-figures/iCAT_Paper_Figures.xlsx) (21개 시트, `verify_paper_figures.py` PASS) | **1차 전달 가능 (READY)** | `batchG` (9/9) + `m1` (2/2) 시트·수치 최종 재빌드 |
| **3** | **논문용 Figure와 CSV** | [report/paper-figures/figures/](file:///C:/Users/oyeon/orca/iCAT-experiments/report/paper-figures/figures/) (7종 × PNG 300dpi/PDF/SVG) + [report/revision-final-integration/paper_figures/](file:///C:/Users/oyeon/orca/iCAT-experiments/report/revision-final-integration/paper_figures/) (7종 비교도) + [figure_manifest.csv](file:///C:/Users/oyeon/orca/iCAT-experiments/report/paper-figures/figure_manifest.csv) | **1차 전달 가능 (READY)** | `fig_greedy_gc_vs_v4` (`mixFYF n=3` 업그레이드) & `figure07_resources` (`m1` 실측 반영) |
| **4** | **Robustness 감사 보고서** | [robustness_audit.md](file:///C:/Users/oyeon/orca/iCAT-experiments/report/final-robustness-20261126/robustness_audit.md) + [figure_robustness.csv](file:///C:/Users/oyeon/orca/iCAT-experiments/report/final-robustness-20261126/figure_robustness.csv) + [fixed_arm47_audit.csv](file:///C:/Users/oyeon/orca/iCAT-experiments/report/final-robustness-20261126/fixed_arm47_audit.csv) | **완료 (READY)** | `batchG`/`m1` 최종 수치 부록 추가 |
| **5** | **M1 자원 오버헤드 비교표** | [robustness_audit.md §C-1](file:///C:/Users/oyeon/orca/iCAT-experiments/report/final-robustness-20261126/robustness_audit.md) + `iCAT_Paper_Figures.xlsx` (`Fig_07_Resources` Table 7A–7D) | **iCAT 10h + Sim 12/12 + Smoke 2/2 완료; SmartGC 10h 대기** | `mixY-m1-smartgc-eq8-rep1` 완료 즉시 `kernel.log` 단독 `M1PROF` + `VmallocUsed` 채워 최종 확정 |
| **6** | **M3·M6 실험 결과표** | [statistical_audit.csv](file:///C:/Users/oyeon/orca/iCAT-experiments/report/final-robustness-20261126/statistical_audit.csv) (25개 `n=3` 대비 + 3개 `n<3` 대기) + [robustness_audit.md §C-2](file:///C:/Users/oyeon/orca/iCAT-experiments/report/final-robustness-20261126/robustness_audit.md) | **Random·Orig·Greedy·ELIM·60arm·drift12 완료; `batchG` 6/9 완료** | `batchG` rep3 도착 즉시 `Greedy GC` 및 `drift50` `n=3` Welch/Paired/Holm 확정 |
| **7** | **심사 의견별 대응 근거표** | [reviewer_evidence_matrix.csv](file:///C:/Users/oyeon/orca/iCAT-experiments/report/final-robustness-20261126/reviewer_evidence_matrix.csv) + [forensic_requirement_matrix.csv](file:///C:/Users/oyeon/orca/iCAT-experiments/report/revision-final-integration/forensic_requirement_matrix.csv) | **완료 (READY)** | `batchG`/`m1` 완료 시 M1·M3-5·M6-3 판정 최종 승격 |
| **8** | **미충족 항목 및 논문 표현상 한계** | 아래 §2–§3 + [additional_experiments_required.md](file:///C:/Users/oyeon/orca/iCAT-experiments/report/final-robustness-20261126/additional_experiments_required.md) | **완료 (READY)** | 최종 반영 확인 |

---

## 2. 논문 반영 시 반드시 지켜야 할 표현 경계 (주장 가능 vs 주장 불가)

### ✅ 입증되어 논문에 확정 서술 가능한 주장
1. **Random Selection 대비 우위 (M3):** 고컴 `mixFYF n=3`에서 `−8.43%` (`+0.1959 [+0.184, +0.208]`, `g=29.9`, Holm `p<0.001`).
2. **기존 iCAT(`online`) 대비 우위 (M3):** 고컴 `mixFYF n=3`에서 `−11.49%` (`+0.2751 [+0.203, +0.347]`, `g=10.53`, Holm `p=0.014`).
3. **Greedy GC 대비 우위 (M3):** 레거시 유효 9종(`n=3×9`, `−7.1%`~`−42.0%`, 9/9 CI>0) + `mixFYF` `batchG` (`2.633` vs `2.106`, 오늘 밤 `n=3` 확정 예정).
4. **기능 묶음(`VARIANT=2`) 기여 (M2):** 두 호스트 모두 동일 배치 `n=3`에서 Holm 보정 통과 (`고컴 +0.1355 p=0.0003`, `승컴 +0.1241 p=0.028`, 탐색 비중 `85.5%`).
5. **단독 후보 제거(`NoElim`) 및 부분 복원(`Partial vs FullReset`) 기여 (M2):** 동일 배치 `n=3` 사전 등록 Welch CI>0 (`NoElim +0.0913 [+0.030, +0.153]`, 짝 CI>0; `FullReset +0.0596` 전체 / `+0.1296` Phase C). *(단, 4대비 Holm `p=0.060–0.091` 민감도 투명 병기.)*
6. **파라미터 강건성 (M6/m5):** 제거 임계값 10~25% 및 후보 공간 60→45개 축소 시 전체 WAF 손실 미확인(`CI 0 포함`); 과민한 감지 임계값 12.5%는 Phase B 조기 리셋(3/3)으로 WAF 악화(`+0.0720 [+0.012, +0.132]`).
7. **학습기 상태 메모리 및 결정 로직 경량성 (M1/M5):** 4파티션 학습 구조체 `10,112 B` vs SmartGC `1,951,648 B` (`193×`, GC 버퍼 포함 `232×`); 실측 `VmallocUsed` 약 `3 MiB` 절감; 10시간 `mixY`에서 iCAT 학습기(`LEARN`) 누적 `ktime` `4.30 s` (`40.8 ns/GC`, `GC`의 `0.041%`).

### ❌ 현재 결과로 절대 주장할 수 없는 항목 (논문 한계·투명 보고 필수)
1. **"iCAT-v4가 단순 Online Greedy보다 WAF가 낮거나 더 빨리 적응한다"** → 승컴 `mixFYF n=3`에서 전체 WAF 차이 미확인(`−0.0086 [−0.051, +0.034]`, `p=0.54`), 단계 C 첫 5분 WAF는 오히려 Greedy(`2.407`)가 V4(`2.598`)보다 낮음(`p=0.012`).
2. **"할인 계수 `γ=0.9995`가 90분 부하에서 WAF를 낮춘다"** → 동일 배치 `n=3`에서 `−0.0038 [−0.064, +0.057]` (Holm `p=1.000`, `γ^250=0.882`와 일치하는 정직한 Null).
3. **"변화 감지 단독(`NoDrift`) 또는 정착 단독(`NoSettle`)의 통계적 유의성"** → 두 호스트 모두 `n=3` Welch CI가 0을 포함(`NoDrift`는 방향성·분산 감소만 보고).
4. **"iCAT-v4의 GC 1회 전체 CPU 시간이 SmartGC보다 짧다"** → **거짓(반대 결과)!** CAT 전 라인 스캔(`SELECT 48.9–87.0 µs`) 때문에 GC 1회 전체 경과 시간은 iCAT(`53–98 µs`)이 SmartGC(`5.3–7.6 µs`)보다 약 7~17배 김. 반드시 **"학습기 오버헤드 경량성 vs 전 라인 스캔 GC 시간"**을 분리 서술할 것.
5. **"`mixY`에서 SmartGC 대비 WAF 우위가 통계적으로 입증되었다"** → 사용자 결정으로 `n=1` 단일 실행이므로 통계적 유의성 부여 금지 (`n=1` 단일 비교 명시).
6. **"`mixFYF`에서 iCAT-v4가 오프라인 최적 고정 Arm 47(`1.987`, `n=1`)을 능가한다"** → 96% FIO-Fast 편중 부하에서 오라클 고정 조합은 탐색 비용 0으로 더 낮음.
7. **실제 SSD·대용량·다양한 OP·TLC/QLC 비영 erase 지연·실서버 트레이스·미측정 파라미터(판단 구간·정착 조건·`PROBE`·`STALE`·`UCB c`) 일반화** → §8 한계로 명시.

---

## 3. 내일(11-27) 원고 전달 전 반드시 수정할 `PAPER_KCI_DRAFT.md` 오류 4건 (0시간 작업)
1. **L260 그림 9(`fig8_robustness`) 구 수치 불일치 즉시 정정:** 현재 본문 `"CAT-Best 3.0%, iCAT-v4 6.5%, CAT-Robust 7.2%"` → 실제 오염 제외 후 `paper_fig_numbers.json` 수치 **`CAT-Best 0.21%, CAT-Robust 4.95%, iCAT-v4 5.04%`** (최댓값 `1.27% / 20.19% / 15.20%`)로 정정!
2. **표 8("YCSB-A 30만 레코드", 전부 "대기") & 그림 10(`mixR` INVALID):** 유효 `revA/revD mixFYF 250k n=3` 결과로 교체.
3. **표 6·7의 `【결과 대기: arm 47·17·50 각 3회】` 등 잔존 `【...】` 자리표시자:** 모두 제거하고 `고정 조합 n=1 탐색적 비교`로 투명 정정.
4. **M5 본문·참고문헌 `[12]`·`MB/MiB` 통일:** `resource-v124`의 분리 실측값(보상갱신 `1.442 ms`, 선택 `1.273 ms`, `set_arm 0.059 ms`, 에뮬 `do_gc 206.84 s`) 반영 + `m1-20261126`의 불리한 `SELECT` 시간 투명 반영 + SmartGC 저자명 보완.
