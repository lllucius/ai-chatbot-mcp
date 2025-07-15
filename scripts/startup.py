"""
Application startup script for database initialization and setup.

This script handles initial database setup, creates default users,
and prepares the application for first use with REQUIRED FastMCP integration.

Generated on: 2025-07-14 04:20:12 UTC
Current User: lllucius
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the app
sys.path.append(str(Path(__file__).parent.parent))

from app.config import settings
from app.database import init_db, AsyncSessionLocal
from app.models.user import User
from app.utils.security import get_password_hash
from app.utils.logging import setup_logging

logger = logging.getLogger(__name__)


async def create_default_admin():
    """Create default admin user if it doesn't exist."""
    async with AsyncSessionLocal() as db:
        try:
            # Check if admin user already exists
            from sqlalchemy import select
            result = await db.execute(
                select(User).where(User.username == "admin")
            )
            existing_admin = result.scalar_one_or_none()
            
            if existing_admin:
                logger.info("Admin user already exists")
                return existing_admin
            
            # Create admin user
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("Admin123!"),
                full_name="System Administrator",
                is_active=True,
                is_superuser=True
            )
            
            db.add(admin_user)
            await db.commit()
            await db.refresh(admin_user)
            
            logger.info("Default admin user created successfully")
            logger.info("Username: admin")
            logger.info("Email: admin@example.com") 
            logger.info("Password: Admin123!")
            logger.warning("⚠️  IMPORTANT: Change the default password immediately in production!")
            
            return admin_user
            
        except Exception as e:
            logger.error(f"Failed to create admin user: {e}")
            await db.rollback()
            raise


async def check_database_connection():
    """Test database connection."""
    try:
        async with AsyncSessionLocal() as db:
            from sqlalchemy import text
            await db.execute(text("SELECT 1"))
            logger.info("✅ Database connection successful")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


async def check_openai_connection():
    """Test OpenAI API connection."""
    try:
        from app.services.openai_client import OpenAIClient
        
        if settings.openai_api_key == "your-openai-api-key-here":
            logger.warning("⚠️  OpenAI API key not configured - using placeholder")
            return False
        
        client = OpenAIClient()
        health_result = await client.health_check()
        
        if health_result.get("openai_available") and health_result.get("status") == "healthy":
            chat_available = health_result.get("chat_model_available", False)
            embedding_available = health_result.get("embedding_model_available", False)
            
            if chat_available and embedding_available:
                logger.info("✅ OpenAI API connection successful (chat + embeddings)")
                return True
            elif chat_available:
                logger.warning("⚠️  OpenAI chat model available, but embedding model failed")
                return True
            else:
                logger.warning("⚠️  OpenAI API connection failed - models not available")
                return False
        else:
            error_msg = health_result.get("error", "Unknown error")
            logger.warning(f"⚠️  OpenAI API connection failed: {error_msg}")
            return False
            
    except Exception as e:
        logger.warning(f"⚠️  OpenAI API connection failed: {e}")
        return False


async def check_fastmcp_services():
    """
    Test FastMCP services connection.
    
    FastMCP is REQUIRED - this will fail startup if not available.
    """
    try:
        from app.services.mcp_client import get_mcp_client
        
        # FastMCP is required - this should always be enabled
        if not settings.mcp_enabled:
            logger.error("❌ FastMCP is disabled but required for this application")
            return False
        
        logger.info("🔧 Initializing REQUIRED FastMCP services...")
        mcp_client = await get_mcp_client()
        health = await mcp_client.health_check()
        
        if not health.get("fastmcp_available"):
            logger.error("❌ FastMCP not available but required for this application")
            return False
        
        healthy_servers = health.get("healthy_servers", 0)
        total_servers = health.get("total_servers", 0)
        tools_count = health.get("tools_count", 0)
        
        if healthy_servers == 0:
            logger.error("❌ No FastMCP servers are healthy - at least one is required")
            return False
        
        logger.info(f"✅ FastMCP services: {healthy_servers}/{total_servers} servers healthy")
        logger.info(f"🛠️  Total tools available: {tools_count}")
        
        # Log individual server status
        for server_name, status in health.get("server_status", {}).items():
            if status.get("status") == "healthy":
                server_tools_count = status.get("tools_count", 0)
                logger.info(f"   ✅ {server_name}: {server_tools_count} tools available")
            else:
                error = status.get("error", "Unknown error")
                logger.warning(f"   ❌ {server_name}: {error}")
        
        # Check if we have required servers
        server_status = health.get("server_status", {})
        required_servers = ["filesystem", "memory"]  # These are required
        
        for required_server in required_servers:
            if required_server not in server_status or server_status[required_server].get("status") != "healthy":
                logger.warning(f"⚠️  Required server '{required_server}' is not healthy")
        
        return True
            
    except Exception as e:
        logger.error(f"❌ FastMCP services failed (REQUIRED): {e}")
        return False


