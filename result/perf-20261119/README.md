# perf cross-check (2026-11-19)
- Run: uninstrumented iCAT v4 (`nvmev-online-v4.ko`), mixY FIO-Fast, `mixY-onlinev4-rep1/`, commit 3279500fb.
- `sudo perf record -a -g -- sleep 60`, started 120 s into the measurement window (10:44:21). 1,373,524 samples, all CPUs.
- `perf-v4.data` (200 MB) is not committed; text reports are `perf-v4-comm.txt`, `perf-v4-dispatcher-sym*.txt`.

| | share of all samples | share of nvmev_dispatcher |
|---|---|---|
| nvmev_dispatcher thread | 21.79 % | 100 % |
| busy-poll loop (`nvmev_dispatcher`) | 15.92 % | 73.1 % |
| `do_gc` (learner inlined into it) | 2.29 % | 10.5 % |
| learner symbols (`watgc_v2_set_arm`, `watgc_v2_waf_q16`, `watgc_v2_neighbour`) | 0 samples | 0 % |

- Cross-check: instrumented v4 GC time was 206.8 s / 1,800 s = 11.5 % of the window; perf gives 10.5 % → consistent.
- Learner: instrumented net cost ≈ 20 ms / 30 min ≈ 0.7 ms per minute ≈ 3 samples at ~4 kHz; observed 0 in the out-of-line learner functions. The rest of the learner is inlined into `do_gc` and cannot be separated by perf.
