# CAT-47 기준선 차이 조사: mixY 10월 2.864 대 11월 3.233 (고컴)

- 작성: 2026-11-23, 고컴. 원시 파일과 소스만 사용했다. 새 실험은 하지 않았다.
- **결론: 원인은 아직 확정할 수 없다.** 배제된 후보와 남은 후보를 아래에 나눴다. 승컴 E0(10월 모듈을 11월에 다시 실행, mixY 앞 4단계)의 결과가 남은 후보를 가른다. E0 결과는 23:32 기준 main에 아직 없다.

## 1. 비교 대상

| | 10월 | 11월 (승컴) | 11월 (고컴, 참고) |
|---|---|---|---|
| run | `result/gc-20261010/mixY-fixed47-rep1` | `result/gc-20261010/mixY-sg-arm47-rep1` | `result/gocom-sg-20261119/mixY-sg-arm47-rep1` |
| 시작 | 2026-10-10 12:20 | 2026-11-20 01:10 | 2026-11-20 21:33 |
| 호스트 | 승컴 i7-7700 | 승컴 | 고컴 Ryzen 3600XT |
| 모듈 | `nvmev-varmail-20260908-fixed47.ko` 9fde0ea4… | `nvmev-sg-arm47.ko` 138024d0… | `nvmev-sg-arm47.ko` 2b39b358… (cbd444949) |
| 소스 | `varmail-compare-src` (마지막 변경 9-14) | `smartgc-src` @5bd64c679, `NVMEVIRT_GC_POLICY=CAT_FIG7 FIXED_ARM=47` | smartgc-src @cbd444949 |
| 전체 WAF | **2.864** | **3.233** | 3.298 |

## 2. 항목별 대조

| 확인 항목 | 결과 | 근거 | 원인 여부 |
|---|---|---|---|
| 커널, 부팅 인자 | 같음: 7.0.0-31-generic, `memmap=8G$4G` | 두 run의 `environment.txt` 2–3행 | 배제 |
| 시스템 설정 | CPU 주파수 표시 79 % 대 77 %. 메모리 free 5.7 Gi 대 1.4 Gi (buff/cache 0.7 대 4.9 Gi). JDK 21.0.12 대 21.0.13 (YCSB에만 쓰이고, mixY에는 YCSB가 없다) | `environment.txt` | **미확인** (page cache 상태 차이) |
| 러너 스크립트 | SHA가 다르다 (c96d3093 대 c65debdf). 차이는 정책→모듈 대응표 2줄과 `MIXY_SEQ` 길이 검사 1줄뿐이고, 부하 정의는 같다 | `git diff 374b0e31f 60174df07 -- script/mix-gc-20261010.sh` | 배제 |
| FIO 설정과 seed | `mix-test4.fio` b5edbcc7 같음. seed는 rep1 같음 (20260911/20261011/20261111). `mix-test3.fio`는 9-14 이후 변경 없음 | `environment.txt`, `git log -- workloads/mix-test3.fio` | 배제 |
| Varmail 설정 | `workloads/filebench/varmail.f` 9-14 이후 변경 없음. **filebench seed 지정이 없다** (파일에 seed 항목 없음) | `git log`, grep | **미확인** (Varmail의 run마다 다른 난수) |
| 부하 순서 | 같음: F S V F V S F S V F V S F S V F V S F S, 1800 s | summary.txt 단계 이름 | 배제 |
| 준비 단계와 초기 상태 | prepare 786,432 IO, runtime 78,644 ms로 같다. S01 시작 카운터는 둘 다 0. mkfs는 UUID만 다르다 | `prepare.json`, `phase-S01-start.txt`, `mkfs.txt` | 배제 |
| 장치 | CSL_Virt_MN_01, 같은 크기 | `device.txt` | 배제 |
| GC 버퍼 | 11월 빌드에는 SmartGC 코드가 들어 있다. 하지만 CAT_FIG7 빌드에서는 `smartgc_absorb/unbuffer/buffered`가 모두 `return false`인 빈 함수다. absorbed = evicted = 0 | `smartgc-src@5bd64c679 conv_ftl.c:2015–2052`, final-control | 배제 |
| NAND 페이지 계산 | CAT 빌드에는 `smartgc part=` 줄이 없다. WAF_nand = (host + gc)/host = WAF | `waf_recalculation_audit.md` | 배제 (두 값 모두 같은 식) |
| 소스 차이: GC 희생 블록 선택(CAT) 경로 | `varmail-compare-src`와 `smartgc-src@5bd64c679` 사이에서 ssd.c, channel_model.c, io.c, main.c, pqueue.c는 차이가 0줄이다. conv_ftl.c 차이(787줄)는 SmartGC 블록, 마모 통계, `struct line` 필드 추가(48 → 72 B), `erase_cnt++`/`closed` 표시, 측정 파일 출력에 한정된다. **CAT 점수 계산과 희생 블록 선택 코드는 바뀌지 않았다** | `diff varmail-compare-src/conv_ftl.c smartgc-src/conv_ftl.c` hunk 목록 | 정책 논리 차이는 배제. **간접 영향(구조체 크기, 30 s마다 전체 line을 훑는 마모 통계)은 미확인** |
| CAT 우선순위의 시간 의존성 | CAT 점수가 `ktime_get_ns()` 기준 나이를 쓴다 ("A line's CAT priority changes as wall-clock time advances"). 그래서 실행 속도가 달라지면 희생 블록 선택이 달라질 수 있다 | `smartgc-src conv_ftl.c:2151–2160` 주석 | **미확인** (가능한 경로) |

