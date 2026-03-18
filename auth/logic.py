from pwdlib import PasswordHash
from sqlalchemy.ext.asyncio import AsyncSession
from auth.models import User
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from functools import partial
from configure import  config
import jwt
import anyio


password_hash = PasswordHash.recommended()


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    func = partial(password_hash.verify, plain_password, hashed_password)
    return await anyio.to_thread.run_sync(func)

async def get_password_hash(password: str) -> str:
    return await anyio.to_thread.run_sync(password_hash.hash, password)

async def get_user(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()

async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | bool | None:
    user = await get_user(db, username)
    if not user:
        return False
    if not await verify_password(password, user.hashed_password):
        return None
    return user

async def create_access_token(data: dict, expire_delta: timedelta | None = None) -> str:
    if "sub" not in data:
        raise ValueError("Token payload must include 'sub'")
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expire_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)