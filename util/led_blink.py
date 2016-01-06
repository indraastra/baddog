import time

import RPi.GPIO as GPIO

import config

GPIO.setmode(GPIO.BCM)
GPIO.setup(config.LED_OUT_PIN, GPIO.OUT, initial=GPIO.HIGH)
for i in range(10):
    GPIO.output(config.LED_OUT_PIN, GPIO.HIGH)
    time.sleep(.5)
    GPIO.output(config.LED_OUT_PIN, GPIO.LOW)
    time.sleep(.5)

GPIO.cleanup()
