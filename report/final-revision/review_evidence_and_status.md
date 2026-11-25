# 심사 의견별 답변 근거표 및 리비전 완료 현황 (고컴 작성, 2026-11-25 15:10)

- 이 문서는 진행 중인 실험이 끝날 때마다 갱신한다. (11-26 04:40 revE 반영)
  - revE: 11-26 04:07 종료, 9/9 유효
  - M1 자원 측정 m1-20261126: 11-26 04:09 시작, 11-28 20:00경 종료 예정
  - 승컴 abl: 9/9 유효, 고컴 검증 일치 (result/abl-20261125-verify/verify.md). greedy: 진행 중 (2/3)
- 모든 수치의 근거 경로는 이 브랜치(`report/data-validity-20261124`) 기준이다. 원시 데이터는 `result/<배치>/raw/`에 있고, 승컴 원시 데이터는 origin/main에 있다.
- 유효성 판정 기준
  - exit 0
  - 모듈 해시가 사전 등록값과 일치
  - YCSB 실패 ≤ 1 %, SQLITE_FULL 0
  - 커널·FIO 오류 0
  - WAF 두 경로 일치
  - 고컴 독립 재계산 (`analysis/online_greedy/og_audit.py`)

## 1. 심사 의견별 답변 근거표

| 심사 요구사항 | 실험 이름 (호스트, 배치) | 결과 파일 | 원시 근거 | 반복 수 | 유효성 | 논문 반영 여부 |
|---|---|---|---|---|---|---|
| **M1** 기존 학습 기반 GC(SmartGC)와 비교 | smartgc-20261119: SmartGC-EQ8, SmartGC 순위 목록, CAT-47, iCAT-v4. 승컴, mixY 20단계 10 h | `report/final-revision/M1_smartgc_comparison.md`, `result/final-revision-analysis/m1_*.csv` | `result/smartgc-20261119/`, `result/gc-20261010/mixY-*` | **정책당 1회** | 4/4 유효 (고컴 재계산 WAF 일치). 채널 모델 포화 경고가 4개 모두에 있어 지연 비교는 제외 | 반영: §6.3 표 9, §2.4, 참고문헌 [12] |
| **M2** 구성 요소 제거 실험 | revA V1 (감지 끔), V2 (제거·정착 끔). 고컴 | `report/final-revision/M4_statistics_final.md` §3 | `result/revA-20261114/raw/` | 3 | 6/6 유효 | 반영: §6.4 표 10 |
| | revD NoDrift, FullReset. 승컴 | `result/revD-20261124-verify/verify.md` | origin/main `result/revD-20261124/raw/` | 3 | 9/9 유효 (고컴 독립 검증, 승컴 값과 일치) | 반영: §6.4 표 10·11 |
| | **revE NoElim 단독** (정착·감지 켬, 같은 배치 V4 3회). 고컴 | `report/final-revision/revE_final.md`, `result/revE-20261125-analysis/` | `result/revE-20261125/raw/` | 3 | 9/9 유효. +0.091 [+0.030, +0.153], Holm p=0.091 | 반영: 표 10·11 배치 E |
| | 승컴 abl-20261125: NoDiscount, 제거+정착+감지+probe 묶음 끔 | `result/abl-20261125-verify/verify.md` | origin/main `result/revision-additional-ablation/raw/` | 3 | 9/9 유효, 고컴 재계산 일치. 묶음 끔 +0.124 (Holm 0.028), NoDiscount 구분 안 됨 | 반영: 표 10 배치 F |
| **M3** 온라인 기준선 비교 | revA Random Selection. 고컴 | `report/online-greedy-audit.md`, `M4_statistics_final.md` | `result/revA-20261114/raw/` | 3 | 6/6 유효 | 반영: §6.4 표 10 |
| | revC 원래 iCAT (온라인 학습 원 구현). 고컴 | `report/final-revision/revC_E2_E6_E7_final.md` | `result/revC-20261124/raw/mixFYF-online-*` | 3 | 3/3 유효 | 반영: §6.4 표 10·11 |
| | 승컴 greedy-20261125 Online Greedy (대조군 revD-v4) | `report/online-greedy-audit.md` (설계 감사) | origin/main `result/greedy-20261125/` (아직 없음) | 3 (대기) | 설계 6/7 PASS, 항목 7은 실행 후 확인 | 표 10에 【결과 대기】 행 |
| | Periodic Switching | — | — | 0 | **실행하지 않음** | 미반영. 논문에서 주장하지 않는다 |
| **M4** 반복과 통계 검증 | revA·revB·revC·revD 전체 재계산 | `report/final-revision/M4_statistics_final.md`, `M4_validity_data.md`, `result/final-revision-analysis/m4/*.csv` | 위 원시 디렉터리 44개 | 정책당 3 (revB V4·Arm60은 1) | 44/44 유효, 제외 0 | 반영: §6.4 (Welch CI, Holm 각주). revB n=1은 쓰지 않음 |
| **M5** 자원 효율 (메모리, CPU, 지연) | revA 지연·학습 경과 시간 (고컴), revC 추가, SmartGC 메모리 | `report/final-revision/M5_resource_comparison.md`, `result/final-revision-analysis/{cpu_overhead,latency_comparison,memory_overhead,m5_stats}.csv` | revA·revC 원시 로그, 모듈 DWARF | 3 | 유효 | 반영: §6.3, §7 "자원 비용". CPU 시간과 GC 수행 시간은 **미측정**이라고 명시 |
| **M6** 적응 성능, 파라미터 근거 | revA·revC·revD 적응 지표. revC 제거 문턱 10/15/25 %, 후보 45/60 | `report/final-revision/M6_adaptation_parameters.md`, `revC_E2_E6_E7_final.md`, `result/final-revision-analysis/{adaptation_*,parameter_sensitivity}.csv` | 커널 로그 (`kernel*.log`, `kernel-snapshots/`) | 3 | 유효 | 반영: §6.4 표 10·11, 한계 4 |
| | **revE 감지 문턱 12.5 %**. 고컴 | `report/final-revision/revE_final.md` | `result/revE-20261125/raw/` | 3 | 유효. +0.072 [+0.012, +0.132], Holm p=0.091 | 반영: 표 10·11 배치 E |
| | 판단 구간 512 MiB 민감도 | `result/revE-20261125/window_plan.md` (계획만) | — | 0 | **승인 안 됨, 실행 안 함** | 한계 4에 "미측정 경험적 설정"으로 명시 |
| **M7** 환경 일반화 | 실험 없음. 실행 모듈 설정 정리 | `report/final-revision/M7_scope_and_limitations.md` | `revC-src/ssd_config.h`, 러너, `environment.txt` | — | — | 반영: §7 "적용 범위", 한계 5 |

