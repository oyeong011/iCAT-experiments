# iCAT 논문 리비전 최종 Robustness 감사 보고서 (`final_robustness_audit.md`)

- **작성 주체**: 집컴 (독립 연구 감사·원시 로그 검증·최종 통합 담당)
- **생성 시각**: `2026-11-27 01:08:16 KST`
- **기준 원격 커밋**: 승컴 `origin/main @ 2ccac44b7` / 고컴 `origin/report/data-validity-20261124 @ 2a0900382` / 자원 계측 `origin/resource-overhead-20261114 @ c046de0d0`
- **절대 원칙**: 원시 로그(`result/`)·원본 `figs/` 무변경, 신규 NVMeVirt 미실행, 호스트·배치 무분별 합산 금지, `n<3` 통계적 유의성 미부여, 미검증·실행 중 항목 `PASS` 표기 금지.

---

## 1. 기존 논문 Figure 1~10 전수 감사 (원시 데이터 연결 · 반복 수 · 사용 범위)

| Figure | 원고 절 | 원시 로그 경로 (검증됨) | 반복 횟수 | 분류 | 사용 가능 범위 및 필수 조치 |
|---|---|---|---|---|---|
| **그림 1** (`fig1_sensitivity`) | §3.3 | `result/sweep-20260915/rank-test4.txt`, `result/gh-repro-20260914/*.console.txt` | 60 arm 각 **`n=1`** (10m); Greedy **`n=3`** (`2.186`) | **PARTIAL** | 동기 부여·`k=2` 하위 군집 배제 근거로 사용 가능. 단 arm별 `n=1` 명시, 1·2위(`arm31 1.744` vs `arm47 1.746`) 우열 주장 금지. |
| **그림 2** (`fig3_time_use`) | §4.1 | `result/mix-20260911/t4-online{,v2,v3}-rep1-x18`, `t4-onlinev4-rep1-x60/kernel.log` | 정책당 **`n=1`** | **FRAGILE** | 통계적 증명 불가 — **"1회 실행 사례"**로 명시하고, `n=3` 탐색 비중 정량 근거(`revC` `97%` vs `27%`, `figure04_exploration.png`) 병기. |
| **그림 3** (`paper_fig03_v4_overview`) | §5 | 코드 매핑 (`online-v4-src/conv_ftl.c`, `analysis/final_e1/fig3_v4_overview.py`) | 도식 (N/A) | **ROBUST** | 그대로 사용 가능 (투고 시 검토용 내부 제목만 제거). |
| **그림 4** (`fig9_rank_over_time`) | §6.1 | `t4-online{,v3,v4}-rep1-x{18,60}` + 고정 조합 15종 `rep1` | 정책·기준 모두 **`n=1`** | **FRAGILE** | "약 8시간에 5위"를 결정적 일반화로 주장 금지 → **1회 실행 사례**로 완화. |
| **그림 5** (`fig10_v4_choices`) | §6.1 | `result/mix-20260911/t4-onlinev4-rep1-x60/kernel.log` | **`n=1`** | **PARTIAL** | 제거·정착·이웃탐색 동작 메커니즘 예시로만 사용 (`1회 실행` 캡션 유지). |
| **그림 6** (`fig6_ablation`) | §6.1 | `t4-onlinev3-rep1-x18`, `v3probe`, `online`, `v3k2` | 각 **`n=1`** (**구버전 v3**) | **FRAGILE** | 주 Ablation 근거로 부적합(구버전 v3, `n=1`). L232 `【결과 대기】` 삭제 후, §6.4 `n=3` v4 Ablation(표 10·`figure02_ablation.png`)을 주 근거로 명시. |
| **그림 7** (`fig4_mixes_v4_vs_robust`) | §6.2 | `result/mix-20260911/mix*-{onlinev4,fixed50}-rep*-x3` (유효 8종) | CAT-Robust **`n=1`** (8/8); v4 **`n=1~3`** | **FRAGILE** | 탐색적 다중 워크로드 요약으로만 사용(v4 3승 5패, `fixed50 n=1`). L240 `【결과 대기】` 삭제. |
| **그림 8** (`fig7_mix_loss_by_workload`) | §6.2 | `result/mix-20260911/mix{C,D,F,K,O,P}-*-x3` (유효 6종) | 고정 arm 전부 **`n=1`**; v4 **`n=1~3`** | **FRAGILE** | 탐색적 참고 자료로 제한. L260 `【선별 실험 결과로 갱신 예정】` 삭제. |
| **그림 9** (`fig8_robustness`) | §6.2 | 위 6종 공통 유효 전환 워크로드 | 고정 arm 전부 **`n=1`** | **FRAGILE** | 과거 초안 구수치(`3.0/6.5/7.2%`)는 `30cf9b9fb` L262에서 `0.2%/5.0%/5.0%`로 수정됨. 단 소수 2자리 정확값은 **`CAT-Best 0.21%, CAT-Robust 4.95%, iCAT-v4 5.04%`**이므로 평균 우위 오독 방지를 위해 소수 2자리 병기 권고. |
| **그림 10** (`fig5_three_phase_mix` / `paper_fig10_e1_three_phase`) | §6.2/6.4 | 구 `mixR-*-x3` (**SQLITE_FULL 오염으로 무효**) / 300k 재측정 **미실행** | **INVALID / 미실행** | **INVALID** | **절대 사용 금지.** 표 8(`300k records` 전원 대기)·그림 10(`생성 대기`)을 유효 `mixFYF 250k (n=3)` 결과(`revA/revD`, 표 10·`figure03_adaptation.png`)로 전면 대체. |
| **신규 리비전 Figure 1~7** (`report/paper-figures/figures/`) | §6.4/§7 | 75+ 검증 `mixFYF 250k` run + `resource-v124` + `3×60` sweep | 핵심 조건 전부 **`n=3`** | **ROBUST** | 논문 리비전의 **1차 통계적 확정 근거** (`verify_paper_figures.py` 전수 수치 일치 검증). |

