# Safety adapter for the unchanged latest measurement script.
ICAT_ROOT=/home/oy/iCAT
MNT_DIR=/home/oy/iCAT/mnt
source /home/oy/iCAT/result/v7-20261011-icat2/inputs/cat60-env-snapshot.sh
sudo() {
 local -a original=("$@"); local executable arg target=""
 while [[ ${1:-} == -* ]]; do shift; done
 executable=${1##*/}; shift
 case "$executable" in
  insmod)
   [[ ! -e /sys/module/nvmev ]] && ! mountpoint -q /home/oy/iCAT/mnt || return 1
   [[ "$1" == /home/oy/iCAT/buildoutput/nvmev-online-v7.ko ]] || return 1
   [[ "$(modinfo -F vermagic "$1" | cut -d' ' -f1)" == "$(uname -r)" ]] || return 1
   [[ "$(sha256sum "$1" | cut -d' ' -f1)" == eca51601893326439f79854dedf7a2cfa75296812b8f08d3fff7ad4bdb00e5ac ]] || return 1
   ;;
  mkfs.ext4|mount|nvme)
   for arg in "$@"; do [[ "$arg" =~ ^/dev/nvme[0-9]+n1$ ]] && target="$arg"; done
   [[ -n "$target" && "$target" == /dev/nvme1n1 ]] || return 1
   assert_virtual_dev "$target" || return 1
   ;;
  umount|chown)
   assert_virtual_mount /dev/nvme1n1 || return 1
   ;;
  rmmod)
   [[ "$1" == nvmev ]] && ! mountpoint -q /home/oy/iCAT/mnt || return 1
   ;;
 esac
 command /usr/bin/sudo "${original[@]}"
}
