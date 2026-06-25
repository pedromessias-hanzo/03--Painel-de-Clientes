import os
import subprocess
import time
import sys

artifacts_dir = r"C:\Users\Krypt\.gemini\antigravity\brain\31ae2eed-7df5-4552-9dc3-18c1232d4d3b"
workspace_dir = r"c:\Users\Krypt\OneDrive\01 - Consultorias\08 - Soul Governance\04 - Hanzo\01 - Finanças\03 -Painel de Clientes"

edge_paths = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
]

edge_exe = None
for p in edge_paths:
    if os.path.exists(p):
        edge_exe = p
        break

if not edge_exe:
    print("Edge not found!")
    sys.exit(1)

# Start Streamlit on 8502
print("Starting Streamlit...")
cmd_streamlit = ["streamlit", "run", "app.py", "--server.port=8502", "--server.headless=true"]
process = subprocess.Popen(cmd_streamlit, cwd=workspace_dir)

time.sleep(8)

try:
    output_path = os.path.join(artifacts_dir, "test_page1.png")
    
    # Try with timeout and virtual-time-budget
    cmd_screenshot = [
        edge_exe,
        "--headless",
        f"--screenshot={output_path}",
        "--window-size=1440,1100",
        "--disable-gpu",
        "--hide-scrollbars",
        "--timeout=10000",
        "--virtual-time-budget=10000",
        "http://localhost:8502/?page=Vis%C3%A3o+Executiva"
    ]
    
    print("Running Edge screenshot command...")
    subprocess.run(cmd_screenshot, check=True)
    
    if os.path.exists(output_path):
        size = os.path.getsize(output_path)
        print(f"Screenshot taken! File path: {output_path} | Size: {size} bytes")
    else:
        print("Screenshot file was not created!")
finally:
    print("Stopping Streamlit...")
    process.terminate()
    process.wait()
