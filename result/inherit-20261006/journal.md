
## mixV FIO5GiB / DB600000 — icat-2 local execution preregistration 2026-10-06T22:23:54.416883+09:00
- User request: stop all waiting work; main pull at8e338f49a2191d4a1f789a42fca1c3f95ab37037, verified0698bc27 ancestor. Execute fixed37 thenfixed50: `env MIXV_FIO_GB=5 MIXV_RECORDS=600000 PH_SECS=4000 bash script/mix-inherit-20261006.sh mixV POLICY 1`. No additional fitcheck or DB size search.
- Each9phases YA/O/V/YA/YB/F/V/YA/O x4000s (~10h). Total~20h10–20min including prep/load. Error at any stage stops queue, preserves evidence, publishesicat-2. No automatic retry. Pending old mixUfixed37/fixed50 explicitly stopped and will not resume.
- Preparation5GiB sequential128KiB +2.5GiB random4KiB at10kIOPS seed20260907; excluded frommanual counters. FIOfile5GiB kept across phases; regions512MiB hot,1536MiB warm,3GiB cold, original40kIOPS and bytepayload retained. This differs from original6GiB FIOFast and must not be treated as identical workload.
- DB600000records loadedA/D/H, deleted beforeB/F/I; D->E sameDB;OLTP32MiB4x1000s;Varmail24000files4000s. Request/insert Return=ERROR triggers upstream exit3 after that YCSB call. Strong post-run validation also rejects errors, incomplete operations/durations, invalid counters, wrongfile/regions. Full initial phase costs and transition writes included.
- Run IDs mixV-fixed37-rep1 andmixV-fixed50-rep1; raw paths result/inherit-20261006/. Previous6GiBfailed rawfitcheck stays unchanged atfitcheck/mixV-fixed37-rep1; previous control/results preserved inarchive-6g-fitcheck-20261006 with hashes. Oldprep archive unchanged.
- Source/module/kernel/machine/seed metadata saved inmetadata.json andhost-environment.txt. Existing currentkernel fixed37/fixed50 modules reused by hash; no rebuild. Globaldevice.lock held throughcampaign; mandatory NVMeVirt guards rejectphysicalnvme0n1. Immutable runner copy equals installed rootrunner; localdiff only existingdevice safety and extra evidence(stat file identity, preserved load summaries, blockstat snapshots).
-30s counters/extents/rawlogs retained. Per-run validate exit0,9phasecompletion,fioerror0/exactbytes/runtime/cold3GiB, all600000inserts A/D/H and zeroYCSBrequesterrors, Filebenchchunks, manualstart/stop/final, host_bytes vsblockstat, fixedarm andparts, retained5GiB inode. Extents are file snapshots, not wholeLBA write trace; GC pageWAF not independentphysicalNAND measurement.

### inherit-20261006 mixV fixed37 — started 2026-10-06T22:24:43+09:00

- mixV (inheritance): 9 time-based phases of 4000 s — YCSB-A (load 600000 records) -> OLTP (DB deleted) -> Varmail -> YCSB-A (DB reloaded) -> YCSB-B (same DB) -> FIO-Fast (DB deleted; Table-3 FIO file overwritten, payload x 4000/600) -> Varmail -> YCSB-A (DB reloaded) -> OLTP (DB deleted). Switches follow the Table-3 two-phase mixes; prep identical to Table 3 (6 GiB file kept all run). Extents recorded per switch. Module `nvmev-fixed37.ko`.
- Command: `env PH_SECS=4000 bash script/mix-inherit-20261006.sh mixV fixed37 1`; evidence `result/inherit-20261006/mixV-fixed37-rep1/`.

- Actual requested settings: MIXV_FIO_GB=5 MIXV_RECORDS=600000 PH_SECS=4000; these override stale fixed-size descriptions above.
