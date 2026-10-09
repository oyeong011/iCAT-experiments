# 고정 CAT 60조합 — 90분 혼합 전체 순위 사전 등록

- 등록: 2026-10-09T14:42:55.657046+09:00, run_id `mixX-cat60-90min-20261009`; 각 실행 ID `mixX-arm00-rep1`부터 `mixX-arm59-rep1`까지, 오름차순 단일 큐.
- 사용자 목적: 고정 CAT 파라미터 전체 순위. 10시간 대신 30분 워크로드·약1시간반으로 축소 요청. 구간당30분을 기준으로 **FIO-Fast30분 → Varmail30분 → OLTP30분**, 총3구간5400초로 해석해 진행. 6구간×15분 대안은 질문했으나 응답 없이 위 가정을 명시함. 워크로드를 다시 반복하지 않으므로 이전10시간 mixX의 반복전환 순위로 해석하지 않는다.
- 명령: `bash script/icat2-mixX-cat60-90min.sh`; 내부 각 실행 `env PH_SECS=1800 MIX_BASE=/home/oy/iCAT/result/mixX-cat60-90min-20261009 MIX_JOURNAL=/home/oy/iCAT/result/mixX-cat60-90min-20261009/journal.md BASH_ENV=/home/oy/iCAT/result/mixX-cat60-90min-20261009/safety-env.sh MIXX_LOCK_HELD=1 bash /home/oy/iCAT/result/mixX-cat60-90min-20261009/execution-mix.sh mixX armNN 1`.
- 60조합: k=(2,4,7,10), scale_pct=(25,50,100,200,400), age_ratio=(4,7,16); arm=ki*15+si*3+ri. fixed37=arm37, fixed50=arm50 등 별칭은 중복 조합으로 세지 않음. **60개 모두 동일한 새90분 실행**, 기존10시간 결과/prefix는 새실행으로 대체하지 않음.
- 총 순수측정90시간, 준비·검증·push 포함 약92시간 예상. 한호스트/한가상장치에서 하나씩 실행. arm00부터 시작; 별도추가시험 없음. 실패/중단/검증오류/push실패 시 후속큐 중단, 원본보존; 자동재시도·덮어쓰기 없음.
- 호스트 `oy-B550M-DS3H`, machine_id `f4f3e77cb5bf4a08ab288227cf288de0`, kernel `7.0.0-31-generic`. 소스 기준 `5e569073f2e980708ebebccb5104810c6c95779a`, 기존 검증된 cycle runner snapshot에서 구간수만3으로 축소하고 arm00..59 제한/loadedarm검사/FIO시간제한 추가. 전체변경은 runner-local.diff. 루트dirty작업보존; source-status와실행코드해시 기록. 모듈60개 현커널용기존파일 재사용; SHA256/vermagic/파라미터는 module-inventory.csv와metadata.json, 실행전해시검사 및4partition runtimearm/k/scale/ratio검증. 재빌드없음.
- NVMeVirt전용 `/dev/nvme1n1`, model/serial/vendor/PCI/mount 보호유지, 물리nvme0n1 거부. 전역device.lock을 캠페인전체동안보유. 매arm모듈생성/가상FS포맷/준비/측정/해제를 동일하게 수행. 강제reset·재부팅 없음.
- 모듈옵션 `memmap_start=4G memmap_size=8192M cpus=1,2 measurement_manual=1 measurement_uid=1000`. 준비:6GiB순차128KiB+3GiB랜덤4KiB10kIOPS seed20260907, 계측제외. 같은6GiB파일유지;hot512MiB/warm1536MiB/cold4GiB,24k/12k/4kIOPS. FIO측정요청량176947200000/88473600000/29491200000bytes;seed20260911/20261011/20261111. FIO완료상한2700초, 미완료시실패. 준비설정과모듈FTL/GC코드는source/와inputs/에보존.
- Varmail24000files1800초, OLTP32MiB파일900초×2(메모리누수회피). Filebenchseed미지정. 각응용종료파일삭제,nodiscard,6GiBFIO파일유지. YCSB없음.
- 계측: measurement_manual1,준비후start,3구간종료flush후stop. 30초카운터와구간경계저장. WAF=1+gc_pages/host_pages. 전체WAF는전체카운터비율이며구간WAF산술평균이아님. 독립NAND계측아님.
- 판정: runner/cleanup exit0,FIOerror0/요청쓰기완료/실행시간,Filebench구간/청크완료와오류검색,정확한3개구간,초기0/단일epoch/stop후불변,4partition합계와arm/파라미터일치,host_bytes=blockstat증분×512,6GiB파일동일inode유지. 검증통과값만순위포함.
- 결과: inventory.csv, rank-reference.csv(전체WAF), phase-ranks.csv(구간별), ranking.md, 30초series/armNN.csv, 원본mixX-armNN-rep1/ 및resultJSON. rank=1+count(고정CAT WAF<해당값), 분모60; 중간순위는완료풀크기와미측정수/가능순위범위명시. 단일실행차이를통계적우열로해석하지않음. v4/v6는이번60개고정조합에포함하지않음; 나중에추가하면동일90분/동일호스트조건필요.
- 기존20분/30분10시간결과는보존. 다른호스트결과를같은풀로합치지않음. 구간길이축소에대한10시간수렴증거없음;90분전체순위를10시간전체순위로표현하지않음.
- 공개: 요청된기존방식대로 검증된각arm후icat-2만push. 실패원본도보존push. main수정/push없음.

