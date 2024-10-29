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
    __tablename__ = 'Roles'
    ID = Column(Integer, primary_key=True, autoincrement=True)
    Role_Name = Column(String, nullable=False, unique=True)
    users = relationship('User', back_populates='role')


class User(Base):
    __tablename__ = 'UserData'
    UID = Column(Integer, primary_key=True, autoincrement=True)
    Username = Column(String, nullable=False, unique=False)
    Email = Column(String, nullable=False, unique=True)
    Role_id = Column(Integer, ForeignKey('Roles.ID'))
    Points = Column(Integer, default=0)
    role = relationship('Role', back_populates='users')
    credentials = relationship('Credentials', back_populates='user', uselist=False)
    session_keys = relationship('SessionKey', back_populates='user')
    shopping_cart = relationship('ShoppingCart', back_populates='user')
    order = relationship('Order', back_populates='user')
    user_voucher = relationship('UserVoucher', back_populates='user')
    user_item_rating = relationship('UserItemRating', back_populates='user')
    user_overall_rating = relationship('UserOverallFeedback', back_populates='user')


class Credentials(Base):
    __tablename__ = 'Credentials'
    UID = Column(Integer, ForeignKey('UserData.UID'), primary_key=True)
    Password_hash = Column(String, nullable=False)
    user = relationship('User', back_populates='credentials')


class SessionKey(Base):
    __tablename__ = 'sessionKey'
    Session_Key = Column(String, primary_key=True)
    UID = Column(Integer, ForeignKey('UserData.UID'), primary_key=True)
    user = relationship('User', back_populates='session_keys')


class Inventory(Base):
    __tablename__ = 'inventory'
    Inventory_id = Column(Integer, primary_key=True, autoincrement=True)
    Inventory_name = Column(String, nullable=False, unique=True)
    Quantity = Column(Float, nullable=False)
    Unit = Column(String, nullable=True)
    item_ingredient = relationship('Item_ingredients', back_populates='inventory')  
    batch = relationship('InventoryBatch', back_populates='inventory')
    package = relationship('BatchPackage', back_populates='inventory')


class InventoryBatch(Base):
    __tablename__ = 'inventory_batch'
    Batch_id = Column(Integer, primary_key=True)
    Inventory_id = Column(Integer, ForeignKey('inventory.Inventory_id'), primary_key=True)
    No_of_Package = Column(Integer,nullable=False)
    Quantity_per_package = Column(Float, nullable=False)
    Acquisition_date = Column(DateTime, default= datetime.now(timezone.utc))
    Expiration_date = Column(DateTime,nullable = False)
    Cost = Column(Float, nullable=False)
    Cost_per_unit = Column(Float, nullable=False)
    inventory = relationship('Inventory', back_populates='batch')
    package = relationship('BatchPackage', back_populates='batch')

class BatchPackage(Base):
    __tablename__ = 'package'
    Package_id = Column(Integer, primary_key=True, autoincrement=True)
    Batch_id = Column(Integer,ForeignKey('inventory_batch.Batch_id'))
    Inventory_id = Column(Integer, ForeignKey('inventory.Inventory_id'))
    Status = Column(Enum('New','In use','Finished',name='category_enum'), nullable=False)
    batch = relationship('InventoryBatch',back_populates='package')
    inventory = relationship('Inventory', back_populates='package')


class Menu_items(Base):
    __tablename__ = 'MenuItems'  
    Item_id = Column(Integer, primary_key=True, autoincrement=True)
    Item_name = Column(String, nullable=False, unique=True)
    Price = Column(Float, nullable=False)
    Picture_link = Column(String)
    Description = Column(String)
    Ratings = Column(Float, nullable=True)
    Category = Column(Enum('All','Brunch/Breakfast','Rice','Noodle','Italian','Main Courses','Sides','Signature Dishes','Vegan','Dessert','Beverages',name='category_enum'), nullable=False)
    item_ingredients = relationship('Item_ingredients', back_populates='menu_item') 
    cart_items = relationship('CartItem', back_populates='item')
    user_item_rating = relationship('UserItemRating', back_populates='item')


class Item_ingredients(Base):
    __tablename__ = 'ItemIngredients'
    Item_id = Column(Integer, ForeignKey('MenuItems.Item_id'), primary_key=True)
    Inventory_id = Column(Integer, ForeignKey('inventory.Inventory_id'), primary_key=True)
    quantity = Column(Float, nullable=False)
    
    menu_item = relationship('Menu_items', back_populates='item_ingredients')
    inventory = relationship('Inventory', back_populates='item_ingredient')

class TableNumber(Base):
    __tablename__ = 'TableNumber'
    Table_id = Column(Integer, primary_key=True, autoincrement=True)
    Status = Column(Enum('Occupied','Available','Reserved'), default='Available')
    shopping_cart = relationship('ShoppingCart', back_populates='table_number')
    order = relationship('Order', back_populates='table_number')

