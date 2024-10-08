from fastapi import FastAPI, status, Depends, HTTPException
from typing import Annotated
from sqlalchemy.orm import Session

from root.account.database_models import SessionLocal, engine
from root.account.account import sign_up, try_sign_up,login_for_session_key, logout, verify_login
from root import database_models
from root import account
from root.account.api import app

# Dependency to provide database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
