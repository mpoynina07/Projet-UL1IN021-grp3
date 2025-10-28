# ______________ Si distance < seuil --> LED rouge ______________

import RPi.GPIO as GPIO
import time

TRIG = 23 # envoie un signal ultrasonique (broche sortie)
ECHO = 24 # reçoit le signal réfléchi (broche entrée)

LED_ROUGE = 27 (sortie)

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(LED_VERTE, GPIO.OUT)
GPIO.setup(LED_ROUGE, GPIO.OUT)


seuil = # en cm, à determiner
def distance():
  """ renvoie la mesure de laprofondeur de la boîte depuis le ultrasonic ranger (float)
  """
  GPIO.input(TRIG, True)
  time.sleep(0.00001)  # pause de 0.00001s pour emettre ultrason
  GPIO.input(TRIG, False)
  
  while GPIO.input(ECHO) == 0 :
    debut = time.time()
  while GPIO.input(ECHO) == 1 :
    fin = time.time()
  
  return ((fin-debut)*34300)/2 # calcul de la distance w/vitesse du son
  
  try :
    while True :
      distance = distance()
      print("Distance:"+distance+"cm")

    if distance < seuil :
      GPIO.output(LED_ROUGE, False)
    else:
      GPIO.output(LED_ROUGE, True)

# Ctrl + C pour quitter programme

      

     
      
      
      
      
      

  
