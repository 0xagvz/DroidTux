#!/bin/bash
# uninstall.sh - Script de desinstalación limpia para DroidTux

echo "=== Desinstalando DroidTux ==="

# 1. Detener y deshabilitar servicios
echo "[1/4] Deteniendo servicios y procesos..."
systemctl --user stop android-integrator.service || true
systemctl --user disable android-integrator.service || true

# 2. Eliminar archivos del sistema (requiere pkexec)
echo "[2/4] Eliminando reglas udev, scripts y repo APT..."
pkexec rm -f /etc/udev/rules.d/99-android-integrator.rules
pkexec rm -f /usr/local/bin/android-integrator-trigger.sh
pkexec rm -f /etc/apt/sources.list.d/inled.list
pkexec rm -f /usr/share/keyrings/inled-archive-keyring.gpg
pkexec udevadm control --reload-rules

# 3. Eliminar archivos y entorno del usuario
echo "[3/4] Eliminando archivos locales y configuración de usuario..."
rm -f "$HOME/.local/bin/app_integrator.py"
rm -f "$HOME/.local/bin/droidtux_settings.py"
rm -f "$HOME/.local/bin/droidtux-bridge-final.apk"
rm -f "$HOME/.config/systemd/user/android-integrator.service"
rm -f "$HOME/.local/share/icons/droidtux.png"
rm -rf "$HOME/.local/share/droidtux"  # Eliminar directorio de la aplicación
systemctl --user daemon-reload

# 4. Limpiar caché generada (.desktop e iconos)
echo "[4/4] Limpiando archivos autogenerados por la app (basura)..."
rm -rf "$HOME/.local/share/icons/android_apps"
rm -f "$HOME/.local/share/applications/droidtux_sync.desktop"
rm -f "$HOME/.local/share/applications/droidtux_settings.desktop"

# Eliminar accesos directos de ambas ubicaciones posibles y con ambos prefijos
for dir in "$HOME/.local/share/applications" "$HOME/Desktop" "$HOME/Escritorio" "$(xdg-user-dir DESKTOP 2>/dev/null)"; do
    if [ -d "$dir" ]; then
        find "$dir" -name "dtapp-*.desktop" -type f -delete 2>/dev/null || true
        find "$dir" -name "droidtux-*.desktop" -type f -delete 2>/dev/null || true
    fi
done

# Actualizar base de datos de aplicaciones si el comando existe
if command -v update-desktop-database >/dev/null; then
    update-desktop-database "$HOME/.local/share/applications"
fi

echo "=== Desinstalación completada. Tu sistema ha quedado impecable. ==="
