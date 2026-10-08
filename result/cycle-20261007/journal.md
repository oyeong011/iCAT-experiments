# mixX 30min x20 — icat-2 preregistration

- Run ID cycle-20261007-30min-20261008, registered 2026-10-08T10:33:17.541264+09:00; requested replacement ofobsolete20min x30 campaign. Source main 5e569073f2e980708ebebccb5104810c6c95779a, marker checked: `30-min phases, 20 phases`. Rootdirtycheckout retained; latestupstream scripts extracted from cleanpublishingworktree aftergitpull; inputfiles matchlatestmain exactly.
- Command `bash script/icat2-mixX.sh`. Order CAT50 60s x20 fitcheck -> CAT50 1800s x20 long -> CAT37 fitcheck -> CAT37long. About21hours includingchecks,prep,validation/publishing. No benchmark overlap. Anyfailure stopsremainingqueue andpreserves/pushes evidence.
- Sequence (FIO-Fast,Varmail,OLTP,FIO-Fast,OLTP,Varmail)x3 + (FIO-Fast,Varmail), 20phases,19transitions. FIO7phases,Varmail7phases,OLTP6phases. Long eachphase1800s;OLTP2x900s,fitcheck2x30s;Varmail24000files.
- Preparation6GiBseq128K+3GiBrand4K,10kIOPS seed20260907 excludedfrommeasurement;6GiBFIOfile retained. Hot512MiB,warm1536MiB,cold4GiB at24k/12k/4kIOPS. Seeds20260911/20261011/20261111,rep1;Filebenchseednotexplicit. Files deletedafterFilebenchphase,nodiscard. NoYCSB.
- Samehost/kernel/modules verifiedagainstpreviousmetadata; moduleSHA/currentkernel/provenance inmetadata.json, currentenvironment inhost-environment.txt. Moduleoptionsmemmap_start4G,memmap_size8192M,cpus1,2,measurement_manual1,measurement_uid1000;4FTLpartitions;fixedarm37/50. No rebuild.
- Mandatoryglobaldevice.lock, guardedNVMeVirtmodel/serial/vendor/PCI/mount only. Physicalnvme0n1 forbidden. Rootrunnerlocaldiff contains onlysafetyadapter andextraevidencecollection; workloadsequence/durations unchangedfromlatestmain.
- Validateexit0,exact20phasecompletion/order/durations,FIOfullrequestedI/O,error0,Filebenchcompletedchunks/noerrors,start/stop/flushboundaries,constantmeasurementepoch,counter/partitionvalidity,host_bytes=blockstatdelta*512,retained6GiBfile.30ssamplesaretime series,notindependentrepeats. WAF=1+gc_pages/host_pages,notindependentNANDmeasurement. LegacyA/Baliasesarenotadditionalphases.
- Oldresults preservedbyteexactly under `/home/oy/iCAT/result/cycle-20261007-20min`, manifest20min-preservation.json;CAT50completedoldWAF3.366786233869258,CAT37partialexit143. Do notpoolwith30minresults. Already pushedcd4e3f98.
- Evidence `/home/oy/iCAT/result/cycle-20261007`; publishonlyicat-2,atstagecompletionandfailure. Currentstatepreregistered,notyetstarted.

### cycle-20261007 mixX fixed50 — started 2026-10-08T10:34:12+09:00

- mixX: (FIO-Fast, Varmail, OLTP, FIO-Fast, OLTP, Varmail) x 3 + (FIO-Fast, Varmail) = 20 time-based phases of 60 s. Table-3 prep, 6 GiB FIO file kept; FIO payload x 60/600; Filebench files deleted after each Filebench phase; no YCSB. Module `nvmev-fixed50.ko`.
- Command: `env PH_SECS=60 bash script/mix-cycle-20261007.sh mixX fixed50 1`; evidence `result/cycle-20261007/fitcheck/mixX-fixed50-rep1/`.

- Launch confirmed {"time": "2026-10-08T10:34:36.822603+09:00", "unit": "icat-cycle-20261008-30min", "command": "bash script/icat2-mixX.sh", "status": "started_fixed50_fitcheck_preparation", "source_commit": "5e569073f2e980708ebebccb5104810c6c95779a", "remote_prereg_commit": "187ab4a6618cfcebdf0bdd0211c32e3a3216bd35", "old_archive_commit": "e11980d6", "old_cancel_exit_code": 143}

