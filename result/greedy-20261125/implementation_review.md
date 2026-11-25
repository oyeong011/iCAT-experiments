# Online Greedy 구현 검토 (greedy-src, ICAT_VARIANT=8)

- `greedy-src`는 `revD-src`의 사본이다.
  - revD-src는 수정하지 않았다. 추가 ablation의 `sources.sha256`가 그 해시를 참조한다.
  - 차이는 `greedy-src.diff`에 있다: conv_ftl.c 4곳, conv_ftl.h 1곳.

## 1. 지시 항목과 코드 대응

| 지시 | 구현 | 위치 |
|---|---|---|
| 1. 45개 arm을 처음에 1회씩 평가 | 기존 `watgc_v2_choose_search` 첫 루프를 그대로 쓴다 (방문 수가 가장 적은 arm, 동률이면 작은 번호). 첫 창은 초기 arm 37이고, 이어서 15, 16, … 순서로 아직 안 본 arm을 1회씩 평가한다. MIN_VISITS = 1 | conv_ftl.c `choose_search` 앞부분 (변경 없음) |
| 2. arm별 평균 WAF | V4와 같은 추정량이다: 그 arm이 평가된 창들의 Σgc / Σhost (host 가중 평균) | `watgc_v2_waf_q16` (변경 없음) |
| 3. 매 판단 구간마다 평균이 가장 낮은 arm | 커버가 끝난 뒤 `#if ICAT_VARIANT == 8` 블록에서 argmin을 고른다. UCB 보너스와 stale 재방문은 건너뛴다 | `choose_search` 새 블록 |
| 4. 동률이면 작은 번호 | 낮은 번호부터 돌고 `mean < lowest`(엄격한 부등호)일 때만 바꾼다 | 같음 |
| 5. 새 관측으로 평균 갱신 | 매 창의 host, gc를 그 arm의 합에 더한다 (변경 없음) | `watgc_v2_observe` |
| Discount 없음 | 창마다 45개 arm에 γ를 곱하는 루프를 `#if ICAT_VARIANT != 8`로 감쌌다 | `observe` |
| UCB 없음 | 위 argmin 블록이 UCB 계산보다 먼저 return한다 | `choose_search` |
| ε-greedy 없음 | 원래 코드에 없다 | – |
| 후보 제거 없음 | 제거 조건에 `ICAT_VARIANT != 8`을 더했다 | `observe` 제거 블록 |
| 정착 없음 | 정착 조건에 `ICAT_VARIANT != 8`을 더했다 | `update_best` |
| 변화 감지, 재탐색 없음 | 감지는 `settled`일 때만 동작하므로 정착이 없으면 동작하지 않는다. 리셋도 일어나지 않는다 | `observe` 567–568 (변경 없음) |
| 주기적 probe 없음 | probe는 `settled`일 때만 동작하므로 마찬가지로 동작하지 않는다 | `observe` probe 블록 (변경 없음) |

## 2. 판단 구간 (WAF 관측 단위), V4와 같음
- **창의 크기:** host 쓰기 512 MiB 이상, 그리고 GC 128회 이상이면 창 하나가 끝난다.
- **창 상한:** GC 8192회 또는 300 s를 넘으면 undersized로 버린다.
- **창 사이:** burn-in(host 32768 페이지, GC 32회)을 거친다.
- **시작 전:** warm-up으로 GC 100회를 거친다.
- **창의 WAF:** 1 + 그 창의 gc_pages / host_pages (Q16). 창마다 arm 하나만 쓴다.

## 3. 그대로 남긴 것 (V4와 같음)
- `watgc_v2_update_best`는 로그의 `best=` 필드에만 쓰인다. 0.5 % 지연 규칙이 있지만 Greedy의 선택에는 영향이 없다.
  - 그래서 `best_change` 카운터는 "정책 변경 횟수"로 쓰지 않는다.
  - 정책 변경 횟수는 `select` 카운터(next ≠ evaluated)를 쓴다.
- 카운터가 넘칠 때 쌍으로 >>1 하는 보호 코드도 남아 있다.
  - 할인이 없으면 합이 계속 커진다. 그래도 창마다 최대 8.6 × 10⁹ × 약 250창 ≈ 2 × 10¹²로, u64 한계보다 훨씬 작다.
  - 이 보호 코드는 실험 기간 안에서 실행되지 않는다.
- 구조체 `watgc_v2_tuner`의 크기는 V4와 같다. 학습 자료구조 메모리 차이는 0이다.

## 4. 빌드 검증
- 빌드 명령: `taskset -c 7 nice -n 19 make -j1 -C /lib/modules/7.0.0-31-generic/build M=greedy-src ICAT_VARIANT=… modules`
  - 실행 중인 ablation run에 주는 영향을 줄이려고 이렇게 빌드했다.
  - 빌드 시각: 10:56:37–10:56:56, 약 19 s (`build/build-times.txt`)
  - 같은 시각에 ablation 단기 실행(NoDiscount 다음 정책)이 진행 중이었다. 단기 실행은 합산하지 않는다.
- greedy-src를 `ICAT_VARIANT=4`로 빌드한 모듈과 revD-v4 모듈을 비교했다.
  - objdump 정규화 기계어 diff는 0줄이다.
  - 다른 것은 srcversion과 빌드 경로 문자열뿐이다.
  - 즉 greedy-src의 V4 경로는 바뀌지 않았다. 대조군 V4는 기존 `nvmev-abl-v4.ko`(= revD-v4)를 쓴다.
- Greedy와 V4 기계어 차이는 학습기가 인라인된 `do_gc` 하나뿐이다 (V4 972줄 → 536줄; UCB, 할인, 제거, 정착, 감지, probe 경로가 빠졌다).
- **동작 검증 (실행 뒤):** `greedy_analysis.py`가 커널 로그의 창별 host, gc로 argmin을 다시 계산한다. 그 값과 로그의 `next`가 모든 창에서 같은지 확인한다 (`greedy_rule_check.csv`, 불일치 0이 기준).
  - 같은 함수를 revD-v4 rep1에 시험 적용했다. 파싱 결과: 첫 45창에 서로 다른 arm 45개, 커버 창 45.

## 5. 정정 (11-25 11:00)
- 처음에는 새 모듈을 `buildoutput/nvmev-greedy.ko`로 복사했다. 그런데 그 이름의 파일은 09-14 백업 커밋(f15d092ef)에 이미 있던 예전 greedy 모듈(sha256 20b211e5…)이었다.
- git에서 원래 파일로 되돌렸다. 덮어쓴 내용은 커밋되지 않았다.
- 새 모듈은 `buildoutput/nvmev-greedy-online.ko`(4df03c90…)로 옮겼다. 모든 문서와 러너의 경로를 고쳤다.
