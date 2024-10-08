from fastapi import FastAPI, status, Depends, HTTPException
from typing import Annotated
from sqlalchemy.orm import Session
from accounts_related.database_models import SessionLocal, engine
from accounts_related.account import sign_up, try_sign_up,login_for_session_key, logout, verify_login
import accounts_related.database_models

# FastAPI app setup
app = FastAPI()
app.include_router(accounts_related.account.router)

# Create all tables
accounts_related.database_models.Base.metadata.create_all(bind=engine)

# Dependency to provide database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# Sample route to check user authentication
@app.get("/", status_code=status.HTTP_200_OK)
async def get_user(user: str = None, db: db_dependency = Depends()):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    return {"User": user}

