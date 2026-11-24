# 승컴 E1(v4nodrift)·E2(random45)와 고컴 revA의 중복 판정

- 작성: 2026-11-23 23시대, 고컴.
- 대조 대상:
  - 승컴: main `2f6ae2dec`의 `online-v4nodrift-src`, `online-random45-src`, `script/revision-queue-20261123.sh`, `script/mix-20260911.sh`
  - 고컴: `revA-src`, `result/revA-20261114/runner-revA.sh`, revA 결과 (브랜치 `report/final-20261123`, push됨)
- **결론:**
  - **E2 random45는 사실상 중복이다. 생략을 권한다** (승컴 시간 약 7.5–9시간 절약).
  - **E1 v4nodrift는 중복이 아니다. 유지를 권한다.** 기존 revA 결과로는 결론이 나지 않았고, mixR×3은 다른 전환을 시험한다.

## 1. 대조표

| 항목 | 승컴 E1 v4nodrift | 고컴 revA-V1 | 승컴 E2 random45 | 고컴 revA-Random |
|---|---|---|---|---|
| 기반 소스 | online-v4-src (계측 없음) | revA-src = online-v4 + 계측 카운터 + 변형 분기 (정책 로직 동일, diff 87줄) | online-v4-src | revA-src |
| 바꾼 코드 | `DRIFT_WINDOWS 0xFFFFFFFF` (h:59). drift 카운터는 올라가지만 reset이 일어나지 않는다 | drift 검사 블록 전체를 건너뜀 (`conv_ftl.c:563`). reset이 일어나지 않는다 | observe()에서 보상을 누적한 직후 반환 (c:570–579). update_best, 제거, 정착을 하지 않는다 | 보상 누적 뒤 반환 (c:611–613). 정착은 c:536에서 금지, 제거도 하지 않는다 |
| 정책 동작 | **같다** (drift_windows는 reset 판단에만 쓰인다. c:467/500/513/540–543 확인) | ← | **같다**: 판단 구간마다 45개(arm 15–59) 중 균등 추첨, 학습 없음 | ← |
| 난수 | — | — | splitmix64(파티션, 구간 번호). **rep와 무관**해서 3회 모두 같은 추첨 순서다 | xorshift64*, seed = splitmix(icat_seed = 2026111400 + rep, 파티션). rep마다 순서가 다르다 |
| 탐색 공간 | 45 | 45 | 45 | 45 |
| 판단 구간 | 128 GC + 512 MiB | 같음 | 같음 | 같음 |
| 부하 | **mixR×3**: FIO-Fast(약 72 M 페이지) → YCSB-A 600k records, 42 M ops(약 72 M 페이지, 약 56분) → FIO-Fast | **mixFYF**: FIO-Fast 1800 s(72 M 페이지) → YCSB-A 250k records, 1800 s(약 5.7 M 페이지) → FIO-Fast 1800 s | mixR×3 | mixFYF |
| FIO seed | 20260910/20261010/20261110 + rep | 같음 | 같음 | 같음 |
| 준비 단계 | 6 GiB, 3 GiB randwrite seed 20260907 | 같음 | 같음 | 같음 |
| 호스트 | 승컴 i7-7700 | 고컴 Ryzen 3600XT | 승컴 | 고컴 |
| 반복 | 3 | 3 | 3 | 3 |
| 1회 시간 | 약 2.5–3 h (9월 mixR×3 측정 구간 1시간 56분 + 준비) | 약 1.5 h | 약 2.5–3 h | 약 1.5 h |
| 같은 배치 기준 V4 | E1의 onlinev4 ×3 | revA-v4 ×3 | 같음 | 같음 |

## 2. 판정

### E2 random45 → **실질적 중복, 생략 권장**

- 정책 동작이 같다. 탐색 공간, 판단 구간, 학습 없음이 모두 같다.
- 고컴 revA-Random(n=3)이 이미 분명한 결론을 냈다.
  - Random − V4 = **+0.196 [0.184, 0.208]**, Random이 9.2 % 나쁘다.
  - 세 구간 모두 Random이 나쁘다: FIO-Fast 1 +0.040, YCSB-A +0.022, FIO-Fast 2 +0.366. 모두 CI가 0을 포함하지 않는다.
- 남는 차이는 두 가지다.
  - (a) 부하 mixR×3 (YCSB-A 비중이 큼)
  - (b) 호스트
  - 둘 다 "무작위보다 학습이 낫다"는 결론을 바꿀 가능성은 낮다. 효과 크기가 이미 CI 폭의 16배다.
- random45 설계에는 약점이 있다. 난수 seed가 rep와 무관해서, **3회 반복이 같은 추첨 순서를 쓴다.** 그래서 n=3이어도 추첨에 따른 편차는 재지 못하고 장치 타이밍 편차만 잰다. 이 점에서는 revA-Random이 더 적절한 대조군이다.
- **권장:**
  - E2를 생략한다.
  - 다른 부하에서도 보이고 싶다면 1회만 남긴다. 그 1회는 "보조 관측"으로 보고하고, 통계적 결론은 revA-Random으로 낸다.
