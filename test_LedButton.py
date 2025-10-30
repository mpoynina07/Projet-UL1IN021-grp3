import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
from grove.grove_button import GroveButton

pin_led = 5
pin_button = 22

GPIO.setup(pin_led, GPIO.OUT)
GPIO.setup(pin_button, GPIO.IN)

state_led = 0

while True:
	# connect to pin and define pin number (22)
	if GPIO.input(pin_button) == 1:
		state_led = 1 - state_led
	#else:
	#	GPIO.output(pin_led, 1)	
	GPIO.output(pin_led, state_led)	
	time.sleep(0.1)

	
		
