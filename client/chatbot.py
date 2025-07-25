"""
AI Chatbot Terminal Client - Interactive command-line interface for the AI Chatbot Platform.

This module provides a terminal-based chat interface for interacting with the AI Chatbot
Platform, supporting conversation management, authentication, real-time chat, and
advanced features like registry management, document handling, and configuration.

"""

# Add the app directory to the Python path
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import json
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Try to import readline for command history support
try:
    import readline

    READLINE_AVAILABLE = True
except ImportError:
    READLINE_AVAILABLE = False

from client.ai_chatbot_sdk import (AIChatbotSDK, ApiError, ChatRequest, ConversationCreate,
                                   DocumentSearchRequest)
from client.config import ChatbotConfig, get_default_token_file, load_config

# --- UTILITIES ---


def setup_readline():
    """Configure readline for command history and editing features."""
    if not READLINE_AVAILABLE:
        return

    # Set up history file
    history_file = os.path.expanduser("~/.ai_chatbot_history")
    try:
        readline.read_history_file(history_file)
    except FileNotFoundError:
        pass  # History file doesn't exist yet

    # Configure readline
    readline.parse_and_bind("tab: complete")
    readline.parse_and_bind('"\\e[A": history-search-backward')  # Up arrow
    readline.parse_and_bind('"\\e[B": history-search-forward')  # Down arrow
    readline.set_history_length(1000)

    # Save history on exit
    import atexit

    atexit.register(lambda: readline.write_history_file(history_file))


def input_prompt(prompt: str) -> str:
    """
    Get user input with graceful handling of EOF and readline support for command history.

    Args:
        prompt: The input prompt to display.

    Returns:
        User input string.
    """
    try:
        return input(prompt)
    except EOFError:
        print("\nGoodbye!")
        sys.exit(0)


def print_boxed(msg: str):
    """
    Print a message in a box format.

    Args:
        msg: The message to print.
    """
    print("=" * 60)
    print(msg)
    print("=" * 60)


def spinner(label="Waiting..."):
    """
    Create a spinning loading indicator.

    Args:
        label: The label to display next to the spinner.

    Returns:
        Tuple of (thread, running_flag) for controlling the spinner.
    """
    chars = "|/-\\"
    idx = [0]
    running = [True]

    def spin():
        """Internal function to animate the spinner."""
        while running[0]:
            print(f"\r{label} {chars[idx[0] % len(chars)]}", end="", flush=True)
            idx[0] += 1
            time.sleep(0.07)
        print("\r" + " " * (len(label) + 3) + "\r", end="", flush=True)

    t = threading.Thread(target=spin)
    t.start()
    return t, running


# --- MAIN CHATBOT LOGIC ---


