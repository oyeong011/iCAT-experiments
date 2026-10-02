#!/usr/bin/env python3
"""Summarize NVMeVirt GC dmesg logs.

  parse.py result/*.log            -> per-run summary CSV on stdout
  parse.py --windows result/*.log  -> per-window WAF series CSV
  parse.py --selftest
"""
import csv, re, statistics, sys
from pathlib import Path

RUN = re.compile(r"GC stats: policy=(?P<policy>\S+)(?: age_mode=(?P<age_mode>\S+))? "
                 r"host_pages=(?P<host>\d+) gc_pages=(?P<gc>\d+) gc_count=(?P<gc_count>\d+) "
                 r"WAF=(?P<waf>[\d.]+|N/A)(?: scale_pct=(?P<scale>\d+) age_ratio=(?P<ratio>\d+))?")
HIST = re.compile(r"GC victim hist: level=(?P<level>\d+) count=(?P<count>\d+)")
MEAN = re.compile(r"GC victim mean: victims=(?P<victims>\d+) vpc=(?P<vpc>[\d.]+) age_ms=(?P<age_ms>\d+)")
WIN = re.compile(r"GC window: seq=(?P<seq>\d+) host_pages=(?P<host>\d+) gc_pages=(?P<gc>\d+) "
                 r"WAF=(?P<waf>[\d.]+) cum_host=(?P<cum_host>\d+) cum_gc=(?P<cum_gc>\d+)")
# result/<workload>-<tag>-rep<N>-<date>-<pid>.log
NAME = re.compile(r"^(?P<workload>[^-]+)-(?P<tag>.+)-rep(?P<rep>\d+)-\d{8}-\d{6}-\d+$")


def name_fields(path):
    m = NAME.match(Path(path).stem)
    return m.groupdict() if m else {"workload": "", "tag": Path(path).stem, "rep": ""}


def parse(path):
    """One dmesg log -> (summary dict, list of window dicts)."""
    text = Path(path).read_text(errors="replace")
    run = RUN.search(text)
    if not run:
        return None, []
    row = {"file": Path(path).name, **name_fields(path), **run.groupdict()}
    # WAF from the counters, not the kernel's rounded print.
    host, gc = int(row["host"]), int(row["gc"])
    row["waf"] = (host + gc) / host if host else float("nan")
    row["gc_pages_per_gc"] = gc / int(row["gc_count"]) if int(row["gc_count"]) else float("nan")
    for m in HIST.finditer(text):
        row["hist_l" + m["level"]] = int(m["count"])
    mean = MEAN.search(text)
    if mean:
        row.update(victim_vpc=float(mean["vpc"]), victim_age_ms=int(mean["age_ms"]))
    windows = [{"file": Path(path).name, **name_fields(path), **m.groupdict()}
               for m in WIN.finditer(text)]
    return row, windows


def main(argv):
    if "--selftest" in argv:
        return selftest()
    want_windows = "--windows" in argv
    paths = [a for a in argv[1:] if not a.startswith("--")]
    rows, windows = [], []
    for p in paths:
        row, wins = parse(p)
        if row:
            rows.append(row)
            windows.extend(wins)
        else:
            print(f"{p}: no GC stats line", file=sys.stderr)
    out = windows if want_windows else rows
    if not out:
        return 1
    keys = sorted({k for r in out for k in r}, key=lambda k: (k not in
                  ("file", "workload", "tag", "rep", "policy", "age_mode"), k))
    w = csv.DictWriter(sys.stdout, fieldnames=keys, restval="")
    w.writeheader()
    w.writerows(out)
    if not want_windows:
        groups = {}
        for r in rows:
            groups.setdefault((r["workload"], r["tag"]), []).append(r["waf"])
        print("\n# workload,tag,n,mean_waf,stdev_waf", file=sys.stderr)
        for (wl, tag), v in sorted(groups.items()):
            sd = statistics.stdev(v) if len(v) > 1 else 0.0
            print(f"# {wl},{tag},{len(v)},{statistics.fmean(v):.4f},{sd:.4f}", file=sys.stderr)
    return 0


def selftest():
    import tempfile, os
    log = ("[1] NVMeVirt: GC window: seq=0 host_pages=262144 gc_pages=131072 WAF=1.500 "
           "cum_host=262144 cum_gc=131072\n"
           "[2] NVMeVirt: GC victim hist: level=0 count=7\n"
           "[3] NVMeVirt: GC victim mean: victims=10 vpc=12.50 age_ms=4200\n"
           "[4] NVMeVirt: GC stats: policy=cat-fig7 age_mode=create host_pages=100 "
           "gc_pages=50 gc_count=5 WAF=1.500 scale_pct=100 age_ratio=7\n")
    d = tempfile.mkdtemp()
    p = os.path.join(d, "test3-cat-a100-r7-rep2-20260101-000000-1.log")
    Path(p).write_text(log)
    row, wins = parse(p)
    assert row["workload"] == "test3" and row["tag"] == "cat-a100-r7" and row["rep"] == "2", row
    assert abs(row["waf"] - 1.5) < 1e-9 and row["gc_pages_per_gc"] == 10.0, row
    assert row["age_mode"] == "create" and row["hist_l0"] == 7 and row["victim_vpc"] == 12.5
    assert len(wins) == 1 and wins[0]["waf"] == "1.500", wins
    # a log without the summary line must not be silently counted
    p2 = os.path.join(d, "empty-x-rep1-20260101-000000-1.log")
    Path(p2).write_text("nothing here\n")
    assert parse(p2) == (None, [])
    print("selftest ok")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
