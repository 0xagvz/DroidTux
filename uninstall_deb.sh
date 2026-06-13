#!/bin/bash
# uninstall_deb.sh - Desinstalación completa de DroidTux instalado vía .deb

echo "=== Desinstalando DroidTux (Paquete .deb) ==="

# 1. Eliminar el paquete del sistema
echo "[1/4] Eliminando paquete droidtux..."
pkexec dpkg -r droidtux

# 2. Detener y deshabilitar servicios de usuario residuales
echo "[2/4] Limpiando servicios de usuario..."
systemctl --user stop android-integrator.service 2>/dev/null || true
systemctl --user disable android-integrator.service 2>/dev/null || true
rm -f "$HOME/.config/systemd/user/android-integrator.service"
systemctl --user daemon-reload

# 3. Limpiar scripts y accesos directos locales (si existieran por instalaciones previas)
echo "[3/4] Eliminando archivos locales residuales..."
rm -f "$HOME/.local/bin/app_integrator.py"
rm -f "$HOME/.local/bin/droidtux_settings.py"
rm -f "$HOME/.local/share/applications/droidtux_sync.desktop"
rm -f "$HOME/.local/share/applications/droidtux_settings.desktop"
rm -rf "$HOME/.local/share/droidtux"

# 4. Limpiar caché de iconos, archivos .desktop y fuentes APT
echo "[4/4] Limpiando iconos, accesos y fuentes APT..."
rm -f "/etc/apt/sources.list.d/droidtux.list" 2>/dev/null || pkexec rm -f "/etc/apt/sources.list.d/droidtux.list"
rm -rf "$HOME/.local/share/icons/android_apps"

# Buscar y borrar en aplicaciones y escritorios
for dir in "$HOME/.local/share/applications" "$HOME/Desktop" "$HOME/Escritorio" "$(xdg-user-dir DESKTOP 2>/dev/null)"; do
    if [ -d "$dir" ]; then
        find "$dir" -name "dtapp-*.desktop" -type f -delete 2>/dev/null || true
        find "$dir" -name "droidtux-*.desktop" -type f -delete 2>/dev/null || true
    fi
done

if command -v update-desktop-database >/dev/null; then
    update-desktop-database "$HOME/.local/share/applications"
fi

echo "=== Desinstalación del .deb completada con éxito ==="
