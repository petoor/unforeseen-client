import os, sys
import pathlib
import re
import yaml
import pdb
import subprocess
from subprocess import Popen, PIPE
from getmac import get_mac_address

# TODO, Running Popen with shell=True is discuraged, refactor to run without.

setup = {}

### Device ###
# Linux has the convension that camera0 is the acutal feed and 1 is the metadata
# Therefore we filter out all the odd numbered video finds.
# Name of the device / application.

device_name = "device-name"

process = Popen(["cat /proc/device-tree/model"], stdout=PIPE, stderr=PIPE, shell=True)
stdout, stderr = process.communicate()
stdout = stdout.decode("utf-8")
if "nano" in stdout.lower():
    device_type = "NANO"
elif "xavier" in stdout.lower():
    device_type = "XAVIER" # This line is untestet, since i do not have access to an xavier.
else:
    device_type = "PC"

device_mode = "development" # development, production, etc..

# Connected cameras
process = Popen(["ls /dev/video*"], stdout=PIPE, stderr=PIPE, shell=True)
stdout, stderr = process.communicate()
stdout = stdout.decode("utf-8").split("\n")
cameras = []

for camera in stdout:
        if re.match(".*[02468]$", camera):
          cameras.append(camera)

# We only keep the first resolution this setting needs to be tweaked by the user.
# Can be found by running v4l2-ctl --device=/dev/video0 --list-formats-ext
# For the html page, the first camera resolution is used for the window.

camera_list = []
for camera in cameras:
    process = Popen([f"v4l2-ctl --device={camera} --list-formats-ext"], stdout=PIPE, stderr=PIPE, shell=True)
    stdout, stderr = process.communicate()
    stdout = stdout.decode("utf-8").split("\n\t\t")
    #TODO: Improve this fps, width and height could be wrong if format is mjpeg
    for idx, line in enumerate(stdout):
        if "MJPG" in line:
            camera_format = "image/jpeg"
            break
        else:
            camera_format = "video/x-raw"

    fps = int(float(stdout[2].split("(")[-1].replace(" fps)","")))
    width = int(stdout[1].split(" ")[-1].split("x")[0])
    height = int(stdout[1].split(" ")[-1].split("x")[1])
    camera_list.append([{f"{camera}":{"camera_format":camera_format,"framerate": fps, "width": width, "height": height, "bitrate": 2048}}])
    subprocess.call(f"v4l2-ctl --device={camera} --list-ctrls > cameras/{camera.split('/')[-1]}.txt", shell=True)


camera_list = [item for sublist in camera_list for item in sublist]
setup.update({"cameras": camera_list})

# Ipv4 
# We get the MAC address of the network card, it will either be wifi or ethernet depending on the connection
try:
    ip = re.search(re.compile(r'(?<=inet )(.*)(?=\/)', re.M), os.popen('ip addr show eth0').read()).groups()[0]
    mac = get_mac_address(interface="eth0")
except:
    try:
        print("Ethernet cablet not connectet, using wireless IP instead")
        ip = re.search(re.compile(r'(?<=inet )(.*)(?=\/)', re.M), os.popen('ip addr show wlp4s0').read()).groups()[0]
        mac = get_mac_address(interface="wlp4s0")
    except:
        try:
            ip = re.search(re.compile(r'(?<=inet )(.*)(?=\/)', re.M), os.popen('ip addr show wlan0').read()).groups()[0]
            mac = get_mac_address(interface="wlan0")
        except:
            ip = "Not_connected_to_internet"
            mac = "Not_connected_to_internet"
   

### server ###
hls_sink_port = 8080
udp_sink_port = 8554

### InfluxDB ###
influxdb_port = 8086
token =  "inset_token_from_influxdb_here"
org = "inset_org_here"
bucket = "inset_bucket_name_here"
influx_ip = ".".join(ip.split(".")[:-1])+"._insert_last_numbers"

### Output signal ###
# The following is an example
# Might be a seperate script since it is so dependent on the use case
output_protocol = "GPIO" # Http, GPIO etc...
output_pin = 8

### Input signal ###
# The following is an example
# Might be a seperate script since it is so dependent on the use case
input_protocol = "GPIO" # Http, GPIO etc...
input_pin = 12

### Notification ###
# How we notify from the AI model.
email = None

