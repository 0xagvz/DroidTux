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



# Setup RPM Repository (Fedora/RHEL/openSUSE)
if [ -d /etc/yum.repos.d ]; then
    echo "Configuring DroidTux RPM repository..."
    cat > /etc/yum.repos.d/inled.repo << EOF
[inled]
name=Inled Repository
baseurl=https://apt.inled.es/rpm/
enabled=1
gpgcheck=1
gpgkey=https://apt.inled.es/archive.key
EOF
fi

# Setup Pacman Repository (Arch Linux)
# Note: Arch doesn't have a sources.list.d equivalent, we add to pacman.conf
if [ -f /etc/pacman.conf ] && ! grep -q "\[inled\]" /etc/pacman.conf; then
    echo "Configuring DroidTux Pacman repository..."
    cat >> /etc/pacman.conf << EOF

[inled]
SigLevel = Optional TrustAll
Server = https://apt.inled.es/arch/
EOF
fi

# Update databases
update-desktop-database /usr/share/applications || true
gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true
