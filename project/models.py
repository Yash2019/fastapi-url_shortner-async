from sqlalchemy.orm import Mapped, mapped_column
from db import Base

class UrlShortner(Base):
    
    __tablename__ = 'urlshortner'

    id: Mapped[int] = mapped_column(primary_key=True)
    long_url: Mapped[str] = mapped_column(nullable=False)
    short_url: Mapped[str] = mapped_column(nullable=False)
