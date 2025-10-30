# ______________ Si distance < seuil --> LED rouge ______________

import RPi.GPIO as GPIO
import time

ULTRA = 5

LED_ROUGE = 22 

GPIO.setmode(GPIO.BCM)
GPIO.setup(ULTRA, GPIO.OUT)
#GPIO.setup(LED_VERTE, GPIO.OUT)
GPIO.setup(LED_ROUGE, GPIO.OUT)


seuil = # en cm, à determiner (14)

try :
  while True :
    GPIO.output(ULTRA, 0)
    time.sleep(0.002)
    GPIO.output(ULTRA, 1)
    time.sleep(0.00001)  # pause de 0.00001s pour emettre ultrason
    GPIO.output(ULTRA, 0)
    
    GPIO.setup(ULTRA, GPIO.IN)
  
    debut = time.time()
    while GPIO.input(ULTRA) == 0 :
      debut = time.time()
    while GPIO.input(ULTRA) == 1 :
      fin = time.time()
    GPIO.setup(ULTRA, GPIO.OUT)
    
    distance = (fin-debut)*34300/2 # calcul de la distance w/vitesse du son
    
    
    if distance < seuil :
      GPIO.output(LED_ROUGE, 1)
    else:
      GPIO.output(LED_ROUGE, 0)
    time.sleep(1)

except KeyboardInterrupt:
    print("Programme interrompu par l'utilisateur")      
      
finally :
    GPIO.cleanup()

# Ctrl + C pour quitter programme

      

  
 
     
      
      
      
      
      

  
