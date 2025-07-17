"""Create whatsapp template."""

# Copyright (c) 2022, Shridhar Patil and contributors
# For license information, please see license.txt
import os
import json
import frappe
import magic
from frappe.model.document import Document
from frappe.integrations.utils import make_post_request, make_request
from frappe.desk.form.utils import get_pdf_link
from ...utils.carousel_utils import validate_carousel_template, build_carousel_payload


class WhatsAppTemplates(Document):
    """Create whatsapp template."""

    def validate(self):
        if not self.language_code or self.has_value_changed("language"):
            lang_code = frappe.db.get_value("Language", self.language) or "en"
            self.language_code = lang_code.replace("-", "_")

        if self.header_type in ["IMAGE", "DOCUMENT"] and self.sample:
            self.get_session_id()
            self.get_media_id()

        # Validate carousel template if it's a carousel type
        if self.template_type == "Carousel":
            is_valid, error = validate_carousel_template(self)
            if not is_valid:
                frappe.throw(f"Carousel template validation failed: {error}")

        if not self.is_new():
            self.update_template()


    def get_session_id(self):
        """Upload media."""
        self.get_settings()
        file_path = self.get_absolute_path(self.sample)
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(file_path)

        payload = {
            'file_length': os.path.getsize(file_path),
            'file_type': file_type,
            'messaging_product': 'whatsapp'
        }

        response = make_post_request(
            f"{self._url}/{self._version}/{self._app_id}/uploads",
            headers=self._headers,
            data=json.loads(json.dumps(payload))
        )
        self._session_id = response['id']

    def get_media_id(self):
        self.get_settings()

        headers = {
                "authorization": f"OAuth {self._token}"
            }
        file_name = self.get_absolute_path(self.sample)
        with open(file_name, mode='rb') as file: # b is important -> binary
            file_content = file.read()

        payload = file_content
        response = make_post_request(
            f"{self._url}/{self._version}/{self._session_id}",
            headers=headers,
            data=payload
        )

        self._media_id = response['h']

    def get_absolute_path(self, file_name):
        if(file_name.startswith('/files/')):
            file_path = f'{frappe.utils.get_bench_path()}/sites/{frappe.utils.get_site_base_path()[2:]}/public{file_name}'
        if(file_name.startswith('/private/')):
            file_path = f'{frappe.utils.get_bench_path()}/sites/{frappe.utils.get_site_base_path()[2:]}{file_name}'
        return file_path


    def after_insert(self):
        if self.template_name:
            self.actual_name = self.template_name.lower().replace(" ", "_")

        self.get_settings()
        data = {
            "name": self.actual_name,
            "language": self.language_code,
            "category": self.category,
            "components": [],
        }

        body = {
            "type": "BODY",
            "text": self.template,
        }
        if self.sample_values:
            body.update({"example": {"body_text": [self.sample_values.split(",")]}})

        data["components"].append(body)
        if self.header_type:
            data["components"].append(self.get_header())

        # add footer
        if self.footer:
            data["components"].append({"type": "FOOTER", "text": self.footer})

        # Handle carousel templates
        if self.template_type == "Carousel":
            carousel_component = self.get_carousel_component()
            if carousel_component:
                data["components"].append(carousel_component)
        else:
            # add buttons if any
            if self.buttons:
                button_component = self.get_buttons_component()
                if button_component:
                    data["components"].append(button_component)

        try:
            response = make_post_request(
                f"{self._url}/{self._version}/{self._business_id}/message_templates",
                headers=self._headers,
                data=json.dumps(data),
            )
            self.id = response["id"]
            self.status = response["status"]
            self.db_update()
        except Exception as e:
            res = frappe.flags.integration_request.json()["error"]
            error_message = res.get("error_user_msg", res.get("message"))
            frappe.throw(
                msg=error_message,
                title=res.get("error_user_title", "Error"),
            )

    def update_template(self):
        """Update template to meta."""
        self.get_settings()
        data = {"components": []}

        body = {
            "type": "BODY",
            "text": self.template,
        }
        if self.sample_values:
            body.update({"example": {"body_text": [self.sample_values.split(",")]}})
        data["components"].append(body)
        if self.header_type:
            data["components"].append(self.get_header())
        if self.footer:
            data["components"].append({"type": "FOOTER", "text": self.footer})
        
        # add buttons if any
        if self.buttons:
            button_component = self.get_buttons_component()
            if button_component:
                data["components"].append(button_component)
                
        try:
            # post template to meta for update
            make_post_request(
                f"{self._url}/{self._version}/{self.id}",
                headers=self._headers,
                data=json.dumps(data),
            )
        except Exception as e:
            raise e
            # res = frappe.flags.integration_request.json()['error']
            # frappe.throw(
            #     msg=res.get('error_user_msg', res.get("message")),
            #     title=res.get("error_user_title", "Error"),
            # )

    def get_settings(self):
        """Get whatsapp settings."""
        settings = frappe.get_doc("WhatsApp Settings", "WhatsApp Settings")
        self._token = settings.get_password("token")
        self._url = settings.url
        self._version = settings.version
        self._business_id = settings.business_id
        self._app_id = settings.app_id

        self._headers = {
            "authorization": f"Bearer {self._token}",
            "content-type": "application/json",
        }

    def on_trash(self):
        self.get_settings()
        url = f"{self._url}/{self._version}/{self._business_id}/message_templates?name={self.actual_name}"
        try:
            make_request("DELETE", url, headers=self._headers)
        except Exception:
            res = frappe.flags.integration_request.json()["error"]
            if res.get("error_user_title") == "Message Template Not Found":
                frappe.msgprint(
                    "Deleted locally", res.get("error_user_title", "Error"), alert=True
                )
            else:
                frappe.throw(
                    msg=res.get("error_user_msg"),
                    title=res.get("error_user_title", "Error"),
                )

    def get_header(self):
        """Get header format."""
        header = {"type": "header", "format": self.header_type}
        if self.header_type == "TEXT":
            header["text"] = self.header
            if self.sample:
                samples = self.sample.split(", ")
                header.update({"example": {"header_text": samples}})
        else:
            pdf_link = ''
            if not self.sample:
                key = frappe.get_doc(self.doctype, self.name).get_document_share_key()
                link = get_pdf_link(self.doctype, self.name)
                pdf_link = f"{frappe.utils.get_url()}{link}&key={key}"
            header.update({"example": {"header_handle": [self._media_id]}})

        return header

    def get_buttons_component(self):
        """Get buttons component for template."""
        if not self.buttons or len(self.buttons) > 3:
            return None
            
        buttons = []
        for button in self.buttons:
            button_data = {
                "type": button.button_type,
                "text": button.button_text
            }
            
            # According to WhatsApp API docs, when creating templates:
            # - QUICK_REPLY buttons: only type and text
            # - URL buttons: type, text, and example URL
            # - PHONE_NUMBER buttons: type, text, and example phone_number
            # - COPY_CODE buttons: type, text, and example code
            
            if button.button_type == "URL" and button.url:
                button_data["url"] = button.url
            elif button.button_type == "PHONE_NUMBER" and button.phone_number:
                button_data["phone_number"] = button.phone_number
            elif button.button_type == "COPY_CODE" and button.copy_code_example:
                button_data["example"] = [button.copy_code_example]
            elif button.button_type == "FLOW" and button.flow_id:
                button_data["flow_id"] = button.flow_id
                if button.flow_action:
                    button_data["flow_action"] = button.flow_action
                if button.navigate_screen:
                    button_data["navigate_screen"] = button.navigate_screen
            # QUICK_REPLY buttons only need type and text for template creation
                
            buttons.append(button_data)
            
        return {
            "type": "BUTTONS",
            "buttons": buttons
        }

    def get_carousel_component(self):
        """Build carousel component for template creation."""
        if not self.carousel_cards:
            return None
        cards = []
        for card in self.carousel_cards:
            card_data = {
                "card_index": card.card_index,
                "components": []
            }
            # Header
            if card.header_type == "TEXT":
                card_data["components"].append({
                    "type": "header",
                    "text": card.header_text
                })
            elif card.header_type in ["IMAGE", "VIDEO"]:
                card_data["components"].append({
                    "type": "header",
                    "parameters": [
                        {
                            "type": card.header_type.lower(),
                            card.header_type.lower(): {
                                "link": card.header_content
                            }
                        }
                    ]
                })
            # Body
            if card.body_text:
                card_data["components"].append({
                    "type": "body",
                    "text": card.body_text
                })
            # Buttons
            if card.buttons:
                buttons = []
                for button in card.buttons:
                    button_data = {
                        "type": button.button_type,
                        "text": button.button_text
                    }
                    if button.button_type == "URL" and button.url:
                        button_data["url"] = button.url
                    elif button.button_type == "PHONE_NUMBER" and button.phone_number:
                        button_data["phone_number"] = button.phone_number
                    elif button.button_type == "COPY_CODE" and button.copy_code_example:
                        button_data["example"] = [button.copy_code_example]
                    elif button.button_type == "FLOW" and button.flow_id:
                        button_data["flow_id"] = button.flow_id
                        if button.flow_action:
                            button_data["flow_action"] = button.flow_action
                        if button.navigate_screen:
                            button_data["navigate_screen"] = button.navigate_screen
                    buttons.append(button_data)
                card_data["components"].append({
                    "type": "buttons",
                    "buttons": buttons
                })
            cards.append(card_data)
        return {
            "type": "carousel",
            "cards": cards
        }

    @frappe.whitelist()
    def preview(self):
        """Return a preview of the carousel template structure."""
        if self.template_type != "Carousel":
            return {"error": "Not a carousel template"}
        preview = {
            "template_name": self.template_name,
            "language": self.language_code,
            "category": self.category,
            "cards": []
        }
        for card in self.carousel_cards:
            card_info = {
                "card_index": card.card_index,
                "header_type": card.header_type,
                "header_content": card.header_content if card.header_type in ["IMAGE", "VIDEO"] else card.header_text,
                "body_text": card.body_text,
                "buttons": []
            }
            if card.buttons:
                for button in card.buttons:
                    card_info["buttons"].append({
                        "type": button.button_type,
                        "text": button.button_text
                    })
            preview["cards"].append(card_info)
        return preview


