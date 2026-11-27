# 용어 통일표 (고컴, 2026-11-27)

- 목적: Excel, 그림, 보고서, 논문 초안에서 같은 실험을 같은 이름으로 부른다.
- 조사 범위
  - `PAPER_KCI_DRAFT.md`
  - `report/final-revision/*.md`
  - `report/paper-figures-20261127/*.csv`
  - `result/*-verify/verify.md`
  - `analysis/final_revision/complete_results.py`의 그룹 라벨
  - 각 배치의 `preregistration.md` (정의 확인용)
- 이 문서는 표기만 정한다. 기존 Excel, CSV, 원시 디렉터리 이름은 바꾸지 않았다. 원시 경로와 run 이름은 기록이므로 그대로 둔다.
- 심사 요구사항 번호는 `review_evidence_and_status.md` §1을 따랐다.
  - M1 SmartGC 비교
  - M2 구성 요소 제거
  - M3 온라인 기준선
  - M4 반복·통계
  - M5 자원 효율
  - M6 적응·파라미터
  - M7 환경 일반화

## 1. 표기 규칙

- 그림 범례, 표 행, 본문 모두 아래 "최종 표기명"을 쓴다. 캡션에서는 `V4`, `v4`, `bg-v4` 같은 줄임말을 쓰지 않는다.
- 대조군을 밝혀야 할 때는 이름 뒤에 배치를 괄호로 붙인다. 예: `iCAT-v4 (배치 G)`.
  - 배치 문자는 논문 표 10을 따른다. A=revA, B=revB, C=revC, D=revD, D′=greedy, E=revE, F=abl, G=batchG.
  - Arm 47 반복은 표 10에 없으므로 `배치 H (arm47-20261127)`를 새로 제안한다. 논문에 넣을 때 확정한다.
- 호스트는 처음 한 번만 CPU로 밝힌다: 호스트 1 = Ryzen 5 3600XT (고컴), 호스트 2 = i7-7700 (승컴). 논문에 "고컴", "승컴"은 쓰지 않는다.
- 문턱은 두 종류가 있다. 이름에서 섞지 않는다.
  - **변화 감지 문턱** (Drift): 기본 25 %. 측정한 값은 12.5 %, 25 %, 50 %다.
  - **후보 제거 문턱** (Elim): 기본 15 %. 측정한 값은 10 %, 15 %, 25 %다.
  - "15 %"는 제거 문턱의 기본값이다. 변화 감지 15 %는 실행한 적이 없다.

## 2. 통일표

