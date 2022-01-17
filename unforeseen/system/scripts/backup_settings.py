import subprocess
import sys, os

from zipfile import ZipFile

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

backup_path = "./storage/backup"

subprocess.call(f"cp -r ./analysis  {backup_path}", shell=True)
subprocess.call(f"cd {backup_path}/ && mkdir cameras", shell=True)
subprocess.call(f"cp -r ./cameras/*.txt {backup_path}/cameras", shell=True)
subprocess.call(f"cp SETUP.yml {backup_path}", shell=True)
subprocess.call(f"cp ModelDescription.md {backup_path}", shell=True)

# Zipping
zipfile_name = "backup.zip"
zipObj = ZipFile(f"{backup_path}/{zipfile_name}", "w")

# Write folders
#for folder in folders:
for folderName, subfolders, filenames in os.walk(backup_path):
   for filename in filenames:
       if filename== zipfile_name:
           continue
       filePath = os.path.join(folderName, filename)
       folderPath = folderName.replace(f"{backup_path}","")
       zipObj.write(filePath, folderPath+"/"+os.path.basename(filePath))

# close the Zip File
zipObj.close()
