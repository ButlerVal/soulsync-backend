# 💖 SoulSync Backend

---
title: SoulSync Backend API
emoji: 💖🧠
colorFrom: yellow
colorTo: pink
sdk: docker
app_port: 7860
secrets:
  - DATABASE_URL
  - SECRET_KEY
  - REDIS_HOST
  - REDIS_PORT
env:
  ENVIRONMENT: production
  DEBUG: false
  API_V1_STR: /api/v1
  PYTHON_VERSION: 3.12
---

<div align="center">

**Connect Through Emotions, Not Just Words**

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg?style=flat-square)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-00C7B7.svg?style=flat-square)](https://fastapi.tiangolo.com)
[![Built by The Hive](https://img.shields.io/badge/Built%20by-The%20Hive-yellow.svg?style=flat-square)](https://github.com/ButlerVal)

[Quick Start](#-quick-start) •
[API Endpoints](#-api-endpoints-reference) •
[Authentication](#-authentication-flow) •
[ML Model](#-ml-model--hugging-face-integration) •
[Deployment](#-deployment)

</div>

---

## 🌟 What is SoulSync?

SoulSync is an emotion-based matching platform that connects people through **emotional compatibility**. Using NLP and machine learning, we analyze emotional expressions to find meaningful connections for friendships, dating, co-founding, and support.

---

## ✨ Features

### 🔐 Authentication & Security
- Email/Password registration & login
- JWT tokens (access & refresh)
- Password reset flow
- Bcrypt password hashing
- Block & report users

### 👤 User Profiles
- Customizable profiles (bio, name, DOB)
- Privacy controls
- Profile management API

### 🧠 Emotion AI
- DistilBERT fine-tuned on GoEmotions dataset (hosted on Hugging Face Hub: `Valisces/soulsync-emotion-model`)
- 8-dimensional emotion vectors: Joy, Sadness, Anxiety, Calm, Anger, Excitement, Empathy, Confidence
- Text analysis API
- Automatic model download from Hugging Face Hub on startup

### 💝 Smart Matching
- Cosine similarity algorithm with context-aware weighting
- Daily match generation
- Connect/Pass functionality
- Match history tracking

### 💬 Real-Time Messaging
- WebSocket connections
- Persistent chat history
- Conversation management
- Real-time message delivery

### 🛡️ Safety & Moderation
- User blocking system
- Report functionality
- Block list management

---

## 🛠️ Tech Stack

| Category | Technologies |
|----------|-------------|
| **Backend** | FastAPI, Python 3.12 |
| **Database** | PostgreSQL, SQLAlchemy (async) |
| **ML/AI** | 🤗 Transformers, PyTorch, DistilBERT |
| **Model Hosting** | Hugging Face Hub |
| **Real-time** | WebSockets |
| **Auth** | JWT, Bcrypt |
| **Deployment** | Docker, Gunicorn, Uvicorn, Hugging Face Spaces, Render |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12
- PostgreSQL 13+
- Git

### Installation

**1. Clone the Repository**

```bash
git clone https://github.com/ButlerVal/soulsync-backend.git
cd soulsync_backend
```

**2. Set Up Virtual Environment**

```bash
# Windows
py -3.12 -m venv venv
venv\Scripts\activate

# macOS/Linux
python3.12 -m venv venv
source venv/bin/activate
```

**3. Install Dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure PostgreSQL**

```bash
# Connect to PostgreSQL
psql -U your_username

# Create database
CREATE DATABASE soulsync_db;
```

**5. Set Up Environment Variables**

```bash
# Copy example environment file
cp .env.example .env

# Generate a secret key
python -c "import secrets; print(secrets.token_hex(32))"
```

Edit `.env` with your configuration:

```env
APP_NAME=SoulSync
ENVIRONMENT=development
DEBUG=True
API_V1_STR=/api/v1
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/soulsync_db
SECRET_KEY=your_generated_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

**6. Run Database Migrations**

```bash
alembic upgrade head
```

**7. Start the Development Server**

```bash
uvicorn app.main:app --reload
```

🎉 **Success!** Your API is now running at `http://127.0.0.1:8000`

> **Note on First Run:** The server will download the ML model (`Valisces/soulsync-emotion-model`) from Hugging Face Hub the first time it starts. This might take a few minutes depending on your internet connection. Subsequent startups will use the cached model.

**8. Access Interactive API Docs**

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

---

## 📡 API Endpoints Reference

Base URL: `http://127.0.0.1:8000/api/v1`

### 🔐 Authentication Endpoints

#### Register New User
```http
POST /auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "name": "John Doe",
  "date_of_birth": "1995-06-15"
}
```

**Response (201):**
```json
{
  "id": "uuid-string",
  "email": "user@example.com",
  "name": "John Doe",
  "date_of_birth": "1995-06-15",
  "created_at": "2025-10-29T10:30:00Z"
}
```

**Frontend Notes:**
- Password must be at least 8 characters
- Email must be unique
- Date format: `YYYY-MM-DD`

---

#### Login
```http
POST /auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Frontend Notes:**
- Store both tokens securely (localStorage/sessionStorage)
- Access token expires in 15 minutes
- Refresh token expires in 7 days
- Use access token in Authorization header: `Bearer {access_token}`

---

#### Refresh Access Token
```http
POST /auth/refresh
```

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Frontend Notes:**
- Call this endpoint when access token expires
- Returns a new access token
- Keep the same refresh token

---

#### Forgot Password
```http
POST /auth/forgot-password
```

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response (200):**
```json
{
  "message": "Password reset email sent"
}
```

**Frontend Notes:**
- Currently returns mock response
- In production, will send actual email with reset token

---

#### Reset Password
```http
POST /auth/reset-password
```

**Request Body:**
```json
{
  "token": "reset-token-from-email",
  "new_password": "NewSecurePass123!"
}
```

**Response (200):**
```json
{
  "message": "Password reset successful"
}
```

---

### 👤 User Profile Endpoints

#### Get Current User Profile
```http
GET /users/me
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "id": "uuid-string",
  "email": "user@example.com",
  "name": "John Doe",
  "bio": "Software developer passionate about AI",
  "date_of_birth": "1995-06-15",
  "created_at": "2025-10-29T10:30:00Z",
  "updated_at": "2025-10-29T10:30:00Z"
}
```

**Frontend Notes:**
- Requires authentication
- Use to display user's own profile

---

#### Update Current User Profile
```http
PUT /users/me
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "name": "John Smith",
  "bio": "Tech enthusiast and coffee lover",
  "date_of_birth": "1995-06-15"
}
```

**Response (200):**
```json
{
  "id": "uuid-string",
  "email": "user@example.com",
  "name": "John Smith",
  "bio": "Tech enthusiast and coffee lover",
  "date_of_birth": "1995-06-15",
  "updated_at": "2025-10-29T11:45:00Z"
}
```

**Frontend Notes:**
- All fields are optional
- Only send fields that need updating

---

### 🧠 Emotion Profile Endpoints

#### Analyze Emotional Profile
```http
POST /profiles/analyze
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "text_samples": [
    "I'm really excited about this new opportunity! It's going to be amazing.",
    "Sometimes I feel overwhelmed by all the responsibilities.",
    "I love helping others and being there for my friends."
  ]
}
```

**Response (200):**
```json
{
  "user_id": "uuid-string",
  "emotion_vector": {
    "joy": 0.72,
    "sadness": 0.15,
    "anxiety": 0.28,
    "calm": 0.45,
    "anger": 0.05,
    "excitement": 0.81,
    "empathy": 0.68,
    "confidence": 0.62
  },
  "analyzed_at": "2025-10-29T12:00:00Z"
}
```

**Frontend Notes:**
- Requires 2-5 text samples (each 50-500 characters)
- Use diverse samples (journal entries, social media posts, etc.)
- Emotion values range from 0.0 to 1.0
- This profile is used for matching
- Can be re-analyzed to update profile

---

#### Get User's Emotion Profile
```http
GET /profiles/me
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "user_id": "uuid-string",
  "emotion_vector": {
    "joy": 0.72,
    "sadness": 0.15,
    "anxiety": 0.28,
    "calm": 0.45,
    "anger": 0.05,
    "excitement": 0.81,
    "empathy": 0.68,
    "confidence": 0.62
  },
  "analyzed_at": "2025-10-29T12:00:00Z"
}
```

**Frontend Notes:**
- Returns null if user hasn't analyzed their emotions yet
- Prompt user to analyze if profile doesn't exist

---

### 💝 Matching Endpoints

#### Get Daily Matches
```http
GET /matches/daily?use_case=dating
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `use_case` (optional): `friends`, `dating`, `cofounder`, `support` (default: `dating`)

**Response (200):**
```json
{
  "matches": [
    {
      "id": "match-uuid-1",
      "user": {
        "id": "user-uuid",
        "name": "Jane Smith",
        "bio": "Adventure seeker and book lover",
        "age": 28
      },
      "compatibility_score": 0.87,
      "emotional_compatibility": {
        "joy": 0.89,
        "empathy": 0.91,
        "calm": 0.78
      },
      "conversation_starters": [
        "What's your favorite adventure you've been on?",
        "What book changed your perspective on life?"
      ],
      "matched_at": "2025-10-29T08:00:00Z"
    }
  ],
  "total": 5,
  "generated_at": "2025-10-29T08:00:00Z"
}
```

**Frontend Notes:**
- New matches generated daily at 8:00 AM
- Compatibility score ranges from 0.0 to 1.0 (higher is better)
- Use conversation starters as ice-breakers
- User must have emotion profile to get matches

---

#### Connect with Match
```http
POST /matches/{match_id}/connect
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "status": "connected",
  "conversation_id": "conversation-uuid",
  "message": "You're now connected! Start chatting."
}
```

**Response if not mutual (200):**
```json
{
  "status": "pending",
  "message": "Connection request sent. Waiting for response."
}
```

**Frontend Notes:**
- Use `conversation_id` to navigate to chat
- If one-sided, status is "pending"
- When both users connect, conversation is automatically created

---

#### Pass on Match
```http
POST /matches/{match_id}/pass
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "status": "passed",
  "message": "Match passed"
}
```

**Frontend Notes:**
- Removes match from daily matches
- User won't see this match again
- Action is permanent

---

### 💬 Messaging Endpoints

#### Get Conversations List
```http
GET /conversations
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "conversations": [
    {
      "id": "conversation-uuid-1",
      "participant": {
        "id": "user-uuid",
        "name": "Jane Smith"
      },
      "last_message": {
        "content": "That sounds great!",
        "sent_at": "2025-10-29T14:30:00Z",
        "is_read": true
      },
      "unread_count": 0,
      "updated_at": "2025-10-29T14:30:00Z"
    }
  ],
  "total": 3
}
```

**Frontend Notes:**
- Sorted by most recent activity
- Use `unread_count` for notification badges
- Display last message as preview

---

#### Get Conversation Messages
```http
GET /conversations/{conversation_id}/messages?limit=50&offset=0
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `limit` (optional): Number of messages to return (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response (200):**
```json
{
  "messages": [
    {
      "id": "message-uuid-1",
      "conversation_id": "conversation-uuid",
      "sender_id": "user-uuid",
      "content": "Hey! How are you doing?",
      "sent_at": "2025-10-29T14:25:00Z",
      "is_read": true
    },
    {
      "id": "message-uuid-2",
      "conversation_id": "conversation-uuid",
      "sender_id": "current-user-uuid",
      "content": "I'm good, thanks! How about you?",
      "sent_at": "2025-10-29T14:26:00Z",
      "is_read": true
    }
  ],
  "total": 24,
  "limit": 50,
  "offset": 0
}
```

**Frontend Notes:**
- Messages ordered by `sent_at` (oldest first)
- Use pagination for loading older messages
- Compare `sender_id` with current user ID to align messages

---

#### WebSocket Connection (Real-time Messaging)
```
WS /ws?token={access_token}
```

**Connection:**
```javascript
const ws = new WebSocket('ws://127.0.0.1:8000/ws?token=' + accessToken);
```

**Send Message:**
```json
{
  "type": "message",
  "conversation_id": "conversation-uuid",
  "content": "Hello there!"
}
```

**Receive Message:**
```json
{
  "type": "message",
  "message": {
    "id": "message-uuid",
    "conversation_id": "conversation-uuid",
    "sender_id": "user-uuid",
    "content": "Hello there!",
    "sent_at": "2025-10-29T14:30:00Z"
  }
}
```

**Frontend Notes:**
- Pass access token in query parameter
- Connection stays open for real-time updates
- Listen for incoming messages
- Handle reconnection on disconnect
- Send heartbeat/ping to keep connection alive

---

### 🛡️ Safety & Moderation Endpoints

#### Block User
```http
POST /safety/users/{user_id}/block
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "status": "blocked",
  "message": "User blocked successfully"
}
```

**Frontend Notes:**
- Blocked user can't message you
- Removes all matches with this user
- Removes from match suggestions

---

#### Unblock User
```http
DELETE /safety/users/{user_id}/unblock
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "status": "unblocked",
  "message": "User unblocked successfully"
}
```

---

#### Get Blocked Users List
```http
GET /safety/blocked-list
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "blocked_users": [
    {
      "id": "user-uuid",
      "name": "John Doe",
      "blocked_at": "2025-10-28T10:00:00Z"
    }
  ],
  "total": 1
}
```

---

#### Report User
```http
POST /safety/reports
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "reported_user_id": "user-uuid",
  "reason": "harassment",
  "description": "User sent inappropriate messages"
}
```

**Reason Options:**
- `harassment`
- `spam`
- `inappropriate_content`
- `fake_profile`
- `other`

**Response (201):**
```json
{
  "id": "report-uuid",
  "status": "submitted",
  "message": "Report submitted successfully"
}
```

**Frontend Notes:**
- Include clear report form in UI
- Allow users to provide context
- Confirm submission to user

---

## 🔒 Authentication Flow

### For Frontend Implementation

**1. User Registration:**
```javascript
POST /api/v1/auth/register 
→ Store tokens 
→ Redirect to profile setup
```

**2. User Login:**
```javascript
POST /api/v1/auth/login 
→ Store tokens 
→ Fetch user profile 
→ Redirect to dashboard
```

**3. Protected Requests:**
```javascript
// Add to all authenticated requests
headers: {
  'Authorization': `Bearer ${accessToken}`,
  'Content-Type': 'application/json'
}
```

**4. Token Refresh (when 401 received):**
```javascript
// Pseudo-code
if (response.status === 401) {
  const newToken = await refreshAccessToken(refreshToken);
  // Retry original request with new token
}
```

**5. Logout:**
```javascript
// Clear tokens from storage
localStorage.removeItem('access_token');
localStorage.removeItem('refresh_token');
// Redirect to login
```

**6. WebSocket Connection:**
```javascript
// Connect to WebSocket
const ws = new WebSocket(`wss://your-api-url/ws?token=${accessToken}`);

