---
name: verify-nvmevirt-gc
description: Verify the NVMeVirt GC policies of the iCAT experiments repo (Greedy, fixed CAT, SmartGC in smartgc-src) by driving the real FTL code. Covers the userspace FTL driver, the kernel-module compile, and the real kernel run on the experiment computer. Use it after changing conv_ftl.c or a module source copy, before claiming a GC policy works, and before starting a kernel experiment with a new module.
---

# Verify NVMeVirt GC policies

The product of this repo is an NVMeVirt kernel module (`nvmev.ko`) whose FTL picks GC victims with one of several policies. A user touches it in three ways, and each has its own proof.

| Surface | Where it runs | What it proves |
|---|---|---|
| Userspace FTL driver (`smartgc-src/test/`) | any Linux or WSL with gcc | FTL logic: mapping, line and GC-buffer invariants hold under millions of writes |
| Kernel-module compile | any Linux or WSL with the experiment kernel's headers | the module builds for the experiment kernel and exposes its parameters |
| Kernel run (`script/mix-gc-20261010.sh`) | the original experiment computer only | the module loads, serves I/O, and reports WAF through `/proc/nvmevirt_measurement` |

The first two never touch a device. The third is the only one that produces experiment numbers. A pass on the first two is not a pass on the third.

## Rules that come before any drive

- `AGENTS.md` makes every drive an experiment. Before running, append an entry to `EXPERIMENT_LOG.md` with a run ID, purpose, pass criteria, commands, changed and fixed variables, environment, and the evidence path. After running, append status, exit codes, results, limits, and cleanup state. Failed and aborted drives are logged too.
- Never delete or overwrite an evidence file. Rerun under a new name (the helper refuses to overwrite) and say why in the log.
- If the host is not the original experiment computer, read `CODEX_HANDOFF.md` before a kernel run.
- Numbers from the userspace driver are not measurements. It uses a fake clock and a zero-delay channel model. Never report its WAF as an experiment result.

## Helper

`verify.sh` sits next to this file. It runs inside Linux or WSL from any directory and writes evidence to `result/<run-id>/`.

```bash
V=.claude/skills/verify-nvmevirt-gc/verify.sh
bash $V doctor                                              # read-only readiness check
bash $V sim <run-id> <name> <policy> [sim options]          # one userspace FTL run
bash $V kbuild <run-id> <tag> <src dir> [make vars]         # compile one module copy
bash $V check <log>...                                      # pass/fail of sim logs
bash $V same <log A> <log B>                                # same host and GC page counts
```

From Windows, call it through WSL with plain arguments only. `wsl.exe` passes the command line through a second shell, so `$variables`, quotes and `&&` inside the command are mangled. Set environment variables with `env`.

```powershell
wsl -d Ubuntu-26.04 -- bash /mnt/c/Users/oyeon/orca/iCAT-experiments/.claude/skills/verify-nvmevirt-gc/verify.sh doctor
wsl -d Ubuntu-26.04 -- env KDIR=/home/oy/sgbuild/hdr/root/usr/src/linux-headers-7.0.0-31-generic bash /mnt/c/Users/oyeon/orca/iCAT-experiments/.claude/skills/verify-nvmevirt-gc/verify.sh kbuild <run-id> <tag> smartgc-src NVMEVIRT_GC_POLICY=SMARTGC
```

## Launch

There is no server. Each drive builds what it needs in its own temporary directory and removes it on exit.

- Userspace driver: needs `gcc`. `verify.sh sim` compiles `smartgc-src/test/sim.c` together with the real `conv_ftl.c`, `ssd.c` and `pqueue/pqueue.c` of the chosen source copy, then runs it. Ready means the log ends with `exit=0`.
- Kernel compile: needs the build directory of the experiment kernel. On the experiment computer that is `/lib/modules/$(uname -r)/build`. On the Windows development PC the headers of kernel 7.0.0-31-generic are unpacked at `/home/oy/sgbuild/hdr/root/usr/src/linux-headers-7.0.0-31-generic` in WSL, so pass that as `KDIR`.
- Kernel run: `bash script/build-all-modules.sh` once per kernel (about 15 minutes, writes `buildoutput/nvmev-<tag>.ko`), then `script/mix-gc-20261010.sh` loads the module itself with `insmod`, mounts the device, runs the workload, unloads, and writes its own `EXPERIMENT_LOG.md` entry.

## Doctor

Run `bash $V doctor` first, and again whenever something looks off. It prints one line per surface (`sim:`, `kbuild:`, `kernel run:`) and exits non-zero when a required file is missing, when `nvmev` is already loaded, or when `result/mix-20260911/device.lock` is held. A loaded module or a held lock means an experiment is running. Do not drive the device then.

## Drive

Use the feature map in [`features/`](features/README.md). Each file gives the exact commands and the end state that proves the feature.

- [Userspace FTL run](features/sim-ftl.md)
- [SmartGC victim selection rule](features/sim-selection-rule.md)
- [Unchanged baseline policies](features/sim-baseline-equivalence.md)
- [Kernel-module compile](features/module-build.md)
- [Kernel run on the experiment computer](features/kernel-run.md)

## Evidence

- Location: `result/<run-id>/`, one file per drive. Link it from the `EXPERIMENT_LOG.md` entry.
- A sim log holds the command line, host, git commit, changed-file count and SHA256 of the sources, the full driver output, `exit=<rc>` and timestamps. The proof line is `sim policy=... host_pages=... gc_pages=... waf=... invariants=ok`.
- A kbuild log holds the same header, the compiler output, `exit=<rc>`, the module SHA256 and its `parm=` list.
- A kernel run stores its evidence under `result/gc-20261010/<label>-<policy>[-rep<n>][-smoke]/`: `final-control.txt`, `kernel.log`, `kernel-snapshots/`.
- Proof standards: drive the real FTL code path through NVMe write and read commands, not internal setters. Capture the command and the resulting state. Check side effects too: the erase-wear lines, the per-partition counters, and for SmartGC the `smartgc part=` lines. Before reporting a number, reread it from the evidence file.
- `verify.sh check` passes a log only when it has `exit=0`, a `sim` line ending in `invariants=ok`, and no `BUG at` or `INVARIANT FAILED`.

## Cleanup

- `verify.sh` removes its own temporary build directory on exit. Nothing else needs cleaning for the userspace driver and the compile.
- The kernel run script unmounts, runs `rmmod nvmev`, and stops its collectors in its exit handler. If it was killed, check `lsmod | grep nvmev` and `mountpoint mnt` and undo only what that run started. Never kill processes by name.
- Cleanup never removes anything under `result/`.

## What has and has not been proven

Proven on the Windows development PC in WSL on 2026-11-19 (run `verify-skill-20261119` in `EXPERIMENT_LOG.md`): doctor, one userspace SmartGC run, the baseline comparison against an earlier log, a deliberate failure, and one kernel-module compile. The selection-rule feature was driven the same day (run `verify-skill-20261119b`).

Not covered by this skill: the analysis and figure scripts in `analysis/` and the dashboard built by `analysis/dashboard-build.sh`. They read result files and never drive the module.

Not proven anywhere yet: the kernel run with a `smartgc-src` module. The stand-in skipped these steps: `insmod` with the memmap arguments, I/O worker threads and locking, the `/proc/nvmevirt_measurement` read and write handlers in a real kernel, module parameters at load time, `rmmod` teardown, and real timing. They stay unverified until [the kernel run](features/kernel-run.md) is driven on the experiment computer.

Keep the map current with `/pstack:maintain-verification-skill` when policies or scripts change.
