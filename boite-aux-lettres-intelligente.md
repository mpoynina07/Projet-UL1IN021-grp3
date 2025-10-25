boite-aux-lettres-intelligente/

│

├── raspberry/                

│   ├── capteur\_ultrason.py        # presence lettre
     
│   ├── actionneurs.py             # LED + buzzer + ecran

│   ├── main.py                    

│   	               

├── database/

│   ├── model.py                   # enregistrer donnees

│   └── boite.db                   # Bdd SQLite (courrier, ouverture, historique)

│

├── web/                      ← Site web pour consultation et interaction

│   ├── app.py                     # site web

│   ├── templates/

│   │   ├── index.html             # page d accueil + etat de la boîte

│   │   ├── historique.html        # page d historique 

│   │   ├── style.css              # design site

│   

├── tests/                    ← tests sur capteurs

│   └── test\_capteurs.py

│

├── README.md                 ← presentation projet





