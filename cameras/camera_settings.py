# Settings can be set with
# power_line_frequency = 1 for Europe (50 hz) and 2 for us / japan (60 hz)
# if the settings has a flags=inactive it will be invalid or incomplete, we can ignore this.
# set exposure_auto to 1 in order to not screw with the framerate while recording
import sys, os
import json
import subprocess
import pdb

def apply_camera_settings(camera):
    camera_settings = {}

    with open(f"cameras/{camera.split('/')[-1]}.txt", "r") as f:
        print(f)
        for line in f:
            print(line)
            camera_settings[line.lstrip().split(" ")[0]]=int(line.lstrip().split("value=")[-1].split(" ")[0])

    for key in camera_settings:
        subprocess.call([f"v4l2-ctl -d {camera} --set-ctrl {key}={camera_settings[key]}"], shell=True)
        
#apply_camera_settings("/dev/video0")
