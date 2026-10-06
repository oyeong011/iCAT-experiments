
## icat-2 mixV Table-3 prep restart — 2026-10-06T19:36:52.338390+09:00
- User explicitly interrupted obsolete mixV fixed37 (exit143). All544 files byte-verified and archived under result/inherit-20261006-oldprep; raw names end-oldprep; archive pushed53f08223. No old values are valid results of this new design.
- main pulled at 13b5b1835321c2cd0265c42ec7e9a09c6fda04da; git merge-base verifies40b28518 is ancestor. Dirty root preserved; exact upstream scripts and local safety/evidence diffs saved here.
- Command: bash script/icat2-mixV.sh; order fixed37 full-size fitcheck60s -> fixed37 long4000s -> fixed50 fitcheck60s -> fixed50 long4000s. Each has9phases YA/O/V/YA/YB/F/V/YA/O. Estimated fitcheck12–16min each including prep and loads, full campaign~20h40m. Never overwrite, shrink DB, or retry failed fitcheck automatically.
- Identical latest-main workload:6GiB sequential128KiB preset then3GiB random4KiB at10kIOPS seed20260907, excluded from measurement;6GiB FIO file kept through9phases. DB600000records loaded inA/D/H; deleted beforeB/F/I. OLTP32MiB files4chunks;Varmail24000files;YCSBA/B sameDB onlyD->E. This differs from older Table3 mixP in deletion beforeOLTP; not claim all transitions identical.
- Safety: current-kernel fixed37/fixed50 modules identified inmetadata, reused; NVMeVirt model/serial/PCI/vendor guards; physicalnvme0 forbidden; exclusive shareddevice.lock. One experiment at a time. Actualmachine/kernel/module hashes/source/seeds/environment inmetadata andhost-environment. YCSB/Filebench seeds not explicitly supplied.
- Measurement:manual=1, one continuous epoch per run;30s samples; keep initial learning/preparation-inside-phase costs. Validate9phase duration/order, DB600000insert successes forA/D/H, noYCSBerrors, fioerror0 exactbytes/time, Filebench allchunks, counters, host_bytes vsblockstats, same6GiBfileinode/size atphase starts, usableextent snapshots. GCpageWAF is not independent physicalNAND measurement.
- Local changes only safety adapter, stronger post-stage validation/publication, preserve overwritten DBload summaries/blockstats and fileidentity evidence. Raw extents are end-phase snapshots, not complete LBAwrite traces.
- Any failed stage stops all remaining stages; raw partiallogs/counters retained and pushedicat-2. Existing mixUfixed37/fixed50 waiters resume only after this newcampaign validates. Result rootresult/inherit-20261006; fitcheck subdirectoryfitcheck/.

### inherit-20261006 mixV fixed37 — started 2026-10-06T19:37:18+09:00

- mixV (inheritance): 9 time-based phases of 60 s — YCSB-A (load 600000 records) -> OLTP (DB deleted) -> Varmail -> YCSB-A (DB reloaded) -> YCSB-B (same DB) -> FIO-Fast (DB deleted; Table-3 FIO file overwritten, payload x 60/600) -> Varmail -> YCSB-A (DB reloaded) -> OLTP (DB deleted). Switches follow the Table-3 two-phase mixes; prep identical to Table 3 (6 GiB file kept all run). Extents recorded per switch. Module `nvmev-fixed37.ko`.
- Command: `env PH_SECS=60 bash script/mix-inherit-20261006.sh mixV fixed37 1`; evidence `result/inherit-20261006/fitcheck/mixV-fixed37-rep1/`.

- Finished 2026-10-06T19:49:50+09:00; mixV fixed37 exit=0; evidence `/home/oy/iCAT/result/inherit-20261006/fitcheck/mixV-fixed37-rep1`; cleanup attempted.
- total host_bytes=116991696896 host_pages=28562426 gc_pages=57276061 WAF=3.005294
- phaseA(sqlite-a) host_pages=2820731 gc_pages=1522945 WAF=1.539911
- phaseB(oltp) host_pages=2452694 gc_pages=1131989 WAF=1.461529
- phaseC(varmail) host_pages=8698022 gc_pages=13479088 WAF=2.549673
- phaseD(sqlite-a) host_pages=2404903 gc_pages=2717348 WAF=2.129920
- phaseE(sqlite-b) host_pages=317910 gc_pages=236498 WAF=1.743915
- phaseF(test4) host_pages=2400067 gc_pages=11612948 WAF=5.838593
- phaseG(varmail) host_pages=4899229 gc_pages=18335138 WAF=4.742454
- phaseH(sqlite-a) host_pages=2328072 gc_pages=5151433 WAF=3.212746
- phaseI(oltp) host_pages=2240693 gc_pages=3088597 WAF=2.378412
- phaseA-load host_pages=1398339 gc_pages=626720 WAF=1.448189
- phaseA-run host_pages=1422392 gc_pages=896225 WAF=1.630083
- ycsb-load [OVERALL], Throughput(ops/sec), 24395.202276885546
- ycsb-run [OVERALL], Throughput(ops/sec), 10282.619202373215

- mixV fixed37 fitcheck finished {"policy": "fixed37", "stage": "fitcheck", "finished_at": "2026-10-06T19:49:51.158385+09:00", "validation_exit": 1, "status": "failed_validation_preserved"}

- mixV campaign FINISHED {"run_id": "inherit-20261006", "exit_code": 1, "status": "failed_or_incomplete_preserved", "issues": ["entrypoint exited 1; inspect pipeline console and stage logs", "fixed37 fitcheck not validated", "fixed37 long not validated", "fixed50 fitcheck not validated", "fixed50 long not validated"], "finished_at": "2026-10-06T19:49:53.019719+09:00", "source_commit": "13b5b1835321c2cd0265c42ec7e9a09c6fda04da", "raw_path": "/home/oy/iCAT/result/inherit-20261006"}

## 공간 확인 실패 진단 2026-10-06T19:57:34.774680+09:00

CAT-37 fitcheck ended19:49 with runner exit0 but validation exit1. SQLITE_FULL occurred in A/D/E/H; failed YCSB operations: 2056988. CAT-37 long and CAT-50 were not started. WAF3.005294 is a failed-workload diagnostic, not valid policy performance. Raw compressed YCSB logs preserved; full counts/source paths in fitcheck-failure-diagnosis.json. No automatic retry or workload-size change.
