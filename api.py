from fastapi import FastAPI
from pydantic import BaseModel
from BDD import (  # Import des fonctions
    init_BDD,
    ajouter_utilisateur,
    supprimer_utilisateur,
    nouveau_courrier,
    modifier_objet_courrier,
    historique_courrier,
    rechercher_courrier,
    get_etat_mailbox,
    vider_mailbox
)

app = FastAPI()

# Init database
@app.on_event("startup")
def on_startup():
    init_BDD()

# Modèle Pydantic pour l'utilisateur
class UserCreate(BaseModel):
    nom: str
    mot_de_passe: str
    id_mailbox: int

class CourrierCreate(BaseModel):
    id_mailbox: int
    objet: str

# Exemple d'API pour ajouter un utilisateur
@app.post("/utilisateur/ajouter")
async def api_ajouter_utilisateur(user: UserCreate):
    ajouter_utilisateur(user.nom, user.mot_de_passe, user.id_mailbox)
    return {"status": "OK", "message": f"Utilisateur {user.nom} ajouté."}

@app.post("/courrier/nouveau")
async def api_nouveau_courrier(data: CourrierCreate):
    nouveau_courrier(data.id_mailbox, data.objet)
    return {"status": "OK", "message": "Nouveau courrier ajouté."}

@app.get("/mailbox/etat/{id_mailbox}")
async def api_get_etat(id_mailbox: int):
    etat = get_etat_mailbox(id_mailbox)
    return {"etat": etat}

@app.get("/courrier/historique/{id_mailbox}")
async def api_historique(id_mailbox: int):
    historique = historique_courrier(id_mailbox)
    return {"historique": historique}

# Recherche de courrier
@app.get("/courrier/rechercher/{id_mailbox}/{mot_cle}")
async def api_rechercher(id_mailbox: int, mot_cle: str):
    resultats = rechercher_courrier(id_mailbox, mot_cle)
    return {"resultats": resultats}

@app.post("/mailbox/vider/{id_mailbox}")
async def api_vider_mailbox(id_mailbox: int):
    vider_mailbox(id_mailbox)
    return {"status": "OK", "message": "Mailbox vidée."}

@app.post("/init_bdd")
async def init_database():
    init_BDD()
    return {"status": "OK", "message": "Base de données initialisée."}