| 최종 표기명 | 현재 쓰인 다른 이름 | 한 줄 설명 | 심사 요구사항 |
|---|---|---|---|
| **iCAT-v4** | V4, v4, iCAT V4, `revA-v4`·`revC-v4`·`revD-v4`·`revE-v4`·`abl-v4`·`bg-v4`, `onlinev4`, `online-v4`, WATGC_V2 (커널 로그 접두어) | 제안 기법. 후보 45개에 대한 할인 UCB, 후보 제거 15 %, 수렴 후 정착, 변화 감지 25 %, 감지 후 제거된 후보만 복원, 이웃 probe. 배치마다 대조군으로 3회 다시 실행했다 | 전체 (모든 비교의 대조군) |
| **iCAT (원 구현)** | 원래 iCAT, 원 구현, `revC-online`, `mixFYF-online-rep*`, online iCAT | 원 저장소의 학습기. 후보 60개, 변화 감지 12.5 % | M3 |
| **Random Selection** | Random, random, 무작위 선택, `revA-random` | 매 판단 구간마다 후보 45개 중 하나를 균등 무작위로 고른다. 제거·정착·감지 없음 | M3 |
| **Online Greedy** | 탐욕 선택, Greedy (선택 규칙), `greedy-online`, `greedy` | 45개를 1회씩 평가한 뒤, 매 판단 구간 할인 없는 누적 평균 WAF가 가장 낮은 arm을 고른다 | M3 |
| **Greedy GC** | greedygc, GreedyGC, Greedy (논문 표 2·3장), "Greedy GC (학습 없음)" | 학습 없이 유효 페이지가 가장 적은 블록을 희생 블록으로 고른다. arm을 고르는 정책이 아니라 희생 블록 선택 규칙이다 | M3 |
| **NoDrift** | V1, `revA-v1`, 변화 감지 없음, 감지 끔, `revD-nodrift`, `online-v4nodrift` | 변화 감지를 끈다(VARIANT 1). 재설정이 일어나지 않는다. revA V1과 revD NoDrift는 같은 소스다 | M2, M6 |
| **FullReset** | fullreset, 전체 재설정, 전체 리셋, `revD-fullreset` | 변화를 감지하면 제거된 후보만이 아니라 45개를 모두 복원한다 | M2, M6 |
| **NoElim** | noelim, 실행 중 제거만 끔, 제거 끔, `revB-noelim`, `revE-noelim` | 후보 제거만 끈다(VARIANT 3). 정착, 감지, probe는 켜져 있다. revB와 revE는 같은 모듈이다 | M2 |
| **NoSettle** | nosettle, 정착 끔, `revB-nosettle` | 정착을 끈다(VARIANT 5). 감지와 probe는 정착이 전제라 함께 꺼진다. 대조군이 n=1이라 통계에 쓰지 않는다 | M2 (보조) |
| **NoElim+NoSettle** | V2, `revA-v2`, 제거·정착 없음, 묶음 끔, offbundle, `abl-off-elim-settle-drift-probe`, "제거·정착·변화 감지·탐색 묶음 끔" | 후보 제거와 정착을 끈다(VARIANT 2). 감지, 재탐색, probe는 구조상 함께 꺼진다. 45개 전체에 할인 UCB만 남는다 | M2 |
| **NoDiscount** | nodiscount, 할인 없음, 할인 끔, `abl-nodiscount` | 할인 계수 γ를 1로 바꾼다. 나머지는 iCAT-v4와 같다 | M2, M6 |
| **Drift12.5** | drift12, `revE-drift12`, 감지 문턱 12.5 %, 변화 감지 임계값 12.5 % | 변화 감지 문턱을 25 %에서 12.5 %로 낮춘다. 원 구현 iCAT의 값과 같다 | M6 |
| **Drift50** | drift50, `drift50`, 감지 문턱 50 %, 변화 감지 임계값 50 % | 변화 감지 문턱을 25 %에서 50 %로 올린다 | M6 |
| **Elim10 / Elim25** | elim10, elim25, 제거 임계값 10 % / 25 %, 제거 문턱 10 % / 25 % | 후보 제거 문턱을 15 %에서 10 % 또는 25 %로 바꾼다 | M6 |
| **Arms60** | arm60, 60 arms, 후보 60개, `revB-arm60` (revC에서도 같은 run 이름) | 후보 축소(k=2 제외)를 풀어 60개로 학습한다 | M6 |
| **Arm 47** | arm47, Arm47, 고정 Arm 47, CAT-47, CAT-Best, Fixed CAT arm=47, `mixY-sg-arm47` | 학습 없이 고정한 CAT 조합 (k, s, r) = (10, 25 %, 16). 원 저장소 기록에서 FIO-Fast 최상위였던 조합이다 | M3 보조, M4 (반복 재현성) |
| **SmartGC-EQ8** | smartgc-eq8, SmartGC EQ8 | SmartGC 재구현 중 식 8의 블록별 행동 선택을 따른 판. M1의 대표 비교 대상이다 | M1, M5 |
| **SmartGC-Rank** | SmartGC, SmartGC 순위 목록, `mixY-smartgc` | SmartGC 재구현 중 Q값 순위로 희생 목록을 만든 판. 사전 규칙에 따라 대표에서 빠졌다 | M1 |
| (쓰지 않음) | SmartGC-Q, `mixY-smartgcq` | 고컴 gocom-sg 보조 run. 정의를 이 문서에서 다시 확인하지 못했다. 논문에 쓰지 않는다 | — |

## 3. 발견한 불일치와 정리 방법

1. **V2와 "묶음 끔"은 같은 정책이다.**
   - revA V2와 abl `off-elim-settle-drift-probe`는 둘 다 `ICAT_VARIANT=2`다. abl 사전 등록 33행에 "고컴 revA V2와 같은 VARIANT"라고 적혀 있다.
   - 논문 표 10은 배치 A에서 "제거·정착 없음", 배치 F에서 "제거·정착·변화 감지·탐색 묶음 끔"으로 다르게 적었다. 그래서 다른 실험처럼 읽힌다.
   - 정리: 두 행 모두 **NoElim+NoSettle**로 쓰고, 설명란에 "감지·probe는 구조상 함께 꺼짐"을 붙인다.
   - 결과도 일관된다: 배치 A +0.135 [+0.117, +0.154], 배치 F +0.124 [+0.073, +0.175]. 다만 호스트가 달라 합치지 않는다.
