import frappe
from datetime import datetime, timedelta
from frappe.utils import getdate, cint, today, flt, validate_email_address
import razorpay
import frappe
from datetime import datetime, timedelta, date
import json
from frappe.types import DF
from frappe.utils import getdate, nowdate
from frappe import FrappeTypeError
from dinks.config import validate_request_params 
from inspect import signature

@frappe.whitelist()
def create_booking(
            court: str,
            date: date,
            customer_name: str,
            email: str,
            start_time: str,
            end_time: str,
            players_count: int,
            team_id: str = None
            ):
    """Create a court booking for a specific court, date, and time schedule."""
    if not validate_email_address(email):
        frappe.local.response.update({
            "http_status_code": 400,
            "error": "Invalid email address."
        })
        return

    try:
        # Check if court is already booked
        existing_booking = frappe.get_all(
            "Court Schedule",
            {"court": court, "date": date, "start_time": start_time, "end_time": end_time},
        )
        if existing_booking:
            frappe.local.response.update({
                "http_status_code": 400,
                "error": "Court is already booked for the selected time."
            })
            return

        # Ensure customer exists or create one
        if frappe.db.exists("Customer", {"email_id": email}): 
            customer = frappe.get_value("Customer", {"email_id": email}, "name")
        else:
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
        booking = frappe.new_doc("Booking")
        booking.customer = customer
        booking.court = court
        booking.date = date
        booking.start_time = start_time
        booking.end_time = end_time
        booking.players = players_count
        booking.team_id = team_id
        booking.insert()
        booking.submit()
        frappe.db.commit()

        frappe.local.response.update({
            "http_status_code": 200,
            "message": "Booking created successfully.",
            "data": {
                "court": court,
                "date": date,
                "start_time": start_time,
                "end_time": end_time,
                "players": players_count,
                "team_id": team_id
            }
        })
    except Exception as e:
        frappe.log_error(f"Error creating booking: {str(e)}", "Create Booking")
        frappe.local.response.update({
            "http_status_code": 400,
            "error": str(e)
        })


@frappe.whitelist(allow_guest=True)
def get_location():
    try:
        locations = frappe.get_all("Location")
        data = []
        for loc in locations:
            location = frappe.get_doc("Location", loc.get("name"))
            data.append({
                "name": location.get("name"),
                "location_name": location.get("location_name"),
                "thumbnail": location.get("thumbnail"),
                "city": location.city,
                "address": location.get("address"),
                "address_url": location.get("address_url"),
                "full_address": location.get("full_address"),
                "price": location.get("price"),
                "indoor_courts": location.get("indoor_courts"),
                "outdoor_courts": location.get("outdoor_courts"),
                "facilities": location.get("facilities"),
                "photos": frappe.get_all("Location Photo", {"location": location.get("name")}, ["photo"]),
            })

        frappe.local.response.update({
            "http_status_code": 200,
            "data": data
        })
    except Exception as e:
        frappe.log_error(f"Error fetching locations: {str(e)}", "Get Locations")
        frappe.local.response.update({
            "http_status_code": 400,
            "error": str(e)
        })

@frappe.whitelist()
def get_location_booked_slots():
    # try:
    form_data = frappe.local.form_dict
    location = form_data.get("location")
    date = getdate(form_data.get("date"))
    facilities = frappe.get_list("Facility", {"location": location}, ["name", "location"])
    data = []
    for facility in facilities:
        schedules = frappe.get_list("Schedule", {"facility": facility.name, "date": date}, ["date", "start_time", "end_time"])
        booked_slots = []
        for schedule in schedules:
            start_time = schedule.get("start_time")
            end_time = schedule.get("end_time")
            booked_slots.append({
                "start_time": start_time,
                "end_time": end_time
            })
        data.append({
            "facility_id": facility.get("name"),
            "booked_slots": booked_slots
        })
    
    frappe.local.response.update({
        "http_status_code": 200,
        "message": "Timeslots fetched successfully",
        "date": date,
        "data": booked_slots
    })
    # except Exception as e:
    #     frappe.log_error(f"Error fetching booked slots: {str(e)}", "Get Booked Slots")
    #     frappe.local.response.update({
    #         "http_status_code": 400,
    #         "error": str(e)
    #     })

