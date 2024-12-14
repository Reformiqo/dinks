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
    frappe.local.response = {
        "success": True,
        "data": get_days(start_date=nowdate(), days=30)
    }

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

        frappe.local.response = {
            "success": True,
            "data": available_courts
        }

    except Exception as e:
        frappe.log_error(f"Error fetching available courts: {str(e)}", "Get Available Courts")
        frappe.local.response = {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def create_booking(court: str, date: str, time_schedules: str, customer_name: str, email: str):
    """Create a court booking for a specific court, date, and time schedule."""
    if not is_email_valid(email):
        frappe.local.response = {
            "success": False,
            "error": "Invalid email address."
        }
        return

    try:
        # Check if court is already booked
        existing_booking = frappe.get_all(
            "Court Schedule",
            filters={"court": court, "date": date, "time_schedules": ("like", f"%{time_schedules}%")},
        )
        if existing_booking:
            frappe.local.response = {
                "success": False,
                "error": "Court is already booked for the selected time."
            }
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

        frappe.local.response = {
            "success": True,
            "message": "Booking created successfully."
        }

    except Exception as e:
        frappe.log_error(f"Error creating booking: {str(e)}", "Create Booking")
        frappe.local.response = {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def get_everything():
    """Fetch all available courts, schedules, and rates."""
    try:
        courts = frappe.get_all("Court", fields=["name", "price"])
        schedules = frappe.get_all("Court Schedule", fields=["court", "date", "time_schedules"])
        frappe.local.response = {
            "success": True,
            "data": {
                "courts": courts,
                "schedules": schedules
            }
        }

    except Exception as e:
        frappe.log_error(f"Error fetching everything: {str(e)}", "Get Everything")
        frappe.local.response = {
            "success": False,
            "error": str(e)
        }
