from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .models import CompanyData, User, Tab, TabType, get_db
import random

def generate_sample_company_data():
    """Generate sample data for company dashboard"""
    db = next(get_db())

    # Clear existing data
    db.query(CompanyData).delete()

    # Get all tabs
    tabs = {tab.name: tab for tab in db.query(Tab).all()}

    # Generate 30 days of data for each tab
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)

    sample_data = []

    # Overview metrics
    for date in (start_date + timedelta(days=x) for x in range(31)):
        sample_data.extend([
            CompanyData(
                date=date,
                tab_id=tabs[TabType.OVERVIEW.value].id,
                metric_name="Total Revenue",
                value=random.uniform(50000, 100000)
            ),
            CompanyData(
                date=date,
                tab_id=tabs[TabType.OVERVIEW.value].id,
                metric_name="Active Orders",
                value=random.randint(100, 500)
            )
        ])

    # Sales metrics
    for date in (start_date + timedelta(days=x) for x in range(31)):
        sample_data.extend([
            CompanyData(
                date=date,
                tab_id=tabs[TabType.SALES.value].id,
                metric_name="Daily Sales",
                value=random.uniform(5000, 15000)
            ),
            CompanyData(
                date=date,
                tab_id=tabs[TabType.SALES.value].id,
                metric_name="Orders Count",
                value=random.randint(50, 200)
            )
        ])

    # Gross Profit metrics
    for date in (start_date + timedelta(days=x) for x in range(31)):
        sample_data.extend([
            CompanyData(
                date=date,
                tab_id=tabs[TabType.GROSS_PROFIT.value].id,
                metric_name="Gross Profit",
                value=random.uniform(20000, 40000)
            ),
            CompanyData(
                date=date,
                tab_id=tabs[TabType.GROSS_PROFIT.value].id,
                metric_name="Profit Margin",
                value=random.uniform(0.2, 0.4)
            )
        ])

    # Inventory metrics
    for date in (start_date + timedelta(days=x) for x in range(31)):
        sample_data.extend([
            CompanyData(
                date=date,
                tab_id=tabs[TabType.INVENTORY.value].id,
                metric_name="Stock Level",
                value=random.randint(1000, 5000)
            ),
            CompanyData(
                date=date,
                tab_id=tabs[TabType.INVENTORY.value].id,
                metric_name="Low Stock Items",
                value=random.randint(5, 50)
            )
        ])

    # Shipment metrics
    for date in (start_date + timedelta(days=x) for x in range(31)):
        sample_data.extend([
            CompanyData(
                date=date,
                tab_id=tabs[TabType.SHIPMENT.value].id,
                metric_name="Packages Shipped",
                value=random.randint(50, 200)
            ),
            CompanyData(
                date=date,
                tab_id=tabs[TabType.SHIPMENT.value].id,
                metric_name="Average Delivery Time",
                value=random.uniform(1, 5)
            )
        ])

    # Add all sample data
    db.bulk_save_objects(sample_data)
    db.commit()

def get_tab_data(username: str, tab_name: str):
    """Get data for a specific dashboard tab"""
    db = next(get_db())

    # Get user and tab
    user = db.query(User).filter(User.username == username).first()
    tab = db.query(Tab).filter(Tab.name == tab_name).first()

    if not user:
        return None, "User not found"

    if not tab:
        return None, "Tab not found"

    # Super admin can access all tabs
    if user.role_name != "super_admin":
        # Check if user has access to this tab
        if tab not in user.accessible_tabs:
            return None, "No access to this tab"

    # Get data for the tab
    data = db.query(CompanyData).filter(
        CompanyData.tab_id == tab.id
    ).order_by(CompanyData.date.desc()).all()

    return data, "Success"