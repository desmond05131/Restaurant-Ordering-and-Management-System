from pydantic import BaseModel, Field
from typing import List
from sqlalchemy import select
from sqlalchemy import select
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import Session
from root.database.database_models import User, SessionKey, Credentials, Role, SessionLocal,session

# Dependency to provide database session
def get_db():
    session = session
    try:
        yield session
    finally:
        session.close()


class UserData(BaseModel):
    UID: int
    Username: str
    Email: str
    Role_id: int
    Password_hash: str
    Key: List[str] = Field(default_factory=list)
    current_using_key: str = None

    def commit(self):
        db_session_keys = [sk.Session_Key for sk in session.query(SessionKey).filter_by(UID=self.UID).all()]

        add_session_keys = [key for key in self.Key if key not in db_session_keys]
        remove_session_keys = [key for key in db_session_keys if key not in self.Key]

        for key in add_session_keys:
            session.add(SessionKey(Session_Key=key, UID=self.UID))

        for key in remove_session_keys:
            session.query(SessionKey).filter_by(Session_Key=key, UID=self.UID).delete()

        user = session.query(User).filter_by(UID=self.UID).one()
        user.Username = self.Username
        user.Email = self.Email
        user.Role_id = self.Role_id
        session.commit()


# get user data by UID
def get_user_data_by_UID(user_id: int) -> dict:
    try:
        user = session.query(User).filter_by(UID=user_id).one()#session.execute(select(User.UID).where(User.UID==UID)).one()
        credentials = session.query(Credentials).filter_by(UID=user_id).one() #session.execute(select(Credentials.UID).where(Credentials.UID==UID)).one()
        session_keys = session.query(SessionKey).filter_by(UID=user_id).all() #session.execute(select(SessionKey.UID).where( SessionKey.UID==UID)).all()

        print(user)

        user_data = {
            "UID": user_id,
            "Username": user.Username,
            "Email": user.Email,
            "Role_id": user.Role_id,
            "Password_hash": credentials.Password_hash,
            "Key": [sk.Session_Key for sk in session_keys]
        }

        print(user_data)


        print(user_data)

        return user_data
    except NoResultFound:
        return {}


# get role by UID
def get_role(user_id: int) -> str:
    try:
        user = session.query(User).filter_by(UID=user_id).one()
        role = session.query(Role).filter_by(ID=user.Role_id).one()
        return role.Role_Name
    except NoResultFound:
        return None


class Users(UserData):
    def get_user_role(self):
        return get_role(self.Role_id)


# get user object
def get_user(user_id: int) -> Users:
    user_data = get_user_data_by_UID(user_id)
    if not user_data:
        raise LookupError("User doesn't exist")
    return Users(**user_data)
    
    