## 3. 단계별 패턴 (승컴 run, 계산값)

| 단계 | 10월 fixed47 | 11월 sg-arm47 | 11월 고컴 sg-arm47 | 10월 v6 | 10월 v7 | 11월 V4 |
|---|---|---|---|---|---|---|
| S01 F | 1.771 | 1.774 | 1.775 | 1.904 | 1.925 | 1.904 |
| S02 S | 1.758 | 1.761 | 1.761 | 1.789 | 1.802 | 1.780 |
| S03 V | **2.143** | 2.481 | 2.575 | 2.497 | 2.422 | 2.433 |
| S09 V | 2.367 | 2.723 | 2.854 | 2.664 | 2.589 | 2.720 |
| Varmail 처리량 S03 | 105,433 ops/s | 105,809 ops/s | 98,799 | — | — | — |

- S01–S02(FIO)는 0.2 % 안에서 같다. 차이는 첫 Varmail(S03)부터 생긴다.
- S03 Varmail 처리량은 10월과 11월이 0.4 % 안에서 같다. 처리량이 달라서 생긴 WAF 차이로는 보기 어렵다.
- **10월 v6(승컴)은 S09에서 판단 구간의 85 %를 arm 47로 썼는데도 WAF가 2.664다.** 11월 arm47(2.723)에 가깝고, 10월 fixed47(2.367)과는 멀다. 이전 단계의 이력이 다르므로 증거로는 약하다.
  - 이 관측은 "10월 전체가 낮았다"(시기 효과)보다 "10월 fixed47 run 또는 그 모듈이 다르다" 쪽과 더 맞는다.
  - 다만 **확정하지 않는다.**

## 4. 판정

| 후보 | 상태 |
|---|---|
| 부하 정의, seed, 커널, 장치, 준비 단계, GC 버퍼, NAND 계산식 | **배제** (원시 파일로 같음을 확인) |
| CAT 정책 논리 | **배제** (소스 diff상 바뀌지 않음) |
| 빌드 간 간접 효과 (struct line 72 B, 30 s 마모 통계 스캔, 시간 의존 CAT 점수와의 상호작용) | **미확인.** E0가 가른다 |
| 시기·환경 (page cache 상태, 시스템 부하) | **미확인.** E0가 가른다 |
| Varmail 난수 (filebench seed 미지정)에 따른 run마다 다른 편차 | **미확인.** fixed47 mixY 반복이 1회뿐이라 편차 크기를 모른다 |

**논문 대응 권장:**
- mixY 비교는 같은 배치(11월)의 CAT-47(3.233)을 기준으로 한다. 10월 2.864와 섞지 않는다.
- E0 결과가 나오면 이 문서를 갱신한다.
- 판정 기준(승컴 사전 등록): S03/S04가 10월 값에 가까우면 빌드 차이, 11월 값에 가까우면 시기 차이다.
- 고컴은 E0 원시 로그로 같은 표를 다시 계산하겠다.
