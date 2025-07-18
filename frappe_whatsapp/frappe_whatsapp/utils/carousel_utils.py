# Copyright (c) 2025, Frappe Whatsapp and Contributors
# See license.txt

import frappe
import re
import requests
import os
from frappe.model.document import Document
from .button_utils import process_dynamic_payload


def build_carousel_payload(template, carousel_parameters=None, doc=None, doc_data=None, access_token=None, app_id=None):
    """
    Build carousel payload for WhatsApp API.
    
    Args:
        template: WhatsApp Template document
        carousel_parameters: List of carousel parameter documents
        doc (Document): Frappe document object
        doc_data (dict): Document data as dictionary
        access_token (str): WhatsApp access token (optional)
        app_id (str): WhatsApp App ID (optional)
    
    Returns:
        dict: Carousel payload for WhatsApp API
    """
    if not template.carousel_cards:
        return None
    
    # Process carousel parameters
    processed_params = process_carousel_parameters(carousel_parameters, doc, doc_data)
    
    # Build carousel component
    carousel_component = {
        "type": "CAROUSEL",
        "cards": []
    }
    
    # Process each card
    for card in template.carousel_cards:
        card_payload = build_card_payload(card, processed_params, doc, doc_data, access_token, app_id)
        if card_payload:
            carousel_component["cards"].append(card_payload)
    
    return carousel_component


def process_carousel_parameters(carousel_parameters, doc=None, doc_data=None):
    """
    Process carousel parameters and organize them by type and card index.
    
    Args:
        carousel_parameters: List of carousel parameter documents
        doc (Document): Frappe document object
        doc_data (dict): Document data as dictionary
    
    Returns:
        dict: Organized parameters by type and card index
    """
    if not carousel_parameters:
        return {}
    
    processed = {
        "body_variables": {},
        "card_headers": {},
        "card_bodies": {}
    }
    
    for param in carousel_parameters:
        value = param.get_parameter_value(doc)
        
        if param.parameter_type == "body_variable":
            processed["body_variables"][param.variable_name] = value
        elif param.parameter_type == "card_header":
            card_key = f"card_{param.card_index}"
            if card_key not in processed["card_headers"]:
                processed["card_headers"][card_key] = {}
            processed["card_headers"][card_key][param.variable_name] = value
        elif param.parameter_type == "card_body":
            card_key = f"card_{param.card_index}"
            if card_key not in processed["card_bodies"]:
                processed["card_bodies"][card_key] = {}
            processed["card_bodies"][card_key][param.variable_name] = value
    
    return processed


def build_card_payload(card, processed_params, doc=None, doc_data=None, access_token=None, app_id=None):
    """
    Build individual card payload for carousel.
    
    Args:
        card: WhatsApp Carousel Cards document
        processed_params: Processed carousel parameters
        doc (Document): Frappe document object
        doc_data (dict): Document data as dictionary
        access_token (str): WhatsApp access token (optional)
        app_id (str): WhatsApp App ID (optional)
    
    Returns:
        dict: Card payload for WhatsApp API
    """
    card_payload = {
        "components": []
    }
    
    # Add header component
    header_component = build_header_component(card, processed_params, doc, doc_data, access_token, app_id)
    if header_component:
        card_payload["components"].append(header_component)
    
    # Add body component
    body_component = build_body_component(card, processed_params, doc, doc_data)
    if body_component:
        card_payload["components"].append(body_component)
    
    # Add buttons component
    buttons_component = build_buttons_component(card, doc, doc_data)
    if buttons_component:
        card_payload["components"].append(buttons_component)
    else:
        # Add default button if no buttons are specified (Meta requires at least 1 button per card)
        default_button_component = {
            "type": "buttons",
            "buttons": [
                {
                    "type": "quick_reply",
                    "text": "Learn More"
                }
            ]
        }
        card_payload["components"].append(default_button_component)
    
    return card_payload


