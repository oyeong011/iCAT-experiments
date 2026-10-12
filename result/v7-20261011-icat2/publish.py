"""Publish this campaign only, after CAT60's publisher exits."""
from pathlib import Path
import subprocess,shutil,hashlib,json,fcntl
P=Path(__file__).resolve().parent;R=P.parents[1];W=Path('/home/oy/iCAT-publish-icat2')
def run(*a,**kw):return subprocess.run(list(a),cwd=W,check=True,**kw)
def output(*a):return subprocess.check_output(list(a),cwd=W,text=True).strip()
def main():
    lock=(W.parent/'.icat-publish.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX)
    assert output('git','branch','--show-current')=='icat-2'
    assert not output('git','diff','--name-only','--diff-filter=U'),'unresolved merge'
    assert not output('git','diff','--cached','--name-only'),'unrelated staged work'
    rel=P.relative_to(R);dest=W/rel
    shutil.copytree(P,dest,dirs_exist_ok=True,ignore=shutil.ignore_patterns('*.lock','__pycache__'))
    for f in list(dest.rglob('*')):
        if not f.is_file() or f.stat().st_size<=90*1024**2:continue
        size=f.stat().st_size;pieces=[];digest=hashlib.sha256()
        with f.open('rb') as stream:
            i=0
            while True:
                data=stream.read(64*1024**2)
                if not data:break
                part=Path(str(f)+f'.part{i:04d}');part.write_bytes(data);digest.update(data);pieces.append(part.name);i+=1
        Path(str(f)+'.parts.json').write_text(json.dumps(dict(original_bytes=size,sha256=digest.hexdigest(),parts=pieces,reassemble='concatenate parts in listed order'),indent=2)+'\n')
        f.unlink()  # Only publishing copy; local raw untouched.
    run('git','add','--sparse','-f','--',str(rel))
    if subprocess.run(['git','diff','--cached','--quiet'],cwd=W).returncode:
        run('git','-c','user.name=Codex (icat-2)','-c','user.email=icat-2@localhost','commit','-q','-m','icat-2: v7 FVO90 and mixY evidence after CAT60')
    run('git','push','origin','HEAD:refs/heads/icat-2',timeout=1200)
    print('PUBLISHED',output('git','rev-parse','HEAD'))
if __name__=='__main__':main()
