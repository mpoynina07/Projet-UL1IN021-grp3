from flask import Flask, jsonify, request
from flask_cors import CORS
import RPi.GPIO as GPIO
import time
import threading
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
CORS(app)

# ==================== CONFIGURATION ====================

# Configuration GPIO 
ULTRA = 5        # Pin pour echo 
BUZZER = 24      # Pin buzzer
LED_ROUGE = 22   # Pin LED rouge
LED_VERTE = 27   # Pin LED verte 
BOUTON_VIDAGE = 17  # Pin pour le bouton de vidage

seuil = 15       # Seuil en cm
n = 0.2          # Durée buzzer

# Configuration BDD
DB_PATH = "mailbox.db"

# Initialisation GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(ULTRA, GPIO.OUT)
GPIO.setup(LED_ROUGE, GPIO.OUT)
GPIO.setup(LED_VERTE, GPIO.OUT)
GPIO.setup(BUZZER, GPIO.OUT)
GPIO.setup(BOUTON_VIDAGE, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Variables 
courrier_present = False  # État boîte
lock = threading.Lock()

# ==================== FONCTIONS BDD ====================

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
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
                    
                    # bip de confirmation
                    GPIO.output(BUZZER, 1)
                    time.sleep(0.1)
                    GPIO.output(BUZZER, 0)
                    
            time.sleep(0.5)  Éviter les pressions multiples

def save_new_mail():
    """Sauvegarde un nouveau courrier dans la BDD"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        heure = datetime.now().isoformat()
        
        # Insérer le courrier
        cursor.execute("""
            INSERT INTO Courrier (heure_arrivee) 
            VALUES (?)
        """, (heure,))
        
        courrier_id = cursor.lastrowid
        
        # Mettre à jour la mailbox
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

@app.route('/api/mail-status', methods=['GET'])
def api_mail_status():
    """Retourne le statut de la boîte"""
    try:
        distance = mesure_distance()
        
        return jsonify({
            'success': True,
            'has_mail': courrier_present,
            'distance': distance,
            'led_etat': 'rouge' if courrier_present else 'verte',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/mail-history', methods=['GET'])
def api_mail_history():
    """Retourne l'historique des courriers"""
    try:
        limit = request.args.get('limit', 50)
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id_courrier, objet, heure_arrivee 
            FROM Courrier 
            ORDER BY heure_arrivee DESC 
            LIMIT ?
        """, (int(limit),))
        
        courriers = []
        for row in cursor.fetchall():
            courriers.append({
                'id': row['id_courrier'],
                'objet': row['objet'] if row['objet'] else 'Non spécifié',
                'heure_arrivee': row['heure_arrivee']
            })
        
        conn.close()
        return jsonify({
            'success': True,
            'data': courriers
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/empty-mailbox', methods=['POST'])
def api_empty_mailbox():
    """Marque la boîte comme vidée via l'API"""
    global courrier_present
    
    try:
        with lock:
            if courrier_present:
                courrier_present = False
                update_leds()
                update_mailbox_state()
                
                print("Boîte vidée via API")
                
                return jsonify({
                    'success': True,
                    'message': 'Boîte marquée comme vidée'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'La boîte est déjà vide'
                })
                
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/login', methods=['POST'])
def api_login():
    """Authentification utilisateur"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Champs manquants'})
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM Utilisateur 
            WHERE nom_utilisateur = ? AND mot_de_passe = ?
        """, (username, password))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return jsonify({
                'success': True,
                'username': user['nom_utilisateur'],
                'mailbox_id': user['id_Mailbox']
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Nom d\'utilisateur ou mot de passe incorrect'
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/register', methods=['POST'])
def api_register():
    """Inscription d'un nouvel utilisateur"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Champs manquants'})
        
        if len(username) > 30:
            return jsonify({'success': False, 'error': 'Nom d\'utilisateur trop long'})
        
        if len(password) > 20:
            return jsonify({'success': False, 'error': 'Mot de passe trop long'})
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Vérifier si l'utilisateur existe déjà
        cursor.execute("SELECT * FROM Utilisateur WHERE nom_utilisateur = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Nom d\'utilisateur déjà utilisé'})
        
        # Créer l'utilisateur
        cursor.execute("""
            INSERT INTO Utilisateur (nom_utilisateur, mot_de_passe, id_Mailbox)
            VALUES (?, ?, 1)
        """, (username, password))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/health', methods=['GET'])
def api_health():
    """Vérifie que l'API fonctionne"""
    return jsonify({
        'status': 'ok',
        'service': 'Smart MailBox API',
        'courrier_present': courrier_present,
        'timestamp': datetime.now().isoformat()
    })

# ==================== THREADS ====================

def thread_capteur():
    """surveiller le capteur"""
    print(" capteur démarré")
    while True:
        try:
            check_capteur()
            time.sleep(1)  # Vérifier toutes les secondes
        except Exception as e:
            print(f"Erreur thread capteur: {e}")
            time.sleep(5)

def thread_bouton():
    """pour surveiller le bouton"""
    print("Thread bouton démarré")
    while True:
        try:
            check_bouton()
            time.sleep(0.1)  # Vérifier souvent pour réactivité
        except Exception as e:
            print(f"Erreur thread bouton: {e}")
            time.sleep(1)

# ==================== LANCEMENT ====================

if __name__ == '__main__':
    try:
        # Initialiser la base de données
        print("Initialisation...")
        init_db()
        
        # Initialiser les LEDs
        update_leds()
        print("LEDs initialisées")
        
        # Démarrer les threads
        print("Démarrage des threads...")
        thread1 = threading.Thread(target=thread_capteur, daemon=True)
        thread2 = threading.Thread(target=thread_bouton, daemon=True)
        thread1.start()
        thread2.start()
        
        # Démarrer le serveur Flask
        print(f"\n{'='*50}")
        print("API MailBox démarrée sur http://0.0.0.0:5000")
        print("Endpoints disponibles:")
        print("  GET  /api/health          - Vérification API")
        print("  GET  /api/mail-status     - Statut de la boîte")
        print("  GET  /api/mail-history    - Historique des courriers")
        print("  POST /api/empty-mailbox   - Vider la boîte (API)")
        print("  POST /api/login           - Connexion")
        print("  POST /api/register        - Inscription")
        print(f"{'='*50}")
        print("\nContrôles physiques:")
        print("  • Bouton GPIO17        - Vider la boîte manuellement")
        print("  • LED Rouge GPIO22     - Courrier présent")
        print("  • LED Verte GPIO27     - Boîte vide")
        print("  • Buzzer GPIO24        - Alarme nouveau courrier")
        print(f"{'='*50}")
        print("\nAppuyez sur Ctrl+C pour arrêter...")
        
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
        
    except KeyboardInterrupt:
        print("\nArrêt du programme...")
    except Exception as e:
        print(f"Erreur critique: {e}")
    finally:
        GPIO.cleanup()
        print("GPIO nettoyé. Programme terminé.")