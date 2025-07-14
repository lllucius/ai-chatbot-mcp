# AI Chatbot Platform

**Generated on: 2025-07-14 03:52:46 UTC**  
**Current User: lllucius**

A production-grade AI chatbot platform with RAG (Retrieval-Augmented Generation) capabilities, document processing, vector search, and MCP (Model Context Protocol) tool integration.

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

### 🛠️ Tool Integration (MCP)
- **MCP Protocol**: Model Context Protocol client
- **External Tools**: File system, web search, and custom tools
- **Function Calling**: AI can execute external functions
- **Extensible Architecture**: Easy plugin development

### 📊 Monitoring & Analytics
- **Health Checks**: Comprehensive system monitoring
- **Performance Metrics**: Response times and usage statistics
- **Error Tracking**: Structured logging and error handling
- **Admin Dashboard**: System statistics and user management

## 🏗️ Architecture

### Technology Stack
- **Backend**: FastAPI with async/await
- **Database**: PostgreSQL 14+ with pgvector
- **AI/ML**: OpenAI API, sentence-transformers
- **Authentication**: JWT with python-jose
- **Document Processing**: PyPDF2, python-docx, striprtf
- **Vector Search**: pgvector with multiple algorithms

### Project Structure
```
ai-chatbot-platform/
├── app/                          # Main application
│   ├── api/                     # REST API endpoints
│   ├── core/                    # Core functionality
│   ├── models/                  # Database models
│   ├── schemas/                 # Pydantic schemas
│   ├── services/                # Business logic
│   └── utils/                   # Utilities
├── scripts/                     # Management scripts
├── migrations/                  # Database migrations
└── requirements.txt             # Dependencies
```

## 🚦 Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 14+ with pgvector extension
- OpenAI API key

### Installation

1. **Clone and setup environment:**
```bash
git clone <repository-url>
cd ai-chatbot-platform
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your settings:
# - DATABASE_URL
# - SECRET_KEY 
# - OPENAI_API_KEY
```

3. **Setup PostgreSQL with pgvector:**
```sql
-- Connect to PostgreSQL as superuser
CREATE DATABASE ai_chatbot;
\c ai_chatbot;
CREATE EXTENSION vector;
```

4. **Initialize database and create admin user:**
```bash
python scripts/startup.py
```

5. **Start the application:**
```bash
uvicorn app.main:app --reload
```

6. **Access the application:**
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health

### Default Admin Credentials
- **Username**: admin
- **Email**: admin@example.com
- **Password**: Admin123!

⚠️ **IMPORTANT**: Change these credentials immediately in production!

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

## 🔧 Management Commands

### User Management
```bash
# Create a regular user
python scripts/manage_simple.py create-user username email@example.com password

# Create a superuser
python scripts/manage_simple.py create-superuser admin admin@example.com password

# List all users
python scripts/manage_simple.py list-users

# Reset user password
python scripts/manage_simple.py reset-password username newpassword

# Deactivate a user
python scripts/manage_simple.py deactivate-user username
```

### System Operations
```bash
# Show system statistics
python scripts/manage_simple.py stats

# Initialize database
python scripts/manage_simple.py init-db

# Run API usage examples
python scripts/example_usage.py workflow
python scripts/example_usage.py register
```

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

### Search Algorithms

The platform supports multiple search algorithms:

1. **Vector Search**: Pure semantic similarity using embeddings
2. **Text Search**: Traditional keyword-based full-text search
3. **Hybrid Search**: Combines vector and text search with weighted scores
4. **MMR Search**: Maximum Marginal Relevance for diverse results

## 🚀 Deployment

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/ai_chatbot
      - SECRET_KEY=your-secret-key
      - OPENAI_API_KEY=your-openai-key
    depends_on:
      - db

  db:
    image: pgvector/pgvector:pg14
    environment:
      - POSTGRES_DB=ai_chatbot
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
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

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run with debug output
pytest -v -s
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

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

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