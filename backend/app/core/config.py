from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    QDRANT_URL: str
    QDRANT_API_KEY: str
    QDRANT_COLLECTION: str = "legal_clauses"

    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    BM25_INDEX_PATH: str = "./data/bm25_index.pkl"

    class Config:
        env_file = ".env"


settings = Settings()