- Finished 2026-10-08T10:56:43+09:00; mixX fixed50 exit=0; evidence `/home/oy/iCAT/result/cycle-20261007/fitcheck/mixX-fixed50-rep1`; cleanup attempted.
- total host_bytes=327901016064 host_pages=80053959 gc_pages=165101194 WAF=3.062374
- phaseA(test4) host_pages=2400067 gc_pages=2038244 WAF=1.849245
- phaseB(varmail) host_pages=8040770 gc_pages=12715436 WAF=2.581370
- phaseS01(test4) host_pages=2400067 gc_pages=2038244 WAF=1.849245
- phaseS02(varmail) host_pages=8040770 gc_pages=12715436 WAF=2.581370
- phaseS03(oltp) host_pages=2450082 gc_pages=1698832 WAF=1.693378
- phaseS04(test4) host_pages=2400068 gc_pages=5266277 WAF=3.194220
- phaseS05(oltp) host_pages=2370943 gc_pages=2304247 WAF=1.971869
- phaseS06(varmail) host_pages=7316060 gc_pages=14516168 WAF=2.984151
- phaseS07(test4) host_pages=2400068 gc_pages=6977410 WAF=3.907172
- phaseS08(varmail) host_pages=6701587 gc_pages=16503975 WAF=3.462697
- phaseS09(oltp) host_pages=2383422 gc_pages=2100615 WAF=1.881344
- phaseS10(test4) host_pages=2400068 gc_pages=7130245 WAF=3.970851
- phaseS11(oltp) host_pages=2307431 gc_pages=2255941 WAF=1.977685
- phaseS12(varmail) host_pages=6969624 gc_pages=15566338 WAF=3.233454
- phaseS13(test4) host_pages=2400068 gc_pages=7522417 WAF=4.134252
- phaseS14(varmail) host_pages=6590635 gc_pages=16720649 WAF=3.537032
- phaseS15(oltp) host_pages=2344974 gc_pages=2102303 WAF=1.896514
- phaseS16(test4) host_pages=2400067 gc_pages=7292201 WAF=4.038332
- phaseS17(oltp) host_pages=2299935 gc_pages=2331837 WAF=2.013871
- phaseS18(varmail) host_pages=6934545 gc_pages=15697732 WAF=3.263700
- phaseS19(test4) host_pages=2400068 gc_pages=7633666 WAF=4.180604
- phaseS20(varmail) host_pages=6543474 gc_pages=16726661 WAF=3.556236
- ycsb-load 
- ycsb-run 

