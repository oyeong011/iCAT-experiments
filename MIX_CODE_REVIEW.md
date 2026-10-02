# 믹스 실험 준비 코드 리뷰 — 2026-09-07

대상: meendragon/iCAT commit `7236149a01efad760aed084acf5b270f5a0408f6`, 읽기 전용 별도 checkout `/tmp/icat-review-2KewI6/repo`.
판정: **REQUEST CHANGES / architecture BLOCK — 정식 비교 실험 전 수정 필요**.
검증: C/header/Kbuild/runner 정적 검토, 독립 구현·설계 리뷰, shell 스크립트 bash -n 통과. 새 소스 빌드/로드/워크로드 실행은 하지 않았다. 실행 중인 로컬 CAT batch와 해당 소스를 변경하지 않았다.

## 우선 발견 사항

1. **HIGH: 학습 코드가 기본 빌드에서 비활성화된다.** `nvmevirt_test/Kbuild:7,28-29,45`는 GREEDY를 기본으로 하며 온라인 정책 선택 분기가 없다. header의 온라인 기본값은 `-DCONV_GC_POLICY=0`에 의해 무효화된다. 삼성 SSD는 이미 `Kbuild:3,21`에서 선택돼 있다. 명시적 online 분기와 로드 후 정책 확인이 필요하다.
2. **HIGH: static CAT 빌드 옵션이 새 헤더와 충돌한다.** `Kbuild:41-43`이 전달하는 CAT_FIG7_* 매크로를 `conv_ftl.h:22-23`이 #error로 거부한다. 기존 build.sh도 이전 매크로를 검사한다. 임의 action을 고정해 온라인 경로와 비교하는 인터페이스도 필요하다.
3. **HIGH: 개별 runner 동시 실행은 장치 수명주기를 충돌시킨다.** `script/sqlite.sh:400`, `script/filebench.sh:500` 각각 start_virt를 호출한다. `start_virt.sh:7,10-26`은 고정 /dev/nvme1n1을 대상으로 모듈 제거/로드/포맷하며 장치 정체와 insmod 성공에 대한 안전한 중단 검증이 없다. 기존 runner를 병렬로 실행하지 말고 하나의 검증된 장치 소유 runner 아래 component-only 작업을 실행해야 한다.
4. **MEDIUM / 실험 gate: 공통 측정 경계가 없다.** `conv_ftl.c:1452-1454`는 partition별 100회 GC 후 측정을 시작한다. 준비 데이터가 포함되거나 정책마다 다른 입력 위치에서 집계될 수 있다. 로컬 측정 start/stop과 최신 learner를 검증하며 통합해야 한다. 학습 초기화와 측정 초기화도 분리해야 한다.
5. **설계 BLOCK: Q-learning이라는 설명과 구현이 다르다.** `conv_ftl.c:140-145,269-286,394-412`는 discounted UCB 계열 bandit이다. 상태별 Q-table/Bellman update가 없고 gamma는 과거 통계의 망각 계수다. 코드 자체의 오류라기보다는 논문 주장과 실험 라벨의 불일치다.
6. **설계 WATCH: 기존 static 결과를 새 기준선으로 재사용할 수 없다.** `conv_ftl.c:65-67,1115`는 마지막 invalidation 이후 시간을 Age로 사용한다. 기존 로컬 실행은 생성 시각 기준이다. 새 `conv_ftl.c:55`는 가중치를 선형 보간하므로 이전 strong 계단 값과도 다르다. 동일 Age·점수·action 변환으로 static/online을 다시 비교해야 한다.
7. **MEDIUM: SQLite YCSB-F 실행 경로가 막혀 있다.** `script/sqlite.sh:364`, `script/run_all.sh:152-155`는 a/b/d만 허용한다. workloadf 파일 존재만으로 실행 지원이 완성된 것은 아니다. 경로 `/home/meen` 및 도구/binding도 현 호스트에 맞게 검증해야 한다.

## 정상적으로 연결된 부분 및 한계

- action 변경은 GC 완료 후 적용되고 다음 victim 비교가 새 파라미터를 읽는다 (`conv_ftl.c:1457,520-523,1291-1292`). 실행 검증 전의 정적 확인이다.
- reward 관측은 같은 구간의 host/GC delta를 사용하며 Q16 WAF로 변환한다. 작은 구간은 폐기한다 (`conv_ftl.c:473-506`). 원시 정수와 독립 계측을 대조하는 테스트는 아직 필요하다.
- host 분모는 touched FTL pages (`conv_ftl.c:1643-1645`)이다. 혼합 앱의 sub-page writes를 허용하면 host bytes 기반 WAF와 다르므로 byte 계측 또는 alignment 검증이 필요하다.
- burn-in은 learner 관측에는 제외되지만 전체 비교 WAF에는 포함해야 한다.
- drift reset은 arm 통계를 지운다 (`conv_ftl.c:305`). A→B→A에서 과거 A를 기억한다고 미리 주장하면 안 된다.
- 추가 arm 통계는 60 × 5 × 8 = 2,400 bytes/partition, 4 partitions에서 9,600 bytes + metadata이다. 전체 FTL 메모리가 일정한 것은 아니다.

실행 계획: [MIX_EXPERIMENT_PLAN.md](MIX_EXPERIMENT_PLAN.md). 이번 요청은 계획/리뷰이므로 위 문제를 자동 수정하거나 새 믹스 실험을 실행하지 않았다.
