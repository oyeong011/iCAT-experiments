# 집컴 독립 검증 요청: batchG-20261126 (M3·M6, 승컴)

승컴 내부 검증만 끝났다. 아래를 **승컴 코드를 쓰지 않고** 다시 계산해 일치 여부를 회신해 주기 바란다.

1. 원시 카운터에서 WAF 재계산 (9 run, 전체와 단계 A/B/C)
   - 입력:
     - `result/{batchG-20261126,drift50-20261126,greedygc-20261126}/raw/mixFYF-*-rep[123]/`
     - 그 안의 `phase-{A,B,C}-{start,end}.txt`, `stopped.txt`
   - 정의: 1 + Δgc_pages / Δhost_pages. 각 파일의 첫 줄(control 합계)을 쓴다.
   - 대조값: `runs.csv`의 `total_waf, A_waf, B_waf, C_waf`
2. 유효성
   - exit-code 0
   - `ycsb-run-B.txt.gz`의 READ+UPDATE `Return=OK` = Operations, SQLITE_FULL 0
   - FIO json `error` 0
   - kernel.log에 BUG/WARNING/Oops 0
   - environment.txt의 모듈 sha256이 `result/batchG-20261126/modules.sha256`과 같은지
3. 통계 (`contrasts.csv`)
   - 대비: greedygc − bg-v4, drift50 − bg-v4 (total_waf, C_waf)
   - Welch 95 % CI, p, Hedges' g
   - 위 4개에 대한 Holm 보정
4. drift50 리셋 (`reset_events.csv`)
   - 모든 리셋에서 |sample − reference| / reference > 0.5 인지
   - kernel.log `WATGC_V2 reset ... reference_q16= sample_q16=` 줄로 확인한다
5. 고컴 참고값
   - `origin/report/data-validity-20261124` bba0886e9의 `result/revE-20261125/raw`에서 revE-drift12 − revE-v4를 계산한다
   - 승컴과 합산하지 않는다

승컴 커밋: 원시 로그는 run별 커밋 (a25b74687 … 8f621a451, 큐 종료 e61d6b697)에 있다. 분석은 이 파일이 들어간 커밋에 있다.
