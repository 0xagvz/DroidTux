import os
import subprocess
import shutil
import tempfile
import argparse
import logging
import threading
import time
import sys
import signal
import re
from pathlib import Path
from io import BytesIO
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import scrolledtext

# Intentar importar Androguard con soporte para v3 y v4
try:
    from androguard.core.apk import APK
except ImportError:
    try:
        from androguard.core.bytecodes.apk import APK
    except ImportError:
        logging.error("No se pudo importar Androguard.")
        APK = None

# Directorios según estándar XDG
ICONS_DIR = Path.home() / ".local/share/icons/android_apps"
DESKTOP_DIR = Path.home() / ".local/share/applications"

# Ruta de scrcpy
SCRCPY_PATH = "/usr/local/bin/scrcpy"
if not os.path.exists(SCRCPY_PATH):
    SCRCPY_PATH = "scrcpy"

PLAY_STORE_URL = "https://play.google.com/store/apps/details?id=com.farmerbb.secondscreen.free"
QR_API_URL = "https://api.qrserver.com/v1/create-qr-code/?size=200x200&data="

class DroidTuxGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DroidTux - Integrador de Android")
        self.root.geometry("800x600")
        self.root.configure(bg="#2e3440")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.main_frame = tk.Frame(root, bg="#2e3440")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.text_area = scrolledtext.ScrolledText(self.main_frame, wrap=tk.WORD, width=85, height=20, 
                                                 bg="#3b4252", fg="#eceff4", font=("Monospace", 10))
        self.text_area.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        self.status_label = tk.Label(self.main_frame, text="Iniciando...", bg="#2e3440", fg="#88c0d0", font=("Sans", 11, "bold"))
        self.status_label.pack(pady=5)

        self.close_btn = tk.Button(self.main_frame, text="Cerrar", command=self.on_close, state=tk.DISABLED,
                                 bg="#4c566a", fg="#eceff4", relief=tk.FLAT, padx=20, pady=8)
        self.close_btn.pack(pady=10)

        self.selected_device = None
        self.device_event = threading.Event()
        self.qr_photo = None

    def log(self, message):
        self.text_area.insert(tk.END, f"{message}\n")
        self.text_area.see(tk.END)
        self.root.update_idletasks()

    def set_status(self, status, color="#88c0d0"):
        self.status_label.config(text=status, fg=color)
        self.root.update_idletasks()

    def show_secondscreen_help(self):
        help_win = tk.Toplevel(self.root)
        help_win.title("SecondScreen Requerido")
        help_win.geometry("500x650")
        help_win.configure(bg="#3b4252")
        help_win.transient(self.root)
        help_win.grab_set()
        tk.Label(help_win, text="¡Falta SecondScreen!", bg="#3b4252", fg="#bf616a", font=("Sans", 14, "bold")).pack(pady=10)
        instructions = (
            "Para un modo escritorio real necesitas instalar SecondScreen.\n\n"
            "1. Escanea el código QR para descargar la app.\n"
            "2. Abre la app y crea un perfil llamado exactly 'Linux'.\n"
            "3. Configura la resolución a 1920x1080 (o similar).\n"
            "4. Una vez configurado, pulsa 'LISTO' para continuar."
        )
        tk.Label(help_win, text=instructions, bg="#3b4252", fg="#eceff4", justify=tk.LEFT, padx=20).pack(pady=10)
        try:
            resp = requests.get(QR_API_URL + PLAY_STORE_URL, timeout=5)
            if resp.status_code == 200:
                qr_img = Image.open(BytesIO(resp.content))
                self.qr_photo = ImageTk.PhotoImage(qr_img)
                tk.Label(help_win, image=self.qr_photo, bg="#3b4252").pack(pady=10)
        except: pass
        tk.Button(help_win, text="¡LISTO, YA LO TENGO!", command=help_win.destroy, 
                             bg="#a3be8c", fg="#2e3440", font=("Sans", 10, "bold"), padx=20, pady=10).pack(pady=20)

    def select_device_dialog(self, devices):
        dialog = tk.Toplevel(self.root)
        dialog.title("Seleccionar Dispositivo")
        dialog.geometry("450x350")
        dialog.configure(bg="#3b4252")
        dialog.transient(self.root)
        dialog.grab_set()
        tk.Label(dialog, text="Varios dispositivos detectados:", bg="#3b4252", fg="#eceff4", font=("Sans", 11, "bold")).pack(pady=15)
        lb = tk.Listbox(dialog, bg="#434c5e", fg="#eceff4", font=("Monospace", 11), selectbackground="#88c0d0")
        for d in devices: lb.insert(tk.END, d)
        lb.pack(padx=30, pady=10, fill=tk.BOTH, expand=True)
        def on_select():
            selection = lb.curselection()
            if selection:
                self.selected_device = devices[selection[0]]
                self.device_event.set()
                dialog.destroy()
        tk.Button(dialog, text="CONECTAR", command=on_select, bg="#88c0d0", fg="#2e3440", font=("Sans", 10, "bold"), padx=20).pack(pady=20)

    def on_close(self):
        self.root.destroy()
        os._exit(0)

    def finish(self):
        self.close_btn.config(state=tk.NORMAL, bg="#a3be8c", fg="#2e3440")
        self.set_status("¡Proceso finalizado!", color="#a3be8c")

