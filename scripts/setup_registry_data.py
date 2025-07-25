"""
Setup script to create default data for testing the registry functionality.

This script creates sample data including:
- Default prompt
- Sample LLM profiles
- Example MCP server registrations

"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.llm_profile_service import LLMProfileService
from app.services.mcp_registry import MCPRegistryService
from app.services.prompt_service import PromptService


async def create_default_prompt():
    """Create a default prompt."""
    try:
        default_prompt = await PromptService.create_prompt(
            name="default_assistant",
            title="Default AI Assistant",
            content="""You are a helpful, knowledgeable AI assistant. You provide accurate, helpful, and concise responses to user questions. When appropriate, you:

- Ask clarifying questions if the request is unclear
- Provide step-by-step explanations for complex topics
- Acknowledge when you don't know something
- Suggest alternatives when applicable
- Use tools when they would be helpful for the user's request

Be professional but friendly in your responses.""",
            description="Default prompt for general AI assistant interactions",
            is_default=True,
            category="general",
            tags=["assistant", "general", "helpful"],
        )
        print(f"✅ Created default prompt: {default_prompt.name}")
    except Exception as e:
        print(f"❌ Failed to create default prompt: {e}")


async def create_sample_prompts():
    """Create sample prompts for different use cases."""
    sample_prompts = [
        {
            "name": "code_review",
            "title": "Code Review Assistant",
            "content": """You are an expert code reviewer. When reviewing code, you should:

1. Check for correctness and functionality
2. Look for potential bugs or security issues
3. Evaluate code style and readability
4. Suggest improvements for performance
5. Ensure proper error handling
6. Verify documentation and comments

Provide constructive feedback with specific suggestions for improvement.""",
            "description": "Specialized prompt for code review tasks",
            "category": "development",
            "tags": ["code", "review", "development", "programming"],
        },
        {
            "name": "creative_writing",
            "title": "Creative Writing Assistant",
            "content": """You are a creative writing assistant. Help users with:

- Story development and plot ideas
- Character creation and development
- Writing style and voice
- Grammar and flow improvement
- Genre-specific guidance
- Overcoming writer's block

Be encouraging and provide detailed, actionable suggestions to improve their writing.""",
            "description": "Assistant for creative writing and storytelling",
            "category": "creative",
            "tags": ["writing", "creative", "storytelling", "literature"],
        },
        {
            "name": "technical_documentation",
            "title": "Technical Documentation Assistant",
            "content": """You are a technical documentation specialist. Help create clear, comprehensive documentation that:

- Uses clear, concise language
- Follows proper documentation structure
- Includes relevant examples and code snippets
- Considers the target audience's technical level
- Provides step-by-step instructions
- Includes troubleshooting information

Focus on making complex technical concepts accessible and actionable.""",
            "description": "Specialized assistant for technical documentation",
            "category": "documentation",
            "tags": ["documentation", "technical", "writing", "guides"],
        },
    ]

    for prompt_data in sample_prompts:
        try:
            prompt = await PromptService.create_prompt(**prompt_data)
            print(f"✅ Created sample prompt: {prompt.name}")
        except Exception as e:
            print(f"❌ Failed to create prompt {prompt_data['name']}: {e}")


async def create_default_llm_profile():
    """Create a default LLM profile."""
    try:
        default_profile = await LLMProfileService.create_profile(
            name="balanced",
            title="Balanced - General Purpose",
            description="Balanced parameters suitable for general conversation and tasks",
            is_default=True,
            temperature=0.7,
            top_p=0.9,
            max_tokens=2000,
            presence_penalty=0.0,
            frequency_penalty=0.0,
        )
        print(f"✅ Created default LLM profile: {default_profile.name}")
    except Exception as e:
        print(f"❌ Failed to create default LLM profile: {e}")


async def create_sample_llm_profiles():
    """Create sample LLM profiles for different use cases."""
    sample_profiles = [
        {
            "name": "creative",
            "title": "Creative - High Variability",
            "description": "Higher temperature for creative writing and brainstorming",
            "temperature": 1.0,
            "top_p": 0.95,
            "max_tokens": 3000,
            "presence_penalty": 0.5,
            "frequency_penalty": 0.3,
        },
        {
            "name": "precise",
            "title": "Precise - Low Variability",
            "description": "Lower temperature for factual, technical, or analytical tasks",
            "temperature": 0.3,
            "top_p": 0.8,
            "max_tokens": 1500,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0,
        },
        {
            "name": "concise",
            "title": "Concise - Short Responses",
            "description": "Optimized for brief, to-the-point responses",
            "temperature": 0.5,
            "top_p": 0.85,
            "max_tokens": 500,
            "presence_penalty": 0.2,
            "frequency_penalty": 0.1,
        },
        {
            "name": "detailed",
            "title": "Detailed - Comprehensive Responses",
            "description": "Configured for thorough, detailed explanations",
            "temperature": 0.6,
            "top_p": 0.9,
            "max_tokens": 4000,
            "presence_penalty": 0.1,
            "frequency_penalty": 0.0,
        },
    ]

    for profile_data in sample_profiles:
        try:
            profile = await LLMProfileService.create_profile(**profile_data)
            print(f"✅ Created sample LLM profile: {profile.name}")
        except Exception as e:
            print(f"❌ Failed to create profile {profile_data['name']}: {e}")


async def create_sample_mcp_servers():
    """Create sample MCP server registrations."""
    sample_servers = [
        {
            "name": "filesystem",
            "url": "http://localhost:9001/mcp",
            "description": "File system operations and management",
            "transport": "http",
            "timeout": 30,
        },
        {
            "name": "web_search",
            "url": "http://localhost:9002/mcp",
            "description": "Web search and information retrieval",
            "transport": "http",
            "timeout": 45,
        },
        {
            "name": "database",
            "url": "http://localhost:9003/mcp",
            "description": "Database query and management tools",
            "transport": "http",
            "timeout": 60,
        },
    ]

    for server_data in sample_servers:
        try:
            server = await MCPRegistryService.create_server(**server_data)
            print(f"✅ Created sample MCP server: {server.name}")
        except Exception as e:
            print(f"❌ Failed to create server {server_data['name']}: {e}")


async def main():
    """Main setup function."""
    print("🚀 Setting up default data for AI Chatbot Platform registries...")
    print()

    print("📝 Creating default and sample prompts...")
    await create_default_prompt()
    await create_sample_prompts()
    print()

    print("🎛️ Creating default and sample LLM profiles...")
    await create_default_llm_profile()
    await create_sample_llm_profiles()
    print()

    print("🔌 Creating sample MCP server registrations...")
    await create_sample_mcp_servers()
    print()

    print("✨ Setup complete! You can now test the registry functionality:")
    print("  • python manage.py prompts list")
    print("  • python manage.py profiles list")
    print("  • python manage.py mcp list-servers")
    print()


if __name__ == "__main__":
    asyncio.run(main())
