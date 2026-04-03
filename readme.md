# FlowLink: Advanced URL Shortener & Analytics API

A high-performance URL shortener built incrementally. It scales from a simple redirect service to a fully-featured analytics platform with JWT authentication, custom API keys with sliding-window rate limiting, and real-time click streaming via WebSockets.

## 🚀 Features (Incremental Phases)

1. **Core Shortening**: Fast async generation and redirection using Base62 encoding.
2. **User Authentication**: Secure user registration, login, and JWT access tokens.
3. **Background Processing**: Click tracking (IP, User-Agent, Referer) handled asynchronously so redirects remain lightning-fast.
4. **Caching & Analytics**: Endpoint to view total clicks and history, cached in Redis with a 5-minute TTL to reduce DB load.
5. **API Keys & Rate Limiting**: Dual-auth system. Free JWT users get 10 req/min, API Key users get 100 req/min powered by a Redis sliding window algorithm inside a FastAPI Middleware.
6. **Scheduled Maintenance**: Background worker powered by `asyncio` that cleans up links expired over 30 days ago.
7. **Real-time WebSockets**: Live event streaming. Connect via WebSocket to watch clicks on your short link happen in real-time, powered by Redis Pub/Sub.

## 🛠️ Tech Stack

*   **Framework:** FastAPI (Python)
*   **Database:** PostgreSQL (with Async SQLAlchemy)
*   **Cache & Pub/Sub:** Redis (`redis.asyncio`)
*   **Security:** `pwdlib` (bcrypt), JWT, SHA-256 for API keys.

## ⚙️ Local Setup

1. **Clone the repo and install dependencies:**
   ```bash
   pip install -r requirements.txt

2. Set up Environment Variables: Create a .env file in the root directory:
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your_super_secret_jwt_key
ALGORITHM=HS256

3. Start your Databases: Make sure you have a local PostgreSQL server and a Redis instance running.

4. Run the server:
uvicorn app:app --reload

 Core API Endpoints
Auth & Users
POST / - Register a new user
POST /login - Get a JWT token
POST /api/api-keys - Generate a hashed API key for higher rate limits
Links
POST /api/url_shortner - Create a new short link (requires Auth)
GET /api/{short_code} - Redirect to long URL and log click
GET /api/stats/{short_code} - Get click analytics (Cached)
WS /api/links/{short_code}/live - WebSocket connection for real-time click notifications