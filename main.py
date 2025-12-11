from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from pydantic import BaseModel
import os
import BDD  # Assure-toi d'avoir ton fichier BDD.py pour les interactions avec la base de données

app = FastAPI()

# Utiliser le chemin absolu pour accéder au dossier templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "../templates"))

# Initialisation de la base de données à chaque démarrage
@app.on_event("startup")
def startup_event():
    BDD.init_BDD()

# Modèle Pydantic pour l'utilisateur
class UserCreate(BaseModel):
    nom: str
    email: str
    mot_de_passe: str

# Modèle Pydantic pour la connexion (login)
class LoginRequest(BaseModel):
    username: str
    password: str

class CourrierCreate(BaseModel):
    id_mailbox: int
    objet: str

class CourrierSearch(BaseModel):
    mot_cle: str
    date_from: str = None
    date_to: str = None

# Rediriger vers la page de connexion lors de l'ouverture du projet
@app.get("/")
async def root():
    return RedirectResponse(url="/login")

# Route pour servir la page de connexion
@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Route pour gérer la soumission du formulaire de connexion (POST)
@app.post("/login")
async def login_user(request: Request, login_data: LoginRequest):
    username = login_data.username
    password = login_data.password
    
    # Logique pour valider les identifiants utilisateur (ex: avec la base de données)
    # Pour l'instant, on simule une connexion réussie
    return {"status": "OK", "message": f"Utilisateur {username} connecté avec succès."}

# Route pour la page d'inscription
@app.get("/signup")
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

# Route pour créer un utilisateur
@app.post("/utilisateur/ajouter")
async def create_user(user: UserCreate):
    try:
        # Ajouter l'utilisateur à la base de données
        BDD.ajouter_utilisateur(user.nom, user.email, user.mot_de_passe)
        return {"status": "OK", "message": f"Utilisateur {user.nom} ajouté."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Route pour récupérer l'état de la boîte aux lettres
@app.get("/mailbox/etat/{id_mailbox}")
async def get_mailbox_status(id_mailbox: int):
    etat = BDD.get_etat_mailbox(id_mailbox)
    return {"etat": etat}

# Route pour ajouter un courrier
@app.post("/courrier/nouveau")
async def add_new_courrier(courrier: CourrierCreate):
    try:
        BDD.nouveau_courrier(courrier.id_mailbox, courrier.objet)
        return {"status": "OK", "message": "Nouveau courrier ajouté."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Route pour récupérer l'historique des courriers
@app.get("/courrier/historique/{id_mailbox}")
async def get_mailbox_history(id_mailbox: int):
    historique = BDD.historique_courrier(id_mailbox)
    return {"historique": historique}

# Route pour rechercher un courrier
@app.post("/courrier/rechercher")
async def search_courrier(search: CourrierSearch):
    resultats = BDD.rechercher_courrier(search.mot_cle, search.date_from, search.date_to)
    return {"resultats": resultats}

# Route pour changer le mot de passe de l'utilisateur
@app.post("/utilisateur/changer_mot_de_passe")
async def change_password(mot_de_passe: str):
    try:
        # Assurez-vous de lier cette action à un utilisateur authentifié
        BDD.changer_mot_de_passe_utilisateur(mot_de_passe)
        return {"status": "OK", "message": "Mot de passe modifié avec succès."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Route pour servir la page du tableau de bord
@app.get("/dashboard")
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
