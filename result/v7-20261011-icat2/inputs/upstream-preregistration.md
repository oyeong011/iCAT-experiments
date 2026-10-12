## iCAT-v7: GC 횟수로만 판정 — 사전 등록 2026-10-11

- 이유: mixY v6 로그에서 512 MiB 판정 창 하나에 GC가 약 3,900번 일어남. 즉 "GC 128번" 조건은 항상 먼저 채워지고 판정 시점은 쓰기 512 MiB가 정함. 30분 구간당 파티션별 판정 횟수: Varmail 420, FIO-Fast 150, FIO-Slow 35 (후보 45개 한 바퀴도 못 돎) → v6가 mixY에서 CAT-47보다 14% 나쁨(3.265 vs 2.864).
- 변경(v6 대비 이것만): 판정 창 = GC 1,024번(쓰기 양 조건 없음), 버닝 = GC 256번(쓰기 양 조건 없음). 점수(창 WAF)·제거·변화 감지는 v6 그대로. 소스 `online-v7-src/`, 모듈 `buildoutput/nvmev-online-v7.ko` SHA256 `eca51601…`.
- 예상 판정 횟수(30분, 파티션당): FIO-Slow 약 300, FIO-Fast 약 1,300, Varmail 약 2,300.
- 실행: queue54(`script/gh-queue54-v7.sh`), queue53(baseline) 끝난 뒤 자동 시작. ① 90분 혼합(F V O, baseline과 동일) ② mixY 20구간(v6·CAT-47과 같은 순서). 결과 `result/v7-20261011/`.
- 판정: ① 60개 고정 CAT 순위 안 어디에 오는지, ② mixY에서 CAT-47(2.864) 대비 차이. 실패해도 기록 유지.
