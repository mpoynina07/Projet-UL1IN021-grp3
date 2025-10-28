# ---------- Buzzer activé pendant n secondes quand nouvelle lettre détectée -----------
# COMBINER AVEC LEDs.py !!!!!
Buzzer = 22
n = 0.2

GPIO.setput(BUZZER, GPIO.OUT)

etat_precedent = 0 # 1 pour vide 0 pour non vide

while True : 
  distance = distance()
  etat = 1 if distance < seuil else 0

  if etat and etat-precedent == 0 : 
    print("Nouveau courrier détecté !")
    GPIO.output(BUZZER,True)
    time.sleep(n)
    GPIO.output(BUZZER, False)

etat_precedent = etat
time.sleep(1)
    
