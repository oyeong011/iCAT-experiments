
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
