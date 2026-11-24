#!/usr/bin/env python3
"""E1 (mixR x3: online-v4 / v4nodrift / v4fullreset) analysis with a validity gate. GoCom, 2026-11-24.

    python3 -I analysis/final_e1/e1_analyze.py [GLOB ...]
Default globs: every result/**/mixR-online{v4,v4nodrift,v4fullreset}-rep*-x3 directory (smoke runs excluded).
Every run is classified by analysis/final_e1/validity.py; a phase enters statistics only if it is usable.
Outputs (overwritten on each run; all are derived files, not raw results):
  result/final-e1-validation/e1_runs.csv        per run: validity, reasons, module, seeds, WAF per usable phase, YCSB success/throughput
  result/final-e1-validation/e1_phaseA.csv      phase A of every run whose phase A is usable (contaminated runs included here)
  result/final-e1-validation/e1_stats.csv       per batch x policy x metric: n, mean, SD, 95 % t-CI; Welch vs online-v4 (same batch)
  result/final-e1-validation/e1_resets.csv      reset events (this run's kernel lines only), phase, seconds after phase start
  result/final-e1-validation/e1_timeseries.csv  5-minute WAF windows per phase (counter differences)
  report/final-e1-validation/e1_status.md       generated summary
Rules: n < 3 -> no CI comparison is printed as a claim; runs from different batches are never pooled."""
import csv, datetime as dt, math, re, statistics as st, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import validity as V

ROOT = V.ROOT
OUT = ROOT / 'result/final-e1-validation'; OUT.mkdir(parents=True, exist_ok=True)
REP = ROOT / 'report/final-e1-validation'; REP.mkdir(parents=True, exist_ok=True)
POL = ('onlinev4', 'onlinev4nodrift', 'onlinev4fullreset')
T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228, 12: 2.179, 15: 2.131, 20: 2.086, 30: 2.042}
def tq(df): return T95[min(T95, key=lambda k: abs(k - df))]


def dirs(globs):
    out = set()
    for g in globs:
        out |= {p for p in ROOT.glob(g) if p.is_dir()}
    return sorted(p for p in out if 'smoke' not in p.name and re.search(r'mixR6?-(onlinev4|onlinev4nodrift|onlinev4fullreset)-rep\d+-x3$', p.name))


def ycsb_records(d):
    """records actually loaded (YCSB load INSERT Return=OK). 300k (11-24 rerun) and 600k (Sept, 11-23) must never pool."""
    f = next(iter(sorted(d.glob('ycsb-load.txt*'))), None)
    if not f: return None
    det = V.ycsb_status(str(f))[1]
    return det.get('INSERT', (None, None))[0]


def batch(d):
    """Batch label = result directory + loaded YCSB records. Different labels are never pooled."""
    e = (d / 'environment.txt').read_text().splitlines()[0][:10] if (d / 'environment.txt').exists() else '?'
    rec = ycsb_records(d)
    return f'{d.parent.relative_to(ROOT)}/rec{rec // 1000 if rec else "?"}k'   # date not used: a queue crossing midnight is still one batch


def cnt(p):
    m = re.search(r'host_pages=(\d+) gc_pages=(\d+)', p.read_text()); return int(m[1]), int(m[2])
def ts(p): return dt.datetime.fromisoformat(p.read_text().strip()).timestamp()


def klines(d, pol, label='mixR'):
    txt = []
    for f in [d / 'kernel.log', d / 'kernel-final.log', *sorted((d / 'kernel-snapshots').glob('*.log'))]:
        if f.exists(): txt += f.read_text(errors='replace').splitlines()
    z = d / 'kernel.log.zst'
    if z.exists(): txt += subprocess.run(['zstdcat', str(z)], capture_output=True, text=True).stdout.splitlines()
    txt = sorted(set(txt))
    tag = f'mix-{label}-{pol}-'
    b = [float(m[1]) for l in txt for m in [re.match(r'\[\s*([\d.]+)\] (\S+) BEGIN', l)] if m and m[2].startswith(tag)]
    if not b: return [], {}
    t0 = max(b)   # dmesg may still hold earlier runs: keep this run only
    txt = [l for l in txt if (m := re.match(r'\[\s*([\d.]+)\]', l)) and float(m[1]) >= t0]
    mark = {m[2]: float(m[1]) for l in txt for m in [re.match(r'\[\s*([\d.]+)\] mix-\S+ phase=(\w) START', l)] if m}
    return txt, mark


def ycsb(d):
    f = next(iter(sorted(d.glob('ycsb-run-B.txt*'))), None) or next(iter(sorted(d.glob('ycsb-run.txt*'))), None)
    if not f: return {}
    worst, det, thr, done = V.ycsb_status(str(f))
    r = {'ycsb_file': f.name, 'ycsb_complete': done, 'ycsb_throughput': f'{thr:.1f}' if thr else ''}
    lf = next(iter(sorted(d.glob('ycsb-load.txt*'))), None)
    if lf:
        lw, ld, lt, ldone = V.ycsb_status(str(lf))
        r['ycsb_load_records_ok'] = ld.get('INSERT', (0, 0))[0]; r['ycsb_load_failed'] = ld.get('INSERT', (0, 0))[1]
    for op, (good, bad) in det.items():
        r[f'ycsb_{op.lower()}_ok'] = good; r[f'ycsb_{op.lower()}_failed'] = bad
        r[f'ycsb_{op.lower()}_success_pct'] = f'{100 * good / (good + bad):.3f}' if good + bad else ''
    return r


