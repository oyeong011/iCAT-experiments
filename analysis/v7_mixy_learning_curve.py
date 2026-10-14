import re, sys, glob, datetime as dt
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
R = '/home/oy/iCAT/result/v7-20261011/mixY/mixY-onlinev7-rep1'
OUT = sys.argv[1]
seq = open('/home/oy/iCAT/result/gc-20261010/mixy-seq.txt').read().split()
ts = lambda f: dt.datetime.fromisoformat(open(f).read().strip()).timestamp()
t0 = ts(f'{R}/phase-S01-start.time')
bounds = [(ts(f'{R}/phase-S{i:02d}-start.time')-t0, ts(f'{R}/phase-S{i:02d}-end.time')-t0) for i in range(1, 21)]
rx = re.compile(r'\[\s*([\d.]+)\] NVMeVirt: WATGC_V2 sample .*?part=(\d) .*?evaluated=(\d+) .*?waf_q16=(\d+) best=(\d+)')
d = {p: [] for p in range(4)}; k0 = None
for line in open(f'{R}/kernel.log'):
    m = rx.search(line)
    if not m: continue
    k, p, ev, w, b = float(m[1]), int(m[2]), int(m[3]), int(m[4]) / 65536, int(m[5])
    k0 = k if k0 is None else k0
    d[p].append(((k - k0) / 3600, ev, w, b))
col = {'F': '#e8eef8', 'S': '#f8efe2', 'V': '#e6f3ea'}
fig, ax = plt.subplots(2, 1, figsize=(13, 7), sharex=True)
for a in ax:
    for (s, e), w in zip(bounds, seq): a.axvspan(s/3600, e/3600, color=col[w], lw=0)
for (s, e), w in zip(bounds, seq): ax[0].text((s+e)/7200, 61, w, ha='center', fontsize=9)
cs = ['#2a6fdb', '#d9822b', '#2e9e5b', '#9b59b6']
for p in range(4):
    x = [r[0] for r in d[p]]
    ax[0].scatter(x, [r[1] for r in d[p]], s=1, color=cs[p], alpha=.25)
    ax[0].plot(x, [r[3] for r in d[p]], color=cs[p], lw=1.2, label=f'part{p} best')
    # 1-min rolling median of window WAF
    ws = [r[2] for r in d[p]]; n = 60
    sm = [sorted(ws[max(0, i-n):i+1])[len(ws[max(0, i-n):i+1])//2] for i in range(len(ws))]
    ax[1].plot(x, sm, color=cs[p], lw=.8, label=f'part{p}')
ax[0].axhline(47, ls='--', color='k', lw=.8); ax[0].text(0.1, 48, 'CAT-47 (best fixed)', fontsize=8)
ax[0].set_ylabel('CAT value\n(dots = tried, line = current best)'); ax[0].set_ylim(0, 64)
ax[0].legend(loc='lower right', fontsize=8, ncol=4, markerscale=1)
ax[1].set_ylabel('window WAF (rolling median)'); ax[1].set_xlabel('hours'); ax[1].set_ylim(1, 8)
ax[1].legend(loc='upper right', fontsize=8, ncol=4)
fig.suptitle('iCAT-v7 learning curve, mixY (F=FIO-Fast  S=FIO-Slow  V=Varmail, 30 min each)')
fig.tight_layout(); fig.savefig(OUT, dpi=110)
for p in range(4): print(p, len(d[p]), d[p][-1])
