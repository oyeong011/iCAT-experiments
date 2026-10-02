# one run's learner log: all dmesg snapshots + final, deduped by kernel timestamp, only lines after this run's BEGIN marker
import re,sys,glob
def lines(d):
    seen={}
    for f in sorted(glob.glob(d+'/kernel-snapshots/*.log'))+[d+'/kernel-final.log',d+'/kernel.log']:
        try:
            for l in open(f,errors='replace'):
                m=re.match(r'\[\s*(\d+\.\d+)\]',l)
                if m: seen.setdefault((m[1],l[15:60]),l.rstrip())
        except FileNotFoundError: pass
    L=[seen[k] for k in sorted(seen,key=lambda k:float(k[0]))]
    b=[i for i,l in enumerate(L) if ' BEGIN' in l and 'mix-' in l]
    return L[b[-1]:] if b else L
if __name__=='__main__':
    for d in sys.argv[1:]:
        t='\n'.join(lines(d)); out=[]
        for P in '0123':
            a=[(int(m[1]),int(m[2]),int(m[3])) for m in re.finditer(rf'part={P} epoch=\d+ window=(\d+) .*?settled=(\d) active=(\d+)',t)]
            if not a: continue
            w,_,mn=min(a,key=lambda x:(x[2],x[0])); out.append(f'p{P}: n={len(a)} first w{a[0][0]} min {mn}@w{w} end {a[-1][2]}')
        print(f'{d:28s}', ' | '.join(out), 'RESETx%d'%t.count('WATGC_V2 reset') if 'WATGC_V2 reset' in t else '')
