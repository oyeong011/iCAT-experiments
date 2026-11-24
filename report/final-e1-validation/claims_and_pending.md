# 유효한 주장, 사용 불가 주장, E1 미완료 실험 (고컴, 2026-11-24)

- 수치는 모두 원시 로그를 다시 계산한 값이다.
- 통계 해석과 적용 범위는 기존 검증 문서를 따른다:
  - `report/revision-20261123-gocom/random_v4_statistical_audit.md`
  - `ablation_validation.md`
  - `resource_overhead_final.md`
  - `cat47_baseline_audit.md`
- 이 문서는 범위를 넓히지 않는다.

## 1. 유효한 주장 (기존 검증값 유지)

| 주장 | 값 | 범위와 한계 | 근거 |
|---|---|---|---|
| Random보다 V4의 WAF가 낮다 | Random − V4 = **+0.196 [0.184, 0.208]**, 8.43 % | mixFYF 한 부하, 고컴 호스트, n=3:3. 다른 부하로 일반화하지 않는다 | `recheck_gocom_effects.csv`, `random_v4_statistical_audit.md` |
| 후보 제거가 WAF를 낮춘다 | NoElim − V4 = **+0.094 [0.071, 0.117]** | mixFYF, n=3:3 | 같은 파일, `ablation_validation.md` |
| SmartGC보다 WAF가 낮다 (mixY) | WAF_nand 3.211 대 4.492(EQ8) | 각 n=1. 비교에 쓴 16개 run은 YCSB를 쓰지 않았고, 모두 정상 완료됐다. 원래 SmartGC 실행은 호스트 디스크 부족으로 실패해 제외했다 | `recheck_smartgc_runs.csv` |
| 학습 CPU와 메모리 오버헤드가 작다 | 결정 경로 3.88 ± 0.11 ms / 90분, 학습 전용 10,112 B (계산값) | FIO만 사용. SmartGC CPU는 측정하지 않았다 | `resource_overhead_final.md` |
| CAT-47 기준선 (mixY) | 11월 3.233을 쓴다. 10월 2.864는 10-10 run 하나의 이상치다 | n=1. 원인은 미확인이다 | `cat47_baseline_audit.md` §5 |
| 3배 전환 워크로드에서 v4 대 CAT-Robust | 유효 8종 중 3종 우수(−1.1 ~ −5.3 %), 5종 열세(+3.2 ~ +4.9 %) | v4는 1~3회, CAT-Robust는 1회. 유의성 없음 | `figs/paper_fig_numbers.json` |
| 3배 전환 워크로드에서 v4 대 CAT-Default | 유효 3종 모두 낮음(−4.3 ~ −18.3 %) | 3종뿐이다 | 같은 계산 |
| 견고성 (유효 6종) | 평균 CAT-Best 0.2, v4 5.0, Robust 5.0 %. 최댓값 1.3 / 15.2 / 20.2 % | 기준 조합 2~7개 | `paper_fig_numbers.json` |
| 표 6 (O, F, P) | OLTP → Varmail에서 v4가 1/7, 나머지 2종은 2/7 | 고정 조합은 1회 측정 | `tables/table6_valid.md` |
| 단일 FIO 결과 (그림 1–6, 표 4·5) | 원고 값 | YCSB를 쓰지 않는다 | — |
| SQLite 단독 순위 (arm 47 상위) | `rank-sqlite-a.txt` | 87개 run, YCSB 실패 0 % | `recheck_sqlite_single.csv` |

## 2. 사용 불가 주장

