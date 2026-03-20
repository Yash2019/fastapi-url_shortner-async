from sqlalchemy.ext.asyncio import AsyncSession
import secrets
from rate_limiter.models import APIKey
import hashlib



'''
    secrets.token_urlsafe gives us raw string such as xK9mQ2..., which is raw so
    if db leaks then there is a problem 

    "URL-safe" just means no characters that would break a URL or HTTP header

    .encode() — converts the string to bytes, because hashlib only accepts bytes

    sha256(...) — runs the SHA-256 hashing algorithm on those bytes. 
    SHA-256 is a one-way function — 
    given the hash, you cannot get the original string back. 
    That's the entire point. It always produces a 256-bit (32 byte) output regardless of input size

    .hexdigest() — those 32 bytes expressed as a hex string (0-9, a-f). Each byte becomes 2 hex chars, so output is always 64 characters.
'''
async def generate_api_key(user_id: int, db: AsyncSession):

    raw = secrets.token_urlsafe(32) 

    hashed = hashlib.sha256(raw.encode()).hexdigest() 

    new_key = APIKey(key=hashed, 
                     user_id=user_id)

    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)
    return new_key