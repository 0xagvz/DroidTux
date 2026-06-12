import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf
import json
import os
import subprocess
from pathlib import Path

SETTINGS_DIR = Path.home() / ".config/droidtux"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"
BASE_DIR = Path(__file__).resolve().parent
LOCAL_LOGO = BASE_DIR / "droidtux.png"
LOGO_PATH = Path.home() / ".local/share/icons/droidtux.png"

if not LOGO_PATH.exists() and LOCAL_LOGO.exists():
    LOGO_PATH = LOCAL_LOGO

DEFAULT_SETTINGS = {
    "resolution": "1280x720",
    "dpi": 240,
    "bitrate": "16M"
}

def load_settings():
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return {**DEFAULT_SETTINGS, **json.load(f)}
        except: pass
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

class DroidTuxSettingsApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Ajustes de DroidTux")
        self.set_default_size(450, 600)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        self.settings = load_settings()
        self.setup_ui()
        self.show_all()

    def setup_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(20)
        vbox.set_margin_bottom(20)
        vbox.set_margin_start(20)
        vbox.set_margin_end(20)
        self.add(vbox)

        # Logo
        if LOGO_PATH.exists():
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(LOGO_PATH), 80, 80, True)
            img = Gtk.Image.new_from_pixbuf(pixbuf)
            vbox.pack_start(img, False, False, 0)

        title = Gtk.Label(label="Panel de Control DroidTux")
        title.set_markup("<span size='large' weight='bold'>Panel de Control DroidTux</span>")
        vbox.pack_start(title, False, False, 10)

        grid = Gtk.Grid(column_spacing=15, row_spacing=15)
        grid.set_halign(Gtk.Align.CENTER)
        vbox.pack_start(grid, True, True, 0)

        # Resolution
        grid.attach(Gtk.Label(label="Resolución:", xalign=1), 0, 0, 1, 1)
        self.res_combo = Gtk.ComboBoxText()
        res_opts = ["1920x1080", "1600x900", "1280x720", "1024x576", "800x450"]
        for opt in res_opts: self.res_combo.append_text(opt)
        self.res_combo.set_active(res_opts.index(self.settings["resolution"]) if self.settings["resolution"] in res_opts else 2)
        grid.attach(self.res_combo, 1, 0, 1, 1)

        # DPI
        grid.attach(Gtk.Label(label="DPI (Densidad):", xalign=1), 0, 1, 1, 1)
        self.dpi_adj = Gtk.Adjustment(value=self.settings["dpi"], lower=120, upper=480, step_increment=10, page_increment=40, page_size=0)
        self.dpi_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.dpi_adj)
        self.dpi_scale.set_size_request(200, -1)
        grid.attach(self.dpi_scale, 1, 1, 1, 1)

        # Bitrate
        grid.attach(Gtk.Label(label="Bitrate:", xalign=1), 0, 2, 1, 1)
        self.bit_combo = Gtk.ComboBoxText()
        bit_opts = ["4M", "8M", "16M", "32M"]
        for opt in bit_opts: self.bit_combo.append_text(opt)
        self.bit_combo.set_active(bit_opts.index(self.settings["bitrate"]) if self.settings["bitrate"] in bit_opts else 2)
        grid.attach(self.bit_combo, 1, 2, 1, 1)

        # Save Button
        save_btn = Gtk.Button(label="GUARDAR CAMBIOS")
        save_btn.connect("clicked", self.on_save_clicked)
        save_btn.get_style_context().add_class("suggested-action")
        vbox.pack_start(save_btn, False, False, 10)

        # Help Buttons
        help_label = Gtk.Label(label="Ayuda y Configuración")
        help_label.set_markup("<span weight='bold'>Ayuda y Configuración</span>")
        vbox.pack_start(help_label, False, False, 10)

        h_bbox = Gtk.ButtonBox(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        vbox.pack_start(h_bbox, False, False, 0)

        btns = [
            ("Depuración ADB", self.show_adb_help),
            ("SecondScreen", self.show_ss_help),
            ("Instalación USB", self.show_usb_help)
        ]
        for label, cmd in btns:
            b = Gtk.Button(label=label)
            b.connect("clicked", cmd)
            h_bbox.add(b)

    def on_save_clicked(self, btn):
        self.settings["resolution"] = self.res_combo.get_active_text()
        self.settings["dpi"] = int(self.dpi_adj.get_value())
        self.settings["bitrate"] = self.bit_combo.get_active_text()
        save_settings(self.settings)
        
        dialog = Gtk.MessageDialog(transient_for=self, flags=0, message_type=Gtk.MessageType.INFO,
                                  buttons=Gtk.ButtonsType.OK, text="Ajustes Guardados")
        dialog.format_secondary_text("Se aplicarán en la próxima conexión.")
        dialog.run()
        dialog.destroy()

    def show_help(self, title, content):
        dialog = Gtk.MessageDialog(transient_for=self, flags=0, message_type=Gtk.MessageType.INFO,
                                  buttons=Gtk.ButtonsType.OK, text=title)
        dialog.format_secondary_text(content)
        dialog.run()
        dialog.destroy()

    def show_adb_help(self, btn):
        self.show_help("Depuración ADB", 
            "1. Ve a 'Ajustes' en tu móvil.\n"
            "2. 'Información del teléfono' -> Pulsa 7 veces en 'Número de compilación'.\n"
            "3. Vuelve atrás -> 'Sistema' -> 'Opciones de desarrollador'.\n"
            "4. Activa 'Depuración por USB'.")

    def show_ss_help(self, btn):
        self.show_help("SecondScreen", 
            "1. Instala SecondScreen desde la Play Store.\n"
            "2. Crea un nuevo perfil llamado exactamente 'Linux'.\n"
            "3. Configura la resolución a 1920x1080 y la densidad a 240.")

    def show_usb_help(self, btn):
        self.show_help("Instalación USB", 
            "En móviles Xiaomi/MIUI:\n\n1. Opciones de desarrollador -> Activa 'Instalar vía USB'.\n2. Puede requerir Mi Account.")

if __name__ == "__main__":
    app = DroidTuxSettingsApp()
    Gtk.main()
