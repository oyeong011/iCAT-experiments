import re,sys,glob,collections
R=re.compile(r'WATGC_V2 sample ns=\d+ part=(\d) epoch=(\d+) window=(\d+) .*?evaluated=(\d+) .*?host=(\d+) gc_pages=(\d+) .*?waf_q16=(\d+) best=(\d+) next=(\d+)')
for d in sorted(glob.glob(sys.argv[1]+'/mixFYF-greedy-online-rep[0-9]')):
    s={}
    for f in ('kernel.log','kernel-final.log'):
        for m in R.finditer(open(f'{d}/{f}',errors='replace').read()):
            p,e,w,ev,h,g,q,b,n=map(int,m.groups()); s[(p,e,w)]=(ev,h,g,q,b,n)
    res=collections.Counter()
    for p in range(4):
        ws=sorted(k for k in s if k[0]==p)
        A=collections.defaultdict(list)
        for k in ws:
            ev,h,g,q,b,n=s[k]; A[ev].append((q,h,g))
            if len(A)<45: res['pre-cover']+=1; continue
            m1=min(A,key=lambda a:(sum(x[0] for x in A[a])/len(A[a]),a))
            m2=min(A,key=lambda a:(sum(x[2] for x in A[a])/sum(x[1] for x in A[a]),a))
            if n!=m1: print("MISMATCH",p,k,"next",n,"argmin",m1,"means",[(a,round(sum(x[0] for x in A[a])/len(A[a]),1),len(A[a])) for a in (n,m1)])
            res["n"]+=1; res['eq_meanq']+= n==m1; res['eq_ratio']+= n==m2; res['eq_best']+= n==b
    print(d.split('/')[-1],dict(res), 'epochs',sorted({k[1] for k in s}))
