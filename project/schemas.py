from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UrlResponse(BaseModel):
    short_url: str
    long_url: str

class UrlRequest(BaseModel):
    long_url: str
    expires_at: Optional[datetime] = None

