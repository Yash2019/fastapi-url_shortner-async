from db import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import func
from datetime import datetime

class User(Base):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[int] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(nullable=True)
    hased_password: Mapped[str] = mapped_column(nullable=False)
    is_verified: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at : Mapped[datetime] = mapped_column(server_default=func.now())