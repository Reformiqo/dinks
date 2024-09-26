import frappe
from datetime import datetime, timedelta
@frappe.whitelist(allow_guest=True)
def get_next_30_days():
    
    today = datetime.today()
    next_30_days = []
    for i in range(30):
        next_date = today + timedelta(days=i)
        day_name = next_date.strftime('%A')  # Get the day name
        date_str = next_date.strftime('%Y-%m-%d')  # Format date as YYYY-MM-DD
        
        next_30_days.append({
            "day": day_name[:3],
            "date": date_str.split('-')[-1]
        })
    
    return next_30_days

@frappe.whitelist(allow_guest=True)
def get_courts():
    courts = frappe.get_all("Court", fields=["name", "location", "image"])
    data = []
    for court in courts:
        data.append({
            "name": court.name,
            "lacation": court.location,
            "image": court.image
        })
    return data

@frappe.whitelist()
def get_court_schedules(court_name):
    schedules = frappe.get_all("Court Schedules", {"court": court_name}, ["court", "date", "time"])
<<<<<<< HEAD
    return schedules

=======
    data = []
    for schedule in schedules:
        data.append({
            "court": schedule.court,
            "date": schedule.date,
            "time": schedule.time
        })
    return data

@frappe.whitelist()
def get_location_courts(court_name):
    courts = frappe.get_all("Location Courts", {"court": court_name}, ["name", "court_number", "court"])
    return courts
>>>>>>> b47c3bc57e8dcd84d5d57cb5841b91150149dbd6
