from datetime import datetime, time
from fastapi import FastAPI, status, Depends, HTTPException
from typing import Annotated
from root.database.database_models import MenuItem, Inventory, ItemIngredient, SessionKey, SessionLocal, TableNumber, session
from root.account.account import sign_up, try_sign_up,login_for_session_key, logout, verify_login, create_account, CreateAccountDetails, get_UID_by_email
from root.components.inventory_management import create_inventory, create_item, create_item_ingredient
from root.components.voucher import create_voucher
# from root.components.order_management import create_order, create_order_item
# from root.components.customer_feedback import create_user_item_rating
# from root.components.machines import create_machine, create_machine_ingredient
from api import app
from root.schemas.voucher import VoucherBase, VoucherRequirementBase

# Dependency to provide database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

## test sign up users
def test_signup():
    create_account(CreateAccountDetails(
        email= 'customer0001@mail.com',
        username= 'AlanBeth',
        password= 'Cus0001@',
        role_id= 1
    ))

def test_signup_manager():
    create_account(CreateAccountDetails(
        email= 'manager0001@mail.com',
        username= 'CharlieDowney',
        password= 'Maneger0001@',
        role_id= 4
    ))


def generate_test_data():
    # Sample inventory data
    inventory_data = [
        Inventory(inventory_name='Flour', quantity=50.0, unit='kg'),
        Inventory(inventory_name='Milk', quantity=100.0, unit='liters'),
        Inventory(inventory_name='Eggs', quantity=200.0, unit='pcs'),
        Inventory(inventory_name='Sugar', quantity=70.0, unit='kg'),
        Inventory(inventory_name='Chicken', quantity=150.0, unit='kg'),
        Inventory(inventory_name='Lettuce', quantity=30.0, unit='kg'),
        Inventory(inventory_name='Tomato Sauce', quantity=40.0, unit='liters'),
        Inventory(inventory_name='Rice', quantity=120.0, unit='kg'),
        Inventory(inventory_name='Beef', quantity=80.0, unit='kg'),
        Inventory(inventory_name='Cheese', quantity=30.0, unit='kg'),
        Inventory(inventory_name='Butter', quantity=25.0, unit='kg'),
        Inventory(inventory_name='Salt', quantity=60.0, unit='kg'),
        Inventory(inventory_name='Pepper', quantity=20.0, unit='kg'),
        Inventory(inventory_name='Olive Oil', quantity=50.0, unit='liters'),
        Inventory(inventory_name='Garlic', quantity=15.0, unit='kg'),
        Inventory(inventory_name='Onions', quantity=40.0, unit='kg'),
        Inventory(inventory_name='Carrots', quantity=35.0, unit='kg'),
        Inventory(inventory_name='Potatoes', quantity=100.0, unit='kg'),
        Inventory(inventory_name='Bacon', quantity=50.0, unit='kg'),
        Inventory(inventory_name='Mushrooms', quantity=25.0, unit='kg'),
    ]

    # Create inventory entries
    for inv in inventory_data:
        create_inventory(inv)

    # Sample menu items data
    menu_items_data = [
        MenuItem(item_name='Pancakes', price=5.0, picture_link='link_to_pancakes', description='Fluffy pancakes.', category='Brunch/Breakfast'),
        MenuItem(item_name='Spaghetti Carbonara', price=12.0, picture_link='link_to_spaghetti', description='Classic Italian pasta.', category='Italian'),
        MenuItem(item_name='Chicken Salad', price=8.0, picture_link='link_to_salad', description='Healthy chicken salad.', category='Main Courses'),
        MenuItem(item_name='Beef Burger', price=10.0, picture_link='link_to_burger', description='Juicy beef burger.', category='Main Courses'),
        MenuItem(item_name='Chocolate Cake', price=4.5, picture_link='link_to_cake', description='Delicious chocolate cake.', category='Dessert'),
        MenuItem(item_name='Garlic Bread', price=3.0, picture_link='link_to_garlic_bread', description='Crispy garlic bread.', category='Sides'),
        MenuItem(item_name='Caesar Salad', price=7.0, picture_link='link_to_caesar_salad', description='Fresh Caesar salad.', category='Sides'),
        MenuItem(item_name='Grilled Chicken', price=15.0, picture_link='link_to_grilled_chicken', description='Grilled chicken with herbs.', category='Main Courses'),
        MenuItem(item_name='Vegetable Stir Fry', price=9.0, picture_link='link_to_stir_fry', description='Mixed vegetable stir fry.', category='Vegan'),
        MenuItem(item_name='Fish and Chips', price=11.0, picture_link='link_to_fish_and_chips', description='Classic fish and chips.', category='Main Courses'),
    ]

    # Create menu items
    for items in menu_items_data:
        create_item(items)

    # Sample item ingredients data
    item_ingredients_data = [
        # Pancakes
        ItemIngredient(item_id=1, inventory_id=1, quantity=0.2),  # Flour
        ItemIngredient(item_id=1, inventory_id=3, quantity=2),  # Eggs
        ItemIngredient(item_id=1, inventory_id=2, quantity=0.5),  # Milk
        # Spaghetti Carbonara
        ItemIngredient(item_id=2, inventory_id=9, quantity=0.3),  # Beef
        ItemIngredient(item_id=2, inventory_id=7, quantity=0.1),  # Tomato Sauce
        ItemIngredient(item_id=2, inventory_id=20, quantity=0.2),  # Bacon
        # Chicken Salad
        ItemIngredient(item_id=3, inventory_id=5, quantity=0.25),  # Chicken
        ItemIngredient(item_id=3, inventory_id=6, quantity=0.1),  # Lettuce
        ItemIngredient(item_id=3, inventory_id=16, quantity=0.05),  # Onions
        # Beef Burger
        ItemIngredient(item_id=4, inventory_id=9, quantity=0.2),  # Beef
        ItemIngredient(item_id=4, inventory_id=10, quantity=0.05),  # Cheese
        ItemIngredient(item_id=4, inventory_id=15, quantity=0.02),  # Garlic
        # Chocolate Cake
        ItemIngredient(item_id=5, inventory_id=4, quantity=0.1),  # Sugar
        ItemIngredient(item_id=5, inventory_id=2, quantity=0.3),  # Milk
        ItemIngredient(item_id=5, inventory_id=3, quantity=2),  # Eggs
        ItemIngredient(item_id=5, inventory_id=11, quantity=0.1),  # Butter
        # Garlic Bread
        ItemIngredient(item_id=6, inventory_id=1, quantity=0.1),  # Flour
        ItemIngredient(item_id=6, inventory_id=15, quantity=0.05),  # Garlic
        ItemIngredient(item_id=6, inventory_id=11, quantity=0.1),  # Butter
        # Caesar Salad
        ItemIngredient(item_id=7, inventory_id=6, quantity=0.2),  # Lettuce
        ItemIngredient(item_id=7, inventory_id=10, quantity=0.05),  # Cheese
        ItemIngredient(item_id=7, inventory_id=16, quantity=0.05),  # Onions
        # Grilled Chicken
        ItemIngredient(item_id=8, inventory_id=5, quantity=0.3),  # Chicken
        ItemIngredient(item_id=8, inventory_id=14, quantity=0.05),  # Olive Oil
        ItemIngredient(item_id=8, inventory_id=15, quantity=0.02),  # Garlic
        # Vegetable Stir Fry
        ItemIngredient(item_id=9, inventory_id=17, quantity=0.2),  # Carrots
        ItemIngredient(item_id=9, inventory_id=18, quantity=0.2),  # Potatoes
        ItemIngredient(item_id=9, inventory_id=19, quantity=0.1),  # Mushrooms
        ItemIngredient(item_id=9, inventory_id=14, quantity=0.05),  # Olive Oil
        # Fish and Chips
        ItemIngredient(item_id=10, inventory_id=18, quantity=0.3),  # Potatoes
        ItemIngredient(item_id=10, inventory_id=14, quantity=0.05),  # Olive Oil
        ItemIngredient(item_id=10, inventory_id=12, quantity=0.02),  # Salt
    ]

    # Create item ingredients entries
    for ing in item_ingredients_data:
        create_item_ingredient(ing)

    # Generate sample table
    tables = [
        TableNumber(status='Available'),
        TableNumber(status='Available'),
        TableNumber(status='Available'),
        TableNumber(status='Available'),
        TableNumber(status='Available'),
        TableNumber(status='Available'),
        TableNumber(status='Available'),
        TableNumber(status='Available'),
    ]

    session.add_all(tables)
    session.commit()



