from sqlalchemy import create_engine, Column, String, Integer, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.exc import IntegrityError


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


class Credentials(Base):
    __tablename__ = 'Credentials'
    UID = Column(Integer, ForeignKey('UserData.UID'), primary_key=True)
    Password_hash = Column(String, nullable=False)
    user = relationship('User', back_populates='credentials')


class SessionKey(Base):
    __tablename__ = 'SessionKey'
    Session_Key = Column(String, primary_key=True)
    UID = Column(Integer, ForeignKey('UserData.UID'), primary_key=True)
    user = relationship('User', back_populates='session_keys')


# Create all tables in the database
Base.metadata.create_all(bind=engine)

# Add initial roles to the Roles table
def add_roles():
    roles = ["customer", "cashier", "chef", "manager"]
    session = SessionLocal()  # Creating a session inside the function
    for role_name in roles:
        try:
            role = Role(Role_Name=role_name)
            session.add(role)
            session.commit()  # Commit each role addition
        except IntegrityError:
            session.rollback()  # Rollback if the role already exists
    session.close()  # Close the session after adding roles


add_roles()  # Call the function to add initial roles



