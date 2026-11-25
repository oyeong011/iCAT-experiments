
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
