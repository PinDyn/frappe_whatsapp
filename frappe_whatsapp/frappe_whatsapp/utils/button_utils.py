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
    
    def replace_field(match):
        field_name = match.group(1).strip()
        
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
        
        # Convert to string and handle None values
        if current_value is None:
            return ""
        elif isinstance(current_value, (list, dict)):
            return str(current_value)
        else:
            return str(current_value)
    
    # Replace all {{field_name}} patterns
    processed_string = re.sub(r'\{\{([^}]+)\}\}', replace_field, template_string)
    
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
        if param.button_index >= len(template.buttons):
            continue
            
        template_button = template.buttons[param.button_index]
        
        button_data = {
            "type": param.button_type,
            "text": template_button.button_text
        }
        
        # Process dynamic values based on button type
        if param.button_type == "QUICK_REPLY":
            payload = process_dynamic_payload(param.payload, doc, doc_data)
            button_data["payload"] = payload
        elif param.button_type == "URL":
            url = process_dynamic_payload(param.url, doc, doc_data)
            button_data["url"] = url
        elif param.button_type == "PHONE_NUMBER":
            phone = process_dynamic_payload(param.phone_number, doc, doc_data)
            button_data["phone_number"] = phone
        elif param.button_type == "COPY_CODE":
            example = process_dynamic_payload(param.copy_code_example, doc, doc_data)
            button_data["example"] = [example]
        elif param.button_type == "FLOW":
            flow_token = process_dynamic_payload(param.flow_token, doc, doc_data)
            button_data["flow_token"] = flow_token
        
        buttons.append(button_data)
    
    return buttons 