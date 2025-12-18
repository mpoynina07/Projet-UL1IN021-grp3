from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
# Import conditionnel de RPi.GPIO pour la compatibilité hors Raspberry Pi
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("ATTENTION: RPi.GPIO n'est pas disponible. Le serveur fonctionnera en mode simulation.")
    class DummyGPIO: # Classe factice si RPi.GPIO n'est pas installé
        LOW = 0
        HIGH = 1
        OUT = 1
        IN = 1
        BCM = 1
        PUD_UP = 1
        def setmode(self, mode): pass
        def setup(self, pin, mode, pull_up_down=None): pass
        def output(self, pin, value): pass
        def input(self, pin): return 1 # Simule un état HIGH par défaut
        def cleanup(self): pass
    GPIO = DummyGPIO()
    
import time
import threading
from datetime import datetime
import sqlite3
import os
import uvicorn

# 🚨 IMPORT DES FONCTIONS BDD 🚨
from BDD import init_BDD, get_etat_mailbox, vider_mailbox, nouveau_courrier, get_connection 


app = FastAPI(
    title="Smart MailBox API",
    description="API pour la boîte aux lettres intelligente",
    version="1.0.0"
)

# ==================== CONFIGURATION GLOBALE ====================
MAILBOX_ID = 1 
seuil = 15 # Distance maximale en cm pour considérer la boîte comme 'pleine'
lock = threading.Lock()

# PINS GPIO (BCM)
ULTRA = 5  # Broche pour le capteur ultrason (TRIG et ECHO sur la même broche pour les capteurs 1-pin)
BOUTON = 18 # Broche pour le bouton physique (pour vider la boîte)
LED_ROUGE = 26
LED_VERT = 19

# Statut global (synchronisé avec la BDD au démarrage)
courrier_present = False 