### 1.1 고정 Arm 47 (`1.987`) 사용 범위 및 재현성 감사
- **`revA/mixFYF-arm47-rep1` (`WAF = 1.987355`)**: `mixFYF 250k`에서 확보된 **유일한 `n=1` 단일 실행** (`rep2–3` 미존재). 따라서 `1.987`은 "단일 실행 참고 상한(oracle reference, `n=1`)"으로만 표기하며, `iCAT-v4`와의 통계적 차이 검정이나 CI 산출에 사용 금지.
- **기존 `n=3` Arm 47 증거**: FIO-Fast 단일 10분(`SD=0.00017`, `t4-fixed47-rep1..3`), FIO-Fast 30분(`1.774`, `resource-v124`), `mixY 90m`(`cat60-90min`)에서는 `n=3` 재현성이 높으나, **`mixY 10h` 교차 월 비교**에서는 10월(`2.864`)과 11월(`3.233`) 사이에 **`+12.9%` 시기 편차**가 실측되어 교차 날짜/배치 `n=1` 비교 불가 원칙을 실증함.
- **표 6·표 7의 x3 Arm 47**: 3배 길이 전환 워크로드(표 6, 7)의 고정 조합은 모두 `n=1`이므로, L256 `【결과 대기: arm 47·17·50 각 3회】`는 삭제하고 "고정 조합 1회 측정 참고값"으로 한계를 명시해야 함.

---

## 2. 전달 자료 오류 7건 전수 점검 및 수정 내역 (Section 2.C)