- CAT60 screen90 {"event": "started", "policy": "arm00", "time": "2026-10-09T14:43:35.323910+09:00", "module": {"path": "/home/oy/iCAT/buildoutput/nvmev-arm00.ko", "sha256": "2af2e56dbb46b7d3eb3c519d8802f8252f9472425bf9b633be21b607d2a99951", "vermagic": "7.0.0-31-generic SMP preempt mod_unload modversions", "k": 2, "scale_pct": 25, "age_ratio": 4, "provenance": "existingcurrentkernelmodule;source griddecode snapshotted;runtimeparamcheckmandatory"}, "phase_order": ["FIO-Fast", "Varmail", "OLTP"], "phase_seconds": 1800}

### cycle-20261007 mixX arm00 — started 2026-10-09T14:43:35+09:00

- mixX: (FIO-Fast, Varmail, OLTP) = 3 time-based phases of 1800 s. Table-3 prep, 6 GiB FIO file kept; FIO payload x 1800/600; Filebench files deleted after each Filebench phase; no YCSB. Module `nvmev-arm00.ko`.
- Command: `env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX arm00 1`; evidence `result/mixX-cat60-90min-20261009/mixX-arm00-rep1/`.

- Finished 2026-10-09T16:15:11+09:00; mixX arm00 exit=0; evidence `/home/oy/iCAT/result/mixX-cat60-90min-20261009/mixX-arm00-rep1`; cleanup attempted.
- total host_bytes=1241684865024 host_pages=303145719 gc_pages=687901479 WAF=3.269211
- phaseA(test4) host_pages=72002119 gc_pages=91104501 WAF=2.265303
- phaseB(varmail) host_pages=163542739 gc_pages=527865727 WAF=4.227693
- phaseS01(test4) host_pages=72002119 gc_pages=91104501 WAF=2.265303
- phaseS02(varmail) host_pages=163542739 gc_pages=527865727 WAF=4.227693
- phaseS03(oltp) host_pages=67600860 gc_pages=68931251 WAF=2.019680
- ycsb-load 
- ycsb-run 

