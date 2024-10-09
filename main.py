from fastapi import FastAPI, status, Depends, HTTPException
from typing import Annotated
from sqlalchemy.orm import Session
from root.database.database_models import SessionLocal, engine, session, User
from root.account.account import sign_up, try_sign_up,login_for_session_key, logout, verify_login, create_account, create_account_details, get_UID_by_email
from root.manager.inventory_management import inventory, create_item, manage_inventory, remove_inventory
from root import database_models
from root import account
from api import app

# Dependency to provide database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

## test sign up users
def test_signup():
    create_account(create_account_details(
        Email= 'customer0001@mail.com',
        Username= 'AlanBeth',
        Password= 'Cus0001@',
        Role_id= 1
    ))

def test_signup_manager():
    create_account(create_account_details(
        Email= 'manager0001@mail.com',
        Username= 'CharlieDowney',
        Password= 'Maneger0001@',
        Role_id= 4
    ))

def test_login():
    login_for_session_key(get_UID_by_email('manager0001@mail.com'),'Manager0001@')

user = session.query(User).filter_by(Username = 'CharlieDowney').one()


##test_signup_manager()
##test_signup()
##test_login()

