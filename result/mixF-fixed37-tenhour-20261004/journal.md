
### mixF-fixed37-tenhour-20261004 preregistration 2026-10-04T00:08:02.602657+09:00

Command: `env MULT=30 VM_RUN=900 VM_CHUNKS=20 bash script/mix-20260911.sh mixF fixed37 1`. Latest main 4557a68510759320b79d083977959ffe16d6a5d8 pulled in clean icat-2 worktree. Measurement snapshot differs only by documented physical-controller compatibility check using strong NVMeVirt guard. Purpose: CAT37 baseline for 10h mixF. Wait for existing CAT50 then v4, single shared device lock; no concurrent experiments. Expected ~10h plus preparation, estimated Oct4 18:40 -> Oct5 04:45 KST dependent on predecessors.

FIO A fixed write amounts hot1769472000000/warm884736000000/cold294912000000 bytes at24000/12000/4000 IOPS imply nominal18000s; actual wall time can be longer and is recorded, not forced. B Varmail one18000s process because profile has no reuse. Same6GiB+3GiB preparation outside counters, seed20260907; workload seeds20260911/20261011/20261111. module fixed37 SHA/kernel and machine_id/hostname in metadata/module-info; build-option equivalence to another host remains unconfirmed.

Acceptance: exit0, fio all errors0 and every requested write byte complete, zero prepared/start counters, final/stopped equality and partition totals, block-stat match asserted by runner, Varmail one IO Summary with actual runtime, policy37 evidence. Save 30s raw counters/WAF including active/preparation distinction, actual time and final totals. Retain failures. Publish only this campaign to icat-2 after validation. Existing source changes/results preserved; global mount/module/model/serial/PCI protection applied.

- 2026-10-04T00:15:30.481498+09:00 USER PRIORITY CHANGE: cancel old mixO queue; stop active mixO fixed50 preserving incomplete evidence; run mixF fixed37 then fixed50, each MULT30 VM_RUN900 VM_CHUNKS20.

- 2026-10-04T00:17:20.039147+09:00 Prelaunch attempt rejected occupied module (no measurement started); prior OLTP interruption temporarily left mount busy. Confirmed no remaining workload processes or mount users; normal guarded umount and rmmod completed. Retrying same preregistered mixF37 output since no raw run directory was created.

### mix-20260911 mixF fixed37 — started 2026-10-04T00:17:20+09:00

- Phase A fio test4 fixed payload (1769472000000/884736000000/294912000000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixF fixed37`; evidence `result/mix-20260911/mixF-fixed37/`.

- Finished 2026-10-04T10:18:48+09:00; mixF fixed37 exit=0; evidence `/home/oy/iCAT/result/mixF-fixed37-tenhour-20261004/mixF-fixed37-rep1-x30`; cleanup attempted.
- total host_bytes=12105020948480 host_pages=2955327380 gc_pages=4391789899 WAF=2.486059
- phaseA(test4) host_pages=720019796 gc_pages=710159004 WAF=1.986305
- phaseB(varmail) host_pages=2235307584 gc_pages=3681630895 WAF=2.647035
- ycsb-load 
- ycsb-run 

- FINISHED {"run_id": "mixF-fixed37-tenhour-20261004", "exit_code": 0, "sample_rows": 1203, "started_at": "2026-10-04T00:17:20.112863+09:00", "finished_at": "2026-10-04T10:18:48.932042+09:00", "raw_path": "/home/oy/iCAT/result/mixF-fixed37-tenhour-20261004/mixF-fixed37-rep1-x30", "measurement": "manual continuous FIO-Fast MULT30 -> Varmail18000", "hostname": "oy-B550M-DS3H", "machine_id": "f4f3e77cb5bf4a08ab288227cf288de0", "source_commit": "4557a68510759320b79d083977959ffe16d6a5d8", "module_sha256": "7045a5b2c4d2ae437f43275c6dc93bf882916efb1af708312664194ac7cba1f0", "waf": 2.4860586778714175, "host_bytes": 12105020948480, "host_pages": 2955327380, "gc_pages": 4391789899, "phases": [{"slot": "A", "actual_seconds": 18000.0, "profile": "mix-test4.fio", "requested_write_bytes": 2949120000000, "duration_note": "fixed I/O amount at rate caps; actual duration may exceed five hours"}, {"slot": "B", "actual_seconds": 18005.0, "profile": "varmail.f"}], "actual_measured_seconds": 36005.0, "issues": [], "status": "validated_saved_evidence"}
