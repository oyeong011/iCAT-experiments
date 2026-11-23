# Revision 독립 감사: E1 코드 감사 · 재현성 · 무결성 (고컴)

- 작성: 2026-11-23, 고컴.
- **NVMeVirt 모듈은 로드하지 않았고 부하 실험도 하지 않았다.** 소스 비교와 크기 확인용 컴파일, 기존 결과 분석만 했다.
  - 컴파일은 scratch 디렉터리에서만 했다(`/tmp/claude-1000/e1b`, 저장소 밖).
- 관련 문서:
  - `random_v4_statistical_audit.md`, `cat47_baseline_audit.md`, `waf_recalculation_audit.md`, `revision_claim_evidence_matrix.md`
  - 앞서 작성한 `ablation_validation.md`, `parameter_sensitivity.md`, `resource_overhead_final.md`, `revision_evidence_check.md`, `duplication_check_E1_E2.md`

## 1. E1 코드 감사 (V4 / v4nodrift / v4fullreset)

기준 소스: `online-v4-src`. 승컴 mixY V4 모듈 db93f822와 같은 트리이고, 아래 줄 번호는 이 트리 기준이다.

### 1.1 소스 차이: 의도한 줄 하나씩

```
$ diff -r online-v4-src online-v4nodrift-src     → conv_ftl.h:59 한 줄
-#define WATGC_V2_DRIFT_WINDOWS 3U
+#define WATGC_V2_DRIFT_WINDOWS 0xFFFFFFFFU /* ablation (revision-20261123): change detection off; v4: 3U */

$ diff -r online-v4-src online-v4fullreset-src   → conv_ftl.c:459 한 줄
-	t->active = watgc_v2_grow(t->active);   /* v4: survivors + 1-step neighbours, not all arms */
+	t->active = WATGC_V2_ALLOWED;   /* ablation: reset restores all 45 arms */
```

두 트리 모두 나머지 파일(.c, .h, Kbuild, Makefile)은 `diff -r` 결과 차이가 없다.

### 1.2 바이너리 확인 (기계어 함수 단위 비교)

| 비교 | 방법 | 결과 |
|---|---|---|
| online-v4 대 v4nodrift | 세 소스를 같은 컴파일러와 경로로 빌드해 `objdump -d`를 함수 단위로 비교 | 다른 함수는 `do_gc`(학습기가 inline된 곳) **하나**이고, 그 안에서도 **명령 2개**만 다르다: `cmp $0x2,%edx; jbe` → `add $0x1,%edx; jne`. 곧 `drift_windows >= 3`이 `drift_windows == 0xFFFFFFFF`로 바뀌었다 |
| online-v4 대 v4fullreset (저장소의 실제 .ko: db93f822 대 9b4ac457) | 같은 방법 | 다른 함수는 `do_gc` 하나다. `watgc_v2_neighbour`는 grow 호출이 없어지면서 inline으로 흡수됐다. 그 밖의 함수는 모두 같다 |
| 같은 비교를 고컴에서 빌드한 fullreset으로 | 같은 방법 | 결과 같음 |

- **한계:** 승컴이 실제로 실행할 nodrift 모듈(SHA 094b7a38…, 승컴 일지)은 저장소에 없다. 그래서 바이너리를 직접 대조하지는 못했다. 같은 소스를 고컴에서 빌드한 결과로 대신 확인했다. 고컴 빌드의 SHA(7286c297…)는 빌드 경로가 달라 승컴 것과 다르다.

### 1.3 기능별 확인

| 질문 | V4 | v4nodrift | v4fullreset | 근거 (online-v4-src) |
|---|---|---|---|---|
| 변화 감지가 실제로 꺼졌는가 | 켜짐: 정착 상태에서 1등 arm의 구간 WAF가 기준과 25 % 넘게 다른 구간이 3번 이어지면 `watgc_v2_reset_epoch` 호출 | **꺼짐.** 카운터는 증가하지만 reset 조건은 `drift_windows == 0xFFFFFFFF`다. 즉 42.9억 구간이 연속으로 벗어나야 한다. mixR×3 한 run은 파티션당 약 1,000구간이다. 카운터는 c:500, 513, 542, 467에서 0으로 돌아간다 | 켜짐 (V4와 같음) | c:534–545, h:58–59 |
| 후보 제거가 같은가 | 첫 순회 뒤 매 구간 15 % 제거 | **같음** (코드 변경 없음, 기계어 동일) | **같음** | c:581–598, h:34 |
| 정착이 같은가 | 12구간 안정, 1등 확인 3회, 교체 문턱 0.5 % | **같음** | **같음** | c:489–520, h:53–55 |
| reset 시 후보 복구 방식 | 살아남은 후보와 그 1칸 이웃 (`watgc_v2_grow`) | reset이 일어나지 않음 | **45개 전부** (`WATGC_V2_ALLOWED`) | c:448–470 (459) |
| reset 시 함께 초기화되는 것 | arm 통계 60개 전부 0, epoch+1, best=current, 정착 해제 | — | V4와 같음 | c:457–469 |
| 정착 후 probe | 8구간마다 1등의 1칸 이웃을 시험하고, 그 이웃을 `active`에 다시 넣음 | **유지** | 유지 | c:606–618, 특히 613 |
| 오래된 후보 재방문 (240구간) | 정착 전 탐색 중에만 | 유지 | 유지 | h:57, c:414–416 |

