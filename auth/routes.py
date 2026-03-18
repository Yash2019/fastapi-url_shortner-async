from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db import get_db
from auth.dependencies import registration, login
from auth.schemas import UserRegistration, UserResponse, Token
from fastapi.security import OAuth2PasswordRequestForm


auth_routes = APIRouter()


@auth_routes.post('/', response_model=UserResponse)
async def register(task: UserRegistration, db: AsyncSession = Depends(get_db)):
    return await registration(task, db)

@auth_routes.post('/login', response_model=Token)
async def login_endpoint(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    return await login(
        db=db,
        username=form_data.username,
        password=form_data.password
    )