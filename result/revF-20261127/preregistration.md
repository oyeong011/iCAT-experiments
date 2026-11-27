# revF-20261127 사전 등록: 할인 계수 γ와 탐색 계수 C 민감도 (고컴, 정책당 1회)

- 작성: 2026-11-27, 실행 전.
- 지시 (사용자, 2026-11-27)
  - "C가 이제 0.75 0.5 0.25 그리고 0.99 0.95 0.90"
  - "시간 없으니까 각 1회만 진행하자"
- 심사 요구사항: M6 파라미터 근거. 이전 리비전 배치에서는 γ 0.9995/1.0과 C 0.25만 측정했다.
- **정책당 n=1이다. 평균, CI, 검정, 우열 판정을 하지 않는다.** 값만 보고하고 "1회 실행"으로 표시한다.

## 1. 정책

| 정책 | 모듈 | sha256 앞 16자 | 빌드 | γ | C |
|---|---|---|---|---|---|
| revF-v4 (같은 배치 대조군) | `buildoutput/nvmev-revC-v4.ko` (revC·revE 대조군과 같은 파일) | df2be25144d186ee | 기존 | 0.9995 (Q16 65503) | 0.25 (Q16 16384) |
| revF-g99 | `buildoutput/nvmev-revF-g99.ko` | 8a3366e90fc5b8d6 | revF-src, `ICAT_VARIANT=4 ICAT_EXTRA=-DWATGC_V2_GAMMA_Q16=64881ULL` | 0.99 | 0.25 |
| revF-g95 | `buildoutput/nvmev-revF-g95.ko` | d7894034815d3cf7 | `-DWATGC_V2_GAMMA_Q16=62259ULL` | 0.95 | 0.25 |
| revF-g90 | `buildoutput/nvmev-revF-g90.ko` | 053392f3d51dbfbe | `-DWATGC_V2_GAMMA_Q16=58982ULL` | 0.90 | 0.25 |
| revF-c050 | `buildoutput/nvmev-revF-c050.ko` | b77f6caa7c5a866d | `-DWATGC_V2_UCB_C_Q16=32768ULL` | 0.9995 | 0.50 |
| revF-c075 | `buildoutput/nvmev-revF-c075.ko` | d7b8109ef4788632 | `-DWATGC_V2_UCB_C_Q16=49152ULL` | 0.9995 | 0.75 |

- C 0.25 수준은 대조군 revF-v4가 맡는다.
- **revF-src** = `revC-src` 사본에 `conv_ftl.h`의 `WATGC_V2_UCB_C_Q16` 정의를 `#ifndef … #endif`로 감싼 3줄만 더했다 (γ, 제거 문턱, 감지 문턱과 같은 방식). 다른 차이는 없다 (`diff -r`).
- 빌드: `taskset -c 11 nice -n 19 make -j1`, 측정이 없을 때 했다. 로그는 `build/build-*.log`에 있다.
- 기계어 확인: `build/objdump-*-vs-revC-v4.diff`. 정규화는 주소와 원시 바이트를 지우고 명령어만 남긴 것이다.
  - 방법 검증: 기존 drift12와 revC-v4는 2줄 차이로 재현된다 (revE 기록과 같음).
  - revF-src를 옵션 없이 빌드한 모듈 (`nvmev-revF-defaultcheck.ko`, 08ffdbfd…)은 revC-v4와 **차이 0줄**이다. 소스 변경은 기본 동작을 바꾸지 않는다.
  - g99, g95, g90은 할인 상수만 바뀐다: 0xffdf → 0xfd71 / 0xf333 / 0xe666 (push 1줄, imul 6줄).
  - c050은 C 상수 0x4000 → 0x8000과 `shl $0xe` → `shl $0xf`만 바뀐다.
  - c075는 C 상수 0x4000 → 0xc000이다. ×49152는 shift로 할 수 없어 `imul` 1줄로 바뀐다. 그래서 분기 주소가 밀린다.
    - 분기 대상을 정규화한 diff에서는 상수, 곱셈, 명령 순서 1개, 정렬 nop만 다르다 (`objdump-c075-vs-revC-v4.targets-normalized.diff`).
- 반감기 (판단 구간 기준, 계산): γ 0.9995 ≈ 1,386; 0.99 ≈ 69; 0.95 ≈ 13.5; 0.90 ≈ 6.6. 한 run에서 파티션당 판단 구간은 약 250개다.

## 2. 조건 (revC·revE와 같음)

- 부하: mixFYF = FIO-Fast(test4) 1800 s → YCSB-A (SQLite 250,000 records, load + run 1800 s) → FIO-Fast 1800 s
- 초기화: insmod (memmap 4G+8G, cpus=1,2, measurement_manual) → mkfs, mount nodiscard → Table-3 준비 (randseed 20260907) → 카운터 0 확인
- seed: rep 1. FIO hot/warm/cold = 20260911 / 20261011 / 20261111, icat_seed = 2026111401 (run-one.sh 규칙 그대로)
- 러너: `runner-revF.sh` = `runner-revE.sh`에서 배치 경로, 정책 목록, 모듈 분기만 바꿨다 (`port.diff`)
- 안전: `safety-env.sh`가 insmod 모듈 해시, 가상 장치(nvme1n1)만 허용한다. 물리 nvme0n1에는 쓰지 않는다.

## 3. 실행 순서 (사전 등록, 바꾸지 않음)

- 단기 실행(120 s): 새 모듈 5개를 g90, c075, g99, g95, c050 순서로 돌린다. revF-v4는 이미 확인된 revC-v4.ko라 생략한다.
- 본 실행: `queue-order.registered.txt`. `random.Random(20261127).shuffle`로 정했다.
  1. revF-g90
  2. revF-c075
  3. revF-g99
  4. revF-g95
  5. revF-c050
  6. revF-v4
- 각 run 뒤 `check-run.py`가 다음을 검사한다. 이상이 있으면 큐를 멈추고 다음 run을 시작하지 않는다.
  - exit, 단계 누락, WAF 두 경로, YCSB 유효성, FIO 오류, 커널 오류, NVMeVirt CPU
  - 이번 배치 추가: 커널 init 줄의 γ, C, VARIANT가 위 표와 같고 4개 파티션 모두에 있는지
- 실패하거나 무효인 run은 제외하지 않고 원인을 기록한다. 재실행은 사용자 승인 후에만 한다.

## 4. 보고할 값 (n=1, 통계 없음)

- WAF: 전체, 단계 A/B/C, 단계 C 첫 5분
- 대조군과의 차이: 단순 차이와 비율. **판정하지 않는다.** 참고 기준으로 기존 iCAT-v4의 반복 간 범위를 함께 적는다.
  - 기존 범위 (고컴): revA SD 0.005, revC 0.029, revE 0.026
- 학습 지표 (커널 로그)
  - 탐색 횟수 (eval_explore), 선택 수, 재설정 수
  - 단계 A 끝과 종료 시 남은 후보 수
  - 첫 정착 시간
  - 단계 C 감지·복원·재정착 시간, 탐색 조합이 처리한 쓰기 비중
  - 학습 ktime (CPU 시간 아님)
- 해석 금지
  - "최적 γ / C"
  - n=1 차이를 효과로 단정하는 문장
  - C를 무작위 선택 확률로 해석
