#!/bin/bash
set -e

# Packaging script for DroidTux
# Dependencies: fpm, zip, build-essential, curl, gnupg

VERSION="${1:-1.0.0}"
BUILD_DIR="pkg_build"
STAGING_DIR="$BUILD_DIR/staging"

echo "[*] Starting packaging process v$VERSION..."

# 1. Build the Bridge APK
echo "[*] Building Bridge APK..."
./build_bridge.sh

# 2. Prepare Staging Area
rm -rf "$BUILD_DIR"
mkdir -p "$STAGING_DIR/usr/local/bin"
mkdir -p "$STAGING_DIR/usr/local/share/droidtux"
mkdir -p "$STAGING_DIR/usr/share/icons/hicolor/512x512/apps"
mkdir -p "$STAGING_DIR/etc/udev/rules.d"
mkdir -p "$STAGING_DIR/usr/share/applications"
mkdir -p "$STAGING_DIR/usr/lib/systemd/user"

# Copy files
cp app_integrator.py "$STAGING_DIR/usr/local/share/droidtux/"
cp droidtux_settings.py "$STAGING_DIR/usr/local/share/droidtux/"
cp droidtux-bridge-final.apk "$STAGING_DIR/usr/local/share/droidtux/"
cp droidtux.png "$STAGING_DIR/usr/local/share/droidtux/"
cp droidtux.png "$STAGING_DIR/usr/share/icons/hicolor/512x512/apps/droidtux.png"
cp 99-android-integrator.rules "$STAGING_DIR/etc/udev/rules.d/"
cp android-integrator.service "$STAGING_DIR/usr/lib/systemd/user/"

# Create desktop entries for the package
cat > "$STAGING_DIR/usr/share/applications/droidtux_sync.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=DroidTux Sync
Comment=Sync your Android apps
Exec=/usr/local/bin/droidtux-sync
Icon=droidtux
Terminal=false
Categories=Utility;
EOF

cat > "$STAGING_DIR/usr/share/applications/droidtux_settings.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=DroidTux Settings
Comment=Configure DroidTux
Exec=/usr/local/bin/droidtux-settings
Icon=droidtux
Terminal=false
Categories=Settings;
EOF

# Create wrapper scripts for /usr/local/bin
cat > "$STAGING_DIR/usr/local/bin/droidtux-sync" << 'EOF'
#!/bin/bash
/usr/local/share/droidtux/venv/bin/python3 /usr/local/share/droidtux/app_integrator.py "$@"
EOF

cat > "$STAGING_DIR/usr/local/bin/droidtux-settings" << 'EOF'
#!/bin/bash
/usr/local/share/droidtux/venv/bin/python3 /usr/local/share/droidtux/droidtux_settings.py "$@"
EOF

chmod +x "$STAGING_DIR/usr/local/bin/droidtux-sync"
chmod +x "$STAGING_DIR/usr/local/bin/droidtux-settings"

# Prepare after-install script for venv setup and APT repo
cat > "$BUILD_DIR/after-install.sh" << 'EOF'
#!/bin/bash
set -e

# Setup Python Virtual Environment
VENV_DIR="/usr/local/share/droidtux/venv"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv --system-site-packages "$VENV_DIR"
fi
"$VENV_DIR/bin/pip" install --upgrade pip wheel
"$VENV_DIR/bin/pip" install "cryptography<47" androguard Pillow requests beautifulsoup4 fastapi uvicorn python-multipart jinja2

# Setup Udev rules
udevadm control --reload-rules && udevadm trigger

# Setup APT Repository (apt.inled.es) with GPG key
if [ -d /etc/apt/sources.list.d ]; then
    echo "Configuring DroidTux APT repository..."
    KEYRING="/usr/share/keyrings/inled-archive-keyring.gpg"
    # Download and convert GPG key to binary format for signed-by
    curl -fsSL https://apt.inled.es/archive.key | gpg --dearmor -o "$KEYRING" || \
    wget -qO- https://apt.inled.es/archive.key | gpg --dearmor -o "$KEYRING"
    
    echo "deb [signed-by=$KEYRING] https://apt.inled.es stable main" > /etc/apt/sources.list.d/inled.list
fi

# Update desktop and icon databases
if command -v update-desktop-database >/dev/null; then
    update-desktop-database /usr/share/applications
fi
if command -v gtk-update-icon-cache >/dev/null; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor
fi
EOF

# Prepare after-remove script for cleanup
cat > "$BUILD_DIR/after-remove.sh" << 'EOF'
#!/bin/bash
# Cleanup APT repository configuration
rm -f /etc/apt/sources.list.d/inled.list
rm -f /usr/share/keyrings/inled-archive-keyring.gpg

# Update desktop and icon databases
if command -v update-desktop-database >/dev/null; then
    update-desktop-database /usr/share/applications
fi
if command -v gtk-update-icon-cache >/dev/null; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor
fi
EOF

# 3. Build Packages using FPM
echo "[*] Building .deb package..."
fpm -s dir -t deb -n droidtux -v "$VERSION" \
    --after-install "$BUILD_DIR/after-install.sh" \
    --after-remove "$BUILD_DIR/after-remove.sh" \
    --depends scrcpy --depends adb --depends python3-venv --depends python3-gi --depends python3-tk --depends curl --depends gnupg \
    -C "$STAGING_DIR" .

echo "[*] Building .rpm package..."
fpm -s dir -t rpm -n droidtux -v "$VERSION" \
    --after-install "$BUILD_DIR/after-install.sh" \
    --after-remove "$BUILD_DIR/after-remove.sh" \
    --depends scrcpy --depends android-tools --depends python3-venv --depends python3-gobject --depends python3-tkinter --depends curl --depends gnupg \
    -C "$STAGING_DIR" .

echo "[+] Packaging complete!"
mplete!"
