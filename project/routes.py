from fastapi import APIRouter, Depends, HTTPException
from db import get_db
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from project.schemas import UrlResponse, UrlRequest
from project.logic import shorten, query

router = APIRouter(prefix='/api')

@router.post('/url_shortner', response_model=UrlResponse)
async def url_schoretn_endpoint(data: UrlRequest, db: AsyncSession = Depends(get_db)):
    return await shorten(data.long_url, db)

@router.get('/{short_code}')
async def get_code_endpoint(short_code: str, db: AsyncSession = Depends(get_db)):
    url = await query(short_code, db)

    if not url:
        raise HTTPException(status_code=404, detail="Short URL not found")
    return RedirectResponse(url=url.long_url, status_code=307)
