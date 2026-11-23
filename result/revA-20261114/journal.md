
### revA-20261114 mixFYF revA-random rep1 — started 2026-11-14T20:21:47+09:00
- FIO-Fast 120s -> YCSB-A (load 600000 records + run, 120s total) -> FIO-Fast 120s; Table-3 prep; seeds hot/warm/cold=20260911/20261011/20261111; icat_seed=2026111401; module `/home/oy/iCAT/buildoutput/nvmev-revA-random.ko`; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-random-rep1-smoke120`.

- Finished 2026-11-14T20:27:12+09:00; mixFYF revA-random exit=3; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-random-rep1-smoke120`; cleanup attempted.

### revA-20261114 mixFYF revA-random rep2 — started 2026-11-14T20:28:11+09:00
- FIO-Fast 120s -> YCSB-A (load 250000 records + run, 120s total) -> FIO-Fast 120s; Table-3 prep; seeds hot/warm/cold=20260912/20261012/20261112; icat_seed=2026111402; module `/home/oy/iCAT/buildoutput/nvmev-revA-random.ko`; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-random-rep2-smoke120`.

- Finished 2026-11-14T20:35:37+09:00; mixFYF revA-random exit=0; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-random-rep2-smoke120`; cleanup attempted.
- total host_bytes=42990092288 host_pages=10495628 gc_pages=12283106 WAF=2.170307
- phaseA(test4) host_pages=4800133 gc_pages=4877349 WAF=2.016086
- phaseB(sqlite-a) host_pages=895362 gc_pages=444161 WAF=1.496069
- phaseC(test4) host_pages=4800133 gc_pages=6961596 WAF=2.450292
- phaseB-load host_pages=452310 gc_pages=300732 WAF=1.664880
- phaseB-run host_pages=443052 gc_pages=143429 WAF=1.323729
- ycsb-load [OVERALL], Throughput(ops/sec), 34279.446044151926
- ycsb-run [OVERALL], Throughput(ops/sec), 75487.58324570628

### revA-20261114 mixFYF arm47 rep1 — started 2026-11-14T20:36:09+09:00
- FIO-Fast 1800s -> YCSB-A (load 250000 records + run, 1800s total) -> FIO-Fast 1800s; Table-3 prep; seeds hot/warm/cold=20260911/20261011/20261111; icat_seed=2026111401; module `/home/oy/iCAT/buildoutput/nvmev-arm47.ko`; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-arm47-rep1`.

- Finished 2026-11-14T22:07:35+09:00; mixFYF arm47 exit=0; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-arm47-rep1`; cleanup attempted.
- total host_bytes=613766361088 host_pages=149845303 gc_pages=147950440 WAF=1.987355
- phaseA(test4) host_pages=72001978 gc_pages=55759231 WAF=1.774412
- phaseB(sqlite-a) host_pages=5841347 gc_pages=155208 WAF=1.026571
- phaseC(test4) host_pages=72001978 gc_pages=92036001 WAF=2.278243
- phaseB-load host_pages=452310 gc_pages=74838 WAF=1.165457
- phaseB-run host_pages=5389037 gc_pages=80370 WAF=1.014914
- ycsb-load [OVERALL], Throughput(ops/sec), 30226.091161890945
- ycsb-run [OVERALL], Throughput(ops/sec), 82053.69282181795

### revA-20261114 mixFYF revA-v4 rep1 — started 2026-11-14T22:07:35+09:00
- FIO-Fast 1800s -> YCSB-A (load 250000 records + run, 1800s total) -> FIO-Fast 1800s; Table-3 prep; seeds hot/warm/cold=20260911/20261011/20261111; icat_seed=2026111401; module `/home/oy/iCAT/buildoutput/nvmev-revA-v4.ko`; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-v4-rep1`.

- Finished 2026-11-14T23:39:02+09:00; mixFYF revA-v4 exit=0; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-v4-rep1`; cleanup attempted.
- total host_bytes=613450784768 host_pages=149768258 gc_pages=168146988 WAF=2.122714
- phaseA(test4) host_pages=72002143 gc_pages=64822042 WAF=1.900279
- phaseB(sqlite-a) host_pages=5764137 gc_pages=306205 WAF=1.053122
- phaseC(test4) host_pages=72001978 gc_pages=103018741 WAF=2.430777
- phaseB-load host_pages=452310 gc_pages=185839 WAF=1.410866
- phaseB-run host_pages=5311827 gc_pages=120366 WAF=1.022660
- ycsb-load [OVERALL], Throughput(ops/sec), 35166.69011112674
- ycsb-run [OVERALL], Throughput(ops/sec), 83339.4219181245

