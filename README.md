# AI Chatbot Platform

**Generated on: 2025-07-14 03:52:46 UTC**  
**Current User: lllucius**

A production-grade AI chatbot platform with RAG (Retrieval-Augmented Generation) capabilities, document processing, vector search, MCP (Model Context Protocol) tool integration, and a comprehensive React frontend for experimentation and management.

## 🚀 Features

### 🔐 Authentication & User Management
- JWT-based authentication with secure token handling
- User registration, login, and profile management
- Role-based access control (regular users and superusers)
- Password hashing with bcrypt
- Admin interface for user administration

### 📄 Document Processing System
- **Multi-format Support**: PDF, DOCX, TXT, MD, RTF
- **Intelligent Processing**: Automatic text extraction and chunking
- **Vector Embeddings**: Semantic search capabilities
- **Async Processing**: Non-blocking document processing
- **Status Tracking**: Real-time processing status updates

### 🔍 Advanced Search Capabilities
- **Vector Search**: Semantic similarity using embeddings
- **Text Search**: Traditional full-text search with ranking
- **Hybrid Search**: Combines vector and text search results
- **MMR Search**: Maximum Marginal Relevance for diverse results
- **Configurable Parameters**: Similarity thresholds and result limits

### 🤖 AI Chat Interface
- **OpenAI Integration**: GPT-4 and embedding models
- **RAG Capabilities**: Document-aware AI responses
- **Conversation Management**: Persistent chat history
- **Context Retention**: Maintains conversation context
- **Usage Tracking**: Token usage monitoring and optimization
- **Prompt Registry**: Centralized prompt management with categories and tags
- **LLM Profile System**: Parameter profiles for different use cases (creative, precise, etc.)
- **Default Configurations**: Easy switching between conversation modes

### 🛠️ Tool Integration (MCP)
- **MCP Protocol**: Model Context Protocol client
- **Server Registry**: Centralized management of MCP servers
- **Tool Management**: Enable/disable individual tools with usage tracking
- **External Tools**: File system, web search, and custom tools
- **Function Calling**: AI can execute external functions
- **Usage Analytics**: Comprehensive tool usage statistics and performance metrics
- **Extensible Architecture**: Easy plugin development

### 📊 Monitoring & Analytics
- **Health Checks**: Comprehensive system monitoring
- **Performance Metrics**: Response times and usage statistics
- **Error Tracking**: Structured logging and error handling
- **Admin Dashboard**: System statistics and user management

### 🎨 Advanced React Frontend
- **TypeScript Integration**: Full type safety with comprehensive API interfaces
- **Material-UI v5**: Modern, responsive design system
- **Real-time Chat**: Advanced chatbot interface with conversation management
- **Document Management**: Drag-and-drop upload with processing status tracking
- **Analytics Dashboard**: Interactive charts and visualizations using Chart.js
- **LLM Profile Management**: Parameter tuning interface for different conversation modes
- **Prompt Template System**: Manage and organize AI prompts with categorization
- **MCP Tools Interface**: Server and tool management with usage analytics
- **Advanced Search**: Multiple algorithms with filtering and result visualization
- **Responsive Design**: Mobile-friendly interface with optimized navigation

## 🏗️ Architecture

### Technology Stack

#### Backend
- **Backend**: FastAPI with async/await
- **Database**: PostgreSQL 14+ with pgvector
- **AI/ML**: OpenAI API, sentence-transformers
- **Authentication**: JWT with python-jose
- **Document Processing**: PyPDF2, python-docx, striprtf
- **Vector Search**: pgvector with multiple algorithms
- **MCP Integration**: FastMCP for tool integration
- **Registry Systems**: Comprehensive management for servers, tools, prompts, and LLM profiles
- **CLI Framework**: Typer with Rich for beautiful terminal interfaces

#### Frontend
- **Framework**: React 18 with TypeScript
- **UI Library**: Material-UI v5
- **State Management**: React Query (TanStack Query) + React Context
- **Charts**: Chart.js with react-chartjs-2
- **Routing**: React Router v6
- **HTTP Client**: Axios with interceptors
- **Build Tool**: Create React App with TypeScript template

### Project Structure
```
ai-chatbot-platform/
├── app/                          # FastAPI backend
│   ├── api/                     # REST API endpoints
│   ├── core/                    # Core functionality
│   ├── models/                  # Database models
│   ├── schemas/                 # Pydantic schemas
│   ├── services/                # Business logic
│   └── utils/                   # Utilities
├── frontend/                    # React TypeScript frontend
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   ├── pages/              # Page components
│   │   ├── hooks/              # React Query hooks
│   │   ├── services/           # API service layer
│   │   ├── types/              # TypeScript definitions
│   │   └── contexts/           # React contexts
│   ├── public/                 # Static assets
│   └── package.json            # Dependencies
├── scripts/                     # Management scripts
├── migrations/                  # Database migrations
└── requirements.txt             # Backend dependencies
```

