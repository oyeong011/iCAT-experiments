#!/usr/bin/env python3
import re,collections,sys
from pathlib import Path
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import matplotlib.font_manager as fm, glob
ff=(glob.glob('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')+glob.glob('/usr/share/fonts/opentype/noto/NotoSansCJK*.ttc'))[0]
fm.fontManager.addfont(ff); matplotlib.rcParams['font.family']=fm.FontProperties(fname=ff).get_name(); matplotlib.rcParams['axes.unicode_minus']=False
def series(d):
    rows=[]; marks=[]
    for l in open(d/'kernel.log',errors='replace'):
        t=re.match(r'\[\s*([\d.]+)\]',l)
        if not t: continue
        t=float(t[1]); m=re.search(r'phase=(\w+) START',l)
        if m and 'WATGC' not in l: marks.append(t)
        if 'WATGC_V2 sample' not in l: continue
        v=dict(re.findall(r'(\w+)=(-?\w+)',l)); rows.append((t,int(v['host']),int(v['gc_pages']),int(v['evaluated'])))
    t0=rows[0][0]; B=600; bins=collections.defaultdict(list)
    for r in rows: bins[int((r[0]-t0)//B)].append(r)
    xs=sorted(bins); tm=[(b+.5)*10 for b in xs]
    waf=[(sum(r[1] for r in bins[b])+sum(r[2] for r in bins[b]))/sum(r[1] for r in bins[b]) for b in xs]
    narm=[len({r[3] for r in bins[b]}) for b in xs]
    return tm,waf,narm,[(m-t0)/60 for m in marks]
runs=[("빠른 3영역 쓰기 60분 → SQLite 60분", Path('result/mix-20260911/mixA-online-rep1-x6'), [(0,60,1.773,'앞 구간 최적 고정 CAT (arm47)'),(60,120,1.416,'뒤 구간 최선 고정 CAT (arm50)')]),
      ("느린 3영역 60분 → 빠른 3영역 60분", Path('result/mix-20260911/mixC-online-rep1-x6'), [(0,60,1.759,'앞 구간 최적 고정 CAT (arm47)'),(60,120,1.773,'뒤 구간 최적 고정 CAT (arm47)')])]
fig,ax=plt.subplots(2,2,figsize=(13,7.5))
for i,(title,d,opts) in enumerate(runs):
    tm,waf,narm,marks=series(d)
    a=ax[0][i]; a.plot(tm,waf,'o-',label='iCAT v1 (10분 평균)')
    for x0,x1,y,lab in opts: a.hlines(y,x0,x1,colors='tab:green',linestyles='--',label=lab)
    for m in marks[1:]: a.axvline(m,color='k',lw=.8,ls=':')
    a.set_title(title); a.set_ylabel('WAF (낮을수록 좋음)'); a.grid(alpha=.3); a.legend(fontsize=8)
    b=ax[1][i]; b.bar(tm,narm,width=8,color='tab:orange'); b.set_ylim(0,62); b.set_ylabel('10분 동안 시험한 설정 수 (60개 중)'); b.set_xlabel('분'); b.grid(alpha=.3)
    for m in marks[1:]: b.axvline(m,color='k',lw=.8,ls=':')
    b.text(1,56,'막대 높음 = 아직 고르는 중 / 낮음 = 정착',fontsize=8)
fig.suptitle('iCAT v1은 학습하는가?  초록 점선 = 그 구간에서 제일 좋은 고정 CAT. 파란 선이 거기에 얼마나 가까워지고, 유지되는가',fontsize=11)
fig.tight_layout(); out='result/mix-20260911/learning-v1-60min.png'; fig.savefig(out,dpi=110); print(out)
