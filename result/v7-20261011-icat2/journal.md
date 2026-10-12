
## 두 번째 PC v7 실행 — 사전 등록 2026-10-12T13:52:29.413898+09:00

- Run ID: `v7-20261011-icat2`. 목적: 같은 호스트 CAT60 90분 분포에 v7의 누적 WAF를 배치하고, mixY의 FIO-Slow 구간에서 파티션별 판정 횟수를 확인한다. 각 조건 1회이며 일반적인 통계적 우열로 확대하지 않는다.
- 선행 조건: CAT60 resume-20261011의 arm29 종료 및 push=0, 캠페인 최종 push=0, 정상 할당 완료 상태, 서비스 종료, 공통 device.lock 획득, 기존 module/mount 없음. CAT60 중 장치·모듈·실행 러너 변경 금지. 기존 러너는 이후에도 보존하고 캠페인 전용 복사본만 생성한다.
- 소스: `d6698f591185eca302fbfe38798b899978f50a7d`의 online-v7-src, gh-queue54-v7.sh, mixY 러너/순서/원본 사전 등록을 inputs에 보존. origin/main fetch 당시 `daac0b88815ac165402cb84c9a8929a8f7847259`. 작업 트리 HEAD `c06a372a5e940f911734946f1ffd574d2bdd7ca8`, 로컬 변경은 source-status.txt에 기록. 전체 pull/reset으로 진행 중 입력을 바꾸지 않는다.
- v6 대비 변경: conv_ftl.c/h 두 파일. 판정 GC 1024회, 버닝 GC 256회, 각각 host-page AND 조건 제거. 나머지 40개 소스 동일. 점수/탐색/제거/전환 감지 코드는 동일. 기존 timeout fallback은 그대로다.
- 호스트 `oy-B550M-DS3H`, machine_id `f4f3e77cb5bf4a08ab288227cf288de0`, 커널 `7.0.0-31-generic`.
- 빌드 명령 `nice -n 19 ionice -c 3 make -C /lib/modules/7.0.0-31-generic/build M=/home/oy/iCAT/online-v7-src modules`; exit=0. 이 빌드 준비 기록은 빌드 종료 후 작성했으며 실제 실험 시작 전 사전 등록이다. 빌드 로그 build-online-v7.log. MODULE_DESCRIPTION 없음 및 vmlinux 부재 BTF 생략 경고, .ko 링크 성공. 모듈은 아직 로드하지 않았다.
- 모듈 `/home/oy/iCAT/buildoutput/nvmev-online-v7.ko`, SHA256 `eca51601893326439f79854dedf7a2cfa75296812b8f08d3fff7ad4bdb00e5ac`, vermagic `7.0.0-31-generic SMP preempt mod_unload modversions`. 기본 Kbuild WATGC_V2=2; initial arm37; 4 FTL partitions. `memmap_start=4G memmap_size=8192M cpus=1,2 measurement_manual=1 measurement_uid=1000`.
- 대상 `/dev/nvme1n1`, CSL_Virt 모델·시리얼·PCI/vendor 및 mount 검사 유지; 물리 nvme0n1 사용 금지. 8 GiB 예약 메모리. 준비: 가상장치 전용 ext4/nodiscard, 6 GiB 순차 preset, 3 GiB randwrite(seed 20260907), 동기화 후 명시 start/stop. 6 GiB 파일 유지, Filebench 구간 후 해당 파일셋 삭제. FIO seed hot/warm/cold=20260911/20261011/20261111. 기존 Filebench seed 지정 없음(임의 반복 seed로 해석 금지).
- 실행 1: `env PH_SECS=1800 MIX_BASE=/home/oy/iCAT/result/v7-20261011-icat2/fvo90 MIX_JOURNAL=/home/oy/iCAT/result/v7-20261011-icat2/journal.md BASH_ENV=/home/oy/iCAT/result/v7-20261011-icat2/safety-env.sh MIXX_LOCK_HELD=1 bash /home/oy/iCAT/result/v7-20261011-icat2/execution-v7.sh mixX onlinev7 1`. FIO-Fast 30분 → Varmail 30분 → OLTP 15분×2. CAT60의 실행 입력을 복제하며 정책만 v7, 기존 보호 검사 및 계측 유지.
- 실행 2: `env PH_SECS=1800 MIXY_SEQ='F S V F V S F S V F V S F S V F V S F S' MIX_BASE=/home/oy/iCAT/result/v7-20261011-icat2/mixY MIX_JOURNAL=/home/oy/iCAT/result/v7-20261011-icat2/journal.md BASH_ENV=/home/oy/iCAT/result/v7-20261011-icat2/safety-env.sh MIXX_LOCK_HELD=1 bash /home/oy/iCAT/result/v7-20261011-icat2/execution-v7.sh mixY onlinev7 1`. upstream icat2-mixY.sh와 같은 20×30분. mixY case를 원본 그대로 가져온다. Filebench 함수의 추가 stat은 읽기 전용 증거 수집이며 workload 동일. FIO timeout은 CAT60의 45분 실패 방지 제한을 유지.
- 전용 launch.py가 공통 flock을 실제로 보유한 상태에서만 위 명령을 실행한다. 각 raw 디렉터리 존재 시 덮어쓰기 금지. 예상 측정 11시간30분 + 준비/검증/push 약 수분. 현재 CAT60 종료 예상 약 18시 이후, 실제 종료에 연동한다.
- 검증: runner/cleanup exit, fio error/완료 바이트/구간 시간, Filebench IO Summary 및 오류, epoch/start/stop/flush, host_bytes vs block-stat, 파티션 카운터 합, 6 GiB 유지, 모듈 해시, 30초 시계열, phase marker 포함 커널 로그. WAF=1+gc_pages/host_pages; 구간은 경계 카운터 차분. 초기 학습 비용 포함.
- WATGC_V2 sample: marker로 구간을 나눠 ns/part별 실제 줄 수 계산, 구간 밖/누락 marker 별도 기록. FIO-Slow 파티션당 약300은 확인 대상이며 성공 판정에 쓰지 않는다. gc_count로부터 추산한 수와 실제 sample 수를 혼동하지 않는다.
- 실패 원본 보존, failures.tsv에 기록; 바이트 불일치 등 검증 실패는 정상 순위에 넣지 않고 다음 실험 진행. 단 모듈/마운트 정리 실패로 장치가 점유돼 있으면 새 insmod 하지 않고 중지한다. 각 실험 결과를 icat-2로 push. 네트워크 push 실패는 기록 후 재시도하며 다음 측정은 허용한다.
- 순위는 이 PC에서 검증된 CAT60 결과만 사용하고 비교 풀/미확정 수를 명시한다. 다른 PC arm30~59를 같은 반복으로 합치지 않는다.
- 증거 `/home/oy/iCAT/result/v7-20261011-icat2/`: metadata.json, inputs/, module.sha256, build-online-v7.log, journal.md, 각 원본/검증 JSON/구간 WAF와 sample CSV, failures.tsv, report.md. 실행 도구 버전/CPU/메모리/장치 용량은 각 raw/environment.txt/device.txt에 실제 실행 시 수집한다.

