# revD-20261124 사전 등록 (승컴: E1 변화 감지·재탐색 제거 실험, mixFYF)

- 작성: 2026-11-24, 본 실험 시작 전이다. **사용자 실행 승인 전에는 아무것도 실행하지 않는다.**
- 호스트: 승컴 (oy-System-Product-Name), 커널 7.0.0-31-generic, NVMeVirt = nvme0n1 (물리 NVMe 없음).
- 목적: 최초 E1 중 "워크로드 변화 감지·재탐색"과 "재탐색 시 후보 복원 범위"가 성능에 기여하는지 분리한다.
- 고컴 결과와 합치지 않는다. 같은 배치 안에서 세 정책만 비교한다. 고컴 mixFYF(revA)와는 효과 방향과 크기만 대조한다.

## 1. 정책 (같은 소스 `revD-src`에서 `ICAT_VARIANT`만 다르게 빌드)

- `revD-src` = 고컴 `revC-src` 사본에 VARIANT 7 한 블록을 더했다. 차이는 `conv_ftl.c` 4줄과 `conv_ftl.h` 주석·검사 3줄이다.
- **기계어 대조:** 이 PC에서 빌드한 revC-v4와 revD-v4는 objdump 정규화 차이가 0줄이다.
- 고컴 확인 사항: revC-v4는 revB-v4와 기계어가 같고, revB-src는 revA-src에서 V4 경로를 바꾸지 않았다.
- 따라서 **revD-v4의 정책 로직은 고컴 mixFYF V4와 같다.**

| 정책 | VARIANT | 후보 제거 15 % | 정착 | 변화 감지(25 %, 3구간 연속) | 리셋 시 후보 복원 | 리셋 시 학습 통계 | 모듈 SHA256 |
|---|---|---|---|---|---|---|---|
| revD-v4 | 4 | O | O | O (정착 상태, 현재 arm = best일 때) | 살아남은 후보 + 1단계 이웃 (`watgc_v2_grow`) | 45개 전부 0으로 | b35775057f2e7dc6… |
| revD-nodrift | 1 | O | O | **X** (감지 블록을 건너뜀 → 리셋이 일어나지 않음) | (리셋 없음) | (초기화 없음) | 4c267cd599976c59… |
| revD-fullreset | 7 | O | O | O | **45개 전부** (`WATGC_V2_ALLOWED`) | 45개 전부 0으로 | 5a34cb8487ac3c79… |

- 세 정책에서 같은 것 (같은 헤더): γ = 0.99949646 (Q16 65503), UCB c = 0.25, 판단 구간 128 GC 그리고 512 MiB host, 정착 12구간 + 3회 확인, probe 8구간마다, STALE 240, 후보 45개, 초기 arm 37.
- NoDrift 동작 동등성:
  - 승컴 `online-v4nodrift`(DRIFT_WINDOWS = 0xFFFFFFFF)와 동작이 같다. 둘 다 리셋이 절대 일어나지 않는다.
  - 고컴 revA "V1"(VARIANT 1)과는 소스가 같다.
- 계측 (관측 전용, 정책 영향 없음): `select`, `eval_explore`, `elim`, `best_change`, `reset`, `learner_ns`를 WATGC_V2 sample 로그에 남긴다.

## 2. 통제 조건 (고컴 revA/revC mixFYF와 같음)

- **러너:** `runner-revD.sh` = 고컴 `runner-revC.sh` 사본. 바꾼 것은 정책 목록, 경로, 안전 장치의 장치 이름(nvme1n1 → nvme0n1)뿐이다. 전체 diff는 `port.diff`에 있다.
- **부하:** mixFYF
  - FIO-Fast(test4, payload ×3) 1800 s → YCSB-A(SQLite, 250,000 records, load + run 합계 1800 s) → FIO-Fast 1800 s
  - 6 GiB test.dat는 처음부터 끝까지 유지한다. 지우거나 다시 만들지 않는다.
- **부하 파일 해시:** 고컴 revA와 같다.
  - `mix-test4.fio` b5edbcc7…
  - `workloada` c0aff8a2…
- **초기화 (매 run):**
  1. 모듈을 새로 insmod한다 (memmap 4G + 8G, cpus=1,2, measurement_manual=1, `icat_seed`).
  2. `mkfs.ext4`, mount nodiscard, chown.
  3. Table-3 준비: 6 GiB 128k 순차 쓰기 + 3 GiB 4k 랜덤 쓰기 (randseed 20260907, 10k IOPS).
  4. 카운터가 0인지 확인한 뒤 start.
  5. 끝나면 stop → umount → rmmod.
- **seed:** FIO hot/warm/cold = 20260910/20261010/20261110 + rep. icat_seed = 2026111400 + rep.
- **반복:** 정책마다 n = 3 (rep 1–3). rep 블록마다 순서를 `random.Random(20261124 + rep)`로 섞었다 (`queue-order.registered.txt`).
- **본 실행 전 단기 실행:** 정책마다 120 s 1회. 합산하지 않는다.

### ⚠️ 저자 결정 필요: 단계 B 부하

