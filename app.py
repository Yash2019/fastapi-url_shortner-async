from fastapi import FastAPI
from db import creat_table
from project.routes import router


app = FastAPI()

@app.on_event('startup')
async def on_startup() -> None:
    await creat_table()
app.include_router(
    router
)