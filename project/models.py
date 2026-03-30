from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, func
from db import Base
from datetime import datetime

class UrlShortner(Base):
    
    __tablename__ = 'urlshortner'

    id: Mapped[int] = mapped_column(primary_key=True)
    long_url: Mapped[str] = mapped_column(nullable=False)
    short_url: Mapped[str] = mapped_column(nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=True) #we are not doinf server default as we take it as input

class Clicks(Base):
    __tablename__ = 'clicks'
    id:Mapped[int] = mapped_column(primary_key=True)
    url_id: Mapped[int] = mapped_column(ForeignKey('urlshortner.id'))
    timestamp: Mapped[datetime] = mapped_column(server_default=func.now())
    ip_address: Mapped[str] = mapped_column(nullable=False)
    user_agent: Mapped[str] = mapped_column(nullable=True)
    referer: Mapped[str] = mapped_column(nullable=True)