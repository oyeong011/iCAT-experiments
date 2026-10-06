if __name__ != '__main__':
 raise ImportError('Explicit publisher only')
from pathlib import Path
import subprocess,shutil,hashlib,json
P=Path(__file__).resolve().parent;ROOT=P.parents[1];W=Path('/home/oy/iCAT-publish-icat2')
assert subprocess.check_output(['git','branch','--show-current'],cwd=W,text=True).strip()=='icat-2'
assert not subprocess.check_output(['git','diff','--name-only','--diff-filter=U'],cwd=W,text=True).strip(),'Unresolved merge'
paths=[]
for source in [P]:
 rel=source.relative_to(ROOT);dest=W/rel
 # Preserve raw large files in byte-exact chunks if the individual GitHub cap is exceeded.
 shutil.copytree(source,dest,dirs_exist_ok=True,ignore=shutil.ignore_patterns('*.lock','__pycache__'))
 for f in list(dest.rglob('*')):
  if f.is_file() and f.stat().st_size>90*1024**2:
   pieces=[];digest=hashlib.sha256()
   with f.open('rb') as stream:
    i=0
    while True:
     data=stream.read(64*1024**2)
     if not data:break
     part=Path(str(f)+f'.part{i:04d}');part.write_bytes(data);digest.update(data);pieces.append(part.name);i+=1
   Path(str(f)+'.parts.json').write_text(json.dumps({'original_bytes':f.stat().st_size,'sha256':digest.hexdigest(),'parts':pieces,'reassemble':'concatenate parts in listed order'},indent=2)+'\n')
   f.unlink() # publication copy only; original raw data always retained
 paths.append(str(rel))
subprocess.run(['git','add','--sparse','-f','--']+paths,cwd=W,check=True)
if subprocess.run(['git','diff','--cached','--quiet'],cwd=W).returncode:
 subprocess.run(['git','-c','user.name=Codex (icat-2)','-c','user.email=icat-2@localhost','commit','-m','icat-2: mixV inheritance CAT37 CAT50 evidence'],cwd=W,check=True)
subprocess.run(['git','push','origin','HEAD:refs/heads/icat-2'],cwd=W,check=True)