## 2. 리비전 완료 현황표

- **실험 완료**: 계획한 실행이 모두 끝났다.
- **데이터 검증 완료**: 고컴이 원시 로그에서 독립적으로 다시 계산했다.
- **논문 반영 완료**: `PAPER_KCI_DRAFT.md`에 수치가 들어갔다.
- **심사 답변 완료**: 아래 §3의 답변 초안이 있다. 제출은 사용자가 결정한다.

| 요구사항 | 실험 완료 | 데이터 검증 완료 | 논문 반영 완료 | 심사 답변 완료 | 남은 일 |
|---|---|---|---|---|---|
| M1 SmartGC | △ WAF n=1 완료. 자원 측정·3회 반복(m1-20261126) 진행 중 | ✔ (n=1분) | △ n=1분 | 초안 △ | m1-20261126 종료 후 표 9와 자원 비교 갱신 |
| M2 구성 요소 | ✔ V1·V2·NoDrift·FullReset·NoElim·NoDiscount·묶음 끔 | ✔ | ✔ | 초안 ✔ | 정착·탐색(probe) 단독 효과는 분리 측정하지 않음 |
| M3 온라인 기준선 | △ Random·원래 iCAT 완료. Greedy 대기. Periodic 안 함 | △ | △ | 초안 △ | 승컴 greedy 검증 후 표 10 갱신 |
| M4 통계 | ✔ (진행 중 배치 제외) | ✔ 53/53 (revE 포함) | ✔ | 초안 ✔ | abl, greedy 추가 |
| M5 자원 | ✔ (기존 로그) | ✔ | ✔ | 초안 ✔ | CPU 시간과 GC 시간은 측정 불가로 명시 (새 계측 빌드 없이는 불가) |
| M6 적응·파라미터 | △ 제거 문턱, 후보 수, 리셋 범위, 감지 12.5 % 완료. 판단 구간은 미승인 | ✔ | ✔ | 초안 ✔ | 판단 구간 등 4개는 미측정으로 명시 |
| M7 일반화 | 해당 없음 (실험 없이 범위 명시) | ✔ (설정값 확인) | ✔ | 초안 ✔ | — |