def main(globs):
    runs, pa, resets, series = [], [], [], []
    for d in dirs(globs):
        pol = re.search(r'mixR6?-(\w+?)-rep', d.name)[1]; rep = int(re.search(r'rep(\d+)', d.name)[1])
        use = V.usable_phases(d); why = V.reasons(d)
        summ = (d / 'summary.txt').read_text() if (d / 'summary.txt').exists() else ''
        env = (d / 'environment.txt').read_text() if (d / 'environment.txt').exists() else ''
        ko = next((l.split()[0][:12] for l in env.splitlines() if l.strip().endswith('.ko')), '')
        seeds = re.findall(r'"randseed" : "(\d+)"', (d / 'phase-A.json').read_text())[:1] if (d / 'phase-A.json').exists() else []
        r = dict(batch=batch(d), policy=pol, rep=rep, run_ok=V.run_ok(d), usable_phases=''.join(sorted(use)), reasons=' | '.join(why),
                 module=ko, fio_seed='/'.join(seeds), dir=str(d.relative_to(ROOT)))
        ph = {}
        for p in 'ABC':
            if not (d / f'phase-{p}-start.txt').exists(): continue
            (h0, g0), (h1, g1) = cnt(d / f'phase-{p}-start.txt'), cnt(d / f'phase-{p}-end.txt')
            ph[p] = 1 + (g1 - g0) / (h1 - h0)
            sm = re.search(rf'^phase{p}\(\S+\) host_pages=(\d+) gc_pages=(\d+)', summ, re.M)
            r[f'waf_{p}'] = f'{ph[p]:.6f}' if p in use else ''
            r[f'waf_{p}_two_path_match'] = bool(sm) and (int(sm[1]), int(sm[2])) == (h1 - h0, g1 - g0)
        m = re.search(r'^total .*host_pages=(\d+) gc_pages=(\d+)', summ, re.M)
        r['waf_total'] = f'{1 + int(m[2]) / int(m[1]):.6f}' if m and r['run_ok'] else ''
        r.update(ycsb(d))
        lines, mark = klines(d, pol, d.name.split('-')[0])
        n = {p: 0 for p in 'ABC'}
        for l in lines:
            mm = re.match(r'\[\s*([\d.]+)\] NVMeVirt: WATGC_V2 reset .*part=(\d) .*window=(\d+) arm=(\d+) reason=(\S+)', l)
            if not mm: continue
            t = float(mm[1]); p = max((q for q in 'ABC' if q in mark and mark[q] <= t), default='?')
            if p in n: n[p] += 1
            resets.append(dict(batch=r['batch'], policy=pol, rep=rep, phase=p, phase_usable=p in use, part=mm[2], window=mm[3], arm=mm[4],
                               reason=mm[5], s_after_phase_start=round(t - mark[p], 1) if p in mark else ''))
        r.update({f'resets_{p}': n[p] for p in 'ABC'})
        runs.append(r)
        if 'A' in use and 'A' in ph:
            pa.append(dict(batch=r['batch'], policy=pol, rep=rep, waf_A=f'{ph["A"]:.6f}', run_ok=r['run_ok'], dir=r['dir']))
        # 5-minute windows from the 30 s counter series
        ser = [(int(l.split()[0]), *map(int, re.search(r'host_pages=(\d+) gc_pages=(\d+)', l).groups()))
               for l in (d / 'control-series.txt').read_text().splitlines() if 'host_pages' in l] if (d / 'control-series.txt').exists() else []
        for p in 'ABC':
            if p not in use or not (d / f'phase-{p}-start.time').exists(): continue
            t0, t1 = ts(d / f'phase-{p}-start.time'), ts(d / f'phase-{p}-end.time')
            pts = [x for x in ser if t0 <= x[0] <= t1]
            for i in range(0, len(pts) - 10, 10):
                a, b = pts[i], pts[i + 10]
                if b[1] > a[1]:
                    series.append(dict(batch=r['batch'], policy=pol, rep=rep, phase=p, minute_from=round((a[0] - t0) / 60, 1),
                                       minute_to=round((b[0] - t0) / 60, 1), waf=f'{1 + (b[2] - a[2]) / (b[1] - a[1]):.4f}'))

    def w(name, rows):
        if not rows: (OUT / name).write_text(''); return
        keys = []
        for x in rows:
            keys += [k for k in x if k not in keys]
        with open(OUT / name, 'w', newline='') as f:
            cw = csv.DictWriter(f, fieldnames=keys); cw.writeheader(); cw.writerows(rows)
    w('e1_runs.csv', runs); w('e1_phaseA.csv', pa); w('e1_resets.csv', resets); w('e1_timeseries.csv', series)

    # guard: one batch = one record count; 300k and 600k are never mixed (labels already differ; this asserts it)
    for b in {r['batch'] for r in runs}:
        recs = {r.get('ycsb_load_records_ok') for r in runs if r['batch'] == b}
        if len(recs) > 1: raise SystemExit(f'batch {b} mixes YCSB record counts {recs}: refusing to compute statistics')
    # statistics: per batch, per policy, per metric; only usable values
    stats = []
    metrics = ['waf_total', 'waf_A', 'waf_B', 'waf_C', 'ycsb_throughput']
    for b in sorted({r['batch'] for r in runs}):
        for met in metrics:
            vals = {p: [float(r[met]) for r in runs if r['batch'] == b and r['policy'] == p and r.get(met) not in ('', None)] for p in POL}
            for p in POL:
                v = vals[p]
                if not v: continue
                n = len(v); m = st.mean(v); sd = st.stdev(v) if n > 1 else float('nan')
                row = dict(batch=b, metric=met, policy=p, n=n, mean=f'{m:.4f}', sd=f'{sd:.4f}' if n > 1 else '',
                           ci95=f'[{m - tq(n - 1) * sd / math.sqrt(n):.4f}, {m + tq(n - 1) * sd / math.sqrt(n):.4f}]' if n > 1 else '',
                           welch_minus_v4='', welch_ci95='', welch_df='', claim_allowed='')
                base = vals['onlinev4']
                if n < 3:   # 11-24 instruction: statistics only for policies with 3 valid repetitions
                    row.update(ci95='', sd='', claim_allowed='n<3: 통계 없음'); stats.append(row); continue
                if p != 'onlinev4' and len(base) >= 3:
                    va, vb = st.variance(v) / n, st.variance(base) / len(base); diff = m - st.mean(base); se = math.sqrt(va + vb)
                    df = (va + vb) ** 2 / (va ** 2 / (n - 1) + vb ** 2 / (len(base) - 1)) if se > 0 else float('nan')
                    q = tq(df) if df == df else float('nan')
                    row.update(welch_minus_v4=f'{diff:+.4f}', welch_ci95=f'[{diff - q * se:+.4f}, {diff + q * se:+.4f}]', welch_df=f'{df:.1f}',
                               claim_allowed='yes' if n >= 3 and len(base) >= 3 and (diff - q * se > 0 or diff + q * se < 0) else 'no')
                stats.append(row)
    w('e1_stats.csv', stats)

    # markdown status
    L = ['# E1 검증 상태 (자동 생성)', '', f'- 생성: {dt.datetime.now():%Y-%m-%d %H:%M}, `python3 -I analysis/final_e1/e1_analyze.py`',
         '- 유효성 규칙: `analysis/final_e1/validity.py`. 실패한 YCSB 단계와 그 뒤 단계는 통계에서 뺀다. 다른 배치끼리는 합치지 않는다.',
         '- `claim_allowed=yes`는 정책별·v4 모두 n ≥ 3이고 Welch 95 % CI가 0을 포함하지 않을 때만이다.', '',
         '## 실행별 유효성', '', '| 배치 | 정책 | rep | 쓸 수 있는 단계 | 전체 WAF | A | B | C | C reset | YCSB 적재 | YCSB READ 성공 % | UPDATE 성공 % | YCSB ops/s | 사유 |', '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in runs:
        L.append(f"| {r['batch']} | {r['policy']} | {r['rep']} | {r['usable_phases'] or '없음'} | {r['waf_total'] or '제외'} | {r.get('waf_A') or '제외'} | "
                 f"{r.get('waf_B') or '제외'} | {r.get('waf_C') or '제외'} | {r['resets_C'] if 'C' in r['usable_phases'] else '제외'} | {r.get('ycsb_load_records_ok', '')} | {r.get('ycsb_read_success_pct', '')} | {r.get('ycsb_update_success_pct', '')} | {r.get('ycsb_throughput', '')} | {r['reasons'] or '-'} |")
    L += ['', '## 통계 (쓸 수 있는 값만)', '', '| 배치 | 지표 | 정책 | n | 평균 | SD | 95 % CI | v4 대비 차이 | Welch 95 % CI | 주장 가능 |', '|---|---|---|---|---|---|---|---|---|---|']
    for s in stats:
        L.append(f"| {s['batch']} | {s['metric']} | {s['policy']} | {s['n']} | {s['mean']} | {s['sd']} | {s['ci95']} | {s['welch_minus_v4']} | {s['welch_ci95']} | {s['claim_allowed']} |")
    (REP / 'e1_status.md').write_text('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    # default: the 11-24 rerun (result/revision-20261124/mixR, 300k records) plus every older mixR E1-policy run for reference;
    # older runs enter only with their valid phases (phase A), and batches are never pooled.
    main(sys.argv[1:] or [f'result/**/{m}-{p}-rep*-x3' for m in ('mixR', 'mixR6') for p in ('onlinev4', 'onlinev4nodrift', 'onlinev4fullreset')])
