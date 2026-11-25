# revE-20261125 사전 등록 (고컴: M2 후보 제거 같은 배치 검증 · M6 변화 감지 문턱 민감도)

- 작성: 2026-11-25 11:40경, 실행 전. 근거 지시: 사용자 11-25 "고컴 추가 실험 지시" 1·2번 (3번 판단 구간은 계획만 제출: `window_plan.md`).
- 호스트: 고컴 oy-B550M-DS3H (Ryzen 5 3600XT), 커널 7.0.0-31-generic. 러너, 부하, seed, 준비 절차는 revA·revB·revC와 같다.
- 시작 조건: revC 본 큐가 **정상 종료**한 뒤에만 자동 시작한다 (`queue-revE.sh`). 이상으로 멈췄으면 시작하지 않는다. 장치 잠금(`result/mix-20260911/device.lock`)은 revC와 같은 것을 쓴다.
- 승컴과의 관계:
  - 승컴 추가 ablation(abl-20261125)은 V4 / NoDiscount / 제거+정착+감지+probe 묶음 끔이다. Online Greedy는 greedy-online이다.
  - **NoElim 단독(정착·감지는 켬)과 감지 12.5 %는 승컴에서 하지 않는다.** 그래서 중복이 아니다.
  - 승컴 결과와 합치지 않는다.
  - revB의 `noelim`은 이번 것과 같은 모듈이다. 승컴의 "NoElim+NoSettle" 묶음과는 다른 정책이다.

## 1. 실험과 변수

| 실험 | 질문 | 비교군 | 대조군 | 바꾼 것 하나 |
|---|---|---|---|---|
| **M2 후보 제거** | 정착과 변화 감지를 켠 채 후보 제거만 끄면 WAF가 달라지는가 (revB noelim − revA V4 +0.094는 배치를 넘는 비교였고, revB 배치 연결 판정이 불합격이었다) | `revE-noelim` | `revE-v4` | 후보 제거 (ICAT_VARIANT 3 대 4) |
| **M6 감지 문턱** | 변화 감지 문턱 25 %를 12.5 %로 낮추면 WAF, 감지 시점, 재탐색 횟수, 재정착 시간, 탐색 비용이 어떻게 달라지는가 | `revE-drift12` | `revE-v4` | `WATGC_V2_DRIFT_Q16` 16384 → 8192 |

## 2. 모듈 (`modules.sha256`)

| 정책 | 모듈 | SHA256 | 근거 |
|---|---|---|---|
| revE-v4 | `buildoutput/nvmev-revC-v4.ko` (재사용) | df2be251… | revC-v4와 같은 파일. revB-v4와 기계어 차이 0줄 (revC 사전 등록 §2) |
| revE-noelim | `buildoutput/nvmev-revB-noelim.ko` (재사용) | b1663b47… | revB 사전 등록 해시와 같다. 코드: 제거 블록만 VARIANT 3에서 건너뛴다. 정착(VARIANT 2·9·5만 제외), 감지(VARIANT 1만 제외), probe는 켜져 있다 |
| revE-drift12 | `buildoutput/nvmev-revE-drift12.ko` (새 빌드) | f6a02e98… | revC-src, `ICAT_VARIANT=4 ICAT_EXTRA=-DWATGC_V2_DRIFT_Q16=8192ULL`, CPU 11 nice 19 -j1 (`build/build-revE-drift12.log`, revC 실행 중 11:3x에 빌드). revC-v4 대비 objdump 정규화 차이 1줄: `shl $0xe` → `shl $0xd` (감지 비교식의 ×16384 → ×8192). `build/objdump-drift12-vs-revC-v4.diff` |

- 12.5 %를 고른 근거: v1의 원래 값이다. v3에서 "잡음으로 발동했다"는 주석과 함께 25 %로 올렸지만, 측정 비교는 없었다 (`conv_ftl.h:75`).

## 3. 통제와 반복

