import frappe
from frappe.utils import getdate, nowdate
from datetime import datetime, timedelta

# Helper Functions
@frappe.whitelist()
def get_days(start_date: str, days: int = 30):
    """Generate a list of dates from the given start_date for the next `days` days."""
    start = datetime.strptime(start_date, '%Y-%m-%d')
    return [(start + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days)]

def is_email_valid(email: str):
    """Validate if the provided email address is valid."""
    return frappe.utils.validate_email_address(email)

def fetch_schedules(court: str):
    """Fetch all schedules for a specific court."""
    return frappe.get_all(
        "Court Schedule",
        filters={"court": court},
        fields=["start_time", "end_time", "date"]
    )

# API Functions
@frappe.whitelist()
def get_next_30_days():
    """Get a list of the next 30 days starting from today."""
    frappe.local.response.update({
        "http_status_code": 200,
        "data": get_days(start_date=nowdate(), days=30)
    })
@frappe.whitelist()
def get_location_booked_slots(location:str, date:str):
    try:
        data = []
        schedules = frappe.get_list("Court Schedule", {"location": location, "date": date}, ["date", "start_time", "end_time"])
        booked_slots = []
        for schedule in schedules:
            start_time = schedule.get("start_time")
            end_time = schedule.get("end_time")
            booked_slots.append({
                "start_time": start_time,
                "end_time": end_time
            })
        data.append({
            "booked_slots": booked_slots
        })

        frappe.local.response.update({
            "http_status_code": 200,
            "date": date,
            "data": booked_slots
        })
    except Exception as e:
        frappe.log_error(f"Error fetching booked slots: {str(e)}", "Get Booked Slots")
        frappe.local.response.update({
            "http_status_code": 400,
            "error": str(e)
        })

@frappe.whitelist()
def get_available_courts(date: str, time_slot: dict):
    """Fetch courts that are available on a specific date and time schedule."""
    try:
        date = getdate(date)
        all_courts = frappe.get_all("Court", fields=["*"])
        available_courts = []
        start_time = time_slot.get("start_time")
        end_time = time_slot.get("end_time")
        for court in all_courts:
            schedules = fetch_schedules(court.name)
            
            if frappe.db.exists("Court Schedule", {"court": court.name, "date": date, "start_time": start_time, "end_time": end_time}):
                available_courts.append({
                    "court_id": court.name,
                    "court_name": court.court_name,
                    "is_available": False
                })
            else:
                available_courts.append({
                    "court_id": court.name,
                    "court_name": court.court_name,
                    "is_available": True,
                    
                })
                
        frappe.local.response.update({
            "http_status_code": 200,
            "data": available_courts
        })

    except Exception as e:
        frappe.log_error(f"Error fetching available courts: {str(e)}", "Get Available Courts")
        frappe.local.response.update({
            "http_status_code": 400,
            "error": str(e)
        })

@frappe.whitelist()
def create_booking(court: str, date: str, time_schedules: str, customer_name: str, email: str):
    """Create a court booking for a specific court, date, and time schedule."""
    if not is_email_valid(email):
        frappe.local.response.update({
            "http_status_code": 400,
            "error": "Invalid email address."
        })
        return

    try:
        # Check if court is already booked
        existing_booking = frappe.get_all(
            "Court Schedule",
            filters={"court": court, "date": date, "time_schedules": ("like", f"%{time_schedules}%")},
        )
        if existing_booking:
            ffrappe.local.response.update({
                "http_status_code": 400,
                "error": "Court is already booked for the selected time."
            })
            return

        # Ensure customer exists or create one
        customer = frappe.db.get_value("Customer", {"email_id": email}, "name")
        if not customer:
            customer_doc = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": customer_name,
                "email_id": email,
                "customer_type": "Individual",
                "customer_group": "Individual",
                "territory": "All Territories"
            })
            customer_doc.insert()
            frappe.db.commit()
            customer = customer_doc.name


        # Create Booking
        booking = frappe.get_doc({
            "doctype": "Court Schedule",
            "court": court,
            "date": date,
            "time_schedules": time_schedules,
            "customer": customer
        })
        booking.insert()
        frappe.db.commit()

        frappe.local.response.update({
            "http_status_code": 200,
            "data": "Booking created successfully."
        })

    except Exception as e:
        frappe.log_error(f"Error creating booking: {str(e)}", "Create Booking")
        frappe.local.response.update({
            "http_status_code": 400,
            "error": str(e)
        })

@frappe.whitelist(allow_guest=True)
def get_everything(location):
    try:
        dates = get_days(location)  # Fetch next 30 days
        schedule_data = []

        # Fetch all courts for the location at once
        courts = frappe.get_all("Location Courts", filters={"court": location}, fields=["name", "court_number", "status"], order_by="court_number")

        for date in dates:
            date_str = date.get("date")
            court_data = []
            for court in courts:
                schedules = frappe.get_all("Court Schedules", filters={"court": location, "date": date_str, "court_number": court.name}, fields=["court_number", "time"])
                # Find if the court has a schedule for the current date
                # scheduled_court = next((s for s in schedules if s.get("court_number") == court.get("name")), None)
                s_data = []
                for s in schedules:
                    if s.get("court_number") == court.get("name"):
                        s_data.append({
                            "time": s.get("time")
                        })
                court_data.append({
                    "court_number": court.get("court_number"),
                    "schedules": s_data
                })
            
            
            schedule_data.append({
                "date": date_str,
                "court_data": court_data
            })

            frappe.local.response.update({
                "http_status_code": 200,
                "data": schedule_data
            })

    except Exception as e:
        frappe.log_error(f"Error fetching courts: {str(e)}", "Get Courts")
        frappe.local.response.update({
            "http_status_code": 400,
            "error": str(e)
        })