### revA-20261114 mixFYF revA-v1 rep1 — started 2026-11-14T23:39:02+09:00
- FIO-Fast 1800s -> YCSB-A (load 250000 records + run, 1800s total) -> FIO-Fast 1800s; Table-3 prep; seeds hot/warm/cold=20260911/20261011/20261111; icat_seed=2026111401; module `/home/oy/iCAT/buildoutput/nvmev-revA-v1.ko`; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-v1-rep1`.

- Finished 2026-11-15T01:10:28+09:00; mixFYF revA-v1 exit=0; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-v1-rep1`; cleanup attempted.
- total host_bytes=613372649472 host_pages=149749182 gc_pages=174353340 WAF=2.164302
- phaseA(test4) host_pages=72002119 gc_pages=65037850 WAF=1.903277
- phaseB(sqlite-a) host_pages=5745085 gc_pages=239875 WAF=1.041753
- phaseC(test4) host_pages=72001978 gc_pages=109075615 WAF=2.514897
- phaseB-load host_pages=452312 gc_pages=131597 WAF=1.290943
- phaseB-run host_pages=5292773 gc_pages=108278 WAF=1.020458
- ycsb-load [OVERALL], Throughput(ops/sec), 35161.74402250352
- ycsb-run [OVERALL], Throughput(ops/sec), 83021.12103436852

### revA-20261114 mixFYF revA-random rep1 — started 2026-11-15T01:10:28+09:00
- FIO-Fast 1800s -> YCSB-A (load 250000 records + run, 1800s total) -> FIO-Fast 1800s; Table-3 prep; seeds hot/warm/cold=20260911/20261011/20261111; icat_seed=2026111401; module `/home/oy/iCAT/buildoutput/nvmev-revA-random.ko`; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-random-rep1`.

- Finished 2026-11-15T02:41:55+09:00; mixFYF revA-random exit=0; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-random-rep1`; cleanup attempted.
- total host_bytes=613360685056 host_pages=149746261 gc_pages=198632831 WAF=2.326463
- phaseA(test4) host_pages=72002005 gc_pages=67452423 WAF=1.936813
- phaseB(sqlite-a) host_pages=5742278 gc_pages=433840 WAF=1.075552
- phaseC(test4) host_pages=72001978 gc_pages=130746568 WAF=2.815875
- phaseB-load host_pages=452310 gc_pages=277634 WAF=1.613814
- phaseB-run host_pages=5289968 gc_pages=156206 WAF=1.029529
- ycsb-load [OVERALL], Throughput(ops/sec), 35546.70837480449
- ycsb-run [OVERALL], Throughput(ops/sec), 82374.24286086141

### revA-20261114 mixFYF revA-v2 rep1 — started 2026-11-15T02:41:55+09:00
- FIO-Fast 1800s -> YCSB-A (load 250000 records + run, 1800s total) -> FIO-Fast 1800s; Table-3 prep; seeds hot/warm/cold=20260911/20261011/20261111; icat_seed=2026111401; module `/home/oy/iCAT/buildoutput/nvmev-revA-v2.ko`; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-v2-rep1`.

- Finished 2026-11-15T04:13:21+09:00; mixFYF revA-v2 exit=0; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-v2-rep1`; cleanup attempted.
- total host_bytes=613494001664 host_pages=149778809 gc_pages=187847174 WAF=2.254164
- phaseA(test4) host_pages=72030832 gc_pages=66153578 WAF=1.918406
- phaseB(sqlite-a) host_pages=5745999 gc_pages=312484 WAF=1.054383
- phaseC(test4) host_pages=72001978 gc_pages=121381112 WAF=2.685802
- phaseB-load host_pages=452310 gc_pages=198570 WAF=1.439013
- phaseB-run host_pages=5293689 gc_pages=113914 WAF=1.021519
- ycsb-load [OVERALL], Throughput(ops/sec), 35350.67873303167
- ycsb-run [OVERALL], Throughput(ops/sec), 82752.23552139486

### revA-20261114 mixFYF revA-v2 rep2 — started 2026-11-15T04:13:21+09:00
- FIO-Fast 1800s -> YCSB-A (load 250000 records + run, 1800s total) -> FIO-Fast 1800s; Table-3 prep; seeds hot/warm/cold=20260912/20261012/20261112; icat_seed=2026111402; module `/home/oy/iCAT/buildoutput/nvmev-revA-v2.ko`; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-v2-rep2`.

- Finished 2026-11-15T05:44:48+09:00; mixFYF revA-v2 exit=0; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-v2-rep2`; cleanup attempted.
- total host_bytes=613800566784 host_pages=149853654 gc_pages=189606101 WAF=2.265275
- phaseA(test4) host_pages=72024513 gc_pages=67219093 WAF=1.933281
- phaseB(sqlite-a) host_pages=5827163 gc_pages=452711 WAF=1.077690
- phaseC(test4) host_pages=72001978 gc_pages=121934297 WAF=2.693485
- phaseB-load host_pages=452310 gc_pages=309192 WAF=1.683584
- phaseB-run host_pages=5374853 gc_pages=143519 WAF=1.026702
- ycsb-load [OVERALL], Throughput(ops/sec), 32249.742002063984
- ycsb-run [OVERALL], Throughput(ops/sec), 81802.62252367711