@frappe.whitelist()
def get_court_schedules():
    form_data = frappe.local.form_dict
    date = form_data.get("date")
    location = form_data.get("location")
    time_slot = form_data.get("time_slot")
    start_time = time_slot.get("start_time")
    end_time = time_slot.get("end_time")


    court_schedules = frappe.get_list("Court Schedule", {"location": location, "date": date, "start_time": start_time, "end_time": end_time}, ["court", "start_time", "end_time"])
    schedules = []
    for schedule in court_schedules:
        if schedule.get("start_time") == start_time or schedule.get("end_time") == end_time:
            schedules.append({
                "court": schedule.get("court"),
                "start_time": schedule.get("start_time"),
                "end_time": schedule.get("end_time")
            })
    courts = frappe.get_all("Court", {"location": location}, ["name", "court_name", "court_type"])
    indoor_courts = []
    outdoor_courts = []
    for court in courts:
        if not any(schedule.get("court") == court.get("name") for schedule in schedules):
            if court.get("court_type") == "Indoor":
                indoor_courts.append({
                    "court_id": court.get("name"),
                    "court_name": court.get("court_name"),
                    "is_available": True
                })
            else:
                outdoor_courts.append({
                    "court_id": court.get("name"),
                    "court_name": court.get("court_name"),
                    "is_available": True
                })

    
    
    frappe.local.response.update({
        "http_status_code": 200,
        "message": "Schedules fetched successfully",
        "data": {
            "indoor_courts": indoor_courts,
            "outdoor_courts": outdoor_courts
        },
        
    })

@frappe.whitelist()
def get_teams():
    form_data = frappe.local.form_dict
    try:
        date = form_data.get("date")
        court = form_data.get("court")
        time_slot = form_data.get("time_slot")
        start_time = time_slot.get("start_time")
        end_time = time_slot.get("end_time")
        if not frappe.db.exists("Court Schedule", {"court": court, "date": date, "start_time": start_time, "end_time": end_time}):
            frappe.local.response.update({
                "http_status_code": 400,
                "error": "Invalid court schedule"
            })
            return

        court_schedule = frappe.get_doc("Court Schedule", {"court": court, "date": date, "start_time": start_time, "end_time": end_time}, ["court", "start_time", "end_time"])
        teams = frappe.get_all("Team", {"slot": court_schedule.get("name")}, ["name", "team_leader", "players_count", "status"])
        data = []
        for team in teams:
            team_doc = frappe.get_doc("Team", team.get("name"))
            data.append({
                "team_id": team.get("name"),
                "team_leader": team.get("team_leader"),
                "players_count": team.get("players_count"),
                "time_slot":{
                    "start_time": court_schedule.get("start_time"),
                    "end_time": court_schedule.get("end_time"),
                },
                "status": team.get("status"),
            })
            frappe.local.response.update({
                "http_status_code": 200,
                "message": "Teams fetched successfully",
                "data": data
            })
    except Exception as e:
        frappe.log_error(f"Error fetching teams: {str(e)}", "Get Teams")
        frappe.local.response.update({
            "http_status_code": 400,
            "error": str(e)
        })

@frappe.whitelist()
def join_team(team_id:str, player_id:str):
    try:
        if not frappe.db.exists("Team", team_id):
            frappe.local.response.update({
                "http_status_code": 400,
                "error": "Invalid team"
            })
            return
        team = frappe.get_doc("Team", team_id)
        team.append("team_players", {
            "player_id": player_id
        })
        team.save()
        frappe.db.commit()
        data = {
            "team_id": team_id,
            "leader": team.team_leader,
            "players_count": team.players_count,
            "time_slot": {
                "start_time": frappe.get_value("Court Schedule", team.slot, "start_time"),
                "end_time": frappe.get_value("Court Schedule", team.slot, "end_time"),
            },
            
        }
        frappe.local.response.update({
            "http_status_code": 200,
            "message": "Joined team successfully",
            "data": data
            
        })
    
    except Exception as e:
        frappe.log_error(f"Error joining team: {str(e)}", "Join Team")
        frappe.clear_messages()
        frappe.local.response.update({
            "http_status_code": 400,
            "error": str(e)
        })

