"""
AI Chatbot Platform Command Line Interface.

This package provides a comprehensive command-line interface for the AI Chatbot Platform,
enabling developers and administrators to interact with the platform through terminal
commands. The CLI offers full functionality for managing users, conversations, analytics,
and system administration tasks.

The CLI is built using AsyncTyper for high-performance async operations and Rich for
beautiful terminal output with progress bars, tables, and formatted text. It integrates
seamlessly with the AI Chatbot SDK for secure API communication.

Key Features:
    - Comprehensive user and conversation management
    - Real-time analytics and reporting
    - Database administration and maintenance
    - MCP server integration and management
    - Profile and prompt template management
    - Document processing and search capabilities
    - Task queue monitoring and control
    - Rich terminal interface with colors and formatting

Architecture:
    - async_typer: Modern async CLI framework with type hints
    - Rich: Beautiful terminal formatting and progress indicators
    - AI Chatbot SDK: Secure API communication layer
    - Modular commands: Organized by functional domain

Security Features:
    - JWT token-based authentication with secure storage
    - Role-based access control for administrative commands
    - Audit logging for all CLI operations
    - Secure credential management and token refresh

Performance Optimizations:
    - Async operations for non-blocking I/O
    - Efficient batch operations for bulk data processing
    - Progress indicators for long-running operations
    - Optimized API calls with request batching

Use Cases:
    - Development workflow automation
    - Production system administration
    - Data migration and bulk operations
    - Monitoring and troubleshooting
    - Integration testing and validation

Example:
    # Install and authenticate
    pip install ai-chatbot-mcp
    ai-chatbot login --username admin

    # Manage conversations
    ai-chatbot conversations list --limit 10
    ai-chatbot conversations create --title "New Chat"

    # View analytics
    ai-chatbot analytics dashboard --date-range 7d
    ai-chatbot analytics export --format json

Installation:
    The CLI is available as part of the ai-chatbot-mcp package:

    ```bash
    pip install ai-chatbot-mcp
    ai-chatbot --help
    ```

Configuration:
    Configuration is managed through environment variables and .env files:

    ```bash
    export API_BASE_URL="https://api.chatbot.example.com"
    export CLIENT_TIMEOUT=30
    ai-chatbot config show
    ```

Integration:
    The CLI integrates with:
    - CI/CD pipelines for automated testing
    - Monitoring systems for health checks
    - Backup systems for data export
    - Development tools for debugging
"""
