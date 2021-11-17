import cv2
import torch
from torchvision import transforms
from torchvision.models.detection import fasterrcnn_mobilenet_v3_large_320_fpn as fasterrcnn
import logging

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
        self.model = fasterrcnn
        self.bucket = bucket
        self.org = org
        self.url = url
        self.token = token
        self.pin = pin
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = fasterrcnn(pretrained=True)
        self.model.eval().to(device)
        
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
        #Sends an output signal with GPIO
        if self.pin is not None:
            GPIO.output(self.pin, signal)
            #logging.info(f"Sent {signal} to {self.pin}")

    def bbox(self, img, preds, org_size, h, w, thresh = 0.5):
        nr_people = 0
        for pred in preds:
            bboxes = pred["boxes"].cpu().numpy()
            label = pred["labels"].cpu().numpy()
            scores = pred["scores"].cpu().numpy()
            for idx, bbox in enumerate(bboxes):
                if scores[idx] < thresh: # Threshold for probability.
                    pass
                elif label[idx] != 1: # We only want to classify people
                    pass
                else:
                    nr_people += 1
                    cv2.rectangle(img, (int(org_size[1]*(bbox[0]/w)), int(org_size[0]*(bbox[1]/h))),
                                       (int(org_size[1]*(bbox[2]/w)), int(org_size[0]*(bbox[3]/h))),
                                       (255,0,0), 2)
        
        return img, nr_people

    def detect(self, frame=None, frameid=None, h=320, w=320):
        transform_pipeline = transforms.Compose([transforms.ToTensor(),transforms.Resize((h,w))])
        org_size = frame.shape
        img_transform = transform_pipeline(frame)
        img_transform = img_transform.unsqueeze(0)
        with torch.no_grad():
            preds = self.model(img_transform)

        img, nr_people = self.bbox(frame, preds, org_size=org_size, h=h, w=w, thresh=0.75)

        if self.pin is not None:
            if nr_people==0:
                self.gpio_signal(signal=GPIO.LOW)
            else:
                self.gpio_signal(signal=GPIO.HIGH)
        
        if self.url is not None:
            self.write_to_db(frameid, nr_people)
            

        return img
