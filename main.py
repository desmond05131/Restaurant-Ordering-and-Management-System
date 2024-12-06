from datetime import datetime, time
from fastapi import FastAPI, status, Depends, HTTPException
from typing import Annotated
from root.database.database_models import MenuItem,Machine, Inventory, ItemIngredient,InventoryBatch, SessionKey, SessionLocal, TableNumber, session, Order, OrderItem
from root.account.account import sign_up, try_sign_up,login_for_session_key, logout, verify_login, create_account, CreateAccountDetails, get_UID_by_email
from root.components.inventory_management import create_inventory, create_item, create_item_ingredient, recalculate_inventory_quantities, check_inventory_levels
from root.components.voucher import create_voucher
# from root.components.order_management import create_order, create_order_item
# from root.components.customer_feedback import create_user_item_rating
# from root.components.machines import create_machine, create_machine_ingredient
from api import app
from root.schemas.voucher import VoucherBase, VoucherRequirementBase
# from fastapi_utils.tasks import repeat_every
# from asyncio import thr


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
                "expiry_date": datetime(2024, 11, 30).date(),
                "begin_date": datetime(2024, 1, 1).date(),
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
                "expiry_date": datetime(2024, 11, 30).date(),
                "begin_date": datetime(2024, 1, 1).date(),
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
                "expiry_date": datetime(2024, 11, 30).date(),
                "begin_date": datetime(2024, 1, 1).date(),
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


