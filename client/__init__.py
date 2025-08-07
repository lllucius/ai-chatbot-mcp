"""AI Chatbot Platform Client Library and SDK.

This package provides comprehensive client-side functionality for the AI Chatbot Platform,
including a powerful Python SDK for programmatic access and an interactive terminal-based
client for seamless integration with the platform's API services.
"""
    - Unified configuration management across all client components
    - Secure authentication and session management
    - Real-time streaming support for conversations and long-running operations
    - Advanced error handling and retry mechanisms
    - Rich terminal interface with colors, formatting, and progress indicators

SDK Capabilities:
    - Full platform API coverage including authentication, users, conversations
    - Document management with upload, processing, and vector search
    - Analytics and reporting with comprehensive metrics
    - MCP server integration and tool management
    - Async operations for high-performance applications
    - Type hints and Pydantic models for robust development

Terminal Client Features:
    - Interactive conversation sessions with AI models
    - Real-time configuration and parameter adjustment
    - Command history and line editing with arrow key navigation
    - LLM parameter experimentation and profile management
    - Document upload and search capabilities
    - User and system administration functions
    - Export and backup functionality

Architecture:
    - Async-first design for optimal performance
    - Modular structure for easy extension and customization
    - Rich terminal interface using Rich library for beautiful output
    - Comprehensive error handling and graceful degradation
    - Configuration management with environment variable support

Security Features:
    - JWT-based authentication with secure token storage
    - Encrypted communication with the platform
    - Secure credential handling and validation
    - Session management with automatic token refresh
    - Audit logging for client operations

Use Cases:
    - Application development and integration with AI Chatbot Platform
    - Interactive AI experimentation and development
    - System administration and platform management
    - Automated testing and validation workflows
    - Data analysis and reporting applications

Example Usage:
    ```python
    # SDK Usage
    from client import AIChatbotSDK

    async def main():
        sdk = AIChatbotSDK(base_url="https://api.chatbot.example.com")
        token = await sdk.auth.login("username", "password")
        sdk.set_token(token.access_token)

        # Use SDK methods
        conversations = await sdk.conversations.list()
        documents = await sdk.documents.search("machine learning")

    # Terminal Client Usage
    from client.chatbot import main as chatbot_main

    # Run interactive client
    asyncio.run(chatbot_main())
    ```

Installation:
    The client library is included with the ai-chatbot-mcp package:

    ```bash
    pip install ai-chatbot-mcp
    ```

Configuration:
    Client configuration is managed through environment variables and .env files:

    ```bash
    export API_BASE_URL="https://api.chatbot.example.com"
    export CLIENT_TIMEOUT=30
    export CLIENT_TOKEN_FILE="~/.ai-chatbot/token"
    ```

Integration:
    - Seamless integration with CI/CD pipelines for automated testing
    - Integration with development tools and IDEs
    - Compatibility with data analysis and reporting tools
    - Support for custom applications and workflow automation
"""