class ShoppingCart(Base):
    __tablename__ = 'ShoppingCart'
    Cart_id = Column(Integer, primary_key=True, autoincrement=True)
    UID = Column(Integer, ForeignKey('UserData.UID'), nullable=False)
    Table_id = Column(Integer, ForeignKey('TableNumber.Table_id'), nullable=True)
    Creation_time = Column(DateTime, default= datetime.now(timezone.utc))
    VoucherApplied = Column(Integer, ForeignKey('voucher.voucher_code'), nullable=True)
    Subtotal = Column(Float, nullable=False)
    ServiceCharge = Column(Float, nullable=False)
    ServiceTax = Column(Float, nullable=False)
    RoundingAdjustment = Column(Float, nullable=False)
    NetTotal = Column(Float, nullable=False)
    Status = Column(Enum('Active','Expired','Submitted'), default='Active')
    LastUpdate = Column(DateTime)
    table_number = relationship('TableNumber', back_populates='shopping_cart')
    user = relationship('User', back_populates='shopping_cart')
    voucher = relationship('Voucher', back_populates='shopping_cart')
    cart_items = relationship('CartItem', back_populates='cart')
    order = relationship('Order', back_populates='shopping_cart')

class CartItem(Base):
    __tablename__ = 'CartItems'
    Item_id = Column(Integer, ForeignKey('MenuItems.Item_id'),primary_key=True)
    Cart_id = Column(Integer, ForeignKey('ShoppingCart.Cart_id'), primary_key=True)
    Item_Name = Column(String, nullable=False)
    Quantity = Column(Integer, nullable=False)
    Remarks = Column(String, nullable=True)
    Price = Column(Float, nullable=False)
    Added_time = Column(DateTime, default= datetime.now(timezone.utc))
    item = relationship('Menu_items', back_populates='cart_items')
    cart = relationship('ShoppingCart', back_populates='cart_items')
    

class Order(Base):
    __tablename__ = 'Orders'
    Order_id = Column(Integer, primary_key=True, autoincrement=True)
    UID = Column(Integer, ForeignKey('UserData.UID'), nullable=False)
    Table_id = Column(Integer, ForeignKey('TableNumber.Table_id'), nullable=True)
    Time_Placed = Column(DateTime, default= datetime.now(timezone.utc))
    VoucherApplied = Column(Integer, ForeignKey('voucher.voucher_id'), nullable=True)
    Subtotal = Column(Float,ForeignKey('ShoppingCart.Subtotal'), nullable=False)
    ServiceCharge = Column(Float,nullable=False)
    ServiceTax = Column(Float,nullable=False)
    RoundinfAdjustment = Column(Float,nullable=False)
    NetTotal = Column(Float,nullable=False)
    PayingMethod = Column(Enum('Not Paid Yet','Cash','Credit Card','Debit Card','E-Wallet'), default='Not Paid Yet', nullable=False)
    table_number = relationship('TableNumber', back_populates='order')
    user = relationship('User', back_populates='order')
    order_items = relationship('OrderItem', back_populates='order')
    shopping_cart = relationship('ShoppingCart', back_populates='order')
    user_item_rating = relationship('UserItemRating', back_populates='order')


class OrderItem(Base):
    __tablename__ = 'OrderItems'
    Item_id = Column(Integer, ForeignKey('MenuItems.Item_id'),primary_key=True)
    Order_id = Column(Integer, ForeignKey('Orders.Order_id'), nullable=False)
    Item_Name = Column(String, nullable=False)
    Quantity = Column(Integer, nullable=False)
    Remarks = Column(String, nullable=True)
    Status = Column(Enum('Order Received','In Progress','Served','Cancelled'), default='Order Received')
    order = relationship("Order", back_populates="order_items")

class Voucher(Base):
    __tablename__ = 'voucher'
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
    __tablename__ = 'voucher_requirement'
    voucher_id = Column(Integer, ForeignKey('voucher.voucher_id'), primary_key=True)
    applicable_item_id = Column(Integer, nullable=True)
    requirement_time = Column(Time, nullable=True)
    minimum_spend = Column(Float, nullable=True)
    capped_amount = Column(Float, nullable=True)
    voucher = relationship('Voucher', back_populates='requirement')

class UserVoucher(Base):
    __tablename__= 'user_voucher'
    UID = Column(Integer, ForeignKey('UserData.UID'), primary_key=True)
    voucher_id = Column(Integer, ForeignKey('voucher.voucher_id'), primary_key=True)
    use_date = Column(DateTime)
    user = relationship('User', back_populates='user_voucher')
    voucher = relationship('Voucher', back_populates='user_voucher')

class UserItemRating(Base):
    __tablename__ = 'user_item_rating'
    Order_id = Column(Integer, ForeignKey('Orders.Order_id'), primary_key=True)
    UID = Column(Integer, ForeignKey('UserData.UID'), primary_key=True)
    Item_id = Column(Integer, ForeignKey('MenuItems.Item_id'), primary_key=True)
    Rating = Column(Integer, nullable=False)
    Description = Column(String, nullable=True)
    order = relationship('Order', back_populates='user_item_rating')
    user = relationship('User', back_populates='user_item_rating')
    item = relationship('Menu_items', back_populates='user_item_rating')


class UserOverallFeedback(Base):
    __tablename__ = 'user_overall_rating'
    UID = Column(Integer, ForeignKey('UserData.UID'), primary_key=True)
    Overall_Rating = Column(Integer, nullable=False)
    Description = Column(String, nullable=True)
    user = relationship('User', back_populates='user_overall_rating')

class Machines(Base):
    __tablename__ = 'machines'
    machine_id = Column(Integer, primary_key=True, autoincrement=True)
    machine_name = Column(String, nullable=False)
    machine_type = Column(String, nullable=False)
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
            role = Role(Role_Name=role_name)
            session.add(role)
            session.commit()  
        except IntegrityError:
            session.rollback()  
    session.close()  


add_roles()  