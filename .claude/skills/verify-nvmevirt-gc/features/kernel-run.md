# Kernel run on the experiment computer

The mix script loads one module, prepares the emulated 8 GiB NVMe device, runs a workload mix while measuring through `/proc/nvmevirt_measurement`, then unloads the module. It is the only path that yields experiment numbers. For the `smartgc-src` modules (`smartgc`, `smartgcq`, `smartgc-eq8`, `smartgcq-eq8`, `sg-greedy`, `sg-arm47`) this feature has not been driven yet.

## Sub-features

- `run-load` loads the module and finds the NVMeVirt controller.
- `run-measure` starts and stops the measurement and reads `host_pages`, `gc_pages` and the per-partition lines.
- `run-wear` reads the `wear part=N` lines that every `smartgc-src` build prints.
- `run-smartgc` reads the `smartgc part=N` lines and the `SmartGC init` and `SmartGC summary` kernel-log lines.
- `run-unload` unmounts, unloads the module, and saves the kernel log.

## How to get to it (user POV)

- Run `bash script/mix-gc-20261010.sh <label> <policy> [rep]` on the experiment computer, with the checkout at `/home/oy/iCAT`.
- Shortest full path: label `t4` (one FIO workload, about 600 s). `SMOKE=1` in front cuts the payload to one tenth and adds `-smoke` to the evidence directory.
- The GC-heavy mix used for the paper: `env MIXY_SEQ="F S V F V S F S V F V S F S V F V S F S" PH_SECS=1800 bash script/mix-gc-20261010.sh mixY <policy> 1`.

## Driving it with mix-gc-20261010.sh

Preconditions:

- The host is the original experiment computer. On any other host read `CODEX_HANDOFF.md` first and follow only that.
- `bash .claude/skills/verify-nvmevirt-gc/verify.sh doctor` exits 0: `nvmev` not loaded, `device.lock` free.
- `bash script/build-all-modules.sh` has produced `buildoutput/nvmev-<policy>.ko` for the running kernel.
- The evidence directory `result/gc-20261010/<label>-<policy>-rep<rep>[-smoke]` does not exist. The script refuses to overwrite it.
- `sudo -n` works for `insmod`, `rmmod`, `mount`, `dmesg`.

- **Smoke load.** Run `env SMOKE=1 bash script/mix-gc-20261010.sh t4 smartgc 1`. The script exits 0 and appends its own entry to `EXPERIMENT_LOG.md`.
- **Module identity.** Read `kernel.log` in the evidence directory. It contains a `SmartGC init` line with the parameter values in effect.
- **Measurement.** Read `final-control.txt`. The first line has `host_pages=` and `gc_pages=` above zero. Four `part=N` lines follow.
- **Wear report.** `final-control.txt` has four `wear part=N erase_min= erase_max= erase_mean_milli= erase_std_milli=` lines.
- **SmartGC report.** `final-control.txt` has four `smartgc part=N steps=... absorbed=... evicted=...` lines with `steps` above zero.
- **Unload.** `lsmod | grep nvmev` prints nothing, `mountpoint mnt` reports not a mountpoint, and `kernel.log` holds `Wear:` and `SmartGC summary` lines with no `BUG`, `Oops`, `Call Trace` or `soft lockup`.
- **Baseline pair.** Repeat with policy `sg-greedy`. Its `final-control.txt` has `wear` lines and no `smartgc` lines.
- **Proof.** The evidence directory, the script's log entry, and the lines above quoted from the files.

## Gotchas

- Not yet verified for `smartgc-src` modules on any host. The first run is itself the test of `insmod`, the proc handlers, locking and `rmmod`. Start with `SMOKE=1` and watch `dmesg` before a long run.
- The script computes WAF as `1 + gc_pages/host_pages` from the first line. With the GC buffer on, `host_pages` includes writes the buffer absorbed. The NAND-side WAF is the sum of `nand_pages=` over the `smartgc part=` lines divided by `host_pages` of the first line.
- `start` resets the SmartGC Q-table and counters, so learning begins cold at the measured interval.
- `smartgc` starts the Q-table at zero as in the paper. `smartgcq` starts Q(s, erase) at 2000. State which one a result used.
- Only one kernel run can exist at a time. A second start exits at once because `device.lock` is held.
- The script writes to `result/gc-20261010/` and `EXPERIMENT_LOG.md` by itself. Set `MIX_BASE` and `MIX_JOURNAL` to redirect on a second computer.
