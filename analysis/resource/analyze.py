"""resource-v124-20261114: CSVs, figures and manifest from the raw run directories.
usage: python3 analysis/resource/analyze.py   (reads result/resource-v124-20261114, writes report/)"""
import csv, json, os, re, statistics as st, subprocess, platform
from pathlib import Path
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib import font_manager
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family': 'Noto Sans CJK JP', 'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})

ROOT = Path(__file__).resolve().parents[2]; B = ROOT / 'result/resource-v124-20261114'; OUT = B / 'report'; OUT.mkdir(exist_ok=True)
POL = [('resfixed47', 'Fixed CAT-47'), ('resv1', 'iCAT v1'), ('resv2', 'iCAT v2'), ('resv4', 'iCAT v4')]
NOINSTR = {'resfixed47': 'resfixed47n', 'resv1': 'online', 'resv2': 'onlinev2', 'resv4': 'onlinev4'}
MOD = {'resfixed47': 'nvmev-res-fixed47.ko', 'resv1': 'nvmev-res-v1.ko', 'resv2': 'nvmev-res-v2.ko', 'resv4': 'nvmev-res-v4.ko',
       'resfixed47n': 'nvmev-res-fixed47-noinstr.ko', 'online': 'nvmev-online-mix-20260907.ko', 'onlinev2': 'nvmev-online-v2.ko', 'onlinev4': 'nvmev-online-v4.ko'}
SLOTS = ['dogc', 'ongc', 'observe', 'update', 'select', 'log', 'setarm']
NA = '미측정'
COL = {'resfixed47': '#5A5A5A', 'resv1': '#1F4E9A', 'resv2': '#B85C00', 'resv4': '#1B7A3E'}

def sh(cmd): return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()
def write(name, rows, head):
    with open(OUT / name, 'w', newline='') as f: w = csv.writer(f); w.writerow(head); w.writerows(rows)
def agg(xs):
    xs = [x for x in xs if x is not None]
    if not xs: return [NA] * 5
    return [len(xs), st.mean(xs), st.stdev(xs) if len(xs) > 1 else 0.0, min(xs), max(xs)]
COMMIT = sh(f'git -C {ROOT} rev-parse HEAD')

def mtime(p): return os.path.getmtime(p)
def run(policy, rep):
    D = B / f'mixY-{policy}-rep{rep}'
    if not (D / 'summary.txt').exists(): return None
    r = {'policy': policy, 'rep': rep, 'dir': str(D.relative_to(ROOT))}
    s = (D / 'summary.txt').read_text()
    r['waf'] = float(re.search(r'phaseS01\(\w+\).*WAF=([\d.]+)', s)[1])
    r['t0'], r['t1'] = mtime(D / 'started.txt'), mtime(D / 'stopped.txt'); r['wall_s'] = r['t1'] - r['t0']
    ctl = dict(re.findall(r'(\w+)=(\d+)', (D / 'stopped.txt').read_text())); r['host_pages'], r['gc_pages'] = int(ctl['host_pages']), int(ctl['gc_pages'])
    # counters (sum over 4 partitions; max over partitions)
    res = {}
    f = B / f'{policy}-rep{rep}.resource.txt'
    for ln in (f.read_text().splitlines() if f.exists() else []):
        m = re.search(r'part=(\d+) slot=(\w+) n=(\d+) sum_ns=(\d+) max_ns=(\d+)', ln)
        if m:
            a = res.setdefault(m[2], [0, 0, 0]); a[0] += int(m[3]); a[1] += int(m[4]); a[2] = max(a[2], int(m[5]))
        m = re.search(r'part=(\d+) arm=(\d+) sizeof_tuner=(\d+) sizeof_arm=(\d+) arm_slots=(\d+) sizeof_param=(\d+) sizeof_conv_ftl=(\d+) sizeof_line=(\d+) tt_lines=(\d+)', ln)
        if m: r.update(final_arm=int(m[2]), sizeof_tuner=int(m[3]), sizeof_arm=int(m[4]), arm_slots=int(m[5]), sizeof_param=int(m[6]),
                       sizeof_conv_ftl=int(m[7]), sizeof_line=int(m[8]), tt_lines_per_part=int(m[9]))
    r['res'] = res
    # samples: kernel memory and kthread CPU
    smp = []
    for ln in (B / f'{policy}-rep{rep}.samples.txt').read_text().splitlines():
        kv = dict(re.findall(r'(\w+)=([\w.]+)', ln.split('threads=')[0])); ts = float(ln.split()[0]); tag = kv.get('tag')
        th = {}
        for t in re.search(r'threads="(.*)"', ln)[1].split(';'):
            if t:
                pid, comm, sched, ut, stt, rss = t.split(':'); th[comm] = (int(sched or 0), int(ut or 0) + int(stt or 0), rss.replace('rss=', ''))
        smp.append((ts, tag, kv, th))
    r['samples'] = smp
    def near(t): return min((x for x in smp if x[1] == 'run' and 'nvmev_dispatcher' in x[3]), key=lambda x: abs(x[0] - t))
    a, b = near(r['t0']), near(r['t1'])
    r['disp_cpu_ns'] = b[3]['nvmev_dispatcher'][0] - a[3]['nvmev_dispatcher'][0]; r['disp_wall_ns'] = (b[0] - a[0]) * 1e9
    io = [k for k in b[3] if k.startswith('nvmev_io_worker')]
    r['io_cpu_ns'] = sum(b[3][k][0] - a[3][k][0] for k in io if k in a[3])
    r['disp_ticks'] = b[3]['nvmev_dispatcher'][1] - a[3]['nvmev_dispatcher'][1]
    r['kthread_rss'] = sorted({v[2] or 'none' for x in smp for v in x[3].values()})
    mem = lambda tag, key: [int(x[2][key]) for x in smp if x[1] == tag and key in x[2]]
    r['mem'] = {k: {'before': mem('before', k)[0], 'loaded': mem('loaded', k)[0], 'run_max': max(mem('run', k)), 'run_min': min(mem('run', k)),
                    'run_std': st.pstdev(mem('run', k)), 'after': mem('after', k)[0]} for k in ['VmallocUsed', 'Slab', 'SUnreclaim', 'Percpu', 'KernelStack', 'MemAvailable']}
    r['coresize'] = int(next(x[2]['coresize'] for x in smp if x[1] == 'loaded'))
    return r

