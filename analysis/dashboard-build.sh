#!/usr/bin/env bash
# Build the results board: data from raw results -> dashboard/icat-board.html
set -e
cd /home/oy/iCAT; mkdir -p dashboard
python3 analysis/dashboard-data.py > dashboard/data.json
python3 -c "import sys;t=open('analysis/dashboard-template.html').read();d=open('dashboard/data.json').read();open('dashboard/icat-board.html','w').write(t.replace('__DATA__',d))"
echo dashboard/icat-board.html