def generate_test_orders():
                orders_data = [
                    {
                        "order_id": 1,
                        "user_id": 1,
                        "table_id": 1,
                        "cart_id": 1,
                        "time_placed": datetime(2023, 11, 2, 12, 0),
                        "user_voucher_id": None,
                        "subtotal": 50.0,
                        "service_charge": 5.0,
                        "service_tax": 2.5,
                        "rounding_adjustment": 0.0,
                        "net_total": 57.5,
                        "paying_method": "Credit Card"
                    },
                    {
                        "order_id": 2,
                        "user_id": 1,
                        "table_id": 1,
                        "cart_id": 1,
                        "time_placed": datetime(2023, 11, 3, 12, 0),
                        "user_voucher_id": None,
                        "subtotal": 50.0,
                        "service_charge": 5.0,
                        "service_tax": 2.5,
                        "rounding_adjustment": 0.0,
                        "net_total": 57.5,
                        "paying_method": "Credit Card"
                    },
                    {
                        "order_id": 3,
                        "user_id": 2,
                        "table_id": 2,
                        "cart_id": 2,
                        "time_placed": datetime(2023, 11, 4, 15, 24),
                        "user_voucher_id": 1,
                        "subtotal": 30.0,
                        "service_charge": 3.0,
                        "service_tax": 1.5,
                        "rounding_adjustment": 0.0,
                        "net_total": 34.5,
                        "paying_method": "Cash"
                    },
                    {
                        "order_id": 4,
                        "user_id": 1,
                        "table_id": 3,
                        "cart_id": 3,
                        "time_placed": datetime(2023, 10, 1, 12, 0),
                        "user_voucher_id": 2,
                        "subtotal": 20.0,
                        "service_charge": 2.0,
                        "service_tax": 1.0,
                        "rounding_adjustment": 0.0,
                        "net_total": 23.0,
                        "paying_method": "Debit Card"
                    },
                    {
                        "order_id": 5,
                        "user_id": 1,
                        "table_id": 1,
                        "cart_id": 1,
                        "time_placed": datetime(2024, 10, 2, 13, 0),
                        "user_voucher_id": None,
                        "subtotal": 50.0,
                        "service_charge": 5.0,
                        "service_tax": 2.5,
                        "rounding_adjustment": 0.0,
                        "net_total": 57.5,
                        "paying_method": "Credit Card"
                    },
                    {
                        "order_id": 6,
                        "user_id": 2,
                        "table_id": 2,
                        "cart_id": 2,
                        "time_placed": datetime(2024, 10, 3, 14, 0),
                        "user_voucher_id": 1,
                        "subtotal": 30.0,
                        "service_charge": 3.0,
                        "service_tax": 1.5,
                        "rounding_adjustment": 0.0,
                        "net_total": 34.5,
                        "paying_method": "Cash"
                    },
                    {
                        "order_id": 7,
                        "user_id": 1,
                        "table_id": 3,
                        "cart_id": 3,
                        "time_placed": datetime(2024, 10, 1, 14, 0),
                        "user_voucher_id": 2,
                        "subtotal": 20.0,
                        "service_charge": 2.0,
                        "service_tax": 1.0,
                        "rounding_adjustment": 0.0,
                        "net_total": 23.0,
                        "paying_method": "Debit Card"
                    },
                    {
                        "order_id": 8,
                        "user_id": 1,
                        "table_id": 1,
                        "cart_id": 1,
                        "time_placed": datetime(2024, 10, 2, 12, 0),
                        "user_voucher_id": None,
                        "subtotal": 50.0,
                        "service_charge": 5.0,
                        "service_tax": 2.5,
                        "rounding_adjustment": 0.0,
                        "net_total": 57.5,
                        "paying_method": "Credit Card"
                    },
                    {
                        "order_id": 9,
                        "user_id": 1,
                        "table_id": 3,
                        "cart_id": 3,
                        "time_placed": datetime(2024, 10, 3, 14, 0),
                        "user_voucher_id": 2,
                        "subtotal": 20.0,
                        "service_charge": 2.0,
                        "service_tax": 1.0,
                        "rounding_adjustment": 0.0,
                        "net_total": 23.0,
                        "paying_method": "Debit Card"
                    },
                    {
                        "order_id": 10,
                        "user_id": 1,
                        "table_id": 1,
                        "cart_id": 1,
                        "time_placed": datetime(2024, 9, 1, 12, 0),
                        "user_voucher_id": None,
                        "subtotal": 50.0,
                        "service_charge": 5.0,
                        "service_tax": 2.5,
                        "rounding_adjustment": 0.0,
                        "net_total": 57.5,
                        "paying_method": "Credit Card"
                    },
                    {
                        "order_id": 11,
                        "user_id": 2,
                        "table_id": 2,
                        "cart_id": 2,
                        "time_placed": datetime(2024, 9, 2, 13, 0),
                        "user_voucher_id": 1,
                        "subtotal": 30.0,
                        "service_charge": 3.0,
                        "service_tax": 1.5,
                        "rounding_adjustment": 0.0,
                        "net_total": 34.5,
                        "paying_method": "Cash"
                    },
                    {
                        "order_id": 12,
                        "user_id": 1,
                        "table_id": 3,
                        "cart_id": 3,
                        "time_placed": datetime(2024, 9, 3, 14, 0),
                        "user_voucher_id": 2,
                        "subtotal": 20.0,
                        "service_charge": 2.0,
                        "service_tax": 1.0,
                        "rounding_adjustment": 0.0,
                        "net_total": 23.0,
                        "paying_method": "Debit Card"
                    },
                    {
                        "order_id": 13,
                        "user_id": 1,
                        "table_id": 1,
                        "cart_id": 1,
                        "time_placed": datetime(2024, 10, 11, 12, 0),
                        "user_voucher_id": None,
                        "subtotal": 50.0,
                        "service_charge": 5.0,
                        "service_tax": 2.5,
                        "rounding_adjustment": 0.0,
                        "net_total": 57.5,
                        "paying_method": "Credit Card"
                    },
                    {
                        "order_id": 14,
                        "user_id": 2,
                        "table_id": 2,
                        "cart_id": 2,
                        "time_placed": datetime(2024, 10, 12, 13, 0),
                        "user_voucher_id": 1,
                        "subtotal": 30.0,
                        "service_charge": 3.0,
                        "service_tax": 1.5,
                        "rounding_adjustment": 0.0,
                        "net_total": 34.5,
                        "paying_method": "Cash"
                    },
                    {
                        "order_id": 15,
                        "user_id": 1,
                        "table_id": 3,
                        "cart_id": 3,
                        "time_placed": datetime(2024, 10, 31, 14, 0),
                        "user_voucher_id": 2,
                        "subtotal": 20.0,
                        "service_charge": 2.0,
                        "service_tax": 1.0,
                        "rounding_adjustment": 0.0,
                        "net_total": 23.0,
                        "paying_method": "Debit Card"
                    },
                    {
                        "order_id": 16,
                        "user_id": 1,
                        "table_id": 1,
                        "cart_id": 1,
                        "time_placed": datetime(2024, 10, 31, 12, 0),
                        "user_voucher_id": None,
                        "subtotal": 50.0,
                        "service_charge": 5.0,
                        "service_tax": 2.5,
                        "rounding_adjustment": 0.0,
                        "net_total": 57.5,
                        "paying_method": "Credit Card"
                    },
                    {
                        "order_id": 17,
                        "user_id": 2,
                        "table_id": 2,
                        "cart_id": 2,
                        "time_placed": datetime(2024, 1, 2, 13, 0),
                        "user_voucher_id": 1,
                        "subtotal": 30.0,
                        "service_charge": 3.0,
                        "service_tax": 1.5,
                        "rounding_adjustment": 0.0,
                        "net_total": 34.5,
                        "paying_method": "Cash"
                    },
                    {
                        "order_id": 18,
                        "user_id": 1,
                        "table_id": 3,
                        "cart_id": 3,
                        "time_placed": datetime(2024, 1, 3, 14, 0),
                        "user_voucher_id": 2,
                        "subtotal": 20.0,
                        "service_charge": 2.0,
                        "service_tax": 1.0,
                        "rounding_adjustment": 0.0,
                        "net_total": 23.0,
                        "paying_method": "Debit Card"
                    }
                ]

                for order_data in orders_data:
                    order = Order(
                        order_id=order_data["order_id"],
                        user_id=order_data["user_id"],
                        table_id=order_data["table_id"],
                        cart_id=order_data["cart_id"],
                        time_placed=order_data["time_placed"],
                        user_voucher_id=order_data["user_voucher_id"],
                        subtotal=order_data["subtotal"],
                        service_charge=order_data["service_charge"],
                        service_tax=order_data["service_tax"],
                        rounding_adjustment=order_data["rounding_adjustment"],
                        net_total=order_data["net_total"],
                        paying_method=order_data["paying_method"]
                    )
                    session.add(order)
                session.commit()


