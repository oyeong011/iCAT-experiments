# Online mix pre-run review

2026-09-07. Two bounded native agents implemented isolated source and independently reviewed kernel/runner changes; primary agent integrated runner corrections. This is not runtime acceptance.

- Source builds online policy 2 and fixed reference policy 1. Final module hash: a34e2a86907675230fbc4b80e4ed1e49f7f5713384b569357800930f754d9479.
- Independent review: no unresolved blocker to measurement validation then smoke; main remains gated on both passing.
- Kernel: common FTL/control mutex; cold learner start preserves mapping/Age/lifetime; new-GC warmup baseline; stopped learning/counters frozen; proc removed before namespace free.
- Runner fixes: existing-batch lock, exact-device refusal guards, cleanup error propagation, persistent kernel snapshots, dedup that does not inject historical samples, sample WAF recomputation and action changes per partition, host-byte/block-stat equality and payload guard.
- Shell syntax and fio parse-only passed before loading. Source and runner hashes in run-inputs.sha256.
- Active telemetry snapshots are not transactional across small reads. Official whole-run totals use stopped snapshots. GC counts are internal FTL instrumentation, not independent NAND program measurement.
- The request is an online-only pilot, not proof of superiority against static CAT or Q-learning. Existing standalone CAT batch is preserved and must release device before this pilot.
