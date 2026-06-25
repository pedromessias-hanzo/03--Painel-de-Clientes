import os
import sys

artifacts_dir = r"C:\Users\Krypt\.gemini\antigravity\brain\31ae2eed-7df5-4552-9dc3-18c1232d4d3b"
p = os.path.join(artifacts_dir, "test_page1.png")

if not os.path.exists(p):
    print("Image not found!")
    sys.exit(1)

try:
    from PIL import Image
    im = Image.open(p)
    print("Image properties:")
    print("  Format:", im.format)
    print("  Size:", im.size)
    print("  Mode:", im.mode)
    
    # Check if the image is blank (all white or all transparent)
    # Get distinct colors
    colors = im.getcolors(maxcolors=256)
    if colors:
        print("  Distinct colors found (max 256):", len(colors))
        print("  Colors sample:", colors[:5])
    else:
        print("  More than 256 distinct colors found.")
except Exception as e:
    print("Error inspecting with Pillow:", e)
    # Fallback checking file header
    with open(p, 'rb') as f:
        header = f.read(20)
        print("File header bytes:", header)
