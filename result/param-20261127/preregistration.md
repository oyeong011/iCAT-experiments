# param-20261127 사전 등록: γ·C 민감도 (승컴, 설정당 3회)

- 작성: 2026-11-27, 실행 전.
- 지시 (사용자, 2026-11-27): "파라미터 민감도 실험을 승컴에서 모두 수행하라"
  - γ 0.90 / 0.95 / 0.99 각 3회, C 0.50 / 0.75 각 3회
  - 대조군(γ 0.9995, C 0.25)은 기존 3회 결과를 재활용한다 → 신규 15회
  - 후보 제거 문턱 실험과 메모리 실험은 다시 돌리지 않는다.
- 이 지시는 직전 지시("승컴은 중복 실행하지 않는다", 고컴 revF n=1)를 대체해요.
- 고컴 revF와 이 배치는 호스트가 달라서 **결과를 합치지 않아요.**

## 1. 정책

| 정책 | 모듈 | sha256 앞 16자 | 빌드 (paramF-src, `ICAT_VARIANT=4`) | γ (Q16) | C (Q16) |
|---|---|---|---|---|---|
| pf-g99 | `buildoutput/nvmev-pf-g99.ko` | 3579149ed280c652 | `ICAT_EXTRA=-DWATGC_V2_GAMMA_Q16=64881ULL` | 0.99 (64881) | 0.25 (16384) |
| pf-g95 | `buildoutput/nvmev-pf-g95.ko` | 9201e6383024cede | `-DWATGC_V2_GAMMA_Q16=62259ULL` | 0.95 (62259) | 0.25 |
| pf-g90 | `buildoutput/nvmev-pf-g90.ko` | 171378e3664d487c | `-DWATGC_V2_GAMMA_Q16=58982ULL` | 0.90 (58982) | 0.25 |
| pf-c050 | `buildoutput/nvmev-pf-c050.ko` | acc93d72294d577a | `-DWATGC_V2_UCB_C_Q16=32768ULL` | 0.9995 (65503) | 0.50 (32768) |
| pf-c075 | `buildoutput/nvmev-pf-c075.ko` | cfc02069b52f76f2 | `-DWATGC_V2_UCB_C_Q16=49152ULL` | 0.9995 | 0.75 (49152) |

- Q16 값은 고컴 revF와 같게 정했어요 (반올림).
- **paramF-src** = `revD-src` 사본이에요. 차이는 `conv_ftl.h`에서 `WATGC_V2_UCB_C_Q16` 정의를 `#ifndef … #endif`로 감싼 2줄뿐이에요 (`diff -r`). `revD-src`는 바꾸지 않았어요.
- **기계어 확인** (`build/objdump-pf-*-vs-revD-v4.diff`, 주소와 원시 바이트를 지우고 정규화)
  - 옵션 없이 빌드한 모듈(`pf-defaultcheck`, 설치하지 않음)은 실행된 V4 모듈(`nvmev-revD-v4.ko` = `abl-v4` = `bg-v4`)과 **0줄 차이**예요. 소스 변경은 기본 동작을 바꾸지 않아요.
  - g99 / g95 / g90: 할인 상수만 바뀌어요. 0xffdf → 0xfd71 / 0xf333 / 0xe666이고, `push` 1줄과 `imul` 6줄이에요 (각 14줄).
  - c050: `push $0x4000→$0x8000`, `shl $0xe→$0xf`만 바뀌어요 (4줄).
  - c075: `push $0x4000→$0xc000`, `shl $0xe` → `imul $0xc000`이 바뀌고, 나머지는 정렬 nop과 명령 순서 1개예요 (9줄).
- 빌드는 측정이 없을 때 `taskset -c 0 nice -n 19 make -j1`로 했어요. 로그는 `build/build-pf-*.log`에 있어요.

## 2. 대조군 (재활용, 신규 실행 없음)

- **bg-v4** (batchG-20261126, 승컴, 3회, 2026-11-26)을 대조군으로 써요.
  - 이 배치 직전의 승컴 V4 배치예요.
  - 모듈(b35775057f2e7dc6…), 러너, seed 규칙이 이 배치와 같아요.
  - Greedy GC와 drift50 비교에도 쓴 대조군이에요.
