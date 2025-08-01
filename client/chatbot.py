#!/usr/bin/env python3
"""
Enhanced AI Chatbot CLI

Terminal-based AI Chatbot client for advanced LLM experimentation, runtime configuration,
and full management of users, MCP servers, search, registry, analytics, and more.

Features:
- Modern async SDK usage (from ai_chatbot_sdk.py)
- Robust error handling, spinner, and streaming support
- Interactive runtime settings via /set, /config
- LLM profile parameter experimentation and saving with /llmparam, /llmreset, /llmsave
- User and MCP server management commands
- Semantic search across documents and conversations
- Registry, analytics, export, DB, and document management
- Settings persistence and CLI/server version info
- Arrow-key history navigation and line editing support
- Detailed docstrings for all commands and classes

Author: Your Name
"""

import asyncio
import sys
import os
import re
import shlex
import signal
import textwrap
import getpass
import json
from datetime import datetime
from typing import Any, Dict, Optional, List, Tuple, Callable
from pathlib import Path

try:
    import readline
except ImportError:
    readline = None  # Windows fallback

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from ai_chatbot_sdk import (
    AIChatbotSDK,
    ChatRequest,
    ToolHandlingMode,
    UserUpdate,
    UserPasswordUpdate,
    DocumentSearchRequest,
    PromptCreate,
    LLMProfileCreate,
    ApiError
)
from config import (
    load_config,
    get_default_token_file,
    get_default_backup_dir,
    ClientConfig,
)

console: Console = Console()
config: ClientConfig = load_config()
TOKEN_FILE: str = config.client_token_file or get_default_token_file()
BACKUP_DIR: str = config.client_conversation_backup_dir or get_default_backup_dir()
SETTINGS_FILE: str = str(Path(BACKUP_DIR).parent / "settings.json")
CLI_VERSION: str = "2.0.0"

def save_token(token: str) -> None:
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        f.write(token)
def load_token() -> Optional[str]:
    try:
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()
    except Exception:
        return None
def clear_token() -> None:
    try:
        os.remove(TOKEN_FILE)
    except FileNotFoundError:
        pass
def print_error(msg: str) -> None:
    console.print(f"[bold red]Error:[/bold red] {msg}")
def print_success(msg: str) -> None:
    console.print(f"[bold green]{msg}[/bold green]")
def print_info(msg: str) -> None:
    console.print(f"[bold cyan]{msg}[/bold cyan]")
def print_warn(msg: str) -> None:
    console.print(f"[yellow]{msg}[/yellow]")
def prettify_dict(
    data: Any,
    title: Optional[str] = None,
    max_depth: int = 2,
    indent: int = 0,
    key_color: str = "cyan",
    value_color: str = "white",
    title_color: str = "magenta",
) -> None:
    if hasattr(data, "model_dump"):
        data = data.model_dump()
    if hasattr(data, "__dict__") and not isinstance(data, dict):
        data = vars(data)
    if not isinstance(data, dict):
        console.print(f"[{value_color}]{data}[/{value_color}]")
        return
    if title:
        console.print(f"[bold {title_color}]{title}[/bold {title_color}]")
    for k, v in data.items():
        if isinstance(v, dict) and max_depth > 0:
            console.print(f"{'  ' * indent}[{key_color}]{k}[/]:")
            prettify_dict(v, max_depth=max_depth-1, indent=indent+1)
        elif isinstance(v, list) and max_depth > 0 and all(isinstance(i, dict) for i in v) and v:
            console.print(f"{'  ' * indent}[{key_color}]{k}[/]:")
            for idx, elem in enumerate(v, 1):
                console.print(f"{'  ' * (indent+1)}-")
                prettify_dict(elem, max_depth=max_depth-1, indent=indent+2)
        else:
            console.print(f"{'  ' * indent}[{key_color}]{k}[/]: [{value_color}]{v}[/{value_color}]")

