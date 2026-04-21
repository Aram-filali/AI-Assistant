import asyncio
import httpx
import os

# Configuration
KB_ID = "debd4568-7987-4af0-833d-b60f9bf01d83"
BASE_URL = "http://127.0.0.1:8000"
FILE_NAME = "test_ia.txt"
FILE_CONTENT = """
L'intelligence artificielle (IA) est un domaine de l'informatique qui vise a creer des systemes capables de simuler l'intelligence humaine.
Elle comprend l'apprentissage automatique (machine learning), le traitement du langage naturel et la vision par ordinateur.
L'objectif est de permettre aux machines de resoudre des problemes complexes, de prendre des decisions et d'apprendre au fil du temps.
"""

async def fill_kb():
    # 1. Creer le fichier texte de test
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        f.write(FILE_CONTENT)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("Connexion...")
            login_res = await client.post(
                f"{BASE_URL}/auth/login",
                data={"username": "test@example.com", "password": "Test123!@#"}
            )
            
            if login_res.status_code != 200:
                print(f"Erreur login : {login_res.text}")
                return
                
            token = login_res.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 2. Upload du fichier
            print(f"Upload du fichier {FILE_NAME}...")
            files = {"file": (FILE_NAME, open(FILE_NAME, "rb"), "text/plain")}
            res = await client.post(
                f"{BASE_URL}/knowledge/bases/{KB_ID}/documents/upload",
                headers=headers,
                files=files
            )
            
            if res.status_code == 200:
                print("Done ! Le fichier a ete ajoute et indexe.")
                print("Vous pouvez maintenant relancer 'python test_hybrid_rag.py'")
            else:
                print(f"Erreur upload : {res.status_code}")
                print(res.text)
    finally:
        # Nettoyage
        if os.path.exists(FILE_NAME):
            os.remove(FILE_NAME)

if __name__ == "__main__":
    asyncio.run(fill_kb())