### Storage ###
# The following folders might not be appiciable, however they form the base for a CV 
# The analysis folder contains the data basis for the CV model used.
# We see if there is an external drive (e.g USB flash drive) is plugged in.
# If it exists we use that as root.
# It is bad practice to continiously read / write to a SD card, so an USB drive is preferable.
# However, if none exists, we use the root dir.


process = Popen([f"ls /media/{os.environ.get('USER')}"], stdout=PIPE, stderr=PIPE, shell=True)
stdout, stderr = process.communicate()
stdout = stdout.decode("utf-8").split("\n")[0]

root_dir = os.getcwd() # The storage folder should be symlinked to USB storage
local_storage_path = root_dir+"/storage"
streaming = "streaming" # Folder where the camera feed being streamed is stored, the feed gets quickly deleted.
images_dir = "images" # Images of particular interest, e.g. saved imaged of feed when anormality is detected.
training_dir = "training_data" # Images / videos used for training the analysis model
test_dir = "test_data" # Images / videos used for training the analysis model
recordings_dir = "recordings" # All recordings, normally the majoriy of data is useless.
backup_dir = "backup" # All recordings, normally the majoriy of data is useless.
logging_dir = "logging" # All logs.

for path in [local_storage_path, streaming, recordings_dir, images_dir, training_dir, test_dir, backup_dir, logging_dir]:
    pathlib.Path(local_storage_path+"/"+path).mkdir(parents=True, exist_ok=True) 

# We create an empty file with the device name and mac address in order to 
# tell which device the data comes from.

f = open(f"{local_storage_path}/device_info.txt", "w")
f.write(f"Device name : {device_name} \n")
f.write(f"MAC address : {mac}")
f.close()

# If we are about to run out of diskspace, we need to either sync with cloud storage,
# and / or delete local files. We can either delete files based on harddisk space
# avaiable, or their date (e.g delete files older than 30 days).
# The delete script deletes everything in the folders_to_delete older than delete_time
# and deletes in chronological order files when the space hits delete_space upper value and
# deletes files until the harddisk pace reaches the lower value. Which means if a lot of files 
# are saved to storage, we might not keep files for the duration of delete_time.
# One minute of video takes approx 5 mb of space, so on a 64gb sd card we can store 7 days, if we record around the clock, therefore the default is to delete any file older than 5 days
# If any recordings have an event that is useful, it needs to be trasfered to a long storage disk / folder in order to be kept.
 
folders_to_delete = [recordings_dir]
delete_time = "5d"
delete_space = "20%, 90%"

setup.update({"device": {"name":f"{device_name}", "ip":f"{ip}", "MAC_address":f"{mac}", "type":f"{device_type}", "mode":f"{device_mode}","root": root_dir}})
setup.update({"output_signal": {"protocol": output_protocol, "out_pin": output_pin}})
setup.update({"input_signal": {"protocol": input_protocol, "in_pin": input_pin}})
setup.update({"notification": {"email": None}})
setup.update({"model": {"script": None, "pipeline": None}})
setup.update({"server" : {"hls_sink_port": hls_sink_port, "udp_sink": udp_sink_port}})
setup.update({"influxdb": {"port": influxdb_port, "token": token, "org": org, "bucket": bucket, "ip": influx_ip}})
setup.update({"storage": 
             {"local_storage": {"path": local_storage_path, "folders_to_delete": folders_to_delete, "delete_time": delete_time, "delete_space": delete_space}, 
             "cloud": {"use_sync":False, "protocol": "scp", "url": None, "user": None, "password": None, "path": None},
             "NAS":{"use_sync":False, "protocol": "scp", "url": None, "port": 22, "user": None, "password": None, "path": None}}
             })

with open('SETUP.yml', 'w') as f:
    yaml.dump(setup, f)

# Lastly we add a Model description that contains details about the model.
# e.g what is important parameter wise for the given model and how it works.

with open('ModelDescription.md', 'w+') as f:
    f.write("# Start of ModelDescription")

with open('rtsp.sdp', 'w+') as f:
    f.write("v=0 \n")
    f.write("m=video 8554 RTP/AVP 96 \n")
    f.write(f"c=IN IP4 {ip} \n")
    f.write("a=rtpmap:96 H264/90000 \n")
