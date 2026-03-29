# Autonomous Price Comparator

AI-powered price comparison platform that autonomously tracks product prices across multiple e-commerce platforms and provides personalized recommendations.

## Features

- 🔍 **Multi-Platform Price Comparison**: Compare prices across Flipkart, Amazon, Myntra, Meesho
- 🤖 **AI-Powered Recommendations**: Personalized product suggestions using LangGraph + GROQ
- 🔔 **Smart Notifications**: Get notified when prices drop or relevant products are available
- 📊 **Price History Tracking**: Monitor price trends over time
- ⚡ **Real-Time Updates**: WebSocket-based live notifications
- 🕷️ **Automated Web Scraping**: Scheduled scraping with anti-bot measures

## Technology Stack

### Backend
- **FastAPI** - Modern async Python web framework
- **LangGraph** - AI agent workflow orchestration
- **GROQ API** - Fast LLM inference
- **PostgreSQL** - Main database
- **Redis** - Caching and session storage
- **Celery + RabbitMQ** - Background task processing
- **SQLAlchemy 2.0** - Async ORM
- **Playwright/BeautifulSoup** - Web scraping

### Frontend
- **React 18 + Vite** - Fast UI development
- **Tailwind CSS** - Utility-first styling
- **Zustand** - State management
- **React Query** - Server state caching
- **Recharts** - Price visualization

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose

### 1. Clone the repository
```bash
git clone <repository-url>
cd Autonomous_Price_comparator
```

### 2. Start infrastructure services
```bash
docker-compose up -d postgres redis rabbitmq
```

Wait for services to be healthy:
```bash
docker-compose ps
```

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env and add your GROQ API key
# GROQ_API_KEY=your-groq-api-key-here

# Run database migrations (will be added in Phase 1)
# alembic upgrade head

# Start the backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at http://localhost:8000

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start the frontend
npm run dev
```

Frontend will be available at http://localhost:5173

## Project Structure

```
autonomous-price-comparator/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/     # API routes
│   │   ├── models/               # Database models
│   │   ├── schemas/              # Pydantic schemas
│   │   ├── services/             # Business logic
│   │   ├── agents/               # LangGraph AI agents
│   │   ├── scrapers/             # Web scrapers
│   │   ├── tasks/                # Celery tasks
│   │   └── main.py               # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/                # Page components
│   │   ├── components/           # Reusable components
│   │   ├── services/             # API services
│   │   ├── hooks/                # Custom hooks
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
└── docker-compose.yml
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

### Running Tests

Backend:
```bash
cd backend
pytest
```

Frontend:
```bash
cd frontend
npm test
```

### Database Migrations

Create a new migration:
```bash
cd backend
alembic revision --autogenerate -m "Description"
```

Apply migrations:
```bash
alembic upgrade head
```

### Celery Workers

Start a Celery worker for background tasks:
```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=info
```

Start Celery Beat (scheduler):
```bash
celery -A app.tasks.celery_app beat --loglevel=info
```

## Environment Variables

### Backend (.env)
```bash
DATABASE_URL=postgresql+asyncpg://pricecomp:pricecomp123@localhost:5432/pricecomparator
REDIS_URL=redis://localhost:6379/0
GROQ_API_KEY=your-groq-api-key
SECRET_KEY=your-secret-key-256-bit
```

### Frontend (.env)
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/api/v1/ws
```

## Implementation Roadmap

- [x] **Phase 1**: Foundation (Project setup, Docker, Auth) - *Current*
- [ ] **Phase 2**: Web Scraping (Platform-specific scrapers)
- [ ] **Phase 3**: Core Product API (Search, price tracking)
- [ ] **Phase 4**: LangGraph AI Agents (Recommendations, notifications)
- [ ] **Phase 5**: Real-Time Notifications (WebSocket, email)
- [ ] **Phase 6**: User Dashboard & Personalization
- [ ] **Phase 7**: Optimization & Caching
- [ ] **Phase 8**: Testing & Quality Assurance
- [ ] **Phase 9**: Production Deployment

## Contributing

This is a personal project currently in development. Contributions, issues, and feature requests are welcome!

## License

MIT License

## Support

For issues or questions, please create an issue in the repository.

---

**Status**: 🚧 In Development - Phase 1 (Foundation)

**Last Updated**: 2026-03-29
