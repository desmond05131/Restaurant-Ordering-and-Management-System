from pydantic import BaseModel, Field
from typing import List
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
    Role_ID: int
    Role_Name: str
    UID: int
    Username: str
    Email: str
    Role_id: int
    Password_hash: str
    Key: List[str] = Field(default_factory=list)

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
def get_user_data_by_UID(UID: int) -> dict:
    try:
        user = session.query(User).filter_by(UID=UID).one()#session.execute(select(User.UID).where(User.UID==UID)).one()
        credentials = session.query(Credentials).filter_by(UID=UID).one() #session.execute(select(Credentials.UID).where(Credentials.UID==UID)).one()
        session_keys = session.query(SessionKey).filter_by(UID=UID).all() #session.execute(select(SessionKey.UID).where( SessionKey.UID==UID)).all()

        print(user)

        user_data = {
            "UID": UID,
            "Username": user.Username,
            "Email": user.Email,
            "Password_hash": credentials.Password_hash,
            "Key": [sk.Session_Key for sk in session_keys]
        }

        print(user_data)

        return user_data
    except NoResultFound:
        return {}


# get role by UID
def get_role(UID: int) -> str:
    try:
        user = session.query(User).filter_by(UID=UID).one()
        role = session.query(Role).filter_by(Role_ID=user.Role_id).one()
        return role.Role_Name
    except NoResultFound:
        return None


class Users(UserData):
    def get_user_role(self):
        return get_role(self.Role_id, session)


# get user object
def get_user(UID: int) -> Users:
    user_data = get_user_data_by_UID(UID, session)
    if not user_data:
        raise LookupError("User doesn't exist")
    return Users(**user_data)
    