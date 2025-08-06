"""
GUI Application Management Commands.

This module provides CLI commands for launching and managing the PySide6 desktop GUI
client for the AI Chatbot Platform.
"""
import os
import subprocess
import sys
from pathlib import Path

from async_typer import AsyncTyper
from rich.console import Console

gui_app = AsyncTyper(help="GUI Desktop Application Commands")
console = Console()


@gui_app.command("launch")
def launch_gui():
    """Launch the PySide6 desktop GUI application."""
    try:
        # Check if PySide6 is available
        try:
            import PySide6
            console.print("✓ PySide6 found", style="green")
        except ImportError:
            console.print("✗ PySide6 not installed. Installing...", style="yellow")
            subprocess.run([
                sys.executable, "-m", "pip", "install", "PySide6"
            ], check=True)
            console.print("✓ PySide6 installed successfully", style="green")
        
        # Get the script path
        base_dir = Path(__file__).parent.parent
        gui_script = base_dir / "client" / "gui_chatbot.py"
        
        if not gui_script.exists():
            console.print(f"✗ GUI script not found: {gui_script}", style="red")
            return
        
        console.print("🚀 Launching AI Chatbot GUI...", style="cyan")
        
        # Set environment for the GUI
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{base_dir / 'client'}:{base_dir}"
        
        # Launch the GUI application
        process = subprocess.Popen([
            sys.executable, str(gui_script)
        ], env=env)
        
        console.print("✓ GUI application started", style="green")
        console.print(f"Process ID: {process.pid}", style="dim")
        
    except subprocess.CalledProcessError as e:
        console.print(f"✗ Failed to install PySide6: {e}", style="red")
    except Exception as e:
        console.print(f"✗ Failed to launch GUI: {e}", style="red")


@gui_app.command("check")
def check_gui_requirements():
    """Check if GUI requirements are met."""
    console.print("Checking GUI requirements...", style="cyan")
    
    # Check Python version
    if sys.version_info >= (3, 8):
        console.print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} (compatible)", style="green")
    else:
        console.print(f"✗ Python {sys.version_info.major}.{sys.version_info.minor} (requires 3.8+)", style="red")
        return
    
    # Check PySide6
    try:
        import PySide6
        console.print(f"✓ PySide6 {PySide6.__version__}", style="green")
    except ImportError:
        console.print("✗ PySide6 not installed", style="red")
        console.print("  Install with: pip install PySide6", style="dim")
    
    # Check GUI script
    base_dir = Path(__file__).parent.parent
    gui_script = base_dir / "client" / "gui_chatbot.py"
    
    if gui_script.exists():
        console.print(f"✓ GUI script found: {gui_script}", style="green")
    else:
        console.print(f"✗ GUI script missing: {gui_script}", style="red")
    
    # Check launcher
    launcher = base_dir / "chatbot-gui"
    if launcher.exists() and launcher.stat().st_mode & 0o111:
        console.print(f"✓ GUI launcher: {launcher}", style="green")
    else:
        console.print(f"✗ GUI launcher missing or not executable: {launcher}", style="red")
    
    # Check display (Linux/macOS)
    if os.name != "nt":
        if "DISPLAY" in os.environ:
            console.print(f"✓ Display server: {os.environ['DISPLAY']}", style="green")
        else:
            console.print("⚠ No DISPLAY environment variable (headless mode)", style="yellow")
    
    console.print("\nGUI requirements check complete.", style="cyan")


@gui_app.command("info")
def gui_info():
    """Show information about the GUI client."""
    console.print("AI Chatbot Platform - Desktop GUI Client", style="bold cyan")
    console.print()
    console.print("Built with PySide6 for cross-platform desktop compatibility")
    console.print()
    console.print("Features:", style="bold")
    console.print("• Native desktop interface with Qt styling")
    console.print("• Real-time chat with streaming responses")
    console.print("• Tabbed interface for chat, settings, and management")
    console.print("• Document upload and search capabilities")
    console.print("• Visual settings configuration")
    console.print("• Authentication and user management")
    console.print("• System administration tools")
    console.print()
    console.print("Usage:", style="bold")
    console.print("• Launch with: python manage.py gui launch")
    console.print("• Or directly: ./chatbot-gui")
    console.print("• Check requirements: python manage.py gui check")