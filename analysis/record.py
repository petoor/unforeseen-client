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
import cv2
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from unforeseen-client.config import setup_loader

# Apply camera settings
from unforeseen-client.cameras.camera_settings import apply_camera_settings

class GstPipeline:
    def __init__(self, pipeline, width, height, framerate, buffer_length, record_path):
        self.running = False
        self.gstsample = None
        self.width = width
        self.height = height
        self.framerate = framerate
        self.record_path = record_path
        self.buffer_length = buffer_length
        self.gstfifo = []
        self.frameid = 0
        self.condition = threading.Condition()
        self.player = Gst.parse_launch(pipeline)

        # Fetch different pads from pipeline for manipulation
        appsink = self.player.get_by_name("appsink")
        appsink.connect("new-preroll", self.on_new_sample, True)
        appsink.connect("new_sample", self.on_new_sample, False)

        # src pad in which to put the model output
        #self.appsrc = self.player.get_by_name('appsrc')
        #self.appsrc.set_property("format", Gst.Format.TIME)
        #self.appsrc.set_property("block", True)
        # Set up a pipeline bus watch to catch errors.
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_bus_message)
        
    def run(self):
        self.running = True
        worker = threading.Thread(target=self.record_loop)
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

    def record_loop(self):
        while True:
            if self.frameid % self.buffer_length == 0:
                try:
                    out.release()
                except NameError:
                    pass
                current_time = f"{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}"
                out = cv2.VideoWriter(f"{self.record_path}/{current_time}.mp4", cv2.VideoWriter_fourcc(*"mp4v"), float(framerate), (width,height))
            with self.condition:
                while not self.gstsample and self.running:
                    self.condition.wait()
                if not self.running:
                    break
                gstsample = self.gstsample
                self.frameid +=1
                print(self.frameid, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
                self.gstsample = None

            # Passing Gst.Buffer as input tensor avoids 2 copies of it.
            gstbuffer = gstsample.get_buffer()
            success, map_info = gstbuffer.map(Gst.MapFlags.READ)
            if not success:
                raise RuntimeError("Could not map buffer data!")
            else:
                frame = np.ndarray(
                        shape=(self.height,self.width,3),
                        dtype=np.uint8,
                        buffer=map_info.data)
                out.write(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                gstbuffer.unmap(map_info)


if __name__=="__main__":
    
    parser = argparse.ArgumentParser(description='Record and stream video.')

    parser.add_argument('--pipeline_path', default="analysis/pipelines/record-and-stream-raw.txt",
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
    record_path = "storage/recordings"
    pipeline_path = args.pipeline_path

    with open(pipeline_path, "r") as pipeline:
        pipeline = pipeline.read()
        pipeline = pipeline.replace("{camera}", str(args.camera))
        pipeline = pipeline.replace("{camera_format}", str(camera_format))
        pipeline = pipeline.replace("{width}", str(width))
        pipeline = pipeline.replace("{height}", str(height))
        pipeline = pipeline.replace("{framerate}", str(framerate))
        pipeline = pipeline.replace("{bitrate}", str(bitrate))
        pipeline = pipeline.replace("{name}", str(name))

    Gst.init(None)
    # framerate*900 = 15 minutes
    GstPipeline(pipeline,width=width, height=height, framerate=framerate, buffer_length=framerate*900,record_path=record_path).run()
