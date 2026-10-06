
### v6-mixT-20261005 preregistration 2026-10-05T19:49:52.611073+09:00

Requested entrypoint: bash script/icat2-v6-mixT.sh. Latest main e5f84db1c3e71f6baaed39a8b3b33b3ad46b3017 pulled into clean icat-2 worktree. Existing mixU 3-policy queue retained (optional priority question unanswered); v6 build itself waits for completion and device lock so compilation cannot disturb measured runs. Estimated start after Oct7 ~01:50 KST, smoke18min+preparation/load then nominal10h if valid.

New online-v6-src extracted exactly, source manifest records all hashes. Local kernel7.0.0-31-generic build uses NVMEVIRT_GC_POLICY=WATGC_V2 and source Kbuild; build logs, actual commands, moduleSHA, vermagic recorded after build. Failure stops without full run. Default gc policy adaptive; learner initialized once per run. Device must be unused and identified as CSL_Virt model/serial/vendor/PCI; global lock and protected sudo preserved. Never writes physical SSD.

Smoke PH_SECS120: 9 phases YA/O/V/YA/YB/F/V/YA/O; DB250000 records; OLTP4x30s32MiB;Varmail2000files120s;FIO requested19660800000 bytes for120s at40kIOPS total. Upstream SMOKE scale10 would instead shorten FIO to12s; documented smoke-only correction restores requested120s without changing long workload. First DB load and startup add overhead. Long PH_SECS4000: same9 order, DB250000 records, OLTP4x1000s32MiB,Varmail24000files4000s,FIO655360000000bytes. These DB sizes differ from earlier300k mixT CAT37/50; do not silently treat them as identical settings.

Both use6GiB preset+3GiB prepare seed20260907 outside counters; FIO seeds20260911/20261011/20261111; YCSB seed not explicitly supplied. One manual measurement epoch per run, first DB load included, every30s counters/rawkernel snapshots. Strict post-smoke validator checks all9 completed durations/order, YCSB250k load and Return=OK/no errors, FIO error0/exactbytes/runtime, Filebench all chunks/IO Summary runtime, zero start/stop/final/part counters, upstream blockstat assertions and learner samples all4 partitions. Only then full run starts. Incomplete results preserved; failure recorded and local desktop notification attempted. All evidence published to icat-2; source/local changes documented by diffs. No success implied before smoke actually executes.

- 2026-10-05T19:54:50.648288+09:00 User explicitly prioritizes v6 now. Stop current mixU v4 with TERM, preserve incomplete evidence, defer all mixU work until validated v6 completion. Interrupted v4 requires fresh run, not continuation of cumulative counters.

- 2026-10-05T19:55:13.306064+09:00 v6-mixT-20261005 START authorized v6 build -> smoke gate -> long pipeline

- 2026-10-05T19:55:15.670078+09:00 v6-mixT-20261005 BUILD complete; moduleSHA=94cb134314e56567e050c7d2a25be8fbf06a90c1ef4de822a7f237fbaeaa95ac

- 2026-10-05T19:55:15.702015+09:00 v6-mixT-20261005 START smoke PH_SECS=120; raw=/home/oy/iCAT/result/v6-mixT-20261005/mixT-onlinev6-rep1-smoke

### mix-20260911 mixT onlinev6 — started 2026-10-05T19:55:15+09:00

- mixT: 9 time-based phases of 120 s each — YCSB-A (load 20000 records) -> OLTP (32 MB x 10 files, 30 s x 4 chunks) -> Varmail -> YCSB-A -> YCSB-B -> FIO-Fast test4 (payload x 120/600) -> Varmail -> YCSB-A -> OLTP. FIO file (6 GiB) kept throughout. Module `nvmev-online-v6.ko`.
- Command: `env PH_SECS=120 bash script/mix-20260911.sh mixT onlinev6 1`; evidence `result/v6-mixT-20261005/mixT-onlinev6-rep1-smoke/`.

- Finished 2026-10-05T20:15:33+09:00; mixT onlinev6 exit=0; evidence `/home/oy/iCAT/result/v6-mixT-20261005/mixT-onlinev6-rep1-smoke`; cleanup attempted.
- total host_bytes=219564670976 host_pages=53604656 gc_pages=25916199 WAF=1.483469
- phaseA(sqlite-a) host_pages=886663 gc_pages=303822 WAF=1.342658
- phaseB(oltp) host_pages=4930186 gc_pages=964420 WAF=1.195615
- phaseC(varmail) host_pages=19584348 gc_pages=1969177 WAF=1.100549
- phaseD(sqlite-a) host_pages=436200 gc_pages=2030 WAF=1.004654
- phaseE(sqlite-b) host_pages=226534 gc_pages=4510 WAF=1.019909
- phaseF(test4) host_pages=4800133 gc_pages=11777764 WAF=3.453633
- phaseG(varmail) host_pages=17587664 gc_pages=9439492 WAF=1.536711
- phaseH(sqlite-a) host_pages=434869 gc_pages=4571 WAF=1.010511
- phaseI(oltp) host_pages=4718059 gc_pages=1450413 WAF=1.307417
- phaseA-load host_pages=452312 gc_pages=212276 WAF=1.469313
- phaseA-run host_pages=434351 gc_pages=91546 WAF=1.210765
- ycsb-load [OVERALL], Throughput(ops/sec), 27123.792991211893
- ycsb-run [OVERALL], Throughput(ops/sec), 70994.09608111902

