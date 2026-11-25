# revision-20261125-analysis: 기존 원시 로그 재분석 (새 실행 없음)

- 스크립트: `analysis/revision/r_suite_20261125.py` (sha256 201c0e88b23a1b74…). 회복 정의는 `e1_revd.py`가 `recovery.py`에서 ast로 가져온 것을 그대로 쓴다 (TOL 1.05, ROLL 10, HOLD 20).
- 재현 방법:
  ```
  git fetch origin
  mkdir G && git archive origin/report/data-validity-20261124 result/revA-20261114 | tar -x -C G
  python3 -I -B analysis/revision/r_suite_20261125.py G
  ```
  - 고컴 브랜치 커밋: 299d6e78d
- 입력:
  - 승컴: `result/revD-20261124/raw/mixFYF-revD-{v4,nodrift,fullreset}-rep{1,2,3}`, 9개 run (main)
  - 고컴: `result/revA-20261114/raw/mixFYF-{revA-v4,revA-v1,revA-v2,revA-random}-rep{1,2,3}` + `mixFYF-arm47-rep1` (위 브랜치)
  - 고컴 revB와 revC는 쓰지 않았다. revC-v4는 아직 n=2다.
- **호스트 분리:** 모든 행에 `host` 열(승컴 또는 고컴)이 있다. 통계는 같은 host, 같은 policy 안에서만 낸다. 두 호스트 값을 합산하거나 평균하지 않는다.
- **유효성:** 모든 행에 `valid`와 `invalid_reason` 열이 있다.
  - 판정 조건: exit 0, 단계 A/B/C 완료, YCSB READ+UPDATE의 OK 수 = 요청 수, SQLITE_FULL 0, 커널 BUG/WARNING/Oops/Call Trace 0
  - 결과: 22개 run이 모두 유효하다.
- **Gate 1 (로그 완전성):** run마다, 파티션마다 WATGC_V2 sample의 `window=`가 1부터 빈틈없이 이어진다.
  - kernel.log와 kernel-snapshots를 합친 결과가 kernel.log와 같다 (21개 learner run).
  - `discarded=1`인 창은 0개다.
- 통계: n=3일 때만 mean, SD, t 95% CI를 낸다 (df 2).
  - 사전 등록된 주 대비(E1 C WAF, 전체 WAF)는 `result/revD-20261124-analysis/contrasts.csv`에 이미 있다.
  - 이 폴더의 값은 모두 **기술 통계**다. 유의성 검정은 하지 않았다.

| 파일 | 내용 | 계산식 | 원천 |
|---|---|---|---|
| `waf_recalc.csv` | 승컴 9 run의 단계별, 전체 WAF | 경로 1: 1 + Δgc/Δhost (control 첫 줄)<br>경로 2: 1 + ΣΔgc_part/ΣΔhost_part<br>경로 3: summary.txt | `phase-{A,B,C}-{start,end}.txt`, `stopped.txt`, `final-control.txt`, `summary.txt`, `started.txt`(0인지 확인) |
| `e3_partition.csv` | run × 단계(B, C) × 파티션별 사건 | detect_s = 해당 파티션의 첫 `WATGC_V2 reset` − 단계 START<br>resettle_s = 같은 파티션의 다음 `settled` − reset<br>explore_windows = 같은 파티션의 (reset, settled] 구간 sample 수 | `kernel.log` |
| `e3_run.csv`, `e3_stats.csv` | run 단위 요약과 정책별 기술 통계 | first_detect = 파티션 중 최솟값<br>explore_windows_sum = 파티션 합<br>resettle_s_max = 파티션 중 최댓값<br>recovery_s = 사전 정의 | 위와 같음, `control-series.txt` |
| `gamma.csv` | 파티션별 창 수와 할인 가중치 | 가중치 = γⁿ, γ = 65503/65536. **매 창마다 45개 arm 전부에 적용된다** (revD-src/conv_ftl.c 582–587).<br>리셋하면 통계가 0이 되므로 "마지막 리셋 이후 창 수"도 함께 계산 | `kernel.log` |
| `latency.csv`, `latency_stats.csv` | FIO 쓰기 완료 지연 (job별 평균, p50, p99, p99.9)<br>YCSB READ/UPDATE 평균, p95, p99, 처리량 | FIO JSON `clat_ns`, YCSB 요약 줄 | `phase-{A,C}.json`, `ycsb-run-B.txt.gz` |
| `random_search.csv`, `random_search_arms.csv` | 고컴만 사용. **[측정]** 정책별 전체 WAF<br>**[보정]** 추정기 오차<br>**[추정]** Random Search 기댓값 | arm별 단계 WAF 추정 = 1 + Σgc/Σhost (random-selection run 3개에서 그 arm이 평가된 창들. host와 gc는 창별 증가량)<br>단계 B는 표본이 적어 arm을 구분하지 않고 합쳤다<br>전체 = arm47 run의 단계별 host 가중 평균<br>Random Search = 파티션마다 k개 arm을 1창씩 시험(관측은 그 arm의 단계 A 창 1개를 무작위로 뽑음) → 관측값이 가장 낮은 arm으로 고정, 20,000회 몬테카를로 (seed 20261125) | 고컴 `revA-random-rep{1,2,3}/kernel.log`, `*/summary.txt` |

## 알려진 한계
- `e1_revd.py`의 `C_explore_windows`와 `C_resettle_s`는 `recovery.py:events()` 정의를 그대로 썼다.
  - 그 정의는 4개 파티션 중 가장 이른 리셋과, 그 뒤 **아무 파티션**의 첫 정착을 쓴다.
  - 사전 등록 지표 5는 "**그 파티션**의 리셋부터 그 파티션의 정착까지"다. 따라서 이 폴더의 `e3_*`가 사전 등록 정의에 맞는 값이다.
  - 이미 push한 `stats.csv`는 고치지 않았다. 차이는 `VERIFY-REQUEST-ADDENDUM-20261125.md`에 기록했다.
- 사전 정의 회복 시간은 "자기 run 단계 후반의 WAF"를 기준으로 삼는다.
  - 그래서 단계 C WAF가 처음부터 거의 평평한 정책(NoDrift, Random, V1)은 최소값 약 300 s(이동창 5분)에 가깝게 나온다.
  - 이 값은 정책 사이의 빠르기 비교로 읽으면 안 된다.
- Random Search 추정기는 같은 고컴 호스트에서 측정한 arm47 고정 run과 비교해 보정했다.
  - 추정 − 측정 = 단계 A +0.148, 단계 C +0.021, 전체 +0.085
  - random-selection 창의 장치 상태는 고정 arm run의 장치 상태와 다르다. 따라서 추정치는 **약 +0.08 높게 치우쳐 있을 수 있다.**
- 지연 시간은 NVMeVirt 시간 모델이 만든 값이다. 실제 장치 지연이 아니다.
- 승컴 단계 B는 시간 기준(1800 s)으로 돌렸다. 그래서 run마다 YCSB 요청 수가 다르다 (1.08–1.22억).
