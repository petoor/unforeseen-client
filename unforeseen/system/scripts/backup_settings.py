import subprocess
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

subprocess.call(f"cp -r ./analysis ./storage/backup", shell=True)
subprocess.call(f"cp -r ./cameras/*.txt ./storage/backup", shell=True)
subprocess.call(f"cp SETUP.yml ./storage/backup", shell=True)
subprocess.call(f"cp ModelDescription.md ./storage/backup", shell=True)
