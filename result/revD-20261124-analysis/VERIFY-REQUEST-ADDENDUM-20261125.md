# 고컴 검증 요청 추가 (2026-11-25)

- `stats.csv`의 `C_explore_windows`와 `C_resettle_s`는 사전 등록 지표 5와 정의가 다르다.
  - 이 두 값은 `recovery.py:events()`의 run 단위 정의로 계산했다: 가장 이른 리셋 → **아무 파티션**의 첫 정착.
  - 사전 등록 지표 5의 정의는 다르다: **같은 파티션**의 리셋 → 정착 구간의 sample 수 (파티션별 값과 합).
  - 사전 등록 정의에 맞춘 값은 `result/revision-20261125-analysis/e3_partition.csv`와 `e3_run.csv`에 있다.
  - `stats.csv`는 수정하지 않았다 (원본 보존).
- 주 대비(C_waf, total_waf)는 영향을 받지 않는다.
- 검증 요청 항목 6: 지표 5를 파티션 단위 정의로 독립적으로 다시 계산해 `e3_partition.csv`와 맞춰 주세요.
  - 승컴 V4 C_explore_windows_sum: 100 / 32 / 69
  - 승컴 FullReset C_explore_windows_sum: 202 / 258 / 184