- **해석 주의 1:** v4nodrift에도 **probe를 통한 부분 재탐색은 남아 있다**(c:613). 제거된 1칸 이웃이 다시 후보가 된다. 그래서 v4nodrift 대 V4는 "**reset을 통한 재탐색**"의 효과이지, 모든 재탐색의 효과가 아니다.
- **해석 주의 2:** v4fullreset 대 V4는 reset 뒤 "**복구 범위**"(살아남은 후보와 이웃 대 45개 전부)의 효과다. reset 빈도는 같으므로 감지 효과와는 분리된다.
- **고컴 revA-V1과의 관계:** revA-V1은 drift 블록 자체를 건너뛴다(`revA-src/conv_ftl.c:563`). v4nodrift와 동작은 같다. 계측 카운터와 변형 분기 외의 소스 차이는 없다.

## 2. 재현성·무결성 대조

| 캠페인 | 호스트 | Git commit (소스) | 모듈 SHA256 (앞 16자리) | 빌드 옵션 | seed | 실행 순서 | FIO / YCSB 설정 | 원본 로그 |
|---|---|---|---|---|---|---|---|---|
| revA-20261114 (mixFYF) | 고컴 | 작업 트리 c06a372a5 + 로컬 `revA-src` (브랜치에 커밋) | random 7d88c9a8, v1 50ee1c59, v2 c74e0714, v4 987d6204, arm47 9fde0ea4 | `make ICAT_VARIANT={9,1,2,4}` (`build-revA-*.log`) | FIO 20260910/20261010/20261110 + rep, icat 2026111400 + rep | rep 블록별 무작위 (`queue-order.txt`), 한 배치 11-14~15 | mix-test4.fio b5edbcc7, workloada c0aff8a2, 250k records | 원본 전체는 고컴 `/home/oy/iCAT/result/revA-20261114/raw` (kernel-snapshots 포함). 브랜치에는 snapshots와 YCSB 원문을 뺀 사본 |
| revB-20261122 (mixFYF) | 고컴 | 같은 작업 트리 + `revB-src` (revA 대비 3줄, `inputs/revB-vs-revA.diff`) | v4 7599cbd6, noelim b1663b47, nosettle 928896fb, arm60 b2a19db3 | `ICAT_VARIANT={4,3,5,6}` | revA와 같음 | revB-v4 먼저, 그다음 무작위 순서. arm60 rep2/3은 19:50에 결과를 보기 전 제외(사전 등록 변경 절) | 같음 | 위와 같은 방식 |
| sg-20261119 (고컴 SmartGC, mixY) | 고컴 | cbd444949 (워크트리) | smartgc da2ebcc0, smartgcq 3f0b2801, sg-greedy de4e038e, sg-arm47 2b39b358 | upstream `b()` 함수 | FIO 20260911… (rep1) | smartgc → smartgcq → greedy → arm47 | mix-test4.fio b5edbcc7. test3, varmail.f는 SHA 미기록 (9-14 이후 git 변경 없음) | kernel.log 172 MB는 zst로 보관 |
| v7-20261011-icat2 (mixY) | 고컴 | 10-11 icat2 | online-v7 eca51601 | — | rep1 | 1회 | 같음 | kernel.log.zst |
| 승컴 mixY (10월, 11월) | 승컴 | e41aa50ab, 29b5f116b, 5bd64c679, 01df84464 등 (`*.commit.txt`) | eq8 cd5432f9, smartgc 33eac944, sg-arm47 138024d0, v4 db93f822, fixed47 9fde0ea4 | `*.module.sha256` | rep1 | — | 같음 | 승컴 SmartGC 재개 run kernel.log는 zst. 실패 run 원본 보존 |
| 승컴 revision E0/E1 | 승컴 | 2f6ae2dec, 1b94a195a | nodrift 094b7a38, fullreset 9b4ac457, v4 db93f822 | — | rep 1..3 | v4/nodrift/fullreset 교대 (random45 제외) | mixR×3: 600k records, 42M ops | 진행 중 |