- mixX fixed50 fitcheck finished {"policy": "fixed50", "stage": "fitcheck", "finished_at": "2026-10-08T10:56:43.933876+09:00", "validation_exit": 0, "status": "validated_saved_evidence", "waf": 3.0623738795978848, "host_bytes": 327901016064, "host_pages": 80053959, "gc_pages": 165101194, "actual_measured_seconds": 1269.0, "phases": [{"slot": "S01", "workload": "FIO-Fast", "actual_seconds": 61.0, "waf": 1.8492446252542116, "host_bytes": 9830674432, "host_pages": 2400067, "gc_pages": 2038244}, {"slot": "S02", "workload": "Varmail", "actual_seconds": 63.0, "waf": 2.5813704408906113, "host_bytes": 32934993920, "host_pages": 8040770, "gc_pages": 12715436, "process_runtimes_seconds": [60.004999999999995]}, {"slot": "S03", "workload": "OLTP", "actual_seconds": 67.0, "waf": 1.6933776094024608, "host_bytes": 10035535872, "host_pages": 2450082, "gc_pages": 1698832, "process_runtimes_seconds": [30.084, 30.061]}, {"slot": "S04", "workload": "FIO-Fast", "actual_seconds": 60.0, "waf": 3.19421991376911, "host_bytes": 9830678528, "host_pages": 2400068, "gc_pages": 5266277}, {"slot": "S05", "workload": "OLTP", "actual_seconds": 66.0, "waf": 1.9718694207325946, "host_bytes": 9711382528, "host_pages": 2370943, "gc_pages": 2304247, "process_runtimes_seconds": [30.06, 30.078999999999997]}, {"slot": "S06", "workload": "Varmail", "actual_seconds": 64.0, "waf": 2.984151032112913, "host_bytes": 29966581760, "host_pages": 7316060, "gc_pages": 14516168, "process_runtimes_seconds": [60.004999999999995]}, {"slot": "S07", "workload": "FIO-Fast", "actual_seconds": 60.0, "waf": 3.9071717967990907, "host_bytes": 9830678528, "host_pages": 2400068, "gc_pages": 6977410}, {"slot": "S08", "workload": "Varmail", "actual_seconds": 64.0, "waf": 3.4626965224804214, "host_bytes": 27449700352, "host_pages": 6701587, "gc_pages": 16503975, "process_runtimes_seconds": [60.005]}, {"slot": "S09", "workload": "OLTP", "actual_seconds": 67.0, "waf": 1.8813441346098174, "host_bytes": 9762496512, "host_pages": 2383422, "gc_pages": 2100615, "process_runtimes_seconds": [30.029999999999998, 30.077]}, {"slot": "S10", "workload": "FIO-Fast", "actual_seconds": 60.0, "waf": 3.970851242548128, "host_bytes": 9830678528, "host_pages": 2400068, "gc_pages": 7130245}, {"slot": "S11", "workload": "OLTP", "actual_seconds": 67.0, "waf": 1.9776851398806725, "host_bytes": 9451237376, "host_pages": 2307431, "gc_pages": 2255941, "process_runtimes_seconds": [30.06, 30.051000000000002]}, {"slot": "S12", "workload": "Varmail", "actual_seconds": 63.0, "waf": 3.2334544876452447, "host_bytes": 28547579904, "host_pages": 6969624, "gc_pages": 15566338, "process_runtimes_seconds": [60.004999999999995]}, {"slot": "S13", "workload": "FIO-Fast", "actual_seconds": 61.0, "waf": 4.134251612870969, "host_bytes": 9830678528, "host_pages": 2400068, "gc_pages": 7522417}, {"slot": "S14", "workload": "Varmail", "actual_seconds": 63.0, "waf": 3.5370315606918, "host_bytes": 26995240960, "host_pages": 6590635, "gc_pages": 16720649, "process_runtimes_seconds": [60.005]}, {"slot": "S15", "workload": "OLTP", "actual_seconds": 67.0, "waf": 1.8965144176438629, "host_bytes": 9605013504, "host_pages": 2344974, "gc_pages": 2102303, "process_runtimes_seconds": [30.034000000000002, 30.083]}, {"slot": "S16", "workload": "FIO-Fast", "actual_seconds": 60.0, "waf": 4.038332263224318, "host_bytes": 9830674432, "host_pages": 2400067, "gc_pages": 7292201}, {"slot": "S17", "workload": "OLTP", "actual_seconds": 67.0, "waf": 2.013870826784235, "host_bytes": 9420533760, "host_pages": 2299935, "gc_pages": 2331837, "process_runtimes_seconds": [30.07, 30.061]}, {"slot": "S18", "workload": "Varmail", "actual_seconds": 64.0, "waf": 3.263700358134528, "host_bytes": 28403896320, "host_pages": 6934545, "gc_pages": 15697732, "process_runtimes_seconds": [60.004999999999995]}, {"slot": "S19", "workload": "FIO-Fast", "actual_seconds": 60.0, "waf": 4.180604049551929, "host_bytes": 9830678528, "host_pages": 2400068, "gc_pages": 7633666}, {"slot": "S20", "workload": "Varmail", "actual_seconds": 64.0, "waf": 3.5562355715022327, "host_bytes": 26802069504, "host_pages": 6543474, "gc_pages": 16726661, "process_runtimes_seconds": [60.006]}], "sample_rows": 46, "transition_count": 19, "measurement": "manual FTLpageWAF, hostbytes verified againstblockstat, no independentNANDmeasurement"}

### cycle-20261007 mixX fixed50 — started 2026-10-08T10:56:47+09:00

