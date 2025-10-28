# -------------bouton pour indiquer que la boïte est vide----------------
# fusionner le programme w/test_LEDs.py, test_Buzzer.py et rajouter l'ecran d'affichage


BOUTON = 5
GPIO.setup(BOUTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)

while True :
  if GPIO.input(BOUTON) == GPIO.LOW : # si bouton appuyé
    print("MailBox vidée par l'utilisateur")
    GPIO.output(LED_ROUGE,False)
    etat_precedent = 0
    time.sleep(1)
    
