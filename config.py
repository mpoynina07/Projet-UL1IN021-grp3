import os
import bcrypt
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Configuration de la base de données
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mailbox.db")

# Clé secrète pour l'API
SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")

# Liste des utilisateurs avec leurs identifiants et mots de passe hachés
def hash_password(password: str) -> str:
    """Fonction pour hasher le mot de passe"""
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

USER_CREDENTIALS = {
    'admin': {
        'username': 'admin',
        'password': hash_password('admin123')
    },
    'user1': {
        'username': 'user1',
        'password': hash_password('user123')
    },
    'user2': {
        'username': 'user2',
        'password': hash_password('user456')
    }
}

# Configuration de l'application (FastAPI)
HOST = "127.0.0.1"
PORT = 8000