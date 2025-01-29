# Copyright (c) 2024, Erpera and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Booking(Document):
	def after_insert(self):
		schedule = frappe.new_doc("Court Schedule")
		schedule.court = self.court
		schedule.location = frappe.db.get_value("Court", self.court, "location")
		schedule.date = self.date
		schedule.start_time = self.start_time
		schedule.end_time = self.end_time
		schedule.players = self.players
		schedule.booking = self.name
		schedule.save()
		frappe.db.commit()
			# schedule.court_number = 
			
			
	def create_invoice(self):
		pass