## 🚦 Quick Start

### Prerequisites
- Python 3.11+ or 3.12
- Node.js 18+ and npm (for frontend)
- PostgreSQL 14+ with pgvector extension
- OpenAI API key

### Option 1: Full Stack Setup with Frontend

1. **Backend Setup**:
```bash
git clone <repository-url>
cd ai-chatbot-mcp

# Setup Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings (DATABASE_URL, SECRET_KEY, OPENAI_API_KEY)

# Setup PostgreSQL with pgvector
# Connect to PostgreSQL as superuser and run:
# CREATE DATABASE ai_chatbot;
# \c ai_chatbot;
# CREATE EXTENSION vector;

# Initialize database
python scripts/startup.py

# Start backend
uvicorn app.main:app --reload
```

2. **Frontend Setup**:
```bash
# In a new terminal, from the project root
./setup-frontend.sh

# Or manually:
cd frontend
npm install
npm start
```

3. **Access the Application**:
- **Frontend**: http://localhost:3000 (React app)
- **Backend API**: http://localhost:8000/docs (Swagger docs)
- **Health Check**: http://localhost:8000/api/v1/health

### Option 2: Backend Only Setup

```bash
git clone <repository-url>
cd ai-chatbot-mcp
python scripts/dev_setup.py
# Follow the printed instructions to complete setup
```

### Default Admin Credentials
- **Username**: admin
- **Email**: admin@example.com  
- **Password**: Admin123!

⚠️ **IMPORTANT**: Change these credentials immediately in production!

## 📱 Frontend Application

The React TypeScript frontend provides a comprehensive interface for all platform features:

### Key Interfaces
- **🏠 Dashboard**: System overview with statistics and quick actions
- **💬 Chat Interface**: Real-time AI conversations with RAG capabilities
- **📄 Document Manager**: Upload, process, and manage documents
- **🔍 Advanced Search**: Multiple search algorithms with result visualization
- **📊 Analytics**: Interactive charts showing usage trends and performance
- **🎛️ LLM Profiles**: Parameter tuning for different AI behaviors
- **📝 Prompt Templates**: Manage AI prompts with categorization
- **🛠️ MCP Tools**: Server and tool management interface
- **⚙️ Settings**: User preferences and account management
- **👤 Admin Panel**: User management and system administration

### Frontend Features
- **TypeScript**: Full type safety with comprehensive API interfaces
- **Responsive Design**: Mobile-friendly interface with Material-UI
- **Real-time Updates**: Live status tracking and notifications
- **Drag & Drop**: Easy file uploads with progress tracking
- **Interactive Charts**: Chart.js visualizations for analytics
- **Advanced Forms**: Rich form controls with validation
- **Error Handling**: User-friendly error messages and recovery
- **Accessibility**: ARIA labels and keyboard navigation

### Getting Started with Frontend
```bash
# Quick setup
./setup-frontend.sh

# Manual setup
cd frontend
npm install
npm start
```

For detailed frontend documentation, see [`frontend/FRONTEND_README.md`](frontend/FRONTEND_README.md).

## 📖 API Usage

### Authentication
```python
import httpx

# Register a new user
response = httpx.post("http://localhost:8000/api/v1/auth/register", json={
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe"
})

# Login to get access token
response = httpx.post("http://localhost:8000/api/v1/auth/login", json={
    "username": "john_doe",
    "password": "SecurePass123!"
})
token = response.json()["access_token"]

# Use token for authenticated requests
headers = {"Authorization": f"Bearer {token}"}
```

### Document Upload and Processing
```python
# Upload a document
with open("document.pdf", "rb") as f:
    files = {"file": f}
    data = {"title": "My Document"}
    response = httpx.post(
        "http://localhost:8000/api/v1/documents/upload",
        files=files,
        data=data,
        headers=headers
    )

document_id = response.json()["document"]["id"]

# Check processing status
response = httpx.get(
    f"http://localhost:8000/api/v1/documents/{document_id}/status",
    headers=headers
)
```

### Document Search
```python
# Search documents
response = httpx.post("http://localhost:8000/api/v1/search/", 
    json={
        "query": "machine learning algorithms",
        "algorithm": "hybrid",
        "limit": 10,
        "threshold": 0.8
    },
    headers=headers
)

results = response.json()["results"]
```