## 3. 심사 답변 초안 (요지)

- **M1.** 원저자 코드가 공개되지 않아 SmartGC를 논문 기술대로 재구현했다. 같은 20단계 10시간 전환 부하로 비교했다(정책당 1회).
  - iCAT-v4의 WAF_nand는 SmartGC-EQ8보다 28.5 % 낮았다.
  - 학습 상태 메모리는 약 1/193이다.
  - 1회 실행이라 통계적 우열은 주장하지 않는다. 지연은 에뮬레이터 채널 모델 포화로 비교에서 뺐다 (§6.3).
- **M2.** 같은 배치에서 각 3회 반복한 제거 실험을 추가했다 (표 10).
  - 실행 중 제거와 수렴 후 탐색 중단을 함께 끄면 WAF가 6.4 % 높아졌다.
  - 부분 재설정 대신 전체 재설정을 쓰면 단계 3 WAF가 0.130 높아졌다. 다중 비교 보정 후에는 경계에 있다.
  - 변화 감지를 끈 변형과는 두 배치 모두 구분되지 않았다. 이 결과를 그대로 보고한다.
  - 정착·감지를 켠 채 실행 중 제거만 끄면 WAF가 4.3 % 높아졌다 (Welch CI가 0 제외, Holm 보정 후 p=0.091).
- **M3.** 매 판단 구간 무작위 선택보다 WAF가 8.4 % 낮았고, 원래 iCAT 구현보다 11.5 % 낮았다 (각 3회, CI가 0 제외).
  - Online Greedy는 【승컴 결과 대기】.
  - 주기적 전환 기준선은 측정하지 않았다.
- **M4.** 44회 실행을 원시 카운터에서 다시 계산했다. 모든 판정은 같은 배치 안에서 Welch 95 % CI로 했다.
  - 다중 비교 보정(Holm)은 민감도 분석으로 함께 보고했다.
  - 서로 다른 호스트와 배치의 결과는 합치지 않았다.
- **M5.**
  - 학습 상태: 10,112 B [계산]
  - 결정 경로 경과 시간: 90분에 3.88 ms (커널 ktime, CPU 시간 아님)
  - FIO p99는 무작위 선택보다 15–20 µs 높았다. WAF 감소가 꼬리 지연 개선으로 이어진다고 주장하지 않는다.
  - CPU 사용 시간과 GC 수행 시간은 측정하지 않았다고 명시했다.
- **M6.**
  - 변화 감지: 단계 전환 후 61–63 s에 감지했다 (세 배치)
  - 재수렴: 340–500 s
  - 복원 후보: 13–17개
  - 제거 임계값 10–25 %와 후보 수 45/60은 WAF가 구분되지 않았다.
  - 판단 구간, UCB 계수, 수렴 조건, 할인 계수는 측정하지 않은 경험적 설정으로 명시했다.
  - 감지 임계값을 12.5 %로 낮추면 WAF가 3.4 % 높아졌다 (Holm 보정 후 p=0.091). 측정한 값은 12.5 %와 25 % 둘뿐이라 최적값은 주장하지 않는다.
- **M7.** 단일 에뮬레이터 구성(MLC, 8 GiB, OP 7 %, erase 지연 0)의 결과임을 §7과 한계 5에 명시했다. 실제 SSD와 다른 용량·OP는 향후 과제로 남긴다.
