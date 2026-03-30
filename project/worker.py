from db import SessionLocal
import asyncio
from project.logic import del_url


async def perodic_cleanup():
    while True:
        async with SessionLocal() as db:
            try:
                await del_url(db)
                print('Clean Up worker ran successfully')
            #Exception catches all type of error we dont have to think 
            # e just prints that error
            except Exception as e:
                print('clean up failed as: {e}')

        #we pause the worker free up the CPU
        await asyncio.sleep(3600)