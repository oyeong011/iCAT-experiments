# E1 검증 상태 (자동 생성)

- 생성: 2026-11-24 12:29, `python3 -I analysis/final_e1/e1_analyze.py`
- 유효성 규칙: `analysis/final_e1/validity.py`. 실패한 YCSB 단계와 그 뒤 단계는 통계에서 뺀다. 다른 배치끼리는 합치지 않는다.
- `claim_allowed=yes`는 정책별·v4 모두 n ≥ 3이고 Welch 95 % CI가 0을 포함하지 않을 때만이다.

## 실행별 유효성

| 배치 | 정책 | rep | 쓸 수 있는 단계 | 전체 WAF | A | B | C | C reset | YCSB 적재 | YCSB READ 성공 % | UPDATE 성공 % | YCSB ops/s | 사유 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| result/mix-20260911/rec600k | onlinev4 | 1 | A | 제외 | 1.899476 | 제외 | 제외 | 제외 | 600000 | 0.166 | 100.000 | 12891.8 | YCSB ycsb-run-B.txt.gz: worst op failed 99.83% |
| result/mix-20260911/rec600k | onlinev4 | 2 | A | 제외 | 1.901916 | 제외 | 제외 | 제외 | 600000 | 100.000 | 90.025 | 8652.5 | YCSB ycsb-run-B.txt.gz: worst op failed 9.98% |
| result/revision-20261123/mixR/rec600k | onlinev4 | 1 | A | 제외 | 1.902747 | 제외 | 제외 | 제외 | 600000 | 0.167 | 100.000 | 12910.3 | INVALID-20261124 lists phases B,C | YCSB ycsb-run-B.txt.gz: worst op failed 99.83% |
| result/revision-20261123/mixR/rec600k | onlinev4 | 2 | A | 제외 | 1.896127 | 제외 | 제외 | 제외 | 600000 | 0.166 | 100.000 | 13143.3 | INVALID-20261124 lists phases B,C | YCSB ycsb-run-B.txt.gz: worst op failed 99.83% |
| result/revision-20261123/mixR/rec600k | onlinev4fullreset | 1 | A | 제외 | 1.894832 | 제외 | 제외 | 제외 | 600000 | 0.166 | 100.000 | 13214.6 | INVALID-20261124 lists phases B,C | YCSB ycsb-run-B.txt.gz: worst op failed 99.83% |
| result/revision-20261123/mixR/rec600k | onlinev4nodrift | 1 | A | 제외 | 1.904017 | 제외 | 제외 | 제외 | 600000 | 100.000 | 90.017 | 8885.3 | INVALID-20261124 lists phases B,C | YCSB ycsb-run-B.txt.gz: worst op failed 9.98% |
| result/revision-20261123/mixR/rec600k | onlinev4nodrift | 2 | A | 제외 | 1.905493 | 제외 | 제외 | 제외 | 600000 | 0.168 | 100.000 | 14662.6 | INVALID-20261124 lists phases B,C | YCSB ycsb-run-B.txt.gz: worst op failed 99.83% |

## 통계 (쓸 수 있는 값만)

| 배치 | 지표 | 정책 | n | 평균 | SD | 95 % CI | v4 대비 차이 | Welch 95 % CI | 주장 가능 |
|---|---|---|---|---|---|---|---|---|---|
| result/mix-20260911/rec600k | waf_A | onlinev4 | 2 | 1.9007 | 0.0017 | [1.8852, 1.9162] |  |  |  |
| result/mix-20260911/rec600k | ycsb_throughput | onlinev4 | 2 | 10772.1500 | 2997.6378 | [-16160.1229, 37704.4229] |  |  |  |
| result/revision-20261123/mixR/rec600k | waf_A | onlinev4 | 2 | 1.8994 | 0.0047 | [1.8574, 1.9415] |  |  |  |
| result/revision-20261123/mixR/rec600k | waf_A | onlinev4nodrift | 2 | 1.9048 | 0.0010 | [1.8954, 1.9141] | +0.0053 | [-0.0378, +0.0484] | no |
| result/revision-20261123/mixR/rec600k | waf_A | onlinev4fullreset | 1 | 1.8948 |  |  |  |  |  |
| result/revision-20261123/mixR/rec600k | ycsb_throughput | onlinev4 | 2 | 13026.8000 | 164.7559 | [11546.5510, 14507.0490] |  |  |  |
| result/revision-20261123/mixR/rec600k | ycsb_throughput | onlinev4nodrift | 2 | 11773.9500 | 4085.1680 | [-24929.2369, 48477.1369] | -1252.8500 | [-37985.8742, +35480.1742] | no |
| result/revision-20261123/mixR/rec600k | ycsb_throughput | onlinev4fullreset | 1 | 13214.6000 |  |  |  |  |  |
