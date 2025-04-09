import frappe
from frappe.utils import getdate
@frappe.whitelist()
def get_court_time_slots(court, date):
    time_slots = frappe.get_all("Time Slots", ["name"])
    data = []
    for slot in time_slots:
        if (
                frappe.db.exists("Court Schedule", {"court": court, "date": getdate(date), "start_time": slot.name}) or
                frappe.db.exists("Court Schedule", {"court": court, "date": getdate(date), "end_time": slot.name})
        ):
            data.append({
                "time_slot": slot.name,
                "is_available": False
            })
        else:
            data.append({
                "time_slot": slot.name,
                "is_available": True
            })

    return data

# in dinks.dinks.page.dink.dink.py
@frappe.whitelist()
def get_courts():
    """
    Retrieves a list of court names from the database.

    Returns:
        list: A list of court names.
    """
    courts = frappe.db.sql("SELECT name FROM `tabCourt`")
    return courts


# in dinks.dinks.page.dink.dink.py
@frappe.whitelist()
def get_booking_details(court, date, time):
    if frappe.db.exists("Booking", {"court": court, "date": getdate(date), "start_time": time}):
        booking = frappe.get_doc("Booking", {"court": court, "date": getdate(date), "start_time": time})
        return {
            "customer_name": booking.customer,
            "customer_phone": frappe.db.get_value("Customer", booking.customer, "phone") 
        }
    
    elif frappe.db.exists("Booking", {"court": court, "date": getdate(date), "end_time": time}):
        booking = frappe.get_doc("Booking", {"court": court, "date": getdate(date), "end_time": time})
        return {
            "customer_name": booking.customer,
            "customer_phone": frappe.db.get_value("Customer", booking.customer, "phone") 
        }
    
    return {
        "customer_name": "N/A",
        "customer_phone": "N/A" 
        
    }
