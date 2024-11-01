from sqlalchemy import create_engine, Column,Boolean, String, Integer, Float, ForeignKey, Enum, Date, Time, DateTime
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import timezone,timedelta, datetime


# Database setup
sqlalchemy_db_url = 'sqlite:///./UserData.db'
engine = create_engine(sqlalchemy_db_url, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()
Base = declarative_base()


# Models
class Role(Base):
    __tablename__ = 'Role'
    role_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    users = relationship('User', back_populates='role')


class User(Base):
    __tablename__ = 'UserData'
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=True, unique=False)
    email = Column(String, nullable=True, unique=True)
    role_id = Column(Integer, ForeignKey('Role.role_id'))
    points = Column(Integer, default=0)
    is_guest = Column(Boolean, default=False)
    created_at = Column(DateTime, default= datetime.now(timezone.utc))
    role = relationship('Role', back_populates='users')
    credentials = relationship('Credential', back_populates='user', uselist=False)
    session_keys = relationship('SessionKey', back_populates='user')
    shopping_cart = relationship('ShoppingCart', back_populates='user')
    order = relationship('Order', back_populates='user')
    user_voucher = relationship('UserVoucher', back_populates='user')
    user_item_rating = relationship('UserItemRating', back_populates='user')
    user_overall_rating = relationship('UserOverallFeedback', back_populates='user')


class Credential(Base):
    __tablename__ = 'Credential'
    credential_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('UserData.user_id'))
    password_hash = Column(String, nullable=False)
    user = relationship('User', back_populates='credentials')


class SessionKey(Base):
    __tablename__ = 'SessionKey'
    session_key_id = Column(Integer, primary_key=True, autoincrement=True)
    session_key = Column(String)
    user_id = Column(Integer, ForeignKey('UserData.user_id'))
    user = relationship('User', back_populates='session_keys')


class Inventory(Base):
    __tablename__ = 'Inventory'
    inventory_id = Column(Integer, primary_key=True, autoincrement=True)
    inventory_name = Column(String, nullable=False, unique=True)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=True)
    item_ingredient = relationship('ItemIngredient', back_populates='inventory')  
    batch = relationship('InventoryBatch', back_populates='inventory')


class InventoryBatch(Base):
    __tablename__ = 'InventoryBatch'
    batch_id = Column(Integer, primary_key=True, autoincrement=True)
    inventory_id = Column(Integer, ForeignKey('Inventory.inventory_id'))
    no_of_package = Column(Integer,nullable=False)
    quantity_per_package = Column(Float, nullable=False)
    acquisition_date = Column(DateTime, default= datetime.now(timezone.utc))
    expiration_date = Column(DateTime,nullable = False)
    cost = Column(Float, nullable=False)
    cost_per_unit = Column(Float, nullable=False)
    status = Column(Enum('New','In use','Finished',name='batch_status_enum'), nullable=False, default='New')
    inventory = relationship('Inventory', back_populates='batch')


class MenuItem(Base):
    __tablename__ = 'MenuItem'  
    item_id = Column(Integer, primary_key=True, autoincrement=True)
    item_name = Column(String, nullable=False, unique=True)
    price = Column(Float, nullable=False)
    picture_link = Column(String)
    description = Column(String)
    ratings = Column(Float, nullable=True)
    category = Column(Enum('All','Brunch/Breakfast','Rice','Noodle','Italian','Main Courses','Sides','Signature Dishes','Vegan','Dessert','Beverages',name='category_enum'), nullable=False)
    item_ingredients = relationship('ItemIngredient', back_populates='menu_item') 
    cart_items = relationship('CartItem', back_populates='item')
    user_item_rating = relationship('UserItemRating', back_populates='item')
    is_deleted = Column(Boolean, default=False)


