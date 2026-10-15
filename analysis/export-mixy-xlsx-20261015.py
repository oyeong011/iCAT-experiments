#!/usr/bin/env python3
"""Export pinned mixY raw counters as editable Excel charts. Requires XlsxWriter.
Run from any checkout containing the pinned main and icat-2 commits; no experiments.
"""
from pathlib import Path
import subprocess,re,json,datetime,hashlib,argparse
import xlsxwriter
R=Path(__file__).resolve().parents[1]
MAIN='bd147817a1cea5cab814eb7b68b676c2a2008f6e'
SECOND='d424f548b548715a190c6b2c7fa105d904f9aca8'
OUT=R/'figs/data/mixY_v7_comparison_20261015.xlsx'
SEQ='F S V F V S F S V F V S F S V F V S F S'.split()
COLORS=['808080','D97706','CC5599','8A752B','154C9A']
SPECS=[('CAT-37 기본','result/gc-20261010/mixY-arm37-rep1'),('CAT-50 견고','result/gc-20261010/mixY-arm50-rep1'),('CAT-47','result/gc-20261010/mixY-fixed47-rep1'),('iCAT-v6','result/gc-20261010/mixY-onlinev6-rep1'),('iCAT-v7','result/v7-20261011/mixY/mixY-onlinev7-rep1')]
manifest=[]
def read(commit,path):
 b=subprocess.check_output(['git','-C',str(R),'show',commit+':'+path]);manifest.append(dict(commit=commit,path=path,sha256=hashlib.sha256(b).hexdigest()));return b.decode()
def counters(s):return {k:int(v) for k,v in re.findall(r'\b(epoch|active|host_bytes|host_pages|gc_pages)=(\d+)',s.splitlines()[0])}
def iso(s):return datetime.datetime.fromisoformat(s.strip()).timestamp()
def run(label,path,commit):
 get=lambda n:read(commit,path+'/'+n)
 assert get('exit-code.txt').strip()=='0'
 env=get('environment.txt');host=re.search(r'^Linux (\S+)',env,re.M)[1]
 stop=counters(get('stopped.txt'));assert stop==counters(get('final-control.txt')) and stop['active']==0
 summary=get('summary.txt');waf=1+stop['gc_pages']/stop['host_pages'];assert abs(float(re.search(r'WAF=([\d.]+)',summary)[1])-waf)<0.00000051
 phases=[]
 for i,w in enumerate(SEQ,1):
  slot=f'S{i:02}';a,b=counters(get(f'phase-{slot}-start.txt')),counters(get(f'phase-{slot}-end.txt'))
  st,en=iso(get(f'phase-{slot}-start.time')),iso(get(f'phase-{slot}-end.time'))
  assert en-st>=1798 and a['active']==b['active']==1
  h,g=b['host_pages']-a['host_pages'],b['gc_pages']-a['gc_pages'];assert h>0 and g>=0
  phases.append(dict(slot=slot,workload=w,start=st,end=en,host_pages=h,gc_pages=g,waf=1+g/h))
 assert len(re.findall(r'^phaseS\d+',summary,re.M))==20
 t0=phases[0]['start'];series=[]
 for line in get('control-series.txt').splitlines():
  c=counters(line);stamp=int(line.split()[0])
  if stamp>=t0 and c['host_pages']>0:series.append(dict(time=stamp,hours=(stamp-t0)/3600,**c,waf=1+c['gc_pages']/c['host_pages']))
 assert series
 # Match analysis/fig-v7.py: nearest 30-second counter sample to each 15-minute boundary.
 bins=[]
 for i in range(40):
  a=min(series,key=lambda x:abs(x['time']-(t0+i*900)));b=min(series,key=lambda x:abs(x['time']-(t0+(i+1)*900)))
  # The initial zero counter is an actual measurement boundary, not a fabricated row.
  if i==0:a=dict(time=t0,host_pages=0,gc_pages=0)
  h,g=b['host_pages']-a['host_pages'],b['gc_pages']-a['gc_pages'];assert h>0 and g>=0
  bins.append(dict(hours=(i+.5)/4,host_pages=h,gc_pages=g,waf=1+g/h,actual_start=a['time'],actual_end=b['time']))
 return dict(label=label,path=path,commit=commit,host=host,total=waf,stop=stop,phases=phases,series=series,bins=bins)
