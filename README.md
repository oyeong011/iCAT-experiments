# iCAT 실험 저장소

NVMeVirt(가상 SSD) 위에서 GC victim 선택 정책 **Greedy / CAT(고정 파라미터) / iCAT(온라인 학습)** 의 WAF를 비교한 실험 기록. 원본 코드·사전 결과는 https://github.com/meendragon/iCAT (commit 7236149). 이 저장소는 그 결과를 재분석하고, 이 머신에서 다시 돌린 모든 실험의 **원본 로그·스크립트·판정 기준**을 그대로 보관한다.

모든 실행은 `EXPERIMENT_LOG.md`에 **실행 전 사전 등록(목적·조건·판정 기준) → 실행 후 결과** 순으로 기록돼 있다. 실패도 지우지 않는다.

## 0. 워크로드 이름

| 이름 | 뜻 |
|---|---|
| test2 | fio, hot 1GB + cold 5GB, 합계 10k IOPS (2영역) |
| test3 | fio, hot 512MB / warm 1.5GB / cold 4GB, 6k/3k/1k IOPS (3영역, 느림) |
| test4 | test3와 같은 배치, IOPS 4배 (24k/12k/4k) (3영역, 빠름) |
| test5 | fio, 앞 2GB hot → 300초 뒤 뒤 4GB hot (hot 위치 이동) |
| sqlite-a/b/d | YCSB on SQLite: a=읽기50/수정50, b=읽기95/수정5, d=최신 읽기 |
| oltp / varmail / webserver / webproxy / videoserver | Filebench 프로필 |
| mixA / mixB / mixC | test4→sqlite-a(파일 유지) / sqlite-a→test4 / test3→test4 |

## 1. 무엇을 비교하나

| 정책 | 설명 |
|---|---|
| Greedy | 유효 페이지가 가장 적은 블록을 지움. age 안 봄 |
| CAT (고정) | `점수 = vpc / (ipc × AgeLevel)`. AgeLevel은 블록 나이를 k단계로 변환. 파라미터 (k, scale, ratio) 60조합 = arm 0~59 |
| iCAT (online, WATGC_V2) | 60 arm 중 discounted-UCB로 10초 단위 window마다 골라 바꿈 |

지표: **WAF = (host_pages + gc_pages) / host_pages** (SSD 내부 카운터, 낮을수록 좋음).

arm 번호 = ki×15 + si×3 + ri, k∈{2,4,7,10}, scale∈{25,50,100,200,400}, ratio∈{4,7,16}.
자주 쓰는 arm: **10** = (2,200,7) test4 최악 / **37** = (7,100,7) GitHub 기본 고정 / **47** = (10,25,16) test4 최적 / **50** = (10,50,16) 6개 워크로드 minimax.

## 2. 환경

- 커널 `7.0.0-31-generic`, NVMeVirt conventional SSD 8 GiB (memmap 4G~12G), cpus 1,2, ext4 nodiscard
- GitHub 원본 소스에는 이 머신에서 insmod 실패하는 큰 연속 메모리 할당이 2곳 있어 `kmalloc→kvmalloc`(ssd.c), `kzalloc→kvzalloc`(io.c)만 바꿨다. 정책 코드는 무변경. patch: `result/varmail-20260911/*.patch`
- 모듈 hash는 각 run의 `environment.txt` 또는 `result/gh-repro-20260914/modules.sha256`

## 3. GitHub 사전 결과 재분석 (새 실행 아님)

`analysis/gh-sweep-waf.py` → `result/gh-sweep-analysis-20260911/per-arm-waf.txt`

| workload | Greedy | 최저 arm | 최고 arm | 편차 |
|---|---:|---|---|---:|
| test3 | 2.026 | k07-s050-r07 1.689 | k02-s100-r07 2.038 | 20.7% |
| **test4** | 2.223 | k10-s025-r16 1.748 | k02-s200-r07 2.231 | **27.7%** |
| test5 | 1.635 | k10-s025-r04 1.529 | k02-s050-r16 1.633 | 6.8% |
| oltp | 1.659 | k10-s050-r07 1.576 | k07-s400-r16 1.698 | 7.7% |
| sqlite-a | 1.497 | k04-s025-r16 1.179 | k02-s400-r07 1.503 | 27.5% |
| sqlite-b | 1.282 | k10-s025-r16 1.074 | k02-s100-r16 1.284 | 19.6% |
| varmail | – | – | – | **무효** (파일 수가 run마다 24000/44000/150000으로 달라 비교 불가; 24000 그룹 내 편차 4.2%) |

