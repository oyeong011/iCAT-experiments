
## CAT60 90min continuation — preregistered 2026-10-11T01:10:45.010659+09:00

User authorization: preserve original arm03, retry it exactly once, then arm04 through arm29 ascending; no arm30-59 on this host. 27 executions, approximately 41 hours plus publishing.
Run ID: mixX-cat60-90min-20261009-resume-20261011. New raw paths: /home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-armNN-rep1. Original campaign raw and results retained byte-exact; preservation manifest saved.
Conditions unchanged: FIO-Fast 1800s -> Varmail 1800s -> OLTP 2x900s. 6GiB sequential +3GiB random preparation excluded; kept6GiB file; nodiscard; manual measurement; rep1 seeds unchanged; 30s counters. Original runner, safety adapter, workload/module hashes, kernel and runtime arm checks retained. Host oy-B550M-DS3H, machine_id f4f3e77cb5bf4a08ab288227cf288de0, kernel 7.0.0-31-generic; metadata contains module and input provenance.
Change is scheduling only: exact final host_bytes/blockstat mismatch may continue after other saved-evidence checks and normal cleanup succeed. Such attempts remain FAILED and excluded from valid ranks. Record all failures in failures.csv, push every completed attempt to icat-2. Any other failure, cleanup problem, or push failure halts. No automatic second retry.
Original arm03 mismatch: module1198937595904 vs block1198938116096 bytes, difference520192. Cause not established. No relaxed tolerance and no counter correction.

