from pydantic import BaseModel, Field
from typing import List
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import Session
from root.account.database_models import User, SessionKey, Credentials, Role, SessionLocal

# Dependency to provide database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class UserData(BaseModel):
    ID: int  # Stored in the Roles table
    Role_Name: str
    UID: int  # Stored in UserData table
    Username: str
    Email: str
    Role_id: int
    Password_hash: str  # Stored in credentials table
    Key: List[str] = Field(default_factory=list)  # Stored in session_key table

    def commit(self, db: Session):
        # Retrieve session keys from the database
        db_session_keys = [sk.Session_Key for sk in db.query(SessionKey).filter_by(UID=self.UID).all()]

        # Identify session keys to add and remove
        add_session_keys = [key for key in self.Key if key not in db_session_keys]
        remove_session_keys = [key for key in db_session_keys if key not in self.Key]

        # Add new session keys
        for key in add_session_keys:
            db.add(SessionKey(Session_Key=key, UID=self.UID))

        # Remove old session keys
        for key in remove_session_keys:
            db.query(SessionKey).filter_by(Session_Key=key, UID=self.UID).delete()

        # Update user data
        user = db.query(User).filter_by(UID=self.UID).one()
        user.Username = self.Username
        user.Email = self.Email
        user.Role_id = self.Role_id
        db.commit()


# Function to retrieve user data by UID
def get_user_data_by_UID(UID: int, db: Session) -> dict:
    try:
        user = db.query(User).filter_by(UID=UID).one()
        credentials = db.query(Credentials).filter_by(UID=UID).one()
        session_keys = db.query(SessionKey).filter_by(UID=UID).all()

        user_data = {
            "UID": UID,
            "Username": user.Username,
            "Email": user.Email,
            "Password_hash": credentials.Password_hash,
            "Key": [sk.Session_Key for sk in session_keys]
        }
        return user_data
    except NoResultFound:
        return {}


# Function to retrieve the user's role
def get_role(UID: int, db: Session) -> str:
    try:
        user = db.query(User).filter_by(UID=UID).one()
        role = db.query(Role).filter_by(ID=user.Role_id).one()
        return role.Role_Name
    except NoResultFound:
        return None


class Users(UserData):
    def get_user_role(self, db: Session):
        return get_role(self.Role_id, db)


# Function to retrieve the user object
def get_user(UID: int, db: Session) -> Users:
    user_data = get_user_data_by_UID(UID, db)
    if not user_data:
        raise LookupError("User doesn't exist")
    return Users(**user_data)








    



                    



