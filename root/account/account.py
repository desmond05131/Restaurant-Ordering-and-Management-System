from datetime import timedelta, datetime,timezone
from fastapi import Depends, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import Annotated,Literal
from pydantic import BaseModel, AfterValidator
from sqlalchemy.orm.exc import NoResultFound
from jwt import encode as jwt_encode, decode as jwt_decode, ExpiredSignatureError
from passlib.context import CryptContext

from root.schemas.auth import Key, SignUpRequest
from root.utils.bcrypt_helper import hash_pwd

from root.database.database_models import session, Role, User, Credential, SessionKey
from root.account.verify_credentials import get_UID_by_email, set_credentials, verify_login, ValidEmail, ValidPassword, ValidUserData, ValidUsername
from root.account.get_user_data_from_db import get_user_data_by_UID, get_role, get_user, UserData, Users
from api import app

SECRET_KEY = "512d12erd518952976c0db0m7trw95unf785mr9642hx57yb215"
ALGORITHM = "HS256"
bcrypt_context = CryptContext(schemes=['bcrypt'])
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/key")


def sign_up(sign_up_request: SignUpRequest):
    user = User(username=sign_up_request.username, email=sign_up_request.email, role_id=1)
    session.add(user)
    session.flush()  # To generate user.UID before it's used in Credentials
    print(sign_up_request.password)
    credential = Credential(user_id=user.user_id, password_hash=hash_pwd(sign_up_request.password))
    session.add(credential)
    session.commit()
    print(f"User {user.username} created successfully.")

@app.post("/account/signup", status_code=status.HTTP_201_CREATED, tags=['Account'])
async def try_sign_up(sign_up_request: SignUpRequest):
    print(sign_up_request)
    try:
        ValidUserData(sign_up_request)
        existing_user = session.query(User).filter_by(email=sign_up_request.email).one_or_none()
        if existing_user:
            raise LookupError("Email already registered")

        sign_up(sign_up_request)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except LookupError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(err)
        )

def create_session_key(username: str, user_id: int, expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    key = jwt_encode(encode, SECRET_KEY, algorithm=ALGORITHM)

    session_key = SessionKey(user_id=user_id, session_key=key)
    session.add(session_key)
    session.commit()

    return key


@app.post("/key", tags = ['Account'])
async def login_for_session_key(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Key:
    user = verify_login(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')

    print(user)

    created_key = create_session_key(user['username'], user['user_id'], timedelta(minutes=120))

    for key in user['key']:
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

        if key not in user.key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user 3')

        user.current_using_key = key
        return user

    except ExpiredSignatureError:
        if user and key in user.key:  # Check if `user` is assigned before accessing it
            user.key.remove(key)
            session.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Session key expired')

@app.delete(path='/account/expire_session_key', tags=['Account'])
async def logout(user: Annotated[Users, Depends(validate_session_key)]):
    try:
        session_keys = session.query(SessionKey).filter_by(user_id = user.user_id).all()
        current_using_key = user.current_using_key
       

        session_key_found = False

        for session_key in session_keys:
            print(session_key.session_key)
            if session_key.session_key == current_using_key:
                session_key_found = True
                break

        if not session_key_found:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user 4')
        
        session_keys = session.query(SessionKey).filter_by(
            user_id = user.user_id, 
            session_key = current_using_key
        ).delete(synchronize_session=False)

        session.commit()
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=err)


## Manager: a. System Administration

class validate_role:
    def __init__(self, roles):
        self.roles = roles

    def __call__(self, user: Annotated[UserData, Depends(validate_session_key)]):
        user_role = get_role(user.user_id)#####

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

class CreateAccountDetails(BaseModel):
    username: Annotated[str, AfterValidator(ValidUsername)]
    email: Annotated[str, AfterValidator(ValidEmail)]
    password: Annotated[str, AfterValidator(ValidPassword)]
    role_id: int

def create_account(account_details: CreateAccountDetails):
    user = User(username=account_details.username, email=account_details.email, role_id=account_details.role_id)
    session.add(user)
    session.flush()  # To generate user.UID before it's used in Credentials
    print(account_details.password)
    credential = Credential(user_id=user.user_id, password_hash=hash_pwd(account_details.password))
    session.add(credential)
    session.commit()
    print(f"User {user.username} created successfully.")

def create_account_if_not_exist(account_details : CreateAccountDetails):

    existing_user = session.query(User).filter_by(email=account_details.email).one_or_none()
    if existing_user:
        raise LookupError("Email already registered")
    
    create_account(account_details)

@app.post('/account/create/',tags = ['Account'])
async def manager_create_account(user : Annotated[User, Depends(validate_role(roles=['manager']))], account_details : CreateAccountDetails):
    try:
        create_account_if_not_exist(account_details)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

##edit credentials
@app.patch('/account/edit/credentials', tags = ['Account'])
def edit_credentials(user: Annotated[User, Depends(validate_role(roles=['manager']))], email : str, new_password : str):
    user_id = get_UID_by_email(email)
    if user_id is None:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail='user not found')
    try:
        new_password_hash= hash_pwd(new_password)
        credentials = session.query(Credential).filter_by(user_id = user_id).one()
        credentials.password_hash = new_password_hash
        session.commit()

        return {"message": f"Password updated seccefully for {email}"}

    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Credentials not found for the user')
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

##edit user acccount detials
@app.patch('/account/edit/user_data', tags = ['Account'])
def edit_user_data(user: Annotated[User, Depends(validate_role(roles=['manager']))], email : str, new_username : str, new_role_id: int ):
    user_id = get_UID_by_email(email)
    if user_id is None:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail='user not found')
    try:
        new_Username= new_username
        new_role_id= new_role_id
        user_data = session.query(User).filter_by(user_id = user_id).one()
        user_data.username = new_username
        user_data.role_id = new_role_id
        session.commit()

        return {"message": f"User_data updated seccefully for {email}"}

    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User data not found for the user')
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.patch('/account/edit/delete_user', tags = ['Account'])
def delete_account(user: Annotated[User, Depends(validate_role(roles=['manager']))], email : str):
    try:
        user_to_delete = session.query(User).filter_by(email=email).one_or_none()
        if user_to_delete is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        credentials_to_delete = session.query(Credential).filter_by(user_id=user_to_delete.user_id).one_or_none()

        if credentials_to_delete is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credentials not found for the given user")

        session.delete(credentials_to_delete)
        session.delete(user_to_delete)
        session.commit()

        return {"message": f"User with email {email} has been successfully deleted"}

    except HTTPException as err:
        raise err
    except Exception as err:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(err)
        )
    
@app.get('/account/view', tags = ['Account'])
async def view_accounts(role: Annotated[Literal['customer', 'cashier', 'chef', 'manager'], None] = None):
    role_id_map = {
        'customer': 1,
        'cashier': 2,
        'chef': 3,
        'manager': 4
    }

    query = session.query(User).filter_by(is_guest=False)
    
    if role:
        role_id = role_id_map.get(role)
        if role_id is not None:
            query = query.filter_by(role_id=role_id)

    accounts = query.all()
    
    return [UserData.from_orm(account) for account in accounts]