
### revF-20261127 mixFYF revF-g90 rep1 — started 2026-11-27T16:11:37+09:00
- FIO-Fast 120s -> YCSB-A (load 250000 records + run, 120s total) -> FIO-Fast 120s; Table-3 prep; seeds hot/warm/cold=20260911/20261011/20261111; icat_seed=2026111401; module `/home/oy/iCAT/buildoutput/nvmev-revF-g90.ko`; evidence `/home/oy/iCAT/result/revF-20261127/raw/mixFYF-revF-g90-rep1-smoke120`.

- Finished 2026-11-27T16:19:02+09:00; mixFYF revF-g90 exit=0; evidence `/home/oy/iCAT/result/revF-20261127/raw/mixFYF-revF-g90-rep1-smoke120`; cleanup attempted.
- total host_bytes=42967109632 host_pages=10490017 gc_pages=13184816 WAF=2.256892
- phaseA(test4) host_pages=4800133 gc_pages=4495260 WAF=1.936487
- phaseB(sqlite-a) host_pages=889751 gc_pages=452965 WAF=1.509092
- phaseC(test4) host_pages=4800133 gc_pages=8236591 WAF=2.715909
- phaseB-load host_pages=452312 gc_pages=317579 WAF=1.702124
- phaseB-run host_pages=437439 gc_pages=135386 WAF=1.309497
- ycsb-load [OVERALL], Throughput(ops/sec), 34345.37711224069
- ycsb-run [OVERALL], Throughput(ops/sec), 77111.38419103021

### revF-20261127 mixFYF revF-c075 rep1 — started 2026-11-27T16:19:02+09:00
- FIO-Fast 120s -> YCSB-A (load 250000 records + run, 120s total) -> FIO-Fast 120s; Table-3 prep; seeds hot/warm/cold=20260911/20261011/20261111; icat_seed=2026111401; module `/home/oy/iCAT/buildoutput/nvmev-revF-c075.ko`; evidence `/home/oy/iCAT/result/revF-20261127/raw/mixFYF-revF-c075-rep1-smoke120`.

- Finished 2026-11-27T16:26:28+09:00; mixFYF revF-c075 exit=0; evidence `/home/oy/iCAT/result/revF-20261127/raw/mixFYF-revF-c075-rep1-smoke120`; cleanup attempted.
- total host_bytes=43047067648 host_pages=10509538 gc_pages=12524408 WAF=2.191718
- phaseA(test4) host_pages=4806792 gc_pages=4251182 WAF=1.884411
- phaseB(sqlite-a) host_pages=895954 gc_pages=435763 WAF=1.486368
- phaseC(test4) host_pages=4806792 gc_pages=7837463 WAF=2.630498
- phaseB-load host_pages=452822 gc_pages=304696 WAF=1.672883
- phaseB-run host_pages=443132 gc_pages=131067 WAF=1.295774
- ycsb-load [OVERALL], Throughput(ops/sec), 34640.43231259526
- ycsb-run [OVERALL], Throughput(ops/sec), 75739.65020248643
