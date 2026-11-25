# Online Greedy 비교 실험: 고컴 독립 검증 (설계 검토 단계)

- 작성: 고컴, 2026-11-25 11:30경. 고컴은 검증만 한다. 신규 NVMeVirt 실험은 실행하지 않는다.
- 대상: 승컴 commit `860e3e4a9`, `800817c3a`, `bf4654a9a` (origin/main)
  - `result/greedy-20261125/` (사전 등록, 구현 검토, 러너)
  - `greedy-src/`
  - `analysis/revision/greedy_analysis.py`
- 상태: 승컴 본 실험은 **시작 전**이다. 사전 등록 기준으로 추가 ablation 큐가 끝난 뒤, 11-26 00:50 이후에 시작한다.
- 판정 표기:
  - **PASS:** 코드나 자료로 확인했다
  - **PASS (실행 후 재확인):** 코드상 맞고, 실행 로그로 한 번 더 확인한다
  - **미검증:** 지금 자료로는 확인할 수 없다
  - **FAIL:** 설계와 구현이 다르다

## 1. 지시 §3 점검 항목 7개

| # | 점검 항목 | 판정 | 근거 (origin/main 기준) |
|---|---|---|---|
| 1 | 초기 45개 arm 평가가 정확한가 | **PASS (실행 후 재확인)** | `conv_ftl.h:64` `WATGC_V2_MIN_VISITS 1U`.<br>`choose_search` 첫 루프는 방문 수가 가장 적은 arm을 고르고, 동률이면 작은 번호를 고른다. 방문 수가 1 미만이면 그 arm을 반환한다.<br>첫 창은 초기 arm 37이고 이어서 15, 16, …, 59(37 제외) 순서다. 그래서 커버는 45창에서 끝난다.<br>고컴 revA-v4 3회도 같은 코드 경로이고, 실측 커버 창이 4개 파티션 모두 45였다.<br>실행 후 확인: 첫 45창의 서로 다른 arm 수 = 45 |
| 2 | 평균 WAF 계산이 올바른가 | **PASS** | 추정량은 arm별 Σgc / Σhost(host 가중)다. V4의 `watgc_v2_waf_q16`을 바꾸지 않았다.<br>이 함수의 이진 나눗셈은 floor(gc·65536/host) + 65536과 같다. 승컴 재현식 `wq16 = 65536 + g*65536//h`과 정확히 일치한다.<br>합은 Q16으로 키운 값이다(host≪16, gc≪16). 비율은 그대로다 |
| 3 | 초기 탐색과 온라인 선택이 구분되는가 | **PASS** | Greedy 블록(`#if ICAT_VARIANT == 8`, conv_ftl.c:414–428)은 `visits < MIN_VISITS` 반환문 **뒤**에 있다. 그래서 커버가 끝나기 전에는 실행되지 않는다.<br>정착이 없으므로(6번) `observe`는 매 창 `choose_search`를 부른다(conv_ftl.c:657) |
| 4 | 동률 처리 방식이 고정돼 있는가 | **PASS** | 낮은 번호부터 돌면서 엄격한 `mean < lowest`일 때만 바꾼다. 그래서 동률이면 작은 번호가 남는다.<br>승컴 재현식 `min(ARMS, key=(wq16, i))`도 같은 규칙이다 |
| 5 | UCB와 Discount가 실제로 제거됐는가 | **PASS** | UCB: Greedy 블록이 UCB 계산과 stale 재방문보다 먼저 `return`한다.<br>Discount: γ를 곱하는 유일한 루프(conv_ftl.c:597–604)가 `#if ICAT_VARIANT != 8` 안에 있다. `watgc_v2_discount(` 호출은 그 루프의 3줄뿐이다(grep) |
| 6 | 후보 제거와 정착이 남아 있지 않은가 | **PASS (실행 후 재확인)** | 제거 블록과 정착 조건에 `ICAT_VARIANT != 8`이 추가됐다.<br>변화 감지(conv_ftl.c:579)와 probe는 `settled`일 때만 동작하므로 도달할 수 없다. 리셋도 일어나지 않는다.<br>`active`는 초기값 45개에서 바뀌지 않는다.<br>실행 후 확인: 로그의 elim = 0, reset = 0, settled 0건, active = 45 |
| 7 | 실제 실행 모듈이 검토한 소스에서 빌드됐는가 | **미검증** | 확인된 것:<br>- `sources.sha256`의 conv_ftl.c, conv_ftl.h, Kbuild 해시가 git의 greedy-src 내용과 일치한다(고컴 재계산)<br>- greedy-src의 나머지 파일은 revD-src와 바이트까지 같다<br>- 승컴 objdump 비교(V4 경로 0줄)는 승컴의 진술이다<br>확인 못 한 것:<br>- **모듈 파일 `nvmev-greedy-online.ko`(4df03c90…)가 git에 없다.** 고컴은 이 해시와 소스 사이의 연결을 독립적으로 확인할 수 없다<br>실행 후 확인할 것:<br>- `environment.txt`의 모듈 해시 = 4df03c90…<br>- 커널 init 줄의 `revA_variant=8`<br>- Greedy 규칙 재현 불일치 0 |

