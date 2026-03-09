from pydantic import BaseModel

class UrlResponse(BaseModel):
    short_url: str
    long_url: str

class UrlRequest(BaseModel):
    long_url: str
