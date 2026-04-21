"""Interactive Chat & Conversation Tester"""

import asyncio
import httpx
import json
from getpass import getpass
import uuid

BASE_URL = "http://localhost:8000"

class ChatTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {}
        self.conversation_id = None
        self.kb_id = None
    
    async def run(self):
        """Run interactive chat test"""
        print("\n[Chat] Chat & Conversation Interactive Tester\n")
        
        # Login
        await self.login()
        
        while True:
            print("\n" + "=" * 60)
            print("--- MENU ---")
            print("1. List Conversations")
            print("2. Create New Conversation")
            print("3. Select Conversation")
            print("4. Send Message (Ask AI)")
            print("5. View Message History")
            print("6. Update Conversation Title")
            print("7. Delete Conversation")
            print("8. Exit")
            print("=" * 60)
            
            if self.conversation_id:
                print(f"Current Conversation ID: {self.conversation_id}")
            
            choice = input("\nChoice (1-8): ").strip()
            
            if choice == "1":
                await self.list_conversations()
            elif choice == "2":
                await self.create_conversation()
            elif choice == "3":
                await self.select_conversation()
            elif choice == "4":
                await self.ask_ai()
            elif choice == "5":
                await self.view_history()
            elif choice == "6":
                await self.update_conversation()
            elif choice == "7":
                await self.delete_conversation()
            elif choice == "8":
                print("\nAu revoir!")
                break
            else:
                print("❌ Invalid choice")
    
    async def login(self):
        """Login user"""
        print("\n[Login] Login")
        email = input("Email: ").strip()
        password = getpass("Password: ")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/auth/login",
                    data={"username": email, "password": password}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.token = data["access_token"]
                    self.headers = {"Authorization": f"Bearer {self.token}"}
                    print("[OK] Logged in!")
                else:
                    print(f"[ERROR] Login failed: {response.status_code} - {response.text}")
                    exit(1)
            except Exception as e:
                print(f"[ERROR] Connection error: {e}")
                exit(1)
    
    async def list_conversations(self):
        """List all conversations"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/chat/conversations",
                headers=self.headers
            )
            
            if response.status_code == 200:
                convs = response.json()
                print(f"\n[Convs] Conversations ({len(convs)}):")
                for c in convs:
                    print(f"   [{c['id']}] {c['title']} (Updated: {c['updated_at']})")
            else:
                print(f"[ERROR] Failed: {response.text}")
    
    async def create_conversation(self):
        """Create a new conversation"""
        title = input("Enter title (optional): ").strip() or "New Conversation"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/conversations",
                headers=self.headers,
                json={"title": title}
            )
            
            if response.status_code == 201:
                data = response.json()
                self.conversation_id = data["id"]
                print(f"[OK] Created! ID: {self.conversation_id}")
            else:
                print(f"[ERROR] Failed: {response.text}")

    async def select_conversation(self):
        """Select a conversation to work with"""
        conv_id = input("Enter conversation UUID: ").strip()
        if not conv_id:
            return
        
        try:
            uuid.UUID(conv_id)
            self.conversation_id = conv_id
            print(f"[OK] Conversation {conv_id} selected.")
        except ValueError:
            print("[ERROR] Invalid UUID format")

    async def ask_ai(self):
        """Send a message to AI"""
        if not self.conversation_id:
            print("[ERROR] No conversation selected. Create or select one first.")
            return
        
        question = input("\nQuestion: ").strip()
        if not question:
            return
            
        print("Thinking...")
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/ask",
                headers=self.headers,
                json={
                    "question": question,
                    "conversation_id": self.conversation_id,
                    "knowledge_base_id": self.kb_id
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\nAssistant:\n{data['answer']}\n")
                
                if data.get('sources'):
                    print(f"[Sources] Sources: {len(data['sources'])} chunks used.")
                
                actions = data.get('triggered_actions')
                if actions:
                    print("-" * 30)
                    print("[Trigger] AUTOMATED ACTIONS TRIGGERED:")
                    for action in actions:
                        print(f"   [Action] Type: {action['type'].upper()} | Status: {action['status'].upper()}")
                        if action['type'] == 'scoring':
                            print(f"      [Info] Ce prospect a été qualifié automatiquement.")
                    print("-" * 30)
            else:
                print(f"[ERROR] Failed: {response.status_code} - {response.text}")

    async def view_history(self):
        """View message history"""
        if not self.conversation_id:
            print("[ERROR] No conversation selected.")
            return
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/chat/conversations/{self.conversation_id}/messages",
                headers=self.headers
            )
            
            if response.status_code == 200:
                messages = response.json()
                print(f"\n[History] History for {self.conversation_id}:")
                for msg in messages:
                    role_icon = "U" if msg['role'] == "user" else "A"
                    print(f"{role_icon} {msg['role'].upper()}: {msg['content']}")
            else:
                print(f"[ERROR] Failed: {response.text}")

    async def update_conversation(self):
        """Update title"""
        if not self.conversation_id:
            print("[ERROR] No conversation selected.")
            return
            
        new_title = input("New title: ").strip()
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/chat/conversations/{self.conversation_id}",
                headers=self.headers,
                json={"title": new_title}
            )
            
            if response.status_code == 200:
                print("[OK] Updated!")
            else:
                print(f"[ERROR] Failed: {response.text}")

    async def delete_conversation(self):
        """Delete conversation"""
        if not self.conversation_id:
            print("[ERROR] No conversation selected.")
            return
            
        confirm = input(f"Are you sure you want to delete {self.conversation_id}? (y/n): ").strip().lower()
        if confirm != 'y':
            return
            
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/chat/conversations/{self.conversation_id}",
                headers=self.headers
            )
            
            if response.status_code == 204:
                print("[OK] Deleted.")
                self.conversation_id = None
            else:
                print(f"[ERROR] Failed: {response.text}")

async def main():
    tester = ChatTester()
    await tester.run()

if __name__ == "__main__":
    asyncio.run(main())
