#!/usr/bin/env bash
# revG-20261128: AFTER the revG batch, restore the original memmap=8G$4G (run as root), then reboot manually.
set -u
G=/home/oy/iCAT/result/revG-20261128; L=$G/switch.log; CFG=/etc/default/grub.d/99-nvmevirt.cfg; B=/etc/default/grub.d/99-nvmevirt.cfg.8g-backup-revG
[[ $EUID == 0 ]] || { echo 'run as root'; exit 1; }
pgrep -f 'queue-revG|runner-revG' >/dev/null && { echo 'revG still running'; exit 1; }
[[ -e $B ]] || { echo "no backup $B"; exit 1; }
cp -p $B $CFG && update-grub && grep -qE 'memmap=8G\\?\$4G' /boot/grub/grub.cfg && echo "$(date -Is) restored memmap=8G\$4G (reboot to apply)" | tee -a $L
