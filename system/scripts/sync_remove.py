# The script will sync files before removing them, if sync is not needed. The files are simply deleted.
# TODO: Sync

import sys, os
import glob
import time
import re
import psutil
import logging 
from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient

# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unforeseen-client.config import setup_loader

def date_to_seconds(time):
    def _intervals_to_seconds(date):
        intervals = (
        ('w', 604800),  # 60 * 60 * 24 * 7
        ('d', 86400),    # 60 * 60 * 24
        ('h', 3600),    # 60 * 60
        ('m', 60),
        ('s', 1),)
        for interval in intervals:
            if date == interval[0]:
                converted_time = interval[1]         
                break
        return converted_time

    temp = re.compile("([0-9]+)([a-zA-Z]+)")
    time = temp.match(time).groups()
    seconds = int(time[0])*_intervals_to_seconds(time[1])
    return seconds

def sync_files(file, remote_url,  remote_folder, username="pi", password="raspberry", port=22):
    try:
        ssh = SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.connect(remote_url, port=port,username=username,password=password, look_for_keys=False)
        scp = SCPClient(ssh.get_transport())
        scp.put(files=file, remote_path=remote_folder)
        scp.close()
    except Exception:
        logging.critical(f"Could not sync files to remove {remote_url}")

setup = setup_loader()

local_storage = setup.get("storage").get("local_storage")
path = local_storage.get("path")
folders_to_delete = local_storage.get("folders_to_delete")
delete_time = time.time() - date_to_seconds(local_storage.get("delete_time"))
delete_space = local_storage.get("delete_space")

sync = list(setup.get("storage").keys())
sync.remove("local_storage")
### Delete old files due to time ###
files = []
for folder in folders_to_delete:
    files.append(glob.glob(path+"/"+folder+"/*"))

files = [item for sublist in files for item in sublist]
files.sort(key=os.path.getmtime)

for file in files:
    file_time = os.path.getmtime(file)
    if file_time < delete_time:
        for remote in sync:
            if setup.get("storage").get(remote).get("use_sync",False):
                remote = setup.get("storage").get(remote)
                sync_files(file, remote_url=remote.get("url"),remote_folder=remote.get("path"),
                                 username=remote.get("user"), password=remote.get("pass"),
                                 port=remote.get("port"))
        os.remove(file)
        logging.warning(f"Deleted file : {file} due to time")

### Delete due to storage ###
files = []
for folder in folders_to_delete:
    files.append(glob.glob(path+"/"+folder+"/*"))

files = [item for sublist in files for item in sublist]
files.sort(key=os.path.getmtime)

hdd = psutil.disk_usage(path)
used_space = hdd.used / hdd.total
space = re.findall(r'\b\d+\b', delete_space)
lower_bound = int(space[0])*0.01
upper_bound = int(space[1])*0.01
print(used_space)
if used_space > upper_bound:
    for file in files:
        for remote in sync:
            if setup.get("storage").get(remote).get("use_sync",False):
                remote = setup.get("storage").get(remote)
                sync_files(file, remote_url=remote.get("url"),remote_folder=remote.get("path"),
                                 username=remote.get("user"), password=remote.get("pass"),
                                 port=remote.get("port"))
        os.remove(file)
        hdd = psutil.disk_usage(path)
        used_space = hdd.used / hdd.total
        logging.warning(f"Deleted file : {file} due to space")
        if used_space < lower_bound:
            break