@frappe.whitelist()
def booking_pass(
        date: date,
        email: str,
        court: str,
        team_id: str,

        ):
    try:         
        validate_request_params(allowed_params=set(signature(booking_pass).parameters.keys()))
        if not validate_email_address(email):
            frappe.local.response.update({
                "http_status_code": 400,
                "error": "Invalid email address."
            })
            return

        

        if not frappe.db.exists("Court", court):
            frappe.local.response.update({
                "http_status_code": 400,
                "error": "Invalid court."
            })
            return

        if not frappe.db.exists("Team", team_id):
            frappe.local.response.update({
                "http_status_code": 400,
                "error": "Invalid team."
            })
            return

        

        if not frappe.db.exists("Booking", {"court": court, "date": date}):
            frappe.local.response.update({
                "http_status_code": 400,
                "error": "Invalid booking."
            })
            return

        booking = frappe.get_doc("Booking", {"court": court, "date": date, "team_id": team_id})
        team = frappe.get_doc("Team", team_id)
        schedule = frappe.get_doc("Court Schedule", {"booking": booking.name})

        data = {
            "email_id": email,
            "booking_id": booking.name,
            "court_id": court,
            "date": date,
            "location_id": schedule.location,
            "team_id": team_id,
            "total_players": team.players_count,
            "booking_person": team.team_leader,
            "start_time": frappe.get_value("Court Schedule", {"booking":booking.name}, "start_time"),
            "end_time": frappe.get_value("Court Schedule", {"booking":booking.name}, "end_time"),
            }    
        
        
        frappe.local.response.update({
            "http_status_code": 200,
            "message": "Confirmed booking pass",
            "data": data
        })
    except Exception as e:
        frappe.log_error(f"Error confirming booking pass: {str(e)}", "Booking Pass")
        frappe.local.response.update({
            "http_status_code": 400,
            "error": str(e)
        })

@frappe.whitelist()
def booking_history():
    user_id = frappe.session.user
    try:
        court_bookings = frappe.get_all("Booking", {"owner": user_id})
        event_bookings = frappe.get_all("Event Registration", {"owner": user_id})
        court_data = []
        event_data = []
        for court in court_bookings:
            doc = frappe.get_doc("Booking", court.name)
            court_data.append({
                "booking_id": doc.name,
                "court_name": frappe.db.get_value("Court", court, "court_name"),
                "location": frappe.db.get_value("Court", court, "location"),
                "date": doc.date,
                "time": f"{doc.start_time} - {doc.end_time}",
                "court": doc.court,
                "image_url": ""

            })
        frappe.local.response.update({
            "http_status_code": 200,
            "data": court_data
        })
    except Exception as e:
        frappe.local.response.update({
            "http_status_code": 400,
            "error": str(e)
        })
    
@frappe.whitelist()
def modify_booking(booking_i: str, new_date: str = None, new_time_slot: dict = None):
    try:
        if not frappe.db.exists("Booking", booking_id):
            frappe.local.response.update({
                "http_status_code": 400,
                "error": "Invalid booking ID"
            })
            return
        start_time = new_time_slot.get("start_time")
        end_time = new_time_slot.get("end_time")


        booking = frappe.get_doc("Booking", booking_id)
        if new_date:
            frappe.db.set_value("Booking", booking_id, "date", new_date)
        if new_time_slot:
            frappe.db.set_value("Booking", booking_id, "start_time", start_time)
            frappe.db.set_value("Booking", booking_id, "end_time", end_time)
        frappe.db.commit()
        frappe.local.response.update({
            "http_status_code": 200,
            "message": "Booking modified successfully",
            "new_booking_details": {
                "booking_id": booking_id,
                "court": booking.court,
                "date": new_date,
                "start_time": start_time,
                "end_time": end_time
            }
        })
    except Exception as e:
        frappe.log_error(f"Error modifying booking: {str(e)}", "Modify Booking")
        frappe.local.response.update({
            "http_status_code": 400,
            "error": str(e)
        })

@frappe.whitelist()
def cancel_booking(booking_id:str):
    try:
        if not frappe.db.exists("Booking", booking_id):
            frappe.local.response.update({
                "http_status_code": 400,
                "error": "Invalid booking ID"
            })
            return
        booking = frappe.get_doc("Booking", booking_id)
        booking.cancel()
        frappe.db.commit()
        frappe.local.response.update({
            "http_status_code": 200,
            "message": "Booking cancelled successfully",
            "refund":"A refund of 100% will be processed in 7 business days"
        })
    except Exception as e:
        frappe.log_error(f"Error cancelling booking: {str(e)}", "Cancel Booking")
        frappe.local.response.update({
            "http_status_code": 400,
            "error": str(e)
        })
