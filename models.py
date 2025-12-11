from pydantic import BaseModel
from typing import List, Optional

# Modèle pour l'utilisateur
class UserCreate(BaseModel):
    nom: str
    email: str
    mot_de_passe: str

class User(BaseModel):
    id: int
    nom: str
    email: str

# Modèle pour le courrier
class Courrier(BaseModel):
    id_courrier: int
    objet: str
    heure_arrivee: str

class CourrierCreate(BaseModel):
    id_mailbox: int
    objet: str

# Modèle pour rechercher des courriers
class CourrierSearch(BaseModel):
    mot_cle: str
    date_from: Optional[str] = None
    date_to: Optional[str] = None

# Modèle pour l'état de la boîte
class MailboxStatus(BaseModel):
    etat: int  # 1 pour pleine, 0 pour vide