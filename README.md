# FastAPI Authentication Backend

A production-ready authentication backend built with FastAPI, PostgreSQL, and SQLAlchemy. This backend mirrors the functionality of the Node.js backend while adding Python-specific features.

## 🚀 Features

### Core Authentication
- **User Registration** with email verification (OTP-based)
- **User Login** with JWT authentication
- **Password Reset** with OTP verification
- **Profile Management** (update name, email)
- **Password Change** for authenticated users
- **Google OAuth** integration (ready for implementation)
- **Session Management** with httpOnly cookies

### Security Features
- ✅ **JWT Authentication** with httpOnly cookies
- ✅ **Bcrypt Password Hashing** (12 rounds)
- ✅ **Rate Limiting** (100 requests per 15 minutes)
- ✅ **CORS Configuration** for frontend
- ✅ **Security Headers** (XSS, CSRF protection)
- ✅ **Input Validation** with Pydantic
- ✅ **OTP Security** (5-minute expiry)

### Python-Specific Features
1. **Execution Timer Decorator** - Logs function execution time
2. **Large File Reader Generator** - Reads files line by line efficiently
3. **Background Tasks** - Async email sending
4. **Pyright Type Checking** - Strict type safety
5. **Pre-commit Hooks** - Code quality enforcement

### CRUD Operations
- ✅ Get all users (with pagination, search, sorting)
- ✅ Bulk user deletion
- ✅ User profile updates
- ✅ User authentication status

## 📁 Project Structure

```
Backend_Python/
├── app/
│   ├── core/                    # Core configuration
│   │   ├── config.py           # Settings management
│   │   ├── database.py         # Database connection
│   │   └── logging.py          # Logging setup
│   ├── features/               # Feature-based modules
│   │   └── auth/               # Authentication feature
│   │       ├── routes.py       # API endpoints
│   │       ├── repository.py   # Database operations
│   │       └── dependencies.py # Dependency injection
│   ├── interfaces/             # Type definitions
│   │   └── auth.py            # Auth schemas
│   ├── middleware/             # Custom middleware
│   │   ├── security.py        # Security headers
│   │   ├── logging.py         # Request logging
│   │   ├── error_handler.py   # Error handling
│   │   └── rate_limit.py      # Rate limiting
│   ├── models/                 # Database models
│   │   └── user.py            # User model
│   ├── services/               # Business logic
│   │   ├── email_service.py   # Email sending
│   │   └── background_tasks.py # Async tasks
│   ├── utils/                  # Utility functions
│   │   ├── decorators.py      # Custom decorators
│   │   ├── file_reader.py     # File reading
│   │   ├── jwt.py             # JWT utilities
│   │   ├── otp.py             # OTP generation
│   │   └── password.py        # Password hashing
│   └── main.py                 # FastAPI app
├── migrations/                 # Database migrations
├── main.py                     # Entry point
├── requirements.txt            # Dependencies
├── pyproject.toml             # Project config
├── alembic.ini                # Migration config
└── .env.example               # Environment template
```

## 🛠️ Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- Virtual environment tool (venv, virtualenv, or conda)

### Setup Steps

1. **Clone and Navigate**
```bash
cd "e:/Auth module/Backend_Python"
```

2. **Create Virtual Environment**
```bash
python -m venv venv
```

3. **Activate Virtual Environment**
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. **Install Dependencies**
```bash
pip install -r requirements.txt
```

5. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

6. **Setup Pre-commit Hooks**
```bash
pre-commit install
```

7. **Run Database Migrations**
```bash
# The backend uses the existing PostgreSQL database from the Node.js backend
# No new migrations needed - it connects to the same database
```

## ⚙️ Configuration

### Environment Variables

Edit `.env` file with your settings:

```env
# Database (use same as Node.js backend)
DATABASE_URL=postgresql://username:password@localhost:5432/auth_db

# JWT (use same secret as Node.js backend for compatibility)
JWT_SECRET=your-super-secret-jwt-key

# Email (SMTP configuration)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Frontend
FRONTEND_URL=http://localhost:3000
```

## 🚀 Running the Application

### Development Mode
```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 5000
```

### Production Mode
```bash
uvicorn app.main:app --host 0.0.0.0 --port 5000 --workers 4
```

The server will start on `http://localhost:5000`

## 📚 API Endpoints

