# Autonomous Price Comparator - Setup Guide

## Phase 1 Foundation - Setup Complete! 🎉

This guide will help you set up and run the Autonomous Price Comparator application locally.

## Prerequisites

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Docker & Docker Compose** - [Download](https://www.docker.com/products/docker-desktop)
- **GROQ API Key** - [Get API Key](https://console.groq.com/)

---

## Quick Start

### 1. Start Infrastructure Services

```bash
# Start PostgreSQL, Redis, and RabbitMQ
docker-compose up -d postgres redis rabbitmq

# Verify services are running
docker-compose ps
```

Wait for all services to show "healthy" status (may take 30-60 seconds).

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# IMPORTANT: Edit .env and add your GROQ API key
# nano .env  # or use your preferred editor
# Set: GROQ_API_KEY=your-groq-api-key-here

# Run database migrations
alembic upgrade head

# Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at **http://localhost:8000**
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### 3. Frontend Setup

Open a **new terminal**:

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start the frontend dev server
npm run dev
```

Frontend will be available at **http://localhost:5173**

---

## Testing the Application

### 1. Register a New User

1. Open http://localhost:5173 in your browser
2. Click "Sign Up" button
3. Fill in the registration form:
   - Email: test@example.com
   - Password: password123 (minimum 8 characters)
   - Full Name: Test User (optional)
   - Age: 25 (optional)
4. Click "Sign up"

You'll be automatically logged in and redirected to the dashboard.

### 2. Test API Endpoints

Using the Swagger UI at http://localhost:8000/docs:

**Register User:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User",
    "age": 25
  }'
```

**Login:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

**Get Current User (requires token):**
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Troubleshooting

### Port Already in Use

If PostgreSQL port 5432 is already in use:
- The docker-compose.yml is configured to use port 5433 instead
- Backend .env file should have: `DATABASE_URL=postgresql+asyncpg://pricecomp:pricecomp123@localhost:5433/pricecomparator`

### Database Migration Errors

If you see migration errors:

```bash
cd backend

# Check current migration status
alembic current

# Upgrade to latest
alembic upgrade head

# If needed, create a new migration
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### Module Not Found Errors

Make sure you're in the correct directory and virtual environment:

```bash
# Backend
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### Docker Services Not Starting

```bash
# Stop all services
docker-compose down

# Remove volumes (warning: deletes data)
docker-compose down -v

# Start fresh
docker-compose up -d postgres redis rabbitmq
```

### CORS Errors

If you see CORS errors in the browser console:
1. Check that frontend is running on http://localhost:5173
2. Verify backend .env has: `CORS_ORIGINS=http://localhost:5173,http://localhost:3000`
3. Restart the backend server

---

## Database Access

### Using psql

```bash
# Connect to PostgreSQL
docker exec -it pricecomp_postgres psql -U pricecomp -d pricecomparator

# List tables
\dt

# Query users
SELECT * FROM users;

# Exit
\q
```

### Using a GUI Tool

- Host: localhost
- Port: 5433 (or 5432 if using system PostgreSQL)
- Database: pricecomparator
- Username: pricecomp
- Password: pricecomp123

---

## Development Workflow

### Backend Development

```bash
cd backend
source venv/bin/activate

# Run with auto-reload
uvicorn app.main:app --reload

# Run tests (when available)
pytest

# Create new migration
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Frontend Development

```bash
cd frontend

# Dev server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

---

## Next Steps

Phase 1 is complete! Here's what's next:

### Phase 2: Web Scraping (Weeks 3-4)
- [ ] Implement base scraper with retry logic
- [ ] Build platform-specific scrapers (Flipkart, Amazon, Myntra, Meesho)
- [ ] Add proxy manager and user agent rotation
- [ ] Create Celery tasks for scheduled scraping

### Phase 3: Core Product API (Weeks 5-6)
- [ ] Product search API with filters
- [ ] Product detail endpoints
- [ ] Price history tracking
- [ ] Price alert management

### Phase 4: AI Agents (Weeks 7-9)
- [ ] LangGraph + GROQ integration
- [ ] Recommendation agent
- [ ] Price tracking agent
- [ ] Notification agent

---

## Environment Variables

### Backend (.env)

```bash
# Database (Docker port 5433 to avoid conflict)
DATABASE_URL=postgresql+asyncpg://pricecomp:pricecomp123@localhost:5433/pricecomparator
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL=3600

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# JWT Authentication
SECRET_KEY=your-secret-key-change-this-in-production-minimum-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# GROQ API (REQUIRED - Get from https://console.groq.com/)
GROQ_API_KEY=your-groq-api-key-here
GROQ_MODEL=llama-3.1-70b-versatile

# Email (Optional - for Phase 5)
SENDGRID_API_KEY=
FROM_EMAIL=noreply@pricecomparator.com

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Environment
ENVIRONMENT=development
```

### Frontend (.env)

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/api/v1/ws
VITE_ENVIRONMENT=development
```

---

## Useful Commands

### Docker

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f postgres
docker-compose logs -f redis
docker-compose logs -f rabbitmq

# Restart a service
docker-compose restart postgres

# Check service health
docker-compose ps
```

### Database

```bash
# Create backup
docker exec pricecomp_postgres pg_dump -U pricecomp pricecomparator > backup.sql

# Restore backup
docker exec -i pricecomp_postgres psql -U pricecomp pricecomparator < backup.sql

# Reset database (warning: deletes all data)
docker-compose down -v
docker-compose up -d postgres
cd backend && alembic upgrade head
```

---

## Support

For issues or questions:
1. Check this SETUP.md guide
2. Review the README.md
3. Check the API documentation at http://localhost:8000/docs
4. Create an issue in the repository

---

**Status**: ✅ Phase 1 Complete - Ready for Phase 2!

**Last Updated**: 2026-03-29