// Listen for messages
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'message') {
    // Handle incoming message
  }
};

// Send message
ws.send(JSON.stringify({
  type: 'message',
  conversation_id: 'conversation-uuid',
  content: 'Hello!'
}));
```

---

## 🧠 ML Model & Hugging Face Integration

### Model Information

**Model ID:** `Valisces/soulsync-emotion-model` on [Hugging Face Hub](https://huggingface.co/Valisces/soulsync-emotion-model)

**Architecture:** Fine-tuned DistilBERT for emotion classification

**Training Dataset:** GoEmotions (Google's emotion dataset)

**Output:** 8-dimensional emotion vectors

### How It Works

1. **Automatic Download:** The backend automatically downloads and caches the model from Hugging Face Hub on first startup
2. **Caching:** Subsequent server restarts use the cached model (stored in `~/.cache/huggingface/`)
3. **Inference:** The model analyzes text samples to generate emotion profiles
4. **No Manual Setup Required:** Just run the server and the model will be downloaded automatically

### Frontend Notes

- First API startup may take 2-5 minutes to download the model (~250MB)
- Show a loading state during user's first emotion analysis
- Model responses are typically fast (<1 second) after initial load
- The model is shared across all users (no per-user download)

### For Developers

The model is loaded in `app/ml/emotion_classifier.py`:

```python
from transformers import pipeline

