import urllib.request
import os
import subprocess
import time
import sys

workspace_dir = r"c:\Users\Krypt\OneDrive\01 - Consultorias\08 - Soul Governance\04 - Hanzo\01 - Finanças\03 -Painel de Clientes"

# Start Streamlit on 8503
cmd = ["streamlit", "run", "app.py", "--server.port=8503", "--server.headless=true"]
process = subprocess.Popen(cmd, cwd=workspace_dir)

time.sleep(5)

try:
    url = "http://localhost:8503/"
    print("Fetching URL:", url)
    response = urllib.request.urlopen(url)
    html = response.read().decode('utf-8')
    print("Response Length:", len(html))
    print("Response Sample (first 1000 chars):")
    print(html[:1000])
finally:
    process.terminate()
    process.wait()
