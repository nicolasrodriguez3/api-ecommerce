from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args=(
        {"check_same_thread": False} if "sqlite" in settings.database_url else {}
    ),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    def to_dict(self) -> dict:
        return {
            column.name: getattr(self, column.name)
            for column in self.__class__.__table__.columns
        }


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
