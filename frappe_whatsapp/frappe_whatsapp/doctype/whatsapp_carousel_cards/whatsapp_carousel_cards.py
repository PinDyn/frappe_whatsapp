import frappe
from frappe.model.document import Document

class WhatsAppCarouselCards(Document):
    """WhatsApp Carousel Cards doctype controller."""
    
    def validate(self):
        """Validate carousel card data."""
        self.validate_header_content()
        self.validate_body_text()
        self.validate_buttons()
    
    def validate_header_content(self):
        """Validate header content based on header type."""
        if self.header_type == "TEXT":
            if not self.header_text:
                frappe.throw("Header text is required for TEXT header type")
            if len(self.header_text) > 60:
                frappe.throw("Header text must be 60 characters or less")
        elif self.header_type in ["IMAGE", "VIDEO"]:
            if not self.header_content:
                frappe.throw("Header content (URL/asset handle) is required for media header types")
    
    def validate_body_text(self):
        """Validate body text length."""
        if self.body_text and len(self.body_text) > 160:
            frappe.throw("Body text must be 160 characters or less")
    
    def validate_buttons(self):
        """Validate button count per card."""
        if self.buttons and len(self.buttons) > 2:
            frappe.throw("Maximum 2 buttons allowed per carousel card")
    
    def get_card_payload(self, parameters=None):
        """Get the card payload for WhatsApp API."""
        card = {
            "card_index": self.card_index,
            "components": []
        }
        
        # Add header component
        if self.header_type == "TEXT":
            card["components"].append({
                "type": "header",
                "text": self.header_text
            })
        elif self.header_type in ["IMAGE", "VIDEO"]:
            header_content = self.header_content
            if parameters and self.header_type == "IMAGE":
                # Replace dynamic content if needed
                header_content = self.replace_parameters(header_content, parameters)
            
            card["components"].append({
                "type": "header",
                "parameters": [
                    {
                        "type": self.header_type.lower(),
                        self.header_type.lower(): {
                            "link": header_content
                        }
                    }
                ]
            })
        
        # Add body component
        if self.body_text:
            body_text = self.body_text
            if parameters:
                body_text = self.replace_parameters(body_text, parameters)
            
            card["components"].append({
                "type": "body",
                "parameters": [
                    {
                        "type": "text",
                        "text": body_text
                    }
                ]
            })
        
        # Add buttons if any
        if self.buttons:
            button_components = []
            for button in self.buttons:
                button_payload = button.get_button_payload(parameters)
                if button_payload:
                    button_components.append(button_payload)
            
            if button_components:
                card["components"].append({
                    "type": "buttons",
                    "buttons": button_components
                })
        
        return card
    
    def replace_parameters(self, text, parameters):
        """Replace parameters in text with actual values."""
        if not text or not parameters:
            return text
        
        # Replace {{field_name}} patterns
        for param in parameters:
            if param.get("variable_name") and param.get("value"):
                text = text.replace(f"{{{{{param['variable_name']}}}}}", str(param["value"]))
        
        return text 