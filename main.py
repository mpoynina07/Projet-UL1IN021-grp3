from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import bcrypt
import os
import sqlite3
from config import USER_CREDENTIALS, DATABASE_URL

app = FastAPI()

# Rediriger vers la page de connexion lorsque l'on ouvre le projet
@app.get("/")
async def root():
    return RedirectResponse(url="/login")

# Fonction pour connecter à la base de données
def get_db():
    conn = sqlite3.connect(DATABASE_URL.split(":///")[1])  # Récupère le chemin du fichier .db
    return conn

# Fonction pour ajouter un utilisateur dans la base de données
def add_user_to_db(username: str, password: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO utilisateurs (username, password) VALUES (?, ?)", 
        (username, password)
    )
    conn.commit()
    conn.close()

# Modèle Pydantic pour l'utilisateur
class UserCreate(BaseModel):
    username: str
    password: str

# Route pour l'inscription d'un utilisateur
@app.post("/signup")
async def signup(user: UserCreate):
    # Vérifier si l'utilisateur existe déjà
    if user.username in USER_CREDENTIALS:
        raise HTTPException(status_code=400, detail="Username already taken")

    # Ajouter le nouvel utilisateur à la base de données
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    add_user_to_db(user.username, hashed_password)

    # Ajouter le nouvel utilisateur à USER_CREDENTIALS (en mémoire)
    USER_CREDENTIALS[user.username] = {
        'username': user.username,
        'password': hashed_password
    }

    return {"message": f"User {user.username} created successfully"}

# Fonction de vérification du mot de passe
def check_password(hashed_password: str, password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# Route pour la connexion des utilisateurs
@app.post("/login")
async def login(username: str, password: str):
    if username not in USER_CREDENTIALS:
        raise HTTPException(status_code=400, detail="Username not found")

    # Vérifier si le mot de passe est correct
    stored_password = USER_CREDENTIALS[username]["password"]
    if not check_password(stored_password, password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    return {"message": f"User {username} logged in successfully"}

# Créer une table pour les utilisateurs si elle n'existe pas
@app.on_event("startup")
def startup_event():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS utilisateurs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

    # Ajouter les utilisateurs initiaux à la base de données
    for username, credentials in USER_CREDENTIALS.items():
        add_user_to_db(credentials["username"], credentials["password"])