def generate_batch_data():
    batch_data = [
        InventoryBatch(inventory_id=11, no_of_package=5, quantity_per_package=2.0, acquisition_date=datetime(2023, 10, 1), expiration_date=datetime(2025, 1, 1), cost=100.0, cost_per_unit=10.0),
        InventoryBatch(inventory_id=12, no_of_package=10, quantity_per_package=2.0, acquisition_date=datetime(2023, 11, 2), expiration_date=datetime(2025, 1, 2), cost=200.0, cost_per_unit=10.0),
        InventoryBatch(inventory_id=13, no_of_package=15, quantity_per_package=2.0, acquisition_date=datetime(2023, 9, 3), expiration_date=datetime(2025, 1, 3), cost=300.0, cost_per_unit=10.0),
        InventoryBatch(inventory_id=14, no_of_package=20, quantity_per_package=2.0, acquisition_date=datetime(2023, 1, 4), expiration_date=datetime(2025, 1, 4), cost=400.0, cost_per_unit=10.0),
        InventoryBatch(inventory_id=15, no_of_package=25, quantity_per_package=2.0, acquisition_date=datetime(2023, 12, 5), expiration_date=datetime(2025, 1, 5), cost=500.0, cost_per_unit=10.0),
        InventoryBatch(inventory_id=16, no_of_package=30, quantity_per_package=2.0, acquisition_date=datetime(2024, 1, 6), expiration_date=datetime(2025, 1, 6), cost=600.0, cost_per_unit=10.0),
        InventoryBatch(inventory_id=17, no_of_package=35, quantity_per_package=2.0, acquisition_date=datetime(2024, 2, 7), expiration_date=datetime(2025, 1, 7), cost=700.0, cost_per_unit=10.0),
        InventoryBatch(inventory_id=18, no_of_package=40, quantity_per_package=2.0, acquisition_date=datetime(2024, 3, 8), expiration_date=datetime(2025, 1, 8), cost=800.0, cost_per_unit=10.0),
        InventoryBatch(inventory_id=19, no_of_package=45, quantity_per_package=2.0, acquisition_date=datetime(2024, 4, 9), expiration_date=datetime(2025, 1, 9), cost=900.0, cost_per_unit=10.0),
        InventoryBatch(inventory_id=20, no_of_package=50, quantity_per_package=2.0, acquisition_date=datetime(2024, 5, 10), expiration_date=datetime(2025, 1, 10), cost=1000.0, cost_per_unit=10.0),
    ]

    for batch in batch_data:
        session.add(batch)
    session.commit()