- 절약: 약 3회 × 2.5–3 h ≈ **7.5–9 h**

### E1 v4nodrift → **중복 아님, 유지 권장**

- 정책 동작은 revA-V1과 같다. 그러나 revA-V1은 **결론을 내지 못했다.**
  - V1 − V4 = +0.079 [−0.050, +0.207]로 구분 불가다.
  - V1의 FIO-Fast 2 구간 SD가 0.108로 크다.
- 부하가 시험하는 전환이 다르다.
  - mixFYF의 YCSB-A는 약 5.7 M 페이지로 작다(WAF 1.05). 사실상 FIO → FIO 재적응(B→C)만 시험한다.
  - mixR×3의 YCSB-A는 약 72 M 페이지(WAF 약 1.43)이고, 최적 arm도 FIO와 다르다(arm 17 대 47, 스크립트 주석). A→B 전환과 B→C 전환을 **둘 다** 시험한다.
  - 승컴 분석에 따르면 25 % drift 문턱은 YCSB-A 진입(WAF가 좋아지는 방향)을 놓친다. 이것은 mixR에서만 볼 수 있다.
- E1에는 revA에 없는 v4fullreset도 있다.
- **권장:**
  - E1은 그대로 진행한다.
  - 분석할 때 revA-V1(mixFYF)과 E1(mixR×3)을 "같은 변형, 다른 부하"로 함께 보고한다. 합산하지는 않는다.

## 3. 승컴에 전달할 내용 (요약)

> 고컴 브랜치 `origin/report/final-20261123`에 revA 원본과 결과가 있다 (`result/revA-20261114/`, 판정 근거 `report/revision-20261123-gocom/duplication_check_E1_E2.md`).
> 1. **E2 random45는 생략해 달라.** revA-Random(매 구간 45개 균등 추첨, rep별 seed, mixFYF n=3)이 같은 질문에 답했다. Random − V4 = +0.196 [0.184, 0.208]. random45는 seed가 rep와 무관해서 3회가 같은 추첨 순서를 쓴다. 다른 부하 관측이 꼭 필요하면 1회만 남긴다.
> 2. **E1 v4nodrift는 유지해 달라.** revA-V1(같은 동작)은 mixFYF에서 구분 불가였다(+0.079 [−0.050, +0.207]). mixR×3은 YCSB-A 비중이 커서 다른 전환을 시험한다.
> 3. 승컴 `random_selection_audit.md`의 "Random 구현과 결과 없음"은 고컴 자료를 반영해 고쳐야 한다.
> 4. 큐 순서상 random45 rep1은 11-24 오전에 시작할 예정이다. 생략하려면 그 전에 `script/revision-queue-20261123.sh`의 for 루프에서 `onlinerandom45`를 빼야 한다. 단기 확인 실행(smoke)은 이미 큐 앞쪽에 있다.

## 4. 승컴 결과가 올라오면 (독립 검증 계획)

- 대상 경로는 `result/revision-20261123/mixR/mixR-*-x3`이다. 승컴 큐가 run마다 commit과 push를 한다.
- 고컴이 원시 파일로 다시 계산할 항목:
  1. 종료 코드, FIO IO 수, YCSB 오류, 커널 오류로 유효성 확인
  2. WAF를 summary.txt와 control-series 두 경로로 계산
  3. v4 / v4nodrift / v4fullreset의 구간별 WAF, Welch 95 % CI
  4. reset·settled 시각에서 구한 감지 시각, 재정착 시간, 재탐색 구간 수 (shift와 drift 경로 구분)
  5. 회복 시간을 단측(승컴)과 양측(고컴) 두 정의로 모두 계산하고, 첫 창에서 바로 통과한 구간은 따로 표시
- 스크립트: `analysis/revision_gocom/verify_seungcom.py`를 확장하고, 결과는 `result/revision-gocom-20261123/`에 새 파일로 쓴다. 기존 파일은 덮어쓰지 않는다.

## 무효 고지 (2026-11-24, 고컴)

> **[2026-11-24 무효 고지, 고컴]** 이 문서가 인용한 YCSB 포함 run(9월·11-23 mixR, 9월 mixA)은 YCSB `SQLITE_FULL` 오염으로 YCSB 단계와 그 뒤 단계, 전체 WAF가 무효다. 근거: `report/final-e1-validation/README.md`, 승컴 `result/revision-20261123/mixR/INVALID-20261124.txt`. 아래 원문은 기록으로 남겨 두고 수정하지 않는다.

- 이 문서에서 영향받는 부분: mixR×3의 YCSB-A 수치(약 72 M 페이지, WAF 약 1.43)와 9월 mixR 측정 시간. 중복 판정(E1 유지, E2 생략)의 논리는 코드와 설계 비교라서 그대로 유효하다.
