# abl-20261125 유효성 보고 (승컴)

- 본 실행 9회와 단기 실행 3회가 모두 `check-run.py`를 통과했다 (`queue.log`에 모두 `exit=0 check=0`, ABLQUEUEDONE 11-26 00:50:28).
- 각 run에서 확인한 항목:
  - 모듈 SHA256 (insmod 전 대조)
  - 단계 A/B/C 완료, FIO 오류 0, YCSB 실패 0, SQLITE_FULL 0
  - 커널 BUG/WARNING/Oops 0
  - WAF 두 경로 일치, 시작 카운터 0, sample window 연속성
  - 언로드와 umount
- `ablation_analysis.py`에서 다시 검사한 결과도 12개 run(abl 9 + revD-v4 3)이 모두 valid다 (`runs.csv`의 `valid`, `waf_paths_agree` 열).
- cpu_check는 `unavailable`이다. 사전 등록대로 CPU 오버헤드는 측정할 수 없으므로 `learner_ns`(ktime)로 대신한다.
- 단기 실행은 통계에 넣지 않았다.
