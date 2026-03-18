from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from db import get_db
from sqlalchemy import select
from auth.models import User
import jwt
from jwt.exceptions import InvalidTokenError
from configure import config
from auth.logic import get_user, get_password_hash, authenticate_user, create_access_token
from auth.schemas import UserRegistration

'''
What does this function do?

-> Given a JWT token from the request, figure out who the user is, or reject them.
-> oauth_schema - extracts Authorization header form incoming request
-> Annotated - type hint in this case a str
-> WWW-Authenticate: Bearer` header - I expect a Bearer token
'''

'''
Full Flow of the Programme

Request hits route
    → FastAPI sees Depends(oauth_schema)
    → oauth_schema reads Authorization header, extracts token string
    → get_current_user() is called with that string
    → jwt.decode() tries to verify + decode it
        → if anything is wrong → InvalidTokenError → 401
    → check payload has 'sub' field → if not → 401
    → query DB for that username → if not found → 401
    → return user object to your route handler
'''

oauth_schema = OAuth2PasswordBearer(tokenUrl='login')


async def get_current_user(
        token: Annotated[str, Depends(oauth_schema)], db: AsyncSession = Depends(get_db)):
    
    credential_exceptions = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                                          detail="Could not validate credentials",
                                          headers={"WWW-Authenticate": 'Bearer'})
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username = payload.get('sub')

        if username is None:
            raise credential_exceptions
        
    except InvalidTokenError:
        raise credential_exceptions
    
#Checks if the user is in database
    user  = await get_user(db, username=username)
    if user is None:
        raise credential_exceptions
    return user

async def registration(user_create: UserRegistration, db: AsyncSession):
    result = await db.execute(select(User).where(User.username == user_create.usernmame))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='User Already Exists'
        )
    
    hashed_password = await get_password_hash(user_create.password)

    new_user = User(
        username = user_create.usernmame,
        email = user_create.email,
        hashed_password = hashed_password
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def login(db: AsyncSession, username:str, password: str):
    user = await authenticate_user(db, username, password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    access_token = await create_access_token(data={'sub': user.username})

    return {
        'access_token': access_token,
        'token_type': 'bearer'
    }