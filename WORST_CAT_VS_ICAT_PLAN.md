# 실험 계획서 — 고정 CAT 최악 설정 vs iCAT (test4)

작성: 2026-09-11. 장치 실행 전 사전 등록 문서. 실행 결과는 `EXPERIMENT_LOG.md`에 run 단위로 기록한다.

## 1. 목적

고정 파라미터 CAT은 설정을 잘못 고르면 WAF가 크게 나빠지는 반면, iCAT(online discounted UCB)은 파라미터를 고르지 않아도 그 손실을 피한다는 것을 **같은 장치·같은 커널·같은 Age 모드·같은 소스**에서 보인다.

연구 질문:
1. iCAT WAF는 고정 CAT 최악 설정보다 낮은가? (요청 비교, 약한 주장)
2. iCAT WAF는 sweep에서 workload 간 최소 최대후회(minimax) 설정보다 낮거나 같은가? (핵심 주장)
3. iCAT WAF는 test4 oracle 설정(사전 sweep 최저)에 얼마나 가까운가? (상한)

## 2. 사전 결과 재분석 (GitHub `meendragon/iCAT` 7236149, 새 실행 아님)

`analysis/gh-sweep-waf.py`로 `result/*/dmesg-*.log`의 host/GC 카운터에서 WAF를 재계산. 원본 표는 `result/gh-sweep-analysis-20260911/per-arm-waf.txt`.

| workload | n | Greedy | 최저 arm (WAF) | 최고 arm (WAF) | 편차 |
|---|---:|---:|---|---|---:|
| test3 | 60 | 2.0264 | k07-s050-r07 (1.6888) | k02-s100-r07 (2.0384) | 20.7% |
| **test4** | 60 | 2.2229 | **k10-s025-r16 (1.7478)** | **k02-s200-r07 (2.2313)** | **27.7%** |
| test5 | 60 | 1.6348 | k10-s025-r04 (1.5287) | k02-s050-r16 (1.6325) | 6.8% |
| varmail | 57 | 2.3817 | k10-s025-r16 (1.3050) | k02-s050-r07 (3.9198) | 200.4% (무효, 아래) |
| oltp | 60 | 1.6590 | k10-s050-r07 (1.5763) | k07-s400-r16 (1.6984) | 7.7% |
| sqlite-a | 60 | 1.4974 | k04-s025-r16 (1.1790) | k02-s400-r07 (1.5028) | 27.5% |
| sqlite-b | 60 | 1.2818 | k10-s025-r16 (1.0738) | k02-s100-r16 (1.2840) | 19.6% |

판정과 주의:
- **varmail 200.4%는 workload 차이다.** 43개 로그는 24000 files/5957 MB, 3.85~3.92 WAF 14개는 44000 files/5477 MB, 2개는 150000 files. 24000-file 그룹 안에서만 보면 편차는 **4.2%**(1.3050~1.3601). 따라서 varmail은 민감도 큰 workload가 아니며, 진행 중인 varmail 비교(fixed37/fixed47/online)의 선정 근거는 성립하지 않는다.
- 통제된 편차가 가장 큰 것은 **test4 (27.7%)**, sqlite-a(27.5%)가 사실상 동률. test4는 fio라 seed·payload 통제가 쉽고 기존 러너가 있으므로 test4를 채택한다. sqlite-a는 후속 2차 workload 후보.
- **모든 workload에서 최악 arm은 k=2이고 Greedy와 0.4% 이내다.** "최악 CAT vs iCAT"은 산술적으로 "Greedy vs iCAT"과 같은 실험이다. 이것만 보이면 허수아비 비교라는 지적을 받는다.
- 6개 workload 전체에서 최대후회가 가장 작은 고정 arm은 **k10-s050-r16 (최대 3.7%)**. iCAT의 정당성은 이 arm보다 나쁘지 않아야 성립한다. 그래서 이 arm을 비교군에 넣는다.
- 위 수치는 arm **선정** 근거로만 쓴다. 생성시각 Age, 커널 6.8/7.0.0-30, arm당 1회 실행이므로 새 iCAT 수치와 나란히 인용하지 않는다.

## 3. 비교군 (5 정책, 모두 재측정)

| 정책 | 설정 (k, scale%, ratio) | arm 번호 | 역할 | 빌드 |
|---|---|---:|---|---|
| Greedy | – | – | 참조선 | `CONV_GC_POLICY=0` |
| CAT-worst | (2, 200, 7) | 10 | 요청한 최악 설정 | `CONV_GC_POLICY=1 FIXED_ARM=10` 신규 |
| CAT-robust | (10, 50, 16) | 50 | minimax 고정 arm | `FIXED_ARM=50` 신규 |
| CAT-oracle | (10, 25, 16) | 47 | test4 사전 최저 | 기존 fixed47 모듈 (검증 완료 `varmail-fixed47-k31`) |
| iCAT | online discounted UCB, 60 arms | – | 제안 기법 | 기존 `online-mix-src` 모듈 |

arm 번호 = ki×15 + si×3 + ri, levels {2,4,7,10}, scales {25,50,100,200,400}, ratios {4,7,16} (`varmail-compare-src/conv_ftl.c` `watgc_v2_decode`). 다섯 모듈 모두 ssd.c kvmalloc + io.c kvzalloc 패치가 적용된 동일 소스 트리에서 빌드하고 SHA256을 `result/worst-cat-20260911/build-info.txt`에 기록한다.

## 4. 고정 조건

