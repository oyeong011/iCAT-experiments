
### mixF fixed50 ten-hour preregistration 2026-10-04T00:16:20.862402+09:00
Command: env MULT=30 VM_RUN=900 VM_CHUNKS=20 bash script/mix-20260911.sh mixF fixed50 1
Purpose: robust CAT50 same-host comparison to default37; run after mixF37. Same immutable latest4557a685 runner, preparation6GiB+3GiB, manual=1, FIO seeds20260911/20261011/20261111, prep20260907, FIO nominal5h requested2949120000000bytes thenVarmail18000s; 30sec counters. Only policy/module differs; exact moduleSHA/kernel/machine_id/hostname in metadata. Same fio/error/bytes/runtime, start/stop/blockstat, partition and policy validation as37. All failed evidence retained. Push icat-2 at completion. Global lock and NVMeVirt guard mandatory. Estimated start10:20 Oct4, finish20:25 Oct4 KST depending on37.

### mix-20260911 mixF fixed50 — started 2026-10-04T10:18:56+09:00

- Phase A fio test4 fixed payload (1769472000000/884736000000/294912000000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixF fixed50`; evidence `result/mix-20260911/mixF-fixed50/`.

- Finished 2026-10-04T20:20:25+09:00; mixF fixed50 exit=0; evidence `/home/oy/iCAT/result/mixF-fixed50-tenhour-20261004/mixF-fixed50-rep1-x30`; cleanup attempted.
- total host_bytes=13382190190592 host_pages=3267136277 gc_pages=4399213881 WAF=2.346505
- phaseA(test4) host_pages=720043891 gc_pages=587712678 WAF=1.816218
- phaseB(varmail) host_pages=2547092386 gc_pages=3811501203 WAF=2.496413
- ycsb-load 
- ycsb-run 

- FINISHED {"run_id": "mixF-fixed50-tenhour-20261004", "exit_code": 0, "sample_rows": 1203, "started_at": "2026-10-04T10:18:56.810911+09:00", "finished_at": "2026-10-04T20:20:26.419331+09:00", "raw_path": "/home/oy/iCAT/result/mixF-fixed50-tenhour-20261004/mixF-fixed50-rep1-x30", "measurement": "manual continuous FIO-Fast MULT30 -> Varmail18000", "hostname": "oy-B550M-DS3H", "machine_id": "f4f3e77cb5bf4a08ab288227cf288de0", "source_commit": "4557a68510759320b79d083977959ffe16d6a5d8", "module_sha256": "f476acff890da8e28ce745ec3f2cf2b0eced8cb33752d99b40a093178511b5b6", "waf": 2.3465045556775834, "host_bytes": 13382190190592, "host_pages": 3267136277, "gc_pages": 4399213881, "phases": [{"slot": "A", "actual_seconds": 18000.0, "profile": "mix-test4.fio", "requested_write_bytes": 2949120000000, "duration_note": "fixed I/O amount at rate caps; actual duration may exceed five hours"}, {"slot": "B", "actual_seconds": 18005.0, "profile": "varmail.f"}], "actual_measured_seconds": 36005.0, "issues": [], "status": "validated_saved_evidence"}
