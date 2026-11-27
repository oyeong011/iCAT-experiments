#!/usr/bin/env bash
# revG-20261128 (run as root ONCE, e.g. `sudo systemd-run --unit=icat-cap16 --collect /home/oy/iCAT/result/revG-20261128/root-switch-16g.sh`).
# Waits until the revF queue has finished NORMALLY, then switches the kernel reservation from memmap=8G$4G to memmap=16G$4G
# (only /etc/default/grub.d/99-nvmevirt.cfg, backup kept), runs update-grub, verifies grub.cfg, and reboots.
# Aborts without changing anything if revF stopped with an anomaly, if nvmev is loaded, or if the config is not the expected one.
set -u
G=/home/oy/iCAT/result/revG-20261128; F=/home/oy/iCAT/result/revF-20261127; L=$G/switch.log; CFG=/etc/default/grub.d/99-nvmevirt.cfg
log() { echo "$(date -Is) $*" >> "$L"; chown oy:oy "$L" 2>/dev/null; }
[[ $EUID == 0 ]] || { echo 'run as root'; exit 1; }
log "root-switch-16g started; waiting for revF to finish normally"
while ! grep -q 'main queue finished' $F/queue.log; do
  if grep -qE 'queue stopped|main queue NOT started' $F/queue.log && ! pgrep -f 'queue-revF' >/dev/null; then
    log "revF stopped with an anomaly; NOT switching (nothing changed)"; exit 1; fi
  sleep 60
done
while pgrep -f 'queue-revF|runner-revF|sync-push.sh' >/dev/null; do sleep 20; done   # let the final sync-push finish
sleep 30
[[ ! -e /sys/module/nvmev ]] && ! mountpoint -q /home/oy/iCAT/mnt || { log "nvmev loaded or mnt mounted; abort"; exit 1; }
expect='GRUB_CMDLINE_LINUX="${GRUB_CMDLINE_LINUX} memmap=8G\\\$4G"'
[[ "$(cat $CFG)" == "$expect" ]] || { log "unexpected $CFG content: $(cat $CFG); abort"; exit 1; }
cp -p $CFG /etc/default/grub.d/99-nvmevirt.cfg.8g-backup-revG   # not *.cfg -> not sourced by update-grub
printf '%s\n' 'GRUB_CMDLINE_LINUX="${GRUB_CMDLINE_LINUX} memmap=16G\\\$4G"' > $CFG
log "wrote $CFG: $(cat $CFG)"
if ! update-grub >> "$L" 2>&1 || ! grep -qE 'memmap=16G\\?\$4G' /boot/grub/grub.cfg || grep -qE 'memmap=8G\\?\$4G' /boot/grub/grub.cfg; then
  cp -p /etc/default/grub.d/99-nvmevirt.cfg.8g-backup-revG $CFG; update-grub >> "$L" 2>&1
  log "grub.cfg verification failed; restored 8G config; NOT rebooting"; exit 1
fi
log "grub.cfg now has: $(grep -oE 'memmap=[^ ]+' /boot/grub/grub.cfg | sort | uniq -c | tr '\n' ' ')"
log "rebooting into memmap=16G\$4G"; sync
systemctl reboot
