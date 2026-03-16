from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from db import get_db
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json
from database.redis_client import redis
from project.schemas import UrlResponse, UrlRequest
from project.logic import shorten, query, log_click, total_clicks, clicks_per_day

router = APIRouter(prefix='/api')

@router.post('/url_shortner', response_model=UrlResponse)
async def url_schoretn_endpoint(data: UrlRequest, db: AsyncSession = Depends(get_db)):
    return await shorten(data.long_url, db)

@router.get('/{short_code}')
async def get_code_endpoint(short_code: str, request: Request, background_tasks: BackgroundTasks,
                            db: AsyncSession = Depends(get_db)):
    
    url = await query(short_code, db)
        
    if not url:
        raise HTTPException(status_code=404, detail="Short URL not found")

    ip_address = request.client.host
    user_agent = request.headers.get('user-agent')
    referer = request.headers.get('referer')
    background_tasks.add_task(log_click, url.id, ip_address, user_agent, referer)

    return RedirectResponse(url=url.long_url, status_code=307)

@router.get('/stats/{short_code}')
async def total_clicks_endpoint(short_code: str, db:AsyncSession = Depends(get_db)):

    cache_key = f"stats:{short_code}"
    cashed = await redis.get(cache_key)

    if cashed:
        return json.loads(cashed) #returns json
    
    url = await query(short_code, db)

    if not url:
        raise HTTPException(status_code=404, detail='Url Not found')
    
    clicks = await total_clicks(url.id, db)
    per_day_clicks = await clicks_per_day(url.id, db)

    response =  {
        "total_clicks": clicks,
        "clicks_per_day": [
            {"day": row[0].isoformat(), "count": row[1]}
            for row in per_day_clicks
        ]
    }
    # setex-> set with expiry, 300 expiry in secs, dumps-> dict being converted to string
    await redis.setex(cache_key, 300, json.dumps(response))
    return response


