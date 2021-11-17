# Standard python imports
import sys, os, logging, threading, argparse
import numpy as np
from datetime import datetime
# Gstreamer related
import gi
import pdb
gi.require_version('Gst', '1.0')
gi.require_version('GstBase', '1.0')
gi.require_version('Gtk', '3.0')

from gi.repository import GLib, Gst, Gtk
from gstreamer import GstPipeline, Gst
import gstreamer.utils as utils

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from unforeseen.config import setup_loader
import pdb
# Apply camera settings
from unforeseen.cameras.camera_settings import apply_camera_settings

class GstPipeline:
    def __init__(self, pipeline):
        self.player = Gst.parse_launch(pipeline)

        # Set up a pipeline bus watch to catch errors.
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_bus_message)

    def run(self):
        # State to start pipeline (player)
        self.player.set_state(Gst.State.PLAYING)
        try:
            Gtk.main()
        except Exception as e:
            print("Error: ", e)
        finally:
            self.player.set_state(Gst.State.NULL)

    def on_bus_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            Gtk.main_quit()
        elif t == Gst.MessageType.WARNING:
            err, debug = message.parse_warning()
            sys.stderr.write('Warning: %s: %s\n' % (err, debug))
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            sys.stderr.write('Error: %s: %s\n' % (err, debug))
            Gtk.main_quit()

if __name__=="__main__":
    
    parser = argparse.ArgumentParser(description='Take an image with camera')

    parser.add_argument('--pipeline_path', default="analysis/pipelines/take-image.txt",
                    help='The path to the gstreamer pipeline you would like to use')

    parser.add_argument('--camera', default="/dev/video0",
                    help='The camera used')


    args = parser.parse_args()

    setup = setup_loader()
    
    camera_used = None
    for camera in setup.get("cameras"):
        if camera.get(args.camera) is not None:
            camera_used = camera
            break
    
    if camera_used is None:
        logging.critical("Camera not found !")

    apply_camera_settings(args.camera)

    camera_settings = camera_used[f"{args.camera}"]
    camera_format = camera_settings.get("camera_format")
    height = camera_settings.get("height")
    width = camera_settings.get("width")
    framerate = camera_settings.get("framerate")
    bitrate = camera_settings.get("bitrate")
    name = setup.get("device").get("name")
    
    pipeline_path = args.pipeline_path
    #pdb.set_trace()
    path = setup.get("storage").get("local_storage").get("path")
    current_time = f"{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}"
    with open(pipeline_path, "r") as pipeline:
        pipeline = pipeline.read()
        pipeline = pipeline.replace("{camera}", str(args.camera))
        pipeline = pipeline.replace("{camera_format}", str(camera_format))
        pipeline = pipeline.replace("{width}", str(width))
        pipeline = pipeline.replace("{height}", str(height))
        pipeline = pipeline.replace("{framerate}", str(framerate))
        pipeline = pipeline.replace("{bitrate}", str(bitrate))
        pipeline = pipeline.replace("{name}", str(name))
        pipeline = pipeline.replace("{image_location}",path+"/images/"+str(current_time)+".jpg")
    Gst.init(None)
    GstPipeline(pipeline).run()
