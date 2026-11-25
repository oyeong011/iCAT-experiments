# m1-20261126 사용자 공간 CPU 벤치마크 결과 메모 (2026-11-26 04:50, 고컴)

## "SIM FAIL" 기록에 대하여 (검사 스크립트 오류, 실행 실패 아님)
- queue.log 04:25:18 "end sim benchmark: SIM FAIL"은 bench-sim.sh 14행 판정식 오류다.
  - 판정식: `grep -L 'invariants=ok' … && echo FAIL || echo OK`
  - GNU grep은 일치 줄이 있으면 -L로 나열한 파일이 없어도 exit 0을 돌려준다. 그래서 항상 FAIL이 찍힌다.
- 실제 결과: 12개 로그 모두 exit=0, invariants=ok.
  - 같은 seed에서 시계 모드 1과 2의 host/gc 페이지 수가 같다. 계측이 동작을 바꾸지 않았다.
- queue.log는 고치지 않았다. 이 메모로 정정한다.

## 조건
- 도구: 실제 conv_ftl.c를 구동하는 사용자 공간 드라이버. 부하는 zones, 8 GiB, 6배 덮어쓰기, CPU 11 고정, seed 1–3.
- **mixY가 아니다.** GC가 매우 잦은 합성 부하이다 (WAF: iCAT 7.16, SmartGC-EQ8 waf_nand 9.19).
- iCAT 학습기는 이 드라이버에서 판단 구간을 한 번도 끝내지 않았다 (windows=0). LEARN 값은 호출당 장부 기록 비용일 뿐이다. 구간 종료 시 UCB 결정 비용은 포함되지 않는다. 그 값은 커널 본 실행(mixY)에서 얻는다.
- 시계
  - 모드 2: CLOCK_MONOTONIC, 고정 코어, 빈 구간 보정값 약 41 ns. **주 결과로 쓴다.**
  - 모드 1: 스레드 CPU 시간. 호출 하나에 약 860 ns 시스템 호출 비용이 들고, 중첩 구간(GC 안의 SELECT, REWARD, BUF)마다 이 비용이 쌓인다. SmartGC의 GC 값이 모드 1에서 56.6 µs, 모드 2에서 7.6 µs로 부풀었다.
  - 그래서 모드 1은 단일 긴 구간(iCAT GC·SELECT, SmartGC step)의 교차 확인에만 쓴다. 두 모드는 iCAT GC 53.7 대 53.0 µs, SmartGC step 275 대 286 µs로 일치한다.
- 보정 후 음수이거나 50 ns 미만인 값은 "시계 분해능 이하"로 본다.

## 결과 (모드 2, seed 3개 평균, analysis/bench_summary.tsv)

| 항목 | iCAT-v4 | SmartGC-EQ8 |
|---|---|---|
| GC 호출 수 | 1.31 M | 1.69 M |
| GC 1회 (보정 후) | 53.0 µs | 7.6 µs |
| 희생 블록 선택 1회 | 48.9 µs (CAT 점수로 전 라인 검사) | 0.39 µs (상태 목록) |
| 학습·점수 갱신 | GC당 < 50 ns (분해능 이하, 구간 결정 미포함) | step 1회 286 µs × 1,540회. GC당 환산 0.26 µs |
| 보상 갱신 | 없음 | 분해능 이하 |
| GC 버퍼 연산 (흡수, 해제, 배출) | 없음 | 호출당 분해능 이하. 호출 수가 1억 3천만 회 |
| 호스트 1 GiB당 GC 경과 시간 | 1.55 s | 0.29 s |
| 프로세스 user CPU (getrusage, 드라이버 포함) | 75 s | 19–22 s |

- 해석 (불리한 결과를 그대로 적는다)
  - 이 합성 부하에서 iCAT-v4의 GC 1회 비용은 SmartGC-EQ8의 약 7배이다. 거의 전부가 고정 CAT과 같은 전 라인 점수 검사이다.
  - 학습기 자체(구간 장부)는 비용이 작다.
  - SmartGC는 step 1회가 비싸지만 드물다.
- 같은 부하에서 WAF는 iCAT이 더 낮았다 (7.16 대 9.19).
- 커널 단기 실행(mixY 3단계 × 120 s, ktime 경과 시간)도 같은 방향이다.
  - GC 1회: iCAT 91.0 µs, SmartGC 36.3 µs
  - 선택: iCAT 85.8 µs, SmartGC 31.8 µs
- 본 실행 6회의 ktime 값으로 최종 판정한다.