### revA-20261114 mixFYF revA-v4 rep2 — started 2026-11-15T05:44:48+09:00
- FIO-Fast 1800s -> YCSB-A (load 250000 records + run, 1800s total) -> FIO-Fast 1800s; Table-3 prep; seeds hot/warm/cold=20260912/20261012/20261112; icat_seed=2026111402; module `/home/oy/iCAT/buildoutput/nvmev-revA-v4.ko`; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-v4-rep2`.

- Finished 2026-11-15T07:16:14+09:00; mixFYF revA-v4 exit=0; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-v4-rep2`; cleanup attempted.
- total host_bytes=613446942720 host_pages=149767320 gc_pages=169384505 WAF=2.130984
- phaseA(test4) host_pages=72001978 gc_pages=65139001 WAF=1.904683
- phaseB(sqlite-a) host_pages=5763364 gc_pages=319137 WAF=1.055373
- phaseC(test4) host_pages=72001978 gc_pages=103926367 WAF=2.443382
- phaseB-load host_pages=452310 gc_pages=200734 WAF=1.443797
- phaseB-run host_pages=5311054 gc_pages=118403 WAF=1.022294
- ycsb-load [OVERALL], Throughput(ops/sec), 35004.200504060485
- ycsb-run [OVERALL], Throughput(ops/sec), 83531.50235212807

### revA-20261114 mixFYF revA-random rep2 — started 2026-11-15T07:16:14+09:00
- FIO-Fast 1800s -> YCSB-A (load 250000 records + run, 1800s total) -> FIO-Fast 1800s; Table-3 prep; seeds hot/warm/cold=20260912/20261012/20261112; icat_seed=2026111402; module `/home/oy/iCAT/buildoutput/nvmev-revA-random.ko`; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-random-rep2`.

- Finished 2026-11-15T08:47:41+09:00; mixFYF revA-random exit=0; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-random-rep2`; cleanup attempted.
- total host_bytes=613614551040 host_pages=149808240 gc_pages=199012798 WAF=2.328450
- phaseA(test4) host_pages=72001978 gc_pages=68410071 WAF=1.950114
- phaseB(sqlite-a) host_pages=5804284 gc_pages=402106 WAF=1.069277
- phaseC(test4) host_pages=72001978 gc_pages=130200621 WAF=2.808292
- phaseB-load host_pages=452312 gc_pages=264861 WAF=1.585571
- phaseB-run host_pages=5351972 gc_pages=137245 WAF=1.025644
- ycsb-load [OVERALL], Throughput(ops/sec), 35400.73633531578
- ycsb-run [OVERALL], Throughput(ops/sec), 82693.74840358311

### revA-20261114 mixFYF revA-v1 rep2 — started 2026-11-15T08:47:41+09:00
- FIO-Fast 1800s -> YCSB-A (load 250000 records + run, 1800s total) -> FIO-Fast 1800s; Table-3 prep; seeds hot/warm/cold=20260912/20261012/20261112; icat_seed=2026111402; module `/home/oy/iCAT/buildoutput/nvmev-revA-v1.ko`; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-v1-rep2`.

- Finished 2026-11-15T10:19:08+09:00; mixFYF revA-v1 exit=0; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-v1-rep2`; cleanup attempted.
- total host_bytes=613973516288 host_pages=149895878 gc_pages=189711944 WAF=2.265625
- phaseA(test4) host_pages=72022449 gc_pages=65227069 WAF=1.905649
- phaseB(sqlite-a) host_pages=5871451 gc_pages=288767 WAF=1.049182
- phaseC(test4) host_pages=72001978 gc_pages=124196108 WAF=2.724899
- phaseB-load host_pages=452312 gc_pages=186759 WAF=1.412899
- phaseB-run host_pages=5419139 gc_pages=102008 WAF=1.018824
- ycsb-load [OVERALL], Throughput(ops/sec), 35521.45495879511
- ycsb-run [OVERALL], Throughput(ops/sec), 83146.94674262514

