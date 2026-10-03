
### mixO-fixed37-chunked-20261003 preregistration
Command: env MULT=20 VM_RUN=900 VM_CHUNKS=20 bash script/mix-20260911.sh mixO fixed37 1
Expected 10h plus preparation/process overhead. Only virtual nvme1n1, global lock; previous failed37 preserved, blocked50/v4 remain stopped. OLTP restart preserves reuse filesets, module and measurement counters; no resets between chunks. 30s samples. Validate exit0, twenty OLTP IO Summary durations900, Varmail18000, preparation fio error0/requested bytes, zero-start/stop counters and blockstat assertion. Environment/module/source metadata adjacent; module build provenance unchanged from earlier current-kernel build, exact upstream build equivalence unconfirmed. Publish complete/failed evidence to icat-2.

### mix-20260911 mixO fixed37 — started 2026-10-03T10:50:22+09:00

- Phase A fio test4 fixed payload (1179648000000/589824000000/196608000000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-fixed37.ko`.
- Command: `bash script/mix-20260911.sh mixO fixed37`; evidence `result/mix-20260911/mixO-fixed37/`.

- Finished 2026-10-03T20:53:28+09:00; mixO fixed37 exit=0; evidence `/home/oy/iCAT/result/mixO-fixed37-chunked-20261003/mixO-fixed37-rep1-x20`; cleanup attempted.
- total host_bytes=14139532218368 host_pages=3452034233 gc_pages=3871572173 WAF=2.121534
- phaseA(oltp) host_pages=711532447 gc_pages=209752950 WAF=1.294790
- phaseB(varmail) host_pages=2740501786 gc_pages=3661819223 WAF=2.336186
- ycsb-load 
- ycsb-run 

- FINISHED {"run_id": "mixO-fixed37-chunked-20261003", "exit_code": 0, "sample_rows": 1205, "started_at": "2026-10-03T10:50:22.061206+09:00", "finished_at": "2026-10-03T20:53:30.299087+09:00", "raw_path": "/home/oy/iCAT/result/mixO-fixed37-chunked-20261003/mixO-fixed37-rep1-x20", "measurement": "manual continuous OLTP900x20 -> Varmail18000", "hostname": "oy-B550M-DS3H", "machine_id": "f4f3e77cb5bf4a08ab288227cf288de0", "source_commit": "35c23ee13f97cdda2ee9cd6b73783fb5266bcdf4", "module_sha256": "7045a5b2c4d2ae437f43275c6dc93bf882916efb1af708312664194ac7cba1f0", "issues": ["all chunk runtimes"], "status": "failed_or_incomplete_preserved"}
