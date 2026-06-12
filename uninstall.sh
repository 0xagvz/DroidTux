#!/bin/bash
# uninstall.sh - Script de desinstalación limpia para DroidTux

echo "=== Desinstalando DroidTux ==="

# 1. Detener y deshabilitar servicios
echo "[1/4] Deteniendo servicios y procesos..."
systemctl --user stop android-integrator.service || true
systemctl --user disable android-integrator.service || true

# 2. Eliminar archivos del sistema (requiere pkexec)
echo "[2/4] Eliminando reglas udev y scripts envolventes del sistema..."
pkexec rm -f /etc/udev/rules.d/99-android-integrator.rules
pkexec rm -f /usr/local/bin/android-integrator-trigger.sh
pkexec udevadm control --reload-rules

# 3. Eliminar archivos y entorno del usuario
echo "[3/4] Eliminando entorno de Python y configuración de usuario..."
rm -f "$HOME/.local/bin/app_integrator.py"
rm -f "$HOME/.config/systemd/user/android-integrator.service"
rm -rf "$HOME/.local/share/droidtux"  # Esto borra el venv y su carpeta
systemctl --user daemon-reload

# 4. Limpiar caché generada (.desktop e iconos)
echo "[4/4] Limpiando archivos autogenerados por la app (basura)..."
rm -rf "$HOME/.local/share/icons/android_apps"
# Los desktop se creaban con el prefijo droidtux-
find "$HOME/.local/share/applications" -name "droidtux-*.desktop" -type f -delete 2>/dev/null || true

# Actualizar base de datos de aplicaciones si el comando existe
if command -v update-desktop-database >/dev/null; then
    update-desktop-database "$HOME/.local/share/applications"
fi

echo "=== Desinstalación completada. Tu sistema ha quedado impecable. ==="
