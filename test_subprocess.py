import subprocess
import sys

tess_path = r"H:\بروجكت برنامج OCR\dist\Portable_SmartDocConverter\tesseract\tesseract.exe"

try:
    print("Testing direct subprocess call...")
    out = subprocess.check_output([tess_path, "--list-langs"], stderr=subprocess.STDOUT)
    print("Success:")
    print(out.decode('utf-8', errors='ignore'))
except Exception as e:
    print("Failed:", type(e), str(e))
    import traceback
    traceback.print_exc()

import shutil
print("shutil.which:", shutil.which(tess_path))