- mixFYF의 YCSB 단계는 **시간 기준**이다. 고컴 V4 3회는 1800 s 동안 148.9–149.9 M 요청을 처리했고, 단계 B host 쓰기는 약 577만 페이지였다.
- 승컴은 같은 시간에 약 95 M 요청을 처리할 것으로 예상한다. 11-24 300k 측정 53.6k ops/s 기준이다.
- 세 정책의 배치 안 비교에는 영향이 없다. 모든 정책이 같은 호스트, 같은 시간을 쓴다.
- 하지만 고컴 결과와 대조할 때는 단계 B 부하가 다르다. 학습기가 단계 C에 들어가는 상태도 달라질 수 있다.

| 선택 | 내용 |
|---|---|
| (기본) 시간 기준 유지 | 고컴과 절차가 같다. 요청 수와 host 쓰기는 기록만 한다. |
| 요청 수 고정 | 1.494 × 10⁸ (고컴 V4 평균). 부하는 같아지지만 승컴의 단계 B가 약 47분으로 길어진다. 러너도 고쳐야 한다. |

## 3. 지표 (사전 고정, 원시 데이터와 정의)

| # | 지표 | 정의 | 원천 |
|---|---|---|---|
| 1 | 단계별 WAF | 1 + Δgc/Δhost (단계 시작·끝 control 스냅샷). 전체 WAF는 summary와 파티션 합 두 경로로 계산 | `summary.txt`, `final-control.txt` |
| 2 | 전환 직후 WAF | 단계 C 시작 뒤 첫 5분 창 WAF (30초 시계열) | `control-series.txt` |
| 3 | 변화 감지 시간 | 단계 C START 뒤 첫 `WATGC_V2 reset` (4개 파티션 중 가장 빠른 것)까지의 시간. NoDrift는 설계상 "해당 없음" | `kernel.log` |
| 4 | 재탐색 시작 시점 | 3과 같다 (리셋 즉시 재순회). 파티션별 값도 함께 보고 | 같음 |
| 5 | 우수 후보까지 유효 관측 구간 수 | 리셋부터 그 파티션의 첫 `WATGC_V2 settled`까지 유효 판단 구간 수 (파티션별 값과 합) | 같음 |
| 6 | WAF 회복 시간 | **11-23 사전 정의 그대로 (주 기준):** 5분 이동창 WAF ≤ (같은 run, 같은 단계 후반 50 % 누적 WAF) × 1.05가 10분(20표본) 이어진 첫 시점 − 전환 시점. 양측 기준(\|비율 − 1\| ≤ 5 %)은 보조로만 보고. 사후에 기준을 바꾸지 않는다 | `analysis/revision/recovery.py` |
| 7 | 후보 제거와 복원 횟수 | 제거: `elim` 카운터의 단계별 증가량. 복원: 리셋 직후 첫 sample의 `active` − 리셋 직전 `active` | `kernel.log` |
| 8 | 탐색 CPU 경과 시간 | `learner_ns`의 단계 C 증가량, 리셋 → 정착 구간 증가량 | 같음 |
| – | 부하 기록 | 단계별 host_pages, YCSB 성공 요청 수(READ+UPDATE), 처리량, 단계 실제 시간 | `summary.txt`, `ycsb-run-B.txt.gz` |

- **주 비교 (사전 지정):**
  - 단계 C WAF: NoDrift − V4, FullReset − V4
  - 전체 WAF: 같은 두 대비
  - Welch 95 % CI
- **보조:** 지표 2–8
- **통계:** 정책별 유효 독립 반복이 3회일 때만 평균, SD, t 95 % CI를 계산한다. 하나라도 부족하면 그 정책은 값만 나열하고 통계는 내지 않는다.

## 4. 유효성 판정 (매 run 뒤 자동 확인, 하나라도 어기면 큐 정지)

- exit 0, 단계 A/B/C 완료, WAF 두 경로 일치
- FIO 오류 0, 커널 BUG/WARNING/Oops 0
- YCSB 유효 (`analysis/final_e1/validity.py`): 실패 ≤ 1 %, SQLITE_FULL 0
  - 승컴 기준은 더 엄격하다: 실패 0건. 1건이라도 있으면 보고서에 표시한다.
- run이 끝난 뒤 모듈이 언로드되고 umount됐는지

## 5. 시간과 저장 공간

- 단기 실행 3 × 약 7.5분 + 본 실행 9 × 약 91.5분 (고컴 실측) ≈ **약 14.1시간**
- 저장 공간: run당 약 80 MB, 합 약 0.8 GB. 루트 여유 공간 20 GB.

## 6. 결과 경로

- run 원시 결과: `result/revD-20261124/raw/mixFYF-<정책>-rep<N>/`
- 콘솔: `result/revD-20261124/console/`
- 판정 로그: `checks.tsv`, `runs.tsv`
- 분석 출력: `result/revD-20261124-analysis/` (본 실험이 끝난 뒤)
- 기존 mixFYF(고컴), mixR, mixR6 결과에는 쓰지 않는다.

## 7. 해시 (`modules.sha256`, `sources.sha256`)

모듈과 실행 소스의 SHA256은 이 폴더의 두 파일에 있다.

- 11-24 16:10 수정: 첫 단기 실행에서 러너가 `icat_seed`를 revD에 넘기지 않는 포팅 오류를 발견했다 (`rev[ABC]-*` 조건). seed는 VARIANT 9의 난수에만 쓰여 세 정책 동작에는 영향이 없다. 조건을 `rev[ABCD]-*`로 고쳤고 그 단기 실행은 `-noseed`로 보존하고 합산하지 않는다. `sources.sha256` 갱신.
