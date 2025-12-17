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

def check_capteur():
    """Vérifie le capteur et détecte les nouveaux courriers"""
    global courrier_present
    
    distance = mesure_distance()
    
    if distance is None:
        return
    
    # Détection nouveau courrier
    if distance < seuil and not courrier_present:
        with lock:
            courrier_present = True
            update_leds()
            
            # Activer le buzzer
            GPIO.output(BUZZER, 1)
            time.sleep(n)
            GPIO.output(BUZZER, 0)
            
            print("Nouveau courrier détecté !")
            
            # Sauvegarder dans la BDD
            save_new_mail()

def check_bouton():
    """Vérifie si le bouton de vidage est pressé"""
    global courrier_present
    
    # Bouton pressé = LOW (pull-up)
    if GPIO.input(BOUTON_VIDAGE) == GPIO.LOW:
        time.sleep(0.05)  # Anti-rebond
        if GPIO.input(BOUTON_VIDAGE) == GPIO.LOW:  # Confirmation
            with lock:
                if courrier_present:
                    courrier_present = False
                    update_leds()
                    update_mailbox_state()
                    print("Bouton pressé - Boîte vidée")
                    
                    # Petit bip de confirmation
                    GPIO.output(BUZZER, 1)
                    time.sleep(0.1)
                    GPIO.output(BUZZER, 0)
            
            time.sleep(0.5)  # Éviter les pressions multiples

def save_new_mail():
    """Sauvegarde un nouveau courrier dans la BDD"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        heure = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO Courrier (heure_arrivee) 
            VALUES (?)
        """, (heure,))
        
        courrier_id = cursor.lastrowid
        
        cursor.execute("""
            UPDATE Mailbox 
            SET etat = 1, id_courrier = ?
            WHERE id_Mailbox = 1
        """, (courrier_id,))
        
        conn.commit()
        conn.close()
        
        print(f"Courrier enregistré - ID: {courrier_id}")
        
    except Exception as e:
        print(f"Erreur sauvegarde courrier: {e}")

def update_mailbox_state():
    """Met à jour l'état de la mailbox dans la BDD"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        etat = 1 if courrier_present else 0
        
        cursor.execute("""
            UPDATE Mailbox 
            SET etat = ?, id_courrier = NULL
            WHERE id_Mailbox = 1
        """, (etat,))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Erreur mise à jour état: {e}")

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
    """Marque la boîte comme vidée via l'API"""
    global courrier_present
    
    try:
        with lock:
            if courrier_present:
                courrier_present = False
                update_leds()
                update_mailbox_state()
                
                print("Boîte vidée via API")
                
                return {
                    "success": True,
                    "message": "Boîte marquée comme vidée"
                }
            else:
                return {
                    "success": False,
                    "message": "La boîte est déjà vide"
                }
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    """Thread pour surveiller le capteur"""
    print("Thread capteur démarré")
    while True:
        try:
            check_capteur()
            time.sleep(1)
        except Exception as e:
            print(f"Erreur thread capteur: {e}")
            time.sleep(5)

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

# ==================== DÉMARRAGE ====================
if __name__ == "__main__":
    try:
        print("Démarrage du serveur...")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        print("\nArrêt...")
    finally:
        GPIO.cleanup()
