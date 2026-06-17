#!/bin/bash
# uninstall_rpm.sh - Uninstall DroidTux from Fedora
# Desinstalar DroidTux de Fedora

echo "Uninstalling DroidTux (RPM)..."
echo "Desinstalando DroidTux (RPM)..."

if command -v dnf >/dev/null; then
    pkexec dnf remove -y droidtux
else
    echo "DNF not found. Please uninstall manually."
    echo "No se encontró DNF. Por favor, desinstala manualmente."
fi
