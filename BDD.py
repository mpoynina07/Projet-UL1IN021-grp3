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

# BDD.py (À ajouter ou modifier vers la fin)

def set_etat_mailbox(id_mailbox, nouvel_etat):
    """Met à jour l'état de la boîte aux lettres (0 = vide, 1 = pleine)."""
    conn = get_connection()
    cursor = conn.cursor()
    # Utilise un UPDATE pour garantir l'atomicité
    cursor.execute("""
        UPDATE Mailbox SET etat = ? WHERE id_Mailbox = ?
    """, (nouvel_etat, id_mailbox))
    conn.commit()
    conn.close()
# BDD.py

def get_etat_mailbox(id_mailbox):
    """Renvoie 0 = vide, 1 = pleine."""
    conn = get_connection() # 🚨 Assurez-vous que cette fonction existe bien dans BDD.py
    cursor = conn.cursor()

    cursor.execute("""
        SELECT etat FROM Mailbox WHERE id_Mailbox = ?
    """, (id_mailbox,))

    etat = cursor.fetchone()
    conn.close()
    # Renvoie 0 ou 1, ou une erreur si la boîte n'existe pas
    return etat[0] if etat else 0
def vider_mailbox(id_mailbox):
    """Marque la boîte comme vide (etat = 0)."""
    set_etat_mailbox(id_mailbox, 0)
# BDD.py (À ajouter ou insérer)

def ajouter_courrier(id_mailbox, objet: str = None):
    """
    1. Ajoute un nouvel enregistrement de courrier dans la table Courrier.
    2. Met à jour l'état de la Mailbox associée à PLEIN (1).

    Args:
        id_mailbox (int): L'ID de la boîte aux lettres à mettre à jour (doit être 1).
        objet (str, optional): Description optionnelle du courrier.
    
    Returns:
        int: L'ID du nouveau courrier inséré.
    """
    conn = get_connection() # 🚨 Utilise la fonction de connexion correcte
    cursor = conn.cursor()
    
    try:
        heure = datetime.now().isoformat()
        
        # 1. Insertion du nouvel enregistrement de courrier
        cursor.execute("""
            INSERT INTO Courrier (objet, heure_arrivee)
            VALUES (?, ?)
        """, (objet, heure))
        
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
        print(f"Erreur d'insertion du courrier dans la BDD: {e}")
        # Annulation de la transaction en cas d'erreur
        conn.rollback() 
        raise 
        
    finally:
        conn.close()
    # L'API utilisera cette fonction pour vider la boîte.
# ==================== EXÉCUTION ====================
if __name__ == "__main__":
    
    print("Démarrage de l'initialisation de la BDD...")
    init_BDD()
    print("Base de données 'mailbox.db' initialisée. Compte 'test'/'test123' créé.")