runs = [x for p, _ in POL for rep in (1, 2, 3) if (x := run(p, rep))]
checks = {p: run(NOINSTR[p], 1) for p, _ in POL}
by = lambda p: [r for r in runs if r['policy'] == p]
lab = dict(POL)

# ---------- data structure sizes from the built modules (gdb ptype /o)
def ptype(ko, s): return sh(f"gdb -batch -ex 'ptype /o struct {s}' {ROOT}/buildoutput/{ko} 2>/dev/null")
CAT = {'host_pages': '후보별 보상 통계 (Q16 누적 host 페이지)', 'gc_pages': '후보별 보상 통계 (Q16 누적 GC 페이지)', 'count_q16': '후보별 가중치 (할인된 관측 수)',
       'visits': '탐색 (후보별 방문 수)', 'last_window': '탐색 (후보별 마지막 관측 구간)', 'param': '공통: 현재 CAT 파라미터 (고정 CAT도 사용)',
       'active': '후보 제거 (활성 후보 비트맵)', 'probe_idx': '탐색 (정착 후 이웃 탐색 위치)',
       'stable_windows': '정착·변화 감지', 'best_confirmations': '정착·변화 감지', 'drift_windows': '정착·변화 감지', 'reference_waf_q16': '정착·변화 감지',
       'settled': '정착·변화 감지', 'exploit_windows': '탐색 (정착 후 이웃 탐색 주기)'}