def create_test_vouchers():
        vouchers = [
            {
                "voucher_code": "DISCOUNT10",
                "voucher_type": "percentage discount",
                "description": "10% off on all items",
                "discount_value": 0.10,
                "expiry_date": datetime(2024, 10, 30).date(),
                "begin_date": datetime(2025, 1, 1).date(),
                "required_points": 100,
                "usage_limit": 100,
                "applicable_item_id": None,
                "requirement_time": time(0, 0),
                "minimum_spend": 50,
                "capped_amount": 20
            },
            {
                "voucher_code": "FIXED5",
                "voucher_type": "fixed amount discount",
                "description": "$5 off on orders above $20",
                "discount_value": 5,
                "expiry_date": datetime(2024, 10, 30).date(),
                "begin_date": datetime(2025, 1, 1).date(),
                "required_points": 50,
                "usage_limit": 50,
                "applicable_item_id": None,
                "requirement_time": time(0, 0),
                "minimum_spend": 20,
                "capped_amount": None
            },
            {
                "voucher_code": "FREEITEM",
                "voucher_type": "free item",
                "description": "Get a free item with your order",
                "discount_value": 0,
                "expiry_date": datetime(2024, 10, 30).date(),
                "begin_date": datetime(2025, 1, 1).date(),
                "required_points": 200,
                "usage_limit": 10,
                "applicable_item_id": 1,  # Assuming item with ID 1 exists
                "requirement_time": time(0, 0),
                "minimum_spend": 0,
                "capped_amount": None
            }
        ]

        for voucher_data in vouchers:
            voucher = VoucherBase(
                voucher_code=voucher_data["voucher_code"],
                voucher_type=voucher_data["voucher_type"],
                description=voucher_data["description"],
                discount_value=voucher_data["discount_value"],
                expiry_date=voucher_data["expiry_date"],
                begin_date=voucher_data["begin_date"],
                required_points=voucher_data["required_points"],
                usage_limit=voucher_data["usage_limit"]
            )
            voucher_requirement = VoucherRequirementBase(
                applicable_item_id=voucher_data["applicable_item_id"],
                requirement_time=voucher_data["requirement_time"],
                minimum_spend=voucher_data["minimum_spend"],
                capped_amount=voucher_data["capped_amount"]
            )
            create_voucher(voucher, voucher_requirement)

# create_test_vouchers()
# Call the function to populate the database with test data
# generate_test_data()
# test_signup_manager()
# test_signup()


def test_remove_sk():
   
    sk_list = session.query(SessionKey).filter_by(user_id=1).all()
    for sk in sk_list:
        session.delete(sk)
    session.commit()

# test_remove_sk()
