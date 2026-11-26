
### arm47-20261127 mixFYF arm47 rep1 — started 2026-11-27T00:42:16+09:00
- FIO-Fast 120s -> YCSB-A (load 250000 records + run, 120s total) -> FIO-Fast 120s; Table-3 prep; seeds hot/warm/cold=20260911/20261011/20261111; icat_seed=2026111401; module `/home/oy/iCAT/buildoutput/nvmev-arm47.ko`; evidence `/home/oy/iCAT/result/arm47-20261127/raw/mixFYF-arm47-rep1-smoke120`.

- Finished 2026-11-27T00:49:49+09:00; mixFYF arm47 exit=0; evidence `/home/oy/iCAT/result/arm47-20261127/raw/mixFYF-arm47-rep1-smoke120`; cleanup attempted.
- total host_bytes=42957082624 host_pages=10487569 gc_pages=9215636 WAF=1.878720
- phaseA(test4) host_pages=4800133 gc_pages=4021970 WAF=1.837887
- phaseB(sqlite-a) host_pages=887303 gc_pages=180930 WAF=1.203910
- phaseC(test4) host_pages=4800133 gc_pages=5012736 WAF=2.044291
- phaseB-load host_pages=452310 gc_pages=101468 WAF=1.224333
- phaseB-run host_pages=434993 gc_pages=79462 WAF=1.182674
- ycsb-load [OVERALL], Throughput(ops/sec), 31438.631790744468
- ycsb-run [OVERALL], Throughput(ops/sec), 56367.99949996428
