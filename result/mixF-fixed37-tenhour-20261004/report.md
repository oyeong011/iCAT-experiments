
### mixF-fixed37-tenhour-20261004 preregistration 2026-10-04T00:08:02.602657+09:00

Command: `env MULT=30 VM_RUN=900 VM_CHUNKS=20 bash script/mix-20260911.sh mixF fixed37 1`. Latest main 4557a68510759320b79d083977959ffe16d6a5d8 pulled in clean icat-2 worktree. Measurement snapshot differs only by documented physical-controller compatibility check using strong NVMeVirt guard. Purpose: CAT37 baseline for 10h mixF. Wait for existing CAT50 then v4, single shared device lock; no concurrent experiments. Expected ~10h plus preparation, estimated Oct4 18:40 -> Oct5 04:45 KST dependent on predecessors.

FIO A fixed write amounts hot1769472000000/warm884736000000/cold294912000000 bytes at24000/12000/4000 IOPS imply nominal18000s; actual wall time can be longer and is recorded, not forced. B Varmail one18000s process because profile has no reuse. Same6GiB+3GiB preparation outside counters, seed20260907; workload seeds20260911/20261011/20261111. module fixed37 SHA/kernel and machine_id/hostname in metadata/module-info; build-option equivalence to another host remains unconfirmed.

Acceptance: exit0, fio all errors0 and every requested write byte complete, zero prepared/start counters, final/stopped equality and partition totals, block-stat match asserted by runner, Varmail one IO Summary with actual runtime, policy37 evidence. Save 30s raw counters/WAF including active/preparation distinction, actual time and final totals. Retain failures. Publish only this campaign to icat-2 after validation. Existing source changes/results preserved; global mount/module/model/serial/PCI protection applied.

User priority update: old OLTP queue cancelled; mixF37 runs as soon as active run cleanup/global lock release finishes, followed by mixF50. Previous estimates superseded.
