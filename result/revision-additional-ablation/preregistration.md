# abl-20261125 사전 등록: 추가 Ablation (심사 의견 M2, 승컴)

- 작성: 2026-11-25, 실행 전. **사용자의 명시적 실행 승인 전에는 아무것도 실행하지 않는다.**
- 호스트: 승컴 (커널 7.0.0-31-generic, NVMeVirt = nvme0n1). 고컴 결과와 합치지 않는다.

## 1. 정책 (모두 `revD-src`에서 빌드, 소스 수정 없음, 빌드 플래그만 다름)

| 정책 | 빌드 플래그 | 바뀌는 것 | 모듈 SHA256 |
|---|---|---|---|
| abl-v4 | `ICAT_VARIANT=4` | 없음. revD-v4와 **바이트 단위로 같다** (다시 빌드한 SHA가 같음) | b35775057f2e7dc6… |
| abl-nodiscount | `ICAT_VARIANT=4 ICAT_EXTRA=-DWATGC_V2_GAMMA_Q16=65536ULL` | γ = 1.0만 바뀐다. `watgc_v2_discount(v) = (v>>16)·65536 + ((v&0xFFFF)·65536>>16) = v` | b26b914ce2e13da7… |
| abl-noelim-nosettle | `ICAT_VARIANT=2` | 후보 제거 OFF (conv_ftl.c 620), 정착 OFF (540) | b35924ab4ee32da5… |

- **abl-nodiscount의 기계어 차이:** objdump 정규화 diff에서 바뀐 함수는 `do_gc`(학습기가 인라인된 함수) 하나다. 할인 곱셈 부분만 빠졌다 (V4 55줄 → 25줄).
- 리셋 시 통계를 0으로 만드는 동작은 두 정책에서 같다. 그래서 γ=1이어도 리셋 이후 데이터만 남는다.
- 오버플로 검토:
  - 창마다 host는 최대 131072 × 2¹⁶ ≈ 8.6 × 10⁹씩 쌓인다. run 한 번에 약 250창이므로 합은 약 2 × 10¹²이다. u64 한계보다 훨씬 작다.
  - 기존 재조정 코드(쌍으로 >>1)도 그대로 있다.

### ⚠️ 실험 B의 구조적 제약 (지시와 다른 점)
- 지시는 "후보 제거와 정착만 끄고 **변화 감지와 재탐색은 유지**"다.
- 하지만 현재 코드에서 변화 감지는 `t->settled && current == best`일 때만 동작한다 (conv_ftl.c 567–568).
- 감지 기준값(`reference_waf_q16`)도 정착할 때만 정해진다 (544–548).
- 1-step 이웃 probe도 정착한 뒤에만 동작한다 (639–655).
- 따라서 **정착을 끄면 변화 감지, 재탐색, probe가 함께 꺼진다.** 소스 변경 없이 두 기능만 끄는 방법은 없다.
- 이 빌드(VARIANT 2)는 "45개 후보 전체에 대한 할인 UCB 탐색만 남은 상태"다. 고컴 revA "V2"와 같은 VARIANT다.
- 변화 감지를 정착과 분리하려면 새 기준값 규칙을 **설계**해야 한다. 그것은 ablation이 아니라 새 정책이므로 이번 등록에 넣지 않는다. 보고서에는 "NoElim+NoSettle (감지, 재탐색, probe도 구조적으로 비활성)"이라고 적는다.

## 2. 통제 조건 (revD-20261124와 같음)
- 러너: `runner-abl.sh` = `runner-revD.sh` 사본. 정책 목록, 경로, 기록 라벨만 바꿨다 (`port.diff`).
- 부하:
  - mixFYF: FIO-Fast(test4, ×3) 1800 s → YCSB-A(SQLite 250,000 records, load+run 1800 s) → FIO-Fast 1800 s
  - test.dat 6 GiB는 계속 유지한다
- 초기화:
  1. insmod (memmap 4G+8G, cpus=1,2, measurement_manual=1, icat_seed)
  2. mkfs.ext4, mount nodiscard
  3. Table-3 준비 (randseed 20260907)
  4. 카운터 0을 확인한 뒤 start
  5. 끝나면 stop, umount, rmmod
- seed:
  - FIO hot/warm/cold = 20260910/20261010/20261110 + rep
  - icat_seed = 2026111400 + rep
  - revD와 rep별로 같다. 그래서 "동일 seed 대응 비교"를 할 수 있다.
