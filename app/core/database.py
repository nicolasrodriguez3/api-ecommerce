from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import Engine, create_engine
from app.core.config import get_settings

settings = get_settings()


class DatabaseConnection:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.__engine = None
        self.__session = None

    @property
    def engine(self) -> Engine:
        if self.__engine is None:
            self.__engine = create_engine(
                self.database_url,
                connect_args=(
                    {"check_same_thread": False}
                    if "sqlite" in self.database_url
                    else {}
                ),
            )
        return self.__engine

    @property
    def session(self):
        if self.__session is None:
            self.__session = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )
        return self.__session()

    def connect(self):
        """Establish a connection to the database."""
        try:
            self.session.connection()
            print(
                "\033[32m", "Database connection established successfully.", "\033[0m"
            )
            return True
        except Exception as e:
            print("\033[31m", f"Failed to connect to the database: {e}", "\033[0m")
            return False

    def disconnect(self):
        """Close the database connection."""
        if self.__session is not None:
            self.__session.close()
            self.__session = None
            print("\033[32m", "Database connection closed successfully.", "\033[0m")
        else:
            print("\033[33m", "No active database session to close.", "\033[0m")




class Base(DeclarativeBase):
    def to_dict(self) -> dict:
        return {
            column.name: getattr(self, column.name)
            for column in self.__class__.__table__.columns
        }


