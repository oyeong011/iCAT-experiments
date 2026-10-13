#!/usr/bin/env python3
# v7 learning curve: 5-min WAF over time (v7 vs fixed) + arm v7 picks per partition.
# Usage: python3 analysis/v7-learning-curve.py [out.png]
import re, sys, glob, datetime as dt
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Noto Sans CJK JP"

R = "result"
RUNS = {  # panel -> [(label, run dir, color)]
    "90분 혼합 (F→V→O)": [("v7", f"{R}/v7-20261011/fvo90/mixY-onlinev7-rep1", "C3"),
                          ("arm47 (고정 1등)", f"{R}/cat60-90min-thispc-20261011/mixY-arm47-rep1", "C0"),
                          ("arm00 (고정 꼴찌)", f"{R}/cat60-90min-thispc-20261011/mixY-arm00-rep1", "0.6")],
    "mixY 20구간 (F/S/V 반복)": [("v7", f"{R}/v7-20261011/mixY/mixY-onlinev7-rep1", "C3"),
                               ("v6", f"{R}/gc-20261010/mixY-onlinev6-rep1", "C1"),
                               ("CAT-47 (고정)", f"{R}/gc-20261010/mixY-fixed47-rep1", "C0")],
}
WIN = 10  # control-series samples are 30 s apart -> 5-min windows

def t0(d):
    s = open(f"{d}/phase-S01-start.time").read().strip()
    return dt.datetime.fromisoformat(s).timestamp()

def waf_series(d):
    rows = []
    for line in open(f"{d}/control-series.txt"):
        f = dict(kv.split("=") for kv in line.split()[1:] if "=" in kv)
        if f.get("active") == "1":
            rows.append((int(line.split()[0]), int(f["host_pages"]), int(f["gc_pages"])))
    base = t0(d); xs, ys = [], []
    for (ta, ha, ga), (tb, hb, gb) in zip(rows, rows[WIN:]):
        if hb > ha:
            xs.append((tb - base) / 60); ys.append(1 + (gb - ga) / (hb - ha))
    return xs, ys

def phases(d):
    out = []
    for p in sorted(glob.glob(f"{d}/phase-S*-start.time")):
        out.append((dt.datetime.fromisoformat(open(p).read().strip()).timestamp() - t0(d)) / 60)
    return out

SAMPLE = re.compile(r"\[\s*([\d.]+)\] NVMeVirt: WATGC_V2 sample .*?part=(\d+) .*?best=(\d+)")
def picks(d):
    # snapshot N is taken with control-series line N; dmesg also holds older runs, so use only its last sample per part
    times = [int(l.split()[0]) for l in open(f"{d}/control-series.txt")]; base = t0(d); by = {}
    for f in sorted(glob.glob(f"{d}/kernel-snapshots/*.log")):
        i = int(f.rsplit("/", 1)[1][:-4])
        if i >= len(times): continue
        last = {int(m[2]): int(m[3]) for m in SAMPLE.finditer(open(f, errors="replace").read())}
        for p, b in last.items():
            by.setdefault(p, ([], [])); by[p][0].append((times[i] - base) / 60); by[p][1].append(b)
    return by

fig, ax = plt.subplots(2, 2, figsize=(16, 9), sharex="col", gridspec_kw={"height_ratios": [3, 2]})
for c, (title, runs) in enumerate(RUNS.items()):
    top, bot = ax[0][c], ax[1][c]
    for label, d, col in runs:
        x, y = waf_series(d)
        top.plot(x, y, color=col, lw=1.6 if label == "v7" else 1.1, label=label)
    for b in phases(runs[0][1])[1:]:
        top.axvline(b, color="0.85", lw=0.8, zorder=0); bot.axvline(b, color="0.85", lw=0.8, zorder=0)
    top.set_title(title); top.set_ylabel("WAF (최근 5분, 낮을수록 좋음)"); top.legend(loc="upper left")
    for p, (x, y) in sorted(picks(runs[0][1]).items()):
        bot.scatter(x, y, s=3, label=f"파티션 {p}", alpha=0.5)
    bot.axhline(47, color="C0", ls="--", lw=1, label="arm47")
    bot.set_ylabel("v7이 '최고'로 고른 arm"); bot.set_xlabel("시간 (분)"); bot.set_ylim(-2, 61)
    bot.legend(loc="lower right", markerscale=4, fontsize=8, ncol=5)
fig.suptitle("iCAT-v7 학습 곡선 — 회색 세로선 = 워크로드 바뀌는 지점")
fig.tight_layout()
out = sys.argv[1] if len(sys.argv) > 1 else "analysis/v7-learning-curve.png"
fig.savefig(out, dpi=110); print(out)
