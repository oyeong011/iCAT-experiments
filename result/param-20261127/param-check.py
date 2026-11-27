#!/usr/bin/env python3
"""param-20261127: the 4 measurement-start WATGC_V2 init lines must carry the registered gamma_q16 / exploration_q16 / VARIANT 4 / 45 candidates.
usage: param-check.py <run dir>   (exit 1 on mismatch -> queue stops)"""
import re, sys
from pathlib import Path
d = Path(sys.argv[1])
EXP = {'pf-g99': (64881, 16384), 'pf-g95': (62259, 16384), 'pf-g90': (58982, 16384), 'pf-c050': (65503, 32768), 'pf-c075': (65503, 49152)}
pol = re.match(r'mixFYF-(pf-\w+?)-rep', d.name)[1]
init = [dict(re.findall(r'(\w+)=(\d+)', l)) for l in (d / 'kernel.log').read_text(errors='replace').splitlines() if 'WATGC_V2 init' in l][-4:]
ok = len(init) == 4 and sorted(i['part'] for i in init) == list('0123') and all(
    (int(i['gamma_q16']), int(i['exploration_q16']), int(i['revA_variant']), int(i['candidates'])) == (*EXP[pol], 4, 45) for i in init)
print(f"{d.name} param-check {'OK' if ok else 'FAIL'} expected gamma_q16={EXP[pol][0]} exploration_q16={EXP[pol][1]} got " +
      ' '.join(f"p{i['part']}:{i['gamma_q16']}/{i['exploration_q16']}/v{i['revA_variant']}" for i in init))
sys.exit(0 if ok else 1)
