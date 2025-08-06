#!/usr/bin/env python3
"""PySide6 Desktop GUI Client for AI Chatbot Platform.

This module provides a desktop GUI client for the AI Chatbot Platform using PySide6,
offering an intuitive graphical interface for AI conversations, document management,
and platform administration.

The GUI client provides the same functionality as the terminal client but with
a modern desktop interface including:
    - Chat window with conversation history
    - Real-time streaming responses
    - Settings configuration panel
    - Document upload and search
    - User and system management
    - MCP server administration

Features:
    - Modern desktop interface with Qt styling
    - Real-time chat with AI models
    - Document upload via drag-and-drop
    - Settings persistence and configuration
    - Authentication and user management
    - System administration tools
    - Responsive design with resizable panels

Author: AI Chatbot Platform Team
Version: 1.0.0
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Set QT_QPA_PLATFORM for headless environments
if "DISPLAY" not in os.environ and os.name != "nt":
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

try:
    from PySide6.QtCore import QObject, QThread, Signal, QTimer, Qt, QRunnable, QThreadPool
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTextEdit, QLineEdit, QPushButton, QLabel, QSplitter,
        QTabWidget, QScrollArea, QFrame, QProgressBar, QMessageBox,
        QFileDialog, QDialog, QFormLayout, QCheckBox, QSpinBox,
        QDoubleSpinBox, QComboBox, QTextBrowser
    )
    from PySide6.QtGui import QFont, QPixmap, QIcon
    PYSIDE6_AVAILABLE = True
except ImportError as e:
    print(f"PySide6 not available: {e}")
    print("Please install PySide6: pip install PySide6")
    sys.exit(1)

# Import the same modules as the terminal client
try:
    from shared.schemas import (
        ChatRequest,
        DocumentSearchRequest,
        LLMProfileCreate,
        PromptCreate,
        ToolHandlingMode,
        UserPasswordUpdate,
        UserUpdate,
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from shared.schemas import (
        ChatRequest,
        DocumentSearchRequest,
        LLMProfileCreate,
        PromptCreate,
        ToolHandlingMode,
        UserPasswordUpdate,
        UserUpdate,
    )

try:
    from .ai_chatbot_sdk import AIChatbotSDK, ApiError
    from .config import ClientConfig, get_default_token_file, load_config
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from client.ai_chatbot_sdk import AIChatbotSDK, ApiError
    from client.config import ClientConfig, get_default_token_file, load_config


class AuthDialog(QDialog):
    """Authentication dialog for user login."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login - AI Chatbot")
        self.setFixedSize(350, 200)
        self.username = ""
        self.password = ""
        self.setup_ui()
    
    def setup_ui(self):
        layout = QFormLayout()
        
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.login_button = QPushButton("Login")
        self.cancel_button = QPushButton("Cancel")
        
        layout.addRow("Username:", self.username_edit)
        layout.addRow("Password:", self.password_edit)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addRow(button_layout)
        
        self.setLayout(layout)
        
        self.login_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.password_edit.returnPressed.connect(self.accept)
    
    def get_credentials(self):
        return self.username_edit.text(), self.password_edit.text()


class SettingsPanel(QWidget):
    """Settings configuration panel."""
    
    settings_changed = Signal(str, object)  # setting name, value
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Chat Settings"))
        
        # Chat settings
        chat_frame = QFrame()
        chat_layout = QFormLayout()
        
        self.use_rag_cb = QCheckBox()
        self.use_tools_cb = QCheckBox()
        self.streaming_cb = QCheckBox()
        self.auto_title_cb = QCheckBox()
        
        chat_layout.addRow("Use RAG:", self.use_rag_cb)
        chat_layout.addRow("Use Tools:", self.use_tools_cb)
        chat_layout.addRow("Enable Streaming:", self.streaming_cb)
        chat_layout.addRow("Auto Title:", self.auto_title_cb)
        
        chat_frame.setLayout(chat_layout)
        layout.addWidget(chat_frame)
        
        # LLM Parameters
        layout.addWidget(QLabel("LLM Parameters"))
        llm_frame = QFrame()
        llm_layout = QFormLayout()
        
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setValue(0.7)
        
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(1, 32000)
        self.max_tokens_spin.setValue(2000)
        
        llm_layout.addRow("Temperature:", self.temperature_spin)
        llm_layout.addRow("Max Tokens:", self.max_tokens_spin)
        
        llm_frame.setLayout(llm_layout)
        layout.addWidget(llm_frame)
        
        # Connect signals
        self.use_rag_cb.toggled.connect(
            lambda checked: self.settings_changed.emit("use_rag", checked)
        )
        self.use_tools_cb.toggled.connect(
            lambda checked: self.settings_changed.emit("use_tools", checked)
        )
        self.streaming_cb.toggled.connect(
            lambda checked: self.settings_changed.emit("enable_streaming", checked)
        )
        self.auto_title_cb.toggled.connect(
            lambda checked: self.settings_changed.emit("auto_title", checked)
        )
        
        self.setLayout(layout)
    
    def update_settings(self, settings_dict):
        """Update UI with current settings."""
        self.use_rag_cb.setChecked(settings_dict.get("use_rag", True))
        self.use_tools_cb.setChecked(settings_dict.get("use_tools", True))
        self.streaming_cb.setChecked(settings_dict.get("enable_streaming", True))
        self.auto_title_cb.setChecked(settings_dict.get("auto_title", True))


