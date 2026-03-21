from pydantic import BaseModel
from datetime import datetime

class APIresponse(BaseModel):
    key: str
    created_at: datetime