- CAT60 screen90 {"event": "finished", "policy": "arm00", "finished_at": "2026-10-09T16:15:14.579647+09:00", "runner_exit": 0, "status": "validated_saved_evidence", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/mixX-arm00-rep1", "validation_exit": 0, "stage": "screen90", "waf": 3.269210600331783, "host_bytes": 1241684865024, "host_pages": 303145719, "gc_pages": 687901479, "actual_measured_seconds": 5414.0, "phases": [{"slot": "S01", "workload": "FIO-Fast", "actual_seconds": 1801.0, "waf": 2.265303053094868, "host_bytes": 294920679424, "host_pages": 72002119, "gc_pages": 91104501}, {"slot": "S02", "workload": "Varmail", "actual_seconds": 1803.0, "waf": 4.227692835693549, "host_bytes": 669871058944, "host_pages": 163542739, "gc_pages": 527865727, "process_runtimes_seconds": [1800.133]}, {"slot": "S03", "workload": "OLTP", "actual_seconds": 1810.0, "waf": 2.019680089868679, "host_bytes": 276893122560, "host_pages": 67600860, "gc_pages": 68931251, "process_runtimes_seconds": [901.073, 901.16]}], "sample_rows": 184, "transition_count": 2, "measurement": "manual FTLpageWAF, hostbytes verified againstblockstat, no independentNANDmeasurement"}

- CAT60 screen90 {"event": "started", "policy": "arm01", "time": "2026-10-09T16:15:18.002226+09:00", "module": {"path": "/home/oy/iCAT/buildoutput/nvmev-arm01.ko", "sha256": "6df3c9595e4385036ded1fb9d05724bf4bbcfd72d390ab8d026bcad21c4ea9dc", "vermagic": "7.0.0-31-generic SMP preempt mod_unload modversions", "k": 2, "scale_pct": 25, "age_ratio": 7, "provenance": "existingcurrentkernelmodule;source griddecode snapshotted;runtimeparamcheckmandatory"}, "phase_order": ["FIO-Fast", "Varmail", "OLTP"], "phase_seconds": 1800}

### cycle-20261007 mixX arm01 — started 2026-10-09T16:15:18+09:00

- mixX: (FIO-Fast, Varmail, OLTP) = 3 time-based phases of 1800 s. Table-3 prep, 6 GiB FIO file kept; FIO payload x 1800/600; Filebench files deleted after each Filebench phase; no YCSB. Module `nvmev-arm01.ko`.
- Command: `env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX arm01 1`; evidence `result/mixX-cat60-90min-20261009/mixX-arm01-rep1/`.

- Finished 2026-10-09T17:46:55+09:00; mixX arm01 exit=0; evidence `/home/oy/iCAT/result/mixX-cat60-90min-20261009/mixX-arm01-rep1`; cleanup attempted.
- total host_bytes=1221698535424 host_pages=298266244 gc_pages=690548190 WAF=3.315207
- phaseA(test4) host_pages=72001984 gc_pages=91153165 WAF=2.265981
- phaseB(varmail) host_pages=158292303 gc_pages=536736223 WAF=4.390792
- phaseS01(test4) host_pages=72001984 gc_pages=91153165 WAF=2.265981
- phaseS02(varmail) host_pages=158292303 gc_pages=536736223 WAF=4.390792
- phaseS03(oltp) host_pages=67971956 gc_pages=62658802 WAF=1.921833
- ycsb-load 
- ycsb-run 

- CAT60 screen90 {"event": "finished", "policy": "arm01", "finished_at": "2026-10-09T17:46:57.385175+09:00", "runner_exit": 0, "status": "validated_saved_evidence", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/mixX-arm01-rep1", "validation_exit": 0, "stage": "screen90", "waf": 3.3152073152468438, "host_bytes": 1221698535424, "host_pages": 298266244, "gc_pages": 690548190, "actual_measured_seconds": 5415.0, "phases": [{"slot": "S01", "workload": "FIO-Fast", "actual_seconds": 1800.0, "waf": 2.2659812957376286, "host_bytes": 294920126464, "host_pages": 72001984, "gc_pages": 91153165}, {"slot": "S02", "workload": "Varmail", "actual_seconds": 1804.0, "waf": 4.390791673553451, "host_bytes": 648365273088, "host_pages": 158292303, "gc_pages": 536736223, "process_runtimes_seconds": [1800.117]}, {"slot": "S03", "workload": "OLTP", "actual_seconds": 1811.0, "waf": 1.9218331454225033, "host_bytes": 278413131776, "host_pages": 67971956, "gc_pages": 62658802, "process_runtimes_seconds": [901.32, 901.119]}], "sample_rows": 184, "transition_count": 2, "measurement": "manual FTLpageWAF, hostbytes verified againstblockstat, no independentNANDmeasurement"}

- CAT60 screen90 {"event": "started", "policy": "arm02", "time": "2026-10-09T17:47:01.131566+09:00", "module": {"path": "/home/oy/iCAT/buildoutput/nvmev-arm02.ko", "sha256": "f84ebdf7ac5e7d99b80810524d6ed7b2f57732dc4bbbed693deacb2922aed654", "vermagic": "7.0.0-31-generic SMP preempt mod_unload modversions", "k": 2, "scale_pct": 25, "age_ratio": 16, "provenance": "existingcurrentkernelmodule;source griddecode snapshotted;runtimeparamcheckmandatory"}, "phase_order": ["FIO-Fast", "Varmail", "OLTP"], "phase_seconds": 1800}

### cycle-20261007 mixX arm02 — started 2026-10-09T17:47:01+09:00

- mixX: (FIO-Fast, Varmail, OLTP) = 3 time-based phases of 1800 s. Table-3 prep, 6 GiB FIO file kept; FIO payload x 1800/600; Filebench files deleted after each Filebench phase; no YCSB. Module `nvmev-arm02.ko`.
- Command: `env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX arm02 1`; evidence `result/mixX-cat60-90min-20261009/mixX-arm02-rep1/`.

- Finished 2026-10-09T19:18:37+09:00; mixX arm02 exit=0; evidence `/home/oy/iCAT/result/mixX-cat60-90min-20261009/mixX-arm02-rep1`; cleanup attempted.
- total host_bytes=1193889259520 host_pages=291476870 gc_pages=699227082 WAF=3.398911
- phaseA(test4) host_pages=72001978 gc_pages=91339411 WAF=2.268568
- phaseB(varmail) host_pages=148857719 gc_pages=541362082 WAF=4.636775
- phaseS01(test4) host_pages=72001978 gc_pages=91339411 WAF=2.268568
- phaseS02(varmail) host_pages=148857719 gc_pages=541362082 WAF=4.636775
- phaseS03(oltp) host_pages=70617172 gc_pages=66525589 WAF=1.942060
- ycsb-load 
- ycsb-run 

- CAT60 screen90 {"event": "finished", "policy": "arm02", "finished_at": "2026-10-09T19:18:40.480726+09:00", "runner_exit": 0, "status": "validated_saved_evidence", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/mixX-arm02-rep1", "validation_exit": 0, "stage": "screen90", "waf": 3.398911042238103, "host_bytes": 1193889259520, "host_pages": 291476870, "gc_pages": 699227082, "actual_measured_seconds": 5414.0, "phases": [{"slot": "S01", "workload": "FIO-Fast", "actual_seconds": 1800.0, "waf": 2.2685680801713533, "host_bytes": 294920101888, "host_pages": 72001978, "gc_pages": 91339411}, {"slot": "S02", "workload": "Varmail", "actual_seconds": 1804.0, "waf": 4.636775342500042, "host_bytes": 609721217024, "host_pages": 148857719, "gc_pages": 541362082, "process_runtimes_seconds": [1800.118]}, {"slot": "S03", "workload": "OLTP", "actual_seconds": 1810.0, "waf": 1.9420596593701034, "host_bytes": 289247936512, "host_pages": 70617172, "gc_pages": 66525589, "process_runtimes_seconds": [901.1610000000001, 901.309]}], "sample_rows": 184, "transition_count": 2, "measurement": "manual FTLpageWAF, hostbytes verified againstblockstat, no independentNANDmeasurement"}