2. **V1과 NoDrift는 같은 정책이다.** 표 10은 두 행 모두 "변화 감지 없음"이다. Excel은 "V1 (변화 감지 끔)"과 "NoDrift"로 다르게 적었다. **NoDrift**로 통일한다.
3. **"Greedy"가 두 정책을 가리킨다.**
   - 논문 2장 표와 3장의 "Greedy"는 희생 블록 선택 규칙이다 = **Greedy GC**.
   - 표 10 D′의 "탐욕 선택"은 arm 선택 규칙이다 = **Online Greedy**.
   - 정리: 논문 전체에서 맨 이름 "Greedy"를 쓰지 않는다.
4. **Arm 47의 이름이 세 개다.** 2장은 CAT-Best, 표 9는 CAT-47, 리비전 보고서는 고정 Arm 47이다.
   - 정리: 처음 나올 때 "고정 Arm 47 (CAT-Best)"로 쓰고, 이후 **Arm 47**로 쓴다.
5. **run 이름 `online`은 Online Greedy가 아니다.** `mixFYF-online-rep*`은 iCAT (원 구현)이다. Online Greedy의 run 이름은 `mixFYF-greedy-online-rep*`이다. 원시 경로를 인용할 때 헷갈리지 않게 최종 표기명을 같이 적는다.
6. **revA V1/V2는 논문의 iCAT-v1/iCAT-v2가 아니다.** revA 사전 등록 15행에 이 주의가 있다. 논문의 iCAT-v2는 판단 구간을 3배로 늘린 이전 버전이다. 리비전 결과에서 "V1", "V2"를 쓰지 않는 이유가 이것이다.
7. **`drift12`는 12.5 %다.** 키 이름이 소수점을 잘랐다. 표기는 **Drift12.5**로 한다.
8. **변화 감지 15 %는 없다.** 감지 문턱 실험을 "12.5 / 15 / 25 / 50 %"로 쓰면 안 된다. 측정한 값은 12.5 / 25 / 50 %다.

## 4. 이름이 아닌 공통 용어

| 최종 표기 | 쓰지 않을 표기 | 뜻 |
|---|---|---|
| 전체 WAF | total WAF, WAF_total | 1 + GC 쓰기 / 호스트 쓰기, 측정 구간 전체 |
| 단계 1 / 2 / 3 WAF | phase A/B/C, 단계 A/B/C | mixFYF의 FIO-Fast / YCSB-A / FIO-Fast 구간. 논문 표 10은 "단계 3"을 쓴다. Excel과 CSV는 A/B/C다 (A=1, B=2, C=3) |
| 단계 3 첫 5분 WAF | C5, waf_C5, phase-C first-5-min | 두 번째 전환 직후 300초의 WAF (control-series 30초 표본) |
| WAF_nand | WAF (SmartGC 비교에서) | NAND 쓰기 기준 WAF. SmartGC가 DRAM 버퍼로 일부 쓰기를 흡수하므로 M1에서만 쓴다 |
| 같은 배치 비교 (직접 비교) | 동일 조건 비교 | 같은 호스트에서 연속 실행하고, 대조군 iCAT-v4를 같은 배치에서 새로 3회 실행한 비교 |
| 간접 비교 | 교차 배치, cross-batch | 대조군이 다른 배치의 iCAT-v4인 비교. Online Greedy (배치 D 대조), Arm 47 (배치 G 대조) |
| 구분되지 않음 | 동등함, 차이 없음, 같음 | Welch 95 % CI가 0을 포함한다. 동등하다는 뜻이 아니다 |
| 차이 있음 | 유의함, 우수함 | Welch 95 % CI가 0을 포함하지 않는다. Holm p를 같이 적는다 |
| ktime 경과 시간 | CPU 시간, CPU 사용량 | 커널 구간 타이머로 잰 벽시계 시간 |
| 계산값 / 실측값 | (구분 없이) 메모리 사용량 | 계산값은 DWARF 구조체 크기, 실측값은 VmallocUsed 증가량(시스템 전체) |
