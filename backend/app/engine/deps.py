"""
Authentication dependencies for FastAPI routes.

Provides:
  - ``get_current_user``         — extract + verify JWT → return User
  - ``require_member``           — ensure user is authenticated and active
  - ``get_project_by_api_key``   — verify Bearer API key for firewall
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.storage.database import get_async_session
from app.storage.models import Project, User

# Cache TTL for API key auth lookups (seconds)
_AUTH_CACHE_TTL = 300  # 5 minutes

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------

async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """Extract and verify JWT from the Authorization header, return User."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not authorization or not authorization.startswith("Bearer "):
        raise credentials_exception
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        user_id: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")
        if user_id is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await session.execute(
        select(User).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


async def require_member(
    current_user: User = Depends(get_current_user),
) -> User:
    """Any authenticated, active user passes."""
    return current_user


async def get_project_by_api_key(
    authorization: Annotated[str | None, Header()] = None,
    session: AsyncSession = Depends(get_async_session),
) -> Project:
    """Verify a project API key from the Authorization header (firewall use).

    Redis-cached auth with negative caching.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    raw_key = authorization.removeprefix("Bearer ").strip()
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    # --- Redis cache check ---
    project_id_cached: str | None = None
    try:
        rd = aioredis.Redis.from_url(
            str(settings.redis_connection_url),
            decode_responses=True,
        )
        cached = await rd.get(f"firewall:auth:{key_hash}")
        await rd.aclose()

        if cached == "null":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )
        if cached:
            data = json.loads(cached)
            project_id_cached = data.get("project_id")
    except HTTPException:
        raise
    except Exception:
        pass  # Redis unavailable — fall through to DB

    # --- Load project ---
    if project_id_cached:
        result = await session.execute(
            select(Project).where(
                Project.id == UUID(project_id_cached),
                Project.is_active.is_(True),
            )
        )
    else:
        result = await session.execute(
            select(Project).where(Project.api_key_hash == key_hash)
        )

    project = result.scalar_one_or_none()
    if project is None or not project.is_active:
        try:
            rd = aioredis.Redis.from_url(
                str(settings.redis_connection_url),
                decode_responses=True,
            )
            await rd.set(f"firewall:auth:{key_hash}", "null", ex=_AUTH_CACHE_TTL)
            await rd.aclose()
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # Cache the valid lookup
    if not project_id_cached:
        try:
            rd = aioredis.Redis.from_url(
                str(settings.redis_connection_url),
                decode_responses=True,
            )
            data = {"project_id": str(project.id)}
            await rd.set(
                f"firewall:auth:{key_hash}",
                json.dumps(data),
                ex=_AUTH_CACHE_TTL,
            )
            await rd.aclose()
        except Exception:
            pass

    return project
