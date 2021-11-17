import cv2
import logging

import jetson.utils
import jetson.inference


# Influxdb
from influxdb_client import Point, WritePrecision
from influxdb.influxdb import InfluxDBObject
from datetime import datetime

try:
    import Jetson.GPIO as GPIO
except (RuntimeError, ModuleNotFoundError):
    try:
        import RPi.GPIO as GPIO
    except (RuntimeError, ModuleNotFoundError):
        import Mock.GPIO as GPIO
   

class PeopleDetect:
    def __init__(self, url=None, token=None, bucket=None, org=None, pin=None):
        self.model = jetson.inference.detectNet("ssd-mobilenet-v2", 0.8)
        self.bucket = bucket
        self.org = org
        self.url = url
        self.token = token
        self.pin = pin
        
        if self.pin is not None:
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(self.pin, GPIO.OUT, initial=GPIO.LOW)
        
        if self.url is None:
            logging.warning("Running without database")
            
        if self.pin is not None:
            logging.info(f"GPIO pin is {self.pin}")
            
        if self.token is not None or url is not None:
            self.influxdb_object = InfluxDBObject(self.token, self.url)

    def write_to_db(self, frameid, result):
        try:
            if frameid % 30 == 0: # We only write to db every second assuming fps = 30
                point = Point("prediction").field("person", result).time(datetime.utcnow(), WritePrecision.NS)
                self.influxdb_object.write_api.write(self.bucket, self.org, point)
        except Exception:
            logging.warning("Connection to database not found, running without writing to database")
    
    def gpio_signal(self, signal=GPIO.HIGH):
        if self.pin is not None:
            GPIO.output(self.pin, signal)

    def bbox(self, img, detections, org_size, h, w):
        nr_people = 0
        for detection in detections:
            nr_people += 1
            cv2.rectangle(img, (int(org_size[1]*(detection.Left/w)), int(org_size[0]*(detection.Top/h))),
                                   (int(org_size[1]*(detection.Right/w)), int(org_size[0]*(detection.Bottom/h))),
                                   (255,0,0), 2)
        
        return img, nr_people

    def detect(self, frame=None, frameid=None, h=320, w=320):
        org_size = frame.shape
        resized_image = cv2.resize(frame, (w,h), interpolation=cv2.INTER_NEAREST)
        cuda_img = jetson.utils.cudaFromNumpy(resized_image)
        detections = self.model.Detect(cuda_img, overlay="none")
        img, nr_people = self.bbox(frame, detections, org_size=org_size, h=h, w=w)

        if self.pin is not None:
            if nr_people==0:
                self.gpio_signal(signal=GPIO.LOW)
            else:
                self.gpio_signal(signal=GPIO.HIGH)
        
        if self.url is not None:
            self.write_to_db(frameid, nr_people)
        print(nr_people)
        del cuda_img
        return img
