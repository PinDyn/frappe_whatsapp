# Copyright (c) 2025, Frappe Whatsapp and Contributors
# See license.txt

import frappe
import re
from frappe.model.document import Document


def process_dynamic_payload(template_string, doc=None, doc_data=None):
    """
    Process dynamic payload by replacing {{field_name}} with actual values from document.
    
    Args:
        template_string (str): String containing {{field_name}} placeholders
        doc (Document): Frappe document object
        doc_data (dict): Document data as dictionary
    
    Returns:
        str: Processed string with replaced values
    """
    if not template_string:
        return template_string
    
    # Use doc_data if available, otherwise use doc
    data_source = doc_data if doc_data is not None else (doc.as_dict() if doc else {})
    
    frappe.log_error("Process Dynamic Payload Input", f"Template: '{template_string}', Doc: {doc.name if doc else 'None'}, Doc Data: {data_source}")
    
    def replace_field(match):
        field_name = match.group(1).strip()
        frappe.log_error("Field Replacement", f"Looking for field: '{field_name}'")
        
        # Handle nested fields like "customer.customer_name"
        if '.' in field_name:
            parts = field_name.split('.')
            current_value = data_source
            for part in parts:
                if isinstance(current_value, dict) and part in current_value:
                    current_value = current_value[part]
                else:
                    current_value = None
                    break
        else:
            current_value = data_source.get(field_name) if isinstance(data_source, dict) else None
        
        frappe.log_error("Field Value Found", f"Field '{field_name}' = '{current_value}'")
        
        # Convert to string and handle None values
        if current_value is None:
            return ""
        elif isinstance(current_value, (list, dict)):
            return str(current_value)
        else:
            return str(current_value)
    
    # Replace all {{field_name}} patterns
    processed_string = re.sub(r'\{\{([^}]+)\}\}', replace_field, template_string)
    
    frappe.log_error("Dynamic Payload Processing Result", f"Template: '{template_string}' -> Result: '{processed_string}'")
    
    return processed_string


def get_template_buttons_with_dynamic_values(template, button_parameters, doc=None, doc_data=None):
    """
    Get template buttons with dynamic values processed from button parameters.
    
    Args:
        template: WhatsApp Template document
        button_parameters: List of button parameter documents
        doc (Document): Frappe document object
        doc_data (dict): Document data as dictionary
    
    Returns:
        list: List of processed button components for message sending
    """
    if not template.buttons or not button_parameters:
        return []
    
    buttons = []
    for param in button_parameters:
        # param is a document object, so we need to access its fields properly
        frappe.log_error("Button Parameter Debug", f"Processing param: {param.as_dict()}")
        
        if param.button_index >= len(template.buttons):
            continue
            
        template_button = template.buttons[param.button_index]
        frappe.log_error("Template Button Debug", f"Template button: {template_button.as_dict()}")
        
        button_data = {
            "type": param.button_type,
            "text": template_button.button_text
        }
        
        frappe.log_error("Button Type Debug", f"Button type: '{param.button_type}'")
        
        # Process dynamic values based on button type
        # According to WhatsApp API docs, when sending template messages:
        # - QUICK_REPLY buttons should include the payload
        # - URL buttons should include the URL
        # - PHONE_NUMBER buttons should include the phone_number
        # - Other button types follow their respective structures
        
        if param.button_type == "QUICK_REPLY":
            # For QUICK_REPLY, notification parameter payload is required
            frappe.log_error("QUICK_REPLY Debug", f"Payload value: '{param.payload}', Type: {type(param.payload)}")
            frappe.log_error("QUICK_REPLY Debug", f"Param fields: {param.as_dict()}")
            payload = process_dynamic_payload(param.payload, doc, doc_data)
            button_data["payload"] = payload
            frappe.log_error("QUICK_REPLY Result", f"Final payload: '{payload}'")
        elif param.button_type == "URL":
            # For URL, notification parameter URL is required
            frappe.log_error("URL Debug", f"URL value: '{param.url}'")
            url = process_dynamic_payload(param.url, doc, doc_data)
            button_data["url"] = url
            frappe.log_error("URL Result", f"Final URL: '{url}'")
        elif param.button_type == "PHONE_NUMBER":
            # For PHONE_NUMBER, notification parameter phone is required
            phone = process_dynamic_payload(param.phone_number, doc, doc_data)
            button_data["phone_number"] = phone
        elif param.button_type == "COPY_CODE":
            # For COPY_CODE, notification parameter example is required
            example = process_dynamic_payload(param.copy_code_example, doc, doc_data)
            button_data["example"] = [example]
        
        buttons.append(button_data)
    
    return buttons 