| # | 발견 오류 항목 | 원본 위치 및 문제 내용 | 수정 상태 및 집컴 최종 패키지 반영 내역 |
|---|---|---|---|
| **1** | **SmartGC `WAF` vs `WAF_nand` 정의 차이** | `iCAT_revision_databook_v2.xlsx` `F7_smartgc_waf`는 호스트 기준 `WAF=1+gc/host` (`EQ8 4.4984`, `SmartGC 11.0723`) 기재, 반면 `PAPER_KCI_DRAFT.md` 표 9는 DRAM 버퍼 흡수 제외 `WAF_nand` (`4.49`, `11.02`) 기재 | `final_experiment_validity.csv`, `iCAT_Paper_Figures.xlsx`, 본 보고서에서 **`WAF`와 `WAF_nand` 두 열을 분리·병기**하고 계산식(`1 + gc/host` vs `1 + (gc - buf_absorb)/host`) 명시. |
| **2** | **`VmallocUsed` 단위 라벨 오류** | `iCAT_revision_databook_v2.xlsx` `F6_memory` R9–R12의 `item` 열에 `(kB)`로 표기하면서 `bytes` 열에 `kB×1024` bytes 값(`38,508,134.4` 등) 저장 | `VmallocUsed_delta_kB`와 `VmallocUsed_delta_bytes`를 별도 열로 엄격 분리하고, 고컴 데이터북 정오표에 R9–R12 라벨 수정 명시. |
| **3** | **Excel 통계값 공란 (`F3_contrasts_same_batch`)** | `revE`(`R26–R33`)에만 `p_unadjusted`·`p_holm_4tests`가 기입되고 `abl`(`R34–R39`), `greedy`(`R40–R45`), `revA/C/D`(`R2–R25`)는 공란 | `final_statistical_audit.csv` 및 `iCAT_Paper_Figures.xlsx`에서 **전 `n=3` 대비의 `Welch_p`, `Holm_p`, `Holm_Family_Spec`, `Hedges_g`, `Paired_p` 공란 0건**으로 전수 기입 (`abl OffBundle`: `Welch p=0.0069`, **`Holm p=0.0277`**; `NoDiscount`: `p=0.869`, `Holm p=1.000`; `greedy vs revD-v4`: `p=0.543`). |
| **4** | **Greedy 비교 부호 비일관** | `DELIVERY_20261127.md` §2·`F3` R40은 `revD-v4 − Online Greedy = +0.009 [−0.034, +0.051]`, 논문 표 10은 `Online Greedy − revD-v4 = −0.009 [−0.051, +0.034]`로 방향 상반 | 집컴 전 산출물에서 **`Δ = 비교 정책 − 대조군(iCAT-v4)`**로 부호 완전 통일 (`Online Greedy − revD-v4 = −0.0086 [−0.0508, +0.0336]`, 양수 = iCAT-v4 우위, 음수 = 비교 정책 우위). |
| **5** | **Figure 9 과거 수치** | 구 초안 L260에 유효성 게이팅 전 구수치(`CAT-Best 3.0%, iCAT-v4 6.5%, CAT-Robust 7.2%`) 잔존 (`30cf9b9fb` L262는 1자리 반올림 `0.2% / 5.0% / 5.0%`로 갱신됨) | 정확한 post-gating 2자리 수치 **`CAT-Best 0.21%, CAT-Robust 4.95%, iCAT-v4 5.04%`**를 정오표·보고서에 명시(반올림 시 `iCAT-v4`와 `CAT-Robust`가 동일하게 보이는 왜곡 방지). |
| **6** | **`PAPER_KCI_DRAFT.md` L385 과거 GC 계측 설명** | L385에 `"GC 수행 시간은 계측하지 않았다"` 잔존 (`origin/resource-overhead-20261114`의 FIO-Fast 30m `do_gc − on_gc` `n=3` 실측 및 `m1-20261126` `M1PROF`와 충돌) | `final_revision_status.md`에 L385 즉시 교체 문안 제공: `resource-v124` (`do_gc − on_gc` iCAT-v4 `206.84 s` vs CAT-47 `255.98 s`, `erase=0` 단서; `reward 1.442 ms`, `select 1.273 ms`, `set_arm 0.059 ms`) 및 `m1-20261126` `ktime`(`SELECT` 스캔 비용 vs `LEARN` 극소 비용) 분리 기재. |
| **7** | **표 6·표 8의 `300k records` 및 `【결과 대기】` 플레이스홀더** | 원고 L004–005, L232(그림 6), L240(그림 7), L256(표 6), L260(그림 8), L297–307(표 8 `300k records` 전원 "대기" & 그림 10)에 미실행/구 플레이스홀더 잔존 | 전 7개 플레이스홀더 위치를 line 번호까지 식별. `300k` 표 8·그림 10은 미실행이므로 삭제·대체(`mixFYF 250k n=3` 표 10·`figure03_adaptation.png`), 표 6·그림 7은 `n=1~3` 탐색적 단서로 확정. |