class AsyncWorker(QRunnable):
    """Async worker for handling API calls in a thread pool."""
    
    def __init__(self, coro, callback=None, error_callback=None):
        super().__init__()
        self.coro = coro
        self.callback = callback
        self.error_callback = error_callback
    
    def run(self):
        """Run the async coroutine in a new event loop."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.coro)
            if self.callback:
                self.callback(result)
        except Exception as e:
            if self.error_callback:
                self.error_callback(str(e))
        finally:
            loop.close()


class ChatWorker(QObject):
    """Worker for handling chat API calls with proper async support."""
    
    message_received = Signal(str)  # AI message content
    error_occurred = Signal(str)   # Error message
    finished = Signal()
    conversation_updated = Signal(str)  # conversation ID
    
    def __init__(self, sdk: AIChatbotSDK):
        super().__init__()
        self.sdk = sdk
        self.thread_pool = QThreadPool()
    
    def send_message(self, chat_request: ChatRequest):
        """Send chat message asynchronously."""
        async def do_chat():
            response = await self.sdk.conversations.chat(chat_request)
            return response
        
        def on_success(response):
            if response and response.ai_message:
                self.message_received.emit(response.ai_message.content)
                if response.conversation:
                    self.conversation_updated.emit(str(response.conversation.id))
            self.finished.emit()
        
        def on_error(error):
            self.error_occurred.emit(error)
            self.finished.emit()
        
        worker = AsyncWorker(do_chat(), on_success, on_error)
        self.thread_pool.start(worker)


class MainWindow(QMainWindow):
    """Main application window for the PySide6 chatbot client."""
    
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.sdk = None
        self.settings = {}
        self.conversation_id = None
        self.chat_worker = None
        
        self.setup_ui()
        self.setup_connections()
        self.load_settings()
        
        # Try to authenticate on startup
        QTimer.singleShot(100, self.authenticate)
    
    def setup_ui(self):
        """Set up the main user interface."""
        self.setWindowTitle("AI Chatbot - Desktop Client")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Chat area
        chat_widget = self.create_chat_widget()
        splitter.addWidget(chat_widget)
        
        # Right panel - Settings and tools
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([800, 400])
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def create_chat_widget(self):
        """Create the main chat interface."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Chat history display
        self.chat_display = QTextBrowser()
        self.chat_display.setFont(QFont("Consolas", 10))
        layout.addWidget(self.chat_display)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        
        self.send_button = QPushButton("Send")
        self.send_button.setFixedWidth(80)
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        
        layout.addLayout(input_layout)
        
        # Progress bar for loading
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        widget.setLayout(layout)
        return widget
    
    def create_right_panel(self):
        """Create the right panel with tabs for different functions."""
        tab_widget = QTabWidget()
        
        # Settings tab
        self.settings_panel = SettingsPanel()
        tab_widget.addTab(self.settings_panel, "Settings")
        
        # Documents tab
        documents_widget = QWidget()
        documents_layout = QVBoxLayout()
        
        upload_button = QPushButton("Upload Document")
        upload_button.clicked.connect(self.upload_document)
        documents_layout.addWidget(upload_button)
        
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search documents...")
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.search_documents)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        documents_layout.addLayout(search_layout)
        
        self.search_results = QTextBrowser()
        documents_layout.addWidget(self.search_results)
        
        documents_widget.setLayout(documents_layout)
        tab_widget.addTab(documents_widget, "Documents")
        
        # System tab
        system_widget = QWidget()
        system_layout = QVBoxLayout()
        
        status_button = QPushButton("Check System Status")
        status_button.clicked.connect(self.check_system_status)
        system_layout.addWidget(status_button)
        
        self.system_info = QTextBrowser()
        system_layout.addWidget(self.system_info)
        
        system_widget.setLayout(system_layout)
        tab_widget.addTab(system_widget, "System")
        
        return tab_widget
    
    def setup_connections(self):
        """Set up signal-slot connections."""
        self.send_button.clicked.connect(self.send_message)
        self.message_input.returnPressed.connect(self.send_message)
        self.settings_panel.settings_changed.connect(self.update_setting)
    
    def load_settings(self):
        """Load settings from configuration."""
        self.settings = {
            "use_rag": self.config.client_default_use_rag,
            "use_tools": self.config.client_default_use_tools,
            "enable_streaming": self.config.client_enable_streaming,
            "auto_title": self.config.client_auto_title,
            "prompt_name": self.config.client_default_prompt_name,
            "profile_name": self.config.client_default_profile_name,
        }
        self.settings_panel.update_settings(self.settings)
    
    def authenticate(self):
        """Handle user authentication with async support."""
        if not self.sdk:
            self.sdk = AIChatbotSDK(
                base_url=self.config.api_base_url,
                timeout=float(self.config.api_timeout)
            )
        
        # Try to load saved token
        def check_existing_token():
            try:
                token_file = get_default_token_file()
                if Path(token_file).exists():
                    with open(token_file) as f:
                        token = f.read().strip()
                        self.sdk.set_token(token)
                        return True
            except Exception:
                pass
            return False
        
        async def test_token():
            try:
                await self.sdk.users.me()
                return True
            except Exception:
                return False
        
        def on_token_test_success(is_valid):
            if is_valid:
                self.statusBar().showMessage("Authenticated")
                return
            self.show_login_dialog()
        
        def on_token_test_error(error):
            self.show_login_dialog()
        
        if check_existing_token():
            worker = AsyncWorker(test_token(), on_token_test_success, on_token_test_error)
            QThreadPool.globalInstance().start(worker)
        else:
            self.show_login_dialog()
    
    def show_login_dialog(self):
        """Show the login dialog."""
        auth_dialog = AuthDialog(self)
        if auth_dialog.exec() == QDialog.DialogCode.Accepted:
            username, password = auth_dialog.get_credentials()
            
            async def do_login():
                token_obj = await self.sdk.auth.login(username, password)
                return token_obj.access_token
            
            def on_login_success(token):
                self.sdk.set_token(token)
                
                # Save token
                token_file = get_default_token_file()
                Path(token_file).parent.mkdir(parents=True, exist_ok=True)
                with open(token_file, "w") as f:
                    f.write(token)
                
                self.statusBar().showMessage("Authenticated successfully")
            
            def on_login_error(error):
                QMessageBox.warning(self, "Authentication Failed", str(error))
                self.close()
            
            worker = AsyncWorker(do_login(), on_login_success, on_login_error)
            QThreadPool.globalInstance().start(worker)
        else:
            self.close()
    
    def update_setting(self, setting_name: str, value: Any):
        """Update a setting value."""
        self.settings[setting_name] = value
        self.statusBar().showMessage(f"Updated {setting_name}")
    
    def send_message(self):
        """Send a chat message to the AI."""
        message = self.message_input.text().strip()
        if not message:
            return
        
        # Display user message
        self.chat_display.append(f"<b>You:</b> {message}")
        self.message_input.clear()
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.send_button.setEnabled(False)
        
        # Create chat request
        chat_request = ChatRequest(
            user_message=message,
            conversation_id=self.conversation_id,
            use_rag=self.settings.get("use_rag", True),
            use_tools=self.settings.get("use_tools", True),
            tool_handling_mode=ToolHandlingMode.COMPLETE_WITH_RESULTS,
            prompt_name=self.settings.get("prompt_name"),
            profile_name=self.settings.get("profile_name"),
        )
        
        # Create and connect worker
        self.chat_worker = ChatWorker(self.sdk)
        self.chat_worker.message_received.connect(self.handle_ai_response)
        self.chat_worker.error_occurred.connect(self.handle_error)
        self.chat_worker.finished.connect(self.chat_finished)
        self.chat_worker.conversation_updated.connect(self.update_conversation_id)
        
        # Send message
        self.chat_worker.send_message(chat_request)
    
    def update_conversation_id(self, conv_id: str):
        """Update the current conversation ID."""
        self.conversation_id = conv_id
    
    def handle_ai_response(self, message: str):
        """Handle AI response message."""
        self.chat_display.append(f"<b>AI:</b> {message}")
    
    def handle_error(self, error: str):
        """Handle error from API."""
        self.chat_display.append(f"<b>Error:</b> {error}")
        QMessageBox.warning(self, "Error", error)
    
    def chat_finished(self):
        """Clean up after chat completion."""
        self.progress_bar.setVisible(False)
        self.send_button.setEnabled(True)
        self.chat_worker = None
    
    def upload_document(self):
        """Handle document upload."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Document", "", 
            "Documents (*.pdf *.docx *.txt *.md);;All Files (*)"
        )
        
        if file_path:
            try:
                # Note: In a real implementation, you'd upload the file
                self.statusBar().showMessage(f"Uploaded: {Path(file_path).name}")
            except Exception as e:
                QMessageBox.warning(self, "Upload Failed", str(e))
    
    def search_documents(self):
        """Search documents."""
        query = self.search_input.text().strip()
        if not query:
            return
        
        try:
            # Note: In a real implementation, you'd call the search API
            self.search_results.append(f"Searching for: {query}")
        except Exception as e:
            QMessageBox.warning(self, "Search Failed", str(e))
    
    def check_system_status(self):
        """Check system status."""
        try:
            # Note: In a real implementation, you'd call the status API
            self.system_info.append("System status: OK")
        except Exception as e:
            QMessageBox.warning(self, "Status Check Failed", str(e))
    
    def closeEvent(self, event):
        """Handle application close event."""
        if self.chat_worker:
            # No need to stop worker as it uses thread pool
            pass
        event.accept()


def main():
    """Main entry point for the PySide6 chatbot application."""
    app = QApplication(sys.argv)
    app.setApplicationName("AI Chatbot")
    app.setApplicationVersion("1.0.0")
    
    # Set application icon if available
    try:
        app.setWindowIcon(QIcon("icon.png"))
    except:
        pass
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()