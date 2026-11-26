# 실험 목록 (고컴, 2026-11-27)

- 통합 Excel: `report/final-revision/iCAT_Complete_Experiment_Results.xlsx`
- 생성 스크립트: `analysis/final_revision/complete_results.py`
- 검사 스크립트: `analysis/final_revision/check_complete_xlsx.py`
- 승컴 원시 자료: origin/main 4689c6797을 git archive로 읽기만 했다.
- 모든 run의 WAF를 원시 카운터에서 다시 계산했다. mixFYF run 78개가 모두 유효하고, 기존 게시값과도 모두 일치한다.
- 부하
  - mixFYF: FIO-Fast 1800 s → YCSB-A(SQLite 250k) 1800 s → FIO-Fast 1800 s
  - mixY: 20단계 × 1800 s (FIO-Fast / FIO-Slow / Varmail)
- 호스트
  - 고컴: AMD Ryzen 5 3600XT, oy-B550M-DS3H
  - 승컴: Intel i7-7700, oy-System-Product-Name
  - 호스트나 배치가 다른 결과는 합치지 않았다.

## 1. 리비전 실험

| 배치 | 호스트 | 심사 의견 | 정책 (run 수) | 부하 | 유효 | Excel 시트 | 원시 경로 |
|---|---|---|---|---|---|---|---|
| revA-20261114 | 고컴 | M2·M3 | V4 3, V1 3, V2 3, Random 3, 고정 Arm 47 1 | mixFYF | 13/13 | Random Selection, Ablation Study, Arm 47 | `result/revA-20261114/raw/` |
| revB-20261122 | 고컴 | M2 | V4 1, NoElim 3, NoSettle 3, 60 arms 1 | mixFYF | 8/8 | Ablation Study (대조군 n=1이라 통계 없음) | `result/revB-20261122/raw/` |
| revC-20261124 | 고컴 | M3·M6 | V4, 제거 10 %, 제거 25 %, 60 arms, 원래 iCAT (각 3) | mixFYF | 15/15 | Ablation Study, Online Greedy | `result/revC-20261124/raw/` |
| revD-20261124 | 승컴 | M2 | V4, NoDrift, FullReset (각 3) | mixFYF | 9/9 | Ablation Study, Drift Threshold | origin/main `result/revD-20261124/raw/` |
| revE-20261125 | 고컴 | M2·M6 | V4, NoElim, 감지 12.5 % (각 3) | mixFYF | 9/9 | Ablation Study, Drift Threshold | `result/revE-20261125/raw/` |
| abl-20261125 | 승컴 | M2 | V4, NoDiscount, 묶음 끔 (각 3) | mixFYF | 9/9 | Ablation Study | origin/main `result/revision-additional-ablation/raw/` |
| greedy-20261125 | 승컴 | M3 | Online Greedy 3 (대조군은 다른 배치) | mixFYF | 3/3 | Online Greedy | origin/main `result/greedy-20261125/raw/` |
| batchG-20261126 | 승컴 | M3·M6 | V4, Greedy GC, 감지 50 % (각 3) | mixFYF | 9/9 | Greedy GC, Drift Threshold | origin/main `result/{batchG,greedygc,drift50}-20261126/raw/` |
| arm47-20261127 | 승컴 | Robustness | 고정 Arm 47 3 | mixFYF | 3/3 | Arm 47 Robustness | origin/main `result/arm47-20261127/raw/` |
| smartgc-20261119, gc-20261010 | 승컴 | M1 | SmartGC-EQ8, SmartGC, CAT-47, iCAT-v4 (각 1) | mixY 10 h | 4/4 | SmartGC Comparison | `result/smartgc-20261119/resume/`, `result/gc-20261010/` |
| gocom-sg-20261119 | 고컴 | M1 보조 | SmartGC, SmartGC-Q, Greedy, Arm 47 (각 1) | mixY | exit 0 4/4 | SmartGC Comparison | `result/gocom-sg-20261119/` |
| m1-20261126 | 고컴 | M1·M5 | iCAT-v4, SmartGC-EQ8 (구간 타이머 빌드, 각 1) | mixY 10 h | 2/2 (4회는 CANCELLED, 실패 아님) | Memory Overhead, CPU and Timing | `/home/oy/iCAT/result/m1-20261126/raw/` (요약 `result/m1-20261126-final/`) |
| bench (sim) | 고컴 | M1 CPU 대체 | icat, smartgc-eq8 (각 seed 3) | 사용자 공간 sim (mixY 아님) | 6/6 | CPU and Timing | `analysis/bench_summary.tsv` |
| secondary-metrics-20261126 | 승컴 (기존 로그 재분석) | M3·M6 보조 | revD-v4, abl-*, greedy | — | 15/15 | Secondary Metrics | origin/main `result/secondary-metrics-20261126/` |

- smoke120 run은 사전 등록상 통계 대상이 아니다. 목록은 Run Validity 시트에 있다.

## 2. 원 논문 Figure 1~10

- 상태는 `report/final-e1-validation/paper_data_validity_matrix.md`를 따랐다. Excel의 Experiment Inventory 시트에도 같은 표가 있다.
- 이 Excel은 원 논문 Figure의 수치를 다시 만들지 않았다.
- 그림 7·8·9와 그림 10(표 8)은 YCSB 오염 때문에 일부만 유효하다. 그림 10은 리비전 mixFYF 실험으로 대체되었다.

## 3. 요청 목록과 실제 대응

| 요청 항목 | 대응 |
|---|---|
| revA–revE | 위 표 |
| Random Selection | revA |
| Ablation Study | revA, revB, revC, revD, revE, abl |
| NoDiscount | abl |
| NoElim | revB (대조군 n=1), revE (같은 배치 n=3) |
| Online Greedy | greedy-20261125 |
| Greedy GC | batchG greedygc |
| SmartGC, SmartGC-EQ8 | smartgc-20261119, gc-20261010, gocom-sg-20261119, m1-20261126 |
| drift12 | revE |
| drift50 | batchG |
| Arm 47 | arm47-20261127 (승컴), revA (고컴 n=1) |
| M1 자원 오버헤드 | m1-20261126 |
| secondary metrics | 고컴 재계산(단계 C 첫 5분 WAF), 승컴 secondary-metrics-20261126, 고컴 F5/F6 |
| batchG 분석 | 고컴 검증 `result/batchG-20261126-verify/` |

## 4. 누락 실험 (실행되지 않음)

- **감지 문턱 15 %**: 실행한 적이 없다.
  - 측정한 감지 수준은 12.5 %, 25 %(기본값), 50 %다.
  - 15 %는 후보 제거 문턱의 기본값이다. 제거 문턱은 revC에서 10/15/25 %로 측정했다.
- **Periodic Switching (M3)**: 실행하지 않았다.
- **판단 구간 512 MiB 민감도, UCB 계수, 수렴 조건, 할인 계수 수준별 실험 (M6)**: 실행하지 않았다. 판단 구간 실험은 승인되지 않았다.
- **M1 정책당 3회 반복**: 사용자 결정으로 1회만 했다. 4회는 CANCELLED이고 실패가 아니다.
- **같은 배치에서 Arm 47 − V4 비교**: 승컴이 제안했지만(V4 ×3, 약 4.7 h) 승인되지 않았다.
- **revB의 V4와 60 arms**: n=1이다. 60 arms는 revC에서 n=3으로 다시 측정했다.