- 반복: 정책마다 n = 3. rep 블록마다 `random.Random(20261125 + rep)`로 순서를 섞었다 (`queue-order.registered.txt`).
- 단기 실행: 정책마다 120 s 1회. 합산하지 않는다.

## 3. V4 대조군
- **같은 배치 안에서 V4를 n=3으로 다시 돌린다 (abl-v4).**
- 이유:
  - revD-v4와 모듈, 러너, seed가 같아도 실행 날짜가 다르다.
  - 이전 감사(E0)에서 시기가 다르면 결과가 달라진 사례가 있었다.
- 부수 효과: abl-v4 대 revD-v4 비교로 배치 사이 재현성을 직접 확인할 수 있다 (같은 모듈, 같은 seed).
  - 일치하면 revD-NoDrift와 revD-FullReset도 이 표에 함께 놓을 근거가 된다.
  - 일치하지 않으면 배치 사이 비교는 하지 않는다.

## 4. 지표 (사전 고정)

| 지표 | 정의 | 원천 |
|---|---|---|
| 단계별 WAF, 전체 WAF | 1 + Δgc/Δhost. control 첫 줄과 파티션 합 두 경로로 계산한다 | `phase-*-start/end.txt`, `stopped.txt` |
| 단계 C 첫 5분 WAF | 30초 시계열 | `control-series.txt` |
| 선택 횟수, 탐색 평가 횟수, 제거 횟수, best 변경 횟수, 리셋 횟수 | sample 카운터 `select`, `eval_explore`, `elim`, `best_change`, `reset`의 run 끝 값 (파티션 합) | `kernel.log` |
| 후보별 누적 평가 횟수 | `evaluated=` arm별 창 수 | `kernel.log` |
| 정착 횟수 | `WATGC_V2 settled` 줄 수 | `kernel.log` |
| 탐색 비용 | evaluated ≠ best인 창의 host, gc 페이지와 그 창들의 WAF | `kernel.log` |
| 적응 시간 | 파티션별 리셋 → 같은 파티션 정착 (s, 창 수). 회복 시간은 11-23 사전 정의 그대로 (보조) | `kernel.log`, `control-series.txt` |
| 학습 실행 시간 | `learner_ns` 증가량. ktime 경과 시간이며 CPU 시간이 아니다 | `kernel.log` |
| 학습 자료구조 메모리 | `sizeof(struct watgc_v2_tuner)` 계산. 세 정책 모두 구조체가 같다 | 소스 |
| CPU 오버헤드 | 측정 불가. NVMeVirt 스레드가 cpu1,2를 계속 점유하므로 학습기만의 CPU 사용을 분리할 수 없다. `learner_ns`로 대신한다 | – |
| YCSB 요청, 성공 수 | READ+UPDATE Operations, Return=OK | `ycsb-run-B.txt.gz` |

- **주 대비 (사전 지정):**
  - 전체 WAF와 단계 C WAF: NoDiscount − V4, NoElimNoSettle − V4 (같은 배치의 abl-v4 대비)
  - Welch 95 % CI, Hedges' g
  - **Holm 보정은 주 대비 4개 묶음에 적용한다**
- **보조:**
  - 같은 seed끼리 짝지은 차이 (rep별 대응 t, df 2)
  - abl-v4 − revD-v4 (재현성)
- n < 3이면 통계적 결론을 유보한다.
- "효과 없음"은 "차이를 확인하지 못했다"로 쓴다. 동등성을 주장하지 않는다.

## 5. 유효성 (매 run 뒤 자동 확인, 하나라도 실패하면 큐 정지, 다음 run을 자동으로 시작하지 않음)
- 모듈 SHA256: insmod 전에 `modules.sha256`과 대조한다. 실행 소스 SHA256은 `sources.sha256`에 있다.
- exit 0, 단계 A/B/C 완료, FIO 오류 0, YCSB 실패 0, SQLITE_FULL 0
- 커널 BUG/WARNING/Oops 0
- WAF 두 경로 일치, 시작 카운터 0
- sample `window=`가 빈틈없이 이어지는지
- run이 끝난 뒤 모듈 언로드와 umount

## 6. 시간
- 단기 실행 3 × 약 7.6분 + 본 실행 9 × 약 91.6분 (revD 실측) ≈ **약 14.1시간**
- 결과 경로: `result/revision-additional-ablation/`
