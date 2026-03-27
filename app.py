from fastapi import FastAPI
from db import creat_table
from project.routes import router
from auth.routes import auth_routes
from rate_limiter.routes import limiter
from rate_limiter.middleware import RateLimiMiddleware

app = FastAPI()

@app.on_event('startup')
async def on_startup() -> None:
    await creat_table()



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
