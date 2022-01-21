from unforeseen.config import setup_loader

try:
    import Jetson.GPIO as GPIO
except (RuntimeError, ModuleNotFoundError):
    try:
        import RPi.GPIO as GPIO
    except (RuntimeError, ModuleNotFoundError):
        import Mock.GPIO as GPIO

def button_press(in_pin, out_pin):
    try:
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(in_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(out_pin, GPIO.OUT, initial=GPIO.LOW)
        while True: # Run forever
            if GPIO.input(in_pin) == GPIO.HIGH:
                print("Button was pushed!")
                print(f"Sending High to pin {out_pin}")
                GPIO.output(out_pin, GPIO.HIGH)
            else:
                GPIO.output(out_pin, GPIO.LOW)
    finally:
        print("Cleaning up")
        GPIO.cleanup()

if __name__=="__main__":
    setup = setup_loader()
    out_pin = setup.get("output_signal").get("out_pin")
    in_pin = setup.get("input_signal").get("in_pin")
    
    button_press(in_pin=in_pin, out_put=out_pin)