from sqlalchemy.ext.asyncio import AsyncSession
from project.models import UrlShortner, Clicks
from sqlalchemy import select, func
from db import SessionLocal
from datetime import datetime, timedelta, timezone
from sqlalchemy import delete
import json
from database.redis_client import redis


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

async def shorten(long_url: str, expires_at: datetime, db: AsyncSession):
    new_url = UrlShortner(long_url=long_url, expires_at=expires_at, short_url="temp")
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

async def log_click(url_id: int, ip_address: str, short_code: str, user_agent: str = None, referer: str = None,):
    async with SessionLocal() as db:
        click = Clicks(
            url_id=url_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referer=referer
        )
        db.add(click)
        await db.commit()

        click_data = {
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        await redis.publish(f'clicks:{short_code}', json.dumps(click_data))


async def total_clicks(url_id: int, db:AsyncSession):
    stmt = select(func.count(Clicks.id)).where(Clicks.url_id == url_id)
    result = await db.execute(stmt)
    clicks = result.scalar_one_or_none()

    return clicks   

async def clicks_per_day(url_id: int, db:AsyncSession):
    day = func.date_trunc('day', Clicks.timestamp)
    stmt = (
        select(day, func.count(Clicks.id))
        .where(Clicks.url_id == url_id, Clicks.timestamp >= datetime.now() - timedelta(days=30))
        .group_by(day)
        .order_by(day)
    )
    result = await db.execute(stmt)
    return result.all()

async def del_url(db: AsyncSession):
    #calculate 30 days ago
    thirty_days = datetime.now(timezone.utc) - timedelta(days=30)



    stmt = delete(UrlShortner).where(UrlShortner.expires_at != None,
                                     UrlShortner.expires_at<thirty_days)
    
    await db.execute(stmt)
    await db.commit()