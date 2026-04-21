import sys
import os

# Ajouter le dossier actuel au path pour l'import 'app'
sys.path.append(os.getcwd())

try:
    from app.main import app
    print("--- Liste des routes enregistrees dans l'application ---")
    for route in app.routes:
        if hasattr(route, 'path'):
            methods = getattr(route, 'methods', 'GET')
            print(f"{methods} {route.path}")
except Exception as e:
    print(f"Erreur lors de l'inspection des routes : {e}")
