# NVMeVirt GC verification map

This directory is the maintained source for verifying the GC policies of the NVMeVirt modules in this repo. Read this index before driving, then use the matching feature file as the recipe.

## Baseline preconditions

- Run from a checkout of this repo. `V=.claude/skills/verify-nvmevirt-gc/verify.sh`.
- `bash $V doctor` exits 0 and reports `sim: ready`. A kernel compile also needs `kbuild: ready`.
- An `EXPERIMENT_LOG.md` entry for the run ID exists before the first drive (see `AGENTS.md`).
- Pick a new run ID per verification, for example `verify-<topic>-<yyyymmdd>`. Evidence lands in `result/<run-id>/`.
- Userspace drives are independent. Several can run at once. Only one kernel run can exist at a time.

## Driving conventions

- Treat every command as literal. Sim options are `key=value` words with no spaces.
- The standard userspace workload is `capacity_mib=8192 overwrite_x=6`. It matches the experiment device size (8 GiB, 4 partitions, 8192 lines each) and takes under a minute.
- Choose the module source copy with `SIM_SRC=<dir>` in front of the command. The default is `smartgc-src`.
- From Windows, wrap each command as `wsl -d Ubuntu-26.04 -- bash /mnt/c/Users/oyeon/orca/iCAT-experiments/<command>` with plain arguments, and `env NAME=value` for variables.

## Proof and skip reporting

- A drive is proven by its evidence file plus the `PASS` line of `verify.sh`.
- Report the run ID, the drive name, and the proof line copied from the file.
- A feature that cannot run on this host is reported as not verified, with the reason. Never count a userspace pass as a kernel pass.
- Userspace WAF values are checks of logic, never measurements.

## Feature entry contract

Each feature file starts with an H1 title and one paragraph on the user-visible behavior, then four H2 sections in this order: `Sub-features`, `How to get to it (user POV)`, `Driving it with verify.sh` (or the named harness), `Gotchas`.

## Features

- [Userspace FTL run](./sim-ftl.md) covers Greedy, fixed CAT and SmartGC under the userspace driver, with SmartGC options.
- [Unchanged baseline policies](./sim-baseline-equivalence.md) covers Greedy and fixed CAT behaving the same in `smartgc-src` as in `varmail-compare-src`.
- [Kernel-module compile](./module-build.md) covers building each module variant against the experiment kernel's headers.
- [Kernel run on the experiment computer](./kernel-run.md) covers loading a module and measuring WAF with the mix script. Not yet driven for `smartgc-src` modules.
