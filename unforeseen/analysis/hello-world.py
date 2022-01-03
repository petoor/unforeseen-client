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

from unforeseen.config import setup_loader

# Apply camera settings
from unforeseen.cameras.camera_settings import apply_camera_settings

class GstPipeline:
    """
    https://github.com/google-coral/examples-camera/blob/master/gstreamer/gstreamer.py
    """

    def __init__(self, pipeline, width, height, model=None, url=None, token=None, bucket=None, org=None, in_pin=None, out_pin=None):
        self.running = False
        self.gstsample = None
        self.width = width
        self.height = height
        self.gstfifo = []
        self.frameid = 0
        self.condition = threading.Condition()
        if model is not None:
            self.model = model
        self.player = Gst.parse_launch(pipeline)

        # Fetch different pads from pipeline for manipulation
        appsink = self.player.get_by_name("appsink")
        appsink.connect("new-preroll", self.on_new_sample, True)
        appsink.connect("new_sample", self.on_new_sample, False)

        # src pad in which to put the model output
        self.appsrc = self.player.get_by_name('appsrc')
        self.appsrc.set_property("format", Gst.Format.TIME)
        self.appsrc.set_property("block", True)
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
                frame = frame.copy()
                # MODEL CODE GOES HERE:
                if self.model is not None:
                    frame = self.model.detect(frame=frame, frameid=self.frameid)
                self.appsrc.emit("push-buffer", utils.ndarray_to_gst_buffer(frame))
                gstbuffer.unmap(map_info)

if __name__=="__main__":
    Gst.init(None)
    parser = argparse.ArgumentParser(description='Find people in your video feed!')
    parser.add_argument('--use_db', default=0, choices=['0','1'],
                    help='If we write to an Influx database or not')
                    
    parser.add_argument('--use_gpio', default=0, choices=['0','1'],
                        help='If the model should output a GPIO signal or not')

    parser.add_argument('--pipeline_path', default="analysis/pipelines/hello-world-local-raw.txt",
                    help='The path to the gstreamer pipeline you would like to use')

    parser.add_argument('--camera', default="/dev/video0",
                    help='The camera used')

    parser.add_argument('--use_model', default=1,
                    help='If the model should be used, or we just stream the feed')

    args = parser.parse_args()
    use_db = bool(int(args.use_db))
    use_gpio = bool(int(args.use_gpio))
    use_model = bool(int(args.use_model))
    
    # Check if pipeline txt is found
    pipeline_path = args.pipeline_path

    if os.path.isfile(pipeline_path):
        logging.info("Pipeline found")
    else:
        logging.critical("Pipeline file not found")
        sys.exit()
    
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
       
    # Use DB
    if use_db:
        url = setup.get("influxdb").get("ip")+":"+str(setup.get("influxdb").get("port"))
        token = setup.get("influxdb").get("token")
        bucket = setup.get("influxdb").get("bucket")
        org = setup.get("influxdb").get("org")
    else:
        url = None
        token = None
        bucket = None
        org = None
    
    # Use GPIO
    if use_gpio and setup.get("output_signal").get("protocol") == "GPIO":
        out_pin = setup.get("output_signal").get("out_pin")
    else:
        out_pin = None
    
    if use_gpio and setup.get("input_signal").get("protocol") == "GPIO":
        in_pin = setup.get("input_signal").get("in_pin")
    else:
        in_pin = None
    
    # Load AI model.
    if use_model:
        if setup.get("device").get("type") == "NANO" or setup.get("device").get("type") == "XAVIER":
            from unforeseen.analysis.models.people_jetson import PeopleDetect as Model
        else:
            from unforeseen.analysis.models.people_torchvision import PeopleDetect as Model
        model = Model(url=url, token=token, bucket=bucket, org=org, db_write_speed=framerate, out_pin=out_pin)
    else:
        model=None
    
    with open(pipeline_path, "r") as pipeline:
        pipeline = pipeline.read()
        pipeline = pipeline.replace("{camera}", str(args.camera))
        pipeline = pipeline.replace("{camera_format}", str(camera_format))
        pipeline = pipeline.replace("{width}", str(width))
        pipeline = pipeline.replace("{height}", str(height))
        pipeline = pipeline.replace("{framerate}", str(framerate))
        pipeline = pipeline.replace("{bitrate}", str(bitrate))
        
    GstPipeline(pipeline, width, height, model, url, token, bucket, org, in_pin, out_pin).run()