### Public Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/signup` | User registration |
| POST | `/api/auth/login` | User login |
| POST | `/api/auth/verify-signup-otp` | Verify signup OTP |
| POST | `/api/auth/resend-signup-otp` | Resend signup OTP |
| POST | `/api/auth/forgot-password` | Request password reset |
| POST | `/api/auth/verify-password-reset-otp` | Verify reset OTP |
| POST | `/api/auth/reset-password` | Reset password |
| GET | `/api/auth/health` | Health check |

### Protected Endpoints (Requires Authentication)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/logout` | User logout |
| GET | `/api/auth/me` | Get current user |
| POST | `/api/auth/refresh` | Refresh JWT token |
| PUT | `/api/auth/change-password` | Change password |
| PUT | `/api/auth/profile` | Update profile |
| GET | `/api/auth/users` | Get all users (paginated) |
| DELETE | `/api/auth/users/delete` | Bulk delete users |
| GET | `/api/auth/socket-token` | Get Socket.IO token |

## 🔧 Python-Specific Features

### 1. Execution Timer Decorator

```python
from app.utils.decorators import execution_timer

@execution_timer
async def my_function():
    # Function code
    pass
```

Automatically logs execution time for any function.

### 2. Large File Reader Generator

```python
from app.utils.file_reader import read_large_file_async

async for line in read_large_file_async("large_file.txt"):
    process(line)
```

Efficiently reads large files line by line without loading entire file into memory.

### 3. Background Tasks

```python
from fastapi import BackgroundTasks
from app.services.background_tasks import send_signup_otp_background

background_tasks.add_task(send_signup_otp_background, email, name, otp)
```

Async email sending without blocking the response.

### 4. Pyright Type Checking

```bash
pyright
```

Strict type checking for all Python code.

### 5. Pre-commit Hooks

Automatically runs on git commit:
- Black (code formatting)
- isort (import sorting)
- Flake8 (linting)
- Pyright (type checking)

## 🧪 Testing

```bash
pytest
```

With coverage:
```bash
pytest --cov=app --cov-report=html
```

## 📖 API Documentation

When running in development mode, access:
- **Swagger UI**: http://localhost:5000/docs
- **ReDoc**: http://localhost:5000/redoc

## 🔄 Database Compatibility

This backend uses the **same PostgreSQL database** as the Node.js backend:
- Same table structure (users table)
- Same data types and constraints
- Compatible JWT tokens (use same secret)
- No migration needed - connects to existing database

## 🎯 Frontend Integration

The backend is fully compatible with the existing Next.js frontend:
- Same API endpoints and response formats
- Same cookie-based authentication
- Same CORS configuration
- Same error response structure

## 🛡️ Security Best Practices

- ✅ httpOnly cookies for JWT tokens
- ✅ Bcrypt password hashing (12 rounds)
- ✅ Rate limiting on all endpoints
- ✅ CORS with specific origins
- ✅ Security headers (XSS, CSRF protection)
- ✅ Input validation with Pydantic
- ✅ OTP expiry (5 minutes)
- ✅ Secure cookie flags in production

## 📝 Code Quality

- **Type Safety**: Strict Pyright type checking
- **Code Formatting**: Black (88 char line length)
- **Import Sorting**: isort
- **Linting**: Flake8
- **Pre-commit Hooks**: Automated quality checks

## 🚀 Deployment

### Using Docker (Recommended)

```bash
# Build image
docker build -t auth-backend-python .

# Run container
docker run -p 5000:5000 --env-file .env auth-backend-python
```

### Using Systemd (Linux)

Create service file: `/etc/systemd/system/auth-backend.service`

```ini
[Unit]
Description=Auth Backend FastAPI
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/Backend_Python
Environment="PATH=/path/to/Backend_Python/venv/bin"
ExecStart=/path/to/Backend_Python/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 5000

[Install]
WantedBy=multi-user.target
```

## 📊 Performance

- **Async/Await**: Non-blocking I/O operations
- **Connection Pooling**: Efficient database connections
- **Background Tasks**: Non-blocking email sending
- **Generator Functions**: Memory-efficient file reading

## 🤝 Contributing

1. Follow the existing code structure
2. Use type hints everywhere
3. Run pre-commit hooks before committing
4. Write tests for new features
5. Update documentation

## 📄 License

MIT License

## 👥 Support

For issues or questions, please contact the development team.

---

**Built with ❤️ using FastAPI, PostgreSQL, and Python 3.11+**