data=[run(label,path,MAIN) for label,path in SPECS]
local=run('iCAT-v7 이 PC','result/v7-20261011-icat2/mixY/mixY-onlinev7-rep1',SECOND)
assert len({d['host'] for d in data})==1 and local['host']!=data[0]['host']
OUT.parent.mkdir(parents=True,exist_ok=True);wb=xlsxwriter.Workbook(OUT)
wb.set_properties({'title':'mixY 10시간 — 고정 CAT와 iCAT-v7 비교','comments':'Source-backed editable charts; one run per policy, hosts separated.'})
header=wb.add_format({'bold':True,'bg_color':'E9EEF5','border':0,'text_wrap':True});num=wb.add_format({'num_format':'0.000000'});wrap=wb.add_format({'text_wrap':True,'valign':'top'});title=wb.add_format({'bold':True,'font_size':16,'font_color':'154C9A'})
def sheet(name,headers=None):
 s=wb.add_worksheet(name);s.freeze_panes(1,2);s.set_column(0,0,23);s.set_column(1,10,18);s.set_default_row(20)
 if headers:s.write_row(0,0,headers,header);s.autofilter(0,0,1,len(headers)-1)
 return s
def formula(s,r,c,f,value):s.write_formula(r,c,f,num,value)
def chart(name,xt,yt,scatter=False):
 c=wb.add_chart({'type':'scatter','subtype':'straight_with_markers'} if scatter else {'type':'line'})
 c.set_title({'name':name});c.set_x_axis({'name':xt,'major_gridlines':{'visible':False}});c.set_y_axis({'name':yt,'major_gridlines':{'visible':True,'line':{'color':'E4E7EB'}}});c.set_legend({'position':'bottom'});c.set_size({'width':1060,'height':480});c.set_chartarea({'border':{'none':True}});return c
info=sheet('안내');info.set_column(0,0,28);info.set_column(1,1,115)
notes=[('내용','mixY: FIO-Fast / FIO-Slow / Varmail, 각 30분 × 20구간. 표 3 준비, 6 GiB FIO 파일 유지.'),('순서',' '.join(SEQ)),('비교 호스트',data[0]['host']+'; 기본37 / 견고50 / CAT47 / v6 / v7'),('이 PC',local['host']+' 결과는 별도 시트. 동일 환경의 반복으로 합치지 않음.'),('WAF 정의','전체=1+누적 gc_pages/host_pages. 구간=1+구간 gc_pages 차분/host_pages 차분. 초기 학습 비용 포함.'),('15분 WAF','30초 시계열에서 15분 경계에 가장 가까운 관측 카운터를 선택해 차분. 첫 경계는 실제 start의 0 카운터. x축은 구간 중앙.'),('누적 WAF','측정 시작 이후 누적 카운터 비율. 30초 표본은 독립 반복이 아님.'),('검증 범위','원본 exit=0, 20개 경계 카운터/시간, stopped와 final-control 일치 및 summary 재계산 확인. 원래 PC의 독립 바이트 검사를 이번 내보내기에서 재수행한 것은 아님.'),('해석','정책별 1회. 통계적 우열 및 1% 오차 범위를 추정하지 않음. CAT47은 mixY 전체 60조합 중 최적으로 확정되지 않음.'),('편집','차트는 Excel 기본 차트이며 셀 데이터와 연결됨. PNG를 붙인 그래프가 아님.'),('원본 main',MAIN),('원본 icat-2',SECOND),('색상','기본37 회색 / 견고50 주황 / CAT47 분홍 / v6 황갈색 / v7 파랑')]
info.write(0,0,'mixY 실험 그래프',title)
for i,(k,v) in enumerate(notes,2):info.write(i,0,k,header);info.write(i,1,v,wrap);info.set_row(i,42)
s=sheet('전체 WAF',['정책','host_pages','gc_pages','전체 WAF','hostname','원본 경로'])
for r,d in enumerate(data,1):
 s.write_row(r,0,[d['label'],d['stop']['host_pages'],d['stop']['gc_pages']]);formula(s,r,3,f'=1+C{r+1}/B{r+1}',d['total']);s.write_row(r,4,[d['host'],d['path']])
