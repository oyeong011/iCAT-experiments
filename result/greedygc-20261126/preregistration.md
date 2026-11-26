# greedygc-20261126 사전 등록: Greedy GC 대 iCAT-v4, mixFYF (M3, 승컴)

- 작성: 2026-11-26, 실행 전. 큐는 `result/batchG-20261126/`에 있다.
- 목적: 논문의 기존 Greedy GC 결과는 다른 워크로드에서 나왔다. 그 불일치를 없애기 위해 mixFYF에서 같은 초기화, 같은 측정 구간으로 다시 비교한다.

## Greedy GC 코드 감사 (새 규칙을 만들지 않음)
- **기존 모듈**
  - `nvmev-greedy.ko` / `nvmev-baseline-20260906-greedy.ko` (sha 20b211e5…)
  - `nvmev-measurement-20260907-greedy.ko` (2ba2686c…)
  - 셋 다 `NVMEVIRT_GC_POLICY=GREEDY`로 빌드했다 (build-info).
  - 소스는 `nvmevirt_test/`다.
- **이 모듈을 그대로 쓸 수 없는 이유**
  - 09월 모듈은 mixFYF 러너의 계측 인터페이스(파티션별 카운터, measurement_manual 동작)가 revD와 다르다.
  - 그래서 V4와 같은 측정 조건을 보장할 수 없다.
- **대신 쓰는 모듈**
  - revD-src(V4와 같은 트리)를 **소스 수정 없이** `NVMEVIRT_GC_POLICY=GREEDY`로 빌드했다.
  - `buildoutput/nvmev-greedygc.ko`, sha256 cd2b7704ef1263a9…
- **선택 규칙이 같다는 코드 대조** (nvmevirt_test → revD-src)
  - `select_victim_line` GREEDY 분기가 같다: `pqueue_peek`(유효 페이지 수 최소), `!force && vpc > pgs_per_line/8`이면 GC 안 함, `pqueue_pop`.
  - `victim_line_cmp_pri`, `victim_line_get_pri`가 같다 (우선순위 = vpc).
  - `pqueue/`가 같고, `ssd_config.h`가 같다.
  - GC 문턱 `gc_thres_lines = gc_thres_lines_high = 2`가 같다.
  - `mark_page_invalid`의 vpc 갱신과 `pqueue_change_priority`가 같다. revD는 `last_invalidated_at_ns` 기록만 더했는데, 이 값은 CAT 전용이라 Greedy는 읽지 않는다.
  - 공통 코드에서 `conv_record_victim`(통계 로그)만 빠졌다. 선택에는 영향이 없다.
- greedygc 모듈에는 `icat_seed` 파라미터가 없다 (WATGC 전용). 그래서 러너는 이 정책에만 icat_seed를 넘기지 않는다. FIO와 YCSB seed는 같다.

## 대조군
- 같은 배치 V4 3회(bg-v4, `result/batchG-20261126/raw`)다.
- revD-v4와 abl-v4는 합치지 않고 참고로만 보고한다 (배치 재현성 미달).

## 지표
- 전체 WAF, 단계 A/B/C WAF
- YCSB 처리량(ops/s)과 성공률
- FIO 쓰기 clat 평균, p99, p99.9 (단계 A, C)
- 오버헤드
  - CPU: 측정할 수 없다. NVMeVirt가 cpu1과 cpu2를 계속 점유한다.
  - 학습기 시간: V4는 `learner_ns`(ktime)로 잰다. Greedy는 학습기가 없어 0이다.
  - 메모리: 구조체 크기 차이로 보고한다 (V4 `struct watgc_v2_tuner`).
  - 둘 다 측정값이 아니라 계산값임을 표시한다.
- 통계: 평균 ± SD, t 95 % CI, Welch CI와 p, Hedges' g, 같은 seed 짝 차이.
