
### mixO-fixed50-chunked-20261003 preregistration 2026-10-03T22:29:20.263986+09:00

Purpose: same-host mixO comparison with completed CAT37. Command: `env MULT=20 VM_RUN=900 VM_CHUNKS=20 bash script/mix-20260911.sh mixO fixed50 1`. Expected duration 10h plus setup/process overhead per policy; fixed50 starts now, onlinev4 waits for fixed50 validation and lock. Only policy/module changes from completed chunked CAT37; identical preparation, workload profiles, manual measurement, 30s samples. Global and per-campaign locks, device model/serial/PCI guards retained. All raw outputs separate, no overwrites. Validate fio requested bytes/errors, 20 OLTP900s processes, one Varmail18000s process, zero/start/stop counters, block-stat equality in runner, partition totals and policy evidence. v4 includes learning cost. metadata.json and module-info.txt identify exact source/module/kernel/host; historical build-option equivalence not newly established. Completion validates and publishes this campaign to icat-2; failures retained and prevent following experiment.

### mix-20260911 mixO fixed50 — started 2026-10-03T22:29:20+09:00

- Phase A fio test4 fixed payload (1179648000000/589824000000/196608000000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed50.ko`.
- Command: `bash script/mix-20260911.sh mixO fixed50`; evidence `result/mix-20260911/mixO-fixed50/`.

- 2026-10-04T00:15:30.481498+09:00 USER PRIORITY CHANGE: cancel old mixO queue; stop active mixO fixed50 preserving incomplete evidence; run mixF fixed37 then fixed50, each MULT30 VM_RUN900 VM_CHUNKS20.

- Finished 2026-10-04T00:16:21+09:00; mixO fixed50 exit=1; evidence `/home/oy/iCAT/result/mixO-fixed50-chunked-20261003/mixO-fixed50-rep1-x20`; cleanup attempted.

- FINISHED {"run_id": "mixO-fixed50-chunked-20261003", "exit_code": 1, "sample_rows": 214, "started_at": "2026-10-03T22:29:20.559224+09:00", "finished_at": "2026-10-04T00:16:22.772929+09:00", "raw_path": "/home/oy/iCAT/result/mixO-fixed50-chunked-20261003/mixO-fixed50-rep1-x20", "measurement": "manual continuous OLTP900x20 -> Varmail18000", "hostname": "oy-B550M-DS3H", "machine_id": "f4f3e77cb5bf4a08ab288227cf288de0", "source_commit": "35c23ee13f97cdda2ee9cd6b73783fb5266bcdf4", "module_sha256": "f476acff890da8e28ce745ec3f2cf2b0eced8cb33752d99b40a093178511b5b6", "issues": ["runner_exit_nonzero", "[Errno 2] No such file or directory: '/home/oy/iCAT/result/mixO-fixed50-chunked-20261003/mixO-fixed50-rep1-x20/stopped.txt'"], "status": "failed_or_incomplete_preserved"}
