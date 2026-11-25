#!/usr/bin/env python3
"""M6 adaptation metrics from existing mixFYF logs (read-only), GoCom 2026-11-25. Independent re-implementation (no code reuse from
recovery.py / e1_revd.py / r_suite_20261125.py) of the pre-registered definitions (revD preregistration section 3, recovery.py docstring):
  switch time      phase B START and phase C START (kernel marker; same clock as learner events)
  detection        first 'WATGC_V2 reset' after the switch (earliest partition), s after the switch
  restored arms    active in the first sample after a reset minus active in the last sample before it (sum over resets in the phase)
  eliminations     sum over windows of drops in 'active' between consecutive samples of a partition, within the phase
  first settle     first 'WATGC_V2 settled' after phase A START, latest partition (s)
  resettle         per partition, first 'settled' after its first reset in the phase; latest partition (s after the switch)
  recovery         one-sided, pre-registered and NOT changed: 30 s control samples, 5 min (10-sample) rolling WAF, reference = the run's own
                   WAF over the second half of the phase; recovered at the end of the first rolling window <= 1.05 x reference that stays
                   <= 1.05 x reference for the next 20 windows (10 min); time = that window end - phase start
  exploration cost windows whose evaluated arm != logged best: count and host-page share, per phase
    python3 -I analysis/final_revision/m6_adapt.py GROUP=HOST:BATCH:GLOB [...]   -> result/final-revision-analysis/adaptation_metrics.csv"""
import csv, re, sys
from datetime import datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'analysis/final_e1'))
import validity as V
OUT = ROOT / 'result/revE-20261125-analysis'; OUT.mkdir(parents=True, exist_ok=True)
TS = re.compile(r'^\[\s*([\d.]+)\]')
iso = lambda s: datetime.fromisoformat(s.strip()).timestamp()


def recovery(d, ph):
    s = [tuple(int(x) for x in m.groups()) for l in (d / 'control-series.txt').read_text().splitlines()
         for m in [re.match(r'(\d+) .*host_pages=(\d+) gc_pages=(\d+)', l)] if m]
    t0, t1 = iso((d / f'phase-{ph}-start.time').read_text()), iso((d / f'phase-{ph}-end.time').read_text())
    pts = [x for x in s if t0 <= x[0] <= t1]
    if len(pts) < 32: return None, None
    wf = lambda a, b: 1 + (b[2] - a[2]) / max(b[1] - a[1], 1)
    half = [x for x in pts if x[0] >= (t0 + t1) / 2]; ref = wf(half[0], half[-1])
    roll = [(pts[i][0], wf(pts[i - 10], pts[i])) for i in range(10, len(pts))]
    return next((roll[i][0] - t0 for i in range(len(roll)) if i + 20 < len(roll) and all(v <= ref * 1.05 for _, v in roll[i:i + 21])), 'none'), ref


