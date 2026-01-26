import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

print("--- DIAGNOSTIC CONNEXION ---")
url = os.getenv("DATABASE_URL_SYNC")
print(f"1. URL lue : {url}")

try:
    print("2. Tentative de connexion brute avec psycopg2...")
    conn = psycopg2.connect(url)
    print("✅ SUCCÈS ! La connexion fonctionne.")
    conn.close()
except Exception as e:
    print(f"❌ ÉCHEC : {e}")