- v7 icat-2 {"event": "offline_automation_validation_and_queue_registration", "time": "2026-10-12T13:56:23.758485+09:00", "checks": "/home/oy/iCAT/result/v7-20261011-icat2/automation-check.json", "no_device_operation": true, "unit": "icat-v7-after-cat60-20261012.service", "current_cat_status": "running_arm27_S01", "module_sha256": "eca51601893326439f79854dedf7a2cfa75296812b8f08d3fff7ad4bdb00e5ac"}

- v7 icat-2 {"event": "queue_started_after_CAT60", "time": "2026-10-12T18:30:24.693297+09:00", "runner_sha256": {"execution-v7.sh": "53f4a660db322e54e870f830768f5c172b3b4d2fa061d17601aea3ae93ec7a58", "safety-env.sh": "1dd7658591a10a092e72b206c542bf85aebf1be17848cc3037413775f449a4b2"}}

- v7 icat-2 {"event": "experiment_started", "time": "2026-10-12T18:30:27.595031+09:00", "stage": "fvo90", "command": ["bash", "/home/oy/iCAT/result/v7-20261011-icat2/execution-v7.sh", "mixX", "onlinev7", "1"], "sequence": "F V O", "module_sha256": "eca51601893326439f79854dedf7a2cfa75296812b8f08d3fff7ad4bdb00e5ac", "raw_path": "/home/oy/iCAT/result/v7-20261011-icat2/fvo90/mixX-onlinev7-rep1"}

### cycle-20261007 mixX onlinev7 — started 2026-10-12T18:30:27+09:00

- mixX: (FIO-Fast, Varmail, OLTP) = 3 time-based phases of 1800 s. Table-3 prep, 6 GiB FIO file kept; FIO payload x 1800/600; Filebench files deleted after each Filebench phase; no YCSB. Module `nvmev-online-v7.ko`.
- Command: `env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX onlinev7 1`; evidence `result/v7-20261011-icat2/fvo90/mixX-onlinev7-rep1/`.

