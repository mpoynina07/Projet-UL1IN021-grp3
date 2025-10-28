# ___________Lit la distance mesurée et l'affiche toutes les n secondes__________

import RPi.GPIO as GPIO
import time 

nb_secondes = # à determiner
BROCHE = 5

GPIO.setmode(GPIO.BCM)
GPIO.setup(BROCHE, GPIO.OUT)


try :
  while True :
    GPIO.output(BROCHE, 0)
        time.sleep(0.002)
        GPIO.output(BROCHE, 1)
        time.sleep(0.0001)
        GPIO.output(BROCHE, 0)
        
        GPIO.setup(BROCHE, GPIO.IN)
        
        debut = time.time()
        while GPIO.input(BROCHE) == 0:
            debut = time.time()
        while GPIO.input(BROCHE) == 1:
            fin = time.time()

  distance = (fin-debut)*34300/2 # (vitesse du son / 2)
  print("Distance:"+distance+"cm")

  sleep(1)


except KeyboardInterrupt:
    
finally:
    GPIO.cleanup()




  

    
   
  

