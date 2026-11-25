
### abl-20261125 mixFYF abl-v4 rep1 — started 2026-11-25T10:40:26+09:00
- FIO-Fast 120s -> YCSB-A (load 250000 records + run, 120s total) -> FIO-Fast 120s; Table-3 prep; seeds hot/warm/cold=20260911/20261011/20261111; icat_seed=2026111401; module `/home/oy/iCAT/buildoutput/nvmev-abl-v4.ko`; evidence `/home/oy/iCAT/result/revision-additional-ablation/raw/mixFYF-abl-v4-rep1-smoke120`.

- Finished 2026-11-25T10:48:01+09:00; mixFYF abl-v4 exit=0; evidence `/home/oy/iCAT/result/revision-additional-ablation/raw/mixFYF-abl-v4-rep1-smoke120`; cleanup attempted.
- total host_bytes=42942337024 host_pages=10483969 gc_pages=13160389 WAF=2.255287
- phaseA(test4) host_pages=4800133 gc_pages=4480388 WAF=1.933388
- phaseB(sqlite-a) host_pages=883703 gc_pages=452501 WAF=1.512051
- phaseC(test4) host_pages=4800133 gc_pages=8227500 WAF=2.714015
- phaseB-load host_pages=452310 gc_pages=326481 WAF=1.721808
- phaseB-run host_pages=431393 gc_pages=126020 WAF=1.292123
- ycsb-load [OVERALL], Throughput(ops/sec), 28052.064631956913
- ycsb-run [OVERALL], Throughput(ops/sec), 57956.30781869486

### abl-20261125 mixFYF abl-nodiscount rep1 — started 2026-11-25T10:48:08+09:00
- FIO-Fast 120s -> YCSB-A (load 250000 records + run, 120s total) -> FIO-Fast 120s; Table-3 prep; seeds hot/warm/cold=20260911/20261011/20261111; icat_seed=2026111401; module `/home/oy/iCAT/buildoutput/nvmev-abl-nodiscount.ko`; evidence `/home/oy/iCAT/result/revision-additional-ablation/raw/mixFYF-abl-nodiscount-rep1-smoke120`.

- Finished 2026-11-25T10:55:46+09:00; mixFYF abl-nodiscount exit=0; evidence `/home/oy/iCAT/result/revision-additional-ablation/raw/mixFYF-abl-nodiscount-rep1-smoke120`; cleanup attempted.
- total host_bytes=43051114496 host_pages=10510526 gc_pages=12983678 WAF=2.235302
- phaseA(test4) host_pages=4812423 gc_pages=4319160 WAF=1.897502
- phaseB(sqlite-a) host_pages=897970 gc_pages=460323 WAF=1.512626
- phaseC(test4) host_pages=4800133 gc_pages=8204195 WAF=2.709160
- phaseB-load host_pages=453333 gc_pages=322741 WAF=1.711929
- phaseB-run host_pages=444637 gc_pages=137582 WAF=1.309425
- ycsb-load [OVERALL], Throughput(ops/sec), 29110.386585933862
- ycsb-run [OVERALL], Throughput(ops/sec), 63810.26773542723

### abl-20261125 mixFYF abl-off-elim-settle-drift-probe rep1 — started 2026-11-25T10:56:07+09:00
- FIO-Fast 120s -> YCSB-A (load 250000 records + run, 120s total) -> FIO-Fast 120s; Table-3 prep; seeds hot/warm/cold=20260911/20261011/20261111; icat_seed=2026111401; module `/home/oy/iCAT/buildoutput/nvmev-abl-off-elim-settle-drift-probe.ko`; evidence `/home/oy/iCAT/result/revision-additional-ablation/raw/mixFYF-abl-off-elim-settle-drift-probe-rep1-smoke120`.

