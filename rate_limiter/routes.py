from fastapi import APIRouter, HTTPException, Depends
from rate_limiter.schemas import APIresponse
from sqlalchemy.ext.asyncio import AsyncSession
from db import get_db
from rate_limiter.logic import generate_api_key
from auth.dependencies import get_current_user
from auth.models import User

limiter = APIRouter(prefix='/api')

'''
So, something smart happned here

we dont take user id here because we leave that part to auth
when a user logs in and generates jwt token for themselfs they also get a 
id, so we use that id as a input here in this endpoint
so the user is also authorized and clean

we avoide the 
 broken object level authorization (BOLA) — 
 one of the most common API security bugs

 by doing this method 
'''

@limiter.post('/api-keys', response_model=APIresponse)
async def rate_limiter_endpoint(db: AsyncSession = Depends(get_db),
                                current_user: User =  Depends(get_current_user)):
    return await generate_api_key(current_user.id, db)