from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

load_dotenv()

from app.adapters.api import nl2sql_router
from app.adapters.api.dependencies import limiter
from app.adapters.db import models
from app.adapters.db.database import engine

# Perintah ini akan membuat semua tabel yang mewarisi dari Base
# Sekarang aman karena 'config' yang dibutuhkan oleh 'engine' sudah di-load.
# models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="RAG Service with Clean Architecture")

# Handler untuk rate limit
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler) # type: ignore

# router
app.include_router(nl2sql_router.router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Welcome to the RAG Service!"}