import frappe
from datetime import datetime, timedelta
@frappe.whitelist()
def get_next_30_days():
    
    today = datetime.today()
    next_30_days = []
    for i in range(30):
        next_date = today + timedelta(days=i)
        day_name = next_date.strftime('%A')  # Get the day name
        date_str = next_date.strftime('%Y-%m-%d')  # Format date as YYYY-MM-DD
        
        next_30_days.append({
            "day": day_name,
            "date": date_str
        })
    
    return next_30_days