- Finished 2026-11-25T11:03:49+09:00; mixFYF abl-off-elim-settle-drift-probe exit=0; evidence `/home/oy/iCAT/result/revision-additional-ablation/raw/mixFYF-abl-off-elim-settle-drift-probe-rep1-smoke120`; cleanup attempted.
- total host_bytes=42961182720 host_pages=10488570 gc_pages=13179902 WAF=2.256597
- phaseA(test4) host_pages=4800133 gc_pages=4496587 WAF=1.936763
- phaseB(sqlite-a) host_pages=888304 gc_pages=451984 WAF=1.508817
- phaseC(test4) host_pages=4800133 gc_pages=8231331 WAF=2.714813
- phaseB-load host_pages=452319 gc_pages=323203 WAF=1.714547
- phaseB-run host_pages=435985 gc_pages=128781 WAF=1.295379
- ycsb-load [OVERALL], Throughput(ops/sec), 24757.37769855417
- ycsb-run [OVERALL], Throughput(ops/sec), 60449.91514117423

### abl-20261125 mixFYF abl-v4 rep1 — started 2026-11-25T11:03:54+09:00
- FIO-Fast 1800s -> YCSB-A (load 250000 records + run, 1800s total) -> FIO-Fast 1800s; Table-3 prep; seeds hot/warm/cold=20260911/20261011/20261111; icat_seed=2026111401; module `/home/oy/iCAT/buildoutput/nvmev-abl-v4.ko`; evidence `/home/oy/iCAT/result/revision-additional-ablation/raw/mixFYF-abl-v4-rep1`.

- Finished 2026-11-25T12:35:31+09:00; mixFYF abl-v4 exit=0; evidence `/home/oy/iCAT/result/revision-additional-ablation/raw/mixFYF-abl-v4-rep1`; cleanup attempted.
- total host_bytes=613916266496 host_pages=149881901 gc_pages=174653550 WAF=2.165274
- phaseA(test4) host_pages=72019377 gc_pages=65057972 WAF=1.903340
- phaseB(sqlite-a) host_pages=5860537 gc_pages=298252 WAF=1.050892
- phaseC(test4) host_pages=72001987 gc_pages=109297326 WAF=2.517977
- phaseB-load host_pages=452310 gc_pages=169548 WAF=1.374849
- phaseB-run host_pages=5408227 gc_pages=128704 WAF=1.023798
- ycsb-load [OVERALL], Throughput(ops/sec), 27703.90070921986
- ycsb-run [OVERALL], Throughput(ops/sec), 63628.27727902095

### abl-20261125 mixFYF abl-off-elim-settle-drift-probe rep1 — started 2026-11-25T12:35:44+09:00
- FIO-Fast 1800s -> YCSB-A (load 250000 records + run, 1800s total) -> FIO-Fast 1800s; Table-3 prep; seeds hot/warm/cold=20260911/20261011/20261111; icat_seed=2026111401; module `/home/oy/iCAT/buildoutput/nvmev-abl-off-elim-settle-drift-probe.ko`; evidence `/home/oy/iCAT/result/revision-additional-ablation/raw/mixFYF-abl-off-elim-settle-drift-probe-rep1`.

- Finished 2026-11-25T14:07:21+09:00; mixFYF abl-off-elim-settle-drift-probe exit=0; evidence `/home/oy/iCAT/result/revision-additional-ablation/raw/mixFYF-abl-off-elim-settle-drift-probe-rep1`; cleanup attempted.
- total host_bytes=614255087616 host_pages=149964621 gc_pages=188685143 WAF=2.258198
- phaseA(test4) host_pages=72017337 gc_pages=67567977 WAF=1.938218
- phaseB(sqlite-a) host_pages=5945297 gc_pages=480948 WAF=1.080896
- phaseC(test4) host_pages=72001987 gc_pages=120636218 WAF=2.675457
- phaseB-load host_pages=452310 gc_pages=327347 WAF=1.723723
- phaseB-run host_pages=5492987 gc_pages=153601 WAF=1.027963
- ycsb-load [OVERALL], Throughput(ops/sec), 26106.934001670845
- ycsb-run [OVERALL], Throughput(ops/sec), 61640.02092638373

### abl-20261125 mixFYF abl-nodiscount rep1 — started 2026-11-25T14:07:34+09:00
- FIO-Fast 1800s -> YCSB-A (load 250000 records + run, 1800s total) -> FIO-Fast 1800s; Table-3 prep; seeds hot/warm/cold=20260911/20261011/20261111; icat_seed=2026111401; module `/home/oy/iCAT/buildoutput/nvmev-abl-nodiscount.ko`; evidence `/home/oy/iCAT/result/revision-additional-ablation/raw/mixFYF-abl-nodiscount-rep1`.

