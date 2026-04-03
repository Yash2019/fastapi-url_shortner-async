from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from db import get_db
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json
from database.redis_client import redis
from project.schemas import UrlResponse, UrlRequest
from project.logic import shorten, query, log_click, total_clicks, clicks_per_day
from auth.dependencies import get_current_user, get_current_user_flexible
from auth.models import User
from datetime import datetime, timezone
#---------websocket stuff----------------
from fastapi import WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis
from configure import config



router = APIRouter(prefix='/api')

@router.post('/url_shortner', response_model=UrlResponse)
async def url_schoretn_endpoint(data: UrlRequest, db: AsyncSession = Depends(get_db),
                                current_user: User = Depends(get_current_user_flexible)):
    return await shorten(data.long_url, data.expires_at, db)

@router.get('/{short_code}')
async def get_code_endpoint(short_code: str, request: Request, background_tasks: BackgroundTasks,
                            db: AsyncSession = Depends(get_db)):
    
    url = await query(short_code, db)
        
    if not url:
        raise HTTPException(status_code=404, detail="Short URL not found")
    #is expire time given   whats the expiry time and delete it immediately(soft delete) background worker will delete it after 30 days
    if url.expires_at and url.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail='link has been deleted')

    ip_address = request.client.host
    user_agent = request.headers.get('user-agent')
    referer = request.headers.get('referer')
    background_tasks.add_task(log_click, url.id, ip_address, user_agent, referer, short_code)

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

@router.websocket('/links/{short_code}/live')
async def websocket_live_clicks(websocket: WebSocket, short_code: str):
    
    #picks up the phone
    await websocket.accept()

    #new connection
    #strictly for listining                            convert back to strings
    punsub_redis = aioredis.from_url(config.REDIS_URL, decode_responses=True)
    pubsub = punsub_redis.pubsub()

    #subscribe to the channel
    await pubsub.subscribe(f'clicks:{short_code}')

    try:
        #stayes open indefinitely
        while True:
            #looks for new messages
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)

            if message is not None:

                await websocket.send_text(message['data'])

    except WebSocketDisconnect:
        pass

    finally:
        # 6. Cleanup: Unsubscribe and close the Redis connection
        await pubsub.unsubscribe(f"clicks:{short_code}")
        await pubsub_redis.aclose()



