# Fixed-arm comparison modules

Isolated copy: `/home/oy/iCAT/varmail-compare-src`, copied from the tested
`online-mix-src`; the latter and existing online module remain unchanged.

Build with `NVMEVIRT_GC_POLICY=CAT_FIG7 FIXED_ARM=<0..59>`. Header rejects
out-of-range values. Old explicit K/scale/ratio overrides are not supported.

Decode is the unchanged online formula:
`arm = k_index * 15 + scale_index * 3 + ratio_index`.
K grid [2,4,7,10], scale grid [25,50,100,200,400], ratio grid [4,7,16].
Thus arm37 = 2*15+2*3+1 = (7,100,7);
arm47 = 3*15+0*3+2 = (10,25,16).

Only the non-online initialization uses CONV_FIXED_ARM. It calls the exact
upstream online `watgc_v2_set_arm`, so threshold rounding, Age levels,
last-invalidation Age, victim comparator and tie breaking are shared.
The fixed branch's on-GC callback is a no-op: no learning or arm changes.
Manual start resets to the selected fixed arm; no mapping/Age reset.
The online initialization still uses WATGC_V2_INITIAL_ARM and was not changed.

Additional startup logging prints decoded arm/K/scale/ratio so the runner can
assert actual loaded settings. Control proc arm fields provide runtime checks.

These builds are compile/static checks only. Device-level execution, fixed-arm
invariance, common workload and WAF accounting must be validated by the runner.
No devices were loaded or formatted by this integration task.
