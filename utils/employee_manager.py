from datetime import datetime
from sqlalchemy.orm import Session
from .models import Employee, User, get_db
from .auth import has_permission, Permission

def create_employee(creator_username: str, employee_data: dict):
    """Create new employee record"""
    if not has_permission(creator_username, Permission.CREATE):
        return False, "No permission to create employee records"

    db = next(get_db())
    new_employee = Employee(
        name=employee_data['name'],
        email=employee_data['email'],
        department=employee_data['department'],
        position=employee_data['position'],
        salary=float(employee_data['salary']),
        joining_date=datetime.now(),
        is_shared=employee_data.get('is_shared', False)
    )
    
    try:
        db.add(new_employee)
        db.commit()
        return True, "Employee created successfully"
    except Exception as e:
        db.rollback()
        return False, f"Failed to create employee: {str(e)}"

def get_accessible_employees(username: str):
    """Get employees accessible to the user"""
    db = next(get_db())
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        return []
    
    # Super admin can see all employees
    if user.role == "super_admin":
        return db.query(Employee).all()
    
    # Others can see shared employees and their accessible employees
    return db.query(Employee).filter(
        (Employee.is_shared == True) | 
        (Employee.id.in_([emp.id for emp in user.accessible_employees]))
    ).all()

def share_employee(username: str, employee_id: int, target_username: str):
    """Share employee data with another user"""
    if not has_permission(username, Permission.UPDATE):
        return False, "No permission to share employee data"

    db = next(get_db())
    target_user = db.query(User).filter(User.username == target_username).first()
    employee = db.query(Employee).filter(Employee.id == employee_id).first()

    if not target_user or not employee:
        return False, "User or employee not found"

    try:
        target_user.accessible_employees.append(employee)
        db.commit()
        return True, f"Employee shared with {target_username}"
    except Exception:
        db.rollback()
        return False, "Failed to share employee"
