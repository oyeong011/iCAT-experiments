from pathlib import Path
import json,csv
P=Path(__file__).resolve().parent

def refresh():
    m=json.loads((P/'metadata.json').read_text());lines=['# 두 번째 PC iCAT-v7 실행 보고', '', '상태: '+((P/'status.txt').read_text().strip() if (P/'status.txt').exists() else '준비'),'',
        '- 호스트: '+m['hostname']+' / '+m['machine_id'], '- 커널: '+m['kernel'],'- 모듈 SHA256: '+m['module_sha256'],
        '- 소스: '+m['source_commit'],'- 각 조건 1회, 명시 start/stop 계측, 초기 학습 비용 포함. 실패 값은 진단용이며 순위에서 제외.','']
    data={}
    for stage in ['fvo90','mixY']:
        f=P/f'{stage}-result.json'
        if not f.exists():lines.append(stage+': 아직 결과 없음\n');continue
        d=json.loads(f.read_text());data[stage]=d
        lines.extend([f"## {stage}",f"- 상태 {d['status']}; runner exit={d['runner_exit']}; 전체 WAF={d.get('waf')}",f"- 원본: `{d['raw_path']}`",f"- host_bytes − block-stat bytes: {d.get('host_bytes_minus_block_stat')}"])
        for x in d.get('issues',[]):lines.append('- 실패/미확인: '+x)
        for x in d.get('warnings',[]):lines.append('- 주의: '+x)
        lines.extend(['','| 구간 | workload | 실제 초 | 구간 WAF | sample p0 / p1 / p2 / p3 |','|---|---|---:|---:|---|'])
        for row in d.get('phases',[]):
            counts=[str(next((v['sample_lines'] for v in d.get('sample_counts',[]) if v['slot']==row['slot'] and v['namespace']==0 and v['partition']==part),0)) for part in range(4)]
            w=row.get('waf');lines.append(f"| {row['slot']} | {row['workload']} | {row['actual_seconds']:.0f} | {w:.6f} | {' / '.join(counts)} |" if w is not None else f"| {row['slot']} | {row['workload']} | {row['actual_seconds']:.0f} | 미확인 | {' / '.join(counts)} |")
        slow=[v['sample_lines'] for v in d.get('sample_counts',[]) if v['workload']=='FIO-Slow' and v['namespace']==0]
        if slow:lines.append(f'\nFIO-Slow의 구간·파티션별 관측 sample: 최소 {min(slow)}, 최대 {max(slow)}, 평균 {sum(slow)/len(slow):.1f}. 약 300회 기대값과 비교할 관측값이며 합격 기준은 아니다.')
        lines.append('')
    rows=[];cat=Path(m['cat_campaign']);q=Path(m['cat_resume'])
    for i in range(30):
        f=(cat if i<3 else q)/f'arm{i:02}-result.json'
        if not f.exists():continue
        d=json.loads(f.read_text())
        if d.get('status')=='validated_saved_evidence' and isinstance(d.get('waf'),(int,float)):
            rows.append(dict(policy=f'arm{i:02}',waf=d['waf'],source=str(f),host=m['hostname'],measurement='manual',phase_seconds=1800))
    rows.sort(key=lambda x:x['waf'])
    for i,r in enumerate(rows,1):r['position']=i
    with (P/'cat-reference.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=['position','policy','waf','host','measurement','phase_seconds','source']);w.writeheader();w.writerows(rows)
    if 'fvo90' in data and data['fvo90']['status']=='validated_saved_evidence':
        value=data['fvo90']['waf'];rank=1+sum(x['waf']<value for x in rows);unknown=60-len(rows)
        lines.extend(['## CAT60 비교',f'동일 호스트·동일 90분 조건에서 검증된 고정 CAT {len(rows)}개와 비교: v7 WAF={value:.6f}, 삽입 순위 {rank}(1+count[CAT WAF < v7 WAF]).',f'전체 60개 중 {unknown}개는 이 보고서의 동일 호스트 검증 풀에 없어 전체 순위는 {rank}–{rank+unknown} 범위. 다른 PC 결과를 자동 합산하지 않음. 각 arm과 v7이 단일 실행이므로 이 순위는 관측 순위이며 통계적 우열이 아님.',''])
    lines.extend(['실패 목록: failures.tsv. 원본은 덮어쓰지 않음. 30초 시계열은 독립 반복이 아님. sample CSV는 kernel.log 구간 marker 사이 실제 로그 수이며 구간 밖 로그는 따로 표시.'])
    (P/'report.md').write_text('\n'.join(lines)+'\n')
if __name__=='__main__':refresh()
