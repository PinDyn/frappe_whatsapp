"""Button utilities for WhatsApp templates."""

import re
import frappe


def process_dynamic_payload(payload, doc=None, doc_data=None):
    """
    Process dynamic payload by replacing {{field_name}} with actual field values.
    
    Args:
        payload (str): The payload string that may contain {{field_name}} placeholders
        doc (Document, optional): Frappe document object
        doc_data (dict, optional): Document data dictionary
        
    Returns:
        str: Processed payload with field values substituted
    """
    if not payload or not (doc or doc_data):
        return payload
    
    # Use doc_data if available, otherwise convert doc to dict
    if doc_data is None and doc:
        doc_data = doc.as_dict()
    
    # Find all {{field_name}} patterns
    pattern = r'\{\{([^}]+)\}\}'
    matches = re.findall(pattern, payload)
    
    processed_payload = payload
    
    for field_name in matches:
        field_name = field_name.strip()
        
        # Get field value
        if doc and hasattr(doc, 'get_formatted'):
            # Use get_formatted for prettier values
            value = doc.get_formatted(field_name)
        elif doc_data and field_name in doc_data:
            value = doc_data[field_name]
            # Convert datetime objects to string
            if hasattr(value, 'strftime'):
                value = str(value)
        else:
            # Field not found, keep the placeholder
            value = f"{{{{{field_name}}}}}"
        
        # Replace the placeholder
        processed_payload = processed_payload.replace(f"{{{{{field_name}}}}}", str(value))
    
    return processed_payload


def process_button_data(button, doc=None, doc_data=None):
    """
    Process button data to handle dynamic values.
    
    Args:
        button (dict): Button data dictionary
        doc (Document, optional): Frappe document object
        doc_data (dict, optional): Document data dictionary
        
    Returns:
        dict: Processed button data
    """
    processed_button = button.copy()
    
    if button.get("type") == "QUICK_REPLY" and button.get("payload"):
        processed_button["payload"] = process_dynamic_payload(
            button["payload"], doc, doc_data
        )
    
    return processed_button


def get_template_buttons_with_dynamic_values(template, doc=None, doc_data=None):
    """
    Get template buttons with dynamic values processed.
    
    Args:
        template (Document): WhatsApp Template document
        doc (Document, optional): Frappe document object
        doc_data (dict, optional): Document data dictionary
        
    Returns:
        list: List of processed button data dictionaries
    """
    if not template.buttons:
        return []
    
    processed_buttons = []
    for button in template.buttons:
        button_data = {
            "type": button.button_type,
            "text": button.button_text
        }
        
        if button.button_type == "QUICK_REPLY":
            payload = process_dynamic_payload(button.payload, doc, doc_data)
            button_data["payload"] = payload
        elif button.button_type == "URL":
            url = process_dynamic_payload(button.url, doc, doc_data)
            button_data["url"] = url
        elif button.button_type == "PHONE_NUMBER":
            button_data["phone_number"] = button.phone_number
        elif button.button_type == "FLOW":
            button_data.update({
                "flow_id": int(button.flow_id) if button.flow_id else 0,
                "flow_action": button.flow_action,
                "navigate_screen": button.navigate_screen
            })
        elif button.button_type == "COPY_CODE":
            button_data["example"] = [button.copy_code_example] if button.copy_code_example else [""]
        
        processed_buttons.append(button_data)
    
    return processed_buttons 