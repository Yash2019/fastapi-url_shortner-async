from db import Base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import ForeignKey, func
from datetime import datetime


'''
Ratelimiter belongs to the user.
Hence its connected to auth/models.user.id
'''

class APIKey(Base):
    __tablename__ = 'apikey'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(nullable=False, unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())