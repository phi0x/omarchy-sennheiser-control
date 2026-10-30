#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo 'Run ./install.sh --device-access'; exit 1; }
# Active desktop user only. The 70 prefix applies before systemd seat ACL rules.
cat > /etc/udev/rules.d/70-sennheiser-control.rules <<'RULE'
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="3542", ATTRS{idProduct}=="3001", TAG+="uaccess"
RULE
udevadm control --reload-rules
udevadm trigger --subsystem-match=hidraw
udevadm settle
echo 'BTD 700 access configured. Replug the dongle if access is not immediate.'
