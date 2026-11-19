# Kernel-module compile

Each experiment module is one source copy compiled with a GC policy chosen by make variables. A successful compile produces `nvmev.ko` for the experiment kernel with the policy's module parameters.

## Sub-features

- `build-smartgc` compiles SmartGC with the Q-table starting at zero (`NVMEVIRT_GC_POLICY=SMARTGC`).
- `build-smartgcq` compiles SmartGC with `SMARTGC_Q_INIT=2000`.
- `build-sg-greedy` compiles Greedy from `smartgc-src` (`NVMEVIRT_GC_POLICY=GREEDY`).
- `build-sg-arm` compiles a fixed CAT arm from `smartgc-src` (`NVMEVIRT_GC_POLICY=CAT_FIG7 FIXED_ARM=47`).
- `build-all` rebuilds every experiment module into `buildoutput/` on the experiment computer.

## How to get to it (user POV)

- Run `bash script/build-all-modules.sh` on the experiment computer. It writes `buildoutput/nvmev-<tag>.ko`, one `buildoutput/build-<tag>.log` per module, and `buildoutput/build-manifest-<kernel>.tsv`.
- Run `make -C <kernel build dir> M=<source copy> <make vars> modules` for one module.

## Driving it with verify.sh

Preconditions:

- `bash $V doctor` reports `kbuild: ready`. On the Windows development PC set `KDIR=/home/oy/sgbuild/hdr/root/usr/src/linux-headers-7.0.0-31-generic`.
- No file `result/<run-id>/kbuild-<tag>.log` exists yet.

- **SmartGC.** Run `bash $V kbuild <run-id> smartgc smartgc-src NVMEVIRT_GC_POLICY=SMARTGC`. It prints `PASS ... exit=0`, and `grep -c '^module parm=smartgc_' result/<run-id>/kbuild-smartgc.log` prints `10`.
- **SmartGC, Q at 2000.** Run `bash $V kbuild <run-id> smartgcq smartgc-src NVMEVIRT_GC_POLICY=SMARTGC SMARTGC_Q_INIT=2000`. It prints `PASS`.
- **Greedy and fixed CAT.** Run `bash $V kbuild <run-id> sg-greedy smartgc-src NVMEVIRT_GC_POLICY=GREEDY` and `bash $V kbuild <run-id> sg-arm47 smartgc-src NVMEVIRT_GC_POLICY=CAT_FIG7 FIXED_ARM=47`. Both print `PASS`, and neither log has a `parm=smartgc_` line.
- **Warnings.** Read the warning list the command prints. Off the experiment computer exactly two are expected: `the compiler differs from the one used to build the kernel` and `pahole version differs from the one used to build the kernel`. Any warning that names a file of the source copy is a finding.
- **Proof.** The `kbuild-<tag>.log` files with `exit=0`, the module SHA256, and the `parm=` list.

## Gotchas

- The compile happens in a temporary copy, so the source tree stays clean and the module is not kept. To get loadable modules, run `script/build-all-modules.sh` on the experiment computer.
- The module SHA256 differs between hosts and build paths. Compare it only with builds from the same host.
- A compile against headers proves that the code builds, nothing more. Loading and running are covered by the kernel run.
- `script/build-all-modules.sh` truncates its manifest and overwrites `buildoutput/nvmev-<tag>.ko`. Record the new manifest in the experiment log when modules are rebuilt.
