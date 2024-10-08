from datetime import timedelta, datetime
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import Annotated, Optional
from pydantic import BaseModel, AfterValidator
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound
from jwt import encode, decode, ExpiredSignatureError
from passlib.context import CryptContext

from .database_models import session, Role, User, Credentials, SessionKey
from .verify_credentials import get_UID_by_email, set_credentials, verify_login, ValidEmail, ValidPassword, ValidUserData, ValidUsername
from .get_user_data_from_db import get_user_data_by_UID, get_role, get_user, UserData, Users
from .api import app

SECRET_KEY = "512d12erd518952976c0db0m7trw95unf785mr9642hx57yb215"
ALGORITHM = "HS256"
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/account/key")

class SignUpRequest(BaseModel):
    Username: str
    Email: str
    Password: str

class EditUserRequest(BaseModel):
    Username: Optional[str] = None
    Email: Optional[str] = None
    Password: Optional[str] = None

class Key(BaseModel):
    access_key: str
    key_type: str

# Dependency to get the database session
def get_db():
    db = session
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# apa lanjau ni
# Sample route to check user authentication
# @app.get("/", status_code=status.HTTP_200_OK)
# async def get_user(user: str, db: db_dependency):
#     if user is None:
#         raise HTTPException(status_code=401, detail='Authentication Failed')
#     return {"User": user}

def sign_up(sign_up_request: SignUpRequest, db: Session):
    user = User(Username=sign_up_request.Username, Email=sign_up_request.Email, Role_id=1)
    db.add(user)
    db.flush()  # To generate user.UID before it's used in Credentials
    credential = Credentials(UID=user.UID, Password_hash=bcrypt_context.hash(sign_up_request.Password))
    db.add(credential)
    db.commit()
    print(f"User {user.Username} created successfully.")

@app.post("/account/signup", status_code=status.HTTP_201_CREATED, tags=['account'])
async def try_sign_up(db: db_dependency, sign_up_request: SignUpRequest):
    try:
        ValidUserData(sign_up_request)
        ValidUsername(sign_up_request.Username)
        ValidEmail(sign_up_request.Email)
        ValidPassword(sign_up_request.Password)

        existing_user = db.query(UserData).filter_by(Email=sign_up_request.Email).one_or_none()
        if existing_user:
            raise LookupError("Email already registered")
        
        sign_up(sign_up_request, db)
    except LookupError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(err)
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(err)
        )

def create_session_key(Username: str, UID: int, expires_delta: timedelta, db: Session):
    encode = {'sub': Username, 'id': UID}
    expires = datetime.utcnow() + expires_delta
    encode.update({'exp': expires})
    key = encode(encode, SECRET_KEY, algorithm=ALGORITHM)
    
    session_key = SessionKey(UID=UID, SessionKey=key)
    db.add(session_key)
    db.commit()
    
    return key

@app.post("/key", response_model=Key, tags = ['account'])
async def login_for_session_key(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = verify_login(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')
    
    created_key = create_session_key(user.Username, user.UID, timedelta(minutes=120), db)
    
    for key in user.session_keys:
        try:
            validate_session_key(key, db)
        except:
            pass
    
    if created_key is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to create session key')

    return {'access_key': created_key, 'key_type': 'bearer'}

async def validate_session_key(key: Annotated[str, Depends(oauth2_bearer)], db: db_dependency):
    try:
        payload = decode(key, SECRET_KEY, algorithms=[ALGORITHM])
        Username: str = payload.get('sub')
        UID: int = payload.get('id')
        if Username is None or UID is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')
        
        user = get_user(UID, db)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')
        
        if key not in [s.SessionKey for s in user.session_keys]:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')
        
        return {'username': Username, 'id': UID}
    except ExpiredSignatureError:
        if key in user.session_keys:
            user.session_keys.remove(key)
            db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Session key expired')

@app.delete(path='/account/expire_session_key', tags=['account'])
async def logout(user: Annotated[User, Depends(validate_session_key)], key: str, db: db_dependency):
    try:
        user = get_user(user.id, db)
        if key not in [s.SessionKey for s in user.session_keys]:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')

        user.session_keys = [s for s in user.session_keys if s.SessionKey != key]
        db.commit()
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')


## Manager: a. System Administration

class validate_role:
    def __init__(self, roles):
        self.roles = roles

    def __call__(self, user: Annotated[User, Depends(validate_session_key)]):
        user_role = get_role(user.UID)

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

def create_account(db : db_dependency, account_details : create_account_details):
    
    existing_user = db.query(UserData).filter_by(Email=create_account_details.Email).one_or_none()
    if existing_user:
        raise LookupError("Email already registered")
    sign_up(account_details)

@app.post('/account/create/',tags = ['account'])
async def manager_create_account(user : Annotated[User, Depends(validate_role(roles=['Manager']))], account_details : create_account_details):
    create_account(create_account_details)

##edit credentials
@app.patch('/account/edit/credentials', tags = ['account'])
def edit_credentials(db : db_dependency, user: Annotated[User, Depends(validate_role(roles=['Manager']))], Email : str, new_password : str):
    user_id = get_UID_by_email(Email)
    if user_id is None:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail='user not found')
    try:
        new_password_hash= bcrypt_context.hash(new_password)
        credentials = db.query(Credentials).filter_by(UID = user_id).one()
        credentials.Password_hash = new_password_hash
        db.commit()

        return {"message": f"Password updated seccefully for {Email}"}
    
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Credentials not found for the user')
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.patch('/account/edit/delete_user', tags = ['account'])
def delete_account(db : db_dependency, user: Annotated[User, Depends(validate_role(roles=['Manager']))], Email : str):
    try:
        user_to_delete = db.query(UserData).filter_by(Email=Email).one_or_none()
        if user_to_delete is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        credentials_to_delete = db.query(Credentials).filter_by(UID=user_to_delete.UID).one_or_none()

        if credentials_to_delete is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credentials not found for the given user")

        db.delete(credentials_to_delete)
        db.delete(user_to_delete)
        db.commit()

        return {"message": f"User with email {Email} has been successfully deleted"}

    except HTTPException as err:
        raise err
    except Exception as err:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(err)
        )








    

   
    



    




   

 



