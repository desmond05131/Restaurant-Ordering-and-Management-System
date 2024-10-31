from datetime import timedelta
from typing import Annotated
import uuid
from fastapi import Depends, HTTPException, status

from fastapi.security import OAuth2PasswordRequestForm
from root.account.account import create_session_key, sign_up, validate_role, validate_session_key
from root.database.database_models import session, Role, User, Credential, SessionKey
from root.account.verify_credentials import get_UID_by_email, set_credentials, verify_login, ValidEmail, ValidPassword, ValidUserData, ValidUsername
from root.account.get_user_data_from_db import get_user_data_by_UID, get_role, get_user, UserData, Users
from api import app
from root.schemas.auth import Key, SignUpRequest
from root.utils.bcrypt_helper import hash_pwd


def create_guest_user():
    user = User(role_id=1, is_guest=True)
    session.add(user)
    session.flush()  # To generate user.UID before it's used in Credentials
    credential = Credential(user_id=user.user_id, password_hash=hash_pwd(str(uuid.uuid4())))
    session.add(credential)
    session.commit()
    print(f"Guest account created successfully.")
    return user

@app.post("/account/guest/key", tags = ['Account'])
async def create_guest_session_key() -> Key:
    user = create_guest_user()
    created_key = create_session_key('dummyUsername', user.user_id, timedelta(minutes=120))

    if created_key is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to create guest session key')

    return Key(access_token= created_key, token_type= 'bearer')

@app.post("/account/guest/signup", tags = ['Account'])
async def guest_signup(user: Annotated[User, Depends(validate_role(roles=['customer','manager']))],sign_up_request: SignUpRequest):
    try:
        user_account = session.query(User).filter(User.user_id == user.user_id).filter(User.is_guest == True).one_or_none()
        if user_account is None:
            raise LookupError('Guest account not found')
        
        ValidUserData(sign_up_request)
        existing_user = session.query(User).filter_by(email=sign_up_request.email).one_or_none()
        if existing_user:
            raise LookupError('Email already registered')

        user_account.credentials.password_hash = hash_pwd(sign_up_request.password)
        user_account.is_guest = False
        user_account.username = sign_up_request.username
        user_account.email = sign_up_request.email
        session.commit()
        
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except LookupError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err))
    
    return {"message": f"Guest account converted to user successfully."}