#!/bin/bash
# install.sh - Script de instalación para DroidTux

# Salir inmediatamente si algún comando falla
set -e

USE_LN=false
for arg in "$@"; do
    if [ "$arg" == "--ln" ]; then
        USE_LN=true
    fi
done

echo "=== Instalando DroidTux (Android App Integrator) ==="
if [ "$USE_LN" = true ]; then
    echo "(!) Modo desarrollo activado: Se usarán enlaces simbólicos."
fi

# 1. Comprobar e instalar dependencias del sistema
echo "[1/4] Instalando dependencias del sistema (requiere pkexec)..."
if command -v apt-get >/dev/null; then
    pkexec apt-get update
    pkexec apt-get install -y scrcpy adb python3-pip python3-venv desktop-file-utils python3-tk
elif command -v dnf >/dev/null; then
    pkexec dnf install -y scrcpy android-tools python3-pip desktop-file-utils python3-tkinter
elif command -v pacman >/dev/null; then
    pkexec pacman -S --noconfirm scrcpy android-tools python-pip desktop-file-utils tk
else
    echo "Gestor de paquetes no soportado nativamente. Por favor, asegúrate de tener scrcpy, adb, python3 y venv."
fi

# 2. Configurar el entorno virtual de Python
echo "[2/4] Configurando el entorno virtual de Python (forzando Python del sistema para soporte Tkinter)..."
VENV_DIR="$HOME/.local/share/droidtux/venv"
mkdir -p "$HOME/.local/share/droidtux"

# Usamos el Python del sistema (/usr/bin/python3) porque el de Homebrew suele carecer de _tkinter
# We use system Python because Homebrew's often lacks _tkinter
SYSTEM_PYTHON="/usr/bin/python3"

if [ -d "$VENV_DIR" ]; then
    echo "Limpiando entorno previo..."
    rm -rf "$VENV_DIR"
fi

$SYSTEM_PYTHON -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip wheel
"$VENV_DIR/bin/pip" install androguard Pillow requests beautifulsoup4

# Verificación rápida / Quick check
if ! "$VENV_DIR/bin/python3" -c "import androguard" 2>/dev/null; then
    echo "(!) Advertencia: androguard no se instaló correctamente. Intentando método alternativo..."
    "$VENV_DIR/bin/pip" install --no-cache-dir androguard
fi

# Instalar el script principal
mkdir -p "$HOME/.local/bin"
if [ "$USE_LN" = true ]; then
    echo "Creando enlace simbólico de app_integrator.py en ~/.local/bin/..."
    ln -sf "$(pwd)/app_integrator.py" "$HOME/.local/bin/app_integrator.py"
else
    echo "Copiando app_integrator.py a ~/.local/bin/..."
    cp app_integrator.py "$HOME/.local/bin/app_integrator.py"
fi
chmod +x "$HOME/.local/bin/app_integrator.py"

# 3. Crear el wrapper para Udev
echo "[3/4] Configurando la integración con Udev y Systemd..."
WRAPPER_PATH="/usr/local/bin/android-integrator-trigger.sh"
pkexec bash -c "cat > $WRAPPER_PATH" << 'EOF'
#!/bin/bash
# Encuentra los usuarios con sesión activa y lanza el servicio systemd de usuario
for uid in $(loginctl list-sessions --no-legend | awk '{print $2}'); do
    user=$(id -un "$uid")
    # Capturamos DISPLAY y XAUTHORITY de la sesión del usuario para la GUI
    display=$(sudo -u "$user" env | grep '^DISPLAY=' | cut -d= -f2-)
    xauthority=$(sudo -u "$user" env | grep '^XAUTHORITY=' | cut -d= -f2-)
    
    if [ -z "$display" ]; then display=":0"; fi

    if [ "$1" == "add" ]; then
        # Usamos restart para asegurar que si el servicio estaba en un estado raro, se limpie y empiece de cero
        pkexec --user "$user" env DISPLAY="$display" XAUTHORITY="$xauthority" XDG_RUNTIME_DIR="/run/user/$uid" systemctl --user restart android-integrator.service
    elif [ "$1" == "remove" ]; then
        pkexec --user "$user" env XDG_RUNTIME_DIR="/run/user/$uid" systemctl --user stop android-integrator.service
    fi
done
EOF
pkexec chmod +x "$WRAPPER_PATH"

# Instalar regla udev
pkexec cp "$(pwd)/99-android-integrator.rules" /etc/udev/rules.d/
pkexec udevadm control --reload-rules
pkexec udevadm trigger

# 4. Instalar y habilitar servicio Systemd de usuario
echo "[4/4] Instalando servicio Systemd..."
mkdir -p "$HOME/.config/systemd/user"
if [ "$USE_LN" = true ]; then
    echo "Creando enlace simbólico del servicio systemd..."
    ln -sf "$(pwd)/android-integrator.service" "$HOME/.config/systemd/user/android-integrator.service"
else
    cp android-integrator.service "$HOME/.config/systemd/user/"
fi

systemctl --user daemon-reload
systemctl --user enable android-integrator.service

echo "=== Instalación completada con éxito ==="
echo "DroidTux está listo. Al conectar tu dispositivo Android por USB (con Depuración USB activada), tus aplicaciones aparecerán automáticamente en tu menú."