class AIChatbotTerminal:
    """
    Terminal-based chatbot interface with advanced features.

    Provides a command-line interface for interacting with the AI Chatbot Platform,
    including authentication, conversation management, real-time chat, registry
    management, document handling, and configuration options.

    Features:
    - Configuration management via files and environment variables
    - Registry support for prompts, LLM profiles, and tools
    - Document upload and search capabilities
    - Enhanced conversation management with search and export
    - Improved error handling and user experience

    Args:
        config: Configuration object with all settings.
    """

    def __init__(self, config: ChatbotConfig):
        self.config = config
        self.sdk = AIChatbotSDK(base_url=config.api_url)
        self.conversation_id = None
        self.conversation_title = None
        self.token = None
        self.username = None
        self.current_prompt = config.default_prompt_name
        self.current_profile = config.default_profile_name

        # Load saved token if available
        self._load_saved_token()

    def _load_saved_token(self):
        """Load previously saved authentication token."""
        token_file = self.config.token_file or get_default_token_file()
        try:
            if os.path.exists(token_file):
                with open(token_file, "r") as f:
                    token_data = json.load(f)
                    if token_data.get("token"):
                        self.sdk.set_token(token_data["token"])
                        self.token = token_data["token"]
                        # Try to verify the token
                        try:
                            user = self.sdk.auth.me()
                            self.username = user.username
                            print(f"Resumed session for {user.username}")
                            return True
                        except ApiError:
                            # Token expired, clear it
                            self._clear_saved_token()
        except Exception as e:
            if self.config.debug_mode:
                print(f"Error loading saved token: {e}")
        return False

    def _save_token(self, token: str):
        """Save authentication token for future use."""
        if not self.config.token_file and not get_default_token_file():
            return

        token_file = self.config.token_file or get_default_token_file()
        try:
            os.makedirs(os.path.dirname(token_file), exist_ok=True)
            with open(token_file, "w") as f:
                json.dump(
                    {
                        "token": token,
                        "username": self.username,
                        "saved_at": datetime.now().isoformat(),
                    },
                    f,
                )
        except Exception as e:
            if self.config.debug_mode:
                print(f"Error saving token: {e}")

    def _clear_saved_token(self):
        """Clear saved authentication token."""
        token_file = self.config.token_file or get_default_token_file()
        try:
            if os.path.exists(token_file):
                os.remove(token_file)
        except Exception as e:
            if self.config.debug_mode:
                print(f"Error clearing token: {e}")

    def authenticate(self):
        """Authenticate user with the API and store token."""
        if self.token and self.username:
            return  # Already authenticated

        print_boxed("AI Chatbot Login")
        while True:
            username = self.config.username or input_prompt("Username: ")
            password = self.config.password or input_prompt("Password: ")
            try:
                token = self.sdk.auth.login(username=username, password=password)
                self.sdk.set_token(token.access_token)
                self.token = token.access_token
                self.username = username
                self._save_token(token.access_token)

                user = self.sdk.auth.me()
                print(f"Welcome, {user.username}!\n")
                break
            except ApiError as e:
                print(
                    f"Login failed: {e.body.get('message') if hasattr(e, 'body') and isinstance(e.body, dict) else str(e)}"
                )
                if self.config.username and self.config.password:
                    sys.exit(1)

    def new_conversation(self):
        """Create a new conversation."""
        title = input_prompt("Start a new conversation (title): ").strip()
        if not title and self.config.auto_title:
            title = f"Chat {time.strftime('%Y-%m-%d %H:%M:%S')}"
        if not title:
            title = "Untitled Conversation"

        convo = self.sdk.conversations.create(ConversationCreate(is_active=True, title=title))
        self.conversation_id = convo.id
        self.conversation_title = convo.title
        print(f"Started new conversation: {self.conversation_title} (ID: {self.conversation_id})\n")

    def load_conversations(self):
        """Load and display conversation history with enhanced options."""
        convos = self.sdk.conversations.list(page=1, size=10)
        if not convos.items:
            print("You have no previous conversations.")
            return False

        print("Your recent conversations:")
        for i, conv in enumerate(convos.items, 1):
            status = "Active" if conv.is_active else "Archived"
            last_msg = (
                conv.last_message_at.strftime("%Y-%m-%d %H:%M")
                if conv.last_message_at
                else "No messages"
            )
            print(
                f"  [{i}] {conv.title[:50]} (ID: {str(conv.id)[:8]}..., {conv.message_count} msgs, {status}, {last_msg})"
            )

        print("Options:")
        print("  [N]ew conversation")
        print("  [S]earch conversations")
        print("  [1-N] Select conversation")

        choice = input_prompt("Choose option: ").strip()

        if choice.lower() in ["n", "new"]:
            self.new_conversation()
            return True
        elif choice.lower() in ["s", "search"]:
            return self.search_conversations()

        try:
            idx = int(choice)
            if 1 <= idx <= len(convos.items):
                chosen = convos.items[idx - 1]
                self.conversation_id = chosen.id
                self.conversation_title = chosen.title
                print(f"Loaded conversation: {self.conversation_title}\n")
                return True
        except (ValueError, IndexError):
            pass

        print("Invalid selection.")
        return False

    def search_conversations(self):
        """Search through conversations by title or content."""
        query = input_prompt("Search conversations (title): ").strip()
        if not query:
            return False

        try:
            # Get all conversations and filter by title (basic search)
            # In a real implementation, this could use full-text search
            convos = self.sdk.conversations.list(page=1, size=50)
            matches = [c for c in convos.items if query.lower() in c.title.lower()]

            if not matches:
                print(f"No conversations found matching '{query}'")
                return False

            print(f"Found {len(matches)} conversations matching '{query}':")
            for i, conv in enumerate(matches, 1):
                print(f"  [{i}] {conv.title} ({conv.message_count} messages)")

            choice = input_prompt("Select conversation [1-N] or press Enter to cancel: ").strip()
            if not choice:
                return False

            idx = int(choice)
            if 1 <= idx <= len(matches):
                chosen = matches[idx - 1]
                self.conversation_id = chosen.id
                self.conversation_title = chosen.title
                print(f"Loaded conversation: {self.conversation_title}\n")
                return True

        except Exception as e:
            print(f"Error searching conversations: {e}")

        return False

    def show_history(self):
        """Show conversation history with pagination."""
        if not self.conversation_id:
            print("No conversation selected.")
            return

        try:
            msgs = self.sdk.conversations.messages(
                conversation_id=self.conversation_id,
                page=1,
                size=self.config.max_history_display,
            )

            if not msgs.items:
                print("No messages in this conversation yet.\n")
                return

            print(f"Conversation History ({len(msgs.items)} recent messages):")
            print("-" * 60)

            for msg in msgs.items:
                role = "You" if msg.role == "user" else "AI"
                timestamp = msg.created_at.strftime("%H:%M:%S") if msg.created_at else ""
                content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                print(f"[{timestamp}] {role}: {content}\n")

            print("-" * 60)

        except Exception as e:
            print(f"Error loading conversation history: {e}")

    def chat_loop(self):
        """Main chat loop for interactive conversation."""
        print_boxed(f"AI Chatbot - {self.conversation_title or 'Untitled'}")

        # Show current settings
        print("Current Settings:")
        print(f"  Prompt: {self.current_prompt or 'Default'}")
        print(f"  Profile: {self.current_profile or 'Default'}")
        print(f"  RAG: {'Enabled' if self.config.default_use_rag else 'Disabled'}")
        print(f"  Tools: {'Enabled' if self.config.default_use_tools else 'Disabled'}")
        print(f"  Streaming: {'Enabled' if self.config.enable_streaming else 'Disabled'}")
        print()

        print("Type your message. /help for commands. /exit or Ctrl+D to quit.\n")
        self.show_history()

        while True:
            msg = input_prompt("You: ")
            if msg.strip() == "":
                continue
            if msg.startswith("/"):
                self.handle_command(msg)
                continue

            # Prepare chat request with current settings
            chat_req = ChatRequest(
                user_message=msg,
                conversation_id=self.conversation_id,
                conversation_title=self.conversation_title,
                use_rag=self.config.default_use_rag,
                use_tools=self.config.default_use_tools,
                prompt_name=self.current_prompt,
                profile_name=self.current_profile,
            )

            try:
                if self.config.enable_streaming:
                    # Use streaming response
                    print("AI: ", end="", flush=True)
                    for chunk in self.sdk.conversations.chat_stream(chat_req):
                        chunk = json.loads(chunk)
                        match chunk["type"]:
                            case "start":
                                print(chunk["message"], end="\n", flush=True)
                            case "content":
                                print(chunk["content"], end="", flush=True)
                            case _:
                                print(chunk, end="", flush=True)

                    print("\n")  # Add newline after streaming is complete
                else:
                    # Show spinner if enabled and not streaming
                    spinner_thread = None
                    if self.config.spinner_enabled:
                        spinner_thread, running = spinner("AI is thinking")

                    try:
                        resp = self.sdk.conversations.chat(chat_req)
                        ai_msg = resp.ai_message.content
                        print(f"AI: {ai_msg}\n")

                        # Update conversation id/title in case of new conversation
                        self.conversation_id = resp.conversation.id
                        self.conversation_title = resp.conversation.title
                    finally:
                        if spinner_thread:
                            running[0] = False
                            spinner_thread.join()

            except Exception as e:
                print(f"Error: {e}")
                continue

    def handle_command(self, cmd: str):
        """Handle special commands during chat with enhanced functionality."""
        cmd = cmd.strip().lower()

        if cmd == "/help":
            self.show_help()
        elif cmd == "/history":
            self.show_history()
        elif cmd == "/new":
            self.new_conversation()
            print_boxed(f"AI Chatbot - {self.conversation_title or 'Untitled'}")
        elif cmd == "/list":
            self.load_conversations()
            print_boxed(f"AI Chatbot - {self.conversation_title or 'Untitled'}")
        elif cmd == "/title":
            print(f"Current conversation: {self.conversation_title or '(none)'}")
        elif cmd == "/settings":
            self.show_settings()
        elif cmd == "/config":
            self.configure_settings()
        elif cmd.startswith("/prompt"):
            self.handle_prompt_command(cmd)
        elif cmd.startswith("/profile"):
            self.handle_profile_command(cmd)
        elif cmd.startswith("/tools"):
            self.handle_tools_command(cmd)
        elif cmd.startswith("/docs"):
            self.handle_docs_command(cmd)
        elif cmd.startswith("/export"):
            self.export_conversation()
        elif cmd.startswith("/search"):
            self.search_conversations()
        elif cmd == "/logout":
            self.logout()
        elif cmd == "/exit":
            print("Goodbye!")
            sys.exit(0)
        else:
            print("Unknown command. Type /help for available commands.")

    def show_help(self):
        """Display comprehensive help information."""
        print("Available Commands:")
        print()
        print("Basic Commands:")
        print("  /help         Show this help")
        print("  /history      Show message history")
        print("  /new          Start a new conversation")
        print("  /list         List recent conversations")
        print("  /search       Search conversations")
        print("  /title        Show current conversation title")
        print("  /settings     Show current settings")
        print("  /config       Configure chatbot settings")
        print("  /export       Export current conversation")
        print("  /logout       Logout and clear saved token")
        print("  /exit         Exit the application")
        print()
        print("Registry Commands:")
        print("  /prompt list           List available prompts")
        print("  /prompt use <name>     Use a specific prompt")
        print("  /prompt show [name]    Show prompt details")
        print("  /prompt reset          Reset to default prompt")
        print()
        print("  /profile list          List available LLM profiles")
        print("  /profile use <name>    Use a specific profile")
        print("  /profile show [name]   Show profile details")
        print("  /profile reset         Reset to default profile")
        print()
        print("  /tools list            List available tools")
        print("  /tools status          Show tools status")
        print("  /tools enable <name>   Enable a specific tool")
        print("  /tools disable <name>  Disable a specific tool")
        print()
        print("Document Commands:")
        print("  /docs list             List your documents")
        print("  /docs upload <file>    Upload a new document")
        print("  /docs search <query>   Search documents")
        print("  /docs status <id>      Check document processing status")

    def show_settings(self):
        """Display current configuration settings."""
        print("Current Settings:")
        print("-" * 40)
        print(f"API URL: {self.config.api_url}")
        print(f"Username: {self.username or 'Not logged in'}")
        print(f"Current Prompt: {self.current_prompt or 'Default'}")
        print(f"Current Profile: {self.current_profile or 'Default'}")
        print(f"RAG Enabled: {self.config.default_use_rag}")
        print(f"Tools Enabled: {self.config.default_use_tools}")
        print(f"Streaming Enabled: {self.config.enable_streaming}")
        print(f"Spinner Enabled: {self.config.spinner_enabled}")
        print(f"Auto Title: {self.config.auto_title}")
        print(f"Max History Display: {self.config.max_history_display}")
        print(f"Debug Mode: {self.config.debug_mode}")

    def configure_settings(self):
        """Interactive configuration of settings."""
        print("Configure Settings (press Enter to keep current value):")
        print()

        # Toggle RAG
        rag_input = input_prompt(f"Enable RAG [{self.config.default_use_rag}]: ").strip().lower()
        if rag_input in ["true", "yes", "y", "1"]:
            self.config.default_use_rag = True
        elif rag_input in ["false", "no", "n", "0"]:
            self.config.default_use_rag = False

        # Toggle Tools
        tools_input = (
            input_prompt(f"Enable Tools [{self.config.default_use_tools}]: ").strip().lower()
        )
        if tools_input in ["true", "yes", "y", "1"]:
            self.config.default_use_tools = True
        elif tools_input in ["false", "no", "n", "0"]:
            self.config.default_use_tools = False

        # Toggle Streaming
        streaming_input = (
            input_prompt(f"Enable Streaming [{self.config.enable_streaming}]: ").strip().lower()
        )
        if streaming_input in ["true", "yes", "y", "1"]:
            self.config.enable_streaming = True
        elif streaming_input in ["false", "no", "n", "0"]:
            self.config.enable_streaming = False

        # Max history
        history_input = input_prompt(
            f"Max History Display [{self.config.max_history_display}]: "
        ).strip()
        if history_input.isdigit():
            self.config.max_history_display = int(history_input)

        print("Settings updated!")

    def handle_prompt_command(self, cmd: str):
        """Handle prompt-related commands."""
        parts = cmd.split(maxsplit=2)
        if len(parts) < 2:
            print("Usage: /prompt [list|use|show|reset] [name]")
            return

        action = parts[1]

        try:
            if action == "list":
                prompts = self.sdk.prompts.list_prompts()
                if prompts.get("prompts"):
                    print("Available Prompts:")
                    for prompt in prompts["prompts"]:
                        status = "*" if prompt["name"] == self.current_prompt else " "
                        print(f" {status} {prompt['name']}: {prompt['title']}")
                else:
                    print("No prompts available.")

            elif action == "use":
                if len(parts) < 3:
                    print("Usage: /prompt use <name>")
                    return
                name = parts[2]
                try:
                    prompt = self.sdk.prompts.get_prompt(name)
                    self.current_prompt = name
                    print(f"Now using prompt: {prompt.title}")
                except ApiError as e:
                    print(f"Error: {e}")

            elif action == "show":
                name = parts[2] if len(parts) > 2 else self.current_prompt
                if not name:
                    print("No prompt specified and no current prompt set.")
                    return
                try:
                    prompt = self.sdk.prompts.get_prompt(name)
                    print(f"Prompt: {prompt.title}")
                    print(f"Description: {prompt.description or 'N/A'}")
                    print(f"Category: {prompt.category or 'N/A'}")
                    print("Content:")
                    print("-" * 40)
                    print(prompt.content)
                    print("-" * 40)
                except ApiError as e:
                    print(f"Error: {e}")

            elif action == "reset":
                self.current_prompt = self.config.default_prompt_name
                print("Reset to default prompt.")

        except Exception as e:
            print(f"Error with prompt command: {e}")

    def handle_profile_command(self, cmd: str):
        """Handle LLM profile-related commands."""
        parts = cmd.split(maxsplit=2)
        if len(parts) < 2:
            print("Usage: /profile [list|use|show|reset] [name]")
            return

        action = parts[1]

        try:
            if action == "list":
                profiles = self.sdk.profiles.list_profiles()
                if profiles.get("profiles"):
                    print("Available LLM Profiles:")
                    for profile in profiles["profiles"]:
                        status = "*" if profile["name"] == self.current_profile else " "
                        default = " (default)" if profile.get("is_default") else ""
                        print(f" {status} {profile['name']}: {profile['title']}{default}")
                else:
                    print("No profiles available.")

            elif action == "use":
                if len(parts) < 3:
                    print("Usage: /profile use <name>")
                    return
                name = parts[2]
                try:
                    profile = self.sdk.profiles.get_profile(name)
                    self.current_profile = name
                    print(f"Now using profile: {profile.title}")
                except ApiError as e:
                    print(f"Error: {e}")

            elif action == "show":
                name = parts[2] if len(parts) > 2 else self.current_profile
                if not name:
                    print("No profile specified and no current profile set.")
                    return
                try:
                    profile = self.sdk.profiles.get_profile(name)
                    print(f"Profile: {profile.title}")
                    print(f"Description: {profile.description or 'N/A'}")
                    print(f"Model: {profile.model_name}")
                    print(f"Parameters: {json.dumps(profile.parameters, indent=2)}")
                except ApiError as e:
                    print(f"Error: {e}")

            elif action == "reset":
                self.current_profile = self.config.default_profile_name
                print("Reset to default profile.")

        except Exception as e:
            print(f"Error with profile command: {e}")

    def handle_tools_command(self, cmd: str):
        """Handle tools-related commands."""
        parts = cmd.split(maxsplit=2)
        if len(parts) < 2:
            print("Usage: /tools [list|status|enable|disable] [name]")
            return

        action = parts[1]

        try:
            if action == "list":
                tools = self.sdk.tools.list_tools()
                print(f"Available Tools ({tools.enabled_count}/{tools.total_count} enabled):")
                for tool in tools.available_tools:
                    status = "✓" if tool.is_enabled else "✗"
                    print(f" {status} {tool.name}: {tool.description[:60]}...")

            elif action == "status":
                tools = self.sdk.tools.list_tools()
                print("Tools Status:")
                print(f"  Total Tools: {tools.total_count}")
                print(f"  Enabled Tools: {tools.enabled_count}")
                print(f"  Disabled Tools: {tools.total_count - tools.enabled_count}")
                for server in tools.servers:
                    print(f"  Server '{server['name']}': {server['status']}")

            elif action in ["enable", "disable"]:
                if len(parts) < 3:
                    print(f"Usage: /tools {action} <tool_name>")
                    return
                tool_name = parts[2]
                try:
                    if action == "enable":
                        self.sdk.tools.enable_tool(tool_name)
                        print(f"Enabled tool: {tool_name}")
                    else:
                        self.sdk.tools.disable_tool(tool_name)
                        print(f"Disabled tool: {tool_name}")
                except ApiError as e:
                    print(f"Error: {e}")

        except Exception as e:
            print(f"Error with tools command: {e}")

    def handle_docs_command(self, cmd: str):
        """Handle document-related commands."""
        parts = cmd.split(maxsplit=2)
        if len(parts) < 2:
            print("Usage: /docs [list|upload|search|status] [args]")
            return

        action = parts[1]

        try:
            if action == "list":
                docs = self.sdk.documents.list(page=1, size=20)
                if docs.items:
                    print("Your Documents:")
                    for doc in docs.items:
                        status = doc.processing_status
                        size_mb = doc.file_size / 1024 / 1024
                        print(f"  {doc.title} ({doc.file_type}, {size_mb:.1f}MB, {status})")
                        print(f"    ID: {str(doc.id)[:8]}... | Chunks: {doc.chunk_count}")
                else:
                    print("No documents found.")

            elif action == "upload":
                if len(parts) < 3:
                    print("Usage: /docs upload <file_path>")
                    return
                file_path = parts[2]
                if not os.path.exists(file_path):
                    print(f"File not found: {file_path}")
                    return
                try:
                    with open(file_path, "rb") as f:
                        result = self.sdk.documents.upload(f, title=os.path.basename(file_path))
                    print(f"Uploaded: {result.document.title}")
                    print(f"Processing status: {result.document.processing_status}")
                except Exception as e:
                    print(f"Error uploading file: {e}")

            elif action == "search":
                if len(parts) < 3:
                    print("Usage: /docs search <query>")
                    return
                query = parts[2]
                try:
                    results = self.sdk.search.search(
                        DocumentSearchRequest(query=query, limit=10)
                    )
                    if results.get("results"):
                        print(f"Found {len(results['results'])} results for '{query}':")
                        for result in results["results"]:
                            print(
                                f"  {result.get('title', 'Unknown')} (Score: {result.get('score', 0):.2f})"
                            )
                            print(f"    {result.get('content', '')[:100]}...")
                    else:
                        print(f"No results found for '{query}'")
                except Exception as e:
                    print(f"Error searching documents: {e}")

            elif action == "status":
                if len(parts) < 3:
                    print("Usage: /docs status <document_id>")
                    return
                doc_id = parts[2]
                try:
                    from uuid import UUID

                    status = self.sdk.documents.status(UUID(doc_id))
                    print(f"Document Status: {status.status}")
                    print(f"Progress: {status.progress:.1%}")
                    print(f"Chunks: {status.chunks_processed}/{status.total_chunks}")
                except Exception as e:
                    print(f"Error getting document status: {e}")

        except Exception as e:
            print(f"Error with docs command: {e}")

    def export_conversation(self):
        """Export current conversation to a file."""
        if not self.conversation_id:
            print("No conversation selected.")
            return

        try:
            msgs = self.sdk.conversations.messages(
                conversation_id=self.conversation_id, page=1, size=1000
            )

            # Prepare export data
            export_data = {
                "conversation_id": str(self.conversation_id),
                "title": self.conversation_title,
                "exported_at": datetime.now().isoformat(),
                "message_count": len(msgs.items),
                "messages": [],
            }

            for msg in msgs.items:
                export_data["messages"].append(
                    {
                        "id": str(msg.id),
                        "role": msg.role,
                        "content": msg.content,
                        "created_at": (msg.created_at.isoformat() if msg.created_at else None),
                        "token_count": msg.token_count,
                    }
                )

            # Save to file
            filename = f"conversation_{str(self.conversation_id)[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, "w") as f:
                json.dump(export_data, f, indent=2)

            print(f"Conversation exported to: {filename}")

        except Exception as e:
            print(f"Error exporting conversation: {e}")

    def logout(self):
        """Logout and clear saved authentication data."""
        try:
            self.sdk.auth.logout()
        except Exception:
            pass  # Ignore errors, we're logging out anyway

        self._clear_saved_token()
        self.token = None
        self.username = None
        self.sdk.clear_token()
        print("Logged out successfully.")


def main(config_file: Optional[str] = None):
    """
    Main entry point for the chatbot terminal application.

    Args:
        config_file: Optional path to configuration file.
    """
    try:
        # Set up readline for command history
        setup_readline()

        # Load configuration
        config = load_config(config_file)

        # Initialize chatbot with config
        bot = AIChatbotTerminal(config)

        # Authenticate (may reuse saved token)
        bot.authenticate()

        # Load or start conversation
        if not bot.load_conversations():
            bot.new_conversation()

        # Start chat loop
        bot.chat_loop()

    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        if config and config.debug_mode:
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI Chatbot Terminal Client")
    parser.add_argument("--config", type=str, help="Path to configuration file (.env format)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    # Set debug mode via environment variable if specified
    if args.debug:
        os.environ["CHATBOT_DEBUG_MODE"] = "true"

    main(args.config)
