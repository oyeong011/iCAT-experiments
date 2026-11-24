
### revD-20261124 mixFYF revD-v4 rep1 — started 2026-11-24T16:02:25+09:00
- FIO-Fast 120s -> YCSB-A (load 250000 records + run, 120s total) -> FIO-Fast 120s; Table-3 prep; seeds hot/warm/cold=20260911/20261011/20261111; icat_seed=2026111401; module `/home/oy/iCAT/buildoutput/nvmev-revD-v4.ko`; evidence `/home/oy/iCAT/result/revD-20261124/raw/mixFYF-revD-v4-rep1-smoke120`.

- Finished 2026-11-24T16:09:58+09:00; mixFYF revD-v4 exit=0; evidence `/home/oy/iCAT/result/revD-20261124/raw/mixFYF-revD-v4-rep1-smoke120`; cleanup attempted.
- total host_bytes=42924101632 host_pages=10479517 gc_pages=13195645 WAF=2.259184
- phaseA(test4) host_pages=4800133 gc_pages=4498260 WAF=1.937112
- phaseB(sqlite-a) host_pages=879251 gc_pages=455001 WAF=1.517487
- phaseC(test4) host_pages=4800133 gc_pages=8242384 WAF=2.717116
- phaseB-load host_pages=452310 gc_pages=326070 WAF=1.720899
- phaseB-run host_pages=426941 gc_pages=128931 WAF=1.301988
- ycsb-load [OVERALL], Throughput(ops/sec), 29066.387629345423
- ycsb-run [OVERALL], Throughput(ops/sec), 45260.81874499861
