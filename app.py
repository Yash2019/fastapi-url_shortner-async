from fastapi import FastAPI
from db import creat_table
from project.routes import router
from auth.routes import auth_routes
from rate_limiter.routes import limiter
from rate_limiter.middleware import RateLimiMiddleware
from project.worker import perodic_cleanup
import asyncio


app = FastAPI()

@app.on_event('startup')
async def on_startup() -> None:
    await creat_table()
    asyncio.create_task(perodic_cleanup())



app.include_router(
    auth_routes,
)

app.include_router(
    limiter
)

app.include_router(
    router
)

app.add_middleware(
    RateLimiMiddleware
    )
