import argparse
import logging
import sys
import threading
from datetime import datetime

import cv2
import gi
import numpy as np
from gstreamer import GstPipeline  # Needed for gi.repository

from unforeseen.cameras.camera_settings import apply_camera_settings
from unforeseen.config import setup_loader

# Gstreamer related
gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")
from gi.repository import GLib  # noreorder # noqa
from gi.repository import Gst  # noreorder # noqa
from gi.repository import Gtk  # noreorder # noqa


class VideoAnalysisPipeline:
    """General pipeline for video manipulation.

    Functions as the pipeline for all scenarios, so that the only changes we should
    do the code to do analysis is change the pipeline, model and setup.yml
    """

    def __init__(
        self, pipeline: str, width: int, height: int, framerate: int, buffer_length: int, record_path: str
    ) -> None:
        """Initializes the relevant constants and functions used in the analysis pipeline.

        Args:
            pipeline (str): valid gst-launch-1.0 pipeline.
            width (int): Video width.
            height (int): Video height.
            framerate (int): Video framerate.
            buffer_length (int): Number of buffers to record. Recorded video in seconds = buffer_length / framerate.
            record_path (str): Video output path.
        """
        self.running = False
        self.gstsample = None
        self.width = width
        self.height = height
        self.framerate = framerate
        self.record_path = record_path
        self.buffer_length = buffer_length
        self.frameid = 0
        self.condition = threading.Condition()
        self.player = Gst.parse_launch(pipeline)

        # Fetch different pads from pipeline for manipulation
        appsink = self.player.get_by_name("appsink")
        appsink.connect("new-preroll", self.on_new_sample, True)
        appsink.connect("new_sample", self.on_new_sample, False)

        # src pad in which to put the model output
        # self.appsrc = self.player.get_by_name('appsrc')
        # self.appsrc.set_property("format", Gst.Format.TIME)
        # self.appsrc.set_property("block", True)
        # Set up a pipeline bus watch to catch errors.
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_bus_message)

    def run(self):
        """Starts the pipeline."""
        self.running = True
        worker = threading.Thread(target=self.record_loop)
        worker.daemon = True
        worker.start()

        # State to start pipeline (player)
        self.player.set_state(Gst.State.PLAYING)
        try:
            Gtk.main()
        except (KeyboardInterrupt, Exception) as e:
            self.out.release()
            print("Error: ", e)

        # Clean up.
        try:
            self.pipeline.set_state(Gst.State.NULL)
        except AttributeError:
            print("AttributeError, potentially caused by user closing the script.")
        while GLib.MainContext.default().iteration(False):
            pass
        with self.condition:
            self.running = False
            self.condition.notify_all()
        worker.join()

    def on_bus_message(
        self,
        bus: gi.repository.Gst.Bus,
        message: gi.repository.Gst.Message,
    ) -> bool:
        """Gets an returns bus messages from video pipeline.

        Args:
            bus (gi.repository.Gst.Bus): Relevant bus.
            message (gi.repository.Gst.Message): Bus message.

        Returns:
            bool: True, required.
        """
        t = message.type

        if t == Gst.MessageType.EOS:
            Gtk.main_quit()
        elif t == Gst.MessageType.WARNING:
            err, debug = message.parse_warning()
            sys.stderr.write("Warning: %s: %s\n" % (err, debug))
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            sys.stderr.write("Error: %s: %s\n" % (err, debug))
            Gtk.main_quit()
        return True

    def on_new_sample(self, sink: gi.repository.GstApp.AppSink, preroll: bool) -> Gst.FlowReturn.OK:
        """Gets new sample (frame) from the app sink, if appsink exists in the pipeline.

        see https://gstreamer.freedesktop.org/documentation/app/appsink.html?gi-language=python

        Args:
            sink (gi.repository.GstApp.AppSink): the appsink defined by the pipeline
            preroll (bool): If the appsink should use preroll

        Returns:
            Gst.FlowReturn.OK: True
        """
        sample = sink.emit("pull-preroll" if preroll else "pull-sample")
        with self.condition:
            self.gstsample = sample
            self.condition.notify_all()
        return Gst.FlowReturn.OK

    def record_loop(self) -> None:
        """Inference loop which excecutes the logic defined in the model.

        Raises:
            RuntimeError: If the buffer is corrupt (bad signal from camera).
        """
        while True:
            if self.frameid % self.buffer_length == 0:
                try:
                    self.out.release()  # type: ignore
                except (NameError, AttributeError):
                    pass
                current_time = f"{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}"
                self.out = cv2.VideoWriter(
                    f"{self.record_path}{current_time}.mp4",
                    cv2.VideoWriter_fourcc(*"mp4v"),
                    float(framerate),
                    (width, height),
                )
            with self.condition:
                while not self.gstsample and self.running:
                    self.condition.wait()
                if not self.running:
                    break
                gstsample = self.gstsample
                self.frameid += 1
                self.gstsample = None

            # Passing Gst.Buffer as input tensor avoids 2 copies of it.
            gstbuffer = gstsample.get_buffer()  # type: ignore
            success, map_info = gstbuffer.map(Gst.MapFlags.READ)
            if not success:
                raise RuntimeError("Could not map buffer data!")
            else:
                frame = np.ndarray(
                    shape=(self.height, self.width, 3), dtype=np.uint8, buffer=map_info.data
                )  # type: ignore
                self.out.write(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                gstbuffer.unmap(map_info)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Record Video.")

    parser.add_argument(
        "--pipeline_path",
        default="analysis/pipelines/record-and-stream-raw.txt",
        help="The path to the gstreamer pipeline you would like to use",
    )

    parser.add_argument("--camera", default="/dev/video0", help="The camera used")

    args = parser.parse_args()

    setup = setup_loader()

    camera_used = None
    for camera in setup.get("cameras"):  # type: ignore
        if camera.get(args.camera) is not None:
            camera_used = camera
            break

    if camera_used is None:
        logging.critical("Camera not found !")

    # Apply camera settings
    apply_camera_settings(args.camera)

    camera_settings = camera_used[f"{args.camera}"]  # type: ignore
    camera_format = camera_settings.get("camera_format")
    height = camera_settings.get("height")
    width = camera_settings.get("width")
    framerate = camera_settings.get("framerate")
    bitrate = camera_settings.get("bitrate")  # type: ignore
    name = setup.get("device").get("name")  # type: ignore
    udpsink_port = setup.get("server").get("udp_sink")  # type: ignore
    ip = setup.get("device").get("ip")  # type: ignore
    record_path = "storage/recordings/"
    record_path = record_path + setup.get("device").get("name") + "_"  # type: ignore
    pipeline_path = args.pipeline_path

    with open(pipeline_path, "r") as pipeline:
        pipeline = pipeline.read()  # type: ignore
        pipeline = pipeline.replace("{camera}", str(args.camera))  # type: ignore
        pipeline = pipeline.replace("{camera_format}", str(camera_format))  # type: ignore
        pipeline = pipeline.replace("{width}", str(width))  # type: ignore
        pipeline = pipeline.replace("{height}", str(height))  # type: ignore
        pipeline = pipeline.replace("{framerate}", str(framerate))  # type: ignore
        pipeline = pipeline.replace("{bitrate}", str(bitrate))  # type: ignore
        pipeline = pipeline.replace("{name}", str(name))  # type: ignore
        pipeline = pipeline.replace("{udpsink_port}", str(udpsink_port))  # type: ignore
        pipeline = pipeline.replace("{ip}", str(ip))  # type: ignore

    Gst.init(None)
    # framerate*900 = 15 minutes
    VideoAnalysisPipeline(
        pipeline,  # type: ignore
        width=width,
        height=height,
        framerate=framerate,
        buffer_length=framerate * 900,
        record_path=record_path,
    ).run()
