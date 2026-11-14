# 구현 감사 (resource-v124-20261114)

모든 위치는 iCAT-experiments 저장소 기준이다. v1 = `online-mix-src`(모듈 `nvmev-online-mix-20260907.ko`), v2 = `online-v2-src`(`nvmev-online-v2.ko`), v4 = `online-v4-src`(`nvmev-online-v4.ko`). 세 소스를 다시 빌드한 `.text` 섹션은 실험에 써 온 `.ko`와 sha256이 같다(v1 `badea139…`, v2 `2002cfa0…`, v4 `380dfe28…`).

## 0. 지시서 정의와 실제 구현의 차이

| 지시서 | 실제 코드 |
|---|---|
| V1 = 변화 감지·재탐색 제거 | **아니다.** v1에도 변화 감지(`watgc_v2_observe` 안 drift 검사, `WATGC_V2_DRIFT_Q16` 12.5%, 3구간 연속)와 재탐색(`watgc_v2_reset_epoch`, `online-mix-src/conv_ftl.c:401`)이 있다. 정착(`settled`)도 있다(`:462`). 후보 제거는 없다. |
| V2 = 후보 제거·정착 제거 | **아니다.** v2는 v1과 함수 구성이 같고 상수만 다르다: 판단 구간 3배(`WINDOW_GC` 64→192, `WINDOW_HOST_PAGES` 256→768 MiB), `MIN_VISITS` 3→1. 정착은 있고, 후보 제거는 v1처럼 원래 없다. |
| V4 = 전체 알고리즘 | 맞다. v1 대비 추가: k=2 조합 제외(`ARM_LO` 15, 후보 45개), 판단 구간 2배, `MIN_VISITS` 1, drift 25%, 후보 제거(`ELIM_Q16` 15%, `online-v4-src/conv_ftl.c:584-596`), 정착 후 이웃 탐색(`PROBE_EVERY` 8, `:601-616`), 재탐색 시 생존 후보+이웃만 복원(`watgc_v2_grow`, `:459`). |

지시서 규칙(구현에 없는 기능을 만들지 않는다)에 따라 **실제 v1/v2/v4를 그대로 측정**했다. 지시서가 뜻한 절제(ablation) 버전은 저장소에 없다(가장 가까운 것은 `online-v4noelim-src`, `online-v4fullreset-src`).

## 1. Fixed CAT-47

- arm 47 = `watgc_v2_decode`(`online-v4-src/conv_ftl.c:125`)로 k=10, scale 25%, age_ratio 16. 논문 표 1의 CAT-Best와 같다.
- 이번 실험의 고정 모듈은 v4 소스(`res-v4-src`)를 `NVMEVIRT_GC_POLICY=CAT_FIG7`, `-DCONV_FIXED_ARM=47`로 빌드했다. 이 경우 학습 코어(`WATGC_V2_CORE_BEGIN..END`)는 `#else` 쪽의 빈 함수가 되며(`watgc_v2_on_gc`는 아무것도 하지 않음), `watgc_v2_init`이 arm 47의 임계값만 한 번 설정한다. 희생 블록 점수 계산(CAT)은 iCAT과 같은 코드다.

## 2. 지시서 3절 항목별 위치 (v4 기준, v1/v2는 괄호)

| # | 항목 | 위치 |
|---|---|---|
| 1 | 초기화 | `watgc_v2_init` `online-v4-src/conv_ftl.c:622` (v1 `:546`). memset 후 arm 37, `active = WATGC_V2_ALLOWED`(v4), phase=WARMUP |
| 2 | 학습 상태 구조체 | `struct watgc_v2_tuner` `online-v4-src/conv_ftl.h:140` (v1 `:138`), `struct conv_ftl` 안에 값으로 포함(`:177`) |
| 3 | 후보별 통계 | `struct watgc_v2_arm` `conv_ftl.h:124`: `host_pages`, `gc_pages`(Q16 누적 합, 보상 = WAF), `count_q16`(할인된 관측 수 = 가중치), `visits`, `last_window`. 배열 크기 `WATGC_V2_ARM_N` = 60 (v4도 60칸, 그중 45개만 후보) |
| 4 | 할인·보상 갱신 | `watgc_v2_discount` `conv_ftl.c:317` (γ = 65503/65536 ≈ 0.9995), 갱신은 `watgc_v2_observe` `:523` 안에서 전체 60개 arm 할인 후 현재 arm에 표본 추가, `watgc_v2_update_best` `:472` |
| 5 | 후보 제거·정착 | 제거: v4만, `observe` `:584-596`. 정착: `update_best` `:511` (v1 `:462`), 조건 = 모든 후보 관측 + 12구간 안정 + 3회 확인 |
| 6 | 변화 감지 | `observe` 시작부 drift 검사 `:534-545` (v1 `:485-496`): 정착 상태에서 표본이 기준 WAF와 DRIFT 이상 3구간 연속 다르면 재탐색 |
| 7 | 재탐색 | `watgc_v2_reset_epoch` `:448` (v1 `:401`): 모든 arm 통계 0으로. v4는 후보 집합을 생존+이웃으로 복원 |
| 8 | 호출 위치·빈도 | `do_gc` `:1594` 끝에서 `watgc_v2_on_gc` `:1662` (GC 1회마다 1번). 판단(`observe`)은 판단 구간이 끝날 때만: GC 수와 호스트 쓰기량이 모두 기준을 넘을 때(`:663`): v1 GC 64회·256 MiB, v2 192회·768 MiB, v4 128회·512 MiB |
| 9 | 파티션 독립성 | `conv_ftls[i]`마다 튜너 1개(`conv_init_ftl(&conv_ftls[i], …, i)` `:1151`). 파티션 4개(`SSD_PARTITIONS` 4), 공유 상태 없음 |
| 10 | GC와 학습의 관계 | 학습은 GC 경로 안에서 같은 스레드(`nvmev_dispatcher` kthread)가 동기적으로 실행한다: `conv_write` → `check_and_refill_write_credit` → `foreground_gc` → `do_gc` → `watgc_v2_on_gc`. 별도 학습 스레드는 없다 |

## 3. 동적 할당

학습 코어에는 `kmalloc`/`vmalloc`이 없다. 모듈의 동적 할당은 모두 공통 FTL 자료구조다: `lm->lines`(`:865`), `maptbl`(`:1052`), `rmap`(`:1068`), `conv_ftls` 배열(`:1145`, 튜너 포함), `struct ssd`(`:1149`). 따라서 튜너 크기는 `sizeof`로 정확히 정해진다.

## 4. 원본 대비 계측 코드 차이

`analysis/resource/instrument.py`가 소스를 `res-v{1,2,4}-src`로 복사하고 아래만 추가한다. 추가분은 모두 `#ifdef RES_INSTR` 안에 있다(`CONV_FIXED_ARM`은 학습기를 끈 빌드의 초기 arm만 바꾼다).

- 파티션×7칸 카운터(호출 수, 합, 최대): `do_gc`, `on_gc`, `observe`, 보상 갱신(`observe` 시작 → `if (!t->settled)` 직전), 정책 선택(그 지점 → 반환), 판단 기록 `printk`, `set_arm`
- rmmod 시 `RESOURCE` 줄 출력(카운터와 `sizeof` 값)

검증: `RES_INSTR` 없이 빌드한 세 복사본의 `.text`가 원본과 sha256 일치. 계측이 WAF에 주는 영향은 비계측 실행 4회와 비교한다(실험 보고서 참조).