---

## 3. 최종 신규 배치 독립 검증 결과 (`batchG-20261126` & `m1-20261126`)

### 3.1 승컴 `batchG-20261126` 독립 검증 완료 (9/9 VALID, `origin/main @ 2ccac44b7`)

모든 9개 run에 대해 종료 코드(`0`), 사전등록 모듈 SHA256, FIO 오류(`0`)·시드(`rep1/2/3`), YCSB 성공률(`100%`, `SQLITE_FULL=0`), 커널 오류(`0`), 원시 카운터 2-경로 WAF 재계산을 독립 검증 완료했습니다. *(참고: `cpu_check=unavailable`은 `loadsampler`가 승컴에 미이식되어 CPU가 미측정임을 뜻하며 WAF 유효성과 무관 — 커밋 `2fd5fa359` 확인)*

| 정책 (n=3) | Total WAF (Mean ± SD) | 95% t-CI | Δ vs `bg-v4` [Welch 95% CI] | Welch p | Holm p (4-test) | Hedges' g | Phase C Δ [Welch 95% CI] | 판정 |
|---|---:|---|---|---:|---:|---:|---|---|
| **iCAT-v4 (`bg-v4`)** | `2.1105 ± 0.0245` | `[2.0497, 2.1712]` | 대조군 | — | — | — | 대조군 | 동일 배치 대조군 |
| **Greedy GC** *(M3-5)* | `2.6293 ± 0.0069` | `[2.6121, 2.6465]` | `+0.5189 [+0.4633, +0.5744]` | `0.000321` | `0.001284` | `23.09` | `+0.7078 [+0.5882, +0.8274]` (`Holm 0.0038`) | **ROBUST_PASS (Welch CI excl. 0 & Holm p<0.05)** |
| **Drift 50%** *(M6-3)* | `2.1288 ± 0.0299` | `[2.0546, 2.2030]` | `+0.0183 [-0.0445, +0.0812]` | `0.458654` | `0.830654` | `0.537` | `+0.0418 [-0.0877, +0.1714]` (`Holm 0.8307`) | **NO_DIFF_FOUND (CI includes 0)** |


### 3.2 고컴 `m1-20261126` 독립 검증 완료 (2/2 VALID, `n=1` per policy, `origin/report/data-validity-20261124 @ 2a0900382`)

> **핵심 검증 규칙:** 모든 `M1PROF` 카운터는 커밋 `08ac54dc9` 규정에 따라 이전 실행 링버퍼가 섞이지 않은 **`kernel.log.nowarn.gz` 단독**에서 파싱했습니다(`kernel-final.log` 미사용). 사용자 결정으로 `rep2–3`은 취소되어 **정책당 `n=1`**이며, 통계적 유의성은 부여하지 않습니다.

