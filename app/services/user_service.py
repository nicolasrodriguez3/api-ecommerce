from sqlalchemy.exc import IntegrityError
from app.core import database_connection
from app.models.user_model import UserModel



class UserService:
    def __init__(self):
        self.db = database_connection.session

    def create(self, new_user_dict: dict) -> dict:
        print(new_user_dict)
        new_user = UserModel(**new_user_dict)
        self.db.add(new_user)
        try:
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()

        self.db.refresh(new_user)
        return new_user.to_dict()
