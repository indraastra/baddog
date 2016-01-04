import time

import RPi.GPIO as GPIO

import config

GPIO.setmode(GPIO.BCM)
GPIO.setup(config.DETECTOR_IN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def motion_detected(channel):
    print("Motion detected!")

GPIO.add_event_detect(config.DETECTOR_IN_PIN, GPIO.RISING,
                      callback=motion_detected, bouncetime=100)

try:
    print("Starting detection.")
    while True:
        pass
except KeyboardInterrupt:
    print("Stopping detection.")
finally:
    GPIO.cleanup()
