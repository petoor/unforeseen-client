import time
try:
    import Jetson.GPIO as GPIO
except (RuntimeError, ModuleNotFoundError):
    try:
        import RPi.GPIO as GPIO
    except (RuntimeError, ModuleNotFoundError):
        import Mock.GPIO as GPIO

def blink_led(pin):
    try:
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
        while True:
            print(f"Sent High to {pin}")
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(1)
            print(f"Sent Low to {pin}")
            GPIO.output(pin, GPIO.LOW)
            time.sleep(1)
    finally:
        print("Cleaning up")
        GPIO.cleanup()

if __name__=="__main__":
    blink_led(12)
