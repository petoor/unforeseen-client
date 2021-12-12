# Unforeseen-client

Assuming you have sat up your nano according to the [setup jetson](https://github.com/petoor/unforeseen-client/blob/main/SETUP_JETSON.md) guide.

All scripts need to be run with the unforeseen folder as root, that is, `cd unforeseen-client/unforeseen` and run the scripts from there. 

To get started, run the following

### 1) Create the SETUP.yml file.
`python initial_setup/create_default_setup.py`

In the **SETUP.yml** file, set the correct parameters for your device.
You can change the height and width of the camera to be e.g 1280 x 720 for 720p streaming.
Set the device-name, set GPIO pins you use (if any) set storage options and so on.
**NB** You need to set the influxdb information in order to stream data to the server. 
It is understood that the unforeseen-server is already up and running following the [setup jetson](https://github.com/petoor/unforeseen-client/blob/main/SETUP_JETSON.md) guide.

### 2) Create basic index.html
Grafana needs the video feed to be in an iframe in order to import it. The easiest way to do this is to have a very simple server we send a hls stream to.

`python initial_setup/create_index_html.py`

### 3) Start the cronjobs
We need to automatically start the hls stream server and clean up scripts in case the jetson looses power.

`python system/start_cronjobs.py`

Once you have created your computer vision model pipeline and added the script to the **SETUP.yml** file, don't forget to rerun  the start_cronjobs script.
### 4) Reboot.
In order for the cronjobs to take effect, the easiest is to reboot the system.

Now you can test the analysis by running 

`python analysis/hello-world.py`

Your camera feed should play with a SSD model trained on the COCO dataset. If you are in front of the camera, you should have a bounding box around you :smiley:

`python analysis/hello-world.py --pipeline analysis/pipelines/hello-world-raw.txt`

Go to DEVICE_IP:8080 and see that the stream is playing with analysis.

If you are using for instance a *Logitech 922c* camera, use
`python analysis/hello-world.py --pipeline analysis/pipelines/hello-world-mjpg.txt`
instead.

If you have sat up the influxdb you can run: 

`python analysis/hello-world.py --pipeline analysis/pipelines/hello-world-raw.txt --use_db 1` 

to send the data to the influxdb.

If you have sat up GPIO logic you can run:  

`python analysis/hello-world.py --pipeline analysis/pipelines/hello-world-raw.txt --use_gpio 1` 

to send output signals every time a COCO object is detected via GPIO.



### 5) Create your own model and pipeline
Have a look at the `analysis/hello-world.py` script to see what happens. Have a look in the `analysis/models` folder and the  `analysis/pipelines` folder to see examples of models and pipelines.
This should be inspiration for you to start creating your own models.
