import frappe
from frappe.utils import getdate, nowdate
from datetime import datetime, timedelta

# Helper Functions
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
        fields=["time_schedules", "date"]
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
def get_available_courts(date: str, time_schedules: str):
    """Fetch courts that are available on a specific date and time schedule."""
    try:
        all_courts = frappe.get_all("Court", fields=["name", "price"])
        available_courts = []

        for court in all_courts:
            schedules = fetch_schedules(court.name)
            is_available = not any(
                schedule["date"] == date and time_schedules in schedule["time_schedules"]
                for schedule in schedules
            )
            if is_available:
                available_courts.append({"name": court.name, "price": court.price})

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
    dates = get_days(location)  # Fetch next 30 days
    schedule_data = []

    # Fetch all courts for the location at once
    courts = frappe.get_all("Location Courts", filters={"court": location}, fields=["name", "court_number", "status"], order_by="court_number")

    # Loop through dates and check court schedules
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
        frappe.log_error(f"Error fetching everything: {str(e)}", "Get Everything")
        frappe.local.response.update({
            "http_status_code": 400,
            "error": str(e)
        })
