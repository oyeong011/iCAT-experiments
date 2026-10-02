import subprocess,shutil,re,sys
from pathlib import Path
ROOT=Path('/home/oy/iCAT');DEST=Path('/home/oy/iCAT-publish-icat2');P=Path(__file__).resolve().parent
if not DEST.exists():
 subprocess.run(['git','worktree','add','--no-checkout','-b','icat-2',str(DEST),'f299c51e806ad87f51761b14b379970da54440b9'],cwd=ROOT,check=True)
 subprocess.run(['git','sparse-checkout','set','--no-cone','/CODEX_HANDOFF.md','/EXPERIMENT_LOG.md','/.gitignore'],cwd=DEST,check=True)
assert subprocess.check_output(['git','branch','--show-current'],cwd=DEST,text=True).strip()=='icat-2'
selected=[P,ROOT/'result/handoff-f299c51e-20261002-r2']
handoff=selected[1]
validation_file=handoff/'validation-path.txt'
if validation_file.exists():
 v=ROOT/validation_file.read_text().strip()
 if v.is_dir():
  selected.append(v)
  for f in v.glob('*.console.txt'):
   for name in re.findall(r'^\[RESULT\]\s+(/\S+)',f.read_text(errors='replace'),re.M):
    raw=Path(name)
    if raw.is_file() and raw.is_relative_to(ROOT/'result'):selected.append(raw)
paths=[]
for src in selected:
 rel=src.relative_to(ROOT);dst=DEST/rel
 if src.is_dir():shutil.copytree(src,dst,dirs_exist_ok=True,ignore=shutil.ignore_patterns('*.lock','__pycache__'))
 else:dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 paths.append(str(rel))
subprocess.run(['git','add','--sparse','-f','--']+paths,cwd=DEST,check=True)
if subprocess.run(['git','diff','--cached','--quiet'],cwd=DEST).returncode:
 subprocess.run(['git','-c','user.name=Codex (icat-2)','-c','user.email=icat-2@localhost','commit','-m','icat-2: '+(sys.argv[1] if len(sys.argv)>1 else 'QUEUE33 evidence')],cwd=DEST,check=True,stdout=subprocess.DEVNULL)
subprocess.run(['git','push','origin','HEAD:refs/heads/icat-2'],cwd=DEST,check=True)
