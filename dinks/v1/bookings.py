import frappe
from datetime import datetime, timedelta
from frappe.utils import getdate, cint, today, flt
import razorpay
import frappe
from datetime import datetime, timedelta
import json
from frappe.types import DF
from frappe.utils import getdate, nowdate

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
    try:
        form_data = frappe.local.form_dict
        location = form_data.get("location")
        date = getdate(form_data.get("date"))
        schedules = frappe.get_list("Court Schedule", {"location": location, "date": date}, ["date", "start_time", "end_time"])
        booked_slots = []
        for schedule in schedules:
            start_time = schedule.get("start_time")
            end_time = schedule.get("end_time")
            booked_slots.append({
                "start_time": start_time,
                "end_time": end_time
            })
        frappe.local.response.update({
            "http_status_code": 200,
            "message": "Timeslots fetched successfully",
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
