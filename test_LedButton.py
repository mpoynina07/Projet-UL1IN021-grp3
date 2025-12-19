import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
from grove.grove_button import GroveButton

pin_led = 5
pin_button = 22

GPIO.setup(pin_led, GPIO.OUT)
GPIO.setup(pin_button, GPIO.IN)

etat_led = 0

while True:
	
	if GPIO.input(pin_button) == 1:
		etat_led = 1 - etat_led
	#else:
	GPIO.output(pin_led, etat_led)	
	time.sleep(0.1)

	
		