### AI Chat
```python
# Start a conversation
response = httpx.post("http://localhost:8000/api/v1/conversations/chat",
    json={
        "user_message": "What is machine learning?",
        "use_rag": True,
        "temperature": 0.7
    },
    headers=headers
)

ai_response = response.json()["ai_message"]["content"]
conversation_id = response.json()["conversation"]["id"]

# Continue conversation
response = httpx.post("http://localhost:8000/api/v1/conversations/chat",
    json={
        "user_message": "Can you give me an example?",
        "conversation_id": conversation_id,
        "use_rag": True
    },
    headers=headers
)
```

### Registry-Based Management APIs

The platform includes comprehensive registry APIs for managing prompts, LLM profiles, and MCP tools:

#### Prompt Management
```python
# List available prompts
response = httpx.get("http://localhost:8000/api/v1/prompts/", headers=headers)
prompts = response.json()["data"]["prompts"]

# Get specific prompt
response = httpx.get("http://localhost:8000/api/v1/prompts/technical_assistant", headers=headers)
prompt_details = response.json()["data"]

# Use specific prompt in chat
response = httpx.post("http://localhost:8000/api/v1/conversations/chat",
    json={
        "user_message": "Explain quantum computing",
        "prompt_name": "technical_assistant",
        "use_rag": True
    },
    headers=headers
)
```

#### LLM Profile Management
```python
# List available LLM profiles
response = httpx.get("http://localhost:8000/api/v1/profiles/", headers=headers)
profiles = response.json()["data"]["profiles"]

# Get specific profile parameters
response = httpx.get("http://localhost:8000/api/v1/profiles/creative", headers=headers)
profile_params = response.json()["data"]["parameters"]

# Use specific profile in chat
response = httpx.post("http://localhost:8000/api/v1/conversations/chat",
    json={
        "user_message": "Write a short story",
        "profile_name": "creative",
        "temperature": 1.0  # Override profile parameter
    },
    headers=headers
)
```

#### Enhanced Tool Management
```python
# List available MCP tools with registry information
response = httpx.get("http://localhost:8000/api/v1/tools/", headers=headers)
tools_data = response.json()["data"]
print(f"Total tools: {tools_data['total_tools']}")
print(f"Enabled tools: {tools_data['enabled_tools']}")

# Enable/disable specific tools
response = httpx.post("http://localhost:8000/api/v1/tools/weather_tool/enable", headers=headers)

# Get tool usage statistics
stats = tools_data["tool_statistics"]
```
```

## 🔧 Management Commands

The platform now includes a comprehensive CLI management system that provides full administrative capabilities:

### New Enhanced CLI (Recommended)
```bash
# Show all available commands
python manage.py --help

# Quick start guide
python manage.py quickstart

# System health check
python manage.py health

# System status overview
python manage.py status

# API duplicate analysis
python manage.py api-analysis
```

### User Management
```bash
# Create users
python manage.py users create username email@example.com --superuser
python manage.py users create john john@example.com "SecurePass123"

# List and manage users
python manage.py users list --active-only --search "john"
python manage.py users show john
python manage.py users reset-password john
python manage.py users stats
```

### Document Management
```bash
# Upload and manage documents
python manage.py documents upload /path/to/file.pdf --user john --process
python manage.py documents list --status completed --user john
python manage.py documents search "machine learning" --limit 10
python manage.py documents show 123
python manage.py documents cleanup --status failed --older-than 30
```

### Conversation Management  
```bash
# Manage conversations
python manage.py conversations list --user john --active-only
python manage.py conversations show 456 --messages --message-limit 20
python manage.py conversations export 456 --format json --output backup.json
python manage.py conversations search "API documentation"
python manage.py conversations archive --older-than 90
```

### Analytics & Reporting
```bash
# System analytics
python manage.py analytics overview
python manage.py analytics usage --period 7d --detailed
python manage.py analytics performance
python manage.py analytics users --top 10 --metric messages
python manage.py analytics export-report --output report.json --details
```

### Database Management
```bash
# Database operations
python manage.py database status
python manage.py database init
python manage.py database upgrade
python manage.py database backup --output backup.sql
python manage.py database tables
python manage.py database vacuum
```

### Background Task Management
```bash
# Task monitoring
python manage.py tasks status
python manage.py tasks workers
python manage.py tasks active
python manage.py tasks retry-failed
python manage.py tasks monitor --refresh 5 --duration 300
```

### Job Management
```bash
# List scheduled jobs
python manage.py jobs list --status active
python manage.py jobs list --overdue-only