- Finished 2026-10-12T20:02:05+09:00; mixX onlinev7 exit=0; evidence `/home/oy/iCAT/result/v7-20261011-icat2/fvo90/mixX-onlinev7-rep1`; cleanup attempted.
- total host_bytes=1598181707776 host_pages=390181081 gc_pages=468645980 WAF=2.201099
- phaseA(test4) host_pages=72026582 gc_pages=65843087 WAF=1.914150
- phaseB(varmail) host_pages=245154967 gc_pages=379412136 WAF=2.547642
- phaseS01(test4) host_pages=72026582 gc_pages=65843087 WAF=1.914150
- phaseS02(varmail) host_pages=245154967 gc_pages=379412136 WAF=2.547642
- phaseS03(oltp) host_pages=72999531 gc_pages=23390757 WAF=1.320423
- ycsb-load 
- ycsb-run 

- v7 icat-2 {"event": "experiment_finished", "time": "2026-10-12T20:02:07.174128+09:00", "stage": "fvo90", "status": "validated_saved_evidence", "runner_exit": 0, "waf": 2.201098676539881, "issues": [], "raw_path": "/home/oy/iCAT/result/v7-20261011-icat2/fvo90/mixX-onlinev7-rep1"}

- v7 icat-2 {"event": "experiment_started", "time": "2026-10-12T20:02:13.967678+09:00", "stage": "mixY", "command": ["bash", "/home/oy/iCAT/result/v7-20261011-icat2/execution-v7.sh", "mixY", "onlinev7", "1"], "sequence": "F S V F V S F S V F V S F S V F V S F S", "module_sha256": "eca51601893326439f79854dedf7a2cfa75296812b8f08d3fff7ad4bdb00e5ac", "raw_path": "/home/oy/iCAT/result/v7-20261011-icat2/mixY/mixY-onlinev7-rep1"}

### v7 mixY onlinev7 — started 2026-10-12T20:02:13+09:00
- Sequence: F S V F V S F S V F V S F S V F V S F S; PH_SECS=1800; Table-3 prep; evidence `/home/oy/iCAT/result/v7-20261011-icat2/mixY/mixY-onlinev7-rep1`; module `/home/oy/iCAT/buildoutput/nvmev-online-v7.ko`.

- Finished 2026-10-13T06:04:04+09:00; mixY onlinev7 exit=0; evidence `/home/oy/iCAT/result/v7-20261011-icat2/mixY/mixY-onlinev7-rep1`; cleanup attempted.
- total host_bytes=8484397760512 host_pages=2071386172 gc_pages=4803265475 WAF=3.318865
- phaseA(test4) host_pages=72001978 gc_pages=67396807 WAF=1.936041
- phaseB(test3) host_pages=18001245 gc_pages=14745452 WAF=1.819135
- phaseS01(test4) host_pages=72001978 gc_pages=67396807 WAF=1.936041
- phaseS02(test3) host_pages=18001245 gc_pages=14745452 WAF=1.819135
- phaseS03(varmail) host_pages=255533300 gc_pages=383284609 WAF=2.499940
- phaseS04(test4) host_pages=72001981 gc_pages=317153870 WAF=5.404794
- phaseS05(varmail) host_pages=232011172 gc_pages=380771730 WAF=2.641178
- phaseS06(test3) host_pages=18001282 gc_pages=72198726 WAF=5.010755
- phaseS07(test4) host_pages=72001978 gc_pages=332248333 WAF=5.614433
- phaseS08(test3) host_pages=18001246 gc_pages=70469281 WAF=4.914689
- phaseS09(varmail) host_pages=242423018 gc_pages=412334436 WAF=2.700888
- phaseS10(test4) host_pages=72001981 gc_pages=318369704 WAF=5.421680
- phaseS11(varmail) host_pages=239481368 gc_pages=395964183 WAF=2.653424
- phaseS12(test3) host_pages=18001246 gc_pages=72420720 WAF=5.023095
- phaseS13(test4) host_pages=72001978 gc_pages=329392146 WAF=5.574765
- phaseS14(test3) host_pages=18001246 gc_pages=67563721 WAF=4.753280
- phaseS15(varmail) host_pages=231146932 gc_pages=392875178 WAF=2.699677
- phaseS16(test4) host_pages=72001981 gc_pages=309956860 WAF=5.304838
- phaseS17(varmail) host_pages=240767770 gc_pages=392301633 WAF=2.629378
- phaseS18(test3) host_pages=18001246 gc_pages=73312512 WAF=5.072635
- phaseS19(test4) host_pages=72001978 gc_pages=330787205 WAF=5.594141
- phaseS20(test3) host_pages=18001246 gc_pages=69718369 WAF=4.872975
- ycsb-load 
- ycsb-run 

- v7 icat-2 {"event": "experiment_finished", "time": "2026-10-13T06:04:05.385911+09:00", "stage": "mixY", "status": "validated_saved_evidence", "runner_exit": 0, "waf": 3.3188652796510025, "issues": [], "raw_path": "/home/oy/iCAT/result/v7-20261011-icat2/mixY/mixY-onlinev7-rep1"}
