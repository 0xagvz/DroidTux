#!/bin/bash
set -e

# Packaging script for DroidTux
# Dependencies: fpm, zip, build-essential (for apk building we assume it's pre-built or env is ready)

VERSION="1.0.0"
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
mkdir -p "$STAGING_DIR/usr/local/bin"

# Copy files
cp app_integrator.py "$STAGING_DIR/usr/local/share/droidtux/"
cp droidtux_settings.py "$STAGING_DIR/usr/local/share/droidtux/"
cp droidtux-bridge-final.apk "$STAGING_DIR/usr/local/share/droidtux/"
cp droidtux.png "$STAGING_DIR/usr/share/icons/hicolor/512x512/apps/droidtux.png"
cp 99-android-integrator.rules "$STAGING_DIR/etc/udev/rules.d/"

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

# Prepare after-install script for venv setup
cat > "$BUILD_DIR/after-install.sh" << 'EOF'
#!/bin/bash
VENV_DIR="/usr/local/share/droidtux/venv"
python3 -m venv --system-site-packages "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip wheel
"$VENV_DIR/bin/pip" install "cryptography<47" androguard Pillow requests beautifulsoup4 fastapi uvicorn python-multipart jinja2
udevadm control --reload-rules && udevadm trigger
EOF

# 3. Build Packages using FPM
# Note: FPM must be installed in the environment
echo "[*] Building .deb package..."
fpm -s dir -t deb -n droidtux -v "$VERSION" \
    --after-install "$BUILD_DIR/after-install.sh" \
    --depends scrcpy --depends adb --depends python3-venv --depends python3-gi \
    -C "$STAGING_DIR" .

echo "[*] Building .rpm package..."
fpm -s dir -t rpm -n droidtux -v "$VERSION" \
    --after-install "$BUILD_DIR/after-install.sh" \
    --depends scrcpy --depends adb --depends python3-venv --depends python3-gi \
    -C "$STAGING_DIR" .

echo "[+] Packaging complete!"
