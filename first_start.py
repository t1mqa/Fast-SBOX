import subprocess
import sys
from pathlib import Path

# Создаем четыре необходимых файла
Path("privatekeys.txt").touch(exist_ok=True)
Path("proxies.txt").touch(exist_ok=True)
Path("results.txt").touch(exist_ok=True)
Path("unbanned.txt").touch(exist_ok=True)

# Устанавливаем зависимости из файла
subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
