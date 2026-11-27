#!/usr/bin/env bash
# revG-20261128: user crontab @reboot. Starts the revG queue ONCE, only if the 16 GiB reservation is verified.
export PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin HOME=/home/oy
G=/home/oy/iCAT/result/revG-20261128; L=$G/queue.log; V=$G/boot-verify.txt
[[ -e $G/boot-start.done ]] && exit 0
sleep 120
log() { echo "$(date -Is) boot-start: $*" >> $L; }
{ date -Is; cat /proc/cmdline; lsmem -b --output RANGE,SIZE,STATE; free -b; for d in /sys/firmware/memmap/*; do echo "$(cat $d/start) $(cat $d/end) $(cat $d/type)"; done | sort; } > $V 2>&1
grep -qE '(^| )memmap=16G\$4G( |$)' /proc/cmdline || { log "cmdline lacks memmap=16G\$4G; queue NOT started ($(cat /proc/cmdline))"; exit 0; }
# 4 GiB .. 20 GiB must not be online System RAM
bad=$(lsmem -b --raw --noheadings --output RANGE,STATE | python3 -I -c "
import sys
for l in sys.stdin:
    r, st = l.split()
    a, b = (int(x, 16) for x in r.split('-'))
    if st == 'online' and a < 20 * 2**30 and b >= 4 * 2**30: print(r)")
[[ -z "$bad" ]] || { log "online RAM overlaps 4G-20G ($bad); queue NOT started"; exit 0; }
[[ ! -e /sys/module/nvmev ]] && ! mountpoint -q /home/oy/iCAT/mnt || { log "device busy at boot; queue NOT started"; exit 0; }
touch $G/boot-start.done
log "16 GiB reservation verified (cmdline + lsmem); starting queue-revG.sh"
setsid nohup $G/queue-revG.sh > $G/queue.console.txt 2>&1 < /dev/null &
