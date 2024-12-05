
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


class DBConnection:
    def __init__(self, connection_string: str) -> None:
        self.connection_string: str = connection_string
        self.__engine: Engine | None = None
        self.__session: Session | None = None
        
    @property
    def session(self):
        if self.__session is None:
            Session = sessionmaker(bind=self.engine)
            self.__session = Session()
        return self.__session
    
    @property
    def engine(self):
        if self.__engine is None:
            self.__engine = create_engine(self.connection_string)
        return self.__engine
        
    def connect(self) -> bool:
        try:
            self.session.connection()
            print("\033[32m","Conectado a la base de datos", "\033[0m")
            return True
        except Exception as e:
            print("\033[31m",f"Error al conectar con la base de datos: {e}", "\033[0m")
            return False
        
    def disconnect(self) -> None:
        if self.__session is not None:
            self.__session.close()
            self.__session = None