- 장치: NVMeVirt conventional, memmap 8 GiB (4G~12G), cpus 1,2, 커널 `7.0.0-31-generic`. 실제 값은 run마다 environment 파일로 기록.
- Age: 모든 정책 `LAST_INVALIDATION` (iCAT과 동일). 생성시각 Age는 쓰지 않는다.
- 준비: `measured-cat-20260907.sh`와 동일 — 새 ext4(nodiscard), 6 GiB 순차 preset, 전체 6 GiB에 3 GiB 4 KiB random(10k IOPS, seed 20260907), sync 후 manual `start`. 준비 중 카운터 0 확인.
- 측정 workload: `workloads/test4.fio`를 **고정 payload**로 변환(measured-cat과 동일 방식, time_based 아님). hot 512 MiB 24k IOPS / warm 1.5 GiB 12k / cold 4 GiB 4k, 비율 6:3:1 유지. 총 24,000,000 writes × 4 KiB = 98,304,000,000 bytes(정상 속도 약 600초). hot/warm/cold 각 14,400,000 / 7,200,000 / 2,400,000회.
- seed round 3개: hot 20260911/12/13, warm 20261011/12/13, cold 20261111/12/13. 같은 round는 5개 정책 모두 같은 seed.
- iCAT learner: 준비 중 학습 금지, `start` 시 cold start, run 사이 리셋(모듈 재로드로 자동). GC warmup 100 GC는 기존 설정 유지.
- CPU governor·부하는 고정하지 않고 기록.

## 5. 실행

- run 수: 5 정책 × 3 seed = **15 run**, 직렬. run당 준비 약 80초 + 측정 약 600초 → 약 2시간 50분.
- 순서: seed round별로 정책 순환(Greedy, worst, robust, oracle, iCAT → 다음 round는 회전)해서 시간 드리프트가 한 정책에 몰리지 않게 한다. 순서는 실행 전 `result/worst-cat-20260911/plan.tsv`에 저장.
- 실행 전 단계 (장치 작업, 사용자 확인 후):
  1. 재부팅 상태 확인: `/sys/module/nvmev` 없음, mnt 없음.
  2. FIXED_ARM=10, 50 모듈 빌드, hash 기록.
  3. `verify-measurement-20260907.sh`로 신규 2개 모듈 + iCAT 모듈 계측 검증 (fixed47은 k31 검증 완료이나 io.c 재빌드본이면 재검증).
  4. 정책별 60초 smoke 1회.
  5. main 15 run. `measured-cat-20260907.sh`를 복사해 정책 목록·payload만 바꾼 `script/worst-cat-20260911.sh`로 실행.
- 명령 초안: `bash script/worst-cat-20260911.sh smoke`, `bash script/worst-cat-20260911.sh batch`.

## 6. 지표

- 주: FTL WAF = (host_pages + gc_pages) / host_pages, `start`~`stop` 구간.
- 보조: gc_pages, gc_count, GC당 복사 page, iCAT의 window별 arm 선택 이력·settled 시각, fio 완료 시간·err.
- iCAT 전용: 최종 수렴 arm이 sweep oracle(47)/robust(50) 근처인지 기록. 근처가 아니어도 실패는 아니다 — WAF로만 판정.

## 7. 판정 기준 (사전 고정)

각 run 유효 조건 (하나라도 실패하면 run 무효, batch 중단, 실패 보존):
- fio err=0, payload 완료, host_bytes = block sectors delta × 512 = host_pages × 4096.
- **host_pages가 5 정책 사이에서 0.5% 이내** (sweep 자체 산포 0.2%). iCAT 선택 오버헤드로 IOPS를 못 채우면 WAF 비교 불가로 보고하고 승리로 쓰지 않는다.
- gc_pages > 0, 준비 구간 카운터 0.

결과 해석 (seed 3개 평균, 개별 seed도 표시):
- Q1: iCAT < CAT-worst 이고 iCAT < Greedy — 예상되는 결과이며 단독으로 정당성 근거가 되지 않는다.
- Q2: iCAT ≤ CAT-robust × 1.02 — **iCAT 정당성의 핵심 조건.** 실패하면 "고정 arm 하나로 충분하다"는 반박이 유효하고 그렇게 보고한다.
- Q3: (iCAT − oracle)/oracle 를 학습 손실로 보고. 목표값을 사전에 두지 않는다.
- 3 seed 단독 비교이며 통계적 유의성을 주장하지 않는다. seed 간 정책 순위가 뒤집히면 그대로 보고.

## 8. 진행 중인 varmail 비교와의 관계

- varmail-20260908/20260911 계획은 200.4% 편차를 근거로 선정됐고 그 근거는 2절에서 무효로 확인됐다. 이미 빌드·검증한 모듈과 러너는 보존하되, **test4 15 run을 먼저 실행**하고 varmail은 "24000-file 고정 시 편차 4.2%"라는 별도 사실로 정리한다. varmail을 계속할지는 사용자 결정.
- 2차 workload가 필요하면 sqlite-a(27.5%, 최저 k04-s025-r16 = arm 17, 최악 k02-s400-r07 = arm 13)를 같은 5-정책 틀로 반복한다.

## 9. 미확인·한계

- test4를 고정 payload로 바꾸면 GitHub의 time_based 600초 조건과 같지 않다(measured-cat과 같은 선택). 결과는 GitHub 수치와 합산하지 않는다.
- rate_iops 합 40k에서 5개 정책 모두 목표 IOPS를 유지하는지는 smoke에서 확인 — 미달 시 IOPS를 낮춰 재등록.
- LAST_INVALIDATION Age에서 sweep 순위(생성시각 Age 기준)가 유지된다는 보장은 없다. oracle/robust/worst 라벨은 사전 sweep 기준 라벨이며 새 측정에서 실제 순위를 다시 보고한다.
- 메모리: 8 GiB 예약 후 남는 약 7 GiB에서 브라우저 등이 돌면 고차 연속 페이지 확보가 불안정했다(2026-09-11 io.c 사례). 실험 중 큰 사용자 프로세스를 줄이는 것을 권고.
