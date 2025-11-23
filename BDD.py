import sqlite3
from datetime import datetime

DB_PATH = "mailbox.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn



def init_BDD():
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
        id_Mailbox INTEGER PRIMARY KEY AUTOINCREMENT,
        taille INTEGER,
        etat INTEGER,
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




def nouveau_courrier(id_mailbox, objet=None):
    """Insère un courrier et met à jour la boîte."""
    conn = get_connection()
    cursor = conn.cursor()

    # Ajouter le courrier
    heure = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO Courrier (objet, heure_arrivee)
        VALUES (?, ?)
    """, (objet, heure))

    id_courrier = cursor.lastrowid

    # Associer le dernier courrier à la Mailbox
    cursor.execute("""
        UPDATE Mailbox SET id_courrier = ?, etat = 1
        WHERE id_Mailbox = ?
    """, (id_courrier, id_mailbox))

    conn.commit()
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
    """Retourne tous les courriers liés à cette Mailbox."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Courrier.id_courrier, Courrier.objet, Courrier.heure_arrivee
        FROM Courrier
        JOIN Mailbox ON Mailbox.id_courrier = Courrier.id_courrier
        WHERE Mailbox.id_Mailbox = ?
        ORDER BY Courrier.heure_arrivee DESC
    """, (id_mailbox,))

    resultats = cursor.fetchall()
    conn.close()
    return resultats

def rechercher_courrier(id_mailbox, mot_cle):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Courrier.id_courrier, Courrier.objet, Courrier.heure_arrivee
        FROM Courrier
        JOIN Mailbox ON Mailbox.id_courrier = Courrier.id_courrier
        WHERE Mailbox.id_Mailbox = ?
        AND Courrier.objet LIKE ?
        ORDER BY Courrier.heure_arrivee DESC
    """, (id_mailbox, f"%{mot_cle}%"))

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
    return etat[0] if etat else None

def vider_mailbox(id_mailbox):
    """Réinitialise l'état et supprime l'association au dernier courrier."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE Mailbox SET etat = 0, id_courrier = NULL
        WHERE id_Mailbox = ?
    """, (id_mailbox,))

    conn.commit()
    conn.close()