@frappe.whitelist()
def fetch():
    """Fetch templates from meta."""

    # get credentials
    settings = frappe.get_doc("WhatsApp Settings", "WhatsApp Settings")
    token = settings.get_password("token")
    url = settings.url
    version = settings.version
    business_id = settings.business_id

    headers = {"authorization": f"Bearer {token}", "content-type": "application/json"}

    try:
        response = make_request(
            "GET",
            f"{url}/{version}/{business_id}/message_templates",
            headers=headers,
        )
        
        frappe.log_error("API Response", f"Total templates received: {len(response.get('data', []))}")
        for template in response["data"]:
            frappe.log_error("Template Structure", f"Template {template.get('name')}: {template}")

        for template in response["data"]:
            # set flag to insert or update
            flags = 1
            if frappe.db.exists("WhatsApp Templates", {"actual_name": template["name"]}):
                doc = frappe.get_doc("WhatsApp Templates", {"actual_name": template["name"]})
            else:
                flags = 0
                doc = frappe.new_doc("WhatsApp Templates")
                doc.template_name = template["name"]
                doc.actual_name = template["name"]

            doc.status = template["status"]
            doc.language_code = template["language"]
            doc.category = template["category"]
            doc.id = template["id"]

            # update components
            frappe.log_error("Template Processing", f"Processing template {doc.name} with {len(template.get('components', []))} components")
            frappe.log_error("All Components", f"All components for {doc.name}: {template.get('components', [])}")

            # Reset carousel fields
            doc.template_type = "Template"
            doc.carousel_cards = []

            for component in template["components"]:
                frappe.log_error("Component Type", f"Processing component type: {component.get('type')} for template {doc.name}")
                frappe.log_error("Component Details", f"Component details: {component}")

                # update header
                if component["type"] == "HEADER":
                    doc.header_type = component["format"]

                    # if format is text update sample text
                    if component["format"] == "TEXT":
                        doc.header = component["text"]
                # Update footer text
                elif component["type"] == "FOOTER":
                    doc.footer = component["text"]

                # update template text
                elif component["type"] == "BODY":
                    doc.template = component["text"]
                    if component.get("example"):
                        doc.sample_values = ",".join(
                            component["example"]["body_text"][0]
                        )

                # update buttons
                elif component["type"] == "BUTTONS":
                    # Debug: Log the button component structure
                    frappe.log_error("Button Component", f"Processing buttons for template {doc.name}: {component}")
                    
                    # Clear existing buttons first
                    if flags:
                        # Delete existing buttons for this template
                        frappe.db.sql("""
                            DELETE FROM `tabWhatsApp Template Buttons` 
                            WHERE parent = %s AND parenttype = 'WhatsApp Templates'
                        """, doc.name)
                    
                    # Add new buttons
                    buttons_list = component.get("buttons", [])
                    frappe.log_error("Button Count", f"Found {len(buttons_list)} buttons")
                    
                    for idx, button in enumerate(buttons_list):
                        frappe.log_error("Button Details", f"Processing button {idx}: {button}")
                        
                        # Skip unsupported button types (if any)
                        if button.get("type") not in ["QUICK_REPLY", "URL", "PHONE_NUMBER", "COPY_CODE", "FLOW"]:
                            frappe.log_error("Skipped Button", f"Skipping unsupported button type: {button.get('type')}")
                            continue
                        
                        button_doc = frappe.new_doc("WhatsApp Template Buttons")
                        button_doc.button_text = button.get("text", "")
                        button_doc.button_type = button.get("type", "")
                        
                        if button.get("type") == "QUICK_REPLY":
                            # For QUICK_REPLY, no payload needed in template creation
                            pass
                        elif button.get("type") == "URL":
                            button_doc.url = button.get("url", "")
                        elif button.get("type") == "PHONE_NUMBER":
                            button_doc.phone_number = button.get("phone_number", "")
                        elif button.get("type") == "COPY_CODE":
                            button_doc.copy_code_example = button.get("example", [""])[0] if button.get("example") else ""
                        elif button.get("type") == "FLOW":
                            # For FLOW buttons, we store the flow_id from template
                            # The flow_token will be set in notification parameters when sending
                            button_doc.flow_id = button.get("flow_id", "")
                            button_doc.flow_action = button.get("flow_action", "")
                            button_doc.navigate_screen = button.get("navigate_screen", "")
                            # Note: flow_token is not stored in template, it's set in notification parameters
                        
                        button_doc.parent = doc.name
                        button_doc.parenttype = "WhatsApp Templates"
                        button_doc.parentfield = "buttons"
                        button_doc.idx = idx + 1
                        
                        try:
                            button_doc.db_insert()
                            frappe.log_error("Button Success", f"Successfully inserted button: {button_doc.button_text} of type {button_doc.button_type}")
                        except Exception as e:
                            frappe.log_error("Button Error", f"Failed to insert button: {e}")

                # update carousel
                elif component["type"] == "CAROUSEL":
                    doc.template_type = "Carousel"
                    # Clear existing carousel cards
                    if flags:
                        frappe.db.sql("""
                            DELETE FROM `tabWhatsApp Carousel Cards` 
                            WHERE parent = %s AND parenttype = 'WhatsApp Templates'
                        """, doc.name)
                    cards_list = component.get("cards", [])
                    for card in cards_list:
                        card_doc = frappe.new_doc("WhatsApp Carousel Cards")
                        card_doc.card_index = card.get("card_index", 0)
                        # Parse card components
                        for c in card.get("components", []):
                            if c.get("type") == "header":
                                if "text" in c:
                                    card_doc.header_type = "TEXT"
                                    card_doc.header_text = c["text"]
                                elif "parameters" in c:
                                    param = c["parameters"][0]
                                    if param["type"] == "image":
                                        card_doc.header_type = "IMAGE"
                                        card_doc.header_content = param["image"]["link"]
                                    elif param["type"] == "video":
                                        card_doc.header_type = "VIDEO"
                                        card_doc.header_content = param["video"]["link"]
                            elif c.get("type") == "body":
                                if "text" in c:
                                    card_doc.body_text = c["text"]
                        card_doc.parent = doc.name
                        card_doc.parenttype = "WhatsApp Templates"
                        card_doc.parentfield = "carousel_cards"
                        card_doc.idx = card.get("card_index", 0) + 1
                        try:
                            card_doc.db_insert()
                            frappe.log_error("Carousel Card Success", f"Inserted card {card_doc.card_index}")
                        except Exception as e:
                            frappe.log_error("Carousel Card Error", f"Failed to insert card: {e}")
            doc.save(ignore_permissions=True)
        frappe.msgprint("Templates fetched and updated successfully!")
    except Exception as e:
        frappe.log_error("Fetch Error", str(e))
        frappe.throw(f"Failed to fetch templates: {e}")