| 지표 (구분) | `m1-icat-v4` (`n=1`) | `m1-smartgc-eq8` (`n=1`) | 해석 및 한계 |
|---|---:|---:|---|
| **호스트 기준 `WAF`** `[실측]` | `3.330464` (`8.285 TB`) | `4.561785` (`5.970 TB`) | `1 + gc_pages/host_pages` |
| **NAND 기준 `WAF_nand`** `[실측]` | `3.330464` | `4.553194` | SmartGC DRAM GC 버퍼 흡수분 구분 |
| **이론적 학습 상태 메모리 (`gdb sizeof`)** `[계산]` | `10,112 B` (전체 tuner `10,624–10,848 B`) | `1,951,648 B` (+GC 버퍼 `393,216 B` = `2,344,864 B`) | 학습 상태 **193.0×** (전체 **231.9×**) 경량 |
| **실측 커널 `VmallocUsed` Δ (`load1s - pre`)** `[실측]` | `34848 kB` (`35684352 B`) | `37752 kB` (`38658048 B`) | 에뮬레이터 공통 ~35 MB 포함; 커널 스레드는 `VmRSS` 미존재 |
| **GC 전체 `ktime` 경과 시간** `[실측, 경과시간]` | `98.37 µs/GC` (누적 `10354.1 s`, `1342 ms/GiB`) | `17.84 µs/GC` (누적 `1849.5 s`, `333 ms/GiB`) | **불리 사실 명시:** iCAT이 호출당 **5.5×** 김(CAT 전 라인 스캔). "GC가 빠르다" 주장 금지 |
| **희생 선택 `SELECT` `ktime`** `[실측, 경과시간]` | `87.05 µs/GC` (`9162.4 s`, GC의 88.5%) | `1.00 µs/GC` (`103.9 s`, step 제외 `56.3 s`) | CAT 전수 스캔 vs SmartGC 상태 목록 |
| **학습 알고리즘 `LEARN` `ktime`** `[실측, 경과시간]` | `40.80 ns/GC` (`4.295 s`, GC의 0.041%) | `975.48 µs/step` (`48,751`회 = `47.56 s`) | 학습 갱신 자체는 iCAT이 11× 작음(`4.3 s` vs `47.6 s`) |
| **보상·GC 버퍼 `ktime`** `[실측, 경과시간]` | 해당 없음 (`REWARD`는 `LEARN`에 포함, GC 버퍼 없음) | `REWARD 9.17 s` + `BUF 상한 473.1 s` (계측 비용 포함) | SmartGC 전용 쓰기 경로 버퍼 비용 |
| **실측 `VmallocUsed` 차이 및 언로드 복귀** `[실측]` | `load1s Δ +34848 kB`, `post +16 kB` | `load1s Δ +37752 kB`, `post +16 kB` | 차이 **`+2904 kB`** (`+2,973,696 B`) — 이론 계산차 `3,058 KiB`와 5% 이내 일치 |
| **채널 모델 포화 경고 (`chmodel_warn`)** `[실측]` | `0` | `22069` | SmartGC에서만 포화 경고 발생 → 지연 비교 제외 유지 |
| **커널 내부 CPU 시간 (`perf` / `task_cputime`)** | **미측정** | **미측정** | busy-poll 구조·`perf` 미지원; `ktime` 경과 시간과 엄격 구분 |
| **NVMeVirt 공통 처리 / FTL 쓰기 경로 비용** | **미측정** | **미측정** | 정책 구간(`GC/SELECT/LEARN/REWARD/BUF`)만 실측, 공통 GC는 차감 추정 |


---

## 4. 원시 데이터 무결성 요약 (`final_experiment_validity.csv`)

- **총 추적 run 수**: `77`건 (**VALID `77`건**, **RUNNING(미검증) `0`건**, 무효 혼입 **0건**)
- 모든 VALID run은 원시 `summary.txt` ↔ `final-control.txt` ↔ 파티션 합산 2-경로 WAF 일치, `exit=0`, 커널 오류 `0`, FIO 오류 `0`, YCSB `SQLITE_FULL=0` (`≥99%`, 실측 `100%`) 및 사전등록 모듈 SHA256 대조를 독립 통과함.
- 상세 run별 표: [final_experiment_validity.csv](file:///C:/Users/oyeon/orca/iCAT-experiments/report/delivery-20261127/final_experiment_validity.csv)
- 상세 통계 대비 표: [final_statistical_audit.csv](file:///C:/Users/oyeon/orca/iCAT-experiments/report/delivery-20261127/final_statistical_audit.csv)