- **주의: 같은 배치 대조군이 아니에요.**
  - 그래서 비교는 "다른 배치 대조군 대비"로 표시하고, 직접(같은 배치) 비교와 구분해요.
  - 참고로 승컴 V4의 배치 간 재현성은 revD, abl, batchG 사이 |Δ| ≤ 0.029였고 모두 유의하지 않았어요.
  - 다른 V4 배치(revD-v4, abl-v4)는 참고 범위로만 적고 합치지 않아요.

## 3. 조건 (batchG와 같음)

- 부하: mixFYF = FIO-Fast(test4) 1800 s → YCSB-A (SQLite 250,000 records, load + run 1800 s) → FIO-Fast 1800 s
- 장치: 8 GiB (memmap 4G + 8192M), cpus=1,2, measurement_manual
- 초기화: mkfs, mount nodiscard → Table-3 준비 (randseed 20260907) → 카운터 0 확인
- seed: rep r → FIO hot/warm/cold = 20260910+r / 20261010+r / 20261110+r, icat_seed = 2026111400+r. bg-v4와 같아요.
- 후보 공간 45개, 초기 arm 37, 후보 제거 문턱 15 %, 변화 감지 25 %. 판단 구간, 정착, probe 상수도 V4와 같아요.
- 러너: `runner-param.sh` = `runner-batchG.sh`에서 배치 경로, 정책 목록, 모듈 분기만 바꿨어요 (`port.diff`).

## 4. 실행 순서 (사전 등록, 바꾸지 않음)

- 단기 실행(120 s): 5개 정책 (정렬 순서). check-run과 param-check를 통과해야 본 실행을 시작해요.
- 본 실행: `queue-order.registered.txt`. 반복마다 `random.Random(20261127 + rep).shuffle`로 정했어요.
- 각 run 뒤 검사
  - `check-run.py`: exit, 단계, WAF 두 경로, YCSB, FIO 오류, 커널 오류
  - `param-check.py`: 측정 시작 init 줄 4개의 `gamma_q16`, `exploration_q16`, VARIANT 4, 후보 45개
  - 이상이 있으면 큐를 멈춰요.
- 실패하거나 무효인 run은 제외하지 않고 원인을 기록해요.
- 예상 소요: run당 약 1.5시간 × 15 + 단기 실행 5개 ≈ 24시간

## 5. 보고할 값

- 반복별 WAF (전체, 단계 A/B/C, 단계 C 첫 5분), 평균, SD, 95 % CI (t, df=2)
- 대조군(bg-v4) 대비: 차이, 95 % CI, Welch p, 같은 seed 쌍 검정
  - Holm 가족: 5개 대비 × {전체, 단계 C} = 10
- 학습 지표
  - 선택 변경 수, 탐색 구간 수, 후보 제거 횟수 (횟수예요. 비율이 아니에요)
  - 첫 정착 때 남은 후보 수
  - 첫 정착 시간
  - 리셋 수와 재정착 비용
- 해석 원칙
  - 유의하지 않은 차이를 우열로 쓰지 않아요.
  - "최적 γ/C"라고 주장하지 않아요.
  - C는 UCB 보너스의 크기(WAF 단위)이고, 무작위 선택 확률이 아니에요.

## 6. 수정 (2026-11-27 16:38, 실행 중 결정 — `host-assignment.md`)

- 파라미터 그룹 단위로 호스트를 나눴어요. **승컴은 C 그룹(pf-c050, pf-c075 각 3회)만** 실행해요.
  - γ 그룹은 고컴 revF가 맡아요.
  - pf-g99/g95/g90 모듈은 빌드했지만 실행하지 않아요.
- C 0.25 대조군은 bg-v4(3회)예요. Holm 가족은 2대비 × {전체, 단계 C} = 4로 바뀌어요.
- 실행 순서: `queue-order.v2-Cgroup.txt` (사전 등록 순서에서 C 줄만 남김), 큐는 `queue-v2.sh`예요.