async def setup_directories():
    """Create necessary directories."""
    directories = [
        settings.upload_directory,
        "logs",
        "migrations/versions"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Directory ensured: {directory}")


async def setup_mcp_workspace():
    """
    Setup MCP workspace directory.
    
    This is REQUIRED for the filesystem server to function.
    """
    try:
        mcp_workspace = "/tmp/mcp_workspace"
        Path(mcp_workspace).mkdir(parents=True, exist_ok=True)
        
        # Create example files for the filesystem server
        readme_content = """# MCP Workspace - REQUIRED

This is the workspace directory for the FastMCP filesystem server.
The AI assistant can read and write files in this directory.

Generated on: 2025-07-14 04:20:12
Current User: lllucius

## Available Operations
- Read files
- Write files  
- List directory contents
- Create directories

## Example Usage
Ask the AI assistant to:
- "Create a file called hello.txt with a greeting"
- "List the files in the workspace"
- "Read the contents of README.md"
- "Create a Python script that prints 'Hello World'"

## Important Notes
- This workspace is REQUIRED for the filesystem MCP server
- Files in this directory can be accessed by the AI assistant
- This enables powerful file manipulation capabilities
"""
        
        (Path(mcp_workspace) / "README.md").write_text(readme_content)
        
        # Create a sample Python file
        sample_python = '''#!/usr/bin/env python3
"""
Sample Python file in MCP workspace.
Generated on: 2025-07-14 04:20:12
Current User: lllucius
"""

def greet(name: str = "World") -> str:
    """Return a greeting message."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet())
    print("This file was created by the FastMCP initialization process.")
'''
        
        (Path(mcp_workspace) / "sample.py").write_text(sample_python)
        
        logger.info(f"✅ MCP workspace setup at: {mcp_workspace}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to setup MCP workspace (REQUIRED): {e}")
        return False


async def run_startup():
    """Run complete startup sequence with REQUIRED FastMCP."""
    logger.info("🚀 Starting AI Chatbot Platform initialization...")
    logger.info("🔧 FastMCP integration is REQUIRED for this application")
    
    try:
        # Setup logging
        setup_logging()
        logger.info("📝 Logging configured")
        
        # Create directories
        await setup_directories()
        
        # Setup MCP workspace (REQUIRED)
        mcp_workspace_ok = await setup_mcp_workspace()
        if not mcp_workspace_ok:
            logger.error("❌ MCP workspace setup failed - this is REQUIRED")
            return False
        
        # Test database connection
        db_ok = await check_database_connection()
        if not db_ok:
            logger.error("❌ Database connection failed - cannot continue")
            return False
        
        # Initialize database
        logger.info("🔧 Initializing database...")
        await init_db()
        logger.info("✅ Database initialized successfully")
        
        # Create default admin user
        logger.info("👤 Creating default admin user...")
        await create_default_admin()
        
        # Test REQUIRED FastMCP services
        logger.info("🔧 Testing REQUIRED FastMCP services...")
        fastmcp_ok = await check_fastmcp_services()
        if not fastmcp_ok:
            logger.error("❌ FastMCP services failed - this is REQUIRED for the application")
            logger.error("   Please ensure:")
            logger.error("   1. npm install -g @modelcontextprotocol/server-filesystem")
            logger.error("   2. npm install -g @modelcontextprotocol/server-memory")
            logger.error("   3. pip install fastmcp")
            return False
        
        # Test OpenAI (optional but recommended)
        logger.info("🤖 Testing OpenAI API connection...")
        openai_ok = await check_openai_connection()
        
        logger.info("🎉 Initialization completed successfully!")
        logger.info("")
        logger.info("=" * 60)
        logger.info("🚀 AI CHATBOT PLATFORM READY")
        logger.info("=" * 60)
        logger.info(f"📊 Application: {settings.app_name} v{settings.app_version}")
        logger.info(f"🌐 Debug mode: {'ON' if settings.debug else 'OFF'}")
        logger.info(f"📁 Upload directory: {settings.upload_directory}")
        logger.info(f"🤖 OpenAI: {'✅ Ready' if openai_ok else '⚠️  Not configured (optional)'}")
        logger.info(f"🔧 FastMCP: {'✅ Ready (REQUIRED)' if fastmcp_ok else '❌ FAILED (REQUIRED)'}")
        logger.info("🔐 Admin credentials:")
        logger.info("   Username: admin")
        logger.info("   Email: admin@example.com")
        logger.info("   Password: Admin123!")
        logger.info("")
        logger.info("🚦 To start the application:")
        logger.info("   uvicorn app.main:app --reload")
        logger.info("")
        logger.info("📚 API Documentation will be available at:")
        logger.info("   http://localhost:8000/docs")
        logger.info("")
        logger.info("🛠️  FastMCP Tools Available (REQUIRED):")
        logger.info("   ✅ File system operations (filesystem server)")
        logger.info("   ✅ Memory management (memory server)")
        logger.info("   ⚠️  Web search (brave_search server - optional)")
        logger.info("")
        logger.info("💡 The AI assistant can now:")
        logger.info("   - Read and write files in /tmp/mcp_workspace")
        logger.info("   - Remember information across conversations")
        logger.info("   - Execute file operations and system tasks")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_startup())
    if not success:
        logger.error("❌ STARTUP FAILED - FastMCP is REQUIRED but not working")
        logger.error("   Install required components:")
        logger.error("   pip install fastmcp")
        logger.error("   npm install -g @modelcontextprotocol/server-filesystem")
        logger.error("   npm install -g @modelcontextprotocol/server-memory")
    sys.exit(0 if success else 1)