- CAT60 continuation {"event": "started", "time": "2026-10-11T01:12:41.639768+09:00", "policy": "arm03", "attempt": "retry1", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm03-rep1", "module": {"path": "/home/oy/iCAT/buildoutput/nvmev-arm03.ko", "sha256": "3bb87a28f73f01c5db2e235b41994ebd1afa9a629c7022b3928b056021a5b22e", "vermagic": "7.0.0-31-generic SMP preempt mod_unload modversions", "k": 2, "scale_pct": 50, "age_ratio": 4, "provenance": "existingcurrentkernelmodule;source griddecode snapshotted;runtimeparamcheckmandatory"}, "phase_order": ["FIO-Fast", "Varmail", "OLTP"], "phase_seconds": 1800}

### cycle-20261007 mixX arm03 — started 2026-10-11T01:12:41+09:00

- mixX: (FIO-Fast, Varmail, OLTP) = 3 time-based phases of 1800 s. Table-3 prep, 6 GiB FIO file kept; FIO payload x 1800/600; Filebench files deleted after each Filebench phase; no YCSB. Module `nvmev-arm03.ko`.
- Command: `env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX arm03 1`; evidence `result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm03-rep1/`.

- Finished 2026-10-11T02:44:18+09:00; mixX arm03 exit=0; evidence `/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm03-rep1`; cleanup attempted.
- total host_bytes=1193722335232 host_pages=291436117 gc_pages=739922662 WAF=3.538885
- phaseA(test4) host_pages=72001981 gc_pages=92265792 WAF=2.281434
- phaseB(varmail) host_pages=148878193 gc_pages=546281835 WAF=4.669321
- phaseS01(test4) host_pages=72001981 gc_pages=92265792 WAF=2.281434
- phaseS02(varmail) host_pages=148878193 gc_pages=546281835 WAF=4.669321
- phaseS03(oltp) host_pages=70555942 gc_pages=101375035 WAF=2.436804
- ycsb-load 
- ycsb-run 

- CAT60 continuation {"event": "finished", "policy": "arm03", "runner_exit": 0, "finished_at": "2026-10-11T02:44:21.032833+09:00", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm03-rep1", "status": "validated_saved_evidence", "validation_exit": 0, "stage": "screen90", "waf": 3.5388845748311972, "host_bytes": 1193722335232, "host_pages": 291436117, "gc_pages": 739922662, "actual_measured_seconds": 5413.0, "phases": [{"slot": "S01", "workload": "FIO-Fast", "actual_seconds": 1800.0, "waf": 2.281434076098545, "host_bytes": 294920114176, "host_pages": 72001981, "gc_pages": 92265792}, {"slot": "S02", "workload": "Varmail", "actual_seconds": 1804.0, "waf": 4.669320697625609, "host_bytes": 609805078528, "host_pages": 148878193, "gc_pages": 546281835, "process_runtimes_seconds": [1800.118]}, {"slot": "S03", "workload": "OLTP", "actual_seconds": 1809.0, "waf": 2.436803650073866, "host_bytes": 288997138432, "host_pages": 70555942, "gc_pages": 101375035, "process_runtimes_seconds": [900.902, 900.979]}], "sample_rows": 184, "transition_count": 2, "measurement": "manual FTLpageWAF, hostbytes verified againstblockstat, no independentNANDmeasurement"}

- CAT60 continuation {"event": "started", "time": "2026-10-11T02:44:25.265754+09:00", "policy": "arm04", "attempt": "first", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm04-rep1", "module": {"path": "/home/oy/iCAT/buildoutput/nvmev-arm04.ko", "sha256": "bc11277eb39b4ed4b0e9ed2b31becc6385372190b67c9d0a920189b6b3e5806b", "vermagic": "7.0.0-31-generic SMP preempt mod_unload modversions", "k": 2, "scale_pct": 50, "age_ratio": 7, "provenance": "existingcurrentkernelmodule;source griddecode snapshotted;runtimeparamcheckmandatory"}, "phase_order": ["FIO-Fast", "Varmail", "OLTP"], "phase_seconds": 1800}

### cycle-20261007 mixX arm04 — started 2026-10-11T02:44:25+09:00

- mixX: (FIO-Fast, Varmail, OLTP) = 3 time-based phases of 1800 s. Table-3 prep, 6 GiB FIO file kept; FIO payload x 1800/600; Filebench files deleted after each Filebench phase; no YCSB. Module `nvmev-arm04.ko`.
- Command: `env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX arm04 1`; evidence `result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm04-rep1/`.

- Finished 2026-10-11T04:16:01+09:00; mixX arm04 exit=0; evidence `/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm04-rep1`; cleanup attempted.
- total host_bytes=1188263878656 host_pages=290103486 gc_pages=756666645 WAF=3.608265
- phaseA(test4) host_pages=72001978 gc_pages=91325328 WAF=2.268372
- phaseB(varmail) host_pages=146049318 gc_pages=558375835 WAF=4.823201
- phaseS01(test4) host_pages=72001978 gc_pages=91325328 WAF=2.268372
- phaseS02(varmail) host_pages=146049318 gc_pages=558375835 WAF=4.823201
- phaseS03(oltp) host_pages=72052189 gc_pages=106965482 WAF=2.484556
- ycsb-load 
- ycsb-run 

- CAT60 continuation {"event": "finished", "policy": "arm04", "runner_exit": 0, "finished_at": "2026-10-11T04:16:04.484671+09:00", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm04-rep1", "status": "validated_saved_evidence", "validation_exit": 0, "stage": "screen90", "waf": 3.608264572870386, "host_bytes": 1188263878656, "host_pages": 290103486, "gc_pages": 756666645, "actual_measured_seconds": 5414.0, "phases": [{"slot": "S01", "workload": "FIO-Fast", "actual_seconds": 1800.0, "waf": 2.2683724883224734, "host_bytes": 294920101888, "host_pages": 72001978, "gc_pages": 91325328}, {"slot": "S02", "workload": "Varmail", "actual_seconds": 1803.0, "waf": 4.823200564346353, "host_bytes": 598218006528, "host_pages": 146049318, "gc_pages": 558375835, "process_runtimes_seconds": [1800.113]}, {"slot": "S03", "workload": "OLTP", "actual_seconds": 1810.0, "waf": 2.4845556184281925, "host_bytes": 295125766144, "host_pages": 72052189, "gc_pages": 106965482, "process_runtimes_seconds": [900.9, 900.79]}], "sample_rows": 184, "transition_count": 2, "measurement": "manual FTLpageWAF, hostbytes verified againstblockstat, no independentNANDmeasurement"}

- CAT60 continuation {"event": "started", "time": "2026-10-11T04:16:08.795061+09:00", "policy": "arm05", "attempt": "first", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm05-rep1", "module": {"path": "/home/oy/iCAT/buildoutput/nvmev-arm05.ko", "sha256": "7f786656f4821080e04de0dc6406b51be118813f8155094482be135c6f7a25de", "vermagic": "7.0.0-31-generic SMP preempt mod_unload modversions", "k": 2, "scale_pct": 50, "age_ratio": 16, "provenance": "existingcurrentkernelmodule;source griddecode snapshotted;runtimeparamcheckmandatory"}, "phase_order": ["FIO-Fast", "Varmail", "OLTP"], "phase_seconds": 1800}

### cycle-20261007 mixX arm05 — started 2026-10-11T04:16:08+09:00

- mixX: (FIO-Fast, Varmail, OLTP) = 3 time-based phases of 1800 s. Table-3 prep, 6 GiB FIO file kept; FIO payload x 1800/600; Filebench files deleted after each Filebench phase; no YCSB. Module `nvmev-arm05.ko`.
- Command: `env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX arm05 1`; evidence `result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm05-rep1/`.

- Finished 2026-10-11T05:47:45+09:00; mixX arm05 exit=0; evidence `/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm05-rep1`; cleanup attempted.
- total host_bytes=1166117117952 host_pages=284696562 gc_pages=761989955 WAF=3.676499
- phaseA(test4) host_pages=72030687 gc_pages=88969766 WAF=2.235165
- phaseB(varmail) host_pages=139598526 gc_pages=558523400 WAF=5.000926
- phaseS01(test4) host_pages=72030687 gc_pages=88969766 WAF=2.235165
- phaseS02(varmail) host_pages=139598526 gc_pages=558523400 WAF=5.000926
- phaseS03(oltp) host_pages=73067348 gc_pages=114496789 WAF=2.567003
- ycsb-load 
- ycsb-run 

- CAT60 continuation {"event": "finished", "policy": "arm05", "runner_exit": 0, "finished_at": "2026-10-11T05:47:47.884900+09:00", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm05-rep1", "status": "validated_saved_evidence", "validation_exit": 0, "stage": "screen90", "waf": 3.676498618904994, "host_bytes": 1166117117952, "host_pages": 284696562, "gc_pages": 761989955, "actual_measured_seconds": 5414.0, "phases": [{"slot": "S01", "workload": "FIO-Fast", "actual_seconds": 1800.0, "waf": 2.2351647569320003, "host_bytes": 295037693952, "host_pages": 72030687, "gc_pages": 88969766}, {"slot": "S02", "workload": "Varmail", "actual_seconds": 1804.0, "waf": 5.00092619889124, "host_bytes": 571795562496, "host_pages": 139598526, "gc_pages": 558523400, "process_runtimes_seconds": [1800.113]}, {"slot": "S03", "workload": "OLTP", "actual_seconds": 1810.0, "waf": 2.5670034856061834, "host_bytes": 299283857408, "host_pages": 73067348, "gc_pages": 114496789, "process_runtimes_seconds": [901.01, 901.046]}], "sample_rows": 184, "transition_count": 2, "measurement": "manual FTLpageWAF, hostbytes verified againstblockstat, no independentNANDmeasurement"}

- CAT60 continuation {"event": "started", "time": "2026-10-11T05:47:52.245708+09:00", "policy": "arm06", "attempt": "first", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm06-rep1", "module": {"path": "/home/oy/iCAT/buildoutput/nvmev-arm06.ko", "sha256": "3546c8f6a0087baeed0fe0552bc83cdc927f83d416fe13ac16341af974f25319", "vermagic": "7.0.0-31-generic SMP preempt mod_unload modversions", "k": 2, "scale_pct": 100, "age_ratio": 4, "provenance": "existingcurrentkernelmodule;source griddecode snapshotted;runtimeparamcheckmandatory"}, "phase_order": ["FIO-Fast", "Varmail", "OLTP"], "phase_seconds": 1800}

### cycle-20261007 mixX arm06 — started 2026-10-11T05:47:52+09:00

- mixX: (FIO-Fast, Varmail, OLTP) = 3 time-based phases of 1800 s. Table-3 prep, 6 GiB FIO file kept; FIO payload x 1800/600; Filebench files deleted after each Filebench phase; no YCSB. Module `nvmev-arm06.ko`.
- Command: `env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX arm06 1`; evidence `result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm06-rep1/`.

- Finished 2026-10-11T07:19:28+09:00; mixX arm06 exit=0; evidence `/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm06-rep1`; cleanup attempted.
- total host_bytes=1150724423680 host_pages=280938580 gc_pages=809402366 WAF=3.881065
- phaseA(test4) host_pages=72019890 gc_pages=92163744 WAF=2.279698
- phaseB(varmail) host_pages=137873201 gc_pages=561148341 WAF=5.070032
- phaseS01(test4) host_pages=72019890 gc_pages=92163744 WAF=2.279698
- phaseS02(varmail) host_pages=137873201 gc_pages=561148341 WAF=5.070032
- phaseS03(oltp) host_pages=71045488 gc_pages=156090281 WAF=3.197047
- ycsb-load 
- ycsb-run 

- CAT60 continuation {"event": "finished", "policy": "arm06", "runner_exit": 0, "finished_at": "2026-10-11T07:19:31.154852+09:00", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm06-rep1", "status": "validated_saved_evidence", "validation_exit": 0, "stage": "screen90", "waf": 3.881065199375607, "host_bytes": 1150724423680, "host_pages": 280938580, "gc_pages": 809402366, "actual_measured_seconds": 5414.0, "phases": [{"slot": "S01", "workload": "FIO-Fast", "actual_seconds": 1800.0, "waf": 2.27969848329399, "host_bytes": 294993469440, "host_pages": 72019890, "gc_pages": 92163744}, {"slot": "S02", "workload": "Varmail", "actual_seconds": 1804.0, "waf": 5.0700320071628715, "host_bytes": 564728631296, "host_pages": 137873201, "gc_pages": 561148341, "process_runtimes_seconds": [1800.114]}, {"slot": "S03", "workload": "OLTP", "actual_seconds": 1810.0, "waf": 3.197047066521663, "host_bytes": 291002318848, "host_pages": 71045488, "gc_pages": 156090281, "process_runtimes_seconds": [900.9159999999999, 900.8009999999999]}], "sample_rows": 184, "transition_count": 2, "measurement": "manual FTLpageWAF, hostbytes verified againstblockstat, no independentNANDmeasurement"}

- CAT60 continuation {"event": "started", "time": "2026-10-11T07:19:35.363782+09:00", "policy": "arm07", "attempt": "first", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm07-rep1", "module": {"path": "/home/oy/iCAT/buildoutput/nvmev-arm07.ko", "sha256": "cb9fdd4d3879a8ec0d96f99ce71b037769a021206d3207cf7d4bed631dc034b2", "vermagic": "7.0.0-31-generic SMP preempt mod_unload modversions", "k": 2, "scale_pct": 100, "age_ratio": 7, "provenance": "existingcurrentkernelmodule;source griddecode snapshotted;runtimeparamcheckmandatory"}, "phase_order": ["FIO-Fast", "Varmail", "OLTP"], "phase_seconds": 1800}

### cycle-20261007 mixX arm07 — started 2026-10-11T07:19:35+09:00

- mixX: (FIO-Fast, Varmail, OLTP) = 3 time-based phases of 1800 s. Table-3 prep, 6 GiB FIO file kept; FIO payload x 1800/600; Filebench files deleted after each Filebench phase; no YCSB. Module `nvmev-arm07.ko`.
- Command: `env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX arm07 1`; evidence `result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm07-rep1/`.

- Finished 2026-10-11T08:51:12+09:00; mixX arm07 exit=0; evidence `/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm07-rep1`; cleanup attempted.
- total host_bytes=1143428358144 host_pages=279157314 gc_pages=815349415 WAF=3.920752
- phaseA(test4) host_pages=72001978 gc_pages=92316496 WAF=2.282138
- phaseB(varmail) host_pages=136555951 gc_pages=566944713 WAF=5.151739
- phaseS01(test4) host_pages=72001978 gc_pages=92316496 WAF=2.282138
- phaseS02(varmail) host_pages=136555951 gc_pages=566944713 WAF=5.151739
- phaseS03(oltp) host_pages=70599384 gc_pages=156088153 WAF=3.210900
- ycsb-load 
- ycsb-run 

- CAT60 continuation {"event": "finished", "policy": "arm07", "runner_exit": 0, "finished_at": "2026-10-11T08:51:14.682734+09:00", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm07-rep1", "status": "validated_saved_evidence", "validation_exit": 0, "stage": "screen90", "waf": 3.920752472206406, "host_bytes": 1143428358144, "host_pages": 279157314, "gc_pages": 815349415, "actual_measured_seconds": 5414.0, "phases": [{"slot": "S01", "workload": "FIO-Fast", "actual_seconds": 1801.0, "waf": 2.282138332366369, "host_bytes": 294920101888, "host_pages": 72001978, "gc_pages": 92316496}, {"slot": "S02", "workload": "Varmail", "actual_seconds": 1803.0, "waf": 5.151739333571776, "host_bytes": 559333175296, "host_pages": 136555951, "gc_pages": 566944713, "process_runtimes_seconds": [1800.114]}, {"slot": "S03", "workload": "OLTP", "actual_seconds": 1810.0, "waf": 3.2108996446767866, "host_bytes": 289175076864, "host_pages": 70599384, "gc_pages": 156088153, "process_runtimes_seconds": [901.0939999999999, 900.8100000000001]}], "sample_rows": 184, "transition_count": 2, "measurement": "manual FTLpageWAF, hostbytes verified againstblockstat, no independentNANDmeasurement"}

- CAT60 continuation {"event": "started", "time": "2026-10-11T08:51:19.191299+09:00", "policy": "arm08", "attempt": "first", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm08-rep1", "module": {"path": "/home/oy/iCAT/buildoutput/nvmev-arm08.ko", "sha256": "1f9dfdfadac90ddbba9118a4dcdf78bfff615eb8149ffcf94cdf9c0f0a6d1fad", "vermagic": "7.0.0-31-generic SMP preempt mod_unload modversions", "k": 2, "scale_pct": 100, "age_ratio": 16, "provenance": "existingcurrentkernelmodule;source griddecode snapshotted;runtimeparamcheckmandatory"}, "phase_order": ["FIO-Fast", "Varmail", "OLTP"], "phase_seconds": 1800}

### cycle-20261007 mixX arm08 — started 2026-10-11T08:51:19+09:00

- mixX: (FIO-Fast, Varmail, OLTP) = 3 time-based phases of 1800 s. Table-3 prep, 6 GiB FIO file kept; FIO payload x 1800/600; Filebench files deleted after each Filebench phase; no YCSB. Module `nvmev-arm08.ko`.
- Command: `env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX arm08 1`; evidence `result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm08-rep1/`.

- Finished 2026-10-11T10:22:55+09:00; mixX arm08 exit=0; evidence `/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm08-rep1`; cleanup attempted.
- total host_bytes=1126226599936 host_pages=274957666 gc_pages=826802823 WAF=4.007019
- phaseA(test4) host_pages=72001978 gc_pages=92355546 WAF=2.282681
- phaseB(varmail) host_pages=132761866 gc_pages=567627572 WAF=5.275532
- phaseS01(test4) host_pages=72001978 gc_pages=92355546 WAF=2.282681
- phaseS02(varmail) host_pages=132761866 gc_pages=567627572 WAF=5.275532
- phaseS03(oltp) host_pages=70193821 gc_pages=166819705 WAF=3.376558
- ycsb-load 
- ycsb-run 

- CAT60 continuation {"event": "finished", "policy": "arm08", "runner_exit": 0, "finished_at": "2026-10-11T10:22:58.129691+09:00", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm08-rep1", "status": "validated_saved_evidence", "validation_exit": 0, "stage": "screen90", "waf": 4.007018625914579, "host_bytes": 1126226599936, "host_pages": 274957666, "gc_pages": 826802823, "actual_measured_seconds": 5413.0, "phases": [{"slot": "S01", "workload": "FIO-Fast", "actual_seconds": 1800.0, "waf": 2.282680678578025, "host_bytes": 294920101888, "host_pages": 72001978, "gc_pages": 92355546}, {"slot": "S02", "workload": "Varmail", "actual_seconds": 1804.0, "waf": 5.275531740417087, "host_bytes": 543792603136, "host_pages": 132761866, "gc_pages": 567627572, "process_runtimes_seconds": [1800.1119999999999]}, {"slot": "S03", "workload": "OLTP", "actual_seconds": 1809.0, "waf": 3.3765582585965794, "host_bytes": 287513890816, "host_pages": 70193821, "gc_pages": 166819705, "process_runtimes_seconds": [900.952, 900.921]}], "sample_rows": 184, "transition_count": 2, "measurement": "manual FTLpageWAF, hostbytes verified againstblockstat, no independentNANDmeasurement"}

- CAT60 continuation {"event": "started", "time": "2026-10-11T10:23:02.975508+09:00", "policy": "arm09", "attempt": "first", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm09-rep1", "module": {"path": "/home/oy/iCAT/buildoutput/nvmev-arm09.ko", "sha256": "f4f070ff06be5b8e97046aac05c982c1ac043173c368ed610af5078492a6dc74", "vermagic": "7.0.0-31-generic SMP preempt mod_unload modversions", "k": 2, "scale_pct": 200, "age_ratio": 4, "provenance": "existingcurrentkernelmodule;source griddecode snapshotted;runtimeparamcheckmandatory"}, "phase_order": ["FIO-Fast", "Varmail", "OLTP"], "phase_seconds": 1800}

### cycle-20261007 mixX arm09 — started 2026-10-11T10:23:02+09:00

- mixX: (FIO-Fast, Varmail, OLTP) = 3 time-based phases of 1800 s. Table-3 prep, 6 GiB FIO file kept; FIO payload x 1800/600; Filebench files deleted after each Filebench phase; no YCSB. Module `nvmev-arm09.ko`.
- Command: `env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX arm09 1`; evidence `result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm09-rep1/`.

- Finished 2026-10-11T11:54:38+09:00; mixX arm09 exit=0; evidence `/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm09-rep1`; cleanup attempted.
- total host_bytes=1099567546368 host_pages=268449108 gc_pages=845558877 WAF=4.149792
- phaseA(test4) host_pages=72001978 gc_pages=92312350 WAF=2.282081
- phaseB(varmail) host_pages=132139621 gc_pages=568499014 WAF=5.302260
- phaseS01(test4) host_pages=72001978 gc_pages=92312350 WAF=2.282081
- phaseS02(varmail) host_pages=132139621 gc_pages=568499014 WAF=5.302260
- phaseS03(oltp) host_pages=64307508 gc_pages=184747513 WAF=3.872876
- ycsb-load 
- ycsb-run 

- CAT60 continuation {"event": "finished", "policy": "arm09", "runner_exit": 0, "finished_at": "2026-10-11T11:54:39.054591+09:00", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm09-rep1", "status": "validated_saved_evidence", "validation_exit": 0, "stage": "screen90", "waf": 4.14979209020132, "host_bytes": 1099567546368, "host_pages": 268449108, "gc_pages": 845558877, "actual_measured_seconds": 5413.0, "phases": [{"slot": "S01", "workload": "FIO-Fast", "actual_seconds": 1800.0, "waf": 2.2820807506149343, "host_bytes": 294920101888, "host_pages": 72001978, "gc_pages": 92312350}, {"slot": "S02", "workload": "Varmail", "actual_seconds": 1804.0, "waf": 5.302260061726679, "host_bytes": 541243887616, "host_pages": 132139621, "gc_pages": 568499014, "process_runtimes_seconds": [1800.117]}, {"slot": "S03", "workload": "OLTP", "actual_seconds": 1809.0, "waf": 3.87287625886545, "host_bytes": 263403552768, "host_pages": 64307508, "gc_pages": 184747513, "process_runtimes_seconds": [901.117, 901.364]}], "sample_rows": 184, "transition_count": 2, "measurement": "manual FTLpageWAF, hostbytes verified againstblockstat, no independentNANDmeasurement"}

- CAT60 continuation {"event": "started", "time": "2026-10-11T11:54:43.835294+09:00", "policy": "arm10", "attempt": "first", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm10-rep1", "module": {"path": "/home/oy/iCAT/buildoutput/nvmev-arm10.ko", "sha256": "05e5e1e2654f527f67de009c93c6b5891611ce8f0f93f0bcc58aa6c910753482", "vermagic": "7.0.0-31-generic SMP preempt mod_unload modversions", "k": 2, "scale_pct": 200, "age_ratio": 7, "provenance": "existingcurrentkernelmodule;source griddecode snapshotted;runtimeparamcheckmandatory"}, "phase_order": ["FIO-Fast", "Varmail", "OLTP"], "phase_seconds": 1800}

### cycle-20261007 mixX arm10 — started 2026-10-11T11:54:43+09:00

- mixX: (FIO-Fast, Varmail, OLTP) = 3 time-based phases of 1800 s. Table-3 prep, 6 GiB FIO file kept; FIO payload x 1800/600; Filebench files deleted after each Filebench phase; no YCSB. Module `nvmev-arm10.ko`.
- Command: `env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX arm10 1`; evidence `result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm10-rep1/`.

- Finished 2026-10-11T13:26:20+09:00; mixX arm10 exit=0; evidence `/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm10-rep1`; cleanup attempted.
- total host_bytes=1107075125248 host_pages=270282013 gc_pages=858610694 WAF=4.176722
- phaseA(test4) host_pages=72028100 gc_pages=91278660 WAF=2.267265
- phaseB(varmail) host_pages=130484751 gc_pages=571611220 WAF=5.380674
- phaseS01(test4) host_pages=72028100 gc_pages=91278660 WAF=2.267265
- phaseS02(varmail) host_pages=130484751 gc_pages=571611220 WAF=5.380674
- phaseS03(oltp) host_pages=67769161 gc_pages=195720814 WAF=3.888051
- ycsb-load 
- ycsb-run 

- CAT60 continuation {"event": "finished", "policy": "arm10", "runner_exit": 0, "finished_at": "2026-10-11T13:26:22.930994+09:00", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm10-rep1", "status": "validated_saved_evidence", "validation_exit": 0, "stage": "screen90", "waf": 4.176721545284629, "host_bytes": 1107075125248, "host_pages": 270282013, "gc_pages": 858610694, "actual_measured_seconds": 5414.0, "phases": [{"slot": "S01", "workload": "FIO-Fast", "actual_seconds": 1800.0, "waf": 2.267264581461957, "host_bytes": 295027097600, "host_pages": 72028100, "gc_pages": 91278660}, {"slot": "S02", "workload": "Varmail", "actual_seconds": 1804.0, "waf": 5.380674489695735, "host_bytes": 534465540096, "host_pages": 130484751, "gc_pages": 571611220, "process_runtimes_seconds": [1800.112]}, {"slot": "S03", "workload": "OLTP", "actual_seconds": 1810.0, "waf": 3.8880513069949325, "host_bytes": 277582483456, "host_pages": 67769161, "gc_pages": 195720814, "process_runtimes_seconds": [901.093, 900.8330000000001]}], "sample_rows": 184, "transition_count": 2, "measurement": "manual FTLpageWAF, hostbytes verified againstblockstat, no independentNANDmeasurement"}

- CAT60 continuation {"event": "started", "time": "2026-10-11T13:26:28.170320+09:00", "policy": "arm11", "attempt": "first", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm11-rep1", "module": {"path": "/home/oy/iCAT/buildoutput/nvmev-arm11.ko", "sha256": "596778e682d72d0825b95ebc019ded637484262d77f206dd792e8de342452eff", "vermagic": "7.0.0-31-generic SMP preempt mod_unload modversions", "k": 2, "scale_pct": 200, "age_ratio": 16, "provenance": "existingcurrentkernelmodule;source griddecode snapshotted;runtimeparamcheckmandatory"}, "phase_order": ["FIO-Fast", "Varmail", "OLTP"], "phase_seconds": 1800}

### cycle-20261007 mixX arm11 — started 2026-10-11T13:26:28+09:00

- mixX: (FIO-Fast, Varmail, OLTP) = 3 time-based phases of 1800 s. Table-3 prep, 6 GiB FIO file kept; FIO payload x 1800/600; Filebench files deleted after each Filebench phase; no YCSB. Module `nvmev-arm11.ko`.
- Command: `env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX arm11 1`; evidence `result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm11-rep1/`.

- Finished 2026-10-11T14:58:06+09:00; mixX arm11 exit=0; evidence `/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm11-rep1`; cleanup attempted.
- total host_bytes=1084726206464 host_pages=264825734 gc_pages=848013589 WAF=4.202157
- phaseA(test4) host_pages=72001978 gc_pages=92372351 WAF=2.282914
- phaseB(varmail) host_pages=129245231 gc_pages=571802484 WAF=5.424167
- phaseS01(test4) host_pages=72001978 gc_pages=92372351 WAF=2.282914
- phaseS02(varmail) host_pages=129245231 gc_pages=571802484 WAF=5.424167
- phaseS03(oltp) host_pages=63578524 gc_pages=183838754 WAF=3.891523
- ycsb-load 
- ycsb-run 

- CAT60 continuation {"event": "finished", "policy": "arm11", "runner_exit": 0, "finished_at": "2026-10-11T14:58:07.389732+09:00", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm11-rep1", "status": "validated_saved_evidence", "validation_exit": 0, "stage": "screen90", "waf": 4.202157041883249, "host_bytes": 1084726206464, "host_pages": 264825734, "gc_pages": 848013589, "actual_measured_seconds": 5415.0, "phases": [{"slot": "S01", "workload": "FIO-Fast", "actual_seconds": 1801.0, "waf": 2.2829140749438857, "host_bytes": 294920101888, "host_pages": 72001978, "gc_pages": 92372351}, {"slot": "S02", "workload": "Varmail", "actual_seconds": 1804.0, "waf": 5.424166985318012, "host_bytes": 529388466176, "host_pages": 129245231, "gc_pages": 571802484, "process_runtimes_seconds": [1800.117]}, {"slot": "S03", "workload": "OLTP", "actual_seconds": 1810.0, "waf": 3.891522835604048, "host_bytes": 260417634304, "host_pages": 63578524, "gc_pages": 183838754, "process_runtimes_seconds": [901.179, 901.4110000000001]}], "sample_rows": 184, "transition_count": 2, "measurement": "manual FTLpageWAF, hostbytes verified againstblockstat, no independentNANDmeasurement"}

- CAT60 continuation {"event": "started", "time": "2026-10-11T14:58:12.130695+09:00", "policy": "arm12", "attempt": "first", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm12-rep1", "module": {"path": "/home/oy/iCAT/buildoutput/nvmev-arm12.ko", "sha256": "3d9ab2d2c7b44697944f4434b4107895b4fd5c6cd2bd1b9f14bd99b9cf5c87d0", "vermagic": "7.0.0-31-generic SMP preempt mod_unload modversions", "k": 2, "scale_pct": 400, "age_ratio": 4, "provenance": "existingcurrentkernelmodule;source griddecode snapshotted;runtimeparamcheckmandatory"}, "phase_order": ["FIO-Fast", "Varmail", "OLTP"], "phase_seconds": 1800}

### cycle-20261007 mixX arm12 — started 2026-10-11T14:58:12+09:00

- mixX: (FIO-Fast, Varmail, OLTP) = 3 time-based phases of 1800 s. Table-3 prep, 6 GiB FIO file kept; FIO payload x 1800/600; Filebench files deleted after each Filebench phase; no YCSB. Module `nvmev-arm12.ko`.
- Command: `env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX arm12 1`; evidence `result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm12-rep1/`.

- Finished 2026-10-11T16:29:47+09:00; mixX arm12 exit=0; evidence `/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm12-rep1`; cleanup attempted.
- total host_bytes=1085916250112 host_pages=265116272 gc_pages=914876238 WAF=4.450849
- phaseA(test4) host_pages=72002140 gc_pages=92375316 WAF=2.282952
- phaseB(varmail) host_pages=126315582 gc_pages=574545020 WAF=5.548489
- phaseS01(test4) host_pages=72002140 gc_pages=92375316 WAF=2.282952
- phaseS02(varmail) host_pages=126315582 gc_pages=574545020 WAF=5.548489
- phaseS03(oltp) host_pages=66798549 gc_pages=247955902 WAF=4.711995
- ycsb-load 
- ycsb-run 

- CAT60 continuation {"event": "finished", "policy": "arm12", "runner_exit": 0, "finished_at": "2026-10-11T16:29:48.181256+09:00", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm12-rep1", "status": "validated_saved_evidence", "validation_exit": 0, "stage": "screen90", "waf": 4.4508490599173784, "host_bytes": 1085916250112, "host_pages": 265116272, "gc_pages": 914876238, "actual_measured_seconds": 5413.0, "phases": [{"slot": "S01", "workload": "FIO-Fast", "actual_seconds": 1800.0, "waf": 2.2829523678046235, "host_bytes": 294920765440, "host_pages": 72002140, "gc_pages": 92375316}, {"slot": "S02", "workload": "Varmail", "actual_seconds": 1804.0, "waf": 5.548488879226317, "host_bytes": 517388623872, "host_pages": 126315582, "gc_pages": 574545020, "process_runtimes_seconds": [1800.117]}, {"slot": "S03", "workload": "OLTP", "actual_seconds": 1809.0, "waf": 4.711995330916544, "host_bytes": 273606856704, "host_pages": 66798549, "gc_pages": 247955902, "process_runtimes_seconds": [900.972, 900.859]}], "sample_rows": 184, "transition_count": 2, "measurement": "manual FTLpageWAF, hostbytes verified againstblockstat, no independentNANDmeasurement"}

- CAT60 continuation {"event": "started", "time": "2026-10-11T16:29:53.669880+09:00", "policy": "arm13", "attempt": "first", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm13-rep1", "module": {"path": "/home/oy/iCAT/buildoutput/nvmev-arm13.ko", "sha256": "ffe2f767dc808ab5f41a084f099d3a9d646a0068ac68ab6d23ddcf64941de715", "vermagic": "7.0.0-31-generic SMP preempt mod_unload modversions", "k": 2, "scale_pct": 400, "age_ratio": 7, "provenance": "existingcurrentkernelmodule;source griddecode snapshotted;runtimeparamcheckmandatory"}, "phase_order": ["FIO-Fast", "Varmail", "OLTP"], "phase_seconds": 1800}

### cycle-20261007 mixX arm13 — started 2026-10-11T16:29:53+09:00

- mixX: (FIO-Fast, Varmail, OLTP) = 3 time-based phases of 1800 s. Table-3 prep, 6 GiB FIO file kept; FIO payload x 1800/600; Filebench files deleted after each Filebench phase; no YCSB. Module `nvmev-arm13.ko`.
- Command: `env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX arm13 1`; evidence `result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm13-rep1/`.

- Finished 2026-10-11T18:01:30+09:00; mixX arm13 exit=0; evidence `/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm13-rep1`; cleanup attempted.
- total host_bytes=1128712388608 host_pages=275564548 gc_pages=863240620 WAF=4.132626
- phaseA(test4) host_pages=72001978 gc_pages=91219509 WAF=2.266903
- phaseB(varmail) host_pages=140272605 gc_pages=568326501 WAF=5.051586
- phaseS01(test4) host_pages=72001978 gc_pages=91219509 WAF=2.266903
- phaseS02(varmail) host_pages=140272605 gc_pages=568326501 WAF=5.051586
- phaseS03(oltp) host_pages=63289964 gc_pages=203694610 WAF=4.218435
- ycsb-load 
- ycsb-run 

- CAT60 continuation {"event": "finished", "policy": "arm13", "runner_exit": 0, "finished_at": "2026-10-11T18:01:33.013646+09:00", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm13-rep1", "status": "validated_saved_evidence", "validation_exit": 0, "stage": "screen90", "waf": 4.132625826744593, "host_bytes": 1128712388608, "host_pages": 275564548, "gc_pages": 863240620, "actual_measured_seconds": 5414.0, "phases": [{"slot": "S01", "workload": "FIO-Fast", "actual_seconds": 1800.0, "waf": 2.266902820364185, "host_bytes": 294920101888, "host_pages": 72001978, "gc_pages": 91219509}, {"slot": "S02", "workload": "Varmail", "actual_seconds": 1804.0, "waf": 5.051585846003216, "host_bytes": 574556590080, "host_pages": 140272605, "gc_pages": 568326501, "process_runtimes_seconds": [1800.1190000000001]}, {"slot": "S03", "workload": "OLTP", "actual_seconds": 1810.0, "waf": 4.2184346004684095, "host_bytes": 259235692544, "host_pages": 63289964, "gc_pages": 203694610, "process_runtimes_seconds": [901.355, 900.999]}], "sample_rows": 184, "transition_count": 2, "measurement": "manual FTLpageWAF, hostbytes verified againstblockstat, no independentNANDmeasurement"}

- CAT60 continuation {"event": "started", "time": "2026-10-11T18:01:39.065510+09:00", "policy": "arm14", "attempt": "first", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm14-rep1", "module": {"path": "/home/oy/iCAT/buildoutput/nvmev-arm14.ko", "sha256": "96c313c89665ad31893c4292e1817c24310bfb63f63c51cdcb76bb4cd07a009a", "vermagic": "7.0.0-31-generic SMP preempt mod_unload modversions", "k": 2, "scale_pct": 400, "age_ratio": 16, "provenance": "existingcurrentkernelmodule;source griddecode snapshotted;runtimeparamcheckmandatory"}, "phase_order": ["FIO-Fast", "Varmail", "OLTP"], "phase_seconds": 1800}

### cycle-20261007 mixX arm14 — started 2026-10-11T18:01:39+09:00

- mixX: (FIO-Fast, Varmail, OLTP) = 3 time-based phases of 1800 s. Table-3 prep, 6 GiB FIO file kept; FIO payload x 1800/600; Filebench files deleted after each Filebench phase; no YCSB. Module `nvmev-arm14.ko`.
- Command: `env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX arm14 1`; evidence `result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm14-rep1/`.

- Finished 2026-10-11T19:33:16+09:00; mixX arm14 exit=0; evidence `/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm14-rep1`; cleanup attempted.
- total host_bytes=1089437122560 host_pages=265975860 gc_pages=922081020 WAF=4.466785
- phaseA(test4) host_pages=72001981 gc_pages=92309597 WAF=2.282042
- phaseB(varmail) host_pages=126545915 gc_pages=578955271 WAF=5.575061
- phaseS01(test4) host_pages=72001981 gc_pages=92309597 WAF=2.282042
- phaseS02(varmail) host_pages=126545915 gc_pages=578955271 WAF=5.575061
- phaseS03(oltp) host_pages=67427963 gc_pages=250816152 WAF=4.719765
- ycsb-load 
- ycsb-run 

- CAT60 continuation {"event": "finished", "policy": "arm14", "runner_exit": 0, "finished_at": "2026-10-11T19:33:18.102266+09:00", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm14-rep1", "status": "validated_saved_evidence", "validation_exit": 0, "stage": "screen90", "waf": 4.466784617220525, "host_bytes": 1089437122560, "host_pages": 265975860, "gc_pages": 922081020, "actual_measured_seconds": 5414.0, "phases": [{"slot": "S01", "workload": "FIO-Fast", "actual_seconds": 1800.0, "waf": 2.282042462137257, "host_bytes": 294920114176, "host_pages": 72001981, "gc_pages": 92309597}, {"slot": "S02", "workload": "Varmail", "actual_seconds": 1804.0, "waf": 5.575060925514664, "host_bytes": 518332067840, "host_pages": 126545915, "gc_pages": 578955271, "process_runtimes_seconds": [1800.113]}, {"slot": "S03", "workload": "OLTP", "actual_seconds": 1810.0, "waf": 4.719764632367731, "host_bytes": 276184936448, "host_pages": 67427963, "gc_pages": 250816152, "process_runtimes_seconds": [901.179, 900.99]}], "sample_rows": 184, "transition_count": 2, "measurement": "manual FTLpageWAF, hostbytes verified againstblockstat, no independentNANDmeasurement"}

- CAT60 continuation {"event": "started", "time": "2026-10-11T19:33:23.818983+09:00", "policy": "arm15", "attempt": "first", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm15-rep1", "module": {"path": "/home/oy/iCAT/buildoutput/nvmev-arm15.ko", "sha256": "9001b1b4b9416d99838942029d00f8c1ae633ed3b629150e07ef8f55d4dee6cc", "vermagic": "7.0.0-31-generic SMP preempt mod_unload modversions", "k": 4, "scale_pct": 25, "age_ratio": 4, "provenance": "existingcurrentkernelmodule;source griddecode snapshotted;runtimeparamcheckmandatory"}, "phase_order": ["FIO-Fast", "Varmail", "OLTP"], "phase_seconds": 1800}

### cycle-20261007 mixX arm15 — started 2026-10-11T19:33:23+09:00

- mixX: (FIO-Fast, Varmail, OLTP) = 3 time-based phases of 1800 s. Table-3 prep, 6 GiB FIO file kept; FIO payload x 1800/600; Filebench files deleted after each Filebench phase; no YCSB. Module `nvmev-arm15.ko`.
- Command: `env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX arm15 1`; evidence `result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm15-rep1/`.

- Finished 2026-10-11T21:04:59+09:00; mixX arm15 exit=0; evidence `/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm15-rep1`; cleanup attempted.
- total host_bytes=1447738310656 host_pages=353451736 gc_pages=588832744 WAF=2.665950
- phaseA(test4) host_pages=72029131 gc_pages=62668564 WAF=1.870045
- phaseB(varmail) host_pages=209638466 gc_pages=476572899 WAF=3.273308
- phaseS01(test4) host_pages=72029131 gc_pages=62668564 WAF=1.870045
- phaseS02(varmail) host_pages=209638466 gc_pages=476572899 WAF=3.273308
- phaseS03(oltp) host_pages=71784138 gc_pages=49591281 WAF=1.690839
- ycsb-load 
- ycsb-run 

- CAT60 continuation {"event": "finished", "policy": "arm15", "runner_exit": 0, "finished_at": "2026-10-11T21:04:59.896299+09:00", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm15-rep1", "status": "validated_saved_evidence", "validation_exit": 0, "stage": "screen90", "waf": 2.6659495032159075, "host_bytes": 1447738310656, "host_pages": 353451736, "gc_pages": 588832744, "actual_measured_seconds": 5413.0, "phases": [{"slot": "S01", "workload": "FIO-Fast", "actual_seconds": 1800.0, "waf": 1.8700447045515514, "host_bytes": 295031320576, "host_pages": 72029131, "gc_pages": 62668564}, {"slot": "S02", "workload": "Varmail", "actual_seconds": 1804.0, "waf": 3.2733084633427914, "host_bytes": 858679156736, "host_pages": 209638466, "gc_pages": 476572899, "process_runtimes_seconds": [1800.116]}, {"slot": "S03", "workload": "OLTP", "actual_seconds": 1809.0, "waf": 1.6908389845121494, "host_bytes": 294027829248, "host_pages": 71784138, "gc_pages": 49591281, "process_runtimes_seconds": [900.962, 900.931]}], "sample_rows": 184, "transition_count": 2, "measurement": "manual FTLpageWAF, hostbytes verified againstblockstat, no independentNANDmeasurement"}

- CAT60 continuation {"event": "started", "time": "2026-10-11T21:05:05.729481+09:00", "policy": "arm16", "attempt": "first", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm16-rep1", "module": {"path": "/home/oy/iCAT/buildoutput/nvmev-arm16.ko", "sha256": "60f019a15e970243c79686a288e30ff50a6555464d42186f18aa4e29c1d5718f", "vermagic": "7.0.0-31-generic SMP preempt mod_unload modversions", "k": 4, "scale_pct": 25, "age_ratio": 7, "provenance": "existingcurrentkernelmodule;source griddecode snapshotted;runtimeparamcheckmandatory"}, "phase_order": ["FIO-Fast", "Varmail", "OLTP"], "phase_seconds": 1800}

### cycle-20261007 mixX arm16 — started 2026-10-11T21:05:05+09:00

- mixX: (FIO-Fast, Varmail, OLTP) = 3 time-based phases of 1800 s. Table-3 prep, 6 GiB FIO file kept; FIO payload x 1800/600; Filebench files deleted after each Filebench phase; no YCSB. Module `nvmev-arm16.ko`.
- Command: `env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX arm16 1`; evidence `result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm16-rep1/`.

- Finished 2026-10-11T22:36:42+09:00; mixX arm16 exit=0; evidence `/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm16-rep1`; cleanup attempted.
- total host_bytes=1465627561984 host_pages=357819229 gc_pages=546244905 WAF=2.526595
- phaseA(test4) host_pages=72013741 gc_pages=60091026 WAF=1.834438
- phaseB(varmail) host_pages=214463547 gc_pages=450299186 WAF=3.099654
- phaseS01(test4) host_pages=72013741 gc_pages=60091026 WAF=1.834438
- phaseS02(varmail) host_pages=214463547 gc_pages=450299186 WAF=3.099654
- phaseS03(oltp) host_pages=71341940 gc_pages=35854693 WAF=1.502575
- ycsb-load 
- ycsb-run 

- CAT60 continuation {"event": "finished", "policy": "arm16", "runner_exit": 0, "finished_at": "2026-10-11T22:36:45.290145+09:00", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm16-rep1", "status": "validated_saved_evidence", "validation_exit": 0, "stage": "screen90", "waf": 2.526594606239007, "host_bytes": 1465627561984, "host_pages": 357819229, "gc_pages": 546244905, "actual_measured_seconds": 5414.0, "phases": [{"slot": "S01", "workload": "FIO-Fast", "actual_seconds": 1800.0, "waf": 1.8344383330953464, "host_bytes": 294968283136, "host_pages": 72013741, "gc_pages": 60091026}, {"slot": "S02", "workload": "Varmail", "actual_seconds": 1804.0, "waf": 3.0996537280995358, "host_bytes": 878442688512, "host_pages": 214463547, "gc_pages": 450299186, "process_runtimes_seconds": [1800.121]}, {"slot": "S03", "workload": "OLTP", "actual_seconds": 1810.0, "waf": 1.5025752453605832, "host_bytes": 292216586240, "host_pages": 71341940, "gc_pages": 35854693, "process_runtimes_seconds": [901.361, 901.08]}], "sample_rows": 184, "transition_count": 2, "measurement": "manual FTLpageWAF, hostbytes verified againstblockstat, no independentNANDmeasurement"}

- CAT60 continuation {"event": "started", "time": "2026-10-11T22:36:51.471736+09:00", "policy": "arm17", "attempt": "first", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm17-rep1", "module": {"path": "/home/oy/iCAT/buildoutput/nvmev-arm17.ko", "sha256": "6a9ec9664ce49458fb7067cd328afd20f73e61a5a2b5940d4d08635bda1adfaf", "vermagic": "7.0.0-31-generic SMP preempt mod_unload modversions", "k": 4, "scale_pct": 25, "age_ratio": 16, "provenance": "existingcurrentkernelmodule;source griddecode snapshotted;runtimeparamcheckmandatory"}, "phase_order": ["FIO-Fast", "Varmail", "OLTP"], "phase_seconds": 1800}

### cycle-20261007 mixX arm17 — started 2026-10-11T22:36:51+09:00

- mixX: (FIO-Fast, Varmail, OLTP) = 3 time-based phases of 1800 s. Table-3 prep, 6 GiB FIO file kept; FIO payload x 1800/600; Filebench files deleted after each Filebench phase; no YCSB. Module `nvmev-arm17.ko`.
- Command: `env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX arm17 1`; evidence `result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm17-rep1/`.

- Finished 2026-10-12T00:08:28+09:00; mixX arm17 exit=0; evidence `/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm17-rep1`; cleanup attempted.
- total host_bytes=1594311725056 host_pages=389236261 gc_pages=547745186 WAF=2.407231
- phaseA(test4) host_pages=72001978 gc_pages=62713157 WAF=1.870992
- phaseB(varmail) host_pages=242531049 gc_pages=456402234 WAF=2.881830
- phaseS01(test4) host_pages=72001978 gc_pages=62713157 WAF=1.870992
- phaseS02(varmail) host_pages=242531049 gc_pages=456402234 WAF=2.881830
- phaseS03(oltp) host_pages=74703233 gc_pages=28629795 WAF=1.383247
- ycsb-load 
- ycsb-run 

- CAT60 continuation {"event": "finished", "policy": "arm17", "runner_exit": 0, "finished_at": "2026-10-12T00:08:30.574703+09:00", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm17-rep1", "status": "validated_saved_evidence", "validation_exit": 0, "stage": "screen90", "waf": 2.4072306228427163, "host_bytes": 1594311725056, "host_pages": 389236261, "gc_pages": 547745186, "actual_measured_seconds": 5415.0, "phases": [{"slot": "S01", "workload": "FIO-Fast", "actual_seconds": 1801.0, "waf": 1.8709921413547832, "host_bytes": 294920101888, "host_pages": 72001978, "gc_pages": 62713157}, {"slot": "S02", "workload": "Varmail", "actual_seconds": 1803.0, "waf": 2.8818301239442543, "host_bytes": 993407176704, "host_pages": 242531049, "gc_pages": 456402234, "process_runtimes_seconds": [1800.118]}, {"slot": "S03", "workload": "OLTP", "actual_seconds": 1811.0, "waf": 1.3832470677674686, "host_bytes": 305984442368, "host_pages": 74703233, "gc_pages": 28629795, "process_runtimes_seconds": [900.975, 900.939]}], "sample_rows": 184, "transition_count": 2, "measurement": "manual FTLpageWAF, hostbytes verified againstblockstat, no independentNANDmeasurement"}

- CAT60 continuation {"event": "started", "time": "2026-10-12T00:08:37.236623+09:00", "policy": "arm18", "attempt": "first", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm18-rep1", "module": {"path": "/home/oy/iCAT/buildoutput/nvmev-arm18.ko", "sha256": "f680b834b05029dc2632cb524f0bc182316e07184a02d1befa1f0fdd97c1e008", "vermagic": "7.0.0-31-generic SMP preempt mod_unload modversions", "k": 4, "scale_pct": 50, "age_ratio": 4, "provenance": "existingcurrentkernelmodule;source griddecode snapshotted;runtimeparamcheckmandatory"}, "phase_order": ["FIO-Fast", "Varmail", "OLTP"], "phase_seconds": 1800}

### cycle-20261007 mixX arm18 — started 2026-10-12T00:08:37+09:00

- mixX: (FIO-Fast, Varmail, OLTP) = 3 time-based phases of 1800 s. Table-3 prep, 6 GiB FIO file kept; FIO payload x 1800/600; Filebench files deleted after each Filebench phase; no YCSB. Module `nvmev-arm18.ko`.
- Command: `env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX arm18 1`; evidence `result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm18-rep1/`.

- Finished 2026-10-12T01:40:14+09:00; mixX arm18 exit=0; evidence `/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm18-rep1`; cleanup attempted.
- total host_bytes=1397214232576 host_pages=341116756 gc_pages=609562486 WAF=2.786961
- phaseA(test4) host_pages=72001978 gc_pages=71146530 WAF=1.988119
- phaseB(varmail) host_pages=199004850 gc_pages=486085979 WAF=3.442584
- phaseS01(test4) host_pages=72001978 gc_pages=71146530 WAF=1.988119
- phaseS02(varmail) host_pages=199004850 gc_pages=486085979 WAF=3.442584
- phaseS03(oltp) host_pages=70109927 gc_pages=52329977 WAF=1.746399
- ycsb-load 
- ycsb-run 

- CAT60 continuation {"event": "finished", "policy": "arm18", "runner_exit": 0, "finished_at": "2026-10-12T01:40:16.245186+09:00", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm18-rep1", "status": "validated_saved_evidence", "validation_exit": 0, "stage": "screen90", "waf": 2.7869614297105945, "host_bytes": 1397214232576, "host_pages": 341116756, "gc_pages": 609562486, "actual_measured_seconds": 5414.0, "phases": [{"slot": "S01", "workload": "FIO-Fast", "actual_seconds": 1800.0, "waf": 1.9881191041723882, "host_bytes": 294920101888, "host_pages": 72001978, "gc_pages": 71146530}, {"slot": "S02", "workload": "Varmail", "actual_seconds": 1804.0, "waf": 3.4425835802494262, "host_bytes": 815123865600, "host_pages": 199004850, "gc_pages": 486085979, "process_runtimes_seconds": [1800.117]}, {"slot": "S03", "workload": "OLTP", "actual_seconds": 1810.0, "waf": 1.7463989657270647, "host_bytes": 287170260992, "host_pages": 70109927, "gc_pages": 52329977, "process_runtimes_seconds": [901.004, 901.0749999999999]}], "sample_rows": 184, "transition_count": 2, "measurement": "manual FTLpageWAF, hostbytes verified againstblockstat, no independentNANDmeasurement"}

- CAT60 continuation {"event": "started", "time": "2026-10-12T01:40:22.663022+09:00", "policy": "arm19", "attempt": "first", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm19-rep1", "module": {"path": "/home/oy/iCAT/buildoutput/nvmev-arm19.ko", "sha256": "7c1cd15170a2e8f79e98f2a258b479242ce57a31582b68e80036e113d05a881c", "vermagic": "7.0.0-31-generic SMP preempt mod_unload modversions", "k": 4, "scale_pct": 50, "age_ratio": 7, "provenance": "existingcurrentkernelmodule;source griddecode snapshotted;runtimeparamcheckmandatory"}, "phase_order": ["FIO-Fast", "Varmail", "OLTP"], "phase_seconds": 1800}

### cycle-20261007 mixX arm19 — started 2026-10-12T01:40:22+09:00

- mixX: (FIO-Fast, Varmail, OLTP) = 3 time-based phases of 1800 s. Table-3 prep, 6 GiB FIO file kept; FIO payload x 1800/600; Filebench files deleted after each Filebench phase; no YCSB. Module `nvmev-arm19.ko`.
- Command: `env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX arm19 1`; evidence `result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm19-rep1/`.

- Finished 2026-10-12T03:11:59+09:00; mixX arm19 exit=0; evidence `/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm19-rep1`; cleanup attempted.
- total host_bytes=1429071597568 host_pages=348894433 gc_pages=593967522 WAF=2.702428
- phaseA(test4) host_pages=72001978 gc_pages=67480449 WAF=1.937203
- phaseB(varmail) host_pages=206339823 gc_pages=487087555 WAF=3.360609
- phaseS01(test4) host_pages=72001978 gc_pages=67480449 WAF=1.937203
- phaseS02(varmail) host_pages=206339823 gc_pages=487087555 WAF=3.360609
- phaseS03(oltp) host_pages=70552631 gc_pages=39399518 WAF=1.558442
- ycsb-load 
- ycsb-run 

- CAT60 continuation {"event": "finished", "policy": "arm19", "runner_exit": 0, "finished_at": "2026-10-12T03:12:01.883329+09:00", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm19-rep1", "status": "validated_saved_evidence", "validation_exit": 0, "stage": "screen90", "waf": 2.702427628015492, "host_bytes": 1429071597568, "host_pages": 348894433, "gc_pages": 593967522, "actual_measured_seconds": 5414.0, "phases": [{"slot": "S01", "workload": "FIO-Fast", "actual_seconds": 1800.0, "waf": 1.9372027112921815, "host_bytes": 294920101888, "host_pages": 72001978, "gc_pages": 67480449}, {"slot": "S02", "workload": "Varmail", "actual_seconds": 1804.0, "waf": 3.3606085723937063, "host_bytes": 845167915008, "host_pages": 206339823, "gc_pages": 487087555, "process_runtimes_seconds": [1800.1180000000002]}, {"slot": "S03", "workload": "OLTP", "actual_seconds": 1810.0, "waf": 1.5584415129749023, "host_bytes": 288983576576, "host_pages": 70552631, "gc_pages": 39399518, "process_runtimes_seconds": [900.92, 900.957]}], "sample_rows": 184, "transition_count": 2, "measurement": "manual FTLpageWAF, hostbytes verified againstblockstat, no independentNANDmeasurement"}

- CAT60 continuation {"event": "started", "time": "2026-10-12T03:12:08.680968+09:00", "policy": "arm20", "attempt": "first", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm20-rep1", "module": {"path": "/home/oy/iCAT/buildoutput/nvmev-arm20.ko", "sha256": "ed673daf5a5dabe516d06c2b2b040448103e8f73535d56ceaa0b316f59c7f789", "vermagic": "7.0.0-31-generic SMP preempt mod_unload modversions", "k": 4, "scale_pct": 50, "age_ratio": 16, "provenance": "existingcurrentkernelmodule;source griddecode snapshotted;runtimeparamcheckmandatory"}, "phase_order": ["FIO-Fast", "Varmail", "OLTP"], "phase_seconds": 1800}

### cycle-20261007 mixX arm20 — started 2026-10-12T03:12:08+09:00

- mixX: (FIO-Fast, Varmail, OLTP) = 3 time-based phases of 1800 s. Table-3 prep, 6 GiB FIO file kept; FIO payload x 1800/600; Filebench files deleted after each Filebench phase; no YCSB. Module `nvmev-arm20.ko`.
- Command: `env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX arm20 1`; evidence `result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm20-rep1/`.

- Finished 2026-10-12T04:43:45+09:00; mixX arm20 exit=0; evidence `/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm20-rep1`; cleanup attempted.
- total host_bytes=1466208632832 host_pages=357961092 gc_pages=581649496 WAF=2.624896
- phaseA(test4) host_pages=72024511 gc_pages=66908919 WAF=1.928974
- phaseB(varmail) host_pages=211329585 gc_pages=481834900 WAF=3.280016
- phaseS01(test4) host_pages=72024511 gc_pages=66908919 WAF=1.928974
- phaseS02(varmail) host_pages=211329585 gc_pages=481834900 WAF=3.280016
- phaseS03(oltp) host_pages=74606995 gc_pages=32905677 WAF=1.441054
- ycsb-load 
- ycsb-run 

- CAT60 continuation {"event": "finished", "policy": "arm20", "runner_exit": 0, "finished_at": "2026-10-12T04:43:48.080693+09:00", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm20-rep1", "status": "validated_saved_evidence", "validation_exit": 0, "stage": "screen90", "waf": 2.6248958587935025, "host_bytes": 1466208632832, "host_pages": 357961092, "gc_pages": 581649496, "actual_measured_seconds": 5414.0, "phases": [{"slot": "S01", "workload": "FIO-Fast", "actual_seconds": 1800.0, "waf": 1.928974290432878, "host_bytes": 295012397056, "host_pages": 72024511, "gc_pages": 66908919}, {"slot": "S02", "workload": "Varmail", "actual_seconds": 1804.0, "waf": 3.280016307229298, "host_bytes": 865605980160, "host_pages": 211329585, "gc_pages": 481834900, "process_runtimes_seconds": [1800.117]}, {"slot": "S03", "workload": "OLTP", "actual_seconds": 1810.0, "waf": 1.4410535097948927, "host_bytes": 305590251520, "host_pages": 74606995, "gc_pages": 32905677, "process_runtimes_seconds": [901.017, 901.2]}], "sample_rows": 184, "transition_count": 2, "measurement": "manual FTLpageWAF, hostbytes verified againstblockstat, no independentNANDmeasurement"}

- CAT60 continuation {"event": "started", "time": "2026-10-12T04:43:54.737568+09:00", "policy": "arm21", "attempt": "first", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm21-rep1", "module": {"path": "/home/oy/iCAT/buildoutput/nvmev-arm21.ko", "sha256": "8ef547766343596b2c5d0b4a2278e21fafc5ce53a04e4614b93c7cacf543b0c4", "vermagic": "7.0.0-31-generic SMP preempt mod_unload modversions", "k": 4, "scale_pct": 100, "age_ratio": 4, "provenance": "existingcurrentkernelmodule;source griddecode snapshotted;runtimeparamcheckmandatory"}, "phase_order": ["FIO-Fast", "Varmail", "OLTP"], "phase_seconds": 1800}

### cycle-20261007 mixX arm21 — started 2026-10-12T04:43:54+09:00

- mixX: (FIO-Fast, Varmail, OLTP) = 3 time-based phases of 1800 s. Table-3 prep, 6 GiB FIO file kept; FIO payload x 1800/600; Filebench files deleted after each Filebench phase; no YCSB. Module `nvmev-arm21.ko`.
- Command: `env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX arm21 1`; evidence `result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm21-rep1/`.

- Finished 2026-10-12T06:15:31+09:00; mixX arm21 exit=0; evidence `/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm21-rep1`; cleanup attempted.
- total host_bytes=1323998801920 host_pages=323241895 gc_pages=648555036 WAF=3.006408
- phaseA(test4) host_pages=72026560 gc_pages=82950477 WAF=2.151665
- phaseB(varmail) host_pages=183257514 gc_pages=506121201 WAF=3.761803
- phaseS01(test4) host_pages=72026560 gc_pages=82950477 WAF=2.151665
- phaseS02(varmail) host_pages=183257514 gc_pages=506121201 WAF=3.761803
- phaseS03(oltp) host_pages=67957820 gc_pages=59483320 WAF=1.875298
- ycsb-load 
- ycsb-run 

- CAT60 continuation {"event": "finished", "policy": "arm21", "runner_exit": 0, "finished_at": "2026-10-12T06:15:34.514115+09:00", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm21-rep1", "status": "validated_saved_evidence", "validation_exit": 0, "stage": "screen90", "waf": 3.0064077275626664, "host_bytes": 1323998801920, "host_pages": 323241895, "gc_pages": 648555036, "actual_measured_seconds": 5414.0, "phases": [{"slot": "S01", "workload": "FIO-Fast", "actual_seconds": 1800.0, "waf": 2.1516651218661558, "host_bytes": 295020789760, "host_pages": 72026560, "gc_pages": 82950477}, {"slot": "S02", "workload": "Varmail", "actual_seconds": 1804.0, "waf": 3.7618032677230357, "host_bytes": 750622777344, "host_pages": 183257514, "gc_pages": 506121201, "process_runtimes_seconds": [1800.1190000000001]}, {"slot": "S03", "workload": "OLTP", "actual_seconds": 1810.0, "waf": 1.8752976478645136, "host_bytes": 278355230720, "host_pages": 67957820, "gc_pages": 59483320, "process_runtimes_seconds": [901.257, 901.373]}], "sample_rows": 184, "transition_count": 2, "measurement": "manual FTLpageWAF, hostbytes verified againstblockstat, no independentNANDmeasurement"}

- CAT60 continuation {"event": "started", "time": "2026-10-12T06:15:41.624448+09:00", "policy": "arm22", "attempt": "first", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm22-rep1", "module": {"path": "/home/oy/iCAT/buildoutput/nvmev-arm22.ko", "sha256": "399c51787aeb10a5cfb2278d861b33f17982ab76e2f5a7442be839f3338588e0", "vermagic": "7.0.0-31-generic SMP preempt mod_unload modversions", "k": 4, "scale_pct": 100, "age_ratio": 7, "provenance": "existingcurrentkernelmodule;source griddecode snapshotted;runtimeparamcheckmandatory"}, "phase_order": ["FIO-Fast", "Varmail", "OLTP"], "phase_seconds": 1800}

### cycle-20261007 mixX arm22 — started 2026-10-12T06:15:41+09:00

- mixX: (FIO-Fast, Varmail, OLTP) = 3 time-based phases of 1800 s. Table-3 prep, 6 GiB FIO file kept; FIO payload x 1800/600; Filebench files deleted after each Filebench phase; no YCSB. Module `nvmev-arm22.ko`.
- Command: `env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX arm22 1`; evidence `result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm22-rep1/`.

- Finished 2026-10-12T07:47:19+09:00; mixX arm22 exit=0; evidence `/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm22-rep1`; cleanup attempted.
- total host_bytes=1349904228352 host_pages=329566462 gc_pages=628719216 WAF=2.907716
- phaseA(test4) host_pages=72001978 gc_pages=81356569 WAF=2.129921
- phaseB(varmail) host_pages=189667513 gc_pages=502814180 WAF=3.651030
- phaseS01(test4) host_pages=72001978 gc_pages=81356569 WAF=2.129921
- phaseS02(varmail) host_pages=189667513 gc_pages=502814180 WAF=3.651030
- phaseS03(oltp) host_pages=67896970 gc_pages=44548467 WAF=1.656119
- ycsb-load 
- ycsb-run 

- CAT60 continuation {"event": "finished", "policy": "arm22", "runner_exit": 0, "finished_at": "2026-10-12T07:47:21.163353+09:00", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm22-rep1", "status": "validated_saved_evidence", "validation_exit": 0, "stage": "screen90", "waf": 2.9077160102534947, "host_bytes": 1349904228352, "host_pages": 329566462, "gc_pages": 628719216, "actual_measured_seconds": 5414.0, "phases": [{"slot": "S01", "workload": "FIO-Fast", "actual_seconds": 1800.0, "waf": 2.129921305773016, "host_bytes": 294920101888, "host_pages": 72001978, "gc_pages": 81356569}, {"slot": "S02", "workload": "Varmail", "actual_seconds": 1804.0, "waf": 3.6510295413637865, "host_bytes": 776878133248, "host_pages": 189667513, "gc_pages": 502814180, "process_runtimes_seconds": [1800.1209999999999]}, {"slot": "S03", "workload": "OLTP", "actual_seconds": 1810.0, "waf": 1.6561186309197597, "host_bytes": 278105989120, "host_pages": 67896970, "gc_pages": 44548467, "process_runtimes_seconds": [901.3620000000001, 901.111]}], "sample_rows": 184, "transition_count": 2, "measurement": "manual FTLpageWAF, hostbytes verified againstblockstat, no independentNANDmeasurement"}

- CAT60 continuation {"event": "started", "time": "2026-10-12T07:47:28.179900+09:00", "policy": "arm23", "attempt": "first", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm23-rep1", "module": {"path": "/home/oy/iCAT/buildoutput/nvmev-arm23.ko", "sha256": "2400a0a3f89559ea174f63e8ed32e80e9bfb6750eea1d3a0e5678ec74fba5c94", "vermagic": "7.0.0-31-generic SMP preempt mod_unload modversions", "k": 4, "scale_pct": 100, "age_ratio": 16, "provenance": "existingcurrentkernelmodule;source griddecode snapshotted;runtimeparamcheckmandatory"}, "phase_order": ["FIO-Fast", "Varmail", "OLTP"], "phase_seconds": 1800}

### cycle-20261007 mixX arm23 — started 2026-10-12T07:47:28+09:00

- mixX: (FIO-Fast, Varmail, OLTP) = 3 time-based phases of 1800 s. Table-3 prep, 6 GiB FIO file kept; FIO payload x 1800/600; Filebench files deleted after each Filebench phase; no YCSB. Module `nvmev-arm23.ko`.
- Command: `env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX arm23 1`; evidence `result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm23-rep1/`.

- Finished 2026-10-12T09:19:05+09:00; mixX arm23 exit=0; evidence `/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm23-rep1`; cleanup attempted.
- total host_bytes=1371903819776 host_pages=334937456 gc_pages=628425417 WAF=2.876247
- phaseA(test4) host_pages=72001978 gc_pages=80793669 WAF=2.122103
- phaseB(varmail) host_pages=192789228 gc_pages=511081385 WAF=3.650985
- phaseS01(test4) host_pages=72001978 gc_pages=80793669 WAF=2.122103
- phaseS02(varmail) host_pages=192789228 gc_pages=511081385 WAF=3.650985
- phaseS03(oltp) host_pages=70146249 gc_pages=36550363 WAF=1.521059
- ycsb-load 
- ycsb-run 

- CAT60 continuation {"event": "finished", "policy": "arm23", "runner_exit": 0, "finished_at": "2026-10-12T09:19:07.648996+09:00", "raw_path": "/home/oy/iCAT/result/mixX-cat60-90min-20261009/resume-20261011/mixX-arm23-rep1", "status": "validated_saved_evidence", "validation_exit": 0, "stage": "screen90", "waf": 2.876247059689854, "host_bytes": 1371903819776, "host_pages": 334937456, "gc_pages": 628425417, "actual_measured_seconds": 5415.0, "phases": [{"slot": "S01", "workload": "FIO-Fast", "actual_seconds": 1800.0, "waf": 2.12210346499092, "host_bytes": 294920101888, "host_pages": 72001978, "gc_pages": 80793669}, {"slot": "S02", "workload": "Varmail", "actual_seconds": 1804.0, "waf": 3.6509851733002425, "host_bytes": 789664677888, "host_pages": 192789228, "gc_pages": 511081385, "process_runtimes_seconds": [1800.122]}, {"slot": "S03", "workload": "OLTP", "actual_seconds": 1811.0, "waf": 1.5210594083227458, "host_bytes": 287319035904, "host_pages": 70146249, "gc_pages": 36550363, "process_runtimes_seconds": [901.432, 901.167]}], "sample_rows": 184, "transition_count": 2, "measurement": "manual FTLpageWAF, hostbytes verified againstblockstat, no independentNANDmeasurement"}
