# E1 검증 상태 (자동 생성)

- 생성: 2026-11-24 12:58, `python3 -I analysis/final_e1/e1_analyze.py`
- 유효성 규칙: `analysis/final_e1/validity.py`. 실패한 YCSB 단계와 그 뒤 단계는 통계에서 뺀다. 다른 배치끼리는 합치지 않는다.
- `claim_allowed=yes`는 정책별·v4 모두 n ≥ 3이고 Welch 95 % CI가 0을 포함하지 않을 때만이다.

## 실행별 유효성

| 배치 | 정책 | rep | 쓸 수 있는 단계 | 전체 WAF | A | B | C | C reset | YCSB 적재 | YCSB READ 성공 % | UPDATE 성공 % | YCSB ops/s | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| result/mix-20260911/rec600k | onlinev4 | 1 | A | 제외 | 1.899476 | 제외 | 제외 | 제외 | 600000 | 0.166 | 100.000 | 12891.8 | YCSB ycsb-run-B.txt.gz: worst op failed 99.83% | SQLITE_FULL in ycsb-run-B.txt.gz |
| result/mix-20260911/rec600k | onlinev4 | 2 | A | 제외 | 1.901916 | 제외 | 제외 | 제외 | 600000 | 100.000 | 90.025 | 8652.5 | YCSB ycsb-run-B.txt.gz: worst op failed 9.98% | SQLITE_FULL in ycsb-run-B.txt.gz |
| result/revision-20261123/mixR/rec600k | onlinev4 | 1 | A | 제외 | 1.902747 | 제외 | 제외 | 제외 | 600000 | 0.167 | 100.000 | 12910.3 | INVALID-20261124 lists phases B,C | YCSB ycsb-run-B.txt.gz: worst op failed 99.83% | SQLITE_FULL in ycsb-run-B.txt.gz |
| result/revision-20261123/mixR/rec600k | onlinev4 | 2 | A | 제외 | 1.896127 | 제외 | 제외 | 제외 | 600000 | 0.166 | 100.000 | 13143.3 | INVALID-20261124 lists phases B,C | YCSB ycsb-run-B.txt.gz: worst op failed 99.83% | SQLITE_FULL in ycsb-run-B.txt.gz |
| result/revision-20261123/mixR/rec600k | onlinev4fullreset | 1 | A | 제외 | 1.894832 | 제외 | 제외 | 제외 | 600000 | 0.166 | 100.000 | 13214.6 | INVALID-20261124 lists phases B,C | YCSB ycsb-run-B.txt.gz: worst op failed 99.83% | SQLITE_FULL in ycsb-run-B.txt.gz |
| result/revision-20261123/mixR/rec600k | onlinev4nodrift | 1 | A | 제외 | 1.904017 | 제외 | 제외 | 제외 | 600000 | 100.000 | 90.017 | 8885.3 | INVALID-20261124 lists phases B,C | YCSB ycsb-run-B.txt.gz: worst op failed 9.98% | SQLITE_FULL in ycsb-run-B.txt.gz |
| result/revision-20261123/mixR/rec600k | onlinev4nodrift | 2 | A | 제외 | 1.905493 | 제외 | 제외 | 제외 | 600000 | 0.168 | 100.000 | 14662.6 | INVALID-20261124 lists phases B,C | YCSB ycsb-run-B.txt.gz: worst op failed 99.83% | SQLITE_FULL in ycsb-run-B.txt.gz |

## 통계 (쓸 수 있는 값만)

| 배치 | 지표 | 정책 | n | 평균 | SD | 95 % CI | v4 대비 차이 | Welch 95 % CI | 주장 가능 |
|---|---|---|---|---|---|---|---|---|---|
| result/mix-20260911/rec600k | waf_A | onlinev4 | 2 | 1.9007 |  |  |  |  | n<3: 통계 없음 |
| result/mix-20260911/rec600k | ycsb_throughput | onlinev4 | 2 | 10772.1500 |  |  |  |  | n<3: 통계 없음 |
| result/revision-20261123/mixR/rec600k | waf_A | onlinev4 | 2 | 1.8994 |  |  |  |  | n<3: 통계 없음 |
| result/revision-20261123/mixR/rec600k | waf_A | onlinev4nodrift | 2 | 1.9048 |  |  |  |  | n<3: 통계 없음 |
| result/revision-20261123/mixR/rec600k | waf_A | onlinev4fullreset | 1 | 1.8948 |  |  |  |  | n<3: 통계 없음 |
| result/revision-20261123/mixR/rec600k | ycsb_throughput | onlinev4 | 2 | 13026.8000 |  |  |  |  | n<3: 통계 없음 |
| result/revision-20261123/mixR/rec600k | ycsb_throughput | onlinev4nodrift | 2 | 11773.9500 |  |  |  |  | n<3: 통계 없음 |
| result/revision-20261123/mixR/rec600k | ycsb_throughput | onlinev4fullreset | 1 | 13214.6000 |  |  |  |  | n<3: 통계 없음 |
