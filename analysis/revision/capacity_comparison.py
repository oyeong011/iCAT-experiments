#!/usr/bin/env python3
"""11-27 capacity / host configuration table for the requested 8 GB vs 16 GB comparison (extraction only, no new runs).
    python3 -I -B analysis/revision/capacity_comparison.py
Finding: every revision mixFYF run on BOTH hosts used the same 8 GiB NVMeVirt (memmap=8G$4G, memmap_size=8192M,
4 FTL x 2 GiB NAND, 15,677,727 sectors). The hosts differ in RAM / CPU, not in SSD capacity.
WAF rows come from result/final-validation-20261127 (recomputed from raw logs). Batches are never pooled."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V = ROOT / 'result/final-validation-20261127'
OUT = ROOT / 'result/capacity-comparison-20261127'
OUT.mkdir(exist_ok=True)
RAW = [r for r in csv.DictReader(open(V / 'final_raw_data_validation.csv')) if r['role'] == 'main' and r['workload'] == 'mixFYF']
D = {(r['batch'], r['policy']): r for r in csv.DictReader(open(V / 'final_statistical_validation.csv')) if r['kind'] == 'descriptive' and r['metric'] == 'total_waf'}

# Host / device configuration (sources: environment.txt (free -h, lscpu, /proc/cmdline), kernel.log NVMeVirt init lines,
# device.txt (sectors), runner insmod line, revD-src/ssd_config.h SAMSUNG_970PRO block). Identical on both hosts except where noted.
HOSTCFG = {
    '고컴': {'host_cpu': 'AMD Ryzen 5 3600XT 6-Core', 'host_ram_os_visible': '23 GiB (free -h, memmap 8 GiB 제외)',
            'host_ram_physical': '약 32 GB 추정 (OS 가시 23 GiB + 예약 8 GiB; dmidecode 미확인)'},
    '승컴': {'host_cpu': 'Intel Core i7-7700', 'host_ram_os_visible': '7.6 GiB (free -h, memmap 8 GiB 제외)',
            'host_ram_physical': '16 GB 추정 (lsmem online 8 GiB + 예약 8 GiB; dmidecode 미확인)'},
}
COMMON = {
    'kernel': '7.0.0-31-generic (양쪽 같음)', 'kernel_cmdline_memmap': 'memmap=8G$4G (양쪽 같음; cmdline 차이는 root UUID뿐)',
    'nvmevirt_alloc': 'insmod memmap_start=4G memmap_size=8192M cpus=1,2 (Storage 8191 MiB)',
    'ssd_physical_nand': '8 GiB = 4 FTL 파티션 × 2 GiB (chs=2 luns=4 lines=8192 per 파티션, blk 64 KiB, line 256 KiB, 4 KiB page 524,288개/파티션)',
    'ssd_logical': '15,677,727 sectors × 512 B = 7,655 MiB (7.48 GiB)',
    'over_provisioning': 'OP_AREA_PERCENT 0.07 (ssd_config.h SAMSUNG_970PRO); (8,192 − 7,655) / 7,655 = 7.0 %',
    'workload': 'mixFYF: FIO-Fast test4 1800 s → YCSB-A SQLite 250k load+run 1800 s → FIO-Fast 1800 s; Table-3 prep randseed 20260907',
    'workload_files': 'mix-test4.fio sha b5edbcc7…, sqlite workloada sha c0aff8a2… (양쪽 같음)',
}
# requested policy -> (label in data, [(batch, policy)])
POL = [
    ('iCAT-v4', [('revA-20261114', 'revA-v4'), ('revB-20261122', 'revB-v4'), ('revC-20261124', 'revC-v4'), ('revE-20261125', 'revE-v4'),
                 ('revD-20261124', 'revD-v4'), ('revision-additional-ablation', 'abl-v4'), ('batchG-20261126', 'bg-v4')]),
    ('Random Selection', [('revA-20261114', 'revA-random')]),
    ('Greedy GC', [('greedygc-20261126', 'greedygc')]),
    ('CAT-Best (arm 47) — 요청 목록 외, 양쪽 공통이라 참고로 포함', [('revA-20261114', 'arm47'), ('arm47-20261127', 'arm47')]),
]
rows = []
for label, keys in POL:
    for b, p in keys:
        runs = sorted((r for r in RAW if r['batch'] == b and r['policy'] == p), key=lambda r: r['rep'])
        if not runs: continue
        h = runs[0]['host']; d = D[(b, p)]
        rows.append({'policy': label, 'host': h, 'batch': b, 'policy_id': p, 'ssd_capacity_actual': '8 GiB (양쪽 같음)',
                     **HOSTCFG[h], **COMMON, 'n': len(runs), 'waf_reps': ' / '.join(f"{float(r['total_waf']):.4f}" for r in runs),
                     'mean_waf': f"{float(d['mean']):.4f}", 'sd_waf': f"{float(d['sd']):.4f}" if d['sd'] else 'n<3: 없음',
                     'ci95': f"[{float(d['ci95_lo']):.4f}, {float(d['ci95_hi']):.4f}]" if d['ci95_lo'] else 'n<3: 없음',
                     'all_valid': all(r['valid'] == 'True' for r in runs),
                     'raw_paths': ' ; '.join(r['raw_path'] for r in runs),
                     'module_sha256': ' ; '.join(sorted({r['module_sha256'][:16] for r in runs})),
                     'source_commit': runs[0]['source_commit']})
for label, why in (('Basic', '논문의 어느 정책인지 확정할 근거가 없고, 리비전 mixFYF에서 확인된 실행이 없음. 수치를 만들지 않음'),
                   ('Robust (CAT-Robust, arm 50)', '리비전 mixFYF에서 양쪽 모두 실행하지 않음. 수치를 만들지 않음')):
    rows.append({'policy': label, 'host': '양쪽', 'n': 0, 'waf_reps': '미실행', 'mean_waf': '미실행', 'note': why})
for r in rows:
    r.setdefault('note', '')
    if r['host'] != '양쪽':
        r['note'] = ('같은 호스트의 다른 배치와 합치지 않음' if r['policy'] == 'iCAT-v4' else
                     '이 호스트에서만 실행 (다른 호스트 짝 없음)' if r['policy'] in ('Random Selection', 'Greedy GC') else 'n=1 (고컴) vs n=3 (승컴)')
keys = list(dict.fromkeys(k for r in rows for k in r))
with open(OUT / 'capacity_comparison.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, keys, lineterminator='\n'); w.writeheader(); w.writerows(rows)
for r in rows: print(r['policy'][:16], r['host'], r.get('batch', ''), r['n'], r['mean_waf'], r.get('sd_waf', ''))
