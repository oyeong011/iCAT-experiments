# 승컴 arm47-20261127 (고정 Arm 47 반복) 고컴 독립 검증 (2026-11-27)

- 원시 자료: origin/main 4689c6797의 `result/arm47-20261127/raw/mixFYF-arm47-rep{1,2,3}`. git archive로 scratchpad에 풀어 읽기만 했다.
- 같이 넣은 비교 자료
  - 승컴 batchG bg-v4 (다른 배치)
  - 고컴 `result/revA-20261114/raw/mixFYF-arm47-rep1` (n=1)
- 도구: 고컴 `analysis/online_greedy/og_audit.py`. 승컴 `arm47_analysis.py`는 쓰지 않았다.
  - 출력: `og_audit.md`, `runs.csv`, `stats.csv`, `contrasts.csv`, `arms.csv`
  - `analysis/final_revision/complete_results.py`도 같은 원시 자료에서 다시 계산했고 값이 같았다.

## 유효성: 3/3 유효
- exit 0이다.
- 모듈 sha256 9fde0ea4…는 `modules.sha256`에 등록되어 있고, 고컴 revA 실행 때와 같은 파일이다.
- FIO seed가 rep 규칙과 맞다.
- YCSB 성공률 1.0, SQLITE_FULL 0, 커널 오류 0, FIO 오류 0이다.
- WAF를 두 경로로 계산한 값이 같고, 시작 카운터는 0이다.
- 커널 로그의 `Fixed CAT init ... arm=47`은 run마다 8줄이다. 다른 arm으로 초기화한 줄은 0이다.

## 결과 (승컴 값과 대조)

| 지표 | 승컴 n=3 (고컴 재계산) | 승컴 statistics.csv | 고컴 revA n=1 |
|---|---|---|---|
| 전체 WAF | 1.98764 ± 0.00027 [1.98698, 1.98831] | 같음 | 1.98735 (CI 안) |
| 단계 A / B / C | 1.77430 / 1.03098 / 2.27865 | 같음 | 1.77441 / 1.02657 / 2.27824 |
| 단계 C 첫 5분 | 2.27319 ± 0.00051 | 같음 | 2.25480 |

- 참고 비교로 bg-v4 − Arm 47을 냈다. +0.1228 [+0.0621, +0.1836]이고, 승컴 Arm 47 − bg-v4 = −0.123과 부호만 반대로 같다.
  - 다른 배치끼리 비교한 간접 비교다.
- 승컴 n=3과 고컴 n=1은 호스트가 달라서 합치지 않았다.
- 상태: 고컴 검증 결과 일치. 집컴 검증은 아직 하지 않았다.
