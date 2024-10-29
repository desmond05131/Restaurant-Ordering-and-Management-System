from fastapi import FastAPI, status, Depends, HTTPException
from typing import Annotated
from sqlalchemy.orm import Session
from root.database.database_models import *
from root.account.account import sign_up, try_sign_up,login_for_session_key, logout, verify_login, create_account, create_account_details, get_UID_by_email
from root.components.inventory_management import *
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



def generate_test_data():
    # Sample inventory data
    inventory_data = [
        inventory(Inventory_name='Flour', Quantity=50.0, Unit='kg'),
        inventory(Inventory_name='Milk', Quantity=100.0, Unit='liters'),
        inventory(Inventory_name='Eggs', Quantity=200.0, Unit='pcs'),
        inventory(Inventory_name='Sugar', Quantity=70.0, Unit='kg'),
        inventory(Inventory_name='Chicken', Quantity=150.0, Unit='kg'),
        inventory(Inventory_name='Lettuce', Quantity=30.0, Unit='kg'),
        inventory(Inventory_name='Tomato Sauce', Quantity=40.0, Unit='liters'),
        inventory(Inventory_name='Rice', Quantity=120.0, Unit='kg'),
        inventory(Inventory_name='Beef', Quantity=80.0, Unit='kg'),
        inventory(Inventory_name='Cheese', Quantity=30.0, Unit='kg'),
        inventory(Inventory_name='Butter', Quantity=25.0, Unit='kg'),
        inventory(Inventory_name='Salt', Quantity=60.0, Unit='kg'),
        inventory(Inventory_name='Pepper', Quantity=20.0, Unit='kg'),
        inventory(Inventory_name='Olive Oil', Quantity=50.0, Unit='liters'),
        inventory(Inventory_name='Garlic', Quantity=15.0, Unit='kg'),
        inventory(Inventory_name='Onions', Quantity=40.0, Unit='kg'),
        inventory(Inventory_name='Carrots', Quantity=35.0, Unit='kg'),
        inventory(Inventory_name='Potatoes', Quantity=100.0, Unit='kg'),
        inventory(Inventory_name='Bacon', Quantity=50.0, Unit='kg'),
        inventory(Inventory_name='Mushrooms', Quantity=25.0, Unit='kg'),
    ]

# Create inventory entries
    for inv in inventory_data:
        create_inventory(inv)