발견:
- 모든 워크로드에서 최악 arm은 k=2이고 Greedy와 0.4% 이내 → "최악 CAT vs iCAT"은 사실상 "Greedy vs iCAT"
- 단일 고정 arm 50이 6개 워크로드 전부에서 최적 대비 3.7% 이내
- **GitHub 저장소 문제**: 60-arm sweep을 만든 소스는 어느 커밋에도 없음(HEAD는 고정 파라미터 빌드를 `#error`로 거부, Kbuild에 online 빌드 옵션 없음). 동봉 .ko 60개는 커널 6.8용. GitHub에 iCAT(online) 실행 결과는 하나도 없음.

## 4. 이 머신에서 돌린 실험 (시간순)

| 날짜 | 실험 | 목적 | 판정 기준 | 결과 | 위치 |
|---|---|---|---|---|---|
| 9/6 | baseline, cat-sweep(test2 45run) | 환경 검증, scale/ratio 영향 | 반복 변동 확인 | CAT 100/7 최저 | `result/baseline-20260906`, `cat-sweep-20260906` |
| 9/7 | measured-cat (18 run) | start/stop 명시 계측으로 CAT 3설정 × test2/3 × 3 seed | host_bytes = 블록 통계 일치 | 통과 | `result/measured-cat-20260907` |
| 9/7 | online-mix (test5, 1h×2 phase) | iCAT 첫 실행 | 학습기 동작 확인 | WAF 1.60, 비교군 없음 | `result/online-mix-20260907` |
| 9/8~11 | varmail 준비 | 민감 워크로드 비교 | – | insmod 메모리 실패 → 할당 패치. filebench 자체 버그도 있었음(9/14 발견) | `result/varmail-*` |
| 9/11 | mix main (test4 10분 → sqlite-a) | 최악 CAT vs iCAT 계획의 mix 버전 | phase별 WAF | fixed47 1.90 / **iCAT 2.43** (짐) | `result/mix-20260911/main-*` |
| 9/12 | mix long (test4 60분 → sqlite 10M op) | "phase가 짧아서 졌나" 검증 | 동일 | fixed47 1.87 / **iCAT 2.19** (짐) → 가설 기각 | `result/mix-20260911/long-*` |
| 9/14 | t4 단일 × 3 seed | mix 없이 반복 평균 | seed 3개 평균 | fixed47 **1.774±0.000** / iCAT **2.001±0.000** | `result/mix-20260911/t4-*` |
| 9/14 | gh-repro (GitHub 스크립트 그대로) | 스크립트 의심 해소 | GitHub 기록 재현 여부 | 아래 표 | `result/gh-repro-20260914`, `result/filebench`, `result/sqlite`, `result/rocksdb` |

### 9/14 GitHub 스크립트·GitHub 계측 방식 결과 (1회씩)

| workload | Greedy | CAT arm37 | iCAT | GitHub 기록(arm37) |
|---|---:|---:|---:|---:|
| fio test4 | 2.203 | **1.938** | 1.953 | 1.869 |
| filebench oltp | – | 1.525 | **1.491** | 1.616 |
| filebench varmail (HEAD 설정 15만 파일) | – | **4.623** | 4.935 | (비교 불가) |
| rocksdb-a | – | 1.000 | 1.000 | (없음) — GC 복사 0, 정책 무관 |

Greedy는 GitHub 기록(2.223)과 0.9% 차이로 재현됨.

## 5. 지금까지의 결론