classifier = pipeline(
    "text-classification",
    model="Valisces/soulsync-emotion-model",
    return_all_scores=True
)
```

No training code is included in this repository - this is inference only. The model was previously trained using Modal GPU infrastructure.

---

## 📁 Project Structure

```
soulsync_backend/
│
├── 📂 alembic/              # Database migrations
├── 📂 app/                  # Main application
│   ├── 📂 api/              # API routes
│   │   ├── deps.py          # Auth dependencies
│   │   └── 📂 endpoints/    # Feature routers
│   ├── 📂 core/             # Core configuration
│   ├── 📂 db/               # Database setup
│   ├── 📂 ml/               # Machine learning inference
│   │   └── emotion_classifier.py  # Loads model from Hugging Face Hub
│   ├── 📂 models/           # Database models
│   ├── 📂 schemas/          # Pydantic schemas
│   ├── 📂 services/         # Business logic
│   └── main.py              # App entry point
│
├── 📂 tests/                # Test suite
├── .env.example             # Environment template
├── .gitignore               # Git ignore file
├── alembic.ini              # Alembic configuration
├── Dockerfile               # Docker deployment for Hugging Face Spaces
├── requirements.txt         # Dependencies
└── README.md                # This file
```

---

## ☁️ Deployment

### Option 1: Deploy to Hugging Face Spaces

**1. Create a New Space**

- Go to [huggingface.co](https://huggingface.co) and click "New" → "Space"
- Give it a name (e.g., `soulsync-api`)
- Select **"Docker"** as the Space SDK
- Choose "Public" (or "Private" if available)
- Click "Create Space"

**2. Link Your GitHub Repository**

- In your new Space, go to the "Settings" tab
- Find the "Sync from GitHub" section
- Connect your `ButlerVal/soulsync-backend` repository
- Select the `main` branch

**3. Configure Secrets (Critical)**

In your Space's "Settings" tab, scroll to "Space secrets" and add:

**Required Secrets:**

| Secret Name | Description | Example |
|------------|-------------|---------|
| `DATABASE_URL` | **CRITICAL:** PostgreSQL connection string from external provider (Render, Railway, etc.) | `postgresql+asyncpg://user:pass@host:5432/db` |
| `SECRET_KEY` | Strong secret key for JWT signing | Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |

