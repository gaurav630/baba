import hashlib
import re
from sqlalchemy.orm import Session
from .models import User, UserRole, Permission, Tab, Role, get_db, role_permissions, user_tab_access, SessionLocal
from datetime import datetime

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def authenticate_user(username_or_email, password):
    """Authenticate user credentials using username or email"""
    db = SessionLocal()
    try:
        # For root user, bypass approval check
        if username_or_email == "root":
            user = (db.query(User)
                   .filter(User.username == username_or_email)
                   .first())
        else:
            user = (db.query(User)
                   .filter((User.username == username_or_email) | 
                          (User.email == username_or_email))
                   .filter(User.is_active == True)
                   .filter(User.is_approved == True)
                   .first())

        if user and user.password == hash_password(password):
            # Update last login time
            user.last_login = datetime.utcnow()
            db.commit()
            # Keep the session open for this user
            db.refresh(user)
            return True, user
        return False, None
    except Exception as e:
        db.rollback()
        print(f"Authentication error: {str(e)}")
        return False, None
    finally:
        db.close()

def create_user(username, email, password, first_name="", last_name="", role=UserRole.VIEWER):
    """Create new user"""
    if not is_valid_email(email):
        return False, "Invalid email format"

    db = SessionLocal()
    try:
        # Check if username or email already exists
        if db.query(User).filter(User.username == username).first():
            return False, "Username already exists"

        if db.query(User).filter(User.email == email).first():
            return False, "Email already exists"

        hashed_password = hash_password(password)
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            role_name=role.value,
            is_active=True if role == UserRole.SUPER_ADMIN else False,
            is_approved=True if role == UserRole.SUPER_ADMIN else False,
            created_at=datetime.utcnow()
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return True, "Registration successful" if role == UserRole.SUPER_ADMIN else "Registration successful. Waiting for admin approval."
    except Exception as e:
        db.rollback()
        print(f"User creation error: {str(e)}")
        return False, "Registration failed"
    finally:
        db.close()

def initialize_super_admin():
    """Initialize super admin user with all permissions"""
    db = SessionLocal()
    try:
        print("Checking for existing super admin...")
        super_admin = db.query(User).filter(User.role_name == UserRole.SUPER_ADMIN.value).first()
        if not super_admin:
            print("No super admin found, creating new one...")
            success, message = create_super_admin(
                username="root",
                email="gauravupadhyay630@gmail.com",
                password="lapu",
                first_name="Super",
                last_name="Admin"
            )
            if not success:
                print(f"Failed to create super admin: {message}")
            else:
                print("Super admin created successfully")
        else:
            print("Super admin already exists")
    except Exception as e:
        print(f"Error initializing super admin: {str(e)}")
    finally:
        db.close()

def create_super_admin(username, email, password, first_name="", last_name=""):
    """Create superadmin user with all permissions"""
    db = SessionLocal()
    try:
        print(f"Attempting to create super admin with username: {username}")

        # Delete existing root user if exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print("Existing root user found, deleting...")
            db.delete(existing_user)
            db.commit()

        # Create new user
        hashed_password = hash_password(password)
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            role_name=UserRole.SUPER_ADMIN.value,
            is_active=True,
            is_approved=True,
            created_at=datetime.utcnow()
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print("Super admin user created")

        # Add all permissions
        print("Adding permissions...")
        for permission in Permission:
            db.execute(
                role_permissions.insert().values(
                    role_name=UserRole.SUPER_ADMIN.value,
                    permission=permission.value
                )
            )

        # Give access to all tabs
        print("Adding tab access...")
        tabs = db.query(Tab).all()
        new_user.accessible_tabs = tabs
        db.commit()
        print("Super admin setup completed successfully")
        return True, "Super admin created successfully"
    except Exception as e:
        db.rollback()
        print(f"Super admin creation error: {str(e)}")
        return False, f"Failed to create super admin: {str(e)}"
    finally:
        db.close()

def has_permission(username, permission):
    """Check if user has specific permission"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return False

        # Super admin has all permissions
        if user.role_name == UserRole.SUPER_ADMIN.value:
            return True

        # Check role permissions
        role_perms = db.query(role_permissions).filter(
            role_permissions.c.role_name == user.role_name
        ).all()
        return any(perm.permission == permission.value for perm in role_perms)
    finally:
        db.close()

def manage_user_tabs(admin_username: str, user_id: int, tab_names: list):
    """Manage which tabs a user can access (only super admin)"""
    if not has_permission(admin_username, Permission.UPDATE):
        return False, "No permission to manage user tabs"

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return False, "User not found"

        # Clear existing tab access
        user.accessible_tabs = []

        # Add new tab access
        tabs = db.query(Tab).filter(Tab.name.in_(tab_names)).all()
        user.accessible_tabs = tabs

        db.commit()
        return True, "User tab access updated successfully"
    except Exception as e:
        db.rollback()
        return False, f"Failed to update user tab access: {str(e)}"
    finally:
        db.close()

def approve_user(admin_username: str, user_id: int):
    """Approve a user (only super admin can do this)"""
    if not has_permission(admin_username, Permission.UPDATE):
        return False, "No permission to approve users"

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return False, "User not found"

        user.is_approved = True
        user.is_active = True
        db.commit()
        return True, f"User {user.username} has been approved"
    except Exception as e:
        db.rollback()
        return False, f"Failed to approve user: {str(e)}"
    finally:
        db.close()