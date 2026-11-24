#!/usr/bin/env python3
"""Per-run traceability manifest from EXISTING files only (no raw file is modified). GoCom, 2026-11-24.
    python3 -I analysis/revision_gocom/run_manifest.py <campaign dir> <source dir> [run ...]
Writes result/<campaign>-analysis/manifests/<run>.json in the report worktree. Every field records where it came from:
  'recorded' = written by the runner at run time; 'derived' = recomputed now from recorded files; 'reconstructed' = not recorded at
  run time, filled from current state (with the caveat stated)."""
import hashlib, json, re, sys, os, datetime as dt
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
camp = Path(sys.argv[1]); src = Path(sys.argv[2]); only = set(sys.argv[3:])
OUT = ROOT / f'result/{camp.name}-analysis/manifests'; OUT.mkdir(parents=True, exist_ok=True)


def tree_sha(d):
    h = hashlib.sha256()
    for f in sorted(p for p in d.rglob('*') if p.is_file() and (p.suffix in ('.c', '.h') or p.name in ('Kbuild', 'Makefile'))):
        h.update(str(f.relative_to(d)).encode() + b'\0' + f.read_bytes())
    return h.hexdigest()


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest() if Path(p).exists() else None


runner = next(iter(sorted(camp.glob('runner-*.sh'))), None)
insmod = sorted({m[0].strip() for m in re.finditer(r'insmod "\$module"[^\n]*', runner.read_text())}) if runner else []
regmods = {l.split()[1].split('/')[-1]: l.split()[0] for l in (camp / 'modules.sha256').read_text().splitlines()} if (camp / 'modules.sha256').exists() else {}
src_sha = tree_sha(src)
for d in sorted(camp.glob('raw/mixFYF-*')):
    if only and d.name not in only: continue
    e = (d / 'environment.txt').read_text(errors='replace').splitlines() if (d / 'environment.txt').exists() else []
    shas = {l.split()[1]: l.split()[0] for l in e if re.match(r'^[0-9a-f]{64}\s+/', l)}
    mod = next((p for p in shas if p.endswith('.ko')), None)
    m = re.match(r'mixFYF-(.+?)-rep(\d)(-smoke120)?$', d.name); pol, rep = m[1], int(m[2])
    g = lambda pat: next((l.split(':', 1)[1].strip() for l in e if re.match(pat, l)), None)
    thr, cores, sockets = g(r'^(코어 당 스레드|Thread\(s\) per core)'), g(r'^(소켓 당 코어 수|Core\(s\) per socket)'), g(r'^(소켓|Socket\(s\))\s*:')
    end = dt.datetime.fromtimestamp((d / 'exit-code.txt').stat().st_mtime).astimezone().isoformat(timespec='seconds') if (d / 'exit-code.txt').exists() else None
    man = {
        'run': d.name, 'policy': pol, 'rep': rep, 'raw_dir': {'value': str(d), 'source': 'recorded'},
        'host': {'value': (e[1].split()[1] if len(e) > 1 else None), 'source': 'recorded (environment.txt uname)'},
        'kernel': {'value': (e[1].split()[2] if len(e) > 1 else None), 'source': 'recorded'},
        'boot_cmdline': {'value': (e[2] if len(e) > 2 else None), 'source': 'recorded'},
        'cpu': {'model': g(r'^(모델 이름|Model name)'), 'sockets': sockets, 'cores_per_socket': cores, 'threads_per_core': thr,
                'logical_cpus': (int(sockets) * int(cores) * int(thr)) if sockets and cores and thr else None, 'source': 'recorded (lscpu)',
                'note': 'revA experiment_manifest.json cpu_cores=8 is wrong for this host (6 physical cores, 12 logical); original file left unchanged'},
        'memory': {'value': next((l for l in e if re.match(r'^(메모리|Mem):', l)), None), 'source': 'recorded (free -h)'},
        'module': {'path': mod, 'sha256': shas.get(mod), 'source': 'recorded',
                   'preregistered_sha256': regmods.get(Path(mod).name) if mod else None,
                   'matches_preregistered': (regmods.get(Path(mod).name) == shas.get(mod)) if mod else None},
        'runner': {'path': next((p for p in shas if p.endswith('.sh')), None), 'sha256': next((v for p, v in shas.items() if p.endswith('.sh')), None),
                   'sha256_now': sha(runner) if runner else None, 'source': 'recorded / derived'},
        'workload_files': {p: v for p, v in shas.items() if p.endswith('.fio') or 'workloada' in p},
        'nvmevirt_params': {'value': insmod, 'source': 'derived from runner whose sha256 is recorded above (static arguments)'},
        'seeds': {'fio_hot_warm_cold': [20260910 + rep, 20261010 + rep, 20261110 + rep], 'icat_seed': 2026111400 + rep,
                  'prepare': 20260907, 'source': 'derived from pre-registered formula; also printed in the journal line of the run'},
        'start': {'value': e[0] if e else None, 'source': 'recorded (environment.txt first line)'},
        'end': {'value': end, 'source': 'derived (mtime of exit-code.txt)'},
        'phase_times': {p: [(d / f'phase-{p}-start.time').read_text().strip() if (d / f'phase-{p}-start.time').exists() else None,
                            (d / f'phase-{p}-end.time').read_text().strip() if (d / f'phase-{p}-end.time').exists() else None] for p in 'ABC'},
        'source_tree': {'path': str(src), 'sha256_now': src_sha, 'source': 'reconstructed',
                        'caveat': 'source tree hash was not recorded at run time; this is the current tree. Link to the run is the module sha256 (and the objdump comparison in preregistration.md)'},
        'git': {'commit': os.popen('git -C /home/oy/iCAT rev-parse HEAD').read().strip(), 'dirty_files': len(os.popen('git -C /home/oy/iCAT status --short').read().splitlines()),
                'source': 'reconstructed (current state of the run tree /home/oy/iCAT; experiment sources are untracked local files there)'},
    }
    (OUT / f'{d.name}.json').write_text(json.dumps(man, ensure_ascii=False, indent=1))
    print(d.name, 'module ok' if man['module']['matches_preregistered'] else 'MODULE MISMATCH', man['cpu']['logical_cpus'], man['start']['value'], man['end']['value'])
