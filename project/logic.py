from sqlalchemy.ext.asyncio import AsyncSession
from project.models import UrlShortner
from sqlalchemy import select

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