- mixX: (FIO-Fast, Varmail, OLTP, FIO-Fast, OLTP, Varmail) x 3 + (FIO-Fast, Varmail) = 20 time-based phases of 1800 s. Table-3 prep, 6 GiB FIO file kept; FIO payload x 1800/600; Filebench files deleted after each Filebench phase; no YCSB. Module `nvmev-fixed50.ko`.
- Command: `env PH_SECS=1800 bash script/mix-cycle-20261007.sh mixX fixed50 1`; evidence `result/cycle-20261007/mixX-fixed50-rep1/`.

- Finished 2026-10-08T20:59:38+09:00; mixX fixed50 exit=0; evidence `/home/oy/iCAT/result/cycle-20261007/mixX-fixed50-rep1`; cleanup attempted.
- total host_bytes=9787292794880 host_pages=2389475780 gc_pages=5460714407 WAF=3.285319
- phaseA(test4) host_pages=72001978 gc_pages=58611828 WAF=1.814031
- phaseB(varmail) host_pages=238734598 gc_pages=446659518 WAF=2.870946
- phaseS01(test4) host_pages=72001978 gc_pages=58611828 WAF=1.814031
- phaseS02(varmail) host_pages=238734598 gc_pages=446659518 WAF=2.870946
- phaseS03(oltp) host_pages=72787013 gc_pages=28560401 WAF=1.392383
- phaseS04(test4) host_pages=72001981 gc_pages=337973044 WAF=5.693941
- phaseS05(oltp) host_pages=69178225 gc_pages=41575875 WAF=1.600997
- phaseS06(varmail) host_pages=204821834 gc_pages=449648818 WAF=3.195317
- phaseS07(test4) host_pages=72001979 gc_pages=343537424 WAF=5.771222
- phaseS08(varmail) host_pages=204298647 gc_pages=452367295 WAF=3.214245
- phaseS09(oltp) host_pages=71836288 gc_pages=29680759 WAF=1.413172
- phaseS10(test4) host_pages=72001981 gc_pages=338918446 WAF=5.707071
- phaseS11(oltp) host_pages=69652922 gc_pages=41346654 WAF=1.593610
- phaseS12(varmail) host_pages=204755984 gc_pages=448779862 WAF=3.191779
- phaseS13(test4) host_pages=72001979 gc_pages=343635725 WAF=5.772587
- phaseS14(varmail) host_pages=202596045 gc_pages=451365584 WAF=3.227909
- phaseS15(oltp) host_pages=71769168 gc_pages=30742607 WAF=1.428354
- phaseS16(test4) host_pages=72001980 gc_pages=338874436 WAF=5.706460
- phaseS17(oltp) host_pages=68738370 gc_pages=41374062 WAF=1.601906
- phaseS18(varmail) host_pages=203566912 gc_pages=442853382 WAF=3.175468
- phaseS19(test4) host_pages=72001982 gc_pages=343647369 WAF=5.772749
- phaseS20(varmail) host_pages=202725911 gc_pages=450561318 WAF=3.222515
- ycsb-load 
- ycsb-run 