1. **측정은 믿을 수 있다.** 우리 계측과 GitHub 계측이 방향·순위·Greedy 절대값에서 일치.
2. **GitHub iCAT 코드는 잘 고른 고정 CAT을 못 이긴다.** 6번 독립 확인 (mix main/long, t4×3, gh-repro). test4에서 12.8% 나쁨.
3. **원인은 학습기의 측정 잡음.** 같은 arm을 10초 window로 여러 번 재면 0.385 흔들리는데 arm 간 실력 차는 0.098. 60분 동안 1등이 37→0→18→49→33→36→48→46으로 계속 바뀜(`settled` 거의 없음). 시간을 6배 줘도 동일. → 학습기 수정(window 확대, 후보 축소)이 다음 단계.
4. mix 실험 설계 결함 2건 기록: phase B의 대부분이 YCSB load(순차 삽입)였고, phase A 파일 삭제 후 TRIM이 없어 6 GiB가 좀비 유효 데이터로 남음.
5. RocksDB는 비교 워크로드로 부적합. varmail은 GitHub 최신 설정이 sweep 설정과 다름.

## 6. 진행 중 / 예약 (무인, 블록마다 자동 push)

- `script/gh-queue-20260914.sh`: fio test3/4/5 × cat37/iCAT 3회 반복, filebench oltp/varmail 3회, webserver/webproxy
- `script/gh-queue2-20260914.sh`: **Greedy / arm10(최악) / arm47(최적) / arm50(견고)** × 모든 워크로드, sqlite d, videoserver, sqlite 반복
- 진행 상황은 커밋 메시지(`results: ...`)와 `EXPERIMENT_LOG.md` 끝부분

## 7. 저장소 구조

```
EXPERIMENT_LOG.md      모든 run의 사전 등록·결과 (원본 기록)
README.md              이 문서
WORKLOADS.md           모든 워크로드 상세 설명 (숫자·한 바퀴 주기·왜 넣었나)
GLOSSARY_KR.md         기초부터 현재 상황까지 용어·개념 설명
EXPERIMENTS_OVERVIEW.md 실험 전체 정리 (단계별 표, 핵심 결과, 정정한 주장, 한계)
RESULTS_ALL.md         모든 결과표 (analysis/all-tables.py로 원본에서 자동 생성)
SETUP_NEW_MACHINE.md   다른 컴퓨터에 실험 환경 만들기 (설정·빌드·검증 스크립트)
WORST_CAT_VS_ICAT_PLAN.md, MIX_EXPERIMENT_PLAN.md, experiment.md   계획서
analysis/              gh-sweep-waf.py (GitHub 결과 재계산), parse.py
script/                실행 스크립트. gh-* 는 GitHub 원본에서 경로만 바꾼 것
workloads/             fio / sqlite(YCSB) / rocksdb / filebench 정의. gh-* 는 GitHub 원본
result/                run별 원본 로그 (summary.txt, kernel.log, environment.txt, fio JSON)
buildoutput/           빌드된 .ko 모듈 (hash는 modules.sha256 / build-info)
nvmevirt_test/         로컬 계측 확장 소스 (start/stop 측정)
online-mix-src/        iCAT 온라인 모듈 소스 (HEAD + 수동 측정 게이트)
varmail-compare-src/   고정 arm 선택(FIXED_ARM) 모듈 소스
gh-src-7236149/        GitHub HEAD 소스 + 할당 패치 (gh-repro용)
tools/filebench-local/ Filebench 1.5-alpha3 (fileset.c 1줄 버그 수정, PROVENANCE.md)
```

## 8. 재현 방법

```bash
# 모듈 빌드 (예: GitHub HEAD online)
make -C /lib/modules/$(uname -r)/build M=$PWD/gh-src-7236149 NVMEVIRT_GC_POLICY=WATGC_V2 modules
# GitHub 방식 fio 실행
GH_TEST_JOB=gh-test4.fio bash script/gh-fio.sh gh-online
# start/stop 계측 방식 (test4 단일, seed rep)
bash script/mix-20260911.sh t4 online 1
```
sudoers 허용 명령 목록은 `EXPERIMENT_LOG.md` 2026-09-11 항목 참조. YCSB 0.17.0은 `~/YCSB/`에 별도 설치(sqlite-jdbc jar 추가, `bin/ycsb.sh` 사용).
