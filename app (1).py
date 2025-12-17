from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import RPi.GPIO as GPIO
import time
import threading
from datetime import datetime
import sqlite3
import os
import uvicorn
from BDD import get_connection, init_BDD, get_etat_mailbox, set_etat_mailbox, ajouter_courrier

app = FastAPI(
    title="Smart MailBox API",
    description="API pour la boîte aux lettres intelligente",
    version="1.0.0"
)

# ==================== CONFIGURATION CORS ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== SERVIR LES PAGES WEB ====================
app.mount("/static", StaticFiles(directory="static"), name="static")
@app.get("/")
async def serve_login():
    return FileResponse("static/login.html")

@app.get("/dashboard")
async def serve_dashboard():
    return FileResponse("static/dashboard.html")

@app.get("/history")
async def serve_history():
    return FileResponse("static/history.html")

@app.get("/signup")
async def serve_signup():
    return FileResponse("static/signup.html")

@app.get("/settings")
async def serve_settings():
    return FileResponse("static/settings.html")

@app.get("/updatepwd")
async def serve_updatepwd():
    return FileResponse("static/updatepwd.html")
# ==================== API ENDPOINTS ====================

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "MailBox", "timestamp": "2024-01-01"}

@app.get("/api/mail-status")
def mail_status():
    return {
        "has_mail": False,
        "led": "green",
        "last_check": "2024-01-01T12:00:00"
    }



@app.post("/api/empty-mailbox")
def empty_mailbox():
    return {"success": True, "message": "Boîte vidée"}

# ==================== MODÈLES ====================
class UserLogin(BaseModel):
    username: str
    password: str

class UserRegister(BaseModel):
    username: str
    password: str

class SearchFilters(BaseModel):
    objet: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None

# ==================== CONFIGURATION GPIO ====================
ULTRA = 5
BUZZER = 24
LED_ROUGE = 22
LED_VERTE = 27
BOUTON_VIDAGE = 18

seuil = 15
n = 0.2
MAILBOX_ID = 1 # ID de la boîte aux lettres par défaut (à utiliser dans les appels BDD)
seuil = 15 
courrier_present = False # Variable globale pour l'état (synchro BDD)
lock = threading.Lock()
DB_PATH = "mailbox.db"


GPIO.setmode(GPIO.BCM)
GPIO.setup(ULTRA, GPIO.OUT)
GPIO.setup(LED_ROUGE, GPIO.OUT)
GPIO.setup(LED_VERTE, GPIO.OUT)
GPIO.setup(BUZZER, GPIO.OUT)
GPIO.setup(BOUTON_VIDAGE, GPIO.IN, pull_up_down=GPIO.PUD_UP)

courrier_present = False
lock = threading.Lock()

