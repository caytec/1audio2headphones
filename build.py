"""
build.py – Kompiluje app.py do jednoplikowego .exe za pomocą PyInstaller.
Uruchom:  python build.py
"""

import subprocess
import sys
import os
import shutil

# Force UTF-8 output so Polish characters work in CI logs and Windows cp1252 consoles
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

APP_NAME = "1Audio2Headphones"
ENTRY = "app.py"
ICON = None  # ścieżka do .ico jeśli masz, np. "icon.ico"

# Znajdź katalog customtkinter (musi być dołączony jako data)
try:
    import customtkinter
    ctk_path = os.path.dirname(customtkinter.__file__)
except ImportError:
    print("ERROR: customtkinter nie jest zainstalowany. Uruchom najpierw:")
    print("  pip install -r requirements.txt")
    sys.exit(1)

args = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",
    "--windowed",
    "--name", APP_NAME,
    "--add-data", f"{ctk_path};customtkinter",
    "--hidden-import", "soundcard",
    "--hidden-import", "numpy",
    "--hidden-import", "customtkinter",
    "--hidden-import", "tkinter",
    "--hidden-import", "cffi",
    "--collect-all", "customtkinter",
    "--collect-all", "soundcard",
    "--noconfirm",
    "--clean",
]

if ICON and os.path.exists(ICON):
    args += ["--icon", ICON]

args.append(ENTRY)

print("=" * 60)
print(f"  Budowanie: {APP_NAME}.exe")
print("=" * 60)
result = subprocess.run(args)

if result.returncode == 0:
    exe_path = os.path.join("dist", f"{APP_NAME}.exe")
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / 1024 / 1024
        print()
        print("=" * 60)
        print(f"  SUKCES! Plik gotowy:")
        print(f"  {os.path.abspath(exe_path)}  ({size_mb:.1f} MB)")
        print("=" * 60)
    else:
        print("Budowanie zakończone, ale nie znaleziono pliku .exe w dist/")
else:
    print()
    print("=" * 60)
    print("  BŁĄD: Budowanie nie powiodło się.")
    print("  Sprawdź komunikaty powyżej.")
    print("=" * 60)
    sys.exit(1)