ds_rows = []
for p, name in POL:
    if p == 'resfixed47': continue
    ko = MOD[p]; arm_n = int(re.search(r'struct watgc_v2_arm arm\[(\d+)\]', ptype(ko, 'watgc_v2_tuner'))[1])
    for ln in ptype(ko, 'watgc_v2_arm').splitlines():
        m = re.match(r'/\*\s+\d+\s+\|\s+(\d+) \*/\s+\S+ (\w+);', ln)
        if m: ds_rows.append([name, 'struct watgc_v2_arm × %d' % arm_n, m[2], int(m[1]), arm_n, int(m[1]) * arm_n, CAT[m[2]]])
    used = arm_n * 40
    tun = ptype(ko, 'watgc_v2_tuner')
    # top-level members only (4-space indent after the comment)
    for ln in tun.splitlines():
        m = re.match(r'/\*\s+\d+\s+\|\s+(\d+) \*/    (?!\s)(.+?)(\w+)(\[\d+\])?;?$', ln)
        if m and m[3] not in ('arm',):
            nm = m[3]; ds_rows.append([name, 'struct watgc_v2_tuner', nm, int(m[1]), 1, int(m[1]), CAT.get(nm, '구간·단계 관리 (bookkeeping)')]); used += int(m[1])
    pm = re.search(r'/\*\s+\d+\s+\|\s+(\d+) \*/\s+struct watgc_v2_param \{', tun)
    ds_rows.append([name, 'struct watgc_v2_tuner', 'param', int(pm[1]), 1, int(pm[1]), CAT['param']]); used += int(pm[1])
    total = int(re.search(r'/\* total size \(bytes\):\s+(\d+) \*/\s*\}\s*$', tun.strip())[1])
    ds_rows.append([name, 'struct watgc_v2_tuner', '(padding/holes)', total - used, 1, total - used, '정렬 패딩'])
    ds_rows.append([name, 'struct watgc_v2_tuner', 'TOTAL per partition', total, 1, total, 'sizeof(struct watgc_v2_tuner)'])
    ds_rows.append([name, 'struct watgc_v2_tuner', 'TOTAL learner-only per partition', total - int(pm[1]), 1, total - int(pm[1]), 'sizeof - param (고정 CAT도 쓰는 부분 제외)'])
    ds_rows.append([name, '4 partitions', 'TOTAL', total * 4, 4, total * 4, 'SSD_PARTITIONS=4'])
    ds_rows.append([name, '4 partitions', 'TOTAL learner-only', (total - int(pm[1])) * 4, 4, (total - int(pm[1])) * 4, ''])
write('data_structure_sizes.csv', ds_rows, ['policy', 'struct', 'member', 'bytes_each', 'count', 'bytes_total', 'category'])
SZ = {r[0]: r[5] for r in ds_rows if r[2] == 'TOTAL learner-only' and r[1] == '4 partitions'}
ALLOC = {r[0]: r[5] for r in ds_rows if r[2] == 'TOTAL' and r[1] == '4 partitions'}