- 2026-10-05T20:15:33.124059+09:00 v6-mixT-20261005 FINISHED smoke {"stage": "smoke", "finished_at": "2026-10-05T20:15:33.123740+09:00", "raw_path": "/home/oy/iCAT/result/v6-mixT-20261005/mixT-onlinev6-rep1-smoke", "status": "validated_saved_evidence", "validation_exit": 0, "waf": 1.483469178498226, "host_bytes": 219564670976, "host_pages": 53604656, "gc_pages": 25916199, "phases": [{"slot": "A", "workload": "YCSB-A", "actual_seconds": 133.0, "host_bytes": 3631771648, "host_pages": 886663, "gc_pages": 303822, "waf": 1.3426578079834166, "runtime_seconds": 121.088, "successful_operations": {"READ": 4335810, "UPDATE": 4338530}}, {"slot": "B", "workload": "OLTP", "actual_seconds": 133.0, "host_bytes": 20194041856, "host_pages": 4930186, "gc_pages": 964420, "waf": 1.195615337839181, "process_runtimes_seconds": [30.049999999999997, 30.059, 30.056, 30.063]}, {"slot": "C", "workload": "Varmail", "actual_seconds": 122.0, "host_bytes": 80217489408, "host_pages": 19584348, "gc_pages": 1969177, "waf": 1.1005485094525485, "process_runtimes_seconds": [120.009]}, {"slot": "D", "workload": "YCSB-A", "actual_seconds": 123.0, "host_bytes": 1786675200, "host_pages": 436200, "gc_pages": 2030, "waf": 1.004653828519028, "runtime_seconds": 121.109, "successful_operations": {"READ": 4315350, "UPDATE": 4317039}}, {"slot": "E", "workload": "YCSB-B", "actual_seconds": 124.0, "host_bytes": 927883264, "host_pages": 226534, "gc_pages": 4510, "waf": 1.0199087112751286, "runtime_seconds": 121.204, "successful_operations": {"READ": 3538361, "UPDATE": 186909}}, {"slot": "F", "workload": "FIO-Fast", "actual_seconds": 120.0, "host_bytes": 19661344768, "host_pages": 4800133, "gc_pages": 11777764, "waf": 3.453632847256524}, {"slot": "G", "workload": "Varmail", "actual_seconds": 122.0, "host_bytes": 72039071744, "host_pages": 17587664, "gc_pages": 9439492, "waf": 1.5367109583171477, "process_runtimes_seconds": [120.009]}, {"slot": "H", "workload": "YCSB-A", "actual_seconds": 123.0, "host_bytes": 1781223424, "host_pages": 434869, "gc_pages": 4571, "waf": 1.0105112114222905, "runtime_seconds": 121.106, "successful_operations": {"READ": 4299127, "UPDATE": 4298684}}, {"slot": "I", "workload": "OLTP", "actual_seconds": 133.0, "host_bytes": 19325169664, "host_pages": 4718059, "gc_pages": 1450413, "waf": 1.3074173086856269, "process_runtimes_seconds": [30.076, 30.049, 30.07, 30.047]}], "actual_measured_seconds": 1134.0, "initial_load": {"runtime_seconds": 9.217, "successful_operations": {"INSERT": 250000}}, "active_sample_rows": 38, "block_stat_validation": "upstream runner stop boundary and host_bytes assertion passed; not independent NAND measurement"}

- 2026-10-05T20:15:33.156304+09:00 v6-mixT-20261005 START long PH_SECS=4000; raw=/home/oy/iCAT/result/v6-mixT-20261005/mixT-onlinev6-rep1

### mix-20260911 mixT onlinev6 — started 2026-10-05T20:15:33+09:00

- mixT: 9 time-based phases of 4000 s each — YCSB-A (load 600000 records) -> OLTP (32 MB x 10 files, 1000 s x 4 chunks) -> Varmail -> YCSB-A -> YCSB-B -> FIO-Fast test4 (payload x 4000/600) -> Varmail -> YCSB-A -> OLTP. FIO file (6 GiB) kept throughout. Module `nvmev-online-v6.ko`.
- Command: `env PH_SECS=4000 bash script/mix-20260911.sh mixT onlinev6 1`; evidence `result/v6-mixT-20261005/mixT-onlinev6-rep1/`.

