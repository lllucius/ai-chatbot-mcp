"""
Example usage scripts demonstrating API functionality.

This script shows how to interact with the AI Chatbot Platform API
programmatically for common operations.

"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

# Add the parent directory to the path so we can import the app
sys.path.append(str(Path(__file__).parent.parent))


class APIClient:
    """Simple API client for demonstration."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize API client."""
        self.base_url = base_url
        self.token: Optional[str] = None
        self.client = httpx.AsyncClient()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def register(
        self, username: str, email: str, password: str, full_name: str = None
    ) -> Dict[str, Any]:
        """Register a new user."""
        data = {"username": username, "email": email, "password": password}
        if full_name:
            data["full_name"] = full_name

        response = await self.client.post(
            f"{self.base_url}/api/v1/auth/register",
            json=data,
            headers=self._get_headers(),
        )
        return response.json()

    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login and store token."""
        data = {"username": username, "password": password}

        response = await self.client.post(
            f"{self.base_url}/api/v1/auth/login", json=data, headers=self._get_headers()
        )

        result = response.json()
        if "access_token" in result:
            self.token = result["access_token"]

        return result

    async def get_profile(self) -> Dict[str, Any]:
        """Get current user profile."""
        response = await self.client.get(
            f"{self.base_url}/api/v1/users/me", headers=self._get_headers()
        )
        return response.json()

    async def upload_document(
        self, file_path: str, title: str = None
    ) -> Dict[str, Any]:
        """Upload a document."""
        with open(file_path, "rb") as f:
            files = {"file": f}
            data = {}
            if title:
                data["title"] = title

            response = await self.client.post(
                f"{self.base_url}/api/v1/documents/upload",
                files=files,
                data=data,
                headers={"Authorization": f"Bearer {self.token}"} if self.token else {},
            )

        return response.json()

    async def list_documents(self) -> Dict[str, Any]:
        """List user documents."""
        response = await self.client.get(
            f"{self.base_url}/api/v1/documents/", headers=self._get_headers()
        )
        return response.json()

    async def search_documents(
        self, query: str, algorithm: str = "hybrid"
    ) -> Dict[str, Any]:
        """Search documents."""
        data = {"query": query, "algorithm": algorithm, "limit": 5, "threshold": 0.7}

        response = await self.client.post(
            f"{self.base_url}/api/v1/search/", json=data, headers=self._get_headers()
        )
        return response.json()

    async def chat(
        self, message: str, conversation_id: int = None, use_rag: bool = True
    ) -> Dict[str, Any]:
        """Send a chat message."""
        data = {
            "user_message": message,
            "use_rag": use_rag,
            "use_tools": True,
            "temperature": 0.7,
        }

        if conversation_id:
            data["conversation_id"] = conversation_id

        response = await self.client.post(
            f"{self.base_url}/api/v1/conversations/chat",
            json=data,
            headers=self._get_headers(),
        )
        return response.json()

    async def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        response = await self.client.get(f"{self.base_url}/api/v1/health/")
        return response.json()


async def demonstrate_workflow():
    """Demonstrate a complete workflow."""
    client = APIClient()

    try:
        print("🤖 AI Chatbot Platform API Demo")
        print("=" * 50)

        # Health check
        print("1. 🏥 Checking API health...")
        health = await client.health_check()
        print(f"   Status: {health.get('status', 'unknown')}")

        # Login with default admin (assuming it exists)
        print("\n2. 🔐 Logging in...")
        login_result = await client.login("admin", "Admin123!")
        if "access_token" in login_result:
            print("   ✅ Login successful")
        else:
            print("   ❌ Login failed - make sure to run startup.py first")
            return

        # Get profile
        print("\n3. 👤 Getting user profile...")
        profile = await client.get_profile()
        print(f"   User: {profile.get('username')} ({profile.get('email')})")

        # Create a sample text file for upload
        print("\n4. 📄 Creating sample document...")
        sample_content = """
        Artificial Intelligence (AI) is a branch of computer science that aims to create
        intelligent machines that work and react like humans. Some of the activities
        computers with artificial intelligence are designed for include:

        - Speech recognition
        - Learning
        - Planning
        - Problem solving

        Machine Learning is a subset of AI that provides systems the ability to
        automatically learn and improve from experience without being explicitly programmed.

        Deep Learning is a subset of machine learning that uses neural networks with
        three or more layers to simulate the behavior of the human brain.
        """

        sample_file = Path("sample_ai_doc.txt")
        sample_file.write_text(sample_content)
        print(f"   Created: {sample_file}")

        # Upload document
        print("\n5. ⬆️ Uploading document...")
        upload_result = await client.upload_document(
            str(sample_file), "AI Introduction"
        )
        if upload_result.get("success"):
            doc_id = upload_result["document"]["id"]
            print(f"   ✅ Document uploaded (ID: {doc_id})")
        else:
            print("   ❌ Upload failed")
            return

        # Wait a moment for processing
        print("\n6. ⏳ Waiting for document processing...")
        await asyncio.sleep(3)

        # List documents
        print("\n7. 📋 Listing documents...")
        docs = await client.list_documents()
        if docs.get("success") and docs.get("items"):
            for doc in docs["items"][:3]:  # Show first 3
                status = doc["processing_status"]
                print(f"   📄 {doc['title']} - Status: {status}")

        # Search documents
        print("\n8. 🔍 Searching documents...")
        search_result = await client.search_documents("What is machine learning?")
        if search_result.get("success") and search_result.get("results"):
            print(f"   Found {len(search_result['results'])} results:")
            for i, result in enumerate(search_result["results"][:2], 1):
                score = result.get("similarity_score", 0)
                content_preview = result["content"][:100] + "..."
                print(f"   {i}. Score: {score:.3f} - {content_preview}")

        # Chat with AI
        print("\n9. 💬 Chatting with AI...")
        chat_result = await client.chat(
            "What is the difference between AI and machine learning?"
        )
        if chat_result.get("success"):
            ai_response = chat_result["ai_message"]["content"]
            print(f"   🤖 AI: {ai_response[:200]}...")

            # Follow-up question
            conv_id = chat_result["conversation"]["id"]
            followup = await client.chat("Can you give me an example?", conv_id)
            if followup.get("success"):
                followup_response = followup["ai_message"]["content"]
                print(f"   🤖 AI: {followup_response[:200]}...")

        # Clean up
        sample_file.unlink(missing_ok=True)

        print("\n✅ Demo completed successfully!")
        print("\n📚 Try the interactive API docs at: http://localhost:8000/docs")

    except Exception as e:
        print(f"❌ Demo failed: {e}")

    finally:
        await client.close()


async def demonstrate_registration():
    """Demonstrate user registration flow."""
    client = APIClient()

    try:
        print("👤 User Registration Demo")
        print("=" * 30)

        # Register new user
        print("1. 📝 Registering new user...")
        reg_result = await client.register(
            username="test_user",
            email="test@mycompany.com",
            password="SecureTestPass123!",
            full_name="Test User",
        )

        if reg_result.get("username"):
            print(f"   ✅ User registered: {reg_result['username']}")

            # Login with new user
            print("\n2. 🔐 Logging in with new user...")
            login_result = await client.login("test_user", "SecureTestPass123!")
            if "access_token" in login_result:
                print("   ✅ Login successful")

                # Get profile
                profile = await client.get_profile()
                print(
                    f"   👤 Profile: {profile.get('full_name')} ({profile.get('email')})"
                )
            else:
                print("   ❌ Login failed")
        else:
            print(f"   ❌ Registration failed: {reg_result}")

    except Exception as e:
        print(f"❌ Registration demo failed: {e}")

    finally:
        await client.close()


def show_usage():
    """Show usage examples."""
    print("🔧 EXAMPLE USAGE SCRIPTS")
    print("=" * 40)
    print("Run complete workflow demo:")
    print("  python scripts/example_usage.py workflow")
    print()
    print("Run registration demo:")
    print("  python scripts/example_usage.py register")
    print()
    print("NOTE: Make sure the application is running:")
    print("  uvicorn app.main:app --reload")
    print("=" * 40)


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        show_usage()
        return

    command = sys.argv[1]

    if command == "workflow":
        await demonstrate_workflow()
    elif command == "register":
        await demonstrate_registration()
    else:
        show_usage()


if __name__ == "__main__":
    asyncio.run(main())
