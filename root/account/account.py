from datetime import timedelta, datetime,timezone
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import Annotated, Optional
from pydantic import BaseModel, AfterValidator
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound
from jwt import encode as jwt_encode, decode as jwt_decode, ExpiredSignatureError
from jwt import encode as jwt_encode, decode as jwt_decode, ExpiredSignatureError
from passlib.context import CryptContext

from ..database.database_models import session, Role, User, Credentials, SessionKey
from ..database.data_format import SignUpRequest, EditUserRequest,Key
from .verify_credentials import get_UID_by_email, set_credentials, verify_login, ValidEmail, ValidPassword, ValidUserData, ValidUsername
from .get_user_data_from_db import get_user_data_by_UID, get_role, get_user, UserData, Users
from api import app

SECRET_KEY = "512d12erd518952976c0db0m7trw95unf785mr9642hx57yb215"
ALGORITHM = "HS256"
bcrypt_context = CryptContext(schemes=['bcrypt'])
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/key")

# apa ni
# Sample route to check user authentication
# @app.get("/", status_code=status.HTTP_200_OK)
# async def get_user(user: str, db: db_dependency):
#     if user is None:
#         raise HTTPException(status_code=401, detail='Authentication Failed')
#     return {"User": user}

def sign_up(sign_up_request: SignUpRequest):
    user = User(Username=sign_up_request.Username, Email=sign_up_request.Email, Role_id=1)
    session.add(user)
    session.flush()  # To generate user.UID before it's used in Credentials
    print(sign_up_request.Password)
    credential = Credentials(UID=user.UID, Password_hash=bcrypt_context.hash(sign_up_request.Password))
    session.add(credential)
    session.commit()
    print(f"User {user.Username} created successfully.")

@app.post("/account/signup", status_code=status.HTTP_201_CREATED, tags=['account'])
async def try_sign_up(sign_up_request: SignUpRequest):
    print(sign_up_request)
    try:
        ValidUserData(sign_up_request)
        ValidUsername(sign_up_request.Username)
        ValidEmail(sign_up_request.Email)
        ValidPassword(sign_up_request.Password)

        existing_user = session.query(User).filter_by(Email=sign_up_request.Email).one_or_none()
        if existing_user:
            raise LookupError("Email already registered")

        sign_up(sign_up_request)
    except LookupError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(err)
        )

def create_session_key(Username: str, UID: int, expires_delta: timedelta):
    encode = {'sub': Username, 'id': UID}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    key = jwt_encode(encode, SECRET_KEY, algorithm=ALGORITHM)

    session_key = SessionKey(UID=UID, Session_Key=key)
    key = jwt_encode(encode, SECRET_KEY, algorithm=ALGORITHM)

    session_key = SessionKey(UID=UID, Session_Key=key)
    session.add(session_key)
    session.commit()


    return key


@app.post("/key", tags = ['account'])
async def login_for_session_key(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Key:
    user = verify_login(form_data.username, form_data.password)
    user = verify_login(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')

    print(user)

    created_key = create_session_key(user['Username'], user['UID'], timedelta(minutes=120))

    for key in user['Key']:

    print(user)

    created_key = create_session_key(user['Username'], user['UID'], timedelta(minutes=120))

    for key in user['Key']:
        try:
            validate_session_key(key)
            validate_session_key(key)
        except:
            pass


    if created_key is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to create session key')

    return Key(access_token= created_key, token_type= 'bearer')

async def validate_session_key(key: Annotated[str, Depends(oauth2_bearer)]) -> Users:
    user = None

    try:
        payload = jwt_decode(key, SECRET_KEY, algorithms=[ALGORITHM])
        payload = jwt_decode(key, SECRET_KEY, algorithms=[ALGORITHM])
        Username: str = payload.get('sub')
        user_id: int = payload.get('id')

        if Username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user 1')

        user = get_user(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user 2')

        if key not in user.Key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user 3')

        user.current_using_key = key
        return user

    except ExpiredSignatureError:
        if user and key in user.Key:  # Check if `user` is assigned before accessing it
            user.Key.remove(key)
            session.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Session key expired')

@app.delete(path='/account/expire_session_key', tags=['account'])
async def logout(user: Annotated[Users, Depends(validate_session_key)]):
    try:
        database_user = session.query(User).filter_by(UID = user.UID).one()
        print("ahh", user.current_using_key)
        if "a" not in database_user.session_keys:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user 4')

        database_user.session_keys = [sk for sk in database_user.session_keys if sk.Session_Key != user.current_using_key]
        session.commit()
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=err)


## Manager: a. System Administration

class validate_role:
    def __init__(self, roles):
        self.roles = roles

    def __call__(self, user: Annotated[UserData, Depends(validate_session_key)]):
        user_role = get_role(user.UID)#####

        if user_role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Role not found for user'
            )

        if user_role in self.roles:
            return user

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Insufficient permissions'
        )

