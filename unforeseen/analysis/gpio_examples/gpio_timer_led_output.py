import time, argparse
from unforeseen.config import setup_loader

try:
    import Jetson.GPIO as GPIO
except (RuntimeError, ModuleNotFoundError):
    try:
        import RPi.GPIO as GPIO
    except (RuntimeError, ModuleNotFoundError):
        import Mock.GPIO as GPIO

def timer_led(pin, seconds=1):
    try:
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
        print(f"Sent High to pin {pin} for {seconds} seconds")
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(seconds)
        GPIO.output(pin, GPIO.LOW)
    finally:
        print("Cleaning up")
        GPIO.cleanup()

if __name__=="__main__":
    setup = setup_loader()
    out_pin = setup.get("output_signal").get("out_pin")
    
    parser = argparse.ArgumentParser(description='Find people in your video feed!')
    parser.add_argument('--seconds', default=1, help='Seconds sending GPIO High signal')
    args = parser.parse_args()
    
    seconds = float(args.seconds)
    timer_led(out_pin, seconds=seconds)