**Optional Secrets (if using Redis):**

| Secret Name | Value |
|------------|-------|
| `REDIS_HOST` | Redis host address |
| `REDIS_PORT` | `6379` |

> **Important:** Hugging Face Spaces does NOT provide a database. You MUST create a PostgreSQL database on an external service (Render, Railway, Supabase, etc.) and use its **external/public connection string**.

**4. Configure Environment Variables**

The environment variables are already defined in the README.md frontmatter:

```yaml
env:
  ENVIRONMENT: production
  DEBUG: false
  API_V1_STR: /api/v1
  PYTHON_VERSION: 3.12
```

These will be automatically loaded by Hugging Face Spaces.

**5. Run Database Migrations**

> **CRITICAL:** Hugging Face Spaces does NOT automatically run migrations. You must run them manually against your remote database.

From your local terminal (with virtual environment activated):

```bash
# Windows
set DATABASE_URL=postgresql+asyncpg://<your-external-db-connection-string>
alembic upgrade head

# macOS/Linux
export DATABASE_URL=postgresql+asyncpg://<your-external-db-connection-string>
alembic upgrade head
```

**6. Deploy!** 🚀

- Push to your GitHub `main` branch
- Hugging Face Spaces will automatically:
  - Detect the `Dockerfile`
  - Build the Docker image
  - Download the ML model from Hugging Face Hub
  - Start the FastAPI server on port 7860

