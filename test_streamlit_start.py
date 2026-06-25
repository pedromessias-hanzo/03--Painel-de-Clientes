import os
import subprocess
import time

workspace_dir = r"c:\Users\Krypt\OneDrive\01 - Consultorias\08 - Soul Governance\04 - Hanzo\01 - Finanças\03 -Painel de Clientes"

cmd = ["streamlit", "run", "app.py", "--server.port=8502", "--server.headless=true"]
print("Running command:", " ".join(cmd))

process = subprocess.Popen(cmd, cwd=workspace_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# Wait 5 seconds and read outputs
time.sleep(5)

# Check if process is still running
poll = process.poll()
if poll is not None:
    print(f"Process exited with code: {poll}")
    stdout, stderr = process.communicate()
    print("--- STDOUT ---")
    print(stdout)
    print("--- STDERR ---")
    print(stderr)
else:
    print("Process is running! Reading current stdout...")
    # Read whatever is available in stdout without blocking
    import select
    if select.select([process.stdout], [], [], 1.0)[0]:
        print(process.stdout.readline())
        print(process.stdout.readline())
    process.terminate()
