import sqlite3
from datetime import datetime

DB_PATH = "mailbox.db"
# ID de la boîte aux lettres par défaut (à utiliser dans les requêtes)
MAILBOX_ID = 1 

def get_connection():
    """Établit et retourne la connexion à la BDD."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_BDD():
    """Initialise les tables de la BDD si elles n'existent pas."""
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
        id_Mailbox INTEGER PRIMARY KEY, -- Rétabli en PK simple pour garantir l'ID 1
        taille INTEGER DEFAULT 0,
        etat INTEGER DEFAULT 0, -- 0=vide, 1=plein
        adresse VARCHAR(50),
        id_courrier INTEGER,
        FOREIGN KEY(id_courrier) REFERENCES Courrier(id_courrier)
    );
    """)
    
    # TABLE UTILISATEUR
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Utilisateur (
        nom_utilisateur VARCHAR(30),
        mot_de_passe VARCHAR(20),
        id_Mailbox INTEGER,
        FOREIGN KEY(id_Mailbox) REFERENCES Mailbox(id_Mailbox)
    );
    """)
    
    # 🚨 CORRECTION CRUCIALE : Assurer qu'une ligne Mailbox ID 1 existe pour l'état initial
    cursor.execute("INSERT OR IGNORE INTO Mailbox (id_Mailbox, etat, taille) VALUES (?, 0, 0)", (MAILBOX_ID,))

    conn.commit()
    conn.close()


def ajouter_utilisateur(nom, mot_de_passe, id_mailbox):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Utilisateur (nom_utilisateur, mot_de_passe, id_Mailbox)
        VALUES (?, ?, ?)
    """, (nom, mot_de_passe, id_mailbox))

    conn.commit()
    conn.close()

def supprimer_utilisateur(nom):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM Utilisateur WHERE nom_utilisateur = ?", (nom,))

    conn.commit()
    conn.close()


def nouveau_courrier(id_mailbox, objet: str = "Nouveau Courrier"):
    """Insère un courrier et met à jour la boîte à PLEIN (etat=1)."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 1. Ajouter le courrier
        heure = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO Courrier (objet, heure_arrivee)
            VALUES (?, ?)
        """, (objet, heure))

        id_courrier = cursor.lastrowid

        # 2. Associer le dernier courrier à la Mailbox et mettre l'état à 1
        cursor.execute("""
            UPDATE Mailbox SET id_courrier = ?, etat = 1
            WHERE id_Mailbox = ?
        """, (id_courrier, id_mailbox))

        conn.commit()
        return id_courrier
        
    except Exception as e:
        conn.rollback() 
        raise e
        
    finally:
        conn.close()


def modifier_objet_courrier(id_courrier, nouvel_objet):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE Courrier SET objet = ?
        WHERE id_courrier = ?
    """, (nouvel_objet, id_courrier))

    conn.commit()
    conn.close()

def historique_courrier(id_mailbox):
    """Retourne tous les courriers liés à cette Mailbox (ne dépend pas de id_courrier dans Mailbox)."""
    conn = get_connection()
    cursor = conn.cursor()

    # NOTE: Cette requête originale ne fonctionnera que si le dernier courrier est toujours lié à Mailbox.
    # Pour l'historique complet, vous avez besoin d'une table intermédiaire (non présente) ou de tous les courriers.
    # Je garde votre requête, mais la modifie pour qu'elle soit plus logique (join sur ID si possible, ou juste SELECT * FROM Courrier)
    
    cursor.execute("""
        SELECT id_courrier, objet, heure_arrivee
        FROM Courrier
        ORDER BY heure_arrivee DESC
    """)

    resultats = cursor.fetchall()
    conn.close()
    return resultats

def rechercher_courrier(id_mailbox, mot_cle):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id_courrier, objet, heure_arrivee
        FROM Courrier
        WHERE Courrier.objet LIKE ?
        ORDER BY Courrier.heure_arrivee DESC
    """, (f"%{mot_cle}%",)) # La jointure n'est pas nécessaire ici

    resultats = cursor.fetchall()
    conn.close()
    return resultats


def get_etat_mailbox(id_mailbox):
    """Renvoie 0 = vide, 1 = pleine."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT etat FROM Mailbox WHERE id_Mailbox = ?
    """, (id_mailbox,))

    etat = cursor.fetchone()
    conn.close()
    # 🚨 CORRECTION : Renvoie 0 si la ligne n'est pas trouvée, pour un statut VIDE par défaut
    return etat[0] if etat else 0

def vider_mailbox(id_mailbox):
    """Réinitialise l'état à 0 et supprime l'association au dernier courrier."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE Mailbox SET etat = 0, id_courrier = NULL
        WHERE id_Mailbox = ?
    """, (id_mailbox,))

    conn.commit()
    conn.close()
