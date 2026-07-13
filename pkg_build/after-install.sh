#!/bin/bash
set -e

# Force Udev rules (in case the package manager didn't install them correctly)
cp /usr/local/share/droidtux/99-android-integrator.rules /etc/udev/rules.d/ 2>/dev/null || true
udevadm control --reload-rules && udevadm trigger



# Update databases
update-desktop-database /usr/share/applications || true
gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true