def prettify_list(
    items: List[Any],
    columns: Optional[List[str]] = None,
    title: Optional[str] = None,
    max_rows: int = 25,
) -> None:
    if not items:
        console.print("[dim]No items.[/dim]")
        return
    if hasattr(items[0], "model_dump"):
        items = [i.model_dump() for i in items]
    if hasattr(items[0], "__dict__") and not isinstance(items[0], dict):
        items = [vars(i) for i in items]
    if not isinstance(items[0], dict):
        for item in items:
            console.print(f"- {item}")
        return
    if columns is None:
        columns = list(items[0].keys())
        if len(columns) > 8:
            columns = columns[:8]
    t = Table(*columns, title=title or "", box=box.SIMPLE)
    for row in items[:max_rows]:
        t.add_row(*(str(row.get(col, "")) for col in columns))
    console.print(t)
    if len(items) > max_rows:
        console.print(f"[dim]+ {len(items)-max_rows} more rows...[/dim]")

def parse_bool(val: str) -> bool:
    return str(val).lower() in ("1", "true", "yes", "y", "on")

def save_settings(settings: Dict[str, Any]) -> None:
    try:
        data = settings.copy()
        data.pop("llm_overrides", None)
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print_warn(f"Failed to save settings: {e}")

def load_settings() -> Dict[str, Any]:
    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def ensure_backup_dir() -> None:
    os.makedirs(BACKUP_DIR, exist_ok=True)

