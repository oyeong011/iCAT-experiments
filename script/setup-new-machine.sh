#!/usr/bin/env bash
# One-time setup of another x86 Ubuntu machine for these experiments. Run as user "oy" from /home/oy/iCAT
# (scripts use /home/oy/... paths). Stage 1 needs a reboot afterwards; then run it again for stage 2.
set -Eeuo pipefail
cd /home/oy/iCAT
if ! grep -q 'memmap=8G\$4G' /proc/cmdline; then
  echo "== stage 1: packages, sudo rules, 8 GiB memory reservation"
  [[ $(awk '/MemTotal/{print int($2/1048576)}' /proc/meminfo) -ge 15 ]] || { echo "need >= 16 GiB RAM"; exit 1; }
  sudo apt-get update
  sudo apt-get install -y build-essential "linux-headers-$(uname -r)" fio jq sqlite3 openjdk-21-jre-headless python3 python3-matplotlib \
       git autoconf automake libtool bison flex
  sudo tee /etc/sudoers.d/icat >/dev/null <<'SUDO'
oy ALL=(root) NOPASSWD: /usr/sbin/insmod /home/oy/iCAT/buildoutput/nvmev-*.ko *
oy ALL=(root) NOPASSWD: /usr/sbin/rmmod nvmev
oy ALL=(root) NOPASSWD: /usr/sbin/mkfs.ext4 /dev/nvme*n1
oy ALL=(root) NOPASSWD: /usr/bin/mount -o nodiscard /dev/nvme*n1 /home/oy/iCAT/mnt
oy ALL=(root) NOPASSWD: /usr/bin/umount /home/oy/iCAT/mnt
oy ALL=(root) NOPASSWD: /usr/bin/chown -R oy\:oy /home/oy/iCAT/mnt
oy ALL=(root) NOPASSWD: /usr/bin/tee /dev/kmsg
oy ALL=(root) NOPASSWD: /usr/bin/dmesg --color=never
oy ALL=(root) NOPASSWD: /usr/bin/true
oy ALL=(root) NOPASSWD: /usr/bin/tee /proc/sys/vm/drop_caches
SUDO
  sudo chmod 0440 /etc/sudoers.d/icat && sudo visudo -cf /etc/sudoers.d/icat
  # physical 4 GiB..12 GiB is handed to NVMeVirt, the same layout as the original machine
  echo 'GRUB_CMDLINE_LINUX_DEFAULT="$GRUB_CMDLINE_LINUX_DEFAULT memmap=8G\\\$4G"' | sudo tee /etc/default/grub.d/99-nvmevirt.cfg
  sudo update-grub
  echo "== reboot now, then run this script again"; exit 0
fi
echo "== stage 2: modules, YCSB, filebench"
bash script/build-all-modules.sh
if [[ ! -d /home/oy/YCSB/ycsb-0.17.0 ]]; then
  mkdir -p /home/oy/YCSB && cd /home/oy/YCSB
  curl -fLO https://github.com/brianfrankcooper/YCSB/releases/download/0.17.0/ycsb-0.17.0.tar.gz && tar xzf ycsb-0.17.0.tar.gz
  curl -fL -o ycsb-0.17.0/jdbc-binding/lib/sqlite-jdbc-3.46.1.3.jar https://repo1.maven.org/maven2/org/xerial/sqlite-jdbc/3.46.1.3/sqlite-jdbc-3.46.1.3.jar
  cd /home/oy/iCAT
fi
(cd tools/filebench-local && { [[ -x configure ]] || autoreconf -i; } && ./configure >/dev/null && make -j"$(nproc)" >/dev/null) && echo "filebench built"
echo "== done. Next: bash script/validate-new-machine.sh"
