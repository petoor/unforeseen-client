### 1)  Download the correct image for your device
Depending on which device you have, download the corrosponding image.

Image 2GB version: https://developer.nvidia.com/jetson-nano-2gb-sd-card-image

Image 4GB version: https://developer.nvidia.com/jetson-nano-sd-card-image

Image Xavier NX: https://developer.nvidia.com/jetson-nx-developer-kit-sd-card-image

### 1) Flash the correct jetson image to your SD Card.
Use the rpi-imager if it is not already install see the 2 point in [server setup](https://github.com/petoor/unforeseen-server/blob/main/SETUP_SERVER.md).
Run the rpi-imager and choose use custom.
select the zip file you just downloaded, for storage choose your SD card and press write.
Once done you can insert the SD card to your jetson and boot. Note the first time you boot you need a monitor in order to agree to NVIDIAs EULA and select device name, password, timezone, etc...
Once setup and you are at the desktop, go to 2).

### 2)  Get the Jetson to boot USB (Portable SSD/HDD).
This is done in order to have the machine being stable. An SD card / USB Flash drive have a limited lifespan due to **write/erase cycles**, this means we can not write logs and continuous data. However there is no such limitation on SSD/HDD drives. 
To boot from USB see : [Boot from USB - youtube](https://www.youtube.com/watch?v=53rRMr1IpWs)

Note: You need to boot to the SD card for the first boot before you can boot to USB.

---


### 0) *(Optional)* Set name of the client to be more descriptive. 
`hostnamectl set-hostname CLIENT_NAME`

### 1) Update and install python3.6 - set is as default python version.
```sudo apt-get update -y && sudo apt-get upgrade -y
sudo apt install -y apt-utils python3.6 python3-pip
sudo ln -sf /usr/bin/python3 /usr/bin/python && sudo ln -sf /usr/bin/pip3 /usr/bin/pip
```

### 2) Install jetson inference + pytorch
To install jetson inference and pytorch run the following.
During installation you will get prompted if you want to install pytorch. Choose **Yes**.
```sudo apt-get install git cmake libpython3-dev python3-numpy
git clone --recursive https://github.com/dusty-nv/jetson-inference
cd jetson-inference
mkdir build
cd build
cmake ../
make -j$(nproc)
sudo make install
sudo ldconfig
cd ../..
```

We end by returning to the root to have a nicer folder structure.

### 3) Install gstreamer and dependecies
Gstreamer will be used as the computer vision pipeline. Run the following to install it and all the dependencies.

`sudo apt-get install v4l-utils gstreamer1.0-tools gstreamer1.0-alsa gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer-plugins-good1.0-dev libgstreamer-plugins-bad1.0-dev libgirepository1.0-dev gcc libcairo2-dev pkg-config python3-dev gir1.2-gtk-3.0 -y`

### 4) Install pip packages
If you havn't already cloned the client, run:

```git clone https://github.com/petoor/unforeseen-client/
cd unforeseen-client
```

Install unforeseen-client as a pip package and install dependicies.
```
pip install -r requirements.txt
pip install -e .
```
We add the -e flag to be in in editable mode.
That means we can add models and functions to the package without rebuilding.
However we do need to restart the session to acces the new functions.

### 5) *(Optional)* Stats
Run the following to install jetson-stats. This can be useful for seeing the health of the device.

`sudo -H pip install -U jetson-stats`

To see the stats run `jtop`

### 6) *(Optional)* RTSP Server
Install the following if you want to see the video feed remotely, that is streaming the feed to e.g. VLC media player.

- Check version with `gst-launch-1.0 --version`
-  and download corrosponding server version from.
https://gstreamer.freedesktop.org/src/gst-rtsp-server/
- untar (tar -xvf gst-rtsp-server-1.*.*.tar.xz) 
- `cd gst-rtsp-server-1.*.*.tar.xz`
- `./configure`
- `make`

The RTSP Server should now be installed and ready for use. See [record and display rtsp](https://github.com/petoor/unforeseen-client/blob/main/unforeseen/analysis/pipelines/record-and-display-rtsp-raw.txt) for an example usage.

### 7) *(Optional)* SSH pass
To run file sync as daemon sshpass is handy. Used to script the password handshake with the server.
`sudo apt-get install -y sshpass`
Remember the target folder must exist on the server.

### 8) Reboot and enjoy.

`sudo reboot`

The jetson is now ready to run computer vision models. See the [get started](https://github.com/petoor/unforeseen-client/blob/main/README.md) to run some pipelines.

To run without GUI - Production Mode

`sudo systemctl set-default multi-user.target`

Not to be confused with headless - see [Headless setup - youtube](https://www.youtube.com/watch?v=Ch1NKfER0oM)
To add GUI back  - Development Mode

`sudo systemctl set-default graphical.target`

and reboot after setting GUI options in order for them to be applied.
