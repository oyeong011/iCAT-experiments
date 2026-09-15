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