# ... (RESTE DE VOTRE CODE EXISTANT ICI - gardez toutes vos fonctions BDD, capteur, etc.) ...
# ==================== FONCTIONS BDD ====================
def get_db():
    """Connexion à la base de données"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialisation de la BDD"""
    if not os.path.exists(DB_PATH):
        print("Création de la base de données...")
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE Courrier (
            id_courrier INTEGER PRIMARY KEY AUTOINCREMENT,
            objet VARCHAR(30),
            heure_arrivee TEXT
        )
        """)
        
        cursor.execute("""
        CREATE TABLE Mailbox (
            id_Mailbox INTEGER PRIMARY KEY AUTOINCREMENT,
            taille INTEGER,
            etat INTEGER DEFAULT 0,
            adresse VARCHAR(50),
            id_courrier INTEGER,
            FOREIGN KEY(id_courrier) REFERENCES Courrier(id_courrier)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE Utilisateur (
            nom_utilisateur VARCHAR(30) PRIMARY KEY,
            mot_de_passe VARCHAR(20),
            id_Mailbox INTEGER,
            FOREIGN KEY(id_Mailbox) REFERENCES Mailbox(id_Mailbox)
        )
        """)
        
        # Créer une mailbox par défaut
        cursor.execute("""
        INSERT INTO Mailbox (taille, adresse, etat) 
        VALUES (30, 'Adresse par défaut', 0)
        """)
        
        # Créer un utilisateur de test
        cursor.execute("""
        INSERT INTO Utilisateur (nom_utilisateur, mot_de_passe, id_Mailbox)
        VALUES (?, ?, 1)
        """, ("test", "test123"))
        
        conn.commit()
        conn.close()
        
        print("Base de données initialisée.")

# ==================== FONCTIONS CAPTEUR ====================
def mesure_distance():
    """Mesure la distance avec le capteur ultrason"""
    try:
        GPIO.output(ULTRA, 0)
        time.sleep(0.002)
        GPIO.output(ULTRA, 1)
        time.sleep(0.00001)
        GPIO.output(ULTRA, 0)
        
        GPIO.setup(ULTRA, GPIO.IN)
        
        debut = time.time()
        while GPIO.input(ULTRA) == 0:
            debut = time.time()
        
        fin = time.time()
        while GPIO.input(ULTRA) == 1:
            fin = time.time()
        
        GPIO.setup(ULTRA, GPIO.OUT)
        
        distance = (fin - debut) * 34300 / 2
        return round(distance, 2)
        
    except Exception as e:
        print(f"Erreur mesure distance: {e}")
        return None

def update_leds():
    """Met à jour les LEDs selon l'état"""
    global courrier_present
    
    with lock:
        if courrier_present:
            GPIO.output(LED_ROUGE, 1)   # Rouge allumé
            GPIO.output(LED_VERTE, 0)   # Verte éteinte
        else:
            GPIO.output(LED_ROUGE, 0)   # Rouge éteint
            GPIO.output(LED_VERTE, 1)   # Verte allumé
def save_new_mail():
    """Sauvegarde un nouveau courrier dans la BDD et met à jour l'état de la Mailbox à PLEIN (1)."""
    # REMARQUE: Assurez-vous que get_db est importé de BDD.py
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        heure = datetime.now().isoformat()
        
        # 1. Insertion du nouveau courrier dans la table 'Courrier'
        cursor.execute("INSERT INTO Courrier (heure_arrivee) VALUES (?)", (heure,))
        courrier_id = cursor.lastrowid
        
        # 2. Mise à jour de la table 'Mailbox'
        cursor.execute("""
            UPDATE Mailbox 
            SET etat = 1, id_courrier = ?
            WHERE id_Mailbox = 1
        """, (courrier_id,))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Courrier enregistré en BDD - ID: {courrier_id}. État Mailbox mis à jour à PLEIN (1).")
        
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde du courrier: {e}")
def update_mailbox_state():
    """
    Met à jour l'état de la mailbox dans la BDD.
    Cette fonction est utilisée pour marquer la boîte comme VIDÉE (etat = 0).
    """
    global courrier_present # Nécessaire pour déterminer l'état actuel
    
    # REMARQUE: Assurez-vous que get_db est importé de BDD.py
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # L'état est 0 si la variable globale est False (suite au vidage par l'API)
        etat = 1 if courrier_present else 0 
        
        # Mise à jour de la table 'Mailbox' : on vide (etat=0) et on retire l'ID du dernier courrier.
        cursor.execute("""
            UPDATE Mailbox 
            SET etat = ?, id_courrier = NULL
            WHERE id_Mailbox = 1
        """, (etat,))
        
        conn.commit()
        conn.close()
        
        print(f"✅ État Mailbox mis à jour en BDD à {'PLEIN (1)' if etat == 1 else 'VIDE (0)'}.")
        
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour de l'état en BDD: {e}")
def load_initial_status():
    global courrier_present
    try:
        # get_etat_mailbox(id) retourne 0 (vide) ou 1 (plein)
        etat_int = get_etat_mailbox(MAILBOX_ID) 
        # On convertit 0/1 en False/True pour la variable globale
        courrier_present = bool(etat_int) 
        print(f"Statut initial de la boîte (lu de la BDD): Courrier {'présent' if courrier_present else 'absent'} (état: {etat_int})")
    except Exception as e:
        print(f"ERREUR BDD lors de l'initialisation: {e}. Statut par défaut: {courrier_present}")

load_initial_status()

# 🚨 Mise à jour de la variable globale au démarrage
# Ceci permet de reprendre l'état en cas de redémarrage du serveur !
courrier_present = load_initial_status()
print(f"Statut initial de la boîte (lu de la BDD): Courrier {'présent' if courrier_present else 'absent'}")

def check_capteur():
    """Vérifie le capteur et détecte les nouveaux courriers"""
    global courrier_present
    
    distance = mesure_distance()
    
    # 🚨 DÉBOGAGE : Affiche la distance lue par le capteur
    if distance is not None:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Distance mesurée: {distance} cm. Seuil: {seuil} cm.")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Erreur de mesure de distance.")
    # FIN DÉBOGAGE
    
    if distance is None:
        return
    
    # Détection nouveau courrier
    if distance < seuil and not courrier_present:
        # ... (le reste du code est correct : lock, update_leds, buzzer, save_new_mail)
        with lock:
            courrier_present = True
            update_leds()
            
            # Activer le buzzer
            GPIO.output(BUZZER, 1)
            time.sleep(n)
            GPIO.output(BUZZER, 0)
            
            print("Nouveau courrier détecté et enregistré !")
            
            # Sauvegarder dans la BDD
            save_new_mail()

