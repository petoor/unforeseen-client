import sys, os
import glob
import time
import re
import psutil
import logging 

from unforeseen.config import setup_loader

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

setup = setup_loader()

local_storage = setup.get("storage").get("local_storage")
path = local_storage.get("path")
folders_to_delete = local_storage.get("folders_to_delete")
delete_time = time.time() - date_to_seconds(local_storage.get("delete_time"))
delete_space = local_storage.get("delete_space")

### Delete old files due to time ###
files = []
for folder in folders_to_delete:
    files.append(glob.glob(path+"/"+folder+"/*"))

files = [item for sublist in files for item in sublist]
files.sort(key=os.path.getmtime)

for f in files:
    file_time = os.path.getmtime(f)
    if file_time < delete_time:
        os.remove(f)
        logging.info(f"Deleted file : {f} due to time")

### Delete due to storage ###
files = []
for folder in folders_to_delete:
    files.append(glob.glob(path+"/"+folder+"/*"))

files = [item for sublist in files for item in sublist]
files.sort(key=os.path.getmtime)

hdd = psutil.disk_usage(path)
used_space = hdd.used / hdd.total
space = re.findall(r'\b\d+\b', delete_space)
lower_bound = float(space[0])*0.01
upper_bound = float(space[1])*0.01
if used_space > upper_bound:
    for f in files:
        os.remove(f)
        hdd = psutil.disk_usage(path)
        used_space = hdd.used / hdd.total
        logging.info(f"Deleted file : {f} due to space")
        if used_space < lower_bound:
            break
