from sqlalchemy.orm import DeclarativeBase


class BaseModel(DeclarativeBase):
    __abstract__ = True
    
    def to_dict(self) -> dict:
        return {
            column.name: getattr(self, column.name)
            for column in self.__class__.__table__.columns
        }