- mixX fixed50 long finished {"policy": "fixed50", "stage": "long", "finished_at": "2026-10-08T20:59:39.166416+09:00", "validation_exit": 0, "status": "validated_saved_evidence", "waf": 3.285319002898619, "host_bytes": 9787292794880, "host_pages": 2389475780, "gc_pages": 5460714407, "actual_measured_seconds": 36088.0, "phases": [{"slot": "S01", "workload": "FIO-Fast", "actual_seconds": 1800.0, "waf": 1.814030803431539, "host_bytes": 294920101888, "host_pages": 72001978, "gc_pages": 58611828}, {"slot": "S02", "workload": "Varmail", "actual_seconds": 1804.0, "waf": 2.870945902864067, "host_bytes": 977856913408, "host_pages": 238734598, "gc_pages": 446659518, "process_runtimes_seconds": [1800.1209999999999]}, {"slot": "S03", "workload": "OLTP", "actual_seconds": 1810.0, "waf": 1.3923831989093989, "host_bytes": 298135605248, "host_pages": 72787013, "gc_pages": 28560401, "process_runtimes_seconds": [901.053, 901.18]}, {"slot": "S04", "workload": "FIO-Fast", "actual_seconds": 1800.0, "waf": 5.69394090698699, "host_bytes": 294920114176, "host_pages": 72001981, "gc_pages": 337973044}, {"slot": "S05", "workload": "OLTP", "actual_seconds": 1810.0, "waf": 1.6009965563585942, "host_bytes": 283354009600, "host_pages": 69178225, "gc_pages": 41575875, "process_runtimes_seconds": [901.094, 901.087]}, {"slot": "S06", "workload": "Varmail", "actual_seconds": 1803.0, "waf": 3.1953168234984166, "host_bytes": 838950232064, "host_pages": 204821834, "gc_pages": 449648818, "process_runtimes_seconds": [1800.1190000000001]}, {"slot": "S07", "workload": "FIO-Fast", "actual_seconds": 1801.0, "waf": 5.771221968773942, "host_bytes": 294920105984, "host_pages": 72001979, "gc_pages": 343537424}, {"slot": "S08", "workload": "Varmail", "actual_seconds": 1803.0, "waf": 3.214245182935548, "host_bytes": 836807258112, "host_pages": 204298647, "gc_pages": 452367295, "process_runtimes_seconds": [1800.118]}, {"slot": "S09", "workload": "OLTP", "actual_seconds": 1810.0, "waf": 1.4131722257141126, "host_bytes": 294241435648, "host_pages": 71836288, "gc_pages": 29680759, "process_runtimes_seconds": [901.196, 901.028]}, {"slot": "S10", "workload": "FIO-Fast", "actual_seconds": 1801.0, "waf": 5.707071129056852, "host_bytes": 294920114176, "host_pages": 72001981, "gc_pages": 338918446}, {"slot": "S11", "workload": "OLTP", "actual_seconds": 1809.0, "waf": 1.5936097555246858, "host_bytes": 285298368512, "host_pages": 69652922, "gc_pages": 41346654, "process_runtimes_seconds": [900.9910000000001, 901.06]}, {"slot": "S12", "workload": "Varmail", "actual_seconds": 1804.0, "waf": 3.191778981170094, "host_bytes": 838680510464, "host_pages": 204755984, "gc_pages": 448779862, "process_runtimes_seconds": [1800.119]}, {"slot": "S13", "workload": "FIO-Fast", "actual_seconds": 1800.0, "waf": 5.772587222915082, "host_bytes": 294920105984, "host_pages": 72001979, "gc_pages": 343635725}, {"slot": "S14", "workload": "Varmail", "actual_seconds": 1803.0, "waf": 3.227909157851527, "host_bytes": 829833400320, "host_pages": 202596045, "gc_pages": 451365584, "process_runtimes_seconds": [1800.118]}, {"slot": "S15", "workload": "OLTP", "actual_seconds": 1810.0, "waf": 1.428353955559301, "host_bytes": 293966512128, "host_pages": 71769168, "gc_pages": 30742607, "process_runtimes_seconds": [901.018, 901.06]}, {"slot": "S16", "workload": "FIO-Fast", "actual_seconds": 1800.0, "waf": 5.706459961239955, "host_bytes": 294920110080, "host_pages": 72001980, "gc_pages": 338874436}, {"slot": "S17", "workload": "OLTP", "actual_seconds": 1811.0, "waf": 1.6019063588502318, "host_bytes": 281552363520, "host_pages": 68738370, "gc_pages": 41374062, "process_runtimes_seconds": [901.131, 900.959]}, {"slot": "S18", "workload": "Varmail", "actual_seconds": 1803.0, "waf": 3.1754683884972428, "host_bytes": 833810071552, "host_pages": 203566912, "gc_pages": 442853382, "process_runtimes_seconds": [1800.1200000000001]}, {"slot": "S19", "workload": "FIO-Fast", "actual_seconds": 1801.0, "waf": 5.7727487418332455, "host_bytes": 294920118272, "host_pages": 72001982, "gc_pages": 343647369}, {"slot": "S20", "workload": "Varmail", "actual_seconds": 1804.0, "waf": 3.2225147036088546, "host_bytes": 830365331456, "host_pages": 202725911, "gc_pages": 450561318, "process_runtimes_seconds": [1800.119]}], "sample_rows": 1205, "transition_count": 19, "measurement": "manual FTLpageWAF, hostbytes verified againstblockstat, no independentNANDmeasurement"}