def save_conversation_to_file(content: str, filename: Optional[str] = None) -> str:
    ensure_backup_dir()
    if filename is None:
        filename = f"conversation_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.txt"
    path = os.path.join(BACKUP_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path

def extract_ai_content(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<\?xml[^>]*\?>", "", text).strip()
    match = re.search(r"<content[^>]*>(.*?)</content>", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(r"<message[^>]*>(.*?)</message>", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    text_stripped = re.sub(r"</?[^>]+>", "", text)
    if len(text_stripped) < 0.95 * len(text):
        return text_stripped.strip()
    return text.strip()

def display_token_stats(usage: Optional[Dict[str, Any]], response_time_ms: Optional[float]) -> None:
    if usage:
        tkns = usage.get("total_tokens")
        prompt_tkns = usage.get("prompt_tokens")
        comp_tkns = usage.get("completion_tokens")
        model = usage.get("model")
        msg = []
        if tkns: msg.append(f"Total tokens: {tkns}")
        if prompt_tkns: msg.append(f"Prompt: {prompt_tkns}")
        if comp_tkns: msg.append(f"Completion: {comp_tkns}")
        if model: msg.append(f"Model: {model}")
        if response_time_ms is not None:
            msg.append(f"Latency: {response_time_ms:.0f} ms")
        if msg:
            print_info(" | ".join(msg))
    elif response_time_ms is not None:
        print_info(f"Latency: {response_time_ms:.0f} ms")

def ellipsis(text: str, max_len: int = 100) -> str:
    if len(text) > max_len:
        return text[:max_len - 3] + "..."
    return text

def prompt_password(confirm: bool = False) -> str:
    while True:
        pw = getpass.getpass("Password: ")
        if not confirm:
            return pw
        pw2 = getpass.getpass("Confirm password: ")
        if pw == pw2:
            return pw
        print_warn("Passwords do not match. Try again.")

def setup_readline(history_file: str = "~/.ai-chatbot-history") -> None:
    if not readline:
        return
    histfile = os.path.expanduser(history_file)
    try:
        readline.read_history_file(histfile)
    except FileNotFoundError:
        pass
    readline.set_history_length(1000)
    import atexit
    atexit.register(lambda: readline.write_history_file(histfile))

class SpinnerContext:
    def __init__(self, message: str = "Thinking...", enabled: bool = True):
        self.enabled = enabled
        self.message = message
        self.task: Optional[asyncio.Task] = None
        self.stop_event: asyncio.Event = asyncio.Event()
    async def __aenter__(self) -> "SpinnerContext":
        if self.enabled:
            self.task = asyncio.create_task(self._spin())
        return self
    async def __aexit__(self, exc_type, exc, tb) -> None:
        self.stop_event.set()
        if self.task:
            await self.task
    async def _spin(self) -> None:
        with console.status(f"[bold blue]{self.message}"):
            while not self.stop_event.is_set():
                await asyncio.sleep(0.05)

class Settings:
    _persist_keys = [
        "use_rag",
        "use_tools",
        "prompt_name",
        "profile_name",
        "enable_streaming",
        "spinner_enabled",
        "auto_title",
    ]
    def __init__(self, config: ClientConfig):
        self.use_rag: bool = config.client_default_use_rag
        self.use_tools: bool = config.client_default_use_tools
        self.prompt_name: Optional[str] = config.client_default_prompt_name
        self.profile_name: Optional[str] = config.client_default_profile_name
        self.enable_streaming: bool = config.client_enable_streaming
        self.spinner_enabled: bool = config.client_spinner_enabled
        self.auto_title: bool = config.client_auto_title
        self.llm_overrides: Dict[str, Any] = {}
        self.last_conversation_id: Optional[str] = None
        loaded = load_settings()
        for key in self._persist_keys:
            if key in loaded:
                setattr(self, key, loaded[key])
    def display(self) -> None:
        t = Table(title="Current Settings", box=box.SIMPLE)
        t.add_column("Setting", style="cyan")
        t.add_column("Value", style="magenta")
        for k, v in [
            ("use_rag", self.use_rag),
            ("use_tools", self.use_tools),
            ("prompt_name", self.prompt_name),
            ("profile_name", self.profile_name),
            ("enable_streaming", self.enable_streaming),
            ("spinner_enabled", self.spinner_enabled),
            ("auto_title", self.auto_title),
            ("llm_overrides", json.dumps(self.llm_overrides)),
        ]:
            t.add_row(k, str(v))
        console.print(t)
    def settings_dict(self) -> Dict[str, Any]:
        return {k: getattr(self, k) for k in self._persist_keys}
    def set(self, key: str, value: Any) -> None:
        if hasattr(self, key):
            setattr(self, key, value)
            print_success(f"Set {key} = {value}")
            save_settings(self.settings_dict())
        else:
            print_warn(f"Unknown setting: {key}")
    def reset_llm(self) -> None:
        self.llm_overrides.clear()
        print_success("Cleared all LLM parameter overrides.")
    def set_llm_param(self, key: str, value: Any) -> None:
        self.llm_overrides[key] = value
        print_success(f"LLM parameter override: {key} = {value}")
    def unset_llm_param(self, key: str) -> None:
        if key in self.llm_overrides:
            self.llm_overrides.pop(key)
            print_success(f"Removed override for {key}")
    def get_llm_params(self) -> Dict[str, Any]:
        return self.llm_overrides.copy()
    def display_llm_params(self) -> None:
        if not self.llm_overrides:
            print_info("No LLM parameter overrides set.")
        else:
            t = Table(title="Current LLM Parameter Overrides", box=box.SIMPLE)
            t.add_column("Parameter", style="cyan")
            t.add_column("Value", style="magenta")
            for k, v in self.llm_overrides.items():
                t.add_row(k, str(v))
            console.print(t)
    def available_settings(self) -> List[Tuple[str, str, str]]:
        return [
            ("use_rag", "bool", "Enable RAG (true/false)"),
            ("use_tools", "bool", "Enable tool calling (true/false)"),
            ("prompt_name", "str", "Registry prompt name"),
            ("profile_name", "str", "Registry LLM profile name"),
            ("enable_streaming", "bool", "Streaming output (true/false)"),
            ("spinner_enabled", "bool", "Show spinner during responses"),
            ("auto_title", "bool", "Auto-generate conversation titles"),
        ]


# ---- Command Handlers ----

class CommandHandler:
    """
    Handles slash commands and CLI logic for the chatbot.
    """

    def __init__(self, sdk: AIChatbotSDK, settings: Settings, history: List[str]):
        self.sdk: AIChatbotSDK = sdk
        self.settings: Settings = settings
        self.history: List[str] = history

    async def handle(self, line: str) -> bool:
        """
        Parse and execute a command. Returns True if handled, else False.
        """
        if not line.startswith("/"):
        return False
        cmd, *args = shlex.split(line)
        cmd = cmd.lower()

        try:
            if cmd in ("/help", "/h", "/?"):
                self.show_help()
            elif cmd == "/settings":
                self.show_settings_help()
            elif cmd in ("/exit", "/quit", "/q"):
                print_info("Goodbye!")
                sys.exit(0)
            elif cmd == "/set":
                await self.cmd_set(args)
            elif cmd == "/config":
                self.settings.display()
            elif cmd == "/llmparam":
                await self.cmd_llmparam(args)
            elif cmd == "/llmreset":
                self.settings.reset_llm()
            elif cmd == "/llmsave":
                await self.cmd_llmsave(args)
            elif cmd == "/user":
                await self.cmd_user(args)
            elif cmd == "/mcp":
                await self.cmd_mcp(args)
            elif cmd == "/search":
                await self.cmd_search(args)
            elif cmd == "/prompt":
                await self.cmd_prompt(args)
            elif cmd == "/profile":
                await self.cmd_profile(args)
            elif cmd == "/documents":
                await self.cmd_documents(args)
            elif cmd == "/analytics":
                await self.cmd_analytics(args)
            elif cmd == "/db":
                await self.cmd_db(args)
            elif cmd == "/export":
                await self.cmd_export(args)
            elif cmd in ("/about", "/version"):
                await self.cmd_about()
            elif cmd == "/history":
                self.cmd_history()
            else:
                print_warn(f"Unknown command: {cmd}")
                return True
        except KeyboardInterrupt:
            print_warn("Interrupted.")
        except ApiError as e:
            self.display_api_error(e)
        except Exception as e:
            print_error(f"Error: {e}")
        return True

    # ---- Command Implementations ----

    def show_help(self) -> None:
        """Prints all supported commands and help."""
        help_text = """
        [bold]AI Chatbot CLI Commands[/bold]
        /help                   Show this help
        /settings               Show all available runtime settings
        /set <key> <val>        Change session setting (use_rag, use_tools, streaming, spinner, etc.)
        /config                 Show current session settings
        /llmparam <k> <v>       Set LLM param override (temperature, max_tokens, etc.)
        /llmparam               Show current LLM param overrides
        /llmreset               Clear all LLM param overrides
        /llmsave <name>         Save current LLM overrides as new profile
        /user ...               User management (list, show, update, password, etc.)
        /mcp ...                MCP server management (list, add, enable, disable, remove, test)
        /search <text>          Search documents and conversation history
        /prompt ...             Prompt registry management
        /profile ...            LLM profile registry management
        /documents ...          Document management
        /analytics ...          System analytics
        /db ...                 Database management
        /export ...             Export data (conversations, etc.)
        /about, /version        Show CLI and server version info
        /history                Show your message history for this session
        /exit, /quit, /q        Quit the CLI

        Type a message to chat with the AI.
        """
        console.print(Panel(textwrap.dedent(help_text), title="Chatbot CLI Help", box=box.ROUNDED))

    def show_settings_help(self) -> None:
        """Show available settings and their types."""
        t = Table(title="Available Settings (for /set)", box=box.SIMPLE)
        t.add_column("Setting", style="cyan")
        t.add_column("Type", style="magenta")
        t.add_column("Description", style="green")
        for key, typ, desc in self.settings.available_settings():
            t.add_row(key, typ, desc)
        console.print(t)

    async def cmd_set(self, args: List[str]) -> None:
        if not args:
            self.show_settings_help()
            return
        if len(args) != 2:
            print_warn("Usage: /set <key> <value>")
            return
        key, value = args
        if key in ("use_rag", "use_tools", "enable_streaming", "spinner_enabled", "auto_title"):
            parsed = parse_bool(value)
            self.settings.set(key, parsed)
        else:
            self.settings.set(key, value)

    async def cmd_llmparam(self, args: List[str]) -> None:
        if not args:
            self.settings.display_llm_params()
        elif len(args) == 2:
            key, value = args
            if value.isdigit():
                value = int(value)
            else:
        try:
                    value = float(value)
                except ValueError:
                    if value.lower() in ("true", "false"):
                        value = parse_bool(value)
            self.settings.set_llm_param(key, value)
        else:
            print_warn("Usage: /llmparam <key> <value>")

    async def cmd_llmsave(self, args: List[str]) -> None:
        if not self.settings.llm_overrides:
            print_warn("No overrides to save. Use /llmparam to set some first.")
            return
        if not args:
            print_warn("Usage: /llmsave <name>")
            return
        name = args[0]
        title = Prompt.ask("Profile Title", default=name)
        model_name = Prompt.ask("Model Name (e.g. gpt-4)", default="gpt-4")
        description = Prompt.ask("Description", default="")
        data = LLMProfileCreate(
            name=name,
            title=title,
            description=description,
            model_name=model_name,
            parameters=self.settings.get_llm_params(),
            is_default=False,
            )
            try:
            result = await self.sdk.profiles.create_profile(data)
            print_success(f"Saved new LLM profile '{result.name}'")
        except ApiError as e:
            self.display_api_error(e)

    async def cmd_user(self, args: List[str]) -> None:
        if not args:
            print_warn("Usage: /user <list|show|update|password> ...")
            return
        subcmd = args[0]
        if subcmd == "list":
            users = await self.sdk.users.list()
            prettify_list([u.model_dump() for u in users.items], columns=["username", "email", "is_active", "is_superuser", "created_at"], title="Users")
        elif subcmd == "show":
            me = await self.sdk.users.me()
            prettify_dict(me, title="User Profile")
        elif subcmd == "update":
            if len(args) != 3:
                print_warn("Usage: /user update <key> <value>")
                return
            key, value = args[1], args[2]
            update = UserUpdate(**{key: value})
            user = await self.sdk.users.update_me(update)
            print_success("Updated user info.")
            prettify_dict(user, title="Updated Profile")
        elif subcmd == "password":
            pw = prompt_password(confirm=True)
            update = UserPasswordUpdate(current_password="", new_password=pw)
            await self.sdk.users.change_password(update)
            print_success("Password changed.")
                else:
            print_warn("Unknown user command.")

    async def cmd_mcp(self, args: List[str]) -> None:
        if not args:
            print_warn("Usage: /mcp <list|add|enable|disable|remove|test> ...")
            return
        subcmd = args[0]
        if subcmd == "list":
            servers = await self.sdk.mcp.list_servers(detailed=True)
            prettify_list(servers.get("servers", []), columns=["name", "url", "enabled", "connected", "description"], title="MCP Servers")
        elif subcmd == "add":
            if len(args) < 3:
                print_warn("Usage: /mcp add <name> <url>")
                return
            name, url = args[1], args[2]
            desc = Prompt.ask("Description", default="")
            await self.sdk.mcp.add_server(name=name, url=url, description=desc)
            print_success(f"Added MCP server '{name}'")
        elif subcmd in ("enable", "disable", "remove", "test"):
            if len(args) != 2:
                print_warn(f"Usage: /mcp {subcmd} <name>")
                return
            name = args[1]
            if subcmd == "enable":
                await self.sdk.mcp.enable_server(name)
                print_success(f"Enabled MCP server {name}")
            elif subcmd == "disable":
                await self.sdk.mcp.disable_server(name)
                print_success(f"Disabled MCP server {name}")
            elif subcmd == "remove":
                await self.sdk.mcp.remove_server(name)
                print_success(f"Removed MCP server {name}")
            elif subcmd == "test":
                resp = await self.sdk.mcp.test_server(name)
                prettify_dict(resp, title="MCP Test Result")
        else:
            print_warn("Unknown MCP command.")

    async def cmd_search(self, args: List[str]) -> None:
        if not args:
            print_warn("Usage: /search <text>")
            return
        query = " ".join(args)
        doc_req = DocumentSearchRequest(query=query, limit=5)
        docs = await self.sdk.search.search(doc_req)
        console.print("[bold]Top document matches:[/bold]")
        prettify_list(docs.get("results", []), columns=["chunk_id", "document_id", "score", "content"], title="Document Matches")
        try:
            history = await self.sdk.search.history(limit=50)
            matches = [
                m for m in history if query.lower() in str(m).lower()
            ]
            if matches:
                console.print("[bold]Conversation history matches:[/bold]")
                prettify_list(matches, title="History Matches")
        except Exception:
            pass

    async def cmd_prompt(self, args: List[str]) -> None:
        if not args:
            print_warn("Usage: /prompt <list|show|create|delete> ...")
            return
        subcmd = args[0]
        if subcmd == "list":
                prompts = await self.sdk.prompts.list_prompts()
            prettify_list(prompts.get("prompts", []), columns=["name", "title", "is_active", "created_at"], title="Prompts")
        elif subcmd == "show":
            if len(args) != 2:
                print_warn("Usage: /prompt show <name>")
                return
            name = args[1]
            p = await self.sdk.prompts.get_prompt(name)
            prettify_dict(p, title="Prompt")
        elif subcmd == "create":
            name = Prompt.ask("Name")
            title = Prompt.ask("Title")
            content = Prompt.ask("Content")
            data = PromptCreate(name=name, title=title, content=content)
            result = await self.sdk.prompts.create_prompt(data)
            print_success(f"Created prompt '{result.name}'")
        elif subcmd == "delete":
            if len(args) != 2:
                print_warn("Usage: /prompt delete <name>")
                return
            name = args[1]
            await self.sdk.prompts.delete_prompt(name)
            print_success(f"Deleted prompt '{name}'")
        else:
            print_warn("Unknown prompt command.")

    async def cmd_profile(self, args: List[str]) -> None:
        if not args:
            print_warn("Usage: /profile <list|show|delete> ...")
            return
        subcmd = args[0]
        if subcmd == "list":
                profiles = await self.sdk.profiles.list_profiles()
            prettify_list(profiles.get("profiles", []), columns=["name", "title", "is_active", "is_default", "model_name"], title="LLM Profiles")
        elif subcmd == "show":
            if len(args) != 2:
                print_warn("Usage: /profile show <name>")
                return
            name = args[1]
            p = await self.sdk.profiles.get_profile(name)
            prettify_dict(p, title="LLM Profile")
        elif subcmd == "delete":
            if len(args) != 2:
                print_warn("Usage: /profile delete <name>")
                return
            name = args[1]
            await self.sdk.profiles.delete_profile(name)
            print_success(f"Deleted profile '{name}'")
        else:
            print_warn("Unknown profile command.")

    async def cmd_documents(self, args: List[str]) -> None:
        if not args:
            print_warn("Usage: /documents <list|show|delete> ...")
            return
        subcmd = args[0]
        if subcmd == "list":
            docs = await self.sdk.documents.list()
            prettify_list([d.model_dump() for d in docs.items], columns=["id", "title", "filename", "file_type", "processing_status", "chunk_count"], title="Documents")
        elif subcmd == "show":
            if len(args) != 2:
                print_warn("Usage: /documents show <id>")
                return
            doc_id = args[1]
            doc = await self.sdk.documents.get(doc_id)
            prettify_dict(doc, title="Document Info")
        elif subcmd == "delete":
            if len(args) != 2:
                print_warn("Usage: /documents delete <id>")
                return
            doc_id = args[1]
            await self.sdk.documents.delete(doc_id)
            print_success(f"Deleted document {doc_id}")
                    else:
            print_warn("Unknown documents command.")

    async def cmd_analytics(self, args: List[str]) -> None:
        if not args:
            print_warn("Usage: /analytics <overview|usage> ...")
            return
        subcmd = args[0]
        if subcmd == "overview":
            data = await self.sdk.analytics.get_overview()
            prettify_dict(data, title="Analytics Overview")
        elif subcmd == "usage":
            data = await self.sdk.analytics.get_usage()
            prettify_dict(data, title="Analytics Usage")
        else:
            print_warn("Unknown analytics command.")

    async def cmd_db(self, args: List[str]) -> None:
        if not args:
            print_warn("Usage: /db <status|tables> ...")
            return
        subcmd = args[0]
        if subcmd == "status":
            data = await self.sdk.database.get_status()
            prettify_dict(data, title="Database Status")
        elif subcmd == "tables":
            data = await self.sdk.database.get_tables()
            prettify_dict(data, title="Database Tables")
        else:
            print_warn("Unknown db command.")
                
    async def cmd_export(self, args: List[str]) -> None:
        if not args:
            print_warn("Usage: /export <conversations|analytics> ...")
            return
        subcmd = args[0]
        if subcmd == "conversations":
            if len(args) != 2:
                print_warn("Usage: /export conversations <id>")
                return
            conv_id = args[1]
            data = await self.sdk.admin.export_conversation(conv_id)
            out_file = Prompt.ask("Enter output filename (leave empty for auto)", default="")
            out_file = out_file or None
            content = json.dumps(data, indent=2)
            path = save_conversation_to_file(content, filename=out_file)
            print_success(f"Conversation exported to {path}")
        elif subcmd == "analytics":
            data = await self.sdk.analytics.export_report()
            out_file = Prompt.ask("Enter output filename (leave empty for auto)", default="")
            out_file = out_file or None
            content = json.dumps(data, indent=2)
            path = save_conversation_to_file(content, filename=out_file)
            print_success(f"Analytics exported to {path}")
        else:
            print_warn("Unknown export command.")

    async def cmd_about(self) -> None:
        cli_ver, server_ver = get_version_info(self.sdk)
        msg = f"AI Chatbot CLI version: {cli_ver}\n"
        msg += f"Server version: {server_ver or '(unknown)'}"
        console.print(Panel(msg, title="About", box=box.SIMPLE))

    def cmd_history(self) -> None:
        if not self.history:
            print_info("No history in this session yet.")
            return
        t = Table("No.", "Message", box=box.SIMPLE)
        for i, msg in enumerate(self.history[-50:], 1):
            t.add_row(str(i), ellipsis(msg, 120))
        console.print(t)

    def display_api_error(self, e: ApiError) -> None:
        print_error(f"HTTP {e.status} {e.reason} {e.url}")
        if e.body:
                try:
                if isinstance(e.body, dict):
                    prettify_dict(e.body, title="API Error")
                    else:
                    console.print(str(e.body))
            except Exception:
                pass

async def auto_generate_title(user_message: str, sdk: AIChatbotSDK, settings: Settings) -> str:
    raw = user_message.strip()
    words = raw.split()
    if len(words) < 12:
        return ellipsis(raw, 80)
                try:
        return ellipsis(" ".join(words[:10]), 80)
    except Exception:
        return "AI Chat"

def get_user_input() -> str:
    prompt_str = "You: "
        try:
        return input(prompt_str)
    except EOFError:
        return ""
                    
async def chat_loop(
    sdk: AIChatbotSDK,
    settings: Settings,
    handler: Any,
    history: List[str]
) -> None:
    console.print("[bold green]Welcome to the AI Chatbot CLI! Type /help for commands.[/bold green]")
    conversation_id: Optional[str] = None
                
    while True:
        try:
            user_message: str = get_user_input()
            if not user_message.strip():
                continue
            if readline:
                readline.add_history(user_message)
            history.append(user_message)
            if await handler.handle(user_message):
                continue
                    
            conversation_title: Optional[str] = None
            if conversation_id is None and settings.auto_title:
                conversation_title = await auto_generate_title(user_message, sdk, settings)

            chat_req = ChatRequest(
                user_message=user_message,
                conversation_id=conversation_id,
                conversation_title=conversation_title,
                use_rag=settings.use_rag,
                use_tools=settings.use_tools,
                tool_handling_mode=ToolHandlingMode.COMPLETE_WITH_RESULTS,
                rag_documents=None,
                prompt_name=settings.prompt_name,
                profile_name=settings.profile_name,
                llm_profile=settings.get_llm_params() if settings.llm_overrides else None,
                )

            response = None
            spinner_msg = "Waiting for AI response..."

            async def fetch_and_retry_on_auth(func: Callable[[], Any]) -> Any:
                try:
                    return await func()
                except ApiError as e:
                    if e.status in (401, 403):
                        print_warn("Session expired, please log in again.")
                        if await ensure_auth(sdk):
                            return await func()
                        else:
                            raise
                    raise

            if settings.enable_streaming:
                async def do_stream():
                    stream = sdk.conversations.chat_stream(chat_req)
                    usage = None
                    latency = None
                    final_content = []
                    async for chunk in stream:
        try:
                            data = json.loads(chunk)
        except Exception:
                            data = None
                        if isinstance(data, dict):
                            if data.get("type") == "content":
                                content_piece = data.get("content", "")
                                final_content.append(content_piece)
                                print(content_piece, end="", flush=True)
                            elif data.get("type") == "start":
                                continue
                            elif data.get("type") == "complete":
                                resp = data.get("response", {})
                                usage = resp.get("usage")
                                latency = None
                            elif data.get("type") == "end":
                                continue
                        else:
                            print(chunk, end="", flush=True)
                            final_content.append(str(chunk))
                    print()
                    if usage:
                        display_token_stats(usage, latency)
                await do_stream()
            else:
                async with SpinnerContext(spinner_msg, enabled=True):
                    response = await fetch_and_retry_on_auth(lambda: sdk.conversations.chat(chat_req))

            if response:
                ai_msg_raw = response.ai_message.content
                ai_msg = extract_ai_content(ai_msg_raw)
                console.print(f"[bold green]AI:[/bold green] {ai_msg}")
                conversation_id = str(response.conversation.id)
                settings.last_conversation_id = conversation_id
                display_token_stats(response.usage, response.response_time_ms)
        except KeyboardInterrupt:
            print_warn("\nInterrupted.")
            break
        except ApiError as e:
            handler.display_api_error(e)
        except Exception as e:
            print_error(f"Unexpected error: {e}")

async def ensure_auth(sdk: AIChatbotSDK) -> bool:
    token = load_token()
    if token:
        sdk.set_token(token)
    try:
            await sdk.users.me()
            return True
        except Exception:
            pass
    username = config.client_username or input("Username: ")
    password = config.client_password or prompt_password()
    try:
        token_obj = await sdk.auth.login(username, password)
        sdk.set_token(token_obj.access_token)
        save_token(token_obj.access_token)
        print_success("Logged in.")
        return True
    except Exception as e:
        print_error(f"Login failed: {e}")
        return False

def setup_graceful_exit(loop: asyncio.AbstractEventLoop) -> None:
    def _exit_handler():
        print_warn("\nExiting. (Ctrl+C)")
        sys.exit(0)
    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, _exit_handler)
    except NotImplementedError:
        pass

async def main() -> None:
    if readline:
        setup_readline()
    history: List[str] = []
    sdk = AIChatbotSDK(
        base_url=config.api_base_url,
        token=None,
        timeout=float(config.api_timeout),
    )
    settings = Settings(config)
    handler = CommandHandler(sdk, settings, history)
    async with sdk:
        loop = asyncio.get_event_loop()
        setup_graceful_exit(loop)
        if not await ensure_auth(sdk):
            sys.exit(1)
        await chat_loop(sdk, settings, handler, history)

if __name__ == "__main__":
    asyncio.run(main())
