"""Default data initialization for the AI Chatbot MCP platform.

This module contains functions to create default prompts, LLM profiles,
and sample MCP server configurations during database initialization.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.mcp_service import MCPService
from app.services.profile_service import LLMProfileService
from app.services.prompt_service import PromptService
from app.services.user import UserService
from shared.schemas.mcp import MCPServerCreateSchema

logger = logging.getLogger(__name__)


async def create_default_admin_user(db: AsyncSession):
    """Create a default admin user."""
    try:
        user_service = UserService(db)
        default_admin = await user_service.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass",
            full_name="Admin User",
            is_superuser=True,
        )
        logger.info(f"Created default admin user: {default_admin.username}")
        return default_admin
    except Exception as e:
        logger.warning(f"Failed to create default admin user: {e}")
        return None


async def create_default_prompt(db: AsyncSession):
    """Create a default prompt."""
    try:
        prompt_service = PromptService(db)
        default_prompt = await prompt_service.create_prompt(
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
        logger.info(f"Created default prompt: {default_prompt.name}")
        return default_prompt
    except Exception as e:
        logger.warning(f"Failed to create default prompt: {e}")
        return None


async def create_sample_prompts(db: AsyncSession):
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

    prompt_service = PromptService(db)
    created_count = 0
    for prompt_data in sample_prompts:
        try:
            prompt = await prompt_service.create_prompt(**prompt_data)
            logger.info(f"Created sample prompt: {prompt.name}")
            created_count += 1
        except Exception as e:
            logger.warning(f"Failed to create prompt {prompt_data['name']}: {e}")

    logger.info(f"Created {created_count}/{len(sample_prompts)} sample prompts")
    return created_count


async def create_default_llm_profile(db: AsyncSession):
    """Create a default LLM profile."""
    try:
        default_profile = {
            "name": "balanced",
            "title": "Balanced - General Purpose",
            "model_name": "llama3",
            "description": "Balanced parameters suitable for general conversation and tasks",
            "is_default": True,
            "parameters": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2000,
                "presence_penalty": 0.0,
                "frequency_penalty": 0.0,
            },
        }
        profile_service = LLMProfileService(db)
        profile = await profile_service.create_profile(**default_profile)
        logger.info(f"Created default LLM profile: {profile.name}")
        return default_profile
    except Exception as e:
        logger.warning(f"Failed to create default LLM profile: {e}")
        return None


async def create_sample_llm_profiles(db: AsyncSession):
    """Create sample LLM profiles for different use cases."""
    sample_profiles = [
        {
            "name": "creative",
            "title": "Creative - High Variability",
            "model_name": "llama3",
            "description": "Higher temperature for creative writing and brainstorming",
            "is_default": False,
            "parameters": {
                "temperature": 1.0,
                "top_p": 0.95,
                "max_tokens": 3000,
                "presence_penalty": 0.5,
                "frequency_penalty": 0.3,
            },
        },
        {
            "name": "precise",
            "title": "Precise - Low Variability",
            "model_name": "llama3",
            "description": "Lower temperature for factual, technical, or analytical tasks",
            "is_default": False,
            "parameters": {
                "temperature": 0.3,
                "top_p": 0.8,
                "max_tokens": 1500,
                "presence_penalty": 0.0,
                "frequency_penalty": 0.0,
            },
        },
        {
            "name": "concise",
            "title": "Concise - Short Responses",
            "model_name": "llama3",
            "description": "Optimized for brief, to-the-point responses",
            "is_default": False,
            "parameters": {
                "temperature": 0.5,
                "top_p": 0.85,
                "max_tokens": 500,
                "presence_penalty": 0.2,
                "frequency_penalty": 0.1,
            },
        },
        {
            "name": "detailed",
            "title": "Detailed - Comprehensive Responses",
            "model_name": "llama3",
            "description": "Configured for thorough, detailed explanations",
            "is_default": False,
            "parameters": {
                "temperature": 0.6,
                "top_p": 0.9,
                "max_tokens": 4000,
                "presence_penalty": 0.1,
                "frequency_penalty": 0.0,
            },
        },
    ]

    profile_service = LLMProfileService(db)
    created_count = 0
    for profile_data in sample_profiles:
        try:
            profile = await profile_service.create_profile(**profile_data)
            logger.info(f"Created sample LLM profile: {profile.name}")
            created_count += 1
        except Exception as e:
            logger.warning(f"Failed to create profile {profile_data['name']}: {e}")

    logger.info(f"Created {created_count}/{len(sample_profiles)} sample LLM profiles")
    return created_count


async def create_sample_mcp_servers(db: AsyncSession):
    """Create sample MCP server registrations."""
    sample_servers = [
        {
            "name": "filesystem",
            "url": "http://localhost:9001/mcp",
            "description": "File system operations and management",
            "transport": "http",
            "timeout": 30,
            "is_enabled": False,
        },
        {
            "name": "web_search",
            "url": "http://localhost:9002/mcp",
            "description": "Web search and information retrieval",
            "transport": "http",
            "timeout": 45,
            "is_enabled": False,
        },
        {
            "name": "database",
            "url": "http://localhost:9003/mcp",
            "description": "Database query and management tools",
            "transport": "http",
            "timeout": 60,
            "is_enabled": False,
        },
    ]

    mcp_service = MCPService(db)
    mcp_service.initialize()
    created_count = 0
    for server_data in sample_servers:
        try:
            server_schema = MCPServerCreateSchema(**server_data)
            server = await mcp_service.create_server(server_schema, auto_discover=False)
            logger.info(f"Created sample MCP server: {server.name}")
            created_count += 1
        except Exception as e:
            logger.warning(f"Failed to create server {server_data['name']}: {e}")

    logger.info(f"Created {created_count}/{len(sample_servers)} sample MCP servers")
    return created_count


async def create_default_jobs(db: AsyncSession):
    """Create default scheduled jobs for system maintenance and monitoring."""
    default_jobs = [
        {
            "name": "system_health_check",
            "title": "System Health Check",
            "description": "Periodic system health monitoring and alerting",
            "job_type": "system_health_check",
            "schedule_type": "interval",
            "schedule_expression": "15",  # Every 15 minutes
            "timezone": "UTC",
            "task_name": "app.tasks.system.health_check",
            "task_queue": "monitoring",
            "task_priority": 8,
            "timeout_seconds": 300,
            "max_retries": 2,
            "is_enabled": True,
            "config": {
                "check_database": True,
                "check_openai": True,
                "check_mcp_servers": True,
                "alert_on_failure": True
            }
        },
        {
            "name": "document_cleanup",
            "title": "Document Cleanup",
            "description": "Clean up old processed documents and temporary files",
            "job_type": "document_cleanup",
            "schedule_type": "daily",
            "schedule_expression": "02:00",  # Daily at 2:00 AM
            "timezone": "UTC",
            "task_name": "app.tasks.documents.cleanup_old_documents",
            "task_queue": "maintenance",
            "task_priority": 3,
            "timeout_seconds": 3600,
            "max_retries": 2,
            "is_enabled": True,
            "config": {
                "older_than_days": 30,
                "status_filter": "failed",
                "cleanup_temp_files": True
            }
        },
        {
            "name": "analytics_aggregation",
            "title": "Analytics Data Aggregation",
            "description": "Aggregate usage statistics and generate reports",
            "job_type": "analytics_aggregation",
            "schedule_type": "daily",
            "schedule_expression": "01:00",  # Daily at 1:00 AM
            "timezone": "UTC",
            "task_name": "app.tasks.analytics.aggregate_daily_stats",
            "task_queue": "analytics",
            "task_priority": 4,
            "timeout_seconds": 1800,
            "max_retries": 3,
            "is_enabled": True,
            "config": {
                "aggregate_users": True,
                "aggregate_documents": True,
                "aggregate_conversations": True,
                "retention_days": 90
            }
        },
        {
            "name": "database_maintenance",
            "title": "Database Maintenance",
            "description": "Perform database optimization and maintenance tasks",
            "job_type": "database_maintenance",
            "schedule_type": "weekly",
            "schedule_expression": "0:03:00",  # Weekly on Monday at 3:00 AM
            "timezone": "UTC",
            "task_name": "app.tasks.database.maintenance",
            "task_queue": "maintenance",
            "task_priority": 2,
            "timeout_seconds": 7200,
            "max_retries": 1,
            "is_enabled": False,  # Disabled by default, enable manually
            "config": {
                "vacuum_analyze": True,
                "reindex_tables": False,
                "update_statistics": True
            }
        },
        {
            "name": "mcp_server_health_check",
            "title": "MCP Server Health Check",
            "description": "Monitor MCP server connectivity and performance",
            "job_type": "mcp_server_health_check",
            "schedule_type": "interval",
            "schedule_expression": "30",  # Every 30 minutes
            "timezone": "UTC",
            "task_name": "app.tasks.mcp.health_check_servers",
            "task_queue": "monitoring",
            "task_priority": 6,
            "timeout_seconds": 600,
            "max_retries": 3,
            "is_enabled": True,
            "config": {
                "check_connectivity": True,
                "check_tool_availability": True,
                "update_status": True,
                "disable_on_failure": False
            }
        }
    ]

    try:
        from app.services.job_service import JobService
        from shared.schemas.job import JobCreate
        
        job_service = JobService(db)
        created_count = 0
        
        for job_data in default_jobs:
            try:
                # Check if job already exists
                existing = await job_service.get_job_by_name(job_data["name"], raise_if_not_found=False)
                if existing:
                    logger.info(f"Default job '{job_data['name']}' already exists, skipping")
                    continue
                
                # Create job
                job_schema = JobCreate(**job_data)
                job = await job_service.create_job(job_schema)
                logger.info(f"Created default job: {job.name}")
                created_count += 1
                
            except Exception as e:
                logger.warning(f"Failed to create default job {job_data['name']}: {e}")

        logger.info(f"Created {created_count}/{len(default_jobs)} default jobs")
        return created_count
        
    except Exception as e:
        logger.error(f"Failed to create default jobs: {e}")
        return 0


async def initialize_default_data(db: AsyncSession):
    """Initialize all default data for the platform."""
    logger.info("Initializing default data for AI Chatbot Platform...")

    # Create default Admin user
    default_admin = await create_default_admin_user(db)

    # Create default prompt
    default_prompt = await create_default_prompt(db)

    # Create sample prompts
    sample_prompts_count = await create_sample_prompts(db)

    # Create default LLM profile
    default_profile = await create_default_llm_profile(db)

    # Create sample LLM profiles
    sample_profiles_count = await create_sample_llm_profiles(db)

    # Create sample MCP servers
    sample_servers_count = await create_sample_mcp_servers(db)
    
    # Create default jobs
    default_jobs_count = await create_default_jobs(db)

    # Summary
    success_count = 0
    if default_prompt:
        success_count += 1
    if default_profile:
        success_count += 1
    if default_admin:
        success_count += 1

    total_created = (
        success_count
        + sample_prompts_count
        + sample_profiles_count
        + sample_servers_count
        + default_jobs_count
    )

    logger.info(f"Default data initialization complete - {total_created} items created")

    return {
        "default_prompt": default_prompt is not None,
        "default_profile": default_profile is not None,
        "sample_prompts": sample_prompts_count,
        "sample_profiles": sample_profiles_count,
        "sample_servers": sample_servers_count,
        "default_jobs": default_jobs_count,
        "total_created": total_created,
    }