# ==================== GPIO SETUP ====================
try:
    GPIO.setmode(GPIO.BCM)
    
    # Capteur ultrason (doit être configuré dynamiquement dans mesure_distance)
    # Bouton (Input avec PULL_UP, l'état est LOW quand pressé)
    GPIO.setup(BOUTON, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
    
    # LED (Output)
    GPIO.setup(LED_ROUGE, GPIO.OUT)
    GPIO.setup(LED_VERT, GPIO.OUT)
    
    print("Configuration GPIO réussie.")
except Exception as e:
    print(f"AVERTISSEMENT: Erreur de configuration GPIO. Le serveur fonctionne sans RPi.GPIO. Erreur: {e}")


# ==================== LOGIQUE BDD ET SYNCHRONISATION ====================

def load_initial_status():
    """Charge l'état de la boîte depuis la BDD vers la variable globale 'courrier_present'."""
    global courrier_present
    try:
        etat_int = get_etat_mailbox(MAILBOX_ID) 
        courrier_present = bool(etat_int) 
        print(f"Statut initial de la boîte (lu de la BDD): Courrier {'présent' if courrier_present else 'absent'} (état: {etat_int})")
        update_leds()
    except Exception as e:
        print(f"ERREUR BDD lors du chargement initial: {e}. Statut par défaut: {courrier_present}")

def update_leds():
    """Met à jour l'état des LEDs selon l'état global."""
    if courrier_present:
        GPIO.output(LED_ROUGE, GPIO.HIGH)
        GPIO.output(LED_VERT, GPIO.LOW)
    else:
        GPIO.output(LED_ROUGE, GPIO.LOW)
        GPIO.output(LED_VERT, GPIO.HIGH)


def update_mailbox_state(etat: bool):
    """
    Met à jour l'état dans la BDD et la variable globale.
    Utilisé par le thread bouton et l'API /api/empty (etat=False).
    """
    global courrier_present 
    
    try:
        if not etat:
            # Si False (état vide), on appelle la fonction BDD pour vider la boîte
            vider_mailbox(MAILBOX_ID) 
        # Note : Si etat=True, c'est géré directement par nouveau_courrier()
        
        courrier_present = etat
        update_leds()
        print(f"✅ STATUT INTERNE MIS À JOUR : Courrier {'présent' if etat else 'absent'}")
        
    except Exception as e:
        print(f"❌ Erreur mise à jour état: {e}")


# ==================== LOGIQUE CAPTEURS ====================

def mesure_distance():
    """Mesure la distance avec le capteur ultrason (1-pin)."""
    try:
        # 1. Envoi du signal (TRIG)
        GPIO.setup(ULTRA, GPIO.OUT)
        GPIO.output(ULTRA, GPIO.LOW)
        time.sleep(0.000002) # 2 us
        GPIO.output(ULTRA, GPIO.HIGH)
        time.sleep(0.00001)  # 10 us (Impulsion de 10us)
        GPIO.output(ULTRA, GPIO.LOW)
        
        # 2. Lecture du temps de retour (ECHO)
        GPIO.setup(ULTRA, GPIO.IN)
        timeout_counter = 0.05 # Temps maximal pour éviter une boucle infinie
        start_time = time.time()
        
        # Attendre que la broche passe à HIGH
        while GPIO.input(ULTRA) == GPIO.LOW:
            start_time = time.time()
            if start_time > time.time() + timeout_counter: return None # Timeout
        
        # Mesurer le temps HIGH
        stop_time = time.time()
        while GPIO.input(ULTRA) == GPIO.HIGH:
            stop_time = time.time()
            if stop_time > start_time + timeout_counter: return None # Timeout

        time_elapsed = stop_time - start_time
        
        # Distance = (Temps * Vitesse du son (34300 cm/s)) / 2
        distance = (time_elapsed * 34300) / 2
        
        return distance

    except Exception as e:
        return None


def check_capteur():
    """Vérifie le capteur et détecte les nouveaux courriers."""
    global courrier_present
    
    distance = mesure_distance()
    
    # 🚨 DÉBOGAGE : Affiche la distance lue
    if distance is not None:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Capteur : {distance:.2f} cm. Seuil: {seuil} cm.")
    
    if distance is None:
        return
    
    # Logique de détection de nouveau courrier
    if distance < seuil and not courrier_present:
        with lock:
            if not courrier_present: # Double vérification sous verrou
                
                # 1. Enregistrement BDD et mise à jour de Mailbox.etat à 1 (PLEIN)
                try:
                    courrier_id = nouveau_courrier(MAILBOX_ID)
                    print(f"🚨 ALERTE : Nouveau courrier détecté et enregistré - ID: {courrier_id}")
                    
                    # 2. Mise à jour de la variable globale et des LEDs
                    update_mailbox_state(True) 
                    
                except Exception as e:
                    print(f"❌ Erreur critique lors de l'enregistrement du courrier: {e}")


def check_bouton():
    """Vérifie l'état du bouton physique et vide la boîte si pressé (BCM 18)."""
    global courrier_present
    
    # 🚨 Logique de détection du bouton pressé (LOW)
    if GPIO.input(BOUTON) == GPIO.LOW: 
        
        # Anti-rebond (debounce) simple
        time.sleep(0.05) 
        if GPIO.input(BOUTON) == GPIO.LOW:
            
            with lock:
                if courrier_present:
                    
                    # 1. Réinitialiser la variable globale et la BDD à VIDE (0)
                    update_mailbox_state(False) 
                    
                    print("🔓 Bouton physique pressé : Boîte marquée comme vidée.")
            
            # Attendre que le bouton soit relâché pour éviter les détections multiples
            while GPIO.input(BOUTON) == GPIO.LOW:
                time.sleep(0.1)


# ==================== CONFIGURATION CORS ET PAGES WEB ====================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Routes de pages (servir les fichiers HTML)
@app.get("/")
async def serve_login(): 
    return FileResponse("static/login.html")

@app.get("/dashboard")
async def serve_dashboard(): 
    return FileResponse("static/dashboard.html")

@app.get("/history")
async def serve_history(): 
    return FileResponse("static/history.html")

@app.get("/settings")
async def serve_settings(): 
    return FileResponse("static/settings.html")

@app.get("/apropos")
async def serve_apropos(): 
    return FileResponse("static/apropos.html")

@app.get("/signup")
async def serve_signup(): 
    return FileResponse("static/signup.html")

@app.get("/updatepwd")
async def serve_updatepwd(): 
    return FileResponse("static/updatepwd.html")

# Route pour api.js
@app.get("/api.js")
async def serve_api_js():
    return FileResponse("static/api.js")


# ==================== API ENDPOINTS ====================

@app.post("/api/empty-mailbox")
async def empty_mailbox_api():
    """API pour marquer la boîte comme vidée."""
    global courrier_present
    
    try:
        with lock:
            if courrier_present:
                # Réinitialiser la variable globale et la BDD à VIDE (0)
                update_mailbox_state(False) 
                print("Boîte vidée via API")
                
            return {"success": True, "has_mail": courrier_present}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne lors du vidage: {str(e)}")

@app.get("/api/mail-status")
async def get_mailbox_status():
    """Renvoie l'état actuel de la boîte aux lettres."""
    global courrier_present
    
    try:
        # Lecture de la BDD pour s'assurer que l'API est synchronisée
        etat_int = get_etat_mailbox(MAILBOX_ID)
        courrier_present = bool(etat_int) 
        
        return {
            "success": True,
            "has_mail": courrier_present, 
            "last_check": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== THREADS ====================
def thread_capteur():
    """Thread pour surveiller le capteur toutes les 1 seconde."""
    print("Thread capteur démarré et actif.")
    while True:
        try:
            check_capteur()
            time.sleep(1) 
        except Exception as e:
            print(f"❌ Erreur thread capteur: {e}")
            time.sleep(5)

def thread_bouton():
    """Thread pour surveiller le bouton toutes les 0.1 seconde."""
    print("Thread bouton démarré.")
    while True:
        try:
            check_bouton()
            time.sleep(0.1)
        except Exception as e:
            print(f"❌ Erreur thread bouton: {e}")
            time.sleep(1)


# ==================== DÉMARRAGE ET ARRÊT (FastAPI Events) ====================

@app.on_event("startup")
async def startup_event():
    """Démarre l'initialisation de la BDD et les threads au lancement de l'application."""
    print("Initialisation de la base de données...")
    init_BDD() # 1. Assure que la BDD est prête
    
    print("Démarrage des threads de surveillance des capteurs en arrière-plan...")
    
    # 2. Démarrage des threads
    threading.Thread(target=thread_capteur, daemon=True).start()
    threading.Thread(target=thread_bouton, daemon=True).start()
    
    # 3. Réaliser la synchronisation initiale après l'initialisation de la BDD
    load_initial_status()
    
    print("Threads de surveillance lancés.")

@app.on_event("shutdown")
def shutdown_event():
    """Nettoie les ressources GPIO à l'arrêt du serveur."""
    GPIO.cleanup()
    print("Ressources GPIO nettoyées.")


# ==================== LANCEMENT DU SERVEUR ====================

if __name__ == "__main__":
    try:
        print("Démarrage du serveur Uvicorn...")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        print("\nArrêt manuel du serveur...")