def generate_test_machine_data():
    machine_data = [
        Machine(machine_name='Espresso Machine', machine_type='Coffee Maker', acquisition_date=datetime(2023, 1, 15), machine_status='Available', cost=1500.0, maintenance_required=False, issue_description=None, last_maintenance=None),
        Machine(machine_name='Oven', machine_type='Baking', acquisition_date=datetime(2023, 3, 22), machine_status='Available', cost=3000.0, maintenance_required=False, issue_description=None, last_maintenance=None),
        Machine(machine_name='Blender', machine_type='Mixing', acquisition_date=datetime(2023, 5, 10), machine_status='Under maintenance', cost=200.0, maintenance_required=True, issue_description='Blade replacement needed', last_maintenance=datetime(2023, 10, 1)),
        Machine(machine_name='Grill', machine_type='Cooking', acquisition_date=datetime(2023, 7, 5), machine_status='Available', cost=800.0, maintenance_required=False, issue_description=None, last_maintenance=None),
        Machine(machine_name='Dishwasher', machine_type='Cleaning', acquisition_date=datetime(2023, 9, 18), machine_status='Available', cost=1200.0, maintenance_required=False, issue_description=None, last_maintenance=None),
        Machine(machine_name='Ice Cream Maker', machine_type='Dessert', acquisition_date=datetime(2023, 11, 30), machine_status='Under maintenance', cost=500.0, maintenance_required=True, issue_description='Compressor issue', last_maintenance=datetime(2024, 1, 15)),
        Machine(machine_name='Juicer', machine_type='Juicing', acquisition_date=datetime(2024, 2, 14), machine_status='Available', cost=300.0, maintenance_required=False, issue_description=None, last_maintenance=None),
        Machine(machine_name='Microwave', machine_type='Heating', acquisition_date=datetime(2024, 4, 25), machine_status='Available', cost=400.0, maintenance_required=False, issue_description=None, last_maintenance=None),
        Machine(machine_name='Refrigerator', machine_type='Cooling', acquisition_date=datetime(2024, 6, 12), machine_status='Available', cost=2500.0, maintenance_required=False, issue_description=None, last_maintenance=None),
        Machine(machine_name='Toaster', machine_type='Toasting', acquisition_date=datetime(2024, 8, 8), machine_status='Available', cost=100.0, maintenance_required=False, issue_description=None, last_maintenance=None),
    ]

    for machine in machine_data:
        session.add(machine)
    session.commit()
def test_remove_sk():
   
    sk_list = session.query(SessionKey).filter_by(user_id=1).all()
    for sk in sk_list:
        session.delete(sk)
    session.commit()

# Call the function to populate the database with test data
# create_test_vouchers()
# generate_test_data()
# test_signup_manager()
# test_signup()
# generate_test_orders()
# generate_batch_data()
# generate_test_machine_data()
# test_remove_sk()