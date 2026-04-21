import asyncio
import httpx

BASE_URL = "http://127.0.0.1:8000"

async def rebuild():
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("Reconstruction de l'index FAISS en cours...")
        try:
            # Note: l'endpoint rebuild-index demande une session, mais ici on teste sans user_id si possible 
            # ou on s'authentifie comme avant.
            
            # Login d'abord
            login_res = await client.post(
                f"{BASE_URL}/auth/login",
                data={"username": "test@example.com", "password": "Test123!@#"}
            )
            token = login_res.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            response = await client.post(
                f"{BASE_URL}/knowledge/rebuild-index",
                headers=headers
            )
            
            if response.status_code == 200:
                print("Done ! L'index a ete rafraichi avec les nouveaux documents.")
            else:
                print(f"Erreur : {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"Erreur : {e}")

if __name__ == "__main__":
    asyncio.run(rebuild())