c=wb.add_chart({'type':'column'});c.add_series({'name':'전체 WAF','categories':['전체 WAF',1,0,5,0],'values':['전체 WAF',1,3,5,3],'points':[{'fill':{'color':v},'border':{'none':True}} for v in COLORS],'data_labels':{'value':True,'num_format':'0.000'}});c.set_title({'name':'mixY 10시간 — 같은 호스트, 정책별 1회'});c.set_y_axis({'name':'전체 WAF (낮을수록 좋음)','min':0});c.set_legend({'none':True});c.set_size({'width':1060,'height':480});s.insert_chart('A10',c)
raw=sheet('구간 카운터',['정책','구간','워크로드','시작 epoch','종료 epoch','host_pages 차분','gc_pages 차분','구간 WAF'])
for k,d in enumerate(data):
 for i,p in enumerate(d['phases']):
  r=1+k*20+i;raw.write_row(r,0,[d['label'],p['slot'],p['workload'],p['start'],p['end'],p['host_pages'],p['gc_pages']]);formula(raw,r,7,f'=1+G{r+1}/F{r+1}',p['waf'])
s=sheet('30분 구간 WAF',['구간','워크로드']+[d['label'] for d in data]);c=chart('mixY — 30분 구간별 WAF','구간 / workload','구간 WAF')
for i,w in enumerate(SEQ,1):
 s.write_row(i,0,[f'S{i:02} {w}',w])
 for k,d in enumerate(data):formula(s,i,k+2,f"='구간 카운터'!H{2+k*20+i-1}",d['phases'][i-1]['waf'])
for k,d in enumerate(data):c.add_series({'name':d['label'],'categories':[s.name,1,0,20,0],'values':[s.name,1,k+2,20,k+2],'line':{'color':COLORS[k],'width':2},'marker':{'type':['circle','square','diamond','triangle','circle'][k],'size':4}})
s.insert_chart('A25',c)
s=sheet('15분 구간 WAF',['시간(h)']+[d['label'] for d in data]);br=sheet('15분 카운터',['정책','중앙 시간(h)','실제 시작 epoch','실제 종료 epoch','host_pages 차분','gc_pages 차분','WAF'])
c=chart('mixY — 15분 구간 WAF','시간 (h)','15분 WAF',True)
for i in range(40):
 s.write(i+1,0,data[0]['bins'][i]['hours'])
 for k,d in enumerate(data):
  b=d['bins'][i];r=1+k*40+i;br.write_row(r,0,[d['label'],b['hours'],b['actual_start'],b['actual_end'],b['host_pages'],b['gc_pages']]);formula(br,r,6,f'=1+F{r+1}/E{r+1}',b['waf']);formula(s,i+1,k+1,f"='15분 카운터'!G{r+1}",b['waf'])