rows = []
for a in sys.argv[1:]:
    name, spec = a.split('=', 1); host, batch, glob = spec.split(':', 2)
    for d in sorted(p for p in (Path('/').glob(glob.lstrip('/')) if glob.startswith('/') else ROOT.glob(glob)) if p.is_dir()):
        rep = int(re.search(r'rep(\d)', d.name)[1])
        ok = (d / 'exit-code.txt').exists() and (d / 'exit-code.txt').read_text().strip() == '0' and V.run_ok(d)
        lines = set()
        for f in [d / 'kernel.log', d / 'kernel-final.log', *sorted((d / 'kernel-snapshots').glob('*.log'))]:
            if f.exists(): lines.update(f.read_text(errors='replace').splitlines())
        L = sorted((float(m[1]), l) for l in lines if (m := TS.match(l)))
        beg = [t for t, l in L if re.search(r'mix-mixFYF-\S+ BEGIN', l)]
        if beg: L = [(t, l) for t, l in L if t >= max(beg)]
        mark = {m[1]: t for t, l in L for m in [re.search(r'phase=(\w) START', l)] if m}
        r = dict(group=name, host=host, batch=batch, rep=rep, valid=ok, dir=str(d))
        if not all(p in mark for p in 'ABC'):
            r['note'] = 'no phase markers'; rows.append(r); continue
        end = L[-1][0]
        samp = [(t, int(m[1]), int(m[2]), int(m[3]), int(m[4]), int(a[1]) if a else None) for t, l in L
                for m in [re.search(r'WATGC_V2 sample ns=\d+ part=(\d) .*?evaluated=(\d+) .*?host=(\d+) .*?best=(\d+)', l)] if m
                for a in [re.search(r' active=(\d+)', l)]]
        resets = [(t, int(m[1])) for t, l in L for m in [re.search(r'WATGC_V2 (?:reset|shift-reset) .*?part=(\d)', l)] if m]
        settles = [(t, int(m[1])) for t, l in L for m in [re.search(r'WATGC_V2 settled .*?part=(\d)', l)] if m]
        r['learner_log'] = bool(samp)
        st_A = [t for t, p in settles if t >= mark['A']]
        firsts = {}
        for t, p in settles:
            if t >= mark['A'] and p not in firsts: firsts[p] = t
        r['first_settle_s_latest_part'] = round(max(firsts.values()) - mark['A'], 1) if len(firsts) == 4 else ('partial' if firsts else 'none')
        for ph, nxt in (('B', 'C'), ('C', None)):
            t0, t1 = mark[ph], mark[nxt] if nxt else end
            rs = [(t, p) for t, p in resets if t0 <= t < t1]
            r[f'{ph}_resets'] = len(rs); r[f'{ph}_parts_reset'] = len({p for _, p in rs})
            r[f'{ph}_detect_s'] = round(min(t for t, _ in rs) - t0, 1) if rs else 'none'
            restored = 0
            for t, p in rs:
                pre = [x for x in samp if x[1] == p and x[0] < t and x[5] is not None]; post = [x for x in samp if x[1] == p and x[0] > t and x[5] is not None]
                if pre and post: restored += post[0][5] - pre[-1][5]
            r[f'{ph}_restored_arms'] = restored if rs else 0
            el = 0
            for p in range(4):
                ss = [x for x in samp if x[1] == p and t0 <= x[0] < t1 and x[5] is not None]
                el += sum(max(0, ss[i - 1][5] - ss[i][5]) for i in range(1, len(ss)))
            r[f'{ph}_elim_drops'] = el
            res, res_from_reset, exw = [], [], 0
            for p in range(4):
                rp = [t for t, q in rs if q == p]
                if rp:
                    s2 = [t for t, q in settles if q == p and t > rp[0] and t < t1]
                    res.append(s2[0] - t0 if s2 else None); res_from_reset.append(s2[0] - rp[0] if s2 else None)
                    exw += sum(1 for x in samp if x[1] == p and rp[0] < x[0] <= (s2[0] if s2 else t1))   # metric 5: windows reset -> settled
            r[f'{ph}_resettle_s_latest'] = ('none' if not rs else 'not all' if None in res else round(max(res), 1))            # from the switch
            r[f'{ph}_resettle_from_reset_s_max'] = ('none' if not rs else round(max(x for x in res_from_reset if x is not None), 1) if any(x is not None for x in res_from_reset) else 'not settled')
            r[f'{ph}_parts_resettled'] = sum(x is not None for x in res)
            r[f'{ph}_reexplore_windows_sum'] = exw if rs else 0
            win = [x for x in samp if t0 <= x[0] < t1]; hh = sum(x[3] for x in win)
            r[f'{ph}_windows'] = len(win); r[f'{ph}_explore_windows'] = sum(x[2] != x[4] for x in win)
            r[f'{ph}_explore_host_share'] = round(sum(x[3] for x in win if x[2] != x[4]) / hh, 4) if hh else ''
            rec, ref = recovery(d, ph); r[f'{ph}_recovery_s'] = rec; r[f'{ph}_ref_waf'] = round(ref, 4) if ref else ''
        rows.append(r)
with open(OUT / 'adaptation_revE.csv', 'w', newline='') as f:
    x = csv.DictWriter(f, list(dict.fromkeys(k for r in rows for k in r))); x.writeheader(); x.writerows(rows)
for r in rows:
    print(r['group'], r['rep'], r['valid'], 'settle', r.get('first_settle_s_latest_part'), '| C det', r.get('C_detect_s'), 'resets', r.get('C_resets'), 'restored', r.get('C_restored_arms'),
          'elim', r.get('C_elim_drops'), 'resettle', r.get('C_resettle_s_latest'), r.get('C_resettle_from_reset_s_max'), 'rexw', r.get('C_reexplore_windows_sum'), 'rec', r.get('C_recovery_s'), 'expl', r.get('C_explore_host_share'))
