import pathlib
from pydantic_settings import BaseSettings, SettingsConfigDict

# Define the base directory of the project
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    # Load .env file from the project's base directory
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    # --- Application Settings ---
    APP_NAME: str = "SoulSync"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # --- Database (PostgreSQL) ---
    DATABASE_URL: str

    # --- Security & JWT ---
    SECRET_KEY: str = "your-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # --- Caching (Redis) ---
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

# Create a single, importable instance of the settings
settings = Settings()