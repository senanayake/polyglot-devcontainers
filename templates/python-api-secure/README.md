# python-api-secure

Production-ready FastAPI starter template with security best practices, database integration, and authentication patterns.

## What This Template Is For

Use this template when you need to build:
- REST APIs with FastAPI
- Microservices
- Backend services for web/mobile apps
- API-first applications

**Not for**: CLI tools (use `python-cli-secure`), data pipelines (use `python-data-secure`), or libraries (use `python-library-secure`)

## What's Included

### Core Stack
- **FastAPI 0.115+** - Modern, fast web framework
- **Uvicorn** - ASGI server with auto-reload
- **Pydantic v2** - Data validation and settings
- **SQLAlchemy 2.0** - Database ORM
- **Alembic** - Database migrations

### Security
- JWT authentication patterns
- Password hashing (bcrypt)
- CORS middleware configured
- Security headers
- Input validation via Pydantic

### Developer Experience
- **uv** for fast dependency management
- **Ruff** for linting and formatting
- **MyPy** for type checking
- **pytest** with coverage
- **pre-commit** hooks
- Hot reload for development

### Production Ready
- Health check endpoints (`/api/health`, `/api/ready`)
- Structured logging patterns
- Environment-based configuration
- Database migration system
- OpenAPI/Swagger docs at `/api/docs`

## Quick Start

### 1. Open in Devcontainer

```bash
# Using VS Code
code .

# Or using DevPod
devpod up .
```

### 2. Initialize

```bash
task init
```

This will:
- Install dependencies with `uv`
- Set up pre-commit hooks
- Create initial database

### 3. Run the API

```bash
task dev
```

API will be available at:
- http://localhost:8000 - Root
- http://localhost:8000/api/docs - Swagger UI
- http://localhost:8000/api/redoc - ReDoc

### 4. Verify Everything Works

```bash
task ci
```

This runs: lint → test → scan

## Project Structure

```
.
├── src/python_api_secure_template/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings management
│   ├── routers/             # API endpoints
│   │   ├── health.py        # Health checks
│   │   └── items.py         # Example CRUD
│   ├── models/              # SQLAlchemy models (add your own)
│   ├── schemas/             # Pydantic schemas (add your own)
│   └── services/            # Business logic (add your own)
├── tests/                   # Test suite
├── alembic/                 # Database migrations
├── pyproject.toml           # Dependencies and config
├── uv.lock                  # Locked dependencies
└── Taskfile.yml             # Task automation
```

## Common Tasks

### Development

```bash
task dev          # Start API with hot reload
task test         # Run tests
task test:watch   # Run tests in watch mode
task lint         # Check code quality
task format       # Auto-format code
```

### Database

```bash
task db:migrate   # Create new migration
task db:upgrade   # Apply migrations
task db:downgrade # Rollback migration
```

### Production

```bash
task ci           # Full CI pipeline
task scan         # Security scans
task build        # Build for deployment
```

## Configuration

### Environment Variables

Create `.env` file:

```env
PROJECT_NAME="My API"
DATABASE_URL="postgresql://user:pass@localhost/db"
SECRET_KEY="your-secret-key-here"
ALLOWED_ORIGINS=["http://localhost:3000"]
```

### Settings

Edit `src/python_api_secure_template/config.py`:

```python
class Settings(BaseSettings):
    PROJECT_NAME: str = "My API"
    DATABASE_URL: str = "sqlite:///./app.db"
    SECRET_KEY: str = "change-me"
    # Add your settings here
```

## Adding Features

### Add a New Endpoint

1. Create router in `src/python_api_secure_template/routers/`:

```python
# users.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_users():
    return {"users": []}
```

2. Register in `main.py`:

```python
from .routers import users

app.include_router(users.router, prefix="/api/users", tags=["users"])
```

### Add Database Model

1. Create model in `src/python_api_secure_template/models/`:

```python
from sqlalchemy import Column, Integer, String
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
```

2. Create migration:

```bash
task db:migrate -m "add users table"
task db:upgrade
```

### Add Authentication

See `docs/how-to/add-authentication.md` for JWT authentication patterns.

## Testing

### Write Tests

```python
# tests/test_items.py
from fastapi.testclient import TestClient
from python_api_secure_template.main import app

client = TestClient(app)

def test_create_item():
    response = client.post("/api/items/", json={
        "name": "Test",
        "price": 10.0
    })
    assert response.status_code == 201
```

### Run Tests

```bash
task test              # Run all tests
task test:cov          # With coverage report
pytest tests/test_items.py  # Specific file
pytest -k "test_create"     # Specific test
```

## Deployment

### Docker

```bash
task build
docker run -p 8000:8000 python-api-secure
```

### Environment Variables in Production

**Never commit secrets!** Use:
- Environment variables
- Secret management services (AWS Secrets Manager, etc.)
- `.env` files (gitignored)

## Security Checklist

- [ ] Change `SECRET_KEY` in production
- [ ] Use strong database passwords
- [ ] Enable HTTPS in production
- [ ] Configure CORS properly
- [ ] Review `ALLOWED_ORIGINS`
- [ ] Run `task scan` before deploying
- [ ] Keep dependencies updated

## Migration from Other Frameworks

### From Flask

- Replace `@app.route` with `@router.get/post/etc`
- Use Pydantic models instead of request.json
- Async/await for async operations
- See `docs/migration/flask-to-fastapi.md`

### From Django REST Framework

- Replace ViewSets with routers
- Use Pydantic instead of serializers
- SQLAlchemy instead of Django ORM
- See `docs/migration/drf-to-fastapi.md`

## Troubleshooting

### Port Already in Use

```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### Database Locked

```bash
# Reset database
rm app.db
task db:upgrade
```

### Import Errors

```bash
# Reinstall dependencies
uv sync --reinstall
```

## Next Steps

1. **Customize** - Update `config.py` with your settings
2. **Add Models** - Create your database models
3. **Add Endpoints** - Build your API routes
4. **Add Tests** - Write comprehensive tests
5. **Deploy** - Ship to production

## Learn More

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- `man polyglot-python-api` - Runtime guidance
- `docs/` - Additional guides and patterns
