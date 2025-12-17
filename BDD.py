import sqlite3
from datetime import datetime

# Chemin vers le fichier de la base de données
DB_PATH = "mailbox.db"
MAILBOX_ID = 1 # ID par défaut pour les opérations

def get_connection():
    """Établit et retourne la connexion à la BDD."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_BDD():
    """Initialise les tables de la BDD."""
    conn = get_connection()
    cursor = conn.cursor()

    # TABLE COURRIER
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Courrier (
        id_courrier INTEGER PRIMARY KEY AUTOINCREMENT,
        objet VARCHAR(30),
        heure_arrivee TEXT
    );
    """)

    # TABLE MAILBOX
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Mailbox (
        id_Mailbox INTEGER PRIMARY KEY,
        taille INTEGER DEFAULT 0,
        etat INTEGER DEFAULT 0,
        adresse VARCHAR(50),
        id_courrier INTEGER,
        FOREIGN KEY(id_courrier) REFERENCES Courrier(id_courrier)
    );
    """)

    # TABLE UTILISATEUR
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Utilisateur (
        nom_utilisateur VARCHAR(30) UNIQUE,
        mot_de_passe VARCHAR(20),
        id_Mailbox INTEGER,
        FOREIGN KEY(id_Mailbox) REFERENCES Mailbox(id_Mailbox)
    );
    """)
    
    # Assurer qu'une ligne Mailbox existe (pour les jointures)
    cursor.execute("INSERT OR IGNORE INTO Mailbox (id_Mailbox, etat) VALUES (?, 0)", (MAILBOX_ID,))

    conn.commit()
    conn.close()


def ajouter_utilisateur(nom_utilisateur, mot_de_passe):
    """Ajoute un utilisateur et lui lie la Mailbox par défaut."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO Utilisateur (nom_utilisateur, mot_de_passe, id_Mailbox)
        VALUES (?, ?, ?)
    """, (nom_utilisateur, mot_de_passe, MAILBOX_ID))
    
    conn.commit()
    conn.close()


def get_etat_mailbox(id_mailbox):
    """Renvoie 0 = vide, 1 = pleine."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT etat FROM Mailbox WHERE id_Mailbox = ?
    """, (id_mailbox,))

    etat = cursor.fetchone()
    conn.close()
    return etat[0] if etat else 0 # Retourne 0 par défaut si non trouvé

def ajouter_courrier_et_maj_mailbox(id_mailbox, objet: str = "Nouveau Courrier"):
    """Insère un courrier et met à jour l'état de la Mailbox à PLEIN (1)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        heure = datetime.now().isoformat()
        
        # 1. Insertion du nouvel enregistrement de courrier
        cursor.execute("INSERT INTO Courrier (objet, heure_arrivee) VALUES (?, ?)", (objet, heure))
        courrier_id = cursor.lastrowid
        
        # 2. Mise à jour de la table Mailbox: etat = 1 (plein) et lien vers le nouveau courrier
        cursor.execute("""
            UPDATE Mailbox 
            SET etat = 1, id_courrier = ?
            WHERE id_Mailbox = ?
        """, (courrier_id, id_mailbox))
        
        conn.commit()
        return courrier_id
        
    except Exception as e:
        conn.rollback() 
        raise e
        
    finally:
        conn.close()


def set_mailbox_empty(id_mailbox):
    """Marque la boîte comme VIDÉE (etat = 0) et retire la référence au dernier courrier."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE Mailbox 
            SET etat = 0, id_courrier = NULL
            WHERE id_Mailbox = ?
        """, (id_mailbox,))
        
        conn.commit()
        
    except Exception as e:
        conn.rollback() 
        raise e
        
    finally:
        conn.close()

# ... (les autres fonctions get_historique, rechercher_courrier, etc. restent ici)