def build_header_component(card, processed_params, doc=None, doc_data=None, access_token=None, app_id=None):
    """
    Build header component for carousel card.
    
    Args:
        card: WhatsApp Carousel Cards document
        processed_params: Processed carousel parameters
        doc (Document): Frappe document object
        doc_data (dict): Document data as dictionary
        access_token (str): WhatsApp access token (optional)
        app_id (str): WhatsApp App ID (optional)
    
    Returns:
        dict: Header component payload
    """
    if card.header_type in ["IMAGE", "VIDEO"]:
        frappe.log_error("Header Debug", f"Building header component for card {card.card_index}, type: {card.header_type}")
        frappe.log_error("Header Debug", f"Card header_content: {card.header_content}")
        frappe.log_error("Header Debug", f"Card has whatsapp_handle attr: {hasattr(card, 'whatsapp_handle')}")
        if hasattr(card, 'whatsapp_handle'):
            frappe.log_error("Header Debug", f"Card whatsapp_handle value: {card.whatsapp_handle}")
        
        # Check if we already have a WhatsApp handle stored
        if hasattr(card, 'whatsapp_handle') and card.whatsapp_handle:
            frappe.log_error("Header Debug", f"Using stored WhatsApp handle for card {card.card_index}: {card.whatsapp_handle}")
            return {
                "type": "header",
                "format": card.header_type.lower(),
                "example": {
                    "header_handle": [card.whatsapp_handle]
                }
            }
        elif hasattr(card, 'name') and card.name:
            # Try to get the handle from the database
            stored_handle = frappe.db.get_value("WhatsApp Carousel Cards", card.name, "whatsapp_handle")
            frappe.log_error("Header Debug", f"Database lookup for card {card.name}: {stored_handle}")
            if stored_handle:
                frappe.log_error("Header Debug", f"Using database WhatsApp handle for card {card.card_index}: {stored_handle}")
                return {
                    "type": "header",
                    "format": card.header_type.lower(),
                    "example": {
                        "header_handle": [stored_handle]
                    }
                }
        
        # Upload attach field to WhatsApp and get handle
        if card.header_content:
            try:
                frappe.log_error("Header Debug", f"Attempting to upload header content: {card.header_content}")
                handle = upload_attach_to_whatsapp(card.header_content, access_token, app_id)
                frappe.log_error("Header Debug", f"Upload successful, got handle: {handle}")
                return {
                    "type": "header",
                    "format": card.header_type.lower(),
                    "example": {
                        "header_handle": [handle]
                    }
                }
            except Exception as e:
                frappe.log_error("Header Debug", f"Failed to upload header media: {str(e)}")
                # Fallback to direct URL if upload fails
                frappe.log_error("Header Debug", f"Falling back to direct URL: {card.header_content}")
                return {
                    "type": "header",
                    "format": card.header_type.lower(),
                    "example": {
                        "header_handle": [card.header_content]
                    }
                }
    
    return None


def build_body_component(card, processed_params, doc=None, doc_data=None):
    """
    Build body component for carousel card.
    
    Args:
        card: WhatsApp Carousel Cards document
        processed_params: Processed carousel parameters
        doc (Document): Frappe document object
        doc_data (dict): Document data as dictionary
    
    Returns:
        dict: Body component payload
    """
    if not card.body_text:
        return None
    
    body_text = card.body_text
    
    # Process dynamic content
    if processed_params and f"card_{card.card_index}" in processed_params["card_bodies"]:
        card_params = processed_params["card_bodies"][f"card_{card.card_index}"]
        body_text = process_dynamic_payload(body_text, doc, doc_data)
    
    body_component = {
        "type": "body",
        "text": body_text
    }
    
    # Add example for variables if any are present in the text
    if "{{" in body_text and "}}" in body_text:
        # Extract variable placeholders and create example values
        import re
        variables = re.findall(r'\{\{(\d+)\}\}', body_text)
        if variables:
            # Create example values for each variable
            example_values = []
            for var_num in variables:
                example_values.append(f"Sample{var_num}")
            
            body_component["example"] = {
                "body_text": [example_values]
            }
    
    return body_component


def build_buttons_component(card, doc=None, doc_data=None):
    """
    Build buttons component for carousel card.
    
    Args:
        card: WhatsApp Carousel Cards document
        doc (Document): Frappe document object
        doc_data (dict): Document data as dictionary
    
    Returns:
        dict: Buttons component payload
    """
    if not card.buttons:
        return None
    
    buttons = []
    for button in card.buttons:
        button_payload = build_button_payload(button, doc, doc_data)
        if button_payload:
            buttons.append(button_payload)
    
    if buttons:
        return {
            "type": "buttons",
            "buttons": buttons
        }
    
    return None


def build_button_payload(button, doc=None, doc_data=None):
    """
    Build individual button payload for carousel card.
    
    Args:
        button: WhatsApp Template Buttons document
        doc (Document): Frappe document object
        doc_data (dict): Document data as dictionary
    
    Returns:
        dict: Button payload for WhatsApp API
    """
    button_data = {
        "type": button.button_type.lower(),
        "text": button.button_text
    }
    
    # Add button-specific data based on type
    if button.button_type == "QUICK_REPLY":
        if button.payload:
            payload = process_dynamic_payload(button.payload, doc, doc_data)
            button_data["payload"] = payload
    elif button.button_type == "URL":
        if button.url:
            url = process_dynamic_payload(button.url, doc, doc_data)
            button_data["url"] = url
            
            # Add example for URL parameters if any are present
            if "{{" in url and "}}" in url:
                import re
                variables = re.findall(r'\{\{(\d+)\}\}', url)
                if variables:
                    # Create example values for each variable
                    example_values = []
                    for var_num in variables:
                        example_values.append(f"Sample{var_num}")
                    button_data["example"] = example_values
    elif button.button_type == "PHONE_NUMBER":
        if button.phone_number:
            phone = process_dynamic_payload(button.phone_number, doc, doc_data)
            button_data["phone_number"] = phone
    elif button.button_type == "COPY_CODE":
        if button.copy_code_example:
            example = process_dynamic_payload(button.copy_code_example, doc, doc_data)
            button_data["example"] = [example]
    elif button.button_type == "FLOW":
        if button.flow_token:
            flow_token = process_dynamic_payload(button.flow_token, doc, doc_data)
            button_data["flow_token"] = flow_token
    
    return button_data


