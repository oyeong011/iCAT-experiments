# revG-20261128 사전 등록: SSD 용량 확장 (8 GiB → 16 GiB), 고컴

- 작성: 2026-11-27, 실행 전. 실행은 revF가 정상 종료하고 재부팅한 뒤에 시작한다.
- 지시 (사용자, 2026-11-27) "iCAT SSD Capacity Scalability Experiment"
  - 16 GiB에서 iCAT-v4 3회, Random Selection 3회
  - 8 GiB 쪽은 기존 고컴 revA 결과를 쓴다 (iCAT-v4 3회, Random 3회)
- 사용자 결정 (2026-11-27, 질문 응답)
  1. NAND 구성: **블록 크기는 그대로 두고 블록 수를 2배**로 한다 (64 KiB 블록, 256 KiB line, 32 KiB 페이지, line 16384개)
  2. 쓰기량: **FIO 쓰기량 2배, IOPS 유지**. 용량 대비 누적 쓰기량을 8 GiB와 같게 맞춘다 (약 76배)
  3. YCSB-A: **그대로** (25만 레코드, 단계 1800 s)
  4. 재부팅: revF가 끝난 뒤 자동 전환하고 자동 시작한다 (아래 §4)

## 1. 정책과 모듈

| 정책 | 모듈 | sha256 앞 16자 | 빌드 |
|---|---|---|---|
| revG-v4 (iCAT-v4, 16 GiB) | `buildoutput/nvmev-revG-v4.ko` | d16031935604c16b | revG-src, `ICAT_VARIANT=4 ICAT_EXTRA=-DICAT_BLKS_PER_PLN=16384` |
| revG-random (Random Selection, 16 GiB) | `buildoutput/nvmev-revG-random.ko` | 9206fdd3269ead14 | revG-src, `ICAT_VARIANT=9 ICAT_EXTRA=-DICAT_BLKS_PER_PLN=16384` |
| (8 GiB 대조, 기존) revA-v4 / revA-random | `nvmev-revA-v4.ko` 987d6204… / `nvmev-revA-random.ko` 7d88c9a8… | — | revA-src |

- **revG-src** = `revA-src` 사본에 두 곳만 바꿨다 (`diff -r`).
  - `ssd_config.h`: `#ifdef ICAT_BLKS_PER_PLN`이면 `BLKS_PER_PLN`을 그 값으로 한다. 기본값 8192는 그대로다.
  - `Kbuild`: `ccflags-y += $(ICAT_EXTRA)` 한 줄 (revC와 같은 방식)
- 기계어 확인 (`build/objdump-*.diff`, 주소와 원시 바이트를 지우고 명령어만 비교)
  - revG-src를 옵션 없이 빌드한 모듈이 revA-v4.ko, revA-random.ko와 **차이 0줄**이다 (`nvmev-revG-defaultcheck-{v4,random}.ko`).
  - 16 GiB 빌드는 22줄이 다르다. 모두 `ssd_init_params`의 블록 수 상수다: 0x2000 → 0x4000, 0x4000 → 0x8000, 시프트 +1.
  - v4와 random의 변경 내용이 서로 같다. **학습기 코드는 8 GiB 대조군과 같다.**
- 학습기 파라미터는 모두 기본값이다: γ 0.9995, C 0.25, 제거 15 %, 감지 25 %, 판단 구간 GC 128회 + 512 MiB.

## 2. 16 GiB 장치 조건

| 항목 | 8 GiB (revA, 기존) | 16 GiB (revG) | 확인 방법 |
|---|---|---|---|
| 커널 예약 | `memmap=8G$4G` | `memmap=16G$4G` | `/proc/cmdline`, `lsmem` (4–20 GiB가 online RAM이 아님) |
| insmod | `memmap_start=4G memmap_size=8192M` | `memmap_size=16384M` | 러너 |
| 저장 영역 | 0x100100000–0x300000000 (8191 MiB) | 0x100100000–0x500000000 (16383 MiB) 예상 | 커널 로그. 러너가 확인하고, 다르면 측정 전에 종료한다 |
| 파티션당 구성 | lines=8192, 블록 64 KiB, line 256 KiB | lines=16384, 블록 64 KiB, line 256 KiB | 커널 로그 `Total Capacity` (러너, check-run 둘 다 검사) |
| 논리 용량 | 7655 MiB | 약 15,310 MiB 예상 (15,000–15,700이 아니면 종료) | 커널 로그 `ns 0/1: size`, `device.txt` |
| NAND | MLC, ch 8 × LUN 2, page 32 KiB, OP 7 %, erase 0 | 같음 | 같은 `ssd_config.h` |
| GC 시작 | 빈 line 2개 이하 | 같음 (2개). **전체 line 대비 비율은 절반이 된다** | `conv_ftl.c:1182` (바꾸지 않음) |
| 호스트 RAM (OS가 쓰는 양) | 약 24 GiB | 약 16 GiB | `free` (boot-verify.txt) |

