# Standard python imports
import sys, os, logging, threading, argparse
import numpy as np

# Gstreamer related
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstBase', '1.0')
gi.require_version('Gtk', '3.0')

from gi.repository import GLib, Gst, Gtk
from gstreamer import GstPipeline, Gst
import gstreamer.utils as utils

# AI Model
#from unforeseen.analysis.models.people_torchvision import PeopleDetect
#from models.people_jetson import PeopleDetect

from unforeseen.config import setup_loader

# Apply camera settings
from unforeseen.cameras.camera_settings import apply_camera_settings

class GstPipeline:
    """
    https://github.com/google-coral/examples-camera/blob/master/gstreamer/gstreamer.py
    """

    def __init__(self, pipeline, camera):
        self.running = False
        self.camera = camera
        self.gstsample = None
        self.frameid = 0
        self.condition = threading.Condition()
        self.player = Gst.parse_launch(pipeline)

        # Fetch different pads from pipeline for manipulation
        appsink = self.player.get_by_name("appsink")
        appsink.connect("new-preroll", self.on_new_sample, True)
        appsink.connect("new_sample", self.on_new_sample, False)

        # Set up a pipeline bus watch to catch errors.
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_bus_message)

    def run(self):
        self.running = True
        worker = threading.Thread(target=self.inference_loop)
        worker.start()

        # State to start pipeline (player)
        self.player.set_state(Gst.State.PLAYING)
        try:
            Gtk.main()
        except Exception as e:
            print("Error: ", e)
        
        # Clean up.
        self.pipeline.set_state(Gst.State.NULL)
        while GLib.MainContext.default().iteration(False):
            pass
        with self.condition:
            self.running = False
            self.condition.notify_all()
        worker.join()

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
        return True

    def on_new_sample(self, sink, preroll):
        sample = sink.emit('pull-preroll' if preroll else 'pull-sample')
        with self.condition:
            self.gstsample = sample
            self.condition.notify_all()
        return Gst.FlowReturn.OK

    def inference_loop(self):
        while True:
            with self.condition:
                while not self.gstsample and self.running:
                    self.condition.wait()
                if not self.running:
                    break
                gstsample = self.gstsample
                self.frameid +=1
                self.gstsample = None
                if self.frameid % 60 == 0:
                    apply_camera_settings(self.camera)

if __name__=="__main__":
    Gst.init(None)
    parser = argparse.ArgumentParser(description='Calibration script')

    parser.add_argument('--pipeline_path', default="analysis/pipelines/record-and-display-raw.txt",
                    help='The path to the gstreamer pipeline you would like to use')

    parser.add_argument('--camera', default="/dev/video0",
                    help='The camera used')

    args = parser.parse_args()   
    pipeline_path = args.pipeline_path

    # Check if pipeline txt is found
    if os.path.isfile(pipeline_path):
        logging.info("Pipeline found")
    else:
        logging.critical("Pipeline file not found")
    
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
    udpsink_port = setup.get("server").get("udp_sink")
    ip = setup.get("device").get("ip")

    with open(pipeline_path, "r") as pipeline:
        pipeline = pipeline.read()
        pipeline = pipeline.replace("{camera}", str(args.camera))
        pipeline = pipeline.replace("{camera_format}", str(camera_format))
        pipeline = pipeline.replace("{width}", str(width))
        pipeline = pipeline.replace("{height}", str(height))
        pipeline = pipeline.replace("{framerate}", str(framerate))
        pipeline = pipeline.replace("{bitrate}", str(bitrate))
        pipeline = pipeline.replace("{udpsink_port}", str(udpsink_port))
        pipeline = pipeline.replace("{ip}", str(ip))
        
    GstPipeline(pipeline, args.camera).run()


