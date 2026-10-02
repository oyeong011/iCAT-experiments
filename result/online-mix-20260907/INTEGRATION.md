# Isolated online source integration

Source: `/tmp/icat-review-2KewI6/repo/nvmevirt_test`, GitHub revision
7236149a01efad760aed084acf5b270f5a0408f6. Copied to
`/home/oy/iCAT/online-mix-src`; original experiment source is not edited.

## Behavior

- Kbuild defaults to WATGC_V2 and explicitly compiles policy 2. GREEDY is 0;
  CAT_FIG7 is the upstream fixed (7,100,7) reference, policy 1. Unsupported
  fixed-reference values fail rather than silently selecting a different setting.
- `measurement_manual=1 measurement_uid=1000` exposes root-group, owner-only
  `/proc/nvmevirt_measurement` (0600). Preparation writes do not update measured
  counters or the tuner. GC still runs using the upstream initial arm37.
- `start` resets ONLY measured counters and tuner cold-start state. Lifetime
  counters, mappings, last-invalidation Age, write pointers and SSD state remain.
- Each tuner enters WARMUP with an anchor at its current lifetime GC count;
  therefore 100 NEW GC cycles per partition are required after start. The normal
  upstream burn-in and measurement windows follow. All writes since start count
  in the externally measured WAF, including learner warmup and exploration.
- Do not issue a second start at the workload phase switch: it would erase the
  learning history. A whole A-to-B run has one start and one stop.
- `stop` freezes measured counters and learning. Subsequent filesystem cleanup
  can change lifetime counters/data but cannot change the stopped result.
- Original lifetime counters, last-invalidation Age semantics and all learner
  action-space, discount, exploration and drift parameters are retained.
- Without manual mode, the upstream first-100-GC accounting behavior remains;
  the initial warmup anchor is zero, preserving original learning behavior.

## Synchronization and validation boundaries

Control callbacks and the complete synchronous FTL I/O command handler share a
mutex only in manual mode. The serialized dispatcher is a sleeping kernel
thread. No early return bypasses unlock. Proc removal happens before FTL memory
is freed. Registration occurs after device initialization's failure branches.
Proc reads use a bounded buffer; use stopped snapshots for final values because
separate short reads during live I/O are not a transactional snapshot.

The integration task builds and statically inspects code but does not load a
module or execute device writes. Runner must validate preparation exclusion,
host-byte versus block-sector accounting, partition sums, actual arm/window
advancement and stopped-counter invariance before long experiments. Accounting
is at FTL command boundaries, not independent NAND hardware instrumentation.

Initial online build succeeded with an added stack-frame warning from a 2048-byte
proc buffer. This was reduced to 768 bytes before fixed-reference and final online
builds. Build logs preserve that initial warning. Four configured partitions fit
the buffer for this experiment; this reporting interface is not a general
unbounded-partition telemetry format.
