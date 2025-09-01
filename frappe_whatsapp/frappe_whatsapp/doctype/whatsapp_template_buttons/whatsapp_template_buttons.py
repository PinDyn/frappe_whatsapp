# Copyright (c) 2025, Shridhar Patil and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document


class WhatsAppTemplateButtons(Document):
    """WhatsApp Template Buttons."""
    
    def validate(self):
        """Validate button configuration for template storage."""
        # Note: payload and flow_token are only required when sending messages,
        # not when storing template definitions from Meta
        
        # Only validate fields that are actually required for template storage
        if self.button_type == "URL" and hasattr(self, 'url') and self.url and not self.url.strip():
            frappe.throw("URL cannot be empty for URL buttons")
            
        if self.button_type == "PHONE_NUMBER" and hasattr(self, 'phone_number') and self.phone_number and not self.phone_number.strip():
            frappe.throw("Phone number cannot be empty for Phone Number buttons")
            
        if self.button_type == "FLOW" and hasattr(self, 'flow_id') and self.flow_id and not str(self.flow_id).strip():
            frappe.throw("Flow ID cannot be empty for Flow buttons") 