## 3. 워크로드 (용량에 비례해 확장)

| 항목 | 8 GiB | 16 GiB |
|---|---|---|
| 준비 쓰기 | 6 GiB 순차 + 3 GiB 4K 랜덤 (seed 20260907, 10k IOPS) | 12 GiB 순차 + 6 GiB 랜덤 (같은 seed, 같은 IOPS) |
| FIO 작업 영역 (`mix-test4.fio` → `mix-test4-16g.fio`) | hot 0+512M, warm 512M+1.5G, cold 2G+4G | hot 0+1G, warm 1G+3G, cold 4G+8G (오프셋·크기 2배, 비율 6:3:1 유지) |
| FIO 단계 쓰기량 / IOPS | 1배 / 24k·12k·4k | **2배** / 같음 → 단계 A·C가 각각 약 3,600 s |
| YCSB-A | 25만 레코드, 단계 1800 s | 같음 |
| 순서 | FIO-Fast → YCSB-A → FIO-Fast | 같음 |
| 누적 호스트 쓰기 / 논리 용량 | 약 76배 (revA 실측) | 약 76배 예상 (FIO), YCSB 부분은 절반 |
| 측정 구간 | 준비 후 카운터 0에서 시작, 단계 C 끝에서 종료 | 같음 |
| phase_fio 제한 시간 | PH_SECS + 900 s | 2 × PH_SECS + 900 s |

- seed: FIO hot/warm/cold = 20260910/20261010/20261110 + rep, icat_seed = 2026111400 + rep. revA와 같은 규칙이다.

## 4. 실행 절차

1. revF가 정상 종료하면 `root-switch-16g.sh`가 다음을 순서대로 한다. 이 스크립트는 사용자가 root로 한 번 실행해 두며, revF가 끝날 때까지 기다린다.
   - `99-nvmevirt.cfg`를 16G로 바꾼다. 원본은 백업한다.
   - `update-grub`을 실행하고 grub.cfg를 검증한다.
   - 재부팅한다.
   - revF가 이상으로 멈췄으면 아무것도 바꾸지 않는다.
2. 부팅 후 사용자 crontab `@reboot boot-start.sh`가 다음을 확인한다. 하나라도 어긋나면 시작하지 않는다.
   - `/proc/cmdline`에 `memmap=16G$4G`가 있다.
   - 4–20 GiB 구간이 online RAM이 아니다.
   - 장치가 비어 있다.
3. 확인되면 단기 실행(120 s, FIO 단계 240 s) 2개를 돌린다: revG-v4, revG-random.
   - 러너 검사: 용량과 구성 불일치, 커널 오류, γ·C·VARIANT 불일치가 있으면 멈춘다.
4. 본 실행 순서 (`queue-order.registered.txt`, `random.Random(20261128)`로 반복 블록마다 섞음)
   1. revG-v4 1
   2. revG-random 1
   3. revG-random 2
   4. revG-v4 2
   5. revG-random 3
   6. revG-v4 3
5. 각 run 뒤에 `check-run.py`를 돌린다. 이상이 있으면 멈추고 다음 run을 시작하지 않는다.
   - 검사 항목: exit, WAF 두 경로, YCSB, FIO, 커널 오류, CPU, init γ/C/VARIANT, 16 GiB 구성
   - 검사 뒤 `sync-push.sh`가 원시 로그(kernel-snapshots 제외)를 push하고 `capG_analyze.py`를 다시 돌린다.
6. 끝난 뒤 8 GiB 복원은 자동으로 하지 않는다. `root-switch-8g.sh`를 root로 실행한 뒤 재부팅한다.

- 예상 시간 (계산): run 1회 약 2.6 h (준비 약 3분, 3,600 + 1,800 + 3,600 s), 6회 약 15.5 h, 단기 실행 2회 약 0.5 h.

## 5. 분석 (`analysis/final_revision/capG_analyze.py`)

- 원시 카운터에서 계산하는 값
  - 전체 WAF, 단계 A/B/C WAF, 단계 C 첫 5분 WAF
  - 호스트 쓰기량, GC 횟수 (final-control의 gc_count 합)
  - 논리 용량 (`device.txt`), 누적 쓰기 / 용량
- 통계: 용량별 평균, SD, 95 % CI (t, df = 2)
- 용량 안의 비교 (같은 배치): Random − iCAT의 Welch 95 % CI, Improvement (%) = (Random − iCAT) / Random × 100
- **주된 비교는 각 용량 안의 Improvement다.** 8 GiB와 16 GiB는 배치가 다르다 (revA 11-14, revG 재부팅 후).
  - 따라서 같은 정책의 8 대 16 절대 WAF 차이는 용량 효과와 배치 효과가 섞여 있다고 적는다.
  - GC 시작 비율이 절반이 되는 점과 OS RAM이 줄어드는 점도 차이로 적는다.
- 8 GiB 원시 결과는 읽기만 한다.
- 무효 run은 빼지 않고 사유와 함께 표시한다.
