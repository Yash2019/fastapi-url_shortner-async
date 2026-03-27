from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
import hashlib
from sqlalchemy import select
from rate_limiter.models import APIKey
from db import SessionLocal
import jwt
from jose import JWTError
from configure import config
from database.redis_client import redis




class RateLimiMiddleware(BaseHTTPMiddleware):

    '''
    we learn do build a Ratelimiter in form of middleware

    call_next(request) hands it off to the actual route handler


    we get the api key from the header and check if it exists
    we hash and compare it to db to find the user, we cannot use depends hence we
    create our own database session.


    'authorization', '' -> '' returns '' insted of None 

    When a client sends an auth header, it looks like this in the raw HTTP request:
    Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6...
    So auth_header holds the entire string "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6...".
    You only want the token part — the JWT — not the word "Bearer". So .replace('Bearer ', '') 
    strips that prefix out, leaving just eyJhbGciOiJIUzI1NiIsInR5cCI6...

    call_next(request) hands it off to the actual route handler
    
    '''

    

    async def dispatch(self, request: Request, call_next):
        skip_paths = ['/', '/login', '/docs', '/openapi.json']
        if request.url.path in skip_paths:
            return await call_next(request)
        
        # 1. Code HERE runs BEFORE the route

        '''
        Checks if the request sent an x-api-key header
If yes → hashes it with SHA-256 (because raw keys are never stored in DB, only their hashes)
Opens a DB session and looks up the APIKey row where the stored hash matches
Pulls user_id from that row and sets limit = 100 (free user rate limit)
        '''


        x_api_key = request.headers.get('x-api-key')
        if x_api_key:
            hashed = hashlib.sha256(x_api_key.encode()).hexdigest()

            async with SessionLocal() as db:
                stmt = select(APIKey).where(APIKey.key == hashed)
                result = await db.execute(stmt)

                key = result.scalar_one_or_none()

                if key is None:
                    return Response('Invalid API key', status_code=401)

                user_identifier = key.user_id
                limit = 100 #for free 
                
        #If there was no API key, it falls into the JWT path
        elif not x_api_key:    #using not early covers None and ""
            try:
                auth_header = request.headers.get('authorization', '')
                token = auth_header.replace('Bearer ', '')

                payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
                user_identifier  = payload.get('sub')
                limit = 10

            except JWTError: 
                return Response("Unauthorized", status_code=401)
            
        redis_key = f"rate_limiter:{user_identifier}"

        current_counter = await redis.incr(redis_key)
        if current_counter == 1:
            await redis.expire(redis_key, 60)
        
        if current_counter>limit:
            return JSONResponse({'detail': 'Too many request'}, status_code=429)
                
        response = await call_next(request)    
        return response