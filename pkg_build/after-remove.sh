#!/bin/bash
rm -f /usr/local/bin/android-integrator-trigger.sh
rm -f /etc/udev/rules.d/99-android-integrator.rules
udevadm control --reload-rules
rm -f /etc/apt/sources.list.d/inled.list
rm -f /usr/share/keyrings/inled-archive-keyring.gpg
update-desktop-database /usr/share/applications || true
