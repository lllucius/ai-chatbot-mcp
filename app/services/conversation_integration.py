"""
Integration example showing how to use the prompt and profile registries
in conversation services.

This demonstrates how the existing conversation service can be enhanced
to use the new registry systems.

Current Date and Time (UTC): 2025-07-23 03:55:00
Current User: lllucius / assistant
"""

from typing import Any, Dict, Optional

from ..services.enhanced_mcp_client import get_enhanced_mcp_client
from ..services.llm_profile_service import LLMProfileService
from ..services.prompt_service import PromptService
from ..utils.logging import get_api_logger

logger = get_api_logger("conversation_integration")


class EnhancedConversationService:
    """
    Enhanced conversation service that integrates with registries.

    This shows how the existing conversation service can be updated
    to use prompts, profiles, and enhanced MCP tools.
    """

    @staticmethod
    async def prepare_chat_request(
        user_message: str,
        prompt_name: Optional[str] = None,
        profile_name: Optional[str] = None,
        use_tools: bool = True,
        **additional_params,
    ) -> Dict[str, Any]:
        """
        Prepare a chat request using the registry systems.

        Args:
            user_message: The user's message
            prompt_name: Optional specific prompt to use (defaults to default prompt)
            profile_name: Optional specific profile to use (defaults to default profile)
            use_tools: Whether to include MCP tools
            additional_params: Additional parameters to override profile settings

        Returns:
            dict: Prepared chat request parameters
        """

        # Get the system prompt
        if prompt_name:
            prompt = await PromptService.get_prompt(prompt_name)
            if not prompt:
                logger.warning(f"Prompt '{prompt_name}' not found, using default")
                prompt = await PromptService.get_default_prompt()
        else:
            prompt = await PromptService.get_default_prompt()

        if not prompt:
            logger.warning("No default prompt found, using fallback")
            system_content = "You are a helpful AI assistant."
        else:
            system_content = prompt.content
            # Record prompt usage
            await PromptService.record_prompt_usage(prompt.name)

        # Get LLM parameters from profile
        if profile_name:
            llm_params = await LLMProfileService.get_profile_for_openai(profile_name)
        else:
            llm_params = await LLMProfileService.get_profile_for_openai()

        # Override with any additional parameters
        llm_params.update(additional_params)

        # Prepare messages
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_message},
        ]

        # Prepare the base request
        chat_request = {"messages": messages, **llm_params}

        # Add tools if requested
        if use_tools:
            try:
                enhanced_client = await get_enhanced_mcp_client()
                tools = await enhanced_client.get_tools_for_openai(enabled_only=True)
                if tools:
                    chat_request["tools"] = tools
                    chat_request["tool_choice"] = "auto"
                    logger.info(f"Added {len(tools)} tools to chat request")
            except Exception as e:
                logger.warning(f"Failed to add tools to chat request: {e}")

        return chat_request

    @staticmethod
    async def execute_tool_calls(tool_calls: list) -> list:
        """Execute tool calls using the enhanced MCP client."""
        try:
            enhanced_client = await get_enhanced_mcp_client()
            return await enhanced_client.execute_tool_calls(tool_calls)
        except Exception as e:
            logger.error(f"Failed to execute tool calls: {e}")
            return []

    @staticmethod
    async def get_conversation_stats() -> Dict[str, Any]:
        """Get statistics about prompt and profile usage in conversations."""
        try:
            prompt_stats = await PromptService.get_prompt_stats()
            profile_stats = await LLMProfileService.get_profile_stats()

            # Get tool stats
            enhanced_client = await get_enhanced_mcp_client()
            health = await enhanced_client.health_check()

            return {
                "prompts": {
                    "total": prompt_stats["total_prompts"],
                    "active": prompt_stats["active_prompts"],
                    "default": prompt_stats["default_prompt"],
                    "most_used": prompt_stats["most_used"][:3],  # Top 3
                },
                "profiles": {
                    "total": profile_stats["total_profiles"],
                    "active": profile_stats["active_profiles"],
                    "default": profile_stats["default_profile"],
                    "most_used": profile_stats["most_used"][:3],  # Top 3
                },
                "tools": health.get("registry", {}),
            }
        except Exception as e:
            logger.error(f"Failed to get conversation stats: {e}")
            return {}


# Example usage functions for testing
async def example_chat_with_custom_prompt():
    """Example: Chat with a specific prompt."""
    request = await EnhancedConversationService.prepare_chat_request(
        user_message="Can you review this Python code?",
        prompt_name="code_review",
        profile_name="precise",
    )
    print("Chat request for code review:")
    print(f"  System prompt: {request['messages'][0]['content'][:100]}...")
    print(
        f"  Parameters: temperature={request.get('temperature')}, max_tokens={request.get('max_tokens')}"
    )
    print(f"  Tools available: {len(request.get('tools', []))}")


async def example_chat_with_creative_profile():
    """Example: Chat with creative profile."""
    request = await EnhancedConversationService.prepare_chat_request(
        user_message="Write a short story about a robot",
        prompt_name="creative_writing",
        profile_name="creative",
    )
    print("\nChat request for creative writing:")
    print(f"  System prompt: {request['messages'][0]['content'][:100]}...")
    print(
        f"  Parameters: temperature={request.get('temperature')}, max_tokens={request.get('max_tokens')}"
    )


async def example_default_chat():
    """Example: Chat with defaults."""
    request = await EnhancedConversationService.prepare_chat_request(
        user_message="What's the weather like?", use_tools=True
    )
    print("\nDefault chat request:")
    print(f"  System prompt: {request['messages'][0]['content'][:100]}...")
    print(
        f"  Parameters: temperature={request.get('temperature')}, max_tokens={request.get('max_tokens')}"
    )
    print(f"  Tools available: {len(request.get('tools', []))}")


# Main integration demo
async def demo_conversation_integration():
    """Demo the conversation integration features."""
    print("🚀 Demonstrating Conversation Integration with Registries")
    print("=" * 60)

    try:
        await example_chat_with_custom_prompt()
        await example_chat_with_creative_profile()
        await example_default_chat()

        print("\n📊 Conversation Statistics:")
        stats = await EnhancedConversationService.get_conversation_stats()
        print(f"  Prompts: {stats.get('prompts', {}).get('active', 0)} active")
        print(f"  Profiles: {stats.get('profiles', {}).get('active', 0)} active")
        print(f"  Tools: {stats.get('tools', {}).get('enabled_tools', 0)} enabled")

    except Exception as e:
        print(f"❌ Demo failed: {e}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(demo_conversation_integration())
