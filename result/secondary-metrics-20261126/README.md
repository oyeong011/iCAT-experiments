# secondary-metrics-20261126: 사전 등록 보조 지표 3개 (기존 원시 로그만 사용, 새 실행 없음)

- 스크립트: `analysis/revision/secondary_metrics.py` (sha256 8bfdd2ea73430a78…)
- 재현: `python3 -I -B analysis/revision/secondary_metrics.py`
- 호스트는 모두 승컴이다. 고컴 자료는 쓰지 않았다.
- 15개 run 모두 valid다 (`runs.csv`의 `valid` 열).

## 원시 로그 경로

| 정책 | 경로 | 실행일 |
|---|---|---|
| revD-v4 (Greedy 주 대조군) | `result/revD-20261124/raw/mixFYF-revD-v4-rep{1,2,3}` | 11-24 |
| abl-v4, abl-nodiscount, abl-off-elim-settle-drift-probe | `result/revision-additional-ablation/raw/mixFYF-<정책>-rep{1,2,3}` | 11-25 |
| greedy-online | `result/greedy-20261125/raw/mixFYF-greedy-online-rep{1,2,3}` | 11-26 |

- 쓰는 파일: `control-series.txt` (30 s), `phase-C-start.time`, `kernel.log`의 `WATGC_V2 sample / reset / settled` 줄과 `phase=X START` 줄

## 정의

| 지표 | 정의 | 출처 |
|---|---|---|
| 1. 단계 C 첫 5분 WAF | 단계 C START 이후 첫 30 s 표본부터 START+300 s 이후 첫 표본까지 1 + Δgc/Δhost | `e1_revd.py`와 같은 정의 |
| 2. 탐색 비용 | sample 줄에서 `evaluated ≠ best`인 창의 수, 그 창들의 host 비중, 그 창들의 WAF (1 + Σgc/Σhost). run 전체와 단계 C 따로 | 사전 등록 지표 정의 |
| 3. 적응 시간 | 파티션마다 단계 안 첫 `reset`부터 같은 파티션의 다음 `settled`까지의 시간(s)과 창 수 | 11-25 `e3_partition.csv`와 같은 정의 |
| 3 보조. 회복 시간 | 11-23 사전 정의 (`recovery.py`, TOL 1.05, ROLL 10, HOLD 20) | |

## 독립 재계산 대조 (`crosscheck.csv`)
- 120개 항목이 **모두 일치**한다 (차이 < 1e-6).
- 두 경로를 비교했다:
  - 기존 코드 경로: `recovery.py`와 `r_suite.e3`
  - 이 스크립트의 독립 구현: 별도 파서
- 두 결과를 다시 이미 push한 값과 비교했다: revD `runs.csv`의 `C_first5min_waf`, 11-25 `e3_partition.csv`의 파티션별 `resettle_s`.

## 결과 (mean ± SD, n=3; seed별 값은 `statistics.csv`)

| 지표 | revD-v4 | abl-v4 | NoDiscount | 묶음 OFF | Greedy |
|---|---|---|---|---|---|
| 단계 C 첫 5분 WAF | 2.598 ± 0.009 | 2.618 ± 0.092 | 2.565 ± 0.073 | 2.740 ± 0.022 | **2.407 ± 0.042** |
| 탐색 host 비중 (run 전체) | 0.536 | 0.485 | 0.513 | 0.855 | 0.355 |
| 탐색 창 WAF (run 전체) | 2.055 | 2.032 | 2.053 | 2.287 | 2.247 |
| 탐색 host 비중 (단계 C) | 0.267 | 0.189 | 0.247 | 0.856 | 0.328 |
| 단계 C 리셋 파티션 수 | 3.0 | 3.7 | 3.3 | 0 | 0 |
| 단계 C 적응 시간, 파티션 평균 (s) | 352 ± 150 | 275 ± 31 | 316 ± 46 | 측정 불가 | 측정 불가 |
| 단계 C 적응 창 수 (합) | 67 ± 34 | 64 ± 16 | 68 ± 23 | 측정 불가 | 측정 불가 |
| (보조) 회복 시간 (s) | 911 ± 105 | 1000 ± 24 | 631 ± 326 | 941 ± 17 | 320 ± 4 |

