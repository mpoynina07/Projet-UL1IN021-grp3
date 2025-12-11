from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import BDD  # Assure-toi d'avoir le fichier BDD.py pour les interactions avec la base de données

app = FastAPI()

# Initialisation de la base de données à chaque démarrage
@app.on_event("startup")
def startup_event():
    BDD.init_BDD()

# Modèle Pydantic pour l'utilisateur
class UserCreate(BaseModel):
    nom: str
    email: str
    mot_de_passe: str

class CourrierCreate(BaseModel):
    id_mailbox: int
    objet: str

class CourrierSearch(BaseModel):
    mot_cle: str
    date_from: str = None
    date_to: str = None

# Route pour créer un utilisateur
@app.post("/utilisateur/ajouter")
async def create_user(user: UserCreate):
    try:
        BDD.ajouter_utilisateur(user.nom, user.email, user.mot_de_passe)
        return {"status": "OK", "message": f"Utilisateur {user.nom} ajouté."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Route pour récupérer l'état de la boîte
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
        # Exemple: BDD.changer_mot_de_passe_utilisateur(user_id, mot_de_passe)
        BDD.changer_mot_de_passe_utilisateur(mot_de_passe)
        return {"status": "OK", "message": "Mot de passe modifié avec succès."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))