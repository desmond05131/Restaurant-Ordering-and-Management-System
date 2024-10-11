from fastapi import FastAPI, status, Depends, HTTPException
from typing import Annotated
from sqlalchemy.orm import Session
from root.database.database_models import SessionLocal, engine, session, User, SessionKey
from root.account.account import sign_up, try_sign_up,login_for_session_key, logout, verify_login, create_account, create_account_details, get_UID_by_email
from root.manager.inventory_management import get_item,inventory,item, create_item, manage_inventory, remove_inventory,create_ingredient
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

# '''
# def test_create_item():
#     create_ingredient(inventory(
#         Inventory_name = 'Rice',
#         Quantity = 128

#     ))
#     create_ingredient(inventory(
#         Inventory_name = 'Egg',
#         Quantity = 256
#     ))
#     create_item(item(
#         Item_name= 'Egg_fried_rice',
#         Price= 28.8,
#         Picture_link= 'https://www.kitchensanctuary.com/wp-content/uploads/2021/03/Egg-fried-rice-square-FS-40.jpg',
#         Description= 'Expensive egg fried rice',
#         Category= 'Rice'
#     ))
#     create_item_ingredient(item_ingredients(
#         Item_id = 1,
#         Inventory_id = 1,
#         quantity = 1
#     ))
#     create_item_ingredient(item_ingredients(
#         Item_id = 1,
#         Inventory_id = 2,
#         quantity = 3
#     ))
# '''



##test_signup_manager()
##test_signup()
##test_login()
##get_item(1)

def test_remove_sk():
   
    sk_list = session.query(SessionKey).filter_by(UID=1).all()
    for sk in sk_list:
        session.delete(sk)
    session.commit()

test_remove_sk()
