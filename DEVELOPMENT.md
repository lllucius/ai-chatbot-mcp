# AI Chatbot Platform - Development Setup Guide

This guide will help you set up the development environment for the AI Chatbot Platform.

## Prerequisites

- Python 3.11 or 3.12
- PostgreSQL 14+ with pgvector extension
- Git
- OpenAI API key

## Quick Start (Recommended)

### Automated Setup Script

```bash
# Clone the repository
git clone <repository-url>
cd ai-chatbot-mcp

# Run automated setup
python scripts/dev_setup.py
```

### Manual Setup

#### Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest-asyncio pytest-cov black isort mypy flake8 pre-commit
```

#### Database Setup

```bash
# Install PostgreSQL with pgvector (Ubuntu/Debian)
sudo apt-get install postgresql postgresql-contrib postgresql-14-pgvector

# Or using Homebrew (macOS)
brew install postgresql pgvector

# Start PostgreSQL
sudo systemctl start postgresql

# Create database
sudo -u postgres psql
CREATE DATABASE ai_chatbot_dev;
CREATE USER chatbot_user WITH PASSWORD 'dev_password';
GRANT ALL PRIVILEGES ON DATABASE ai_chatbot_dev TO chatbot_user;
\c ai_chatbot_dev;
CREATE EXTENSION vector;
\q
```

#### Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit with your settings
DATABASE_URL=postgresql+asyncpg://chatbot_user:dev_password@localhost:5432/ai_chatbot_dev
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key
DEBUG=true
LOG_LEVEL=DEBUG
```

#### Initialize Database

```bash
# Run database initialization
python scripts/startup.py

# Or manually initialize
python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"
```

#### Start Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Development Workflow

### Code Quality Tools

```bash
# Format code
black app tests
isort app tests

# Lint code
flake8 app tests

# Type checking
mypy app

# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v

# Run tests with coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html  # View coverage report
```

## Project Structure

```
ai-chatbot-mcp/
├── app/                    # Main application
│   ├── api/               # API endpoints
│   ├── core/              # Core functionality
│   ├── models/            # Database models
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   ├── utils/             # Utilities
│   ├── config.py          # Configuration
│   ├── database.py        # Database setup
│   └── main.py            # FastAPI application
├── tests/                 # Test files
├── scripts/               # Management scripts
├── .github/workflows/     # CI/CD workflows
├── requirements.txt       # Dependencies
├── pytest.ini           # Pytest configuration
└── .pre-commit-config.yaml # Pre-commit hooks
```

## API Documentation

When running in development mode, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Common Development Tasks

### Creating a New API Endpoint

1. Define schema in `app/schemas/`
2. Create service logic in `app/services/`
3. Implement API endpoint in `app/api/`
4. Add tests in `tests/`
5. Update documentation

### Adding a New Model

1. Create model in `app/models/`
2. Create corresponding schema in `app/schemas/`
3. Create database migration (if needed)
4. Add service methods in `app/services/`
5. Write tests

### Running Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Debugging

### Using debugger with VS Code

Add to `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "FastAPI Debug",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/venv/bin/uvicorn",
            "args": ["app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
            "console": "integratedTerminal",
            "envFile": "${workspaceFolder}/.env"
        }
    ]
}
```

### Logging

Logs are written to:
- Console (development)
- `logs/app.log` (production)

Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Health Checks

Monitor application health:
- Basic: http://localhost:8000/ping
- Detailed: http://localhost:8000/api/v1/health/detailed
- Readiness: http://localhost:8000/api/v1/health/readiness

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql
   
   # Check pgvector extension
   psql -d ai_chatbot_dev -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
   ```

2. **Import Errors**
   ```bash
   # Ensure you're in the virtual environment
   source venv/bin/activate
   
   # Check Python path
   echo $PYTHONPATH
   export PYTHONPATH=${PYTHONPATH}:$(pwd)
   ```

3. **Port Already in Use**
   ```bash
   # Find process using port 8000
   lsof -i :8000
   
   # Kill process
   kill -9 <PID>
   ```

4. **OpenAI API Issues**
   ```bash
   # Test API key
   curl -H "Authorization: Bearer YOUR_API_KEY" https://api.openai.com/v1/models
   ```

### Getting Help

- Check application logs: `tail -f logs/app.log`
- Review health endpoints for system status
- Check GitHub Issues for known problems
- Run `python scripts/manage_simple.py stats` for system statistics

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes following the coding standards
4. Run tests: `pytest`
5. Run code quality checks: `pre-commit run --all-files`
6. Commit changes: `git commit -m 'Add amazing feature'`
7. Push to branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

## Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | - | Yes |
| `SECRET_KEY` | JWT secret key | - | Yes |
| `OPENAI_API_KEY` | OpenAI API key | - | Yes |
| `DEBUG` | Enable debug mode | false | No |
| `LOG_LEVEL` | Logging level | INFO | No |
| `MAX_FILE_SIZE` | Max upload size | 10485760 | No |
| `ALLOWED_FILE_TYPES` | Allowed file types | pdf,docx,txt,md,rtf | No |

## Performance Tips

- Use connection pooling for database
- Enable caching for embeddings
- Monitor memory usage with large documents
- Use async/await patterns consistently
- Profile code with `cProfile` for bottlenecks

## Security Considerations

- Never commit API keys to version control
- Use strong SECRET_KEY in production
- Enable HTTPS in production
- Implement rate limiting
- Validate all input data
- Keep dependencies updated