# Create and manage jobs
python manage.py jobs create system_backup "System Backup" database_maintenance daily "03:00" "app.tasks.backup"
python manage.py jobs update 1 --schedule "04:00" --enabled
python manage.py jobs execute 1 --force

# Job scheduling and validation
python manage.py jobs validate-schedule daily "09:30"
python manage.py jobs stats
python manage.py jobs overdue
```

### MCP Server & Tool Management
```bash
# Server management
python manage.py mcp list-servers --detailed
python manage.py mcp add-server myserver http://localhost:9000/mcp --description "My MCP Server"
python manage.py mcp enable-server myserver
python manage.py mcp disable-server myserver
python manage.py mcp remove-server myserver --confirm

# Tool management
python manage.py mcp list-tools --enabled-only
python manage.py mcp enable-tool myserver_tool
python manage.py mcp disable-tool myserver_tool
python manage.py mcp stats --limit 20
```

### Prompt Management
```bash
# Prompt management
python manage.py prompts list --category general
python manage.py prompts add myprompt --title "My Prompt" --content "You are a helpful assistant..."
python manage.py prompts update myprompt --description "Updated description"
python manage.py prompts set-default myprompt
python manage.py prompts activate myprompt
python manage.py prompts deactivate myprompt
python manage.py prompts remove myprompt --confirm

# Organization and discovery
python manage.py prompts categories
python manage.py prompts tags
python manage.py prompts stats
```

### LLM Parameter Profile Management
```bash
# Profile management
python manage.py profiles list --detailed
python manage.py profiles add creative --title "Creative Writing" --temperature 1.0 --top-p 0.95
python manage.py profiles update creative --max-tokens 3000
python manage.py profiles set-default balanced
python manage.py profiles clone creative creative-v2 --title "Creative v2"
python manage.py profiles activate creative
python manage.py profiles deactivate creative
python manage.py profiles remove creative --confirm

# Statistics and monitoring
python manage.py profiles stats
```

### API Analysis and Maintenance
```bash
# Analyze project for duplicate APIs
python manage.py api-analysis

# View detailed analysis reports
cat docs/duplicate_api_analysis_report.md
cat docs/duplicate_api_implementation_guide.md

# Quick analysis summary
python scripts/duplicate_api_summary.py
```

The API analysis feature identifies potentially duplicate or functionally similar APIs across the project:
- **High Priority Duplicates**: Identical functionality requiring consolidation
- **Medium Priority**: Similar functionality that could be optimized  
- **Low Priority**: Acceptable functional overlaps (API vs CLI)

Generated reports provide detailed implementation guidance for consolidating duplicate endpoints and improving API consistency.

### Legacy CLI (Deprecated)
The original simple management commands are still available but deprecated:
```bash
# Create a regular user (deprecated - use new CLI)
python scripts/manage_simple.py create-user username email@example.com password

# Create a superuser (deprecated - use new CLI) 
python scripts/manage_simple.py create-superuser admin admin@example.com password

# List all users (deprecated - use new CLI)
python scripts/manage_simple.py list-users

# Show system statistics (deprecated - use new CLI)
python scripts/manage_simple.py stats
```

**Migration Notice**: Please migrate to the new CLI system using `python manage.py`. The old scripts will show migration guidance when used.

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SECRET_KEY` | JWT secret key (32+ chars) | Required |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_CHAT_MODEL` | OpenAI chat model | gpt-4 |
| `OPENAI_EMBEDDING_MODEL` | OpenAI embedding model | text-embedding-3-small |
| `MAX_FILE_SIZE` | Max upload size in bytes | 10485760 (10MB) |
| `ALLOWED_FILE_TYPES` | Comma-separated file types | pdf,docx,txt,md,rtf |
| `DEFAULT_CHUNK_SIZE` | Text chunk size | 1000 |
| `DEFAULT_CHUNK_OVERLAP` | Text chunk overlap | 200 |
| `DEBUG` | Debug mode | false |
| `LOG_LEVEL` | Logging level | INFO |

### Database Configuration

The application requires PostgreSQL 14+ with the pgvector extension:

```sql
-- Install pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- The application will create these tables:
-- - users (authentication and profiles)
-- - documents (file metainfo and status)
-- - document_chunks (text chunks with embeddings)
-- - conversations (chat sessions)
-- - messages (individual chat messages)
```

All tables use auto-incrementing BIGSERIAL primary keys for optimal performance and scalability.

### Search Algorithms

The platform supports multiple search algorithms:

1. **Vector Search**: Pure semantic similarity using embeddings
2. **Text Search**: Traditional keyword-based full-text search
3. **Hybrid Search**: Combines vector and text search with weighted scores
4. **MMR Search**: Maximum Marginal Relevance for diverse results

## 🚀 Deployment

### Production Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/ai_chatbot
export SECRET_KEY=your-secret-key
export OPENAI_API_KEY=your-openai-key

# Run database migrations
alembic upgrade head

# Start production server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Production Checklist

- [ ] Change default admin credentials
- [ ] Set strong `SECRET_KEY` (32+ characters)
- [ ] Configure proper `DATABASE_URL`
- [ ] Set `DEBUG=false`
- [ ] Configure CORS origins for your domain
- [ ] Set up HTTPS/TLS termination
- [ ] Configure rate limiting
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy
- [ ] Set resource limits (file size, request size)

## 🧪 Testing

The project includes comprehensive test coverage with unit and integration tests.

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html --cov-report=term-missing

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m auth          # Authentication tests

# Run specific test file
pytest tests/test_auth.py -v

# Check code quality (includes testing)
python scripts/check_quality.py

# Run tests with coverage in CI mode
python scripts/check_quality.py --coverage
```

