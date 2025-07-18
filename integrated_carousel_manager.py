#!/usr/bin/env python3
"""
Integrated Carousel Manager for Frappe WhatsApp App

This script provides a complete workflow for:
1. Uploading media files to WhatsApp
2. Creating carousel templates
3. Checking template status
4. Sending carousel messages

Usage:
    python integrated_carousel_manager.py --action upload --file /path/to/image.jpg
    python integrated_carousel_manager.py --action create --template "Test Carousel"
    python integrated_carousel_manager.py --action status --template "Test Carousel"
    python integrated_carousel_manager.py --action send --template "Test Carousel" --to "1234567890"
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime
import frappe
from frappe_whatsapp.frappe_whatsapp.utils.carousel_utils import (
    build_carousel_payload,
    upload_attach_to_whatsapp
)

class IntegratedCarouselManager:
    def __init__(self):
        """Initialize the carousel manager with WhatsApp settings."""
        self.settings = frappe.get_doc("WhatsApp Settings")
        self.access_token = self.settings.get_password("token")
        self.app_id = self.settings.app_id
        self.business_id = self.settings.business_id
        self.phone_id = self.settings.phone_id
        
        if not all([self.access_token, self.app_id, self.business_id, self.phone_id]):
            raise Exception("WhatsApp settings not configured properly. Please check token, app_id, business_id, and phone_id.")
        
        # Create data directory for storing uploads and templates
        self.data_dir = os.path.join(os.path.dirname(__file__), "carousel_data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.uploads_file = os.path.join(self.data_dir, "uploads.json")
        self.templates_file = os.path.join(self.data_dir, "templates.json")
        
        # Load existing data
        self.uploads = self._load_json(self.uploads_file, {})
        self.templates = self._load_json(self.templates_file, {})
    
    def _load_json(self, file_path, default=None):
        """Load JSON data from file."""
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load {file_path}: {e}")
        return default or {}
    
    def _save_json(self, file_path, data):
        """Save JSON data to file."""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save {file_path}: {e}")
    
    def upload_media(self, file_path):
        """
        Upload a media file to WhatsApp using the Resumable Upload API.
        
        Args:
            file_path (str): Path to the file to upload
            
        Returns:
            dict: Upload result with handle and metadata
        """
        if not os.path.exists(file_path):
            raise Exception(f"File not found: {file_path}")
        
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        # Determine MIME type
        mime_type = 'image/jpeg'  # Default
        if file_name.lower().endswith('.png'):
            mime_type = 'image/png'
        elif file_name.lower().endswith('.gif'):
            mime_type = 'image/gif'
        elif file_name.lower().endswith('.mp4'):
            mime_type = 'video/mp4'
        
        print(f"Uploading {file_name} ({file_size} bytes, {mime_type})...")
        
        # Step 1: Create upload session
        session_url = f"https://graph.facebook.com/v23.0/{self.app_id}/uploads"
        params = {
            "file_name": file_name,
            "file_length": file_size,
            "file_type": mime_type,
            "access_token": self.access_token
        }
        
        try:
            print("Creating upload session...")
            session_response = requests.post(session_url, params=params)
            session_response.raise_for_status()
            session_data = session_response.json()
            
            session_id = session_data.get('id')
            if not session_id:
                raise Exception("Failed to get session ID from response")
            
            print(f"Upload session created: {session_id}")
            
            # Step 2: Upload the file
            upload_url = f"https://graph.facebook.com/v23.0/{session_id}"
            upload_headers = {
                "Authorization": f"OAuth {self.access_token}",
                "file_offset": "0"
            }
            
            print("Uploading file...")
            with open(file_path, 'rb') as file:
                upload_response = requests.post(upload_url, headers=upload_headers, data=file.read())
                upload_response.raise_for_status()
                upload_data = upload_response.json()
            
            asset_handle = upload_data.get('h')
            if not asset_handle:
                raise Exception("Failed to get asset handle from response")
            
            print(f"File uploaded successfully! Asset handle: {asset_handle}")
            
            # Save upload info
            upload_info = {
                "file_name": file_name,
                "file_path": file_path,
                "file_size": file_size,
                "mime_type": mime_type,
                "asset_handle": asset_handle,
                "uploaded_at": datetime.now().isoformat(),
                "session_id": session_id
            }
            
            self.uploads[asset_handle] = upload_info
            self._save_json(self.uploads_file, self.uploads)
            
            return upload_info
            
        except requests.exceptions.RequestException as e:
            print(f"Upload failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            raise Exception(f"Failed to upload file: {e}")
    
    def create_carousel_template(self, template_name, cards_data):
        """
        Create a carousel template using the WhatsApp Business API.
        
        Args:
            template_name (str): Name for the template
            cards_data (list): List of card data dictionaries
            
        Returns:
            dict: Template creation result
        """
        print(f"Creating carousel template: {template_name}")
        
        # Build carousel payload
        carousel_payload = {
            "name": template_name,
            "language": "en_US",
            "category": "MARKETING",
            "components": [
                {
                    "type": "carousel",
                    "cards": []
                }
            ]
        }
        
        # Process each card
        for i, card_data in enumerate(cards_data):
            card = {
                "components": []
            }
            
            # Add header if image handle provided
            if card_data.get("image_handle"):
                card["components"].append({
                    "type": "header",
                    "format": "image",
                    "example": {
                        "header_handle": [card_data["image_handle"]]
                    }
                })
            
            # Add body
            if card_data.get("body_text"):
                body_component = {
                    "type": "body",
                    "text": card_data["body_text"]
                }
                
                # Add example if variables present
                if "{{" in card_data["body_text"] and "}}" in card_data["body_text"]:
                    import re
                    variables = re.findall(r'\{\{(\d+)\}\}', card_data["body_text"])
                    if variables:
                        example_values = [f"Sample{var_num}" for var_num in variables]
                        body_component["example"] = {
                            "body_text": [example_values]
                        }
                
                card["components"].append(body_component)
            
            # Add buttons
            buttons = card_data.get("buttons", [])
            if buttons:
                button_components = []
                for button in buttons:
                    button_component = {
                        "type": button.get("type", "quick_reply").lower(),
                        "text": button["text"]
                    }
                    
                    if button.get("payload"):
                        button_component["payload"] = button["payload"]
                    elif button.get("url"):
                        button_component["url"] = button["url"]
                    
                    button_components.append(button_component)
                
                card["components"].append({
                    "type": "buttons",
                    "buttons": button_components
                })
            else:
                # Add default button
                card["components"].append({
                    "type": "buttons",
                    "buttons": [
                        {
                            "type": "quick_reply",
                            "text": "Learn More"
                        }
                    ]
                })
            
            carousel_payload["components"][0]["cards"].append(card)
        
        # Create template via WhatsApp Business API
        url = f"https://graph.facebook.com/v23.0/{self.business_id}/message_templates"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            print("Sending template creation request...")
            print(f"Payload: {json.dumps(carousel_payload, indent=2)}")
            
            response = requests.post(url, headers=headers, json=carousel_payload)
            
            print(f"Response status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                template_id = result.get("id")
                
                if template_id:
                    template_info = {
                        "name": template_name,
                        "template_id": template_id,
                        "status": "PENDING",
                        "created_at": datetime.now().isoformat(),
                        "cards": cards_data,
                        "payload": carousel_payload
                    }
                    
                    self.templates[template_name] = template_info
                    self._save_json(self.templates_file, self.templates)
                    
                    print(f"Template created successfully! ID: {template_id}")
                    return template_info
                else:
                    raise Exception("No template ID in response")
            else:
                raise Exception(f"Template creation failed: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Template creation failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            raise Exception(f"Failed to create template: {e}")
    
    def check_template_status(self, template_name):
        """
        Check the status of a template.
        
        Args:
            template_name (str): Name of the template
            
        Returns:
            dict: Template status information
        """
        if template_name not in self.templates:
            raise Exception(f"Template '{template_name}' not found in local records")
        
        template_info = self.templates[template_name]
        template_id = template_info["template_id"]
        
        print(f"Checking status for template: {template_name} (ID: {template_id})")
        
        url = f"https://graph.facebook.com/v23.0/{template_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                status = result.get("status", "UNKNOWN")
                
                # Update local status
                template_info["status"] = status
                template_info["last_checked"] = datetime.now().isoformat()
                template_info["meta_response"] = result
                
                self.templates[template_name] = template_info
                self._save_json(self.templates_file, self.templates)
                
                print(f"Template status: {status}")
                return template_info
            else:
                raise Exception(f"Status check failed: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Status check failed: {e}")
            raise Exception(f"Failed to check template status: {e}")
    
    def send_carousel_message(self, template_name, to_number, parameters=None):
        """
        Send a carousel message using a template.
        
        Args:
            template_name (str): Name of the template to use
            to_number (str): Recipient phone number
            parameters (dict): Template parameters (optional)
            
        Returns:
            dict: Send result
        """
        if template_name not in self.templates:
            raise Exception(f"Template '{template_name}' not found in local records")
        
        template_info = self.templates[template_name]
        
        if template_info["status"] != "APPROVED":
            raise Exception(f"Template is not approved. Current status: {template_info['status']}")
        
        print(f"Sending carousel message to {to_number} using template: {template_name}")
        
        # Build message payload
        message_payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": "en_US"
                }
            }
        }
        
        # Add parameters if provided
        if parameters:
            message_payload["template"]["components"] = []
            
            # Add body parameters if any
            body_params = parameters.get("body", [])
            if body_params:
                message_payload["template"]["components"].append({
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": str(param)} for param in body_params
                    ]
                })
        
        # Send message
        url = f"https://graph.facebook.com/v23.0/{self.phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            print("Sending message...")
            print(f"Payload: {json.dumps(message_payload, indent=2)}")
            
            response = requests.post(url, headers=headers, json=message_payload)
            
            print(f"Response status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get("messages", [{}])[0].get("id")
                
                send_info = {
                    "template_name": template_name,
                    "to_number": to_number,
                    "message_id": message_id,
                    "sent_at": datetime.now().isoformat(),
                    "parameters": parameters,
                    "response": result
                }
                
                print(f"Message sent successfully! ID: {message_id}")
                return send_info
            else:
                raise Exception(f"Message sending failed: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Message sending failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            raise Exception(f"Failed to send message: {e}")
    
    def list_uploads(self):
        """List all uploaded media files."""
        if not self.uploads:
            print("No uploads found.")
            return
        
        print(f"\nUploaded Media Files ({len(self.uploads)}):")
        print("-" * 80)
        for handle, info in self.uploads.items():
            print(f"Handle: {handle}")
            print(f"File: {info['file_name']}")
            print(f"Size: {info['file_size']} bytes")
            print(f"Type: {info['mime_type']}")
            print(f"Uploaded: {info['uploaded_at']}")
            print("-" * 80)
    
    def list_templates(self):
        """List all created templates."""
        if not self.templates:
            print("No templates found.")
            return
        
        print(f"\nCreated Templates ({len(self.templates)}):")
        print("-" * 80)
        for name, info in self.templates.items():
            print(f"Name: {name}")
            print(f"ID: {info['template_id']}")
            print(f"Status: {info['status']}")
            print(f"Created: {info['created_at']}")
            print(f"Cards: {len(info['cards'])}")
            print("-" * 80)


def main():
    parser = argparse.ArgumentParser(description="Integrated Carousel Manager for Frappe WhatsApp")
    parser.add_argument("--action", required=True, 
                       choices=["upload", "create", "status", "send", "list-uploads", "list-templates"],
                       help="Action to perform")
    parser.add_argument("--file", help="File path for upload")
    parser.add_argument("--template", help="Template name")
    parser.add_argument("--to", help="Recipient phone number for sending")
    parser.add_argument("--cards", help="JSON file with cards data for template creation")
    parser.add_argument("--parameters", help="JSON string with template parameters for sending")
    
    args = parser.parse_args()
    
    try:
        manager = IntegratedCarouselManager()
        
        if args.action == "upload":
            if not args.file:
                print("Error: --file is required for upload action")
                return
            result = manager.upload_media(args.file)
            print(f"Upload successful! Handle: {result['asset_handle']}")
            
        elif args.action == "create":
            if not args.template or not args.cards:
                print("Error: --template and --cards are required for create action")
                return
            with open(args.cards, 'r') as f:
                cards_data = json.load(f)
            result = manager.create_carousel_template(args.template, cards_data)
            print(f"Template created! ID: {result['template_id']}")
            
        elif args.action == "status":
            if not args.template:
                print("Error: --template is required for status action")
                return
            result = manager.check_template_status(args.template)
            print(f"Template status: {result['status']}")
            
        elif args.action == "send":
            if not args.template or not args.to:
                print("Error: --template and --to are required for send action")
                return
            parameters = None
            if args.parameters:
                parameters = json.loads(args.parameters)
            result = manager.send_carousel_message(args.template, args.to, parameters)
            print(f"Message sent! ID: {result['message_id']}")
            
        elif args.action == "list-uploads":
            manager.list_uploads()
            
        elif args.action == "list-templates":
            manager.list_templates()
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 