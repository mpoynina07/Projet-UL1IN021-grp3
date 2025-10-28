# ______________ Si distance < seuil --> LED rouge ______________

import RPi.GPIO as GPIO
import time

ULTRA = 5

LED_ROUGE = 4 

GPIO.setmode(GPIO.BCM)
GPIO.setup(ULTRA, GPIO.OUT)
#GPIO.setup(LED_VERTE, GPIO.OUT)
GPIO.setup(LED_ROUGE, GPIO.OUT)


seuil = # en cm, à determiner

def distance():
  """ renvoie la mesure de laprofondeur de la boîte depuis le ultrasonic ranger (float)
  """
  GPIO.output(ULTRA, 0)
  time.sleep(0.002)
  GPIO.output(ULTRA, 1)
  time.sleep(0.00001)  # pause de 0.00001s pour emettre ultrason
  GPIO.output(ULTRA, 0)
  
  GPIO.setup(ULTRA, GPIO.IN)

  debut = time.time()
  while GPIO.input(ECHO) == 0 :
    debut = time.time()
  while GPIO.input(ECHO) == 1 :
    fin = time.time()
  
  return (fin-debut)*34300/2 # calcul de la distance w/vitesse du son
  
  try :
    while True :
      distance = distance()
      print("Distance:"+distance+"cm")

    if distance < seuil :
      GPIO.output(LED_ROUGE, 1)
    else:
      GPIO.output(LED_ROUGE, 0)

# Ctrl + C pour quitter programme

      

  
 
     
      
      
      
      
      

  
