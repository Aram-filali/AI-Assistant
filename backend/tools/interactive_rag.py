"""Interactive RAG Testing Script"""

import asyncio
import httpx
import json
from getpass import getpass

BASE_URL = "http://localhost:8000"

class InteractiveTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {}
        self.kb_id = None
    
    async def run(self):
        """Run interactive test"""
        print("\n🤖 RAG System Interactive Tester\n")
        
        # Login
        await self.login()
        
        while True:
            print("\n" + "=" * 60)
            print("📋 MENU:")
            print("1. Create Knowledge Base")
            print("2. List Knowledge Bases")
            print("3. Upload Document")
            print("4. Add URL")
            print("5. Query RAG")
            print("6. View Stats")
            print("7. Exit")
            print("=" * 60)
            
            choice = input("\nChoix (1-7): ").strip()
            
            if choice == "1":
                await self.create_kb()
            elif choice == "2":
                await self.list_kbs()
            elif choice == "3":
                await self.upload_doc()
            elif choice == "4":
                await self.add_url()
            elif choice == "5":
                await self.query()
            elif choice == "6":
                await self.view_stats()
            elif choice == "7":
                print("\n👋 Au revoir!")
                break
            else:
                print("❌ Choix invalide")
    
    async def login(self):
        """Login user"""
        print("\n🔐 Login")
        email = input("Email: ").strip()
        password = getpass("Password: ")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/login",
                data={"username": email, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
                print("✅ Logged in!")
            else:
                print(f"❌ Login failed: {response.text}")
                exit(1)
    
    async def create_kb(self):
        """Create knowledge base"""
        print("\n📚 Create Knowledge Base")
        name = input("Name: ").strip()
        description = input("Description: ").strip()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/knowledge/bases",
                headers=self.headers,
                json={"name": name, "description": description}
            )
            
            if response.status_code == 201:
                data = response.json()
                self.kb_id = data["id"]
                print(f"✅ Created! ID: {data['id']}")
            else:
                print(f"❌ Failed: {response.text}")
    
    async def list_kbs(self):
        """List knowledge bases"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/knowledge/bases",
                headers=self.headers
            )
            
            if response.status_code == 200:
                kbs = response.json()
                print(f"\n📚 Knowledge Bases ({len(kbs)}):")
                for kb in kbs:
                    print(f"   {kb['id']}. {kb['name']} - {kb['document_count']} docs")
            else:
                print(f"❌ Failed: {response.text}")
    
    async def upload_doc(self):
        """Upload document"""
        if not self.kb_id:
            self.kb_id = int(input("Knowledge Base ID: "))
        
        file_path = input("File path: ").strip()
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(file_path, "rb") as f:
                files = {"file": f}
                response = await client.post(
                    f"{self.base_url}/knowledge/bases/{self.kb_id}/documents/upload",
                    headers=self.headers,
                    files=files
                )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Uploaded! {data['chunk_count']} chunks")
            else:
                print(f"❌ Failed: {response.text}")
    
    async def add_url(self):
        """Add URL"""
        if not self.kb_id:
            self.kb_id = int(input("Knowledge Base ID: "))
        
        url = input("URL: ").strip()
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/knowledge/bases/{self.kb_id}/documents/url",
                headers=self.headers,
                json={"url": url, "knowledge_base_id": self.kb_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Added! {data['chunk_count']} chunks")
            else:
                print(f"❌ Failed: {response.text}")
    
    async def query(self):
        """Query RAG"""
        if not self.kb_id:
            kb_input = input("Knowledge Base ID (leave empty for all): ").strip()
            self.kb_id = int(kb_input) if kb_input else None
        
        question = input("Question: ").strip()
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/knowledge/query",
                headers=self.headers,
                json={
                    "question": question,
                    "knowledge_base_id": self.kb_id,
                    "top_k": 5
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n💬 Answer:\n{data['answer']}\n")
                print(f"📊 Used {data['context_used']} chunks from {len(data.get('sources', []))} sources")
            else:
                print(f"❌ Failed: {response.text}")
    
    async def view_stats(self):
        """View stats"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/knowledge/stats",
                headers=self.headers
            )
            
            if response.status_code == 200:
                stats = response.json()
                print(f"\n📊 System Stats:")
                print(f"   Vectors: {stats['total_vectors']}")
                print(f"   Documents: {stats['total_documents']}")
                print(f"   Model: {stats['embedding_model']}")
            else:
                print(f"❌ Failed: {response.text}")


async def main():
    tester = InteractiveTester()
    await tester.run()


if __name__ == "__main__":
    asyncio.run(main())