def check_bouton():
    """Vérifie l'état du bouton physique et vide la boîte si pressé."""
    global courrier_present
    
    # 🚨 Logique de détection du bouton (méthode de lecture directe)
    if GPIO.input(BOUTON) == GPIO.LOW: # BOUTON = 18. LOW = bouton pressé
        
        # Anti-rebond (debounce) simple
        time.sleep(0.05) 
        if GPIO.input(BOUTON) == GPIO.LOW:
            
            with lock:
                if courrier_present:
                    # 1. Réinitialiser la variable globale et la BDD
                    update_mailbox_state(False) # Met l'état à False / 0
                    
                    # 2. Mettre à jour les LEDs (partie physique)
                    update_leds()
                    
                    print("🔔 Bouton physique pressé : Boîte marquée comme vidée.")
            
            # Attendre que le bouton soit relâché pour éviter les détections multiples
            while GPIO.input(BOUTON) == GPIO.LOW:
                time.sleep(0.1)
# ==================== ROUTES API ====================
@app.get("/api/health")
async def health_check():
    """Vérifie que l'API fonctionne"""
    return {
        "status": "ok",
        "service": "Smart MailBox API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/mail-status")
async def get_mail_status():
    """Retourne le statut de la boîte"""
    try:
        distance = mesure_distance()
        
        return {
            "success": True,
            "has_mail": courrier_present,
            "distance": distance,
            "led_etat": "rouge" if courrier_present else "verte",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mail-history")
async def get_mail_history(limit: int = 50):
    """Retourne l'historique des courriers"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id_courrier, objet, heure_arrivee 
            FROM Courrier 
            ORDER BY heure_arrivee DESC 
            LIMIT ?
        """, (limit,))
        
        courriers = []
        for row in cursor.fetchall():
            courriers.append({
                "id": row["id_courrier"],
                "objet": row["objet"] if row["objet"] else "Non spécifié",
                "heure_arrivee": row["heure_arrivee"]
            })
        
        conn.close()
        return {
            "success": True,
            "data": courriers,
            "count": len(courriers)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search-mail")
async def search_mail(filters: SearchFilters):
    """Recherche des courriers par objet ou date"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        query = "SELECT * FROM Courrier WHERE 1=1"
        params = []
        
        if filters.objet:
            query += " AND objet LIKE ?"
            params.append(f"%{filters.objet}%")
        
        if filters.date_from:
            query += " AND date(heure_arrivee) >= ?"
            params.append(filters.date_from)
        
        if filters.date_to:
            query += " AND date(heure_arrivee) <= ?"
            params.append(filters.date_to)
        
        query += " ORDER BY heure_arrivee DESC"
        
        cursor.execute(query, params)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row["id_courrier"],
                "objet": row["objet"] if row["objet"] else "Non spécifié",
                "heure_arrivee": row["heure_arrivee"]
            })
        
        conn.close()
        return {
            "success": True,
            "data": results,
            "count": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
import os
from pathlib import Path

# Obtenez le chemin absolu
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

# Puis utilisez le chemin complet
@app.get("/api.js")
def api_js():
    file_path = STATIC_DIR / "api.js"
    print(f"Tentative de servir: {file_path}")  # Pour debug
    print(f"Fichier existe: {file_path.exists()}")  # Pour debug
    return FileResponse(str(file_path))
    
@app.post("/api/empty-mailbox")
async def empty_mailbox():
    """Marque la boîte comme vidée via l'API, synchronise l'état global et BDD."""
    global courrier_present # On doit modifier l'état global du serveur
    
    try:
        # On utilise le verrou (lock) pour éviter que le thread capteur ne s'exécute en même temps.
        with lock: 
            if courrier_present:
                # 1. Mise à jour de la variable globale (permet la prochaine détection par le capteur)
                courrier_present = False
                
                # 2. Mise à jour des LEDs (partie physique)
                update_leds()
                
                # 3. Mise à jour de la BDD (l'état passe à 0 / VIDE)
                update_mailbox_state()
                
                print("Boîte vidée via API")
                
                return {
                    "success": True,
                    "message": "Boîte marquée comme vidée"
                }
            else:
                # Si le courrier_present était déjà False, on confirme le succès de l'opération
                return {
                    "success": True,
                    "message": "La boîte est déjà vide"
                }

    except Exception as e:
        # Renvoie une erreur FastAPI standard
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur interne lors du vidage: {str(e)}"
        )
# app.py
# app.py (Ajoutez ceci n'importe où dans la section API ENDPOINTS)
@app.get("/api/debug-user/{username}")
def debug_user(username: str):
    """
    Endpoint temporaire pour vérifier ce qui est enregistré dans la BDD pour un utilisateur.
    NE DOIT JAMAIS ÊTRE UTILISÉ EN PRODUCTION.
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        username_clean = username.strip()

        cursor.execute("SELECT nom_utilisateur, mot_de_passe FROM Utilisateur WHERE nom_utilisateur = ?", (username_clean,))
        user_data = cursor.fetchone()
        
        conn.close()
        
        if user_data:
            return {
                "success": True, 
                "message": "Utilisateur trouvé. Détails ci-dessous:",
                "username_saisi": username,
                "username_en_bdd": user_data[0], 
                "password_en_bdd": user_data[1] 
            }
        return {"success": False, "message": f"Utilisateur '{username}' non trouvé dans la BDD."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne de débogage: {str(e)}")

@app.post("/api/login")
async def login(user: UserLogin):
    """Authentification utilisateur (Version durcie)"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        username_clean = user.username.strip()
        password_clean = user.password.strip()

        cursor.execute("""
            SELECT nom_utilisateur, id_Mailbox FROM Utilisateur 
            WHERE nom_utilisateur = ? AND mot_de_passe = ?
        """, (username_clean, password_clean)) # UTILISER les variables nettoyées
        
        user_data = cursor.fetchone()
        
        if not user_data:
            raise HTTPException(
                status_code=401,
                detail="Nom d'utilisateur ou mot de passe incorrects"
            )
        
        return {"success": True, "token": "simulated_token", "username": user_data[0]}
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Erreur interne du serveur lors de la connexion.")
@app.post("/api/register")
async def register(user: UserRegister):
    """Inscription d'un nouvel utilisateur"""
    try:
        username_clean = user.username.strip()
        password_clean = user.password.strip()
        if len(username_clean) > 30:
            raise HTTPException(
                status_code=400,
                detail="Nom d'utilisateur trop long (max 30 caractères)"
            )
        
        if len(password_clean) > 20:
            raise HTTPException(
                status_code=400,
                detail="Mot de passe trop long (max 20 caractères)"
            )
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Vérifier si l'utilisateur existe déjà
        cursor.execute(
            "SELECT * FROM Utilisateur WHERE nom_utilisateur = ?", 
            (username_clean,)
        )
        if cursor.fetchone():
            conn.close()
            raise HTTPException(
                status_code=400,
                detail="Nom d'utilisateur déjà utilisé"
            )
        
        # Créer l'utilisateur
        cursor.execute("""
            INSERT INTO Utilisateur (nom_utilisateur, mot_de_passe, id_Mailbox)
            VALUES (?, ?, 1)
        """, (username_clean, password_clean))
        
        conn.commit()
        conn.close()
        
        return {"success": True}
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

# ==================== THREADS ====================
def thread_capteur():
    """Thread pour surveiller le capteur et exécuter la vérification toutes les secondes."""
    print("Thread capteur démarré et actif.")
    while True:
        try:
            # check_capteur() contient la logique de mesure de distance et d'appel à save_new_mail()
            check_capteur()
            time.sleep(1) # Vérifie l'état du capteur toutes les 1 seconde
        except Exception as e:
            # Gère les erreurs sans arrêter le serveur, mais en mettant le thread en pause
            print(f"❌ Erreur critique dans thread capteur. Le thread va se mettre en pause. Erreur: {e}")
            time.sleep(5) # Pause de 5 secondes avant de réessayer

def thread_bouton():
    """Thread pour surveiller le bouton"""
    print("Thread bouton démarré")
    while True:
        try:
            check_bouton()
            time.sleep(0.1)
        except Exception as e:
            print(f"Erreur thread bouton: {e}")
            time.sleep(1)


# ==================== DÉMARRAGE ET ARRÊT (FastAPI Events) ====================

@app.on_event("startup")
async def startup_event():
    """Démarre l'initialisation de la BDD et les threads au lancement de l'application."""
    print("Initialisation de la base de données...")
    init_BDD() # 1. Initialisation de la BDD
    
    print("Démarrage des threads de surveillance des capteurs en arrière-plan...")
    
    # 2. Démarrage des threads (daemon=True permet aux threads de s'arrêter proprement)
    threading.Thread(target=thread_capteur, daemon=True).start()
    threading.Thread(target=thread_bouton, daemon=True).start()
    
    print("Threads de surveillance lancés.")

@app.on_event("shutdown")
def shutdown_event():
    """Nettoie les ressources GPIO à l'arrêt du serveur."""
    # 3. Nettoyage du GPIO
    GPIO.cleanup()
    print("Ressources GPIO nettoyées.")

# ==================== Lancement du Serveur ====================

if __name__ == "__main__":
    try:
        print("Démarrage du serveur Uvicorn...")
        # L'appel à uvicorn.run() déclenchera l'événement startup_event
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        print("\nArrêt manuel du serveur...")
    # Le nettoyage du GPIO se fait maintenant via shutdown_event