# Sample menu items data
    menu_items_data = [
        item(Item_name='Pancakes', Price=5.0, Picture_link='link_to_pancakes', Description='Fluffy pancakes.', Category='Brunch/Breakfast'),
        item(Item_name='Spaghetti Carbonara', Price=12.0, Picture_link='link_to_spaghetti', Description='Classic Italian pasta.', Category='Italian'),
        item(Item_name='Chicken Salad', Price=8.0, Picture_link='link_to_salad', Description='Healthy chicken salad.', Category='Main Courses'),
        item(Item_name='Beef Burger', Price=10.0, Picture_link='link_to_burger', Description='Juicy beef burger.', Category='Main Courses'),
        item(Item_name='Chocolate Cake', Price=4.5, Picture_link='link_to_cake', Description='Delicious chocolate cake.', Category='Dessert'),
        item(Item_name='Garlic Bread', Price=3.0, Picture_link='link_to_garlic_bread', Description='Crispy garlic bread.', Category='Sides'),
        item(Item_name='Caesar Salad', Price=7.0, Picture_link='link_to_caesar_salad', Description='Fresh Caesar salad.', Category='Sides'),
        item(Item_name='Grilled Chicken', Price=15.0, Picture_link='link_to_grilled_chicken', Description='Grilled chicken with herbs.', Category='Main Courses'),
        item(Item_name='Vegetable Stir Fry', Price=9.0, Picture_link='link_to_stir_fry', Description='Mixed vegetable stir fry.', Category='Vegan'),
        item(Item_name='Fish and Chips', Price=11.0, Picture_link='link_to_fish_and_chips', Description='Classic fish and chips.', Category='Main Courses'),
    ]

    # Create menu items
    for items in menu_items_data:
        create_item(items)

    # Sample item ingredients data
    item_ingredients_data = [
        # Pancakes
        item_ingredients(Item_id=1, Inventory_id=1, quantity=0.2),  # Flour
        item_ingredients(Item_id=1, Inventory_id=3, quantity=2),    # Eggs
        item_ingredients(Item_id=1, Inventory_id=2, quantity=0.5),  # Milk
        # Spaghetti Carbonara
        item_ingredients(Item_id=2, Inventory_id=9, quantity=0.3),  # Beef
        item_ingredients(Item_id=2, Inventory_id=7, quantity=0.1),  # Tomato Sauce
        item_ingredients(Item_id=2, Inventory_id=20, quantity=0.2), # Bacon
        # Chicken Salad
        item_ingredients(Item_id=3, Inventory_id=5, quantity=0.25), # Chicken
        item_ingredients(Item_id=3, Inventory_id=6, quantity=0.1),  # Lettuce
        item_ingredients(Item_id=3, Inventory_id=16, quantity=0.05),# Onions
        # Beef Burger
        item_ingredients(Item_id=4, Inventory_id=9, quantity=0.2),  # Beef
        item_ingredients(Item_id=4, Inventory_id=10, quantity=0.05),# Cheese
        item_ingredients(Item_id=4, Inventory_id=15, quantity=0.02),# Garlic
        # Chocolate Cake
        item_ingredients(Item_id=5, Inventory_id=4, quantity=0.1),  # Sugar
        item_ingredients(Item_id=5, Inventory_id=2, quantity=0.3),  # Milk
        item_ingredients(Item_id=5, Inventory_id=3, quantity=2),    # Eggs
        item_ingredients(Item_id=5, Inventory_id=11, quantity=0.1), # Butter
        # Garlic Bread
        item_ingredients(Item_id=6, Inventory_id=1, quantity=0.1),  # Flour
        item_ingredients(Item_id=6, Inventory_id=15, quantity=0.05),# Garlic
        item_ingredients(Item_id=6, Inventory_id=11, quantity=0.1), # Butter
        # Caesar Salad
        item_ingredients(Item_id=7, Inventory_id=6, quantity=0.2),  # Lettuce
        item_ingredients(Item_id=7, Inventory_id=10, quantity=0.05),# Cheese
        item_ingredients(Item_id=7, Inventory_id=16, quantity=0.05),# Onions
        # Grilled Chicken
        item_ingredients(Item_id=8, Inventory_id=5, quantity=0.3),  # Chicken
        item_ingredients(Item_id=8, Inventory_id=14, quantity=0.05),# Olive Oil
        item_ingredients(Item_id=8, Inventory_id=15, quantity=0.02),# Garlic
        # Vegetable Stir Fry
        item_ingredients(Item_id=9, Inventory_id=17, quantity=0.2), # Carrots
        item_ingredients(Item_id=9, Inventory_id=18, quantity=0.2), # Potatoes
        item_ingredients(Item_id=9, Inventory_id=19, quantity=0.1), # Mushrooms
        item_ingredients(Item_id=9, Inventory_id=14, quantity=0.05),# Olive Oil
        # Fish and Chips
        item_ingredients(Item_id=10, Inventory_id=18, quantity=0.3),# Potatoes
        item_ingredients(Item_id=10, Inventory_id=14, quantity=0.05),# Olive Oil
        item_ingredients(Item_id=10, Inventory_id=12, quantity=0.02),# Salt
    ]

        # Create item ingredients entries
    for ing in item_ingredients_data:
            create_item_ingredient(ing)

# Call the function to populate the database with test data
generate_test_data()


# def test_login():
#     login_for_session_key(get_UID_by_email('manager0001@mail.com'),'Manager0001@')

# user = session.query(User).filter_by(Username = 'CharlieDowney').one()

test_signup_manager()
test_signup()
##test_login()
##get_item(1)

def test_remove_sk():
   
    sk_list = session.query(SessionKey).filter_by(UID=1).all()
    for sk in sk_list:
        session.delete(sk)
    session.commit()

test_remove_sk=()
