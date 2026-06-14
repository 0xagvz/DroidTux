#!/bin/bash
set -e

# Setup Python Virtual Environment
VENV_DIR="/usr/local/share/droidtux/venv"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv --system-site-packages "$VENV_DIR"
fi
"$VENV_DIR/bin/pip" install --upgrade pip wheel
"$VENV_DIR/bin/pip" install "cryptography<47" androguard Pillow requests beautifulsoup4 fastapi uvicorn python-multipart jinja2

# Force Udev rules (in case the package manager didn't install them correctly)
cp /usr/local/share/droidtux/99-android-integrator.rules /etc/udev/rules.d/ 2>/dev/null || true
udevadm control --reload-rules && udevadm trigger

# Setup APT Repository
if [ -d /etc/apt/sources.list.d ]; then
    echo "Configuring DroidTux APT repository..."
    KEYRING="/usr/share/keyrings/inled-archive-keyring.gpg"
    curl -fsSL https://apt.inled.es/archive.key | gpg --dearmor -o "$KEYRING" || \
    wget -qO- https://apt.inled.es/archive.key | gpg --dearmor -o "$KEYRING"
    echo "deb [signed-by=$KEYRING] https://apt.inled.es stable main" > /etc/apt/sources.list.d/inled.list
fi

# Update databases
update-desktop-database /usr/share/applications || true
gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true
