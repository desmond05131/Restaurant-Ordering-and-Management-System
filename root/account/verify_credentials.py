import re
from sqlalchemy.orm.exc import NoResultFound
from root.account.get_user_data_from_db import get_user_data_by_UID
from root.database.database_models import session, Credential,User
from passlib.context import CryptContext

from root.utils.bcrypt_helper import hash_pwd, verify_pwd
from root.schemas.auth import SignUpRequest
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


# Input validation for Username
def ValidUsername(Username: str):
    """Username must be 3-50 characters long and only include A-Z, a-z & 0-9"""
    if re.fullmatch(r'[A-Za-z0-9]{3,50}', Username):
        return Username
    else:
        raise ValueError("Username must be 3-50 characters long and only include A-Z, a-z & 0-9")


# Input validation for Email
def ValidEmail(Email: str):
    """Email must be in a valid format (e.g., user@example.com)"""
    if re.fullmatch(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', Email):
        return Email
    else:
        raise ValueError("Email must be in a valid format (e.g., user@example.com)")


# Input validation for Password
def ValidPassword(Password: str):
    """Password must be 6-50 characters long and contain at least one A-Z, a-z, 0-9, and special character"""
    if re.fullmatch(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&]).{6,50}$', Password):
        return Password
    else:
        raise ValueError("Password must be 6-50 characters long and contain at least one A-Z, a-z, 0-9, and special character")


# Validate if user data is a dictionary and perform input checks
def ValidUserData(data: SignUpRequest):

    ValidUsername(data.username)
    ValidEmail(data.email)
    ValidPassword(data.password)


# Get UID from Email
def get_UID_by_email(email: str) -> int:
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.user_id
    except NoResultFound:
        raise ValueError("User with this email doesn't exist.")


# Set credentials in the database
def set_credentials(email: str, password: str):
    try:
        password_hash = hash_pwd(password)
        user_id = get_UID_by_email(email)
        new_credentials = Credential(user_id=user_id, password_hash=password_hash)
        session.add(new_credentials)
        session.commit()
        print("Credentials set successfully.")
    except Exception as e:
        session.rollback()
        raise ValueError(f"An error occurred while setting credentials: {str(e)}")


# Verify credentials and login
def verify_login(email: str, password: str):
    try:
        user_data = get_user_data_by_UID(get_UID_by_email(email))
        credentials = session.query(Credential).filter_by(user_id=user_data['user_id']).one()

        if verify_pwd(password, credentials.password_hash):
            print("Login successfully")
            return user_data
        else:
            raise ValueError("Invalid password")
    except NoResultFound:
        raise ValueError("Invalid Email or user doesn't exist")
    except Exception as e:
        raise ValueError(f"An error occurred during login: {str(e)}")