#!/bin/bash
# uninstall_pacman.sh - Uninstall DroidTux from Arch Linux
# Desinstalar DroidTux de Arch Linux

echo "Uninstalling DroidTux (Pacman)..."
echo "Desinstalando DroidTux (Pacman)..."

if command -v pacman >/dev/null; then
    pkexec pacman -Rs droidtux
else
    echo "Pacman not found. Please uninstall manually."
    echo "No se encontró Pacman. Por favor, desinstala manualmente."
fi