class ItemIngredient(Base):
    __tablename__ = 'ItemIngredient'
    item_id = Column(Integer, ForeignKey('MenuItem.item_id'), primary_key=True)
    inventory_id = Column(Integer, ForeignKey('Inventory.inventory_id'), primary_key=True)
    quantity = Column(Float, nullable=False)
    
    menu_item = relationship('MenuItem', back_populates='item_ingredients')
    inventory = relationship('Inventory', back_populates='item_ingredient')

class TableNumber(Base):
    __tablename__ = 'TableNumber'
    table_id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(Enum('Occupied','Available','Reserved'), default='Available')
    shopping_cart = relationship('ShoppingCart', back_populates='table_number')
    order = relationship('Order', back_populates='table_number')

class ShoppingCart(Base):
    __tablename__ = 'ShoppingCart'
    user_id = Column(Integer, ForeignKey('UserData.user_id'), nullable=False)
    cart_id = Column(Integer, primary_key=True, autoincrement=True)
    table_id = Column(Integer, ForeignKey('TableNumber.table_id'), nullable=True)
    creation_time = Column(DateTime, default= datetime.now(timezone.utc))
    voucher_applied = Column(Integer, ForeignKey('Voucher.voucher_code'), nullable=True)
    subtotal = Column(Float, nullable=False)
    service_charge = Column(Float, nullable=False)
    service_tax = Column(Float, nullable=False)
    rounding_adjustment = Column(Float, nullable=False)
    net_total = Column(Float, nullable=False)
    status = Column(Enum('Active','Expired','Submitted'), default='Active')
    last_update = Column(DateTime)
    table_number = relationship('TableNumber', back_populates='shopping_cart')
    user = relationship('User', back_populates='shopping_cart')
    voucher = relationship('Voucher', back_populates='shopping_cart')
    cart_items = relationship('CartItem', back_populates='cart')
    order = relationship('Order', back_populates='shopping_cart')

class CartItem(Base):
    __tablename__ = 'CartItem'
    item_id = Column(Integer, ForeignKey('MenuItem.item_id'),primary_key=True)
    cart_id = Column(Integer, ForeignKey('ShoppingCart.cart_id'), primary_key=True)
    item_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    remarks = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    added_time = Column(DateTime, default= datetime.now(timezone.utc))
    item = relationship('MenuItem', back_populates='cart_items')
    cart = relationship('ShoppingCart', back_populates='cart_items')
    

class Order(Base):
    __tablename__ = 'Order'
    order_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('UserData.user_id'), nullable=False)
    table_id = Column(Integer, ForeignKey('TableNumber.table_id'), nullable=False)
    cart_id = Column(Integer, ForeignKey('ShoppingCart.cart_id'), nullable=False)
    time_placed = Column(DateTime, default= datetime.now(timezone.utc))
    # voucher_applied = Column(String, ForeignKey('Voucher.voucher_code'), nullable=True)
    user_voucher_id = Column(Integer, ForeignKey('UserVoucher.user_voucher_id'), nullable=True)
    user_voucher = relationship('UserVoucher', back_populates='order')
    subtotal = Column(Float, nullable=False)
    service_charge = Column(Float,nullable=False)
    service_tax = Column(Float,nullable=False)
    rounding_adjustment = Column(Float,nullable=False)
    net_total = Column(Float,nullable=False)
    paying_method = Column(Enum('Not Paid Yet','Cash','Credit Card','Debit Card','E-Wallet'), default='Not Paid Yet', nullable=False)
    is_cancelled = Column(Boolean, default=False)
    table_number = relationship('TableNumber', back_populates='order')
    user = relationship('User', back_populates='order')
    order_items = relationship('OrderItem', back_populates='order')
    shopping_cart = relationship('ShoppingCart', back_populates='order')
    user_item_rating = relationship('UserItemRating', back_populates='order')


