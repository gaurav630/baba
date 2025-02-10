from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Enum, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
import enum
from datetime import datetime

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Create database engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class UserRole(enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    VIEWER = "viewer"

class Permission(enum.Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"

class TabType(enum.Enum):
    OVERVIEW = "overview"
    SALES = "sales"
    GROSS_PROFIT = "gross_profit"
    INVENTORY = "inventory"
    SHIPMENT = "shipment"

# Define tables with proper relationships
role_permissions = Table('role_permissions', Base.metadata,
    Column('role_name', String, ForeignKey('roles.name', ondelete='CASCADE')),
    Column('permission', String)
)

user_employee_access = Table('user_employee_access', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE')),
    Column('employee_id', Integer, ForeignKey('employees.id', ondelete='CASCADE'))
)

user_tab_access = Table('user_tab_access', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE')),
    Column('tab_id', Integer, ForeignKey('tabs.id', ondelete='CASCADE'))
)

class Role(Base):
    __tablename__ = "roles"
    name = Column(String, primary_key=True)
    description = Column(String)
    users = relationship("User", back_populates="role_info")

class Tab(Base):
    __tablename__ = "tabs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=False)
    data = relationship("CompanyData", back_populates="tab", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    role_name = Column(String, ForeignKey('roles.name', ondelete='CASCADE'))
    is_active = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    role_info = relationship("Role", back_populates="users")
    accessible_tabs = relationship("Tab", secondary=user_tab_access)
    accessible_employees = relationship("Employee", secondary=user_employee_access)

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    department = Column(String)
    position = Column(String)
    salary = Column(Float)
    joining_date = Column(DateTime)
    is_shared = Column(Boolean, default=False)

class CompanyData(Base):
    __tablename__ = "company_data"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, index=True)
    tab_id = Column(Integer, ForeignKey('tabs.id', ondelete='CASCADE'))
    metric_name = Column(String)
    value = Column(Float)
    notes = Column(String, nullable=True)
    tab = relationship("Tab", back_populates="data")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def initialize_roles(db):
    """Initialize available roles in the database"""
    try:
        # Check if roles already exist
        if db.query(Role).count() == 0:
            print("Initializing roles...")
            for role in UserRole:
                db.add(Role(
                    name=role.value,
                    description=role.value.replace('_', ' ').title()
                ))
            db.commit()
            print("Roles initialized successfully")
    except Exception as e:
        db.rollback()
        print(f"Error initializing roles: {str(e)}")
        raise

def initialize_tabs(db):
    """Initialize available tabs in the database"""
    try:
        # Check if tabs already exist
        if db.query(Tab).count() == 0:
            print("Initializing tabs...")
            for tab_type in TabType:
                tab = Tab(
                    name=tab_type.value,
                    display_name=tab_type.value.replace('_', ' ').title()
                )
                db.add(tab)
            db.commit()
            print("Tabs initialized successfully")
    except Exception as e:
        db.rollback()
        print(f"Error initializing tabs: {str(e)}")
        raise

def init_db():
    """Initialize database tables and data"""
    db = SessionLocal()
    try:
        print("Starting database initialization...")

        # Drop all tables first to ensure clean state
        Base.metadata.drop_all(bind=engine)
        print("Dropped existing tables")

        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("Created database tables")

        # Initialize roles and tabs
        initialize_roles(db)
        initialize_tabs(db)

        print("Database initialization completed successfully")
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise
    finally:
        db.close()