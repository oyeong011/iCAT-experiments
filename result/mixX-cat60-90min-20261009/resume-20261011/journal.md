
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
