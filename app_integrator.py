import os
import subprocess
import shutil
import tempfile
import threading
import json
import time
from pathlib import Path
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango, Gio, GdkPixbuf

# Configuración de Rutas
BASE_DIR = Path(__file__).resolve().parent
ICONS_DIR = Path.home() / ".local/share/icons/android_apps"
DESKTOP_DIR = Path.home() / ".local/share/applications"
SETTINGS_DIR = Path.home() / ".config/droidtux"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"
BRIDGE_APK = BASE_DIR / "droidtux-bridge-final.apk"
LOCAL_LOGO = BASE_DIR / "droidtux.png"
LOGO_PATH = Path.home() / ".local/share/icons/droidtux.png"

# Si no existe el logo en la ruta de iconos, usamos el local
if not LOGO_PATH.exists() and LOCAL_LOGO.exists():
    LOGO_PATH = LOCAL_LOGO

# CSS para estilo nativo con espaciado
NORD_CSS = b"""
.header { padding: 20px; border-bottom: 2px solid @theme_selected_bg_color; }
.title { font-size: 24px; font-weight: bold; }
.subtitle { font-size: 14px; opacity: 0.8; }
.card { border-radius: 12px; margin: 20px; padding: 20px; border: 1px solid @theme_bg_color; }
.log-view { font-family: 'Monospace'; font-size: 12px; border-radius: 8px; }
progressbar trough { border-radius: 5px; min-height: 10px; }
progressbar progress { border-radius: 5px; }
"""

def load_settings():
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except: pass
    return {"resolution": "1280x720", "dpi": 240, "bitrate": "16M"}

class DroidTuxApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="DroidTux Dashboard")
        self.set_default_size(500, 700)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.settings = load_settings()

        # Aplicar CSS
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(NORD_CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.setup_ui()
        self.show_all()
        
    def setup_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(vbox)

        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        header.get_style_context().add_class("header")
        
        if LOGO_PATH.exists():
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                str(LOGO_PATH), 120, 120, True
            )
            img = Gtk.Image.new_from_pixbuf(pixbuf)
            header.pack_start(img, False, False, 0)

        title = Gtk.Label(label="DROIDTUX")
        title.get_style_context().add_class("title")
        header.pack_start(title, False, False, 0)
        
        subtitle = Gtk.Label(label="Android Desktop Integrator")
        subtitle.get_style_context().add_class("subtitle")
        header.pack_start(subtitle, False, False, 0)
        vbox.pack_start(header, False, False, 0)

        # Main Card
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        card.get_style_context().add_class("card")
        vbox.pack_start(card, True, True, 0)

        self.status_label = Gtk.Label(label="Listo para sincronizar")
        self.status_label.set_halign(Gtk.Align.CENTER)
        card.pack_start(self.status_label, False, False, 0)

        self.progress_bar = Gtk.ProgressBar()
        card.pack_start(self.progress_bar, False, False, 0)

        # Log Area
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.get_style_context().add_class("log-view")
        self.text_view = Gtk.TextView()
        self.text_view.set_editable(False)
        self.text_view.set_cursor_visible(False)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        scrolled.add(self.text_view)
        card.pack_start(scrolled, True, True, 0)

        # Action Buttons
        bbox = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
        bbox.set_layout(Gtk.ButtonBoxStyle.SPREAD)
        card.pack_start(bbox, False, False, 10)

        self.sync_btn = Gtk.Button(label="INICIAR SINCRONIZACIÓN")
        self.sync_btn.get_style_context().add_class("suggested-action")
        self.sync_btn.connect("clicked", self.on_sync_clicked)
        bbox.pack_start(self.sync_btn, True, True, 0)

        help_btn = Gtk.Button(label="AYUDA USB")
        help_btn.connect("clicked", self.show_usb_help)
        bbox.pack_start(help_btn, True, True, 0)

    def log(self, message):
        print(f"[DroidTux] {message}")
        if hasattr(self, 'text_view'):
            GLib.idle_add(self._log_idle, message)

    def _log_idle(self, message):
        buffer = self.text_view.get_buffer()
        buffer.insert(buffer.get_end_iter(), f"> {message}\n")
        # Scroll to bottom
        adj = self.text_view.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())
        return False

    def update_progress(self, text, fraction):
        print(f"[Progress {int(fraction*100)}%] {text}")
        if hasattr(self, 'status_label'):
            GLib.idle_add(self._update_progress_idle, text, fraction)

    def _update_progress_idle(self, text, fraction):
        self.status_label.set_text(text)
        self.progress_bar.set_fraction(fraction)
        return False

    def on_sync_clicked(self, btn):
        self.sync_btn.set_sensitive(False)
        self.text_view.get_buffer().set_text("")
        threading.Thread(target=self.run_sync, daemon=True).start()

    def show_usb_help(self, btn):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Cómo habilitar 'Instalar vía USB'"
        )
        msg = (
            "Si no ves la opción 'Instalar vía USB' en Opciones de Desarrollador:\n\n"
            "1. XIAOMI / MIUI: Debes iniciar sesión en tu Mi Account y tener una tarjeta SIM insertada.\n"
            "2. REALME / OPPO: Activa 'Instalación ADB'.\n"
            "3. OTROS: Busca 'Permitir instalación de apps por ADB'.\n\n"
            "Sin esto, DroidTux no puede obtener los iconos de alta calidad."
        )
        dialog.format_secondary_text(msg)
        dialog.run()
        dialog.destroy()

    def run_adb(self, cmd, serial=None):
        prefix = f"adb -s {serial} " if serial else "adb "
        try:
            res = subprocess.run(f"{prefix}{cmd}", shell=True, capture_output=True, text=True, timeout=20)
            if res.returncode != 0: return f"ERROR: {res.stderr.strip()}"
            return res.stdout.strip()
        except Exception as e: return f"ERROR: {str(e)}"

    def run_sync(self):
        self.update_progress("Buscando dispositivo...", 0.1)
        serial = None
        while not serial:
            output = self.run_adb("devices")
            lines = [l for l in (output or "").splitlines()[1:] if l.strip()]
            devs = [l.split()[0] for l in lines if "\tdevice" in l]
            if devs: serial = devs[0]
            else: 
                self.log("Esperando dispositivo USB...")
                time.sleep(2)
        
        self.log(f"Conectado a {serial}")
        
        # Evitar que el teléfono se suspenda
        self.log("Configurando modo 'Stay Awake'...")
        self.run_adb("shell svc power stayon usb", serial)
        self.run_adb("shell wm dismiss-keyguard", serial)

        self.update_progress("Validando App Puente...", 0.2)
        
        bridge_pkg = "com.droidtux.bridge"
        check = self.run_adb(f"shell pm list packages {bridge_pkg}", serial)
        if bridge_pkg not in check:
            self.log("Instalando Bridge APK...")
            if BRIDGE_APK.exists():
                res = self.run_adb(f"install -g {BRIDGE_APK}", serial)
                if "INSTALL_FAILED_USER_RESTRICTED" in res:
                    self.log("ERROR: Instalación USB bloqueada por el móvil.")
                    GLib.idle_add(self.show_usb_help, None)
                    self.update_progress("Error: Habilita Instalación USB", 0)
                    GLib.idle_add(self.sync_btn.set_sensitive, True)
                    return
            else:
                self.log("Error: No se encuentra el APK del Bridge.")
                GLib.idle_add(self.sync_btn.set_sensitive, True)
                return

        self.update_progress("Sincronizando apps...", 0.4)
        ICONS_DIR.mkdir(parents=True, exist_ok=True)
        DESKTOP_DIR.mkdir(parents=True, exist_ok=True)
        
        # Cargar ajustes actuales antes de generar .desktop
        self.settings = load_settings()
        res_w = self.settings.get("resolution", "1280x720").split('x')[0]
        bitrate = self.settings.get("bitrate", "16M").lower()

        cmd = "shell \"cmd package query-activities --brief -a android.intent.action.MAIN -c android.intent.category.LAUNCHER\""
        pkgs_raw = self.run_adb(cmd, serial)
        packages = list(set([l.split("/")[0].strip() for l in pkgs_raw.splitlines() if "/" in l]))

        for i, pkg in enumerate(packages):
            perc = 0.4 + (0.5 * (i/len(packages)))
            self.update_progress(f"Procesando {pkg}", perc)
            self.log(f"Integrando: {pkg}")
            
            # Extraer icono real usando el bridge (con reintentos)
            self.run_adb(f"shell rm /sdcard/Download/{pkg}.png", serial)
            self.run_adb(f"shell am start-foreground-service -n com.droidtux.bridge/.IconService --es package {pkg}", serial)
            
            icon_path = ICONS_DIR / f"{pkg}.png"
            # Esperar a que el archivo aparezca y tenga tamaño (máximo 3 segundos)
            for _ in range(15):
                size_raw = self.run_adb(f"shell stat -c %s /sdcard/Download/{pkg}.png", serial)
                if size_raw.isdigit() and int(size_raw) > 0:
                    self.run_adb(f"pull /sdcard/Download/{pkg}.png {icon_path}", serial)
                    break
                time.sleep(0.2)
            
            # Obtener nombre real de la app
            name_raw = self.run_adb(f"shell dumpsys package {pkg} | grep -i 'label=' | head -n 1", serial)
            name = name_raw.split("=")[-1].strip() if "label=" in (name_raw or "") else pkg.split('.')[-1].capitalize()
            
            # Construir comando scrcpy con ajustes
            scrcpy_args = f"-s {serial} --start-app={pkg} --window-title=\"{name}\" -m {res_w} -b {bitrate} --always-on-top --stay-awake --power-off-on-close"
            exec_cmd = f"scrcpy {scrcpy_args}"
            
            # Usar ruta absoluta para el icono
            content = f"[Desktop Entry]\nType=Application\nName={name}\nExec={exec_cmd}\nIcon={icon_path.absolute()}\nTerminal=false\n"
            (DESKTOP_DIR / f"droidtux-{pkg}.desktop").write_text(content)

        # Opcional: Aplicar resolución global si se usa SecondScreen o wm density
        self.log("Aplicando ajustes de densidad (DPI)...")
        self.run_adb(f"shell wm density {self.settings['dpi']}", serial)

        subprocess.run(["update-desktop-database", str(DESKTOP_DIR)], capture_output=True)
        self.update_progress("Sincronización completa", 1.0)
        self.log("¡Todo listo! Tus apps ya están en el menú.")
        if hasattr(self, 'sync_btn'):
            GLib.idle_add(self.sync_btn.set_sensitive, True)

import sys
import argparse

def cleanup():
    print("Limpiando aplicaciones de DroidTux...")
    for f in DESKTOP_DIR.glob("droidtux-*.desktop"):
        f.unlink()
    if ICONS_DIR.exists():
        shutil.rmtree(ICONS_DIR)
    subprocess.run(["update-desktop-database", str(DESKTOP_DIR)], capture_output=True)
    print("Limpieza completada.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DroidTux Integrator")
    parser.add_argument("--add", action="store_true", help="Sincronizar automáticamente")
    parser.add_argument("--remove", action="store_true", help="Eliminar aplicaciones")
    args = parser.parse_args()

    if args.remove:
        cleanup()
        sys.exit(0)
    
    app = DroidTuxApp()
    
    if args.add:
        print("Iniciando sincronización automática...")
        # Ejecutamos la lógica de sincronización en un hilo para no bloquear si hubiera GUI,
        # pero en este caso simplemente llamamos a run_sync y cerramos.
        # Para hacerlo bien sin GUI, run_sync no debería depender de widgets.
        # Vamos a llamar a run_sync directamente.
        app.run_sync()
        sys.exit(0)
    else:
        Gtk.main()