class OrderItem(Base):
    __tablename__ = 'OrderItem'
    order_item_id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey('MenuItem.item_id'), nullable=False)
    order_id = Column(Integer, ForeignKey('Order.order_id'), nullable=False)
    item_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    remarks = Column(String, nullable=True)
    status = Column(Enum('Order Received','In Progress','Served','Cancelled'), default='Order Received')
    order = relationship("Order", back_populates="order_items")

class Voucher(Base):
    __tablename__ = 'Voucher'
    voucher_id = Column(Integer, primary_key=True)
    voucher_code = Column(String, nullable=False, unique=True)  
    voucher_type = Column(Enum('percentage discount','fixed amount discount','free item'), nullable=False)
    description = Column(String, nullable=False)
    discount_value = Column(Float, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    begin_date = Column(DateTime, nullable=True)
    required_points = Column(Integer, nullable=True)
    usage_limit = Column(Integer)
    shopping_cart = relationship('ShoppingCart', back_populates='voucher')
    requirement = relationship('VoucherRequirement', back_populates= 'voucher')
    user_voucher = relationship('UserVoucher', back_populates='voucher')

class VoucherRequirement(Base):
    __tablename__ = 'VoucherRequirement'
    voucher_id = Column(Integer, ForeignKey('Voucher.voucher_id'), primary_key=True)
    applicable_item_id = Column(Integer, nullable=True)
    requirement_time = Column(Time, nullable=True)
    minimum_spend = Column(Float, nullable=True)
    capped_amount = Column(Float, nullable=True)
    voucher = relationship('Voucher', back_populates='requirement')

class UserVoucher(Base):
    __tablename__= 'UserVoucher'
    user_voucher_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('UserData.user_id'), nullable=False)
    voucher_id = Column(Integer, ForeignKey('Voucher.voucher_id'), nullable=False)
    use_date = Column(DateTime)
    user = relationship('User', back_populates='user_voucher')
    voucher = relationship('Voucher', back_populates='user_voucher')
    order = relationship('Order', back_populates='user_voucher')

class UserItemRating(Base):
    __tablename__ = 'UserItemRating'
    order_id = Column(Integer, ForeignKey('Order.order_id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('UserData.user_id'), primary_key=True)
    item_id = Column(Integer, ForeignKey('MenuItem.item_id'), primary_key=True)
    rating = Column(Integer, nullable=False)
    description = Column(String, nullable=True)
    order = relationship('Order', back_populates='user_item_rating')
    user = relationship('User', back_populates='user_item_rating')
    item = relationship('MenuItem', back_populates='user_item_rating')


class UserOverallFeedback(Base):
    __tablename__ = 'UserOverallFeedback'
    user_id = Column(Integer, ForeignKey('UserData.user_id'), primary_key=True)
    order_id = Column(Integer, ForeignKey('Order.order_id'), primary_key=True)
    overall_rating = Column(Integer, nullable=False)
    description = Column(String, nullable=True)
    user = relationship('User', back_populates='user_overall_rating')

class Machine(Base):
    __tablename__ = 'Machine'
    machine_id = Column(Integer, primary_key=True, autoincrement=True)
    machine_name = Column(String, nullable=False)
    machine_type = Column(String, nullable=False)
    acquisition_date = Column(DateTime, default= datetime.now(timezone.utc))
    machine_status = Column(Enum('Available','Under maintenance'), default='Available')
    cost = Column(Float, nullable=False)
    maintenance_required = Column(Boolean, default=False)
    issue_description = Column(String, nullable=True)
    last_maintenance = Column(DateTime, nullable=True)

## for cashier: add sales and expenses, add cost in inventory if needed

# create all tables in the database
Base.metadata.create_all(bind=engine)

# add initial roles to the Roles table
def add_roles():
    roles = ["customer", "cashier", "chef", "manager"]
    session = SessionLocal() 
    for role_name in roles:
        try:
            role = Role(name=role_name)
            session.add(role)
            session.commit()  
        except IntegrityError:
            session.rollback()  
    session.close()  


add_roles()  