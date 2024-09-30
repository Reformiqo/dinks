import frappe
from datetime import datetime, timedelta
from frappe.utils import getdate

@frappe.whitelist(allow_guest=True)
def get_next_30_days(court_name):
    
    today = datetime.today()
    data = []
    for i in range(30):

        next_date = today + timedelta(days=i)
        schedules = frappe.get_all("Court Schedules",{"court": court_name, "date": getdate(next_date)}, ["time", ])
        courts = frappe.get_all("Location Courts", {"court": court_name}, ["court_number", "status"])


        day_name = next_date.strftime('%A')  
        date_str = next_date.strftime('%Y-%m-%d') 
        schedule_data = []
        for schedule in schedules:
             schedule_data.append({
                 "time": schedule.time,
                 "courts": courts
             })
        
        data.append({
            "weekday": day_name[:3],
            "day": date_str.split("-")[-1],
            "date": date_str,
            "schedules": schedule_data,

        })
    
    return data

@frappe.whitelist(allow_guest=True)
def get_courts():
    courts = frappe.get_all("Court", fields=["name", "location", "image"])
    data = []
    for court in courts:
        data.append({
            "name": court.name,
            "location": court.location,
            "image": court.image
        })
    return data

@frappe.whitelist(allow_guest=True)
def get_court_schedules(court_name):
    schedules = frappe.get_all("Court Schedules", {"court": court_name}, ["court", "date", "time"])
    data = []
    for schedule in schedules:
        data.append({
            "court": schedule.court,
            "date": schedule.date,
            "time": schedule.time
        })
    return data

@frappe.whitelist(allow_guest=True)
def get_location_courts(court_name):
    courts = frappe.get_all("Location Courts", {"court": court_name}, ["name", "court_number", "court"])
    return courts
@frappe.whitelist(allow_guest=True)
def register_member():
    form_data = frappe.local.form_dict
    first_name = form_data.get("first_name")
    last_name = form_data.get("last_name")
    phone  = form_data.get("phone")
    gender = form_data.get("gender")

    lead = frappe.get_doc({
        "doctype": "Lead",
        "first_name": first_name,
        "last_name": last_name,
        "phone": phone,
    })
    lead.save(ignore_permissions=True)
    frappe.db.commit()
