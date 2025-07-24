"Core default_data functionality and business logic."

import logging
from app.services.llm_profile_service import LLMProfileService
from app.services.mcp_registry import MCPRegistryService
from app.services.prompt_service import PromptService

logger = logging.getLogger(__name__)


async def create_default_prompt():
    "Create new default prompt."
    try:
        default_prompt = await PromptService.create_prompt(
            name="default_assistant",
            title="Default AI Assistant",
            content="You are a helpful, knowledgeable AI assistant. You provide accurate, helpful, and concise responses to user questions. When appropriate, you:\n\n- Ask clarifying questions if the request is unclear\n- Provide step-by-step explanations for complex topics\n- Acknowledge when you don't know something\n- Suggest alternatives when applicable\n- Use tools when they would be helpful for the user's request\n\nBe professional but friendly in your responses.",
            description="Default prompt for general AI assistant interactions",
            is_default=True,
            category="general",
            tags=["assistant", "general", "helpful"],
        )
        logger.info(f"Created default prompt: {default_prompt.name}")
        return default_prompt
    except Exception as e:
        logger.warning(f"Failed to create default prompt: {e}")
        return None


async def create_sample_prompts():
    "Create new sample prompts."
    sample_prompts = [
        {
            "name": "code_review",
            "title": "Code Review Assistant",
            "content": "You are an expert code reviewer. When reviewing code, you should:\n\n1. Check for correctness and functionality\n2. Look for potential bugs or security issues\n3. Evaluate code style and readability\n4. Suggest improvements for performance\n5. Ensure proper error handling\n6. Verify documentation and comments\n\nProvide constructive feedback with specific suggestions for improvement.",
            "description": "Specialized prompt for code review tasks",
            "category": "development",
            "tags": ["code", "review", "development", "programming"],
        },
        {
            "name": "creative_writing",
            "title": "Creative Writing Assistant",
            "content": "You are a creative writing assistant. Help users with:\n\n- Story development and plot ideas\n- Character creation and development\n- Writing style and voice\n- Grammar and flow improvement\n- Genre-specific guidance\n- Overcoming writer's block\n\nBe encouraging and provide detailed, actionable suggestions to improve their writing.",
            "description": "Assistant for creative writing and storytelling",
            "category": "creative",
            "tags": ["writing", "creative", "storytelling", "literature"],
        },
        {
            "name": "technical_documentation",
            "title": "Technical Documentation Assistant",
            "content": "You are a technical documentation specialist. Help create clear, comprehensive documentation that:\n\n- Uses clear, concise language\n- Follows proper documentation structure\n- Includes relevant examples and code snippets\n- Considers the target audience's technical level\n- Provides step-by-step instructions\n- Includes troubleshooting information\n\nFocus on making complex technical concepts accessible and actionable.",
            "description": "Specialized assistant for technical documentation",
            "category": "documentation",
            "tags": ["documentation", "technical", "writing", "guides"],
        },
    ]
    created_count = 0
    for prompt_data in sample_prompts:
        try:
            prompt = await PromptService.create_prompt(**prompt_data)
            logger.info(f"Created sample prompt: {prompt.name}")
            created_count += 1
        except Exception as e:
            logger.warning(f"Failed to create prompt {prompt_data['name']}: {e}")
    logger.info(f"Created {created_count}/{len(sample_prompts)} sample prompts")
    return created_count


async def create_default_llm_profile():
    "Create new default llm profile."
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
        logger.info(f"Created default LLM profile: {default_profile.name}")
        return default_profile
    except Exception as e:
        logger.warning(f"Failed to create default LLM profile: {e}")
        return None


async def create_sample_llm_profiles():
    "Create new sample llm profiles."
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
    created_count = 0
    for profile_data in sample_profiles:
        try:
            profile = await LLMProfileService.create_profile(**profile_data)
            logger.info(f"Created sample LLM profile: {profile.name}")
            created_count += 1
        except Exception as e:
            logger.warning(f"Failed to create profile {profile_data['name']}: {e}")
    logger.info(f"Created {created_count}/{len(sample_profiles)} sample LLM profiles")
    return created_count


async def create_sample_mcp_servers():
    "Create new sample mcp servers."
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
    created_count = 0
    for server_data in sample_servers:
        try:
            server = await MCPRegistryService.create_server(**server_data)
            logger.info(f"Created sample MCP server: {server.name}")
            created_count += 1
        except Exception as e:
            logger.warning(f"Failed to create server {server_data['name']}: {e}")
    logger.info(f"Created {created_count}/{len(sample_servers)} sample MCP servers")
    return created_count


async def initialize_default_data():
    "Initialize Default Data operation."
    logger.info("Initializing default data for AI Chatbot Platform...")
    default_prompt = await create_default_prompt()
    sample_prompts_count = await create_sample_prompts()
    default_profile = await create_default_llm_profile()
    sample_profiles_count = await create_sample_llm_profiles()
    sample_servers_count = await create_sample_mcp_servers()
    success_count = 0
    if default_prompt:
        success_count += 1
    if default_profile:
        success_count += 1
    total_created = (
        (success_count + sample_prompts_count) + sample_profiles_count
    ) + sample_servers_count
    logger.info(f"Default data initialization complete - {total_created} items created")
    return {
        "default_prompt": (default_prompt is not None),
        "default_profile": (default_profile is not None),
        "sample_prompts": sample_prompts_count,
        "sample_profiles": sample_profiles_count,
        "sample_servers": sample_servers_count,
        "total_created": total_created,
    }
