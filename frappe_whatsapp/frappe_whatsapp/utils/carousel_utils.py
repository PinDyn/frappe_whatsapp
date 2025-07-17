# Copyright (c) 2025, Frappe Whatsapp and Contributors
# See license.txt

import frappe
import re
from frappe.model.document import Document
from .button_utils import process_dynamic_payload


def build_carousel_payload(template, carousel_parameters=None, doc=None, doc_data=None):
    """
    Build carousel payload for WhatsApp API.
    
    Args:
        template: WhatsApp Template document
        carousel_parameters: List of carousel parameter documents
        doc (Document): Frappe document object
        doc_data (dict): Document data as dictionary
    
    Returns:
        dict: Carousel payload for WhatsApp API
    """
    if not template.carousel_cards:
        return None
    
    # Process carousel parameters
    processed_params = process_carousel_parameters(carousel_parameters, doc, doc_data)
    
    # Build carousel component
    carousel_component = {
        "type": "carousel",
        "cards": []
    }
    
    # Process each card
    for card in template.carousel_cards:
        card_payload = build_card_payload(card, processed_params, doc, doc_data)
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


def build_card_payload(card, processed_params, doc=None, doc_data=None):
    """
    Build individual card payload for carousel.
    
    Args:
        card: WhatsApp Carousel Cards document
        processed_params: Processed carousel parameters
        doc (Document): Frappe document object
        doc_data (dict): Document data as dictionary
    
    Returns:
        dict: Card payload for WhatsApp API
    """
    card_payload = {
        "card_index": card.card_index,
        "components": []
    }
    
    # Add header component
    header_component = build_header_component(card, processed_params, doc, doc_data)
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
    
    return card_payload


def build_header_component(card, processed_params, doc=None, doc_data=None):
    """
    Build header component for carousel card.
    
    Args:
        card: WhatsApp Carousel Cards document
        processed_params: Processed carousel parameters
        doc (Document): Frappe document object
        doc_data (dict): Document data as dictionary
    
    Returns:
        dict: Header component payload
    """
    if card.header_type == "TEXT":
        return {
            "type": "header",
            "text": card.header_text
        }
    elif card.header_type in ["IMAGE", "VIDEO"]:
        header_content = card.header_content
        
        # Process dynamic content if needed
        if processed_params and f"card_{card.card_index}" in processed_params["card_headers"]:
            card_params = processed_params["card_headers"][f"card_{card.card_index}"]
            header_content = process_dynamic_payload(header_content, doc, doc_data)
        
        return {
            "type": "header",
            "parameters": [
                {
                    "type": card.header_type.lower(),
                    card.header_type.lower(): {
                        "link": header_content
                    }
                }
            ]
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
    
    return {
        "type": "body",
        "parameters": [
            {
                "type": "text",
                "text": body_text
            }
        ]
    }


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
    if card.header_type == "TEXT":
        if not card.header_text:
            return False, "Text header requires header text"
        if len(card.header_text) > 60:
            return False, "Text header must be 60 characters or less"
    elif card.header_type in ["IMAGE", "VIDEO"]:
        if not card.header_content:
            return False, f"{card.header_type} header requires content URL"
    
    # Validate body
    if card.body_text and len(card.body_text) > 160:
        return False, "Body text must be 160 characters or less"
    
    # Validate buttons
    if card.buttons and len(card.buttons) > 2:
        return False, "Maximum 2 buttons allowed per card"
    
    return True, None 