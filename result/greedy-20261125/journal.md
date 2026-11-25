
### greedy-20261125 mixFYF greedy-online rep1 — started 2026-11-26T00:50:53+09:00
- FIO-Fast 120s -> YCSB-A (load 250000 records + run, 120s total) -> FIO-Fast 120s; Table-3 prep; seeds hot/warm/cold=20260911/20261011/20261111; icat_seed=2026111401; module `/home/oy/iCAT/buildoutput/nvmev-greedy-online.ko`; evidence `/home/oy/iCAT/result/greedy-20261125/raw/mixFYF-greedy-online-rep1-smoke120`.

- Finished 2026-11-26T00:58:30+09:00; mixFYF greedy-online exit=0; evidence `/home/oy/iCAT/result/greedy-20261125/raw/mixFYF-greedy-online-rep1-smoke120`; cleanup attempted.
- total host_bytes=43015475200 host_pages=10501825 gc_pages=12326227 WAF=2.173722
- phaseA(test4) host_pages=4805258 gc_pages=4226796 WAF=1.879619
- phaseB(sqlite-a) host_pages=891823 gc_pages=427577 WAF=1.479442
- phaseC(test4) host_pages=4804744 gc_pages=7671854 WAF=2.596725
- phaseB-load host_pages=452310 gc_pages=302244 WAF=1.668223
- phaseB-run host_pages=439513 gc_pages=125333 WAF=1.285163
- ycsb-load [OVERALL], Throughput(ops/sec), 31989.76327575176
- ycsb-run [OVERALL], Throughput(ops/sec), 60110.60935994003