- Finished 2026-11-25T15:39:14+09:00; mixFYF abl-nodiscount exit=0; evidence `/home/oy/iCAT/result/revision-additional-ablation/raw/mixFYF-abl-nodiscount-rep1`; cleanup attempted.
- total host_bytes=613777137664 host_pages=149847934 gc_pages=168993038 WAF=2.127764
- phaseA(test4) host_pages=72001990 gc_pages=64991092 WAF=1.902629
- phaseB(sqlite-a) host_pages=5843957 gc_pages=302366 WAF=1.051740
- phaseC(test4) host_pages=72001987 gc_pages=103699580 WAF=2.440232
- phaseB-load host_pages=452310 gc_pages=165091 WAF=1.364995
- phaseB-run host_pages=5391647 gc_pages=137275 WAF=1.025461
- ycsb-load [OVERALL], Throughput(ops/sec), 28646.728543600322
- ycsb-run [OVERALL], Throughput(ops/sec), 59576.26532587864

### abl-20261125 mixFYF abl-off-elim-settle-drift-probe rep2 — started 2026-11-25T15:39:30+09:00
- FIO-Fast 1800s -> YCSB-A (load 250000 records + run, 1800s total) -> FIO-Fast 1800s; Table-3 prep; seeds hot/warm/cold=20260912/20261012/20261112; icat_seed=2026111402; module `/home/oy/iCAT/buildoutput/nvmev-abl-off-elim-settle-drift-probe.ko`; evidence `/home/oy/iCAT/result/revision-additional-ablation/raw/mixFYF-abl-off-elim-settle-drift-probe-rep2`.

- Finished 2026-11-25T17:11:02+09:00; mixFYF abl-off-elim-settle-drift-probe exit=0; evidence `/home/oy/iCAT/result/revision-additional-ablation/raw/mixFYF-abl-off-elim-settle-drift-probe-rep2`; cleanup attempted.
- total host_bytes=613164298240 host_pages=149698315 gc_pages=188662590 WAF=2.260285
- phaseA(test4) host_pages=72001987 gc_pages=67556811 WAF=1.938263
- phaseB(sqlite-a) host_pages=5694344 gc_pages=345070 WAF=1.060599
- phaseC(test4) host_pages=72001984 gc_pages=120760709 WAF=2.677186
- phaseB-load host_pages=452318 gc_pages=221023 WAF=1.488645
- phaseB-run host_pages=5242026 gc_pages=124047 WAF=1.023664
- ycsb-load [OVERALL], Throughput(ops/sec), 26491.46974674155
- ycsb-run [OVERALL], Throughput(ops/sec), 58410.72800059432

### abl-20261125 mixFYF abl-nodiscount rep2 — started 2026-11-25T17:11:16+09:00
- FIO-Fast 1800s -> YCSB-A (load 250000 records + run, 1800s total) -> FIO-Fast 1800s; Table-3 prep; seeds hot/warm/cold=20260912/20261012/20261112; icat_seed=2026111402; module `/home/oy/iCAT/buildoutput/nvmev-abl-nodiscount.ko`; evidence `/home/oy/iCAT/result/revision-additional-ablation/raw/mixFYF-abl-nodiscount-rep2`.

- Finished 2026-11-25T18:42:52+09:00; mixFYF abl-nodiscount exit=0; evidence `/home/oy/iCAT/result/revision-additional-ablation/raw/mixFYF-abl-nodiscount-rep2`; cleanup attempted.
- total host_bytes=613430685696 host_pages=149763351 gc_pages=166332184 WAF=2.110633
- phaseA(test4) host_pages=72001990 gc_pages=64796536 WAF=1.899927
- phaseB(sqlite-a) host_pages=5759377 gc_pages=272436 WAF=1.047303
- phaseC(test4) host_pages=72001984 gc_pages=101263212 WAF=2.406395
- phaseB-load host_pages=452310 gc_pages=137549 WAF=1.304103
- phaseB-run host_pages=5307067 gc_pages=134887 WAF=1.025416
- ycsb-load [OVERALL], Throughput(ops/sec), 23848.135075837068
- ycsb-run [OVERALL], Throughput(ops/sec), 59521.85140408036