**무결성 확인 결과**
- 모든 run에서 `exit-code`, FIO IO 수, YCSB 오류, 커널 오류를 확인했다. revA와 revB 21회가 모두 유효하다.
- summary와 카운터는 35 run 모두 정확히 같다 (`waf_recalculation_audit.md`).
- revB 단기 실행 3회는 통계에서 제외했고, 원본은 보존했다.
- 승컴 실패 run(`gc-20261010/mixY-smartgc-rep1`, S13 중단)도 보존돼 있다.
- **고컴 쪽 미흡한 점:**
  1. revA/revB 소스는 git commit이 아니라 **커밋되지 않은 로컬 사본**으로 빌드했다. 이번 브랜치에 사본을 커밋해서 보완했다. 다만 빌드 시점 소스의 SHA를 모듈 SHA와 연결한 기록은 `build-*.log`와 `modules.sha256`뿐이다.
  2. FIO-Slow(test3)와 varmail.f의 파일 SHA가 run별 environment에 없다. 모두 git상 9-14 이후 변경이 없어서 내용은 확인된다.
  3. **filebench Varmail에는 seed가 없다.** 같은 rep라도 run마다 다른 난수를 쓴다. mixY의 반복 간 편차 원인 후보다 (`cat47_baseline_audit.md`).
  4. 브랜치 사본에서는 kernel-snapshots를 뺐다. 원본은 고컴 디스크에만 있다. 외부 보관이 필요하면 별도로 정해야 한다.

## 3. 논문 제출 전에 반드시 해결할 문제 / 현재 데이터로 해결할 수 없는 문제

### 3.1 제출 전에 반드시 해결 (데이터는 있고, 문서와 표기만 고치면 됨)

1. **V1 명칭 혼동:**
   - 논문의 V1(online-mix, 6가지가 다름), 고컴 revA-V1(drift만 끔), 승컴 v4nodrift는 서로 다른 것이다.
   - 논문 표에 소스 기준 정의를 적는다.
2. **"후보 제거 25 %" 표기 오류:** 코드상 15 %다(h:34). 25 %는 drift 문턱이다.
3. **회복 시간 정의 통일:**
   - 승컴(단측, 후반부 기준)과 고컴(양측, 마지막 600 s 기준)의 정의가 다르다.
   - 단측 정의에서는 106/170 구간이 첫 창에서 바로 통과한다. 이 구간을 회복 측정 대상에서 빼거나 따로 표시해야 한다.
4. **v7 reset 집계:** 104회는 drift 39회와 shift 65회의 합이다.
5. **SmartGC 메모리 배율:** 232배는 GC 버퍼를 포함한 값이다. 학습 전용끼리는 193배다(10,112 B 기준). 어느 정의인지 적는다.
6. **CPU 표기:**
   - 3.88 ms / 90분은 학습 결정 경로만의 측정값이다.
   - 0.97 s / 10 h와 9.4 ns/GC는 차분 계수를 빌린 추정값이다.
   - 시스템 CPU로 표현하지 않는다.
7. **CAT-47 기준선:** mixY 비교는 같은 11월 배치(3.233)로 한다. 10월 2.864와 섞지 않는다.
8. **브리지 불합격 공개:**
   - revB-v4는 revA-v4보다 +1.11 %, +4.8 SD였다.
   - V4 반복 간 편차가 revA 3회로 잰 것보다 클 수 있다는 점을 한계에 적는다.
9. **Random 비교 범위:** mixFYF 한 부하, n=3. E2는 생략됐다.

### 3.2 현재 데이터로 해결할 수 없는 문제 (새 실험이 필요하거나 결과를 기다려야 함)

| 문제 | 필요한 것 | 예상 시간 | 상태 |
|---|---|---|---|
| 변화 감지(reset)와 복구 범위 효과 | 승컴 E1 (v4 / nodrift / fullreset × 3, mixR×3) | 약 27 h 남음 | 진행 중 |
| CAT-47 10월/11월 차이 원인 | 승컴 E0 | 약 2.3 h | 진행 중 (결과 미도착) |
| 정착 효과 (제거가 켜진 상태) | nosettle n 추가 또는 V4·nosettle 같은 배치 재측정 | 3–6회 × 1.5 h = 4.6–9.2 h | 미계획 |
| 45개 제한 효과 | arm60 n=2 추가 | 2 × 1.5 h = 3 h | 미계획 |
| 판단 구간, 정착 조건, probe 주기 민감도 | 한 번에 하나만 바꾼 빌드 | 약 33 h (`parameter_sensitivity.md` §3) | 미계획 |
| γ, 제거 문턱, drift 문턱 민감도 | 승컴 E4 | 약 36 h | 미계획 (E1 뒤) |
| SmartGC 학습 CPU 실측 | 계측 빌드 | 1회 mixY 약 12 h | 미계획 |
| mixY 반복 간 편차 (Varmail seed 없음) | 같은 정책 mixY 반복 | 회당 10–12 h | 미계획 |