# ---------- raw per-run rows
raw, cpu_rows, mem_rows = [], [], []
for r in runs:
    c = r['res']; g = lambda s, i: c.get(s, [None] * 3)[i]
    raw.append([lab[r['policy']], r['rep'], r['dir'], COMMIT, MOD[r['policy']], f"{r['waf']:.6f}", f"{r['wall_s']:.0f}", r['host_pages'], r['gc_pages'],
                r.get('final_arm', NA), g('dogc', 0), g('ongc', 0), g('observe', 0)])
    for s in SLOTS:
        n, sm, mx = c.get(s, [0, 0, 0])
        cpu_rows.append([lab[r['policy']], r['rep'], s, n, sm, f'{sm / n:.1f}' if n else NA, mx])
    cpu_rows.append([lab[r['policy']], r['rep'], 'dispatcher_kthread_schedstat', 1, r['disp_cpu_ns'], NA, NA])
    cpu_rows.append([lab[r['policy']], r['rep'], 'io_worker_kthread_schedstat', 1, r['io_cpu_ns'], NA, NA])
    cpu_rows.append([lab[r['policy']], r['rep'], 'measurement_wall', 1, int(r['wall_s'] * 1e9), NA, NA])
    for k, v in r['mem'].items():
        mem_rows.append([lab[r['policy']], r['rep'], k, 'kB', v['before'], v['loaded'], v['run_min'], v['run_max'], f"{v['run_std']:.1f}", v['after']])
    mem_rows.append([lab[r['policy']], r['rep'], 'module_coresize', 'B', NA, r['coresize'], NA, NA, NA, NA])
    mem_rows.append([lab[r['policy']], r['rep'], 'kthread VmRSS/VmHWM/PSS', '-', 'N/A (kthread, no mm)', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'])
write('resource_raw.csv', raw, ['policy', 'rep', 'run_dir', 'git_commit', 'module', 'waf_fio_fast', 'measured_wall_s', 'host_pages', 'gc_pages', 'final_arm', 'gc_calls', 'ongc_calls', 'decisions'])
write('cpu_measurements.csv', cpu_rows, ['policy', 'rep', 'slot', 'calls', 'sum_ns', 'mean_ns', 'max_ns'])
write('memory_measurements.csv', mem_rows, ['policy', 'rep', 'metric', 'unit', 'before_insmod', 'after_insmod', 'run_min', 'run_max', 'run_std', 'after_rmmod'])

# ---------- summaries
def per(p, f): return [f(r) for r in by(p)]
learn = lambda r: r['res'].get('ongc', [0, 0])[1] if r['policy'] != 'resfixed47' else 0
cpu_sum = []
for p, name in POL:
    rows = [('학습 CPU 시간 (on_gc 합, 4파티션) [ms]', lambda r: learn(r) / 1e6),
            ('계측/빈 호출 비용 (Fixed의 on_gc) [ms]', lambda r: r['res'].get('ongc', [0, 0])[1] / 1e6 if r['policy'] == 'resfixed47' else None),
            ('알고리즘 (observe = 보상 갱신 + 정책 선택) [ms]', lambda r: r['res'].get('observe', [0, 0])[1] / 1e6 if r['policy'] != 'resfixed47' else 0),
            ('보상 갱신 [ms]', lambda r: r['res'].get('update', [0, 0])[1] / 1e6 if r['policy'] != 'resfixed47' else 0),
            ('정책 선택 [ms]', lambda r: r['res'].get('select', [0, 0])[1] / 1e6 if r['policy'] != 'resfixed47' else 0),
            ('판단 기록 printk [ms]', lambda r: r['res'].get('log', [0, 0])[1] / 1e6 if r['policy'] != 'resfixed47' else 0),
            ('set_arm [ms]', lambda r: r['res'].get('setarm', [0, 0])[1] / 1e6 if r['policy'] != 'resfixed47' else 0),
            ('공통 GC 비용 (do_gc - on_gc) [ms]', lambda r: (r['res']['dogc'][1] - r['res']['ongc'][1]) / 1e6),
            ('정책 결정 횟수 (observe 호출)', lambda r: r['res'].get('observe', [0])[0] if r['policy'] != 'resfixed47' else 0),
            ('GC 횟수', lambda r: r['res']['dogc'][0]),
            ('결정당 평균 CPU (observe) [us]', lambda r: r['res']['observe'][1] / r['res']['observe'][0] / 1e3 if r['policy'] != 'resfixed47' and r['res'].get('observe', [0])[0] else None),
            ('결정당 최대 CPU (observe, 파티션 최대) [us]', lambda r: r['res']['observe'][2] / 1e3 if r['policy'] != 'resfixed47' and r['res'].get('observe') else None),
            ('GC당 평균 학습 CPU (on_gc) [ns]', lambda r: r['res']['ongc'][1] / r['res']['ongc'][0] if r['res'].get('ongc', [0])[0] else None),
            ('dispatcher kthread CPU (schedstat) [s]', lambda r: r['disp_cpu_ns'] / 1e9),
            ('dispatcher CPU / 경과 시간 [%]', lambda r: 100 * r['disp_cpu_ns'] / r['disp_wall_ns']),
            ('학습 / dispatcher CPU [%]', lambda r: 100 * learn(r) / r['disp_cpu_ns']),
            ('학습 / 공통 GC 비용 [%]', lambda r: 100 * learn(r) / (r['res']['dogc'][1] - r['res']['ongc'][1])),
            ('측정 구간 경과 시간 [s]', lambda r: r['wall_s']),
            ('WAF (FIO-Fast, 계측 빌드)', lambda r: r['waf'])]
    for k, f in rows: cpu_sum.append([name, k] + agg(per(p, f)))
write('cpu_overhead_summary.csv', cpu_sum, ['policy', 'metric', 'n_runs', 'mean', 'std', 'min', 'max'])
fixed_disp = [r['disp_cpu_ns'] for r in by('resfixed47')]
cpu_time = []
for p, name in POL:
    d = [r['disp_cpu_ns'] for r in by(p)]
    pct = (st.mean(d) - st.mean(fixed_disp)) / st.mean(fixed_disp) * 100 if d and fixed_disp and p != 'resfixed47' else NA
    cpu_time.append([name, 'dispatcher kthread CPU', *agg([x / 1e9 for x in d]), pct, '지시서 식. 단 dispatcher는 바쁜 대기(busy-poll)라 ~100%로 고정되어 학습 비용을 반영하지 못함'])
    lc = [learn(r) / 1e6 for r in by(p)]
    cpu_time.append([name, '학습 CPU [ms]', *agg(lc), NA if p != 'resfixed47' else '', '기준(Fixed) 학습 CPU = 0 → 백분율 정의 불가 (지시서 8절)'])

mem_sum = []
for p, name in POL:
    mem_sum.append([name, '학습 자료구조, 4파티션, 할당됨 [B]', ALLOC.get(name, ALLOC.get('iCAT v4')), 'sizeof (gdb, 빌드된 .ko)', '고정 CAT 빌드도 같은 struct를 conv_ftl 안에 할당(2,656 B×4), 사용은 param 128 B뿐' if p == 'resfixed47' else 'struct watgc_v2_tuner × 4, conv_ftls vmalloc 안'])
    mem_sum.append([name, '학습 전용 바이트, 4파티션 (param 제외) [B]', SZ.get(name, 0), 'sizeof', '고정 CAT은 학습 상태를 쓰지 않음 → 0'])
    for k in ['VmallocUsed', 'Slab']:
        dl = [r['mem'][k]['loaded'] - r['mem'][k]['before'] for r in by(p)]; sd = [r['mem'][k]['run_std'] for r in by(p)]
        mem_sum.append([name, f'{k} 증가 (insmod 후 - 전) [kB]', *[f'{x:.1f}' if isinstance(x, float) else x for x in agg(dl)[1:3]], f"실행 중 표준편차 평균 {st.mean(sd):.1f} kB" if sd else NA])
    cs = [r['coresize'] for r in by(p)]
    mem_sum.append([name, '모듈 코드+정적 데이터 (coresize) [B]', cs[0] if cs else NA, '/sys/module/nvmev/coresize', ''])
    mem_sum.append([name, 'kthread VmRSS / VmHWM / PSS', 'N/A', '/proc/PID/status', '커널 스레드는 mm이 없어 해당 항목이 없음'])
write('memory_overhead_summary.csv', mem_sum, ['policy', 'metric', 'value_or_mean', 'source_or_std', 'note'])
write('cpu_time.csv', cpu_time, ['policy', 'metric', 'n_runs', 'mean', 'std', 'min', 'max', 'overhead_vs_fixed_pct', 'note'])

summ = []
for p, name in POL:
    rs = by(p); ck = checks.get(p)
    summ.append([name, len(rs), SZ.get(name, 0), *[f'{x:.3f}' if isinstance(x, float) else x for x in agg([learn(r) / 1e6 for r in rs])[1:3]],
                 *[f'{x:.2f}' if isinstance(x, float) else x for x in agg([r['res']['observe'][1] / r['res']['observe'][0] / 1e3 for r in rs if r['res'].get('observe', [0])[0]])[1:3]],
                 *([f'{x:.4f}' for x in agg([r['waf'] for r in rs])[1:3]] if rs else [NA, NA]), f"{ck['waf']:.4f}" if ck else NA])
write('resource_summary.csv', summ, ['policy', 'n_runs', 'learner_bytes_4part', 'learner_cpu_ms_mean', 'learner_cpu_ms_std', 'decision_us_mean', 'decision_us_std',
                                     'waf_instr_mean', 'waf_instr_std', 'waf_uninstrumented_1run'])

# ---------- SmartGC theoretical (geometry only; SmartGC-specific terms unverified)
TiB = 2 ** 40
sg = []
for page_kib, ppb in [(16, 1536), (16, 768), (16, 384)]:
    blk = page_kib * 1024 * ppb
    for cap_tb in (1, 4, 16):
        n = cap_tb * 10 ** 12 // blk
        sg.append([f'{cap_tb} TB (10^12 B)', page_kib, ppb, blk / 2 ** 20, n, NA, NA, NA, '블록 수만 계산. Q-table 상태 수·행동 수·항목 크기는 원문 미확보로 미확인'])
sg.append(['초안 값 역산', 16, 1536, 24.0, 5461, 104e6 / 5461, 104, '1 Tb die', '초안: 1 Tb die=5,461 blocks → 104 MB. 128 GiB/5,461 = 24 MiB 블록과 일치. 블록당 약 19,044 B는 역산값이며 근거 미확인'])
sg.append(['초안 값 역산', 16, 1536, 24.0, 5461 * 8, 104e6 / 5461, 833, '1 TB = 8 dies', '833 MB = 104 MB × 8 (근거 미확인)'])
sg.append(['초안 값 역산', 16, 1536, 24.0, 5461 * 32, 104e6 / 5461, 3328, '4 TB = 32 dies', '3.3 GB = 104 MB × 32 (근거 미확인)'])
write('smartgc_theoretical_estimate.csv', sg, ['capacity', 'page_KiB', 'pages_per_block', 'block_MiB', 'blocks', 'bytes_per_block', 'MB_total', 'note2', 'note'])

# ---------- figures
pn = [n for _, n in POL]
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
learner = [SZ.get(n, 0) for n in pn]
ax[0].bar(pn, learner, color=[COL[p] for p, _ in POL]); ax[0].set_ylabel('바이트 (4 파티션 합)')
for i, v in enumerate(learner): ax[0].text(i, v, f'{v:,} B', ha='center', va='bottom', fontsize=9)
ax[0].set_title('(가) 학습 전용 자료구조 크기 (sizeof, 빌드된 모듈)')
vm = [[(r['mem']['VmallocUsed']['loaded'] - r['mem']['VmallocUsed']['before']) for r in by(p)] for p, _ in POL]
noise = st.mean([r['mem']['VmallocUsed']['run_std'] for r in runs]) if runs else 0
ax[1].bar(pn, [st.mean(v) if v else 0 for v in vm], yerr=[st.stdev(v) if len(v) > 1 else 0 for v in vm], capsize=4, color=[COL[p] for p, _ in POL])
ax[1].axhline(learner[-1] / 1024, color='k', ls=':', lw=1); ax[1].text(3.4, learner[-1] / 1024, 'v4 학습 자료구조\n(10.1 kB)', fontsize=8, va='bottom', ha='right')
ax[1].set_ylabel('kB'); ax[1].set_title(f'(나) insmod 후 VmallocUsed 증가 (평균±표준편차, n=3)\n실행 중 변동 σ≈{noise:.0f} kB')
fig.suptitle('그림 10. 메모리 오버헤드 — Fixed CAT-47 vs iCAT v1/v2/v4, FIO-Fast 30분, 3회'); fig.tight_layout(); fig.savefig(OUT / 'figure10_memory_overhead.png', dpi=150)

fig, ax = plt.subplots(1, 2, figsize=(11, 4))
for i, (p, n) in enumerate(POL):
    v = [learn(r) / 1e6 for r in by(p)]; ax[0].bar(i, st.mean(v) if v else 0, yerr=st.stdev(v) if len(v) > 1 else 0, capsize=4, color=COL[p])
    ax[0].scatter([i] * len(v), v, color='k', s=10, zorder=3)
    w = [100 * learn(r) / r['disp_cpu_ns'] for r in by(p)]; ax[1].bar(i, st.mean(w) if w else 0, yerr=st.stdev(w) if len(w) > 1 else 0, capsize=4, color=COL[p])
for a in ax: a.set_xticks(range(4)); a.set_xticklabels(pn)
ax[0].set_ylabel('ms (30분 측정 구간, 4 파티션 합)'); ax[0].set_title('(가) 학습 CPU 시간 (막대 = 평균, 오차 = 표준편차, 점 = 각 회)')
ax[1].set_ylabel('%'); ax[1].set_title('(나) 학습 시간 / dispatcher 스레드 CPU 시간')
fig.suptitle('그림 11. CPU 오버헤드 — FIO-Fast 30분, 정책당 3회 (Fixed CAT-47은 학습 없음 = 0)'); fig.tight_layout(); fig.savefig(OUT / 'figure11_cpu_overhead.png', dpi=150)

fig, ax = plt.subplots(1, 2, figsize=(11, 4))
parts = [('update', '보상 갱신'), ('select', '정책 선택'), ('log', '판단 기록 printk'), ('setarm', 'set_arm')]
for i, (p, n) in enumerate(POL[1:]):
    bottom = 0
    for j, (s, sn) in enumerate(parts):
        v = [r['res'][s][1] / r['res']['observe'][0] / 1e3 for r in by(p) if r['res'].get('observe', [0])[0]]
        m = st.mean(v) if v else 0
        ax[0].bar(i, m, bottom=bottom, color=['#1F4E9A', '#5B8BD9', '#B0B0B0', '#E0B060'][j], label=sn if i == 0 else None); bottom += m
    mx = [r['res']['observe'][2] / 1e3 for r in by(p) if r['res'].get('observe')]
    ax[1].bar(i, st.mean(mx) if mx else 0, yerr=st.stdev(mx) if len(mx) > 1 else 0, capsize=4, color=COL[p])
for a in ax: a.set_xticks(range(3)); a.set_xticklabels(pn[1:])
ax[0].set_ylabel('us / 정책 결정'); ax[0].set_title('(가) 정책 결정 1회당 평균 시간 구성 (3회 평균)'); ax[0].legend(fontsize=8)
ax[1].set_ylabel('us'); ax[1].set_title('(나) 정책 결정 1회 최대 시간 (observe, 평균±표준편차)')
fig.suptitle('그림 12. 학습 비용 — iCAT v1/v2/v4, FIO-Fast 30분, 정책당 3회'); fig.tight_layout(); fig.savefig(OUT / 'figure12_learning_cost.png', dpi=150)

# ---------- manifest
env = {'cpu': sh("lscpu | sed -n 's/^Model name: *//p'"), 'cpus': os.cpu_count(), 'mem_total_kB': sh("awk '/MemTotal/{print $2}' /proc/meminfo"),
       'os': sh("sed -n 's/^PRETTY_NAME=//p' /etc/os-release").strip('"'), 'kernel': platform.release(), 'gcc': sh('gcc --version | head -1'),
       'host_storage': sh("lsblk -d -n -o NAME,MODEL,SIZE,ROTA | grep -v loop"), 'emulated_device': 'NVMeVirt conventional SSD, RAM-backed, memmap_start=4G memmap_size=8192M, 4 FTL partitions',
       'nvmevirt_base': 'oyeong011/nvmevirt fork (see repo), conv FTL; iCAT sources online-mix-src / online-v2-src / online-v4-src',
       'insmod_args': 'memmap_start=4G memmap_size=8192M cpus=1,2 measurement_manual=1', 'make_flags': {
           'resv1/resv2/resv4': 'NVMEVIRT_GC_POLICY=WATGC_V2 KCFLAGS=-DRES_INSTR', 'resfixed47': 'NVMEVIRT_GC_POLICY=CAT_FIG7 KCFLAGS="-DRES_INSTR -DCONV_FIXED_ARM=47"',
           'resfixed47n': 'NVMEVIRT_GC_POLICY=CAT_FIG7 KCFLAGS=-DCONV_FIXED_ARM=47', 'kbuild_ccflags': sh(f"grep -h '^ccflags' {ROOT}/res-v4-src/Kbuild | tr '\\n' ' '")}}
man = {'experiment': 'resource-v124-20261114', 'git_commit_at_analysis': COMMIT, 'git_commit_at_start': (B / 'start-commit.txt').read_text().strip() if (B / 'start-commit.txt').exists() else None,
       'branch': sh(f'git -C {ROOT} rev-parse --abbrev-ref HEAD'), 'environment': env,
       'modules_sha256': {m: sh(f'sha256sum {ROOT}/buildoutput/{m} | cut -c1-64') for m in MOD.values()},
       'workload': 'mixY prep (6 GiB FIO file: 128k seq write + 3 GiB 4k randwrite) then FIO-Fast test4 for 1800 s; workloads/mix-test4.fio',
       'order': {'rep1': 'F v1 v2 v4', 'rep2': 'v4 v2 v1 F', 'rep3': 'v2 F v4 v1', 'waf_check': 'F-noinstr v1 v2 v4 (uninstrumented, 1 run each)'},
       'measurement_window': 'from `start` written to /proc/nvmevirt_measurement (started.txt mtime) to `stop` (stopped.txt mtime); counters accumulate only while active',
       'runs': [{k: r[k] for k in ('policy', 'rep', 'dir', 'waf', 'wall_s')} for r in runs],
       'waf_check_runs': {p: ({'policy': c['policy'], 'dir': c['dir'], 'waf': c['waf']} if c else None) for p, c in checks.items()}}
(OUT / 'experiment_manifest.json').write_text(json.dumps(man, ensure_ascii=False, indent=1))
print(f'{len(runs)} runs, checks: {sum(1 for c in checks.values() if c)}')
