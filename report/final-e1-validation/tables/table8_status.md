# 표 8 · 그림 10 (3단계 균등 전환) 사용 금지

- 원자료 `result/mix-20260911/mixR-*-x3` 11개 run 중 단계 2·3이 유효한 run: 0개.
- 단계 1(FIO-Fast)만 유효하다. 단계 2(YCSB-A)와 단계 3, 전체 WAF는 YCSB SQLITE_FULL 오염으로 무효다.
- E1 재실험(`result/revision-20261124/mixR`, YCSB 300k records)에서 정책별로 유효한 3회가 모이기 전에는 표 8과 그림 10을 논문에 싣지 않는다.
- 재실험은 YCSB 레코드 수가 600k → 300k로 바뀌었다. 그래서 원래 표 8의 정책(CAT-Best, CAT-Robust, arm 17, iCAT, iCAT-v3, CAT-Default)과는 같은 조건이 아니다. 재실험은 v4 / nodrift / fullreset만 다룬다.

| run | 유효 단계 | 판정 |
|---|---|---|
| mixR-arm17-rep1-x3 | A | 무효(단계 2·3·전체): YCSB ycsb-run-B.txt.gz: worst op failed 99.83%; SQLITE_FULL in ycsb-run-B.txt.gz |
| mixR-arm32-rep1-x3 | A | 무효(단계 2·3·전체): YCSB ycsb-run-B.txt.gz: worst op failed 9.98%; SQLITE_FULL in ycsb-run-B.txt.gz |
| mixR-fixed37-rep1-x3 | A | 무효(단계 2·3·전체): YCSB ycsb-run-B.txt.gz: worst op failed 99.83%; SQLITE_FULL in ycsb-run-B.txt.gz |
| mixR-fixed47-rep1-x3 | A | 무효(단계 2·3·전체): YCSB ycsb-run-B.txt.gz: worst op failed 9.98%; SQLITE_FULL in ycsb-run-B.txt.gz |
| mixR-fixed50-rep1-x3 | A | 무효(단계 2·3·전체): YCSB ycsb-run-B.txt.gz: worst op failed 99.84%; SQLITE_FULL in ycsb-run-B.txt.gz |
| mixR-fixed50-rep2-x3 | A | 무효(단계 2·3·전체): YCSB ycsb-run-B.txt.gz: worst op failed 99.83%; SQLITE_FULL in ycsb-run-B.txt.gz |
| mixR-greedy-rep1-x3 | A | 무효(단계 2·3·전체): YCSB ycsb-run-B.txt.gz: worst op failed 99.83%; SQLITE_FULL in ycsb-run-B.txt.gz |
| mixR-online-rep1-x3 | A | 무효(단계 2·3·전체): YCSB ycsb-run-B.txt.gz: worst op failed 99.83%; SQLITE_FULL in ycsb-run-B.txt.gz |
| mixR-onlinev3-rep1-x3 | A | 무효(단계 2·3·전체): YCSB ycsb-run-B.txt.gz: worst op failed 9.99%; SQLITE_FULL in ycsb-run-B.txt.gz |
| mixR-onlinev4-rep1-x3 | A | 무효(단계 2·3·전체): YCSB ycsb-run-B.txt.gz: worst op failed 99.83%; SQLITE_FULL in ycsb-run-B.txt.gz |
| mixR-onlinev4-rep2-x3 | A | 무효(단계 2·3·전체): YCSB ycsb-run-B.txt.gz: worst op failed 9.98%; SQLITE_FULL in ycsb-run-B.txt.gz |
