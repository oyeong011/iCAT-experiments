# iCAT 실험일지

## 2026-09-08 — varmail 계측 검증 실패 / 장치 실행 차단

- 실제 실행: `MEASUREMENT_AGE_DESCRIPTION=LAST_INVALIDATION bash script/verify-measurement-20260907.sh varmail-20260908-fixed47 varmail-fixed47`. exit137; module insmod 단계에서 종료되어 포맷/fileset/workload는 실행되지 않았다. WAF 결과 없음.
- 커널 로그: `insmod: page allocation failure: order:6` 직후 `BUG: kernel NULL pointer dereference,address:0000000000000008`, `RIP:ssd_init+0x138/0x3b0`. SSD metadata 초기화의 할당 실패 뒤 NULL 접근이 관측됨. ssd.c는 기존 online source와 동일하며 fixed arm 설정 코드의 실행 효과라고 판단할 근거 없음.
- 복구 상태: nvmev initstate=coming,refcnt=1. 일반 `sudo -n rmmod nvmev`도 Module nvmev is in use로 실패. 강제 제거/재부팅/다른 사용자 프로세스 종료는 수행하지 않음. mount와 NVMe namespace는 생성되지 않았음. 정상 정리 완료로 표시하지 않는다.
- 안전한 성능 실험을 계속하려면 controlled reboot가 필요하며 사용자 확인 전 기기 작업은 중단한다. 비교 batch/main은 시작하지 않았다.
- 준비 완료: 동일 점수/변환의 fixed37/fixed47 모듈과 varmail runner 초안, 로컬 Filebench1.5-alpha3 executable. Runner는 실제 Filebench smoke/seed/barrier/후속 검증이 아직 남아 있어 실험 완료가 아니다.
- 실패 원본: `result/measurement-control-20260907/varmail-fixed47/`, `result/varmail-20260908/verify-fixed47.console.txt`, 추가 커널 로그 `result/varmail-20260908/initialization-failure.log`. 가설/복구 기록 `.debug-journal.md`.

## 2026-09-08 — varmail-20260908 사전 등록

- 사용자 요청: 사전 결과에서 민감도가 큰 workload로 고정 CAT와 iCAT 비교를 실제 실행. 대상 Filebench varmail. 온라인은 기존 검증된 discounted UCB; 고정 비교군은 동일 Age/변환/점수의 arm37=(7,100,7), arm47=(10,25,16).
- 중요 정정: 앞서 보고한 GitHub varmail 최저1.305/최고3.920의 200.4% 범위는 같은 workload 설정의 효과로 해석하면 안 된다. 최저 로그는 24000files/5957.171MB, 최고 로그는 44000files/5477.249MB이며 파일 수/평균 크기가 다르다. 또한 CAT 로그는57개로60개 미충족. arm47은 사전 최저 관측 후보이지 검증된 oracle가 아니다. 원본 로그를 보존하고 이번에는 동일 workload를 적용한다.
- 소스: upstream7236149 + online-mix-src의 검증된 manual start/stop. `varmail-compare-src/` 격리 복사본에서 policy1의 고정 arm 선택만 추가한다. 온라인 module은 기존 a34e2a86907675230fbc4b80e4ed1e49f7f5713384b569357800930f754d9479 사용. 고정 module hashes/build logs/diffs는 `result/varmail-20260908/`에 저장한다. 빌드 중 기록이며 장치 실험 전에 작성함.
- 실행 계획: Filebench 준비/시작 barrier 확인 및 두 고정 module 계측 검증 → 정책별 짧은 smoke → 같은 varmail 파일을 사용한 정책별 장시간 pilot. 한 번에 하나의 정책만 실행하고 각 run은 신규 virtual SSD, ext4 nodiscard, 같은 preconditioning과 fileset 설정이다.
- 장치 안전: /sys/module/nvmev와 기존 NVMe controller 및 mnt가 없어야 시작. CSL_Virt 모델/정확한 namespace 검증 후에만 포맷. 기존 global experiment locks 사용. 물리 장치는 접근하지 않는다.
- 기준 workload는 기존 최저 관측과 가까운 24000 files, gamma mean256KiB/gamma1.5,16threads, meanappend16KiB,read1MiB,prealloc80%로 고정한다. 실제 생성 크기는 run마다 기록. Filebench seed 제어 가능 여부를 확인해 고정하거나 미통제라고 표시한다. 파일 생성 후 sync와 공통 start, 종료 후 sync/stop으로 구간을 맞춘다. cache drop은 권한과 시스템 영향 때문에 하지 않으며 모든 정책에서 동일하게 유지한다.
- 주요 지표: host bytes, host FTL pages, GC pages, WAF(페이지 기준 및 host-byte 기준을 구분), GC/window/action, 실제 app operations/throughput/error. Buffered varmail은4KiB단위 정렬이 보장되지 않으므로 host_bytes=host_pages×4096을 강제하지 않는다. host_bytes는 Linux block write sectors와 일치해야 한다.
- 중단: 실행오류/ENOSPC/장치식별 실패/계측불일치/로그손실은 run 실패 및 후속 main 중단. 성능저하나 미수렴은 결과로 보존. 단일 반복 pilot이며 우월성/통계적 유의성 결론을 내리지 않는다.
- 변경/미확인: Filebench는 PATH에 없어 사용자 로컬 prefix로 준비 중. executable version/hash, 실제 runtime/seed 및 시작 barrier 상세는 준비 검증 후 실행 전에 아래 추가한다. 결과 루트 `result/varmail-20260908/`, 모든 실패/재실행 포함 기록.

## 2026-09-07 — online-mix-20260907 사전 등록 및 구현 준비

- 사용자 요청: GitHub의 iCAT 온라인 모델로 믹스 워크로드 실험 실행. 현재 온라인 알고리즘은 Q-learning이 아닌 discounted UCB bandit이다.
- 원본 commit: `7236149a01efad760aed084acf5b270f5a0408f6`; 별도 `online-mix-src/`에서만 Kbuild 정책 연결과 manual measurement/learning gate를 통합한다. 기존 CAT source/module/run은 변경하지 않는다. 구현 diff, build 로그 및 SHA256은 `result/online-mix-20260907/`에 저장한다.
- 기존 measured-cat batch가 장치를 해제한 뒤에만 시작한다. 새 가상 namespace의 모델/용량 확인 전 포맷 금지. 물리 NVMe 또는 기존 module/mount 존재 시 중단.
- 실행 순서: isolated build → 기존 계측 검증기 online 모듈 대상 실행 → 30초 A + 30초 B smoke → 성공 시 3600초 A + 3600초 B 본 파일럿. 각 실행은 새 장치이며 실패/중단도 보존한다. 빌드 준비 문서는 에이전트 구현 진행 중 작성되었으며 성능 실행 전에 등록됨.
- 목적: 실제 online 정책 활성화, 준비 중 학습 금지, 공통 counter, partition별 유효 reward/action 변경을 검증하고 A→B 변화에 대한 동작을 관측한다. 단독 1-seed pilot이며 성능 우월성/수렴 보장/통계적 결론을 주장하지 않는다.
- 설정: 삼성970PRO conventional NVMeVirt, reserved 4G~12G(8GiB), cpus=1,2, 기존 커널/호스트 유지. 4 FTL partitions, 최신 소스 last-invalidation Age/60 arms/default bandit thresholds. 실제 geometry/build options는 로그로 보존. CPU governor는 변경하지 않고 기록.
- 준비: ext4 nodiscard, 6GiB 순차 생성 + 전체 6GiB에 3GiB 균등 랜덤, 4KiB 10kIOPS seed20260907. 준비/flush 완료 후 counters와 learner cold-start. GC warmup은 start 이후 partition별 새로운 100GC 기준. phase 사이 학습 초기화·모듈 재로드 없음.
- A: 앞2GiB 32kIOPS(seed20260911), 뒤4GiB 8kIOPS(seed20260912). B: 앞2GiB 8kIOPS(seed20260913), 뒤4GiB32kIOPS(seed20260914). 모두4KiB direct libaio depth32, time-based. 원본 test5의 hot 위치 전환을 유지하고 경로/시간/phase 로그를 조정. 각 phase는 별도 fio 호출이며 사이 flush/실행 지연은 기록하고 cumulative 측정에서 제외하지 않는다. DB/Filebench 미포함.
- 실행 명령: `bash script/verify-measurement-20260907.sh online-mix-20260907 online-final`; `bash script/online-mix-20260907.sh smoke`; `bash script/online-mix-20260907.sh main`.
- 판정: shell/fio parse 통과; 초기화 online 로그; 준비 중 measured counters/window0; 시작 이후 네 partition 모두 sample 및 2개 이상 action 관측; fio err0; host bytes = block sectors delta×512 = host pages×4096; GC pages>0; stopped 결과/원시 로그/종료 코드 보존. 준비 중 sample 발견, 계측 불일치, 잘못된 장치, I/O 실패 시 main 미실행.
- 결과 경로: `result/online-mix-20260907/{smoke,main}/`, 계측 검증은 `result/measurement-control-20260907/online-final/`. source/module hash, 커널/fio/CPU 및 phase 시각을 실행별 기록한다. 독립 NAND program 검증 및 exact SSD snapshot 동일성은 미검증.
- 본 파일럿 phase당1시간은 원래300초보다 길게 선정했다. 60arms×3visits coverage에 필요한 양을 고려한 후보 시간이며, 실제 coverage/settled/discard를 통해 충분성을 사후 평가한다. coverage가 안 되면 미수렴으로 보고하며 임의 시간 연장하지 않는다.

## 2026-09-07 — measured-cat-20260907 사전 등록

- 사용자 승인: 새 측정 구간으로 CAT 비교 시작. 설정 (100,7), (400,16), (200,7) × test2/test3 × seed 3개 = 신규 18회. 이전 90개 결과와 합산하지 않는다.
- 목적: 공통 측정 절차와 별도 seed에서 후보 설정의 결과가 유지되는지 확인한다. iCAT/Q-learning/phase 전환 실험이 아니다.
- 각 run: 새 conventional SSD/ext4(nodiscard), 6 GiB 순차 preset 후 전체 6 GiB 영역에 3 GiB 4 KiB random preparation, 10000 IOPS, seed 20260907. fio 및 sync 완료 후 start, 측정 workload/fio/sync 완료 후 stop. 실제 내부 SSD 배치는 정책에 따라 다를 수 있으며 snapshot 동일성은 주장하지 않는다.
- 측정은 time_based가 아니라 고정 payload 24,576,000,000 bytes = 6,000,000 × 4 KiB이다. test2 hot/cold 각각 4,800,000/1,200,000회, test3 hot/warm/cold 각각 3,600,000/1,800,000/600,000회. 기존 영역 크기와 각 job의 IOPS 비율 유지. 정상 속도에서 약 600초이며 payload 완료까지 실행한다.
- seed round 1/2/3: hot 20260911/12/13, warm 20261011/12/13, cold 20261111/12/13. 같은 round에서는 모든 CAT 설정에 같은 seed를 사용한다. concurrent job interleaving은 완전히 고정되지 않는다. 각 seed별 1회로 총 3개 seed 비교이며 동일 seed 3반복 실험은 아니다.
- 고정: CREATE Age, 7단계, 기존 NAND/GC/geometry, memmap start4G/size8192M, dispatcher1/worker2, window262144, measurement_manual=1, owner UID1000. CPU 부하/주파수는 고정하지 않고 기록한다.
- 모델 소스는 검증 완료 버전과 hash 일치를 확인했다. 모듈 3개를 별도 빌드하며 100/7은 검증한 CAT v2와 byte 일치 확인 후 사용한다. 소스/입력과 모듈 hash를 run마다 검증한다.
- 명령: `bash script/measured-cat-20260907.sh batch`. 순서는 `result/measured-cat-20260907/plan.tsv`에 사전 저장하며 설정 순서를 seed round별 순환하고 workload를 교차한다.
- 매 run에 준비 단계 카운터 0, start/stop 경계의 block sectors 불변, fio payload 합계 및 error, host_bytes=block sectors delta×512, host_pages×4096 일치를 검사한다. 파일시스템 metadata 쓰기량은 payload와 별도로 기록한다. 일치하지 않으면 실패 기록과 함께 batch를 중단한다.
- 결과: `result/measured-cat-20260907/run-NN/`에 environment, fio JSON, start/stop counters, summary, kernel log. 시작·종료·실패를 일지에 자동 기록한다.
- 예상: 준비 약 80초 + 측정 약 600초 × 18회, 약 3시간 25분 이상. 독립 NAND program 검증, 측정모드 CPU overhead, queue drain의 일반적 보장까지 검증한 것은 아니다.

## 2026-09-07 — 명시적 측정 제어 구현 완료

- 변경 파일: `nvmevirt_test/conv_ftl.c`, `conv_ftl.h`, `main.c`; 검증 실행기 `script/verify-measurement-20260907.sh`; 사용 설명 `MEASUREMENT.md`.
- 구현 전후 소스 및 diff: `result/measurement-control-20260907/{before-source.tar.gz,after-source.tar.gz,implementation.patch,changed-files.sha256}`. 기존 모듈/90개 관측은 덮어쓰지 않았다.
- 최종 Greedy 모듈 SHA256 `db3648cd4e086f22a381775d814d84b847a9e25a57561d6959ce88bcc62c7000`, CAT `54fdeb4e7720822cedefc0df701ae1eec3227ea9e7ebcb70f80b93606ebe4874`.
- 최종 manual 검증 greedy-final/cat-final 모두 exit=0. 준비 9 GiB 동안 카운터 0, measured epoch의 module host_bytes=Linux sectors×512=1,073,758,208, partition 합 일치, GC 양수, stop 후 256 MiB 쓰기에도 snapshot 동일, reset 확인, 1 MiB checksum 표본 보존 확인. 후속 128 MiB payload epoch도 두 정책 모두 host_bytes=134,234,112로 block stat와 일치했다. filesystem 쓰기가 포함되므로 payload보다 16 KiB 크다.
- Legacy 회귀: 2026-09-07 16:15:32 시작, 16:16:36 종료, test3 60초, 600000 writes, fio err=0/script exit=0. 수동 mode=N 및 proc endpoint 부재를 실행 중 확인했다. 로그 `result/test3-measurement-20260907-greedy-v2-rep1-20260907-161532-370320.log`. 기존 자동 계측이 동작하는지 확인하는 smoke이며 과거 결과와 정확한 결정성 비교는 아니다.
- 코드 검토: 명령 단위 mutex, 잘못된 command/중복 start 거부, retry 시 host_bytes 중복 없음, normal/failure 초기화 경로 proc 수명 검토 통과. 파일기반 runtime 검증에서도 최종 snapshot 확인.
- 정적 검사: Greedy/CAT 커널 모듈 빌드 성공, bash -n 통과. checkpatch 0 errors, 4 warnings (긴 줄 3개 및 diff의 commit description 부재). 빌드 기존 compiler/pahole 차이, MODULE_DESCRIPTION 및 BTF 경고는 로그에 보존했다.
- 실패 CAT v2 기록과 추적 재실행은 보존했다. 간헐적 실패의 정확한 원인은 확정하지 않으며, 이후 검증은 checksum 읽기를 정지 구간으로 분리하고 시작/종료의 조용한 경계를 실제 sector 값으로 확인했다. debugging 절차는 이 실패 조건의 조사와 실제 재실행 검증에 사용했다.
- 최종 module/proc endpoint/가상 namespace/mount 해제 확인. 새 장치에 쓴 검증 데이터는 장치 해제로 소멸했고 기존 물리 디스크 데이터는 사용하지 않았다.
- 완료 범위: 명시적 계측 시작/종료 및 host 요청량 대조. 독립 NAND program 계측, 장시간 concurrent 제어 stress, 전체 데이터 integrity, 정책 간 동일 내부 SSD 상태, window reward 귀속은 검증하지 않았다. 이후 CAT 비교는 새 계측 모드를 명시하고 준비/측정 구간을 동일하게 설정해야 한다.

### 2026-09-07 — 측정 제어 검증 중간 결과 및 legacy 회귀 사전 등록

- Greedy v2 최초 검증 PASS. CAT v2 최초 검증 FAIL, 후속 동일 코드 추적 재실행 PASS. 실패 run은 reset 후 checksum 두 개가 같고 second_epoch fio가 시작되기 전 종료했다. 간헐적인 filesystem 쓰기/경계 불안정이 유력하지만 당시 sector 값이 저장되지 않아 원인을 확정하지 않는다.
- 검증 실행기를 보완해 데이터 checksum 읽기를 정지 구간으로 옮기고, 경계 실패 시 expected/actual sector와 카운터를 출력한다. 커널 코드는 이 검증 보완 중 변경하지 않았다.
- 보완된 최종 검증: greedy-final 및 cat-final 모두 PASS. 두 정책 모두 measured 1 GiB + filesystem 쓰기를 포함한 1,073,758,208 bytes가 module host_bytes 및 block stat delta와 일치. Greedy gc_pages=373, CAT gc_pages=26863. 이는 짧은 계측 검증의 관측이며 정책 성능 비교 수치가 아니다.
- 추가 회귀 run 계획: 수동 모드를 지정하지 않은 measurement-20260907-greedy-v2로 기존 run.sh/test3/FIO_RUNTIME=60/rep=1 실행. 기존 자동 첫-GC 계측과 proc endpoint 부재, fio/script 종료를 확인한다. 기존 preset/seed/SSD 설정 유지. 콘솔 `result/measurement-control-20260907/legacy-console.txt`, 커널 로그는 기존 run.sh가 기록한다.

## 2026-09-07 — measurement-control-20260907 변경·검증 사전 등록

### 검증 실패 조사 기록

- Greedy v2 최초 검증 exit=0. CAT v2는 첫 epoch byte 대조, stop 불변, reset, checksum 파일 생성까지 진행한 뒤 exit=1. 원본 실패 로그를 보존한다.
- 가설 1: reset이 데이터 손상 유발 — 전후 checksum 비교로 판별.
- 가설 2: checksum 읽기/flush 또는 ext4 background 쓰기가 두 번째 epoch 경계의 block stat를 변경 — 실패 지점과 before/current sectors로 판별.
- 가설 3: 두 번째 fio 실행 자체 실패 — second_epoch.json 존재 및 fio error로 판별. 최초 실패에는 해당 JSON이 없어 이 가설은 맞지 않는다.
- 재실행에서 bash 실행 추적을 결과 폴더에 남겨 실제 실패 조건을 확인한다. 추적 및 실패 기록은 사용자 실험일지 보존 지시에 따라 유지하고, 커널에 임시 디버그 코드는 넣지 않는다.

- 사용자 승인: 측정 시작 기준을 맞추고 검증. 정책 선택·Age·SSD geometry는 변경하지 않는다.
- 구현: opt-in 수동 측정 모드, 전용 proc start/stop/read, 명령 처리와 공통 mutex, 모든 FTL 통계 동시 시작/정지. 기존 모드 기본값과 첫-GC 계측은 유지. 준비 데이터와 mapping은 reset하지 않는다.
- 권한: 모듈 로드 시 명시한 실험 사용자 UID에만 proc 제어 권한을 부여하며 기본 UID는 root. endpoint는 namespace 생성 후 추가, 해제 전에 제거한다.
- 원본 보존: `result/measurement-control-20260907/before-source.tar.gz`. GitHub 8542e25 대비 기존 로컬 확장 위에 수정한다. 기존 모듈·실험 결과는 보존한다.
- 검증 계획: Greedy/CAT 빌드, 새 가상 장치에서 준비 쓰기 후 카운터 0, start 후 정해진 쓰기량과 Linux block-stat write sectors 대조, GC 포함, stop 후 추가 쓰기에도 불변, 재start 후 reset, 읽기로 데이터 보존 확인. 중복 start와 잘못된 command 거부 확인. 실제 실행 조건과 로그는 run 전에 추가 기록한다.
- 한계: FTL 명령 경계 동기화는 NAND 완료/queue drain 자체가 아니다. workload 완료 및 sync/flush 후 start/stop한다. 파일 기반 검증의 filesystem metadata 쓰기는 장치 통계에 포함되므로 fio payload와 별도 구분한다. 독립 NAND program 총량 검증은 별도다. window 단위 reward 귀속은 이번 변경의 검증 대상이 아니다.

시간대: Asia/Seoul (KST). 예비 실행·실패·중단을 포함해 모든 실행을 기록한다.

## 2026-09-06 — E0 Greedy 계측 예비 실험

기록 구분: **사후 작성**. 이 세션의 실행 출력, 저장된 로그, 빌드 정보로 복원했다. 실행 당시 기록하지 않은 값은 미확인으로 남긴다. 9월 3~4일 등 기존 실험은 이번 기록의 범위에 포함되지 않으며, 전체 과거 이력을 복원했다고 주장하지 않는다.

### 목적과 판정 범위

NVMeVirt 실행 가능 여부, GC 계측 출력, 기록된 host/GC 페이지 수로 재계산한 WAF의 일치를 확인한다. Greedy/CAT/iCAT 성능 비교나 E0 전체 통과 판정은 하지 않는다.

### 공통 환경과 실행 절차

- 커널: `7.0.0-30-generic`, fio `3.36`, mke2fs `1.47.0`.
- 모듈: [nvmev-e0-greedy-20260906.ko](buildoutput/nvmev-e0-greedy-20260906.ko).
- [빌드 정보](buildoutput/nvmev-e0-greedy-20260906.build-info.txt): 2026-09-06 16:01:57+09:00, `NVMEVIRT_GC_POLICY=GREEDY`.
- 모듈 SHA256: `20b211e576fdfd1d17bf3078fa53ef20dc71c7b72ff913f76f33a2a513eafe26`。사후 파일 해시와 빌드 기록의 일치를 확인했다. 실행별 로드 시점 해시 기록은 없다.
- 소스: `nvmevirt_test/`. 이 세션에서 정책 소스는 수정하지 않았다. 실행 당시 소스 전체 snapshot/hash 및 Git 변경 상태는 별도 보존하지 않았다.
- 예약 메모리: `memmap=8G$4G`, 모듈 인자 `memmap_start=4G memmap_size=8192M cpus=1,2`.
- 대상: 새 `/dev/nvme0n1`, model `CSL_Virt_MN_01`. 실행 전 namespace 및 대상 mount가 없음을 확인했다. 물리 SATA 디스크는 사용하지 않았다.
- 실제 초기화 로그: 물리 8,588,886,016 bytes, 논리 8,026,996,276 bytes, physical/logical 비율 설정 107%, FTL 4개, 각 FTL 8192 lines, line 크기 256 KiB.
- dispatcher CPU 1, I/O worker CPU 2. 실행 당시 CPU 주파수, 온도, background 부하, fio affinity 기록은 없다.
- 두 실행 모두 새 ext4, `mount -o nodiscard`, 6 GiB 순차 preset (128 KiB, libaio, direct I/O, iodepth 32, end_fsync).
- 본 작업: [test3.fio](workloads/test3.fio), 4 KiB random write, libaio, direct I/O, 최대 iodepth 32, time_based, randrepeat=1.
- hot: offset 0, 512 MiB, 6000 IOPS, seed 20260831.
- warm: offset 512 MiB, 1536 MiB, 3000 IOPS, seed 20260901.
- cold: offset 2 GiB, 4 GiB, 1000 IOPS, seed 20260902.
- 세 job이 동시에 실행되며 실제 요청 interleaving은 저장하지 않았다.
- 종료 절차: workload 종료, unmount, 모듈 제거, run marker 사이 dmesg 저장. 최종 카운터는 teardown 시점에 출력되므로 filesystem 종료 쓰기도 배제했다고 볼 수 없다.

### Run 1 — 60초

- ID: `20260906-160209-198214`, 시작 16:02:09 (ID 기준), 로그 파일 저장 약 16:03:14.
- 명령: `FIO_RUNTIME=60 bash /home/oy/iCAT/script/run.sh e0-greedy-20260906 test3 1`.
- 결과: script exit=0, preset 및 본 fio err=0. 본 작업 600,000 write I/O, 9999 IOPS, 39.1 MiB/s.
- 측정 카운터: host 125,697 pages, GC copy 0 pages, GC count 1962.
- WAF: 재계산 1.000000000, 로그 1.000. 선택 victim 1966개, 평균 vpc 0.
- 판정: 실행과 산술 확인 성공. GC 복사가 없어 복사 계측을 충분히 확인하지 못했다.
- 증거: [커널 로그](result/test3-e0-greedy-20260906-rep1-20260906-160209-198214.log). fio stdout은 세션 출력에만 있고 독립 파일로 저장하지 못했다.
- 후속 조치: 같은 workload의 실행 시간을 120초로 늘려 새로운 장치 상태에서 재실행.

### Run 2 — 120초

- ID: `20260906-160335-198920`, 시작 16:03:35 (ID 기준), 로그 파일 저장 약 16:05:39.
- 명령: `FIO_RUNTIME=120 bash /home/oy/iCAT/script/run.sh e0-greedy-20260906 test3 2` (stdout은 pipefail을 켜고 tee로 별도 저장).
- 변경 변수: 실행 시간 60초 → 120초. Run 1과 동일 조건 반복 실험이 아니다.
- 결과: script pipeline exit=0, preset 및 본 fio err=0. 본 작업 1,200,000 write I/O, 9999 IOPS, 39.1 MiB/s.
- 측정 카운터: host 725,723 pages, GC copy 342,531 pages, GC count 16,683.
- WAF: 재계산 1.471985868, 로그 1.471 (소수 셋째 자리 버림).
- 완결 window 0: host 262,144, GC 71,806, 재계산 1.273918152, 로그 1.273.
- 완결 window 1: host 262,144, GC 146,420, 재계산 1.558547974, 로그 1.558.
- latency: 평균 total latency 20.75 us, p99 completion latency 59 us. 두 지표의 정의가 다름에 유의한다. IOPS는 workload에서 제한한 값으로 장치 최대 성능이 아니다.
- 증거: [커널 로그](result/test3-e0-greedy-20260906-rep2-20260906-160335-198920.log), [fio 콘솔 출력](result/e0-greedy-20260906-rep2-console.txt).
- 판정: GC 복사가 관측됐으며 출력 카운터와 WAF 산술이 일치한다. 독립 NAND 쓰기 계측 검증은 아니다.

### 환경 대조와 한계

- 두 run의 초기화 로그에서 용량, geometry, Greedy 정책, channel 모델, CPU 배치가 일치한다. 시간·수행량·filesystem UUID 및 관측 결과는 다르다.
- 현재 카운터는 FTL별 첫 GC 완료 후 활성화된다. 공통 시점부터 전체 host 쓰기를 센 값이 아니며 fio 전체 I/O와 직접 비교하면 안 된다. victim 수와 GC count가 4 차이 나는 것도 FTL 4개의 첫 GC 제외와 일치한다.
- 동일 seed만으로 동시 job의 요청 순서나 FTL의 정확한 초기 상태가 동일하다고 보장할 수 없다. snapshot 비교나 trace 재생은 수행하지 않았다.
- 설정 소스 확인 결과: GC free-line threshold 2, GC delay 활성화, NAND program latency 185000 ns, erase latency 0, write early completion 1. 실제 SSD latency 재현성은 검증하지 않았다.
- 사후 조회한 CPU는 i7-7700, CPU 1/2 governor는 powersave였다. 실행 당시 governor/주파수 기록을 대신하는 근거로 사용하지 않는다.
- 빌드 경고: compiler 이름 차이, pahole 차이, MODULE_DESCRIPTION 누락, vmlinux 부재에 따른 BTF 생략. 빌드는 성공했다.
- 저장 커널 로그에서 BUG/Oops/WARNING/error 패턴은 발견하지 못했다. 두 실행 종료 뒤 namespace와 mount가 제거됨을 확인했다.
- 다음 과제: 공통 측정 시작 경계, 독립 쓰기량 대조, 실행별 환경 manifest와 콘솔 보존, 동일 시간/쓰기량 반복 검증. CAT/iCAT 비교와 full sweep은 아직 실행하지 않았다.

## 2026-09-06 — 실험 전 코드 구조·변경 범위 사후 점검

새 실험을 실행하지 않은 읽기 전용 코드 점검이다. 정책 코드를 수정하지 않았다.

- 비교 기준: `/home/oy/nvmevirt`, origin `https://github.com/snu-csl/nvmevirt.git`, 로컬 HEAD `61c90f7758cbd9545b4a4727e89377bf88eab060`, 추적 파일 변경 없음. 이 기준이 실험 코드의 정확한 역사적 부모라고 확인한 것은 아니다.
- 실험 디렉터리 `/home/oy/iCAT/nvmevirt_test`에는 Git 메타데이터가 없다. 변경 작성자·커밋 이력은 확인할 수 없다.
- 생성물과 `.git`을 제외한 디렉터리 비교에서 공통 파일의 차이는 `Kbuild`, `conv_ftl.c`, `conv_ftl.h` 세 개다. `Makefile.local`은 비교 기준에만 있다. 실험 build.sh는 외부 모듈 빌드 방식으로 해당 상위 Makefile을 거치지 않는다.
- 이번 세션에서는 Linux 커널 본체 수정/재빌드 없이 기존 NVMeVirt 실험 소스로 `.ko`를 빌드하고 로드했다.
- Kbuild 차이: 기본 NVM 타깃에서 conventional SSD 타깃으로 변경, Greedy/CAT_FIG7 및 Age/scale/ratio/window 컴파일 옵션 추가. 기준 디렉터리 기본 빌드를 그대로 비교군으로 쓰면 SSD 유형 자체가 달라진다.
- conv_ftl 차이: CAT age 변환과 점수 비교, CAT 후보 탐색, line 시각 필드, host/GC 카운터, WAF window와 종료 통계, victim 히스토그램 추가. Greedy 선택 분기는 기존 queue 경로를 유지하지만 계측 코드의 실행 비용은 추가된다.
- 실제 저장 컴파일 명령은 `BASE_SSD=SAMSUNG_970PRO`, `CONV_AGE_MODE=0`, `CONV_WAF_WINDOW_PAGES=262144`, `CONV_GC_POLICY=0`이다.
- 기존 README/REVIEW 설명과 불일치 발견: `last_invalid_ns`는 생성 시각으로 초기화되고 erase 시 0으로 초기화될 뿐, `mark_page_invalid()`에서 갱신되지 않는다. 따라서 현재 LAST_INVAL 경로는 의도한 마지막 무효화 Age를 구현하지 않는다. 기존 REVIEW.md의 갱신 구현 완료 주장은 현재 소스로 뒷받침되지 않는다. 이전 Age 비교 결과를 해당 의미의 증거로 사용하면 안 된다.
- 현재 소스에는 Greedy/CAT_FIG7만 정의돼 있으며 Q-table, reward update, 온라인 parameter 전환 구현은 확인되지 않았다. 두 예비 실행은 Greedy 계측 확인에만 해당한다.
- 사용자 요청에 따라 본 실험에 앞서 구조와 변경 범위를 설명한다. 추가 실행 전에 측정 시작 경계, Age 정의, 재현 가능한 입력과 환경 기록을 정리해야 한다.

## 2026-09-06 — 사용자 제공 GitHub 기준으로 변경 출처 정정

새 실험 없이 `https://github.com/meendragon/iCAT`을 별도 임시 디렉터리에 clone하여 읽기 전용으로 비교했다. 기존 로컬 코드와 결과는 덮어쓰지 않았다.

- 확인한 main HEAD: `8542e25a74034bcadd8417780ca64366d8586a5c`, 2026-08-24, `no reset age`. 이력은 `811884c` → `0a5c30d` → `8542e25`이다.
- 앞선 “Git 이력 없음”은 로컬 실험 폴더에 대한 설명이다. 제공된 GitHub 저장소에는 이력이 존재하며, 공개 코드의 변경은 이제 해당 커밋을 기준으로 추적할 수 있다. 로컬 추가 변경의 작성자/정확한 이력은 여전히 미확인이다.
- GitHub main에는 이미 Greedy/CAT_FIG7, 생성 시각 기준 Age, scale/ratio 컴파일 옵션, 누적 WAF 계측, 첫 GC 이후 계측 시작이 있다. 기존 전체 NVMeVirt와의 비교만으로 이를 모두 로컬 추가 구현이라고 해석하면 안 된다.
- GitHub main 대비 로컬 모듈 차이도 `Kbuild`, `conv_ftl.c`, `conv_ftl.h` 세 파일이다. 로컬에 추가된 것은 주로 WAF window 계측, victim 히스토그램, Age 모드 선택과 last_invalid_ns 필드, scale 5/10 허용이다.
- LAST_INVAL 갱신 누락은 로컬 확장에 해당한다. GitHub HEAD는 해당 옵션 없이 생성 시각을 사용하며, 무효화마다 Age를 갱신하지 않는 동작을 그 원본의 구현 오류라고 단정하면 안 된다.
- 공개 main의 소스에서도 Q-learning, Q-table, 온라인 parameter 변경 구현은 확인되지 않았다. 저장소 명칭과 현재 구현 범위를 구분한다.
- 이후 코드 비교 기준은 사용자 제공 저장소의 고정 커밋과 명시적인 로컬 diff로 기록한다.

## 2026-09-06 — GitHub 기존 결과 재분석과 후속 실험 기준

사용자 지시: GitHub의 기존 결과를 출발점으로 삼는다. 새 장치 실험 없이 공개 커밋 `8542e25a74034bcadd8417780ca64366d8586a5c`의 `result`, `result_e1`, `result_e2`를 읽고 host/GC 카운터에서 WAF를 재계산했다. 아래는 새 실행 결과가 아니다.

| 묶음 | workload/설정 라벨 | 재계산 WAF |
|---|---|---:|
| result_e1 | test2 Greedy | 1.555971 |
| result_e1 | test2 CAT | 1.510401 |
| result_e1 | test3 Greedy | 2.026447 |
| result_e1 | test3 CAT | 1.789770 |
| result_e2 | scale 25 | 1.839010 |
| result_e2 | scale 50 | 1.823606 |
| result_e2 | scale 100 | 1.789770 |
| result_e2 | scale 200 | 1.806792 |
| result_e2 | scale 400 | 1.820649 |
| result | scale 100 / ratio 4 | 1.826972 |
| result | scale 100 / ratio 7 | 1.815534 |
| result | scale 100 / ratio 16 | 1.807503 |

- 위 표는 비교 묶음별 표시다. `result/test3-cat-fig7-20260824-034545-992038.log`, `result_e1/test3-cat-fig7-20260824-034545-992038.log`, `result_e2/dmesg-100-cat-fig7-20260824-114247-1189444.log`는 SHA256 `12829d6237cba4433b839905a3d35eb3db7737794f00663501f58416fa1e9a28`로 동일하다. 전체 로그 13개는 고유 내용 11개이며 이 세 파일을 반복 3회로 세면 안 된다.
- `result_e1` 관측상 CAT WAF는 Greedy 대비 test2 약 2.93%, test3 약 11.68% 낮다. 반복 검증을 거친 평균 개선율은 아니다.
- scale 라벨 25/50/100/200/400에서는 100 라벨 결과가 가장 낮다. 다만 이 로그들은 scale/ratio를 본문에 출력하지 않아 파일명에 따른 설정 식별이다. 특히 100 결과는 앞선 실행의 복사본이다. 동일 모듈·조건에서 새로 수행한 완전한 sweep으로 단정할 수 없다.
- ratio 4/7/16은 로그에 scale=100 및 해당 ratio가 명시되어 있다. 실제 workload 이름은 로그 본문에 없으므로 묶음의 workload 대응은 문서/실행 기록과 추가 대조가 필요하다.
- 1.789770과 1.815534 차이를 곧바로 동일 조건 반복 편차라고 단정하지 않는다. 앞선 값에는 정확한 빌드·파라미터 연결 기록이 부족하다. 기존 REVIEW.md의 일부 ratio 숫자도 이번 원본 카운터 재계산값과 다르므로 위 값을 기준으로 사용한다.
- 저장 workload는 runtime=600, 6 GiB 영역, direct 4 KiB, 고정 seed와 합계 10000 IOPS 설정이다. 기존 모듈 build-info에는 kernel build dir `6.8.0-136-generic`가 기록돼 있으며 현재 예비 실행 커널은 `7.0.0-30-generic`이다. 모든 과거 run의 실제 커널을 확인한 것은 아니고, 두 환경의 동등성을 입증한 것도 아니다.
- 후속 첫 비교는 GitHub 기준의 생성 시각 Age와 600초 workload 조건을 유지한 Greedy 및 CAT scale=100/ratio=7의 반복 재현으로 정한다. 코드·계측 변경은 별도 버전과 일지로 구분한다. 동일 환경 반복의 변동을 확인한 뒤 scale/ratio sweep을 확장하고 phase 실험으로 진행한다.
- 이번 60/120초 로컬 예비 결과는 위 600초 기존 결과와 합산하거나 성능 개선 비교에 사용하지 않는다. LAST_INVAL이나 온라인 학습기를 이 재현 기준에 섞지 않는다.

## 2026-09-06 — baseline-20260906 사전 등록

- 목적: 현재 환경에서 Greedy와 고정 CAT의 기준 WAF와 동일 seed 반복 변동 확인. 과거 WAF와 일치하는 것을 통과 조건으로 삼지 않는다.
- 상태: 실행 준비. 예정 run ID는 baseline-20260906/run-1~6. 실제 실행 전후 시각과 결과는 아래에 자동 추가한다.
- 순서: Greedy, CAT, CAT, Greedy, Greedy, CAT. 정책별 3회이며 동일 장치 자원을 사용하므로 직렬 실행한다. 약 61분 예상.
- 사용 소스: 현재 `/home/oy/iCAT/nvmevirt_test`. GitHub 8542e25 대비 기존 로컬 계측 확장을 포함한다. 이번에는 정책 소스를 수정하지 않는다. 소스·스크립트·workload snapshot을 `result/baseline-20260906/source-snapshot.tar.gz`로 보존한다.
- 모듈: `baseline-20260906-greedy`, `baseline-20260906-cat`. 공통 CREATE Age, WAF window 262144 pages. CAT scale=100, ratio=7. 빌드 로그와 각 모듈 SHA256을 보존한다.
- workload: 기존 test3, 600초, 6 GiB preset, 4 KiB direct random write, hot/warm/cold=6000/3000/1000 IOPS, seeds=20260831/20260901/20260902.
- 장치/FTL: 기존 conventional SSD 설정, 약 8 GiB physical, PBA 비율 107%, FTL 4개, line 256 KiB. 각 run마다 새 장치·ext4·preset, nodiscard. CPU 1/2, memmap start 4G/size 8192M.
- 측정 경계: 기존 구현대로 각 FTL의 첫 GC 이후부터 teardown 시점까지. 전체 workload WAF나 정책 간 정확히 같은 입력 구간이라고 주장하지 않는다. 이 batch는 기존 계측 정의의 기준 측정이며 E0 전체 통과가 아니다.
- CPU governor·주파수·background 부하는 변경하지 않고 매 run 시작 snapshot에 기록한다. fio affinity 및 실제 요청 interleaving은 고정하지 않는다. 따라서 완전한 결정성이나 간섭 배제는 보장하지 않는다.
- 성공 기준: 6회 fio/script 오류 없이 종료, 각 로그의 정책/설정과 사전 조건 일치, host/GC 카운터 및 WAF 산술 확인, 종료 후 장치 해제. 실패하면 batch 중단하고 실패 로그 보존.
- 결과: `result/baseline-20260906/`에 build/console/environment, 기존 `result/`에 run별 커널 로그. 실행기는 `script/baseline-20260906.sh`이며 기존 실험 스크립트를 호출한다.
- 후속: 실행 후 정책별 WAF 평균·범위 및 run별 측정 쓰기량을 확인한다. 3회 동일 seed 결과를 multi-seed 통계로 표현하지 않는다.

### baseline-20260906 실행기 시작 시도 기록

18:20:58경 nohup 방식으로 batch 시작을 시도했으나, 다음 확인에서 프로세스가 종료되어 있었다. 환경 수집 파일은 커널 정보까지 있고 fio version 이전에 끊겨 있으며, 장치 생성과 workload 실행은 시작되지 않았다. 종료 원인과 코드는 미확인이다. 불완전 환경 파일을 `result/baseline-20260906/launch-attempt-1.environment.txt`로 보존하고 도구가 관리하는 지속 실행 세션으로 재시작한다.

## 이후 실행 기록 양식

- Run ID / 작성·시작·종료 시각 / 상태:
- 목적 / 판정 기준:
- 명령 / 변경 변수 / 고정 조건:
- 소스·모듈 식별 / 커널·도구 버전:
- 장치 / FTL·GC 설정 / CPU·시스템 부하:
- workload / seed / 초기화 / 측정 시작·종료 기준:
- 원본 로그·콘솔·환경 기록 경로:
- 종료 코드 / 수행량 / 결과 / 오류·경고:
- 해석 / 미검증 사항 / 정리 상태 / 다음 조치:

### baseline-20260906 run-1 greedy — started 2026-09-06T18:21:15+09:00

- Command: `FIO_RUNTIME=600 script/run.sh baseline-20260906-greedy test3 1`
- Environment: [snapshot](result/baseline-20260906/run-1-greedy.environment.txt)
- Output: [console](result/baseline-20260906/run-1-greedy.console.txt)

- Finished: 2026-09-06T18:31:19+09:00; run exit=0
- Kernel log: [test3-baseline-20260906-greedy-rep1-20260906-182115-216494.log](result/test3-baseline-20260906-greedy-rep1-20260906-182115-216494.log)
- Raw counters: `[244570.415769] NVMeVirt: GC stats: policy=greedy age_mode=create host_pages=5526019 gc_pages=5686448 gc_count=175185 WAF=2.029 scale_pct=0 age_ratio=0`
- Cleanup: module absent and target unmounted.

### baseline-20260906 run-2 cat — started 2026-09-06T18:31:19+09:00

- Command: `FIO_RUNTIME=600 script/run.sh baseline-20260906-cat test3 2`
- Environment: [snapshot](result/baseline-20260906/run-2-cat.environment.txt)
- Output: [console](result/baseline-20260906/run-2-cat.console.txt)

- Finished: 2026-09-06T18:41:23+09:00; run exit=0
- Kernel log: [test3-baseline-20260906-cat-rep2-20260906-183119-217870.log](result/test3-baseline-20260906-cat-rep2-20260906-183119-217870.log)
- Raw counters: `[245174.310666] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526019 gc_pages=4503182 gc_count=156697 WAF=1.814 scale_pct=100 age_ratio=7`
- Cleanup: module absent and target unmounted.

### baseline-20260906 run-3 cat — started 2026-09-06T18:41:23+09:00

- Command: `FIO_RUNTIME=600 script/run.sh baseline-20260906-cat test3 3`
- Environment: [snapshot](result/baseline-20260906/run-3-cat.environment.txt)
- Output: [console](result/baseline-20260906/run-3-cat.console.txt)

- Finished: 2026-09-06T18:51:27+09:00; run exit=0
- Kernel log: [test3-baseline-20260906-cat-rep3-20260906-184123-218968.log](result/test3-baseline-20260906-cat-rep3-20260906-184123-218968.log)
- Raw counters: `[245778.229991] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526077 gc_pages=4467979 gc_count=156148 WAF=1.808 scale_pct=100 age_ratio=7`
- Cleanup: module absent and target unmounted.

### baseline-20260906 run-4 greedy — started 2026-09-06T18:51:27+09:00

- Command: `FIO_RUNTIME=600 script/run.sh baseline-20260906-greedy test3 4`
- Environment: [snapshot](result/baseline-20260906/run-4-greedy.environment.txt)
- Output: [console](result/baseline-20260906/run-4-greedy.console.txt)

- Finished: 2026-09-06T19:01:30+09:00; run exit=0
- Kernel log: [test3-baseline-20260906-greedy-rep4-20260906-185127-220080.log](result/test3-baseline-20260906-greedy-rep4-20260906-185127-220080.log)
- Raw counters: `[246382.121876] NVMeVirt: GC stats: policy=greedy age_mode=create host_pages=5526077 gc_pages=5643188 gc_count=174510 WAF=2.021 scale_pct=0 age_ratio=0`
- Cleanup: module absent and target unmounted.

### baseline-20260906 run-5 greedy — started 2026-09-06T19:01:31+09:00

- Command: `FIO_RUNTIME=600 script/run.sh baseline-20260906-greedy test3 5`
- Environment: [snapshot](result/baseline-20260906/run-5-greedy.environment.txt)
- Output: [console](result/baseline-20260906/run-5-greedy.console.txt)

- Finished: 2026-09-06T19:11:34+09:00; run exit=0
- Kernel log: [test3-baseline-20260906-greedy-rep5-20260906-190131-221212.log](result/test3-baseline-20260906-greedy-rep5-20260906-190131-221212.log)
- Raw counters: `[246986.005109] NVMeVirt: GC stats: policy=greedy age_mode=create host_pages=5526019 gc_pages=5647665 gc_count=174579 WAF=2.022 scale_pct=0 age_ratio=0`
- Cleanup: module absent and target unmounted.

### baseline-20260906 run-6 cat — started 2026-09-06T19:11:34+09:00

- Command: `FIO_RUNTIME=600 script/run.sh baseline-20260906-cat test3 6`
- Environment: [snapshot](result/baseline-20260906/run-6-cat.environment.txt)
- Output: [console](result/baseline-20260906/run-6-cat.console.txt)

- Finished: 2026-09-06T19:21:38+09:00; run exit=0
- Kernel log: [test3-baseline-20260906-cat-rep6-20260906-191134-222270.log](result/test3-baseline-20260906-cat-rep6-20260906-191134-222270.log)
- Raw counters: `[247589.911098] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=4509700 gc_count=156799 WAF=1.816 scale_pct=100 age_ratio=7`
- Cleanup: module absent and target unmounted.

- baseline-20260906: all six executions finished at 2026-09-06T19:21:38+09:00; statistical review pending.

## 2026-09-06 — cat-sweep-20260906 사전 등록

- 사용자 승인: CAT 추가 실험 시작. 목적은 scale/ratio 민감도 및 test2/test3별 좋은 설정 차이를 관측하는 것이다.
- 후보: scale={25,50,100,200,400}, ratio={4,7,16}, 15개 조합. Age=CREATE, 구간 수 7 고정. 전체 x/y/z sweep이 아닌 기존 두 축의 전체 조합 실험이다.
- 각 workload·조합 600초 × 동일 seed 3회. 90개 관측 중 기존 baseline test3 scale=100/ratio=7의 run-2,3,6을 각각 반복 1,2,3으로 재사용하고 신규 실행은 87회다. 재사용 조건은 새 100/7 모듈과 baseline 모듈의 byte 일치 및 workload/preset/script·소스 보존본 비교이다. 시점 차이와 host 부하 차이는 여전히 한계다.
- 고정 조건: 기존 test2/test3의 seed와 IOPS, 6 GiB 순차 preset, 새 ext4/nodiscard, physical 약 8 GiB, logical 비율 107%, FTL 4개, line 256 KiB, CPU 1/2, memmap 4G+8192M, 동일 커널. 기존 NAND 지연 모델과 첫 GC 이후 계측 정의 유지. 정책 코드 수정 없음.
- test2: hot 1 GiB/8000 IOPS/seed 20260821, cold 5 GiB/2000 IOPS/seed 20260822. test3는 baseline과 동일.
- 실행 순서는 `result/cat-sweep-20260906/plan.tsv`에 사전 저장한다. 각 반복에서 15개 설정의 순서를 결정적 순열로 바꾸고 workload를 교차 실행한다. 무작위 추출이나 multi-seed 실험이라고 표현하지 않는다.
- 예상 소요: 신규 87회 약 14시간 40분 이상, 빌드·시스템 지연 별도. 같은 장치를 사용하므로 직렬 실행한다.
- 실행기: `script/cat-sweep-20260906.sh`. 단계: plan → 소스/입력 보존 → build → run. 매 run 전에 입력/모듈 hash 확인, 장치 미사용 확인, 환경 snapshot과 일지 작성. 종료 후 console/kernel log/카운터/상태 기록. 오류나 hash 변경 시 중단하며 기존 결과를 덮어쓰지 않는다.
- 성공 기준: 계획된 신규 87회 완료, 정책/scale/ratio와 카운터 일치, 각 run 종료 후 장치 해제. 완료 후 재사용 3건을 포함해 설정별 평균·범위·민감도를 계산한다. 차이가 작으면 단일 최적점을 확정하지 않는다.
- 한계: 첫 GC 시점은 partition별, fio job interleaving/CPU 부하/주파수는 고정하지 않고 환경을 기록한다. 전체 workload WAF, 독립 NAND 계측 검증, 온라인 적응 효과, phase oracle, Q-learning 비교는 이번 범위가 아니다.

### cat-sweep 시작 전 검증

- 실행기 `bash -n` 통과. 계획 87행, 신규 조건 29개, 조건별 반복 3회 확인.
- baseline snapshot 대비 소스·workload 디렉터리 및 run/start/end/env 스크립트가 일치한다 (빌드 생성물 제외).
- 15개 모듈 빌드 완료, build 단계 exit=0. 새 scale=100/ratio=7 모듈은 기존 baseline CAT 모듈과 byte 단위로 일치한다. SHA256 `2e4616f1bcf460e595952a24f7e67fc56d80d7f26122c14bfe2cf8bedcf9a15e`.
- 모든 모듈 hash는 `result/cat-sweep-20260906/modules.sha256`, 입력 hash는 `inputs.sha256`, 소스 보존본은 `source-snapshot.tar.gz`에 저장했다.
- 빌드 로그에 기존 compiler/pahole 차이, MODULE_DESCRIPTION/BTF 관련 경고가 있을 수 있으며 각 build 로그를 보존했다. 성공 빌드를 경고 없음으로 표현하지 않는다.

### baseline-20260906 완료 후 기초 집계

- 6회 모두 run exit=0, preset/main fio err=0. 본 workload는 각 6,000,000 write I/O 수행. 종료 후 namespace 없음 및 mount 해제를 다시 확인했다.
- 원시 host/GC 카운터로 재계산한 WAF는 6회 모두 로그의 소수 셋째 자리 버림 값과 일치했다.
- Greedy: 2.029031569, 2.021192430, 2.022013316. 평균 2.024079105, 범위 2.021192430~2.029031569.
- CAT: 1.814905269, 1.808526374, 1.816085223. 평균 1.813172289, 범위 1.808526374~1.816085223.
- 평균 WAF 기준 CAT 감소율 10.4199%. 단일 test3, 동일 seed 3회, 기존 첫-GC 이후 계측 정의에서 관측한 결과다. iCAT 효과나 multi-seed 검증을 뜻하지 않는다.
- 이 집계는 실행 완료와 기본 수치 검증이다. 환경 snapshot 전체 대조 및 논문용 통계 분석 완료를 뜻하지 않는다.

### cat-sweep-20260906 run-001 — started 2026-09-06T19:44:45+09:00

- Workload=test2 scale=25 ratio=4 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a25-r4 test2 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-001.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-001.console.txt)

- Finished: 2026-09-06T19:54:49+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a25-r4-rep1-20260906-194445-231423.log](result/test2-sweep-20260906-a25-r4-rep1-20260906-194445-231423.log)
- Raw counters: `[249580.882933] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=3045637 gc_count=133922 WAF=1.551 scale_pct=25 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-002 — started 2026-09-06T19:54:49+09:00

- Workload=test3 scale=25 ratio=4 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a25-r4 test3 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-002.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-002.console.txt)

- Finished: 2026-09-06T20:04:53+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a25-r4-rep1-20260906-195449-232693.log](result/test3-sweep-20260906-a25-r4-rep1-20260906-195449-232693.log)
- Raw counters: `[250184.845188] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=4855434 gc_count=162201 WAF=1.878 scale_pct=25 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-003 — started 2026-09-06T20:04:53+09:00

- Workload=test2 scale=100 ratio=7 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a100-r7 test2 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-003.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-003.console.txt)

- Finished: 2026-09-06T20:14:57+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a100-r7-rep1-20260906-200453-233817.log](result/test2-sweep-20260906-a100-r7-rep1-20260906-200453-233817.log)
- Raw counters: `[250788.814210] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=2887231 gc_count=131446 WAF=1.522 scale_pct=100 age_ratio=7`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-004 — started 2026-09-06T20:14:57+09:00

- Workload=test2 scale=400 ratio=16 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a400-r16 test2 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-004.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-004.console.txt)

- Finished: 2026-09-06T20:25:01+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a400-r16-rep1-20260906-201457-235012.log](result/test2-sweep-20260906-a400-r16-rep1-20260906-201457-235012.log)
- Raw counters: `[251392.789419] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526082 gc_pages=2533119 gc_count=125916 WAF=1.458 scale_pct=400 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-005 — started 2026-09-06T20:25:01+09:00

- Workload=test3 scale=400 ratio=16 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a400-r16 test3 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-005.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-005.console.txt)

- Finished: 2026-09-06T20:35:05+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a400-r16-rep1-20260906-202501-236052.log](result/test3-sweep-20260906-a400-r16-rep1-20260906-202501-236052.log)
- Raw counters: `[251996.686389] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=4596245 gc_count=158151 WAF=1.831 scale_pct=400 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-006 — started 2026-09-06T20:35:05+09:00

- Workload=test2 scale=100 ratio=4 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a100-r4 test2 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-006.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-006.console.txt)

- Finished: 2026-09-06T20:45:09+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a100-r4-rep1-20260906-203505-237387.log](result/test2-sweep-20260906-a100-r4-rep1-20260906-203505-237387.log)
- Raw counters: `[252600.608417] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526019 gc_pages=2911862 gc_count=131833 WAF=1.526 scale_pct=100 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-007 — started 2026-09-06T20:45:09+09:00

- Workload=test3 scale=100 ratio=4 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a100-r4 test3 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-007.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-007.console.txt)

- Finished: 2026-09-06T20:55:13+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a100-r4-rep1-20260906-204509-238560.log](result/test3-sweep-20260906-a100-r4-rep1-20260906-204509-238560.log)
- Raw counters: `[253204.540135] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526078 gc_pages=4536168 gc_count=157213 WAF=1.820 scale_pct=100 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-008 — started 2026-09-06T20:55:13+09:00

- Workload=test2 scale=400 ratio=7 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a400-r7 test2 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-008.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-008.console.txt)

- Finished: 2026-09-06T21:05:17+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a400-r7-rep1-20260906-205513-239823.log](result/test2-sweep-20260906-a400-r7-rep1-20260906-205513-239823.log)
- Raw counters: `[253808.451460] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526085 gc_pages=2616967 gc_count=127225 WAF=1.473 scale_pct=400 age_ratio=7`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-009 — started 2026-09-06T21:05:17+09:00

- Workload=test3 scale=400 ratio=7 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a400-r7 test3 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-009.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-009.console.txt)

- Finished: 2026-09-06T21:15:21+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a400-r7-rep1-20260906-210517-240955.log](result/test3-sweep-20260906-a400-r7-rep1-20260906-210517-240955.log)
- Raw counters: `[254412.373017] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526019 gc_pages=4507658 gc_count=156767 WAF=1.815 scale_pct=400 age_ratio=7`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-010 — started 2026-09-06T21:15:21+09:00

- Workload=test2 scale=50 ratio=16 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a50-r16 test2 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-010.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-010.console.txt)

- Finished: 2026-09-06T21:25:25+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a50-r16-rep1-20260906-211521-242120.log](result/test2-sweep-20260906-a50-r16-rep1-20260906-211521-242120.log)
- Raw counters: `[255016.301960] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=2923698 gc_count=132016 WAF=1.529 scale_pct=50 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-011 — started 2026-09-06T21:25:25+09:00

- Workload=test3 scale=50 ratio=16 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a50-r16 test3 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-011.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-011.console.txt)

- Finished: 2026-09-06T21:35:28+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a50-r16-rep1-20260906-212525-243167.log](result/test3-sweep-20260906-a50-r16-rep1-20260906-212525-243167.log)
- Raw counters: `[255620.222373] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526086 gc_pages=4468366 gc_count=156154 WAF=1.808 scale_pct=50 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-012 — started 2026-09-06T21:35:28+09:00

- Workload=test2 scale=400 ratio=4 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a400-r4 test2 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-012.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-012.console.txt)

- Finished: 2026-09-06T21:45:32+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a400-r4-rep1-20260906-213529-244303.log](result/test2-sweep-20260906-a400-r4-rep1-20260906-213529-244303.log)
- Raw counters: `[256224.163741] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=2845126 gc_count=130789 WAF=1.514 scale_pct=400 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-013 — started 2026-09-06T21:45:32+09:00

- Workload=test3 scale=400 ratio=4 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a400-r4 test3 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-013.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-013.console.txt)

- Finished: 2026-09-06T21:55:36+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a400-r4-rep1-20260906-214532-245482.log](result/test3-sweep-20260906-a400-r4-rep1-20260906-214532-245482.log)
- Raw counters: `[256828.103173] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526024 gc_pages=4468081 gc_count=156148 WAF=1.808 scale_pct=400 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-014 — started 2026-09-06T21:55:36+09:00

- Workload=test2 scale=50 ratio=7 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a50-r7 test2 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-014.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-014.console.txt)

- Finished: 2026-09-06T22:05:40+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a50-r7-rep1-20260906-215536-246469.log](result/test2-sweep-20260906-a50-r7-rep1-20260906-215536-246469.log)
- Raw counters: `[257432.044463] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=2955511 gc_count=132513 WAF=1.534 scale_pct=50 age_ratio=7`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-015 — started 2026-09-06T22:05:40+09:00

- Workload=test3 scale=50 ratio=7 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a50-r7 test3 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-015.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-015.console.txt)

- Finished: 2026-09-06T22:15:44+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a50-r7-rep1-20260906-220540-247727.log](result/test3-sweep-20260906-a50-r7-rep1-20260906-220540-247727.log)
- Raw counters: `[258035.975845] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=4572147 gc_count=157774 WAF=1.827 scale_pct=50 age_ratio=7`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-016 — started 2026-09-06T22:15:44+09:00

- Workload=test2 scale=200 ratio=16 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a200-r16 test2 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-016.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-016.console.txt)

- Finished: 2026-09-06T22:25:48+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a200-r16-rep1-20260906-221544-248879.log](result/test2-sweep-20260906-a200-r16-rep1-20260906-221544-248879.log)
- Raw counters: `[258639.906233] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526015 gc_pages=2801296 gc_count=130105 WAF=1.506 scale_pct=200 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-017 — started 2026-09-06T22:25:48+09:00

- Workload=test3 scale=200 ratio=16 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a200-r16 test3 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-017.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-017.console.txt)

- Finished: 2026-09-06T22:35:52+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a200-r16-rep1-20260906-222548-249933.log](result/test3-sweep-20260906-a200-r16-rep1-20260906-222548-249933.log)
- Raw counters: `[259243.806376] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526023 gc_pages=4481270 gc_count=156355 WAF=1.810 scale_pct=200 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-018 — started 2026-09-06T22:35:52+09:00

- Workload=test2 scale=50 ratio=4 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a50-r4 test2 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-018.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-018.console.txt)

- Finished: 2026-09-06T22:45:56+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a50-r4-rep1-20260906-223552-251127.log](result/test2-sweep-20260906-a50-r4-rep1-20260906-223552-251127.log)
- Raw counters: `[259847.713879] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526042 gc_pages=2970799 gc_count=132754 WAF=1.537 scale_pct=50 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-019 — started 2026-09-06T22:45:56+09:00

- Workload=test3 scale=50 ratio=4 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a50-r4 test3 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-019.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-019.console.txt)

- Finished: 2026-09-06T22:56:00+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a50-r4-rep1-20260906-224556-252279.log](result/test3-sweep-20260906-a50-r4-rep1-20260906-224556-252279.log)
- Raw counters: `[260451.675824] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526015 gc_pages=4637708 gc_count=158799 WAF=1.839 scale_pct=50 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-020 — started 2026-09-06T22:56:00+09:00

- Workload=test2 scale=200 ratio=7 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a200-r7 test2 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-020.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-020.console.txt)

- Finished: 2026-09-06T23:06:04+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a200-r7-rep1-20260906-225600-253271.log](result/test2-sweep-20260906-a200-r7-rep1-20260906-225600-253271.log)
- Raw counters: `[261055.591786] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5525577 gc_pages=2722754 gc_count=128871 WAF=1.492 scale_pct=200 age_ratio=7`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-021 — started 2026-09-06T23:06:04+09:00

- Workload=test3 scale=200 ratio=7 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a200-r7 test3 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-021.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-021.console.txt)

- Finished: 2026-09-06T23:16:08+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a200-r7-rep1-20260906-230604-254440.log](result/test3-sweep-20260906-a200-r7-rep1-20260906-230604-254440.log)
- Raw counters: `[261659.548864] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526084 gc_pages=4393946 gc_count=154991 WAF=1.795 scale_pct=200 age_ratio=7`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-022 — started 2026-09-06T23:16:08+09:00

- Workload=test2 scale=25 ratio=16 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a25-r16 test2 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-022.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-022.console.txt)

- Finished: 2026-09-06T23:26:12+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a25-r16-rep1-20260906-231608-255562.log](result/test2-sweep-20260906-a25-r16-rep1-20260906-231608-255562.log)
- Raw counters: `[262263.422379] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526082 gc_pages=2957400 gc_count=132545 WAF=1.535 scale_pct=25 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-023 — started 2026-09-06T23:26:12+09:00

- Workload=test3 scale=25 ratio=16 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a25-r16 test3 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-023.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-023.console.txt)

- Finished: 2026-09-06T23:36:15+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a25-r16-rep1-20260906-232612-256610.log](result/test3-sweep-20260906-a25-r16-rep1-20260906-232612-256610.log)
- Raw counters: `[262867.331460] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526017 gc_pages=4763460 gc_count=160764 WAF=1.862 scale_pct=25 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-024 — started 2026-09-06T23:36:16+09:00

- Workload=test2 scale=200 ratio=4 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a200-r4 test2 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-024.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-024.console.txt)

- Finished: 2026-09-06T23:46:19+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a200-r4-rep1-20260906-233616-257792.log](result/test2-sweep-20260906-a200-r4-rep1-20260906-233616-257792.log)
- Raw counters: `[263471.249514] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526017 gc_pages=2958521 gc_count=132561 WAF=1.535 scale_pct=200 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-025 — started 2026-09-06T23:46:19+09:00

- Workload=test3 scale=200 ratio=4 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a200-r4 test3 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-025.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-025.console.txt)

- Finished: 2026-09-06T23:56:23+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a200-r4-rep1-20260906-234620-258904.log](result/test3-sweep-20260906-a200-r4-rep1-20260906-234620-258904.log)
- Raw counters: `[264075.185143] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526081 gc_pages=4422672 gc_count=155440 WAF=1.800 scale_pct=200 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-026 — started 2026-09-06T23:56:23+09:00

- Workload=test2 scale=25 ratio=7 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a25-r7 test2 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-026.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-026.console.txt)

- Finished: 2026-09-07T00:06:27+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a25-r7-rep1-20260906-235623-259905.log](result/test2-sweep-20260906-a25-r7-rep1-20260906-235623-259905.log)
- Raw counters: `[264679.149311] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=3009097 gc_count=133352 WAF=1.544 scale_pct=25 age_ratio=7`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-027 — started 2026-09-07T00:06:27+09:00

- Workload=test3 scale=25 ratio=7 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a25-r7 test3 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-027.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-027.console.txt)

- Finished: 2026-09-07T00:16:31+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a25-r7-rep1-20260907-000627-261301.log](result/test3-sweep-20260906-a25-r7-rep1-20260907-000627-261301.log)
- Raw counters: `[265283.056392] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=4789705 gc_count=161174 WAF=1.866 scale_pct=25 age_ratio=7`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-028 — started 2026-09-07T00:16:31+09:00

- Workload=test2 scale=100 ratio=16 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a100-r16 test2 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-028.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-028.console.txt)

- Finished: 2026-09-07T00:26:35+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a100-r16-rep1-20260907-001631-262448.log](result/test2-sweep-20260906-a100-r16-rep1-20260907-001631-262448.log)
- Raw counters: `[265886.992457] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=2826834 gc_count=130503 WAF=1.511 scale_pct=100 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-029 — started 2026-09-07T00:26:35+09:00

- Workload=test3 scale=100 ratio=16 repetition=1, runtime=600
- Command: `script/run.sh sweep-20260906-a100-r16 test3 1`
- Environment: [snapshot](result/cat-sweep-20260906/run-029.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-029.console.txt)

- Finished: 2026-09-07T00:36:39+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a100-r16-rep1-20260907-002635-263559.log](result/test3-sweep-20260906-a100-r16-rep1-20260907-002635-263559.log)
- Raw counters: `[266490.924719] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5517897 gc_pages=4348999 gc_count=154161 WAF=1.788 scale_pct=100 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-030 — started 2026-09-07T00:36:39+09:00

- Workload=test2 scale=50 ratio=16 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a50-r16 test2 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-030.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-030.console.txt)

- Finished: 2026-09-07T00:46:43+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a50-r16-rep2-20260907-003639-264732.log](result/test2-sweep-20260906-a50-r16-rep2-20260907-003639-264732.log)
- Raw counters: `[267094.864461] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=2919128 gc_count=131945 WAF=1.528 scale_pct=50 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-031 — started 2026-09-07T00:46:43+09:00

- Workload=test3 scale=50 ratio=16 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a50-r16 test3 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-031.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-031.console.txt)

- Finished: 2026-09-07T00:56:47+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a50-r16-rep2-20260907-004643-265856.log](result/test3-sweep-20260906-a50-r16-rep2-20260907-004643-265856.log)
- Raw counters: `[267698.808795] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=4536910 gc_count=157224 WAF=1.821 scale_pct=50 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-032 — started 2026-09-07T00:56:47+09:00

- Workload=test2 scale=400 ratio=4 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a400-r4 test2 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-032.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-032.console.txt)

- Finished: 2026-09-07T01:06:51+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a400-r4-rep2-20260907-005647-266868.log](result/test2-sweep-20260906-a400-r4-rep2-20260907-005647-266868.log)
- Raw counters: `[268302.691645] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526041 gc_pages=2841946 gc_count=130739 WAF=1.514 scale_pct=400 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-033 — started 2026-09-07T01:06:51+09:00

- Workload=test3 scale=400 ratio=4 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a400-r4 test3 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-033.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-033.console.txt)

- Finished: 2026-09-07T01:16:55+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a400-r4-rep2-20260907-010651-268056.log](result/test3-sweep-20260906-a400-r4-rep2-20260907-010651-268056.log)
- Raw counters: `[268906.620663] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526020 gc_pages=4472466 gc_count=156217 WAF=1.809 scale_pct=400 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-034 — started 2026-09-07T01:16:55+09:00

- Workload=test2 scale=50 ratio=7 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a50-r7 test2 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-034.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-034.console.txt)

- Finished: 2026-09-07T01:26:59+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a50-r7-rep2-20260907-011655-269169.log](result/test2-sweep-20260906-a50-r7-rep2-20260907-011655-269169.log)
- Raw counters: `[269510.539256] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=2954989 gc_count=132506 WAF=1.534 scale_pct=50 age_ratio=7`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-035 — started 2026-09-07T01:26:59+09:00

- Workload=test3 scale=50 ratio=7 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a50-r7 test3 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-035.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-035.console.txt)

- Finished: 2026-09-07T01:37:02+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a50-r7-rep2-20260907-012659-270205.log](result/test3-sweep-20260906-a50-r7-rep2-20260907-012659-270205.log)
- Raw counters: `[270114.382987] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=4581235 gc_count=157917 WAF=1.829 scale_pct=50 age_ratio=7`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-036 — started 2026-09-07T01:37:02+09:00

- Workload=test2 scale=200 ratio=16 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a200-r16 test2 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-036.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-036.console.txt)

- Finished: 2026-09-07T01:47:06+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a200-r16-rep2-20260907-013703-271418.log](result/test2-sweep-20260906-a200-r16-rep2-20260907-013703-271418.log)
- Raw counters: `[270718.288008] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=2839823 gc_count=130706 WAF=1.513 scale_pct=200 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-037 — started 2026-09-07T01:47:06+09:00

- Workload=test3 scale=200 ratio=16 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a200-r16 test3 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-037.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-037.console.txt)

- Finished: 2026-09-07T01:57:10+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a200-r16-rep2-20260907-014707-272553.log](result/test3-sweep-20260906-a200-r16-rep2-20260907-014707-272553.log)
- Raw counters: `[271322.204900] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=4471619 gc_count=156204 WAF=1.809 scale_pct=200 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-038 — started 2026-09-07T01:57:10+09:00

- Workload=test2 scale=50 ratio=4 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a50-r4 test2 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-038.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-038.console.txt)

- Finished: 2026-09-07T02:07:14+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a50-r4-rep2-20260907-015710-273546.log](result/test2-sweep-20260906-a50-r4-rep2-20260907-015710-273546.log)
- Raw counters: `[271926.147672] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=2966022 gc_count=132678 WAF=1.536 scale_pct=50 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-039 — started 2026-09-07T02:07:14+09:00

- Workload=test3 scale=50 ratio=4 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a50-r4 test3 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-039.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-039.console.txt)

- Finished: 2026-09-07T02:17:18+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a50-r4-rep2-20260907-020714-274722.log](result/test3-sweep-20260906-a50-r4-rep2-20260907-020714-274722.log)
- Raw counters: `[272530.116780] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526065 gc_pages=4639762 gc_count=158832 WAF=1.839 scale_pct=50 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-040 — started 2026-09-07T02:17:18+09:00

- Workload=test2 scale=200 ratio=7 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a200-r7 test2 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-040.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-040.console.txt)

- Finished: 2026-09-07T02:27:22+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a200-r7-rep2-20260907-021718-275868.log](result/test2-sweep-20260906-a200-r7-rep2-20260907-021718-275868.log)
- Raw counters: `[273134.097746] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=2876978 gc_count=131287 WAF=1.520 scale_pct=200 age_ratio=7`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-041 — started 2026-09-07T02:27:22+09:00

- Workload=test3 scale=200 ratio=7 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a200-r7 test3 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-041.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-041.console.txt)

- Finished: 2026-09-07T02:37:26+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a200-r7-rep2-20260907-022722-276911.log](result/test3-sweep-20260906-a200-r7-rep2-20260907-022722-276911.log)
- Raw counters: `[273738.036581] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526073 gc_pages=4441125 gc_count=155728 WAF=1.803 scale_pct=200 age_ratio=7`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-042 — started 2026-09-07T02:37:26+09:00

- Workload=test2 scale=25 ratio=16 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a25-r16 test2 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-042.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-042.console.txt)

- Finished: 2026-09-07T02:47:30+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a25-r16-rep2-20260907-023726-278094.log](result/test2-sweep-20260906-a25-r16-rep2-20260907-023726-278094.log)
- Raw counters: `[274341.901412] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=3032825 gc_count=133722 WAF=1.548 scale_pct=25 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-043 — started 2026-09-07T02:47:30+09:00

- Workload=test3 scale=25 ratio=16 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a25-r16 test3 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-043.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-043.console.txt)

- Finished: 2026-09-07T02:57:34+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a25-r16-rep2-20260907-024730-279214.log](result/test3-sweep-20260906-a25-r16-rep2-20260907-024730-279214.log)
- Raw counters: `[274945.807849] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526079 gc_pages=4695697 gc_count=159706 WAF=1.849 scale_pct=25 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-044 — started 2026-09-07T02:57:34+09:00

- Workload=test2 scale=200 ratio=4 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a200-r4 test2 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-044.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-044.console.txt)

- Finished: 2026-09-07T03:07:38+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a200-r4-rep2-20260907-025734-280207.log](result/test2-sweep-20260906-a200-r4-rep2-20260907-025734-280207.log)
- Raw counters: `[275549.720276] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=2952715 gc_count=132470 WAF=1.534 scale_pct=200 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-045 — started 2026-09-07T03:07:38+09:00

- Workload=test3 scale=200 ratio=4 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a200-r4 test3 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-045.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-045.console.txt)

- Finished: 2026-09-07T03:17:42+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a200-r4-rep2-20260907-030738-281402.log](result/test3-sweep-20260906-a200-r4-rep2-20260907-030738-281402.log)
- Raw counters: `[276153.636310] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=4492342 gc_count=156528 WAF=1.812 scale_pct=200 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-046 — started 2026-09-07T03:17:42+09:00

- Workload=test2 scale=25 ratio=7 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a25-r7 test2 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-046.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-046.console.txt)

- Finished: 2026-09-07T03:27:46+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a25-r7-rep2-20260907-031742-282536.log](result/test2-sweep-20260906-a25-r7-rep2-20260907-031742-282536.log)
- Raw counters: `[276757.563963] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5512263 gc_pages=2820573 gc_count=130191 WAF=1.511 scale_pct=25 age_ratio=7`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-047 — started 2026-09-07T03:27:46+09:00

- Workload=test3 scale=25 ratio=7 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a25-r7 test3 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-047.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-047.console.txt)

- Finished: 2026-09-07T03:37:49+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a25-r7-rep2-20260907-032746-283557.log](result/test3-sweep-20260906-a25-r7-rep2-20260907-032746-283557.log)
- Raw counters: `[277361.493672] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=4791319 gc_count=161199 WAF=1.867 scale_pct=25 age_ratio=7`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-048 — started 2026-09-07T03:37:50+09:00

- Workload=test2 scale=100 ratio=16 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a100-r16 test2 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-048.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-048.console.txt)

- Finished: 2026-09-07T03:47:53+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a100-r16-rep2-20260907-033750-284747.log](result/test2-sweep-20260906-a100-r16-rep2-20260907-033750-284747.log)
- Raw counters: `[277965.413478] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526085 gc_pages=2707983 gc_count=128648 WAF=1.490 scale_pct=100 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-049 — started 2026-09-07T03:47:53+09:00

- Workload=test3 scale=100 ratio=16 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a100-r16 test3 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-049.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-049.console.txt)

- Finished: 2026-09-07T03:57:57+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a100-r16-rep2-20260907-034754-285891.log](result/test3-sweep-20260906-a100-r16-rep2-20260907-034754-285891.log)
- Raw counters: `[278569.330682] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=4485160 gc_count=156415 WAF=1.811 scale_pct=100 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-050 — started 2026-09-07T03:57:57+09:00

- Workload=test2 scale=25 ratio=4 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a25-r4 test2 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-050.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-050.console.txt)

- Finished: 2026-09-07T04:08:01+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a25-r4-rep2-20260907-035757-286890.log](result/test2-sweep-20260906-a25-r4-rep2-20260907-035757-286890.log)
- Raw counters: `[279173.249632] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526018 gc_pages=3047419 gc_count=133950 WAF=1.551 scale_pct=25 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-051 — started 2026-09-07T04:08:01+09:00

- Workload=test3 scale=25 ratio=4 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a25-r4 test3 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-051.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-051.console.txt)

- Finished: 2026-09-07T04:18:05+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a25-r4-rep2-20260907-040801-288063.log](result/test3-sweep-20260906-a25-r4-rep2-20260907-040801-288063.log)
- Raw counters: `[279777.171017] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=4845736 gc_count=162049 WAF=1.876 scale_pct=25 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-052 — started 2026-09-07T04:18:05+09:00

- Workload=test2 scale=100 ratio=7 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a100-r7 test2 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-052.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-052.console.txt)

- Finished: 2026-09-07T04:28:09+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a100-r7-rep2-20260907-041805-289226.log](result/test2-sweep-20260906-a100-r7-rep2-20260907-041805-289226.log)
- Raw counters: `[280381.141576] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=2886079 gc_count=131429 WAF=1.522 scale_pct=100 age_ratio=7`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-053 — started 2026-09-07T04:28:09+09:00

- Workload=test2 scale=400 ratio=16 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a400-r16 test2 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-053.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-053.console.txt)

- Finished: 2026-09-07T04:38:13+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a400-r16-rep2-20260907-042809-290248.log](result/test2-sweep-20260906-a400-r16-rep2-20260907-042809-290248.log)
- Raw counters: `[280985.082246] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526048 gc_pages=2621311 gc_count=127292 WAF=1.474 scale_pct=400 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-054 — started 2026-09-07T04:38:13+09:00

- Workload=test3 scale=400 ratio=16 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a400-r16 test3 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-054.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-054.console.txt)

- Finished: 2026-09-07T04:48:17+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a400-r16-rep2-20260907-043813-291447.log](result/test3-sweep-20260906-a400-r16-rep2-20260907-043813-291447.log)
- Raw counters: `[281589.000824] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=4597250 gc_count=158167 WAF=1.831 scale_pct=400 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-055 — started 2026-09-07T04:48:17+09:00

- Workload=test2 scale=100 ratio=4 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a100-r4 test2 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-055.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-055.console.txt)

- Finished: 2026-09-07T04:58:21+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a100-r4-rep2-20260907-044817-292578.log](result/test2-sweep-20260906-a100-r4-rep2-20260907-044817-292578.log)
- Raw counters: `[282192.949168] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=2938163 gc_count=132243 WAF=1.531 scale_pct=100 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-056 — started 2026-09-07T04:58:21+09:00

- Workload=test3 scale=100 ratio=4 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a100-r4 test3 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-056.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-056.console.txt)

- Finished: 2026-09-07T05:08:25+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a100-r4-rep2-20260907-045821-293571.log](result/test3-sweep-20260906-a100-r4-rep2-20260907-045821-293571.log)
- Raw counters: `[282796.834750] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526046 gc_pages=4560380 gc_count=157591 WAF=1.825 scale_pct=100 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-057 — started 2026-09-07T05:08:25+09:00

- Workload=test2 scale=400 ratio=7 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a400-r7 test2 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-057.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-057.console.txt)

- Finished: 2026-09-07T05:18:29+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a400-r7-rep2-20260907-050825-294738.log](result/test2-sweep-20260906-a400-r7-rep2-20260907-050825-294738.log)
- Raw counters: `[283400.751641] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=2761231 gc_count=129478 WAF=1.499 scale_pct=400 age_ratio=7`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-058 — started 2026-09-07T05:18:29+09:00

- Workload=test3 scale=400 ratio=7 repetition=2, runtime=600
- Command: `script/run.sh sweep-20260906-a400-r7 test3 2`
- Environment: [snapshot](result/cat-sweep-20260906/run-058.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-058.console.txt)

- Finished: 2026-09-07T05:28:33+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a400-r7-rep2-20260907-051829-295885.log](result/test3-sweep-20260906-a400-r7-rep2-20260907-051829-295885.log)
- Raw counters: `[284004.664005] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=4529274 gc_count=157105 WAF=1.819 scale_pct=400 age_ratio=7`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-059 — started 2026-09-07T05:28:33+09:00

- Workload=test2 scale=200 ratio=7 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a200-r7 test2 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-059.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-059.console.txt)

- Finished: 2026-09-07T05:38:37+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a200-r7-rep3-20260907-052833-296928.log](result/test2-sweep-20260906-a200-r7-rep3-20260907-052833-296928.log)
- Raw counters: `[284608.603701] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526059 gc_pages=2861430 gc_count=131044 WAF=1.517 scale_pct=200 age_ratio=7`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-060 — started 2026-09-07T05:38:37+09:00

- Workload=test3 scale=200 ratio=7 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a200-r7 test3 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-060.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-060.console.txt)

- Finished: 2026-09-07T05:48:40+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a200-r7-rep3-20260907-053837-298110.log](result/test3-sweep-20260906-a200-r7-rep3-20260907-053837-298110.log)
- Raw counters: `[285212.527944] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526028 gc_pages=4461178 gc_count=156041 WAF=1.807 scale_pct=200 age_ratio=7`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-061 — started 2026-09-07T05:48:40+09:00

- Workload=test2 scale=25 ratio=16 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a25-r16 test2 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-061.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-061.console.txt)

- Finished: 2026-09-07T05:58:44+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a25-r16-rep3-20260907-054841-299222.log](result/test2-sweep-20260906-a25-r16-rep3-20260907-054841-299222.log)
- Raw counters: `[285816.465225] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526032 gc_pages=3045721 gc_count=133924 WAF=1.551 scale_pct=25 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-062 — started 2026-09-07T05:58:44+09:00

- Workload=test3 scale=25 ratio=16 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a25-r16 test3 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-062.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-062.console.txt)

- Finished: 2026-09-07T06:08:48+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a25-r16-rep3-20260907-055845-300237.log](result/test3-sweep-20260906-a25-r16-rep3-20260907-055845-300237.log)
- Raw counters: `[286420.405826] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526020 gc_pages=4759326 gc_count=160699 WAF=1.861 scale_pct=25 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-063 — started 2026-09-07T06:08:48+09:00

- Workload=test2 scale=200 ratio=4 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a200-r4 test2 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-063.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-063.console.txt)

- Finished: 2026-09-07T06:18:52+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a200-r4-rep3-20260907-060848-301419.log](result/test2-sweep-20260906-a200-r4-rep3-20260907-060848-301419.log)
- Raw counters: `[287024.345516] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=2954351 gc_count=132496 WAF=1.534 scale_pct=200 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-064 — started 2026-09-07T06:18:52+09:00

- Workload=test3 scale=200 ratio=4 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a200-r4 test3 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-064.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-064.console.txt)

- Finished: 2026-09-07T06:28:56+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a200-r4-rep3-20260907-061852-302581.log](result/test3-sweep-20260906-a200-r4-rep3-20260907-061852-302581.log)
- Raw counters: `[287628.273822] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526019 gc_pages=4476705 gc_count=156283 WAF=1.810 scale_pct=200 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-065 — started 2026-09-07T06:28:56+09:00

- Workload=test2 scale=25 ratio=7 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a25-r7 test2 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-065.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-065.console.txt)

- Finished: 2026-09-07T06:39:00+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a25-r7-rep3-20260907-062856-303711.log](result/test2-sweep-20260906-a25-r7-rep3-20260907-062856-303711.log)
- Raw counters: `[288232.198105] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526009 gc_pages=3009055 gc_count=133350 WAF=1.544 scale_pct=25 age_ratio=7`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-066 — started 2026-09-07T06:39:00+09:00

- Workload=test3 scale=25 ratio=7 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a25-r7 test3 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-066.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-066.console.txt)

- Finished: 2026-09-07T06:49:04+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a25-r7-rep3-20260907-063900-304902.log](result/test3-sweep-20260906-a25-r7-rep3-20260907-063900-304902.log)
- Raw counters: `[288836.144688] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5516870 gc_pages=4610156 gc_count=158226 WAF=1.835 scale_pct=25 age_ratio=7`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-067 — started 2026-09-07T06:49:04+09:00

- Workload=test2 scale=100 ratio=16 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a100-r16 test2 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-067.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-067.console.txt)

- Finished: 2026-09-07T06:59:08+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a100-r16-rep3-20260907-064904-306014.log](result/test2-sweep-20260906-a100-r16-rep3-20260907-064904-306014.log)
- Raw counters: `[289440.096487] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5523014 gc_pages=2684196 gc_count=128228 WAF=1.486 scale_pct=100 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-068 — started 2026-09-07T06:59:08+09:00

- Workload=test3 scale=100 ratio=16 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a100-r16 test3 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-068.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-068.console.txt)

- Finished: 2026-09-07T07:09:12+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a100-r16-rep3-20260907-065908-307010.log](result/test3-sweep-20260906-a100-r16-rep3-20260907-065908-307010.log)
- Raw counters: `[290044.006127] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=4486109 gc_count=156430 WAF=1.811 scale_pct=100 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-069 — started 2026-09-07T07:09:12+09:00

- Workload=test2 scale=25 ratio=4 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a25-r4 test2 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-069.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-069.console.txt)

- Finished: 2026-09-07T07:19:16+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a25-r4-rep3-20260907-070912-308186.log](result/test2-sweep-20260906-a25-r4-rep3-20260907-070912-308186.log)
- Raw counters: `[290647.893629] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=3050930 gc_count=134005 WAF=1.552 scale_pct=25 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-070 — started 2026-09-07T07:19:16+09:00

- Workload=test3 scale=25 ratio=4 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a25-r4 test3 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-070.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-070.console.txt)

- Finished: 2026-09-07T07:29:20+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a25-r4-rep3-20260907-071916-309315.log](result/test3-sweep-20260906-a25-r4-rep3-20260907-071916-309315.log)
- Raw counters: `[291251.837303] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526082 gc_pages=4775883 gc_count=160959 WAF=1.864 scale_pct=25 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-071 — started 2026-09-07T07:29:20+09:00

- Workload=test2 scale=100 ratio=7 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a100-r7 test2 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-071.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-071.console.txt)

- Finished: 2026-09-07T07:39:24+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a100-r7-rep3-20260907-072920-310357.log](result/test2-sweep-20260906-a100-r7-rep3-20260907-072920-310357.log)
- Raw counters: `[291855.744492] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=2884751 gc_count=131409 WAF=1.522 scale_pct=100 age_ratio=7`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-072 — started 2026-09-07T07:39:24+09:00

- Workload=test2 scale=400 ratio=16 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a400-r16 test2 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-072.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-072.console.txt)

- Finished: 2026-09-07T07:49:28+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a400-r16-rep3-20260907-073924-311530.log](result/test2-sweep-20260906-a400-r16-rep3-20260907-073924-311530.log)
- Raw counters: `[292459.692393] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=2619234 gc_count=127260 WAF=1.473 scale_pct=400 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-073 — started 2026-09-07T07:49:28+09:00

- Workload=test3 scale=400 ratio=16 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a400-r16 test3 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-073.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-073.console.txt)

- Finished: 2026-09-07T07:59:31+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a400-r16-rep3-20260907-074928-312674.log](result/test3-sweep-20260906-a400-r16-rep3-20260907-074928-312674.log)
- Raw counters: `[293063.596051] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5507145 gc_pages=4414557 gc_count=155017 WAF=1.801 scale_pct=400 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-074 — started 2026-09-07T07:59:31+09:00

- Workload=test2 scale=100 ratio=4 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a100-r4 test2 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-074.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-074.console.txt)

- Finished: 2026-09-07T08:09:35+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a100-r4-rep3-20260907-075932-313683.log](result/test2-sweep-20260906-a100-r4-rep3-20260907-075932-313683.log)
- Raw counters: `[293667.516747] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526017 gc_pages=2936082 gc_count=132210 WAF=1.531 scale_pct=100 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-075 — started 2026-09-07T08:09:35+09:00

- Workload=test3 scale=100 ratio=4 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a100-r4 test3 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-075.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-075.console.txt)

- Finished: 2026-09-07T08:19:39+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a100-r4-rep3-20260907-080936-314874.log](result/test3-sweep-20260906-a100-r4-rep3-20260907-080936-314874.log)
- Raw counters: `[294271.416881] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526030 gc_pages=4563403 gc_count=157638 WAF=1.825 scale_pct=100 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-076 — started 2026-09-07T08:19:39+09:00

- Workload=test2 scale=400 ratio=7 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a400-r7 test2 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-076.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-076.console.txt)

- Finished: 2026-09-07T08:29:43+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a400-r7-rep3-20260907-081939-316012.log](result/test2-sweep-20260906-a400-r7-rep3-20260907-081939-316012.log)
- Raw counters: `[294875.339675] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=2757619 gc_count=129422 WAF=1.499 scale_pct=400 age_ratio=7`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-077 — started 2026-09-07T08:29:43+09:00

- Workload=test3 scale=400 ratio=7 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a400-r7 test3 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-077.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-077.console.txt)

- Finished: 2026-09-07T08:39:47+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a400-r7-rep3-20260907-082943-317022.log](result/test3-sweep-20260906-a400-r7-rep3-20260907-082943-317022.log)
- Raw counters: `[295479.234756] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526071 gc_pages=4515487 gc_count=156890 WAF=1.817 scale_pct=400 age_ratio=7`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-078 — started 2026-09-07T08:39:47+09:00

- Workload=test2 scale=50 ratio=16 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a50-r16 test2 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-078.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-078.console.txt)

- Finished: 2026-09-07T08:49:51+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a50-r16-rep3-20260907-083947-318194.log](result/test2-sweep-20260906-a50-r16-rep3-20260907-083947-318194.log)
- Raw counters: `[296083.145266] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526078 gc_pages=2867985 gc_count=131147 WAF=1.518 scale_pct=50 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-079 — started 2026-09-07T08:49:51+09:00

- Workload=test3 scale=50 ratio=16 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a50-r16 test3 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-079.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-079.console.txt)

- Finished: 2026-09-07T08:59:55+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a50-r16-rep3-20260907-084951-319332.log](result/test3-sweep-20260906-a50-r16-rep3-20260907-084951-319332.log)
- Raw counters: `[296687.091136] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=4538333 gc_count=157246 WAF=1.821 scale_pct=50 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-080 — started 2026-09-07T08:59:55+09:00

- Workload=test2 scale=400 ratio=4 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a400-r4 test2 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-080.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-080.console.txt)

- Finished: 2026-09-07T09:09:59+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a400-r4-rep3-20260907-085955-320340.log](result/test2-sweep-20260906-a400-r4-rep3-20260907-085955-320340.log)
- Raw counters: `[297291.048089] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526028 gc_pages=2847668 gc_count=130830 WAF=1.515 scale_pct=400 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-081 — started 2026-09-07T09:09:59+09:00

- Workload=test3 scale=400 ratio=4 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a400-r4 test3 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-081.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-081.console.txt)

- Finished: 2026-09-07T09:20:03+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a400-r4-rep3-20260907-090959-321512.log](result/test3-sweep-20260906-a400-r4-rep3-20260907-090959-321512.log)
- Raw counters: `[297894.974266] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526027 gc_pages=4475303 gc_count=156261 WAF=1.809 scale_pct=400 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-082 — started 2026-09-07T09:20:03+09:00

- Workload=test2 scale=50 ratio=7 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a50-r7 test2 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-082.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-082.console.txt)

- Finished: 2026-09-07T09:30:07+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a50-r7-rep3-20260907-092003-322725.log](result/test2-sweep-20260906-a50-r7-rep3-20260907-092003-322725.log)
- Raw counters: `[298498.904792] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526082 gc_pages=2863101 gc_count=131071 WAF=1.518 scale_pct=50 age_ratio=7`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-083 — started 2026-09-07T09:30:07+09:00

- Workload=test3 scale=50 ratio=7 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a50-r7 test3 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-083.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-083.console.txt)

- Finished: 2026-09-07T09:40:11+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a50-r7-rep3-20260907-093007-323864.log](result/test3-sweep-20260906-a50-r7-rep3-20260907-093007-323864.log)
- Raw counters: `[299102.807251] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526085 gc_pages=4500314 gc_count=156653 WAF=1.814 scale_pct=50 age_ratio=7`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-084 — started 2026-09-07T09:40:11+09:00

- Workload=test2 scale=200 ratio=16 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a200-r16 test2 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-084.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-084.console.txt)

- Finished: 2026-09-07T09:50:15+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a200-r16-rep3-20260907-094011-324981.log](result/test2-sweep-20260906-a200-r16-rep3-20260907-094011-324981.log)
- Raw counters: `[299706.800904] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526056 gc_pages=2825589 gc_count=130485 WAF=1.511 scale_pct=200 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-085 — started 2026-09-07T09:50:15+09:00

- Workload=test3 scale=200 ratio=16 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a200-r16 test3 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-085.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-085.console.txt)

- Finished: 2026-09-07T10:00:19+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a200-r16-rep3-20260907-095015-326123.log](result/test3-sweep-20260906-a200-r16-rep3-20260907-095015-326123.log)
- Raw counters: `[300310.711342] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526016 gc_pages=4477481 gc_count=156295 WAF=1.810 scale_pct=200 age_ratio=16`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-086 — started 2026-09-07T10:00:19+09:00

- Workload=test2 scale=50 ratio=4 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a50-r4 test2 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-086.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-086.console.txt)

- Finished: 2026-09-07T10:10:22+09:00; run exit=0
- Kernel log: [test2-sweep-20260906-a50-r4-rep3-20260907-100019-327246.log](result/test2-sweep-20260906-a50-r4-rep3-20260907-100019-327246.log)
- Raw counters: `[300914.644654] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526047 gc_pages=2971564 gc_count=132765 WAF=1.537 scale_pct=50 age_ratio=4`
- Cleanup: module absent and target unmounted.

### cat-sweep-20260906 run-087 — started 2026-09-07T10:10:22+09:00

- Workload=test3 scale=50 ratio=4 repetition=3, runtime=600
- Command: `script/run.sh sweep-20260906-a50-r4 test3 3`
- Environment: [snapshot](result/cat-sweep-20260906/run-087.environment.txt)
- Console: [output](result/cat-sweep-20260906/run-087.console.txt)

- Finished: 2026-09-07T10:20:26+09:00; run exit=0
- Kernel log: [test3-sweep-20260906-a50-r4-rep3-20260907-101023-328324.log](result/test3-sweep-20260906-a50-r4-rep3-20260907-101023-328324.log)
- Raw counters: `[301518.571753] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=5526027 gc_pages=4652915 gc_count=159037 WAF=1.842 scale_pct=50 age_ratio=4`
- Cleanup: module absent and target unmounted.
- All 87 new runs completed; analysis pending.

- cat-sweep batch exit=0 at 2026-09-07T10:20:26+09:00; last stage=complete

### 2026-09-07 — CAT sweep 집계 완료

- 신규 87개 및 재사용 baseline 3개를 합쳐 90개 로그, 30조건 각각 n=3 확인. 카운터로 재계산한 WAF와 출력 값의 소수 셋째 자리 버림은 90개 모두 일치한다. 신규 fio 87회 모두 본 workload 6,000,000 writes 및 err=0 확인.
- test2 관측 평균 최소: scale=400/ratio=16, WAF=1.468910367. 기준 100/7=1.522260582 대비 3.5047% 감소.
- test3 관측 평균 최소: scale=200/ratio=7, WAF=1.802032871. 기준 100/7=1.813172289 대비 0.6144% 감소. 상위 후보의 반복 범위가 겹치므로 최적점 확정이나 통계적 우월성으로 표현하지 않는다.
- 관측 평균의 (최대-최소)/최소: test2=5.6274%, test3=3.9528%.
- 전체 설정 표와 검증 한계: [SUMMARY.md](result/cat-sweep-20260906/SUMMARY.md). 동일 seed 반복의 static CAT 비교이며 iCAT/Q-learning/phase 실험은 아니다.

### Measurement validation measurement-20260907-greedy-v2 — started 2026-09-07T16:11:46+09:00

- Explicit mode, CREATE Age; fresh ext4, 6 GiB preset, 3 GiB random preparation, measured 1 GiB, stopped 256 MiB, second epoch 128 MiB. Single fio job, 4 KiB direct, fixed seed 20260907, no rate limit.
- Evidence: `result/measurement-control-20260907/measurement-20260907-greedy-v2/`

- Finished 2026-09-07T16:11:58+09:00; validation exit=0; evidence `/home/oy/iCAT/result/measurement-control-20260907/measurement-20260907-greedy-v2`

### Measurement validation measurement-20260907-cat-v2 — started 2026-09-07T16:12:32+09:00

- Explicit mode, CREATE Age; fresh ext4, 6 GiB preset, 3 GiB random preparation, measured 1 GiB, stopped 256 MiB, second epoch 128 MiB. Single fio job, 4 KiB direct, fixed seed 20260907, no rate limit.
- Evidence: `result/measurement-control-20260907/measurement-20260907-cat-v2/`

- Finished 2026-09-07T16:12:42+09:00; validation exit=1; evidence `/home/oy/iCAT/result/measurement-control-20260907/measurement-20260907-cat-v2`

### Measurement validation cat-v2-boundary-trace — started 2026-09-07T16:13:33+09:00

- Explicit mode, CREATE Age; fresh ext4, 6 GiB preset, 3 GiB random preparation, measured 1 GiB, stopped 256 MiB, second epoch 128 MiB. Single fio job, 4 KiB direct, fixed seed 20260907, no rate limit.
- Evidence: `result/measurement-control-20260907/cat-v2-boundary-trace/`

- Finished 2026-09-07T16:13:45+09:00; validation exit=0; evidence `/home/oy/iCAT/result/measurement-control-20260907/cat-v2-boundary-trace`

### Measurement validation greedy-final — started 2026-09-07T16:14:20+09:00

- Explicit mode, CREATE Age; fresh ext4, 6 GiB preset, 3 GiB random preparation, measured 1 GiB, stopped 256 MiB, second epoch 128 MiB. Single fio job, 4 KiB direct, fixed seed 20260907, no rate limit.
- Evidence: `result/measurement-control-20260907/greedy-final/`

- Finished 2026-09-07T16:14:32+09:00; validation exit=0; evidence `/home/oy/iCAT/result/measurement-control-20260907/greedy-final`

### Measurement validation cat-final — started 2026-09-07T16:14:44+09:00

- Explicit mode, CREATE Age; fresh ext4, 6 GiB preset, 3 GiB random preparation, measured 1 GiB, stopped 256 MiB, second epoch 128 MiB. Single fio job, 4 KiB direct, fixed seed 20260907, no rate limit.
- Evidence: `result/measurement-control-20260907/cat-final/`

- Finished 2026-09-07T16:14:56+09:00; validation exit=0; evidence `/home/oy/iCAT/result/measurement-control-20260907/cat-final`

### measured-cat-20260907 run-01 — started 2026-09-07T16:50:03+09:00

- test2 scale=100 ratio=7, seed hot/warm/cold=20260911/20261011/20261111, measured payload=24576000000 bytes.
- Evidence: `result/measured-cat-20260907/run-01/`, console `run-01.console.txt`.

- Finished 2026-09-07T17:01:26+09:00; run exit=0
- host_bytes=24577601536 payload_bytes=24576000000 extra_host_bytes=1601536 host_pages=6000391 gc_pages=4002104 WAF=1.666973869

### measured-cat-20260907 run-02 — started 2026-09-07T17:01:26+09:00

- test3 scale=100 ratio=7, seed hot/warm/cold=20260911/20261011/20261111, measured payload=24576000000 bytes.
- Evidence: `result/measured-cat-20260907/run-02/`, console `run-02.console.txt`.

- Finished 2026-09-07T17:12:49+09:00; run exit=0
- host_bytes=24672092160 payload_bytes=24576000000 extra_host_bytes=96092160 host_pages=6023460 gc_pages=5358999 WAF=1.889687821

### measured-cat-20260907 run-03 — started 2026-09-07T17:12:49+09:00

- test2 scale=400 ratio=16, seed hot/warm/cold=20260911/20261011/20261111, measured payload=24576000000 bytes.
- Evidence: `result/measured-cat-20260907/run-03/`, console `run-03.console.txt`.

- Finished 2026-09-07T17:24:12+09:00; run exit=0
- host_bytes=24577589248 payload_bytes=24576000000 extra_host_bytes=1589248 host_pages=6000388 gc_pages=3683874 WAF=1.613939299

### measured-cat-20260907 run-04 — started 2026-09-07T17:24:12+09:00

- test3 scale=400 ratio=16, seed hot/warm/cold=20260911/20261011/20261111, measured payload=24576000000 bytes.
- Evidence: `result/measured-cat-20260907/run-04/`, console `run-04.console.txt`.

- Finished 2026-09-07T17:35:35+09:00; run exit=0
- host_bytes=24577712128 payload_bytes=24576000000 extra_host_bytes=1712128 host_pages=6000418 gc_pages=5498135 WAF=1.916291998

### measured-cat-20260907 run-05 — started 2026-09-07T17:35:35+09:00

- test2 scale=200 ratio=7, seed hot/warm/cold=20260911/20261011/20261111, measured payload=24576000000 bytes.
- Evidence: `result/measured-cat-20260907/run-05/`, console `run-05.console.txt`.

- Finished 2026-09-07T17:46:57+09:00; run exit=0
- host_bytes=24577589248 payload_bytes=24576000000 extra_host_bytes=1589248 host_pages=6000388 gc_pages=4046734 WAF=1.674412055

### measured-cat-20260907 run-06 — started 2026-09-07T17:46:57+09:00

- test3 scale=200 ratio=7, seed hot/warm/cold=20260911/20261011/20261111, measured payload=24576000000 bytes.
- Evidence: `result/measured-cat-20260907/run-06/`, console `run-06.console.txt`.

- Finished 2026-09-07T17:58:20+09:00; run exit=0
- host_bytes=24577699840 payload_bytes=24576000000 extra_host_bytes=1699840 host_pages=6000415 gc_pages=5325566 WAF=1.887532946

### measured-cat-20260907 run-07 — started 2026-09-07T17:58:20+09:00

- test2 scale=400 ratio=16, seed hot/warm/cold=20260912/20261012/20261112, measured payload=24576000000 bytes.
- Evidence: `result/measured-cat-20260907/run-07/`, console `run-07.console.txt`.

- Finished 2026-09-07T18:09:43+09:00; run exit=0
- host_bytes=24577589248 payload_bytes=24576000000 extra_host_bytes=1589248 host_pages=6000388 gc_pages=3679634 WAF=1.613232678

### measured-cat-20260907 run-08 — started 2026-09-07T18:09:43+09:00

- test3 scale=400 ratio=16, seed hot/warm/cold=20260912/20261012/20261112, measured payload=24576000000 bytes.
- Evidence: `result/measured-cat-20260907/run-08/`, console `run-08.console.txt`.

- Finished 2026-09-07T18:21:06+09:00; run exit=0
- host_bytes=24577712128 payload_bytes=24576000000 extra_host_bytes=1712128 host_pages=6000418 gc_pages=5504592 WAF=1.917368090

### measured-cat-20260907 run-09 — started 2026-09-07T18:21:06+09:00

- test2 scale=200 ratio=7, seed hot/warm/cold=20260912/20261012/20261112, measured payload=24576000000 bytes.
- Evidence: `result/measured-cat-20260907/run-09/`, console `run-09.console.txt`.

- Finished 2026-09-07T18:32:29+09:00; run exit=0
- host_bytes=24577589248 payload_bytes=24576000000 extra_host_bytes=1589248 host_pages=6000388 gc_pages=4028360 WAF=1.671349919

### measured-cat-20260907 run-10 — started 2026-09-07T18:32:29+09:00

- test3 scale=200 ratio=7, seed hot/warm/cold=20260912/20261012/20261112, measured payload=24576000000 bytes.
- Evidence: `result/measured-cat-20260907/run-10/`, console `run-10.console.txt`.

- Finished 2026-09-07T18:43:52+09:00; run exit=0
- host_bytes=24577712128 payload_bytes=24576000000 extra_host_bytes=1712128 host_pages=6000418 gc_pages=5318609 WAF=1.886373083

### measured-cat-20260907 run-11 — started 2026-09-07T18:43:52+09:00

- test2 scale=100 ratio=7, seed hot/warm/cold=20260912/20261012/20261112, measured payload=24576000000 bytes.
- Evidence: `result/measured-cat-20260907/run-11/`, console `run-11.console.txt`.

- Finished 2026-09-07T18:55:15+09:00; run exit=0
- host_bytes=24600645632 payload_bytes=24576000000 extra_host_bytes=24645632 host_pages=6006017 gc_pages=4012928 WAF=1.668151289

### measured-cat-20260907 run-12 — started 2026-09-07T18:55:15+09:00

- test3 scale=100 ratio=7, seed hot/warm/cold=20260912/20261012/20261112, measured payload=24576000000 bytes.
- Evidence: `result/measured-cat-20260907/run-12/`, console `run-12.console.txt`.

- Finished 2026-09-07T19:06:38+09:00; run exit=0
- host_bytes=24577724416 payload_bytes=24576000000 extra_host_bytes=1724416 host_pages=6000421 gc_pages=5360356 WAF=1.893329985

### measured-cat-20260907 run-13 — started 2026-09-07T19:06:38+09:00

- test2 scale=200 ratio=7, seed hot/warm/cold=20260913/20261013/20261113, measured payload=24576000000 bytes.
- Evidence: `result/measured-cat-20260907/run-13/`, console `run-13.console.txt`.

- Finished 2026-09-07T19:18:01+09:00; run exit=0
- host_bytes=24577601536 payload_bytes=24576000000 extra_host_bytes=1601536 host_pages=6000391 gc_pages=4029294 WAF=1.671505240

### measured-cat-20260907 run-14 — started 2026-09-07T19:18:01+09:00

- test3 scale=200 ratio=7, seed hot/warm/cold=20260913/20261013/20261113, measured payload=24576000000 bytes.
- Evidence: `result/measured-cat-20260907/run-14/`, console `run-14.console.txt`.

- Finished 2026-09-07T19:29:24+09:00; run exit=0
- host_bytes=24577712128 payload_bytes=24576000000 extra_host_bytes=1712128 host_pages=6000418 gc_pages=5313111 WAF=1.885456813

### measured-cat-20260907 run-15 — started 2026-09-07T19:29:24+09:00

- test2 scale=100 ratio=7, seed hot/warm/cold=20260913/20261013/20261113, measured payload=24576000000 bytes.
- Evidence: `result/measured-cat-20260907/run-15/`, console `run-15.console.txt`.

- Finished 2026-09-07T19:40:46+09:00; run exit=0
- host_bytes=24577589248 payload_bytes=24576000000 extra_host_bytes=1589248 host_pages=6000388 gc_pages=3998663 WAF=1.666400739

### measured-cat-20260907 run-16 — started 2026-09-07T19:40:46+09:00

- test3 scale=100 ratio=7, seed hot/warm/cold=20260913/20261013/20261113, measured payload=24576000000 bytes.
- Evidence: `result/measured-cat-20260907/run-16/`, console `run-16.console.txt`.

- Finished 2026-09-07T19:52:09+09:00; run exit=0
- host_bytes=24680505344 payload_bytes=24576000000 extra_host_bytes=104505344 host_pages=6025514 gc_pages=5335739 WAF=1.885524289

### measured-cat-20260907 run-17 — started 2026-09-07T19:52:09+09:00

- test2 scale=400 ratio=16, seed hot/warm/cold=20260913/20261013/20261113, measured payload=24576000000 bytes.
- Evidence: `result/measured-cat-20260907/run-17/`, console `run-17.console.txt`.

- Finished 2026-09-07T20:03:32+09:00; run exit=0
- host_bytes=24657256448 payload_bytes=24576000000 extra_host_bytes=81256448 host_pages=6019838 gc_pages=3673638 WAF=1.610255293

### measured-cat-20260907 run-18 — started 2026-09-07T20:03:32+09:00

- test3 scale=400 ratio=16, seed hot/warm/cold=20260913/20261013/20261113, measured payload=24576000000 bytes.
- Evidence: `result/measured-cat-20260907/run-18/`, console `run-18.console.txt`.

- Finished 2026-09-07T20:14:55+09:00; run exit=0
- host_bytes=24627998720 payload_bytes=24576000000 extra_host_bytes=51998720 host_pages=6012695 gc_pages=5507264 WAF=1.915939358
- measured-cat: all 18 runs complete; analysis pending.

- measured-cat batch exit=0 at 2026-09-07T20:14:55+09:00

### Measurement validation online-final — started 2026-09-07T20:14:55+09:00

- Explicit mode, Age=LAST_INVALIDATION; fresh ext4, 6 GiB preset, 3 GiB random preparation, measured 1 GiB, stopped 256 MiB, second epoch 128 MiB. Single fio job, 4 KiB direct, fixed seed 20260907, no rate limit.
- Evidence: `result/measurement-control-20260907/online-final/`

- Finished 2026-09-07T20:15:08+09:00; validation exit=0; evidence `/home/oy/iCAT/result/measurement-control-20260907/online-final`

### online-mix-20260907 smoke — started 2026-09-07T20:15:19+09:00

- Online discounted UCB; last-invalidation Age; A(front hot)→B(back hot), 30 seconds/phase; total target 40k 4KiB IOPS.
- Command: `bash script/online-mix-20260907.sh smoke`; evidence `result/online-mix-20260907/smoke/`.
- Fresh device, 6GiB sequential + 3GiB uniform preparation; measurement and cold learner start after preparation; no learner reset between phases.

- Finished 2026-09-07T20:17:42+09:00; smoke exit=0; evidence `/home/oy/iCAT/result/online-mix-20260907/smoke`; module/mount cleanup attempted.
- host_bytes=9830506496 host_pages=2400026 gc_pages=1977985 WAF=1.824151488
- before_sectors=19260082 after_sectors=38460290

### online-mix-20260907 main — started 2026-09-07T20:17:55+09:00

- Online discounted UCB; last-invalidation Age; A(front hot)→B(back hot), 3600 seconds/phase; total target 40k 4KiB IOPS.
- Command: `bash script/online-mix-20260907.sh main`; evidence `result/online-mix-20260907/main/`.
- Fresh device, 6GiB sequential + 3GiB uniform preparation; measurement and cold learner start after preparation; no learner reset between phases.

- Finished 2026-09-07T22:19:19+09:00; main exit=0; evidence `/home/oy/iCAT/result/online-mix-20260907/main`; module/mount cleanup attempted.
- host_bytes=1179665719296 host_pages=288004326 gc_pages=173359805 WAF=1.601934726
- before_sectors=19260082 after_sectors=2323294690

### Measurement validation varmail-fixed47 — started 2026-09-08T15:27:04+09:00

- Explicit mode, Age=LAST_INVALIDATION; fresh ext4, 6 GiB preset, 3 GiB random preparation, measured 1 GiB, stopped 256 MiB, second epoch 128 MiB. Single fio job, 4 KiB direct, fixed seed 20260907, no rate limit.
- Evidence: `result/measurement-control-20260907/varmail-fixed47/`

- Finished 2026-09-08T15:27:08+09:00; validation exit=137; evidence `/home/oy/iCAT/result/measurement-control-20260907/varmail-fixed47`

## 2026-09-11 — varmail-20260908 재개 사전 등록 (ssd.c 할당 수정 + 커널 7.0.0-31 재빌드)

- 사용자 요청: 8 GiB 예약 메모리(memmap=8G$4G) 가상 SSD로 중단된 varmail 비교(fixed37/fixed47/online)를 마저 실행. 사전 결과에서 민감도가 큰 workload로 varmail을 선택한 기존 사전 등록(2026-09-08)을 그대로 따른다. 2026-09-08 정정(GitHub varmail 1.305/3.920 범위는 동일 workload가 아님, arm47은 oracle 아님)은 유지한다.
- 변경 조건 1 — 커널: 재부팅 후 `7.0.0-31-generic`(이전 30). buildoutput의 모든 기존 .ko와 기록 hash(online `a34e2a86…`, fixed37 `3ade5dc4…`, fixed47 `818ee4b4…`)는 30용이므로 세 모듈을 모두 재빌드한다. 이번 결과는 2026-09-07 measured-cat/online-mix 결과와 커널이 달라 합산하지 않는다.
- 변경 조건 2 — `ssd.c`: 2026-09-08 실패 원인(order:6 kmalloc 실패 후 NULL 역참조, `ssd_init+0x138`)에 대해 `ssd_init` 경로의 배열 할당 6곳(`pg->sec`, `blk->pg`, `pl->blk`, `lun->pl`, `ch->lun`, `ssd->ch`)을 `kmalloc/kfree`→`kvmalloc/kvfree`로 바꿨다. `varmail-compare-src`와 `online-mix-src`에 동일 diff를 적용해 세 모듈이 같은 ssd.c를 쓴다. NULL 검사 추가는 하지 않았다(void 초기화 체인, 주석으로 표시). 정책/FTL/계측 코드는 변경하지 않는다. diff는 `result/varmail-20260911/ssd-kvmalloc.patch`.
- 실행 계획: (1) 세 모듈 빌드, hash·build log를 `result/varmail-20260911/`에 저장, `result/varmail-20260908/run-inputs.sha256`·`filebench-path.txt` 생성. (2) `verify-measurement-20260907.sh`로 fixed47·online 계측 검증. (3) smoke(60초)를 정책별 개별 실행하고 barrier-failed/lock 잔류 프로세스 확인 후 (4) main(3600초) 정책별 개별 실행. batch를 맹목 실행하지 않는다.
- 판정: 각 run은 runner 내부 검사(host_bytes = block sectors delta×512, gc_pages>0, filebench IO Summary 존재, 오류 문자열 없음)를 통과해야 한다. 단일 반복 pilot이며 통계적 우월성 결론을 내리지 않는다. 실패는 보존한다.
- 미확인: Filebench seed 통제 여부, fileset 생성 시간이 smoke timeout(660초) 안에 드는지 — 첫 smoke에서 기록한다.

### Measurement validation varmail-fixed47-k31 — started 2026-09-11T19:26:29+09:00

- Explicit mode, Age=LAST_INVALIDATION; fresh ext4, 6 GiB preset, 3 GiB random preparation, measured 1 GiB, stopped 256 MiB, second epoch 128 MiB. Single fio job, 4 KiB direct, fixed seed 20260907, no rate limit.
- Evidence: `result/measurement-control-20260907/varmail-fixed47-k31/`

- Finished 2026-09-11T19:26:42+09:00; validation exit=0; evidence `/home/oy/iCAT/result/measurement-control-20260907/varmail-fixed47-k31`

### Measurement validation online-k31 — started 2026-09-11T19:26:48+09:00

- Explicit mode, Age=LAST_INVALIDATION; fresh ext4, 6 GiB preset, 3 GiB random preparation, measured 1 GiB, stopped 256 MiB, second epoch 128 MiB. Single fio job, 4 KiB direct, fixed seed 20260907, no rate limit.
- Evidence: `result/measurement-control-20260907/online-k31/`

- Finished 2026-09-11T19:26:48+09:00; validation exit=137; evidence `/home/oy/iCAT/result/measurement-control-20260907/online-k31`

### 2026-09-11 — 재빌드 후 검증 결과 및 2차 할당 실패

- ssd.c 수정본(커널 7.0.0-31) fixed47 계측 검증 `varmail-fixed47-k31`: exit=0 PASS (module host_bytes=Linux bytes=1,073,758,208, host_pages=262148, gc_pages=14535, arm=47 k=10 scale_pct=25 age_ratio=16 로드 확인). 콘솔 `result/varmail-20260911/verify-fixed47-k31.console.txt`. 이 검증에 쓴 모듈 hash는 9b7c1b45…(ssd.c 수정만 포함)로, 아래 재빌드본과 다르다.
- online 모듈 검증 `online-k31`: exit=137. insmod 중 `page allocation failure: order:9` 후 `NVMEV_IO_WORKER_INIT+0x79` NULL 역참조. 원인은 io.c의 `work_queue = kzalloc(sizeof(nvmev_io_work)×16384)`(2 MiB 연속 페이지) 미검사 할당 — ssd.c와 별개의 두 번째 site. 모듈은 다시 initstate=coming, refcnt=1로 잔류하여 정상 rmmod 불가. controlled reboot 필요. 증거 `result/measurement-control-20260907/online-k31/`.
- 수정: 두 소스 io.c의 work_queue를 `kvzalloc/kvfree`로 변경(`result/varmail-20260911/io-kvzalloc.patch`). 세 모듈 재빌드(ssd.c+io.c 수정 포함), 새 hash는 build-info 및 `result/varmail-20260911/run-inputs.sha256`에 기록. 재부팅 후 fixed47/online 계측 검증부터 다시 수행한다.
- 관찰: 시스템은 16 GiB 중 8 GiB를 예약하고 남는 약 7 GiB에서 브라우저 등이 동작 중이라 고차 연속 페이지 확보가 불안정하다. 실험 중 큰 사용자 프로세스를 줄이는 것을 권고하되 sysctl/compaction 조작은 하지 않았다.

## 2026-09-11 — GitHub sweep 재분석: 최악 CAT vs iCAT 계획 사전 등록 (새 실행 없음)

- 사용자 요청: GitHub 사전 결과에서 편차가 가장 큰 설정을 찾고, CAT 최악 결과와 iCAT을 비교하는 실험 계획서 작성.
- 분석: `meendragon/iCAT` 7236149 shallow clone의 `result/{test3,test4,test5,filebench/varmail,filebench/oltp,sqlite/workloada,sqlite/workloadb}` dmesg 카운터에서 WAF 재계산. 스크립트 `analysis/gh-sweep-waf.py`, 출력 `result/gh-sweep-analysis-20260911/`.
- 결과: 통제된 편차 최대는 test4 27.7% (k10-s025-r16 1.7478 → k02-s200-r07 2.2313), sqlite-a 27.5% 동률. varmail 200.4%는 fileset 차이(24000/44000/150000 files)이며 24000-file 그룹 내 편차는 4.2% — 2026-09-08 정정을 정량 확인. 모든 workload의 최악 arm은 k=2로 Greedy와 0.4% 이내. 6 workload minimax 고정 arm은 k10-s050-r16(최대후회 3.7%).
- 계획: `WORST_CAT_VS_ICAT_PLAN.md`. test4 고정 payload, 5 정책(Greedy, arm10 worst, arm50 robust, arm47 oracle, iCAT) × 3 seed = 15 run, LAST_INVALIDATION Age, 커널 7.0.0-31 재측정. 장치 실행은 사용자 확인 후 시작하며 varmail 비교보다 우선할지는 사용자 결정.

### mix-20260911 smoke fixed47 — started 2026-09-11T22:54:54+09:00

- Phase A fio test4 fixed payload (5898240000/2949120000/983040000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (20000 records, 20000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh smoke fixed47`; evidence `result/mix-20260911/smoke-fixed47/`.

- Finished 2026-09-11T22:57:30+09:00; smoke fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/smoke-fixed47`; cleanup attempted.
- total host_bytes=9934962688 host_pages=2425528 gc_pages=2048810 WAF=1.844686
- phaseA(test4) host_pages=2400067 gc_pages=2040223 WAF=1.850069
- phaseB(sqlite-a) host_pages=25346 gc_pages=8525 WAF=1.336345
- phaseB-load host_pages=16263 gc_pages=5021 WAF=1.308738
- phaseB-run host_pages=9083 gc_pages=3504 WAF=1.385776
- ycsb-load [OVERALL], Throughput(ops/sec), 16736.401673640168
- ycsb-run [OVERALL], Throughput(ops/sec), 25284.450063211127

### mix-20260911 smoke online — started 2026-09-11T22:57:55+09:00

- Phase A fio test4 fixed payload (5898240000/2949120000/983040000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (20000 records, 20000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh smoke online`; evidence `result/mix-20260911/smoke-online/`.

- Finished 2026-09-11T23:00:37+09:00; smoke online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/smoke-online`; cleanup attempted.
- total host_bytes=9935151104 host_pages=2425574 gc_pages=2509572 WAF=2.034630
- phaseA(test4) host_pages=2400073 gc_pages=2494054 WAF=2.039158
- phaseB(sqlite-a) host_pages=25386 gc_pages=15440 WAF=1.608209
- phaseB-load host_pages=16263 gc_pages=9566 WAF=1.588206
- phaseB-run host_pages=9123 gc_pages=5874 WAF=1.643867
- ycsb-load [OVERALL], Throughput(ops/sec), 15860.428231562251
- ycsb-run [OVERALL], Throughput(ops/sec), 23612.75088547816

### mix-20260911 main fixed47 — started 2026-09-11T23:00:46+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (4000000 records, 1000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh main fixed47`; evidence `result/mix-20260911/main-fixed47/`.

- Finished 2026-09-11T23:17:57+09:00; main fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/main-fixed47`; cleanup attempted.
- total host_bytes=150612217856 host_pages=36770561 gc_pages=33127129 WAF=1.900914
- phaseA(test4) host_pages=24017549 gc_pages=18537691 WAF=1.771839
- phaseB(sqlite-a) host_pages=12752897 gc_pages=14589393 WAF=2.144006
- phaseB-load host_pages=11917536 gc_pages=12453686 WAF=2.044988
- phaseB-run host_pages=835361 gc_pages=2135707 WAF=3.556628
- ycsb-load [OVERALL], Throughput(ops/sec), 19477.89502388477
- ycsb-run [OVERALL], Throughput(ops/sec), 7982.31119838438

### mix-20260911 main online — started 2026-09-11T23:17:58+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (4000000 records, 1000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh main online`; evidence `result/mix-20260911/main-online/`.

- Finished 2026-09-11T23:35:11+09:00; main online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/main-online`; cleanup attempted.
- total host_bytes=150727503872 host_pages=36798707 gc_pages=52646990 WAF=2.430675
- phaseA(test4) host_pages=24026270 gc_pages=23270312 WAF=1.968536
- phaseB(sqlite-a) host_pages=12772322 gc_pages=29376551 WAF=3.300016
- phaseB-load host_pages=11917754 gc_pages=27247321 WAF=3.286280
- phaseB-run host_pages=854568 gc_pages=2129230 WAF=3.491586
- ycsb-load [OVERALL], Throughput(ops/sec), 17950.662603833363
- ycsb-run [OVERALL], Throughput(ops/sec), 8761.861369829407

### 2026-09-11 — mix-20260911 main 결과 해석 (fixed47 vs online, 1 seed)

- 두 run 모두 exit=0, host_bytes = block sectors delta×512 통과. 총 host 약 150.6 GB (phase A 24.0M pages, phase B 12.8M pages).
- WAF: phase A(test4) fixed47 1.7718 / online 1.9685; phase B(sqlite-a) fixed47 2.1440 / online 3.3000; 전체 1.9009 / 2.4307. **online이 두 phase 모두 크게 나쁨.**
- 원인(kernel.log WATGC_V2 sample, part0): learner가 arm 0→59를 window당 1개씩 순서대로 한 번씩 시도(window ≈ 10초, 60 arms ≈ 600초). phase A 600초는 정확히 1회 sweep으로 끝났고, phase B에서 두 번째 sweep 시작. 92 window 동안 settled=0, exploitation 없음. 즉 측정 구간 전체가 탐색이었고, k=2 arm들(WAF 2.0~3.9)을 포함한 60개 평균이 결과가 됐다. 2026-09-07 pilot의 "60arms×3visits는 3600초/phase 필요" 관찰과 일치.
- 부수 관찰: phase B sweep에서 k=2 arm의 window WAF 3.4~3.9는 GitHub varmail k=2 로그의 3.85~3.92와 같은 수준이다.
- 결론: 이 결과는 "iCAT이 나쁘다"가 아니라 "600초 phase는 현재 learner의 탐색 기간보다 짧다"를 보인다. 다음 조치는 사용자 결정: (a) phase 길이를 탐색 기간의 수 배로 늘림(fio time/payload, YCSB operationcount 확대), (b) learner 파라미터(window 크기, arm 수) 조정 — (b)는 알고리즘 변경이므로 별도 버전/일지로 구분.

## 2026-09-12 — mix-20260911 long 사전 등록

- 목적: 2026-09-11 main에서 iCAT이 진 원인(측정 구간 전체가 60-arm 탐색, settled=0)이 phase 길이 부족인지 확인. phase A payload 6배(약 3600초), phase B YCSB operationcount 100만→1000만. 나머지 조건(준비, seed, Age=LAST_INVALIDATION, drop_caches 4s, 모듈 hash)은 main과 동일.
- 실행: `bash script/mix-20260911.sh long fixed47`, `... long online`. 결과 `result/mix-20260911/long-{fixed47,online}/`. 정책당 약 2시간, 직렬.
- 판정: 각 run은 기존 내부 검사(fio err=0, YCSB Return=OK, host_bytes=sectors×512, gc_pages>0) 통과. 해석은 phase별 WAF와 함께 learner의 settled/best 추이를 본다. iCAT이 여전히 지면 phase 길이 가설이 기각되며 learner 파라미터 문제로 넘어간다(별도 버전).
- 단일 seed pilot이며 통계적 우월성을 주장하지 않는다. main 결과는 보존한다.

### mix-20260911 long fixed47 — started 2026-09-12T12:15:25+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (4000000 records, 10000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh long fixed47`; evidence `result/mix-20260911/long-fixed47/`.

- Finished 2026-09-12T13:49:42+09:00; long fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/long-fixed47`; cleanup attempted.
- total host_bytes=704182980608 host_pages=171919673 gc_pages=149022695 WAF=1.866816
- phaseA(test4) host_pages=144003975 gc_pages=111326391 WAF=1.773079
- phaseB(sqlite-a) host_pages=27915583 gc_pages=37696228 WAF=2.350365
- phaseB-load host_pages=11922228 gc_pages=11263752 WAF=1.944769
- phaseB-run host_pages=15993355 gc_pages=26432476 WAF=2.652716
- ycsb-load [OVERALL], Throughput(ops/sec), 17104.250406225947
- ycsb-run [OVERALL], Throughput(ops/sec), 5790.327605155245

### mix-20260911 long online — started 2026-09-12T13:49:42+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (4000000 records, 10000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh long online`; evidence `result/mix-20260911/long-online/`.

- Finished 2026-09-12T15:15:56+09:00; long online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/long-online`; cleanup attempted.
- total host_bytes=703275540480 host_pages=171698130 gc_pages=203651727 WAF=2.186103
- phaseA(test4) host_pages=144003966 gc_pages=137027965 WAF=1.951557
- phaseB(sqlite-a) host_pages=27694049 gc_pages=66623645 WAF=3.405703
- phaseB-load host_pages=11918413 gc_pages=25776196 WAF=3.162720
- phaseB-run host_pages=15775636 gc_pages=40847449 WAF=3.589274
- ycsb-load [OVERALL], Throughput(ops/sec), 19036.831509763513
- ycsb-run [OVERALL], Throughput(ops/sec), 7906.600904831407

### 2026-09-12 — mix-20260911 long 결과 (phase 길이 가설 기각)

- 두 run 모두 exit=0. host_pages phase A 144,003,9xx로 두 정책 일치(0.00001% 차), phase B load 11.92M 일치.
- WAF: phase A fixed47 1.7731 / online 1.9516; phase B 전체 2.3504 / 3.4057; phase B-run 구간 2.6527 / 3.5893; 전체 1.8668 / 2.1861. **6배 길게 해도 iCAT이 모든 구간에서 졌다.**
- 참고: main(600초)에서는 phase B-run 구간만 iCAT이 근소하게 나았으나(3.5566 vs 3.4916) long에서는 역전됐다. 1 seed 비교이므로 두 관측 모두 확정적이지 않다.
- learner 추이(part0, 439 window): phase A 370 window 중 settled=1이 2회뿐이고 best arm이 37→0→18→49→33→36→48→46으로 계속 이동, phase B 69 window에서도 settled=0이며 best가 33→48→46→19→18로 재이동. 탐색이 끝나지 않는 것이 phase 길이 때문이 아니라 arm 간 reward 차이 대비 window 잡음이 커서 UCB가 수렴하지 않기 때문으로 보인다. 가설 "phase 600초가 짧아서 졌다"는 기각한다.
- 설계 결함 2건 기록: (1) phase B의 93%(main) / 43%(long)가 YCSB load(순차 삽입)이며 목표였던 update workload가 아니다. (2) phase A 파일을 rm만 하고 TRIM을 하지 않아 FTL 관점에서 6 GiB가 계속 유효 상태로 남아 phase B 내내 GC가 이를 재배치한다. phase B WAF 2.4~3.6은 workload 특성보다 이 잔존 데이터의 영향이 크다.
- 다음: 사용자와 A안(phase A 파일을 유지한 채 남은 공간에 DB 생성) 설계 합의 후 재실행. learner 수렴 문제는 별도 항목으로 분리한다.

## 2026-09-14 — t4 단일 workload 반복 비교 사전 등록 (fixed47 vs online, seed 3개)

- 사용자 요청: mix 없이 test4 단일 workload로 iCAT과 CAT 고정(arm47)을 여러 번 돌려 평균 비교. `mix-20260911.sh t4 <policy> <rep>` 모드 추가(phase B 생략, rep=1..3이 seed hot/warm/cold = 2026091x/2026101x/2026111x 선택). 준비·payload(24M writes)·Age·모듈은 main과 동일.
- 순서: fixed47 rep1, online rep1, fixed47 rep2, online rep2, fixed47 rep3, online rep3. 6 run ≈ 70분. 결과 `result/mix-20260911/t4-{policy}-rep{N}/`.
- 판정: seed별 WAF와 3-seed 평균을 보고. host_pages가 정책 간 0.5% 이내여야 비교 유효. 통계적 유의성은 주장하지 않는다.

### mix-20260911 t4 fixed47 — started 2026-09-14T10:44:38+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh t4 fixed47`; evidence `result/mix-20260911/t4-fixed47/`.

- Finished 2026-09-14T10:56:02+09:00; t4 fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-fixed47-rep1`; cleanup attempted.
- total host_bytes=98306695168 host_pages=24000658 gc_pages=18575198 WAF=1.773945
- phaseA(test4) host_pages=24000658 gc_pages=18575198 WAF=1.773945
- phaseB(sqlite-a) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 online — started 2026-09-14T10:56:02+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh t4 online`; evidence `result/mix-20260911/t4-online/`.

- Finished 2026-09-14T11:07:25+09:00; t4 online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-online-rep1`; cleanup attempted.
- total host_bytes=98306707456 host_pages=24000661 gc_pages=24017319 WAF=2.000694
- phaseA(test4) host_pages=24000661 gc_pages=24017319 WAF=2.000694
- phaseB(sqlite-a) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 fixed47 — started 2026-09-14T11:07:25+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh t4 fixed47`; evidence `result/mix-20260911/t4-fixed47/`.

- Finished 2026-09-14T11:18:48+09:00; t4 fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-fixed47-rep2`; cleanup attempted.
- total host_bytes=98336026624 host_pages=24007819 gc_pages=18574730 WAF=1.773695
- phaseA(test4) host_pages=24007819 gc_pages=18574730 WAF=1.773695
- phaseB(sqlite-a) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 online — started 2026-09-14T11:18:48+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh t4 online`; evidence `result/mix-20260911/t4-online/`.

- Finished 2026-09-14T11:30:11+09:00; t4 online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-online-rep2`; cleanup attempted.
- total host_bytes=98313019392 host_pages=24002202 gc_pages=24031059 WAF=2.001202
- phaseA(test4) host_pages=24002202 gc_pages=24031059 WAF=2.001202
- phaseB(sqlite-a) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 fixed47 — started 2026-09-14T11:30:11+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh t4 fixed47`; evidence `result/mix-20260911/t4-fixed47/`.

- Finished 2026-09-14T11:41:34+09:00; t4 fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-fixed47-rep3`; cleanup attempted.
- total host_bytes=98306719744 host_pages=24000664 gc_pages=18567441 WAF=1.773622
- phaseA(test4) host_pages=24000664 gc_pages=18567441 WAF=1.773622
- phaseB(sqlite-a) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 online — started 2026-09-14T11:41:34+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh t4 online`; evidence `result/mix-20260911/t4-online/`.

- Finished 2026-09-14T11:52:57+09:00; t4 online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-online-rep3`; cleanup attempted.
- total host_bytes=98306695168 host_pages=24000658 gc_pages=24032113 WAF=2.001311
- phaseA(test4) host_pages=24000658 gc_pages=24032113 WAF=2.001311
- phaseB(sqlite-a) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

- t4 결과(2026-09-14 12:21 완료, 6 run 모두 exit=0): fixed47 WAF 1.773945 / 1.773695 / 1.773622 (평균 1.7737), online 2.000694 / 2.001202 / 2.001311 (평균 2.0011). host_pages 24,000,658~24,007,819로 일치. seed 간 편차가 두 정책 모두 0.001 이하로, iCAT의 열세(+12.8%)는 재현 가능하고 seed 잡음이 아니다. 사용자 요청으로 다음은 GitHub 원본 스크립트(fio.sh)와 GitHub 방식 빌드 arm47 모듈로 test4를 돌려 GitHub 1.7478 재현 여부를 확인한다.

## 2026-09-14 — gh-repro-20260914 사전 등록: GitHub 원본 스크립트·소스로 test4 재현

- 사용자 요청: GitHub 스크립트로 직접 돌려 확인. 조사 결과: (1) GitHub HEAD 7236149의 `nvmevirt_test`는 기본 정책이 online(WATGC_V2)이고, 고정 CAT은 arm37(K=7,scale=100,ratio=7) 하나만 지원하며 Kbuild의 CAT_FIG7_* 플래그는 conv_ftl.h가 #error로 거부한다(저장소 자체 불일치). (2) 60-arm sweep 모듈의 소스는 어느 커밋에도 없고(8542e25는 K 플래그 없음), 동봉된 .ko는 커널 6.8.0-138용이라 7.0.0-31에서 로드 불가. 따라서 arm47 고정을 GitHub 소스 그대로 재현하는 것은 불가능하며, 우리 fixed47 모듈(HEAD + FIXED_ARM 선택)이 가장 가까운 구현이다.
- 실행 가능한 재현: HEAD 소스(`gh-src-7236149/`, ssd.c kvmalloc·io.c kvzalloc 할당 패치만 적용, 정책 코드 무변경) → `nvmev-gh-online.ko`(기본), `nvmev-gh-cat37.ko`(CAT_FIG7, Kbuild의 CAT_FIG7_* 3줄만 제거해 빌드). hash `result/gh-repro-20260914/modules.sha256`.
- 스크립트: GitHub `script/fio.sh`를 경로만 바꿔 `script/gh-fio.sh`(diff: 경로, nvme0n1, nvme-cli 부재 시 sync, sudo -v 제거). workload `gh-test4.fio`/`gh-preset.fio`는 GitHub 원본에서 경로만 변경. 계측은 GitHub 방식(모듈 자동 카운터, rmmod 시 GC stats 출력), 600초 time_based, Age는 HEAD 기본.
- 비교 기준: GitHub test4 sweep의 arm37(k07-s100-r07) = 1.8687. gh-cat37이 이 값 근처면 이 머신 계측과 GitHub 계측이 일치한다고 본다. gh-online은 GitHub iCAT 그대로의 test4 성적이며 GitHub에 해당 기록은 없다.
- 명령: `bash script/gh-fio.sh gh-cat37`, `bash script/gh-fio.sh gh-online`. 각 1회, 약 12분. 결과 `result/gh-repro-20260914/dmesg-*.log`.

- gh-repro 진행 기록(2026-09-14): gh-cat37 exit=0, `policy=cat-fig7-fixed host_pages=23500672 gc_pages=22054275 WAF=1.938` (GitHub sweep arm37 test4 1.8687 대비 +3.7%; Age 기본값 차이 등 미확인). **정정:** 처음 빌드한 `nvmev-gh-online.ko`(hash 091f1132…)는 Kbuild 기본 `NVMEVIRT_GC_POLICY ?= GREEDY` 때문에 실제로는 Greedy였다(dmesg `policy=greedy WAF=2.203`; GitHub greedy test4 2.2229 대비 -0.9%). GitHub Kbuild에는 WATGC_V2 분기가 없어 HEAD의 online 학습기는 GitHub 빌드 절차로는 빌드할 수 없다. 해당 run은 `dmesg-gh-online-WAS-GREEDY-*.log`로 이름을 바꿔 보존(Greedy 재현 자료로 유효). Kbuild에 `WATGC_V2 → -DCONV_GC_POLICY=2` 2줄을 추가해 다시 빌드(hash faf199fd…), gh-online을 재실행한다.
- gh-online(진짜 WATGC_V2, hash faf199fd…) exit=0: `policy=watgc-v2 host_pages=23500672 gc_pages=22410744 WAF=1.953`. host_pages가 gh-cat37과 동일(23,500,672). 600초 동안 part0 sample 59개, best 37→0→1 — 첫 sweep도 못 끝냈다(GitHub 자동 계측은 warmup 100 GC 이후 시작). GitHub 방식 test4 요약: Greedy 2.203 / CAT arm37 고정 1.938 / iCAT 1.953. iCAT은 GitHub 자체 고정 기준(arm37)보다 0.8% 높고, 우리 계측(t4: fixed47 1.774 vs iCAT 2.001)과 방향이 같다. GitHub 스크립트로도 iCAT이 고정 CAT을 이기지 못함을 확인.

- 2026-09-14 GitHub 스크립트 이식(장치 실행 없음): `script/gh-{fio,rocksdb,filebench,llama,run_all,build}.sh` — 경로(/home/meen→/home/oy, mnt, nvme0n1), sudoers 허용 명령으로의 치환(drop_caches→tee, chown 제거, sudo -v 제거, nvme-cli 부재 시 sync), YCSB python2 런처→ycsb.sh, filebench 기본 경로→tools/filebench-local. 워크로드 `workloads/{filebench,rocksdb}/` 원본 복사. YCSB rocksdb 바인딩 로컬 smoke 통과(1000 insert OK). llama는 llama.cpp 빌드와 3B gguf 모델이 없어 실행 불가. gh-build.sh는 GitHub Kbuild 불일치 때문에 고정 CAT 빌드가 실패하는 원본 상태 그대로다.
- 2026-09-14 장치 smoke: `gh-rocksdb.sh gh-cat37 smoke`(20k/20k) exit=0, INSERT/READ/UPDATE OK (WAF N/A는 warmup 100 GC 미도달, 정상). `gh-filebench.sh gh-cat37 oltp`(60초) 첫 실행은 filebench 자체 abort("buffer overflow detected", `fileset.c fileset_resolvepath`의 strlcpy 크기 버그, _FORTIFY_SOURCE). 이는 varmail 등 하위 디렉터리를 만드는 모든 workload에서 재현되며, 이 머신의 filebench는 오늘 전까지 한 번도 workload를 완주한 적이 없다(varmail-20260908 계열은 insmod 단계에서 멈춰 filebench에 도달하지 않았음). `tools/filebench-local/filebench-1.5-alpha3/fileset.c` 1줄 수정 후 재빌드(PROVENANCE.md에 기록), oltp 60초 재실행 exit=0, IO Summary 38192 ops/s, WAF 1.265(60초 smoke 값, 비교용 아님).

## 2026-09-14 — gh-repro 앱 workload 비교 사전 등록 (GitHub 스크립트, cat37 vs online)

- 사용자 요청: 이식한 러너로 실제 실행. 모듈 `gh-cat37`(GitHub HEAD 고정 CAT k7/s100/r7)과 `gh-online`(GitHub HEAD WATGC_V2)로 filebench oltp, filebench varmail, rocksdb workloada를 각 1회. 스크립트·계측·워크로드 정의는 GitHub 원본(경로만 변경). filebench runtime은 GitHub 원본 workload의 `run` 값 사용(FILEBENCH_RUNTIME 미지정 시 스크립트 기본 60초이므로 300으로 지정).
- 비교 기준: GitHub sweep에서 oltp arm37 = 1.6159, varmail arm37 = 1.3492(24000 files 조건; HEAD varmail.f는 nfiles=150000이라 직접 비교 불가, 원본 그대로 실행) — `result/gh-sweep-analysis-20260911/per-arm-waf.txt` 참조. GitHub에 online 결과는 없다.
- 순서: oltp cat37 → oltp online → varmail cat37 → varmail online → rocksdb-a cat37 → rocksdb-a online. 결과 `result/filebench/{oltp,varmail}/`, `result/rocksdb/workloada/`. 1 seed, 통계적 결론 없음.
- gh-repro 앱 workload 결과(2026-09-14 15:07, 6 run 모두 exit=0, GitHub 계측): oltp cat37 1.525(host 6,859,110) / online 1.491(host 7,429,715) — online이 2.2% 낮으나 time_based라 host_pages가 8% 다름, 편차 작은 workload(sweep 7.7%). varmail(HEAD 설정 150000 files) cat37 4.623 / online 4.935 — cat37이 6.7% 낮음, GitHub sweep(24000 files, 1.35)과 비교 불가. rocksdb-a cat37 WAF 1.000(gc_pages=0, gc_count=125,716) / online 1.000(gc_pages=0, gc_count=127,038) — 순차 대용량 쓰기·파일 단위 삭제로 victim이 전부 무효 페이지뿐이라 정책 무관, 비교 workload로 부적합(GitHub에 rocksdb 결과가 없는 이유로 추정).

## 2026-09-14 — gh-repro 잔여 workload 사전 등록 (test3, test5, test2, sqlite a/b; cat37 vs online)

- 사용자 요청: 남은 GitHub workload 전부 실행. `gh-fio.sh`는 TEST_JOB이 파일에 고정돼 있어 환경변수 `GH_TEST_JOB`으로 선택하도록 1줄 수정(기본 gh-test4.fio). sqlite는 이식된 `script/sqlite.sh`(GitHub sqlite.sh 경로·권한만 변경) 사용.
- 순서: test3 → test5 → test2 → sqlite a → sqlite b, 각 cat37, online. 10 run, 약 2.5시간. GitHub 기준값(arm37): test3 1.7323, test5 1.5459, sqlite-a 1.3419, sqlite-b 1.1354.

## 2026-09-14 — gh-queue-20260914 사전 등록 (무인 연속 실행)

- 사용자 요청: 돌릴 수 있는 실험 계속 실행, 사용자 부재. `script/gh-queue-20260914.sh`가 현재 batch(ALLDONE) 종료를 기다린 뒤 순서대로: (1) fio test4/test3/test5 × cat37/online × rep2,3 (GitHub fio는 randseed 고정이므로 동일 seed 반복 = run-to-run 변동 측정), (2) filebench oltp/varmail × cat37/online × rep2,3, (3) filebench webserver/webproxy × cat37/online 1회. 각 블록 후 git commit/push(oyeong011/iCAT-experiments). 총 ~24 run, 약 6시간. 실패는 콘솔에 FAIL로 남기고 다음으로 진행.
- 참고: gh-fio.sh/gh-filebench.sh는 dmesg 결과 파일명에 run ID를 넣어(fio) 또는 고정 이름(filebench: `dmesg-<tag>.log`, 덮어씀)을 쓴다. filebench 반복은 원본 스크립트가 같은 파일명에 덮어쓰므로, 각 rep의 콘솔(`*-repN.console.txt`)에 WAF 라인이 보존된다 — dmesg-*.log는 마지막 rep만 남는다.

## 2026-09-14 — gh-queue2-20260914 사전 등록 (무인 연속 실행 2차)

- 사용자 요청: 가능한 실험 전부 실행. 모듈 추가 빌드: `nvmev-gh-greedy.ko`(GitHub HEAD GREEDY), `nvmev-fixed10.ko`(arm10 = test4 최악, k2/s200/r7), `nvmev-fixed50.ko`(arm50 = 6-workload minimax, k10/s50/r16), `nvmev-fixed47.ko`(기존 fixed47 복사). fixed*는 varmail-compare-src(HEAD+할당 패치+FIXED_ARM), measurement_manual 기본 0이라 GitHub 자동 계측으로 동작. hash `result/gh-repro-20260914/modules.sha256`.
- 순서(queue1 QUEUEDONE 이후): fio test4/test3/test5/test2 × {greedy,fixed10,fixed47,fixed50} → sqlite a/b × 4 → filebench oltp/varmail × 4 → sqlite d × 6 정책 → filebench videoserver × cat37/online → sqlite a/b × cat37/online rep2,3. 약 40 run, 12시간 이상. 블록마다 push.
- 이로써 WORST_CAT_VS_ICAT_PLAN의 5-정책 비교가 GitHub 계측 방식으로 test4에서 완성된다(cat37/online은 queue1에서 3회, 나머지 1회).

## 2026-09-14 — gh-queue3-20260914 사전 등록 (무인 연속 실행 3차)

- 사용자 요청: 추가 실험 예약. (1) fio test4/3/5의 randseed를 +1/+2한 변형(`gh-*-s2.fio`, `-s3.fio`) × 6정책(greedy, fixed10, cat37, fixed47, fixed50, online) = 36 run — GitHub fio는 seed 고정이라 seed 변동을 이것으로 확보. (2) filebench webserver/webproxy/videoserver × 4 고정 정책. (3) **mix A안**: `mix-20260911.sh mixA` — phase A test4(24M writes) 후 파일을 지우지 않고 남은 공간에 sqlite DB(60만 건, 400만 op) 생성. 좀비 유효 데이터 없이 "두 앱이 SSD를 나눠 쓰다 주도권이 바뀜"을 재현. fixed10/fixed47/fixed50/online × rep 1~3(seed 변경) = 12 run. 총 ~60 run, 15시간 이상. queue2 종료 후 자동 시작, 블록마다 push.
- mixA 판정: 각 run 내부 검사 통과, phase B가 ENOSPC 없이 완료. phase A/B WAF를 정책별로 비교하고 iCAT의 arm 추이를 본다.
- 2026-09-14 23:10 queue1 완료(QUEUEDONE 20:43). FAIL 2건: filebench webproxy × cat37/online — GitHub 원본 `webproxy.f`(및 `videoserver.f`)에 `run` 지시가 없어 스크립트가 거부. 두 프로필 끝에 `run 300` 추가(스크립트가 FILEBENCH_RUNTIME으로 덮어씀). webproxy cat37/online은 queue3에서 4 고정 정책만 돌므로 cat37/online 2 run은 별도 재실행 필요. queue2 진행 중(fio test4/3/5 × 4정책 완료, test2 진행 중).

## 2026-09-14 — gh-queue4-20260914 사전 등록 (무인 연속 실행 4차: mix 전 설계 × 전 정책)

- 사용자 요청: mix workload에서 iCAT/CAT/Greedy 가능한 조합 전부. `mix-20260911.sh`를 phase 함수로 재구성해 3설계 추가/정리:
  - **mixA** test4 → sqlite-a(60만 건/400만 op), fio 파일 유지(좀비 없음)
  - **mixB** sqlite-a → test4 (앱 먼저, 그 다음 fio; 파일은 preset 것 유지)
  - **mixC** test3(1/4 IOPS·1/4 payload, 600초) → test4(600초): 같은 배치에서 overwrite 시간축만 4배 변화
  - main(원 설계, 파일 삭제 후 sqlite)은 아직 안 돌린 정책만 추가
- 정책 6개(start/stop 계측 모듈): greedy(`nvmev-greedy-m.ko`, varmail-compare-src GREEDY), fixed10, fixed37(기존 varmail fixed37 복사), fixed47, fixed50, online. gh-* 모듈은 manual 계측이 없어 mix에 못 쓴다.
- 순서(queue3 종료 후): mixB/mixC SMOKE(1/10) → rep1~3 × {mixB, mixC} × 6정책 + mixA × {greedy, fixed37} → main × {greedy, fixed10, fixed37, fixed50}. 약 46 run, 12시간 이상. 블록마다 push. mixB/mixC는 장치가 점유 중이라 사전 smoke를 못 했고 queue4 첫 단계에서 smoke한다(실패해도 본 run 시도, FAIL 기록).
- 2026-09-15 10:55 queue2 완료(07:13). FAIL 2건: filebench videoserver × cat37/online — 원본 프로필이 파일 226개 × 10 GiB(2.3 TB)라 7.6 GiB 장치에서 ENOSPC. `$filesize=16m`으로 축소(3.6 GiB). 이 변경은 workload 크기 자체를 바꾸므로 videoserver 결과는 GitHub와 비교 불가하고 정책 간 상대 비교로만 쓴다. cat37/online videoserver는 queue3의 4 고정 정책과 별개로 재실행 필요. queue3 진행 중(fio seed s2 × 6정책 완료, s3 진행 중).

## 2026-09-15 — 큐 재편성: mix 우선 (gh-queue5-20260915)

- 사용자 요청: mix 결과를 먼저 보고 싶음. queue3(fio s3 진행 중)·queue4 스크립트를 중단(진행 중이던 gh-fio fixed47 test5-s3 run은 완주하게 둠). 새 queue5가 장치가 빌 때까지 기다린 뒤: mixB/mixC smoke → **rep1: mixA·mixB·mixC × 6정책(greedy, fixed10, fixed37, fixed47, fixed50, online)** → rep2 → rep3 → 남은 fio s3(test3 fixed50/online, test5 전부) → filebench webserver/webproxy/videoserver × 6정책 → main × greedy/fixed10/fixed37/fixed50. 이미 summary가 있는 run은 건너뛴다. 블록마다 push.
- 예상: mix rep1 18 run ≈ 5시간(오늘 저녁), rep2/3 ≈ 내일, 나머지 모레.

### mix-20260911 mixB online — started 2026-09-15T12:41:33+09:00

- Phase A fio test4 fixed payload (5898240000/2949120000/983040000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (20000 records, 20000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixB online`; evidence `result/mix-20260911/mixB-online/`.

- Finished 2026-09-15T12:44:10+09:00; mixB online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-online-rep1-smoke`; cleanup attempted.
- total host_bytes=9933803520 host_pages=2425245 gc_pages=2522168 WAF=2.039964
- phaseA(sqlite-a) host_pages=25178 gc_pages=20407 WAF=1.810509
- phaseB(test4) host_pages=2400067 gc_pages=2501761 WAF=2.042371
- phaseA-load host_pages=16274 gc_pages=13629 WAF=1.837471
- phaseA-run host_pages=8904 gc_pages=6778 WAF=1.761231
- ycsb-load [OVERALL], Throughput(ops/sec), 17559.26251097454
- ycsb-run [OVERALL], Throughput(ops/sec), 28089.887640449437

### mix-20260911 mixC online — started 2026-09-15T12:44:10+09:00

- Phase A fio test4 fixed payload (5898240000/2949120000/983040000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (20000 records, 20000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixC online`; evidence `result/mix-20260911/mixC-online/`.

- Finished 2026-09-15T12:47:36+09:00; mixC online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-online-rep1-smoke`; cleanup attempted.
- total host_bytes=12288462848 host_pages=3000113 gc_pages=2887960 WAF=1.962617
- phaseA(test3) host_pages=600046 gc_pages=476379 WAF=1.793904
- phaseB(test4) host_pages=2400067 gc_pages=2411581 WAF=2.004797
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD online — started 2026-09-15T12:47:36+09:00

- Phase A fio test4 fixed payload (5898240000/2949120000/983040000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (20000 records, 20000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixD online`; evidence `result/mix-20260911/mixD-online/`.

- Finished 2026-09-15T12:51:00+09:00; mixD online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-online-rep1-smoke`; cleanup attempted.
- total host_bytes=12288462848 host_pages=3000113 gc_pages=3170292 WAF=2.056724
- phaseA(test4) host_pages=2400067 gc_pages=2499435 WAF=2.041402
- phaseB(test3) host_pages=600046 gc_pages=670857 WAF=2.118009
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF online — started 2026-09-15T12:51:00+09:00

- Phase A fio test4 fixed payload (5898240000/2949120000/983040000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (20000 records, 20000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixF online`; evidence `result/mix-20260911/mixF-online/`.

- Finished 2026-09-15T12:53:45+09:00; mixF online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-online-rep1-smoke`; cleanup attempted.
- total host_bytes=21255577600 host_pages=5189350 gc_pages=5397398 WAF=2.040091
- phaseA(test4) host_pages=2400067 gc_pages=2492754 WAF=2.038619
- phaseB(varmail) host_pages=2789283 gc_pages=2904644 WAF=2.041359
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG online — started 2026-09-15T12:53:45+09:00

- Phase A fio test4 fixed payload (5898240000/2949120000/983040000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (20000 records, 20000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixG online`; evidence `result/mix-20260911/mixG-online/`.

- Finished 2026-09-15T12:55:40+09:00; mixG online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-online-rep1-smoke`; cleanup attempted.
- total host_bytes=5019004928 host_pages=1225343 gc_pages=1216852 WAF=1.993071
- phaseA(concurrent-test4+sqlite-a) host_pages=1225343 gc_pages=1216852 WAF=1.993071
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixH online — started 2026-09-15T12:55:41+09:00

- Phase A fio test4 fixed payload (5898240000/2949120000/983040000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (20000 records, 20000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixH online`; evidence `result/mix-20260911/mixH-online/`.

- Finished 2026-09-15T12:59:19+09:00; mixH online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-online-rep1-smoke`; cleanup attempted.
- total host_bytes=12392329216 host_pages=3025471 gc_pages=2903206 WAF=1.959588
- phaseA(test3) host_pages=600043 gc_pages=476779 WAF=1.794575
- phaseB(test4) host_pages=2400067 gc_pages=2408951 WAF=2.003702
- phaseC(sqlite-a) host_pages=25361 gc_pages=17476 WAF=1.689090
- phaseC-load host_pages=16274 gc_pages=10882 WAF=1.668674
- phaseC-run host_pages=9087 gc_pages=6594 WAF=1.725652
- ycsb-load [OVERALL], Throughput(ops/sec), 18066.847335140017
- ycsb-run [OVERALL], Throughput(ops/sec), 25940.33722438392

### mix-20260911 mixJ online — started 2026-09-15T12:59:19+09:00

- Phase A fio test4 fixed payload (5898240000/2949120000/983040000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (20000 records, 20000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixJ online`; evidence `result/mix-20260911/mixJ-online/`.

- Finished 2026-09-15T13:01:03+09:00; mixJ online exit=1; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-online-rep1-smoke`; cleanup attempted.
- total host_bytes=110546944 host_pages=26989 gc_pages=21628 WAF=1.801364
- phaseA(sqlite-a) host_pages=25373 gc_pages=19883 WAF=1.783628
- phaseB(sqlite-b) host_pages=1616 gc_pages=1745 WAF=2.079827
- phaseA-load host_pages=16274 gc_pages=13102 WAF=1.805088
- phaseA-run host_pages=9099 gc_pages=6781 WAF=1.745247
- ycsb-load [OVERALL], Throughput(ops/sec), 19550.342130987294
- ycsb-run [OVERALL], Throughput(ops/sec), 16891.891891891893

### mix-20260911 mixK online — started 2026-09-15T13:01:04+09:00

- Phase A fio test4 fixed payload (5898240000/2949120000/983040000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (20000 records, 20000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixK online`; evidence `result/mix-20260911/mixK-online/`.

- Finished 2026-09-15T13:04:32+09:00; mixK online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-online-rep1-smoke`; cleanup attempted.
- total host_bytes=19661692928 host_pages=4800218 gc_pages=5273526 WAF=2.098601
- phaseA(test4-hot512M) host_pages=2400085 gc_pages=2499854 WAF=2.041569
- phaseB(test4-hot128M) host_pages=2400133 gc_pages=2773672 WAF=2.155633
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL online — started 2026-09-15T13:04:32+09:00

- Phase A fio test4 fixed payload (5898240000/2949120000/983040000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (20000 records, 20000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixL online`; evidence `result/mix-20260911/mixL-online/`.

- Finished 2026-09-15T13:06:57+09:00; mixL online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-online-rep1-smoke`; cleanup attempted.
- total host_bytes=6192537600 host_pages=1511850 gc_pages=291356 WAF=1.192715
- phaseA(alternate-fast/slow-x5) host_pages=1511850 gc_pages=291356 WAF=1.192715
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixM online — started 2026-09-15T13:06:57+09:00

- Phase A fio test4 fixed payload (5898240000/2949120000/983040000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (20000 records, 20000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixM online`; evidence `result/mix-20260911/mixM-online/`.

- Finished 2026-09-15T13:09:22+09:00; mixM online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixM-online-rep1-smoke`; cleanup attempted.
- total host_bytes=7373037568 host_pages=1800058 gc_pages=833055 WAF=1.462793
- phaseA(ramp-10k-to-50k) host_pages=1800058 gc_pages=833055 WAF=1.462793
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO online — started 2026-09-15T13:09:22+09:00

- Phase A fio test4 fixed payload (5898240000/2949120000/983040000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (20000 records, 20000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixO online`; evidence `result/mix-20260911/mixO-online/`.

- Finished 2026-09-15T13:11:31+09:00; mixO online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-online-rep1-smoke`; cleanup attempted.
- total host_bytes=16414842880 host_pages=4007530 gc_pages=1973341 WAF=1.492408
- phaseA(oltp) host_pages=708795 gc_pages=562747 WAF=1.793949
- phaseB(varmail) host_pages=3298735 gc_pages=1410594 WAF=1.427617
- ycsb-load 
- ycsb-run 

### mix-20260911 mixP online — started 2026-09-15T13:11:31+09:00

- Phase A fio test4 fixed payload (5898240000/2949120000/983040000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (20000 records, 20000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixP online`; evidence `result/mix-20260911/mixP-online/`.

- Finished 2026-09-15T13:13:27+09:00; mixP online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-online-rep1-smoke`; cleanup attempted.
- total host_bytes=2654924800 host_pages=648175 gc_pages=362205 WAF=1.558807
- phaseA(sqlite-a) host_pages=26218 gc_pages=20842 WAF=1.794950
- phaseB(oltp) host_pages=621957 gc_pages=341363 WAF=1.548853
- phaseA-load host_pages=16274 gc_pages=12940 WAF=1.795133
- phaseA-run host_pages=9944 gc_pages=7902 WAF=1.794650
- ycsb-load [OVERALL], Throughput(ops/sec), 17889.08765652952
- ycsb-run [OVERALL], Throughput(ops/sec), 25188.91687657431

### mix-20260911 mixQ online — started 2026-09-15T13:13:28+09:00

- Phase A fio test4 fixed payload (5898240000/2949120000/983040000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (20000 records, 20000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixQ online`; evidence `result/mix-20260911/mixQ-online/`.

- Finished 2026-09-15T13:16:27+09:00; mixQ online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-online-rep1-smoke`; cleanup attempted.
- total host_bytes=9864196096 host_pages=2408251 gc_pages=2247494 WAF=1.933247
- phaseA(test4) host_pages=1208217 gc_pages=1149594 WAF=1.951480
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=1200034 gc_pages=1097900 WAF=1.914891
- ycsb-load 
- ycsb-run 

### mix-20260911 mixA greedy — started 2026-09-15T13:37:07+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixA greedy`; evidence `result/mix-20260911/mixA-greedy/`.

## 2026-09-15 — mix 설계 14종 사전 등록 및 마스터 큐(gh-queue6-20260915)

- 사용자 요청: 타당한 mix workload를 더 만들어 iCAT/CAT/Greedy 전부 실행. `mix-20260911.sh`에 설계 추가(모두 start/stop 계측, 준비 동일, seed=rep):
  - 핵심: **A** test4→sqlite-a(파일 유지) / **B** sqlite-a→test4 / **C** test3→test4(속도 4배) / **D** test4→test3 / **J** 같은 DB에서 workload a→b / **G** test4(1/2 payload)+sqlite-a 동시
  - 추가: **K** hot 512M→128M(속도 동일) / **L** 60초 빠름·느림 5회 반복 / **M** 10k→50k IOPS 5단계 ramp / **Q** test4(1/2)→300초 유휴→test4(1/2)
  - 보조: **O** oltp(64m 파일)→varmail(24000 files) / **P** sqlite-a→oltp(32m) / **H** test3→test4→sqlite-a / **F** test4→varmail
  - filebench phase는 6 GiB preset 파일이 남아 있어 ~1.5 GiB 안에서 돌도록 파일 크기를 줄였다(원본 oltp 512m×10 불가). varmail은 sweep 조건(24000 files)으로 고정.
- smoke(1/10 크기) 13종 전부 완주(mixJ exit=1은 online 모듈의 4-partition sample 검사가 작은 workload에서 미충족된 것; summary는 정상). 증거 `result/mix-20260911/*-online-rep1-smoke/`.
- 실행 순서: rep1 [핵심 6 → 추가 4 → 보조 4] × 6정책(greedy, fixed10, fixed37, fixed47, fixed50, online) → rep2 → rep3 → 단일 잔여(fio s3, filebench web 3종, main 나머지). 약 250 run, 3~4일. 블록마다 push. 이미 summary가 있는 run은 건너뜀.
- 사전 판정: 각 run 내부 검사 통과. mix의 목적은 "phase 전환 시 고정 arm의 손해 크기"를 정책별·구간별 WAF로 확정하는 것이며, 현재 학습기(12% 손실)로 iCAT 우세는 기대하지 않는다.

- Finished 2026-09-15T13:57:10+09:00; mixA greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-greedy-rep1`; cleanup attempted.
- total host_bytes=131593355264 host_pages=32127284 gc_pages=45660420 WAF=2.421235
- phaseA(test4) host_pages=24000658 gc_pages=30053271 WAF=2.252185
- phaseB(sqlite-a) host_pages=8126626 gc_pages=15607149 WAF=2.920496
- phaseB-load host_pages=1398351 gc_pages=1656201 WAF=2.184396
- phaseB-run host_pages=6728275 gc_pages=13950948 WAF=3.073481
- ycsb-load [OVERALL], Throughput(ops/sec), 24620.434961017643
- ycsb-run [OVERALL], Throughput(ops/sec), 8246.334504312834

### mix-20260911 mixA fixed10 — started 2026-09-15T13:57:10+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixA fixed10`; evidence `result/mix-20260911/mixA-fixed10/`.

- Finished 2026-09-15T14:15:28+09:00; mixA fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-fixed10-rep1`; cleanup attempted.
- total host_bytes=132029214720 host_pages=32233695 gc_pages=45697205 WAF=2.417684
- phaseA(test4) host_pages=24000658 gc_pages=30289977 WAF=2.262048
- phaseB(sqlite-a) host_pages=8233037 gc_pages=15407228 WAF=2.871391
- phaseB-load host_pages=1398345 gc_pages=1686779 WAF=2.206268
- phaseB-run host_pages=6834692 gc_pages=13720449 WAF=3.007471
- ycsb-load [OVERALL], Throughput(ops/sec), 23254.91260028681
- ycsb-run [OVERALL], Throughput(ops/sec), 10880.65283917035

### mix-20260911 mixA fixed37 — started 2026-09-15T14:15:28+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixA fixed37`; evidence `result/mix-20260911/mixA-fixed37/`.

- Finished 2026-09-15T14:33:09+09:00; mixA fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-fixed37-rep1`; cleanup attempted.
- total host_bytes=131603685376 host_pages=32129806 gc_pages=29153011 WAF=1.907351
- phaseA(test4) host_pages=24000658 gc_pages=23373849 WAF=1.973884
- phaseB(sqlite-a) host_pages=8129148 gc_pages=5779162 WAF=1.710919
- phaseB-load host_pages=1398351 gc_pages=1191905 WAF=1.852365
- phaseB-run host_pages=6730797 gc_pages=4587257 WAF=1.681533
- ycsb-load [OVERALL], Throughput(ops/sec), 23538.642604943114
- ycsb-run [OVERALL], Throughput(ops/sec), 12107.820138331845

### mix-20260911 mixA fixed47 — started 2026-09-15T14:33:10+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixA fixed47`; evidence `result/mix-20260911/mixA-fixed47/`.

- Finished 2026-09-15T14:50:51+09:00; mixA fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-fixed47-rep1`; cleanup attempted.
- total host_bytes=131651080192 host_pages=32141377 gc_pages=22801918 WAF=1.709426
- phaseA(test4) host_pages=24000667 gc_pages=18576196 WAF=1.773987
- phaseB(sqlite-a) host_pages=8140710 gc_pages=4225722 WAF=1.519085
- phaseB-load host_pages=1398349 gc_pages=521171 WAF=1.372705
- phaseB-run host_pages=6742361 gc_pages=3704551 WAF=1.549444
- ycsb-load [OVERALL], Throughput(ops/sec), 21037.130535394972
- ycsb-run [OVERALL], Throughput(ops/sec), 12089.267148625451

### mix-20260911 mixA fixed50 — started 2026-09-15T14:50:52+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixA fixed50`; evidence `result/mix-20260911/mixA-fixed50/`.

- Finished 2026-09-15T15:08:28+09:00; mixA fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-fixed50-rep1`; cleanup attempted.
- total host_bytes=131587219456 host_pages=32125786 gc_pages=23558002 WAF=1.733305
- phaseA(test4) host_pages=24000658 gc_pages=19507313 WAF=1.812782
- phaseB(sqlite-a) host_pages=8125128 gc_pages=4050689 WAF=1.498538
- phaseB-load host_pages=1398349 gc_pages=548011 WAF=1.391899
- phaseB-run host_pages=6726779 gc_pages=3502678 WAF=1.520707
- ycsb-load [OVERALL], Throughput(ops/sec), 21381.989237732083
- ycsb-run [OVERALL], Throughput(ops/sec), 12275.88831396812

### mix-20260911 mixA online — started 2026-09-15T15:08:28+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixA online`; evidence `result/mix-20260911/mixA-online/`.

- Finished 2026-09-15T15:28:51+09:00; mixA online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-online-rep1`; cleanup attempted.
- total host_bytes=131765182464 host_pages=32169234 gc_pages=36112905 WAF=2.122591
- phaseA(test4) host_pages=24000658 gc_pages=23994209 WAF=1.999731
- phaseB(sqlite-a) host_pages=8168576 gc_pages=12118696 WAF=2.483575
- phaseB-load host_pages=1398351 gc_pages=1718945 WAF=2.229266
- phaseB-run host_pages=6770225 gc_pages=10399751 WAF=2.536101
- ycsb-load [OVERALL], Throughput(ops/sec), 23122.278315156655
- ycsb-run [OVERALL], Throughput(ops/sec), 7975.038130651063

### mix-20260911 mixB greedy — started 2026-09-15T15:29:31+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixB greedy`; evidence `result/mix-20260911/mixB-greedy/`.

- Finished 2026-09-15T15:46:57+09:00; mixB greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-greedy-rep1`; cleanup attempted.
- total host_bytes=131522187264 host_pages=32109909 gc_pages=84224019 WAF=3.622992
- phaseA(sqlite-a) host_pages=8109251 gc_pages=9543591 WAF=2.176877
- phaseB(test4) host_pages=24000658 gc_pages=74680428 WAF=4.111599
- phaseA-load host_pages=1399363 gc_pages=1048019 WAF=1.748926
- phaseA-run host_pages=6709888 gc_pages=8495572 WAF=2.266127
- ycsb-load [OVERALL], Throughput(ops/sec), 25197.379472534856
- ycsb-run [OVERALL], Throughput(ops/sec), 12439.435498417082

### mix-20260911 mixB fixed10 — started 2026-09-15T15:46:57+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixB fixed10`; evidence `result/mix-20260911/mixB-fixed10/`.

- Finished 2026-09-15T16:06:45+09:00; mixB fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-fixed10-rep1`; cleanup attempted.
- total host_bytes=131447197696 host_pages=32091601 gc_pages=83237650 WAF=3.593752
- phaseA(sqlite-a) host_pages=8090943 gc_pages=8174338 WAF=2.010307
- phaseB(test4) host_pages=24000658 gc_pages=75063312 WAF=4.127552
- phaseA-load host_pages=1398341 gc_pages=1068910 WAF=1.764413
- phaseA-run host_pages=6692602 gc_pages=7105428 WAF=2.061684
- ycsb-load [OVERALL], Throughput(ops/sec), 24299.368216426374
- ycsb-run [OVERALL], Throughput(ops/sec), 8519.71995680502

### mix-20260911 mixB fixed37 — started 2026-09-15T16:06:45+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixB fixed37`; evidence `result/mix-20260911/mixB-fixed37/`.

- Finished 2026-09-15T16:24:08+09:00; mixB fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-fixed37-rep1`; cleanup attempted.
- total host_bytes=131533479936 host_pages=32112666 gc_pages=70697956 WAF=3.201560
- phaseA(sqlite-a) host_pages=8112001 gc_pages=4145288 WAF=1.511007
- phaseB(test4) host_pages=24000665 gc_pages=66552668 WAF=3.772951
- phaseA-load host_pages=1398349 gc_pages=612125 WAF=1.437748
- phaseA-run host_pages=6713652 gc_pages=3533163 WAF=1.526265
- ycsb-load [OVERALL], Throughput(ops/sec), 24229.697532609134
- ycsb-run 

### mix-20260911 mixB fixed47 — started 2026-09-15T16:24:09+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixB fixed47`; evidence `result/mix-20260911/mixB-fixed47/`.

- Finished 2026-09-15T16:41:33+09:00; mixB fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-fixed47-rep1`; cleanup attempted.
- total host_bytes=131462688768 host_pages=32095383 gc_pages=46487490 WAF=2.448417
- phaseA(sqlite-a) host_pages=8094722 gc_pages=3382154 WAF=1.417822
- phaseB(test4) host_pages=24000661 gc_pages=43105336 WAF=2.796006
- phaseA-load host_pages=1398347 gc_pages=367286 WAF=1.262657
- phaseA-run host_pages=6696375 gc_pages=3014868 WAF=1.450224
- ycsb-load [OVERALL], Throughput(ops/sec), 21951.487213258697
- ycsb-run [OVERALL], Throughput(ops/sec), 12703.89755577011

### mix-20260911 mixB fixed50 — started 2026-09-15T16:41:34+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixB fixed50`; evidence `result/mix-20260911/mixB-fixed50/`.

- Finished 2026-09-15T17:01:13+09:00; mixB fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-fixed50-rep1`; cleanup attempted.
- total host_bytes=131342823424 host_pages=32066119 gc_pages=51880004 WAF=2.617907
- phaseA(sqlite-a) host_pages=8065461 gc_pages=3642854 WAF=1.451661
- phaseB(test4) host_pages=24000658 gc_pages=48237150 WAF=3.009826
- phaseA-load host_pages=1398349 gc_pages=381067 WAF=1.272512
- phaseA-run host_pages=6667112 gc_pages=3261787 WAF=1.489235
- ycsb-load [OVERALL], Throughput(ops/sec), 21176.719726114425
- ycsb-run [OVERALL], Throughput(ops/sec), 8749.231708090634

### mix-20260911 mixB online — started 2026-09-15T17:01:13+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixB online`; evidence `result/mix-20260911/mixB-online/`.

- Finished 2026-09-15T17:18:52+09:00; mixB online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-online-rep1`; cleanup attempted.
- total host_bytes=131650646016 host_pages=32141271 gc_pages=70941833 WAF=3.207188
- phaseA(sqlite-a) host_pages=8140610 gc_pages=7835731 WAF=1.962548
- phaseB(test4) host_pages=24000661 gc_pages=63106102 WAF=3.629349
- phaseA-load host_pages=1398351 gc_pages=922745 WAF=1.659881
- phaseA-run host_pages=6742259 gc_pages=6912986 WAF=2.025322
- ycsb-load [OVERALL], Throughput(ops/sec), 23655.57483046838
- ycsb-run [OVERALL], Throughput(ops/sec), 12050.733588407194

### mix-20260911 mixC greedy — started 2026-09-15T17:18:58+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixC greedy`; evidence `result/mix-20260911/mixC-greedy/`.

- Finished 2026-09-15T17:40:23+09:00; mixC greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-greedy-rep1`; cleanup attempted.
- total host_bytes=122922139648 host_pages=30010288 gc_pages=37502866 WAF=2.249667
- phaseA(test3) host_pages=6009624 gc_pages=6952444 WAF=2.156885
- phaseB(test4) host_pages=24000664 gc_pages=30550422 WAF=2.272899
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC fixed10 — started 2026-09-15T17:40:23+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixC fixed10`; evidence `result/mix-20260911/mixC-fixed10/`.

- Finished 2026-09-15T18:01:46+09:00; mixC fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-fixed10-rep1`; cleanup attempted.
- total host_bytes=122947317760 host_pages=30016435 gc_pages=37779603 WAF=2.258631
- phaseA(test3) host_pages=6015768 gc_pages=7001438 WAF=2.163848
- phaseB(test4) host_pages=24000667 gc_pages=30778165 WAF=2.282388
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC fixed37 — started 2026-09-15T18:01:46+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixC fixed37`; evidence `result/mix-20260911/mixC-fixed37/`.

- Finished 2026-09-15T18:23:09+09:00; mixC fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-fixed37-rep1`; cleanup attempted.
- total host_bytes=122884419584 host_pages=30001079 gc_pages=26744864 WAF=1.891463
- phaseA(test3) host_pages=6000421 gc_pages=4947449 WAF=1.824517
- phaseB(test4) host_pages=24000658 gc_pages=21797415 WAF=1.908201
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC fixed47 — started 2026-09-15T18:23:09+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixC fixed47`; evidence `result/mix-20260911/mixC-fixed47/`.

## 2026-09-15 — 결정: v1 실험 완료 후 iCAT v2 (판단 window 확대만)

- 사용자 결정: 현재 큐(mix 14종 × 6정책 × 3 seed + 단일 잔여)를 끝까지 돌린 뒤, iCAT v2를 시험한다. v2의 변경은 **window 확대 하나만**(64 GC/256 MiB → 약 6배, 60초 수준). k=2 제거·조기 탈락·dwell은 v2 결과를 본 뒤 결정. v2 결과는 v1과 분리해 기록한다.
- 큐 진행 중 장치를 쓰지 않는 준비(v2 소스 분기·빌드·hash 기록)는 미리 한다. 장치 smoke는 큐 종료 후.
- 노벨티 관련 관찰(기록용): 사전 sweep과 본 측정 모두에서 최적 arm은 scale 25~50%·k 7~10에 몰려 있고 scale 200/400%가 최적인 워크로드가 없다. 현재 워크로드가 모두 재기록 주기 초 단위의 "빠른" 워크로드이기 때문으로 보이며, "고정 하나로는 안 된다"를 강하게 보이려면 재기록 주기가 분~시간 단위인 느린 워크로드 추가가 필요하다(추후 결정).

- Finished 2026-09-15T18:44:33+09:00; mixC fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-fixed47-rep1`; cleanup attempted.
- total host_bytes=122884419584 host_pages=30001079 gc_pages=22524804 WAF=1.750800
- phaseA(test3) host_pages=6000421 gc_pages=4787838 WAF=1.797917
- phaseB(test4) host_pages=24000658 gc_pages=17736966 WAF=1.739020
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC fixed50 — started 2026-09-15T18:44:33+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixC fixed50`; evidence `result/mix-20260911/mixC-fixed50/`.

## 2026-09-15 — iCAT v2 사전 등록 (gh-queue7-v2, queue6 종료 후 자동 시작)

- 사용자 요청: v1 큐가 끝나는 즉시 v2 시작. **v2 = online-mix-src 복사본(`online-v2-src/`)에서 conv_ftl.h 두 상수만 변경**: `WATGC_V2_WINDOW_GC` 64→384, `WATGC_V2_WINDOW_HOST_PAGES` 65536→393216 (256 MiB→1.5 GiB, 6배). 그 외 학습기 상수·정책·계측 코드 무변경. 목적: window당 관측 WAF의 잡음(v1에서 동일 arm 폭 0.385)을 줄여 arm 간 차이(0.098)를 분별 가능하게 함. 부작용으로 STABLE/STALE/DRIFT window 수는 그대로이므로 시간 기준으로는 6배 길어짐(기록).
- 모듈 `buildoutput/nvmev-online-v2.ko` SHA256 `8a8909a1…`(`modules.sha256`). mix 러너에 정책 `onlinev2` 추가.
- 실행: t4 smoke → t4 × 3 seed(명시 계측) → GitHub 방식 단일(fio 4종 × seed 3, sqlite a/b × 3, filebench oltp/varmail × 3) → mix 14종 × 3 seed. v2는 online만 다시 돌리며 고정 정책·Greedy 결과는 v1 것을 공유한다(코드 동일). 결과는 `*-online-v2*`, `*-onlinev2-*`로 구분.
- 판정: v1 대비 (1) settled 비율·best arm 교체 횟수 감소, (2) 단일 워크로드에서 최적 고정 CAT 대비 손실이 v1의 12%에서 유의미하게 감소, 목표 ≤4%(arm50 수준). 실패 시 window 외 요인(탐색 상수, 후보 축소)로 넘어간다.

- Finished 2026-09-15T19:05:56+09:00; mixC fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-fixed50-rep1`; cleanup attempted.
- total host_bytes=122884419584 host_pages=30001079 gc_pages=23404766 WAF=1.780131
- phaseA(test3) host_pages=6000421 gc_pages=4810121 WAF=1.801631
- phaseB(test4) host_pages=24000658 gc_pages=18594645 WAF=1.774756
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC online — started 2026-09-15T19:05:56+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixC online`; evidence `result/mix-20260911/mixC-online/`.

- Finished 2026-09-15T19:27:19+09:00; mixC online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-online-rep1`; cleanup attempted.
- total host_bytes=122884419584 host_pages=30001079 gc_pages=29989276 WAF=1.999607
- phaseA(test3) host_pages=6000421 gc_pages=6836509 WAF=2.139338
- phaseB(test4) host_pages=24000658 gc_pages=23152767 WAF=1.964672
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD greedy — started 2026-09-15T19:27:22+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixD greedy`; evidence `result/mix-20260911/mixD-greedy/`.

- Finished 2026-09-15T19:48:45+09:00; mixD greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-greedy-rep1`; cleanup attempted.
- total host_bytes=122964094976 host_pages=30020531 gc_pages=37481592 WAF=2.248532
- phaseA(test4) host_pages=24020113 gc_pages=29861464 WAF=2.243186
- phaseB(test3) host_pages=6000418 gc_pages=7620128 WAF=2.269933
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD fixed10 — started 2026-09-15T19:48:45+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixD fixed10`; evidence `result/mix-20260911/mixD-fixed10/`.

- Finished 2026-09-15T20:10:08+09:00; mixD fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-fixed10-rep1`; cleanup attempted.
- total host_bytes=122884419584 host_pages=30001079 gc_pages=37983178 WAF=2.266060
- phaseA(test4) host_pages=24000658 gc_pages=30301177 WAF=2.262514
- phaseB(test3) host_pages=6000421 gc_pages=7682001 WAF=2.280244
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD fixed37 — started 2026-09-15T20:10:08+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixD fixed37`; evidence `result/mix-20260911/mixD-fixed37/`.

- Finished 2026-09-15T20:31:31+09:00; mixD fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-fixed37-rep1`; cleanup attempted.
- total host_bytes=122884431872 host_pages=30001082 gc_pages=28512349 WAF=1.950377
- phaseA(test4) host_pages=24000658 gc_pages=23408914 WAF=1.975345
- phaseB(test3) host_pages=6000424 gc_pages=5103435 WAF=1.850512
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD fixed47 — started 2026-09-15T20:31:31+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixD fixed47`; evidence `result/mix-20260911/mixD-fixed47/`.

- Finished 2026-09-15T20:52:55+09:00; mixD fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-fixed47-rep1`; cleanup attempted.
- total host_bytes=122884419584 host_pages=30001079 gc_pages=23346628 WAF=1.778193
- phaseA(test4) host_pages=24000664 gc_pages=18503876 WAF=1.770974
- phaseB(test3) host_pages=6000415 gc_pages=4842752 WAF=1.807070
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD fixed50 — started 2026-09-15T20:52:55+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixD fixed50`; evidence `result/mix-20260911/mixD-fixed50/`.

- Finished 2026-09-15T21:14:18+09:00; mixD fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-fixed50-rep1`; cleanup attempted.
- total host_bytes=122913775616 host_pages=30008246 gc_pages=24380415 WAF=1.812457
- phaseA(test4) host_pages=24007828 gc_pages=19506579 WAF=1.812509
- phaseB(test3) host_pages=6000418 gc_pages=4873836 WAF=1.812249
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD online — started 2026-09-15T21:14:18+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixD online`; evidence `result/mix-20260911/mixD-online/`.

- Finished 2026-09-15T21:35:41+09:00; mixD online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-online-rep1`; cleanup attempted.
- total host_bytes=122972483584 host_pages=30022579 gc_pages=31364517 WAF=2.044698
- phaseA(test4) host_pages=24022161 gc_pages=23749162 WAF=1.988636
- phaseB(test3) host_pages=6000418 gc_pages=7615355 WAF=2.269137
- ycsb-load 
- ycsb-run 

### mix-20260911 mixJ greedy — started 2026-09-15T21:35:44+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixJ greedy`; evidence `result/mix-20260911/mixJ-greedy/`.

- Finished 2026-09-15T21:47:28+09:00; mixJ greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-greedy-rep1`; cleanup attempted.
- total host_bytes=35566329856 host_pages=8683186 gc_pages=8864192 WAF=2.020846
- phaseA(sqlite-a) host_pages=8051761 gc_pages=8170771 WAF=2.014781
- phaseB(sqlite-b) host_pages=631425 gc_pages=693421 WAF=2.098184
- phaseA-load host_pages=1398351 gc_pages=1050059 WAF=1.750927
- phaseA-run host_pages=6653410 gc_pages=7120712 WAF=2.070235
- ycsb-load [OVERALL], Throughput(ops/sec), 23500.84211350907
- ycsb-run [OVERALL], Throughput(ops/sec), 45656.88848304988

## 2026-09-15 — 우선순위 변경: 60-arm sweep을 이 머신에서 재실행 (sweep-20260915)

- 사용자 결정: 고정 4개(최악/기본/최적/견고) 라벨이 선행 연구 sweep(다른 환경, 소스 미커밋)에 의존하므로, 60 arm 전부를 이 머신에서 직접 돌려 순위를 확정한다. 이를 v1 mix·v2보다 우선한다.
- 모듈: `varmail-compare-src` FIXED_ARM=0..59 → `buildoutput/nvmev-arm00..59.ko`(hash `result/sweep-20260915/modules.sha256`). 동일 소스·동일 커널.
- 워크로드 3개(GitHub 계측 방식, 각 1회): test4(fio 3영역 빠름), sqlite-a, filebench oltp. 60×3=180 run ≈ 39시간. 결과 콘솔 `result/sweep-20260915/`, `result/sqlite/a-armNN.*`, `result/filebench/oltp-armNN.*`.
- 판정: 워크로드별 60 arm 순위와 선행 sweep 순위의 일치도(Spearman), 최악/기본/최적/견고 라벨의 이 환경 등수. 라벨이 바뀌면 이후 실험의 고정 arm을 갱신한다.
- 순서: 진행 중이던 v1 run(mixJ greedy rep1) 완주 → sweep → queue6(v1 mix, 완료분 건너뜀) → queue7(v2) 자동 재개. queue6/7 스크립트는 중단해 두었다.
- 부수 관찰(long-online 재분석): iCAT v1은 30분경 후보를 25개로 좁히며 WAF 2.00→1.84로 개선되나 이후 다시 42~49개로 확장되며 1.86으로 되돌아감. "학습되지만 정착하지 못함"으로 정정.

## 2026-09-15 — phase 길이 vs 학습 시간 실험 사전 등록 (gh-queue8-phaselen, sweep 직후)

- 사용자 제안: mix에서 phase 길이가 iCAT 학습 시간(v1 재분석에서 약 30분)보다 짧으면 iCAT이 따라갈 수 없으므로, phase 길이를 축으로 두고 어느 길이부터 iCAT이 고정 CAT을 따라잡는지 본다.
- 설계: mixA(test4→sqlite-a), mixC(test3→test4)를 phase ×1(10분, queue6 결과 공유), ×3(30분), ×6(60분). `MULT` 환경변수로 fio payload와 YCSB op 수를 배수 적용(load 크기는 고정). 정책: online(v1), onlinev2, fixed47, fixed50. 16 run ≈ 14시간. seed 1만.
- 분석: 구간별 WAF + 10분 단위 시계열(WAF, 시험 중 arm 수)로 전환 후 재수렴 시간을 본다. 판정: 어떤 길이에서 iCAT(v1/v2)이 견고(arm50) 이내(≤4%)에 들어오는가.
- 순서: sweep(180 run, 진행 중 — test4 arm00부터) → 본 실험 → queue6(v1 mix 잔여) → queue7(v2). sweep 스크립트의 queue6/7 자동 재개는 제거하고 queue8이 대신 재개한다.

## 2026-09-15 — mix 60-arm sweep 사전 등록 (gh-queue9-mixsweep)

- 사용자 결정: mix에서도 60 arm 전부. 대상 mixA(test4→sqlite-a, 파일 유지)와 mixC(test3→test4), seed 1, 명시 계측. 120 run ≈ 30시간. 정책 이름 `armNN`을 mix 러너에 추가(`buildoutput/nvmev-armNN.ko`, sweep과 동일 모듈).
- 목적: phase 전환 시 "각 phase의 최적 arm이 실제로 다른가"와 "두 phase 합산 최적 arm"을 우리 환경에서 직접 확인. 이것이 iCAT이 넘어야 할 진짜 기준선(mix별 최적 고정)이 된다.
- 순서: sweep(단일 180) → phase 길이(16) → **mix sweep(120)** → queue6(v1 mix 잔여) → queue7(v2). 총 예상 9/20 전후.
- 2026-09-16 11:05 sweep test4 60/60 완료(07:54 push). 이 머신 순위(`result/sweep-20260915/rank-test4.txt`, `analysis/sweep-rank.py`): 1등 arm31(k7/s25/r7) 1.7439, 2등 arm47 1.7455(차 0.1%), 견고 arm50 6등 1.7859, 기본 arm37 21등 1.9375, 최악 arm10 51등 2.2070(꼴찌 arm12 2.2321, 차 1.1%). GitHub sweep과 Spearman ρ=0.959, 편차 28.0% vs 27.7%. 결론: 선행 sweep 순위가 이 환경에서 재현되며, 최적/견고/최악 라벨은 유지해도 된다(최적은 arm31과 사실상 동률). k=2 arm 15개가 하위 16등 중 14개를 차지.

## 2026-09-17 — 다음 후보 (현재 큐 종료 후, 사용자 결정 대기)

리뷰 대응 관점에서 순서: (1) 격자 확장 scale 5%/10% × k10 × ratio 3 = 6 arm, test4·sqlite-a (최적이 격자 끝 25%에 있음) (2) 실제 trace 재생 (MSR Cambridge, fio read_iolog, 주소 축소) (3) OP 비율 변경(논리 용량 6.5 GiB) (4) 앱 워크로드 반복 5회. 사용자 지시: 진행 중 큐부터 마무리.

### mix-20260911 mixA online — started 2026-09-18T03:14:27+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixA online`; evidence `result/mix-20260911/mixA-online/`.

- Finished 2026-09-18T04:09:06+09:00; mixA online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-online-rep1-x3`; cleanup attempted.
- total host_bytes=383081099264 host_pages=93525659 gc_pages=86055798 WAF=1.920130
- phaseA(test4) host_pages=72011197 gc_pages=73904607 WAF=2.026293
- phaseB(sqlite-a) host_pages=21514462 gc_pages=12151191 WAF=1.564792
- phaseB-load host_pages=1398349 gc_pages=970655 WAF=1.694144
- phaseB-run host_pages=20116113 gc_pages=11180536 WAF=1.555800
- ycsb-load [OVERALL], Throughput(ops/sec), 25275.92889038672
- ycsb-run [OVERALL], Throughput(ops/sec), 8847.202182899686

### mix-20260911 mixA onlinev2 — started 2026-09-18T04:09:07+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v2.ko`.
- Command: `bash script/mix-20260911.sh mixA onlinev2`; evidence `result/mix-20260911/mixA-onlinev2/`.

- Finished 2026-09-18T05:03:54+09:00; mixA onlinev2 exit=1; evidence `/home/oy/iCAT/result/mix-20260911/mixA-onlinev2-rep1-x3`; cleanup attempted.
- total host_bytes=383134408704 host_pages=93538674 gc_pages=83236248 WAF=1.889859
- phaseA(test4) host_pages=72001996 gc_pages=70352803 WAF=1.977095
- phaseB(sqlite-a) host_pages=21536678 gc_pages=12883445 WAF=1.598209
- phaseB-load host_pages=1398349 gc_pages=1067286 WAF=1.763247
- phaseB-run host_pages=20138329 gc_pages=11816159 WAF=1.586750
- ycsb-load [OVERALL], Throughput(ops/sec), 22744.503411675512
- ycsb-run [OVERALL], Throughput(ops/sec), 8806.001583612619

### mix-20260911 mixA fixed47 — started 2026-09-18T05:03:54+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixA fixed47`; evidence `result/mix-20260911/mixA-fixed47/`.

- Finished 2026-09-18T05:52:08+09:00; mixA fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-fixed47-rep1-x3`; cleanup attempted.
- total host_bytes=383726972928 host_pages=93683343 gc_pages=65158882 WAF=1.695523
- phaseA(test4) host_pages=72001993 gc_pages=55546848 WAF=1.771463
- phaseB(sqlite-a) host_pages=21681350 gc_pages=9612034 WAF=1.443332
- phaseB-load host_pages=1398349 gc_pages=305486 WAF=1.218462
- phaseB-run host_pages=20283001 gc_pages=9306548 WAF=1.458835
- ycsb-load [OVERALL], Throughput(ops/sec), 26647.717178895007
- ycsb-run [OVERALL], Throughput(ops/sec), 12628.70757806646

### mix-20260911 mixA fixed50 — started 2026-09-18T05:52:08+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixA fixed50`; evidence `result/mix-20260911/mixA-fixed50/`.

- Finished 2026-09-18T06:40:14+09:00; mixA fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-fixed50-rep1-x3`; cleanup attempted.
- total host_bytes=383446188032 host_pages=93614792 gc_pages=67668600 WAF=1.722841
- phaseA(test4) host_pages=72001990 gc_pages=58597544 WAF=1.813832
- phaseB(sqlite-a) host_pages=21612802 gc_pages=9071056 WAF=1.419708
- phaseB-load host_pages=1398351 gc_pages=399266 WAF=1.285526
- phaseB-run host_pages=20214451 gc_pages=8671790 WAF=1.428990
- ycsb-load [OVERALL], Throughput(ops/sec), 21616.16889433296
- ycsb-run [OVERALL], Throughput(ops/sec), 12945.30500756761

### mix-20260911 mixC online — started 2026-09-18T06:40:28+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixC online`; evidence `result/mix-20260911/mixC-online/`.

- Finished 2026-09-18T07:41:55+09:00; mixC online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-online-rep1-x3`; cleanup attempted.
- total host_bytes=368653275136 host_pages=90003241 gc_pages=87515905 WAF=1.972364
- phaseA(test3) host_pages=18001246 gc_pages=17182540 WAF=1.954519
- phaseB(test4) host_pages=72001995 gc_pages=70333365 WAF=1.976825
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC onlinev2 — started 2026-09-18T07:41:55+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v2.ko`.
- Command: `bash script/mix-20260911.sh mixC onlinev2`; evidence `result/mix-20260911/mixC-onlinev2/`.

- Finished 2026-09-18T08:43:18+09:00; mixC onlinev2 exit=1; evidence `/home/oy/iCAT/result/mix-20260911/mixC-onlinev2-rep1-x3`; cleanup attempted.
- total host_bytes=368653238272 host_pages=90003232 gc_pages=84612578 WAF=1.940106
- phaseA(test3) host_pages=18001240 gc_pages=14511609 WAF=1.806145
- phaseB(test4) host_pages=72001992 gc_pages=70100969 WAF=1.973598
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC fixed47 — started 2026-09-18T08:43:18+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixC fixed47`; evidence `result/mix-20260911/mixC-fixed47/`.

- Finished 2026-09-18T09:44:41+09:00; mixC fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-fixed47-rep1-x3`; cleanup attempted.
- total host_bytes=368653201408 host_pages=90003223 gc_pages=69493283 WAF=1.772120
- phaseA(test3) host_pages=18001243 gc_pages=13839737 WAF=1.768821
- phaseB(test4) host_pages=72001980 gc_pages=55653546 WAF=1.772945
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC fixed50 — started 2026-09-18T09:44:41+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixC fixed50`; evidence `result/mix-20260911/mixC-fixed50/`.

- Finished 2026-09-18T10:46:05+09:00; mixC fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-fixed50-rep1-x3`; cleanup attempted.
- total host_bytes=368653484032 host_pages=90003292 gc_pages=72342345 WAF=1.803774
- phaseA(test3) host_pages=18001246 gc_pages=13886145 WAF=1.771399
- phaseB(test4) host_pages=72002046 gc_pages=58456200 WAF=1.811869
- ycsb-load 
- ycsb-run 

### mix-20260911 mixA online — started 2026-09-18T10:46:09+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 24000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixA online`; evidence `result/mix-20260911/mixA-online/`.

- Finished 2026-09-18T12:33:01+09:00; mixA online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-online-rep1-x6`; cleanup attempted.
- total host_bytes=760507162624 host_pages=185670694 gc_pages=157519216 WAF=1.848380
- phaseA(test4) host_pages=144003969 gc_pages=135936440 WAF=1.943977
- phaseB(sqlite-a) host_pages=41666725 gc_pages=21582776 WAF=1.517986
- phaseB-load host_pages=1398349 gc_pages=857852 WAF=1.613475
- phaseB-run host_pages=40268376 gc_pages=20724924 WAF=1.514670
- ycsb-load [OVERALL], Throughput(ops/sec), 24492.795036126874
- ycsb-run [OVERALL], Throughput(ops/sec), 8921.515200403252

### mix-20260911 mixA onlinev2 — started 2026-09-18T12:33:01+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 24000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v2.ko`.
- Command: `bash script/mix-20260911.sh mixA onlinev2`; evidence `result/mix-20260911/mixA-onlinev2/`.

- Finished 2026-09-18T14:07:28+09:00; mixA onlinev2 exit=1; evidence `/home/oy/iCAT/result/mix-20260911/mixA-onlinev2-rep1-x6`; cleanup attempted.
- total host_bytes=762155798528 host_pages=186073193 gc_pages=165176338 WAF=1.887696
- phaseA(test4) host_pages=144028043 gc_pages=140673324 WAF=1.976708
- phaseB(sqlite-a) host_pages=42045150 gc_pages=24503014 WAF=1.582779
- phaseB-load host_pages=1398340 gc_pages=1105627 WAF=1.790671
- phaseB-run host_pages=40646810 gc_pages=23397387 WAF=1.575627
- ycsb-load [OVERALL], Throughput(ops/sec), 24790.315250175598
- ycsb-run [OVERALL], Throughput(ops/sec), 12650.341401088563

### mix-20260911 mixA fixed47 — started 2026-09-18T14:07:28+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 24000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixA fixed47`; evidence `result/mix-20260911/mixA-fixed47/`.

- Finished 2026-09-18T15:55:24+09:00; mixA fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-fixed47-rep1-x6`; cleanup attempted.
- total host_bytes=761267073024 host_pages=185856219 gc_pages=134239928 WAF=1.722278
- phaseA(test4) host_pages=144008570 gc_pages=111375538 WAF=1.773395
- phaseB(sqlite-a) host_pages=41847649 gc_pages=22864390 WAF=1.546372
- phaseB-load host_pages=1398348 gc_pages=270199 WAF=1.193227
- phaseB-run host_pages=40449301 gc_pages=22594191 WAF=1.558581
- ycsb-load [OVERALL], Throughput(ops/sec), 26810.849457080298
- ycsb-run [OVERALL], Throughput(ops/sec), 8717.961943916624

### mix-20260911 mixA fixed50 — started 2026-09-18T15:55:24+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 24000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixA fixed50`; evidence `result/mix-20260911/mixA-fixed50/`.

- Finished 2026-09-18T17:29:46+09:00; mixA fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-fixed50-rep1-x6`; cleanup attempted.
- total host_bytes=762013675520 host_pages=186038495 gc_pages=134684650 WAF=1.723961
- phaseA(test4) host_pages=144011124 gc_pages=117209862 WAF=1.813895
- phaseB(sqlite-a) host_pages=42027371 gc_pages=17474788 WAF=1.415795
- phaseB-load host_pages=1398349 gc_pages=352608 WAF=1.252160
- phaseB-run host_pages=40629022 gc_pages=17122180 WAF=1.421427
- ycsb-load [OVERALL], Throughput(ops/sec), 22487.912746898543
- ycsb-run [OVERALL], Throughput(ops/sec), 12730.08298953269

### mix-20260911 mixC online — started 2026-09-18T17:30:04+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixC online`; evidence `result/mix-20260911/mixC-online/`.

- Finished 2026-09-18T19:31:33+09:00; mixC online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-online-rep1-x6`; cleanup attempted.
- total host_bytes=737306546176 host_pages=180006481 gc_pages=169122207 WAF=1.939534
- phaseA(test3) host_pages=36002496 gc_pages=34599625 WAF=1.961034
- phaseB(test4) host_pages=144003985 gc_pages=134522582 WAF=1.934159
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC onlinev2 — started 2026-09-18T19:31:33+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v2.ko`.
- Command: `bash script/mix-20260911.sh mixC onlinev2`; evidence `result/mix-20260911/mixC-onlinev2/`.

- Finished 2026-09-18T21:32:56+09:00; mixC onlinev2 exit=1; evidence `/home/oy/iCAT/result/mix-20260911/mixC-onlinev2-rep1-x6`; cleanup attempted.
- total host_bytes=737308585984 host_pages=180006979 gc_pages=170206457 WAF=1.945555
- phaseA(test3) host_pages=36003012 gc_pages=28770530 WAF=1.799115
- phaseB(test4) host_pages=144003967 gc_pages=141435927 WAF=1.982167
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC fixed47 — started 2026-09-18T21:32:56+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixC fixed47`; evidence `result/mix-20260911/mixC-fixed47/`.

- Finished 2026-09-18T23:34:19+09:00; mixC fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-fixed47-rep1-x6`; cleanup attempted.
- total host_bytes=737306472448 host_pages=180006463 gc_pages=138673362 WAF=1.770380
- phaseA(test3) host_pages=36002493 gc_pages=27342284 WAF=1.759455
- phaseB(test4) host_pages=144003970 gc_pages=111331078 WAF=1.773111
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC fixed50 — started 2026-09-18T23:34:19+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixC fixed50`; evidence `result/mix-20260911/mixC-fixed50/`.

- Finished 2026-09-19T01:35:44+09:00; mixC fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-fixed50-rep1-x6`; cleanup attempted.
- total host_bytes=737306640384 host_pages=180006504 gc_pages=144678132 WAF=1.803738
- phaseA(test3) host_pages=36002499 gc_pages=27356758 WAF=1.759857
- phaseB(test4) host_pages=144004005 gc_pages=117321374 WAF=1.814709
- ycsb-load 
- ycsb-run 

### mix-20260911 mixA arm00 — started 2026-09-19T01:36:07+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm00.ko`.
- Command: `bash script/mix-20260911.sh mixA arm00`; evidence `result/mix-20260911/mixA-arm00/`.

- Finished 2026-09-19T01:53:44+09:00; mixA arm00 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm00-rep1`; cleanup attempted.
- total host_bytes=131725692928 host_pages=32159593 gc_pages=36864482 WAF=2.146298
- phaseA(test4) host_pages=24015521 gc_pages=27490798 WAF=2.144710
- phaseB(sqlite-a) host_pages=8144072 gc_pages=9373684 WAF=2.150982
- phaseB-load host_pages=1398861 gc_pages=1630438 WAF=2.165547
- phaseB-run host_pages=6745211 gc_pages=7743246 WAF=2.147962
- ycsb-load [OVERALL], Throughput(ops/sec), 25635.54795983764
- ycsb-run [OVERALL], Throughput(ops/sec), 12026.494367090701

### mix-20260911 mixA arm01 — started 2026-09-19T01:53:44+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm01.ko`.
- Command: `bash script/mix-20260911.sh mixA arm01`; evidence `result/mix-20260911/mixA-arm01/`.

- Finished 2026-09-19T02:11:20+09:00; mixA arm01 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm01-rep1`; cleanup attempted.
- total host_bytes=131605438464 host_pages=32130234 gc_pages=39467550 WAF=2.228362
- phaseA(test4) host_pages=24000664 gc_pages=29819094 WAF=2.242428
- phaseB(sqlite-a) host_pages=8129570 gc_pages=9648456 WAF=2.186835
- phaseB-load host_pages=1398349 gc_pages=1696213 WAF=2.213011
- phaseB-run host_pages=6731221 gc_pages=7952243 WAF=2.181397
- ycsb-load [OVERALL], Throughput(ops/sec), 23458.576064432888
- ycsb-run [OVERALL], Throughput(ops/sec), 12217.470983506415

### mix-20260911 mixA arm02 — started 2026-09-19T02:11:21+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm02.ko`.
- Command: `bash script/mix-20260911.sh mixA arm02`; evidence `result/mix-20260911/mixA-arm02/`.

- Finished 2026-09-19T02:30:58+09:00; mixA arm02 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm02-rep1`; cleanup attempted.
- total host_bytes=131374399488 host_pages=32073828 gc_pages=37858044 WAF=2.180341
- phaseA(test4) host_pages=24015498 gc_pages=29840770 WAF=2.242563
- phaseB(sqlite-a) host_pages=8058330 gc_pages=8017274 WAF=1.994905
- phaseB-load host_pages=1398349 gc_pages=1693500 WAF=2.211071
- phaseB-run host_pages=6659981 gc_pages=6323774 WAF=1.949518
- ycsb-load [OVERALL], Throughput(ops/sec), 25327.14225411566
- ycsb-run [OVERALL], Throughput(ops/sec), 8768.680028673583

### mix-20260911 mixA arm03 — started 2026-09-19T02:30:59+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm03.ko`.
- Command: `bash script/mix-20260911.sh mixA arm03`; evidence `result/mix-20260911/mixA-arm03/`.

- Finished 2026-09-19T02:50:46+09:00; mixA arm03 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm03-rep1`; cleanup attempted.
- total host_bytes=131553464320 host_pages=32117545 gc_pages=40347865 WAF=2.256256
- phaseA(test4) host_pages=24023703 gc_pages=29776509 WAF=2.239464
- phaseB(sqlite-a) host_pages=8093842 gc_pages=10571356 WAF=2.306099
- phaseB-load host_pages=1398349 gc_pages=1688512 WAF=2.207504
- phaseB-run host_pages=6695493 gc_pages=8882844 WAF=2.326690
- ycsb-load [OVERALL], Throughput(ops/sec), 24394.21044072207
- ycsb-run [OVERALL], Throughput(ops/sec), 8544.744554861532

### mix-20260911 mixA arm04 — started 2026-09-19T02:50:47+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm04.ko`.
- Command: `bash script/mix-20260911.sh mixA arm04`; evidence `result/mix-20260911/mixA-arm04/`.

- Finished 2026-09-19T03:08:31+09:00; mixA arm04 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm04-rep1`; cleanup attempted.
- total host_bytes=131711086592 host_pages=32156027 gc_pages=41984221 WAF=2.305641
- phaseA(test4) host_pages=24000658 gc_pages=30311950 WAF=2.262963
- phaseB(sqlite-a) host_pages=8155369 gc_pages=11672271 WAF=2.431238
- phaseB-load host_pages=1398349 gc_pages=1695479 WAF=2.212486
- phaseB-run host_pages=6757020 gc_pages=9976792 WAF=2.476508
- ycsb-load [OVERALL], Throughput(ops/sec), 24537.870112874203
- ycsb-run [OVERALL], Throughput(ops/sec), 11830.049508757194

### mix-20260911 mixA arm05 — started 2026-09-19T03:08:32+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm05.ko`.
- Command: `bash script/mix-20260911.sh mixA arm05`; evidence `result/mix-20260911/mixA-arm05/`.

- Finished 2026-09-19T03:28:20+09:00; mixA arm05 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm05-rep1`; cleanup attempted.
- total host_bytes=131451154432 host_pages=32092567 gc_pages=40094735 WAF=2.249346
- phaseA(test4) host_pages=24000658 gc_pages=30239130 WAF=2.259929
- phaseB(sqlite-a) host_pages=8091909 gc_pages=9855605 WAF=2.217958
- phaseB-load host_pages=1398349 gc_pages=1691317 WAF=2.209510
- phaseB-run host_pages=6693560 gc_pages=8164288 WAF=2.219723
- ycsb-load [OVERALL], Throughput(ops/sec), 23071.59886180112
- ycsb-run [OVERALL], Throughput(ops/sec), 8585.68080155916

### mix-20260911 mixA arm06 — started 2026-09-19T03:28:20+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm06.ko`.
- Command: `bash script/mix-20260911.sh mixA arm06`; evidence `result/mix-20260911/mixA-arm06/`.

- Finished 2026-09-19T03:46:26+09:00; mixA arm06 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm06-rep1`; cleanup attempted.
- total host_bytes=131972870144 host_pages=32219939 gc_pages=45347716 WAF=2.407443
- phaseA(test4) host_pages=24000673 gc_pages=30346254 WAF=2.264392
- phaseB(sqlite-a) host_pages=8219266 gc_pages=15001462 WAF=2.825158
- phaseB-load host_pages=1398349 gc_pages=1681740 WAF=2.202661
- phaseB-run host_pages=6820917 gc_pages=13319722 WAF=2.952776
- ycsb-load [OVERALL], Throughput(ops/sec), 24433.946896888745
- ycsb-run [OVERALL], Throughput(ops/sec), 11155.982953658047

### mix-20260911 mixA arm07 — started 2026-09-19T03:46:27+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm07.ko`.
- Command: `bash script/mix-20260911.sh mixA arm07`; evidence `result/mix-20260911/mixA-arm07/`.

- Finished 2026-09-19T04:06:32+09:00; mixA arm07 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm07-rep1`; cleanup attempted.
- total host_bytes=131664695296 host_pages=32144701 gc_pages=43252820 WAF=2.345566
- phaseA(test4) host_pages=24017032 gc_pages=30157127 WAF=2.255656
- phaseB(sqlite-a) host_pages=8127669 gc_pages=13095693 WAF=2.611248
- phaseB-load host_pages=1398351 gc_pages=1691610 WAF=2.209718
- phaseB-run host_pages=6729318 gc_pages=11404083 WAF=2.694686
- ycsb-load [OVERALL], Throughput(ops/sec), 24670.03823855927
- ycsb-run [OVERALL], Throughput(ops/sec), 8248.545162846904

### mix-20260911 mixA arm08 — started 2026-09-19T04:06:32+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm08.ko`.
- Command: `bash script/mix-20260911.sh mixA arm08`; evidence `result/mix-20260911/mixA-arm08/`.

- Finished 2026-09-19T04:26:37+09:00; mixA arm08 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm08-rep1`; cleanup attempted.
- total host_bytes=131634823168 host_pages=32137408 gc_pages=43272191 WAF=2.346474
- phaseA(test4) host_pages=24000658 gc_pages=30301717 WAF=2.262537
- phaseB(sqlite-a) host_pages=8136750 gc_pages=12970474 WAF=2.594061
- phaseB-load host_pages=1398345 gc_pages=1681753 WAF=2.202674
- phaseB-run host_pages=6738405 gc_pages=11288721 WAF=2.675281
- ycsb-load [OVERALL], Throughput(ops/sec), 27084.367805714803
- ycsb-run [OVERALL], Throughput(ops/sec), 8226.102657648116

### mix-20260911 mixA arm09 — started 2026-09-19T04:26:38+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm09.ko`.
- Command: `bash script/mix-20260911.sh mixA arm09`; evidence `result/mix-20260911/mixA-arm09/`.

- Finished 2026-09-19T04:46:57+09:00; mixA arm09 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm09-rep1`; cleanup attempted.
- total host_bytes=131746893824 host_pages=32164769 gc_pages=45930965 WAF=2.427990
- phaseA(test4) host_pages=24000664 gc_pages=30253867 WAF=2.260543
- phaseB(sqlite-a) host_pages=8164105 gc_pages=15677098 WAF=2.920247
- phaseB-load host_pages=1398351 gc_pages=1695439 WAF=2.212456
- phaseB-run host_pages=6765754 gc_pages=13981659 WAF=3.066534
- ycsb-load [OVERALL], Throughput(ops/sec), 26585.138907350793
- ycsb-run [OVERALL], Throughput(ops/sec), 8067.44383042233

### mix-20260911 mixA arm10 — started 2026-09-19T04:46:57+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm10.ko`.
- Command: `bash script/mix-20260911.sh mixA arm10`; evidence `result/mix-20260911/mixA-arm10/`.

- Finished 2026-09-19T05:07:17+09:00; mixA arm10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm10-rep1`; cleanup attempted.
- total host_bytes=131816460288 host_pages=32181753 gc_pages=45472926 WAF=2.413003
- phaseA(test4) host_pages=24023751 gc_pages=29832424 WAF=2.241789
- phaseB(sqlite-a) host_pages=8158002 gc_pages=15640502 WAF=2.917198
- phaseB-load host_pages=1398349 gc_pages=1689367 WAF=2.208115
- phaseB-run host_pages=6759653 gc_pages=13951135 WAF=3.063883
- ycsb-load [OVERALL], Throughput(ops/sec), 20490.40366095212
- ycsb-run [OVERALL], Throughput(ops/sec), 8102.6771245219425

### mix-20260911 mixA arm11 — started 2026-09-19T05:07:18+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm11.ko`.
- Command: `bash script/mix-20260911.sh mixA arm11`; evidence `result/mix-20260911/mixA-arm11/`.

- Finished 2026-09-19T05:27:37+09:00; mixA arm11 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm11-rep1`; cleanup attempted.
- total host_bytes=131747893248 host_pages=32165013 gc_pages=45983365 WAF=2.429608
- phaseA(test4) host_pages=24000658 gc_pages=30295234 WAF=2.262267
- phaseB(sqlite-a) host_pages=8164355 gc_pages=15688131 WAF=2.921540
- phaseB-load host_pages=1398349 gc_pages=1682630 WAF=2.203298
- phaseB-run host_pages=6766006 gc_pages=14005501 WAF=3.069981
- ycsb-load [OVERALL], Throughput(ops/sec), 22760.896779333107
- ycsb-run [OVERALL], Throughput(ops/sec), 8052.1132771295825

### mix-20260911 mixA arm12 — started 2026-09-19T05:27:38+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm12.ko`.
- Command: `bash script/mix-20260911.sh mixA arm12`; evidence `result/mix-20260911/mixA-arm12/`.

- Finished 2026-09-19T05:47:58+09:00; mixA arm12 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm12-rep1`; cleanup attempted.
- total host_bytes=131789852672 host_pages=32175257 gc_pages=46301030 WAF=2.439026
- phaseA(test4) host_pages=24000670 gc_pages=30566611 WAF=2.273573
- phaseB(sqlite-a) host_pages=8174587 gc_pages=15734419 WAF=2.924797
- phaseB-load host_pages=1398349 gc_pages=1684317 WAF=2.204504
- phaseB-run host_pages=6776238 gc_pages=14050102 WAF=3.073437
- ycsb-load [OVERALL], Throughput(ops/sec), 25558.016697904244
- ycsb-run [OVERALL], Throughput(ops/sec), 7989.533710838801

### mix-20260911 mixA arm13 — started 2026-09-19T05:47:58+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm13.ko`.
- Command: `bash script/mix-20260911.sh mixA arm13`; evidence `result/mix-20260911/mixA-arm13/`.

- Finished 2026-09-19T06:08:13+09:00; mixA arm13 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm13-rep1`; cleanup attempted.
- total host_bytes=131751022592 host_pages=32165777 gc_pages=46029177 WAF=2.430998
- phaseA(test4) host_pages=24000658 gc_pages=30358276 WAF=2.264893
- phaseB(sqlite-a) host_pages=8165119 gc_pages=15670901 WAF=2.919250
- phaseB-load host_pages=1398351 gc_pages=1684776 WAF=2.204831
- phaseB-run host_pages=6766768 gc_pages=13986125 WAF=3.066884
- ycsb-load [OVERALL], Throughput(ops/sec), 25278.058645096058
- ycsb-run [OVERALL], Throughput(ops/sec), 8056.621938987202

### mix-20260911 mixA arm14 — started 2026-09-19T06:08:14+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm14.ko`.
- Command: `bash script/mix-20260911.sh mixA arm14`; evidence `result/mix-20260911/mixA-arm14/`.

- Finished 2026-09-19T06:28:40+09:00; mixA arm14 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm14-rep1`; cleanup attempted.
- total host_bytes=131878068224 host_pages=32196794 gc_pages=44946885 WAF=2.396005
- phaseA(test4) host_pages=24026784 gc_pages=29241801 WAF=2.217050
- phaseB(sqlite-a) host_pages=8170010 gc_pages=15705084 WAF=2.922285
- phaseB-load host_pages=1398351 gc_pages=1691837 WAF=2.209880
- phaseB-run host_pages=6771659 gc_pages=14013247 WAF=3.069396
- ycsb-load [OVERALL], Throughput(ops/sec), 24156.534342539657
- ycsb-run [OVERALL], Throughput(ops/sec), 8007.815628052979

### mix-20260911 mixA arm15 — started 2026-09-19T06:28:40+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm15.ko`.
- Command: `bash script/mix-20260911.sh mixA arm15`; evidence `result/mix-20260911/mixA-arm15/`.

- Finished 2026-09-19T06:48:11+09:00; mixA arm15 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm15-rep1`; cleanup attempted.
- total host_bytes=131217170432 host_pages=32035442 gc_pages=27205574 WAF=1.849234
- phaseA(test4) host_pages=24000667 gc_pages=21047269 WAF=1.876945
- phaseB(sqlite-a) host_pages=8034775 gc_pages=6158305 WAF=1.766456
- phaseB-load host_pages=1398349 gc_pages=1103301 WAF=1.789003
- phaseB-run host_pages=6636426 gc_pages=5055004 WAF=1.761706
- ycsb-load [OVERALL], Throughput(ops/sec), 25076.27366573327
- ycsb-run [OVERALL], Throughput(ops/sec), 8915.496693465164

### mix-20260911 mixA arm16 — started 2026-09-19T06:48:12+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm16.ko`.
- Command: `bash script/mix-20260911.sh mixA arm16`; evidence `result/mix-20260911/mixA-arm16/`.

- Finished 2026-09-19T07:05:34+09:00; mixA arm16 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm16-rep1`; cleanup attempted.
- total host_bytes=131467460608 host_pages=32096548 gc_pages=24794626 WAF=1.772501
- phaseA(test4) host_pages=24000670 gc_pages=19988067 WAF=1.832813
- phaseB(sqlite-a) host_pages=8095878 gc_pages=4806559 WAF=1.593704
- phaseB-load host_pages=1398351 gc_pages=832407 WAF=1.595278
- phaseB-run host_pages=6697527 gc_pages=3974152 WAF=1.593376
- ycsb-load [OVERALL], Throughput(ops/sec), 26677.33760170735
- ycsb-run [OVERALL], Throughput(ops/sec), 12613.999016108077

### mix-20260911 mixA arm17 — started 2026-09-19T07:05:34+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm17.ko`.
- Command: `bash script/mix-20260911.sh mixA arm17`; evidence `result/mix-20260911/mixA-arm17/`.

- Finished 2026-09-19T07:24:56+09:00; mixA arm17 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm17-rep1`; cleanup attempted.
- total host_bytes=131176546304 host_pages=32025524 gc_pages=23852586 WAF=1.744799
- phaseA(test4) host_pages=24017032 gc_pages=20882657 WAF=1.869494
- phaseB(sqlite-a) host_pages=8008492 gc_pages=2969929 WAF=1.370847
- phaseB-load host_pages=1398349 gc_pages=407944 WAF=1.291733
- phaseB-run host_pages=6610143 gc_pages=2561985 WAF=1.387584
- ycsb-load [OVERALL], Throughput(ops/sec), 22353.86162959651
- ycsb-run [OVERALL], Throughput(ops/sec), 9144.257520580295

### mix-20260911 mixA arm18 — started 2026-09-19T07:24:56+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm18.ko`.
- Command: `bash script/mix-20260911.sh mixA arm18`; evidence `result/mix-20260911/mixA-arm18/`.

- Finished 2026-09-19T07:44:38+09:00; mixA arm18 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm18-rep1`; cleanup attempted.
- total host_bytes=131454169088 host_pages=32093303 gc_pages=29765667 WAF=1.927473
- phaseA(test4) host_pages=24021130 gc_pages=23425343 WAF=1.975197
- phaseB(sqlite-a) host_pages=8072173 gc_pages=6340324 WAF=1.785454
- phaseB-load host_pages=1398349 gc_pages=1243733 WAF=1.889430
- phaseB-run host_pages=6673824 gc_pages=5096591 WAF=1.763669
- ycsb-load [OVERALL], Throughput(ops/sec), 23673.308344841193
- ycsb-run [OVERALL], Throughput(ops/sec), 8665.17336845617

### mix-20260911 mixA arm19 — started 2026-09-19T07:44:38+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm19.ko`.
- Command: `bash script/mix-20260911.sh mixA arm19`; evidence `result/mix-20260911/mixA-arm19/`.

- Finished 2026-09-19T08:01:57+09:00; mixA arm19 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm19-rep1`; cleanup attempted.
- total host_bytes=131401834496 host_pages=32080526 gc_pages=27629903 WAF=1.861267
- phaseA(test4) host_pages=24000658 gc_pages=22448331 WAF=1.935321
- phaseB(sqlite-a) host_pages=8079868 gc_pages=5181572 WAF=1.641294
- phaseB-load host_pages=1398351 gc_pages=946270 WAF=1.676704
- phaseB-run host_pages=6681517 gc_pages=4235302 WAF=1.633883
- ycsb-load [OVERALL], Throughput(ops/sec), 23960.704444710675
- ycsb-run [OVERALL], Throughput(ops/sec), 12850.78630748719

### mix-20260911 mixA arm20 — started 2026-09-19T08:02:14+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm20.ko`.
- Command: `bash script/mix-20260911.sh mixA arm20`; evidence `result/mix-20260911/mixA-arm20/`.

- Finished 2026-09-19T08:21:32+09:00; mixA arm20 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm20-rep1`; cleanup attempted.
- total host_bytes=131142742016 host_pages=32017271 gc_pages=26536337 WAF=1.828813
- phaseA(test4) host_pages=24000661 gc_pages=22386345 WAF=1.932739
- phaseB(sqlite-a) host_pages=8016610 gc_pages=4149992 WAF=1.517674
- phaseB-load host_pages=1398349 gc_pages=662294 WAF=1.473626
- phaseB-run host_pages=6618261 gc_pages=3487698 WAF=1.526981
- ycsb-load [OVERALL], Throughput(ops/sec), 25860.954269212532
- ycsb-run [OVERALL], Throughput(ops/sec), 9088.285881120677

### mix-20260911 mixA arm21 — started 2026-09-19T08:21:33+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm21.ko`.
- Command: `bash script/mix-20260911.sh mixA arm21`; evidence `result/mix-20260911/mixA-arm21/`.

- Finished 2026-09-19T08:39:04+09:00; mixA arm21 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm21-rep1`; cleanup attempted.
- total host_bytes=131550285824 host_pages=32116769 gc_pages=35479050 WAF=2.104689
- phaseA(test4) host_pages=24000658 gc_pages=27422750 WAF=2.142583
- phaseB(sqlite-a) host_pages=8116111 gc_pages=8056300 WAF=1.992631
- phaseB-load host_pages=1398349 gc_pages=1516544 WAF=2.084525
- phaseB-run host_pages=6717762 gc_pages=6539756 WAF=1.973502
- ycsb-load [OVERALL], Throughput(ops/sec), 24022.100332305723
- ycsb-run [OVERALL], Throughput(ops/sec), 12345.031279223003

### mix-20260911 mixA arm22 — started 2026-09-19T08:39:05+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm22.ko`.
- Command: `bash script/mix-20260911.sh mixA arm22`; evidence `result/mix-20260911/mixA-arm22/`.

- Finished 2026-09-19T08:58:37+09:00; mixA arm22 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm22-rep1`; cleanup attempted.
- total host_bytes=131368202240 host_pages=32072315 gc_pages=32142191 WAF=2.002179
- phaseA(test4) host_pages=24025253 gc_pages=26025653 WAF=2.083262
- phaseB(sqlite-a) host_pages=8047062 gc_pages=6116538 WAF=1.760096
- phaseB-load host_pages=1398349 gc_pages=1356385 WAF=1.969990
- phaseB-run host_pages=6648713 gc_pages=4760153 WAF=1.715951
- ycsb-load [OVERALL], Throughput(ops/sec), 22593.764121102577
- ycsb-run [OVERALL], Throughput(ops/sec), 8879.594912880075

### mix-20260911 mixA arm23 — started 2026-09-19T08:58:38+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm23.ko`.
- Command: `bash script/mix-20260911.sh mixA arm23`; evidence `result/mix-20260911/mixA-arm23/`.

- Finished 2026-09-19T09:18:12+09:00; mixA arm23 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm23-rep1`; cleanup attempted.
- total host_bytes=131289796608 host_pages=32053173 gc_pages=30958360 WAF=1.965844
- phaseA(test4) host_pages=24025253 gc_pages=25846600 WAF=2.075810
- phaseB(sqlite-a) host_pages=8027920 gc_pages=5111760 WAF=1.636748
- phaseB-load host_pages=1398349 gc_pages=1092625 WAF=1.781368
- phaseB-run host_pages=6629571 gc_pages=4019135 WAF=1.606244
- ycsb-load [OVERALL], Throughput(ops/sec), 22481.17201843456
- ycsb-run [OVERALL], Throughput(ops/sec), 9008.52206187053

### mix-20260911 mixA arm24 — started 2026-09-19T09:18:12+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm24.ko`.
- Command: `bash script/mix-20260911.sh mixA arm24`; evidence `result/mix-20260911/mixA-arm24/`.

- Finished 2026-09-19T09:35:53+09:00; mixA arm24 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm24-rep1`; cleanup attempted.
- total host_bytes=131628453888 host_pages=32135853 gc_pages=38176547 WAF=2.187974
- phaseA(test4) host_pages=24000664 gc_pages=28885045 WAF=2.203510
- phaseB(sqlite-a) host_pages=8135189 gc_pages=9291502 WAF=2.142137
- phaseB-load host_pages=1398349 gc_pages=1693844 WAF=2.211317
- phaseB-run host_pages=6736840 gc_pages=7597658 WAF=2.127778
- ycsb-load [OVERALL], Throughput(ops/sec), 23154.401265773937
- ycsb-run [OVERALL], Throughput(ops/sec), 12141.447867658218

### mix-20260911 mixA arm25 — started 2026-09-19T09:35:54+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm25.ko`.
- Command: `bash script/mix-20260911.sh mixA arm25`; evidence `result/mix-20260911/mixA-arm25/`.

- Finished 2026-09-19T09:53:28+09:00; mixA arm25 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm25-rep1`; cleanup attempted.
- total host_bytes=131582353408 host_pages=32124598 gc_pages=37201118 WAF=2.158026
- phaseA(test4) host_pages=24000658 gc_pages=28919832 WAF=2.204960
- phaseB(sqlite-a) host_pages=8123940 gc_pages=8281286 WAF=2.019368
- phaseB-load host_pages=1398349 gc_pages=1705035 WAF=2.219320
- phaseB-run host_pages=6725591 gc_pages=6576251 WAF=1.977795
- ycsb-load [OVERALL], Throughput(ops/sec), 24659.89889441453
- ycsb-run [OVERALL], Throughput(ops/sec), 12283.654141433994

### mix-20260911 mixA arm26 — started 2026-09-19T09:53:28+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm26.ko`.
- Command: `bash script/mix-20260911.sh mixA arm26`; evidence `result/mix-20260911/mixA-arm26/`.

- Finished 2026-09-19T10:10:54+09:00; mixA arm26 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm26-rep1`; cleanup attempted.
- total host_bytes=131489271808 host_pages=32101873 gc_pages=36588228 WAF=2.139754
- phaseA(test4) host_pages=24000661 gc_pages=28950030 WAF=2.206218
- phaseB(sqlite-a) host_pages=8101212 gc_pages=7638198 WAF=1.942846
- phaseB-load host_pages=1398351 gc_pages=1712894 WAF=2.224939
- phaseB-run host_pages=6702861 gc_pages=5925304 WAF=1.883996
- ycsb-load [OVERALL], Throughput(ops/sec), 23641.593443398084
- ycsb-run [OVERALL], Throughput(ops/sec), 12598.702963529904

### mix-20260911 mixA arm27 — started 2026-09-19T10:10:55+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm27.ko`.
- Command: `bash script/mix-20260911.sh mixA arm27`; evidence `result/mix-20260911/mixA-arm27/`.

- Finished 2026-09-19T10:30:59+09:00; mixA arm27 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm27-rep1`; cleanup attempted.
- total host_bytes=131510542336 host_pages=32107066 gc_pages=38704633 WAF=2.205486
- phaseA(test4) host_pages=24025265 gc_pages=29092974 WAF=2.210932
- phaseB(sqlite-a) host_pages=8081801 gc_pages=9611659 WAF=2.189297
- phaseB-load host_pages=1398349 gc_pages=1694591 WAF=2.211851
- phaseB-run host_pages=6683452 gc_pages=7917068 WAF=2.184578
- ycsb-load [OVERALL], Throughput(ops/sec), 22854.530910753056
- ycsb-run [OVERALL], Throughput(ops/sec), 8574.123295892994

### mix-20260911 mixA arm28 — started 2026-09-19T10:31:00+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm28.ko`.
- Command: `bash script/mix-20260911.sh mixA arm28`; evidence `result/mix-20260911/mixA-arm28/`.

- Finished 2026-09-19T10:48:41+09:00; mixA arm28 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm28-rep1`; cleanup attempted.
- total host_bytes=131743375360 host_pages=32163910 gc_pages=39517062 WAF=2.228615
- phaseA(test4) host_pages=24019600 gc_pages=29557320 WAF=2.230550
- phaseB(sqlite-a) host_pages=8144310 gc_pages=9959742 WAF=2.222908
- phaseB-load host_pages=1398349 gc_pages=1691835 WAF=2.209880
- phaseB-run host_pages=6745961 gc_pages=8267907 WAF=2.225608
- ycsb-load [OVERALL], Throughput(ops/sec), 22907.75809407453
- ycsb-run [OVERALL], Throughput(ops/sec), 12031.23308107848

### mix-20260911 mixA arm29 — started 2026-09-19T10:48:41+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm29.ko`.
- Command: `bash script/mix-20260911.sh mixA arm29`; evidence `result/mix-20260911/mixA-arm29/`.

- Finished 2026-09-19T11:08:28+09:00; mixA arm29 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm29-rep1`; cleanup attempted.
- total host_bytes=131315666944 host_pages=32059489 gc_pages=37724307 WAF=2.176697
- phaseA(test4) host_pages=24000661 gc_pages=29477274 WAF=2.228186
- phaseB(sqlite-a) host_pages=8058828 gc_pages=8247033 WAF=2.023354
- phaseB-load host_pages=1398357 gc_pages=1678536 WAF=2.200363
- phaseB-run host_pages=6660471 gc_pages=6568497 WAF=1.986191
- ycsb-load [OVERALL], Throughput(ops/sec), 23493.48055914484
- ycsb-run [OVERALL], Throughput(ops/sec), 8744.774996939328

### mix-20260911 mixA arm30 — started 2026-09-19T11:08:29+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm30.ko`.
- Command: `bash script/mix-20260911.sh mixA arm30`; evidence `result/mix-20260911/mixA-arm30/`.

- Finished 2026-09-19T11:25:59+09:00; mixA arm30 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm30-rep1`; cleanup attempted.
- total host_bytes=131546894336 host_pages=32115941 gc_pages=26000819 WAF=1.809592
- phaseA(test4) host_pages=24000664 gc_pages=20136293 WAF=1.838989
- phaseB(sqlite-a) host_pages=8115277 gc_pages=5864526 WAF=1.722653
- phaseB-load host_pages=1398349 gc_pages=1025996 WAF=1.733720
- phaseB-run host_pages=6716928 gc_pages=4838530 WAF=1.720349
- ycsb-load [OVERALL], Throughput(ops/sec), 23012.311586698885
- ycsb-run [OVERALL], Throughput(ops/sec), 12443.692292376994

### mix-20260911 mixA arm31 — started 2026-09-19T11:26:00+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm31.ko`.
- Command: `bash script/mix-20260911.sh mixA arm31`; evidence `result/mix-20260911/mixA-arm31/`.

- Finished 2026-09-19T11:43:22+09:00; mixA arm31 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm31-rep1`; cleanup attempted.
- total host_bytes=131472171008 host_pages=32097698 gc_pages=23745570 WAF=1.739790
- phaseA(test4) host_pages=24000658 gc_pages=19117056 WAF=1.796522
- phaseB(sqlite-a) host_pages=8097040 gc_pages=4628514 WAF=1.571630
- phaseB-load host_pages=1398351 gc_pages=742996 WAF=1.531337
- phaseB-run host_pages=6698689 gc_pages=3885518 WAF=1.580042
- ycsb-load [OVERALL], Throughput(ops/sec), 22873.699058366055
- ycsb-run [OVERALL], Throughput(ops/sec), 12721.59427019394

### mix-20260911 mixA arm32 — started 2026-09-19T11:43:23+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm32.ko`.
- Command: `bash script/mix-20260911.sh mixA arm32`; evidence `result/mix-20260911/mixA-arm32/`.

- Finished 2026-09-19T12:01:05+09:00; mixA arm32 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm32-rep1`; cleanup attempted.
- total host_bytes=131504447488 host_pages=32105578 gc_pages=23120824 WAF=1.720150
- phaseA(test4) host_pages=24013962 gc_pages=19072372 WAF=1.794220
- phaseB(sqlite-a) host_pages=8091616 gc_pages=4048452 WAF=1.500327
- phaseB-load host_pages=1398345 gc_pages=467112 WAF=1.334046
- phaseB-run host_pages=6693271 gc_pages=3581340 WAF=1.535066
- ycsb-load [OVERALL], Throughput(ops/sec), 21957.913998170174
- ycsb-run [OVERALL], Throughput(ops/sec), 12658.428139685755

### mix-20260911 mixA arm33 — started 2026-09-19T12:01:05+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm33.ko`.
- Command: `bash script/mix-20260911.sh mixA arm33`; evidence `result/mix-20260911/mixA-arm33/`.

- Finished 2026-09-19T12:20:45+09:00; mixA arm33 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm33-rep1`; cleanup attempted.
- total host_bytes=131306348544 host_pages=32057214 gc_pages=28129919 WAF=1.877491
- phaseA(test4) host_pages=24000661 gc_pages=21906526 WAF=1.912747
- phaseB(sqlite-a) host_pages=8056553 gc_pages=6223393 WAF=1.772463
- phaseB-load host_pages=1398349 gc_pages=1199179 WAF=1.857568
- phaseB-run host_pages=6658204 gc_pages=5024214 WAF=1.754590
- ycsb-load [OVERALL], Throughput(ops/sec), 24049.06008256844
- ycsb-run [OVERALL], Throughput(ops/sec), 8773.488273136238

### mix-20260911 mixA arm34 — started 2026-09-19T12:20:46+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm34.ko`.
- Command: `bash script/mix-20260911.sh mixA arm34`; evidence `result/mix-20260911/mixA-arm34/`.

- Finished 2026-09-19T12:38:10+09:00; mixA arm34 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm34-rep1`; cleanup attempted.
- total host_bytes=131578421248 host_pages=32123638 gc_pages=25066929 WAF=1.780327
- phaseA(test4) host_pages=24025250 gc_pages=20130379 WAF=1.837884
- phaseB(sqlite-a) host_pages=8098388 gc_pages=4936550 WAF=1.609572
- phaseB-load host_pages=1398352 gc_pages=932589 WAF=1.666920
- phaseB-run host_pages=6700036 gc_pages=4003961 WAF=1.597603
- ycsb-load [OVERALL], Throughput(ops/sec), 22983.222247759135
- ycsb-run [OVERALL], Throughput(ops/sec), 12679.614666510284

### mix-20260911 mixA arm35 — started 2026-09-19T12:38:11+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm35.ko`.
- Command: `bash script/mix-20260911.sh mixA arm35`; evidence `result/mix-20260911/mixA-arm35/`.

- Finished 2026-09-19T12:55:31+09:00; mixA arm35 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm35-rep1`; cleanup attempted.
- total host_bytes=131465547776 host_pages=32096081 gc_pages=24357636 WAF=1.758898
- phaseA(test4) host_pages=24000661 gc_pages=20274429 WAF=1.844745
- phaseB(sqlite-a) host_pages=8095420 gc_pages=4083207 WAF=1.504385
- phaseB-load host_pages=1398345 gc_pages=547326 WAF=1.391410
- phaseB-run host_pages=6697075 gc_pages=3535881 WAF=1.527974
- ycsb-load [OVERALL], Throughput(ops/sec), 24733.0887505668
- ycsb-run [OVERALL], Throughput(ops/sec), 12761.73521313693

### mix-20260911 mixA arm36 — started 2026-09-19T12:55:32+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm36.ko`.
- Command: `bash script/mix-20260911.sh mixA arm36`; evidence `result/mix-20260911/mixA-arm36/`.

- Finished 2026-09-19T13:15:06+09:00; mixA arm36 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm36-rep1`; cleanup attempted.
- total host_bytes=131291660288 host_pages=32053628 gc_pages=31887471 WAF=1.994816
- phaseA(test4) host_pages=24000664 gc_pages=25022373 WAF=2.042570
- phaseB(sqlite-a) host_pages=8052964 gc_pages=6865098 WAF=1.852493
- phaseB-load host_pages=1398349 gc_pages=1378804 WAF=1.986023
- phaseB-run host_pages=6654615 gc_pages=5486294 WAF=1.824434
- ycsb-load [OVERALL], Throughput(ops/sec), 21758.05047867711
- ycsb-run [OVERALL], Throughput(ops/sec), 8872.661776351251

### mix-20260911 mixA arm37 — started 2026-09-19T13:15:06+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm37.ko`.
- Command: `bash script/mix-20260911.sh mixA arm37`; evidence `result/mix-20260911/mixA-arm37/`.

- Finished 2026-09-19T13:32:37+09:00; mixA arm37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm37-rep1`; cleanup attempted.
- total host_bytes=131516809216 host_pages=32108596 gc_pages=29150147 WAF=1.907861
- phaseA(test4) host_pages=24000658 gc_pages=23356171 WAF=1.973147
- phaseB(sqlite-a) host_pages=8107938 gc_pages=5793976 WAF=1.714605
- phaseB-load host_pages=1398348 gc_pages=1206089 WAF=1.862510
- phaseB-run host_pages=6709590 gc_pages=4587887 WAF=1.683781
- ycsb-load [OVERALL], Throughput(ops/sec), 23159.763770409543
- ycsb-run [OVERALL], Throughput(ops/sec), 12418.542125247206

### mix-20260911 mixA arm38 — started 2026-09-19T13:32:37+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm38.ko`.
- Command: `bash script/mix-20260911.sh mixA arm38`; evidence `result/mix-20260911/mixA-arm38/`.

- Finished 2026-09-19T13:52:07+09:00; mixA arm38 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm38-rep1`; cleanup attempted.
- total host_bytes=131229085696 host_pages=32038351 gc_pages=26875027 WAF=1.838839
- phaseA(test4) host_pages=24000658 gc_pages=22301364 WAF=1.929198
- phaseB(sqlite-a) host_pages=8037693 gc_pages=4573663 WAF=1.569027
- phaseB-load host_pages=1398349 gc_pages=854472 WAF=1.611058
- phaseB-run host_pages=6639344 gc_pages=3719191 WAF=1.560174
- ycsb-load [OVERALL], Throughput(ops/sec), 26200.873362445414
- ycsb-run [OVERALL], Throughput(ops/sec), 8972.512707321122

### mix-20260911 mixA arm39 — started 2026-09-19T13:52:07+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm39.ko`.
- Command: `bash script/mix-20260911.sh mixA arm39`; evidence `result/mix-20260911/mixA-arm39/`.

- Finished 2026-09-19T14:11:50+09:00; mixA arm39 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm39-rep1`; cleanup attempted.
- total host_bytes=131389612032 host_pages=32077542 gc_pages=35917691 WAF=2.119715
- phaseA(test4) host_pages=24000658 gc_pages=28052210 WAF=2.168810
- phaseB(sqlite-a) host_pages=8076884 gc_pages=7865481 WAF=1.973826
- phaseB-load host_pages=1398349 gc_pages=1581874 WAF=2.131244
- phaseB-run host_pages=6678535 gc_pages=6283607 WAF=1.940866
- ycsb-load [OVERALL], Throughput(ops/sec), 24564.994882292733
- ycsb-run [OVERALL], Throughput(ops/sec), 8634.05010339275

### mix-20260911 mixA arm40 — started 2026-09-19T14:12:08+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm40.ko`.
- Command: `bash script/mix-20260911.sh mixA arm40`; evidence `result/mix-20260911/mixA-arm40/`.

- Finished 2026-09-19T14:29:44+09:00; mixA arm40 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm40-rep1`; cleanup attempted.
- total host_bytes=131590074368 host_pages=32126483 gc_pages=34527688 WAF=2.074742
- phaseA(test4) host_pages=24000679 gc_pages=27293990 WAF=2.137217
- phaseB(sqlite-a) host_pages=8125804 gc_pages=7233698 WAF=1.890213
- phaseB-load host_pages=1398351 gc_pages=1493313 WAF=2.067910
- phaseB-run host_pages=6727453 gc_pages=5740385 WAF=1.853278
- ycsb-load [OVERALL], Throughput(ops/sec), 23086.69052291354
- ycsb-run [OVERALL], Throughput(ops/sec), 12275.021864882698

### mix-20260911 mixA arm41 — started 2026-09-19T14:29:45+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm41.ko`.
- Command: `bash script/mix-20260911.sh mixA arm41`; evidence `result/mix-20260911/mixA-arm41/`.

- Finished 2026-09-19T14:49:22+09:00; mixA arm41 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm41-rep1`; cleanup attempted.
- total host_bytes=131299078144 host_pages=32055439 gc_pages=32384358 WAF=2.010261
- phaseA(test4) host_pages=24000664 gc_pages=26628519 WAF=2.109491
- phaseB(sqlite-a) host_pages=8054775 gc_pages=5755839 WAF=1.714587
- phaseB-load host_pages=1398351 gc_pages=1402831 WAF=2.003204
- phaseB-run host_pages=6656424 gc_pages=4353008 WAF=1.653956
- ycsb-load [OVERALL], Throughput(ops/sec), 23739.8116641608
- ycsb-run [OVERALL], Throughput(ops/sec), 8813.67882954345

### mix-20260911 mixA arm42 — started 2026-09-19T14:49:23+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm42.ko`.
- Command: `bash script/mix-20260911.sh mixA arm42`; evidence `result/mix-20260911/mixA-arm42/`.

- Finished 2026-09-19T15:09:10+09:00; mixA arm42 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm42-rep1`; cleanup attempted.
- total host_bytes=131426181120 host_pages=32086470 gc_pages=38409930 WAF=2.197076
- phaseA(test4) host_pages=24000658 gc_pages=29438423 WAF=2.226567
- phaseB(sqlite-a) host_pages=8085812 gc_pages=8971507 WAF=2.109537
- phaseB-load host_pages=1398349 gc_pages=1692427 WAF=2.210304
- phaseB-run host_pages=6687463 gc_pages=7279080 WAF=2.088467
- ycsb-load [OVERALL], Throughput(ops/sec), 25529.742149604288
- ycsb-run [OVERALL], Throughput(ops/sec), 8554.118701228157

### mix-20260911 mixA arm43 — started 2026-09-19T15:09:11+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm43.ko`.
- Command: `bash script/mix-20260911.sh mixA arm43`; evidence `result/mix-20260911/mixA-arm43/`.

- Finished 2026-09-19T15:28:53+09:00; mixA arm43 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm43-rep1`; cleanup attempted.
- total host_bytes=131336167424 host_pages=32064494 gc_pages=36975334 WAF=2.153155
- phaseA(test4) host_pages=24000661 gc_pages=29041832 WAF=2.210043
- phaseB(sqlite-a) host_pages=8063833 gc_pages=7933502 WAF=1.983838
- phaseB-load host_pages=1398348 gc_pages=1702554 WAF=2.217547
- phaseB-run host_pages=6665485 gc_pages=6230948 WAF=1.934808
- ycsb-load [OVERALL], Throughput(ops/sec), 25460.409063905627
- ycsb-run [OVERALL], Throughput(ops/sec), 8729.08837765528

### mix-20260911 mixA arm44 — started 2026-09-19T15:28:53+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm44.ko`.
- Command: `bash script/mix-20260911.sh mixA arm44`; evidence `result/mix-20260911/mixA-arm44/`.

- Finished 2026-09-19T15:46:28+09:00; mixA arm44 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm44-rep1`; cleanup attempted.
- total host_bytes=131661885440 host_pages=32144015 gc_pages=36528985 WAF=2.136416
- phaseA(test4) host_pages=24022680 gc_pages=28555569 WAF=2.188692
- phaseB(sqlite-a) host_pages=8121335 gc_pages=7973416 WAF=1.981786
- phaseB-load host_pages=1398349 gc_pages=1716043 WAF=2.227192
- phaseB-run host_pages=6722986 gc_pages=6257373 WAF=1.930743
- ycsb-load [OVERALL], Throughput(ops/sec), 24807.740014884643
- ycsb-run [OVERALL], Throughput(ops/sec), 12396.911929238428

### mix-20260911 mixA arm45 — started 2026-09-19T15:46:29+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm45.ko`.
- Command: `bash script/mix-20260911.sh mixA arm45`; evidence `result/mix-20260911/mixA-arm45/`.

- Finished 2026-09-19T16:03:53+09:00; mixA arm45 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm45-rep1`; cleanup attempted.
- total host_bytes=131447889920 host_pages=32091770 gc_pages=25646561 WAF=1.799163
- phaseA(test4) host_pages=24000661 gc_pages=19813767 WAF=1.825551
- phaseB(sqlite-a) host_pages=8091109 gc_pages=5832794 WAF=1.720889
- phaseB-load host_pages=1398351 gc_pages=1022847 WAF=1.731467
- phaseB-run host_pages=6692758 gc_pages=4809947 WAF=1.718679
- ycsb-load [OVERALL], Throughput(ops/sec), 23481.5278647464
- ycsb-run [OVERALL], Throughput(ops/sec), 12697.646808605195

### mix-20260911 mixA arm46 — started 2026-09-19T16:03:54+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm46.ko`.
- Command: `bash script/mix-20260911.sh mixA arm46`; evidence `result/mix-20260911/mixA-arm46/`.

- Finished 2026-09-19T16:21:16+09:00; mixA arm46 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm46-rep1`; cleanup attempted.
- total host_bytes=131418906624 host_pages=32084694 gc_pages=23418728 WAF=1.729903
- phaseA(test4) host_pages=24000664 gc_pages=18796620 WAF=1.783171
- phaseB(sqlite-a) host_pages=8084030 gc_pages=4622108 WAF=1.571758
- phaseB-load host_pages=1398349 gc_pages=738851 WAF=1.528374
- phaseB-run host_pages=6685681 gc_pages=3883257 WAF=1.580832
- ycsb-load [OVERALL], Throughput(ops/sec), 21554.821094984913
- ycsb-run [OVERALL], Throughput(ops/sec), 12852.768325637739

### mix-20260911 mixA arm47 — started 2026-09-19T16:21:16+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm47.ko`.
- Command: `bash script/mix-20260911.sh mixA arm47`; evidence `result/mix-20260911/mixA-arm47/`.

- Finished 2026-09-19T16:40:56+09:00; mixA arm47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm47-rep1`; cleanup attempted.
- total host_bytes=131374116864 host_pages=32073759 gc_pages=23483798 WAF=1.732181
- phaseA(test4) host_pages=24000679 gc_pages=18574840 WAF=1.773930
- phaseB(sqlite-a) host_pages=8073080 gc_pages=4908958 WAF=1.608065
- phaseB-load host_pages=1398349 gc_pages=537025 WAF=1.384042
- phaseB-run host_pages=6674731 gc_pages=4371933 WAF=1.654998
- ycsb-load [OVERALL], Throughput(ops/sec), 24596.21218332377
- ycsb-run [OVERALL], Throughput(ops/sec), 8713.514879415847

### mix-20260911 mixA arm48 — started 2026-09-19T16:40:56+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm48.ko`.
- Command: `bash script/mix-20260911.sh mixA arm48`; evidence `result/mix-20260911/mixA-arm48/`.

- Finished 2026-09-19T16:58:32+09:00; mixA arm48 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm48-rep1`; cleanup attempted.
- total host_bytes=131605716992 host_pages=32130302 gc_pages=27775953 WAF=1.864478
- phaseA(test4) host_pages=24000661 gc_pages=21482704 WAF=1.895088
- phaseB(sqlite-a) host_pages=8129641 gc_pages=6293249 WAF=1.774112
- phaseB-load host_pages=1398349 gc_pages=1185191 WAF=1.847565
- phaseB-run host_pages=6731292 gc_pages=5108058 WAF=1.758853
- ycsb-load [OVERALL], Throughput(ops/sec), 22807.617744326606
- ycsb-run [OVERALL], Throughput(ops/sec), 12285.61600078628

### mix-20260911 mixA arm49 — started 2026-09-19T16:58:33+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm49.ko`.
- Command: `bash script/mix-20260911.sh mixA arm49`; evidence `result/mix-20260911/mixA-arm49/`.

- Finished 2026-09-19T17:15:54+09:00; mixA arm49 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm49-rep1`; cleanup attempted.
- total host_bytes=131445407744 host_pages=32091164 gc_pages=24895074 WAF=1.775761
- phaseA(test4) host_pages=24000658 gc_pages=19966017 WAF=1.831895
- phaseB(sqlite-a) host_pages=8090506 gc_pages=4929057 WAF=1.609240
- phaseB-load host_pages=1398347 gc_pages=912946 WAF=1.652875
- phaseB-run host_pages=6692159 gc_pages=4016111 WAF=1.600122
- ycsb-load [OVERALL], Throughput(ops/sec), 24394.21044072207
- ycsb-run [OVERALL], Throughput(ops/sec), 12720.46149834316

### mix-20260911 mixA arm50 — started 2026-09-19T17:15:55+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm50.ko`.
- Command: `bash script/mix-20260911.sh mixA arm50`; evidence `result/mix-20260911/mixA-arm50/`.

- Finished 2026-09-19T17:35:22+09:00; mixA arm50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm50-rep1`; cleanup attempted.
- total host_bytes=131317673984 host_pages=32059979 gc_pages=24233921 WAF=1.755893
- phaseA(test4) host_pages=24020103 gc_pages=19447422 WAF=1.809631
- phaseB(sqlite-a) host_pages=8039876 gc_pages=4786499 WAF=1.595345
- phaseB-load host_pages=1398349 gc_pages=564348 WAF=1.403582
- phaseB-run host_pages=6641527 gc_pages=4222151 WAF=1.635720
- ycsb-load [OVERALL], Throughput(ops/sec), 26337.737588341162
- ycsb-run [OVERALL], Throughput(ops/sec), 8931.681567688749

### mix-20260911 mixA arm51 — started 2026-09-19T17:35:23+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm51.ko`.
- Command: `bash script/mix-20260911.sh mixA arm51`; evidence `result/mix-20260911/mixA-arm51/`.

- Finished 2026-09-19T17:55:01+09:00; mixA arm51 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm51-rep1`; cleanup attempted.
- total host_bytes=131332747264 host_pages=32063659 gc_pages=31120604 WAF=1.970588
- phaseA(test4) host_pages=24000661 gc_pages=24294731 WAF=2.012253
- phaseB(sqlite-a) host_pages=8062998 gc_pages=6825873 WAF=1.846568
- phaseB-load host_pages=1398349 gc_pages=1370358 WAF=1.979983
- phaseB-run host_pages=6664649 gc_pages=5455515 WAF=1.818575
- ycsb-load [OVERALL], Throughput(ops/sec), 24653.819287504622
- ycsb-run [OVERALL], Throughput(ops/sec), 8757.832786698604

### mix-20260911 mixA arm52 — started 2026-09-19T17:55:01+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm52.ko`.
- Command: `bash script/mix-20260911.sh mixA arm52`; evidence `result/mix-20260911/mixA-arm52/`.

- Finished 2026-09-19T18:14:40+09:00; mixA arm52 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm52-rep1`; cleanup attempted.
- total host_bytes=131410051072 host_pages=32082532 gc_pages=26952844 WAF=1.840110
- phaseA(test4) host_pages=24021151 gc_pages=21419827 WAF=1.891707
- phaseB(sqlite-a) host_pages=8061381 gc_pages=5533017 WAF=1.686361
- phaseB-load host_pages=1399375 gc_pages=1106780 WAF=1.790910
- phaseB-run host_pages=6662006 gc_pages=4426237 WAF=1.664400
- ycsb-load [OVERALL], Throughput(ops/sec), 21921.812203142126
- ycsb-run [OVERALL], Throughput(ops/sec), 8780.113043955442

### mix-20260911 mixA arm53 — started 2026-09-19T18:14:41+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm53.ko`.
- Command: `bash script/mix-20260911.sh mixA arm53`; evidence `result/mix-20260911/mixA-arm53/`.

- Finished 2026-09-19T18:32:04+09:00; mixA arm53 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm53-rep1`; cleanup attempted.
- total host_bytes=131486982144 host_pages=32101314 gc_pages=25362355 WAF=1.790072
- phaseA(test4) host_pages=24024238 gc_pages=20984039 WAF=1.873453
- phaseB(sqlite-a) host_pages=8077076 gc_pages=4378316 WAF=1.542067
- phaseB-load host_pages=1398349 gc_pages=763168 WAF=1.545764
- phaseB-run host_pages=6678727 gc_pages=3615148 WAF=1.541293
- ycsb-load [OVERALL], Throughput(ops/sec), 23392.724862567742
- ycsb-run [OVERALL], Throughput(ops/sec), 12968.234310057514

### mix-20260911 mixA arm54 — started 2026-09-19T18:32:04+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm54.ko`.
- Command: `bash script/mix-20260911.sh mixA arm54`; evidence `result/mix-20260911/mixA-arm54/`.

- Finished 2026-09-19T18:49:44+09:00; mixA arm54 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm54-rep1`; cleanup attempted.
- total host_bytes=131724365824 host_pages=32159269 gc_pages=35469726 WAF=2.102939
- phaseA(test4) host_pages=24020622 gc_pages=27117944 WAF=2.128944
- phaseB(sqlite-a) host_pages=8138647 gc_pages=8351782 WAF=2.026188
- phaseB-load host_pages=1398349 gc_pages=1531275 WAF=2.095059
- phaseB-run host_pages=6740298 gc_pages=6820507 WAF=2.011900
- ycsb-load [OVERALL], Throughput(ops/sec), 23178.552113111335
- ycsb-run [OVERALL], Throughput(ops/sec), 12069.095572150562

### mix-20260911 mixA arm55 — started 2026-09-19T18:49:45+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm55.ko`.
- Command: `bash script/mix-20260911.sh mixA arm55`; evidence `result/mix-20260911/mixA-arm55/`.

- Finished 2026-09-19T19:09:22+09:00; mixA arm55 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm55-rep1`; cleanup attempted.
- total host_bytes=131331858432 host_pages=32063442 gc_pages=32446926 WAF=2.011960
- phaseA(test4) host_pages=24000658 gc_pages=26004689 WAF=2.083499
- phaseB(sqlite-a) host_pages=8062784 gc_pages=6442237 WAF=1.799009
- phaseB-load host_pages=1398349 gc_pages=1476711 WAF=2.056039
- phaseB-run host_pages=6664435 gc_pages=4965526 WAF=1.745078
- ycsb-load [OVERALL], Throughput(ops/sec), 25449.609772650154
- ycsb-run [OVERALL], Throughput(ops/sec), 8744.583823394385

### mix-20260911 mixA arm56 — started 2026-09-19T19:09:22+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm56.ko`.
- Command: `bash script/mix-20260911.sh mixA arm56`; evidence `result/mix-20260911/mixA-arm56/`.

- Finished 2026-09-19T19:26:50+09:00; mixA arm56 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm56-rep1`; cleanup attempted.
- total host_bytes=131525763072 host_pages=32110782 gc_pages=30150610 WAF=1.938956
- phaseA(test4) host_pages=24000661 gc_pages=24701031 WAF=2.029181
- phaseB(sqlite-a) host_pages=8110121 gc_pages=5449579 WAF=1.671948
- phaseB-load host_pages=1398349 gc_pages=1215927 WAF=1.869545
- phaseB-run host_pages=6711772 gc_pages=4233652 WAF=1.630780
- ycsb-load [OVERALL], Throughput(ops/sec), 22154.118819923937
- ycsb-run [OVERALL], Throughput(ops/sec), 12582.810622408728

### mix-20260911 mixA arm57 — started 2026-09-19T19:26:51+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm57.ko`.
- Command: `bash script/mix-20260911.sh mixA arm57`; evidence `result/mix-20260911/mixA-arm57/`.

- Finished 2026-09-19T19:44:33+09:00; mixA arm57 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm57-rep1`; cleanup attempted.
- total host_bytes=131825422336 host_pages=32183941 gc_pages=38520746 WAF=2.196893
- phaseA(test4) host_pages=24025763 gc_pages=28126263 WAF=2.170671
- phaseB(sqlite-a) host_pages=8158178 gc_pages=10394483 WAF=2.274118
- phaseB-load host_pages=1398351 gc_pages=1684484 WAF=2.204622
- phaseB-run host_pages=6759827 gc_pages=8709999 WAF=2.288494
- ycsb-load [OVERALL], Throughput(ops/sec), 26340.050046095086
- ycsb-run [OVERALL], Throughput(ops/sec), 11829.66465858109

### mix-20260911 mixA arm58 — started 2026-09-19T19:44:34+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm58.ko`.
- Command: `bash script/mix-20260911.sh mixA arm58`; evidence `result/mix-20260911/mixA-arm58/`.

- Finished 2026-09-19T20:04:14+09:00; mixA arm58 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm58-rep1`; cleanup attempted.
- total host_bytes=131330412544 host_pages=32063089 gc_pages=36140892 WAF=2.127181
- phaseA(test4) host_pages=24000664 gc_pages=28538704 WAF=2.189080
- phaseB(sqlite-a) host_pages=8062425 gc_pages=7602188 WAF=1.942916
- phaseB-load host_pages=1398351 gc_pages=1621175 WAF=2.159348
- phaseB-run host_pages=6664074 gc_pages=5981013 WAF=1.897501
- ycsb-load [OVERALL], Throughput(ops/sec), 22323.08951558896
- ycsb-run [OVERALL], Throughput(ops/sec), 8781.963603151848

### mix-20260911 mixA arm59 — started 2026-09-19T20:04:15+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm59.ko`.
- Command: `bash script/mix-20260911.sh mixA arm59`; evidence `result/mix-20260911/mixA-arm59/`.

- Finished 2026-09-19T20:23:47+09:00; mixA arm59 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-arm59-rep1`; cleanup attempted.
- total host_bytes=131266310144 host_pages=32047439 gc_pages=34769739 WAF=2.084946
- phaseA(test4) host_pages=24000658 gc_pages=28076137 WAF=2.169807
- phaseB(sqlite-a) host_pages=8046781 gc_pages=6693602 WAF=1.831836
- phaseB-load host_pages=1398351 gc_pages=1693608 WAF=2.211147
- phaseB-run host_pages=6648430 gc_pages=4999994 WAF=1.752056
- ycsb-load [OVERALL], Throughput(ops/sec), 26033.75710504621
- ycsb-run [OVERALL], Throughput(ops/sec), 8878.353243040481

### mix-20260911 mixC arm00 — started 2026-09-19T20:24:03+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm00.ko`.
- Command: `bash script/mix-20260911.sh mixC arm00`; evidence `result/mix-20260911/mixC-arm00/`.

- Finished 2026-09-19T20:45:29+09:00; mixC arm00 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm00-rep1`; cleanup attempted.
- total host_bytes=122884468736 host_pages=30001091 gc_pages=36832759 WAF=2.227714
- phaseA(test3) host_pages=6000424 gc_pages=6897173 WAF=2.149448
- phaseB(test4) host_pages=24000667 gc_pages=29935586 WAF=2.247281
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm01 — started 2026-09-19T20:45:29+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm01.ko`.
- Command: `bash script/mix-20260911.sh mixC arm01`; evidence `result/mix-20260911/mixC-arm01/`.

- Finished 2026-09-19T21:06:52+09:00; mixC arm01 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm01-rep1`; cleanup attempted.
- total host_bytes=122976718848 host_pages=30023613 gc_pages=36892647 WAF=2.228788
- phaseA(test3) host_pages=6022955 gc_pages=6865489 WAF=2.139887
- phaseB(test4) host_pages=24000658 gc_pages=30027158 WAF=2.251097
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm02 — started 2026-09-19T21:06:52+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm02.ko`.
- Command: `bash script/mix-20260911.sh mixC arm02`; evidence `result/mix-20260911/mixC-arm02/`.

- Finished 2026-09-19T21:28:15+09:00; mixC arm02 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm02-rep1`; cleanup attempted.
- total host_bytes=122976714752 host_pages=30023612 gc_pages=36957324 WAF=2.230942
- phaseA(test3) host_pages=6022951 gc_pages=6873479 WAF=2.141214
- phaseB(test4) host_pages=24000661 gc_pages=30083845 WAF=2.253459
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm03 — started 2026-09-19T21:28:15+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm03.ko`.
- Command: `bash script/mix-20260911.sh mixC arm03`; evidence `result/mix-20260911/mixC-arm03/`.

- Finished 2026-09-19T21:49:39+09:00; mixC arm03 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm03-rep1`; cleanup attempted.
- total host_bytes=122987200512 host_pages=30026172 gc_pages=37631314 WAF=2.253284
- phaseA(test3) host_pages=6025514 gc_pages=6855580 WAF=2.137759
- phaseB(test4) host_pages=24000658 gc_pages=30775734 WAF=2.282287
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm04 — started 2026-09-19T21:49:39+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm04.ko`.
- Command: `bash script/mix-20260911.sh mixC arm04`; evidence `result/mix-20260911/mixC-arm04/`.

- Finished 2026-09-19T22:11:02+09:00; mixC arm04 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm04-rep1`; cleanup attempted.
- total host_bytes=122978799616 host_pages=30024121 gc_pages=37676283 WAF=2.254867
- phaseA(test3) host_pages=6023463 gc_pages=6918049 WAF=2.148517
- phaseB(test4) host_pages=24000658 gc_pages=30758234 WAF=2.281558
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm05 — started 2026-09-19T22:11:02+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm05.ko`.
- Command: `bash script/mix-20260911.sh mixC arm05`; evidence `result/mix-20260911/mixC-arm05/`.

- Finished 2026-09-19T22:32:25+09:00; mixC arm05 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm05-rep1`; cleanup attempted.
- total host_bytes=122884407296 host_pages=30001076 gc_pages=37768383 WAF=2.258901
- phaseA(test3) host_pages=6000415 gc_pages=6985423 WAF=2.164157
- phaseB(test4) host_pages=24000661 gc_pages=30782960 WAF=2.282588
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm06 — started 2026-09-19T22:32:25+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm06.ko`.
- Command: `bash script/mix-20260911.sh mixC arm06`; evidence `result/mix-20260911/mixC-arm06/`.

- Finished 2026-09-19T22:53:48+09:00; mixC arm06 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm06-rep1`; cleanup attempted.
- total host_bytes=122884407296 host_pages=30001076 gc_pages=37791256 WAF=2.259663
- phaseA(test3) host_pages=6000418 gc_pages=6996143 WAF=2.165943
- phaseB(test4) host_pages=24000658 gc_pages=30795113 WAF=2.283095
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm07 — started 2026-09-19T22:53:48+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm07.ko`.
- Command: `bash script/mix-20260911.sh mixC arm07`; evidence `result/mix-20260911/mixC-arm07/`.

- Finished 2026-09-19T23:15:12+09:00; mixC arm07 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm07-rep1`; cleanup attempted.
- total host_bytes=122884431872 host_pages=30001082 gc_pages=37870236 WAF=2.262296
- phaseA(test3) host_pages=6000421 gc_pages=7023153 WAF=2.170443
- phaseB(test4) host_pages=24000661 gc_pages=30847083 WAF=2.285260
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm08 — started 2026-09-19T23:15:12+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm08.ko`.
- Command: `bash script/mix-20260911.sh mixC arm08`; evidence `result/mix-20260911/mixC-arm08/`.

- Finished 2026-09-19T23:36:35+09:00; mixC arm08 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm08-rep1`; cleanup attempted.
- total host_bytes=122884481024 host_pages=30001094 gc_pages=37893270 WAF=2.263063
- phaseA(test3) host_pages=6000418 gc_pages=6993426 WAF=2.165490
- phaseB(test4) host_pages=24000676 gc_pages=30899844 WAF=2.287457
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm09 — started 2026-09-19T23:36:35+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm09.ko`.
- Command: `bash script/mix-20260911.sh mixC arm09`; evidence `result/mix-20260911/mixC-arm09/`.

- Finished 2026-09-19T23:57:58+09:00; mixC arm09 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm09-rep1`; cleanup attempted.
- total host_bytes=122884407296 host_pages=30001076 gc_pages=37788215 WAF=2.259562
- phaseA(test3) host_pages=6000418 gc_pages=6990268 WAF=2.164964
- phaseB(test4) host_pages=24000658 gc_pages=30797947 WAF=2.283213
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm10 — started 2026-09-19T23:57:58+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm10.ko`.
- Command: `bash script/mix-20260911.sh mixC arm10`; evidence `result/mix-20260911/mixC-arm10/`.

- Finished 2026-09-20T00:19:21+09:00; mixC arm10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm10-rep1`; cleanup attempted.
- total host_bytes=122884419584 host_pages=30001079 gc_pages=37812717 WAF=2.260379
- phaseA(test3) host_pages=6000418 gc_pages=6991081 WAF=2.165099
- phaseB(test4) host_pages=24000661 gc_pages=30821636 WAF=2.284199
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm11 — started 2026-09-20T00:19:21+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm11.ko`.
- Command: `bash script/mix-20260911.sh mixC arm11`; evidence `result/mix-20260911/mixC-arm11/`.

- Finished 2026-09-20T00:40:45+09:00; mixC arm11 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm11-rep1`; cleanup attempted.
- total host_bytes=122884481024 host_pages=30001094 gc_pages=37780230 WAF=2.259295
- phaseA(test3) host_pages=6000421 gc_pages=6984684 WAF=2.164032
- phaseB(test4) host_pages=24000673 gc_pages=30795546 WAF=2.283112
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm12 — started 2026-09-20T00:40:45+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm12.ko`.
- Command: `bash script/mix-20260911.sh mixC arm12`; evidence `result/mix-20260911/mixC-arm12/`.

- Finished 2026-09-20T01:02:08+09:00; mixC arm12 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm12-rep1`; cleanup attempted.
- total host_bytes=122884407296 host_pages=30001076 gc_pages=37886694 WAF=2.262845
- phaseA(test3) host_pages=6000418 gc_pages=7023419 WAF=2.170488
- phaseB(test4) host_pages=24000658 gc_pages=30863275 WAF=2.285935
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm13 — started 2026-09-20T01:02:08+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm13.ko`.
- Command: `bash script/mix-20260911.sh mixC arm13`; evidence `result/mix-20260911/mixC-arm13/`.

- Finished 2026-09-20T01:23:31+09:00; mixC arm13 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm13-rep1`; cleanup attempted.
- total host_bytes=122997739520 host_pages=30028745 gc_pages=37269764 WAF=2.241136
- phaseA(test3) host_pages=6020398 gc_pages=6617758 WAF=2.099223
- phaseB(test4) host_pages=24008347 gc_pages=30652006 WAF=2.276723
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm14 — started 2026-09-20T01:23:31+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm14.ko`.
- Command: `bash script/mix-20260911.sh mixC arm14`; evidence `result/mix-20260911/mixC-arm14/`.

- Finished 2026-09-20T01:44:54+09:00; mixC arm14 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm14-rep1`; cleanup attempted.
- total host_bytes=123002163200 host_pages=30029825 gc_pages=36750057 WAF=2.223785
- phaseA(test3) host_pages=6016306 gc_pages=6535903 WAF=2.086365
- phaseB(test4) host_pages=24013519 gc_pages=30214154 WAF=2.258214
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm15 — started 2026-09-20T01:44:54+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm15.ko`.
- Command: `bash script/mix-20260911.sh mixC arm15`; evidence `result/mix-20260911/mixC-arm15/`.

- Finished 2026-09-20T02:06:17+09:00; mixC arm15 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm15-rep1`; cleanup attempted.
- total host_bytes=122964074496 host_pages=30020526 gc_pages=25140669 WAF=1.837449
- phaseA(test3) host_pages=6019868 gc_pages=4949086 WAF=1.822125
- phaseB(test4) host_pages=24000658 gc_pages=20191583 WAF=1.841293
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm16 — started 2026-09-20T02:06:17+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm16.ko`.
- Command: `bash script/mix-20260911.sh mixC arm16`; evidence `result/mix-20260911/mixC-arm16/`.

- Finished 2026-09-20T02:27:41+09:00; mixC arm16 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm16-rep1`; cleanup attempted.
- total host_bytes=122884419584 host_pages=30001079 gc_pages=24198019 WAF=1.806572
- phaseA(test3) host_pages=6000421 gc_pages=4941514 WAF=1.823528
- phaseB(test4) host_pages=24000658 gc_pages=19256505 WAF=1.802332
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm17 — started 2026-09-20T02:27:41+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm17.ko`.
- Command: `bash script/mix-20260911.sh mixC arm17`; evidence `result/mix-20260911/mixC-arm17/`.

- Finished 2026-09-20T02:49:04+09:00; mixC arm17 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm17-rep1`; cleanup attempted.
- total host_bytes=122884431872 host_pages=30001082 gc_pages=24996316 WAF=1.833180
- phaseA(test3) host_pages=6000421 gc_pages=4949375 WAF=1.824838
- phaseB(test4) host_pages=24000661 gc_pages=20046941 WAF=1.835266
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm18 — started 2026-09-20T02:49:04+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm18.ko`.
- Command: `bash script/mix-20260911.sh mixC arm18`; evidence `result/mix-20260911/mixC-arm18/`.

- Finished 2026-09-20T03:10:27+09:00; mixC arm18 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm18-rep1`; cleanup attempted.
- total host_bytes=122884395008 host_pages=30001073 gc_pages=27164930 WAF=1.905465
- phaseA(test3) host_pages=6000415 gc_pages=5077654 WAF=1.846217
- phaseB(test4) host_pages=24000658 gc_pages=22087276 WAF=1.920278
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm19 — started 2026-09-20T03:10:27+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm19.ko`.
- Command: `bash script/mix-20260911.sh mixC arm19`; evidence `result/mix-20260911/mixC-arm19/`.

- Finished 2026-09-20T03:31:50+09:00; mixC arm19 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm19-rep1`; cleanup attempted.
- total host_bytes=122884407296 host_pages=30001076 gc_pages=25960037 WAF=1.865304
- phaseA(test3) host_pages=6000418 gc_pages=4944496 WAF=1.824025
- phaseB(test4) host_pages=24000658 gc_pages=21015541 WAF=1.875624
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm20 — started 2026-09-20T03:31:55+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm20.ko`.
- Command: `bash script/mix-20260911.sh mixC arm20`; evidence `result/mix-20260911/mixC-arm20/`.

- Finished 2026-09-20T03:53:18+09:00; mixC arm20 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm20-rep1`; cleanup attempted.
- total host_bytes=122884419584 host_pages=30001079 gc_pages=26152329 WAF=1.871713
- phaseA(test3) host_pages=6000418 gc_pages=5190299 WAF=1.864990
- phaseB(test4) host_pages=24000661 gc_pages=20962030 WAF=1.873394
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm21 — started 2026-09-20T03:53:18+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm21.ko`.
- Command: `bash script/mix-20260911.sh mixC arm21`; evidence `result/mix-20260911/mixC-arm21/`.

- Finished 2026-09-20T04:14:41+09:00; mixC arm21 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm21-rep1`; cleanup attempted.
- total host_bytes=122966204416 host_pages=30021046 gc_pages=31012061 WAF=2.033011
- phaseA(test3) host_pages=6020385 gc_pages=5345792 WAF=1.887949
- phaseB(test4) host_pages=24000661 gc_pages=25666269 WAF=2.069398
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm22 — started 2026-09-20T04:14:41+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm22.ko`.
- Command: `bash script/mix-20260911.sh mixC arm22`; evidence `result/mix-20260911/mixC-arm22/`.

- Finished 2026-09-20T04:36:04+09:00; mixC arm22 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm22-rep1`; cleanup attempted.
- total host_bytes=122997755904 host_pages=30028749 gc_pages=29863798 WAF=1.994507
- phaseA(test3) host_pages=6021942 gc_pages=4996773 WAF=1.829761
- phaseB(test4) host_pages=24006807 gc_pages=24867025 WAF=2.035832
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm23 — started 2026-09-20T04:36:04+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm23.ko`.
- Command: `bash script/mix-20260911.sh mixC arm23`; evidence `result/mix-20260911/mixC-arm23/`.

- Finished 2026-09-20T04:57:28+09:00; mixC arm23 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm23-rep1`; cleanup attempted.
- total host_bytes=122978795520 host_pages=30024120 gc_pages=30059749 WAF=2.001187
- phaseA(test3) host_pages=6023462 gc_pages=5389946 WAF=1.894825
- phaseB(test4) host_pages=24000658 gc_pages=24669803 WAF=2.027880
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm24 — started 2026-09-20T04:57:28+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm24.ko`.
- Command: `bash script/mix-20260911.sh mixC arm24`; evidence `result/mix-20260911/mixC-arm24/`.

- Finished 2026-09-20T05:18:51+09:00; mixC arm24 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm24-rep1`; cleanup attempted.
- total host_bytes=122985107456 host_pages=30025661 gc_pages=33957958 WAF=2.130965
- phaseA(test3) host_pages=6024997 gc_pages=5892931 WAF=1.978080
- phaseB(test4) host_pages=24000664 gc_pages=28065027 WAF=2.169344
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm25 — started 2026-09-20T05:18:51+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm25.ko`.
- Command: `bash script/mix-20260911.sh mixC arm25`; evidence `result/mix-20260911/mixC-arm25/`.

- Finished 2026-09-20T05:40:14+09:00; mixC arm25 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm25-rep1`; cleanup attempted.
- total host_bytes=122943078400 host_pages=30015400 gc_pages=33585436 WAF=2.118940
- phaseA(test3) host_pages=6014742 gc_pages=5824949 WAF=1.968445
- phaseB(test4) host_pages=24000658 gc_pages=27760487 WAF=2.156655
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm26 — started 2026-09-20T05:40:14+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm26.ko`.
- Command: `bash script/mix-20260911.sh mixC arm26`; evidence `result/mix-20260911/mixC-arm26/`.

- Finished 2026-09-20T06:01:37+09:00; mixC arm26 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm26-rep1`; cleanup attempted.
- total host_bytes=122991403008 host_pages=30027198 gc_pages=33570960 WAF=2.118018
- phaseA(test3) host_pages=6026540 gc_pages=5744820 WAF=1.953253
- phaseB(test4) host_pages=24000658 gc_pages=27826140 WAF=2.159391
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm27 — started 2026-09-20T06:01:38+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm27.ko`.
- Command: `bash script/mix-20260911.sh mixC arm27`; evidence `result/mix-20260911/mixC-arm27/`.

- Finished 2026-09-20T06:23:01+09:00; mixC arm27 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm27-rep1`; cleanup attempted.
- total host_bytes=122884468736 host_pages=30001091 gc_pages=36597606 WAF=2.219876
- phaseA(test3) host_pages=6000421 gc_pages=6793160 WAF=2.132114
- phaseB(test4) host_pages=24000670 gc_pages=29804446 WAF=2.241817
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm28 — started 2026-09-20T06:23:01+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm28.ko`.
- Command: `bash script/mix-20260911.sh mixC arm28`; evidence `result/mix-20260911/mixC-arm28/`.

- Finished 2026-09-20T06:44:24+09:00; mixC arm28 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm28-rep1`; cleanup attempted.
- total host_bytes=122884419584 host_pages=30001079 gc_pages=36330750 WAF=2.210981
- phaseA(test3) host_pages=6000418 gc_pages=6759071 WAF=2.126433
- phaseB(test4) host_pages=24000661 gc_pages=29571679 WAF=2.232119
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm29 — started 2026-09-20T06:44:24+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm29.ko`.
- Command: `bash script/mix-20260911.sh mixC arm29`; evidence `result/mix-20260911/mixC-arm29/`.

- Finished 2026-09-20T07:05:47+09:00; mixC arm29 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm29-rep1`; cleanup attempted.
- total host_bytes=122884407296 host_pages=30001076 gc_pages=36393907 WAF=2.213087
- phaseA(test3) host_pages=6000418 gc_pages=6775898 WAF=2.129238
- phaseB(test4) host_pages=24000658 gc_pages=29618009 WAF=2.234050
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm30 — started 2026-09-20T07:05:47+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm30.ko`.
- Command: `bash script/mix-20260911.sh mixC arm30`; evidence `result/mix-20260911/mixC-arm30/`.

- Finished 2026-09-20T07:27:10+09:00; mixC arm30 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm30-rep1`; cleanup attempted.
- total host_bytes=122884407296 host_pages=30001076 gc_pages=24030870 WAF=1.801000
- phaseA(test3) host_pages=6000418 gc_pages=4841221 WAF=1.806814
- phaseB(test4) host_pages=24000658 gc_pages=19189649 WAF=1.799547
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm31 — started 2026-09-20T07:27:10+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm31.ko`.
- Command: `bash script/mix-20260911.sh mixC arm31`; evidence `result/mix-20260911/mixC-arm31/`.

- Finished 2026-09-20T07:48:34+09:00; mixC arm31 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm31-rep1`; cleanup attempted.
- total host_bytes=122884419584 host_pages=30001079 gc_pages=22906683 WAF=1.763529
- phaseA(test3) host_pages=6000421 gc_pages=4787092 WAF=1.797793
- phaseB(test4) host_pages=24000658 gc_pages=18119591 WAF=1.754962
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm32 — started 2026-09-20T07:48:34+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm32.ko`.
- Command: `bash script/mix-20260911.sh mixC arm32`; evidence `result/mix-20260911/mixC-arm32/`.

- Finished 2026-09-20T08:09:57+09:00; mixC arm32 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm32-rep1`; cleanup attempted.
- total host_bytes=122884407296 host_pages=30001076 gc_pages=22991717 WAF=1.766363
- phaseA(test3) host_pages=6000415 gc_pages=4797052 WAF=1.799453
- phaseB(test4) host_pages=24000661 gc_pages=18194665 WAF=1.758090
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm33 — started 2026-09-20T08:09:57+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm33.ko`.
- Command: `bash script/mix-20260911.sh mixC arm33`; evidence `result/mix-20260911/mixC-arm33/`.

- Finished 2026-09-20T08:31:20+09:00; mixC arm33 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm33-rep1`; cleanup attempted.
- total host_bytes=122884407296 host_pages=30001076 gc_pages=25752674 WAF=1.858392
- phaseA(test3) host_pages=6000418 gc_pages=4942798 WAF=1.823742
- phaseB(test4) host_pages=24000658 gc_pages=20809876 WAF=1.867054
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm34 — started 2026-09-20T08:31:20+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm34.ko`.
- Command: `bash script/mix-20260911.sh mixC arm34`; evidence `result/mix-20260911/mixC-arm34/`.

- Finished 2026-09-20T08:52:43+09:00; mixC arm34 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm34-rep1`; cleanup attempted.
- total host_bytes=122884407296 host_pages=30001076 gc_pages=24355499 WAF=1.811821
- phaseA(test3) host_pages=6000418 gc_pages=4836394 WAF=1.806010
- phaseB(test4) host_pages=24000658 gc_pages=19519105 WAF=1.813274
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm35 — started 2026-09-20T08:52:43+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm35.ko`.
- Command: `bash script/mix-20260911.sh mixC arm35`; evidence `result/mix-20260911/mixC-arm35/`.

- Finished 2026-09-20T09:14:07+09:00; mixC arm35 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm35-rep1`; cleanup attempted.
- total host_bytes=122884419584 host_pages=30001079 gc_pages=24341522 WAF=1.811355
- phaseA(test3) host_pages=6000418 gc_pages=4875018 WAF=1.812446
- phaseB(test4) host_pages=24000661 gc_pages=19466504 WAF=1.811082
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm36 — started 2026-09-20T09:14:07+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm36.ko`.
- Command: `bash script/mix-20260911.sh mixC arm36`; evidence `result/mix-20260911/mixC-arm36/`.

- Finished 2026-09-20T09:35:30+09:00; mixC arm36 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm36-rep1`; cleanup attempted.
- total host_bytes=122884444160 host_pages=30001085 gc_pages=28430384 WAF=1.947645
- phaseA(test3) host_pages=6000427 gc_pages=5172759 WAF=1.862065
- phaseB(test4) host_pages=24000658 gc_pages=23257625 WAF=1.969041
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm37 — started 2026-09-20T09:35:30+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm37.ko`.
- Command: `bash script/mix-20260911.sh mixC arm37`; evidence `result/mix-20260911/mixC-arm37/`.

- Finished 2026-09-20T09:56:53+09:00; mixC arm37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm37-rep1`; cleanup attempted.
- total host_bytes=122884407296 host_pages=30001076 gc_pages=26680463 WAF=1.889317
- phaseA(test3) host_pages=6000418 gc_pages=4937886 WAF=1.822924
- phaseB(test4) host_pages=24000658 gc_pages=21742577 WAF=1.905916
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm38 — started 2026-09-20T09:56:53+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm38.ko`.
- Command: `bash script/mix-20260911.sh mixC arm38`; evidence `result/mix-20260911/mixC-arm38/`.

- Finished 2026-09-20T10:18:16+09:00; mixC arm38 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm38-rep1`; cleanup attempted.
- total host_bytes=122884616192 host_pages=30001127 gc_pages=25977505 WAF=1.865884
- phaseA(test3) host_pages=6000424 gc_pages=5058266 WAF=1.842985
- phaseB(test4) host_pages=24000703 gc_pages=20919239 WAF=1.871609
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm39 — started 2026-09-20T10:18:16+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm39.ko`.
- Command: `bash script/mix-20260911.sh mixC arm39`; evidence `result/mix-20260911/mixC-arm39/`.

- Finished 2026-09-20T10:39:40+09:00; mixC arm39 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm39-rep1`; cleanup attempted.
- total host_bytes=122884407296 host_pages=30001076 gc_pages=31853587 WAF=2.061748
- phaseA(test3) host_pages=6000415 gc_pages=5598501 WAF=1.933019
- phaseB(test4) host_pages=24000661 gc_pages=26255086 WAF=2.093932
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm40 — started 2026-09-20T10:39:44+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm40.ko`.
- Command: `bash script/mix-20260911.sh mixC arm40`; evidence `result/mix-20260911/mixC-arm40/`.

- Finished 2026-09-20T11:01:07+09:00; mixC arm40 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm40-rep1`; cleanup attempted.
- total host_bytes=122966175744 host_pages=30021039 gc_pages=30636749 WAF=2.020509
- phaseA(test3) host_pages=6020381 gc_pages=5264325 WAF=1.874417
- phaseB(test4) host_pages=24000658 gc_pages=25372424 WAF=2.057155
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm41 — started 2026-09-20T11:01:07+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm41.ko`.
- Command: `bash script/mix-20260911.sh mixC arm41`; evidence `result/mix-20260911/mixC-arm41/`.

- Finished 2026-09-20T11:22:30+09:00; mixC arm41 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm41-rep1`; cleanup attempted.
- total host_bytes=122884407296 host_pages=30001076 gc_pages=29958169 WAF=1.998570
- phaseA(test3) host_pages=6000418 gc_pages=5237751 WAF=1.872898
- phaseB(test4) host_pages=24000658 gc_pages=24720418 WAF=2.029989
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm42 — started 2026-09-20T11:22:30+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm42.ko`.
- Command: `bash script/mix-20260911.sh mixC arm42`; evidence `result/mix-20260911/mixC-arm42/`.

- Finished 2026-09-20T11:43:54+09:00; mixC arm42 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm42-rep1`; cleanup attempted.
- total host_bytes=122972516352 host_pages=30022587 gc_pages=34711689 WAF=2.156186
- phaseA(test3) host_pages=6021926 gc_pages=6190788 WAF=2.028041
- phaseB(test4) host_pages=24000661 gc_pages=28520901 WAF=2.188338
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm43 — started 2026-09-20T11:43:54+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm43.ko`.
- Command: `bash script/mix-20260911.sh mixC arm43`; evidence `result/mix-20260911/mixC-arm43/`.

- Finished 2026-09-20T12:05:17+09:00; mixC arm43 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm43-rep1`; cleanup attempted.
- total host_bytes=122951483392 host_pages=30017452 gc_pages=33878853 WAF=2.128639
- phaseA(test3) host_pages=6016794 gc_pages=5980211 WAF=1.993920
- phaseB(test4) host_pages=24000658 gc_pages=27898642 WAF=2.162412
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm44 — started 2026-09-20T12:05:17+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm44.ko`.
- Command: `bash script/mix-20260911.sh mixC arm44`; evidence `result/mix-20260911/mixC-arm44/`.

- Finished 2026-09-20T12:26:40+09:00; mixC arm44 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm44-rep1`; cleanup attempted.
- total host_bytes=122884431872 host_pages=30001082 gc_pages=33545750 WAF=2.118151
- phaseA(test3) host_pages=6000421 gc_pages=5822372 WAF=1.970327
- phaseB(test4) host_pages=24000661 gc_pages=27723378 WAF=2.155109
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm45 — started 2026-09-20T12:26:40+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm45.ko`.
- Command: `bash script/mix-20260911.sh mixC arm45`; evidence `result/mix-20260911/mixC-arm45/`.

- Finished 2026-09-20T12:48:03+09:00; mixC arm45 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm45-rep1`; cleanup attempted.
- total host_bytes=122926309376 host_pages=30011306 gc_pages=23746504 WAF=1.791252
- phaseA(test3) host_pages=6010648 gc_pages=4839894 WAF=1.805220
- phaseB(test4) host_pages=24000658 gc_pages=18906610 WAF=1.787754
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm46 — started 2026-09-20T12:48:03+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm46.ko`.
- Command: `bash script/mix-20260911.sh mixC arm46`; evidence `result/mix-20260911/mixC-arm46/`.

- Finished 2026-09-20T13:09:27+09:00; mixC arm46 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm46-rep1`; cleanup attempted.
- total host_bytes=122983231488 host_pages=30025203 gc_pages=22684186 WAF=1.755505
- phaseA(test3) host_pages=6024483 gc_pages=4767688 WAF=1.791385
- phaseB(test4) host_pages=24000720 gc_pages=17916498 WAF=1.746498
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm47 — started 2026-09-20T13:09:27+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm47.ko`.
- Command: `bash script/mix-20260911.sh mixC arm47`; evidence `result/mix-20260911/mixC-arm47/`.

- Finished 2026-09-20T13:30:50+09:00; mixC arm47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm47-rep1`; cleanup attempted.
- total host_bytes=122884407296 host_pages=30001076 gc_pages=22527570 WAF=1.750892
- phaseA(test3) host_pages=6000415 gc_pages=4789424 WAF=1.798182
- phaseB(test4) host_pages=24000661 gc_pages=17738146 WAF=1.739069
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm48 — started 2026-09-20T13:30:50+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm48.ko`.
- Command: `bash script/mix-20260911.sh mixC arm48`; evidence `result/mix-20260911/mixC-arm48/`.

- Finished 2026-09-20T13:52:13+09:00; mixC arm48 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm48-rep1`; cleanup attempted.
- total host_bytes=122964119552 host_pages=30020537 gc_pages=25263225 WAF=1.841531
- phaseA(test3) host_pages=6019873 gc_pages=4898173 WAF=1.813667
- phaseB(test4) host_pages=24000664 gc_pages=20365052 WAF=1.848520
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm49 — started 2026-09-20T13:52:13+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm49.ko`.
- Command: `bash script/mix-20260911.sh mixC arm49`; evidence `result/mix-20260911/mixC-arm49/`.

- Finished 2026-09-20T14:13:36+09:00; mixC arm49 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm49-rep1`; cleanup attempted.
- total host_bytes=122985254912 host_pages=30025697 gc_pages=23845996 WAF=1.794186
- phaseA(test3) host_pages=6025003 gc_pages=4765255 WAF=1.790913
- phaseB(test4) host_pages=24000694 gc_pages=19080741 WAF=1.795008
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm50 — started 2026-09-20T14:13:36+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm50.ko`.
- Command: `bash script/mix-20260911.sh mixC arm50`; evidence `result/mix-20260911/mixC-arm50/`.

- Finished 2026-09-20T14:34:59+09:00; mixC arm50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm50-rep1`; cleanup attempted.
- total host_bytes=122884419584 host_pages=30001079 gc_pages=23381946 WAF=1.779370
- phaseA(test3) host_pages=6000421 gc_pages=4803346 WAF=1.800501
- phaseB(test4) host_pages=24000658 gc_pages=18578600 WAF=1.774087
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm51 — started 2026-09-20T14:34:59+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm51.ko`.
- Command: `bash script/mix-20260911.sh mixC arm51`; evidence `result/mix-20260911/mixC-arm51/`.

- Finished 2026-09-20T14:56:23+09:00; mixC arm51 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm51-rep1`; cleanup attempted.
- total host_bytes=122884407296 host_pages=30001076 gc_pages=27914443 WAF=1.930448
- phaseA(test3) host_pages=6000418 gc_pages=5126445 WAF=1.854348
- phaseB(test4) host_pages=24000658 gc_pages=22787998 WAF=1.949474
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm52 — started 2026-09-20T14:56:23+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm52.ko`.
- Command: `bash script/mix-20260911.sh mixC arm52`; evidence `result/mix-20260911/mixC-arm52/`.

- Finished 2026-09-20T15:17:46+09:00; mixC arm52 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm52-rep1`; cleanup attempted.
- total host_bytes=122884431872 host_pages=30001082 gc_pages=26034120 WAF=1.867773
- phaseA(test3) host_pages=6000421 gc_pages=4873791 WAF=1.812242
- phaseB(test4) host_pages=24000661 gc_pages=21160329 WAF=1.881656
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm53 — started 2026-09-20T15:17:46+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm53.ko`.
- Command: `bash script/mix-20260911.sh mixC arm53`; evidence `result/mix-20260911/mixC-arm53/`.

- Finished 2026-09-20T15:39:09+09:00; mixC arm53 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm53-rep1`; cleanup attempted.
- total host_bytes=122884431872 host_pages=30001082 gc_pages=24985565 WAF=1.832822
- phaseA(test3) host_pages=6000424 gc_pages=4926234 WAF=1.820981
- phaseB(test4) host_pages=24000658 gc_pages=20059331 WAF=1.835783
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm54 — started 2026-09-20T15:39:09+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm54.ko`.
- Command: `bash script/mix-20260911.sh mixC arm54`; evidence `result/mix-20260911/mixC-arm54/`.

- Finished 2026-09-20T16:00:32+09:00; mixC arm54 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm54-rep1`; cleanup attempted.
- total host_bytes=122884407296 host_pages=30001076 gc_pages=30897157 WAF=2.029868
- phaseA(test3) host_pages=6000418 gc_pages=5510450 WAF=1.918344
- phaseB(test4) host_pages=24000658 gc_pages=25386707 WAF=2.057750
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm55 — started 2026-09-20T16:00:32+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm55.ko`.
- Command: `bash script/mix-20260911.sh mixC arm55`; evidence `result/mix-20260911/mixC-arm55/`.

- Finished 2026-09-20T16:21:56+09:00; mixC arm55 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm55-rep1`; cleanup attempted.
- total host_bytes=122884407296 host_pages=30001076 gc_pages=29392061 WAF=1.979700
- phaseA(test3) host_pages=6000415 gc_pages=5149622 WAF=1.858211
- phaseB(test4) host_pages=24000661 gc_pages=24242439 WAF=2.010074
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm56 — started 2026-09-20T16:21:56+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm56.ko`.
- Command: `bash script/mix-20260911.sh mixC arm56`; evidence `result/mix-20260911/mixC-arm56/`.

- Finished 2026-09-20T16:43:19+09:00; mixC arm56 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm56-rep1`; cleanup attempted.
- total host_bytes=122884431872 host_pages=30001082 gc_pages=28069857 WAF=1.935628
- phaseA(test3) host_pages=6000418 gc_pages=5067562 WAF=1.844535
- phaseB(test4) host_pages=24000664 gc_pages=23002295 WAF=1.958402
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm57 — started 2026-09-20T16:43:19+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm57.ko`.
- Command: `bash script/mix-20260911.sh mixC arm57`; evidence `result/mix-20260911/mixC-arm57/`.

- Finished 2026-09-20T17:04:42+09:00; mixC arm57 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm57-rep1`; cleanup attempted.
- total host_bytes=122940973056 host_pages=30014886 gc_pages=33773589 WAF=2.125228
- phaseA(test3) host_pages=6014228 gc_pages=6117038 WAF=2.017094
- phaseB(test4) host_pages=24000658 gc_pages=27656551 WAF=2.152325
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm58 — started 2026-09-20T17:04:42+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm58.ko`.
- Command: `bash script/mix-20260911.sh mixC arm58`; evidence `result/mix-20260911/mixC-arm58/`.

- Finished 2026-09-20T17:26:05+09:00; mixC arm58 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm58-rep1`; cleanup attempted.
- total host_bytes=122932600832 host_pages=30012842 gc_pages=32810247 WAF=2.093207
- phaseA(test3) host_pages=6012184 gc_pages=5773722 WAF=1.960337
- phaseB(test4) host_pages=24000658 gc_pages=27036525 WAF=2.126491
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC arm59 — started 2026-09-20T17:26:05+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm59.ko`.
- Command: `bash script/mix-20260911.sh mixC arm59`; evidence `result/mix-20260911/mixC-arm59/`.

- Finished 2026-09-20T17:47:29+09:00; mixC arm59 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-arm59-rep1`; cleanup attempted.
- total host_bytes=122884431872 host_pages=30001082 gc_pages=31909498 WAF=2.063612
- phaseA(test3) host_pages=6000424 gc_pages=5489698 WAF=1.914885
- phaseB(test4) host_pages=24000658 gc_pages=26419800 WAF=2.100795
- ycsb-load 
- ycsb-run 

### mix-20260911 mixJ fixed10 — started 2026-09-20T17:47:39+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixJ fixed10`; evidence `result/mix-20260911/mixJ-fixed10/`.

- Finished 2026-09-20T18:02:34+09:00; mixJ fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-fixed10-rep1`; cleanup attempted.
- total host_bytes=36555055104 host_pages=8924574 gc_pages=9082798 WAF=2.017729
- phaseA(sqlite-a) host_pages=8100965 gc_pages=8230699 WAF=2.016015
- phaseB(sqlite-b) host_pages=823609 gc_pages=852099 WAF=2.034592
- phaseA-load host_pages=1398349 gc_pages=1068963 WAF=1.764447
- phaseA-run host_pages=6702616 gc_pages=7161736 WAF=2.068499
- ycsb-load [OVERALL], Throughput(ops/sec), 23435.66908835247
- ycsb-run [OVERALL], Throughput(ops/sec), 13605.11824548395

### mix-20260911 mixJ fixed37 — started 2026-09-20T18:02:35+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixJ fixed37`; evidence `result/mix-20260911/mixJ-fixed37/`.

- Finished 2026-09-20T18:11:48+09:00; mixJ fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-fixed37-rep1`; cleanup attempted.
- total host_bytes=35821469696 host_pages=8745476 gc_pages=4440714 WAF=1.507773
- phaseA(sqlite-a) host_pages=8112615 gc_pages=4150672 WAF=1.511632
- phaseB(sqlite-b) host_pages=632861 gc_pages=290042 WAF=1.458303
- phaseA-load host_pages=1398349 gc_pages=597678 WAF=1.427417
- phaseA-run host_pages=6714266 gc_pages=3552994 WAF=1.529171
- ycsb-load [OVERALL], Throughput(ops/sec), 22953.328232593725
- ycsb-run [OVERALL], Throughput(ops/sec), 45374.624241393

### mix-20260911 mixJ fixed47 — started 2026-09-20T18:11:48+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixJ fixed47`; evidence `result/mix-20260911/mixJ-fixed47/`.

- Finished 2026-09-20T18:23:13+09:00; mixJ fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-fixed47-rep1`; cleanup attempted.
- total host_bytes=35593097216 host_pages=8689721 gc_pages=4061859 WAF=1.467433
- phaseA(sqlite-a) host_pages=8053355 gc_pages=3771052 WAF=1.468259
- phaseB(sqlite-b) host_pages=636366 gc_pages=290807 WAF=1.456981
- phaseA-load host_pages=1398349 gc_pages=368926 WAF=1.263830
- phaseA-run host_pages=6655006 gc_pages=3402126 WAF=1.511213
- ycsb-load [OVERALL], Throughput(ops/sec), 23912.003825920612
- ycsb-run [OVERALL], Throughput(ops/sec), 45293.44490618595

### mix-20260911 mixJ fixed50 — started 2026-09-20T18:23:14+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixJ fixed50`; evidence `result/mix-20260911/mixJ-fixed50/`.

- Finished 2026-09-20T18:32:48+09:00; mixJ fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-fixed50-rep1`; cleanup attempted.
- total host_bytes=35770232832 host_pages=8732967 gc_pages=3543145 WAF=1.405721
- phaseA(sqlite-a) host_pages=8101318 gc_pages=3302325 WAF=1.407628
- phaseB(sqlite-b) host_pages=631649 gc_pages=240820 WAF=1.381256
- phaseA-load host_pages=1398339 gc_pages=385368 WAF=1.275590
- phaseA-run host_pages=6702979 gc_pages=2916957 WAF=1.435173
- ycsb-load [OVERALL], Throughput(ops/sec), 24142.926122646066
- ycsb-run [OVERALL], Throughput(ops/sec), 44597.06551308924

### mix-20260911 mixJ online — started 2026-09-20T18:32:49+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixJ online`; evidence `result/mix-20260911/mixJ-online/`.

## 2026-09-20 — 진행 보고 및 v2 빌드 결함 정정

- 완료: 단일 sweep 180 run(SWEEPDONE 9/18 03:13), phase 길이 16 run(9/19 01:35), mix sweep 120 run(9/20 17:47). queue6(v1 mix) 재개되어 진행 중(mixJ). 실패 4건은 모두 v2 phase-length run.
- **v2 결함:** 첫 v2 빌드(hash 8a8909a1…)는 WINDOW_GC/WINDOW_HOST_PAGES만 6배로 올리고 `WATGC_V2_MAX_WINDOW_GC`(4096)를 그대로 두어, 모든 window가 4096 GC에서 강제 종료되며 host 145k < 393216로 `reason=undersized` 폐기됨(kernel.log: sample 0건, discard 536건). 학습이 전혀 일어나지 않았고 실질적으로 초기 arm37 고정 실행이었다. 해당 4 run은 `*-v2broken`으로 이름을 바꿔 보존(무효).
- 수정: MAX_WINDOW_GC 4096→24576(6배). 재빌드 hash `74d88d42…`. queue7 시작부에 phase-length v2 4 run 재실행을 추가. 다른 v2 run은 아직 시작 전이었으므로 영향 없음.
- 2026-09-20 결과 정리 (분석 스크립트 `analysis/sweep-rank.py`, `analysis/summary.py` 확장):
  - 단일 sweep: test4 1등 arm31 1.744(arm47 2등 1.746), sqlite-a 1등 **arm47** 1.157(arm17 2등 1.158, 견고 arm50 4등), oltp 1등 arm46 1.332(견고 11등, 최적 16등, 기본 17등). GitHub와 ρ: test4 0.959, sqlite-a 0.979, **oltp 0.164**(GitHub oltp 편차 7.7%로 순위가 잡음 수준이었음; 우리 편차 27%). 최악 arm10: test4 51등, sqlite-a 60등, oltp 33등.
  - mix sweep(A, C, 60 arm, seed1): A 전체 1등 arm32 1.720(arm47 3등 1.732, 0.7% 차); phase별 최적은 test4→arm47, sqlite→arm17로 다르지만 전체 최적 대비 손실 0.7%. C 전체 1등 arm47 1.751; phase별 arm49/arm47, 차이 0.4%. **phase 전환에 따른 최적 arm 변화는 존재하나 단일 고정 arm의 손실은 1% 미만.**
  - phase 길이(v1 online, seed1): mixA 전체 x1 2.123 → x3 1.920 → x6 1.848 (arm47 1.709/1.696/1.722); mixC x1 2.000 → x3 1.972 → x6 1.940 (arm47 1.751/1.772/1.770). phase가 길수록 iCAT v1이 개선되나 60분에서도 arm47 대비 7~11% 열세.
  - v1 mix seed1: D(빠름→느림) 전체 online 2.045 vs arm47 1.778; J(sqlite a→b) online 미완, 고정 arm50 1.406 최저.

- Finished 2026-09-20T18:44:41+09:00; mixJ online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-online-rep1`; cleanup attempted.
- total host_bytes=35797409792 host_pages=8739602 gc_pages=7330155 WAF=1.838729
- phaseA(sqlite-a) host_pages=8112102 gc_pages=6988664 WAF=1.861511
- phaseB(sqlite-b) host_pages=627500 gc_pages=341491 WAF=1.544209
- phaseA-load host_pages=1398350 gc_pages=916596 WAF=1.655484
- phaseA-run host_pages=6713752 gc_pages=6072068 WAF=1.904422
- ycsb-load [OVERALL], Throughput(ops/sec), 20563.438206868188
- ycsb-run [OVERALL], Throughput(ops/sec), 44995.89412466112

### mix-20260911 mixG greedy — started 2026-09-20T18:44:47+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixG greedy`; evidence `result/mix-20260911/mixG-greedy/`.

- Finished 2026-09-20T18:55:03+09:00; mixG greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-greedy-rep1`; cleanup attempted.
- total host_bytes=84252323840 host_pages=20569415 gc_pages=63234029 WAF=4.074177
- phaseA(concurrent-test4+sqlite-a) host_pages=20569415 gc_pages=63234029 WAF=4.074177
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG fixed10 — started 2026-09-20T18:55:03+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixG fixed10`; evidence `result/mix-20260911/mixG-fixed10/`.

- Finished 2026-09-20T19:06:22+09:00; mixG fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-fixed10-rep1`; cleanup attempted.
- total host_bytes=84912488448 host_pages=20730588 gc_pages=62068090 WAF=3.994034
- phaseA(concurrent-test4+sqlite-a) host_pages=20730588 gc_pages=62068090 WAF=3.994034
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG fixed37 — started 2026-09-20T19:06:22+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixG fixed37`; evidence `result/mix-20260911/mixG-fixed37/`.

- Finished 2026-09-20T19:19:31+09:00; mixG fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-fixed37-rep1`; cleanup attempted.
- total host_bytes=83909439488 host_pages=20485703 gc_pages=49449888 WAF=3.413873
- phaseA(concurrent-test4+sqlite-a) host_pages=20485703 gc_pages=49449888 WAF=3.413873
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG fixed47 — started 2026-09-20T19:19:31+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixG fixed47`; evidence `result/mix-20260911/mixG-fixed47/`.

- Finished 2026-09-20T19:32:06+09:00; mixG fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-fixed47-rep1`; cleanup attempted.
- total host_bytes=83796246528 host_pages=20458068 gc_pages=33841424 WAF=2.654185
- phaseA(concurrent-test4+sqlite-a) host_pages=20458068 gc_pages=33841424 WAF=2.654185
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG fixed50 — started 2026-09-20T19:32:06+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixG fixed50`; evidence `result/mix-20260911/mixG-fixed50/`.

- Finished 2026-09-20T19:45:01+09:00; mixG fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-fixed50-rep1`; cleanup attempted.
- total host_bytes=83897368576 host_pages=20482756 gc_pages=40947859 WAF=2.999138
- phaseA(concurrent-test4+sqlite-a) host_pages=20482756 gc_pages=40947859 WAF=2.999138
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG online — started 2026-09-20T19:45:02+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixG online`; evidence `result/mix-20260911/mixG-online/`.

- Finished 2026-09-20T19:56:06+09:00; mixG online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-online-rep1`; cleanup attempted.
- total host_bytes=84724576256 host_pages=20684711 gc_pages=59457701 WAF=3.874476
- phaseA(concurrent-test4+sqlite-a) host_pages=20684711 gc_pages=59457701 WAF=3.874476
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK greedy — started 2026-09-20T19:56:15+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixK greedy`; evidence `result/mix-20260911/mixK-greedy/`.

- Finished 2026-09-20T20:17:41+09:00; mixK greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-greedy-rep1`; cleanup attempted.
- total host_bytes=196616105984 host_pages=48001979 gc_pages=64162024 WAF=2.336654
- phaseA(test4-hot512M) host_pages=24000658 gc_pages=29964932 WAF=2.248505
- phaseB(test4-hot128M) host_pages=24001321 gc_pages=34197092 WAF=2.424800
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK fixed10 — started 2026-09-20T20:17:41+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixK fixed10`; evidence `result/mix-20260911/mixK-fixed10/`.

- Finished 2026-09-20T20:39:04+09:00; mixK fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-fixed10-rep1`; cleanup attempted.
- total host_bytes=196616167424 host_pages=48001994 gc_pages=64721540 WAF=2.348309
- phaseA(test4-hot512M) host_pages=24000670 gc_pages=30258898 WAF=2.260752
- phaseB(test4-hot128M) host_pages=24001324 gc_pages=34462642 WAF=2.435864
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK fixed37 — started 2026-09-20T20:39:04+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixK fixed37`; evidence `result/mix-20260911/mixK-fixed37/`.

- Finished 2026-09-20T21:00:27+09:00; mixK fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-fixed37-rep1`; cleanup attempted.
- total host_bytes=196700000256 host_pages=48022461 gc_pages=45796108 WAF=1.953639
- phaseA(test4-hot512M) host_pages=24021131 gc_pages=23192758 WAF=1.965515
- phaseB(test4-hot128M) host_pages=24001330 gc_pages=22603350 WAF=1.941754
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK fixed47 — started 2026-09-20T21:00:27+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixK fixed47`; evidence `result/mix-20260911/mixK-fixed47/`.

- Finished 2026-09-20T21:21:50+09:00; mixK fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-fixed47-rep1`; cleanup attempted.
- total host_bytes=196616105984 host_pages=48001979 gc_pages=37248470 WAF=1.775978
- phaseA(test4-hot512M) host_pages=24000658 gc_pages=18538272 WAF=1.772407
- phaseB(test4-hot128M) host_pages=24001321 gc_pages=18710198 WAF=1.779549
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK fixed50 — started 2026-09-20T21:21:50+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixK fixed50`; evidence `result/mix-20260911/mixK-fixed50/`.

- Finished 2026-09-20T21:43:14+09:00; mixK fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-fixed50-rep1`; cleanup attempted.
- total host_bytes=196616105984 host_pages=48001979 gc_pages=38522865 WAF=1.802527
- phaseA(test4-hot512M) host_pages=24000658 gc_pages=19515870 WAF=1.813139
- phaseB(test4-hot128M) host_pages=24001321 gc_pages=19006995 WAF=1.791915
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK online — started 2026-09-20T21:43:14+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixK online`; evidence `result/mix-20260911/mixK-online/`.

- Finished 2026-09-20T22:04:37+09:00; mixK online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-online-rep1`; cleanup attempted.
- total host_bytes=196616105984 host_pages=48001979 gc_pages=49071274 WAF=2.022276
- phaseA(test4-hot512M) host_pages=24000658 gc_pages=24062327 WAF=2.002569
- phaseB(test4-hot128M) host_pages=24001321 gc_pages=25008947 WAF=2.041982
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL greedy — started 2026-09-20T22:04:40+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixL greedy`; evidence `result/mix-20260911/mixL-greedy/`.

- Finished 2026-09-20T22:16:06+09:00; mixL greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-greedy-rep1`; cleanup attempted.
- total host_bytes=61534539776 host_pages=15023081 gc_pages=15198093 WAF=2.011650
- phaseA(alternate-fast/slow-x5) host_pages=15023081 gc_pages=15198093 WAF=2.011650
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL fixed10 — started 2026-09-20T22:16:06+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixL fixed10`; evidence `result/mix-20260911/mixL-fixed10/`.

- Finished 2026-09-20T22:27:31+09:00; mixL fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-fixed10-rep1`; cleanup attempted.
- total host_bytes=61442289664 host_pages=15000559 gc_pages=15798737 WAF=2.053210
- phaseA(alternate-fast/slow-x5) host_pages=15000559 gc_pages=15798737 WAF=2.053210
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL fixed37 — started 2026-09-20T22:27:31+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixL fixed37`; evidence `result/mix-20260911/mixL-fixed37/`.

- Finished 2026-09-20T22:38:57+09:00; mixL fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-fixed37-rep1`; cleanup attempted.
- total host_bytes=61442289664 host_pages=15000559 gc_pages=10016932 WAF=1.667771
- phaseA(alternate-fast/slow-x5) host_pages=15000559 gc_pages=10016932 WAF=1.667771
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL fixed47 — started 2026-09-20T22:38:57+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixL fixed47`; evidence `result/mix-20260911/mixL-fixed47/`.

- Finished 2026-09-20T22:50:23+09:00; mixL fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-fixed47-rep1`; cleanup attempted.
- total host_bytes=61442277376 host_pages=15000556 gc_pages=8212643 WAF=1.547489
- phaseA(alternate-fast/slow-x5) host_pages=15000556 gc_pages=8212643 WAF=1.547489
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL fixed50 — started 2026-09-20T22:50:23+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixL fixed50`; evidence `result/mix-20260911/mixL-fixed50/`.

- Finished 2026-09-20T23:01:48+09:00; mixL fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-fixed50-rep1`; cleanup attempted.
- total host_bytes=61442252800 host_pages=15000550 gc_pages=8547664 WAF=1.569823
- phaseA(alternate-fast/slow-x5) host_pages=15000550 gc_pages=8547664 WAF=1.569823
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL online — started 2026-09-20T23:01:48+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixL online`; evidence `result/mix-20260911/mixL-online/`.

- Finished 2026-09-20T23:13:14+09:00; mixL online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-online-rep1`; cleanup attempted.
- total host_bytes=61442301952 host_pages=15000562 gc_pages=11555451 WAF=1.770335
- phaseA(alternate-fast/slow-x5) host_pages=15000562 gc_pages=11555451 WAF=1.770335
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixM greedy — started 2026-09-20T23:13:20+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixM greedy`; evidence `result/mix-20260911/mixM-greedy/`.

- Finished 2026-09-20T23:24:44+09:00; mixM greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixM-greedy-rep1`; cleanup attempted.
- total host_bytes=73730080768 host_pages=18000508 gc_pages=21312147 WAF=2.183975
- phaseA(ramp-10k-to-50k) host_pages=18000508 gc_pages=21312147 WAF=2.183975
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixM fixed10 — started 2026-09-20T23:24:44+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixM fixed10`; evidence `result/mix-20260911/mixM-fixed10/`.

- Finished 2026-09-20T23:36:08+09:00; mixM fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixM-fixed10-rep1`; cleanup attempted.
- total host_bytes=73730068480 host_pages=18000505 gc_pages=21627594 WAF=2.201499
- phaseA(ramp-10k-to-50k) host_pages=18000505 gc_pages=21627594 WAF=2.201499
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixM fixed37 — started 2026-09-20T23:36:08+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixM fixed37`; evidence `result/mix-20260911/mixM-fixed37/`.

- Finished 2026-09-20T23:47:32+09:00; mixM fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixM-fixed37-rep1`; cleanup attempted.
- total host_bytes=73776201728 host_pages=18011768 gc_pages=14550155 WAF=1.807814
- phaseA(ramp-10k-to-50k) host_pages=18011768 gc_pages=14550155 WAF=1.807814
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixM fixed47 — started 2026-09-20T23:47:32+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixM fixed47`; evidence `result/mix-20260911/mixM-fixed47/`.

- Finished 2026-09-20T23:58:57+09:00; mixM fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixM-fixed47-rep1`; cleanup attempted.
- total host_bytes=73730080768 host_pages=18000508 gc_pages=12653818 WAF=1.702970
- phaseA(ramp-10k-to-50k) host_pages=18000508 gc_pages=12653818 WAF=1.702970
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixM fixed50 — started 2026-09-20T23:58:57+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixM fixed50`; evidence `result/mix-20260911/mixM-fixed50/`.

- Finished 2026-09-21T00:10:21+09:00; mixM fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixM-fixed50-rep1`; cleanup attempted.
- total host_bytes=73730048000 host_pages=18000500 gc_pages=13057620 WAF=1.725403
- phaseA(ramp-10k-to-50k) host_pages=18000500 gc_pages=13057620 WAF=1.725403
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixM online — started 2026-09-21T00:10:21+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixM online`; evidence `result/mix-20260911/mixM-online/`.

- Finished 2026-09-21T00:21:45+09:00; mixM online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixM-online-rep1`; cleanup attempted.
- total host_bytes=73809764352 host_pages=18019962 gc_pages=16211760 WAF=1.899656
- phaseA(ramp-10k-to-50k) host_pages=18019962 gc_pages=16211760 WAF=1.899656
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ greedy — started 2026-09-21T00:21:48+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixQ greedy`; evidence `result/mix-20260911/mixQ-greedy/`.

- Finished 2026-09-21T00:38:11+09:00; mixQ greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-greedy-rep1`; cleanup attempted.
- total host_bytes=98306711552 host_pages=24000662 gc_pages=29888777 WAF=2.245331
- phaseA(test4) host_pages=12000331 gc_pages=14669858 WAF=2.222454
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000331 gc_pages=15218919 WAF=2.268208
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ fixed10 — started 2026-09-21T00:38:11+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixQ fixed10`; evidence `result/mix-20260911/mixQ-fixed10/`.

- Finished 2026-09-21T00:54:34+09:00; mixQ fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-fixed10-rep1`; cleanup attempted.
- total host_bytes=98306723840 host_pages=24000665 gc_pages=30180731 WAF=2.257496
- phaseA(test4) host_pages=12000334 gc_pages=14759022 WAF=2.229884
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000331 gc_pages=15421709 WAF=2.285107
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ fixed37 — started 2026-09-21T00:54:34+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixQ fixed37`; evidence `result/mix-20260911/mixQ-fixed37/`.

- Finished 2026-09-21T01:10:58+09:00; mixQ fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-fixed37-rep1`; cleanup attempted.
- total host_bytes=98306736128 host_pages=24000668 gc_pages=21394941 WAF=1.891431
- phaseA(test4) host_pages=12000331 gc_pages=11563866 WAF=1.963629
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000337 gc_pages=9831075 WAF=1.819233
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ fixed47 — started 2026-09-21T01:10:58+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixQ fixed47`; evidence `result/mix-20260911/mixQ-fixed47/`.

- Finished 2026-09-21T01:27:21+09:00; mixQ fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-fixed47-rep1`; cleanup attempted.
- total host_bytes=98401116160 host_pages=24023710 gc_pages=17550906 WAF=1.730566
- phaseA(test4) host_pages=12023376 gc_pages=9132036 WAF=1.759523
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000334 gc_pages=8418870 WAF=1.701553
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ fixed50 — started 2026-09-21T01:27:21+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixQ fixed50`; evidence `result/mix-20260911/mixQ-fixed50/`.

- Finished 2026-09-21T01:43:44+09:00; mixQ fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-fixed50-rep1`; cleanup attempted.
- total host_bytes=98306723840 host_pages=24000665 gc_pages=18771039 WAF=1.782105
- phaseA(test4) host_pages=12000331 gc_pages=9754189 WAF=1.812827
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000334 gc_pages=9016850 WAF=1.751383
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ online — started 2026-09-21T01:43:44+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixQ online`; evidence `result/mix-20260911/mixQ-online/`.

- Finished 2026-09-21T02:00:07+09:00; mixQ online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-online-rep1`; cleanup attempted.
- total host_bytes=98306711552 host_pages=24000662 gc_pages=22471582 WAF=1.936290
- phaseA(test4) host_pages=12000331 gc_pages=12711916 WAF=2.059297
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000331 gc_pages=9759666 WAF=1.813283
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO greedy — started 2026-09-21T02:00:10+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixO greedy`; evidence `result/mix-20260911/mixO-greedy/`.

- Finished 2026-09-21T02:11:44+09:00; mixO greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-greedy-rep1`; cleanup attempted.
- total host_bytes=178009899008 host_pages=43459448 gc_pages=93630643 WAF=3.154437
- phaseA(oltp) host_pages=8808830 gc_pages=9787012 WAF=2.111046
- phaseB(varmail) host_pages=34650618 gc_pages=83843631 WAF=3.419686
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO fixed10 — started 2026-09-21T02:11:44+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixO fixed10`; evidence `result/mix-20260911/mixO-fixed10/`.

- Finished 2026-09-21T02:23:22+09:00; mixO fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-fixed10-rep1`; cleanup attempted.
- total host_bytes=172328861696 host_pages=42072476 gc_pages=92697368 WAF=3.203278
- phaseA(oltp) host_pages=8249694 gc_pages=9117090 WAF=2.105143
- phaseB(varmail) host_pages=33822782 gc_pages=83580278 WAF=3.471124
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO fixed37 — started 2026-09-21T02:23:22+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixO fixed37`; evidence `result/mix-20260911/mixO-fixed37/`.

- Finished 2026-09-21T02:34:53+09:00; mixO fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-fixed37-rep1`; cleanup attempted.
- total host_bytes=210391154688 host_pages=51365028 gc_pages=69338873 WAF=2.349924
- phaseA(oltp) host_pages=8430706 gc_pages=3747551 WAF=1.444512
- phaseB(varmail) host_pages=42934322 gc_pages=65591322 WAF=2.527713
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO fixed47 — started 2026-09-21T02:34:53+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixO fixed47`; evidence `result/mix-20260911/mixO-fixed47/`.

- Finished 2026-09-21T02:46:23+09:00; mixO fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-fixed47-rep1`; cleanup attempted.
- total host_bytes=235933261824 host_pages=57600894 gc_pages=52539010 WAF=1.912121
- phaseA(oltp) host_pages=8559385 gc_pages=2608526 WAF=1.304756
- phaseB(varmail) host_pages=49041509 gc_pages=49930484 WAF=2.018127
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO fixed50 — started 2026-09-21T02:46:23+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixO fixed50`; evidence `result/mix-20260911/mixO-fixed50/`.

- Finished 2026-09-21T02:57:53+09:00; mixO fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-fixed50-rep1`; cleanup attempted.
- total host_bytes=233266507776 host_pages=56949831 gc_pages=55860863 WAF=1.980878
- phaseA(oltp) host_pages=8676654 gc_pages=2752548 WAF=1.317236
- phaseB(varmail) host_pages=48273177 gc_pages=53108315 WAF=2.100162
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO online — started 2026-09-21T02:57:53+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixO online`; evidence `result/mix-20260911/mixO-online/`.

- Finished 2026-09-21T03:09:24+09:00; mixO online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-online-rep1`; cleanup attempted.
- total host_bytes=236383707136 host_pages=57710866 gc_pages=55769203 WAF=1.966355
- phaseA(oltp) host_pages=8644807 gc_pages=5371991 WAF=1.621412
- phaseB(varmail) host_pages=49066059 gc_pages=50397212 WAF=2.027130
- ycsb-load 
- ycsb-run 

### mix-20260911 mixP greedy — started 2026-09-21T03:09:28+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixP greedy`; evidence `result/mix-20260911/mixP-greedy/`.

- Finished 2026-09-21T03:16:50+09:00; mixP greedy exit=1; evidence `/home/oy/iCAT/result/mix-20260911/mixP-greedy-rep1`; cleanup attempted.

### mix-20260911 mixP fixed10 — started 2026-09-21T03:16:51+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixP fixed10`; evidence `result/mix-20260911/mixP-fixed10/`.

- Finished 2026-09-21T03:26:47+09:00; mixP fixed10 exit=1; evidence `/home/oy/iCAT/result/mix-20260911/mixP-fixed10-rep1`; cleanup attempted.

### mix-20260911 mixP fixed37 — started 2026-09-21T03:26:48+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixP fixed37`; evidence `result/mix-20260911/mixP-fixed37/`.

- Finished 2026-09-21T03:36:21+09:00; mixP fixed37 exit=1; evidence `/home/oy/iCAT/result/mix-20260911/mixP-fixed37-rep1`; cleanup attempted.

### mix-20260911 mixP fixed47 — started 2026-09-21T03:36:22+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixP fixed47`; evidence `result/mix-20260911/mixP-fixed47/`.

- Finished 2026-09-21T03:45:59+09:00; mixP fixed47 exit=1; evidence `/home/oy/iCAT/result/mix-20260911/mixP-fixed47-rep1`; cleanup attempted.

### mix-20260911 mixP fixed50 — started 2026-09-21T03:45:59+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixP fixed50`; evidence `result/mix-20260911/mixP-fixed50/`.

- Finished 2026-09-21T03:53:27+09:00; mixP fixed50 exit=1; evidence `/home/oy/iCAT/result/mix-20260911/mixP-fixed50-rep1`; cleanup attempted.

### mix-20260911 mixP online — started 2026-09-21T03:53:27+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixP online`; evidence `result/mix-20260911/mixP-online/`.

- Finished 2026-09-21T04:03:10+09:00; mixP online exit=1; evidence `/home/oy/iCAT/result/mix-20260911/mixP-online-rep1`; cleanup attempted.

### mix-20260911 mixH greedy — started 2026-09-21T04:03:20+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixH greedy`; evidence `result/mix-20260911/mixH-greedy/`.

- Finished 2026-09-21T04:33:22+09:00; mixH greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-greedy-rep1`; cleanup attempted.
- total host_bytes=156149231616 host_pages=38122371 gc_pages=52978819 WAF=2.389704
- phaseA(test3) host_pages=6000421 gc_pages=6924740 WAF=2.154042
- phaseB(test4) host_pages=24000658 gc_pages=30443765 WAF=2.268455
- phaseC(sqlite-a) host_pages=8121292 gc_pages=15610314 WAF=2.922147
- phaseC-load host_pages=1398349 gc_pages=1662098 WAF=2.188615
- phaseC-run host_pages=6722943 gc_pages=13948216 WAF=3.074719
- ycsb-load [OVERALL], Throughput(ops/sec), 24244.38338451592
- ycsb-run [OVERALL], Throughput(ops/sec), 8326.845333011363

### mix-20260911 mixH fixed10 — started 2026-09-21T04:33:22+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixH fixed10`; evidence `result/mix-20260911/mixH-fixed10/`.

- Finished 2026-09-21T05:03:57+09:00; mixH fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-fixed10-rep1`; cleanup attempted.
- total host_bytes=156434735104 host_pages=38192074 gc_pages=53060627 WAF=2.389310
- phaseA(test3) host_pages=6000421 gc_pages=6969190 WAF=2.161450
- phaseB(test4) host_pages=24000658 gc_pages=30402059 WAF=2.266718
- phaseC(sqlite-a) host_pages=8190995 gc_pages=15689378 WAF=2.915442
- phaseC-load host_pages=1398351 gc_pages=1677880 WAF=2.199899
- phaseC-run host_pages=6792644 gc_pages=14011498 WAF=3.062746
- ycsb-load [OVERALL], Throughput(ops/sec), 21969.16993152942
- ycsb-run [OVERALL], Throughput(ops/sec), 7837.973413594181

### mix-20260911 mixH fixed37 — started 2026-09-21T05:03:58+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixH fixed37`; evidence `result/mix-20260911/mixH-fixed37/`.

- Finished 2026-09-21T05:31:29+09:00; mixH fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-fixed37-rep1`; cleanup attempted.
- total host_bytes=156093227008 host_pages=38108698 gc_pages=32474680 WAF=1.852159
- phaseA(test3) host_pages=6000424 gc_pages=4940837 WAF=1.823415
- phaseB(test4) host_pages=24000658 gc_pages=21795975 WAF=1.908141
- phaseC(sqlite-a) host_pages=8107616 gc_pages=5737868 WAF=1.707713
- phaseC-load host_pages=1398347 gc_pages=1171735 WAF=1.837943
- phaseC-run host_pages=6709269 gc_pages=4566133 WAF=1.680571
- ycsb-load [OVERALL], Throughput(ops/sec), 22315.61721277941
- ycsb-run [OVERALL], Throughput(ops/sec), 12455.47168871285

### mix-20260911 mixH fixed47 — started 2026-09-21T05:31:29+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixH fixed47`; evidence `result/mix-20260911/mixH-fixed47/`.

- Finished 2026-09-21T06:01:15+09:00; mixH fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-fixed47-rep1`; cleanup attempted.
- total host_bytes=155922571264 host_pages=38067034 gc_pages=27443536 WAF=1.720927
- phaseA(test3) host_pages=6000418 gc_pages=4783107 WAF=1.797129
- phaseB(test4) host_pages=24000658 gc_pages=17719299 WAF=1.738284
- phaseC(sqlite-a) host_pages=8065958 gc_pages=4941130 WAF=1.612591
- phaseC-load host_pages=1398349 gc_pages=530207 WAF=1.379166
- phaseC-run host_pages=6667609 gc_pages=4410923 WAF=1.661545
- ycsb-load [OVERALL], Throughput(ops/sec), 21761.207021616134
- ycsb-run [OVERALL], Throughput(ops/sec), 8721.49434084036

### mix-20260911 mixH fixed50 — started 2026-09-21T06:01:15+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixH fixed50`; evidence `result/mix-20260911/mixH-fixed50/`.

- Finished 2026-09-21T06:28:50+09:00; mixH fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-fixed50-rep1`; cleanup attempted.
- total host_bytes=156152176640 host_pages=38123090 gc_pages=27396069 WAF=1.718621
- phaseA(test3) host_pages=6000418 gc_pages=4799461 WAF=1.799854
- phaseB(test4) host_pages=24000658 gc_pages=18538513 WAF=1.772417
- phaseC(sqlite-a) host_pages=8122014 gc_pages=4058095 WAF=1.499641
- phaseC-load host_pages=1398349 gc_pages=546587 WAF=1.390880
- phaseC-run host_pages=6723665 gc_pages=3511508 WAF=1.522261
- ycsb-load [OVERALL], Throughput(ops/sec), 23669.572764211607
- ycsb-run [OVERALL], Throughput(ops/sec), 12324.757356339547

### mix-20260911 mixH online — started 2026-09-21T06:28:51+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixH online`; evidence `result/mix-20260911/mixH-online/`.

- Finished 2026-09-21T06:56:22+09:00; mixH online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-online-rep1`; cleanup attempted.
- total host_bytes=156066177024 host_pages=38102094 gc_pages=34115794 WAF=1.895378
- phaseA(test3) host_pages=6000421 gc_pages=6791807 WAF=2.131888
- phaseB(test4) host_pages=24000667 gc_pages=23012532 WAF=1.958829
- phaseC(sqlite-a) host_pages=8101006 gc_pages=4311455 WAF=1.532212
- phaseC-load host_pages=1398346 gc_pages=773414 WAF=1.553092
- phaseC-run host_pages=6702660 gc_pages=3538041 WAF=1.527856
- ycsb-load [OVERALL], Throughput(ops/sec), 22168.852761869573
- ycsb-run [OVERALL], Throughput(ops/sec), 12567.037289541397

### mix-20260911 mixF greedy — started 2026-09-21T06:56:33+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixF greedy`; evidence `result/mix-20260911/mixF-greedy/`.

- Finished 2026-09-21T07:13:02+09:00; mixF greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-greedy-rep1`; cleanup attempted.
- total host_bytes=189061971968 host_pages=46157708 gc_pages=125265104 WAF=3.713850
- phaseA(test4) host_pages=24000661 gc_pages=29958105 WAF=2.248220
- phaseB(varmail) host_pages=22157047 gc_pages=95306999 WAF=5.301431
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF fixed10 — started 2026-09-21T07:13:02+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixF fixed10`; evidence `result/mix-20260911/mixF-fixed10/`.

- Finished 2026-09-21T07:29:29+09:00; mixF fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-fixed10-rep1`; cleanup attempted.
- total host_bytes=187825786880 host_pages=45855905 gc_pages=125697696 WAF=3.741145
- phaseA(test4) host_pages=24000664 gc_pages=30289871 WAF=2.262043
- phaseB(varmail) host_pages=21855241 gc_pages=95407825 WAF=5.365444
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF fixed37 — started 2026-09-21T07:29:29+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixF fixed37`; evidence `result/mix-20260911/mixF-fixed37/`.

- Finished 2026-09-21T07:45:55+09:00; mixF fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-fixed37-rep1`; cleanup attempted.
- total host_bytes=214319124480 host_pages=52324005 gc_pages=106145676 WAF=3.028623
- phaseA(test4) host_pages=24022176 gc_pages=22154980 WAF=1.922272
- phaseB(varmail) host_pages=28301829 gc_pages=83990696 WAF=3.967677
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF fixed47 — started 2026-09-21T07:45:55+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixF fixed47`; evidence `result/mix-20260911/mixF-fixed47/`.

- Finished 2026-09-21T08:02:21+09:00; mixF fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-fixed47-rep1`; cleanup attempted.
- total host_bytes=258488774656 host_pages=63107611 gc_pages=85432042 WAF=2.353752
- phaseA(test4) host_pages=24000658 gc_pages=18581694 WAF=1.774216
- phaseB(varmail) host_pages=39106953 gc_pages=66850348 WAF=2.709424
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF fixed50 — started 2026-09-21T08:02:21+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixF fixed50`; evidence `result/mix-20260911/mixF-fixed50/`.

- Finished 2026-09-21T08:18:48+09:00; mixF fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-fixed50-rep1`; cleanup attempted.
- total host_bytes=243526492160 host_pages=59454710 gc_pages=93157165 WAF=2.566859
- phaseA(test4) host_pages=24000661 gc_pages=19503369 WAF=1.812618
- phaseB(varmail) host_pages=35454049 gc_pages=73653796 WAF=3.077444
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF online — started 2026-09-21T08:18:48+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixF online`; evidence `result/mix-20260911/mixF-online/`.

- Finished 2026-09-21T08:35:15+09:00; mixF online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-online-rep1`; cleanup attempted.
- total host_bytes=192086953984 host_pages=46896229 gc_pages=117213728 WAF=3.499428
- phaseA(test4) host_pages=24010376 gc_pages=24066116 WAF=2.002321
- phaseB(varmail) host_pages=22885853 gc_pages=93147612 WAF=5.070096
- ycsb-load 
- ycsb-run 

### mix-20260911 mixA greedy — started 2026-09-21T08:35:21+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixA greedy`; evidence `result/mix-20260911/mixA-greedy/`.

- Finished 2026-09-21T08:55:27+09:00; mixA greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-greedy-rep2`; cleanup attempted.
- total host_bytes=131594080256 host_pages=32127461 gc_pages=45582955 WAF=2.418816
- phaseA(test4) host_pages=24000658 gc_pages=29975973 WAF=2.248965
- phaseB(sqlite-a) host_pages=8126803 gc_pages=15606982 WAF=2.920433
- phaseB-load host_pages=1398349 gc_pages=1661131 WAF=2.187923
- phaseB-run host_pages=6728454 gc_pages=13945851 WAF=3.072668
- ycsb-load [OVERALL], Throughput(ops/sec), 24614.37479488021
- ycsb-run [OVERALL], Throughput(ops/sec), 8236.062009310868

### mix-20260911 mixA fixed10 — started 2026-09-21T08:55:28+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixA fixed10`; evidence `result/mix-20260911/mixA-fixed10/`.

- Finished 2026-09-21T09:16:02+09:00; mixA fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-fixed10-rep2`; cleanup attempted.
- total host_bytes=131904544768 host_pages=32203258 gc_pages=46131359 WAF=2.432506
- phaseA(test4) host_pages=24000658 gc_pages=30322910 WAF=2.263420
- phaseB(sqlite-a) host_pages=8202600 gc_pages=15808449 WAF=2.927249
- phaseB-load host_pages=1398351 gc_pages=1688206 WAF=2.207283
- phaseB-run host_pages=6804249 gc_pages=14120243 WAF=3.075210
- ycsb-load [OVERALL], Throughput(ops/sec), 21254.738035353716
- ycsb-run [OVERALL], Throughput(ops/sec), 7825.705878670256

### mix-20260911 mixA fixed37 — started 2026-09-21T09:16:02+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixA fixed37`; evidence `result/mix-20260911/mixA-fixed37/`.

- Finished 2026-09-21T09:35:45+09:00; mixA fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-fixed37-rep2`; cleanup attempted.
- total host_bytes=131374186496 host_pages=32073776 gc_pages=29037634 WAF=1.905339
- phaseA(test4) host_pages=24009865 gc_pages=23405908 WAF=1.974845
- phaseB(sqlite-a) host_pages=8063911 gc_pages=5631726 WAF=1.698386
- phaseB-load host_pages=1398349 gc_pages=1175794 WAF=1.840844
- phaseB-run host_pages=6665562 gc_pages=4455932 WAF=1.668501
- ycsb-load [OVERALL], Throughput(ops/sec), 22131.238242779684
- ycsb-run [OVERALL], Throughput(ops/sec), 8711.882790328938

### mix-20260911 mixA fixed47 — started 2026-09-21T09:35:46+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixA fixed47`; evidence `result/mix-20260911/mixA-fixed47/`.
- 2026-09-21 09:55 queue6 진행(208/252, rep2 시작). FAIL 6건 = mixP(sqlite-a→oltp) rep1 전 정책: sqlite 60만 건+WAL 뒤 oltp fileset 생성 시 ENOSPC. mixP RECORDS 600k→250k로 축소(러너 수정), rep1 6 run은 queue7 앞부분에서 재실행. rep2/3은 수정본으로 진행. 그 외 실패 없음. mixO/mixH는 exit=0.

- Finished 2026-09-21T09:55:34+09:00; mixA fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-fixed47-rep2`; cleanup attempted.
- total host_bytes=131365404672 host_pages=32071632 gc_pages=23472781 WAF=1.731886
- phaseA(test4) host_pages=24005264 gc_pages=18575402 WAF=1.773805
- phaseB(sqlite-a) host_pages=8066368 gc_pages=4897379 WAF=1.607136
- phaseB-load host_pages=1398349 gc_pages=527674 WAF=1.377355
- phaseB-run host_pages=6668019 gc_pages=4369705 WAF=1.655323
- ycsb-load [OVERALL], Throughput(ops/sec), 21172.983273343216
- ycsb-run [OVERALL], Throughput(ops/sec), 8677.74959919644

### mix-20260911 mixA fixed50 — started 2026-09-21T09:55:34+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixA fixed50`; evidence `result/mix-20260911/mixA-fixed50/`.

- Finished 2026-09-21T10:13:08+09:00; mixA fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-fixed50-rep2`; cleanup attempted.
- total host_bytes=131546419200 host_pages=32115825 gc_pages=23517299 WAF=1.732265
- phaseA(test4) host_pages=24000658 gc_pages=19470354 WAF=1.811243
- phaseB(sqlite-a) host_pages=8115167 gc_pages=4046945 WAF=1.498689
- phaseB-load host_pages=1398349 gc_pages=542704 WAF=1.388103
- phaseB-run host_pages=6716818 gc_pages=3504241 WAF=1.521711
- ycsb-load [OVERALL], Throughput(ops/sec), 23017.608470479918
- ycsb-run [OVERALL], Throughput(ops/sec), 12368.4690618207

### mix-20260911 mixA online — started 2026-09-21T10:13:09+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixA online`; evidence `result/mix-20260911/mixA-online/`.

- Finished 2026-09-21T10:31:11+09:00; mixA online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-online-rep2`; cleanup attempted.
- total host_bytes=131802136576 host_pages=32178256 gc_pages=35732259 WAF=2.110447
- phaseA(test4) host_pages=24000670 gc_pages=23985268 WAF=1.999358
- phaseB(sqlite-a) host_pages=8177586 gc_pages=11746991 WAF=2.436486
- phaseB-load host_pages=1398345 gc_pages=1724786 WAF=2.233448
- phaseB-run host_pages=6779241 gc_pages=10022205 WAF=2.478367
- ycsb-load [OVERALL], Throughput(ops/sec), 23652.777230259788
- ycsb-run [OVERALL], Throughput(ops/sec), 11490.785826115683

### mix-20260911 mixB greedy — started 2026-09-21T10:31:21+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixB greedy`; evidence `result/mix-20260911/mixB-greedy/`.

- Finished 2026-09-21T10:50:52+09:00; mixB greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-greedy-rep2`; cleanup attempted.
- total host_bytes=131337535488 host_pages=32064828 gc_pages=82867108 WAF=3.584362
- phaseA(sqlite-a) host_pages=8064170 gc_pages=8074462 WAF=2.001276
- phaseB(test4) host_pages=24000658 gc_pages=74792646 WAF=4.116275
- phaseA-load host_pages=1401921 gc_pages=1024622 WAF=1.730870
- phaseA-run host_pages=6662249 gc_pages=7049840 WAF=2.058177
- ycsb-load [OVERALL], Throughput(ops/sec), 24903.498941601294
- ycsb-run [OVERALL], Throughput(ops/sec), 8883.795512794886

### mix-20260911 mixB fixed10 — started 2026-09-21T10:50:52+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixB fixed10`; evidence `result/mix-20260911/mixB-fixed10/`.

- Finished 2026-09-21T11:08:39+09:00; mixB fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-fixed10-rep2`; cleanup attempted.
- total host_bytes=131750764544 host_pages=32165714 gc_pages=85736579 WAF=3.665465
- phaseA(sqlite-a) host_pages=8165056 gc_pages=10145646 WAF=2.242569
- phaseB(test4) host_pages=24000658 gc_pages=75590933 WAF=4.149536
- phaseA-load host_pages=1398339 gc_pages=1095200 WAF=1.783215
- phaseA-run host_pages=6766717 gc_pages=9050446 WAF=2.337494
- ycsb-load [OVERALL], Throughput(ops/sec), 24410.089503661515
- ycsb-run [OVERALL], Throughput(ops/sec), 11747.91327690419

### mix-20260911 mixB fixed37 — started 2026-09-21T11:08:40+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixB fixed37`; evidence `result/mix-20260911/mixB-fixed37/`.

- Finished 2026-09-21T11:26:07+09:00; mixB fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-fixed37-rep2`; cleanup attempted.
- total host_bytes=131571777536 host_pages=32122016 gc_pages=70598706 WAF=3.197829
- phaseA(sqlite-a) host_pages=8121358 gc_pages=4081116 WAF=1.502516
- phaseB(test4) host_pages=24000658 gc_pages=66517590 WAF=3.771490
- phaseA-load host_pages=1401932 gc_pages=567543 WAF=1.404829
- phaseA-run host_pages=6719426 gc_pages=3513573 WAF=1.522898
- ycsb-load [OVERALL], Throughput(ops/sec), 23806.689679800023
- ycsb-run [OVERALL], Throughput(ops/sec), 12558.357115722121

### mix-20260911 mixB fixed47 — started 2026-09-21T11:26:07+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixB fixed47`; evidence `result/mix-20260911/mixB-fixed47/`.

- Finished 2026-09-21T11:45:48+09:00; mixB fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-fixed47-rep2`; cleanup attempted.
- total host_bytes=131392811008 host_pages=32078323 gc_pages=46857427 WAF=2.460719
- phaseA(sqlite-a) host_pages=8077665 gc_pages=3776079 WAF=1.467472
- phaseB(test4) host_pages=24000658 gc_pages=43081348 WAF=2.795007
- phaseA-load host_pages=1398341 gc_pages=372253 WAF=1.266210
- phaseA-run host_pages=6679324 gc_pages=3403826 WAF=1.509606
- ycsb-load [OVERALL], Throughput(ops/sec), 24414.0625
- ycsb-run [OVERALL], Throughput(ops/sec), 8654.149881221792

### mix-20260911 mixB fixed50 — started 2026-09-21T11:45:49+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixB fixed50`; evidence `result/mix-20260911/mixB-fixed50/`.

- Finished 2026-09-21T12:03:24+09:00; mixB fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-fixed50-rep2`; cleanup attempted.
- total host_bytes=131476156416 host_pages=32098671 gc_pages=51744731 WAF=2.612052
- phaseA(sqlite-a) host_pages=8098013 gc_pages=3300877 WAF=1.407616
- phaseB(test4) host_pages=24000658 gc_pages=48443854 WAF=3.018439
- phaseA-load host_pages=1398351 gc_pages=385408 WAF=1.275616
- phaseA-run host_pages=6699662 gc_pages=2915469 WAF=1.435167
- ycsb-load [OVERALL], Throughput(ops/sec), 23124.060585038733
- ycsb-run [OVERALL], Throughput(ops/sec), 12618.216919767068

### mix-20260911 mixB online — started 2026-09-21T12:03:24+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixB online`; evidence `result/mix-20260911/mixB-online/`.

- Finished 2026-09-21T12:23:09+09:00; mixB online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-online-rep2`; cleanup attempted.
- total host_bytes=131413340160 host_pages=32083335 gc_pages=70284812 WAF=3.190695
- phaseA(sqlite-a) host_pages=8082671 gc_pages=6943433 WAF=1.859052
- phaseB(test4) host_pages=24000664 gc_pages=63341379 WAF=3.639151
- phaseA-load host_pages=1398349 gc_pages=915540 WAF=1.654729
- phaseA-run host_pages=6684322 gc_pages=6027893 WAF=1.901796
- ycsb-load [OVERALL], Throughput(ops/sec), 23362.66645899852
- ycsb-run [OVERALL], Throughput(ops/sec), 8618.795006270173

### mix-20260911 mixC greedy — started 2026-09-21T12:23:19+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixC greedy`; evidence `result/mix-20260911/mixC-greedy/`.

- Finished 2026-09-21T12:44:44+09:00; mixC greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-greedy-rep2`; cleanup attempted.
- total host_bytes=122884431872 host_pages=30001082 gc_pages=37231749 WAF=2.241014
- phaseA(test3) host_pages=6000424 gc_pages=6921015 WAF=2.153421
- phaseB(test4) host_pages=24000658 gc_pages=30310734 WAF=2.262913
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC fixed10 — started 2026-09-21T12:44:44+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixC fixed10`; evidence `result/mix-20260911/mixC-fixed10/`.

- Finished 2026-09-21T13:06:07+09:00; mixC fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-fixed10-rep2`; cleanup attempted.
- total host_bytes=122884407296 host_pages=30001076 gc_pages=37770754 WAF=2.258980
- phaseA(test3) host_pages=6000415 gc_pages=6984218 WAF=2.163956
- phaseB(test4) host_pages=24000661 gc_pages=30786536 WAF=2.282737
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC fixed37 — started 2026-09-21T13:06:07+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixC fixed37`; evidence `result/mix-20260911/mixC-fixed37/`.

- Finished 2026-09-21T13:27:30+09:00; mixC fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-fixed37-rep2`; cleanup attempted.
- total host_bytes=122884444160 host_pages=30001085 gc_pages=26772056 WAF=1.892370
- phaseA(test3) host_pages=6000421 gc_pages=4948524 WAF=1.824696
- phaseB(test4) host_pages=24000664 gc_pages=21823532 WAF=1.909289
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC fixed47 — started 2026-09-21T13:27:30+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixC fixed47`; evidence `result/mix-20260911/mixC-fixed47/`.

- Finished 2026-09-21T13:48:53+09:00; mixC fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-fixed47-rep2`; cleanup attempted.
- total host_bytes=122983002112 host_pages=30025147 gc_pages=22507716 WAF=1.749629
- phaseA(test3) host_pages=6024486 gc_pages=4761130 WAF=1.790296
- phaseB(test4) host_pages=24000661 gc_pages=17746586 WAF=1.739421
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC fixed50 — started 2026-09-21T13:48:54+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixC fixed50`; evidence `result/mix-20260911/mixC-fixed50/`.

- Finished 2026-09-21T14:10:17+09:00; mixC fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-fixed50-rep2`; cleanup attempted.
- total host_bytes=122884407296 host_pages=30001076 gc_pages=23396449 WAF=1.779854
- phaseA(test3) host_pages=6000418 gc_pages=4799898 WAF=1.799927
- phaseB(test4) host_pages=24000658 gc_pages=18596551 WAF=1.774835
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC online — started 2026-09-21T14:10:17+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixC online`; evidence `result/mix-20260911/mixC-online/`.

- Finished 2026-09-21T14:31:40+09:00; mixC online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-online-rep2`; cleanup attempted.
- total host_bytes=122884395008 host_pages=30001073 gc_pages=29995197 WAF=1.999804
- phaseA(test3) host_pages=6000415 gc_pages=6838098 WAF=2.139604
- phaseB(test4) host_pages=24000658 gc_pages=23157099 WAF=1.964853
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD greedy — started 2026-09-21T14:31:43+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixD greedy`; evidence `result/mix-20260911/mixD-greedy/`.

- Finished 2026-09-21T14:53:06+09:00; mixD greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-greedy-rep2`; cleanup attempted.
- total host_bytes=122884444160 host_pages=30001085 gc_pages=37592359 WAF=2.253033
- phaseA(test4) host_pages=24000664 gc_pages=29986228 WAF=2.249392
- phaseB(test3) host_pages=6000421 gc_pages=7606131 WAF=2.267600
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD fixed10 — started 2026-09-21T14:53:06+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixD fixed10`; evidence `result/mix-20260911/mixD-fixed10/`.

- Finished 2026-09-21T15:14:29+09:00; mixD fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-fixed10-rep2`; cleanup attempted.
- total host_bytes=122884431872 host_pages=30001082 gc_pages=37784945 WAF=2.259453
- phaseA(test4) host_pages=24000667 gc_pages=30131798 WAF=2.255457
- phaseB(test3) host_pages=6000415 gc_pages=7653147 WAF=2.275436
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD fixed37 — started 2026-09-21T15:14:29+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixD fixed37`; evidence `result/mix-20260911/mixD-fixed37/`.

- Finished 2026-09-21T15:35:53+09:00; mixD fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-fixed37-rep2`; cleanup attempted.
- total host_bytes=122945179648 host_pages=30015913 gc_pages=28451191 WAF=1.947870
- phaseA(test4) host_pages=24015495 gc_pages=23347015 WAF=1.972165
- phaseB(test3) host_pages=6000418 gc_pages=5104176 WAF=1.850637
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD fixed47 — started 2026-09-21T15:35:53+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixD fixed47`; evidence `result/mix-20260911/mixD-fixed47/`.

- Finished 2026-09-21T15:57:16+09:00; mixD fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-fixed47-rep2`; cleanup attempted.
- total host_bytes=122980933632 host_pages=30024642 gc_pages=23225615 WAF=1.773552
- phaseA(test4) host_pages=24024215 gc_pages=18365207 WAF=1.764446
- phaseB(test3) host_pages=6000427 gc_pages=4860408 WAF=1.810010
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD fixed50 — started 2026-09-21T15:57:16+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixD fixed50`; evidence `result/mix-20260911/mixD-fixed50/`.

- Finished 2026-09-21T16:18:39+09:00; mixD fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-fixed50-rep2`; cleanup attempted.
- total host_bytes=122955685888 host_pages=30018478 gc_pages=24333959 WAF=1.810633
- phaseA(test4) host_pages=24018060 gc_pages=19454944 WAF=1.810013
- phaseB(test3) host_pages=6000418 gc_pages=4879015 WAF=1.813113
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD online — started 2026-09-21T16:18:39+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixD online`; evidence `result/mix-20260911/mixD-online/`.

- Finished 2026-09-21T16:40:02+09:00; mixD online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-online-rep2`; cleanup attempted.
- total host_bytes=122884431872 host_pages=30001082 gc_pages=31652599 WAF=2.055049
- phaseA(test4) host_pages=24000664 gc_pages=24054277 WAF=2.002234
- phaseB(test3) host_pages=6000418 gc_pages=7598322 WAF=2.266299
- ycsb-load 
- ycsb-run 

### mix-20260911 mixJ greedy — started 2026-09-21T16:40:06+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixJ greedy`; evidence `result/mix-20260911/mixJ-greedy/`.

- Finished 2026-09-21T16:51:22+09:00; mixJ greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-greedy-rep2`; cleanup attempted.
- total host_bytes=35580952576 host_pages=8686756 gc_pages=8859402 WAF=2.019875
- phaseA(sqlite-a) host_pages=8048816 gc_pages=8164091 WAF=2.014322
- phaseB(sqlite-b) host_pages=637940 gc_pages=695311 WAF=2.089932
- phaseA-load host_pages=1398341 gc_pages=1043073 WAF=1.745936
- phaseA-run host_pages=6650475 gc_pages=7121018 WAF=2.070753
- ycsb-load [OVERALL], Throughput(ops/sec), 26181.437360911114
- ycsb-run [OVERALL], Throughput(ops/sec), 45943.214187264544

### mix-20260911 mixJ fixed10 — started 2026-09-21T16:51:22+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixJ fixed10`; evidence `result/mix-20260911/mixJ-fixed10/`.

- Finished 2026-09-21T17:03:02+09:00; mixJ fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-fixed10-rep2`; cleanup attempted.
- total host_bytes=35757522944 host_pages=8729864 gc_pages=8918763 WAF=2.021638
- phaseA(sqlite-a) host_pages=8090215 gc_pages=8226953 WAF=2.016902
- phaseB(sqlite-b) host_pages=639649 gc_pages=691810 WAF=2.081546
- phaseA-load host_pages=1398349 gc_pages=1071600 WAF=1.766332
- phaseA-run host_pages=6691866 gc_pages=7155353 WAF=2.069261
- ycsb-load [OVERALL], Throughput(ops/sec), 23258.51843237586
- ycsb-run [OVERALL], Throughput(ops/sec), 43913.57807834182

### mix-20260911 mixJ fixed37 — started 2026-09-21T17:03:02+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixJ fixed37`; evidence `result/mix-20260911/mixJ-fixed37/`.
- 2026-09-21 학습 여부 분석(v1, 60분 phase run의 WATGC sample 10분 집계): mixA-x6 phase A(test4) iCAT 1.99→1.82(최적 arm47 1.773 대비 +12%→+2.7%), 시험 arm 수 60→23→45; phase B(sqlite) 전환 직후 2.01(+42%)이었다가 70분 이후 1.41→1.30으로 **고정 arm50의 phase 평균(1.416)보다 낮아짐**. mixC-x6: phase A 20분 만에 +2.8%까지 접근하나 40~50분에 +25%로 재이탈, phase B는 +5~13%에서 등락. 결론: 학습은 일어나며 20~30분 후 최적 고정에 2~5%까지 접근하지만 유지되지 않고 주기적으로 재탐색한다. 주의: 고정 arm은 phase 평균만 있어 같은 시간축 비교가 불가(phase 내 WAF 자체가 시간에 따라 변할 수 있음) → 러너에 30초 간격 counter 시계열(`control-series.txt`) 추가. 이후 run(v1 rep2/3, v2)부터 모든 정책의 시계열 비교 가능.

- Finished 2026-09-21T17:12:41+09:00; mixJ fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-fixed37-rep2`; cleanup attempted.
- total host_bytes=35879333888 host_pages=8759603 gc_pages=4440111 WAF=1.506885
- phaseA(sqlite-a) host_pages=8122014 gc_pages=4146539 WAF=1.510531
- phaseB(sqlite-b) host_pages=637589 gc_pages=293572 WAF=1.460441
- phaseA-load host_pages=1398339 gc_pages=604256 WAF=1.432124
- phaseA-run host_pages=6723675 gc_pages=3542283 WAF=1.526837
- ycsb-load [OVERALL], Throughput(ops/sec), 24716.7868177137
- ycsb-run [OVERALL], Throughput(ops/sec), 42848.57314251435

### mix-20260911 mixJ fixed47 — started 2026-09-21T17:12:41+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixJ fixed47`; evidence `result/mix-20260911/mixJ-fixed47/`.

- Finished 2026-09-21T17:27:12+09:00; mixJ fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-fixed47-rep2`; cleanup attempted.
- total host_bytes=36273008640 host_pages=8855715 gc_pages=3867529 WAF=1.436727
- phaseA(sqlite-a) host_pages=8030704 gc_pages=3774257 WAF=1.469978
- phaseB(sqlite-b) host_pages=825011 gc_pages=93272 WAF=1.113055
- phaseA-load host_pages=1398349 gc_pages=370015 WAF=1.264608
- phaseA-run host_pages=6632355 gc_pages=3404242 WAF=1.513278
- ycsb-load [OVERALL], Throughput(ops/sec), 23043.244488824028
- ycsb-run [OVERALL], Throughput(ops/sec), 13396.654855282635

### mix-20260911 mixJ fixed50 — started 2026-09-21T17:27:13+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixJ fixed50`; evidence `result/mix-20260911/mixJ-fixed50/`.

- Finished 2026-09-21T17:38:34+09:00; mixJ fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-fixed50-rep2`; cleanup attempted.
- total host_bytes=35563290624 host_pages=8682444 gc_pages=3889542 WAF=1.447978
- phaseA(sqlite-a) host_pages=8053391 gc_pages=3628516 WAF=1.450558
- phaseB(sqlite-b) host_pages=629053 gc_pages=261026 WAF=1.414951
- phaseA-load host_pages=1398351 gc_pages=385746 WAF=1.275858
- phaseA-run host_pages=6655040 gc_pages=3242770 WAF=1.487265
- ycsb-load [OVERALL], Throughput(ops/sec), 23298.256513804216
- ycsb-run [OVERALL], Throughput(ops/sec), 45114.13877109086

### mix-20260911 mixJ online — started 2026-09-21T17:38:35+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixJ online`; evidence `result/mix-20260911/mixJ-online/`.

- Finished 2026-09-21T17:50:16+09:00; mixJ online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-online-rep2`; cleanup attempted.
- total host_bytes=35802906624 host_pages=8740944 gc_pages=7260320 WAF=1.830611
- phaseA(sqlite-a) host_pages=8104789 gc_pages=6914922 WAF=1.853190
- phaseB(sqlite-b) host_pages=636155 gc_pages=345398 WAF=1.542946
- phaseA-load host_pages=1405509 gc_pages=905728 WAF=1.644413
- phaseA-run host_pages=6699280 gc_pages=6009194 WAF=1.896991
- ycsb-load [OVERALL], Throughput(ops/sec), 23339.038431616616
- ycsb-run [OVERALL], Throughput(ops/sec), 45148.25558427486

### mix-20260911 mixG greedy — started 2026-09-21T17:50:23+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixG greedy`; evidence `result/mix-20260911/mixG-greedy/`.

- Finished 2026-09-21T18:01:10+09:00; mixG greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-greedy-rep2`; cleanup attempted.
- total host_bytes=84208742400 host_pages=20558775 gc_pages=63557591 WAF=4.091507
- phaseA(concurrent-test4+sqlite-a) host_pages=20558775 gc_pages=63557591 WAF=4.091507
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG fixed10 — started 2026-09-21T18:01:10+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixG fixed10`; evidence `result/mix-20260911/mixG-fixed10/`.

- Finished 2026-09-21T18:12:24+09:00; mixG fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-fixed10-rep2`; cleanup attempted.
- total host_bytes=84865671168 host_pages=20719158 gc_pages=62043174 WAF=3.994483
- phaseA(concurrent-test4+sqlite-a) host_pages=20719158 gc_pages=62043174 WAF=3.994483
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG fixed37 — started 2026-09-21T18:12:24+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixG fixed37`; evidence `result/mix-20260911/mixG-fixed37/`.

- Finished 2026-09-21T18:23:12+09:00; mixG fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-fixed37-rep2`; cleanup attempted.
- total host_bytes=84580855808 host_pages=20649623 gc_pages=53891560 WAF=3.609808
- phaseA(concurrent-test4+sqlite-a) host_pages=20649623 gc_pages=53891560 WAF=3.609808
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG fixed47 — started 2026-09-21T18:23:12+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixG fixed47`; evidence `result/mix-20260911/mixG-fixed47/`.

- Finished 2026-09-21T18:35:53+09:00; mixG fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-fixed47-rep2`; cleanup attempted.
- total host_bytes=83630948352 host_pages=20417712 gc_pages=34799046 WAF=2.704356
- phaseA(concurrent-test4+sqlite-a) host_pages=20417712 gc_pages=34799046 WAF=2.704356
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG fixed50 — started 2026-09-21T18:35:53+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixG fixed50`; evidence `result/mix-20260911/mixG-fixed50/`.

### 사전 등록 2026-09-21 — "아주 느린 3영역 쓰기" 60-arm sweep (queue10, queue7 뒤 자동 시작)

- **질문**: 지금까지의 워크로드는 전부 "빠름"(뜨거운 구역 한 바퀴 5~20초)이라 1등 조합이 scale 25~50%에 몰려 있고, 고정 arm 하나로 어느 mix든 1% 미만 손해다. 덮어쓰기 주기가 분 단위로 느려지면 1등이 scale 200~400%로 옮겨 가는가? (옮겨 가야 "앞뒤 구간 1등이 정반대인 mix"를 만들 수 있고, 그래야 iCAT에게 공정한 시험이 된다.)
- **근거**: CAT 나이 문턱은 절대 시간이다 (`threshold_thirds × scale%/300` 초; k10·scale25% = 1.7~90초, scale400% = 27~1440초). 뜨거운 구역 한 바퀴가 87초면 25% 문턱은 전부 "오래됨"으로 뭉개진다.
- **워크로드**: `workloads/gh-test4-slow16.fio` = 빠른 3영역 쓰기(test4)와 배치 동일, IOPS 1/16 (1500/750/250 = 합계 2500), runtime 1200 s (≈12 GB 쓰기). 뜨거운 512 MiB 한 바퀴 ≈ 87초, 미지근 ≈ 524초, 차가움 ≈ 70분.
- **조건**: GitHub 계측 방식(`gh-fio.sh`, warmup 100 GC, rmmod 시 카운터). greedy(`nvmev-gh-greedy.ko`) + arm00~59 (`buildoutput/nvmev-armNN.ko`, hash `result/sweep-20260915/modules.sha256`). 1회씩. 예상 소요 ≈ 22시간.
- **판정**: `analysis/sweep-rank.py slow16` → `result/sweep-slow16-20260921/rank-slow16.txt`.
  - 1등 scale ≥ 200% 이고 arm47(k10,s25,r16)이 1등 대비 ≥3% 나쁘면 → 가설 채택, "빠른 → 아주 느린" mix(mixR) 설계로 진행.
  - 1등이 여전히 scale 25~50%이면 → 가설 기각. "느린 워크로드로 novelty 확보" 방향은 폐기하고 그대로 기록.
- **명령**: `script/gh-queue10-slow16.sh` (QUEUE7DONE 대기 → 실행). 로그 `scratchpad/queue10.out`.

- Finished 2026-09-21T18:48:53+09:00; mixG fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-fixed50-rep2`; cleanup attempted.
- total host_bytes=83853844480 host_pages=20472130 gc_pages=41055885 WAF=3.005453
- phaseA(concurrent-test4+sqlite-a) host_pages=20472130 gc_pages=41055885 WAF=3.005453
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG online — started 2026-09-21T18:48:54+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixG online`; evidence `result/mix-20260911/mixG-online/`.

- Finished 2026-09-21T19:02:31+09:00; mixG online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-online-rep2`; cleanup attempted.
- total host_bytes=84152717312 host_pages=20545097 gc_pages=55643161 WAF=3.708343
- phaseA(concurrent-test4+sqlite-a) host_pages=20545097 gc_pages=55643161 WAF=3.708343
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK greedy — started 2026-09-21T19:02:38+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixK greedy`; evidence `result/mix-20260911/mixK-greedy/`.

- Finished 2026-09-21T19:24:04+09:00; mixK greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-greedy-rep2`; cleanup attempted.
- total host_bytes=196616118272 host_pages=48001982 gc_pages=64231669 WAF=2.338105
- phaseA(test4-hot512M) host_pages=24000658 gc_pages=30012997 WAF=2.250507
- phaseB(test4-hot128M) host_pages=24001324 gc_pages=34218672 WAF=2.425699
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK fixed10 — started 2026-09-21T19:24:04+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixK fixed10`; evidence `result/mix-20260911/mixK-fixed10/`.

- Finished 2026-09-21T19:45:27+09:00; mixK fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-fixed10-rep2`; cleanup attempted.
- total host_bytes=196616142848 host_pages=48001988 gc_pages=64737195 WAF=2.348636
- phaseA(test4-hot512M) host_pages=24000661 gc_pages=30302034 WAF=2.262550
- phaseB(test4-hot128M) host_pages=24001327 gc_pages=34435161 WAF=2.434719
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK fixed37 — started 2026-09-21T19:45:27+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixK fixed37`; evidence `result/mix-20260911/mixK-fixed37/`.

- Finished 2026-09-21T20:06:50+09:00; mixK fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-fixed37-rep2`; cleanup attempted.
- total host_bytes=196616167424 host_pages=48001994 gc_pages=45915371 WAF=1.956530
- phaseA(test4-hot512M) host_pages=24000667 gc_pages=23344440 WAF=1.972658
- phaseB(test4-hot128M) host_pages=24001327 gc_pages=22570931 WAF=1.940403
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK fixed47 — started 2026-09-21T20:06:50+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixK fixed47`; evidence `result/mix-20260911/mixK-fixed47/`.

- Finished 2026-09-21T20:28:13+09:00; mixK fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-fixed47-rep2`; cleanup attempted.
- total host_bytes=196622405632 host_pages=48003517 gc_pages=37312853 WAF=1.777294
- phaseA(test4-hot512M) host_pages=24002196 gc_pages=18572054 WAF=1.773765
- phaseB(test4-hot128M) host_pages=24001321 gc_pages=18740799 WAF=1.780824
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK fixed50 — started 2026-09-21T20:28:13+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixK fixed50`; evidence `result/mix-20260911/mixK-fixed50/`.

- Finished 2026-09-21T20:49:37+09:00; mixK fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-fixed50-rep2`; cleanup attempted.
- total host_bytes=196649701376 host_pages=48010181 gc_pages=38522053 WAF=1.802373
- phaseA(test4-hot512M) host_pages=24008854 gc_pages=19521124 WAF=1.813080
- phaseB(test4-hot128M) host_pages=24001327 gc_pages=19000929 WAF=1.791662
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK online — started 2026-09-21T20:49:37+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixK online`; evidence `result/mix-20260911/mixK-online/`.

- Finished 2026-09-21T21:11:00+09:00; mixK online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-online-rep2`; cleanup attempted.
- total host_bytes=196616118272 host_pages=48001982 gc_pages=49118299 WAF=2.023256
- phaseA(test4-hot512M) host_pages=24000658 gc_pages=24072433 WAF=2.002991
- phaseB(test4-hot128M) host_pages=24001324 gc_pages=25045866 WAF=2.043520
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL greedy — started 2026-09-21T21:11:04+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixL greedy`; evidence `result/mix-20260911/mixL-greedy/`.

- Finished 2026-09-21T21:22:30+09:00; mixL greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-greedy-rep2`; cleanup attempted.
- total host_bytes=61467467776 host_pages=15006706 gc_pages=15585256 WAF=2.038553
- phaseA(alternate-fast/slow-x5) host_pages=15006706 gc_pages=15585256 WAF=2.038553
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL fixed10 — started 2026-09-21T21:22:30+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixL fixed10`; evidence `result/mix-20260911/mixL-fixed10/`.

## 2026-09-21 — iCAT v2 설계 변경 (queue7 시작 전, 장치 사용 없음)

- **문제**: 09-15 v2(판단 구간 ×6, `74d88d42…`)는 강제 순회(60 arm × MIN_VISITS 3 × 약 60초 window)가 **약 3시간**이라 어떤 run(10~60분)보다 길다. 학습 시작 전에 실험이 끝난다. (v1은 60 × 3 × 10초 = 30분.)
- **사용자 결정**: 판단 구간을 줄이고 강제 순회도 줄인다.
- **변경** (`online-v2-src/conv_ftl.h`, v1 대비):
  - `WATGC_V2_WINDOW_GC` 64 → **192** (×3; 09-15 안은 384)
  - `WATGC_V2_WINDOW_HOST_PAGES` 65536 → **196608** (256 MiB → 768 MiB, ×3)
  - `WATGC_V2_MAX_WINDOW_GC` 4096 → **12288** (×3, v1과 같은 cap/window 비율)
  - `WATGC_V2_MIN_VISITS` 3 → **1** (강제 순회 60 × 1 × ~30초 ≈ 30분, v1과 같음)
  - 그 외 무변경 (γ, c, STABLE 12, TOLERANCE 0.5%, PROBE 8, STALE 240, DRIFT 12.5%×3).
- **기대**: window당 잡음 v1의 1/√3 (0.385 → ≈0.22; arm 간 차이 0.098). 부작용: STABLE/STALE/DRIFT는 window 수 기준이므로 시간으로는 3배 길어짐 (STALE 240 window ≈ 2시간 → 실험 안에서는 STALE 재탐색이 사실상 없음; 이것도 기록).
- **모듈** `buildoutput/nvmev-online-v2.ko` SHA256 `74734ee6…` (이전 `74d88d42…`는 폐기; 그 모듈로 낸 결과는 `*-v2broken` 4건뿐이며 모두 MAX_WINDOW_GC 결함으로 무효). 빌드 로그 `result/gh-repro-20260914/build-online-v2c.log`.
- 09-15 사전 등록의 실행 목록·판정 기준은 그대로 유지. queue7은 아직 QUEUE6DONE 대기 중이므로 새 모듈로 실행된다.

- Finished 2026-09-21T21:33:55+09:00; mixL fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-fixed10-rep2`; cleanup attempted.
- total host_bytes=61480001536 host_pages=15009766 gc_pages=15591678 WAF=2.038769
- phaseA(alternate-fast/slow-x5) host_pages=15009766 gc_pages=15591678 WAF=2.038769
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL fixed37 — started 2026-09-21T21:33:55+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixL fixed37`; evidence `result/mix-20260911/mixL-fixed37/`.

- Finished 2026-09-21T21:45:21+09:00; mixL fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-fixed37-rep2`; cleanup attempted.
- total host_bytes=61442252800 host_pages=15000550 gc_pages=10013118 WAF=1.667517
- phaseA(alternate-fast/slow-x5) host_pages=15000550 gc_pages=10013118 WAF=1.667517
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL fixed47 — started 2026-09-21T21:45:21+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixL fixed47`; evidence `result/mix-20260911/mixL-fixed47/`.

- Finished 2026-09-21T21:56:47+09:00; mixL fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-fixed47-rep2`; cleanup attempted.
- total host_bytes=61442252800 host_pages=15000550 gc_pages=8200463 WAF=1.546677
- phaseA(alternate-fast/slow-x5) host_pages=15000550 gc_pages=8200463 WAF=1.546677
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL fixed50 — started 2026-09-21T21:56:47+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixL fixed50`; evidence `result/mix-20260911/mixL-fixed50/`.

- Finished 2026-09-21T22:08:12+09:00; mixL fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-fixed50-rep2`; cleanup attempted.
- total host_bytes=61442277376 host_pages=15000556 gc_pages=8542776 WAF=1.569497
- phaseA(alternate-fast/slow-x5) host_pages=15000556 gc_pages=8542776 WAF=1.569497
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL online — started 2026-09-21T22:08:12+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixL online`; evidence `result/mix-20260911/mixL-online/`.

- Finished 2026-09-21T22:19:38+09:00; mixL online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-online-rep2`; cleanup attempted.
- total host_bytes=61442269184 host_pages=15000554 gc_pages=11524880 WAF=1.768297
- phaseA(alternate-fast/slow-x5) host_pages=15000554 gc_pages=11524880 WAF=1.768297
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixM greedy — started 2026-09-21T22:19:41+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixM greedy`; evidence `result/mix-20260911/mixM-greedy/`.

- Finished 2026-09-21T22:31:05+09:00; mixM greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixM-greedy-rep2`; cleanup attempted.
- total host_bytes=73730056192 host_pages=18000502 gc_pages=21342847 WAF=2.185681
- phaseA(ramp-10k-to-50k) host_pages=18000502 gc_pages=21342847 WAF=2.185681
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixM fixed10 — started 2026-09-21T22:31:05+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixM fixed10`; evidence `result/mix-20260911/mixM-fixed10/`.

- Finished 2026-09-21T22:42:29+09:00; mixM fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixM-fixed10-rep2`; cleanup attempted.
- total host_bytes=73730080768 host_pages=18000508 gc_pages=21585991 WAF=2.199188
- phaseA(ramp-10k-to-50k) host_pages=18000508 gc_pages=21585991 WAF=2.199188
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixM fixed37 — started 2026-09-21T22:42:29+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixM fixed37`; evidence `result/mix-20260911/mixM-fixed37/`.

- Finished 2026-09-21T22:53:53+09:00; mixM fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixM-fixed37-rep2`; cleanup attempted.
- total host_bytes=73730080768 host_pages=18000508 gc_pages=14550863 WAF=1.808358
- phaseA(ramp-10k-to-50k) host_pages=18000508 gc_pages=14550863 WAF=1.808358
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixM fixed47 — started 2026-09-21T22:53:53+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixM fixed47`; evidence `result/mix-20260911/mixM-fixed47/`.

- Finished 2026-09-21T23:05:18+09:00; mixM fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixM-fixed47-rep2`; cleanup attempted.
- total host_bytes=73730080768 host_pages=18000508 gc_pages=12654554 WAF=1.703011
- phaseA(ramp-10k-to-50k) host_pages=18000508 gc_pages=12654554 WAF=1.703011
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixM fixed50 — started 2026-09-21T23:05:18+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixM fixed50`; evidence `result/mix-20260911/mixM-fixed50/`.

- Finished 2026-09-21T23:16:42+09:00; mixM fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixM-fixed50-rep2`; cleanup attempted.
- total host_bytes=73730068480 host_pages=18000505 gc_pages=13060496 WAF=1.725563
- phaseA(ramp-10k-to-50k) host_pages=18000505 gc_pages=13060496 WAF=1.725563
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixM online — started 2026-09-21T23:16:42+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixM online`; evidence `result/mix-20260911/mixM-online/`.

- Finished 2026-09-21T23:28:06+09:00; mixM online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixM-online-rep2`; cleanup attempted.
- total host_bytes=73795059712 host_pages=18016372 gc_pages=16257310 WAF=1.902363
- phaseA(ramp-10k-to-50k) host_pages=18016372 gc_pages=16257310 WAF=1.902363
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ greedy — started 2026-09-21T23:28:09+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixQ greedy`; evidence `result/mix-20260911/mixQ-greedy/`.

- Finished 2026-09-21T23:44:32+09:00; mixQ greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-greedy-rep2`; cleanup attempted.
- total host_bytes=98306711552 host_pages=24000662 gc_pages=29854951 WAF=2.243922
- phaseA(test4) host_pages=12000331 gc_pages=14629922 WAF=2.219127
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000331 gc_pages=15225029 WAF=2.268717
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ fixed10 — started 2026-09-21T23:44:32+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixQ fixed10`; evidence `result/mix-20260911/mixQ-fixed10/`.

- Finished 2026-09-22T00:00:55+09:00; mixQ fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-fixed10-rep2`; cleanup attempted.
- total host_bytes=98306711552 host_pages=24000662 gc_pages=30179398 WAF=2.257440
- phaseA(test4) host_pages=12000331 gc_pages=14786682 WAF=2.232190
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000331 gc_pages=15392716 WAF=2.282691
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ fixed37 — started 2026-09-22T00:00:55+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixQ fixed37`; evidence `result/mix-20260911/mixQ-fixed37/`.

- Finished 2026-09-22T00:17:18+09:00; mixQ fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-fixed37-rep2`; cleanup attempted.
- total host_bytes=98420228096 host_pages=24028376 gc_pages=20580111 WAF=1.856492
- phaseA(test4) host_pages=12011097 gc_pages=10801229 WAF=1.899271
- phaseB(idle-300s) host_pages=10800 gc_pages=7307 WAF=1.676574
- phaseC(test4) host_pages=12006479 gc_pages=9771575 WAF=1.813859
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ fixed47 — started 2026-09-22T00:17:18+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixQ fixed47`; evidence `result/mix-20260911/mixQ-fixed47/`.

- Finished 2026-09-22T00:33:42+09:00; mixQ fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-fixed47-rep2`; cleanup attempted.
- total host_bytes=98306809856 host_pages=24000686 gc_pages=17748526 WAF=1.739501
- phaseA(test4) host_pages=12000355 gc_pages=9311355 WAF=1.775923
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000331 gc_pages=8437171 WAF=1.703078
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ fixed50 — started 2026-09-22T00:33:42+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixQ fixed50`; evidence `result/mix-20260911/mixQ-fixed50/`.

- Finished 2026-09-22T00:50:05+09:00; mixQ fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-fixed50-rep2`; cleanup attempted.
- total host_bytes=98420195328 host_pages=24028368 gc_pages=18194190 WAF=1.757196
- phaseA(test4) host_pages=12010068 gc_pages=9294781 WAF=1.773916
- phaseB(idle-300s) host_pages=10282 gc_pages=4621 WAF=1.449426
- phaseC(test4) host_pages=12008018 gc_pages=8894788 WAF=1.740737
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ online — started 2026-09-22T00:50:05+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixQ online`; evidence `result/mix-20260911/mixQ-online/`.

- Finished 2026-09-22T01:06:28+09:00; mixQ online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-online-rep2`; cleanup attempted.
- total host_bytes=98310930432 host_pages=24001692 gc_pages=22474524 WAF=1.936372
- phaseA(test4) host_pages=12001355 gc_pages=12719879 WAF=2.059870
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000337 gc_pages=9754645 WAF=1.812864
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO greedy — started 2026-09-22T01:06:31+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixO greedy`; evidence `result/mix-20260911/mixO-greedy/`.

- Finished 2026-09-22T01:18:02+09:00; mixO greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-greedy-rep2`; cleanup attempted.
- total host_bytes=186015854592 host_pages=45414027 gc_pages=93734717 WAF=3.064004
- phaseA(oltp) host_pages=9766288 gc_pages=10651328 WAF=2.090622
- phaseB(varmail) host_pages=35647739 gc_pages=83083389 WAF=3.330678
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO fixed10 — started 2026-09-22T01:18:02+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixO fixed10`; evidence `result/mix-20260911/mixO-fixed10/`.

- Finished 2026-09-22T01:29:32+09:00; mixO fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-fixed10-rep2`; cleanup attempted.
- total host_bytes=176280481792 host_pages=43037227 gc_pages=94018900 WAF=3.184595
- phaseA(oltp) host_pages=8791440 gc_pages=9671831 WAF=2.100142
- phaseB(varmail) host_pages=34245787 gc_pages=84347069 WAF=3.462991
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO fixed37 — started 2026-09-22T01:29:32+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixO fixed37`; evidence `result/mix-20260911/mixO-fixed37/`.

- Finished 2026-09-22T01:41:02+09:00; mixO fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-fixed37-rep2`; cleanup attempted.
- total host_bytes=229385588736 host_pages=56002341 gc_pages=74043606 WAF=2.322152
- phaseA(oltp) host_pages=8650941 gc_pages=3500460 WAF=1.404633
- phaseB(varmail) host_pages=47351400 gc_pages=70543146 WAF=2.489780
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO fixed47 — started 2026-09-22T01:41:02+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixO fixed47`; evidence `result/mix-20260911/mixO-fixed47/`.

- Finished 2026-09-22T01:52:32+09:00; mixO fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-fixed47-rep2`; cleanup attempted.
- total host_bytes=259153051648 host_pages=63269788 gc_pages=46277835 WAF=1.731437
- phaseA(oltp) host_pages=8841502 gc_pages=2704508 WAF=1.305888
- phaseB(varmail) host_pages=54428286 gc_pages=43573327 WAF=1.800564
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO fixed50 — started 2026-09-22T01:52:32+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixO fixed50`; evidence `result/mix-20260911/mixO-fixed50/`.

- Finished 2026-09-22T02:04:02+09:00; mixO fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-fixed50-rep2`; cleanup attempted.
- total host_bytes=254172639232 host_pages=62053867 gc_pages=62095566 WAF=2.000672
- phaseA(oltp) host_pages=8829402 gc_pages=2800798 WAF=1.317213
- phaseB(varmail) host_pages=53224465 gc_pages=59294768 WAF=2.114051
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO online — started 2026-09-22T02:04:02+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixO online`; evidence `result/mix-20260911/mixO-online/`.

- Finished 2026-09-22T02:15:32+09:00; mixO online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-online-rep2`; cleanup attempted.
- total host_bytes=259470630912 host_pages=63347322 gc_pages=57989204 WAF=1.915417
- phaseA(oltp) host_pages=9091670 gc_pages=5409241 WAF=1.594967
- phaseB(varmail) host_pages=54255652 gc_pages=52579963 WAF=1.969115
- ycsb-load 
- ycsb-run 

### mix-20260911 mixP greedy — started 2026-09-22T02:15:36+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixP greedy`; evidence `result/mix-20260911/mixP-greedy/`.

- Finished 2026-09-22T02:23:35+09:00; mixP greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-greedy-rep2`; cleanup attempted.
- total host_bytes=42611650560 host_pages=10403235 gc_pages=10736007 WAF=2.031987
- phaseA(sqlite-a) host_pages=805438 gc_pages=377877 WAF=1.469157
- phaseB(oltp) host_pages=9597797 gc_pages=10358130 WAF=2.079220
- phaseA-load host_pages=453849 gc_pages=270512 WAF=1.596040
- phaseA-run host_pages=351589 gc_pages=107365 WAF=1.305371
- ycsb-load [OVERALL], Throughput(ops/sec), 25375.55826228177
- ycsb-run [OVERALL], Throughput(ops/sec), 52426.70091877793

### mix-20260911 mixP fixed10 — started 2026-09-22T02:23:36+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixP fixed10`; evidence `result/mix-20260911/mixP-fixed10/`.

- Finished 2026-09-22T02:31:25+09:00; mixP fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-fixed10-rep2`; cleanup attempted.
- total host_bytes=39041056768 host_pages=9531508 gc_pages=9859349 WAF=2.034396
- phaseA(sqlite-a) host_pages=713211 gc_pages=397461 WAF=1.557284
- phaseB(oltp) host_pages=8818297 gc_pages=9461888 WAF=2.072984
- phaseA-load host_pages=452310 gc_pages=292356 WAF=1.646362
- phaseA-run host_pages=260901 gc_pages=105105 WAF=1.402854
- ycsb-load [OVERALL], Throughput(ops/sec), 27961.07817917459
- ycsb-run [OVERALL], Throughput(ops/sec), 65913.06067297235

### mix-20260911 mixP fixed37 — started 2026-09-22T02:31:25+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixP fixed37`; evidence `result/mix-20260911/mixP-fixed37/`.

- Finished 2026-09-22T02:39:09+09:00; mixP fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-fixed37-rep2`; cleanup attempted.
- total host_bytes=41354145792 host_pages=10096227 gc_pages=2426287 WAF=1.240316
- phaseA(sqlite-a) host_pages=707851 gc_pages=302341 WAF=1.427125
- phaseB(oltp) host_pages=9388376 gc_pages=2123946 WAF=1.226231
- phaseA-load host_pages=452312 gc_pages=216526 WAF=1.478709
- phaseA-run host_pages=255539 gc_pages=85815 WAF=1.335820
- ycsb-load [OVERALL], Throughput(ops/sec), 31581.606872157656
- ycsb-run [OVERALL], Throughput(ops/sec), 69576.10756466229

### mix-20260911 mixP fixed47 — started 2026-09-22T02:39:10+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixP fixed47`; evidence `result/mix-20260911/mixP-fixed47/`.

- Finished 2026-09-22T02:47:10+09:00; mixP fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-fixed47-rep2`; cleanup attempted.
- total host_bytes=40273002496 host_pages=9832276 gc_pages=1653077 WAF=1.168128
- phaseA(sqlite-a) host_pages=795117 gc_pages=207216 WAF=1.260611
- phaseB(oltp) host_pages=9037159 gc_pages=1445861 WAF=1.159991
- phaseA-load host_pages=452310 gc_pages=124302 WAF=1.274816
- phaseA-run host_pages=342807 gc_pages=82914 WAF=1.241868
- ycsb-load [OVERALL], Throughput(ops/sec), 30618.49357011635
- ycsb-run [OVERALL], Throughput(ops/sec), 55021.389565193465

### mix-20260911 mixP fixed50 — started 2026-09-22T02:47:11+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixP fixed50`; evidence `result/mix-20260911/mixP-fixed50/`.

- Finished 2026-09-22T02:55:05+09:00; mixP fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-fixed50-rep2`; cleanup attempted.
- total host_bytes=41843068928 host_pages=10215593 gc_pages=1591574 WAF=1.155798
- phaseA(sqlite-a) host_pages=797021 gc_pages=205413 WAF=1.257726
- phaseB(oltp) host_pages=9418572 gc_pages=1386161 WAF=1.147173
- phaseA-load host_pages=452310 gc_pages=125168 WAF=1.276731
- phaseA-run host_pages=344711 gc_pages=80245 WAF=1.232789
- ycsb-load [OVERALL], Throughput(ops/sec), 25316.45569620253
- ycsb-run [OVERALL], Throughput(ops/sec), 62399.575682885355

### mix-20260911 mixP online — started 2026-09-22T02:55:06+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixP online`; evidence `result/mix-20260911/mixP-online/`.

- Finished 2026-09-22T03:02:54+09:00; mixP online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-online-rep2`; cleanup attempted.
- total host_bytes=41290629120 host_pages=10080720 gc_pages=1794205 WAF=1.177984
- phaseA(sqlite-a) host_pages=711918 gc_pages=296369 WAF=1.416297
- phaseB(oltp) host_pages=9368802 gc_pages=1497836 WAF=1.159875
- phaseA-load host_pages=452310 gc_pages=202550 WAF=1.447812
- phaseA-run host_pages=259608 gc_pages=93819 WAF=1.361387
- ycsb-load [OVERALL], Throughput(ops/sec), 24767.188428769565
- ycsb-run [OVERALL], Throughput(ops/sec), 63940.66306467598

### mix-20260911 mixH greedy — started 2026-09-22T03:03:02+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixH greedy`; evidence `result/mix-20260911/mixH-greedy/`.

- Finished 2026-09-22T03:30:59+09:00; mixH greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-greedy-rep2`; cleanup attempted.
- total host_bytes=156251406336 host_pages=38147316 gc_pages=52622426 WAF=2.379453
- phaseA(test3) host_pages=6021920 gc_pages=6898832 WAF=2.145620
- phaseB(test4) host_pages=24000661 gc_pages=30513103 WAF=2.271344
- phaseC(sqlite-a) host_pages=8124735 gc_pages=15210491 WAF=2.872121
- phaseC-load host_pages=1398347 gc_pages=1660681 WAF=2.187603
- phaseC-run host_pages=6726388 gc_pages=13549810 WAF=3.014426
- ycsb-load [OVERALL], Throughput(ops/sec), 23297.35186767104
- ycsb-run [OVERALL], Throughput(ops/sec), 12095.40858290193

### mix-20260911 mixH fixed10 — started 2026-09-22T03:30:59+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixH fixed10`; evidence `result/mix-20260911/mixH-fixed10/`.

- Finished 2026-09-22T03:59:08+09:00; mixH fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-fixed10-rep2`; cleanup attempted.
- total host_bytes=156529512448 host_pages=38215213 gc_pages=52685684 WAF=2.378657
- phaseA(test3) host_pages=6000421 gc_pages=6955023 WAF=2.159089
- phaseB(test4) host_pages=24000664 gc_pages=30530645 WAF=2.272075
- phaseC(sqlite-a) host_pages=8214128 gc_pages=15200016 WAF=2.850472
- phaseC-load host_pages=1398349 gc_pages=1686478 WAF=2.206049
- phaseC-run host_pages=6815779 gc_pages=13513538 WAF=2.982684
- ycsb-load [OVERALL], Throughput(ops/sec), 20936.562216484053
- ycsb-run [OVERALL], Throughput(ops/sec), 11211.139388096011

### mix-20260911 mixH fixed37 — started 2026-09-22T03:59:09+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixH fixed37`; evidence `result/mix-20260911/mixH-fixed37/`.

- Finished 2026-09-22T04:26:38+09:00; mixH fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-fixed37-rep2`; cleanup attempted.
- total host_bytes=156090208256 host_pages=38107961 gc_pages=32400523 WAF=1.850230
- phaseA(test3) host_pages=6000415 gc_pages=4928979 WAF=1.821440
- phaseB(test4) host_pages=24000673 gc_pages=21709479 WAF=1.904536
- phaseC(sqlite-a) host_pages=8106873 gc_pages=5762065 WAF=1.710763
- phaseC-load host_pages=1398349 gc_pages=1184645 WAF=1.847174
- phaseC-run host_pages=6708524 gc_pages=4577420 WAF=1.682329
- ycsb-load [OVERALL], Throughput(ops/sec), 23015.84257163681
- ycsb-run [OVERALL], Throughput(ops/sec), 12519.483446113014

### mix-20260911 mixH fixed47 — started 2026-09-22T04:26:39+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixH fixed47`; evidence `result/mix-20260911/mixH-fixed47/`.

- Finished 2026-09-22T04:54:03+09:00; mixH fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-fixed47-rep2`; cleanup attempted.
- total host_bytes=156037996544 host_pages=38095214 gc_pages=26612664 WAF=1.698583
- phaseA(test3) host_pages=6000418 gc_pages=4776032 WAF=1.795950
- phaseB(test4) host_pages=24000658 gc_pages=17713529 WAF=1.738043
- phaseC(sqlite-a) host_pages=8094138 gc_pages=4123103 WAF=1.509394
- phaseC-load host_pages=1398349 gc_pages=524044 WAF=1.374759
- phaseC-run host_pages=6695789 gc_pages=3599059 WAF=1.537511
- ycsb-load [OVERALL], Throughput(ops/sec), 23405.500292568755
- ycsb-run [OVERALL], Throughput(ops/sec), 12704.744904603247

### mix-20260911 mixH fixed50 — started 2026-09-22T04:54:03+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixH fixed50`; evidence `result/mix-20260911/mixH-fixed50/`.

- Finished 2026-09-22T05:21:28+09:00; mixH fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-fixed50-rep2`; cleanup attempted.
- total host_bytes=156137660416 host_pages=38119546 gc_pages=27403021 WAF=1.718871
- phaseA(test3) host_pages=6027057 gc_pages=4733559 WAF=1.785385
- phaseB(test4) host_pages=24000664 gc_pages=18621329 WAF=1.775867
- phaseC(sqlite-a) host_pages=8091825 gc_pages=4048133 WAF=1.500274
- phaseC-load host_pages=1398349 gc_pages=552657 WAF=1.395221
- phaseC-run host_pages=6693476 gc_pages=3495476 WAF=1.522221
- ycsb-load [OVERALL], Throughput(ops/sec), 25046.96305572949
- ycsb-run [OVERALL], Throughput(ops/sec), 12705.511650954184

### mix-20260911 mixH online — started 2026-09-22T05:21:28+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixH online`; evidence `result/mix-20260911/mixH-online/`.

- Finished 2026-09-22T05:50:55+09:00; mixH online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-online-rep2`; cleanup attempted.
- total host_bytes=155924561920 host_pages=38067520 gc_pages=33554303 WAF=1.881442
- phaseA(test3) host_pages=6017327 gc_pages=6424570 WAF=2.067678
- phaseB(test4) host_pages=24011937 gc_pages=22913029 WAF=1.954235
- phaseC(sqlite-a) host_pages=8038256 gc_pages=4216704 WAF=1.524579
- phaseC-load host_pages=1398351 gc_pages=790035 WAF=1.564976
- phaseC-run host_pages=6639905 gc_pages=3426669 WAF=1.516072
- ycsb-load [OVERALL], Throughput(ops/sec), 24932.4745480989
- ycsb-run [OVERALL], Throughput(ops/sec), 8966.318026334076

### mix-20260911 mixF greedy — started 2026-09-22T05:51:06+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixF greedy`; evidence `result/mix-20260911/mixF-greedy/`.

- Finished 2026-09-22T06:07:35+09:00; mixF greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-greedy-rep2`; cleanup attempted.
- total host_bytes=188021592064 host_pages=45903709 gc_pages=125107727 WAF=3.725438
- phaseA(test4) host_pages=24000658 gc_pages=30020921 WAF=2.250837
- phaseB(varmail) host_pages=21903051 gc_pages=95086806 WAF=5.341258
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF fixed10 — started 2026-09-22T06:07:35+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixF fixed10`; evidence `result/mix-20260911/mixF-fixed10/`.

- Finished 2026-09-22T06:24:01+09:00; mixF fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-fixed10-rep2`; cleanup attempted.
- total host_bytes=188770533376 host_pages=46086556 gc_pages=126026113 WAF=3.734553
- phaseA(test4) host_pages=24000664 gc_pages=30244994 WAF=2.260173
- phaseB(varmail) host_pages=22085892 gc_pages=95781119 WAF=5.336756
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF fixed37 — started 2026-09-22T06:24:01+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixF fixed37`; evidence `result/mix-20260911/mixF-fixed37/`.

- Finished 2026-09-22T06:40:28+09:00; mixF fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-fixed37-rep2`; cleanup attempted.
- total host_bytes=216241487872 host_pages=52793332 gc_pages=110379172 WAF=3.090779
- phaseA(test4) host_pages=24000658 gc_pages=23380500 WAF=1.974161
- phaseB(varmail) host_pages=28792674 gc_pages=86998672 WAF=4.021556
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF fixed47 — started 2026-09-22T06:40:28+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixF fixed47`; evidence `result/mix-20260911/mixF-fixed47/`.

- Finished 2026-09-22T06:56:54+09:00; mixF fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-fixed47-rep2`; cleanup attempted.
- total host_bytes=270122168320 host_pages=65947795 gc_pages=92057556 WAF=2.395916
- phaseA(test4) host_pages=24023194 gc_pages=18420304 WAF=1.766772
- phaseB(varmail) host_pages=41924601 gc_pages=73637252 WAF=2.756421
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF fixed50 — started 2026-09-22T06:56:54+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixF fixed50`; evidence `result/mix-20260911/mixF-fixed50/`.

- Finished 2026-09-22T07:13:21+09:00; mixF fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-fixed50-rep2`; cleanup attempted.
- total host_bytes=252592832512 host_pages=61668172 gc_pages=97682002 WAF=2.583994
- phaseA(test4) host_pages=24023197 gc_pages=19352526 WAF=1.805577
- phaseB(varmail) host_pages=37644975 gc_pages=78329476 WAF=3.080742
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF online — started 2026-09-22T07:13:21+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixF online`; evidence `result/mix-20260911/mixF-online/`.

- Finished 2026-09-22T07:29:47+09:00; mixF online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-online-rep2`; cleanup attempted.
- total host_bytes=194041131008 host_pages=47373323 gc_pages=116824185 WAF=3.466033
- phaseA(test4) host_pages=24019083 gc_pages=23907596 WAF=1.995358
- phaseB(varmail) host_pages=23354240 gc_pages=92916589 WAF=4.978575
- ycsb-load 
- ycsb-run 

### mix-20260911 mixA greedy — started 2026-09-22T07:29:50+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixA greedy`; evidence `result/mix-20260911/mixA-greedy/`.

- Finished 2026-09-22T07:47:27+09:00; mixA greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-greedy-rep3`; cleanup attempted.
- total host_bytes=131600515072 host_pages=32129032 gc_pages=44900683 WAF=2.397511
- phaseA(test4) host_pages=24000658 gc_pages=29789930 WAF=2.241213
- phaseB(sqlite-a) host_pages=8128374 gc_pages=15110753 WAF=2.859013
- phaseB-load host_pages=1398350 gc_pages=1647445 WAF=2.178135
- phaseB-run host_pages=6730024 gc_pages=13463308 WAF=3.000484
- ycsb-load [OVERALL], Throughput(ops/sec), 27164.070988772182
- ycsb-run [OVERALL], Throughput(ops/sec), 12088.682575372935

### mix-20260911 mixA fixed10 — started 2026-09-22T07:47:28+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixA fixed10`; evidence `result/mix-20260911/mixA-fixed10/`.

- Finished 2026-09-22T08:07:45+09:00; mixA fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-fixed10-rep3`; cleanup attempted.
- total host_bytes=131785371648 host_pages=32174163 gc_pages=46023874 WAF=2.430461
- phaseA(test4) host_pages=24000658 gc_pages=30313749 WAF=2.263038
- phaseB(sqlite-a) host_pages=8173505 gc_pages=15710125 WAF=2.922079
- phaseB-load host_pages=1398351 gc_pages=1687116 WAF=2.206504
- phaseB-run host_pages=6775154 gc_pages=14023009 WAF=3.069770
- ycsb-load [OVERALL], Throughput(ops/sec), 24682.21646303838
- ycsb-run [OVERALL], Throughput(ops/sec), 8018.362049092421

### mix-20260911 mixA fixed37 — started 2026-09-22T08:07:46+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixA fixed37`; evidence `result/mix-20260911/mixA-fixed37/`.

- Finished 2026-09-22T08:25:11+09:00; mixA fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-fixed37-rep3`; cleanup attempted.
- total host_bytes=131450257408 host_pages=32092348 gc_pages=28940238 WAF=1.901780
- phaseA(test4) host_pages=24000658 gc_pages=23267520 WAF=1.969453
- phaseB(sqlite-a) host_pages=8091690 gc_pages=5672718 WAF=1.701055
- phaseB-load host_pages=1398349 gc_pages=1147458 WAF=1.820581
- phaseB-run host_pages=6693341 gc_pages=4525260 WAF=1.676084
- ycsb-load [OVERALL], Throughput(ops/sec), 21003.255504603214
- ycsb-run [OVERALL], Throughput(ops/sec), 12729.650857501107

### mix-20260911 mixA fixed47 — started 2026-09-22T08:25:12+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixA fixed47`; evidence `result/mix-20260911/mixA-fixed47/`.

- Finished 2026-09-22T08:42:31+09:00; mixA fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-fixed47-rep3`; cleanup attempted.
- total host_bytes=131550236672 host_pages=32116757 gc_pages=22145061 WAF=1.689517
- phaseA(test4) host_pages=24026785 gc_pages=18043366 WAF=1.750969
- phaseB(sqlite-a) host_pages=8089972 gc_pages=4101695 WAF=1.507010
- phaseB-load host_pages=1399373 gc_pages=523777 WAF=1.374294
- phaseB-run host_pages=6690599 gc_pages=3577918 WAF=1.534768
- ycsb-load [OVERALL], Throughput(ops/sec), 22954.20635831516
- ycsb-run [OVERALL], Throughput(ops/sec), 12867.859946212346

### mix-20260911 mixA fixed50 — started 2026-09-22T08:42:31+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixA fixed50`; evidence `result/mix-20260911/mixA-fixed50/`.

- Finished 2026-09-22T08:59:49+09:00; mixA fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-fixed50-rep3`; cleanup attempted.
- total host_bytes=131556311040 host_pages=32118240 gc_pages=23247236 WAF=1.723802
- phaseA(test4) host_pages=24025242 gc_pages=19212442 WAF=1.799677
- phaseB(sqlite-a) host_pages=8092998 gc_pages=4034794 WAF=1.498554
- phaseB-load host_pages=1398348 gc_pages=556895 WAF=1.398252
- phaseB-run host_pages=6694650 gc_pages=3477899 WAF=1.519504
- ycsb-load [OVERALL], Throughput(ops/sec), 25069.98704717336
- ycsb-run [OVERALL], Throughput(ops/sec), 12773.635216912293

### mix-20260911 mixA online — started 2026-09-22T08:59:49+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixA online`; evidence `result/mix-20260911/mixA-online/`.

- Finished 2026-09-22T09:19:52+09:00; mixA online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-online-rep3`; cleanup attempted.
- total host_bytes=131606118400 host_pages=32130400 gc_pages=36081779 WAF=2.122979
- phaseA(test4) host_pages=24000658 gc_pages=24013816 WAF=2.000548
- phaseB(sqlite-a) host_pages=8129742 gc_pages=12067963 WAF=2.484421
- phaseB-load host_pages=1398349 gc_pages=1726610 WAF=2.234749
- phaseB-run host_pages=6731393 gc_pages=10341353 WAF=2.536287
- ycsb-load [OVERALL], Throughput(ops/sec), 26797.677534613667
- ycsb-run [OVERALL], Throughput(ops/sec), 8272.598671420654

### mix-20260911 mixB greedy — started 2026-09-22T09:20:03+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixB greedy`; evidence `result/mix-20260911/mixB-greedy/`.

- Finished 2026-09-22T09:37:22+09:00; mixB greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-greedy-rep3`; cleanup attempted.
- total host_bytes=131351330816 host_pages=32068196 gc_pages=84485706 WAF=3.634564
- phaseA(sqlite-a) host_pages=8067537 gc_pages=9743999 WAF=2.207803
- phaseB(test4) host_pages=24000659 gc_pages=74741707 WAF=4.114152
- phaseA-load host_pages=1398349 gc_pages=1050303 WAF=1.751102
- phaseA-run host_pages=6669188 gc_pages=8693696 WAF=2.303561
- ycsb-load [OVERALL], Throughput(ops/sec), 22519.986488008108
- ycsb-run [OVERALL], Throughput(ops/sec), 13021.511537059221

### mix-20260911 mixB fixed10 — started 2026-09-22T09:37:22+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixB fixed10`; evidence `result/mix-20260911/mixB-fixed10/`.

- Finished 2026-09-22T09:54:53+09:00; mixB fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-fixed10-rep3`; cleanup attempted.
- total host_bytes=131587665920 host_pages=32125895 gc_pages=84545260 WAF=3.631686
- phaseA(sqlite-a) host_pages=8125237 gc_pages=9372001 WAF=2.153443
- phaseB(test4) host_pages=24000658 gc_pages=75173259 WAF=4.132133
- phaseA-load host_pages=1398341 gc_pages=1072278 WAF=1.766822
- phaseA-run host_pages=6726896 gc_pages=8299723 WAF=2.233812
- ycsb-load [OVERALL], Throughput(ops/sec), 25295.109612141652
- ycsb-run [OVERALL], Throughput(ops/sec), 12337.530149839304

### mix-20260911 mixB fixed37 — started 2026-09-22T09:54:53+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixB fixed37`; evidence `result/mix-20260911/mixB-fixed37/`.

- Finished 2026-09-22T10:14:09+09:00; mixB fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-fixed37-rep3`; cleanup attempted.
- total host_bytes=131110588416 host_pages=32009421 gc_pages=70383763 WAF=3.198845
- phaseA(sqlite-a) host_pages=8008763 gc_pages=4268085 WAF=1.532927
- phaseB(test4) host_pages=24000658 gc_pages=66115678 WAF=3.754744
- phaseA-load host_pages=1398339 gc_pages=621423 WAF=1.444401
- phaseA-run host_pages=6610424 gc_pages=3646662 WAF=1.551653
- ycsb-load [OVERALL], Throughput(ops/sec), 26708.212775428445
- ycsb-run [OVERALL], Throughput(ops/sec), 9149.465671204802

### mix-20260911 mixB fixed47 — started 2026-09-22T10:14:09+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixB fixed47`; evidence `result/mix-20260911/mixB-fixed47/`.

- Finished 2026-09-22T10:31:20+09:00; mixB fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-fixed47-rep3`; cleanup attempted.
- total host_bytes=131389980672 host_pages=32077632 gc_pages=46571594 WAF=2.451840
- phaseA(sqlite-a) host_pages=8076965 gc_pages=3383674 WAF=1.418929
- phaseB(test4) host_pages=24000667 gc_pages=43187920 WAF=2.799447
- phaseA-load host_pages=1398341 gc_pages=378490 WAF=1.270671
- phaseA-run host_pages=6678624 gc_pages=3005184 WAF=1.449971
- ycsb-load [OVERALL], Throughput(ops/sec), 28471.101831640884
- ycsb-run [OVERALL], Throughput(ops/sec), 13012.023109353042

### mix-20260911 mixB fixed50 — started 2026-09-22T10:31:20+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixB fixed50`; evidence `result/mix-20260911/mixB-fixed50/`.

- Finished 2026-09-22T10:50:39+09:00; mixB fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-fixed50-rep3`; cleanup attempted.
- total host_bytes=131160461312 host_pages=32021597 gc_pages=51779842 WAF=2.617029
- phaseA(sqlite-a) host_pages=8020933 gc_pages=3709489 WAF=1.462476
- phaseB(test4) host_pages=24000664 gc_pages=48070353 WAF=3.002876
- phaseA-load host_pages=1398339 gc_pages=386276 WAF=1.276239
- phaseA-run host_pages=6622594 gc_pages=3323213 WAF=1.501799
- ycsb-load [OVERALL], Throughput(ops/sec), 26931.19080748687
- ycsb-run [OVERALL], Throughput(ops/sec), 9067.416239742486

### mix-20260911 mixB online — started 2026-09-22T10:50:40+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixB online`; evidence `result/mix-20260911/mixB-online/`.

- Finished 2026-09-22T11:08:03+09:00; mixB online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-online-rep3`; cleanup attempted.
- total host_bytes=131588337664 host_pages=32126059 gc_pages=67466850 WAF=3.100066
- phaseA(sqlite-a) host_pages=8107980 gc_pages=6892135 WAF=1.850043
- phaseB(test4) host_pages=24018079 gc_pages=60574715 WAF=3.522047
- phaseA-load host_pages=1399363 gc_pages=877473 WAF=1.627052
- phaseA-run host_pages=6708617 gc_pages=6014662 WAF=1.896558
- ycsb-load [OVERALL], Throughput(ops/sec), 25111.95747708534
- ycsb-run [OVERALL], Throughput(ops/sec), 12650.181371975421

### mix-20260911 mixC greedy — started 2026-09-22T11:08:12+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixC greedy`; evidence `result/mix-20260911/mixC-greedy/`.

- Finished 2026-09-22T11:29:36+09:00; mixC greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-greedy-rep3`; cleanup attempted.
- total host_bytes=122991415296 host_pages=30027201 gc_pages=37292088 WAF=2.241944
- phaseA(test3) host_pages=6026540 gc_pages=6732572 WAF=2.117154
- phaseB(test4) host_pages=24000661 gc_pages=30559516 WAF=2.273278
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC fixed10 — started 2026-09-22T11:29:36+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixC fixed10`; evidence `result/mix-20260911/mixC-fixed10/`.

- Finished 2026-09-22T11:50:59+09:00; mixC fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-fixed10-rep3`; cleanup attempted.
- total host_bytes=122884395008 host_pages=30001073 gc_pages=37865290 WAF=2.262131
- phaseA(test3) host_pages=6000415 gc_pages=7022423 WAF=2.170323
- phaseB(test4) host_pages=24000658 gc_pages=30842867 WAF=2.285084
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC fixed37 — started 2026-09-22T11:50:59+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixC fixed37`; evidence `result/mix-20260911/mixC-fixed37/`.

- Finished 2026-09-22T12:12:23+09:00; mixC fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-fixed37-rep3`; cleanup attempted.
- total host_bytes=122884407296 host_pages=30001076 gc_pages=26733045 WAF=1.891070
- phaseA(test3) host_pages=6000418 gc_pages=4945683 WAF=1.824223
- phaseB(test4) host_pages=24000658 gc_pages=21787362 WAF=1.907782
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC fixed47 — started 2026-09-22T12:12:23+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixC fixed47`; evidence `result/mix-20260911/mixC-fixed47/`.

- Finished 2026-09-22T12:33:46+09:00; mixC fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-fixed47-rep3`; cleanup attempted.
- total host_bytes=122884407296 host_pages=30001076 gc_pages=22480960 WAF=1.749338
- phaseA(test3) host_pages=6000415 gc_pages=4776075 WAF=1.795957
- phaseB(test4) host_pages=24000661 gc_pages=17704885 WAF=1.737683
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC fixed50 — started 2026-09-22T12:33:46+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixC fixed50`; evidence `result/mix-20260911/mixC-fixed50/`.

- Finished 2026-09-22T12:55:09+09:00; mixC fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-fixed50-rep3`; cleanup attempted.
- total host_bytes=122884407296 host_pages=30001076 gc_pages=23386102 WAF=1.779509
- phaseA(test3) host_pages=6000418 gc_pages=4804023 WAF=1.800615
- phaseB(test4) host_pages=24000658 gc_pages=18582079 WAF=1.774232
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC online — started 2026-09-22T12:55:09+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixC online`; evidence `result/mix-20260911/mixC-online/`.

- Finished 2026-09-22T13:16:32+09:00; mixC online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-online-rep3`; cleanup attempted.
- total host_bytes=122976698368 host_pages=30023608 gc_pages=29915887 WAF=1.996412
- phaseA(test3) host_pages=6022950 gc_pages=6775633 WAF=2.124969
- phaseB(test4) host_pages=24000658 gc_pages=23140254 WAF=1.964151
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD greedy — started 2026-09-22T13:16:36+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixD greedy`; evidence `result/mix-20260911/mixD-greedy/`.

- Finished 2026-09-22T13:37:59+09:00; mixD greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-greedy-rep3`; cleanup attempted.
- total host_bytes=122884505600 host_pages=30001100 gc_pages=37655768 WAF=2.255146
- phaseA(test4) host_pages=24000682 gc_pages=30039587 WAF=2.251614
- phaseB(test3) host_pages=6000418 gc_pages=7616181 WAF=2.269275
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD fixed10 — started 2026-09-22T13:37:59+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixD fixed10`; evidence `result/mix-20260911/mixD-fixed10/`.

- Finished 2026-09-22T13:59:23+09:00; mixD fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-fixed10-rep3`; cleanup attempted.
- total host_bytes=122884431872 host_pages=30001082 gc_pages=37976379 WAF=2.265834
- phaseA(test4) host_pages=24000664 gc_pages=30302010 WAF=2.262549
- phaseB(test3) host_pages=6000418 gc_pages=7674369 WAF=2.278972
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD fixed37 — started 2026-09-22T13:59:23+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixD fixed37`; evidence `result/mix-20260911/mixD-fixed37/`.

- Finished 2026-09-22T14:20:46+09:00; mixD fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-fixed37-rep3`; cleanup attempted.
- total host_bytes=122987274240 host_pages=30026190 gc_pages=27907691 WAF=1.929445
- phaseA(test4) host_pages=24025760 gc_pages=22806608 WAF=1.949256
- phaseB(test3) host_pages=6000430 gc_pages=5101083 WAF=1.850120
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD fixed47 — started 2026-09-22T14:20:46+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixD fixed47`; evidence `result/mix-20260911/mixD-fixed47/`.

- Finished 2026-09-22T14:42:09+09:00; mixD fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-fixed47-rep3`; cleanup attempted.
- total host_bytes=122884395008 host_pages=30001073 gc_pages=23373622 WAF=1.779093
- phaseA(test4) host_pages=24000658 gc_pages=18526199 WAF=1.771904
- phaseB(test3) host_pages=6000415 gc_pages=4847423 WAF=1.807848
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD fixed50 — started 2026-09-22T14:42:09+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixD fixed50`; evidence `result/mix-20260911/mixD-fixed50/`.

- Finished 2026-09-22T15:03:32+09:00; mixD fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-fixed50-rep3`; cleanup attempted.
- total host_bytes=122884395008 host_pages=30001073 gc_pages=24371224 WAF=1.812345
- phaseA(test4) host_pages=24000658 gc_pages=19500416 WAF=1.812495
- phaseB(test3) host_pages=6000415 gc_pages=4870808 WAF=1.811745
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD online — started 2026-09-22T15:03:32+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixD online`; evidence `result/mix-20260911/mixD-online/`.

- Finished 2026-09-22T15:24:55+09:00; mixD online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-online-rep3`; cleanup attempted.
- total host_bytes=122884431872 host_pages=30001082 gc_pages=31582776 WAF=2.052721
- phaseA(test4) host_pages=24000658 gc_pages=24009688 WAF=2.000376
- phaseB(test3) host_pages=6000424 gc_pages=7573088 WAF=2.262092
- ycsb-load 
- ycsb-run 

### mix-20260911 mixJ greedy — started 2026-09-22T15:24:59+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixJ greedy`; evidence `result/mix-20260911/mixJ-greedy/`.

- Finished 2026-09-22T15:34:03+09:00; mixJ greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-greedy-rep3`; cleanup attempted.
- total host_bytes=35732127744 host_pages=8723664 gc_pages=10366502 WAF=2.188320
- phaseA(sqlite-a) host_pages=8089013 gc_pages=9667677 WAF=2.195162
- phaseB(sqlite-b) host_pages=634651 gc_pages=698825 WAF=2.101117
- phaseA-load host_pages=1398339 gc_pages=1048441 WAF=1.749776
- phaseA-run host_pages=6690674 gc_pages=8619236 WAF=2.288246
- ycsb-load [OVERALL], Throughput(ops/sec), 24931.438544003988
- ycsb-run [OVERALL], Throughput(ops/sec), 45263.7177354562

### mix-20260911 mixJ fixed10 — started 2026-09-22T15:34:03+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixJ fixed10`; evidence `result/mix-20260911/mixJ-fixed10/`.

- Finished 2026-09-22T15:43:34+09:00; mixJ fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-fixed10-rep3`; cleanup attempted.
- total host_bytes=36036763648 host_pages=8798038 gc_pages=9804894 WAF=2.114441
- phaseA(sqlite-a) host_pages=8156037 gc_pages=9115952 WAF=2.117694
- phaseB(sqlite-b) host_pages=642001 gc_pages=688942 WAF=2.073117
- phaseA-load host_pages=1400394 gc_pages=1072914 WAF=1.766152
- phaseA-run host_pages=6755643 gc_pages=8043038 WAF=2.190566
- ycsb-load [OVERALL], Throughput(ops/sec), 23337.222870478414
- ycsb-run [OVERALL], Throughput(ops/sec), 44106.29617377881

### mix-20260911 mixJ fixed37 — started 2026-09-22T15:43:35+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixJ fixed37`; evidence `result/mix-20260911/mixJ-fixed37/`.

- Finished 2026-09-22T15:52:42+09:00; mixJ fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-fixed37-rep3`; cleanup attempted.
- total host_bytes=35853791232 host_pages=8753367 gc_pages=4457872 WAF=1.509275
- phaseA(sqlite-a) host_pages=8122689 gc_pages=4163596 WAF=1.512588
- phaseB(sqlite-b) host_pages=630678 gc_pages=294276 WAF=1.466603
- phaseA-load host_pages=1404479 gc_pages=601825 WAF=1.428504
- phaseA-run host_pages=6718210 gc_pages=3561771 WAF=1.530167
- ycsb-load [OVERALL], Throughput(ops/sec), 25153.014169531314
- ycsb-run [OVERALL], Throughput(ops/sec), 46243.843788295686

### mix-20260911 mixJ fixed47 — started 2026-09-22T15:52:43+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixJ fixed47`; evidence `result/mix-20260911/mixJ-fixed47/`.

- Finished 2026-09-22T16:04:08+09:00; mixJ fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-fixed47-rep3`; cleanup attempted.
- total host_bytes=35607642112 host_pages=8693272 gc_pages=4051030 WAF=1.465996
- phaseA(sqlite-a) host_pages=8055291 gc_pages=3759749 WAF=1.466743
- phaseB(sqlite-b) host_pages=637981 gc_pages=291281 WAF=1.456567
- phaseA-load host_pages=1398351 gc_pages=368316 WAF=1.263393
- phaseA-run host_pages=6656940 gc_pages=3391433 WAF=1.509458
- ycsb-load [OVERALL], Throughput(ops/sec), 22168.852761869573
- ycsb-run [OVERALL], Throughput(ops/sec), 45427.1858994015

### mix-20260911 mixJ fixed50 — started 2026-09-22T16:04:09+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixJ fixed50`; evidence `result/mix-20260911/mixJ-fixed50/`.

- Finished 2026-09-22T16:15:36+09:00; mixJ fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-fixed50-rep3`; cleanup attempted.
- total host_bytes=35649376256 host_pages=8703461 gc_pages=3921701 WAF=1.450591
- phaseA(sqlite-a) host_pages=8065231 gc_pages=3670248 WAF=1.455070
- phaseB(sqlite-b) host_pages=638230 gc_pages=251453 WAF=1.393985
- phaseA-load host_pages=1398345 gc_pages=384394 WAF=1.274892
- phaseA-run host_pages=6666886 gc_pages=3285854 WAF=1.492862
- ycsb-load [OVERALL], Throughput(ops/sec), 23863.500775563774
- ycsb-run [OVERALL], Throughput(ops/sec), 44147.673969427735

### mix-20260911 mixJ online — started 2026-09-22T16:15:37+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixJ online`; evidence `result/mix-20260911/mixJ-online/`.

- Finished 2026-09-22T16:25:06+09:00; mixJ online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-online-rep3`; cleanup attempted.
- total host_bytes=35909750784 host_pages=8767029 gc_pages=7988500 WAF=1.911198
- phaseA(sqlite-a) host_pages=8134801 gc_pages=7696811 WAF=1.946158
- phaseB(sqlite-b) host_pages=632228 gc_pages=291689 WAF=1.461367
- phaseA-load host_pages=1398349 gc_pages=909972 WAF=1.650747
- phaseA-run host_pages=6736452 gc_pages=6786839 WAF=2.007480
- ycsb-load [OVERALL], Throughput(ops/sec), 21201.413427561838
- ycsb-run [OVERALL], Throughput(ops/sec), 45160.998961297024

### mix-20260911 mixG greedy — started 2026-09-22T16:25:16+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixG greedy`; evidence `result/mix-20260911/mixG-greedy/`.

- Finished 2026-09-22T16:35:28+09:00; mixG greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-greedy-rep3`; cleanup attempted.
- total host_bytes=84185141248 host_pages=20553013 gc_pages=63109477 WAF=4.070571
- phaseA(concurrent-test4+sqlite-a) host_pages=20553013 gc_pages=63109477 WAF=4.070571
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG fixed10 — started 2026-09-22T16:35:29+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixG fixed10`; evidence `result/mix-20260911/mixG-fixed10/`.

- Finished 2026-09-22T16:46:48+09:00; mixG fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-fixed10-rep3`; cleanup attempted.
- total host_bytes=84858085376 host_pages=20717306 gc_pages=62102107 WAF=3.997596
- phaseA(concurrent-test4+sqlite-a) host_pages=20717306 gc_pages=62102107 WAF=3.997596
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG fixed37 — started 2026-09-22T16:46:48+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixG fixed37`; evidence `result/mix-20260911/mixG-fixed37/`.

- Finished 2026-09-22T16:59:46+09:00; mixG fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-fixed37-rep3`; cleanup attempted.
- total host_bytes=83802791936 host_pages=20459666 gc_pages=49549923 WAF=3.421834
- phaseA(concurrent-test4+sqlite-a) host_pages=20459666 gc_pages=49549923 WAF=3.421834
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG fixed47 — started 2026-09-22T16:59:47+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixG fixed47`; evidence `result/mix-20260911/mixG-fixed47/`.

- Finished 2026-09-22T17:10:06+09:00; mixG fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-fixed47-rep3`; cleanup attempted.
- total host_bytes=84186853376 host_pages=20553431 gc_pages=37795769 WAF=2.838903
- phaseA(concurrent-test4+sqlite-a) host_pages=20553431 gc_pages=37795769 WAF=2.838903
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG fixed50 — started 2026-09-22T17:10:07+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixG fixed50`; evidence `result/mix-20260911/mixG-fixed50/`.

- Finished 2026-09-22T17:20:33+09:00; mixG fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-fixed50-rep3`; cleanup attempted.
- total host_bytes=84258230272 host_pages=20570857 gc_pages=44987059 WAF=3.186932
- phaseA(concurrent-test4+sqlite-a) host_pages=20570857 gc_pages=44987059 WAF=3.186932
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG online — started 2026-09-22T17:20:34+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixG online`; evidence `result/mix-20260911/mixG-online/`.

- Finished 2026-09-22T17:33:59+09:00; mixG online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-online-rep3`; cleanup attempted.
- total host_bytes=84045697024 host_pages=20518969 gc_pages=56444139 WAF=3.750827
- phaseA(concurrent-test4+sqlite-a) host_pages=20518969 gc_pages=56444139 WAF=3.750827
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK greedy — started 2026-09-22T17:34:09+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixK greedy`; evidence `result/mix-20260911/mixK-greedy/`.

- Finished 2026-09-22T17:55:34+09:00; mixK greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-greedy-rep3`; cleanup attempted.
- total host_bytes=196616142848 host_pages=48001988 gc_pages=64194321 WAF=2.337326
- phaseA(test4-hot512M) host_pages=24000667 gc_pages=30009013 WAF=2.250341
- phaseB(test4-hot128M) host_pages=24001321 gc_pages=34185308 WAF=2.424309
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK fixed10 — started 2026-09-22T17:55:34+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixK fixed10`; evidence `result/mix-20260911/mixK-fixed10/`.

- Finished 2026-09-22T18:16:58+09:00; mixK fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-fixed10-rep3`; cleanup attempted.
- total host_bytes=196616130560 host_pages=48001985 gc_pages=64792709 WAF=2.349792
- phaseA(test4-hot512M) host_pages=24000658 gc_pages=30348666 WAF=2.264493
- phaseB(test4-hot128M) host_pages=24001327 gc_pages=34444043 WAF=2.435089
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK fixed37 — started 2026-09-22T18:16:58+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixK fixed37`; evidence `result/mix-20260911/mixK-fixed37/`.

- Finished 2026-09-22T18:38:21+09:00; mixK fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-fixed37-rep3`; cleanup attempted.
- total host_bytes=196616155136 host_pages=48001991 gc_pages=45997358 WAF=1.958239
- phaseA(test4-hot512M) host_pages=24000661 gc_pages=23427545 WAF=1.976121
- phaseB(test4-hot128M) host_pages=24001330 gc_pages=22569813 WAF=1.940357
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK fixed47 — started 2026-09-22T18:38:21+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixK fixed47`; evidence `result/mix-20260911/mixK-fixed47/`.

- Finished 2026-09-22T18:59:44+09:00; mixK fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-fixed47-rep3`; cleanup attempted.
- total host_bytes=196616142848 host_pages=48001988 gc_pages=37312695 WAF=1.777316
- phaseA(test4-hot512M) host_pages=24000667 gc_pages=18576542 WAF=1.774001
- phaseB(test4-hot128M) host_pages=24001321 gc_pages=18736153 WAF=1.780630
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK fixed50 — started 2026-09-22T18:59:44+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixK fixed50`; evidence `result/mix-20260911/mixK-fixed50/`.

- Finished 2026-09-22T19:21:07+09:00; mixK fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-fixed50-rep3`; cleanup attempted.
- total host_bytes=196620312576 host_pages=48003006 gc_pages=38518192 WAF=1.802412
- phaseA(test4-hot512M) host_pages=24001685 gc_pages=19521160 WAF=1.813325
- phaseB(test4-hot128M) host_pages=24001321 gc_pages=18997032 WAF=1.791499
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK online — started 2026-09-22T19:21:07+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixK online`; evidence `result/mix-20260911/mixK-online/`.

- Finished 2026-09-22T19:42:31+09:00; mixK online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-online-rep3`; cleanup attempted.
- total host_bytes=196616142848 host_pages=48001988 gc_pages=48766025 WAF=2.015917
- phaseA(test4-hot512M) host_pages=24000661 gc_pages=23947568 WAF=1.997788
- phaseB(test4-hot128M) host_pages=24001327 gc_pages=24818457 WAF=2.034045
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL greedy — started 2026-09-22T19:42:34+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixL greedy`; evidence `result/mix-20260911/mixL-greedy/`.

- Finished 2026-09-22T19:54:00+09:00; mixL greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-greedy-rep3`; cleanup attempted.
- total host_bytes=61513580544 host_pages=15017964 gc_pages=15327409 WAF=2.020605
- phaseA(alternate-fast/slow-x5) host_pages=15017964 gc_pages=15327409 WAF=2.020605
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL fixed10 — started 2026-09-22T19:54:00+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixL fixed10`; evidence `result/mix-20260911/mixL-fixed10/`.

- Finished 2026-09-22T20:05:26+09:00; mixL fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-fixed10-rep3`; cleanup attempted.
- total host_bytes=61442301952 host_pages=15000562 gc_pages=15561678 WAF=2.037406
- phaseA(alternate-fast/slow-x5) host_pages=15000562 gc_pages=15561678 WAF=2.037406
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL fixed37 — started 2026-09-22T20:05:26+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixL fixed37`; evidence `result/mix-20260911/mixL-fixed37/`.

- Finished 2026-09-22T20:16:51+09:00; mixL fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-fixed37-rep3`; cleanup attempted.
- total host_bytes=61442306048 host_pages=15000563 gc_pages=10007388 WAF=1.667134
- phaseA(alternate-fast/slow-x5) host_pages=15000563 gc_pages=10007388 WAF=1.667134
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL fixed47 — started 2026-09-22T20:16:51+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixL fixed47`; evidence `result/mix-20260911/mixL-fixed47/`.

- Finished 2026-09-22T20:28:17+09:00; mixL fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-fixed47-rep3`; cleanup attempted.
- total host_bytes=61530390528 host_pages=15022068 gc_pages=8025802 WAF=1.534267
- phaseA(alternate-fast/slow-x5) host_pages=15022068 gc_pages=8025802 WAF=1.534267
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL fixed50 — started 2026-09-22T20:28:17+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixL fixed50`; evidence `result/mix-20260911/mixL-fixed50/`.

- Finished 2026-09-22T20:39:42+09:00; mixL fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-fixed50-rep3`; cleanup attempted.
- total host_bytes=61442252800 host_pages=15000550 gc_pages=8533599 WAF=1.568886
- phaseA(alternate-fast/slow-x5) host_pages=15000550 gc_pages=8533599 WAF=1.568886
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL online — started 2026-09-22T20:39:42+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixL online`; evidence `result/mix-20260911/mixL-online/`.

- Finished 2026-09-22T20:51:08+09:00; mixL online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-online-rep3`; cleanup attempted.
- total host_bytes=61500899328 host_pages=15014868 gc_pages=11449758 WAF=1.762561
- phaseA(alternate-fast/slow-x5) host_pages=15014868 gc_pages=11449758 WAF=1.762561
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixM greedy — started 2026-09-22T20:51:11+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixM greedy`; evidence `result/mix-20260911/mixM-greedy/`.

- Finished 2026-09-22T21:02:35+09:00; mixM greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixM-greedy-rep3`; cleanup attempted.
- total host_bytes=73730068480 host_pages=18000505 gc_pages=21427003 WAF=2.190356
- phaseA(ramp-10k-to-50k) host_pages=18000505 gc_pages=21427003 WAF=2.190356
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixM fixed10 — started 2026-09-22T21:02:35+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixM fixed10`; evidence `result/mix-20260911/mixM-fixed10/`.

- Finished 2026-09-22T21:13:59+09:00; mixM fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixM-fixed10-rep3`; cleanup attempted.
- total host_bytes=73730068480 host_pages=18000505 gc_pages=21513975 WAF=2.195187
- phaseA(ramp-10k-to-50k) host_pages=18000505 gc_pages=21513975 WAF=2.195187
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixM fixed37 — started 2026-09-22T21:13:59+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixM fixed37`; evidence `result/mix-20260911/mixM-fixed37/`.

- Finished 2026-09-22T21:25:23+09:00; mixM fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixM-fixed37-rep3`; cleanup attempted.
- total host_bytes=73730068480 host_pages=18000505 gc_pages=14536180 WAF=1.807543
- phaseA(ramp-10k-to-50k) host_pages=18000505 gc_pages=14536180 WAF=1.807543
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixM fixed47 — started 2026-09-22T21:25:23+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixM fixed47`; evidence `result/mix-20260911/mixM-fixed47/`.

- Finished 2026-09-22T21:36:47+09:00; mixM fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixM-fixed47-rep3`; cleanup attempted.
- total host_bytes=73828646912 host_pages=18024572 gc_pages=12639379 WAF=1.701230
- phaseA(ramp-10k-to-50k) host_pages=18024572 gc_pages=12639379 WAF=1.701230
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixM fixed50 — started 2026-09-22T21:36:47+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixM fixed50`; evidence `result/mix-20260911/mixM-fixed50/`.

- Finished 2026-09-22T21:48:11+09:00; mixM fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixM-fixed50-rep3`; cleanup attempted.
- total host_bytes=73822351360 host_pages=18023035 gc_pages=13070989 WAF=1.725238
- phaseA(ramp-10k-to-50k) host_pages=18023035 gc_pages=13070989 WAF=1.725238
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixM online — started 2026-09-22T21:48:11+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixM online`; evidence `result/mix-20260911/mixM-online/`.

- Finished 2026-09-22T21:59:36+09:00; mixM online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixM-online-rep3`; cleanup attempted.
- total host_bytes=73730056192 host_pages=18000502 gc_pages=16228188 WAF=1.901541
- phaseA(ramp-10k-to-50k) host_pages=18000502 gc_pages=16228188 WAF=1.901541
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ greedy — started 2026-09-22T21:59:39+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixQ greedy`; evidence `result/mix-20260911/mixQ-greedy/`.

- Finished 2026-09-22T22:16:02+09:00; mixQ greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-greedy-rep3`; cleanup attempted.
- total host_bytes=98306711552 host_pages=24000662 gc_pages=29883926 WAF=2.245129
- phaseA(test4) host_pages=12000331 gc_pages=14662649 WAF=2.221854
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000331 gc_pages=15221277 WAF=2.268405
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ fixed10 — started 2026-09-22T22:16:02+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixQ fixed10`; evidence `result/mix-20260911/mixQ-fixed10/`.

- Finished 2026-09-22T22:32:25+09:00; mixQ fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-fixed10-rep3`; cleanup attempted.
- total host_bytes=98306711552 host_pages=24000662 gc_pages=30223298 WAF=2.259269
- phaseA(test4) host_pages=12000331 gc_pages=14826316 WAF=2.235492
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000331 gc_pages=15396982 WAF=2.283046
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ fixed37 — started 2026-09-22T22:32:25+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixQ fixed37`; evidence `result/mix-20260911/mixQ-fixed37/`.

- Finished 2026-09-22T22:48:48+09:00; mixQ fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-fixed37-rep3`; cleanup attempted.
- total host_bytes=98306748416 host_pages=24000671 gc_pages=21406870 WAF=1.891928
- phaseA(test4) host_pages=12000331 gc_pages=11576240 WAF=1.964660
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000340 gc_pages=9830630 WAF=1.819196
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ fixed47 — started 2026-09-22T22:48:48+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixQ fixed47`; evidence `result/mix-20260911/mixQ-fixed47/`.

- Finished 2026-09-22T23:05:11+09:00; mixQ fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-fixed47-rep3`; cleanup attempted.
- total host_bytes=98306711552 host_pages=24000662 gc_pages=17718129 WAF=1.738235
- phaseA(test4) host_pages=12000331 gc_pages=9303982 WAF=1.775310
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000331 gc_pages=8414147 WAF=1.701160
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ fixed50 — started 2026-09-22T23:05:11+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixQ fixed50`; evidence `result/mix-20260911/mixQ-fixed50/`.

- Finished 2026-09-22T23:21:35+09:00; mixQ fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-fixed50-rep3`; cleanup attempted.
- total host_bytes=98405322752 host_pages=24024737 gc_pages=18499621 WAF=1.770024
- phaseA(test4) host_pages=12024400 gc_pages=9521305 WAF=1.791832
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000337 gc_pages=8978316 WAF=1.748172
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ online — started 2026-09-22T23:21:35+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixQ online`; evidence `result/mix-20260911/mixQ-online/`.

- Finished 2026-09-22T23:37:58+09:00; mixQ online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-online-rep3`; cleanup attempted.
- total host_bytes=98306748416 host_pages=24000671 gc_pages=22459655 WAF=1.935793
- phaseA(test4) host_pages=12000331 gc_pages=12709708 WAF=2.059113
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000340 gc_pages=9749947 WAF=1.812473
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO greedy — started 2026-09-22T23:38:01+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixO greedy`; evidence `result/mix-20260911/mixO-greedy/`.

- Finished 2026-09-22T23:49:31+09:00; mixO greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-greedy-rep3`; cleanup attempted.
- total host_bytes=182743810048 host_pages=44615188 gc_pages=94960565 WAF=3.128436
- phaseA(oltp) host_pages=9825676 gc_pages=10756407 WAF=2.094724
- phaseB(varmail) host_pages=34789512 gc_pages=84204158 WAF=3.420389
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO fixed10 — started 2026-09-22T23:49:31+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixO fixed10`; evidence `result/mix-20260911/mixO-fixed10/`.

- Finished 2026-09-23T00:01:02+09:00; mixO fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-fixed10-rep3`; cleanup attempted.
- total host_bytes=188006166528 host_pages=45899943 gc_pages=90848739 WAF=2.979278
- phaseA(oltp) host_pages=8638813 gc_pages=9505442 WAF=2.100318
- phaseB(varmail) host_pages=37261130 gc_pages=81343297 WAF=3.183060
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO fixed37 — started 2026-09-23T00:01:02+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixO fixed37`; evidence `result/mix-20260911/mixO-fixed37/`.

- Finished 2026-09-23T00:12:33+09:00; mixO fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-fixed37-rep3`; cleanup attempted.
- total host_bytes=231915261952 host_pages=56619937 gc_pages=73837998 WAF=2.304099
- phaseA(oltp) host_pages=8994025 gc_pages=3602443 WAF=1.400537
- phaseB(varmail) host_pages=47625912 gc_pages=70235555 WAF=2.474734
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO fixed47 — started 2026-09-23T00:12:33+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixO fixed47`; evidence `result/mix-20260911/mixO-fixed47/`.

- Finished 2026-09-23T00:24:05+09:00; mixO fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-fixed47-rep3`; cleanup attempted.
- total host_bytes=258865217536 host_pages=63199516 gc_pages=57485862 WAF=1.909593
- phaseA(oltp) host_pages=8794026 gc_pages=2521613 WAF=1.286742
- phaseB(varmail) host_pages=54405490 gc_pages=54964249 WAF=2.010270
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO fixed50 — started 2026-09-23T00:24:05+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixO fixed50`; evidence `result/mix-20260911/mixO-fixed50/`.

- Finished 2026-09-23T00:35:36+09:00; mixO fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-fixed50-rep3`; cleanup attempted.
- total host_bytes=253506801664 host_pages=61891309 gc_pages=63843523 WAF=2.031543
- phaseA(oltp) host_pages=9073648 gc_pages=2921883 WAF=1.322019
- phaseB(varmail) host_pages=52817661 gc_pages=60921640 WAF=2.153433
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO online — started 2026-09-23T00:35:36+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixO online`; evidence `result/mix-20260911/mixO-online/`.

- Finished 2026-09-23T00:47:07+09:00; mixO online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-online-rep3`; cleanup attempted.
- total host_bytes=259729928192 host_pages=63410627 gc_pages=60704941 WAF=1.957331
- phaseA(oltp) host_pages=8940642 gc_pages=5167134 WAF=1.577938
- phaseB(varmail) host_pages=54469985 gc_pages=55537807 WAF=2.019604
- ycsb-load 
- ycsb-run 

### mix-20260911 mixP greedy — started 2026-09-23T00:47:13+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixP greedy`; evidence `result/mix-20260911/mixP-greedy/`.

- Finished 2026-09-23T00:55:14+09:00; mixP greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-greedy-rep3`; cleanup attempted.
- total host_bytes=42377420800 host_pages=10346050 gc_pages=10505846 WAF=2.015445
- phaseA(sqlite-a) host_pages=795246 gc_pages=383015 WAF=1.481631
- phaseB(oltp) host_pages=9550804 gc_pages=10122831 WAF=2.059893
- phaseA-load host_pages=452312 gc_pages=281682 WAF=1.622760
- phaseA-run host_pages=342934 gc_pages=101333 WAF=1.295488
- ycsb-load [OVERALL], Throughput(ops/sec), 22567.250406210507
- ycsb-run [OVERALL], Throughput(ops/sec), 55129.07093733203

### mix-20260911 mixP fixed10 — started 2026-09-23T00:55:15+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixP fixed10`; evidence `result/mix-20260911/mixP-fixed10/`.

- Finished 2026-09-23T01:03:14+09:00; mixP fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-fixed10-rep3`; cleanup attempted.
- total host_bytes=38866534400 host_pages=9488900 gc_pages=9774781 WAF=2.030128
- phaseA(sqlite-a) host_pages=806480 gc_pages=397134 WAF=1.492429
- phaseB(oltp) host_pages=8682420 gc_pages=9377647 WAF=2.080073
- phaseA-load host_pages=453335 gc_pages=282670 WAF=1.623534
- phaseA-run host_pages=353145 gc_pages=114464 WAF=1.324127
- ycsb-load [OVERALL], Throughput(ops/sec), 26957.084321759758
- ycsb-run [OVERALL], Throughput(ops/sec), 56107.277113841665

### mix-20260911 mixP fixed37 — started 2026-09-23T01:03:14+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixP fixed37`; evidence `result/mix-20260911/mixP-fixed37/`.

- Finished 2026-09-23T01:11:08+09:00; mixP fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-fixed37-rep3`; cleanup attempted.
- total host_bytes=39467917312 host_pages=9635722 gc_pages=2157074 WAF=1.223862
- phaseA(sqlite-a) host_pages=712327 gc_pages=294083 WAF=1.412848
- phaseB(oltp) host_pages=8923395 gc_pages=1862991 WAF=1.208776
- phaseA-load host_pages=452312 gc_pages=203805 WAF=1.450585
- phaseA-run host_pages=260015 gc_pages=90278 WAF=1.347203
- ycsb-load [OVERALL], Throughput(ops/sec), 31082.929255253013
- ycsb-run [OVERALL], Throughput(ops/sec), 58953.57406042741

### mix-20260911 mixP fixed47 — started 2026-09-23T01:11:09+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixP fixed47`; evidence `result/mix-20260911/mixP-fixed47/`.

- Finished 2026-09-23T01:18:57+09:00; mixP fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-fixed47-rep3`; cleanup attempted.
- total host_bytes=38954385408 host_pages=9510348 gc_pages=1580143 WAF=1.166150
- phaseA(sqlite-a) host_pages=774676 gc_pages=213117 WAF=1.275105
- phaseB(oltp) host_pages=8735672 gc_pages=1367026 WAF=1.156488
- phaseA-load host_pages=452310 gc_pages=124571 WAF=1.275411
- phaseA-run host_pages=322366 gc_pages=88546 WAF=1.274675
- ycsb-load [OVERALL], Throughput(ops/sec), 28338.24529585128
- ycsb-run [OVERALL], Throughput(ops/sec), 63716.58861384561

### mix-20260911 mixP fixed50 — started 2026-09-23T01:18:57+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixP fixed50`; evidence `result/mix-20260911/mixP-fixed50/`.

- Finished 2026-09-23T01:26:50+09:00; mixP fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-fixed50-rep3`; cleanup attempted.
- total host_bytes=40626040832 host_pages=9918467 gc_pages=1545290 WAF=1.155799
- phaseA(sqlite-a) host_pages=806101 gc_pages=208139 WAF=1.258205
- phaseB(oltp) host_pages=9112366 gc_pages=1337151 WAF=1.146740
- phaseA-load host_pages=453332 gc_pages=128175 WAF=1.282740
- phaseA-run host_pages=352769 gc_pages=79964 WAF=1.226675
- ycsb-load [OVERALL], Throughput(ops/sec), 29110.386585933862
- ycsb-run [OVERALL], Throughput(ops/sec), 58700.08658262771

### mix-20260911 mixP online — started 2026-09-23T01:26:51+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixP online`; evidence `result/mix-20260911/mixP-online/`.

- Finished 2026-09-23T01:34:45+09:00; mixP online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-online-rep3`; cleanup attempted.
- total host_bytes=40137773056 host_pages=9799261 gc_pages=1658199 WAF=1.169217
- phaseA(sqlite-a) host_pages=798818 gc_pages=309202 WAF=1.387074
- phaseB(oltp) host_pages=9000443 gc_pages=1348997 WAF=1.149881
- phaseA-load host_pages=452313 gc_pages=218203 WAF=1.482416
- phaseA-run host_pages=346505 gc_pages=90999 WAF=1.262620
- ycsb-load [OVERALL], Throughput(ops/sec), 31059.758976270343
- ycsb-run [OVERALL], Throughput(ops/sec), 61829.53596933255

### mix-20260911 mixH greedy — started 2026-09-23T01:34:55+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixH greedy`; evidence `result/mix-20260911/mixH-greedy/`.

- Finished 2026-09-23T02:02:25+09:00; mixH greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-greedy-rep3`; cleanup attempted.
- total host_bytes=156121735168 host_pages=38115658 gc_pages=52672178 WAF=2.381904
- phaseA(test3) host_pages=6000421 gc_pages=6927885 WAF=2.154566
- phaseB(test4) host_pages=24000658 gc_pages=30514308 WAF=2.271395
- phaseC(sqlite-a) host_pages=8114579 gc_pages=15229985 WAF=2.876867
- phaseC-load host_pages=1398351 gc_pages=1659248 WAF=2.186575
- phaseC-run host_pages=6716228 gc_pages=13570737 WAF=3.020589
- ycsb-load [OVERALL], Throughput(ops/sec), 25596.177637472803
- ycsb-run [OVERALL], Throughput(ops/sec), 12282.371725980287

### mix-20260911 mixH fixed10 — started 2026-09-23T02:02:26+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixH fixed10`; evidence `result/mix-20260911/mixH-fixed10/`.

- Finished 2026-09-23T02:32:43+09:00; mixH fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-fixed10-rep3`; cleanup attempted.
- total host_bytes=156407808000 host_pages=38185500 gc_pages=53332165 WAF=2.396660
- phaseA(test3) host_pages=6026026 gc_pages=6836409 WAF=2.134481
- phaseB(test4) host_pages=24000658 gc_pages=30861126 WAF=2.285845
- phaseC(sqlite-a) host_pages=8158816 gc_pages=15634630 WAF=2.916287
- phaseC-load host_pages=1398345 gc_pages=1690278 WAF=2.208770
- phaseC-run host_pages=6760471 gc_pages=13944352 WAF=3.062630
- ycsb-load [OVERALL], Throughput(ops/sec), 24416.04948319362
- ycsb-run [OVERALL], Throughput(ops/sec), 8081.493783310907

### mix-20260911 mixH fixed37 — started 2026-09-23T02:32:43+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixH fixed37`; evidence `result/mix-20260911/mixH-fixed37/`.

- Finished 2026-09-23T03:02:15+09:00; mixH fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-fixed37-rep3`; cleanup attempted.
- total host_bytes=155863506944 host_pages=38052614 gc_pages=32499710 WAF=1.854073
- phaseA(test3) host_pages=6000421 gc_pages=4947798 WAF=1.824575
- phaseB(test4) host_pages=24000670 gc_pages=21802182 WAF=1.908399
- phaseC(sqlite-a) host_pages=8051523 gc_pages=5749730 WAF=1.714117
- phaseC-load host_pages=1398349 gc_pages=1264127 WAF=1.904014
- phaseC-run host_pages=6653174 gc_pages=4485603 WAF=1.674205
- ycsb-load [OVERALL], Throughput(ops/sec), 26492.405510420347
- ycsb-run [OVERALL], Throughput(ops/sec), 8815.660138670333

### mix-20260911 mixH fixed47 — started 2026-09-23T03:02:15+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixH fixed47`; evidence `result/mix-20260911/mixH-fixed47/`.

- Finished 2026-09-23T03:31:49+09:00; mixH fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-fixed47-rep3`; cleanup attempted.
- total host_bytes=155884933120 host_pages=38057845 gc_pages=27341200 WAF=1.718412
- phaseA(test3) host_pages=6000418 gc_pages=4771761 WAF=1.795238
- phaseB(test4) host_pages=24000661 gc_pages=17662597 WAF=1.735921
- phaseC(sqlite-a) host_pages=8056766 gc_pages=4906842 WAF=1.609034
- phaseC-load host_pages=1398351 gc_pages=539344 WAF=1.385700
- phaseC-run host_pages=6658415 gc_pages=4367498 WAF=1.655937
- ycsb-load [OVERALL], Throughput(ops/sec), 26858.856707999465
- ycsb-run [OVERALL], Throughput(ops/sec), 8770.333470004363

### mix-20260911 mixH fixed50 — started 2026-09-23T03:31:49+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixH fixed50`; evidence `result/mix-20260911/mixH-fixed50/`.

- Finished 2026-09-23T04:01:14+09:00; mixH fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-fixed50-rep3`; cleanup attempted.
- total host_bytes=155782836224 host_pages=38032919 gc_pages=28041656 WAF=1.737300
- phaseA(test3) host_pages=6000418 gc_pages=4792255 WAF=1.798654
- phaseB(test4) host_pages=24000658 gc_pages=18512993 WAF=1.771354
- phaseC(sqlite-a) host_pages=8031843 gc_pages=4736408 WAF=1.589704
- phaseC-load host_pages=1398349 gc_pages=547665 WAF=1.391651
- phaseC-run host_pages=6633494 gc_pages=4188743 WAF=1.631453
- ycsb-load [OVERALL], Throughput(ops/sec), 25544.959128065395
- ycsb-run [OVERALL], Throughput(ops/sec), 8975.814667378749

### mix-20260911 mixH online — started 2026-09-23T04:01:15+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixH online`; evidence `result/mix-20260911/mixH-online/`.

- Finished 2026-09-23T04:30:50+09:00; mixH online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-online-rep3`; cleanup attempted.
- total host_bytes=155757846528 host_pages=38026818 gc_pages=34227952 WAF=1.900100
- phaseA(test3) host_pages=6007067 gc_pages=6837852 WAF=2.138301
- phaseB(test4) host_pages=24000658 gc_pages=23211849 WAF=1.967134
- phaseC(sqlite-a) host_pages=8019093 gc_pages=4178251 WAF=1.521038
- phaseC-load host_pages=1398349 gc_pages=778978 WAF=1.557070
- phaseC-run host_pages=6620744 gc_pages=3399273 WAF=1.513428
- ycsb-load [OVERALL], Throughput(ops/sec), 23338.13061573768
- ycsb-run [OVERALL], Throughput(ops/sec), 9068.38240461762

### mix-20260911 mixF greedy — started 2026-09-23T04:31:03+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixF greedy`; evidence `result/mix-20260911/mixF-greedy/`.

- Finished 2026-09-23T04:47:31+09:00; mixF greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-greedy-rep3`; cleanup attempted.
- total host_bytes=189513412608 host_pages=46267923 gc_pages=125746336 WAF=3.717786
- phaseA(test4) host_pages=24020107 gc_pages=29877234 WAF=2.243843
- phaseB(varmail) host_pages=22247816 gc_pages=95869102 WAF=5.309147
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF fixed10 — started 2026-09-23T04:47:31+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixF fixed10`; evidence `result/mix-20260911/mixF-fixed10/`.

- Finished 2026-09-23T05:03:58+09:00; mixF fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-fixed10-rep3`; cleanup attempted.
- total host_bytes=188078112768 host_pages=45917508 gc_pages=124633857 WAF=3.714299
- phaseA(test4) host_pages=24025768 gc_pages=28796416 WAF=2.198564
- phaseB(varmail) host_pages=21891740 gc_pages=95837441 WAF=5.377790
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF fixed37 — started 2026-09-23T05:03:58+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixF fixed37`; evidence `result/mix-20260911/mixF-fixed37/`.

- Finished 2026-09-23T05:20:24+09:00; mixF fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-fixed37-rep3`; cleanup attempted.
- total host_bytes=215565967360 host_pages=52628410 gc_pages=109355055 WAF=3.077871
- phaseA(test4) host_pages=24024736 gc_pages=22939336 WAF=1.954822
- phaseB(varmail) host_pages=28603674 gc_pages=86415719 WAF=4.021141
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF fixed47 — started 2026-09-23T05:20:24+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixF fixed47`; evidence `result/mix-20260911/mixF-fixed47/`.

- Finished 2026-09-23T05:36:51+09:00; mixF fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-fixed47-rep3`; cleanup attempted.
- total host_bytes=271076880384 host_pages=66180879 gc_pages=91429719 WAF=2.381513
- phaseA(test4) host_pages=24000658 gc_pages=18566487 WAF=1.773582
- phaseB(varmail) host_pages=42180221 gc_pages=72863232 WAF=2.727427
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF fixed50 — started 2026-09-23T05:36:51+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixF fixed50`; evidence `result/mix-20260911/mixF-fixed50/`.

- Finished 2026-09-23T05:53:17+09:00; mixF fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-fixed50-rep3`; cleanup attempted.
- total host_bytes=251351572480 host_pages=61365130 gc_pages=97859626 WAF=2.594711
- phaseA(test4) host_pages=24000664 gc_pages=19503668 WAF=1.812630
- phaseB(varmail) host_pages=37364466 gc_pages=78355958 WAF=3.097072
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF online — started 2026-09-23T05:53:17+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixF online`; evidence `result/mix-20260911/mixF-online/`.

- Finished 2026-09-23T06:09:44+09:00; mixF online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-online-rep3`; cleanup attempted.
- total host_bytes=195259822080 host_pages=47670855 gc_pages=114663006 WAF=3.405306
- phaseA(test4) host_pages=24016546 gc_pages=22559657 WAF=1.939338
- phaseB(varmail) host_pages=23654309 gc_pages=92103349 WAF=4.893724
- ycsb-load 
- ycsb-run 

### mix-20260911 main greedy — started 2026-09-23T08:38:21+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (4000000 records, 1000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh main greedy`; evidence `result/mix-20260911/main-greedy/`.

- Finished 2026-09-23T08:55:19+09:00; main greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/main-greedy`; cleanup attempted.
- total host_bytes=150660931584 host_pages=36782454 gc_pages=63836268 WAF=2.735509
- phaseA(test4) host_pages=24000661 gc_pages=29978379 WAF=2.249065
- phaseB(sqlite-a) host_pages=12781678 gc_pages=33857760 WAF=3.648929
- phaseB-load host_pages=11916414 gc_pages=31776145 WAF=3.666586
- phaseB-run host_pages=865264 gc_pages=2081615 WAF=3.405757
- ycsb-load [OVERALL], Throughput(ops/sec), 20464.649875421444
- ycsb-run [OVERALL], Throughput(ops/sec), 8001.664346184007

### mix-20260911 main fixed10 — started 2026-09-23T08:55:20+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (4000000 records, 1000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh main fixed10`; evidence `result/mix-20260911/main-fixed10/`.

- Finished 2026-09-23T09:12:32+09:00; main fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/main-fixed10`; cleanup attempted.
- total host_bytes=150747840512 host_pages=36803672 gc_pages=63625238 WAF=2.728774
- phaseA(test4) host_pages=24025243 gc_pages=29655243 WAF=2.234337
- phaseB(sqlite-a) host_pages=12778314 gc_pages=33969908 WAF=3.658403
- phaseB-load host_pages=11917649 gc_pages=31848677 WAF=3.672396
- phaseB-run host_pages=860665 gc_pages=2121231 WAF=3.464642
- ycsb-load [OVERALL], Throughput(ops/sec), 18934.014957871816
- ycsb-run [OVERALL], Throughput(ops/sec), 7977.02616464582

### mix-20260911 main fixed37 — started 2026-09-23T09:12:33+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (4000000 records, 1000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh main fixed37`; evidence `result/mix-20260911/main-fixed37/`.

- Finished 2026-09-23T09:29:52+09:00; main fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/main-fixed37`; cleanup attempted.
- total host_bytes=150794493952 host_pages=36815062 gc_pages=48887482 WAF=2.327921
- phaseA(test4) host_pages=24025753 gc_pages=22810483 WAF=1.949418
- phaseB(sqlite-a) host_pages=12789194 gc_pages=26076888 WAF=3.038978
- phaseB-load host_pages=11917224 gc_pages=24005097 WAF=3.014320
- phaseB-run host_pages=871970 gc_pages=2071791 WAF=3.375989
- ycsb-load [OVERALL], Throughput(ops/sec), 18011.851798483403
- ycsb-run [OVERALL], Throughput(ops/sec), 8206.676952368447

### mix-20260911 main fixed50 — started 2026-09-23T09:29:53+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (4000000 records, 1000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh main fixed50`; evidence `result/mix-20260911/main-fixed50/`.

- Finished 2026-09-23T09:46:53+09:00; main fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/main-fixed50`; cleanup attempted.
- total host_bytes=150628270080 host_pages=36774480 gc_pages=37200130 WAF=2.011575
- phaseA(test4) host_pages=24000658 gc_pages=19517783 WAF=1.813219
- phaseB(sqlite-a) host_pages=12773707 gc_pages=17682262 WAF=2.384270
- phaseB-load host_pages=11917263 gc_pages=15584390 WAF=2.307716
- phaseB-run host_pages=856444 gc_pages=2097872 WAF=3.449515
- ycsb-load [OVERALL], Throughput(ops/sec), 18864.987997151387
- ycsb-run [OVERALL], Throughput(ops/sec), 9045.026140125545

### mix-20260911 t4 onlinev2 — started 2026-09-23T09:48:26+09:00

- Phase A fio test4 fixed payload (5898240000/2949120000/983040000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (20000 records, 20000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v2.ko`.
- Command: `bash script/mix-20260911.sh t4 onlinev2`; evidence `result/mix-20260911/t4-onlinev2/`.

- Finished 2026-09-23T09:50:52+09:00; t4 onlinev2 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-onlinev2-rep1-smoke`; cleanup attempted.
- total host_bytes=9851650048 host_pages=2405188 gc_pages=2332541 WAF=1.969796
- phaseA(test4) host_pages=2405188 gc_pages=2332541 WAF=1.969796
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 onlinev2 — started 2026-09-23T09:50:52+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v2.ko`.
- Command: `bash script/mix-20260911.sh t4 onlinev2`; evidence `result/mix-20260911/t4-onlinev2/`.

- Finished 2026-09-23T10:02:15+09:00; t4 onlinev2 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-onlinev2-rep1`; cleanup attempted.
- total host_bytes=98365558784 host_pages=24015029 gc_pages=26838815 WAF=2.117584
- phaseA(test4) host_pages=24015029 gc_pages=26838815 WAF=2.117584
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 onlinev2 — started 2026-09-23T10:02:15+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v2.ko`.
- Command: `bash script/mix-20260911.sh t4 onlinev2`; evidence `result/mix-20260911/t4-onlinev2/`.

- Finished 2026-09-23T10:13:37+09:00; t4 onlinev2 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-onlinev2-rep2`; cleanup attempted.
- total host_bytes=98306707456 host_pages=24000661 gc_pages=26898114 WAF=2.120724
- phaseA(test4) host_pages=24000661 gc_pages=26898114 WAF=2.120724
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 onlinev2 — started 2026-09-23T10:13:37+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v2.ko`.
- Command: `bash script/mix-20260911.sh t4 onlinev2`; evidence `result/mix-20260911/t4-onlinev2/`.

- Finished 2026-09-23T10:25:00+09:00; t4 onlinev2 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-onlinev2-rep3`; cleanup attempted.
- total host_bytes=98411585536 host_pages=24026266 gc_pages=26038474 WAF=2.083750
- phaseA(test4) host_pages=24026266 gc_pages=26038474 WAF=2.083750
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixP greedy — started 2026-09-23T10:25:03+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixP greedy`; evidence `result/mix-20260911/mixP-greedy/`.

- Finished 2026-09-23T10:32:59+09:00; mixP greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-greedy-rep1`; cleanup attempted.
- total host_bytes=40141365248 host_pages=9800138 gc_pages=9873428 WAF=2.007478
- phaseA(sqlite-a) host_pages=796008 gc_pages=386117 WAF=1.485067
- phaseB(oltp) host_pages=9004130 gc_pages=9487311 WAF=2.053662
- phaseA-load host_pages=452312 gc_pages=282412 WAF=1.624374
- phaseA-run host_pages=343696 gc_pages=103705 WAF=1.301735
- ycsb-load [OVERALL], Throughput(ops/sec), 27636.524430687597
- ycsb-run [OVERALL], Throughput(ops/sec), 57591.24613058815

### mix-20260911 mixP fixed10 — started 2026-09-23T10:33:00+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed10.ko`.
- Command: `bash script/mix-20260911.sh mixP fixed10`; evidence `result/mix-20260911/mixP-fixed10/`.

- Finished 2026-09-23T10:40:55+09:00; mixP fixed10 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-fixed10-rep1`; cleanup attempted.
- total host_bytes=36644470784 host_pages=8946404 gc_pages=9206035 WAF=2.029021
- phaseA(sqlite-a) host_pages=792714 gc_pages=414541 WAF=1.522939
- phaseB(oltp) host_pages=8153690 gc_pages=8791494 WAF=2.078223
- phaseA-load host_pages=452310 gc_pages=291639 WAF=1.644777
- phaseA-run host_pages=340404 gc_pages=122902 WAF=1.361047
- ycsb-load [OVERALL], Throughput(ops/sec), 27602.959037208788
- ycsb-run [OVERALL], Throughput(ops/sec), 57604.51619406961

### mix-20260911 mixP fixed37 — started 2026-09-23T10:40:56+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixP fixed37`; evidence `result/mix-20260911/mixP-fixed37/`.

- Finished 2026-09-23T10:48:54+09:00; mixP fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-fixed37-rep1`; cleanup attempted.
- total host_bytes=37208117248 host_pages=9084013 gc_pages=2079765 WAF=1.228948
- phaseA(sqlite-a) host_pages=797313 gc_pages=300774 WAF=1.377235
- phaseB(oltp) host_pages=8286700 gc_pages=1778991 WAF=1.214680
- phaseA-load host_pages=452310 gc_pages=209317 WAF=1.462773
- phaseA-run host_pages=345003 gc_pages=91457 WAF=1.265090
- ycsb-load [OVERALL], Throughput(ops/sec), 27460.456942003515
- ycsb-run [OVERALL], Throughput(ops/sec), 55263.12153742004

### mix-20260911 mixP fixed47 — started 2026-09-23T10:48:55+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixP fixed47`; evidence `result/mix-20260911/mixP-fixed47/`.

- Finished 2026-09-23T10:56:56+09:00; mixP fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-fixed47-rep1`; cleanup attempted.
- total host_bytes=37633273856 host_pages=9187811 gc_pages=1552733 WAF=1.168999
- phaseA(sqlite-a) host_pages=798814 gc_pages=209999 WAF=1.262888
- phaseB(oltp) host_pages=8388997 gc_pages=1342734 WAF=1.160059
- phaseA-load host_pages=452310 gc_pages=125021 WAF=1.276406
- phaseA-run host_pages=346504 gc_pages=84978 WAF=1.245244
- ycsb-load [OVERALL], Throughput(ops/sec), 28299.750962191534
- ycsb-run [OVERALL], Throughput(ops/sec), 53643.032440623865

### mix-20260911 mixP fixed50 — started 2026-09-23T10:56:57+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixP fixed50`; evidence `result/mix-20260911/mixP-fixed50/`.

- Finished 2026-09-23T11:04:53+09:00; mixP fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-fixed50-rep1`; cleanup attempted.
- total host_bytes=37337989120 host_pages=9115720 gc_pages=1446491 WAF=1.158681
- phaseA(sqlite-a) host_pages=807207 gc_pages=212727 WAF=1.263535
- phaseB(oltp) host_pages=8308513 gc_pages=1233764 WAF=1.148494
- phaseA-load host_pages=455382 gc_pages=126824 WAF=1.278500
- phaseA-run host_pages=351825 gc_pages=85903 WAF=1.244164
- ycsb-load [OVERALL], Throughput(ops/sec), 24161.592732192905
- ycsb-run [OVERALL], Throughput(ops/sec), 57845.26391901663

### mix-20260911 mixP online — started 2026-09-23T11:04:54+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixP online`; evidence `result/mix-20260911/mixP-online/`.

- Finished 2026-09-23T11:13:05+09:00; mixP online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-online-rep1`; cleanup attempted.
- total host_bytes=38379503616 host_pages=9369996 gc_pages=1556170 WAF=1.166080
- phaseA(sqlite-a) host_pages=797304 gc_pages=285572 WAF=1.358172
- phaseB(oltp) host_pages=8572692 gc_pages=1270598 WAF=1.148215
- phaseA-load host_pages=452310 gc_pages=193254 WAF=1.427260
- phaseA-run host_pages=344994 gc_pages=92318 WAF=1.267593
- ycsb-load [OVERALL], Throughput(ops/sec), 22465.851905104242
- ycsb-run [OVERALL], Throughput(ops/sec), 50697.72747436596

### mix-20260911 mixA onlinev2 — started 2026-09-23T11:13:14+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v2.ko`.
- Command: `bash script/mix-20260911.sh mixA onlinev2`; evidence `result/mix-20260911/mixA-onlinev2/`.

## 2026-09-23 — v2는 긴 실험으로만 평가 (queue11, queue7 긴 블록 뒤 인계)

- **관찰**: v2 빠른 3영역 쓰기 10분 × 3회 WAF 2.118 / 2.121 / 2.084 — v1(2.001)보다 나쁨, 최적 고정(1.774) 대비 +18%.
- **해석(추정, kernel.log로 확인 예정)**: v2 강제 순회는 60 arm × 30초 ≈ 30분. 10분 실험에서는 arm 0~19(k=2, k=4 = 가장 나쁜 조합)만 써보고 끝나 학습 단계에 들어가지 못한다. 10분 실험은 v2의 학습을 평가할 수 없다.
- **사용자 결정**: 워크로드 시간을 늘린다.
- **변경**: queue7의 긴 블록(phase-length ×3/×6, 60분 빠른 3영역 ×2 + fixed47)까지만 실행하고, 이후 10분짜리 단일·믹스 v2 run은 취소. 대신 `script/gh-queue11-v2long.sh`:
  1. 60분 빠른 3영역: v2 3회차 + 같은 길이의 v1 / 견고(fixed50) / Greedy 각 1회
  2. 6배 길이 믹스 "빠른→느린 3영역"(mixD), "뜨거운 구역 512→128 MB"(mixK): v2 / v1 / fixed47 / fixed50 각 1회
  3. 6배 길이 mixA, mixC v2 2·3회차
- **판정 (09-15 기준 유지)**: 60분 이상 run에서 v2의 최적 고정 대비 손실이 v1보다 줄었는가, 목표 ≤4%. 끝나면 QUEUE7DONE을 남겨 queue10(아주 느린 sweep)이 이어서 시작.

- Finished 2026-09-23T12:01:53+09:00; mixA onlinev2 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-onlinev2-rep1-x3`; cleanup attempted.
- total host_bytes=383931740160 host_pages=93733335 gc_pages=82615640 WAF=1.881390
- phaseA(test4) host_pages=72001990 gc_pages=72684102 WAF=2.009474
- phaseB(sqlite-a) host_pages=21731345 gc_pages=9931538 WAF=1.457014
- phaseB-load host_pages=1398349 gc_pages=629391 WAF=1.450096
- phaseB-run host_pages=20332996 gc_pages=9302147 WAF=1.457490
- ycsb-load [OVERALL], Throughput(ops/sec), 21759.628635671284
- ycsb-run [OVERALL], Throughput(ops/sec), 12396.924736203773

### mix-20260911 mixC onlinev2 — started 2026-09-23T12:01:54+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v2.ko`.
- Command: `bash script/mix-20260911.sh mixC onlinev2`; evidence `result/mix-20260911/mixC-onlinev2/`.

- Finished 2026-09-23T13:03:21+09:00; mixC onlinev2 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-onlinev2-rep1-x3`; cleanup attempted.
- total host_bytes=368653312000 host_pages=90003250 gc_pages=88489064 WAF=1.983176
- phaseA(test3) host_pages=18001246 gc_pages=20303202 WAF=2.127878
- phaseB(test4) host_pages=72002004 gc_pages=68185862 WAF=1.947000
- ycsb-load 
- ycsb-run 

### mix-20260911 mixA onlinev2 — started 2026-09-23T13:03:21+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 24000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v2.ko`.
- Command: `bash script/mix-20260911.sh mixA onlinev2`; evidence `result/mix-20260911/mixA-onlinev2/`.

- Finished 2026-09-23T14:38:19+09:00; mixA onlinev2 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-onlinev2-rep1-x6`; cleanup attempted.
- total host_bytes=762290143232 host_pages=186105992 gc_pages=157387770 WAF=1.845689
- phaseA(test4) host_pages=144003969 gc_pages=137163555 WAF=1.952498
- phaseB(sqlite-a) host_pages=42102023 gc_pages=20224215 WAF=1.480362
- phaseB-load host_pages=1398351 gc_pages=659943 WAF=1.471944
- phaseB-run host_pages=40703672 gc_pages=19564272 WAF=1.480651
- ycsb-load [OVERALL], Throughput(ops/sec), 22856.272142013637
- ycsb-run [OVERALL], Throughput(ops/sec), 12504.884720593982

### mix-20260911 mixC onlinev2 — started 2026-09-23T14:38:20+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v2.ko`.
- Command: `bash script/mix-20260911.sh mixC onlinev2`; evidence `result/mix-20260911/mixC-onlinev2/`.

- Finished 2026-09-23T16:39:47+09:00; mixC onlinev2 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-onlinev2-rep1-x6`; cleanup attempted.
- total host_bytes=737306497024 host_pages=180006469 gc_pages=170349778 WAF=1.946354
- phaseA(test3) host_pages=36002490 gc_pages=35893190 WAF=1.996964
- phaseB(test4) host_pages=144003979 gc_pages=134456588 WAF=1.933701
- ycsb-load 
- ycsb-run 

### mix-20260911 t4long onlinev2 — started 2026-09-23T16:39:59+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v2.ko`.
- Command: `bash script/mix-20260911.sh t4long onlinev2`; evidence `result/mix-20260911/t4long-onlinev2/`.

- Finished 2026-09-23T17:41:22+09:00; t4long onlinev2 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4long-onlinev2-rep1`; cleanup attempted.
- total host_bytes=589840244736 host_pages=144003966 gc_pages=136979764 WAF=1.951222
- phaseA(test4) host_pages=144003966 gc_pages=136979764 WAF=1.951222
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4long onlinev2 — started 2026-09-23T17:41:22+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v2.ko`.
- Command: `bash script/mix-20260911.sh t4long onlinev2`; evidence `result/mix-20260911/t4long-onlinev2/`.

- Finished 2026-09-23T18:42:45+09:00; t4long onlinev2 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4long-onlinev2-rep2`; cleanup attempted.
- total host_bytes=589840244736 host_pages=144003966 gc_pages=138944200 WAF=1.964864
- phaseA(test4) host_pages=144003966 gc_pages=138944200 WAF=1.964864
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4long fixed47 — started 2026-09-23T18:42:45+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh t4long fixed47`; evidence `result/mix-20260911/t4long-fixed47/`.

- Finished 2026-09-23T19:44:08+09:00; t4long fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4long-fixed47-rep1`; cleanup attempted.
- total host_bytes=589840232448 host_pages=144003963 gc_pages=111293370 WAF=1.772849
- phaseA(test4) host_pages=144003963 gc_pages=111293370 WAF=1.772849
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4long onlinev2 — started 2026-09-23T19:54:21+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v2.ko`.
- Command: `bash script/mix-20260911.sh t4long onlinev2`; evidence `result/mix-20260911/t4long-onlinev2/`.

- Finished 2026-09-23T20:55:44+09:00; t4long onlinev2 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4long-onlinev2-rep3`; cleanup attempted.
- total host_bytes=589840220160 host_pages=144003960 gc_pages=137946702 WAF=1.957937
- phaseA(test4) host_pages=144003960 gc_pages=137946702 WAF=1.957937
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4long online — started 2026-09-23T20:55:44+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh t4long online`; evidence `result/mix-20260911/t4long-online/`.

## 사전 등록 2026-09-23 — 거래 DB 흉내(oltp) ratio 재확인 (queue12, queue10 뒤)

- **질문**: 60-arm sweep(1회)에서 oltp 1등은 arm46(k10,s25,r7) 1.332, k10·r16 중 최고 arm50 1.471 → ratio 7이 10% 좋다. 이 10%가 진짜인가 잡음인가? (oltp는 GitHub 순위와 ρ=0.164로 1회 측정 신뢰도가 낮다.) 이 답에 따라 "후보를 scale 5개로 줄여도 되는가"가 갈린다.
- **조건**: GitHub 방식 `gh-filebench.sh`, runtime 300 s, arm46(k10,s25,r7) / arm47(k10,s25,r16) / arm49(k10,s50,r7) / arm50(k10,s50,r16) × 3회. 같은 scale에서 ratio 7 vs 16 두 쌍.
- **판정**: 3회 평균에서 r7이 r16보다 두 쌍 모두 ≥3% 좋고 반복 편차보다 크면 → ratio는 워크로드마다 달라야 함(후보 축소 불가). 차이 <3% 또는 편차 안이면 → sweep의 10%는 잡음, scale만 학습하는 축소안 재검토 가능.
- **v2 확인(장치 없이)**: `t4-onlinev2-rep1/kernel.log`의 evaluated arm = 0~24, 37 → 10분 run에서 v2는 k=2/k=4 위주로만 써보고 끝났음. 09-23 해석 확인.

- Finished 2026-09-23T21:57:07+09:00; t4long online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4long-online-rep1`; cleanup attempted.
- total host_bytes=589840220160 host_pages=144003960 gc_pages=138786892 WAF=1.963771
- phaseA(test4) host_pages=144003960 gc_pages=138786892 WAF=1.963771
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4long fixed50 — started 2026-09-23T21:57:07+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh t4long fixed50`; evidence `result/mix-20260911/t4long-fixed50/`.

## 사전 등록 2026-09-23 — 3시간 빠른 3영역 쓰기 (queue13, queue11 뒤 / 아주 느린 sweep 앞)

- **이유**: 60분 run에서 v2 +10% (1.951~1.965 vs fixed47 1.773). 순회 30분을 빼면 학습 시간은 30분뿐. 사용자 결정: 실험 시간을 더 늘린다.
- **조건**: `MULT=18 mix-20260911.sh t4` = 빠른 3영역 쓰기 payload ×18 ≈ 3시간 (명시 계측). v2 ×2(seed 1,2), v1 ×1, fixed47 ×1, fixed50 ×1. 약 15시간.
- **판정**: v2의 fixed47 대비 손실이 60분(+10%)보다 줄어 ≤4%에 가까워지면 "시간만 주면 배운다". 60분과 같으면 시간은 원인이 아님 → 학습기 자체(후보 수·드리프트 리셋) 수정으로 넘어감. `control-series.txt`(30초 간격)로 시간대별 WAF도 본다.
- **참고**: v2 STALE 240 window ≈ 2시간 → 3시간 run 안에서 재확인 순회가 한 번 발생할 수 있음(기록).
- queue10(아주 느린 sweep)은 이 큐 뒤로 미룸. 순서: queue11 → queue13 → queue10 → queue12.

- Finished 2026-09-23T22:58:30+09:00; t4long fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4long-fixed50-rep1`; cleanup attempted.
- total host_bytes=589945233408 host_pages=144029598 gc_pages=116895881 WAF=1.811610
- phaseA(test4) host_pages=144029598 gc_pages=116895881 WAF=1.811610
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4long greedy — started 2026-09-23T22:58:30+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh t4long greedy`; evidence `result/mix-20260911/t4long-greedy/`.

- Finished 2026-09-23T23:59:53+09:00; t4long greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4long-greedy-rep1`; cleanup attempted.
- total host_bytes=589957812224 host_pages=144032669 gc_pages=180948184 WAF=2.256300
- phaseA(test4) host_pages=144032669 gc_pages=180948184 WAF=2.256300
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD onlinev2 — started 2026-09-23T23:59:55+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v2.ko`.
- Command: `bash script/mix-20260911.sh mixD onlinev2`; evidence `result/mix-20260911/mixD-onlinev2/`.

- Finished 2026-09-24T02:01:19+09:00; mixD onlinev2 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-onlinev2-rep1-x6`; cleanup attempted.
- total host_bytes=737398837248 host_pages=180029013 gc_pages=169010290 WAF=1.938795
- phaseA(test4) host_pages=144026513 gc_pages=138368967 WAF=1.960719
- phaseB(test3) host_pages=36002500 gc_pages=30641323 WAF=1.851089
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD online — started 2026-09-24T02:01:19+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixD online`; evidence `result/mix-20260911/mixD-online/`.

- Finished 2026-09-24T04:02:42+09:00; mixD online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-online-rep1-x6`; cleanup attempted.
- total host_bytes=737306435584 host_pages=180006454 gc_pages=165429274 WAF=1.919019
- phaseA(test4) host_pages=144003963 gc_pages=136213490 WAF=1.945901
- phaseB(test3) host_pages=36002491 gc_pages=29215784 WAF=1.811493
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD fixed47 — started 2026-09-24T04:02:42+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixD fixed47`; evidence `result/mix-20260911/mixD-fixed47/`.

- Finished 2026-09-24T06:04:06+09:00; mixD fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-fixed47-rep1-x6`; cleanup attempted.
- total host_bytes=737306497024 host_pages=180006469 gc_pages=138614023 WAF=1.770050
- phaseA(test4) host_pages=144003981 gc_pages=111333342 WAF=1.773127
- phaseB(test3) host_pages=36002488 gc_pages=27280681 WAF=1.757744
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD fixed50 — started 2026-09-24T06:04:06+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixD fixed50`; evidence `result/mix-20260911/mixD-fixed50/`.

- Finished 2026-09-24T08:05:29+09:00; mixD fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-fixed50-rep1-x6`; cleanup attempted.
- total host_bytes=737306521600 host_pages=180006475 gc_pages=144570365 WAF=1.803140
- phaseA(test4) host_pages=144003981 gc_pages=117175907 WAF=1.813699
- phaseB(test3) host_pages=36002494 gc_pages=27394458 WAF=1.760904
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK onlinev2 — started 2026-09-24T08:05:42+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v2.ko`.
- Command: `bash script/mix-20260911.sh mixK onlinev2`; evidence `result/mix-20260911/mixK-onlinev2/`.

- Finished 2026-09-24T10:07:06+09:00; mixK onlinev2 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-onlinev2-rep1-x6`; cleanup attempted.
- total host_bytes=1179805794304 host_pages=288038524 gc_pages=266646456 WAF=1.925732
- phaseA(test4-hot512M) host_pages=144030602 gc_pages=137140991 WAF=1.952166
- phaseB(test4-hot128M) host_pages=144007922 gc_pages=129505465 WAF=1.899294
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK online — started 2026-09-24T10:07:06+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixK online`; evidence `result/mix-20260911/mixK-online/`.

- Finished 2026-09-24T12:08:30+09:00; mixK online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-online-rep1-x6`; cleanup attempted.
- total host_bytes=1179696705536 host_pages=288011891 gc_pages=263701119 WAF=1.915591
- phaseA(test4-hot512M) host_pages=144003969 gc_pages=137407501 WAF=1.954192
- phaseB(test4-hot128M) host_pages=144007922 gc_pages=126293618 WAF=1.876991
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK fixed47 — started 2026-09-24T12:08:30+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixK fixed47`; evidence `result/mix-20260911/mixK-fixed47/`.

- Finished 2026-09-24T14:09:53+09:00; mixK fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-fixed47-rep1-x6`; cleanup attempted.
- total host_bytes=1179696791552 host_pages=288011912 gc_pages=222661215 WAF=1.773097
- phaseA(test4-hot512M) host_pages=144003990 gc_pages=111014703 WAF=1.770914
- phaseB(test4-hot128M) host_pages=144007922 gc_pages=111646512 WAF=1.775280
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK fixed50 — started 2026-09-24T14:09:53+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixK fixed50`; evidence `result/mix-20260911/mixK-fixed50/`.

- Finished 2026-09-24T16:11:17+09:00; mixK fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-fixed50-rep1-x6`; cleanup attempted.
- total host_bytes=1179696680960 host_pages=288011885 gc_pages=230308438 WAF=1.799649
- phaseA(test4-hot512M) host_pages=144003966 gc_pages=117226735 WAF=1.814052
- phaseB(test4-hot128M) host_pages=144007919 gc_pages=113081703 WAF=1.785246
- ycsb-load 
- ycsb-run 

### mix-20260911 mixC onlinev2 — started 2026-09-24T16:11:28+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v2.ko`.
- Command: `bash script/mix-20260911.sh mixC onlinev2`; evidence `result/mix-20260911/mixC-onlinev2/`.

## 사전 등록 2026-09-24 — iCAT v3 (queue14: queue13 뒤, 아주 느린 sweep 앞)

- **이유**: v1은 20~30분에 최적의 3~4%까지 좁혀졌다가 다시 벌어짐. v2(구간 ×3)는 60분에서 v1과 같음(+10% vs +11%), 순회 30분이 너무 김. 사용자 결정: 순회 시간을 줄이고, 좁혀진 뒤 유지되게 한 v3를 시험.
- **변경** (`online-v3-src` = online-v2-src 복사 후, v1 대비):
  - 판단 구간 64 → **128 GC** / 256 → **512 MiB** (×2), MAX_WINDOW_GC 8192
  - **k=2 arm 0~14 제외 → 45 arm** (근거: GitHub 6개 + 이 머신 3개 sweep 전부에서 k=2가 최하위, Greedy와 0.4% 이내)
  - 강제 순회 **1회** → 45 × ≈20초 ≈ **15분** (v1·v2 30분)
  - 정착 후 **탐색(PROBE) 끔** (v1은 8구간마다 가장 오래된 arm을 1번 씀)
  - 드리프트 리셋 문턱 12.5% → **25%**
  - 그 외 무변경 (γ, c, STABLE 12, CONFIRM 3, TOLERANCE 0.5%, STALE 240).
- 모듈 `buildoutput/nvmev-online-v3.ko` SHA256 `0757c4cd…`, 빌드 로그 `result/gh-repro-20260914/build-online-v3.log`. 러너 정책 `onlinev3`.
- **실행**: 빠른 3영역 쓰기 10분 ×1 / 30분(×3) ×3 + 같은 길이 fixed47·v2·v1 / 60분 ×2 / 3시간 ×1; 6배 믹스 "빠른→느린"(mixD), "뜨거운 구역 512→128 MB"(mixK). 약 13시간.
- **판정**: 60분 이상에서 fixed47 대비 손실 ≤4% → v3 성공. kernel.log에서 settled 이후 reset 횟수·best 교체 횟수로 "유지"를 확인. 30분에서 v2·v1보다 좋으면 "순회 단축" 효과 확인.
- 순서: queue11 → queue13(3시간 v1/v2) → **queue14(v3)** → queue10(아주 느린 sweep) → queue12(oltp 재확인).
- 2026-09-24 사고 기록: onlinev3 매핑을 넣던 sed가 실패해 `script/mix-20260911.sh`가 빈 파일로 커밋됨(f249faa). 그 사이 시작된 run 없음(진행 중이던 mixC onlinev2 rep2는 16:11 시작, 이전 파일 사용). 5fbf396 판으로 복구 + 매핑 1줄 추가(5e1464d).

- Finished 2026-09-24T18:12:51+09:00; mixC onlinev2 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-onlinev2-rep2-x6`; cleanup attempted.
- total host_bytes=737335853056 host_pages=180013636 gc_pages=172450794 WAF=1.957987
- phaseA(test3) host_pages=36009657 gc_pages=35942133 WAF=1.998125
- phaseB(test4) host_pages=144003979 gc_pages=136508661 WAF=1.947951
- ycsb-load 
- ycsb-run 

### mix-20260911 mixA onlinev2 — started 2026-09-24T18:12:51+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 24000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v2.ko`.
- Command: `bash script/mix-20260911.sh mixA onlinev2`; evidence `result/mix-20260911/mixA-onlinev2/`.

- Finished 2026-09-24T19:47:24+09:00; mixA onlinev2 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-onlinev2-rep2-x6`; cleanup attempted.
- total host_bytes=762126753792 host_pages=186066102 gc_pages=157957113 WAF=1.848930
- phaseA(test4) host_pages=144032148 gc_pages=136692566 WAF=1.949042
- phaseB(sqlite-a) host_pages=42033954 gc_pages=21264547 WAF=1.505890
- phaseB-load host_pages=1398342 gc_pages=698025 WAF=1.499180
- phaseB-run host_pages=40635612 gc_pages=20566522 WAF=1.506121
- ycsb-load [OVERALL], Throughput(ops/sec), 23467.751398286855
- ycsb-run [OVERALL], Throughput(ops/sec), 12643.14409707406

### mix-20260911 mixC onlinev2 — started 2026-09-24T19:47:24+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v2.ko`.
- Command: `bash script/mix-20260911.sh mixC onlinev2`; evidence `result/mix-20260911/mixC-onlinev2/`.

- Finished 2026-09-24T21:48:52+09:00; mixC onlinev2 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-onlinev2-rep3-x6`; cleanup attempted.
- total host_bytes=737306497024 host_pages=180006469 gc_pages=172106905 WAF=1.956115
- phaseA(test3) host_pages=36002493 gc_pages=35946927 WAF=1.998457
- phaseB(test4) host_pages=144003976 gc_pages=136159978 WAF=1.945529
- ycsb-load 
- ycsb-run 

### mix-20260911 mixA onlinev2 — started 2026-09-24T21:48:52+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 24000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v2.ko`.
- Command: `bash script/mix-20260911.sh mixA onlinev2`; evidence `result/mix-20260911/mixA-onlinev2/`.

## 2026-09-24 — v4 설계 메모 (아직 빌드 안 함; v3·아주 느린 sweep 결과 후 결정)

- **사용자 아이디어**: 좁혀진 후보를 유지하고(다시 넓히지 않음), 후보 제거 기준은 실험 중 iCAT이 직접 잰 값으로 정한다(사전 지식 없음). 워크로드가 바뀌면 "좁혀진 집합들 사이의 관계"를 이용한다.
- **근거 데이터** (믹스 60-arm sweep, 구간별 상위 5):
  - mixA 앞(빠른 3영역): 47, 46, 32, 31, 50 / mixA 뒤(SQLite 읽기50/수정50): **17(k4,s25,r16)**, 32, 35, 20, 53
  - mixC 뒤(빠른 3영역): 47, 46, 31, 32, 50 / mixC 앞(느린 3영역): 3% 안에 22개 (평평함)
  - 좋은 조합은 파라미터 공간에서 붙어 있는 한 덩어리이고, 워크로드가 바뀌면 이웃으로 이동한다(32 → k만 한 칸 → 17).
- **v4 안**: (1) v3 순회(45 arm) 후 1등보다 잡음 여유를 넘게 나쁜 arm 제거(successive elimination), (2) 생존 집합 안에서만 UCB, 정착 후 유지, (3) 드리프트(25%) 감지 시 전체가 아니라 생존 집합 + 1칸 이웃(k·scale·ratio 중 하나만 인접)만 복원.
- **미확인**: 증거는 빠른 워크로드 믹스 2개뿐. 아주 느린 sweep에서 최적이 멀리(scale 400%) 가면 이웃 이동이 여러 번 필요.

## 사전 등록 2026-09-24 — mixR: 빠른 3영역 → SQLite 읽기50/수정50 → 빠른 3영역, 구간별 쓰기량 균등 (queue15, v3 뒤)

- **이유**: mixA 60-arm sweep에서 구간 1등이 다름 — 빠른 3영역 구간 arm47 1.774 (arm17 1.869, +5%), SQLite 구간 arm17(k4,s25,r16) 1.371 (arm47 1.608, +17%). 그러나 SQLite 구간 쓰기량이 전체의 25%라 전체 WAF 차이는 1% 안으로 묻힘. 구간별 쓰기량을 같게 하면 이 충돌이 전체에 드러난다. 50:50 추정: arm17 고정 1.620, 구간별 최적 1.572 → 적응 이득 여지 약 3%. (사용자가 가져온 제안: test4 → SQLite A → test4, 쓰기량 균형.)
- **조건**: `mix-20260911.sh mixR <policy> 1` + `MULT=3`. A: 빠른 3영역 쓰기 72M 페이지(30분), B: SQLite 60만 레코드 load + 4,200만 op run(≈71M 페이지, 1.7 페이지/op 기준), C: 빠른 3영역 쓰기 72M 페이지. run당 ≈2.5시간. fio 파일·DB 모두 유지(좀비 데이터 없음).
- **정책**: v3, fixed47(빠른 3영역 최적), arm17(SQLite 구간 최적), fixed50(견고), v1, Greedy. 먼저 SMOKE=1로 실행기 확인. 1회씩(총 ≈15시간), 결과 보고 반복 추가.
- **판정**: (1) 구간별 1등이 실제로 갈리는가 (A·C는 47, B는 17). (2) 최고 고정 대비 v3 손실. v3가 최고 고정보다 좋으면 "적응이 이기는 판이 있다". (3) 구간별 최적 조합(oracle) 추정 = A·C는 fixed47, B는 arm17 구간 WAF를 쓰기량 가중 합산.
- 순서: queue11 → queue13(3시간 v1/v2) → queue14(v3) → **queue15(mixR)** → queue10(아주 느린 sweep) → queue12(oltp 재확인).

- Finished 2026-09-24T23:24:06+09:00; mixA onlinev2 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-onlinev2-rep3-x6`; cleanup attempted.
- total host_bytes=762465185792 host_pages=186148727 gc_pages=159672332 WAF=1.857768
- phaseA(test4) host_pages=144003975 gc_pages=138319969 WAF=1.960529
- phaseB(sqlite-a) host_pages=42144752 gc_pages=21352363 WAF=1.506643
- phaseB-load host_pages=1398340 gc_pages=851777 WAF=1.609134
- phaseB-run host_pages=40746412 gc_pages=20500586 WAF=1.503126
- ycsb-load [OVERALL], Throughput(ops/sec), 21473.819834651586
- ycsb-run [OVERALL], Throughput(ops/sec), 12373.557707179756

### mix-20260911 t4 onlinev2 — started 2026-09-24T23:26:09+09:00

- Phase A fio test4 fixed payload (1061683200000/530841600000/176947200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v2.ko`.
- Command: `bash script/mix-20260911.sh t4 onlinev2`; evidence `result/mix-20260911/t4-onlinev2/`.

### 2026-09-24 mixR 타당성 점검 (실행 전)

- **실행 조건은 문제없음**: 공간(6 GiB fio 파일 + DB ≈0.8 GiB, mixA ×3에서 1,200만 op 정상), 쓰기량(SQLite run 1.69 페이지/op, ×1·×3 모두 같음), 길이(구간당 30~90분 > v3 순회 15분).
- **수정 1 — 가장 좋은 고정 조합이 빠져 있었음**: 3구간 가중(빠른 2 : SQLite 1)으로 mixA 구간값을 합산하면 최고 고정은 **arm32(k7,s25,r16) 1.696**, arm17 1.703, arm47 1.719. arm32를 정책 목록에 추가(queue15 재시작). 구간별 최적 합산(oracle) 1.640 → 적응 이득 여지 **3.5%**.
- **위험 1 — 전제가 1회 측정에 기대고 있음**: SQLite 구간 arm17 1.371은 2등 arm32 1.500보다 9% 낮은 단독값(rep1만 있음). mixR의 arm17·arm47·arm32 run이 재측정이 된다.
- **위험 2 — v3는 구조상 이 믹스에 적응하기 어려움**: 구간 전환 시 현재 arm의 WAF 변화는 arm47 −9.4%, arm32 −16.4%(좋아지는 방향)로 드리프트 문턱 25%를 넘지 않을 가능성이 높다(SQLite load 구간 1.218은 −31%지만 파티션당 약 3 window로 "3 window 연속" 조건에 걸칠락 말락). v3는 정착 후 탐색을 끄고, 할인 반감기는 1,376 window ≈ 7.6시간이라 옛 점수도 거의 안 잊는다. → v3는 사실상 "앞 구간에서 고른 고정 조합 + 순회 비용"이 되어 최고 고정보다 약간 질 것으로 예상. 이 믹스에서 적응하려면 v4의 "좁혀진 후보의 이웃만 가끔 확인(32 → 17)" 같은 탐색이 필요하다. v1(8 window마다 탐색)은 비교 기준으로 유지.

## 사전 등록 2026-09-24 — iCAT v4 (mixR에서 v3와 함께 시험)

- **사용자 결정**: 좁혀진 후보를 유지하고, 워크로드가 바뀌면 좁혀진 집합의 이웃으로 옮겨 가는 v4를 만들어 mixR에 넣는다.
- **변경** (`online-v4-src` = online-v3-src + 아래 3가지; 그 외 v3와 동일: 45 arm, 판단 구간 128 GC/512 MiB, 순회 1회, 드리프트 25%):
  1. **실험 중 후보 제거**: 45개를 한 번씩 다 본 뒤부터, 평균 WAF가 현재 1등보다 **15% 넘게** 나쁜 조합은 후보에서 뺀다(`WATGC_V2_ELIM_Q16`). 사전 지식 없이 이 run에서 잰 값만 쓴다.
  2. **이웃 탐색**: 정착 후 8 window마다(v1은 "가장 오래된 arm") 1등의 **1칸 이웃**(k·scale·ratio 중 하나만 한 칸) 6개를 돌아가며 1번씩 쓴다. 탐색한 이웃은 후보로 되살린다. (예: 32=(k7,s25,r16) → 17, 47, 35, 31)
  3. **리셋 시 부분 복원**: 드리프트 리셋 때 45개 전부가 아니라 **남은 후보 + 그 1칸 이웃**만 살려 다시 순회.
  - 로그: window마다 `active=`(남은 후보 수) 추가.
- **검증**: 사용자 공간 확인 `online-v4-src/v4check.c` (이웃 계산, k=2 제외, 45개, 확장 집합) 통과. 모듈 `buildoutput/nvmev-online-v4.ko` SHA256 `db93f822…`, 빌드 로그 `result/gh-repro-20260914/build-online-v4.log`. 러너 정책 `onlinev4`.
- **알려진 한계 (ponytail)**: 제거 기준 15%는 1회 관측 잡음(window당 대략 10~15%)과 비슷해서 진짜 1등이 운 나쁘게 빠질 수 있다. 이웃 탐색으로 되살아날 수 있지만 1등에서 멀면 못 돌아온다. 더 필요하면 "2회 이상 관측 후 제거"로 강화.
- **실행**: queue15에서 SMOKE(빠른 3영역 1/10)로 모듈·로그 확인 → mixR ×3 길이에서 v4를 첫 번째로 실행, 이어서 v3, arm32, fixed47, arm17, fixed50, v1, Greedy.
- **판정**: mixR에서 v4가 최고 고정(arm32 예상)보다 WAF가 낮으면 "적응이 이기는 판이 있고, 이웃 탐색으로 그 판을 딴다". SQLite 구간에서 v4의 best가 17 근처로 옮겨 갔는지 kernel.log로 확인.

- Finished 2026-09-25T02:27:34+09:00; t4 onlinev2 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-onlinev2-rep1-x18`; cleanup attempted.
- total host_bytes=1769520844800 host_pages=432011925 gc_pages=379503856 WAF=1.878457
- phaseA(test4) host_pages=432011925 gc_pages=379503856 WAF=1.878457
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 fixed47 — started 2026-09-25T02:27:41+09:00

- Phase A fio test4 fixed payload (1061683200000/530841600000/176947200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh t4 fixed47`; evidence `result/mix-20260911/t4-fixed47/`.

- Finished 2026-09-25T05:29:04+09:00; t4 fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-fixed47-rep1-x18`; cleanup attempted.
- total host_bytes=1769520865280 host_pages=432011930 gc_pages=333719035 WAF=1.772476
- phaseA(test4) host_pages=432011930 gc_pages=333719035 WAF=1.772476
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 onlinev2 — started 2026-09-25T05:29:07+09:00

- Phase A fio test4 fixed payload (1061683200000/530841600000/176947200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v2.ko`.
- Command: `bash script/mix-20260911.sh t4 onlinev2`; evidence `result/mix-20260911/t4-onlinev2/`.

- Finished 2026-09-25T08:30:30+09:00; t4 onlinev2 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-onlinev2-rep2-x18`; cleanup attempted.
- total host_bytes=1769520734208 host_pages=432011898 gc_pages=389611313 WAF=1.901853
- phaseA(test4) host_pages=432011898 gc_pages=389611313 WAF=1.901853
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 online — started 2026-09-25T08:30:37+09:00

- Phase A fio test4 fixed payload (1061683200000/530841600000/176947200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh t4 online`; evidence `result/mix-20260911/t4-online/`.

- Finished 2026-09-25T11:32:01+09:00; t4 online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-online-rep1-x18`; cleanup attempted.
- total host_bytes=1769571831808 host_pages=432024373 gc_pages=381723418 WAF=1.883569
- phaseA(test4) host_pages=432024373 gc_pages=381723418 WAF=1.883569
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 fixed50 — started 2026-09-25T11:32:07+09:00

- Phase A fio test4 fixed payload (1061683200000/530841600000/176947200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh t4 fixed50`; evidence `result/mix-20260911/t4-fixed50/`.

- Finished 2026-09-25T14:33:31+09:00; t4 fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-fixed50-rep1-x18`; cleanup attempted.
- total host_bytes=1769521065984 host_pages=432011979 gc_pages=351827048 WAF=1.814392
- phaseA(test4) host_pages=432011979 gc_pages=351827048 WAF=1.814392
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 onlinev3 — started 2026-09-25T14:33:37+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v3.ko`.
- Command: `bash script/mix-20260911.sh t4 onlinev3`; evidence `result/mix-20260911/t4-onlinev3/`.

- Finished 2026-09-25T14:45:00+09:00; t4 onlinev3 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-onlinev3-rep1`; cleanup attempted.
- total host_bytes=98312982528 host_pages=24002193 gc_pages=23114714 WAF=1.963025
- phaseA(test4) host_pages=24002193 gc_pages=23114714 WAF=1.963025
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 onlinev3 — started 2026-09-25T14:45:02+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v3.ko`.
- Command: `bash script/mix-20260911.sh t4 onlinev3`; evidence `result/mix-20260911/t4-onlinev3/`.

- Finished 2026-09-25T15:16:25+09:00; t4 onlinev3 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-onlinev3-rep1-x3`; cleanup attempted.
- total host_bytes=294920151040 host_pages=72001990 gc_pages=67578516 WAF=1.938565
- phaseA(test4) host_pages=72001990 gc_pages=67578516 WAF=1.938565
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 onlinev3 — started 2026-09-25T15:16:25+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v3.ko`.
- Command: `bash script/mix-20260911.sh t4 onlinev3`; evidence `result/mix-20260911/t4-onlinev3/`.

- Finished 2026-09-25T15:47:48+09:00; t4 onlinev3 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-onlinev3-rep2-x3`; cleanup attempted.
- total host_bytes=295031361536 host_pages=72029141 gc_pages=67605400 WAF=1.938584
- phaseA(test4) host_pages=72029141 gc_pages=67605400 WAF=1.938584
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 onlinev3 — started 2026-09-25T15:47:48+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v3.ko`.
- Command: `bash script/mix-20260911.sh t4 onlinev3`; evidence `result/mix-20260911/t4-onlinev3/`.

- Finished 2026-09-25T16:19:11+09:00; t4 onlinev3 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-onlinev3-rep3-x3`; cleanup attempted.
- total host_bytes=294920151040 host_pages=72001990 gc_pages=67616086 WAF=1.939086
- phaseA(test4) host_pages=72001990 gc_pages=67616086 WAF=1.939086
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 fixed47 — started 2026-09-25T16:19:11+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh t4 fixed47`; evidence `result/mix-20260911/t4-fixed47/`.

- Finished 2026-09-25T16:50:34+09:00; t4 fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-fixed47-rep1-x3`; cleanup attempted.
- total host_bytes=295037689856 host_pages=72030686 gc_pages=54735564 WAF=1.759892
- phaseA(test4) host_pages=72030686 gc_pages=54735564 WAF=1.759892
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 onlinev2 — started 2026-09-25T16:50:34+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v2.ko`.
- Command: `bash script/mix-20260911.sh t4 onlinev2`; evidence `result/mix-20260911/t4-onlinev2/`.

- Finished 2026-09-25T17:21:57+09:00; t4 onlinev2 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-onlinev2-rep1-x3`; cleanup attempted.
- total host_bytes=294920163328 host_pages=72001993 gc_pages=72277164 WAF=2.003822
- phaseA(test4) host_pages=72001993 gc_pages=72277164 WAF=2.003822
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 online — started 2026-09-25T17:21:57+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh t4 online`; evidence `result/mix-20260911/t4-online/`.

- Finished 2026-09-25T17:53:20+09:00; t4 online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-online-rep1-x3`; cleanup attempted.
- total host_bytes=295035625472 host_pages=72030182 gc_pages=72181809 WAF=2.002105
- phaseA(test4) host_pages=72030182 gc_pages=72181809 WAF=2.002105
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4long onlinev3 — started 2026-09-25T17:53:30+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v3.ko`.
- Command: `bash script/mix-20260911.sh t4long onlinev3`; evidence `result/mix-20260911/t4long-onlinev3/`.

- Finished 2026-09-25T18:54:53+09:00; t4long onlinev3 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4long-onlinev3-rep1`; cleanup attempted.
- total host_bytes=589940932608 host_pages=144028548 gc_pages=130481583 WAF=1.905943
- phaseA(test4) host_pages=144028548 gc_pages=130481583 WAF=1.905943
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4long onlinev3 — started 2026-09-25T18:54:53+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v3.ko`.
- Command: `bash script/mix-20260911.sh t4long onlinev3`; evidence `result/mix-20260911/t4long-onlinev3/`.

- Finished 2026-09-25T19:56:16+09:00; t4long onlinev3 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4long-onlinev3-rep2`; cleanup attempted.
- total host_bytes=589840355328 host_pages=144003993 gc_pages=129572553 WAF=1.899784
- phaseA(test4) host_pages=144003993 gc_pages=129572553 WAF=1.899784
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 onlinev3 — started 2026-09-25T19:56:22+09:00

- Phase A fio test4 fixed payload (1061683200000/530841600000/176947200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v3.ko`.
- Command: `bash script/mix-20260911.sh t4 onlinev3`; evidence `result/mix-20260911/t4-onlinev3/`.

- Finished 2026-09-25T22:57:45+09:00; t4 onlinev3 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-onlinev3-rep1-x18`; cleanup attempted.
- total host_bytes=1769520660480 host_pages=432011880 gc_pages=366494315 WAF=1.848343
- phaseA(test4) host_pages=432011880 gc_pages=366494315 WAF=1.848343
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD onlinev3 — started 2026-09-25T22:57:52+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v3.ko`.
- Command: `bash script/mix-20260911.sh mixD onlinev3`; evidence `result/mix-20260911/mixD-onlinev3/`.

- Finished 2026-09-26T00:59:16+09:00; mixD onlinev3 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-onlinev3-rep1-x6`; cleanup attempted.
- total host_bytes=737306497024 host_pages=180006469 gc_pages=160881545 WAF=1.893754
- phaseA(test4) host_pages=144003969 gc_pages=132222104 WAF=1.918184
- phaseB(test3) host_pages=36002500 gc_pages=28659441 WAF=1.796040
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK onlinev3 — started 2026-09-26T00:59:16+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v3.ko`.
- Command: `bash script/mix-20260911.sh mixK onlinev3`; evidence `result/mix-20260911/mixK-onlinev3/`.

- Finished 2026-09-26T03:00:39+09:00; mixK onlinev3 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-onlinev3-rep1-x6`; cleanup attempted.
- total host_bytes=1179696889856 host_pages=288011936 gc_pages=251797894 WAF=1.874262
- phaseA(test4-hot512M) host_pages=144003999 gc_pages=132577558 WAF=1.920652
- phaseB(test4-hot128M) host_pages=144007937 gc_pages=119220336 WAF=1.827873
- ycsb-load 
- ycsb-run 

### mix-20260911 mixR fixed47 — started 2026-09-26T03:03:32+09:00

- Phase A fio test4 fixed payload (5898240000/2949120000/983040000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (20000 records, 20000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixR fixed47`; evidence `result/mix-20260911/mixR-fixed47/`.

- Finished 2026-09-26T03:07:08+09:00; mixR fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixR-fixed47-rep1-smoke`; cleanup attempted.
- total host_bytes=19819630592 host_pages=4838777 gc_pages=3680725 WAF=1.760673
- phaseA(test4) host_pages=2406212 gc_pages=1982245 WAF=1.823803
- phaseB(sqlite-a) host_pages=25840 gc_pages=8697 WAF=1.336571
- phaseC(test4) host_pages=2406214 gc_pages=1689718 WAF=1.702231
- phaseB-load host_pages=16274 gc_pages=4771 WAF=1.293167
- phaseB-run host_pages=9566 gc_pages=3926 WAF=1.410412
- ycsb-load [OVERALL], Throughput(ops/sec), 16286.644951140066
- ycsb-run [OVERALL], Throughput(ops/sec), 27548.209366391184

### mix-20260911 t4 onlinev4 — started 2026-09-26T03:07:16+09:00

- Phase A fio test4 fixed payload (5898240000/2949120000/983040000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (20000 records, 20000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh t4 onlinev4`; evidence `result/mix-20260911/t4-onlinev4/`.

- Finished 2026-09-26T03:09:41+09:00; t4 onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-onlinev4-rep1-smoke`; cleanup attempted.
- total host_bytes=9864224768 host_pages=2408258 gc_pages=2203008 WAF=1.914772
- phaseA(test4) host_pages=2408258 gc_pages=2203008 WAF=1.914772
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixR onlinev4 — started 2026-09-26T03:09:43+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 42000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixR onlinev4`; evidence `result/mix-20260911/mixR-onlinev4/`.

- Finished 2026-09-26T05:07:45+09:00; mixR onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixR-onlinev4-rep1-x3`; cleanup attempted.
- total host_bytes=886414479360 host_pages=216409785 gc_pages=228822914 WAF=2.057359
- phaseA(test4) host_pages=72026576 gc_pages=64786155 WAF=1.899476
- phaseB(sqlite-a) host_pages=72381222 gc_pages=31236024 WAF=1.431549
- phaseC(test4) host_pages=72001987 gc_pages=132800735 WAF=2.844404
- phaseB-load host_pages=1398350 gc_pages=817234 WAF=1.584427
- phaseB-run host_pages=70982872 gc_pages=30418790 WAF=1.428537
- ycsb-load [OVERALL], Throughput(ops/sec), 24901.43183233036
- ycsb-run [OVERALL], Throughput(ops/sec), 12891.767777517554

### mix-20260911 mixR onlinev3 — started 2026-09-26T05:07:54+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 42000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v3.ko`.
- Command: `bash script/mix-20260911.sh mixR onlinev3`; evidence `result/mix-20260911/mixR-onlinev3/`.

- Finished 2026-09-26T07:27:14+09:00; mixR onlinev3 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixR-onlinev3-rep1-x3`; cleanup attempted.
- total host_bytes=883442528256 host_pages=215684211 gc_pages=253884231 WAF=2.177111
- phaseA(test4) host_pages=72001993 gc_pages=67308081 WAF=1.934809
- phaseB(sqlite-a) host_pages=71680228 gc_pages=30445142 WAF=1.424736
- phaseC(test4) host_pages=72001990 gc_pages=156131008 WAF=3.168426
- phaseB-load host_pages=1398349 gc_pages=1018096 WAF=1.728070
- phaseB-run host_pages=70281879 gc_pages=29427046 WAF=1.418700
- ycsb-load [OVERALL], Throughput(ops/sec), 20670.410307644608
- ycsb-run [OVERALL], Throughput(ops/sec), 9077.198983872411

### mix-20260911 mixR arm32 — started 2026-09-26T07:27:23+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 42000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm32.ko`.
- Command: `bash script/mix-20260911.sh mixR arm32`; evidence `result/mix-20260911/mixR-arm32/`.

- Finished 2026-09-26T09:50:19+09:00; mixR arm32 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixR-arm32-rep1-x3`; cleanup attempted.
- total host_bytes=885964345344 host_pages=216299889 gc_pages=228251613 WAF=2.055255
- phaseA(test4) host_pages=72005564 gc_pages=57297114 WAF=1.795732
- phaseB(sqlite-a) host_pages=72292344 gc_pages=37218464 WAF=1.514833
- phaseC(test4) host_pages=72001981 gc_pages=133736035 WAF=2.857394
- phaseB-load host_pages=1398349 gc_pages=304955 WAF=1.218082
- phaseB-run host_pages=70893995 gc_pages=36913509 WAF=1.520686
- ycsb-load [OVERALL], Throughput(ops/sec), 27135.814752837952
- ycsb-run [OVERALL], Throughput(ops/sec), 8665.377176015474

### mix-20260911 mixR fixed47 — started 2026-09-26T09:50:26+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 42000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixR fixed47`; evidence `result/mix-20260911/mixR-fixed47/`.

- Finished 2026-09-26T12:12:05+09:00; mixR fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixR-fixed47-rep1-x3`; cleanup attempted.
- total host_bytes=885155704832 host_pages=216102467 gc_pages=221372827 WAF=2.024388
- phaseA(test4) host_pages=72001993 gc_pages=55680692 WAF=1.773322
- phaseB(sqlite-a) host_pages=72098482 gc_pages=36924609 WAF=1.512141
- phaseC(test4) host_pages=72001992 gc_pages=128767526 WAF=2.788388
- phaseB-load host_pages=1398349 gc_pages=299541 WAF=1.214210
- phaseB-run host_pages=70700133 gc_pages=36625068 WAF=1.518034
- ycsb-load [OVERALL], Throughput(ops/sec), 22437.455592535807
- ycsb-run [OVERALL], Throughput(ops/sec), 8807.426254056922

### mix-20260911 mixR arm17 — started 2026-09-26T12:12:13+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 42000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm17.ko`.
- Command: `bash script/mix-20260911.sh mixR arm17`; evidence `result/mix-20260911/mixR-arm17/`.

## 2026-09-26 — 분석: "워크로드를 모를 때" 고정 CAT의 손해 (새 실행 없음)

- 방법: 60-arm sweep이 있는 워크로드 8개(이 머신: 빠른 3영역, SQLite 읽기50/수정50, 거래 DB 흉내, mixA, mixC / GitHub: 느린 3영역, hot 위치 이동, SQLite 읽기95) 중 하나를 빼고, 나머지에서 "최악 손해가 가장 작은" 조합을 고른 뒤 뺀 워크로드에서의 손해를 잰다(leave-one-out).
- 결과: 고른 조합은 거의 항상 arm46(k10,s25,r7). 손해 0.3~5.4%, 단 **거래 DB 흉내를 뺐을 때 arm47이 뽑혀 14.0%** 손해. 평균 3.5%.
- 의미: iCAT이 넘어야 할 공정한 기준선은 "워크로드별 최적"이 아니라 이 값(평균 3.5%). v3 3시간(빠른 3영역)은 sweep 최저 1.744 대비 +6.0%로 아직 못 넘음. 거래 DB 흉내의 14%는 1회 sweep 값이라 queue12 재확인(arm46/47/49/50 ×3) 결과에 달려 있다.

- Finished 2026-09-26T14:11:50+09:00; mixR arm17 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixR-arm17-rep1-x3`; cleanup attempted.
- total host_bytes=887523467264 host_pages=216680534 gc_pages=254904492 WAF=2.176407
- phaseA(test4) host_pages=72001990 gc_pages=62796399 WAF=1.872148
- phaseB(sqlite-a) host_pages=72676557 gc_pages=26995395 WAF=1.371446
- phaseC(test4) host_pages=72001987 gc_pages=165112698 WAF=3.293169
- phaseB-load host_pages=1398345 gc_pages=381287 WAF=1.272670
- phaseB-run host_pages=71278212 gc_pages=26614108 WAF=1.373383
- ycsb-load [OVERALL], Throughput(ops/sec), 21366.76044300417
- ycsb-run [OVERALL], Throughput(ops/sec), 12548.670916483217

### mix-20260911 mixR fixed50 — started 2026-09-26T14:11:55+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 42000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixR fixed50`; evidence `result/mix-20260911/mixR-fixed50/`.

## 사전 등록 2026-09-26 — v4 단일 워크로드 (queue16, queue12 뒤)

- **질문**: v3는 3시간에서도 12%의 시간을 나쁜 조합에 써서 한계 ≈1.82(+2.7%)로 추정된다. v4의 실험 중 후보 제거가 이 한계를 낮추는가?
- **조건**: 빠른 3영역 쓰기, v3와 같은 길이 — 60분(`t4long`) ×2(seed 1,2), 3시간(`MULT=18 t4`) ×1. 모듈 `nvmev-online-v4.ko`(db93f822…).
- **판정**: v3(60분 1.900~1.906, 3시간 1.848)보다 낮으면 후보 제거 효과 확인. kernel.log로 나쁜 조합(1등보다 15% 초과)에 쓴 시간 비율을 v3(12.3%)와 비교. 견고 CAT(1.814)보다 낮으면 3시간 목표 달성.
- 2026-09-26: mixR에 기본 CAT(arm37) ×3 추가(queue17, queue15 뒤·아주 느린 sweep 앞). 모든 학습기 버전을 기본값과 같은 믹스에서 비교하기 위함.

- Finished 2026-09-26T16:12:30+09:00; mixR fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixR-fixed50-rep1-x3`; cleanup attempted.
- total host_bytes=888290013184 host_pages=216867679 gc_pages=232839377 WAF=2.073647
- phaseA(test4) host_pages=72012734 gc_pages=58632664 WAF=1.814199
- phaseB(sqlite-a) host_pages=72852957 gc_pages=29624331 WAF=1.406632
- phaseC(test4) host_pages=72001988 gc_pages=144582382 WAF=3.008033
- phaseB-load host_pages=1398349 gc_pages=402738 WAF=1.288010
- phaseB-run host_pages=71454608 gc_pages=29221593 WAF=1.408953
- ycsb-load [OVERALL], Throughput(ops/sec), 24058.703235895584
- ycsb-run [OVERALL], Throughput(ops/sec), 12299.09285405135

### mix-20260911 mixR online — started 2026-09-26T16:12:37+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 42000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh mixR online`; evidence `result/mix-20260911/mixR-online/`.

## 사전 등록 2026-09-26 — 10시간 빠른 3영역 쓰기 (queue18, 맨 뒤)

- **사용자 판단**: 실제 워크로드는 한 번에 3시간, 10시간 이상 돈다. 그 길이에서의 성능이 현실적인 기준이다.
- **추정**(WAF = 한계 + 순회비용/시간, 60분·3시간 두 점): v3 10시간 ≈1.828(+3.2%), 한계 ≈1.82 / v1 10시간 ≈1.856. 고정 CAT은 길이 무관(47번 10분 1.774, 3시간 1.772)이라 재실행 안 함.
- **조건**: `MULT=60 mix-20260911.sh t4` (빠른 3영역 쓰기 payload ×60 ≈ 10시간), v4 ×1, v3 ×1.
- **판정**: 실측이 추정과 ±0.01 안이면 "한계선 모델" 채택. v4가 v3보다 낮고 견고 CAT(1.814)보다 낮으면 "긴 워크로드에서 모르고 고른 고정 CAT 수준을 넘는다".

- Finished 2026-09-26T18:12:20+09:00; mixR online exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixR-online-rep1-x3`; cleanup attempted.
- total host_bytes=887537442816 host_pages=216683946 gc_pages=278980586 WAF=2.287500
- phaseA(test4) host_pages=72001981 gc_pages=73900569 WAF=2.026369
- phaseB(sqlite-a) host_pages=72679980 gc_pages=27743035 WAF=1.381715
- phaseC(test4) host_pages=72001985 gc_pages=177336982 WAF=3.462946
- phaseB-load host_pages=1398350 gc_pages=936885 WAF=1.669993
- phaseB-run host_pages=71281630 gc_pages=26806150 WAF=1.376060
- ycsb-load [OVERALL], Throughput(ops/sec), 24440.914090186972
- ycsb-run [OVERALL], Throughput(ops/sec), 12525.255537579495

### mix-20260911 mixR greedy — started 2026-09-26T18:12:28+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 42000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh mixR greedy`; evidence `result/mix-20260911/mixR-greedy/`.

- Finished 2026-09-26T20:15:38+09:00; mixR greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixR-greedy-rep1-x3`; cleanup attempted.
- total host_bytes=889359118336 host_pages=217128691 gc_pages=469777117 WAF=3.163588
- phaseA(test4) host_pages=72001981 gc_pages=91479987 WAF=2.270520
- phaseB(sqlite-a) host_pages=73124724 gc_pages=151297218 WAF=3.069030
- phaseC(test4) host_pages=72001986 gc_pages=226999912 WAF=4.152690
- phaseB-load host_pages=1398351 gc_pages=1796235 WAF=2.284538
- phaseB-run host_pages=71726373 gc_pages=149500983 WAF=3.084324
- ycsb-load [OVERALL], Throughput(ops/sec), 20814.542426975648
- ycsb-run [OVERALL], Throughput(ops/sec), 11779.190657419067

### mix-20260911 mixR fixed37 — started 2026-09-26T20:15:56+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 42000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixR fixed37`; evidence `result/mix-20260911/mixR-fixed37/`.

- Finished 2026-09-26T22:14:05+09:00; mixR fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixR-fixed37-rep1-x3`; cleanup attempted.
- total host_bytes=886557904896 host_pages=216444801 gc_pages=305202465 WAF=2.410071
- phaseA(test4) host_pages=72018351 gc_pages=70364311 WAF=1.977033
- phaseB(sqlite-a) host_pages=72424457 gc_pages=36129856 WAF=1.498863
- phaseC(test4) host_pages=72001993 gc_pages=198708298 WAF=3.759761
- phaseB-load host_pages=1398351 gc_pages=1130976 WAF=1.808793
- phaseB-run host_pages=71026106 gc_pages=34998880 WAF=1.492761
- ycsb-load [OVERALL], Throughput(ops/sec), 26024.723487312946
- ycsb-run [OVERALL], Throughput(ops/sec), 12834.334411417423

## 2026-09-27 — 월말 마감에 맞춘 순서 변경 (queue20)

- 사유: 9월 안에 정리해야 함. 기존 순서로는 전부 9/29 오전 종료 → 정리 시간 부족.
- 아주 느린 sweep(7/61 완료)은 진행 중인 arm05가 끝나면 멈추고, 아래를 먼저 실행한 뒤 이어서 재개(이미 끝난 arm은 건너뜀).
- 새 순서: ① v4 10시간 ② 거래 DB 흉내 재확인(arm46/47/49/50 ×3) ③ v4 3시간 ④ mixR 2회차 v4·견고 CAT ⑤ 아주 느린 sweep 나머지 ⑥ v3 10시간(시간 남으면) ⑦ 자동 정리(`result/final-20260929/ALL-NEW-RESULTS.md`) 후 push.
- 취소: v4 60분 ×2(3시간·10시간으로 대체). v5는 이번 달 범위에서 제외(향후 과제: 처음 순회 대신 이웃 따라 오르기 + 더 빠른 후보 제거; 근거는 mixR v4 앞 구간 손해의 60%가 순회, 40%가 순회 뒤 느린 후보 축소).
- 사전 등록된 판정 기준은 각 항목의 원래 등록(9/21, 9/23, 9/24, 9/26)을 그대로 따른다.

### mix-20260911 t4 onlinev4 — started 2026-09-27T00:38:43+09:00

- Phase A fio test4 fixed payload (3538944000000/1769472000000/589824000000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh t4 onlinev4`; evidence `result/mix-20260911/t4-onlinev4/`.
- 2026-09-27 02:15: v4 3시간 별도 실행 취소. 10시간 실행의 30초 누적 카운터(control-series.txt)에서 1시간·3시간·10시간 시점 WAF를 읽는다(같은 워크로드·같은 속도라 동등). 3시간 절약.

- Finished 2026-09-27T10:40:07+09:00; t4 onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-onlinev4-rep1-x60`; cleanup attempted.
- total host_bytes=5898461077504 host_pages=1440053974 gc_pages=1162435040 WAF=1.807216
- phaseA(test4) host_pages=1440053974 gc_pages=1162435040 WAF=1.807216
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### 결과 2026-09-27 — v4 10시간 (빠른 3영역 쓰기, `t4-onlinev4-rep1-x60`)

- 누적 WAF: 30분 1.903 / 1시간 1.871 / 2시간 1.848 / **3시간 1.829** / 5시간 1.816 / 7시간 1.813 / **10시간 1.807**.
- 구간 WAF: 0~1시간 1.871, 1~3시간 1.809, 3~5시간 1.795, 5~7시간 1.805, 7~10시간 1.794 → 3시간 이후 정상 상태 ≈1.80.
- 비교: 최적 고정 arm47 1.772(10시간 누적 +2.0%, 정상 상태 +1.5%), 견고 고정 arm50 1.814(**v4 10시간 누적이 0.4% 낮음**), 기본 arm37 1.938, v3 3시간 1.848(v4 3시간 1.829가 1.0% 낮음).
- 사전 추정(10시간이면 최적의 1% 안 ≈1.79)은 약간 빗나감: 실측 1.807(+2.0%).

### 중간 결과 2026-09-27 — 거래 DB 흉내 재확인 (2회차까지)

- arm46(r7) 1.399 / 1.389, arm47(r16) 1.461 / 1.417, arm49(r7) 1.456 / 1.477, arm50(r16) 1.411 / 1.408.
- sweep 1회값(46 1.332, 47 1.518, 차이 14%)은 재현되지 않음: 46 대 47 ≈3%, 49 대 50은 오히려 ratio 16이 ≈4% 좋음. 같은 arm 반복 폭 최대 3%(arm47). → "거래 DB 흉내에서 ratio 7이 14% 좋다"는 1회 측정 잡음이 크게 섞인 값. leave-one-out 기준선의 최대 14%는 과대. 3회차 후 확정.

### mix-20260911 mixR onlinev4 — started 2026-09-27T11:43:23+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 42000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixR onlinev4`; evidence `result/mix-20260911/mixR-onlinev4/`.

- Finished 2026-09-27T14:06:32+09:00; mixR onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixR-onlinev4-rep2-x3`; cleanup attempted.
- total host_bytes=885861896192 host_pages=216274877 gc_pages=238047093 WAF=2.100669
- phaseA(test4) host_pages=72001981 gc_pages=64939710 WAF=1.901916
- phaseB(sqlite-a) host_pages=72270904 gc_pages=36318675 WAF=1.502535
- phaseC(test4) host_pages=72001992 gc_pages=136788708 WAF=2.899791
- phaseB-load host_pages=1398349 gc_pages=616133 WAF=1.440615
- phaseB-run host_pages=70872555 gc_pages=35702542 WAF=1.503757
- ycsb-load [OVERALL], Throughput(ops/sec), 21496.130696474636
- ycsb-run [OVERALL], Throughput(ops/sec), 8652.54708324698

### mix-20260911 mixR fixed50 — started 2026-09-27T14:06:32+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 42000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixR fixed50`; evidence `result/mix-20260911/mixR-fixed50/`.

## 2026-09-27 — 사용자 지적: v3·v4를 믹스에서 평가해야 함 (queue21로 교체)

- 지적: v1은 믹스 14종 × 3회로 평가했는데 v3·v4는 대부분 단일 워크로드로만 평가했다.
- 변경: queue20의 남은 순서를 queue21로 교체. ① 거래 DB 흉내 재확인 마무리 ② mixR 2회차(v4, 견고 CAT) ③ **v4 × 믹스 14종**(×1, seed 1; 기존 v1·고정·Greedy 3회 결과와 비교) ④ v4 × 3배 길이 mixA·mixC(기존 fixed47·fixed50·v1·v2 ×3과 비교) ⑤ 아주 느린 sweep 나머지 ⑥ **v3 × 믹스 14종** ⑦ 자동 정리. v3 10시간은 취소.
- 판정: 믹스별로 v4가 v1·기본 CAT·견고 CAT보다 좋은지, 최적 고정 대비 손해. 14종 중 몇 개에서 견고 CAT을 이기는지 센다.

### 2026-09-27 — 아주 느린 3영역: 핵심 15조합 먼저 (queue21에 삽입)

- 사용자 판단: 지금까지는 정답 조합이 거의 안 움직여 고정 CAT이 최적 근처에 머물렀고, v4가 견고 CAT을 이긴 것은 잡음 범위(v4 mixR 1회 2.057, 2회 2.101). 조합 간 편차가 크고 정답이 멀리 떨어진 재료로 새 믹스를 만들어야 한다.
- 60조합 전부(약 20시간) 대신 scale 축 15개(k4·r16: 17,20,23,26,29 / k7·r7: 31,34,37,40,43 / k10·r16: 47,50,53,56,59)를 먼저 잰다(약 5.5시간). 기존 greedy·arm00~05는 유지.
- 판정(9/21 사전 등록과 동일 기준): 1등 scale ≥200%이고 arm47이 1등 대비 ≥3% 나쁘면 → 빠른 ↔ 아주 느린 믹스를 새로 설계. 아니면 느린 워크로드 방향 폐기.
- 거래 DB 흉내 재확인 3회 평균: arm46 1.430, arm47 1.453, arm49 1.444, arm50 1.449 (차이 1.6% 이내, 같은 arm 반복 폭 최대 8%). → 이 워크로드는 파라미터 영향이 잡음보다 작다. leave-one-out 기준선의 "최대 14%"는 철회.
- mixR 2회차 v4: 전체 2.101 (A 1.902 / B 1.503 / C 2.900). 1회차 2.057과 2% 차이.

- Finished 2026-09-27T16:05:40+09:00; mixR fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixR-fixed50-rep2-x3`; cleanup attempted.
- total host_bytes=887288680448 host_pages=216623213 gc_pages=232527003 WAF=2.073417
- phaseA(test4) host_pages=72009143 gc_pages=58630306 WAF=1.814206
- phaseB(sqlite-a) host_pages=72612086 gc_pages=29220241 WAF=1.402416
- phaseC(test4) host_pages=72001984 gc_pages=144676456 WAF=3.009340
- phaseB-load host_pages=1398349 gc_pages=399145 WAF=1.285440
- phaseB-run host_pages=71213737 gc_pages=28821096 WAF=1.404713
- ycsb-load [OVERALL], Throughput(ops/sec), 22465.178972592483
- ycsb-run [OVERALL], Throughput(ops/sec), 12621.428661581633

### 결과 2026-09-27 20:10 — 아주 느린 3영역 핵심 조합 (18/60, k10 scale 100~400% 3개 남음)

- 상위 9개(20, 37, 34, 50, 40, 17, 47, 43, 31)가 1.579~1.593 안에 모두 있음(차이 0.9%). 1등 arm20(k4,s50,r16) 1.579, arm47 1.589(+0.6%), 기본 arm37 1.581, Greedy 1.695(+7%). k=2와 k4 큰 scale만 나쁨.
- **사전 등록 판정: 기각.** 1등 scale이 200% 이상으로 옮겨 가지 않았고 arm47이 1등 대비 3% 이상 나쁘지 않음. 속도를 1/16로 늦추면 오히려 괜찮은 조합들 사이 차이가 사라진다(평평해짐).
- 결과: 빠른 3영역 ↔ 아주 느린 3영역은 "구간마다 1등이 다른 짝"이 되지 않는다.

### mix-20260911 mixA onlinev4 — started 2026-09-27T21:07:18+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixA onlinev4`; evidence `result/mix-20260911/mixA-onlinev4/`.

- Finished 2026-09-27T21:24:54+09:00; mixA onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-onlinev4-rep1`; cleanup attempted.
- total host_bytes=131630964736 host_pages=32136466 gc_pages=28905675 WAF=1.899467
- phaseA(test4) host_pages=24000661 gc_pages=23117863 WAF=1.963218
- phaseB(sqlite-a) host_pages=8135805 gc_pages=5787812 WAF=1.711400
- phaseB-load host_pages=1398347 gc_pages=1036173 WAF=1.740998
- phaseB-run host_pages=6737458 gc_pages=4751639 WAF=1.705257
- ycsb-load [OVERALL], Throughput(ops/sec), 22492.970946579193
- ycsb-run [OVERALL], Throughput(ops/sec), 12175.299968952984

### mix-20260911 mixB onlinev4 — started 2026-09-27T21:24:54+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixB onlinev4`; evidence `result/mix-20260911/mixB-onlinev4/`.
- 20:10 이후 남은 3개 완료: arm56(k10,s200,r16) 1.577로 1등(20번 1.579와 0.1% 차), arm53 1.581, arm59 1.593. 1등 scale은 200%이지만 arm47은 1등 대비 +0.7%(<3%)라 판정은 여전히 기각. 상위 12개가 1% 안(평평).

- Finished 2026-09-27T21:44:27+09:00; mixB onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-onlinev4-rep1`; cleanup attempted.
- total host_bytes=131370680320 host_pages=32072920 gc_pages=64648879 WAF=3.015684
- phaseA(sqlite-a) host_pages=8072262 gc_pages=3475120 WAF=1.430501
- phaseB(test4) host_pages=24000658 gc_pages=61173759 WAF=3.548837
- phaseA-load host_pages=1400399 gc_pages=571416 WAF=1.408038
- phaseA-run host_pages=6671863 gc_pages=2903704 WAF=1.435216
- ycsb-load [OVERALL], Throughput(ops/sec), 22047.475564047916
- ycsb-run [OVERALL], Throughput(ops/sec), 8890.963447026528

### mix-20260911 mixC onlinev4 — started 2026-09-27T21:44:28+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixC onlinev4`; evidence `result/mix-20260911/mixC-onlinev4/`.

- Finished 2026-09-27T22:05:53+09:00; mixC onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-onlinev4-rep1`; cleanup attempted.
- total host_bytes=122884419584 host_pages=30001079 gc_pages=27166138 WAF=1.905505
- phaseA(test3) host_pages=6000421 gc_pages=5080978 WAF=1.846770
- phaseB(test4) host_pages=24000658 gc_pages=22085160 WAF=1.920190
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD onlinev4 — started 2026-09-27T22:05:53+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixD onlinev4`; evidence `result/mix-20260911/mixD-onlinev4/`.

## 2026-09-27 21:45 — 실수 정정: 믹스 14종을 1배 길이로 v4에 돌린 것 (queue22로 교체)

- 문제(사용자 지적): 믹스 14종은 v1용 설계로 1배 길이가 10~30분(mixA 16분). v4의 첫 순회(약 15분)보다 짧거나 비슷해 v4를 평가할 수 없다. 큐에 넣기 전에 확인했어야 했음.
- 조치: 1배 길이 v4 실행 중단(진행 중이던 mixB는 끝까지 돌게 둠; mixA 1배 결과 1.899는 "짧은 워크로드" 참고값으로 보관). queue22: 13종을 **3배 길이**(`MULT=3`, 파일벤치 구간 `VM_RUN=900`)로 v4 → 견고 CAT(fixed50) → 최적 CAT(fixed47) 순서. 서서히 빨라지는 믹스(mixM)는 단계 길이 120초 고정이라 제외.
- 비교 기준: 같은 3배 길이의 fixed50·fixed47. 판정: 13종 중 v4가 fixed50과 같거나(±1%) 좋은 믹스 수, 최적 대비 손해.
- 취소: v3 × 믹스 14종, 아주 느린 sweep 나머지 45개(핵심 15개로 판정 완료).

- Finished 2026-09-27T22:27:17+09:00; mixD onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-onlinev4-rep1`; cleanup attempted.
- total host_bytes=122926342144 host_pages=30011314 gc_pages=28586410 WAF=1.952521
- phaseA(test4) host_pages=24010893 gc_pages=23159577 WAF=1.964545
- phaseB(test3) host_pages=6000421 gc_pages=5426833 WAF=1.904409
- ycsb-load 
- ycsb-run 

### mix-20260911 mixA onlinev4 — started 2026-09-27T22:27:32+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixA onlinev4`; evidence `result/mix-20260911/mixA-onlinev4/`.

- Finished 2026-09-27T23:15:34+09:00; mixA onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-onlinev4-rep1-x3`; cleanup attempted.
- total host_bytes=383550509056 host_pages=93640261 gc_pages=75819162 WAF=1.809686
- phaseA(test4) host_pages=72001981 gc_pages=64984349 WAF=1.902536
- phaseB(sqlite-a) host_pages=21638280 gc_pages=10834813 WAF=1.500724
- phaseB-load host_pages=1398349 gc_pages=672654 WAF=1.481034
- phaseB-run host_pages=20239931 gc_pages=10162159 WAF=1.502085
- ycsb-load [OVERALL], Throughput(ops/sec), 23776.500891618783
- ycsb-run [OVERALL], Throughput(ops/sec), 12816.952555913955

### mix-20260911 mixC onlinev4 — started 2026-09-27T23:15:45+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixC onlinev4`; evidence `result/mix-20260911/mixC-onlinev4/`.

- Finished 2026-09-28T00:17:11+09:00; mixC onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-onlinev4-rep1-x3`; cleanup attempted.
- total host_bytes=368741351424 host_pages=90024744 gc_pages=79919381 WAF=1.887749
- phaseA(test3) host_pages=18022761 gc_pages=14987422 WAF=1.831583
- phaseB(test4) host_pages=72001983 gc_pages=64931959 WAF=1.901808
- ycsb-load 
- ycsb-run 

### mix-20260911 mixB onlinev4 — started 2026-09-28T00:17:14+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixB onlinev4`; evidence `result/mix-20260911/mixB-onlinev4/`.

- Finished 2026-09-28T01:04:54+09:00; mixB onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-onlinev4-rep1-x3`; cleanup attempted.
- total host_bytes=383455076352 host_pages=93616962 gc_pages=176645864 WAF=2.886900
- phaseA(sqlite-a) host_pages=21614978 gc_pages=8221977 WAF=1.380383
- phaseB(test4) host_pages=72001984 gc_pages=168423887 WAF=3.339156
- phaseA-load host_pages=1402432 gc_pages=606701 WAF=1.432606
- phaseA-run host_pages=20212546 gc_pages=7615276 WAF=1.376760
- ycsb-load [OVERALL], Throughput(ops/sec), 25442.055718102023
- ycsb-run [OVERALL], Throughput(ops/sec), 13050.201951875206

### mix-20260911 mixD onlinev4 — started 2026-09-28T01:05:02+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixD onlinev4`; evidence `result/mix-20260911/mixD-onlinev4/`.

- Finished 2026-09-28T02:06:26+09:00; mixD onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-onlinev4-rep1-x3`; cleanup attempted.
- total host_bytes=368653238272 host_pages=90003232 gc_pages=78697565 WAF=1.874386
- phaseA(test4) host_pages=72001984 gc_pages=64552792 WAF=1.896542
- phaseB(test3) host_pages=18001248 gc_pages=14144773 WAF=1.785766
- ycsb-load 
- ycsb-run 

### mix-20260911 mixJ onlinev4 — started 2026-09-28T02:06:30+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixJ onlinev4`; evidence `result/mix-20260911/mixJ-onlinev4/`.

- Finished 2026-09-28T02:27:51+09:00; mixJ onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-onlinev4-rep1-x3`; cleanup attempted.
- total host_bytes=96868225024 host_pages=23649469 gc_pages=8920505 WAF=1.377197
- phaseA(sqlite-a) host_pages=21559089 gc_pages=8179666 WAF=1.379407
- phaseB(sqlite-b) host_pages=2090380 gc_pages=740839 WAF=1.354404
- phaseA-load host_pages=1400898 gc_pages=616952 WAF=1.440398
- phaseA-run host_pages=20158191 gc_pages=7562714 WAF=1.375168
- ycsb-load [OVERALL], Throughput(ops/sec), 26421.242679114006
- ycsb-run [OVERALL], Throughput(ops/sec), 64473.83973952569

### mix-20260911 mixK onlinev4 — started 2026-09-28T02:28:00+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixK onlinev4`; evidence `result/mix-20260911/mixK-onlinev4/`.

- Finished 2026-09-28T03:29:27+09:00; mixK onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-onlinev4-rep1-x3`; cleanup attempted.
- total host_bytes=589940621312 host_pages=144028472 gc_pages=123661558 WAF=1.858591
- phaseA(test4-hot512M) host_pages=72024511 gc_pages=64613984 WAF=1.897111
- phaseB(test4-hot128M) host_pages=72003961 gc_pages=59047574 WAF=1.820060
- ycsb-load 
- ycsb-run 

### mix-20260911 mixH onlinev4 — started 2026-09-28T03:29:31+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixH onlinev4`; evidence `result/mix-20260911/mixH-onlinev4/`.

- Finished 2026-09-28T04:47:29+09:00; mixH onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-onlinev4-rep1-x3`; cleanup attempted.
- total host_bytes=457353457664 host_pages=111658559 gc_pages=90130315 WAF=1.807196
- phaseA(test3) host_pages=18016080 gc_pages=15013294 WAF=1.833327
- phaseB(test4) host_pages=72001986 gc_pages=64792150 WAF=1.899866
- phaseC(sqlite-a) host_pages=21640493 gc_pages=10324871 WAF=1.477109
- phaseC-load host_pages=1398351 gc_pages=795645 WAF=1.568988
- phaseC-run host_pages=20242142 gc_pages=9529226 WAF=1.470762
- ycsb-load [OVERALL], Throughput(ops/sec), 25733.401955738547
- ycsb-run [OVERALL], Throughput(ops/sec), 12793.886228234402

### mix-20260911 mixF onlinev4 — started 2026-09-28T04:47:38+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixF onlinev4`; evidence `result/mix-20260911/mixF-onlinev4/`.

- Finished 2026-09-28T05:34:06+09:00; mixF onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-onlinev4-rep1-x3`; cleanup attempted.
- total host_bytes=832846864384 host_pages=203331754 gc_pages=274512234 WAF=2.350071
- phaseA(test4) host_pages=72001996 gc_pages=64969902 WAF=1.902335
- phaseB(varmail) host_pages=131329758 gc_pages=209542332 WAF=2.595543
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG onlinev4 — started 2026-09-28T05:34:10+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixG onlinev4`; evidence `result/mix-20260911/mixG-onlinev4/`.

- Finished 2026-09-28T06:08:03+09:00; mixG onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-onlinev4-rep1-x3`; cleanup attempted.
- total host_bytes=240497029120 host_pages=58715095 gc_pages=143131553 WAF=3.437730
- phaseA(concurrent-test4+sqlite-a) host_pages=58715095 gc_pages=143131553 WAF=3.437730
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL onlinev4 — started 2026-09-28T06:08:12+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixL onlinev4`; evidence `result/mix-20260911/mixL-onlinev4/`.

- Finished 2026-09-28T06:39:41+09:00; mixL onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-onlinev4-rep1-x3`; cleanup attempted.
- total host_bytes=184427401216 host_pages=45026221 gc_pages=34576644 WAF=1.767922
- phaseA(alternate-fast/slow-x5) host_pages=45026221 gc_pages=34576644 WAF=1.767922
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO onlinev4 — started 2026-09-28T06:39:44+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixO onlinev4`; evidence `result/mix-20260911/mixO-onlinev4/`.

- Finished 2026-09-28T07:12:09+09:00; mixO onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-onlinev4-rep1-x3`; cleanup attempted.
- total host_bytes=780628525056 host_pages=190583136 gc_pages=164661802 WAF=1.863989
- phaseA(oltp) host_pages=26394086 gc_pages=7175100 WAF=1.271845
- phaseB(varmail) host_pages=164189050 gc_pages=157486702 WAF=1.959179
- ycsb-load 
- ycsb-run 

### mix-20260911 mixP onlinev4 — started 2026-09-28T07:12:19+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixP onlinev4`; evidence `result/mix-20260911/mixP-onlinev4/`.

- Finished 2026-09-28T07:32:18+09:00; mixP onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-onlinev4-rep1-x3`; cleanup attempted.
- total host_bytes=112219267072 host_pages=27397282 gc_pages=3337703 WAF=1.121826
- phaseA(sqlite-a) host_pages=1080600 gc_pages=315115 WAF=1.291611
- phaseB(oltp) host_pages=26316682 gc_pages=3022588 WAF=1.114854
- phaseA-load host_pages=453846 gc_pages=213406 WAF=1.470217
- phaseA-run host_pages=626754 gc_pages=101709 WAF=1.162279
- ycsb-load [OVERALL], Throughput(ops/sec), 32212.343770132717
- ycsb-run [OVERALL], Throughput(ops/sec), 64967.759749224446

### mix-20260911 mixQ onlinev4 — started 2026-09-28T07:32:27+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixQ onlinev4`; evidence `result/mix-20260911/mixQ-onlinev4/`.

- Finished 2026-09-28T08:08:54+09:00; mixQ onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-onlinev4-rep1-x3`; cleanup attempted.
- total host_bytes=294920118272 host_pages=72001982 gc_pages=65204196 WAF=1.905589
- phaseA(test4) host_pages=36000991 gc_pages=34464083 WAF=1.957309
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=36000991 gc_pages=30740113 WAF=1.853869
- ycsb-load 
- ycsb-run 

### mix-20260911 mixB fixed50 — started 2026-09-28T08:08:58+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixB fixed50`; evidence `result/mix-20260911/mixB-fixed50/`.

- Finished 2026-09-28T08:56:31+09:00; mixB fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-fixed50-rep1-x3`; cleanup attempted.
- total host_bytes=383292485632 host_pages=93577267 gc_pages=153972073 WAF=2.645400
- phaseA(sqlite-a) host_pages=21575280 gc_pages=8299798 WAF=1.384690
- phaseB(test4) host_pages=72001987 gc_pages=145672275 WAF=3.023170
- phaseA-load host_pages=1398339 gc_pages=392722 WAF=1.280849
- phaseA-run host_pages=20176941 gc_pages=7907076 WAF=1.391887
- ycsb-load [OVERALL], Throughput(ops/sec), 27948.574622694243
- ycsb-run [OVERALL], Throughput(ops/sec), 13124.464767921183

### mix-20260911 mixD fixed50 — started 2026-09-28T08:56:38+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixD fixed50`; evidence `result/mix-20260911/mixD-fixed50/`.

- Finished 2026-09-28T09:58:03+09:00; mixD fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-fixed50-rep1-x3`; cleanup attempted.
- total host_bytes=368751857664 host_pages=90027309 gc_pages=72232282 WAF=1.802337
- phaseA(test4) host_pages=72026052 gc_pages=58395714 WAF=1.810758
- phaseB(test3) host_pages=18001257 gc_pages=13836568 WAF=1.768645
- ycsb-load 
- ycsb-run 

### mix-20260911 mixJ fixed50 — started 2026-09-28T09:58:05+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixJ fixed50`; evidence `result/mix-20260911/mixJ-fixed50/`.

- Finished 2026-09-28T10:19:45+09:00; mixJ fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-fixed50-rep1-x3`; cleanup attempted.
- total host_bytes=97061978112 host_pages=23696772 gc_pages=9242387 WAF=1.390027
- phaseA(sqlite-a) host_pages=21602546 gc_pages=8377528 WAF=1.387803
- phaseB(sqlite-b) host_pages=2094226 gc_pages=864859 WAF=1.412973
- phaseA-load host_pages=1398341 gc_pages=390321 WAF=1.279131
- phaseA-run host_pages=20204205 gc_pages=7987207 WAF=1.395324
- ycsb-load [OVERALL], Throughput(ops/sec), 28015.128169211373
- ycsb-run [OVERALL], Throughput(ops/sec), 63145.59796250204

### mix-20260911 mixK fixed50 — started 2026-09-28T10:20:00+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixK fixed50`; evidence `result/mix-20260911/mixK-fixed50/`.

- Finished 2026-09-28T11:21:27+09:00; mixK fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-fixed50-rep1-x3`; cleanup attempted.
- total host_bytes=589898620928 host_pages=144018218 gc_pages=115242437 WAF=1.800193
- phaseA(test4-hot512M) host_pages=72014254 gc_pages=58618317 WAF=1.813982
- phaseB(test4-hot128M) host_pages=72003964 gc_pages=56624120 WAF=1.786403
- ycsb-load 
- ycsb-run 

### mix-20260911 mixH fixed50 — started 2026-09-28T11:21:30+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixH fixed50`; evidence `result/mix-20260911/mixH-fixed50/`.

- Finished 2026-09-28T12:39:36+09:00; mixH fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-fixed50-rep1-x3`; cleanup attempted.
- total host_bytes=457389109248 host_pages=111667263 gc_pages=81598097 WAF=1.730725
- phaseA(test3) host_pages=18001240 gc_pages=13890119 WAF=1.771620
- phaseB(test4) host_pages=72001989 gc_pages=58488095 WAF=1.812312
- phaseC(sqlite-a) host_pages=21664034 gc_pages=9219883 WAF=1.425585
- phaseC-load host_pages=1398339 gc_pages=406250 WAF=1.290523
- phaseC-run host_pages=20265695 gc_pages=8813633 WAF=1.434904
- ycsb-load [OVERALL], Throughput(ops/sec), 25146.68901927913
- ycsb-run [OVERALL], Throughput(ops/sec), 12743.696649044967

### mix-20260911 mixF fixed50 — started 2026-09-28T12:39:44+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixF fixed50`; evidence `result/mix-20260911/mixF-fixed50/`.

## 2026-09-28 12:50 — v4 3배 길이 결과와 6배 길이 추가 (queue23)

- v4 ×3 대 견고 CAT ×3: mixA 1.810/1.723(+5.0%), mixC 1.888/1.804(+4.7%), mixB 2.887/2.645(+9.1%), mixD 1.874/1.802(+4.0%), mixJ 1.377/1.390(−0.9%), mixK 1.859/1.800(+3.3%), mixH 1.807/1.731(+4.4%). 3배 길이(30~90분)에서도 첫 순회 비용이 커서 견고 CAT에 대부분 진다.
- v4 ×3 대 기본 CAT(×1 값): 13종 중 10종에서 같거나 좋음(최대 mixB −10%, mixJ −9%), mixL(60초 반복 전환) +6%, mixQ +1% 나쁨. 파일벤치 믹스(F·O·P)는 ×3에서 VM_RUN=900으로 작업이 달라져 ×1 기본값과 비교 불가.
- 사용자 판단: 실험 시간을 더 늘려야 한다. → 견고 CAT ×3 나머지 6종 후, v4 ×6을 mixA·mixC·mixD·mixK에 실행(이 4종은 fixed47·fixed50·v1·v2·v3 ×6 결과가 이미 있음). fixed47 ×3 13종은 취소(×1 값 사용).

- Finished 2026-09-28T13:26:13+09:00; mixF fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-fixed50-rep1-x3`; cleanup attempted.
- total host_bytes=759922397184 host_pages=185527929 gc_pages=269776840 WAF=2.454104
- phaseA(test4) host_pages=72002002 gc_pages=58597396 WAF=1.813830
- phaseB(varmail) host_pages=113525927 gc_pages=211179444 WAF=2.860187
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG fixed50 — started 2026-09-28T13:26:44+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixG fixed50`; evidence `result/mix-20260911/mixG-fixed50/`.

- Finished 2026-09-28T14:00:57+09:00; mixG fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-fixed50-rep1-x3`; cleanup attempted.
- total host_bytes=240587026432 host_pages=58737067 gc_pages=122316592 WAF=3.082443
- phaseA(concurrent-test4+sqlite-a) host_pages=58737067 gc_pages=122316592 WAF=3.082443
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL fixed50 — started 2026-09-28T14:01:06+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixL fixed50`; evidence `result/mix-20260911/mixL-fixed50/`.

- Finished 2026-09-28T14:32:35+09:00; mixL fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-fixed50-rep1-x3`; cleanup attempted.
- total host_bytes=184326713344 host_pages=45001639 gc_pages=31035375 WAF=1.689650
- phaseA(alternate-fast/slow-x5) host_pages=45001639 gc_pages=31035375 WAF=1.689650
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO fixed50 — started 2026-09-28T14:32:37+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixO fixed50`; evidence `result/mix-20260911/mixO-fixed50/`.

- Finished 2026-09-28T15:04:31+09:00; mixO fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-fixed50-rep1-x3`; cleanup attempted.
- total host_bytes=710508855296 host_pages=173464076 gc_pages=167082081 WAF=1.963209
- phaseA(oltp) host_pages=25308340 gc_pages=6502005 WAF=1.256912
- phaseB(varmail) host_pages=148155736 gc_pages=160580076 WAF=2.083860
- ycsb-load 
- ycsb-run 

### mix-20260911 mixP fixed50 — started 2026-09-28T15:04:38+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixP fixed50`; evidence `result/mix-20260911/mixP-fixed50/`.

- Finished 2026-09-28T15:25:03+09:00; mixP fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-fixed50-rep1-x3`; cleanup attempted.
- total host_bytes=106754179072 host_pages=26063032 gc_pages=3660407 WAF=1.140444
- phaseA(sqlite-a) host_pages=1140553 gc_pages=204912 WAF=1.179660
- phaseB(oltp) host_pages=24922479 gc_pages=3455495 WAF=1.138650
- phaseA-load host_pages=452310 gc_pages=127298 WAF=1.281440
- phaseA-run host_pages=688243 gc_pages=77614 WAF=1.112771
- ycsb-load [OVERALL], Throughput(ops/sec), 27331.36547501913
- ycsb-run [OVERALL], Throughput(ops/sec), 56047.79008234355

### mix-20260911 mixQ fixed50 — started 2026-09-28T15:25:13+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixQ fixed50`; evidence `result/mix-20260911/mixQ-fixed50/`.

- Finished 2026-09-28T16:01:40+09:00; mixQ fixed50 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-fixed50-rep1-x3`; cleanup attempted.
- total host_bytes=294920130560 host_pages=72001985 gc_pages=58802799 WAF=1.816683
- phaseA(test4) host_pages=36000994 gc_pages=29322788 WAF=1.814499
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=36000991 gc_pages=29480011 WAF=1.818867
- ycsb-load 
- ycsb-run 

### mix-20260911 mixA onlinev4 — started 2026-09-28T16:01:43+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 24000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixA onlinev4`; evidence `result/mix-20260911/mixA-onlinev4/`.

- Finished 2026-09-28T17:37:09+09:00; mixA onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixA-onlinev4-rep1-x6`; cleanup attempted.
- total host_bytes=762593132544 host_pages=186179964 gc_pages=145697441 WAF=1.782562
- phaseA(test4) host_pages=144003984 gc_pages=124793598 WAF=1.866598
- phaseB(sqlite-a) host_pages=42175980 gc_pages=20903843 WAF=1.495634
- phaseB-load host_pages=1398340 gc_pages=869221 WAF=1.621609
- phaseB-run host_pages=40777640 gc_pages=20034622 WAF=1.491314
- ycsb-load [OVERALL], Throughput(ops/sec), 21290.940704730136
- ycsb-run [OVERALL], Throughput(ops/sec), 12299.41070448462

### mix-20260911 mixC onlinev4 — started 2026-09-28T17:37:20+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixC onlinev4`; evidence `result/mix-20260911/mixC-onlinev4/`.

## 사전 등록 2026-09-28 — v4 앱 믹스 반복 (queue24, queue23 뒤)

- 이유: 3배 길이에서 v4가 견고 CAT을 이긴 4종(거래 DB 흉내→메일 서버 −5.1%, 빠른 3영역→메일 서버 −4.2%, SQLite→거래 DB 흉내 −1.6%, SQLite 수정 많음→읽기 위주 −0.9%)은 모두 1회. v4는 실행마다 약 2% 흔들림(mixR 2.057/2.101).
- 조건: 같은 4종을 v4 ×3 길이 seed 2로 1회씩. 견고 CAT은 반복 안 함(고정 조합은 반복 간 차이 0.1% 이내: mixR 2.074/2.073).
- 판정: 2회 평균에서도 견고 CAT보다 좋으면 "앱 믹스에서 v4 > 견고 CAT"로 기술. 앞 두 종(−5.1%, −4.2%)은 흔들림보다 커서 유지될 것으로, 뒤 두 종(−1.6%, −0.9%)은 "비슷"으로 바뀔 수 있음.
- 끝나면 `RESULTS_ALL.md` 자동 재생성 후 push.

## 사전 등록 2026-09-28 — 마지막 추가 실험 (queue25, queue24 뒤, 약 19시간)

사용자 결정: 넣을 수 있는 만큼 넣고, 모자란 것은 새 환경에서 한다. 시간이 모자라면 뒤에서부터 버린다.
1. **메일 서버 핵심 15조합 + Greedy** (filebench varmail, 15만 파일, 300초, 원저자 계측 방식; 기존 varmail 결과와 같은 조건). 질문: 최적(47)·견고(50) CAT이 여기서도 상위인가? 판정: 47·50이 1등 대비 3% 이상 나쁘면 "견고 CAT은 fio 워크로드에 치우친 선택"을 직접 뒷받침.
2. **v3 하나씩 빼 보기** (빠른 3영역 3시간, v3 1.848과 비교): `online-v3k2`(v3에 k=2 15개를 되돌림, 60개; SHA256 06874884…), `online-v3probe`(v3에 v1식 정착 후 탐색을 되돌림; f54c1997…). 판정: 1.848보다 1% 이상 나빠진 쪽이 v3 개선의 주요인.
3. **v1 10시간** (빠른 3영역, v4 10시간 1.807과 비교). 판정: 추정 한계 ≈1.84~1.86과 맞는지.
끝나면 `RESULTS_ALL.md` 재생성 후 push.

- Finished 2026-09-28T19:38:46+09:00; mixC onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixC-onlinev4-rep1-x6`; cleanup attempted.
- total host_bytes=737306484736 host_pages=180006466 gc_pages=160290271 WAF=1.890470
- phaseA(test3) host_pages=36002493 gc_pages=29732153 WAF=1.825836
- phaseB(test4) host_pages=144003973 gc_pages=130558118 WAF=1.906629
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD onlinev4 — started 2026-09-28T19:38:51+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixD onlinev4`; evidence `result/mix-20260911/mixD-onlinev4/`.

- Finished 2026-09-28T21:40:15+09:00; mixD onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-onlinev4-rep1-x6`; cleanup attempted.
- total host_bytes=737361354752 host_pages=180019862 gc_pages=153372594 WAF=1.851976
- phaseA(test4) host_pages=144017365 gc_pages=125380408 WAF=1.870592
- phaseB(test3) host_pages=36002497 gc_pages=27992186 WAF=1.777507
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK onlinev4 — started 2026-09-28T21:40:20+09:00

- Phase A fio test4 fixed payload (353894400000/176947200000/58982400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixK onlinev4`; evidence `result/mix-20260911/mixK-onlinev4/`.

- Finished 2026-09-28T23:41:43+09:00; mixK onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-onlinev4-rep1-x6`; cleanup attempted.
- total host_bytes=1179805892608 host_pages=288038548 gc_pages=239070602 WAF=1.829995
- phaseA(test4-hot512M) host_pages=144030611 gc_pages=125777714 WAF=1.873271
- phaseB(test4-hot128M) host_pages=144007937 gc_pages=113292888 WAF=1.786713
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO onlinev4 — started 2026-09-28T23:42:11+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixO onlinev4`; evidence `result/mix-20260911/mixO-onlinev4/`.

- Finished 2026-09-29T00:13:46+09:00; mixO onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-onlinev4-rep2-x3`; cleanup attempted.
- total host_bytes=714255400960 host_pages=174378760 gc_pages=146283832 WAF=1.838886
- phaseA(oltp) host_pages=25820176 gc_pages=6678947 WAF=1.258672
- phaseB(varmail) host_pages=148558584 gc_pages=139604885 WAF=1.939730
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF onlinev4 — started 2026-09-29T00:13:57+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixF onlinev4`; evidence `result/mix-20260911/mixF-onlinev4/`.

- Finished 2026-09-29T01:00:25+09:00; mixF onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-onlinev4-rep2-x3`; cleanup attempted.
- total host_bytes=785569161216 host_pages=191789346 gc_pages=259758892 WAF=2.354397
- phaseA(test4) host_pages=72007614 gc_pages=65115723 WAF=1.904289
- phaseB(varmail) host_pages=119781732 gc_pages=194643169 WAF=2.624982
- ycsb-load 
- ycsb-run 

### mix-20260911 mixP onlinev4 — started 2026-09-29T01:00:31+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixP onlinev4`; evidence `result/mix-20260911/mixP-onlinev4/`.

- Finished 2026-09-29T01:20:56+09:00; mixP onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-onlinev4-rep2-x3`; cleanup attempted.
- total host_bytes=107799568384 host_pages=26318254 gc_pages=3499311 WAF=1.132961
- phaseA(sqlite-a) host_pages=1223303 gc_pages=294965 WAF=1.241122
- phaseB(oltp) host_pages=25094951 gc_pages=3204346 WAF=1.127689
- phaseA-load host_pages=452310 gc_pages=202026 WAF=1.446654
- phaseA-run host_pages=770993 gc_pages=92939 WAF=1.120545
- ycsb-load [OVERALL], Throughput(ops/sec), 26502.703275734126
- ycsb-run [OVERALL], Throughput(ops/sec), 54507.299435849454

### mix-20260911 mixJ onlinev4 — started 2026-09-29T01:21:04+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixJ onlinev4`; evidence `result/mix-20260911/mixJ-onlinev4/`.

- Finished 2026-09-29T01:49:47+09:00; mixJ onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-onlinev4-rep2-x3`; cleanup attempted.
- total host_bytes=96816001024 host_pages=23636719 gc_pages=8385488 WAF=1.354765
- phaseA(sqlite-a) host_pages=21534394 gc_pages=7730820 WAF=1.358999
- phaseB(sqlite-b) host_pages=2102325 gc_pages=654668 WAF=1.311402
- phaseA-load host_pages=1405003 gc_pages=597105 WAF=1.424985
- phaseA-run host_pages=20129391 gc_pages=7133715 WAF=1.354393
- ycsb-load [OVERALL], Throughput(ops/sec), 23703.23549164461
- ycsb-run [OVERALL], Throughput(ops/sec), 63134.30244487586

### mix-20260911 t4 onlinev3k2 — started 2026-09-29T03:14:42+09:00

- Phase A fio test4 fixed payload (1061683200000/530841600000/176947200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v3k2.ko`.
- Command: `bash script/mix-20260911.sh t4 onlinev3k2`; evidence `result/mix-20260911/t4-onlinev3k2/`.

- Finished 2026-09-29T03:14:48+09:00; t4 onlinev3k2 exit=127; evidence `/home/oy/iCAT/result/mix-20260911/t4-onlinev3k2-rep1-x18`; cleanup attempted.

### mix-20260911 t4 onlinev3probe — started 2026-09-29T03:14:51+09:00

- Phase A fio test4 fixed payload (1061683200000/530841600000/176947200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v3probe.ko`.
- Command: `bash script/mix-20260911.sh t4 onlinev3probe`; evidence `result/mix-20260911/t4-onlinev3probe/`.

- Finished 2026-09-29T03:14:51+09:00; t4 onlinev3probe exit=1; evidence `/home/oy/iCAT/result/mix-20260911/t4-onlinev3probe-rep1-x18`; cleanup attempted.

### mix-20260911 t4 online — started 2026-09-29T03:14:53+09:00

- Phase A fio test4 fixed payload (3538944000000/1769472000000/589824000000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-mix-20260907.ko`.
- Command: `bash script/mix-20260911.sh t4 online`; evidence `result/mix-20260911/t4-online/`.

- Finished 2026-09-29T03:14:53+09:00; t4 online exit=1; evidence `/home/oy/iCAT/result/mix-20260911/t4-online-rep1-x60`; cleanup attempted.

### mix-20260911 t4 onlinev3k2 — started 2026-09-29T11:15:19+09:00

- Phase A fio test4 fixed payload (1061683200000/530841600000/176947200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v3k2.ko`.
- Command: `bash script/mix-20260911.sh t4 onlinev3k2`; evidence `result/mix-20260911/t4-onlinev3k2/`.

## 2026-09-29 — 사고: fio 실행 불가 (03:14~11:20 장치 유휴)

- 증상: queue25의 v3 빼 보기 2개와 v1 10시간이 시작 직후 실패. `fio: symbol lookup error: .../ceph/libceph-common.so.2: undefined symbol: _ZZN5boost9function2...`.
- 조사: 패키지 변경 없음(apt 기록상 9/29 06:05 이전 변경 없음), 라이브러리 파일 날짜 2026-02 그대로, 해당 기호는 그 라이브러리 자체가 정의함. `drop_caches` 후 fio 정상 → **메모리에 캐시된 라이브러리 사본(page cache)이 손상**된 것으로 판단. 손상 시점은 01:50(queue24 마지막 fio 정상)~03:14 사이이며, 그 사이에는 메일 서버(filebench) 15조합만 돌았다.
- 원인 미확정: NVMeVirt의 메모리 접근 오류 또는 메모리 하드웨어 문제 가능성. WAF는 FTL 카운터로 계산하므로 다른 페이지 손상이 WAF 값에 영향을 줄 경로는 없다고 판단하나, 검증하지 않았다. 향후 메모리 검사(memtest) 필요.
- 조치: 실패 3건은 `*-fiobroken`으로 이름 변경해 보존. queue26에서 재실행하며 매 실행 전 page cache 비우기 + `fio --version` 확인.

## 결과 2026-09-29 — v4 6배 길이, 앱 믹스 반복, 메일 서버 15조합

- **v4 ×6 (약 2시간)** 대 견고 CAT ×6: 빠른 3영역→SQLite 1.783 / 1.724 (+3.4%), 느린→빠른 1.890 / 1.804 (+4.8%), 빠른→느린 1.852 / 1.803 (+2.7%), 뜨거운 구역 축소 1.830 / 1.800 (+1.7%). v1 ×6(1.848/1.940/1.919/1.916)·v3 ×6(–/–/1.894/1.874)보다 모두 좋고 기본 CAT(×1 1.905/1.892/1.943/1.956)보다 모두 좋음. fio 위주 믹스에서는 2시간에도 견고 CAT에 1.7~4.8% 짐.
- **앱 믹스 v4 ×3 2회차**: 거래 DB 흉내→메일 서버 1.839(1회 1.864, 평균 1.851, 견고 1.963 대비 −5.7%), 빠른 3영역→메일 서버 2.354(2.350, 평균 2.352, −4.2%), SQLite→거래 DB 흉내 1.133(1.122, 평균 1.128, −1.1%), SQLite 수정 많음→읽기 위주 1.355(1.377, 평균 1.366, −1.7%). **4종 모두 2회 평균에서도 견고 CAT보다 좋음** (사전 판정: 앞 두 종은 확실, 뒤 두 종은 차이가 작음).
- **메일 서버 핵심 15조합 + Greedy** (15만 파일, 300초): 1등 47번 3.455, 31번 3.933, 50번 4.008(+16%), 17번 4.139, 기본 37번 4.588, Greedy 4.769. 판정: 최적 CAT(47)은 여기서도 1등 → "47이 fio에만 유리" 가설은 기각. 견고 CAT(50)은 1등보다 16% 나쁨 → "견고 CAT은 fio 위주로 고른 것이라 앱에서는 견고하지 않다"는 지지.

## 사전 등록 2026-09-29 — v4가 이긴 믹스 4종에서 상위 고정 조합과 순위 비교 (queue27, v1 10시간 취소)

- 사용자 지적: 견고 CAT 하나와만 비교할 게 아니라 여러 조합과 비교해 순위를 봐야 한다.
- 60개 전부(약 160시간)는 불가 → 지금까지 모든 워크로드에서 상위였던 조합 47·46·31·17번 + 기본 37번을 같은 3배 길이(`MULT=3 VM_RUN=900`)로 1회씩. 기존 견고 50번 ×3과 합쳐 고정 6개와 v4(2회 평균) 비교. 약 15시간.
- 대상: 거래 DB 흉내→메일 서버(mixO), 빠른 3영역→메일 서버(mixF), SQLite 수정 많음→읽기 위주(mixJ), SQLite→거래 DB 흉내(mixP).
- 판정: v4가 6개 중 몇 등인지. 1등 고정 대비 손해. v4가 6개 모두보다 좋으면 "이 믹스들에서는 상위 고정 조합보다도 좋다".
- v1 10시간은 취소(추정값 사용). 하나씩 빼 보기(v3k2 진행 중, v3probe)는 유지.

## 2026-09-29 — 정정: 빠른 3영역 "60개 중 순위"에 측정 방식이 섞임 (queue28 사전 등록)

- 사용자 질문으로 확인: 60개 고정 조합은 원저자 방식(파티션별 GC 100회 워밍업 제외 ~ 모듈 해제), v1~v4는 명시 계측(사전 조건화 뒤 start~stop)으로 측정. 같은 조합에서 두 방식 차이: arm47 1.746 / 1.774(+1.6%), arm50 1.786 / 1.812~1.814(+1.5%), Greedy 2.186 / 2.256(+3.2%). 원저자 방식이 낮게 측정됨. 이전의 "두 방식 1% 이내 일치" 서술은 부정확(1.5~3%).
- 영향 범위: 빠른 3영역 단일의 "60개 중 N등" 숫자만. 그 외 비교(길이별 표, 믹스 전부, 믹스 60-arm 순위, 느린 3영역·메일 서버·거래 DB·SQLite 순위)는 같은 방식끼리라 영향 없음.
- 조치(queue28, queue27 뒤): 빠른 3영역 상위 12개(31, 46, 32, 34, 16, 45, 49, 30, 35, 17, 15, 33) + Greedy + 기본 37을 명시 계측 10분으로 재측정(47·50은 기존 값 있음). 약 2.5시간. 결과로 v1~v4 순위를 같은 자로 다시 매긴다.

- Finished 2026-09-29T14:16:46+09:00; t4 onlinev3k2 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-onlinev3k2-rep1-x18`; cleanup attempted.
- total host_bytes=1769520734208 host_pages=432011898 gc_pages=390902520 WAF=1.904842
- phaseA(test4) host_pages=432011898 gc_pages=390902520 WAF=1.904842
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 onlinev3probe — started 2026-09-29T14:16:50+09:00

- Phase A fio test4 fixed payload (1061683200000/530841600000/176947200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v3probe.ko`.
- Command: `bash script/mix-20260911.sh t4 onlinev3probe`; evidence `result/mix-20260911/t4-onlinev3probe/`.

- Finished 2026-09-29T17:18:16+09:00; t4 onlinev3probe exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-onlinev3probe-rep1-x18`; cleanup attempted.
- total host_bytes=1769520734208 host_pages=432011898 gc_pages=378199937 WAF=1.875439
- phaseA(test4) host_pages=432011898 gc_pages=378199937 WAF=1.875439
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO fixed47 — started 2026-09-29T17:18:36+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixO fixed47`; evidence `result/mix-20260911/mixO-fixed47/`.

- Finished 2026-09-29T17:50:27+09:00; mixO fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-fixed47-rep1-x3`; cleanup attempted.
- total host_bytes=709052059648 host_pages=173108413 gc_pages=157599202 WAF=1.910408
- phaseA(oltp) host_pages=24260616 gc_pages=6637241 WAF=1.273581
- phaseB(varmail) host_pages=148847349 gc_pages=150961691 WAF=2.014205
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO arm46 — started 2026-09-29T17:50:33+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm46.ko`.
- Command: `bash script/mix-20260911.sh mixO arm46`; evidence `result/mix-20260911/mixO-arm46/`.

- Finished 2026-09-29T18:22:10+09:00; mixO arm46 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-arm46-rep1-x3`; cleanup attempted.
- total host_bytes=715267633152 host_pages=174625887 gc_pages=203715952 WAF=2.166585
- phaseA(oltp) host_pages=25369968 gc_pages=7927207 WAF=1.312464
- phaseB(varmail) host_pages=149255919 gc_pages=195788745 WAF=2.311765
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO arm31 — started 2026-09-29T18:22:16+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm31.ko`.
- Command: `bash script/mix-20260911.sh mixO arm31`; evidence `result/mix-20260911/mixO-arm31/`.

- Finished 2026-09-29T18:53:54+09:00; mixO arm31 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-arm31-rep1-x3`; cleanup attempted.
- total host_bytes=722307543040 host_pages=176344615 gc_pages=207628189 WAF=2.177400
- phaseA(oltp) host_pages=26024591 gc_pages=8071360 WAF=1.310144
- phaseB(varmail) host_pages=150320024 gc_pages=199556829 WAF=2.327547
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO arm17 — started 2026-09-29T18:54:01+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm17.ko`.
- Command: `bash script/mix-20260911.sh mixO arm17`; evidence `result/mix-20260911/mixO-arm17/`.

- Finished 2026-09-29T19:25:52+09:00; mixO arm17 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-arm17-rep1-x3`; cleanup attempted.
- total host_bytes=709806206976 host_pages=173292531 gc_pages=161976252 WAF=1.934698
- phaseA(oltp) host_pages=25540535 gc_pages=6641473 WAF=1.260037
- phaseB(varmail) host_pages=147751996 gc_pages=155334779 WAF=2.051321
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO fixed37 — started 2026-09-29T19:25:59+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixO fixed37`; evidence `result/mix-20260911/mixO-fixed37/`.

### 결과 2026-09-29 — v3 하나씩 빼 보기 (빠른 3영역 3시간, 명시 계측)

- v3 1.848 / v3 + k=2 되돌림(60개) **1.905 (+3.1%)** / v3 + 정착 후 탐색 되돌림 **1.875 (+1.5%)**. (참고 v1 1.884, v2 1.878~1.902)
- 판정: 둘 다 1% 이상 나빠짐 → 두 변경 모두 v3 개선에 기여, k=2 제외의 기여가 더 큼. 1회씩이라 순서는 잠정.

### 중간 결과 2026-09-29 — 거래 DB 흉내 → 메일 서버(mixO) ×3, 고정 조합
- 47번 1.910, 17번 1.935, 견고 50번 1.963, 46번 2.167, 31번 2.177 (기본 37번 진행 중). v4 2회 1.864 / 1.839 (평균 1.851) → **지금까지 잰 고정 조합 5개 모두보다 좋음**(최고 47번 대비 −3.1%).

- Finished 2026-09-29T19:57:38+09:00; mixO fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-fixed37-rep1-x3`; cleanup attempted.
- total host_bytes=655135768576 host_pages=159945256 gc_pages=196137485 WAF=2.226279
- phaseA(oltp) host_pages=24429401 gc_pages=8340017 WAF=1.341393
- phaseB(varmail) host_pages=135515855 gc_pages=187797468 WAF=2.385797
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF fixed47 — started 2026-09-29T19:57:52+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixF fixed47`; evidence `result/mix-20260911/mixF-fixed47/`.
- mixO 기본 37번 ×3: 2.226 → v4(1.851)가 고정 6개 중 최고(47번 1.910)보다 3.1%, 기본보다 16.8% 좋음. 7개 중 1등.

- Finished 2026-09-29T20:44:22+09:00; mixF fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-fixed47-rep1-x3`; cleanup attempted.
- total host_bytes=830048137216 host_pages=202648471 gc_pages=211129804 WAF=2.041852
- phaseA(test4) host_pages=72001996 gc_pages=55514419 WAF=1.771012
- phaseB(varmail) host_pages=130646475 gc_pages=155615385 WAF=2.191118
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF arm46 — started 2026-09-29T20:44:25+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm46.ko`.
- Command: `bash script/mix-20260911.sh mixF arm46`; evidence `result/mix-20260911/mixF-arm46/`.

- Finished 2026-09-29T21:30:55+09:00; mixF arm46 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-arm46-rep1-x3`; cleanup attempted.
- total host_bytes=719482863616 host_pages=175654996 gc_pages=240036803 WAF=2.366524
- phaseA(test4) host_pages=72001981 gc_pages=56563773 WAF=1.785586
- phaseB(varmail) host_pages=103653015 gc_pages=183473030 WAF=2.770069
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF arm31 — started 2026-09-29T21:30:59+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm31.ko`.
- Command: `bash script/mix-20260911.sh mixF arm31`; evidence `result/mix-20260911/mixF-arm31/`.

- Finished 2026-09-29T22:17:31+09:00; mixF arm31 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-arm31-rep1-x3`; cleanup attempted.
- total host_bytes=745438928896 host_pages=181991926 gc_pages=267217415 WAF=2.468293
- phaseA(test4) host_pages=72001990 gc_pages=57445493 WAF=1.797832
- phaseB(varmail) host_pages=109989936 gc_pages=209771922 WAF=2.907192
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF arm17 — started 2026-09-29T22:17:38+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm17.ko`.
- Command: `bash script/mix-20260911.sh mixF arm17`; evidence `result/mix-20260911/mixF-arm17/`.

### 2026-09-29 22:40 — 중간 결과와 마지막 추가 (queue29)
- 빠른 3영역 → 메일 서버(mixF) ×3: 47번 2.042, 46번 2.367, 31번 2.468 (v4 2회 평균 2.352, 견고 2.454). 47번은 빠른 3영역과 메일 서버 모두에서 1등이라 이 믹스에서 v4보다 15% 좋다. v4의 "견고 CAT 대비 승리"는 견고 CAT이 메일 서버에 약해서이며, 최적 조합 대비로는 짐.
- queue29(queue28 뒤): 거래 DB 흉내 → 메일 서버 v4 3회차(seed 3). v4가 고정 6개 모두를 이긴 유일한 사례라 반복 확인. 판정: 3회 평균이 47번(1.910)보다 낮으면 유지.

- Finished 2026-09-29T23:04:09+09:00; mixF arm17 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-arm17-rep1-x3`; cleanup attempted.
- total host_bytes=769174917120 host_pages=187786845 gc_pages=282161517 WAF=2.502563
- phaseA(test4) host_pages=72001981 gc_pages=62785662 WAF=1.871999
- phaseB(varmail) host_pages=115784864 gc_pages=219375855 WAF=2.894685
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF fixed37 — started 2026-09-29T23:04:12+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixF fixed37`; evidence `result/mix-20260911/mixF-fixed37/`.

- Finished 2026-09-29T23:50:42+09:00; mixF fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-fixed37-rep1-x3`; cleanup attempted.
- total host_bytes=655316107264 host_pages=159989284 gc_pages=300550069 WAF=2.878564
- phaseA(test4) host_pages=72021429 gc_pages=70266431 WAF=1.975632
- phaseB(varmail) host_pages=87967855 gc_pages=230283638 WAF=3.617816
- ycsb-load 
- ycsb-run 

### mix-20260911 mixJ fixed47 — started 2026-09-29T23:51:06+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixJ fixed47`; evidence `result/mix-20260911/mixJ-fixed47/`.

- Finished 2026-09-30T00:13:24+09:00; mixJ fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-fixed47-rep1-x3`; cleanup attempted.
- total host_bytes=97432252416 host_pages=23787171 gc_pages=9847109 WAF=1.413967
- phaseA(sqlite-a) host_pages=21671177 gc_pages=8887194 WAF=1.410093
- phaseB(sqlite-b) host_pages=2115994 gc_pages=959915 WAF=1.453647
- phaseA-load host_pages=1398349 gc_pages=367626 WAF=1.262900
- phaseA-run host_pages=20272828 gc_pages=8519568 WAF=1.420246
- ycsb-load [OVERALL], Throughput(ops/sec), 23427.433524657376
- ycsb-run [OVERALL], Throughput(ops/sec), 61489.585201506496

### mix-20260911 mixJ arm46 — started 2026-09-30T00:13:28+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm46.ko`.
- Command: `bash script/mix-20260911.sh mixJ arm46`; evidence `result/mix-20260911/mixJ-arm46/`.

- Finished 2026-09-30T00:42:38+09:00; mixJ arm46 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-arm46-rep1-x3`; cleanup attempted.
- total host_bytes=97166807040 host_pages=23722365 gc_pages=12213879 WAF=1.514868
- phaseA(sqlite-a) host_pages=21605826 gc_pages=11144477 WAF=1.515809
- phaseB(sqlite-b) host_pages=2116539 gc_pages=1069402 WAF=1.505260
- phaseA-load host_pages=1398341 gc_pages=456025 WAF=1.326119
- phaseA-run host_pages=20207485 gc_pages=10688452 WAF=1.528935
- ycsb-load [OVERALL], Throughput(ops/sec), 24405.125076266017
- ycsb-run [OVERALL], Throughput(ops/sec), 62708.04701013258

### mix-20260911 mixJ arm31 — started 2026-09-30T00:42:41+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm31.ko`.
- Command: `bash script/mix-20260911.sh mixJ arm31`; evidence `result/mix-20260911/mixJ-arm31/`.

- Finished 2026-09-30T01:12:01+09:00; mixJ arm31 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-arm31-rep1-x3`; cleanup attempted.
- total host_bytes=97172021248 host_pages=23723638 gc_pages=12419332 WAF=1.523500
- phaseA(sqlite-a) host_pages=21621001 gc_pages=11342525 WAF=1.524607
- phaseB(sqlite-b) host_pages=2102637 gc_pages=1076807 WAF=1.512122
- phaseA-load host_pages=1398349 gc_pages=453653 WAF=1.324420
- phaseA-run host_pages=20222652 gc_pages=10888872 WAF=1.538449
- ycsb-load [OVERALL], Throughput(ops/sec), 22845.82873243727
- ycsb-run [OVERALL], Throughput(ops/sec), 61880.54991182021

### mix-20260911 mixJ arm17 — started 2026-09-30T01:12:04+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm17.ko`.
- Command: `bash script/mix-20260911.sh mixJ arm17`; evidence `result/mix-20260911/mixJ-arm17/`.

- Finished 2026-09-30T01:40:30+09:00; mixJ arm17 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-arm17-rep1-x3`; cleanup attempted.
- total host_bytes=96600506368 host_pages=23584108 gc_pages=4905844 WAF=1.208015
- phaseA(sqlite-a) host_pages=21469602 gc_pages=4502448 WAF=1.209713
- phaseB(sqlite-b) host_pages=2114506 gc_pages=403396 WAF=1.190776
- phaseA-load host_pages=1398349 gc_pages=393486 WAF=1.281393
- phaseA-run host_pages=20071253 gc_pages=4108962 WAF=1.204719
- ycsb-load [OVERALL], Throughput(ops/sec), 22457.61125874911
- ycsb-run [OVERALL], Throughput(ops/sec), 62539.086929330835

### mix-20260911 mixJ fixed37 — started 2026-09-30T01:40:37+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixJ fixed37`; evidence `result/mix-20260911/mixJ-fixed37/`.

- Finished 2026-09-30T02:02:55+09:00; mixJ fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-fixed37-rep1-x3`; cleanup attempted.
- total host_bytes=97476857856 host_pages=23798061 gc_pages=11183404 WAF=1.469929
- phaseA(sqlite-a) host_pages=21698765 gc_pages=10237522 WAF=1.471802
- phaseB(sqlite-b) host_pages=2099296 gc_pages=945882 WAF=1.450571
- phaseA-load host_pages=1398352 gc_pages=608836 WAF=1.435395
- phaseA-run host_pages=20300413 gc_pages=9628686 WAF=1.474310
- ycsb-load [OVERALL], Throughput(ops/sec), 23954.008304056213
- ycsb-run [OVERALL], Throughput(ops/sec), 63554.60929803934

### mix-20260911 mixP fixed47 — started 2026-09-30T02:03:12+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixP fixed47`; evidence `result/mix-20260911/mixP-fixed47/`.

- Finished 2026-09-30T02:23:55+09:00; mixP fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-fixed47-rep1-x3`; cleanup attempted.
- total host_bytes=107846688768 host_pages=26329758 gc_pages=3573871 WAF=1.135735
- phaseA(sqlite-a) host_pages=1247573 gc_pages=221857 WAF=1.177831
- phaseB(oltp) host_pages=25082185 gc_pages=3352014 WAF=1.133641
- phaseA-load host_pages=454360 gc_pages=123623 WAF=1.272082
- phaseA-run host_pages=793213 gc_pages=98234 WAF=1.123843
- ycsb-load [OVERALL], Throughput(ops/sec), 24473.813020068526
- ycsb-run [OVERALL], Throughput(ops/sec), 52200.46719418139

### mix-20260911 mixP arm46 — started 2026-09-30T02:24:05+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm46.ko`.
- Command: `bash script/mix-20260911.sh mixP arm46`; evidence `result/mix-20260911/mixP-arm46/`.

- Finished 2026-09-30T02:25:32+09:00; mixP arm46 exit=1; evidence `/home/oy/iCAT/result/mix-20260911/mixP-arm46-rep1-x3`; cleanup attempted.

### mix-20260911 mixP arm31 — started 2026-09-30T02:25:35+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm31.ko`.
- Command: `bash script/mix-20260911.sh mixP arm31`; evidence `result/mix-20260911/mixP-arm31/`.

- Finished 2026-09-30T02:45:54+09:00; mixP arm31 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-arm31-rep1-x3`; cleanup attempted.
- total host_bytes=105550934016 host_pages=25769271 gc_pages=4891537 WAF=1.189821
- phaseA(sqlite-a) host_pages=1152073 gc_pages=237234 WAF=1.205919
- phaseB(oltp) host_pages=24617198 gc_pages=4654303 WAF=1.189067
- phaseA-load host_pages=455376 gc_pages=148978 WAF=1.327154
- phaseA-run host_pages=696697 gc_pages=88256 WAF=1.126678
- ycsb-load [OVERALL], Throughput(ops/sec), 28597.574925646306
- ycsb-run [OVERALL], Throughput(ops/sec), 59676.84985801883

### mix-20260911 mixP arm17 — started 2026-09-30T02:46:00+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm17.ko`.
- Command: `bash script/mix-20260911.sh mixP arm17`; evidence `result/mix-20260911/mixP-arm17/`.

- Finished 2026-09-30T03:06:24+09:00; mixP arm17 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-arm17-rep1-x3`; cleanup attempted.
- total host_bytes=108902117376 host_pages=26587431 gc_pages=3264508 WAF=1.122784
- phaseA(sqlite-a) host_pages=1146203 gc_pages=212214 WAF=1.185145
- phaseB(oltp) host_pages=25441228 gc_pages=3052294 WAF=1.119974
- phaseA-load host_pages=452310 gc_pages=124993 WAF=1.276344
- phaseA-run host_pages=693893 gc_pages=87221 WAF=1.125698
- ycsb-load [OVERALL], Throughput(ops/sec), 23921.155870251652
- ycsb-run [OVERALL], Throughput(ops/sec), 56936.259857089986

### mix-20260911 mixP fixed37 — started 2026-09-30T03:06:32+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixP fixed37`; evidence `result/mix-20260911/mixP-fixed37/`.

- Finished 2026-09-30T03:08:01+09:00; mixP fixed37 exit=1; evidence `/home/oy/iCAT/result/mix-20260911/mixP-fixed37-rep1-x3`; cleanup attempted.

### mix-20260911 t4 arm31 — started 2026-09-30T03:10:23+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm31.ko`.
- Command: `bash script/mix-20260911.sh t4 arm31`; evidence `result/mix-20260911/t4-arm31/`.

- Finished 2026-09-30T03:21:49+09:00; t4 arm31 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-arm31-rep1`; cleanup attempted.
- total host_bytes=98306707456 host_pages=24000661 gc_pages=19116795 WAF=1.796511
- phaseA(test4) host_pages=24000661 gc_pages=19116795 WAF=1.796511
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 arm46 — started 2026-09-30T03:21:52+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm46.ko`.
- Command: `bash script/mix-20260911.sh t4 arm46`; evidence `result/mix-20260911/t4-arm46/`.

- Finished 2026-09-30T03:33:19+09:00; t4 arm46 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-arm46-rep1`; cleanup attempted.
- total host_bytes=98310901760 host_pages=24001685 gc_pages=18833396 WAF=1.784670
- phaseA(test4) host_pages=24001685 gc_pages=18833396 WAF=1.784670
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 arm32 — started 2026-09-30T03:33:22+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm32.ko`.
- Command: `bash script/mix-20260911.sh t4 arm32`; evidence `result/mix-20260911/t4-arm32/`.

- Finished 2026-09-30T03:44:48+09:00; t4 arm32 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-arm32-rep1`; cleanup attempted.
- total host_bytes=98306695168 host_pages=24000658 gc_pages=19092515 WAF=1.795500
- phaseA(test4) host_pages=24000658 gc_pages=19092515 WAF=1.795500
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 arm34 — started 2026-09-30T03:44:52+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm34.ko`.
- Command: `bash script/mix-20260911.sh t4 arm34`; evidence `result/mix-20260911/t4-arm34/`.

- Finished 2026-09-30T03:56:17+09:00; t4 arm34 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-arm34-rep1`; cleanup attempted.
- total host_bytes=98306695168 host_pages=24000658 gc_pages=20476013 WAF=1.853144
- phaseA(test4) host_pages=24000658 gc_pages=20476013 WAF=1.853144
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 arm16 — started 2026-09-30T03:56:21+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm16.ko`.
- Command: `bash script/mix-20260911.sh t4 arm16`; evidence `result/mix-20260911/t4-arm16/`.

- Finished 2026-09-30T04:07:47+09:00; t4 arm16 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-arm16-rep1`; cleanup attempted.
- total host_bytes=98306695168 host_pages=24000658 gc_pages=20001612 WAF=1.833378
- phaseA(test4) host_pages=24000658 gc_pages=20001612 WAF=1.833378
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 arm45 — started 2026-09-30T04:07:51+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm45.ko`.
- Command: `bash script/mix-20260911.sh t4 arm45`; evidence `result/mix-20260911/t4-arm45/`.

- Finished 2026-09-30T04:19:17+09:00; t4 arm45 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-arm45-rep1`; cleanup attempted.
- total host_bytes=98407395328 host_pages=24025243 gc_pages=19540330 WAF=1.813325
- phaseA(test4) host_pages=24025243 gc_pages=19540330 WAF=1.813325
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 arm49 — started 2026-09-30T04:19:21+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm49.ko`.
- Command: `bash script/mix-20260911.sh t4 arm49`; evidence `result/mix-20260911/t4-arm49/`.

- Finished 2026-09-30T04:30:47+09:00; t4 arm49 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-arm49-rep1`; cleanup attempted.
- total host_bytes=98407395328 host_pages=24025243 gc_pages=19695939 WAF=1.819802
- phaseA(test4) host_pages=24025243 gc_pages=19695939 WAF=1.819802
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 arm30 — started 2026-09-30T04:30:52+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm30.ko`.
- Command: `bash script/mix-20260911.sh t4 arm30`; evidence `result/mix-20260911/t4-arm30/`.

- Finished 2026-09-30T04:42:20+09:00; t4 arm30 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-arm30-rep1`; cleanup attempted.
- total host_bytes=98306781184 host_pages=24000679 gc_pages=20074248 WAF=1.836403
- phaseA(test4) host_pages=24000679 gc_pages=20074248 WAF=1.836403
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 arm35 — started 2026-09-30T04:42:24+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm35.ko`.
- Command: `bash script/mix-20260911.sh t4 arm35`; evidence `result/mix-20260911/t4-arm35/`.

- Finished 2026-09-30T04:53:50+09:00; t4 arm35 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-arm35-rep1`; cleanup attempted.
- total host_bytes=98386415616 host_pages=24020121 gc_pages=20251247 WAF=1.843095
- phaseA(test4) host_pages=24020121 gc_pages=20251247 WAF=1.843095
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 arm17 — started 2026-09-30T04:53:53+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm17.ko`.
- Command: `bash script/mix-20260911.sh t4 arm17`; evidence `result/mix-20260911/t4-arm17/`.

- Finished 2026-09-30T05:05:20+09:00; t4 arm17 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-arm17-rep1`; cleanup attempted.
- total host_bytes=98306695168 host_pages=24000658 gc_pages=20941797 WAF=1.872551
- phaseA(test4) host_pages=24000658 gc_pages=20941797 WAF=1.872551
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 arm15 — started 2026-09-30T05:05:23+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm15.ko`.
- Command: `bash script/mix-20260911.sh t4 arm15`; evidence `result/mix-20260911/t4-arm15/`.

- Finished 2026-09-30T05:16:50+09:00; t4 arm15 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-arm15-rep1`; cleanup attempted.
- total host_bytes=98306695168 host_pages=24000658 gc_pages=21052975 WAF=1.877183
- phaseA(test4) host_pages=24000658 gc_pages=21052975 WAF=1.877183
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 arm33 — started 2026-09-30T05:16:54+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm33.ko`.
- Command: `bash script/mix-20260911.sh t4 arm33`; evidence `result/mix-20260911/t4-arm33/`.

- Finished 2026-09-30T05:28:20+09:00; t4 arm33 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-arm33-rep1`; cleanup attempted.
- total host_bytes=98306732032 host_pages=24000667 gc_pages=21961797 WAF=1.915049
- phaseA(test4) host_pages=24000667 gc_pages=21961797 WAF=1.915049
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 greedy — started 2026-09-30T05:28:24+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-greedy-m.ko`.
- Command: `bash script/mix-20260911.sh t4 greedy`; evidence `result/mix-20260911/t4-greedy/`.

- Finished 2026-09-30T05:39:50+09:00; t4 greedy exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-greedy-rep1`; cleanup attempted.
- total host_bytes=98375864320 host_pages=24017545 gc_pages=29904930 WAF=2.245129
- phaseA(test4) host_pages=24017545 gc_pages=29904930 WAF=2.245129
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 t4 fixed37 — started 2026-09-30T05:39:54+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh t4 fixed37`; evidence `result/mix-20260911/t4-fixed37/`.

- Finished 2026-09-30T05:51:20+09:00; t4 fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/t4-fixed37-rep1`; cleanup attempted.
- total host_bytes=98306695168 host_pages=24000658 gc_pages=23370844 WAF=1.973758
- phaseA(test4) host_pages=24000658 gc_pages=23370844 WAF=1.973758
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO onlinev4 — started 2026-09-30T05:52:55+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-online-v4.ko`.
- Command: `bash script/mix-20260911.sh mixO onlinev4`; evidence `result/mix-20260911/mixO-onlinev4/`.

- Finished 2026-09-30T06:24:49+09:00; mixO onlinev4 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-onlinev4-rep3-x3`; cleanup attempted.
- total host_bytes=705805303808 host_pages=172315748 gc_pages=150870481 WAF=1.875547
- phaseA(oltp) host_pages=25013695 gc_pages=6854807 WAF=1.274042
- phaseB(varmail) host_pages=147302053 gc_pages=144015674 WAF=1.977690
- ycsb-load 
- ycsb-run 

## 2026-09-30 — 사고 2회째: 메모리의 라이브러리 사본 손상

- mixP(SQLite → 거래 DB 흉내) ×3 arm46(02:25)·기본 37번(03:08)이 시작 직후 실패. arm46은 `Inconsistency detected by ld.so: ... elf_machine_rela_relative: Assertion ... failed`, 37번은 SQLite 준비 단계에서 종료(로그 4바이트). 9/29 새벽 fio 사고와 같은 유형(메모리에 캐시된 실행 파일·라이브러리 손상)으로 판단.
- 공통점: 두 번 모두 Filebench가 들어간 실행(메일 서버 sweep, SQLite → 거래 DB 흉내) 도중·직후. 커널 로그에 하드웨어 메모리 오류(MCE/EDAC) 기록은 없음.
- 원인 후보: (1) NVMeVirt의 데이터 복사가 예약 영역 밖 메모리를 건드림, (2) 램 불량. 미확정. **실험이 끝난 뒤 램 검사(memtest86+) 필요.**
- 결과 영향 판단: 손상은 프로그램 시작 실패로 드러났고, 정상 종료한 실행의 WAF는 FTL 카운터로 계산하며 호스트 바이트 수가 블록 계층 통계와 일치하는지 매 실행 검사한다(`mix-20260911.sh` stop 단계). 정상 종료한 실행은 유효로 본다. 다만 이것이 모든 가능성을 배제하지는 않는다(한계에 기록).
- 조치: 실패 2건 `*-libbroken`으로 보존, queue30에서 재실행(시작 전 page cache 비우기 + fio·sqlite3·java 실행 확인).

### mix-20260911 mixP arm46 — started 2026-09-30T09:50:10+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm46.ko`.
- Command: `bash script/mix-20260911.sh mixP arm46`; evidence `result/mix-20260911/mixP-arm46/`.

### 결과 2026-09-30 — 빠른 3영역 순위를 같은 방식(명시 계측)으로 다시 매김 (queue28)

- 명시 계측 10분: 47번 1.774, 46번 1.785, 32번 1.796, 31번 1.797, 견고 50번 1.812(1시간 값), 45번 1.813, 49번 1.820, 16번 1.833, 30번 1.836, 35번 1.843, 34번 1.853, 17번 1.873, 15번 1.877, 33번 1.915, 기본 37번 1.974, Greedy 2.245.
- 학습기 순위(61자리 중): **v4 10시간 1.807 → 5등**(위: 47, 46, 32, 31), v4 3시간 → 8등, v3 3시간 → 11등, v1 3시간·v2 3시간 → 14등, v4 1시간 → 12등. (재측정하지 않은 조합은 원저자 방식에서 모두 1.846 이상이라 명시 계측으로는 약 1.87 이상으로 추정 → 위 순위에 영향 없음. 단 v1 1시간 1.964의 15등은 재측정 안 한 조합 일부보다 나쁠 수 있어 하한.)
- 방식이 섞였던 잠정 순위(v4 10시간 10등, v3 3시간 14등)는 폐기.
- v4 3회차(거래 DB 흉내 → 메일 서버, queue29): 3회 평균 1.859, 여전히 고정 6개 중 최고(47번 1.910)보다 2.7% 좋음.

- Finished 2026-09-30T10:10:46+09:00; mixP arm46 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-arm46-rep1-x3`; cleanup attempted.
- total host_bytes=106552057856 host_pages=26013686 gc_pages=4529579 WAF=1.174123
- phaseA(sqlite-a) host_pages=1143569 gc_pages=232384 WAF=1.203209
- phaseB(oltp) host_pages=24870117 gc_pages=4297195 WAF=1.172785
- phaseA-load host_pages=452312 gc_pages=142186 WAF=1.314354
- phaseA-run host_pages=691257 gc_pages=90198 WAF=1.130484
- ycsb-load [OVERALL], Throughput(ops/sec), 27382.25629791895
- ycsb-run [OVERALL], Throughput(ops/sec), 55817.588122017245

### mix-20260911 mixP fixed37 — started 2026-09-30T10:10:56+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixP fixed37`; evidence `result/mix-20260911/mixP-fixed37/`.

- Finished 2026-09-30T10:31:28+09:00; mixP fixed37 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-fixed37-rep1-x3`; cleanup attempted.
- total host_bytes=106023792640 host_pages=25884715 gc_pages=4597482 WAF=1.177614
- phaseA(sqlite-a) host_pages=1152638 gc_pages=306101 WAF=1.265566
- phaseB(oltp) host_pages=24732077 gc_pages=4291381 WAF=1.173515
- phaseA-load host_pages=454869 gc_pages=215008 WAF=1.472681
- phaseA-run host_pages=697769 gc_pages=91093 WAF=1.130549
- ycsb-load [OVERALL], Throughput(ops/sec), 31075.20198881293
- ycsb-run [OVERALL], Throughput(ops/sec), 56186.614475544775

## 사전 등록 2026-09-30 — 전환 워크로드의 진짜 상위·견고 고정 조합 찾기 (queue31, "짧게 거르고 길게 확인")

- 사용자 지적: 견고 50번은 원저자 워크로드에서 견고한 것이지 전환 워크로드에서도 견고한지 모른다. 60개 전부를 3배 길이로 재면 약 24일(1대) → 사용자 제안에 따라 짧게 걸러 낸 뒤 상위만 길게 확인.
- 근거: 고정 조합의 WAF 값은 1배와 3배에서 달라지지만(메일 서버 믹스 47번 −14%) 조합 간 순서는 대부분 유지(측정 4종 중 3종 동일, 1종은 0.4% 차이로 뒤바뀜).
- 1단계(1배 길이): 11종(mixO, F, J, P, B, D, K, H, G, L, Q) × 후보 13개(46, 31, 32, 17, 16, 15, 30, 34, 35, 45, 49, 53, 56). 47·50·37번은 기존 1배 3회 결과 사용. mixA·mixC는 60개 1배 결과가 이미 있음. 약 45시간.
- 2단계(3배 길이): 믹스마다 1배 기준 상위 3개를 3배로(이미 있으면 건너뜀). 약 10~15시간.
- 안전장치: 매 실행 전후 page cache 비우기 + fio·sqlite3·java 실행 확인. 실행 직후 도구가 망가져 있으면 그 실행 폴더에 `SUSPECT.txt`를 남기고 상위 선정에서 제외.
- 판정: 13종 × (고정 후보 16개 + v4) 표에서 각 믹스의 1등 고정 조합, 13종 전체의 평균·최악 손해가 가장 작은 고정 조합(새 "견고"), 그 대비 v4의 평균·최악 손해.
- 예상 종료: 10/2 저녁.

### mix-20260911 mixO arm46 — started 2026-09-30T10:35:36+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm46.ko`.
- Command: `bash script/mix-20260911.sh mixO arm46`; evidence `result/mix-20260911/mixO-arm46/`.

- Finished 2026-09-30T10:47:09+09:00; mixO arm46 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-arm46-rep1`; cleanup attempted.
- total host_bytes=237061730304 host_pages=57876399 gc_pages=68281905 WAF=2.179788
- phaseA(oltp) host_pages=8752907 gc_pages=3065387 WAF=1.350214
- phaseB(varmail) host_pages=49123492 gc_pages=65216518 WAF=2.327603
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO arm31 — started 2026-09-30T10:47:14+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm31.ko`.
- Command: `bash script/mix-20260911.sh mixO arm31`; evidence `result/mix-20260911/mixO-arm31/`.

- Finished 2026-09-30T10:58:46+09:00; mixO arm31 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-arm31-rep1`; cleanup attempted.
- total host_bytes=240349822976 host_pages=58679156 gc_pages=69191921 WAF=2.179157
- phaseA(oltp) host_pages=8983398 gc_pages=3037633 WAF=1.338139
- phaseB(varmail) host_pages=49695758 gc_pages=66154288 WAF=2.331186
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO arm32 — started 2026-09-30T10:58:51+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm32.ko`.
- Command: `bash script/mix-20260911.sh mixO arm32`; evidence `result/mix-20260911/mixO-arm32/`.

- Finished 2026-09-30T11:10:25+09:00; mixO arm32 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-arm32-rep1`; cleanup attempted.
- total host_bytes=254315831296 host_pages=62088826 gc_pages=61187830 WAF=1.985489
- phaseA(oltp) host_pages=8825219 gc_pages=2859937 WAF=1.324064
- phaseB(varmail) host_pages=53263607 gc_pages=58327893 WAF=2.095080
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO arm17 — started 2026-09-30T11:10:30+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm17.ko`.
- Command: `bash script/mix-20260911.sh mixO arm17`; evidence `result/mix-20260911/mixO-arm17/`.

- Finished 2026-09-30T11:22:03+09:00; mixO arm17 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-arm17-rep1`; cleanup attempted.
- total host_bytes=257957294080 host_pages=62977855 gc_pages=58515989 WAF=1.929152
- phaseA(oltp) host_pages=9156281 gc_pages=2687083 WAF=1.293469
- phaseB(varmail) host_pages=53821574 gc_pages=55828906 WAF=2.037296
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO arm16 — started 2026-09-30T11:22:07+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm16.ko`.
- Command: `bash script/mix-20260911.sh mixO arm16`; evidence `result/mix-20260911/mixO-arm16/`.

- Finished 2026-09-30T11:33:40+09:00; mixO arm16 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-arm16-rep1`; cleanup attempted.
- total host_bytes=243462565888 host_pages=59439103 gc_pages=57134115 WAF=1.961221
- phaseA(oltp) host_pages=8847018 gc_pages=2957425 WAF=1.334285
- phaseB(varmail) host_pages=50592085 gc_pages=54176690 WAF=2.070853
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO arm15 — started 2026-09-30T11:33:47+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm15.ko`.
- Command: `bash script/mix-20260911.sh mixO arm15`; evidence `result/mix-20260911/mixO-arm15/`.

- Finished 2026-09-30T11:45:21+09:00; mixO arm15 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-arm15-rep1`; cleanup attempted.
- total host_bytes=229380288512 host_pages=56001047 gc_pages=74451948 WAF=2.329474
- phaseA(oltp) host_pages=8998873 gc_pages=3527598 WAF=1.392004
- phaseB(varmail) host_pages=47002174 gc_pages=70924350 WAF=2.508959
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO arm30 — started 2026-09-30T11:45:25+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm30.ko`.
- Command: `bash script/mix-20260911.sh mixO arm30`; evidence `result/mix-20260911/mixO-arm30/`.

- Finished 2026-09-30T11:56:58+09:00; mixO arm30 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-arm30-rep1`; cleanup attempted.
- total host_bytes=227505836032 host_pages=55543417 gc_pages=72671765 WAF=2.308378
- phaseA(oltp) host_pages=8725164 gc_pages=3514280 WAF=1.402775
- phaseB(varmail) host_pages=46818253 gc_pages=69157485 WAF=2.477148
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO arm34 — started 2026-09-30T11:57:03+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm34.ko`.
- Command: `bash script/mix-20260911.sh mixO arm34`; evidence `result/mix-20260911/mixO-arm34/`.

- Finished 2026-09-30T12:08:35+09:00; mixO arm34 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-arm34-rep1`; cleanup attempted.
- total host_bytes=235653148672 host_pages=57532507 gc_pages=72132812 WAF=2.253775
- phaseA(oltp) host_pages=9020010 gc_pages=3341167 WAF=1.370417
- phaseB(varmail) host_pages=48512497 gc_pages=68791645 WAF=2.418019
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO arm35 — started 2026-09-30T12:08:40+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm35.ko`.
- Command: `bash script/mix-20260911.sh mixO arm35`; evidence `result/mix-20260911/mixO-arm35/`.

- Finished 2026-09-30T12:20:14+09:00; mixO arm35 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-arm35-rep1`; cleanup attempted.
- total host_bytes=252680290304 host_pages=61689524 gc_pages=62633245 WAF=2.015298
- phaseA(oltp) host_pages=8965803 gc_pages=2785304 WAF=1.310659
- phaseB(varmail) host_pages=52723721 gc_pages=59847941 WAF=2.135124
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO arm45 — started 2026-09-30T12:20:18+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm45.ko`.
- Command: `bash script/mix-20260911.sh mixO arm45`; evidence `result/mix-20260911/mixO-arm45/`.

- Finished 2026-09-30T12:31:51+09:00; mixO arm45 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-arm45-rep1`; cleanup attempted.
- total host_bytes=225750532096 host_pages=55114876 gc_pages=72496014 WAF=2.315362
- phaseA(oltp) host_pages=9031078 gc_pages=3729749 WAF=1.412990
- phaseB(varmail) host_pages=46083798 gc_pages=68766265 WAF=2.492200
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO arm49 — started 2026-09-30T12:31:56+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm49.ko`.
- Command: `bash script/mix-20260911.sh mixO arm49`; evidence `result/mix-20260911/mixO-arm49/`.

- Finished 2026-09-30T12:43:29+09:00; mixO arm49 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-arm49-rep1`; cleanup attempted.
- total host_bytes=239496400896 host_pages=58470801 gc_pages=71002158 WAF=2.214318
- phaseA(oltp) host_pages=9317667 gc_pages=3410048 WAF=1.365977
- phaseB(varmail) host_pages=49153134 gc_pages=67592110 WAF=2.375133
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO arm53 — started 2026-09-30T12:43:34+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm53.ko`.
- Command: `bash script/mix-20260911.sh mixO arm53`; evidence `result/mix-20260911/mixO-arm53/`.

- Finished 2026-09-30T12:55:06+09:00; mixO arm53 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-arm53-rep1`; cleanup attempted.
- total host_bytes=240814157824 host_pages=58792519 gc_pages=71698166 WAF=2.219512
- phaseA(oltp) host_pages=8840242 gc_pages=3075636 WAF=1.347913
- phaseB(varmail) host_pages=49952277 gc_pages=68622530 WAF=2.373762
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO arm56 — started 2026-09-30T12:55:11+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm56.ko`.
- Command: `bash script/mix-20260911.sh mixO arm56`; evidence `result/mix-20260911/mixO-arm56/`.

- Finished 2026-09-30T13:06:43+09:00; mixO arm56 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-arm56-rep1`; cleanup attempted.
- total host_bytes=244947136512 host_pages=59801547 gc_pages=59733895 WAF=1.998869
- phaseA(oltp) host_pages=8853975 gc_pages=3429367 WAF=1.387325
- phaseB(varmail) host_pages=50947572 gc_pages=56304528 WAF=2.105146
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF arm46 — started 2026-09-30T13:06:57+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm46.ko`.
- Command: `bash script/mix-20260911.sh mixF arm46`; evidence `result/mix-20260911/mixF-arm46/`.

- Finished 2026-09-30T13:23:25+09:00; mixF arm46 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-arm46-rep1`; cleanup attempted.
- total host_bytes=241309024256 host_pages=58913336 gc_pages=90345056 WAF=2.533525
- phaseA(test4) host_pages=24027296 gc_pages=18329785 WAF=1.762873
- phaseB(varmail) host_pages=34886040 gc_pages=72015271 WAF=3.064301
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF arm31 — started 2026-09-30T13:23:29+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm31.ko`.
- Command: `bash script/mix-20260911.sh mixF arm31`; evidence `result/mix-20260911/mixF-arm31/`.

- Finished 2026-09-30T13:39:58+09:00; mixF arm31 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-arm31-rep1`; cleanup attempted.
- total host_bytes=239949852672 host_pages=58581507 gc_pages=94829480 WAF=2.618761
- phaseA(test4) host_pages=24000658 gc_pages=19125732 WAF=1.796884
- phaseB(varmail) host_pages=34580849 gc_pages=75703748 WAF=3.189181
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF arm32 — started 2026-09-30T13:40:05+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm32.ko`.
- Command: `bash script/mix-20260911.sh mixF arm32`; evidence `result/mix-20260911/mixF-arm32/`.

- Finished 2026-09-30T13:56:33+09:00; mixF arm32 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-arm32-rep1`; cleanup attempted.
- total host_bytes=266501861376 host_pages=65063931 gc_pages=94922475 WAF=2.458911
- phaseA(test4) host_pages=24000658 gc_pages=19079151 WAF=1.794943
- phaseB(varmail) host_pages=41063273 gc_pages=75843324 WAF=2.846987
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF arm17 — started 2026-09-30T13:56:38+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm17.ko`.
- Command: `bash script/mix-20260911.sh mixF arm17`; evidence `result/mix-20260911/mixF-arm17/`.

- Finished 2026-09-30T14:13:07+09:00; mixF arm17 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-arm17-rep1`; cleanup attempted.
- total host_bytes=253153210368 host_pages=61804983 gc_pages=99705370 WAF=2.613225
- phaseA(test4) host_pages=24025763 gc_pages=20328341 WAF=1.846106
- phaseB(varmail) host_pages=37779220 gc_pages=79377029 WAF=3.101076
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF arm16 — started 2026-09-30T14:13:12+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm16.ko`.
- Command: `bash script/mix-20260911.sh mixF arm16`; evidence `result/mix-20260911/mixF-arm16/`.

- Finished 2026-09-30T14:29:41+09:00; mixF arm16 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-arm16-rep1`; cleanup attempted.
- total host_bytes=235797553152 host_pages=57567762 gc_pages=102362735 WAF=2.778126
- phaseA(test4) host_pages=24000658 gc_pages=19995742 WAF=1.833133
- phaseB(varmail) host_pages=33567104 gc_pages=82366993 WAF=3.453801
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF arm15 — started 2026-09-30T14:29:45+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm15.ko`.
- Command: `bash script/mix-20260911.sh mixF arm15`; evidence `result/mix-20260911/mixF-arm15/`.

- Finished 2026-09-30T14:46:14+09:00; mixF arm15 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-arm15-rep1`; cleanup attempted.
- total host_bytes=224115933184 host_pages=54715804 gc_pages=105521425 WAF=2.928536
- phaseA(test4) host_pages=24000658 gc_pages=21017690 WAF=1.875713
- phaseB(varmail) host_pages=30715146 gc_pages=84503735 WAF=3.751207
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF arm30 — started 2026-09-30T14:46:19+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm30.ko`.
- Command: `bash script/mix-20260911.sh mixF arm30`; evidence `result/mix-20260911/mixF-arm30/`.

- Finished 2026-09-30T15:02:47+09:00; mixF arm30 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-arm30-rep1`; cleanup attempted.
- total host_bytes=225093783552 host_pages=54954537 gc_pages=95359897 WAF=2.735251
- phaseA(test4) host_pages=24023200 gc_pages=19366937 WAF=1.806176
- phaseB(varmail) host_pages=30931337 gc_pages=75992960 WAF=3.456828
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF arm34 — started 2026-09-30T15:02:52+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm34.ko`.
- Command: `bash script/mix-20260911.sh mixF arm34`; evidence `result/mix-20260911/mixF-arm34/`.

- Finished 2026-09-30T15:19:20+09:00; mixF arm34 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-arm34-rep1`; cleanup attempted.
- total host_bytes=229857579008 host_pages=56117573 gc_pages=102659290 WAF=2.829361
- phaseA(test4) host_pages=24000658 gc_pages=20444887 WAF=1.851847
- phaseB(varmail) host_pages=32116915 gc_pages=82214403 WAF=3.559847
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF arm35 — started 2026-09-30T15:19:25+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm35.ko`.
- Command: `bash script/mix-20260911.sh mixF arm35`; evidence `result/mix-20260911/mixF-arm35/`.

- Finished 2026-09-30T15:35:54+09:00; mixF arm35 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-arm35-rep1`; cleanup attempted.
- total host_bytes=241690595328 host_pages=59006493 gc_pages=100525182 WAF=2.703629
- phaseA(test4) host_pages=24000664 gc_pages=20324649 WAF=1.846837
- phaseB(varmail) host_pages=35005829 gc_pages=80200533 WAF=3.291062
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF arm45 — started 2026-09-30T15:35:58+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm45.ko`.
- Command: `bash script/mix-20260911.sh mixF arm45`; evidence `result/mix-20260911/mixF-arm45/`.

- Finished 2026-09-30T15:52:27+09:00; mixF arm45 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-arm45-rep1`; cleanup attempted.
- total host_bytes=226004418560 host_pages=55176860 gc_pages=92720497 WAF=2.680424
- phaseA(test4) host_pages=24000658 gc_pages=19798037 WAF=1.824896
- phaseB(varmail) host_pages=31176202 gc_pages=72922460 WAF=3.339042
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF arm49 — started 2026-09-30T15:52:32+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm49.ko`.
- Command: `bash script/mix-20260911.sh mixF arm49`; evidence `result/mix-20260911/mixF-arm49/`.

- Finished 2026-09-30T16:09:00+09:00; mixF arm49 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-arm49-rep1`; cleanup attempted.
- total host_bytes=222412804096 host_pages=54300001 gc_pages=94301992 WAF=2.736685
- phaseA(test4) host_pages=24000658 gc_pages=19971016 WAF=1.832103
- phaseB(varmail) host_pages=30299343 gc_pages=74330976 WAF=3.453221
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF arm53 — started 2026-09-30T16:09:05+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm53.ko`.
- Command: `bash script/mix-20260911.sh mixF arm53`; evidence `result/mix-20260911/mixF-arm53/`.

- Finished 2026-09-30T16:25:34+09:00; mixF arm53 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-arm53-rep1`; cleanup attempted.
- total host_bytes=226192105472 host_pages=55222682 gc_pages=103930935 WAF=2.882033
- phaseA(test4) host_pages=24009866 gc_pages=21253907 WAF=1.885216
- phaseB(varmail) host_pages=31212816 gc_pages=82677028 WAF=3.648817
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF arm56 — started 2026-09-30T16:25:39+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm56.ko`.
- Command: `bash script/mix-20260911.sh mixF arm56`; evidence `result/mix-20260911/mixF-arm56/`.

- Finished 2026-09-30T16:42:07+09:00; mixF arm56 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-arm56-rep1`; cleanup attempted.
- total host_bytes=210817597440 host_pages=51469140 gc_pages=112255228 WAF=3.181020
- phaseA(test4) host_pages=24023702 gc_pages=24348444 WAF=2.013518
- phaseB(varmail) host_pages=27445438 gc_pages=87906784 WAF=4.202965
- ycsb-load 
- ycsb-run 

### mix-20260911 mixJ arm46 — started 2026-09-30T16:42:21+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm46.ko`.
- Command: `bash script/mix-20260911.sh mixJ arm46`; evidence `result/mix-20260911/mixJ-arm46/`.

- Finished 2026-09-30T16:53:49+09:00; mixJ arm46 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-arm46-rep1`; cleanup attempted.
- total host_bytes=35599581184 host_pages=8691304 gc_pages=4401516 WAF=1.506428
- phaseA(sqlite-a) host_pages=8059346 gc_pages=4095661 WAF=1.508188
- phaseB(sqlite-b) host_pages=631958 gc_pages=305855 WAF=1.483980
- phaseA-load host_pages=1398349 gc_pages=454861 WAF=1.325284
- phaseA-run host_pages=6660997 gc_pages=3640800 WAF=1.546585
- ycsb-load [OVERALL], Throughput(ops/sec), 23127.625949196314
- ycsb-run [OVERALL], Throughput(ops/sec), 43911.64976068151

### mix-20260911 mixJ arm31 — started 2026-09-30T16:53:58+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm31.ko`.
- Command: `bash script/mix-20260911.sh mixJ arm31`; evidence `result/mix-20260911/mixJ-arm31/`.

- Finished 2026-09-30T17:03:01+09:00; mixJ arm31 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-arm31-rep1`; cleanup attempted.
- total host_bytes=35768098816 host_pages=8732446 gc_pages=3808648 WAF=1.436149
- phaseA(sqlite-a) host_pages=8093474 gc_pages=3499716 WAF=1.432412
- phaseB(sqlite-b) host_pages=638972 gc_pages=308932 WAF=1.483483
- phaseA-load host_pages=1398339 gc_pages=462567 WAF=1.330797
- phaseA-run host_pages=6695135 gc_pages=3037149 WAF=1.453635
- ycsb-load [OVERALL], Throughput(ops/sec), 24700.506360380386
- ycsb-run [OVERALL], Throughput(ops/sec), 45057.730216840326

### mix-20260911 mixJ arm32 — started 2026-09-30T17:03:09+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm32.ko`.
- Command: `bash script/mix-20260911.sh mixJ arm32`; evidence `result/mix-20260911/mixJ-arm32/`.

- Finished 2026-09-30T17:12:24+09:00; mixJ arm32 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-arm32-rep1`; cleanup attempted.
- total host_bytes=35762860032 host_pages=8731167 gc_pages=3715054 WAF=1.425493
- phaseA(sqlite-a) host_pages=8098630 gc_pages=3464026 WAF=1.427730
- phaseB(sqlite-b) host_pages=632537 gc_pages=251028 WAF=1.396859
- phaseA-load host_pages=1398349 gc_pages=372405 WAF=1.266318
- phaseA-run host_pages=6700281 gc_pages=3091621 WAF=1.461417
- ycsb-load [OVERALL], Throughput(ops/sec), 22961.23378362864
- ycsb-run [OVERALL], Throughput(ops/sec), 44655.316773653365

### mix-20260911 mixJ arm17 — started 2026-09-30T17:12:31+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm17.ko`.
- Command: `bash script/mix-20260911.sh mixJ arm17`; evidence `result/mix-20260911/mixJ-arm17/`.

- Finished 2026-09-30T17:23:46+09:00; mixJ arm17 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-arm17-rep1`; cleanup attempted.
- total host_bytes=35513671680 host_pages=8670330 gc_pages=2138277 WAF=1.246620
- phaseA(sqlite-a) host_pages=8031608 gc_pages=2004756 WAF=1.249608
- phaseB(sqlite-b) host_pages=638722 gc_pages=133521 WAF=1.209044
- phaseA-load host_pages=1398351 gc_pages=394047 WAF=1.281794
- phaseA-run host_pages=6633257 gc_pages=1610709 WAF=1.242823
- ycsb-load [OVERALL], Throughput(ops/sec), 22751.403003185198
- ycsb-run [OVERALL], Throughput(ops/sec), 44275.214734791465

### mix-20260911 mixJ arm16 — started 2026-09-30T17:23:54+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm16.ko`.
- Command: `bash script/mix-20260911.sh mixJ arm16`; evidence `result/mix-20260911/mixJ-arm16/`.

- Finished 2026-09-30T17:34:59+09:00; mixJ arm16 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-arm16-rep1`; cleanup attempted.
- total host_bytes=35553828864 host_pages=8680134 gc_pages=3481048 WAF=1.401036
- phaseA(sqlite-a) host_pages=8043699 gc_pages=3227023 WAF=1.401186
- phaseB(sqlite-b) host_pages=636435 gc_pages=254025 WAF=1.399137
- phaseA-load host_pages=1399874 gc_pages=471276 WAF=1.336656
- phaseA-run host_pages=6643825 gc_pages=2755747 WAF=1.414783
- ycsb-load [OVERALL], Throughput(ops/sec), 24683.231857824583
- ycsb-run [OVERALL], Throughput(ops/sec), 44301.20388521558

### mix-20260911 mixJ arm15 — started 2026-09-30T17:35:07+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm15.ko`.
- Command: `bash script/mix-20260911.sh mixJ arm15`; evidence `result/mix-20260911/mixJ-arm15/`.

- Finished 2026-09-30T17:46:29+09:00; mixJ arm15 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-arm15-rep1`; cleanup attempted.
- total host_bytes=35620069376 host_pages=8696306 gc_pages=4672525 WAF=1.537300
- phaseA(sqlite-a) host_pages=8057282 gc_pages=4344772 WAF=1.539235
- phaseB(sqlite-b) host_pages=639024 gc_pages=327753 WAF=1.512896
- phaseA-load host_pages=1398349 gc_pages=587585 WAF=1.420199
- phaseA-run host_pages=6658933 gc_pages=3757187 WAF=1.564233
- ycsb-load [OVERALL], Throughput(ops/sec), 24034.60983816696
- ycsb-run [OVERALL], Throughput(ops/sec), 43352.44453596627

### mix-20260911 mixJ arm30 — started 2026-09-30T17:46:36+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm30.ko`.
- Command: `bash script/mix-20260911.sh mixJ arm30`; evidence `result/mix-20260911/mixJ-arm30/`.

- Finished 2026-09-30T17:57:58+09:00; mixJ arm30 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-arm30-rep1`; cleanup attempted.
- total host_bytes=35624304640 host_pages=8697340 gc_pages=4662014 WAF=1.536028
- phaseA(sqlite-a) host_pages=8062254 gc_pages=4337160 WAF=1.537959
- phaseB(sqlite-b) host_pages=635086 gc_pages=324854 WAF=1.511512
- phaseA-load host_pages=1398339 gc_pages=560250 WAF=1.400654
- phaseA-run host_pages=6663915 gc_pages=3776910 WAF=1.566770
- ycsb-load [OVERALL], Throughput(ops/sec), 24707.62642068852
- ycsb-run [OVERALL], Throughput(ops/sec), 43564.917172201225

### mix-20260911 mixJ arm34 — started 2026-09-30T17:58:06+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm34.ko`.
- Command: `bash script/mix-20260911.sh mixJ arm34`; evidence `result/mix-20260911/mixJ-arm34/`.

- Finished 2026-09-30T18:09:23+09:00; mixJ arm34 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-arm34-rep1`; cleanup attempted.
- total host_bytes=35558834176 host_pages=8681356 gc_pages=3897241 WAF=1.448921
- phaseA(sqlite-a) host_pages=8041143 gc_pages=3637683 WAF=1.452384
- phaseB(sqlite-b) host_pages=640213 gc_pages=259558 WAF=1.405424
- phaseA-load host_pages=1398339 gc_pages=489527 WAF=1.350077
- phaseA-run host_pages=6642804 gc_pages=3148156 WAF=1.473920
- ycsb-load [OVERALL], Throughput(ops/sec), 24934.546814611644
- ycsb-run [OVERALL], Throughput(ops/sec), 43931.905546403075

### mix-20260911 mixJ arm35 — started 2026-09-30T18:09:31+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm35.ko`.
- Command: `bash script/mix-20260911.sh mixJ arm35`; evidence `result/mix-20260911/mixJ-arm35/`.

- Finished 2026-09-30T18:18:48+09:00; mixJ arm35 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-arm35-rep1`; cleanup attempted.
- total host_bytes=35775160320 host_pages=8734170 gc_pages=3199219 WAF=1.366288
- phaseA(sqlite-a) host_pages=8098773 gc_pages=3067322 WAF=1.378739
- phaseB(sqlite-b) host_pages=635397 gc_pages=131897 WAF=1.207582
- phaseA-load host_pages=1398349 gc_pages=392921 WAF=1.280989
- phaseA-run host_pages=6700424 gc_pages=2674401 WAF=1.399139
- ycsb-load [OVERALL], Throughput(ops/sec), 21743.069396629824
- ycsb-run [OVERALL], Throughput(ops/sec), 44182.78417814498

### mix-20260911 mixJ arm45 — started 2026-09-30T18:18:59+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm45.ko`.
- Command: `bash script/mix-20260911.sh mixJ arm45`; evidence `result/mix-20260911/mixJ-arm45/`.

- Finished 2026-09-30T18:28:19+09:00; mixJ arm45 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-arm45-rep1`; cleanup attempted.
- total host_bytes=35844005888 host_pages=8750978 gc_pages=4221116 WAF=1.482359
- phaseA(sqlite-a) host_pages=8110660 gc_pages=3894509 WAF=1.480172
- phaseB(sqlite-b) host_pages=640318 gc_pages=326607 WAF=1.510070
- phaseA-load host_pages=1398351 gc_pages=549817 WAF=1.393190
- phaseA-run host_pages=6712309 gc_pages=3344692 WAF=1.498292
- ycsb-load [OVERALL], Throughput(ops/sec), 21458.459997854156
- ycsb-run [OVERALL], Throughput(ops/sec), 44370.98581237729

### mix-20260911 mixJ arm49 — started 2026-09-30T18:28:27+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm49.ko`.
- Command: `bash script/mix-20260911.sh mixJ arm49`; evidence `result/mix-20260911/mixJ-arm49/`.

- Finished 2026-09-30T18:37:48+09:00; mixJ arm49 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-arm49-rep1`; cleanup attempted.
- total host_bytes=35916591104 host_pages=8768699 gc_pages=3876410 WAF=1.442074
- phaseA(sqlite-a) host_pages=8128295 gc_pages=3566944 WAF=1.438831
- phaseB(sqlite-b) host_pages=640404 gc_pages=309466 WAF=1.483236
- phaseA-load host_pages=1398351 gc_pages=479253 WAF=1.342727
- phaseA-run host_pages=6729944 gc_pages=3087691 WAF=1.458799
- ycsb-load [OVERALL], Throughput(ops/sec), 21571.094733057704
- ycsb-run [OVERALL], Throughput(ops/sec), 43931.905546403075

### mix-20260911 mixJ arm53 — started 2026-09-30T18:37:55+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm53.ko`.
- Command: `bash script/mix-20260911.sh mixJ arm53`; evidence `result/mix-20260911/mixJ-arm53/`.

- Finished 2026-09-30T18:50:24+09:00; mixJ arm53 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-arm53-rep1`; cleanup attempted.
- total host_bytes=36518727680 host_pages=8915705 gc_pages=3511374 WAF=1.393841
- phaseA(sqlite-a) host_pages=8088646 gc_pages=3421657 WAF=1.423020
- phaseB(sqlite-b) host_pages=827059 gc_pages=89717 WAF=1.108477
- phaseA-load host_pages=1398351 gc_pages=413858 WAF=1.295961
- phaseA-run host_pages=6690295 gc_pages=3007799 WAF=1.449576
- ycsb-load [OVERALL], Throughput(ops/sec), 23045.01459517591
- ycsb-run [OVERALL], Throughput(ops/sec), 13228.519364898786

### mix-20260911 mixJ arm56 — started 2026-09-30T18:50:31+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm56.ko`.
- Command: `bash script/mix-20260911.sh mixJ arm56`; evidence `result/mix-20260911/mixJ-arm56/`.

- Finished 2026-09-30T19:02:57+09:00; mixJ arm56 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-arm56-rep1`; cleanup attempted.
- total host_bytes=36582072320 host_pages=8931170 gc_pages=4111729 WAF=1.460380
- phaseA(sqlite-a) host_pages=8106864 gc_pages=4004743 WAF=1.493994
- phaseB(sqlite-b) host_pages=824306 gc_pages=106986 WAF=1.129789
- phaseA-load host_pages=1398351 gc_pages=623639 WAF=1.445982
- phaseA-run host_pages=6708513 gc_pages=3381104 WAF=1.504002
- ycsb-load [OVERALL], Throughput(ops/sec), 23217.118755562435
- ycsb-run [OVERALL], Throughput(ops/sec), 13644.705513143263

### mix-20260911 mixP arm46 — started 2026-09-30T19:03:16+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm46.ko`.
- Command: `bash script/mix-20260911.sh mixP arm46`; evidence `result/mix-20260911/mixP-arm46/`.

- Finished 2026-09-30T19:11:12+09:00; mixP arm46 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-arm46-rep1`; cleanup attempted.
- total host_bytes=37953355776 host_pages=9265956 gc_pages=1991502 WAF=1.214927
- phaseA(sqlite-a) host_pages=796306 gc_pages=233194 WAF=1.292845
- phaseB(oltp) host_pages=8469650 gc_pages=1758308 WAF=1.207601
- phaseA-load host_pages=452310 gc_pages=143227 WAF=1.316657
- phaseA-run host_pages=343996 gc_pages=89967 WAF=1.261535
- ycsb-load [OVERALL], Throughput(ops/sec), 26598.57431641664
- ycsb-run [OVERALL], Throughput(ops/sec), 55359.49069268563

### mix-20260911 mixP arm31 — started 2026-09-30T19:11:19+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm31.ko`.
- Command: `bash script/mix-20260911.sh mixP arm31`; evidence `result/mix-20260911/mixP-arm31/`.

- Finished 2026-09-30T19:19:20+09:00; mixP arm31 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-arm31-rep1`; cleanup attempted.
- total host_bytes=37130293248 host_pages=9065013 gc_pages=1883806 WAF=1.207811
- phaseA(sqlite-a) host_pages=810931 gc_pages=240205 WAF=1.296209
- phaseB(oltp) host_pages=8254082 gc_pages=1643601 WAF=1.199126
- phaseA-load host_pages=453334 gc_pages=144758 WAF=1.319319
- phaseA-run host_pages=357597 gc_pages=95447 WAF=1.266912
- ycsb-load [OVERALL], Throughput(ops/sec), 27948.574622694243
- ycsb-run [OVERALL], Throughput(ops/sec), 52164.16061345053

### mix-20260911 mixP arm32 — started 2026-09-30T19:19:27+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm32.ko`.
- Command: `bash script/mix-20260911.sh mixP arm32`; evidence `result/mix-20260911/mixP-arm32/`.

- Finished 2026-09-30T19:27:39+09:00; mixP arm32 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-arm32-rep1`; cleanup attempted.
- total host_bytes=38547382272 host_pages=9410982 gc_pages=1455983 WAF=1.154711
- phaseA(sqlite-a) host_pages=802556 gc_pages=211852 WAF=1.263972
- phaseB(oltp) host_pages=8608426 gc_pages=1244131 WAF=1.144525
- phaseA-load host_pages=452822 gc_pages=124043 WAF=1.273933
- phaseA-run host_pages=349734 gc_pages=87809 WAF=1.251074
- ycsb-load [OVERALL], Throughput(ops/sec), 26680.896478121664
- ycsb-run [OVERALL], Throughput(ops/sec), 48180.0004818

### mix-20260911 mixP arm17 — started 2026-09-30T19:27:47+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm17.ko`.
- Command: `bash script/mix-20260911.sh mixP arm17`; evidence `result/mix-20260911/mixP-arm17/`.

- Finished 2026-09-30T19:35:59+09:00; mixP arm17 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-arm17-rep1`; cleanup attempted.
- total host_bytes=38204473344 host_pages=9327264 gc_pages=1481010 WAF=1.158783
- phaseA(sqlite-a) host_pages=790963 gc_pages=208533 WAF=1.263644
- phaseB(oltp) host_pages=8536301 gc_pages=1272477 WAF=1.149067
- phaseA-load host_pages=452312 gc_pages=126012 WAF=1.278595
- phaseA-run host_pages=338651 gc_pages=82521 WAF=1.243676
- ycsb-load [OVERALL], Throughput(ops/sec), 27499.725002749972
- ycsb-run [OVERALL], Throughput(ops/sec), 50146.0503717076

### mix-20260911 mixP arm16 — started 2026-09-30T19:36:07+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm16.ko`.
- Command: `bash script/mix-20260911.sh mixP arm16`; evidence `result/mix-20260911/mixP-arm16/`.

- Finished 2026-09-30T19:44:17+09:00; mixP arm16 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-arm16-rep1`; cleanup attempted.
- total host_bytes=37030920192 host_pages=9040752 gc_pages=1794643 WAF=1.198506
- phaseA(sqlite-a) host_pages=800310 gc_pages=227677 WAF=1.284486
- phaseB(oltp) host_pages=8240442 gc_pages=1566966 WAF=1.190156
- phaseA-load host_pages=452821 gc_pages=138279 WAF=1.305372
- phaseA-run host_pages=347489 gc_pages=89398 WAF=1.257269
- ycsb-load [OVERALL], Throughput(ops/sec), 24052.33788724264
- ycsb-run [OVERALL], Throughput(ops/sec), 49752.481405010076

### mix-20260911 mixP arm15 — started 2026-09-30T19:44:25+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm15.ko`.
- Command: `bash script/mix-20260911.sh mixP arm15`; evidence `result/mix-20260911/mixP-arm15/`.

- Finished 2026-09-30T19:52:29+09:00; mixP arm15 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-arm15-rep1`; cleanup attempted.
- total host_bytes=37200424960 host_pages=9082135 gc_pages=2336419 WAF=1.257254
- phaseA(sqlite-a) host_pages=799497 gc_pages=260173 WAF=1.325421
- phaseB(oltp) host_pages=8282638 gc_pages=2076246 WAF=1.250674
- phaseA-load host_pages=452310 gc_pages=164243 WAF=1.363120
- phaseA-run host_pages=347187 gc_pages=95930 WAF=1.276306
- ycsb-load [OVERALL], Throughput(ops/sec), 24425.98925256473
- ycsb-run [OVERALL], Throughput(ops/sec), 51768.542844940275

### mix-20260911 mixP arm30 — started 2026-09-30T19:52:36+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm30.ko`.
- Command: `bash script/mix-20260911.sh mixP arm30`; evidence `result/mix-20260911/mixP-arm30/`.

- Finished 2026-09-30T20:00:41+09:00; mixP arm30 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-arm30-rep1`; cleanup attempted.
- total host_bytes=36872491008 host_pages=9002073 gc_pages=2454332 WAF=1.272641
- phaseA(sqlite-a) host_pages=796882 gc_pages=262711 WAF=1.329674
- phaseB(oltp) host_pages=8205191 gc_pages=2191621 WAF=1.267102
- phaseA-load host_pages=452312 gc_pages=168689 WAF=1.372948
- phaseA-run host_pages=344570 gc_pages=94022 WAF=1.272868
- ycsb-load [OVERALL], Throughput(ops/sec), 25070.196550340956
- ycsb-run [OVERALL], Throughput(ops/sec), 53417.37667263161

### mix-20260911 mixP arm34 — started 2026-09-30T20:00:48+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm34.ko`.
- Command: `bash script/mix-20260911.sh mixP arm34`; evidence `result/mix-20260911/mixP-arm34/`.

- Finished 2026-09-30T20:09:01+09:00; mixP arm34 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-arm34-rep1`; cleanup attempted.
- total host_bytes=37047169024 host_pages=9044719 gc_pages=1933547 WAF=1.213776
- phaseA(sqlite-a) host_pages=799888 gc_pages=235458 WAF=1.294364
- phaseB(oltp) host_pages=8244831 gc_pages=1698089 WAF=1.205958
- phaseA-load host_pages=452310 gc_pages=146089 WAF=1.322984
- phaseA-run host_pages=347578 gc_pages=89369 WAF=1.257119
- ycsb-load [OVERALL], Throughput(ops/sec), 24349.85877081913
- ycsb-run [OVERALL], Throughput(ops/sec), 48531.9097306479

### mix-20260911 mixP arm35 — started 2026-09-30T20:09:09+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm35.ko`.
- Command: `bash script/mix-20260911.sh mixP arm35`; evidence `result/mix-20260911/mixP-arm35/`.

- Finished 2026-09-30T20:17:27+09:00; mixP arm35 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-arm35-rep1`; cleanup attempted.
- total host_bytes=37513252864 host_pages=9158509 gc_pages=1497229 WAF=1.163480
- phaseA(sqlite-a) host_pages=794845 gc_pages=209506 WAF=1.263581
- phaseB(oltp) host_pages=8363664 gc_pages=1287723 WAF=1.153966
- phaseA-load host_pages=452313 gc_pages=133111 WAF=1.294290
- phaseA-run host_pages=342532 gc_pages=76395 WAF=1.223030
- ycsb-load [OVERALL], Throughput(ops/sec), 28312.570781426955
- ycsb-run [OVERALL], Throughput(ops/sec), 45118.20970943873

### mix-20260911 mixP arm45 — started 2026-09-30T20:17:38+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm45.ko`.
- Command: `bash script/mix-20260911.sh mixP arm45`; evidence `result/mix-20260911/mixP-arm45/`.

- Finished 2026-09-30T20:25:39+09:00; mixP arm45 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-arm45-rep1`; cleanup attempted.
- total host_bytes=37052444672 host_pages=9046007 gc_pages=2613229 WAF=1.288882
- phaseA(sqlite-a) host_pages=811456 gc_pages=268531 WAF=1.330925
- phaseB(oltp) host_pages=8234040 gc_pages=2344674 WAF=1.284754
- phaseA-load host_pages=453845 gc_pages=165072 WAF=1.363719
- phaseA-run host_pages=357611 gc_pages=103459 WAF=1.289306
- ycsb-load [OVERALL], Throughput(ops/sec), 25143.316906366286
- ycsb-run [OVERALL], Throughput(ops/sec), 55954.22944031782

### mix-20260911 mixP arm49 — started 2026-09-30T20:25:46+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm49.ko`.
- Command: `bash script/mix-20260911.sh mixP arm49`; evidence `result/mix-20260911/mixP-arm49/`.

- Finished 2026-09-30T20:33:52+09:00; mixP arm49 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-arm49-rep1`; cleanup attempted.
- total host_bytes=38574960640 host_pages=9417715 gc_pages=2009777 WAF=1.213404
- phaseA(sqlite-a) host_pages=794273 gc_pages=234802 WAF=1.295619
- phaseB(oltp) host_pages=8623442 gc_pages=1774975 WAF=1.205831
- phaseA-load host_pages=452312 gc_pages=152297 WAF=1.336708
- phaseA-run host_pages=341961 gc_pages=82505 WAF=1.241270
- ycsb-load [OVERALL], Throughput(ops/sec), 28762.080073630925
- ycsb-run [OVERALL], Throughput(ops/sec), 50758.20062178796

### mix-20260911 mixP arm53 — started 2026-09-30T20:34:00+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm53.ko`.
- Command: `bash script/mix-20260911.sh mixP arm53`; evidence `result/mix-20260911/mixP-arm53/`.

- Finished 2026-09-30T20:41:41+09:00; mixP arm53 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-arm53-rep1`; cleanup attempted.
- total host_bytes=40625913856 host_pages=9918436 gc_pages=1723412 WAF=1.173758
- phaseA(sqlite-a) host_pages=722166 gc_pages=219533 WAF=1.303992
- phaseB(oltp) host_pages=9196270 gc_pages=1503879 WAF=1.163531
- phaseA-load host_pages=453845 gc_pages=135942 WAF=1.299534
- phaseA-run host_pages=268321 gc_pages=83591 WAF=1.311534
- ycsb-load [OVERALL], Throughput(ops/sec), 31482.181085505603
- ycsb-run [OVERALL], Throughput(ops/sec), 69493.91059608402

### mix-20260911 mixP arm56 — started 2026-09-30T20:41:49+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm56.ko`.
- Command: `bash script/mix-20260911.sh mixP arm56`; evidence `result/mix-20260911/mixP-arm56/`.

- Finished 2026-09-30T20:49:41+09:00; mixP arm56 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-arm56-rep1`; cleanup attempted.
- total host_bytes=39860142080 host_pages=9731480 gc_pages=1947719 WAF=1.200146
- phaseA(sqlite-a) host_pages=710265 gc_pages=305860 WAF=1.430628
- phaseB(oltp) host_pages=9021215 gc_pages=1641859 WAF=1.182000
- phaseA-load host_pages=452310 gc_pages=215317 WAF=1.476039
- phaseA-run host_pages=257955 gc_pages=90543 WAF=1.351003
- ycsb-load [OVERALL], Throughput(ops/sec), 22630.578437584863
- ycsb-run [OVERALL], Throughput(ops/sec), 60597.79727006923

### mix-20260911 mixB arm46 — started 2026-09-30T20:49:59+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm46.ko`.
- Command: `bash script/mix-20260911.sh mixB arm46`; evidence `result/mix-20260911/mixB-arm46/`.

- Finished 2026-09-30T21:07:15+09:00; mixB arm46 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-arm46-rep1`; cleanup attempted.
- total host_bytes=131454930944 host_pages=32093489 gc_pages=50904998 WAF=2.586147
- phaseA(sqlite-a) host_pages=8092831 gc_pages=3435372 WAF=1.424496
- phaseB(test4) host_pages=24000658 gc_pages=47469626 WAF=2.977847
- phaseA-load host_pages=1402438 gc_pages=460903 WAF=1.328644
- phaseA-run host_pages=6690393 gc_pages=2974469 WAF=1.444588
- ycsb-load [OVERALL], Throughput(ops/sec), 27972.027972027972
- ycsb-run [OVERALL], Throughput(ops/sec), 12994.691668453437

### mix-20260911 mixB arm31 — started 2026-09-30T21:07:21+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm31.ko`.
- Command: `bash script/mix-20260911.sh mixB arm31`; evidence `result/mix-20260911/mixB-arm31/`.

- Finished 2026-09-30T21:24:30+09:00; mixB arm31 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-arm31-rep1`; cleanup attempted.
- total host_bytes=131426390016 host_pages=32086521 gc_pages=47859834 WAF=2.491587
- phaseA(sqlite-a) host_pages=8069976 gc_pages=3188470 WAF=1.395103
- phaseB(test4) host_pages=24016545 gc_pages=44671364 WAF=2.860025
- phaseA-load host_pages=1399372 gc_pages=439493 WAF=1.314064
- phaseA-run host_pages=6670604 gc_pages=2748977 WAF=1.412103
- ycsb-load [OVERALL], Throughput(ops/sec), 23695.74661348288
- ycsb-run [OVERALL], Throughput(ops/sec), 13225.588869344407

### mix-20260911 mixB arm32 — started 2026-09-30T21:24:36+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm32.ko`.
- Command: `bash script/mix-20260911.sh mixB arm32`; evidence `result/mix-20260911/mixB-arm32/`.

- Finished 2026-09-30T21:43:51+09:00; mixB arm32 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-arm32-rep1`; cleanup attempted.
- total host_bytes=131046838272 host_pages=31993857 gc_pages=48314523 WAF=2.510119
- phaseA(sqlite-a) host_pages=7993199 gc_pages=3622122 WAF=1.453150
- phaseB(test4) host_pages=24000658 gc_pages=44692401 WAF=2.862132
- phaseA-load host_pages=1398349 gc_pages=369924 WAF=1.264543
- phaseA-run host_pages=6594850 gc_pages=3252198 WAF=1.493142
- ycsb-load [OVERALL], Throughput(ops/sec), 22456.770716370986
- ycsb-run [OVERALL], Throughput(ops/sec), 9269.343962181076

### mix-20260911 mixB arm17 — started 2026-09-30T21:43:57+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm17.ko`.
- Command: `bash script/mix-20260911.sh mixB arm17`; evidence `result/mix-20260911/mixB-arm17/`.

- Finished 2026-09-30T22:01:05+09:00; mixB arm17 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-arm17-rep1`; cleanup attempted.
- total host_bytes=131302551552 host_pages=32056287 gc_pages=58200780 WAF=2.815581
- phaseA(sqlite-a) host_pages=8055628 gc_pages=2953977 WAF=1.366697
- phaseB(test4) host_pages=24000659 gc_pages=55246803 WAF=3.301887
- phaseA-load host_pages=1398341 gc_pages=399819 WAF=1.285924
- phaseA-run host_pages=6657287 gc_pages=2554158 WAF=1.383663
- ycsb-load [OVERALL], Throughput(ops/sec), 24718.823384006922
- ycsb-run [OVERALL], Throughput(ops/sec), 13237.274842228231

### mix-20260911 mixB arm16 — started 2026-09-30T22:01:11+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm16.ko`.
- Command: `bash script/mix-20260911.sh mixB arm16`; evidence `result/mix-20260911/mixB-arm16/`.

- Finished 2026-09-30T22:18:29+09:00; mixB arm16 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-arm16-rep1`; cleanup attempted.
- total host_bytes=131440467968 host_pages=32089958 gc_pages=58588071 WAF=2.825745
- phaseA(sqlite-a) host_pages=8089300 gc_pages=3514969 WAF=1.434521
- phaseB(test4) host_pages=24000658 gc_pages=55073102 WAF=3.294650
- phaseA-load host_pages=1398349 gc_pages=479244 WAF=1.342721
- phaseA-run host_pages=6690951 gc_pages=3035725 WAF=1.453706
- ycsb-load [OVERALL], Throughput(ops/sec), 23457.65892563922
- ycsb-run [OVERALL], Throughput(ops/sec), 12847.814426168428

### mix-20260911 mixB arm15 — started 2026-09-30T22:18:35+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm15.ko`.
- Command: `bash script/mix-20260911.sh mixB arm15`; evidence `result/mix-20260911/mixB-arm15/`.

- Finished 2026-09-30T22:35:42+09:00; mixB arm15 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-arm15-rep1`; cleanup attempted.
- total host_bytes=131250053120 host_pages=32043470 gc_pages=63259754 WAF=2.974186
- phaseA(sqlite-a) host_pages=8042812 gc_pages=4037502 WAF=1.502001
- phaseB(test4) host_pages=24000658 gc_pages=59222252 WAF=3.467526
- phaseA-load host_pages=1406025 gc_pages=570075 WAF=1.405452
- phaseA-run host_pages=6636787 gc_pages=3467427 WAF=1.522456
- ycsb-load [OVERALL], Throughput(ops/sec), 21251.726702794604
- ycsb-run [OVERALL], Throughput(ops/sec), 13630.477748245075

### mix-20260911 mixB arm30 — started 2026-09-30T22:35:48+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm30.ko`.
- Command: `bash script/mix-20260911.sh mixB arm30`; evidence `result/mix-20260911/mixB-arm30/`.

- Finished 2026-09-30T22:53:04+09:00; mixB arm30 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-arm30-rep1`; cleanup attempted.
- total host_bytes=131378999296 host_pages=32074951 gc_pages=57701850 WAF=2.798969
- phaseA(sqlite-a) host_pages=8074286 gc_pages=3902826 WAF=1.483365
- phaseB(test4) host_pages=24000665 gc_pages=53799024 WAF=3.241564
- phaseA-load host_pages=1398349 gc_pages=554712 WAF=1.396691
- phaseA-run host_pages=6675937 gc_pages=3348114 WAF=1.501520
- ycsb-load [OVERALL], Throughput(ops/sec), 24024.985985424843
- ycsb-run [OVERALL], Throughput(ops/sec), 12933.180721800816

### mix-20260911 mixB arm34 — started 2026-09-30T22:53:11+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm34.ko`.
- Command: `bash script/mix-20260911.sh mixB arm34`; evidence `result/mix-20260911/mixB-arm34/`.

- Finished 2026-09-30T23:10:35+09:00; mixB arm34 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-arm34-rep1`; cleanup attempted.
- total host_bytes=131415719936 host_pages=32083916 gc_pages=61565980 WAF=2.918905
- phaseA(sqlite-a) host_pages=8083258 gc_pages=3642231 WAF=1.450589
- phaseB(test4) host_pages=24000658 gc_pages=57923749 WAF=3.413423
- phaseA-load host_pages=1398351 gc_pages=494328 WAF=1.353508
- phaseA-run host_pages=6684907 gc_pages=3147903 WAF=1.470897
- ycsb-load [OVERALL], Throughput(ops/sec), 24166.26389560174
- ycsb-run [OVERALL], Throughput(ops/sec), 12899.647194649226

### mix-20260911 mixB arm35 — started 2026-09-30T23:10:41+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm35.ko`.
- Command: `bash script/mix-20260911.sh mixB arm35`; evidence `result/mix-20260911/mixB-arm35/`.

- Finished 2026-09-30T23:28:01+09:00; mixB arm35 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-arm35-rep1`; cleanup attempted.
- total host_bytes=131435995136 host_pages=32088866 gc_pages=57175671 WAF=2.781792
- phaseA(sqlite-a) host_pages=8082573 gc_pages=2899061 WAF=1.358680
- phaseB(test4) host_pages=24005782 gc_pages=54276470 WAF=3.260975
- phaseA-load host_pages=1399885 gc_pages=382476 WAF=1.273220
- phaseA-run host_pages=6682688 gc_pages=2516585 WAF=1.376583
- ycsb-load [OVERALL], Throughput(ops/sec), 21973.192704900022
- ycsb-run [OVERALL], Throughput(ops/sec), 13113.55023145416

### mix-20260911 mixB arm45 — started 2026-09-30T23:28:07+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm45.ko`.
- Command: `bash script/mix-20260911.sh mixB arm45`; evidence `result/mix-20260911/mixB-arm45/`.

- Finished 2026-09-30T23:45:19+09:00; mixB arm45 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-arm45-rep1`; cleanup attempted.
- total host_bytes=131386253312 host_pages=32076722 gc_pages=56959543 WAF=2.775728
- phaseA(sqlite-a) host_pages=8076064 gc_pages=3932080 WAF=1.486881
- phaseB(test4) host_pages=24000658 gc_pages=53027463 WAF=3.209417
- phaseA-load host_pages=1398339 gc_pages=563279 WAF=1.402820
- phaseA-run host_pages=6677725 gc_pages=3368801 WAF=1.504483
- ycsb-load [OVERALL], Throughput(ops/sec), 25977.399662293803
- ycsb-run [OVERALL], Throughput(ops/sec), 13003.647523130237

### mix-20260911 mixB arm49 — started 2026-09-30T23:45:25+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm49.ko`.
- Command: `bash script/mix-20260911.sh mixB arm49`; evidence `result/mix-20260911/mixB-arm49/`.

- Finished 2026-10-01T00:04:52+09:00; mixB arm49 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-arm49-rep1`; cleanup attempted.
- total host_bytes=131276619776 host_pages=32049956 gc_pages=57905554 WAF=2.806728
- phaseA(sqlite-a) host_pages=8049289 gc_pages=4096767 WAF=1.508960
- phaseB(test4) host_pages=24000667 gc_pages=53808787 WAF=3.241970
- phaseA-load host_pages=1398341 gc_pages=492335 WAF=1.352085
- phaseA-run host_pages=6650948 gc_pages=3604432 WAF=1.541943
- ycsb-load [OVERALL], Throughput(ops/sec), 27931.660537218937
- ycsb-run [OVERALL], Throughput(ops/sec), 8876.875517355402

### mix-20260911 mixB arm53 — started 2026-10-01T00:04:58+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm53.ko`.
- Command: `bash script/mix-20260911.sh mixB arm53`; evidence `result/mix-20260911/mixB-arm53/`.

- Finished 2026-10-01T00:22:06+09:00; mixB arm53 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-arm53-rep1`; cleanup attempted.
- total host_bytes=131357302784 host_pages=32069654 gc_pages=63820811 WAF=2.990069
- phaseA(sqlite-a) host_pages=8068996 gc_pages=3446779 WAF=1.427163
- phaseB(test4) host_pages=24000658 gc_pages=60374032 WAF=3.515516
- phaseA-load host_pages=1398341 gc_pages=429673 WAF=1.307273
- phaseA-run host_pages=6670655 gc_pages=3017106 WAF=1.452295
- ycsb-load [OVERALL], Throughput(ops/sec), 27607.785395481525
- ycsb-run [OVERALL], Throughput(ops/sec), 13098.434737048923

### mix-20260911 mixB arm56 — started 2026-10-01T00:22:12+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm56.ko`.
- Command: `bash script/mix-20260911.sh mixB arm56`; evidence `result/mix-20260911/mixB-arm56/`.

- Finished 2026-10-01T00:39:39+09:00; mixB arm56 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-arm56-rep1`; cleanup attempted.
- total host_bytes=131485626368 host_pages=32100983 gc_pages=71759677 WAF=3.235436
- phaseA(sqlite-a) host_pages=8100322 gc_pages=4016947 WAF=1.495900
- phaseB(test4) host_pages=24000661 gc_pages=67742730 WAF=3.822536
- phaseA-load host_pages=1398351 gc_pages=605860 WAF=1.433267
- phaseA-run host_pages=6701971 gc_pages=3411087 WAF=1.508968
- ycsb-load [OVERALL], Throughput(ops/sec), 23304.59100442787
- ycsb-run [OVERALL], Throughput(ops/sec), 12707.045421333858

### mix-20260911 mixD arm46 — started 2026-10-01T00:39:59+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm46.ko`.
- Command: `bash script/mix-20260911.sh mixD arm46`; evidence `result/mix-20260911/mixD-arm46/`.

- Finished 2026-10-01T01:01:26+09:00; mixD arm46 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-arm46-rep1`; cleanup attempted.
- total host_bytes=122884431872 host_pages=30001082 gc_pages=23695450 WAF=1.789820
- phaseA(test4) host_pages=24000661 gc_pages=18803981 WAF=1.783478
- phaseB(test3) host_pages=6000421 gc_pages=4891469 WAF=1.815188
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD arm31 — started 2026-10-01T01:01:31+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm31.ko`.
- Command: `bash script/mix-20260911.sh mixD arm31`; evidence `result/mix-20260911/mixD-arm31/`.

- Finished 2026-10-01T01:22:56+09:00; mixD arm31 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-arm31-rep1`; cleanup attempted.
- total host_bytes=122884419584 host_pages=30001079 gc_pages=24024627 WAF=1.800792
- phaseA(test4) host_pages=24000658 gc_pages=19112938 WAF=1.796351
- phaseB(test3) host_pages=6000421 gc_pages=4911689 WAF=1.818557
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD arm32 — started 2026-10-01T01:23:00+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm32.ko`.
- Command: `bash script/mix-20260911.sh mixD arm32`; evidence `result/mix-20260911/mixD-arm32/`.

- Finished 2026-10-01T01:44:26+09:00; mixD arm32 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-arm32-rep1`; cleanup attempted.
- total host_bytes=122884419584 host_pages=30001079 gc_pages=23920836 WAF=1.797333
- phaseA(test4) host_pages=24000658 gc_pages=19094915 WAF=1.795600
- phaseB(test3) host_pages=6000421 gc_pages=4825921 WAF=1.804264
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD arm17 — started 2026-10-01T01:44:30+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm17.ko`.
- Command: `bash script/mix-20260911.sh mixD arm17`; evidence `result/mix-20260911/mixD-arm17/`.

- Finished 2026-10-01T02:05:55+09:00; mixD arm17 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-arm17-rep1`; cleanup attempted.
- total host_bytes=122959872000 host_pages=30019500 gc_pages=25831000 WAF=1.860474
- phaseA(test4) host_pages=24019082 gc_pages=20876132 WAF=1.869148
- phaseB(test3) host_pages=6000418 gc_pages=4954868 WAF=1.825754
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD arm16 — started 2026-10-01T02:06:00+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm16.ko`.
- Command: `bash script/mix-20260911.sh mixD arm16`; evidence `result/mix-20260911/mixD-arm16/`.

- Finished 2026-10-01T02:27:25+09:00; mixD arm16 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-arm16-rep1`; cleanup attempted.
- total host_bytes=122884407296 host_pages=30001076 gc_pages=25039537 WAF=1.834621
- phaseA(test4) host_pages=24000661 gc_pages=19977561 WAF=1.832375
- phaseB(test3) host_pages=6000415 gc_pages=5061976 WAF=1.843604
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD arm15 — started 2026-10-01T02:27:29+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm15.ko`.
- Command: `bash script/mix-20260911.sh mixD arm15`; evidence `result/mix-20260911/mixD-arm15/`.

- Finished 2026-10-01T02:48:55+09:00; mixD arm15 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-arm15-rep1`; cleanup attempted.
- total host_bytes=122884468736 host_pages=30001091 gc_pages=26151532 WAF=1.871686
- phaseA(test4) host_pages=24000676 gc_pages=21052599 WAF=1.877167
- phaseB(test3) host_pages=6000415 gc_pages=5098933 WAF=1.849763
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD arm30 — started 2026-10-01T02:48:59+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm30.ko`.
- Command: `bash script/mix-20260911.sh mixD arm30`; evidence `result/mix-20260911/mixD-arm30/`.

- Finished 2026-10-01T03:10:24+09:00; mixD arm30 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-arm30-rep1`; cleanup attempted.
- total host_bytes=122884419584 host_pages=30001079 gc_pages=25116635 WAF=1.837191
- phaseA(test4) host_pages=24000658 gc_pages=20128730 WAF=1.838674
- phaseB(test3) host_pages=6000421 gc_pages=4987905 WAF=1.831259
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD arm34 — started 2026-10-01T03:10:29+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm34.ko`.
- Command: `bash script/mix-20260911.sh mixD arm34`; evidence `result/mix-20260911/mixD-arm34/`.

- Finished 2026-10-01T03:31:54+09:00; mixD arm34 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-arm34-rep1`; cleanup attempted.
- total host_bytes=122884419584 host_pages=30001079 gc_pages=25310405 WAF=1.843650
- phaseA(test4) host_pages=24000661 gc_pages=20373350 WAF=1.848866
- phaseB(test3) host_pages=6000418 gc_pages=4937055 WAF=1.822785
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD arm35 — started 2026-10-01T03:31:59+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm35.ko`.
- Command: `bash script/mix-20260911.sh mixD arm35`; evidence `result/mix-20260911/mixD-arm35/`.

- Finished 2026-10-01T03:53:24+09:00; mixD arm35 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-arm35-rep1`; cleanup attempted.
- total host_bytes=122884419584 host_pages=30001079 gc_pages=25252646 WAF=1.841725
- phaseA(test4) host_pages=24000658 gc_pages=20316692 WAF=1.846506
- phaseB(test3) host_pages=6000421 gc_pages=4935954 WAF=1.822601
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD arm45 — started 2026-10-01T03:53:29+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm45.ko`.
- Command: `bash script/mix-20260911.sh mixD arm45`; evidence `result/mix-20260911/mixD-arm45/`.

- Finished 2026-10-01T04:14:54+09:00; mixD arm45 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-arm45-rep1`; cleanup attempted.
- total host_bytes=122884431872 host_pages=30001082 gc_pages=24795260 WAF=1.826479
- phaseA(test4) host_pages=24000664 gc_pages=19836198 WAF=1.826485
- phaseB(test3) host_pages=6000418 gc_pages=4959062 WAF=1.826453
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD arm49 — started 2026-10-01T04:14:59+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm49.ko`.
- Command: `bash script/mix-20260911.sh mixD arm49`; evidence `result/mix-20260911/mixD-arm49/`.

- Finished 2026-10-01T04:36:24+09:00; mixD arm49 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-arm49-rep1`; cleanup attempted.
- total host_bytes=122884431872 host_pages=30001082 gc_pages=24897549 WAF=1.829888
- phaseA(test4) host_pages=24000664 gc_pages=19982272 WAF=1.832572
- phaseB(test3) host_pages=6000418 gc_pages=4915277 WAF=1.819156
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD arm53 — started 2026-10-01T04:36:32+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm53.ko`.
- Command: `bash script/mix-20260911.sh mixD arm53`; evidence `result/mix-20260911/mixD-arm53/`.

- Finished 2026-10-01T04:58:00+09:00; mixD arm53 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-arm53-rep1`; cleanup attempted.
- total host_bytes=122907455488 host_pages=30006703 gc_pages=26286044 WAF=1.876006
- phaseA(test4) host_pages=24006288 gc_pages=21240700 WAF=1.884797
- phaseB(test3) host_pages=6000415 gc_pages=5045344 WAF=1.840833
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD arm56 — started 2026-10-01T04:58:05+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm56.ko`.
- Command: `bash script/mix-20260911.sh mixD arm56`; evidence `result/mix-20260911/mixD-arm56/`.

- Finished 2026-10-01T05:19:30+09:00; mixD arm56 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-arm56-rep1`; cleanup attempted.
- total host_bytes=122884431872 host_pages=30001082 gc_pages=29968158 WAF=1.998903
- phaseA(test4) host_pages=24000661 gc_pages=24726774 WAF=2.030254
- phaseB(test3) host_pages=6000421 gc_pages=5241384 WAF=1.873503
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK arm46 — started 2026-10-01T05:19:52+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm46.ko`.
- Command: `bash script/mix-20260911.sh mixK arm46`; evidence `result/mix-20260911/mixK-arm46/`.

- Finished 2026-10-01T05:41:19+09:00; mixK arm46 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-arm46-rep1`; cleanup attempted.
- total host_bytes=196616130560 host_pages=48001985 gc_pages=37738872 WAF=1.786194
- phaseA(test4-hot512M) host_pages=24000661 gc_pages=18846576 WAF=1.785252
- phaseB(test4-hot128M) host_pages=24001324 gc_pages=18892296 WAF=1.787136
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK arm31 — started 2026-10-01T05:41:23+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm31.ko`.
- Command: `bash script/mix-20260911.sh mixK arm31`; evidence `result/mix-20260911/mixK-arm31/`.

- Finished 2026-10-01T06:02:48+09:00; mixK arm31 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-arm31-rep1`; cleanup attempted.
- total host_bytes=196708417536 host_pages=48024516 gc_pages=37676411 WAF=1.784525
- phaseA(test4-hot512M) host_pages=24023189 gc_pages=18950336 WAF=1.788835
- phaseB(test4-hot128M) host_pages=24001327 gc_pages=18726075 WAF=1.780210
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK arm32 — started 2026-10-01T06:02:53+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm32.ko`.
- Command: `bash script/mix-20260911.sh mixK arm32`; evidence `result/mix-20260911/mixK-arm32/`.

- Finished 2026-10-01T06:24:18+09:00; mixK arm32 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-arm32-rep1`; cleanup attempted.
- total host_bytes=196616265728 host_pages=48002018 gc_pages=37929238 WAF=1.790159
- phaseA(test4-hot512M) host_pages=24000679 gc_pages=19078155 WAF=1.794901
- phaseB(test4-hot128M) host_pages=24001339 gc_pages=18851083 WAF=1.785418
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK arm17 — started 2026-10-01T06:24:22+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm17.ko`.
- Command: `bash script/mix-20260911.sh mixK arm17`; evidence `result/mix-20260911/mixK-arm17/`.

- Finished 2026-10-01T06:45:47+09:00; mixK arm17 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-arm17-rep1`; cleanup attempted.
- total host_bytes=196616155136 host_pages=48001991 gc_pages=40978716 WAF=1.853688
- phaseA(test4-hot512M) host_pages=24000661 gc_pages=20938980 WAF=1.872433
- phaseB(test4-hot128M) host_pages=24001330 gc_pages=20039736 WAF=1.834943
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK arm16 — started 2026-10-01T06:45:52+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm16.ko`.
- Command: `bash script/mix-20260911.sh mixK arm16`; evidence `result/mix-20260911/mixK-arm16/`.

- Finished 2026-10-01T07:07:17+09:00; mixK arm16 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-arm16-rep1`; cleanup attempted.
- total host_bytes=196721008640 host_pages=48027590 gc_pages=39319471 WAF=1.818685
- phaseA(test4-hot512M) host_pages=24026269 gc_pages=19624644 WAF=1.816799
- phaseB(test4-hot128M) host_pages=24001321 gc_pages=19694827 WAF=1.820573
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK arm15 — started 2026-10-01T07:07:22+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm15.ko`.
- Command: `bash script/mix-20260911.sh mixK arm15`; evidence `result/mix-20260911/mixK-arm15/`.

- Finished 2026-10-01T07:28:47+09:00; mixK arm15 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-arm15-rep1`; cleanup attempted.
- total host_bytes=196616105984 host_pages=48001979 gc_pages=41478486 WAF=1.864099
- phaseA(test4-hot512M) host_pages=24000658 gc_pages=21057068 WAF=1.877354
- phaseB(test4-hot128M) host_pages=24001321 gc_pages=20421418 WAF=1.850846
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK arm30 — started 2026-10-01T07:28:52+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm30.ko`.
- Command: `bash script/mix-20260911.sh mixK arm30`; evidence `result/mix-20260911/mixK-arm30/`.

- Finished 2026-10-01T07:50:18+09:00; mixK arm30 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-arm30-rep1`; cleanup attempted.
- total host_bytes=196714799104 host_pages=48026074 gc_pages=37923280 WAF=1.789639
- phaseA(test4-hot512M) host_pages=24012449 gc_pages=19047046 WAF=1.793215
- phaseB(test4-hot128M) host_pages=24013625 gc_pages=18876234 WAF=1.786063
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK arm34 — started 2026-10-01T07:50:23+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm34.ko`.
- Command: `bash script/mix-20260911.sh mixK arm34`; evidence `result/mix-20260911/mixK-arm34/`.

- Finished 2026-10-01T08:11:48+09:00; mixK arm34 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-arm34-rep1`; cleanup attempted.
- total host_bytes=196616192000 host_pages=48002000 gc_pages=40371123 WAF=1.841030
- phaseA(test4-hot512M) host_pages=24000679 gc_pages=20439783 WAF=1.851634
- phaseB(test4-hot128M) host_pages=24001321 gc_pages=19931340 WAF=1.830427
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK arm35 — started 2026-10-01T08:11:53+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm35.ko`.
- Command: `bash script/mix-20260911.sh mixK arm35`; evidence `result/mix-20260911/mixK-arm35/`.

- Finished 2026-10-01T08:33:18+09:00; mixK arm35 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-arm35-rep1`; cleanup attempted.
- total host_bytes=196637143040 host_pages=48007115 gc_pages=40095930 WAF=1.835208
- phaseA(test4-hot512M) host_pages=24005791 gc_pages=20339773 WAF=1.847286
- phaseB(test4-hot128M) host_pages=24001324 gc_pages=19756157 WAF=1.823128
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK arm45 — started 2026-10-01T08:33:23+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm45.ko`.
- Command: `bash script/mix-20260911.sh mixK arm45`; evidence `result/mix-20260911/mixK-arm45/`.

- Finished 2026-10-01T08:54:48+09:00; mixK arm45 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-arm45-rep1`; cleanup attempted.
- total host_bytes=196616192000 host_pages=48002000 gc_pages=39295980 WAF=1.818632
- phaseA(test4-hot512M) host_pages=24000667 gc_pages=19746744 WAF=1.822758
- phaseB(test4-hot128M) host_pages=24001333 gc_pages=19549236 WAF=1.814506
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK arm49 — started 2026-10-01T08:54:53+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm49.ko`.
- Command: `bash script/mix-20260911.sh mixK arm49`; evidence `result/mix-20260911/mixK-arm49/`.

- Finished 2026-10-01T09:16:18+09:00; mixK arm49 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-arm49-rep1`; cleanup attempted.
- total host_bytes=196616105984 host_pages=48001979 gc_pages=39540586 WAF=1.823728
- phaseA(test4-hot512M) host_pages=24000658 gc_pages=19964351 WAF=1.831825
- phaseB(test4-hot128M) host_pages=24001321 gc_pages=19576235 WAF=1.815632
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK arm53 — started 2026-10-01T09:16:23+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm53.ko`.
- Command: `bash script/mix-20260911.sh mixK arm53`; evidence `result/mix-20260911/mixK-arm53/`.

- Finished 2026-10-01T09:37:48+09:00; mixK arm53 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-arm53-rep1`; cleanup attempted.
- total host_bytes=196616155136 host_pages=48001991 gc_pages=41170802 WAF=1.857689
- phaseA(test4-hot512M) host_pages=24000670 gc_pages=21252473 WAF=1.885495
- phaseB(test4-hot128M) host_pages=24001321 gc_pages=19918329 WAF=1.829885
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK arm56 — started 2026-10-01T09:37:53+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm56.ko`.
- Command: `bash script/mix-20260911.sh mixK arm56`; evidence `result/mix-20260911/mixK-arm56/`.

- Finished 2026-10-01T09:59:19+09:00; mixK arm56 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-arm56-rep1`; cleanup attempted.
- total host_bytes=196616118272 host_pages=48001982 gc_pages=47959568 WAF=1.999116
- phaseA(test4-hot512M) host_pages=24000661 gc_pages=24659359 WAF=2.027445
- phaseB(test4-hot128M) host_pages=24001321 gc_pages=23300209 WAF=1.970789
- ycsb-load 
- ycsb-run 

### mix-20260911 mixH arm46 — started 2026-10-01T09:59:26+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm46.ko`.
- Command: `bash script/mix-20260911.sh mixH arm46`; evidence `result/mix-20260911/mixH-arm46/`.

- Finished 2026-10-01T10:27:46+09:00; mixH arm46 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-arm46-rep1`; cleanup attempted.
- total host_bytes=156547362816 host_pages=38219571 gc_pages=27451638 WAF=1.718261
- phaseA(test3) host_pages=6000424 gc_pages=4784340 WAF=1.797334
- phaseB(test4) host_pages=24000658 gc_pages=17913735 WAF=1.746385
- phaseC(sqlite-a) host_pages=8218489 gc_pages=4753563 WAF=1.578399
- phaseC-load host_pages=1398349 gc_pages=719924 WAF=1.514839
- phaseC-run host_pages=6820140 gc_pages=4033639 WAF=1.591431
- ycsb-load [OVERALL], Throughput(ops/sec), 18274.85380116959
- ycsb-run [OVERALL], Throughput(ops/sec), 10987.290451769915

### mix-20260911 mixH arm31 — started 2026-10-01T10:27:52+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm31.ko`.
- Command: `bash script/mix-20260911.sh mixH arm31`; evidence `result/mix-20260911/mixH-arm31/`.

## 2026-10-01 — 처음 보는 리뷰어 심사(별도 에이전트, 원고와 그림만 열람) 반영

- 판정: 수정 후 재심. 확인된 지적: iCAT이 "모든 경우" CAT-Default보다 나쁘다는 주장이 1배 길이에서만 성립(3시간 1.884 < 1.974, 3구간 전환 2.288 < 2.410), CAT-Best가 이 환경 측정에서는 2위(1위 arm 31, 1.744), Greedy 값 혼용(2.186 = 3회 평균, 2.203 = 1회), 초록의 "최대 18.3%"가 CAT-Best에 15% 진 워크로드의 값, "5위"가 15개 중 순위, arm 47의 이웃은 32·46·50뿐(44 아님), 워크로드 정의 부족, 그림 7(−5.7%, n=2)과 표 4(−5.3%, n=3) 불일치.
- 로그 분석(실험 없음):
  - 저성능 조합(최상위 대비 15% 초과) 사용 21% 중 초기 순회 7.6%p, 순회 이후 13.3%p (iCAT). iCAT-v3 순회 이후 9.9%, iCAT-v4 1.6%.
  - 같은 조합의 판단 구간 WAF 표준편차: 직전 구간이 같은 조합일 때 0.120, 다른 조합일 때 0.139 (iCAT 3시간). 흔들림의 대부분은 직전 조합의 영향이 아닌 구간 자체의 변동.
- 사전 등록 queue32(queue31 뒤, 약 2일): A. iCAT-v4 ×3 길이를 전환 워크로드 13종 모두 n=3으로 / B. OLTP → Varmail의 arm 47·17·50 ×3 반복(n=3) / C. 구성 요소 제거: iCAT-v3의 판단 구간(64 GC로 복원), 순회 횟수(3회), 초기화 임계값(12.5%), iCAT-v4의 후보 제거 끔, 이웃 탐색 끔(FIO-Fast 3시간), 부분 초기화 대신 전체 복원(3구간 전환), 기존 v3·k2·probe 2회차. 모듈 SHA256은 result/sweep-20260915/modules.sha256 끝 6줄.
- 판정 기준: 반복 3회 평균과 범위로 표 4·그림 7을 다시 계산. OLTP → Varmail에서 iCAT-v4 3회 범위가 고정 조합 3회 범위와 겹치지 않으면 "우위" 유지, 겹치면 "동등"으로 표현을 낮춘다. 구성 요소별로 3시간 WAF가 iCAT-v3/v4 대비 1% 이상 나빠지면 기여로 판정.

- Finished 2026-10-01T10:56:03+09:00; mixH arm31 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-arm31-rep1`; cleanup attempted.
- total host_bytes=156453933056 host_pages=38196761 gc_pages=27714918 WAF=1.725583
- phaseA(test3) host_pages=6000418 gc_pages=4792581 WAF=1.798708
- phaseB(test4) host_pages=24000658 gc_pages=18150084 WAF=1.756233
- phaseC(sqlite-a) host_pages=8195685 gc_pages=4772253 WAF=1.582288
- phaseC-load host_pages=1398349 gc_pages=721671 WAF=1.516088
- phaseC-run host_pages=6797336 gc_pages=4050582 WAF=1.595907
- ycsb-load [OVERALL], Throughput(ops/sec), 18790.517052394225
- ycsb-run [OVERALL], Throughput(ops/sec), 11235.891933191386

### mix-20260911 mixH arm32 — started 2026-10-01T10:56:10+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm32.ko`.
- Command: `bash script/mix-20260911.sh mixH arm32`; evidence `result/mix-20260911/mixH-arm32/`.

- Finished 2026-10-01T11:26:49+09:00; mixH arm32 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-arm32-rep1`; cleanup attempted.
- total host_bytes=156404895744 host_pages=38184789 gc_pages=28039290 WAF=1.734305
- phaseA(test3) host_pages=6000427 gc_pages=4795915 WAF=1.799262
- phaseB(test4) host_pages=24000658 gc_pages=18220104 WAF=1.759150
- phaseC(sqlite-a) host_pages=8183704 gc_pages=5023271 WAF=1.613814
- phaseC-load host_pages=1398351 gc_pages=454675 WAF=1.325151
- phaseC-run host_pages=6785353 gc_pages=4568596 WAF=1.673303
- ycsb-load [OVERALL], Throughput(ops/sec), 19488.112251526567
- ycsb-run [OVERALL], Throughput(ops/sec), 7842.1838913700685

### mix-20260911 mixH arm17 — started 2026-10-01T11:26:57+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm17.ko`.
- Command: `bash script/mix-20260911.sh mixH arm17`; evidence `result/mix-20260911/mixH-arm17/`.

- Finished 2026-10-01T11:54:44+09:00; mixH arm17 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-arm17-rep1`; cleanup attempted.
- total host_bytes=156258791424 host_pages=38149119 gc_pages=28825737 WAF=1.755607
- phaseA(test3) host_pages=6000418 gc_pages=4954268 WAF=1.825654
- phaseB(test4) host_pages=24000667 gc_pages=20047159 WAF=1.835275
- phaseC(sqlite-a) host_pages=8148034 gc_pages=3824310 WAF=1.469354
- phaseC-load host_pages=1398351 gc_pages=397514 WAF=1.284273
- phaseC-run host_pages=6749683 gc_pages=3426796 WAF=1.507697
- ycsb-load [OVERALL], Throughput(ops/sec), 20979.75453687192
- ycsb-run [OVERALL], Throughput(ops/sec), 11911.994186946837

### mix-20260911 mixH arm16 — started 2026-10-01T11:54:53+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm16.ko`.
- Command: `bash script/mix-20260911.sh mixH arm16`; evidence `result/mix-20260911/mixH-arm16/`.

- Finished 2026-10-01T12:24:47+09:00; mixH arm16 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-arm16-rep1`; cleanup attempted.
- total host_bytes=155998478336 host_pages=38085566 gc_pages=29112894 WAF=1.764408
- phaseA(test3) host_pages=6000421 gc_pages=4936995 WAF=1.822775
- phaseB(test4) host_pages=24000658 gc_pages=19234317 WAF=1.801408
- phaseC(sqlite-a) host_pages=8084487 gc_pages=4941582 WAF=1.611242
- phaseC-load host_pages=1398349 gc_pages=753575 WAF=1.538903
- phaseC-run host_pages=6686138 gc_pages=4188007 WAF=1.626372
- ycsb-load [OVERALL], Throughput(ops/sec), 20652.622883106156
- ycsb-run [OVERALL], Throughput(ops/sec), 8522.860442421686

### mix-20260911 mixH arm15 — started 2026-10-01T12:24:54+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm15.ko`.
- Command: `bash script/mix-20260911.sh mixH arm15`; evidence `result/mix-20260911/mixH-arm15/`.

- Finished 2026-10-01T12:54:54+09:00; mixH arm15 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-arm15-rep1`; cleanup attempted.
- total host_bytes=156063379456 host_pages=38101411 gc_pages=31297726 WAF=1.821432
- phaseA(test3) host_pages=6000418 gc_pages=4948248 WAF=1.824651
- phaseB(test4) host_pages=24000658 gc_pages=20205510 WAF=1.841873
- phaseC(sqlite-a) host_pages=8100335 gc_pages=6143968 WAF=1.758483
- phaseC-load host_pages=1398345 gc_pages=1066548 WAF=1.762722
- phaseC-run host_pages=6701990 gc_pages=5077420 WAF=1.757599
- ycsb-load [OVERALL], Throughput(ops/sec), 21803.117845851957
- ycsb-run [OVERALL], Throughput(ops/sec), 8465.393471488554

### mix-20260911 mixH arm30 — started 2026-10-01T12:55:01+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm30.ko`.
- Command: `bash script/mix-20260911.sh mixH arm30`; evidence `result/mix-20260911/mixH-arm30/`.

- Finished 2026-10-01T13:22:38+09:00; mixH arm30 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-arm30-rep1`; cleanup attempted.
- total host_bytes=156123107328 host_pages=38115993 gc_pages=29897073 WAF=1.784371
- phaseA(test3) host_pages=6000430 gc_pages=4844674 WAF=1.807388
- phaseB(test4) host_pages=24000658 gc_pages=19188338 WAF=1.799492
- phaseC(sqlite-a) host_pages=8114905 gc_pages=5864061 WAF=1.722628
- phaseC-load host_pages=1398351 gc_pages=1018419 WAF=1.728300
- phaseC-run host_pages=6716554 gc_pages=4845642 WAF=1.721448
- ycsb-load [OVERALL], Throughput(ops/sec), 21189.43353581014
- ycsb-run [OVERALL], Throughput(ops/sec), 12285.729204099747

### mix-20260911 mixH arm34 — started 2026-10-01T13:22:45+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm34.ko`.
- Command: `bash script/mix-20260911.sh mixH arm34`; evidence `result/mix-20260911/mixH-arm34/`.

- Finished 2026-10-01T13:50:24+09:00; mixH arm34 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-arm34-rep1`; cleanup attempted.
- total host_bytes=156186275840 host_pages=38131415 gc_pages=29315929 WAF=1.768813
- phaseA(test3) host_pages=6000415 gc_pages=4833539 WAF=1.805534
- phaseB(test4) host_pages=24000661 gc_pages=19535962 WAF=1.813976
- phaseC(sqlite-a) host_pages=8130339 gc_pages=4946428 WAF=1.608391
- phaseC-load host_pages=1398349 gc_pages=877745 WAF=1.627701
- phaseC-run host_pages=6731990 gc_pages=4068683 WAF=1.604380
- ycsb-load [OVERALL], Throughput(ops/sec), 21414.040472536493
- ycsb-run [OVERALL], Throughput(ops/sec), 12123.930820850735

### mix-20260911 mixH arm35 — started 2026-10-01T13:50:31+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm35.ko`.
- Command: `bash script/mix-20260911.sh mixH arm35`; evidence `result/mix-20260911/mixH-arm35/`.

- Finished 2026-10-01T14:20:16+09:00; mixH arm35 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-arm35-rep1`; cleanup attempted.
- total host_bytes=155851808768 host_pages=38049758 gc_pages=27652982 WAF=1.726758
- phaseA(test3) host_pages=6000425 gc_pages=4875963 WAF=1.812603
- phaseB(test4) host_pages=24000658 gc_pages=19443022 WAF=1.810104
- phaseC(sqlite-a) host_pages=8048675 gc_pages=3333997 WAF=1.414229
- phaseC-load host_pages=1398348 gc_pages=538597 WAF=1.385167
- phaseC-run host_pages=6650327 gc_pages=2795400 WAF=1.420340
- ycsb-load [OVERALL], Throughput(ops/sec), 23292.82969059358
- ycsb-run [OVERALL], Throughput(ops/sec), 8805.374800778394

### mix-20260911 mixH arm45 — started 2026-10-01T14:20:27+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm45.ko`.
- Command: `bash script/mix-20260911.sh mixH arm45`; evidence `result/mix-20260911/mixH-arm45/`.

- Finished 2026-10-01T14:48:09+09:00; mixH arm45 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-arm45-rep1`; cleanup attempted.
- total host_bytes=156198326272 host_pages=38134357 gc_pages=29553579 WAF=1.774986
- phaseA(test3) host_pages=6000418 gc_pages=4830386 WAF=1.805008
- phaseB(test4) host_pages=24000658 gc_pages=18872833 WAF=1.786346
- phaseC(sqlite-a) host_pages=8133281 gc_pages=5850360 WAF=1.719311
- phaseC-load host_pages=1398349 gc_pages=1009140 WAF=1.721665
- phaseC-run host_pages=6734932 gc_pages=4841220 WAF=1.718822
- ycsb-load [OVERALL], Throughput(ops/sec), 21728.89580994459
- ycsb-run [OVERALL], Throughput(ops/sec), 12169.04013653663

### mix-20260911 mixH arm49 — started 2026-10-01T14:48:19+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm49.ko`.
- Command: `bash script/mix-20260911.sh mixH arm49`; evidence `result/mix-20260911/mixH-arm49/`.

- Finished 2026-10-01T15:15:58+09:00; mixH arm49 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-arm49-rep1`; cleanup attempted.
- total host_bytes=156148711424 host_pages=38122244 gc_pages=28729239 WAF=1.753608
- phaseA(test3) host_pages=6000415 gc_pages=4807305 WAF=1.801162
- phaseB(test4) host_pages=24000664 gc_pages=19059224 WAF=1.794112
- phaseC(sqlite-a) host_pages=8121165 gc_pages=4862710 WAF=1.598770
- phaseC-load host_pages=1398345 gc_pages=872512 WAF=1.623960
- phaseC-run host_pages=6722820 gc_pages=3990198 WAF=1.593530
- ycsb-load [OVERALL], Throughput(ops/sec), 20177.562550443905
- ycsb-run [OVERALL], Throughput(ops/sec), 12238.254335401598

### mix-20260911 mixH arm53 — started 2026-10-01T15:16:06+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm53.ko`.
- Command: `bash script/mix-20260911.sh mixH arm53`; evidence `result/mix-20260911/mixH-arm53/`.

- Finished 2026-10-01T15:43:36+09:00; mixH arm53 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-arm53-rep1`; cleanup attempted.
- total host_bytes=156145758208 host_pages=38121523 gc_pages=29352002 WAF=1.769959
- phaseA(test3) host_pages=6000415 gc_pages=4925560 WAF=1.820870
- phaseB(test4) host_pages=24000658 gc_pages=20074476 WAF=1.836414
- phaseC(sqlite-a) host_pages=8120450 gc_pages=4351966 WAF=1.535927
- phaseC-load host_pages=1398345 gc_pages=745343 WAF=1.533018
- phaseC-run host_pages=6722105 gc_pages=3606623 WAF=1.536532
- ycsb-load [OVERALL], Throughput(ops/sec), 23457.65892563922
- ycsb-run [OVERALL], Throughput(ops/sec), 12359.373503357116

### mix-20260911 mixH arm56 — started 2026-10-01T15:43:42+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm56.ko`.
- Command: `bash script/mix-20260911.sh mixH arm56`; evidence `result/mix-20260911/mixH-arm56/`.

- Finished 2026-10-01T16:11:16+09:00; mixH arm56 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-arm56-rep1`; cleanup attempted.
- total host_bytes=156181405696 host_pages=38130226 gc_pages=33472604 WAF=1.877850
- phaseA(test3) host_pages=6007064 gc_pages=5074478 WAF=1.844752
- phaseB(test4) host_pages=24000664 gc_pages=22987306 WAF=1.957778
- phaseC(sqlite-a) host_pages=8122498 gc_pages=5410820 WAF=1.666152
- phaseC-load host_pages=1398349 gc_pages=1209040 WAF=1.864620
- phaseC-run host_pages=6724149 gc_pages=4201780 WAF=1.624879
- ycsb-load [OVERALL], Throughput(ops/sec), 22946.305644791188
- ycsb-run [OVERALL], Throughput(ops/sec), 12266.100790550196

### mix-20260911 mixG arm46 — started 2026-10-01T16:11:38+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm46.ko`.
- Command: `bash script/mix-20260911.sh mixG arm46`; evidence `result/mix-20260911/mixG-arm46/`.

- Finished 2026-10-01T16:22:02+09:00; mixG arm46 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-arm46-rep1`; cleanup attempted.
- total host_bytes=84385259520 host_pages=20601870 gc_pages=40449399 WAF=2.963385
- phaseA(concurrent-test4+sqlite-a) host_pages=20601870 gc_pages=40449399 WAF=2.963385
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG arm31 — started 2026-10-01T16:22:16+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm31.ko`.
- Command: `bash script/mix-20260911.sh mixG arm31`; evidence `result/mix-20260911/mixG-arm31/`.

- Finished 2026-10-01T16:32:38+09:00; mixG arm31 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-arm31-rep1`; cleanup attempted.
- total host_bytes=84331245568 host_pages=20588683 gc_pages=44298389 WAF=3.151589
- phaseA(concurrent-test4+sqlite-a) host_pages=20588683 gc_pages=44298389 WAF=3.151589
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG arm32 — started 2026-10-01T16:32:45+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm32.ko`.
- Command: `bash script/mix-20260911.sh mixG arm32`; evidence `result/mix-20260911/mixG-arm32/`.

- Finished 2026-10-01T16:43:00+09:00; mixG arm32 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-arm32-rep1`; cleanup attempted.
- total host_bytes=84200640512 host_pages=20556797 gc_pages=40944625 WAF=2.991780
- phaseA(concurrent-test4+sqlite-a) host_pages=20556797 gc_pages=40944625 WAF=2.991780
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG arm17 — started 2026-10-01T16:43:08+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm17.ko`.
- Command: `bash script/mix-20260911.sh mixG arm17`; evidence `result/mix-20260911/mixG-arm17/`.

- Finished 2026-10-01T16:55:45+09:00; mixG arm17 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-arm17-rep1`; cleanup attempted.
- total host_bytes=83551440896 host_pages=20398301 gc_pages=44004881 WAF=3.157282
- phaseA(concurrent-test4+sqlite-a) host_pages=20398301 gc_pages=44004881 WAF=3.157282
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG arm16 — started 2026-10-01T16:55:56+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm16.ko`.
- Command: `bash script/mix-20260911.sh mixG arm16`; evidence `result/mix-20260911/mixG-arm16/`.

- Finished 2026-10-01T17:06:23+09:00; mixG arm16 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-arm16-rep1`; cleanup attempted.
- total host_bytes=84377493504 host_pages=20599974 gc_pages=49271466 WAF=3.391822
- phaseA(concurrent-test4+sqlite-a) host_pages=20599974 gc_pages=49271466 WAF=3.391822
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG arm15 — started 2026-10-01T17:06:32+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm15.ko`.
- Command: `bash script/mix-20260911.sh mixG arm15`; evidence `result/mix-20260911/mixG-arm15/`.

- Finished 2026-10-01T17:17:07+09:00; mixG arm15 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-arm15-rep1`; cleanup attempted.
- total host_bytes=84451418112 host_pages=20618022 gc_pages=51407056 WAF=3.493307
- phaseA(concurrent-test4+sqlite-a) host_pages=20618022 gc_pages=51407056 WAF=3.493307
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG arm30 — started 2026-10-01T17:17:18+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm30.ko`.
- Command: `bash script/mix-20260911.sh mixG arm30`; evidence `result/mix-20260911/mixG-arm30/`.

- Finished 2026-10-01T17:28:06+09:00; mixG arm30 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-arm30-rep1`; cleanup attempted.
- total host_bytes=84549197824 host_pages=20641894 gc_pages=48195381 WAF=3.334833
- phaseA(concurrent-test4+sqlite-a) host_pages=20641894 gc_pages=48195381 WAF=3.334833
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG arm34 — started 2026-10-01T17:28:15+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm34.ko`.
- Command: `bash script/mix-20260911.sh mixG arm34`; evidence `result/mix-20260911/mixG-arm34/`.

- Finished 2026-10-01T17:41:07+09:00; mixG arm34 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-arm34-rep1`; cleanup attempted.
- total host_bytes=83833540608 host_pages=20467173 gc_pages=45660855 WAF=3.230931
- phaseA(concurrent-test4+sqlite-a) host_pages=20467173 gc_pages=45660855 WAF=3.230931
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG arm35 — started 2026-10-01T17:41:15+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm35.ko`.
- Command: `bash script/mix-20260911.sh mixG arm35`; evidence `result/mix-20260911/mixG-arm35/`.

- Finished 2026-10-01T17:51:36+09:00; mixG arm35 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-arm35-rep1`; cleanup attempted.
- total host_bytes=84318289920 host_pages=20585520 gc_pages=48613729 WAF=3.361550
- phaseA(concurrent-test4+sqlite-a) host_pages=20585520 gc_pages=48613729 WAF=3.361550
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG arm45 — started 2026-10-01T17:51:44+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm45.ko`.
- Command: `bash script/mix-20260911.sh mixG arm45`; evidence `result/mix-20260911/mixG-arm45/`.

- Finished 2026-10-01T18:04:37+09:00; mixG arm45 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-arm45-rep1`; cleanup attempted.
- total host_bytes=83788607488 host_pages=20456203 gc_pages=42559073 WAF=3.080497
- phaseA(concurrent-test4+sqlite-a) host_pages=20456203 gc_pages=42559073 WAF=3.080497
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG arm49 — started 2026-10-01T18:04:44+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm49.ko`.
- Command: `bash script/mix-20260911.sh mixG arm49`; evidence `result/mix-20260911/mixG-arm49/`.

- Finished 2026-10-01T18:15:21+09:00; mixG arm49 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-arm49-rep1`; cleanup attempted.
- total host_bytes=84475424768 host_pages=20623883 gc_pages=48151734 WAF=3.334756
- phaseA(concurrent-test4+sqlite-a) host_pages=20623883 gc_pages=48151734 WAF=3.334756
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG arm53 — started 2026-10-01T18:15:28+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm53.ko`.
- Command: `bash script/mix-20260911.sh mixG arm53`; evidence `result/mix-20260911/mixG-arm53/`.

- Finished 2026-10-01T18:28:17+09:00; mixG arm53 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-arm53-rep1`; cleanup attempted.
- total host_bytes=83810902016 host_pages=20461646 gc_pages=46746254 WAF=3.284579
- phaseA(concurrent-test4+sqlite-a) host_pages=20461646 gc_pages=46746254 WAF=3.284579
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixG arm56 — started 2026-10-01T18:28:25+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 4000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm56.ko`.
- Command: `bash script/mix-20260911.sh mixG arm56`; evidence `result/mix-20260911/mixG-arm56/`.

- Finished 2026-10-01T18:39:03+09:00; mixG arm56 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixG-arm56-rep1`; cleanup attempted.
- total host_bytes=84472745984 host_pages=20623229 gc_pages=53887822 WAF=3.612967
- phaseA(concurrent-test4+sqlite-a) host_pages=20623229 gc_pages=53887822 WAF=3.612967
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL arm46 — started 2026-10-01T18:39:26+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm46.ko`.
- Command: `bash script/mix-20260911.sh mixL arm46`; evidence `result/mix-20260911/mixL-arm46/`.

- Finished 2026-10-01T18:50:54+09:00; mixL arm46 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-arm46-rep1`; cleanup attempted.
- total host_bytes=61517758464 host_pages=15018984 gc_pages=8541802 WAF=1.568734
- phaseA(alternate-fast/slow-x5) host_pages=15018984 gc_pages=8541802 WAF=1.568734
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL arm31 — started 2026-10-01T18:50:59+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm31.ko`.
- Command: `bash script/mix-20260911.sh mixL arm31`; evidence `result/mix-20260911/mixL-arm31/`.

- Finished 2026-10-01T19:02:27+09:00; mixL arm31 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-arm31-rep1`; cleanup attempted.
- total host_bytes=61442277376 host_pages=15000556 gc_pages=8565539 WAF=1.571015
- phaseA(alternate-fast/slow-x5) host_pages=15000556 gc_pages=8565539 WAF=1.571015
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL arm32 — started 2026-10-01T19:02:32+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm32.ko`.
- Command: `bash script/mix-20260911.sh mixL arm32`; evidence `result/mix-20260911/mixL-arm32/`.

- Finished 2026-10-01T19:14:00+09:00; mixL arm32 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-arm32-rep1`; cleanup attempted.
- total host_bytes=61442252800 host_pages=15000550 gc_pages=8215898 WAF=1.547706
- phaseA(alternate-fast/slow-x5) host_pages=15000550 gc_pages=8215898 WAF=1.547706
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL arm17 — started 2026-10-01T19:14:05+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm17.ko`.
- Command: `bash script/mix-20260911.sh mixL arm17`; evidence `result/mix-20260911/mixL-arm17/`.

- Finished 2026-10-01T19:25:32+09:00; mixL arm17 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-arm17-rep1`; cleanup attempted.
- total host_bytes=61442228224 host_pages=15000544 gc_pages=8792022 WAF=1.586114
- phaseA(alternate-fast/slow-x5) host_pages=15000544 gc_pages=8792022 WAF=1.586114
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL arm16 — started 2026-10-01T19:25:37+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm16.ko`.
- Command: `bash script/mix-20260911.sh mixL arm16`; evidence `result/mix-20260911/mixL-arm16/`.

- Finished 2026-10-01T19:37:05+09:00; mixL arm16 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-arm16-rep1`; cleanup attempted.
- total host_bytes=61442277376 host_pages=15000556 gc_pages=8992339 WAF=1.599467
- phaseA(alternate-fast/slow-x5) host_pages=15000556 gc_pages=8992339 WAF=1.599467
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL arm15 — started 2026-10-01T19:37:10+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm15.ko`.
- Command: `bash script/mix-20260911.sh mixL arm15`; evidence `result/mix-20260911/mixL-arm15/`.

- Finished 2026-10-01T19:48:37+09:00; mixL arm15 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-arm15-rep1`; cleanup attempted.
- total host_bytes=61496737792 host_pages=15013852 gc_pages=9758996 WAF=1.649999
- phaseA(alternate-fast/slow-x5) host_pages=15013852 gc_pages=9758996 WAF=1.649999
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL arm30 — started 2026-10-01T19:48:42+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm30.ko`.
- Command: `bash script/mix-20260911.sh mixL arm30`; evidence `result/mix-20260911/mixL-arm30/`.

- Finished 2026-10-01T20:00:11+09:00; mixL arm30 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-arm30-rep1`; cleanup attempted.
- total host_bytes=61442265088 host_pages=15000553 gc_pages=9399398 WAF=1.626603
- phaseA(alternate-fast/slow-x5) host_pages=15000553 gc_pages=9399398 WAF=1.626603
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL arm34 — started 2026-10-01T20:00:27+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm34.ko`.
- Command: `bash script/mix-20260911.sh mixL arm34`; evidence `result/mix-20260911/mixL-arm34/`.

- Finished 2026-10-01T20:11:54+09:00; mixL arm34 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-arm34-rep1`; cleanup attempted.
- total host_bytes=61442265088 host_pages=15000553 gc_pages=9142552 WAF=1.609481
- phaseA(alternate-fast/slow-x5) host_pages=15000553 gc_pages=9142552 WAF=1.609481
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL arm35 — started 2026-10-01T20:12:00+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm35.ko`.
- Command: `bash script/mix-20260911.sh mixL arm35`; evidence `result/mix-20260911/mixL-arm35/`.

- Finished 2026-10-01T20:23:27+09:00; mixL arm35 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-arm35-rep1`; cleanup attempted.
- total host_bytes=61442228224 host_pages=15000544 gc_pages=8826409 WAF=1.588406
- phaseA(alternate-fast/slow-x5) host_pages=15000544 gc_pages=8826409 WAF=1.588406
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL arm45 — started 2026-10-01T20:23:32+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm45.ko`.
- Command: `bash script/mix-20260911.sh mixL arm45`; evidence `result/mix-20260911/mixL-arm45/`.

- Finished 2026-10-01T20:35:00+09:00; mixL arm45 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-arm45-rep1`; cleanup attempted.
- total host_bytes=61507264512 host_pages=15016422 gc_pages=9253539 WAF=1.616228
- phaseA(alternate-fast/slow-x5) host_pages=15016422 gc_pages=9253539 WAF=1.616228
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL arm49 — started 2026-10-01T20:35:05+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm49.ko`.
- Command: `bash script/mix-20260911.sh mixL arm49`; evidence `result/mix-20260911/mixL-arm49/`.

- Finished 2026-10-01T20:46:32+09:00; mixL arm49 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-arm49-rep1`; cleanup attempted.
- total host_bytes=61492539392 host_pages=15012827 gc_pages=8930615 WAF=1.594866
- phaseA(alternate-fast/slow-x5) host_pages=15012827 gc_pages=8930615 WAF=1.594866
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL arm53 — started 2026-10-01T20:46:37+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm53.ko`.
- Command: `bash script/mix-20260911.sh mixL arm53`; evidence `result/mix-20260911/mixL-arm53/`.

- Finished 2026-10-01T20:58:04+09:00; mixL arm53 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-arm53-rep1`; cleanup attempted.
- total host_bytes=61442228224 host_pages=15000544 gc_pages=9270460 WAF=1.618008
- phaseA(alternate-fast/slow-x5) host_pages=15000544 gc_pages=9270460 WAF=1.618008
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixL arm56 — started 2026-10-01T20:58:09+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm56.ko`.
- Command: `bash script/mix-20260911.sh mixL arm56`; evidence `result/mix-20260911/mixL-arm56/`.

- Finished 2026-10-01T21:09:37+09:00; mixL arm56 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixL-arm56-rep1`; cleanup attempted.
- total host_bytes=61442240512 host_pages=15000547 gc_pages=10039584 WAF=1.669281
- phaseA(alternate-fast/slow-x5) host_pages=15000547 gc_pages=10039584 WAF=1.669281
- phaseB(none) host_pages=0 gc_pages=0 WAF=N/A
- phaseB-load host_pages=0 gc_pages=0 WAF=N/A
- phaseB-run host_pages=0 gc_pages=0 WAF=N/A
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ arm46 — started 2026-10-01T21:09:54+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm46.ko`.
- Command: `bash script/mix-20260911.sh mixQ arm46`; evidence `result/mix-20260911/mixQ-arm46/`.

- Finished 2026-10-01T21:26:19+09:00; mixQ arm46 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-arm46-rep1`; cleanup attempted.
- total host_bytes=98306748416 host_pages=24000671 gc_pages=17967238 WAF=1.748614
- phaseA(test4) host_pages=12000340 gc_pages=9398915 WAF=1.783221
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000331 gc_pages=8568323 WAF=1.714007
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ arm31 — started 2026-10-01T21:26:24+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm31.ko`.
- Command: `bash script/mix-20260911.sh mixQ arm31`; evidence `result/mix-20260911/mixQ-arm31/`.

- Finished 2026-10-01T21:42:49+09:00; mixQ arm31 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-arm31-rep1`; cleanup attempted.
- total host_bytes=98306711552 host_pages=24000662 gc_pages=18255816 WAF=1.760638
- phaseA(test4) host_pages=12000331 gc_pages=9546777 WAF=1.795543
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000331 gc_pages=8709039 WAF=1.725733
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ arm32 — started 2026-10-01T21:42:54+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm32.ko`.
- Command: `bash script/mix-20260911.sh mixQ arm32`; evidence `result/mix-20260911/mixQ-arm32/`.

- Finished 2026-10-01T21:59:19+09:00; mixQ arm32 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-arm32-rep1`; cleanup attempted.
- total host_bytes=98306711552 host_pages=24000662 gc_pages=18210413 WAF=1.758746
- phaseA(test4) host_pages=12000331 gc_pages=9568294 WAF=1.797336
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000331 gc_pages=8642119 WAF=1.720157
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ arm17 — started 2026-10-01T21:59:24+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm17.ko`.
- Command: `bash script/mix-20260911.sh mixQ arm17`; evidence `result/mix-20260911/mixQ-arm17/`.

- Finished 2026-10-01T22:15:49+09:00; mixQ arm17 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-arm17-rep1`; cleanup attempted.
- total host_bytes=98306711552 host_pages=24000662 gc_pages=20253287 WAF=1.843864
- phaseA(test4) host_pages=12000331 gc_pages=10487118 WAF=1.873902
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000331 gc_pages=9766169 WAF=1.813825
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ arm16 — started 2026-10-01T22:15:54+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm16.ko`.
- Command: `bash script/mix-20260911.sh mixQ arm16`; evidence `result/mix-20260911/mixQ-arm16/`.

- Finished 2026-10-01T22:32:19+09:00; mixQ arm16 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-arm16-rep1`; cleanup attempted.
- total host_bytes=98306711552 host_pages=24000662 gc_pages=19240723 WAF=1.801675
- phaseA(test4) host_pages=12000331 gc_pages=9969807 WAF=1.830794
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000331 gc_pages=9270916 WAF=1.772555
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ arm15 — started 2026-10-01T22:32:25+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm15.ko`.
- Command: `bash script/mix-20260911.sh mixQ arm15`; evidence `result/mix-20260911/mixQ-arm15/`.

- Finished 2026-10-01T22:48:50+09:00; mixQ arm15 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-arm15-rep1`; cleanup attempted.
- total host_bytes=98306736128 host_pages=24000668 gc_pages=19768819 WAF=1.823678
- phaseA(test4) host_pages=12000331 gc_pages=10385723 WAF=1.865453
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000337 gc_pages=9383096 WAF=1.781903
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ arm30 — started 2026-10-01T22:48:55+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm30.ko`.
- Command: `bash script/mix-20260911.sh mixQ arm30`; evidence `result/mix-20260911/mixQ-arm30/`.

- Finished 2026-10-01T23:05:20+09:00; mixQ arm30 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-arm30-rep1`; cleanup attempted.
- total host_bytes=98306711552 host_pages=24000662 gc_pages=19052181 WAF=1.793819
- phaseA(test4) host_pages=12000331 gc_pages=10009224 WAF=1.834079
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000331 gc_pages=9042957 WAF=1.753559
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ arm34 — started 2026-10-01T23:05:25+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm34.ko`.
- Command: `bash script/mix-20260911.sh mixQ arm34`; evidence `result/mix-20260911/mixQ-arm34/`.

- Finished 2026-10-01T23:21:50+09:00; mixQ arm34 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-arm34-rep1`; cleanup attempted.
- total host_bytes=98306723840 host_pages=24000665 gc_pages=19381442 WAF=1.807538
- phaseA(test4) host_pages=12000334 gc_pages=10135793 WAF=1.844626
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000331 gc_pages=9245649 WAF=1.770449
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ arm35 — started 2026-10-01T23:21:55+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm35.ko`.
- Command: `bash script/mix-20260911.sh mixQ arm35`; evidence `result/mix-20260911/mixQ-arm35/`.

- Finished 2026-10-01T23:38:20+09:00; mixQ arm35 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-arm35-rep1`; cleanup attempted.
- total host_bytes=98306711552 host_pages=24000662 gc_pages=19803543 WAF=1.825125
- phaseA(test4) host_pages=12000331 gc_pages=10174988 WAF=1.847892
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000331 gc_pages=9628555 WAF=1.802357
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ arm45 — started 2026-10-01T23:38:25+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm45.ko`.
- Command: `bash script/mix-20260911.sh mixQ arm45`; evidence `result/mix-20260911/mixQ-arm45/`.

- Finished 2026-10-01T23:54:50+09:00; mixQ arm45 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-arm45-rep1`; cleanup attempted.
- total host_bytes=98306760704 host_pages=24000674 gc_pages=18775675 WAF=1.782298
- phaseA(test4) host_pages=12000343 gc_pages=9846458 WAF=1.820515
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000331 gc_pages=8929217 WAF=1.744081
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ arm49 — started 2026-10-01T23:54:55+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm49.ko`.
- Command: `bash script/mix-20260911.sh mixQ arm49`; evidence `result/mix-20260911/mixQ-arm49/`.

- Finished 2026-10-02T00:11:19+09:00; mixQ arm49 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-arm49-rep1`; cleanup attempted.
- total host_bytes=98306785280 host_pages=24000680 gc_pages=19044749 WAF=1.793509
- phaseA(test4) host_pages=12000331 gc_pages=9932710 WAF=1.827703
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000349 gc_pages=9112039 WAF=1.759314
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ arm53 — started 2026-10-02T00:11:24+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm53.ko`.
- Command: `bash script/mix-20260911.sh mixQ arm53`; evidence `result/mix-20260911/mixQ-arm53/`.

- Finished 2026-10-02T00:27:50+09:00; mixQ arm53 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-arm53-rep1`; cleanup attempted.
- total host_bytes=98306736128 host_pages=24000668 gc_pages=20349917 WAF=1.847890
- phaseA(test4) host_pages=12000337 gc_pages=10580547 WAF=1.881687
- phaseB(idle-300s) host_pages=0 gc_pages=0 WAF=N/A
- phaseC(test4) host_pages=12000331 gc_pages=9769370 WAF=1.814092
- ycsb-load 
- ycsb-run 

### mix-20260911 mixQ arm56 — started 2026-10-02T00:27:55+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm56.ko`.
- Command: `bash script/mix-20260911.sh mixQ arm56`; evidence `result/mix-20260911/mixQ-arm56/`.

- Finished 2026-10-02T00:44:20+09:00; mixQ arm56 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixQ-arm56-rep1`; cleanup attempted.
- total host_bytes=98413858816 host_pages=24026821 gc_pages=21889230 WAF=1.911033
- phaseA(test4) host_pages=12017233 gc_pages=11550696 WAF=1.961178
- phaseB(idle-300s) host_pages=9257 gc_pages=6592 WAF=1.712110
- phaseC(test4) host_pages=12000331 gc_pages=10331942 WAF=1.860971
- ycsb-load 
- ycsb-run 

### mix-20260911 mixO arm16 — started 2026-10-02T00:44:36+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm16.ko`.
- Command: `bash script/mix-20260911.sh mixO arm16`; evidence `result/mix-20260911/mixO-arm16/`.

- Finished 2026-10-02T01:16:11+09:00; mixO arm16 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixO-arm16-rep1-x3`; cleanup attempted.
- total host_bytes=723569274880 host_pages=176652655 gc_pages=210291418 WAF=2.190423
- phaseA(oltp) host_pages=26076105 gc_pages=7976886 WAF=1.305908
- phaseB(varmail) host_pages=150576550 gc_pages=202314532 WAF=2.343599
- ycsb-load 
- ycsb-run 

### mix-20260911 mixF arm32 — started 2026-10-02T01:16:27+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm32.ko`.
- Command: `bash script/mix-20260911.sh mixF arm32`; evidence `result/mix-20260911/mixF-arm32/`.

- Finished 2026-10-02T02:02:56+09:00; mixF arm32 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixF-arm32-rep1-x3`; cleanup attempted.
- total host_bytes=838396157952 host_pages=204686562 gc_pages=280363965 WAF=2.369723
- phaseA(test4) host_pages=72001990 gc_pages=57260421 WAF=1.795262
- phaseB(varmail) host_pages=132684572 gc_pages=223103544 WAF=2.681458
- ycsb-load 
- ycsb-run 

### mix-20260911 mixJ arm35 — started 2026-10-02T02:03:09+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm35.ko`.
- Command: `bash script/mix-20260911.sh mixJ arm35`; evidence `result/mix-20260911/mixJ-arm35/`.

- Finished 2026-10-02T02:24:57+09:00; mixJ arm35 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-arm35-rep1-x3`; cleanup attempted.
- total host_bytes=96985649152 host_pages=23678137 gc_pages=8129052 WAF=1.343315
- phaseA(sqlite-a) host_pages=21593608 gc_pages=7665287 WAF=1.354979
- phaseB(sqlite-b) host_pages=2084529 gc_pages=463765 WAF=1.222480
- phaseA-load host_pages=1398339 gc_pages=404206 WAF=1.289062
- phaseA-run host_pages=20195269 gc_pages=7261081 WAF=1.359544
- ycsb-load [OVERALL], Throughput(ops/sec), 26561.600779140288
- ycsb-run [OVERALL], Throughput(ops/sec), 66543.19207692394

### mix-20260911 mixJ arm53 — started 2026-10-02T02:25:06+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm53.ko`.
- Command: `bash script/mix-20260911.sh mixJ arm53`; evidence `result/mix-20260911/mixJ-arm53/`.

- Finished 2026-10-02T02:46:35+09:00; mixJ arm53 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixJ-arm53-rep1-x3`; cleanup attempted.
- total host_bytes=97068986368 host_pages=23698483 gc_pages=9156617 WAF=1.386380
- phaseA(sqlite-a) host_pages=21594090 gc_pages=8550640 WAF=1.395971
- phaseB(sqlite-b) host_pages=2104393 gc_pages=605977 WAF=1.287958
- phaseA-load host_pages=1401925 gc_pages=413530 WAF=1.294973
- phaseA-run host_pages=20192165 gc_pages=8137110 WAF=1.402984
- ycsb-load [OVERALL], Throughput(ops/sec), 25276.99372287989
- ycsb-run [OVERALL], Throughput(ops/sec), 63591.319784849366

### mix-20260911 mixP arm32 — started 2026-10-02T02:46:54+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (250000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm32.ko`.
- Command: `bash script/mix-20260911.sh mixP arm32`; evidence `result/mix-20260911/mixP-arm32/`.

- Finished 2026-10-02T03:07:16+09:00; mixP arm32 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixP-arm32-rep1-x3`; cleanup attempted.
- total host_bytes=112453828608 host_pages=27454548 gc_pages=3336542 WAF=1.121530
- phaseA(sqlite-a) host_pages=1149524 gc_pages=211382 WAF=1.183887
- phaseB(oltp) host_pages=26305024 gc_pages=3125160 WAF=1.118805
- phaseA-load host_pages=452310 gc_pages=124334 WAF=1.274887
- phaseA-run host_pages=697214 gc_pages=87048 WAF=1.124851
- ycsb-load [OVERALL], Throughput(ops/sec), 28551.85015989036
- ycsb-run [OVERALL], Throughput(ops/sec), 61554.244678122595

### mix-20260911 mixB fixed47 — started 2026-10-02T03:07:38+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixB fixed47`; evidence `result/mix-20260911/mixB-fixed47/`.

- Finished 2026-10-02T04:01:48+09:00; mixB fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-fixed47-rep1-x3`; cleanup attempted.
- total host_bytes=382633693184 host_pages=93416429 gc_pages=138954703 WAF=2.487476
- phaseA(sqlite-a) host_pages=21414445 gc_pages=10149173 WAF=1.473941
- phaseB(test4) host_pages=72001984 gc_pages=128805530 WAF=2.788916
- phaseA-load host_pages=1398349 gc_pages=365280 WAF=1.261222
- phaseA-run host_pages=20016096 gc_pages=9783893 WAF=1.488801
- ycsb-load [OVERALL], Throughput(ops/sec), 21881.83807439825
- ycsb-run [OVERALL], Throughput(ops/sec), 9099.360466615204

### mix-20260911 mixB arm31 — started 2026-10-02T04:01:55+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm31.ko`.
- Command: `bash script/mix-20260911.sh mixB arm31`; evidence `result/mix-20260911/mixB-arm31/`.

- Finished 2026-10-02T04:56:09+09:00; mixB arm31 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-arm31-rep1-x3`; cleanup attempted.
- total host_bytes=382805803008 host_pages=93458448 gc_pages=154256069 WAF=2.650531
- phaseA(sqlite-a) host_pages=21456458 gc_pages=11148027 WAF=1.519565
- phaseB(test4) host_pages=72001990 gc_pages=143108042 WAF=2.987557
- phaseA-load host_pages=1398339 gc_pages=460940 WAF=1.329634
- phaseA-run host_pages=20058119 gc_pages=10687087 WAF=1.532806
- ycsb-load [OVERALL], Throughput(ops/sec), 24320.05188277735
- ycsb-run [OVERALL], Throughput(ops/sec), 9004.12163667919

### mix-20260911 mixB arm32 — started 2026-10-02T04:56:15+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm32.ko`.
- Command: `bash script/mix-20260911.sh mixB arm32`; evidence `result/mix-20260911/mixB-arm32/`.

- Finished 2026-10-02T05:50:41+09:00; mixB arm32 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixB-arm32-rep1-x3`; cleanup attempted.
- total host_bytes=382920871936 host_pages=93486541 gc_pages=143510916 WAF=2.535097
- phaseA(sqlite-a) host_pages=21484551 gc_pages=9496525 WAF=1.442016
- phaseB(test4) host_pages=72001990 gc_pages=134014391 WAF=2.861260
- phaseA-load host_pages=1402432 gc_pages=377798 WAF=1.269388
- phaseA-run host_pages=20082119 gc_pages=9118727 WAF=1.454072
- ycsb-load [OVERALL], Throughput(ops/sec), 26967.504157490224
- ycsb-run [OVERALL], Throughput(ops/sec), 8980.9805284858

### mix-20260911 mixD fixed47 — started 2026-10-02T05:50:57+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixD fixed47`; evidence `result/mix-20260911/mixD-fixed47/`.

- Finished 2026-10-02T06:52:23+09:00; mixD fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-fixed47-rep1-x3`; cleanup attempted.
- total host_bytes=368653299712 host_pages=90003247 gc_pages=69170672 WAF=1.768535
- phaseA(test4) host_pages=72002002 gc_pages=55519595 WAF=1.771084
- phaseB(test3) host_pages=18001245 gc_pages=13651077 WAF=1.758341
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD arm46 — started 2026-10-02T06:52:28+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm46.ko`.
- Command: `bash script/mix-20260911.sh mixD arm46`; evidence `result/mix-20260911/mixD-arm46/`.

- Finished 2026-10-02T07:53:54+09:00; mixD arm46 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-arm46-rep1-x3`; cleanup attempted.
- total host_bytes=368653238272 host_pages=90003232 gc_pages=70368990 WAF=1.781850
- phaseA(test4) host_pages=72001984 gc_pages=56534609 WAF=1.785181
- phaseB(test3) host_pages=18001248 gc_pages=13834381 WAF=1.768523
- ycsb-load 
- ycsb-run 

### mix-20260911 mixD arm32 — started 2026-10-02T07:53:59+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm32.ko`.
- Command: `bash script/mix-20260911.sh mixD arm32`; evidence `result/mix-20260911/mixD-arm32/`.

- Finished 2026-10-02T08:55:24+09:00; mixD arm32 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixD-arm32-rep1-x3`; cleanup attempted.
- total host_bytes=368730816512 host_pages=90022172 gc_pages=71003437 WAF=1.788733
- phaseA(test4) host_pages=72020930 gc_pages=57183689 WAF=1.793987
- phaseB(test3) host_pages=18001242 gc_pages=13819748 WAF=1.767711
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK fixed47 — started 2026-10-02T08:55:38+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixK fixed47`; evidence `result/mix-20260911/mixK-fixed47/`.

- Finished 2026-10-02T09:57:03+09:00; mixK fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-fixed47-rep1-x3`; cleanup attempted.
- total host_bytes=589848363008 host_pages=144005948 gc_pages=111693463 WAF=1.775617
- phaseA(test4-hot512M) host_pages=72001981 gc_pages=55753701 WAF=1.774336
- phaseB(test4-hot128M) host_pages=72003967 gc_pages=55939762 WAF=1.776898
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK arm31 — started 2026-10-02T09:57:08+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm31.ko`.
- Command: `bash script/mix-20260911.sh mixK arm31`; evidence `result/mix-20260911/mixK-arm31/`.

- Finished 2026-10-02T10:58:34+09:00; mixK arm31 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-arm31-rep1-x3`; cleanup attempted.
- total host_bytes=589848473600 host_pages=144005975 gc_pages=113273291 WAF=1.786587
- phaseA(test4-hot512M) host_pages=72001993 gc_pages=57469883 WAF=1.798171
- phaseB(test4-hot128M) host_pages=72003982 gc_pages=55803408 WAF=1.775004
- ycsb-load 
- ycsb-run 

### mix-20260911 mixK arm46 — started 2026-10-02T10:58:39+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm46.ko`.
- Command: `bash script/mix-20260911.sh mixK arm46`; evidence `result/mix-20260911/mixK-arm46/`.

- Finished 2026-10-02T12:00:05+09:00; mixK arm46 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixK-arm46-rep1-x3`; cleanup attempted.
- total host_bytes=589936570368 host_pages=144027483 gc_pages=112818004 WAF=1.783309
- phaseA(test4-hot512M) host_pages=72023522 gc_pages=56440339 WAF=1.783638
- phaseB(test4-hot128M) host_pages=72003961 gc_pages=56377665 WAF=1.782980
- ycsb-load 
- ycsb-run 

### mix-20260911 mixH fixed47 — started 2026-10-02T12:00:20+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-varmail-20260908-fixed47.ko`.
- Command: `bash script/mix-20260911.sh mixH fixed47`; evidence `result/mix-20260911/mixH-fixed47/`.

- Finished 2026-10-02T13:24:43+09:00; mixH fixed47 exit=0; evidence `/home/oy/iCAT/result/mix-20260911/mixH-fixed47-rep1-x3`; cleanup attempted.
- total host_bytes=456631812096 host_pages=111482376 gc_pages=80332052 WAF=1.720581
- phaseA(test3) host_pages=18001255 gc_pages=13787226 WAF=1.765904
- phaseB(test4) host_pages=72001986 gc_pages=55402516 WAF=1.769458
- phaseC(sqlite-a) host_pages=21479135 gc_pages=11142310 WAF=1.518750
- phaseC-load host_pages=1398339 gc_pages=302017 WAF=1.215983
- phaseC-run host_pages=20080796 gc_pages=10840293 WAF=1.539834
- ycsb-load [OVERALL], Throughput(ops/sec), 25215.381382643413
- ycsb-run [OVERALL], Throughput(ops/sec), 8956.85483028253

### mix-20260911 mixH arm46 — started 2026-10-02T13:24:50+09:00

- Phase A fio test4 fixed payload (176947200000/88473600000/29491200000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (600000 records, 12000000 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm46.ko`.
- Command: `bash script/mix-20260911.sh mixH arm46`; evidence `result/mix-20260911/mixH-arm46/`.

## QUEUE33 — 고정 CAT 60개 전체 순위 (두 번째 컴퓨터) — 사전 등록 2026-10-02

- 목적: 11개 전환 워크로드(O F J P B D K H G L Q)마다 고정 CAT 60개 전체의 WAF 순위를 구해, 워크로드별 실제 1등과 iCAT-v4의 순위를 "60개 중 몇 등"으로 보고한다. ("CAT-Best=47번"이라는 이름의 근거가 빠른 3영역 한 워크로드뿐이라는 사용자 지적에 따름.)
- 명령: `script/gh-queue33-fullsweep.sh` (1단계 arm00–59 × 1배, 2단계 워크로드별 상위 5개 × 3배 MULT=3 VM_RUN=900). 결과는 브랜치 icat-2, run마다 HOST.txt.
- 고정 조건: 원래 컴퓨터와 같은 커널 7.0.0-31, 같은 소스·빌드 스크립트(build-all-modules.sh), 같은 구간 지정 계측(mix-20260911.sh).
- 컴퓨터 간 동일성 판정(사전 등록):
  1. `validate-new-machine.sh` PASS (3개 정책 모두 원래 값 ±1% 이내) — 미통과 시 큐를 돌리지 않는다.
  2. 원래 컴퓨터에서 이미 잰 arm(13개 + 37/47/50)을 새 컴퓨터도 다시 잰다. 겹치는 arm에서 WAF 차이 중앙값이 ±1% 이내이고 워크로드별 순위 상관(Spearman)이 0.9 이상이면 두 컴퓨터 결과를 합친다. 아니면 새 컴퓨터 결과만으로 순위를 보고한다.
- 1배→3배 순위 유지 판정: 2단계에서 1배·3배 둘 다 있는 arm의 Spearman ≥ 0.8이면 "1배 순위로 60개 전체 순위를 매긴다"를 채택, 아니면 3배로 잰 상위 5개 안에서만 순위를 보고한다.
- v4의 순위: 3배 길이 v4(1~3회 평균)를 3배로 잰 고정 arm들과만 비교한다. 1배 고정값과 3배 v4를 직접 비교하지 않는다.

### QUEUE33 정정 2026-10-02 (시작 전, 원래 등록 내용은 위에 보존)
- 두 번째 PC에서 Codex가 시작 전 중단·보고: (1) 실행 스크립트가 `/dev/nvme0n1`을 고정 사용 — 그 PC에서는 실제 SSD(가상 SSD는 nvme1n1). `set -e` + `grep CSL_Virt nvme0/model` 검사가 mkfs 전에 있어 실제 SSD 포맷은 일어나지 않았을 것이나, 고정 경로 자체를 제거함. (2) 원래 PC 결과 디렉터리를 공유해 겹치는 17개 arm을 건너뛰어 사전 등록한 교차 확인이 불가능 → 결과 경로를 `result/icat2-fullsweep/`로 분리. (3) 미완료 run 디렉터리 삭제 → 이름 변경으로 보존. (4) `git add -A` → 결과 경로만.
- 실행 스크립트 변경: `mix-20260911.sh`(가상 SSD를 모델명으로 탐지, `MIX_BASE`·`MIX_JOURNAL` 환경변수), `gh-fio.sh`, `gh-filebench.sh`(DEVICE를 모듈 적재 후 탐지). 이 PC(가상 SSD = nvme0)에서는 동작 동일 — 다음 queue31 run에서 확인.
- 판정 기준·대상·횟수는 변경 없음.
