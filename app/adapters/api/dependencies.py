from fastapi import Request, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

from app import config
from ..db.database import AsyncSessionLocal

# --- Rate Limiter Setup ---
limiter = Limiter(key_func=get_remote_address)

# --- Authentication (JWT) Setup ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")  # Ganti "token" dengan endpoint login Anda

async def verify_token(token: str = Depends(oauth2_scheme)):
    """Verifikasi token JWT."""
    try:
        payload = jwt.decode(
            token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM]
        )
        username: str | None = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        return {"username": username}
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

# --- Database Session Dependency ---
async def get_db():
    """
    ✅ FIX: Tambahkan fungsi ini.
    Dependency yang membuka dan menutup koneksi DB async per request.
    """
    async with AsyncSessionLocal() as session:
        yield session