def run_adb(command, timeout=30):
    try:
        result = subprocess.run(f"adb {command}", shell=True, check=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip()
    except Exception: return None

def cleanup_apps():
    print("[!] Limpiando archivos del sistema...")
    for f in DESKTOP_DIR.glob("droidtux-*.desktop"):
        try: f.unlink()
        except: pass
    if ICONS_DIR.exists():
        try: shutil.rmtree(ICONS_DIR)
        except: pass
    subprocess.run(["update-desktop-database", str(DESKTOP_DIR)], capture_output=True)

def setup_android_desktop(serial, gui):
    gui.log(f"Optimizando entorno Android en {serial}...")
    run_adb(f"-s {serial} shell wm dismiss-keyguard")
    run_adb(f"-s {serial} shell svc power stayon usb")
    pkgs = run_adb(f"-s {serial} shell pm list packages com.farmerbb.secondscreen.free")
    if "com.farmerbb.secondscreen.free" not in (pkgs or ""):
        gui.log("[!] SecondScreen no detectada. Mostrando ayuda...")
        gui.root.after(0, gui.show_secondscreen_help)
        while any(isinstance(w, tk.Toplevel) and w.title() == "SecondScreen Requerido" for w in gui.root.winfo_children()):
            time.sleep(0.5)
    
    run_adb(f"-s {serial} shell pm grant com.farmerbb.secondscreen.free android.permission.WRITE_SECURE_SETTINGS")
    gui.log("Invocando perfil de SecondScreen 'Linux'...")
    run_adb(f"-s {serial} shell am broadcast -a com.farmerbb.secondscreen.free.ENABLE_PROFILE --es com.farmerbb.secondscreen.free.PROFILE_NAME 'Linux'")
    time.sleep(4)

def scrape_playstore_icon(package, gui):
    url = f"https://play.google.com/store/apps/details?id={package}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            img_tag = soup.find('img', alt='Icon image') or soup.find('img', itemprop='image')
            img_url = img_tag.get('src') or img_tag.get('data-src') if img_tag else None
            if not img_url:
                meta_img = soup.find('meta', property='og:image')
                img_url = meta_img['content'] if meta_img else None
            if img_url:
                if img_url.startswith('//'): img_url = 'https:' + img_url
                img_url = img_url.split('=')[0]
                img_resp = requests.get(img_url, timeout=8)
                if img_resp.status_code == 200:
                    img = Image.open(BytesIO(img_resp.content)).convert("RGBA")
                    img = img.resize((512, 512), Image.Resampling.LANCZOS)
                    out = BytesIO(); img.save(out, format='PNG')
                    return out.getvalue()
    except Exception: pass
    return None

def extract_best_icon(serial, package, gui, temp_dir):
    """Extrae el icono usando la App Puente si existe, o fallback local"""
    app_name = package.split('.')[-1].capitalize()
    
    # 1. INTENTO CON APP PUENTE (La forma profesional)
    bridge_service = "com.droidtux.bridge/.IconService"
    remote_path = f"/sdcard/Download/{package}.png"
    
    # Intentar obtener el nombre real de la app via ADB primero
    name_out = run_adb(f"-s {serial} shell \"dumpsys package {package} | grep -i 'label='\"")
    if name_out:
        # Extraer el valor de label=...
        import re
        match = re.search(r'label=([\w\s]+)', name_out)
        if match: app_name = match.group(1).strip()

    # Lanzar servicio de extracción de la App Puente
    run_adb(f"-s {serial} shell am start-foreground-service -n {bridge_service} --es package {package}")
    
    # Esperar a que el archivo aparezca (máximo 2 segundos)
    for _ in range(10):
        time.sleep(0.2)
        check = run_adb(f"-s {serial} shell ls {remote_path}")
        if check and "No such file" not in check:
            local_icon_path = os.path.join(temp_dir, f"{package}_bridge.png")
            run_adb(f"-s {serial} pull {remote_path} {local_icon_path}")
            if os.path.exists(local_icon_path):
                with open(local_icon_path, 'rb') as f:
                    return app_name, f.read()

    # 2. FALLBACK: MÉTODO LOCAL (Si el bridge no está o falla)
    web_icon = scrape_playstore_icon(package, gui)
    if web_icon: return app_name, web_icon

    path_out = run_adb(f"-s {serial} shell pm path {package}")
    if path_out:
        apk_remote = path_out.splitlines()[0].replace("package:", "").strip()
        apk_local = os.path.join(temp_dir, f"{package}.apk")
        run_adb(f"-s {serial} pull {apk_remote} {apk_local}")
        
        a = None
        icon_res_name = "ic_launcher"
        if APK:
            try:
                a = APK(apk_local)
                app_name = a.get_app_name() or app_name
                manifest_xml = a.get_android_manifest_axml().get_xml_obj()
                icon_attr = manifest_xml.get('{http://schemas.android.com/apk/res/android}icon')
                if icon_attr and '/' in icon_attr: icon_res_name = icon_attr.split('/')[-1]
            except: pass

        if a:
            try:
                import zipfile
                with zipfile.ZipFile(apk_local, 'r') as z:
                    all_files = z.namelist()
                    densities = ['xxxhdpi', 'xxhdpi', 'xhdpi', 'hdpi']
                    for d in densities:
                        matches = [f for f in all_files if d in f and f.endswith('.png') and icon_res_name in f and "anydpi" not in f]
                        if matches:
                            best = sorted(matches, key=lambda x: z.getinfo(x).file_size)[-1]
                            return app_name, z.read(best)
            except: pass
    return app_name, None

def check_adb_status(gui):
    gui.log("Esperando conexión ADB...")
    last_state = None
    while True:
        output = run_adb("devices")
        if not output:
            if last_state != "no_server": gui.log("Iniciando ADB..."); last_state = "no_server"
            time.sleep(2); continue
        lines = [l for l in output.splitlines()[1:] if l.strip()]
        if not lines:
            if last_state != "no_usb": gui.set_status("Buscando móvil...", color="#ebcb8b"); last_state = "no_usb"
            time.sleep(2); continue
        authorized = [line.split()[0] for line in lines if "\tdevice" in line]
        if authorized:
            if len(authorized) == 1: return authorized[0]
            else:
                gui.root.after(0, lambda: gui.select_device_dialog(authorized))
                gui.device_event.wait(); return gui.selected_device
        time.sleep(2)

def monitor_disconnection(serial, gui):
    while True:
        time.sleep(4)
        output = run_adb("devices")
        if not output or serial not in output:
            cleanup_apps(); gui.finish(); break

def worker_integration(gui):
    serial = check_adb_status(gui)
    if not serial: return
    threading.Thread(target=monitor_disconnection, args=(serial, gui), daemon=True).start()
    setup_android_desktop(serial, gui)
    gui.log(f"Buscando apps visibles en {serial}...")
    cmd_query = f"-s {serial} shell \"cmd package query-activities --brief -a android.intent.action.MAIN -c android.intent.category.LAUNCHER\""
    output = run_adb(cmd_query)
    raw_apps = (output or "").splitlines()
    packages = []
    for line in raw_apps:
        if "/" in line:
            pkg = line.split("/")[0].strip()
            if pkg not in packages and not any(x in pkg for x in ["com.android.settings", "com.google.android.setupwizard"]):
                packages.append(pkg)
    if not packages: gui.finish(); return
    gui.log(f"Integrando {len(packages)} aplicaciones.")
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    DESKTOP_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp_dir:
        for i, pkg in enumerate(packages):
            gui.log(f"[{i+1}/{len(packages)}] {pkg}")
            name, icon = extract_best_icon(serial, pkg, gui, temp_dir)
            icon_path = ICONS_DIR / f"{pkg}.png"
            if icon:
                with open(icon_path, 'wb') as f: f.write(icon)
            else:
                icon_path = "android"
                
                # CALIDAD TOP 16:9 CORREGIDA: Sintaxis scrcpy 3.0+ es resolución/dpi
                # TOP QUALITY 16:9 FIXED: scrcpy 3.0+ syntax is resolution/dpi
                exec_cmd = f"{SCRCPY_PATH} -s {serial} --new-display=1280x720/240 --video-bit-rate=16M --start-app={pkg} --window-title=\"{name}\" --orientation=0 --window-width=1280 --window-height=720"
                
                content = f"[Desktop Entry]\nVersion=1.0\nType=Application\nName={name}\nExec={exec_cmd}\nIcon={icon_path}\nTerminal=false\nCategories=Utility;Phone;X-Android;\n"
                (DESKTOP_DIR / f"droidtux-{pkg}.desktop").write_text(content)
    subprocess.run(["update-desktop-database", str(DESKTOP_DIR)], capture_output=True)
    gui.log("\n¡Integración completada!"); gui.finish()

def signal_handler(sig, frame):
    cleanup_apps(); os._exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    parser = argparse.ArgumentParser()
    parser.add_argument("--add", action="store_true")
    parser.add_argument("--remove", action="store_true")
    args = parser.parse_args()
    if args.remove: cleanup_apps(); return
    if args.add:
        root = tk.Tk()
        gui = DroidTuxGUI(root)
        threading.Thread(target=worker_integration, args=(gui,), daemon=True).start()
        try: root.mainloop()
        except KeyboardInterrupt: signal_handler(None, None)

if __name__ == "__main__":
    main()
