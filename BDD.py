import sqlite3
from datetime import datetime

DB_PATH = "mailbox.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_BDD():
    """
    Initialise la base de données : crée les tables, la Mailbox par défaut (ID=1) 
    et l'utilisateur de test.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # ==================== CRÉATION DES TABLES ====================
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
        id_Mailbox INTEGER PRIMARY KEY AUTOINCREMENT,
        taille INTEGER,
        etat INTEGER,
        adresse VARCHAR(50),
        id_courrier INTEGER,
        FOREIGN KEY(id_courrier) REFERENCES Courrier(id_courrier)
    );
    """)

    # TABLE UTILISATEUR (CORRIGÉE avec PRIMARY KEY)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Utilisateur (
        nom_utilisateur VARCHAR(30) PRIMARY KEY, 
        mot_de_passe VARCHAR(20),
        id_Mailbox INTEGER,
        FOREIGN KEY(id_Mailbox) REFERENCES Mailbox(id_Mailbox)
    );
    """)

    # ==================== INITIALISATION DES DONNÉES ====================
    
    # 1. Insertion de la Mailbox par défaut (ID=1)
    # Ceci est la clé étrangère pour l'utilisateur
    cursor.execute("SELECT id_Mailbox FROM Mailbox WHERE id_Mailbox = 1")
    if cursor.fetchone() is None:
        cursor.execute("""
            INSERT INTO Mailbox (id_Mailbox, taille, etat, adresse) 
            VALUES (1, 30, 0, 'Boîte aux lettres Principale')
        """)
    
    # 2. Insertion de l'utilisateur de test
    cursor.execute("SELECT nom_utilisateur FROM Utilisateur WHERE nom_utilisateur = 'test'")
    if cursor.fetchone() is None:
        cursor.execute("""
            INSERT INTO Utilisateur (nom_utilisateur, mot_de_passe, id_Mailbox)
            VALUES (?, ?, 1)
        """, ("test", "test123"))

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
    
# ... [Les autres fonctions BDD (authentifier_utilisateur, ajouter_courrier, etc.) sont ici si vous les avez] ...


# ==================== EXÉCUTION ====================
if __name__ == "__main__":
    
    print("Démarrage de l'initialisation de la BDD...")
    init_BDD()
    print("Base de données 'mailbox.db' initialisée. Compte 'test'/'test123' créé.")
