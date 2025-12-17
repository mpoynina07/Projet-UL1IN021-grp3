import uvicorn
from app import app
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sys

# Configuration du serveur
HOST = "0.0.0.0"
PORT = 8000

# Nous ajoutons les routes statiques et les pages ici pour garantir qu'elles sont définies
# avant le lancement d'Uvicorn.

try:
    print("Configuration des routes web...")
    # Montage des fichiers statiques
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Routes pour les pages principales
    @app.get("/")
    async def serve_login(): 
        return FileResponse("static/login.html")
        
    @app.get("/dashboard")
    async def serve_dashboard(): 
        return FileResponse("static/dashboard.html")
    
    # Lance Uvicorn
    print(f"Démarrage du serveur Uvicorn sur http://{HOST}:{PORT}")
    # Uvicorn utilise la variable 'app' importée de 'app.py'
    uvicorn.run(app, host=HOST, port=PORT)

except KeyboardInterrupt:
    print("\nArrêt manuel du serveur...")
    
except Exception as e:
    print(f"Erreur fatale lors du lancement: {e}", file=sys.stderr)
    print("Veuillez vérifier vos dépendances (fastapi, uvicorn, RPi.GPIO).", file=sys.stderr)