def validate_carousel_template(template):
    """
    Validate carousel template configuration.
    
    Args:
        template: WhatsApp Template document
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not template.carousel_cards:
        return False, "Carousel template must have at least one card"
    
    if len(template.carousel_cards) > 10:
        return False, "Carousel template cannot have more than 10 cards"
    
    # Validate each card
    for card in template.carousel_cards:
        is_valid, error = validate_carousel_card(card)
        if not is_valid:
            return False, f"Card {card.card_index}: {error}"
    
    return True, None


def validate_carousel_card(card):
    """
    Validate individual carousel card.
    
    Args:
        card: WhatsApp Carousel Cards document
    
    Returns:
        tuple: (is_valid, error_message)
    """
    # Validate header
    if card.header_type in ["IMAGE", "VIDEO"]:
        if not card.header_content:
            return False, f"{card.header_type} header requires uploaded file"
    
    # Validate body
    if card.body_text and len(card.body_text) > 160:
        return False, "Body text must be 160 characters or less"
    
    # Validate buttons
    if card.buttons and len(card.buttons) > 2:
        return False, "Maximum 2 buttons allowed per card"
    # Note: We don't validate minimum buttons here since we add a default button if none exist
    
    return True, None 


def upload_attach_to_whatsapp(attach_field, access_token=None, app_id=None):
    """
    Upload an attach field file to WhatsApp using Resumable Upload API and return the handle.
    
    Args:
        attach_field (str): Attach field value (file URL)
        access_token (str): WhatsApp access token (optional, will get from settings)
        app_id (str): WhatsApp App ID (optional, will get from settings)
    
    Returns:
        str: Image handle for use in templates
    """
    if not access_token or not app_id:
        settings = frappe.get_doc("WhatsApp Settings")
        access_token = access_token or settings.get_password("token")
        app_id = app_id or settings.app_id  # We'll need to add this field to settings
    
    if not access_token or not app_id:
        raise Exception("WhatsApp settings not configured properly")
    
    # Get file document from attach field
    file_doc = frappe.get_doc("File", {"file_url": attach_field})
    
    # Get file content from Frappe file system
    file_path = file_doc.get_full_path()
    
    if not os.path.exists(file_path):
        raise Exception(f"File not found: {file_path}")
    
    # Get file info
    file_size = os.path.getsize(file_path)
    mime_type = file_doc.content_type or 'image/jpeg'
    
    frappe.logger().info(f"Uploading file: {file_doc.file_name}, Size: {file_size}, Type: {mime_type}")
    
    # Step 1: Create upload session using App ID
    session_url = f"https://graph.facebook.com/v23.0/{app_id}/uploads"
    
    # Use query parameters as per Meta documentation
    params = {
        "file_name": file_doc.file_name,
        "file_length": file_size,
        "file_type": mime_type,
        "access_token": access_token
    }
    
    try:
        frappe.logger().info("Creating upload session...")
        session_response = requests.post(session_url, params=params)
        
        if session_response.status_code == 200:
            session_data = session_response.json()
            
            session_id = session_data.get('id')
            if not session_id:
                raise Exception("Failed to get session ID")
            
            frappe.logger().info(f"Upload session created: {session_id}")
            
            # Step 2: Upload the file
            upload_url = f"https://graph.facebook.com/v23.0/{session_id}"
            
            upload_headers = {
                "Authorization": f"OAuth {access_token}",
                "file_offset": "0"
            }
            
            frappe.logger().info("Uploading file...")
            with open(file_path, 'rb') as file:
                upload_response = requests.post(upload_url, headers=upload_headers, data=file.read())
                upload_response.raise_for_status()
                upload_data = upload_response.json()
            
            asset_handle = upload_data.get('h')
            if not asset_handle:
                raise Exception("Failed to get asset handle")
            
            frappe.logger().info(f"File uploaded successfully! Asset handle: {asset_handle}")
            return asset_handle
            
        else:
            raise Exception(f"Session creation failed: {session_response.status_code} - {session_response.text}")
            
    except requests.exceptions.RequestException as e:
        frappe.logger().error(f"Upload failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            frappe.logger().error(f"Response: {e.response.text}")
        raise Exception(f"Failed to upload file: {e}") 