- 부하: mixFYF = FIO-Fast 1800 s → YCSB-A (SQLite, 250k records, 1800 s) → FIO-Fast 1800 s. Table-3 준비. ext4 nodiscard, memmap 4G+8G, cpus=1,2, 파티션 4개
- seed: FIO hot/warm/cold = 20260910/20261010/20261110 + rep, icat_seed = 2026111400 + rep (revA–revC와 rep별로 같다. 같은 rep끼리 짝 비교를 할 수 있다)
- **반복 n=3** (rep 1–3). 같은 배치 안에서 V4 대조군도 새로 3회 돌린다. revC-v4를 대조군으로 재사용하지 않는다. revB 배치 연결 실패의 교훈이다.
- 순서: rep 블록마다 `random.Random(20261125 + rep)`로 섞었다 (`queue-order.registered.txt`).
  - rep1: v4, drift12, noelim
  - rep2: drift12, noelim, v4
  - rep3: drift12, v4, noelim
- 단기 실행 120 s: 세 정책 각 1회. 로드, 초기 arm 37, 4개 파티션 sample, 커널 오류 없음을 확인한다. 합산하지 않는다.
- 러너: `runner-revE.sh` = `runner-revC.sh` 사본. 정책 목록, 모듈 경로, icat_seed 전달 조건 `rev[ABCE]`, 표기만 바꿨다 (`port.diff`).
- 매 run 뒤 `check-run.py`를 돌린다. 확인 항목:
  - exit 0, 단계 완료, WAF 두 경로 일치
  - FIO 오류 0, YCSB 실패 ≤ 1 %이고 SQLITE_FULL 0
  - 커널 BUG/WARNING 0
  - NVMeVirt CPU 1·2 ≥ 95 %
- 하나라도 이상이면 큐를 멈추고 다음 run을 시작하지 않는다.
- 예상 시간: 단기 3 × 7.5분 + 본 9 × 91.5분 ≈ **14.1시간**. revC가 14:00에 끝나면 11-26 04:10경 끝난다.

## 4. 지표와 분석 (사전 고정)

**주 지표와 주 대비**
- 주 지표: 전체 WAF (1 + gc/host, summary와 파티션 합 두 경로)
- 주 대비 2개: noelim − v4, drift12 − v4
  - Welch 95 % CI
  - 같은 rep끼리 짝 비교 95 % CI (df 2)
  - Hedges g
- 판정: CI가 0을 포함하지 않으면 "차이 확인", 포함하면 "구분되지 않음". 동등성은 주장하지 않는다.
- 다중 비교: 주 대비 2개 × 지표 2개(전체, 단계 C)에 Holm 보정을 민감도 분석으로 함께 보고한다.

**보조 지표** (`analysis/final_revision/m6_adapt.py`, 정의는 revD 사전 등록 §3과 같고 사후에 바꾸지 않는다)
- 단계별 WAF
- 단계 B·C의 첫 감지 시점, 리셋 수, 복원 후보 수, 제거 횟수
- 재정착 시간 (리셋부터, 전환부터 두 가지)
- 재탐색 창 수, 탐색 창 host 비중
- 회복 시간 (한쪽 기준, 1.05, 5분 창, 10분 유지)
- 학습 경과 시간 (ktime, CPU 시간 아님)

**기타**
- 통계: n<3인 정책은 값만 적고 통계를 내지 않는다.
- 배치 연결 (판정에 쓰지 않음): revE-v4와 revA-v4, revC-v4의 차이를 기록한다.
- 분석: `analysis/revision_gocom/revE_analyze.py` → `result/revE-20261125-analysis/`. 매 run 뒤 자동 갱신한다.

## 5. 범위 밖

- 판단 구간 민감도는 계획만 세운다 (`window_plan.md`). 승인 후 별도 사전 등록한다.
- γ, c, 정착 조건은 이번에 하지 않는다.

## 실행 승인 기록
- 2026-11-25T11:35:19+09:00 사용자 승인: revC 정상 종료 뒤 자동 시작, 조건 변경 없음, 실패·무효 run을 임의로 제외하지 않음. 판단 구간 민감도(window_plan.md)는 승인되지 않음.
