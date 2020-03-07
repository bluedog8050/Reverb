import subprocess
import sys

packages = [
    'discord',
    'wikia'
]

for p in packages:
    subprocess.check_call([sys.executable, "-m", "pip", "install", p])
