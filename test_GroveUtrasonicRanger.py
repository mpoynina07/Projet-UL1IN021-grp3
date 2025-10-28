# ___________Lit la distance mesurée et l'affiche toutes les n secondes__________

import RPi.GPIO as GPIO
import time 

nb_secondes = # à determiner
TRIG = 23 # envoie un signal ultrasonique (broche sortie)
ECHO = 24 # reçoit le signal réfléchi (broche entrée)

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

try :
  while True :
    GPIO.output(TRIG,True) #lancement du signal
    time.sleep(0.00001) # pause 0.00001s pour emettre ultrason
    GPIO.output(TRIG,False) #arret du signal
    
  while GPIO.input(ECHO) == 0 :
    debut = time.time()
  while GPIO.input(ECHO) == 1 :
    fin = time.time()

  distance = (fin-debut)*34300/2 # (vitesse du son / 2)
  print("Distance:"+distance+"cm")



  

    
   
  

