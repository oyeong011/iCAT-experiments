
### batchG-20261126 mixFYF bg-v4 rep1 — started 2026-11-26T10:32:12+09:00
- FIO-Fast 120s -> YCSB-A (load 250000 records + run, 120s total) -> FIO-Fast 120s; Table-3 prep; seeds hot/warm/cold=20260911/20261011/20261111; icat_seed=2026111401; module `/home/oy/iCAT/buildoutput/nvmev-abl-v4.ko`; evidence `/home/oy/iCAT/result/batchG-20261126/raw/mixFYF-bg-v4-rep1-smoke120`.

- Finished 2026-11-26T10:39:46+09:00; mixFYF bg-v4 exit=0; evidence `/home/oy/iCAT/result/batchG-20261126/raw/mixFYF-bg-v4-rep1-smoke120`; cleanup attempted.
- total host_bytes=42922983424 host_pages=10479244 gc_pages=13218768 WAF=2.261424
- phaseA(test4) host_pages=4800133 gc_pages=4495529 WAF=1.936543
- phaseB(sqlite-a) host_pages=878978 gc_pages=455161 WAF=1.517830
- phaseC(test4) host_pages=4800133 gc_pages=8268078 WAF=2.722469
- phaseB-load host_pages=452312 gc_pages=324274 WAF=1.716925
- phaseB-run host_pages=426666 gc_pages=130887 WAF=1.306767
- ycsb-load [OVERALL], Throughput(ops/sec), 31462.37100427888
- ycsb-run [OVERALL], Throughput(ops/sec), 57170.72909412332

### batchG-20261126 mixFYF drift50 rep1 — started 2026-11-26T10:39:53+09:00
- FIO-Fast 120s -> YCSB-A (load 250000 records + run, 120s total) -> FIO-Fast 120s; Table-3 prep; seeds hot/warm/cold=20260911/20261011/20261111; icat_seed=2026111401; module `/home/oy/iCAT/buildoutput/nvmev-drift50.ko`; evidence `/home/oy/iCAT/result/drift50-20261126/raw/mixFYF-drift50-rep1-smoke120`.

- Finished 2026-11-26T10:47:30+09:00; mixFYF drift50 exit=0; evidence `/home/oy/iCAT/result/drift50-20261126/raw/mixFYF-drift50-rep1-smoke120`; cleanup attempted.
- total host_bytes=42966261760 host_pages=10489810 gc_pages=13169523 WAF=2.255459
- phaseA(test4) host_pages=4800133 gc_pages=4489722 WAF=1.935333
- phaseB(sqlite-a) host_pages=889544 gc_pages=456691 WAF=1.513399
- phaseC(test4) host_pages=4800133 gc_pages=8223110 WAF=2.713100
- phaseB-load host_pages=452312 gc_pages=321819 WAF=1.711498
- phaseB-run host_pages=437232 gc_pages=134872 WAF=1.308468
- ycsb-load [OVERALL], Throughput(ops/sec), 31238.28564288392
- ycsb-run [OVERALL], Throughput(ops/sec), 63583.59945255474

### batchG-20261126 mixFYF greedygc rep1 — started 2026-11-26T10:47:36+09:00
- FIO-Fast 120s -> YCSB-A (load 250000 records + run, 120s total) -> FIO-Fast 120s; Table-3 prep; seeds hot/warm/cold=20260911/20261011/20261111; icat_seed=2026111401; module `/home/oy/iCAT/buildoutput/nvmev-greedygc.ko`; evidence `/home/oy/iCAT/result/greedygc-20261126/raw/mixFYF-greedygc-rep1-smoke120`.

- Finished 2026-11-26T10:55:09+09:00; mixFYF greedygc exit=0; evidence `/home/oy/iCAT/result/greedygc-20261126/raw/mixFYF-greedygc-rep1-smoke120`; cleanup attempted.
- total host_bytes=43062923264 host_pages=10513409 gc_pages=15119729 WAF=2.438138
- phaseA(test4) host_pages=4813445 gc_pages=5174428 WAF=2.074995
- phaseB(sqlite-a) host_pages=899831 gc_pages=605264 WAF=1.672642
- phaseC(test4) host_pages=4800133 gc_pages=9340037 WAF=2.945787
- phaseB-load host_pages=453332 gc_pages=417328 WAF=1.920579
- phaseB-run host_pages=446499 gc_pages=187936 WAF=1.420910
- ycsb-load [OVERALL], Throughput(ops/sec), 28061.51083174318
- ycsb-run [OVERALL], Throughput(ops/sec), 68727.90913052953

### batchG-20261126 mixFYF greedygc rep1 — started 2026-11-26T10:55:24+09:00
- FIO-Fast 1800s -> YCSB-A (load 250000 records + run, 1800s total) -> FIO-Fast 1800s; Table-3 prep; seeds hot/warm/cold=20260911/20261011/20261111; icat_seed=2026111401; module `/home/oy/iCAT/buildoutput/nvmev-greedygc.ko`; evidence `/home/oy/iCAT/result/greedygc-20261126/raw/mixFYF-greedygc-rep1`.

- Finished 2026-11-26T12:26:57+09:00; mixFYF greedygc exit=0; evidence `/home/oy/iCAT/result/greedygc-20261126/raw/mixFYF-greedygc-rep1`; cleanup attempted.
- total host_bytes=613480271872 host_pages=149775457 gc_pages=244687955 WAF=2.633699
- phaseA(test4) host_pages=72001981 gc_pages=91599787 WAF=2.272184
- phaseB(sqlite-a) host_pages=5771483 gc_pages=678205 WAF=1.117510
- phaseC(test4) host_pages=72001993 gc_pages=152409963 WAF=3.116746
- phaseB-load host_pages=452310 gc_pages=487562 WAF=2.077938
- phaseB-run host_pages=5319173 gc_pages=190643 WAF=1.035841
- ycsb-load [OVERALL], Throughput(ops/sec), 28509.522180408258
- ycsb-run [OVERALL], Throughput(ops/sec), 62295.44869543563
