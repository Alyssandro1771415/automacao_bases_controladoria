import os
import platform
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def get_base_dir():
    sistema = platform.system()
    home = str(Path.home())
    if sistema == "Windows":
        desktop = os.path.join(home, "Desktop")
        if os.path.exists(desktop):
            return os.path.join(desktop, "automacao")
        else:
            return os.path.join(home, "automacao")
    elif sistema == "Linux":
        desktop = os.path.join(home, "Desktop")
        if os.path.exists(desktop):
            return os.path.join(desktop, "automacao")
        else:
            return "/opt/automacao"
    elif sistema == "Darwin":
        desktop = os.path.join(home, "Desktop")
        if os.path.exists(desktop):
            return os.path.join(desktop, "automacao")
        else:
            return os.path.join(home, "automacao")
    else:
        return "/opt/automacao"

BASE_DIR = os.getenv("BASE_DIR", get_base_dir())
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", os.path.join(BASE_DIR, "downloads"))
FINAL_DIR = os.getenv("FINAL_DIR", os.path.join(BASE_DIR, "outputs"))
LOG_DIR = os.getenv("LOG_DIR", os.path.join(BASE_DIR, "logs"))
GECKO_DRIVER_PATH = os.getenv("GECKO_DRIVER_PATH")