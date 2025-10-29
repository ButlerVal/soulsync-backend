from fastapi import FastAPI, Depends
from app.core.config import settings
from app.api.endpoints import auth, profiles, matches, websocket, conversations, users, safety
from fastapi.middleware.cors import CORSMiddleware
from app.services.emotion_service import lifespan
from app.api.deps import get_current_active_user

origins = [
    "http://localhost:5173", # Your frontend origin
    "http://127.0.0.1:5173", # Also allow this variation
    # Add other origins if needed (e.g., your deployed frontend URL)
]

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # List of allowed origins
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods (GET, POST, PUT, etc.)
    allow_headers=["*"], # Allow all headers
)

@app.get("/", tags=["Health"])
async def read_root():
    """
    Welcome endpoint.
    """
    return {"message": f"Welcome to {settings.APP_NAME}"}

# --- Mount API routers ---
app.include_router(
    auth.router,
    prefix=settings.API_V1_STR,
    tags=["Authentication"]
)

app.include_router(
    profiles.router,
    prefix=f"{settings.API_V1_STR}/profiles", # /api/v1/profiles
    tags=["Profiles"]
)

app.include_router(
    matches.router,
    prefix=f"{settings.API_V1_STR}/matches", # /api/v1/matches
    tags=["Matches"],
    dependencies=[Depends(get_current_active_user)] # Apply auth to all match routes
)

app.include_router(websocket.router, tags=["WebSocket"])

app.include_router(
    conversations.router,
    prefix=f"{settings.API_V1_STR}/conversations", # /api/v1/conversations
    tags=["Conversations"],
    dependencies=[Depends(get_current_active_user)] # Apply auth
)

app.include_router(
    users.router,
    prefix=f"{settings.API_V1_STR}/users", # /api/v1/users
    tags=["Users"],
    dependencies=[Depends(get_current_active_user)] # Apply auth
)

app.include_router(
    safety.router,
    prefix=f"{settings.API_V1_STR}/safety", # /api/v1/safety
    tags=["Safety"],
    dependencies=[Depends(get_current_active_user)] # Apply auth
)