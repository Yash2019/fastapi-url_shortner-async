from sqlalchemy.ext.asyncio import AsyncSession
from project.models import UrlShortner, Clicks
from sqlalchemy import select
from db import SessionLocal

def base62encoding(number: int) -> str:
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    if number == 0:
        return alphabet[0]
    result = []
    while number > 0:
        remainder = number % 62
        result.append(alphabet[remainder])
        number = number // 62
    return ''.join(result[::-1])

async def shorten(long_url: str, db: AsyncSession):
    new_url = UrlShortner(long_url=long_url, short_url="temp")
    db.add(new_url)
    await db.commit()
    await db.refresh(new_url)

    short_code = base62encoding(new_url.id)
    new_url.short_url = short_code
    await db.commit()

    return new_url

async def query(short_code: str, db:AsyncSession):
    stmt = select(UrlShortner).where(UrlShortner.short_url == short_code)
    result = await db.execute(stmt)
    url = result.scalar_one_or_none()
    return url

async def log_click(url_id: int, ip_address: str, user_agent: str = None, referer: str = None):
    async with SessionLocal() as db:
        click = Clicks(
            url_id=url_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referer=referer
        )
        db.add(click)
        await db.commit()