### Test Structure
- **Unit Tests**: Fast tests that test individual components
- **Integration Tests**: Tests that verify API endpoints and database interactions  
- **Test Fixtures**: Comprehensive test data factories and database setup
- **Authentication Tests**: Complete auth flow testing
- **Health Check Tests**: System monitoring validation

## 🛠️ Development Tools

### Code Quality Tools
```bash
# Automated development setup
python scripts/dev_setup.py

# Code quality checks
python scripts/check_quality.py

# Fix formatting automatically
python scripts/check_quality.py --fix

# Pre-commit hooks (run automatically on commit)
pre-commit run --all-files
```

### Development Environment
```bash
# Manual development server
uvicorn app.main:app --reload

# Watch for changes and run tests
pytest --looponfail
```

## 📊 Monitoring

### Health Checks
- **Basic**: `GET /ping` - Simple health check
- **Detailed**: `GET /api/v1/health/detailed` - Full system status
- **Database**: `GET /api/v1/health/database` - Database connectivity
- **Services**: `GET /api/v1/health/services` - External service status

### Metrics and Logging
- Structured JSON logging with correlation IDs
- Request/response timing metrics
- Token usage tracking
- Error rate monitoring
- Performance profiling endpoints

## 🤝 Contributing

We welcome contributions! Please see [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development setup instructions.

### Quick Contribution Guide

1. **Fork and setup**:
   ```bash
   git clone <your-fork>
   cd ai-chatbot-mcp
   python scripts/dev_setup.py  # Automated setup
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **Make changes with quality checks**:
   ```bash
   # Make your changes
   python scripts/check_quality.py --fix  # Fix formatting
   python scripts/check_quality.py        # Run all checks
   ```

4. **Commit and push**:
   ```bash
   git commit -m 'Add amazing feature'
   git push origin feature/amazing-feature
   ```

5. **Open a Pull Request**

### Code Standards
- **Testing**: All new features must include tests
- **Documentation**: Update documentation for API changes
- **Code Quality**: All checks must pass (`python scripts/check_quality.py`)
- **Type Hints**: Use comprehensive type hints
- **Security**: Follow security best practices

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt
pip install black isort mypy pytest pytest-asyncio

# Format code
black app tests
isort app tests

# Type checking
mypy app

# Run tests
pytest
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check pgvector extension
psql -d ai_chatbot -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

**OpenAI API Issues**
```bash
# Test API key
curl -H "Authorization: Bearer YOUR_API_KEY" https://api.openai.com/v1/models
```

**File Upload Issues**
```bash
# Check upload directory permissions
ls -la uploads/
chmod 755 uploads/
```

**Memory Issues with Large Documents**
- Reduce `DEFAULT_CHUNK_SIZE`
- Increase system memory limits
- Use streaming for large file uploads

### Getting Help

- Check the [API Documentation](http://localhost:8000/docs)
- Review application logs in `logs/` directory
- Use health check endpoints for system status
- Check GitHub Issues for known problems

## 🔮 Future Enhancements

- [ ] Streaming chat responses
- [ ] Advanced document analytics
- [ ] Multi-language support
- [ ] Plugin marketplace for MCP tools
- [ ] Advanced user roles and permissions
- [ ] Conversation export/import
- [ ] Document collaboration features
- [ ] Advanced search filters and facets
- [ ] Real-time notifications
- [ ] Mobile API optimizations

---

**Generated on: 2025-07-14 03:52:46 UTC**  
Built with ❤️ using FastAPI, PostgreSQL, and OpenAI