"""
AI Chatbot Terminal Client - Interactive command-line interface for the AI Chatbot Platform.

This module provides a terminal-based chat interface for interacting with the AI Chatbot
Platform, supporting conversation management, authentication, and real-time chat.

"""

import sys
import threading
import time

from ai_chatbot_sdk import (AIChatbotSDK, ApiError, ChatRequest,
                            ConversationCreate)

# --- CONFIGURE THESE ---
API_BASE_URL = "http://localhost:8000"  # Change to your backend
USERNAME = "admin"  # Prompted if not set
PASSWORD = "adminpass"  # Prompted if not set

# --- UTILITIES ---


def input_prompt(prompt: str) -> str:
    """
    Get user input with graceful handling of EOF.
    
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
    Terminal-based chatbot interface.
    
    Provides a command-line interface for interacting with the AI Chatbot Platform,
    including authentication, conversation management, and real-time chat.
    
    Args:
        api_url: Base URL of the AI Chatbot API.
    """
    
    def __init__(self, api_url: str):
        self.sdk = AIChatbotSDK(base_url=api_url)
        self.conversation_id = None
        self.conversation_title = None
        self.token = None
        self.username = None

    def authenticate(self):
        """Authenticate user with the API and store token."""
        print_boxed("AI Chatbot Login")
        while True:
            username = USERNAME or input_prompt("Username: ")
            password = PASSWORD or input_prompt("Password: ")
            try:
                token = self.sdk.auth.login(username=username, password=password)
                self.sdk.set_token(token.access_token)
                self.token = token.access_token
                user = self.sdk.auth.me()
                print(f"Welcome, {user.username}!\n")
                self.username = user.username
                break
            except ApiError as e:
                print(
                    f"Login failed: {e.body.get('message') if hasattr(e, 'body') and isinstance(e.body, dict) else str(e)}"
                )
                if USERNAME and PASSWORD:
                    sys.exit(1)

    def new_conversation(self):
        """Create a new conversation."""
        title = input_prompt("Start a new conversation (title): ").strip()
        if not title:
            title = f"Chat {time.strftime('%Y-%m-%d %H:%M:%S')}"
        convo = self.sdk.conversations.create(
            ConversationCreate(is_active=True, title=title)
        )
        self.conversation_id = convo.id
        self.conversation_title = convo.title
        print(
            f"Started new conversation: {self.conversation_title} (ID: {self.conversation_id})\n"
        )

    def load_conversations(self):
        """Load and display conversation history."""
        convos = self.sdk.conversations.list(page=1, size=10)
        if not convos.items:
            print("You have no previous conversations.")
            return False
        print("Your recent conversations:")
        print("CONVOS", convos)
        for i, conv in enumerate(convos.items, 1):
            print("CONV", conv)
            print(
                f"  [{i}] {conv.title} (ID: {conv.id}, {conv.message_count} messages, active={conv.is_active})"
            )
        idx = input_prompt("Select conversation [1-N] or [N]ew: ").strip()
        if idx.lower() == "n" or idx.lower() == "new":
            self.new_conversation()
            return True
        try:
            idx = int(idx)
            chosen = convos.items[idx - 1]
            self.conversation_id = chosen.id
            self.conversation_title = chosen.title
            print(f"Loaded conversation: {self.conversation_title}\n")
            return True
        except Exception:
            print("Invalid selection.")
            return False

    def show_history(self):
        """Show conversation history with selection option."""
        if not self.conversation_id:
            print("No conversation selected.")
            return
        msgs = self.sdk.conversations.messages(
            conversation_id=self.conversation_id, page=1, size=50
        )
        for msg in msgs.items:
            role = "You" if msg.role == "user" else "AI"
            print(f"[{role}] {msg.content}\n")

    def chat_loop(self):
        """Main chat loop for interactive conversation."""
        print_boxed(f"AI Chatbot - {self.conversation_title or 'Untitled'}")
        print("Type your message. /help for commands. /exit or Ctrl+D to quit.\n")
        self.show_history()
        while True:
            msg = input_prompt("You: ")
            if msg.strip() == "":
                continue
            if msg.startswith("/"):
                self.handle_command(msg)
                continue
            chat_req = ChatRequest(
                user_message=msg,
                conversation_id=self.conversation_id,
                conversation_title=self.conversation_title,
                use_rag=False,
                use_tools=True,
            )
            t, running = spinner("AI is thinking")
            try:
                resp = self.sdk.conversations.chat(chat_req)
            finally:
                running[0] = False
                t.join()
            ai_msg = resp.ai_message.content
            print(f"AI: {ai_msg}\n")
            # Update conversation id/title in case of new conversation
            self.conversation_id = resp.conversation.id
            self.conversation_title = resp.conversation.title

    def handle_command(self, cmd: str):
        """Handle special commands during chat."""
        cmd = cmd.strip().lower()
        if cmd == "/help":
            print(
                "Commands:\n"
                "  /help         Show this help\n"
                "  /history      Show message history\n"
                "  /new          Start a new conversation\n"
                "  /list         List recent conversations\n"
                "  /title        Show current conversation title\n"
                "  /exit         Exit"
            )
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
        elif cmd == "/exit":
            print("Goodbye!")
            sys.exit(0)
        else:
            print("Unknown command. Type /help.")


def main():
    """Main entry point for the chatbot terminal application."""
    bot = AIChatbotTerminal(API_BASE_URL)
    bot.authenticate()
    # Load or start conversation
    if not bot.load_conversations():
        bot.new_conversation()
    bot.chat_loop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGoodbye!")