- Finished 2026-10-06T06:18:09+09:00; mixT onlinev6 exit=0; evidence `/home/oy/iCAT/result/v6-mixT-20261005/mixT-onlinev6-rep1`; cleanup attempted.
- total host_bytes=7311156183040 host_pages=1784950240 gc_pages=1788970854 WAF=2.002253
- phaseA(sqlite-a) host_pages=12034506 gc_pages=328590 WAF=1.027304
- phaseB(oltp) host_pages=160914120 gc_pages=18976830 WAF=1.117931
- phaseC(varmail) host_pages=656616645 gc_pages=481027675 WAF=1.732585
- phaseD(sqlite-a) host_pages=11636846 gc_pages=84784 WAF=1.007286
- phaseE(sqlite-b) host_pages=8154544 gc_pages=729542 WAF=1.089464
- phaseF(test4) host_pages=160004398 gc_pages=623682834 WAF=4.897911
- phaseG(varmail) host_pages=592772814 gc_pages=612254394 WAF=2.032865
- phaseH(sqlite-a) host_pages=11690757 gc_pages=104233 WAF=1.008916
- phaseI(oltp) host_pages=171125610 gc_pages=51781972 WAF=1.302596
- phaseA-load host_pages=452310 gc_pages=235681 WAF=1.521061
- phaseA-run host_pages=11582196 gc_pages=92909 WAF=1.008022
- ycsb-load [OVERALL], Throughput(ops/sec), 34223.134839151266
- ycsb-run [OVERALL], Throughput(ops/sec), 83007.11634645399

- 2026-10-06T06:18:09.216741+09:00 v6-mixT-20261005 FINISHED long {"stage": "long", "finished_at": "2026-10-06T06:18:09.216358+09:00", "raw_path": "/home/oy/iCAT/result/v6-mixT-20261005/mixT-onlinev6-rep1", "status": "validated_saved_evidence", "validation_exit": 0, "waf": 2.00225250761052, "host_bytes": 7311156183040, "host_pages": 1784950240, "gc_pages": 1788970854, "phases": [{"slot": "A", "workload": "YCSB-A", "actual_seconds": 4012.0, "host_bytes": 49293336576, "host_pages": 12034506, "gc_pages": 328590, "waf": 1.0273039873842764, "runtime_seconds": 4001.736, "successful_operations": {"READ": 154753953, "UPDATE": 154742318}}, {"slot": "B", "workload": "OLTP", "actual_seconds": 4022.0, "host_bytes": 659104235520, "host_pages": 160914120, "gc_pages": 18976830, "waf": 1.117931415838461, "process_runtimes_seconds": [1001.359, 1001.543, 1001.386, 1001.452]}, {"slot": "C", "workload": "Varmail", "actual_seconds": 4004.0, "host_bytes": 2689501777920, "host_pages": 656616645, "gc_pages": 481027675, "waf": 1.7325852590897997, "process_runtimes_seconds": [4000.284]}, {"slot": "D", "workload": "YCSB-A", "actual_seconds": 4004.0, "host_bytes": 47664521216, "host_pages": 11636846, "gc_pages": 84784, "waf": 1.0072858229798693, "runtime_seconds": 4001.465, "successful_operations": {"READ": 154065270, "UPDATE": 154060171}}, {"slot": "E", "workload": "YCSB-B", "actual_seconds": 4003.0, "host_bytes": 33401012224, "host_pages": 8154544, "gc_pages": 729542, "waf": 1.0894644752667961, "runtime_seconds": 4001.145, "successful_operations": {"READ": 215739890, "UPDATE": 11355441}}, {"slot": "F", "workload": "FIO-Fast", "actual_seconds": 4000.0, "host_bytes": 655378014208, "host_pages": 160004398, "gc_pages": 623682834, "waf": 4.897910568683243}, {"slot": "G", "workload": "Varmail", "actual_seconds": 4004.0, "host_bytes": 2427997446144, "host_pages": 592772814, "gc_pages": 612254394, "waf": 2.032865171175006, "process_runtimes_seconds": [4000.259]}, {"slot": "H", "workload": "YCSB-A", "actual_seconds": 4003.0, "host_bytes": 47885340672, "host_pages": 11690757, "gc_pages": 104233, "waf": 1.0089158469378843, "runtime_seconds": 4001.351, "successful_operations": {"READ": 166079956, "UPDATE": 166060652}}, {"slot": "I", "workload": "OLTP", "actual_seconds": 4020.0, "host_bytes": 700930498560, "host_pages": 171125610, "gc_pages": 51781972, "waf": 1.302596274163756, "process_runtimes_seconds": [1001.137, 1001.247, 1001.092, 1001.095]}], "actual_measured_seconds": 36072.0, "initial_load": {"runtime_seconds": 7.305, "successful_operations": {"INSERT": 250000}}, "active_sample_rows": 1202, "block_stat_validation": "upstream runner stop boundary and host_bytes assertion passed; not independent NAND measurement"}

- 2026-10-06T06:18:09.732412+09:00 v6-mixT-20261005 FINISHED {"run_id": "v6-mixT-20261005", "status": "validated_saved_evidence", "exit_code": 0, "started_at": "2026-10-05T19:55:13.305528+09:00", "finished_at": "2026-10-06T06:18:09.731587+09:00", "error": null, "smoke_result": "/home/oy/iCAT/result/v6-mixT-20261005/smoke-result.json", "long_result": "/home/oy/iCAT/result/v6-mixT-20261005/long-result.json", "short_failure_blocks_long": true, "waf": 2.00225250761052}