Your API will be available at: `https://huggingface.co/spaces/YOUR_USERNAME/soulsync-api`

> **First Deployment Note:** Initial deployment takes 5-10 minutes due to Docker build and model download.

---

### Option 2: Deploy to Render

**1. Create PostgreSQL Database**
- Dashboard → New → PostgreSQL
- Copy **Internal Connection String**

**2. Create Web Service**
- Connect GitHub repository
- Environment: Python 3
- Build Command: `pip install -r requirements.txt && alembic upgrade head`

**3. Environment Variables**

```
PYTHON_VERSION=3.12
DATABASE_URL=<postgres_url>
SECRET_KEY=<generate_strong_key>
ENVIRONMENT=production
DEBUG=False
```

---

## 🗺️ Roadmap

### Coming Soon
- 📧 Real email verification on registration (SendGrid/AWS SES)
- 📸 Profile photo upload (S3/R2)
- 🗑️ Delete account endpoint
- 🔍 Advanced matching filters & pagination
- 💬 AI-generated conversation starters (LLM integration)
- 🔔 Push notifications for new matches & messages
- 🖼️ Rich message types (images, voice, GIFs)
- ✅ Comprehensive unit & integration tests
- 📊 Production logging (centralized logging service)
- 👨‍💼 Admin panel features
- 💳 Subscription/premium features

---

## 👥 Team

### 🐝 The Hive

Built with 💖 by passionate developers

[![GitHub](https://img.shields.io/badge/GitHub-ButlerVal-181717?style=for-the-badge&logo=github)](https://github.com/ButlerVal)

---

## 🆘 Support

- 📖 [API Documentation](http://localhost:8000/docs)
- 🐛 [Report Issues](https://github.com/ButlerVal/soulsync_backend/issues)

---

<div align="center">

**Made with ❤️ by The Hive 🐝**

*Connecting hearts through technology*

</div>