**결론**
- 설계와 구현이 다른 곳(FAIL)은 없다.
- 7번은 모듈 파일이 없어서 **미검증**이다. PASS로 처리하지 않는다.

## 2. 그 밖의 발견 사항 (FAIL은 아님, 보고서에 반영 필요)

| # | 내용 | 영향 | 권고 |
|---|---|---|---|
| a | `update_best`가 Greedy에서도 그대로 돈다. 그래서 로그의 `best=`는 0.5 % 지연 규칙이 적용된 값이고, Greedy가 실제로 고른 arm(`next`)과 다를 수 있다 | `best=`를 쓰는 지표(“최선이 아닌 arm을 평가한 창 비중”)는 Greedy에 쓸 수 없다 | 고컴 분석은 Greedy에서 이 지표를 n/a로 둔다. 탐색 비용은 모든 정책에 같은 정의(초기 커버 비용)를 쓴다. 승컴도 `select` 카운터를 쓴다고 명시했다 |
| b | V4 대조군 재사용 규칙의 문턱(|abl-v4 − revD-v4| ≤ 0.02, CI가 0 포함)이 느슨하다. 고컴 revA-v4의 SD는 0.005라 0.02는 약 4 SD다. n=3에서 "CI가 0을 포함"은 검정력이 낮아 쉽게 충족된다 | 재사용하면 Greedy − V4가 배치 간 비교가 된다(약 1일 차이) | 같은 배치에서 V4를 새로 돌리는 경로(`queue-order.with-v4.txt`, +4.7 h)가 더 깨끗하다. 재사용하면 보고서와 표에 "간접 비교(배치 다름)"로 표시한다 |
| c | 승컴 러너에 loadsampler가 없다. revD `checks.tsv`가 모두 `cpu_check=unavailable`이었고, greedy `check-run.py`도 같은 코드다 | NVMeVirt 전용 CPU 1·2 점유율과 경합을 확인할 수 없다 | 실행 전에 30 s 간격 loadsampler(고컴 revC와 같은 형식)를 붙이길 권한다. 결정은 승컴과 저자가 한다 |
| d | Random Selection(고컴)과 Greedy(승컴)는 호스트가 다르다. 승컴 단계 B의 YCSB 요청 수는 고컴의 약 72–78 %다(revD 1.08–1.17억 대 고컴 1.48–1.50억) | 두 정책은 직접 비교할 수 없다 | 승컴 사전 등록 §4와 같이 호스트별 "정책 − 같은 호스트 V4"만 나란히 둔다. 서로 빼지 않는다 |
| e | `choose_search` 주석 "Three real observations per arm"이 실제 값(MIN_VISITS 1)과 다르다 | 없음(주석) | 논문과 문서에는 "1회씩"으로 쓴다 |
| f | `queue.sh`는 `queue-order.registered.txt`를 읽는다. 이 파일은 V4 대조군 판단 뒤에 생긴다. 주석에는 "Smokes (120 s, 3 policies)"가 남아 있다 | 판단 전에 시작하면 큐가 비어 있다(안전한 쪽) | 판단 결과 파일 `control-decision.txt`와 `registered` 파일을 실행 전에 push하길 권한다 |

## 3. 기존 결과 감사 (지시 §2) — 진행 상황

- 스크립트: `analysis/online_greedy/og_audit.py` (고컴 독립 구현, e1_revd.py와 greedy_analysis.py 코드는 쓰지 않음)
- 산출: `result/online-greedy-analysis/`, `report/online-greedy-audit-data.md`

| 자료 | 상태 |
|---|---|
| 고컴 revA-random n=3 | **검증 완료.** 아래 항목이 3회 모두 맞다:<br>- 원시 로그 존재, exit 0<br>- 모듈 해시가 사전 등록과 일치(7d88c9a8…)<br>- mixFYF 부하 해시 일치<br>- FIO seed = 2026091x/2026101x/2026111x + rep, icat_seed = 2026111400 + rep<br>- YCSB 실패 0, SQLITE_FULL 0, 커널 오류 0<br>- WAF 두 경로 일치<br>전체 WAF 2.3243 ± 0.0055 |
| 고컴 revA-v4 n=3 | **검증 완료** (위와 같은 항목). 2.1284 ± 0.0049. Random − V4 = +0.196 [0.184, 0.208] (같은 배치, 기존 보고값과 일치) |
| 고컴 revC-v4 | rep1, rep2는 고컴 자동 검사 OK. **rep3은 실행 대기 중이다**(큐 마지막, 14:00경 종료). 큐가 끝난 뒤 검증한다 |
| 승컴 revD-v4 n=3 | 원시 자료(약 450 MB)는 고컴 큐가 끝난 뒤 내려받아 검증한다. 실행 중인 고컴 run에 I/O 부하를 주지 않기 위해서다 |
| 기존 Random vs V4 분석 | 승컴 `random_search.csv`의 [측정] 행이 위 고컴 재계산과 일치한다(2.3243, 2.1284). [추정] Random Search 행은 실측이 아니다 |
