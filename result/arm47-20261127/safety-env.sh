# Safety adapter for the unchanged latest measurement script.
ICAT_ROOT=/home/oy/iCAT
MNT_DIR=/home/oy/iCAT/mnt
source /home/oy/iCAT/result/arm47-20261127/inputs/env-seungcom.sh
sudo() {
 local -a original=("$@"); local executable arg target=""
 while [[ ${1:-} == -* ]]; do shift; done
 executable=${1##*/}; shift
 case "$executable" in
  insmod)
   [[ ! -e /sys/module/nvmev ]] && ! mountpoint -q /home/oy/iCAT/mnt || return 1
   [[ "$(modinfo -F vermagic "$1" | cut -d' ' -f1)" == "$(uname -r)" ]] || return 1
   grep -qxF "$(sha256sum "$1" | cut -d' ' -f1)  $1" <(sed 's#  buildoutput/#  /home/oy/iCAT/buildoutput/#' /home/oy/iCAT/result/arm47-20261127/modules.sha256) || return 1
   ;;
  mkfs.ext4|mount|nvme)
   for arg in "$@"; do [[ "$arg" =~ ^/dev/nvme[0-9]+n1$ ]] && target="$arg"; done
   [[ -n "$target" && "$target" == /dev/nvme0n1 ]] || return 1
   assert_virtual_dev "$target" || return 1
   ;;
  umount|chown)
   assert_virtual_mount /dev/nvme0n1 || return 1
   ;;
  rmmod)
   [[ "$1" == nvmev ]] && ! mountpoint -q /home/oy/iCAT/mnt || return 1
   ;;
 esac
 command /usr/bin/sudo "${original[@]}"
}
