from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
import hashlib
from sqlalchemy import select
from rate_limiter.models import APIKey
from db import SessionLocal
import jwt
from configure import config

class RateLimiMiddleware(BaseHTTPMiddleware):

    '''
    we learn do build a Ratelimiter in form of middleware

    we get the api key from the header and check if it exists
    we hash and compare it to db to find the user, we cannot use depends hence we
    create our own database session.

    'authorization', '' -> '' returns '' insted of None 

    When a client sends an auth header, it looks like this in the raw HTTP request:
    Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6...
    So auth_header holds the entire string "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6...".
    You only want the token part — the JWT — not the word "Bearer". So .replace('Bearer ', '') 
    strips that prefix out, leaving just eyJhbGciOiJIUzI1NiIsInR5cCI6...
    '''

    async def dispatch(self, request: Request, call_next):
        # 1. Code HERE runs BEFORE the route


        x_api_key = request.headers.get('x-api-key')
        if x_api_key:
            hash = hashlib.sha256(x_api_key.encode()).hexdigest()

            async with SessionLocal() as db:
                stmt = select(APIKey).where(APIKey.key == hash)
                result = await db.execute(stmt)

                key = result.scalar_one_or_none()

        #else if no api key is found look for jwt


        if x_api_key is None:
            auth_header = request.headers.get('authorization', '')
            token = auth_header.replace('Bearer ', '')

            payload = jwt.decode(token, config.SECRET_KEY, algorithms=config.ALGORITHM)
            user = payload('sub')

            limit = 10 #for free user

        # 2. This passes the request to the actual route
        response = await call_next(request)




        # 3. Code HERE runs AFTER the route
        #    (you can modify the response if needed)
        
        return response