### 주요 대비 (Welch 95 % CI; 탐색적 분석이며 다중 비교 보정 없음, `contrasts.csv`)
- **Greedy − revD-v4, 단계 C 첫 5분 WAF:** −0.191 [−0.289, −0.093], p = 0.012
  - abl-v4 대비로도 −0.211 [−0.406, −0.017], p = 0.041
  - **Greedy가 단계 C 초반에 더 낮다. V4에 불리한 결과다.**
- NoDiscount − abl-v4: 세 지표 모두 차이를 확인하지 못했다.
  - 예외는 단계 C 탐색 host 비중이다: +0.058 [+0.020, +0.095]
- 묶음 OFF − abl-v4: 탐색 host 비중 +0.37 (run 전체), 탐색 창 WAF +0.25. 둘 다 CI가 0을 포함하지 않는다.

## 측정할 수 없거나 정의가 다른 지표
- **적응 시간: 묶음 OFF와 Greedy는 측정할 수 없다.** 두 정책은 구조적으로 reset과 settled가 없다 (VARIANT 2, 8). 0으로 채우지 않고 빈칸으로 두었다.
  - 그래서 적응 시간은 V4와 NoDiscount 사이에서만 비교할 수 있다.
- **탐색 비용의 `best`는 정책마다 뜻이 다르다.**
  - V4와 NoDiscount: 정착 기준의 best다.
  - Greedy: 로그용 `update_best`(0.5 % 지연 규칙)다. Greedy의 선택은 매 창의 argmin이므로, Greedy의 "탐색 창"은 실제 탐색이 아니다. 대부분 처음 45창과, argmin과 지연된 best가 어긋난 창이다.
  - 묶음 OFF: 정착이 없어서 거의 모든 창이 `evaluated ≠ best`다.
  - 따라서 탐색 비용은 V4 대 NoDiscount 비교에만 같은 뜻으로 쓸 수 있다. 다른 정책과의 비교는 참고용이다.
- **회복 시간(보조)은 정책 사이의 빠르기 비교로 읽으면 안 된다.** 기준이 "자기 run 단계 후반의 WAF"이기 때문이다.
  - 단계 C가 평평한 정책(Greedy 320 s)은 최소값(이동창 5분)에 가깝게 나온다 (11-25 README의 한계와 같다).
- CPU 시간은 측정할 수 없다. `learner_ns`(ktime)로 대신한다 (기존과 같음).
- 대조군 날짜가 다르다:
  - Greedy는 11-26, revD-v4는 11-24, abl-v4는 11-25에 돌렸다.
  - 같은 배치 재현성 기준(±0.02)은 미달했다 (`result/greedy-20261125/control-decision.txt`).

## 논문에 쓸 수 있는 해석
- 쓸 수 있는 것:
  - "기능 묶음(제거, 정착, 감지, probe)을 끄면 host의 약 86 %가 탐색 창에 쓰이고, 탐색 창 WAF도 높아진다."
    - 전체 WAF가 나빠진 원인을 설명하는 기술적 근거다.
  - "할인(γ)을 빼도 탐색 비용, 적응 시간, 첫 5분 WAF에서 차이를 확인하지 못했다."
    - 예외: 단계 C 탐색 비중은 약간 높다.
- 쓰면 안 되는 것:
  - "V4가 부하 변화에 더 빨리 적응한다." Greedy는 단계 C 첫 5분 WAF가 오히려 낮다.
  - 적응 시간을 Greedy나 묶음 OFF와 비교하는 것.
- 한계:
  - n = 3이다.
  - 보조 지표이고 다중 비교 보정을 하지 않았다.
  - 고컴 검증 전이다.