### revA-20261114 mixFYF revA-v4 rep3 — started 2026-11-15T10:19:08+09:00
- FIO-Fast 1800s -> YCSB-A (load 250000 records + run, 1800s total) -> FIO-Fast 1800s; Table-3 prep; seeds hot/warm/cold=20260913/20261013/20261113; icat_seed=2026111403; module `/home/oy/iCAT/buildoutput/nvmev-revA-v4.ko`; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-v4-rep3`.

- Finished 2026-11-15T11:50:35+09:00; mixFYF revA-v4 exit=0; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-v4-rep3`; cleanup attempted.
- total host_bytes=613553508352 host_pages=149793337 gc_pages=169495025 WAF=2.131526
- phaseA(test4) host_pages=72029294 gc_pages=64431036 WAF=1.894512
- phaseB(sqlite-a) host_pages=5762047 gc_pages=256574 WAF=1.044528
- phaseC(test4) host_pages=72001996 gc_pages=104807415 WAF=2.455618
- phaseB-load host_pages=452310 gc_pages=157964 WAF=1.349238
- phaseB-run host_pages=5309737 gc_pages=98610 WAF=1.018572
- ycsb-load [OVERALL], Throughput(ops/sec), 34999.30001399972
- ycsb-run [OVERALL], Throughput(ops/sec), 83105.82796524814

### revA-20261114 mixFYF revA-v2 rep3 — started 2026-11-15T11:50:35+09:00
- FIO-Fast 1800s -> YCSB-A (load 250000 records + run, 1800s total) -> FIO-Fast 1800s; Table-3 prep; seeds hot/warm/cold=20260913/20261013/20261113; icat_seed=2026111403; module `/home/oy/iCAT/buildoutput/nvmev-revA-v2.ko`; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-v2-rep3`.

- Finished 2026-11-15T13:22:02+09:00; mixFYF revA-v2 exit=0; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-v2-rep3`; cleanup attempted.
- total host_bytes=613643489280 host_pages=149815305 gc_pages=190600838 WAF=2.272239
- phaseA(test4) host_pages=72001978 gc_pages=67948728 WAF=1.943706
- phaseB(sqlite-a) host_pages=5811349 gc_pages=396285 WAF=1.068192
- phaseC(test4) host_pages=72001978 gc_pages=122255825 WAF=2.697951
- phaseB-load host_pages=452310 gc_pages=239689 WAF=1.529922
- phaseB-run host_pages=5359039 gc_pages=156596 WAF=1.029221
- ycsb-load [OVERALL], Throughput(ops/sec), 35335.68904593639
- ycsb-run [OVERALL], Throughput(ops/sec), 82464.69519366365

### revA-20261114 mixFYF revA-random rep3 — started 2026-11-15T13:22:02+09:00
- FIO-Fast 1800s -> YCSB-A (load 250000 records + run, 1800s total) -> FIO-Fast 1800s; Table-3 prep; seeds hot/warm/cold=20260913/20261013/20261113; icat_seed=2026111403; module `/home/oy/iCAT/buildoutput/nvmev-revA-random.ko`; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-random-rep3`.

- Finished 2026-11-15T14:53:29+09:00; mixFYF revA-random exit=0; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-random-rep3`; cleanup attempted.
- total host_bytes=613923180544 host_pages=149883589 gc_pages=197551077 WAF=2.318030
- phaseA(test4) host_pages=72029135 gc_pages=67224583 WAF=1.933297
- phaseB(sqlite-a) host_pages=5852476 gc_pages=440992 WAF=1.075351
- phaseC(test4) host_pages=72001978 gc_pages=129885502 WAF=2.803916
- phaseB-load host_pages=452310 gc_pages=287188 WAF=1.634936
- phaseB-run host_pages=5400166 gc_pages=153804 WAF=1.028481
- ycsb-load [OVERALL], Throughput(ops/sec), 35004.200504060485
- ycsb-run [OVERALL], Throughput(ops/sec), 82314.89035097498

### revA-20261114 mixFYF revA-v1 rep3 — started 2026-11-15T14:53:29+09:00
- FIO-Fast 1800s -> YCSB-A (load 250000 records + run, 1800s total) -> FIO-Fast 1800s; Table-3 prep; seeds hot/warm/cold=20260913/20261013/20261113; icat_seed=2026111403; module `/home/oy/iCAT/buildoutput/nvmev-revA-v1.ko`; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-v1-rep3`.

- Finished 2026-11-15T16:24:57+09:00; mixFYF revA-v1 exit=0; evidence `/home/oy/iCAT/result/revA-20261114/raw/mixFYF-revA-v1-rep3`; cleanup attempted.
- total host_bytes=613814779904 host_pages=149857124 gc_pages=178521883 WAF=2.191281
- phaseA(test4) host_pages=72028630 gc_pages=64630108 WAF=1.897284
- phaseB(sqlite-a) host_pages=5826516 gc_pages=293482 WAF=1.050370
- phaseC(test4) host_pages=72001978 gc_pages=113598293 WAF=2.577711
- phaseB-load host_pages=452310 gc_pages=185170 WAF=1.409387
- phaseB-run host_pages=5374206 gc_pages=108312 WAF=1.020154
- ycsb-load [OVERALL], Throughput(ops/sec), 34364.26116838488
- ycsb-run [OVERALL], Throughput(ops/sec), 83229.21418620707