| 주장 (원래) | 이유 | 대체 |
|---|---|---|
| 3단계 균등 전환에서 학습기는 단계 2에서 우수하고 v4는 단계 3에서 빠르게 복귀한다 (표 8, 그림 10) | mixR 9월 11개 run 모두 YCSB SQLITE_FULL(READ 99.83 % 또는 UPDATE 9.98 % 실패) | E1 재실험(300k). 정책 구성이 달라 원래 표는 복원할 수 없다 |
| iCAT(v1)·v4가 3단계 균등 전환에서 CAT-Default보다 낮다(2.288 대 2.410, −13.7 %) | 같은 이유 | 없음 |
| 3배 전환 13종 중 4종 우수, 9종 열세 | 무효 5종(A, B, G, H, J) 포함 | 유효 8종: 3 우수, 5 열세 |
| 견고성: v4 최댓값이 CAT-Best보다 작다(15.2 대 17.0) | CAT-Best 17.0 %는 YCSB-A → YCSB-B(무효)에서 나온 값 | 유효 6종에서는 CAT-Best가 최소(1.3 %) |
| 표 6의 YCSB-A → YCSB-B 행(v4 2/7) | mixJ YCSB 실패 | 행 삭제 |
| 이웃 탐색과 부분 초기화가 워크로드 복귀 시 특히 효과적이다 | 근거가 3단계 균등 전환 | E1 재실험 결과로 다시 판단 |
| 구간 지정 계측에서 고정 조합 반복 차이가 0.1 % 이내(arm 50: 2.074, 2.073) | 근거가 mixR 전체 WAF | 재확인 필요 |
| 1배 길이 전환 14종에서 순서 성립 | 무효 5종 포함. 유효 17종 중 4종은 오염과 무관하게 순서가 성립하지 않는다 | 유효 17종 중 13종 |
| 변화 감지(drift)와 재탐색 범위 효과 (11-23 E1) | 11-23 E1 YCSB 실패 | E1 재실험 |
| 승컴 Random 고정 기댓값 (mixA) | mixA YCSB 실패 | mixC만 유효 |
| 9월 mixA·B·H·J 관련 모든 수치(RESULTS_ALL, V4_VS_CAT 등) | YCSB 실패 | 재측정 계획 없음 |
| FIO-Fast ∥ YCSB-A(mixG) 수치 | YCSB 출력 파일이 0바이트라 검증할 수 없다 | 재측정 계획 없음 |

## 3. E1 미완료 실험

| 실험 | 상태 (11-24 14:30) | 필요한 것 | 비고 |
|---|---|---|---|
| 재실험 사전 검증 run (`result/revision-20261124/validation`) | main에 결과 없음 | `verdict.txt`: exit=0, sqlite_full=0, 적재 300k/300k, run 42M/42M | 승컴 큐는 검증 통과 뒤에만 시작한다 |
| mixR×3 v4 rep1–3 (300k) | 대기 | 유효 3회 | 고컴 감시 작업이 push되면 `e1_analyze.py`를 바로 실행한다 |
| mixR×3 v4nodrift rep1–3 (300k) | 대기 | 유효 3회 | drift 효과(C 단계 WAF) |
| mixR×3 v4fullreset rep1–3 (300k) | 대기 | 유효 3회 | 재탐색 범위 효과 |
| fixed47 mixR (300k) | **재실험 큐에 없음** (`script/revision-rerun-20261124.sh`) | 필요하면 추가 | 11-23 큐에는 있었다 |
| 원래 표 8 정책(CAT-Best, CAT-Robust, arm 17, iCAT, iCAT-v3, CAT-Default) 300k | **계획 없음** | 표 8을 원래 형태로 쓰려면 필요 | — |
| 9월 YCSB 전환 5종(mixA, B, G, H, J) 재측정 | **계획 없음** | 그림 7을 13종으로 되돌리려면 필요 | — |

**분석 규칙 (`analysis/final_e1/e1_analyze.py`):**
- 300k와 600k를 섞지 않는다. 배치 라벨은 결과 디렉터리와 실제 적재 수(`…/rec300k`)로 정한다. 섞이면 계산을 멈춘다.
- YCSB 실패가 1 %를 넘거나 `SQLITE_FULL`이 한 번이라도 나온 run은 YCSB 단계부터 무효다.
- 정책별 유효 3회가 모이기 전에는 통계를 내지 않는다("n<3: 통계 없음").
- Welch CI는 양쪽 모두 n ≥ 3일 때만 계산한다.
- 승컴 보고서가 올라오면 이 독립 계산값과 대조한다. 대조 결과는 이 문서에 추가한다.