class create_account_details(BaseModel):
    Username: Annotated[str, AfterValidator(ValidUsername)]
    Email: Annotated[str, AfterValidator(ValidEmail)]
    Password: Annotated[str, AfterValidator(ValidPassword)]
    Role_id: int

def create_account(account_details: create_account_details):
    user = User(Username=account_details.Username, Email=account_details.Email, Role_id=account_details.Role_id)
    session.add(user)
    session.flush()  # To generate user.UID before it's used in Credentials
    print(account_details.Password)
    credential = Credentials(UID=user.UID, Password_hash=bcrypt_context.hash(account_details.Password))
    session.add(credential)
    session.commit()
    print(f"User {user.Username} created successfully.")

def create_account_if_not_exist(account_details : create_account_details):

    existing_user = session.query(User).filter_by(Email=account_details.Email).one_or_none()
    if existing_user:
        raise LookupError("Email already registered")
    
    create_account(account_details)

@app.post('/account/create/',tags = ['account'])
async def manager_create_account(user : Annotated[User, Depends(validate_role(roles=['manager']))], account_details : create_account_details):
    create_account_if_not_exist(account_details)

##edit credentials
@app.patch('/account/edit/credentials', tags = ['account'])
def edit_credentials(user: Annotated[User, Depends(validate_role(roles=['manager']))], Email : str, new_password : str):
    user_id = get_UID_by_email(Email)
    if user_id is None:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail='user not found')
    try:
        new_password_hash= bcrypt_context.hash(new_password)
        credentials = session.query(Credentials).filter_by(UID = user_id).one()
        credentials.Password_hash = new_password_hash
        session.commit()

        return {"message": f"Password updated seccefully for {Email}"}


    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Credentials not found for the user')
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


##edit user acccount detials
@app.patch('/account/edit/user_data', tags = ['account'])
def edit_user_data(user: Annotated[User, Depends(validate_role(roles=['manager']))], Email : str, new_username : str, new_role_id ):
    user_id = get_UID_by_email(Email)
    if user_id is None:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail='user not found')
    try:
        new_Username= new_username
        new_Role_id= new_role_id
        new_Role_id= new_role_id
        user_data = session.query(UserData).filter_by(UID = user_id).one()
        user_data.Username = new_Username
        user_data.Role_id = new_Role_id

        session.commit()

        return {"message": f"User_data updated seccefully for {Email}"}


    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User data not found for the user')
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.patch('/account/edit/delete_user', tags = ['account'])
def delete_account(user: Annotated[User, Depends(validate_role(roles=['manager']))], Email : str):
    try:
        user_to_delete = session.query(UserData).filter_by(Email=Email).one_or_none()
        if user_to_delete is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        credentials_to_delete = session.query(Credentials).filter_by(UID=user_to_delete.UID).one_or_none()

        if credentials_to_delete is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credentials not found for the given user")

        session.delete(credentials_to_delete)
        session.delete(user_to_delete)
        session.commit()

        return {"message": f"User with email {Email} has been successfully deleted"}

    except HTTPException as err:
        raise err
    except Exception as err:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(err)
        )