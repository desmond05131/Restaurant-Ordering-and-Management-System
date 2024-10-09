from sqlalchemy import create_engine, Column, String, Integer, Float, ForeignKey, Enum, DateTime
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.exc import IntegrityError
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
    role = relationship('Role', back_populates='users')
    credentials = relationship('Credentials', back_populates='user', uselist=False)
    session_keys = relationship('SessionKey', back_populates='user')
    order = relationship('Order', back_populates='user')


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
    Quantity = Column(Integer, nullable=False)
    Unit = Column(String, nullable=True)
    item_ingredient = relationship('Item_ingredients', back_populates='inventory')  # Updated to match


class Menu_items(Base):
    __tablename__ = 'MenuItems'  # Consistent naming
    Item_id = Column(Integer, primary_key=True, autoincrement=True)
    Item_name = Column(String, nullable=False, unique=True)
    Price = Column(Float, nullable=False)
    Picture_link = Column(String)
    Description = Column(String)
    Category = Column(Enum('All', 'Beverage', 'Rice', 'Noodle', 'Snacks', name='category_enum'), nullable=False)
    item_ingredients = relationship('Item_ingredients', back_populates='menu_item') 
    

class Item_ingredients(Base):
    __tablename__ = 'ItemIngredients' 
    Item_id = Column(Integer, ForeignKey('MenuItems.Item_id'), primary_key=True)  
    Inventory_id = Column(Integer, ForeignKey('inventory.Inventory_id'), primary_key=True)  
    quantity = Column(Float, nullable=False)
    menu_item = relationship('Menu_items', back_populates='item_ingredients') 
    inventory = relationship('Inventory', back_populates='item_ingredient') 



class Order(Base):
    __tablename__ = 'Orders'
    Order_id = Column(Integer, primary_key=True, autoincrement=True)
    UID = Column(Integer, ForeignKey('UserData.UID'), nullable=False)
    Status = Column(Enum('In Progress','Completed','Cancelled'), default='In Progress')
    Time_Placed = Column(DateTime, default= datetime.now(timezone.utc))
    Total_Ammount = Column(Float, nullable= False)
    user = relationship('User', back_populates='order')
    order_items = relationship('OrderItem', back_populates='order')


class OrderItem(Base):
    __tablename__ = 'OrderItems'
    Item_id = Column(Integer, primary_key=True, autoincrement=True)
    Order_id = Column(Integer, ForeignKey('Orders.Order_id'), nullable=False)
    Product_Name = Column(String, nullable=False)
    Quantity = Column(Integer, nullable=False)
    order = relationship("Order", back_populates="order_items")

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