for k,d in enumerate(data):c.add_series({'name':d['label'],'categories':[s.name,1,0,40,0],'values':[s.name,1,k+1,40,k+1],'line':{'color':COLORS[k],'width':2},'marker':{'type':'circle','size':3}})
c.set_x_axis({'name':'시간 (h)','min':0,'max':10,'major_unit':1});s.insert_chart('A45',c)
s=sheet('누적 WAF');c=chart('mixY — 측정 시작 이후 누적 WAF','시간 (h)','누적 WAF',True)
for k,d in enumerate(data):
 col=k*4;s.write_row(0,col,[d['label']+' 시간(h)','host_pages','gc_pages',d['label']+' 누적 WAF'],header)
 for i,p in enumerate(d['series'],1):
  s.write_row(i,col,[p['hours'],p['host_pages'],p['gc_pages']]);from xlsxwriter.utility import xl_col_to_name
  formula(s,i,col+3,f'=1+{xl_col_to_name(col+2)}{i+1}/{xl_col_to_name(col+1)}{i+1}',p['waf'])
 c.add_series({'name':d['label'],'categories':[s.name,1,col,len(d['series']),col],'values':[s.name,1,col+3,len(d['series']),col+3],'line':{'color':COLORS[k],'width':2},'marker':{'type':'none'}})
c.set_x_axis({'name':'시간 (h)','min':0,'max':10,'major_unit':1});s.insert_chart('V2',c)
s=sheet('이 PC v7 별도',['구간','워크로드','구간 WAF','sample p0','sample p1','sample p2','sample p3']);ld=json.loads(read(SECOND,'result/v7-20261011-icat2/mixY-result.json'))
for i,p in enumerate(local['phases'],1):s.write_row(i,0,[p['slot']+' '+p['workload'],p['workload'],p['waf']]+[next(x['sample_lines'] for x in ld['sample_counts'] if x['slot']==p['slot'] and x['partition']==part and x['namespace']==0) for part in range(4)])
s.write_row(22,0,['전체 WAF',local['total']]);s.write(23,0,local['host']);c=chart('이 PC v7 — 별도 실행의 구간 WAF','구간','구간 WAF');c.add_series({'name':'iCAT-v7 이 PC','categories':[s.name,1,0,20,0],'values':[s.name,1,2,20,2],'line':{'color':'154C9A','width':2}});s.insert_chart('I2',c)
s=sheet('출처',['정책','hostname','commit','원본 디렉터리','summary 링크'])
for i,d in enumerate(data+[local],1):s.write_row(i,0,[d['label'],d['host'],d['commit'],d['path']]);s.write_url(i,4,'https://github.com/oyeong011/iCAT-experiments/blob/'+d['commit']+'/'+d['path']+'/summary.txt',string='원본 summary.txt')
wb.close()
OUT.with_suffix('.sources.json').write_text(json.dumps({'main':MAIN,'icat2':SECOND,'files':manifest,'workbook_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest()},ensure_ascii=False,indent=2)+'\n')
print(OUT)
# Preview of the same cell values, for visual review without Microsoft Excel.
if '--preview' in __import__('sys').argv:
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 fig,axs=plt.subplots(2,1,figsize=(13,8),layout='constrained')
 labels=['CAT-37','CAT-50','CAT-47','iCAT-v6','iCAT-v7']
 axs[0].bar(labels,[d['total'] for d in data],color=['#'+x for x in COLORS]);axs[0].set_ylabel('Total WAF');axs[0].set_ylim(0,5);axs[0].set_title('mixY 10 h: same host; one run per policy')
 for i,d in enumerate(data):axs[0].text(i,d['total']+.06,f"{d['total']:.6f}",ha='center')
 for k,d in enumerate(data):axs[1].plot(range(1,21),[p['waf'] for p in d['phases']],label=labels[k],color='#'+COLORS[k],marker='o',markersize=3)
 axs[1].set_xticks(range(1,21),[f'{i} {w}' for i,w in enumerate(SEQ,1)]);axs[1].set_ylabel('Phase WAF');axs[1].set_xlabel('30-minute phase / workload');axs[1].legend(ncol=5);axs[1].grid(axis='y',alpha=.2)
 fig.savefig('/tmp/mixY-xlsx-preview-20261015.png',dpi=130)
