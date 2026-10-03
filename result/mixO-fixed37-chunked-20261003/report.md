
### mixO-fixed37-chunked-20261003 preregistration
Command: env MULT=20 VM_RUN=900 VM_CHUNKS=20 bash script/mix-20260911.sh mixO fixed37 1
Expected 10h plus preparation/process overhead. Only virtual nvme1n1, global lock; previous failed37 preserved, blocked50/v4 remain stopped. OLTP restart preserves reuse filesets, module and measurement counters; no resets between chunks. 30s samples. Validate exit0, twenty OLTP IO Summary durations900, Varmail18000, preparation fio error0/requested bytes, zero-start/stop counters and blockstat assertion. Environment/module/source metadata adjacent; module build provenance unchanged from earlier current-kernel build, exact upstream build equivalence unconfirmed. Publish complete/failed evidence to icat-2.
