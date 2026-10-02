#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "$(readlink -f "$0")")/env.sh"
sudo umount "${MNT_DIR}" 2>/dev/null || true
sudo rmmod nvmev
