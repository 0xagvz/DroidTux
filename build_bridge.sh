#!/bin/bash
set -e

# Configuración de rutas
SDK_PLATFORM="/usr/lib/android-sdk/platforms/android-34"
ANDROID_JAR="$SDK_PLATFORM/android.jar"
BUILD_DIR="build_out"
SRC_DIR="bridge_src"
PACKAGE_NAME="com.droidtux.bridge"

echo "[*] Limpiando entorno..."
rm -rf "$BUILD_DIR" && mkdir -p "$BUILD_DIR/obj" "$BUILD_DIR/apk"

echo "[*] Generando recursos..."
aapt2 compile --dir res -o "$BUILD_DIR/res.zip" 2>/dev/null || mkdir -p res # Creamos carpeta res vacía si no existe
aapt2 link "$BUILD_DIR/res.zip" -I "$ANDROID_JAR" \
    --manifest "$SRC_DIR/AndroidManifest.xml" \
    --java "$BUILD_DIR/gen" \
    -o "$BUILD_DIR/base.apk"

echo "[*] Compilando Java..."
javac -d "$BUILD_DIR/obj" \
    -classpath "$ANDROID_JAR" \
    "$SRC_DIR/IconService.java"

echo "[*] Generando DEX..."
mkdir -p "$BUILD_DIR/dex"
d8 --release --output "$BUILD_DIR/dex" \
    --lib "$ANDROID_JAR" \
    "$BUILD_DIR/obj/com/droidtux/bridge/IconService.class"

echo "[*] Construyendo APK final..."
cp "$BUILD_DIR/base.apk" "$BUILD_DIR/droidtux-bridge.apk"
cd "$BUILD_DIR/dex"
zip -u "../droidtux-bridge.apk" "classes.dex"
cd ../..

echo "[*] Alineando APK..."
zipalign -f 4 "$BUILD_DIR/droidtux-bridge.apk" "droidtux-bridge-aligned.apk"

echo "[*] Firmando APK (Debug)..."
# Generar keystore si no existe
if [ ! -f debug.keystore ]; then
    keytool -genkey -v -keystore debug.keystore -alias androiddebugkey -storepass android -keypass android -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=Android Debug,O=Android,C=US"
fi

apksigner sign --ks debug.keystore --ks-pass pass:android --out droidtux-bridge-final.apk droidtux-bridge-aligned.apk

echo "[+] ¡APK generado con éxito: droidtux-bridge-final.apk!"
