from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import Session
from root.database.database_models import User, SessionKey, Credential, Role, SessionLocal,session
from pydantic import ConfigDict


class UserData(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    username: Optional[str] = None
    email: Optional[str] = None
    role_id: int
    password_hash: Optional[str] = None
    key: List[str] = Field(default_factory=list)
    current_using_key: str = None

    def commit(self):
        db_session_keys = [sk.session_key for sk in session.query(SessionKey).filter_by(user_id=self.user_id).all()]

        add_session_keys = [key for key in self.key if key not in db_session_keys]
        remove_session_keys = [key for key in db_session_keys if key not in self.key]

        for key in add_session_keys:
            session.add(SessionKey(session_key=key, user_id=self.user_id))

        for key in remove_session_keys:
            session.query(SessionKey).filter_by(session_key=key, user_id=self.user_id).delete()

        user = session.query(User).filter_by(user_id=self.user_id).one()
        user.username = self.username
        user.email = self.email
        user.role_id = self.role_id
        user.key = self.key
        session.commit()


# get user data by UID
def get_user_data_by_UID(user_id: int) -> dict:
    try:
        user = session.query(User).filter_by(user_id=user_id).one()#session.execute(select(User.UID).where(User.UID==UID)).one()
        credentials = session.query(Credential).filter_by(user_id=user_id).one() #session.execute(select(Credentials.UID).where(Credentials.UID==UID)).one()
        session_keys = session.query(SessionKey).filter_by(user_id=user_id).all() #session.execute(select(SessionKey.UID).where( SessionKey.UID==UID)).all()

        print(user)

        user_data = {
            "user_id": user_id,
            "username": user.username,
            "email": user.email,
            "role_id": user.role_id,
            "password_hash": credentials.password_hash,
            "key": [sk.session_key for sk in session_keys]
        }

        print(user_data)

        return user_data
    except NoResultFound:
        return {}


# get role by UID
def get_role(user_id: int) -> str:
    try:
        user = session.query(User).filter_by(user_id=user_id).one()
        role = session.query(Role).filter_by(role_id=user.role_id).one()
        return role.name
    except NoResultFound:
        return None


class Users(UserData):
    def get_user_role(self):
        return get_role(self.role_id)


# get user object
def get_user(user_id: int) -> Users:
    user_data = get_user_data_by_UID(user_id)
    if not user_data:
        raise LookupError("User doesn't exist")
    return Users(**user_data)
    
    