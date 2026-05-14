import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

print("==> [LegalAI] Python process started", flush=True)

from app.core.config import settings
print(f"==> [LegalAI] Config loaded. DB={settings.DATABASE_URL[:30]}...", flush=True)

from app.core.database import engine, Base
print("==> [LegalAI] Database engine created", flush=True)

from app.api.routes import auth, contracts, search
print("==> [LegalAI] Routes imported", flush=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("==> [LegalAI] Running DB migrations...", flush=True)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("==> [LegalAI] DB migrations complete", flush=True)
    except Exception as e:
        print(f"==> [LegalAI] DB migration failed: {e}", flush=True)
    yield


app = FastAPI(
    title="LegalAI API",
    version="1.0.0",
    description="AI-powered contract analysis",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(contracts.router, prefix="/api")
app.include_router(search.router, prefix="/api")

print("==> [LegalAI] App ready, waiting for uvicorn to bind port...", flush=True)


@app.get("/health")
async def health():
    return {"status": "ok"}
