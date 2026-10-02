# GitHub meendragon/iCAT 7236149 result/ 재계산: workload별 CAT arm WAF 최저/최고/편차. 사용: cd <clone>; python3 gh-sweep-waf.py [-v]
import re,sys,glob,statistics as st
from pathlib import Path
RUN=re.compile(r"GC stats: policy=(\S+) host_pages=(\d+) gc_pages=(\d+) gc_count=(\d+) WAF=([\d.]+|N/A)(?: k=(\d+) scale_pct=(\d+) age_ratio=(\d+))?")
sets={"test3":"result/test3_result/dmesg-*.log","test4":"result/test4_result/dmesg-*.log","test5":"result/test5_result/dmesg-*.log",
"varmail":"result/filebench/varmail/dmesg-*.log","oltp":"result/filebench/oltp/dmesg-*.log",
"sqlite-a":"result/sqlite/workloada/dmesg-*.log","sqlite-b":"result/sqlite/workloadb/dmesg-*.log","llama":"result/llama/dmesg-*.log"}
for wl,pat in sets.items():
    rows=[]
    for f in sorted(glob.glob(pat)):
        t=Path(f).read_text(errors="replace"); ms=RUN.findall(t)
        if not ms: print(f"# {wl} {Path(f).name}: no GC stats",file=sys.stderr); continue
        m=ms[-1]; h,g=int(m[1]),int(m[2]); waf=(h+g)/h if h else float('nan')
        arm=("greedy" if m[0]=="greedy" else f"k{int(m[5]):02d}-s{int(m[6]):03d}-r{int(m[7]):02d}")
        if len(ms)>1: print(f"# {wl} {Path(f).name}: {len(ms)} GC stats lines, using last",file=sys.stderr)
        rows.append((arm,waf,h,g))
    cat=[r for r in rows if r[0]!="greedy"]; gr=[r for r in rows if r[0]=="greedy"]
    if not cat: print(wl,"no cat rows"); continue
    best=min(cat,key=lambda r:r[1]); worst=max(cat,key=lambda r:r[1]); wafs=[r[1] for r in cat]
    print(f"{wl:9s} n={len(cat):2d} greedy={gr[0][1] if gr else float('nan'):.4f} best={best[0]} {best[1]:.4f} worst={worst[0]} {worst[1]:.4f} "
          f"range={worst[1]-best[1]:.4f} ({(worst[1]/best[1]-1)*100:.1f}%) mean={st.fmean(wafs):.4f} sd={st.pstdev([float(x) for x in wafs]):.4f}")
    if "-v" in sys.argv:
        for r in sorted(cat,key=lambda r:r[1]): print(f"   {r[0]} {r[1]:.4f} host={r[2]} gc={r[3]}")
