import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .models import SampleData, get_db

def generate_sample_data():
    """Generate sample data and store in database"""
    db = next(get_db())

    # Clear existing data
    db.query(SampleData).delete()

    # Generate new data
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    values = np.random.normal(100, 15, len(dates))
    categories = np.random.choice(['A', 'B', 'C'], len(dates))

    # Store in database - convert numpy types to Python native types
    for date, value, category in zip(dates, values, categories):
        sample_data = SampleData(
            date=date.to_pydatetime(),  # Convert pandas timestamp to Python datetime
            value=float(value),         # Convert numpy float to Python float
            category=str(category)      # Convert numpy string to Python string
        )
        db.add(sample_data)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error generating sample data: {str(e)}")
        raise

    return load_sample_data()

def load_sample_data():
    """Load sample data from database"""
    db = next(get_db())
    data = db.query(SampleData).all()

    if not data:
        return generate_sample_data()

    # Convert to pandas DataFrame
    df = pd.DataFrame([{
        'Date': d.date,
        'Value': d.value,
        'Category': d.category
    } for d in data])

    return df