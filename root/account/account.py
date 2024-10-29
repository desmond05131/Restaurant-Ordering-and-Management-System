from datetime import timedelta, datetime,timezone
from fastapi import Depends, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import Annotated,Literal
from pydantic import BaseModel, AfterValidator
from sqlalchemy.orm.exc import NoResultFound
from jwt import encode as jwt_encode, decode as jwt_decode, ExpiredSignatureError
from passlib.context import CryptContext

from ..database.database_models import session, Role, User, Credentials, SessionKey
from ..database.data_format import *
from .verify_credentials import get_UID_by_email, set_credentials, verify_login, ValidEmail, ValidPassword, ValidUserData, ValidUsername
from .get_user_data_from_db import get_user_data_by_UID, get_role, get_user, UserData, Users
from api import app

SECRET_KEY = "512d12erd518952976c0db0m7trw95unf785mr9642hx57yb215"
ALGORITHM = "HS256"
bcrypt_context = CryptContext(schemes=['bcrypt'])
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/key")


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
    session.add(session_key)
    session.commit()

    return key


@app.post("/key", tags = ['account'])
async def login_for_session_key(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Key:
    user = verify_login(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')

    print(user)

    created_key = create_session_key(user['Username'], user['UID'], timedelta(minutes=120))

    for key in user['Key']:
        try:
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
        Username: str = payload.get('sub')
        user_id: int = payload.get('id')

        if Username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user 1')

        user = get_user(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user 2')

        if key not in user.Key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user 3')
        print("WHYYYYYYYYY", user.Key)

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
        session_keys = session.query(SessionKey).filter_by(UID = user.UID).all()
        current_using_key = user.current_using_key
       

        session_key_found = False

        for session_key in session_keys:
            print(session_key.Session_Key)
            if session_key.Session_Key == current_using_key:
                session_key_found = True
                break

        if not session_key_found:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user 4')
        
        session_keys = session.query(SessionKey).filter_by(
            UID = user.UID, 
            Session_Key = current_using_key
        ).delete(synchronize_session=False)

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
def edit_user_data(user: Annotated[User, Depends(validate_role(roles=['manager']))], Email : str, new_username : str, new_role_id: int ):
    user_id = get_UID_by_email(Email)
    if user_id is None:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail='user not found')
    try:
        new_Username= new_username
        new_Role_id= new_role_id
        user_data = session.query(User).filter_by(UID = user_id).one()
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
        user_to_delete = session.query(User).filter_by(Email=Email).one_or_none()
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
    
@app.get('/account/view', tags = ['account'])
async def view_accounts(role: Annotated[Literal['customer', 'cashier', 'chef', 'manager'], None] = None):
    role_id_map = {
        'customer': 1,
        'cashier': 2,
        'chef': 3,
        'manager': 4
    }

    query = session.query(User)
    
    if role:
        role_id = role_id_map.get(role)
        if role_id is not None:
            query = query.filter_by(Role_id=role_id)

    accounts = query.all()
    
    return [UserData.from_orm(account) for account in accounts]