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


class WhatsAppTemplates(Document):
    """Create whatsapp template."""

    def validate(self):
        if not self.language_code or self.has_value_changed("language"):
            lang_code = frappe.db.get_value("Language", self.language) or "en"
            self.language_code = lang_code.replace("-", "_")

        if self.header_type in ["IMAGE", "DOCUMENT"] and self.sample:
            self.get_session_id()
            self.get_media_id()

        # Skip update_template during fetch operations to avoid _media_id errors
        if not self.is_new() and not getattr(self, '_skip_update_template', False):
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
        # Skip template creation in Meta if this is a fetch operation
        if getattr(self, '_skip_after_insert', False):
            return
            
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
            header_component = self.get_header()
            # Only add header component if it has the required fields
            if self.header_type == "TEXT" or (self.header_type in ["IMAGE", "DOCUMENT"] and "example" in header_component):
                data["components"].append(header_component)

        # add footer
        if self.footer:
            data["components"].append({"type": "FOOTER", "text": self.footer})

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
        """Update template to meta.
        
        Note: This method should only be called for locally created templates
        that have media files attached. For templates fetched from Meta,
        this method will be skipped to avoid _media_id errors.
        """
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
            header_component = self.get_header()
            # Only add header component if it has the required fields
            if self.header_type == "TEXT" or (self.header_type in ["IMAGE", "DOCUMENT"] and "example" in header_component):
                data["components"].append(header_component)
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
            # For IMAGE and DOCUMENT headers, we need to handle different scenarios:
            # 1. Template creation: We have _media_id and need to include example
            # 2. Template fetching: We don't have _media_id and should skip example
            # 3. Template update: We might have _media_id if updating locally created template
            
            if hasattr(self, '_media_id') and self._media_id:
                # This is for template creation or update of locally created templates
                header.update({"example": {"header_handle": [self._media_id]}})
            elif self.header_type in ["IMAGE", "DOCUMENT"] and self.sample:
                # This is for template creation where we have a sample file but no _media_id yet
                # We need to get the media_id first
                if not hasattr(self, '_media_id'):
                    self.get_session_id()
                    self.get_media_id()
                header.update({"example": {"header_handle": [self._media_id]}})
            # If we don't have _media_id and no sample, this is likely a fetched template
            # In this case, we skip the example field to avoid Meta API errors

        return header

    def get_buttons_component(self):
        """Get buttons component for template."""
        if not self.buttons or len(self.buttons) > 10:
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
                # Skip after_insert during fetch to prevent recreating template in Meta
                doc._skip_after_insert = True

            doc.status = template["status"]
            doc.language_code = template["language"]
            doc.category = template["category"]
            doc.id = template["id"]

            # update components
            for component in template["components"]:

                # update header
                if component["type"] == "HEADER":
                    doc.header_type = component["format"]

                    # if format is text update sample text
                    if component["format"] == "TEXT":
                        doc.header = component["text"]
                    # For IMAGE and DOCUMENT headers, we don't store the media_id from Meta
                    # as it's only needed for template creation/updates, not for fetching
                    # The template will work for sending messages without the media_id
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
                    # Clear existing buttons using proper child table handling
                    doc.buttons = []
                    
                    # Add new buttons
                    buttons_list = component.get("buttons", [])
                    
                    for idx, button in enumerate(buttons_list):
                        # Skip unsupported button types (if any)
                        if button.get("type") not in ["QUICK_REPLY", "URL", "PHONE_NUMBER", "COPY_CODE", "FLOW"]:
                            continue
                        
                        # Create button row for child table (with explicit doctype)
                        button_row = {
                            "doctype": "WhatsApp Template Buttons",
                            "button_text": button.get("text", ""),
                            "button_type": button.get("type", ""),
                            "idx": idx + 1
                        }
                        
                        # Set type-specific fields
                        if button.get("type") == "QUICK_REPLY":
                            # For QUICK_REPLY, no additional fields needed in template creation
                            pass
                        elif button.get("type") == "URL":
                            button_row["url"] = button.get("url", "")
                        elif button.get("type") == "PHONE_NUMBER":
                            button_row["phone_number"] = button.get("phone_number", "")
                        elif button.get("type") == "COPY_CODE":
                            button_row["copy_code_example"] = button.get("example", [""])[0] if button.get("example") else ""
                        elif button.get("type") == "FLOW":
                            # For FLOW buttons, store the flow configuration
                            button_row["flow_id"] = str(button.get("flow_id", ""))
                            button_row["flow_action"] = button.get("flow_action", "")
                            button_row["navigate_screen"] = button.get("navigate_screen", "")
                        
                        # Append to child table
                        doc.append("buttons", button_row)

            # Save document with child tables properly handled
            # Use save() to ensure child tables are processed correctly
            try:
                # Skip template update during fetch to avoid _media_id errors
                doc._skip_update_template = True
                # Preserve the skip flag for after_insert
                if hasattr(doc, '_skip_after_insert'):
                    doc._skip_after_insert = True
                doc.save(ignore_permissions=True)
                frappe.db.commit()
            except Exception as e:
                frappe.log_error("Template Save Error", f"Failed to save template {doc.actual_name}: {str(e)}")
                frappe.db.rollback()
                raise

    except Exception as e:
        # Handle API errors if integration_request exists
        if hasattr(frappe.flags, 'integration_request') and frappe.flags.integration_request:
            try:
                res = frappe.flags.integration_request.json().get("error", {})
                error_message = res.get("error_user_msg", res.get("message", str(e)))
                frappe.throw(
                    msg=error_message,
                    title=res.get("error_user_title", "Error"),
                )
            except (AttributeError, KeyError, TypeError):
                # Fallback if integration_request format is unexpected
                frappe.throw(f"Error fetching templates: {str(e)}")
        else:
            # No integration_request, just throw the original error
            frappe.throw(f"Error fetching templates: {str(e)}")

    return "Successfully fetched templates from meta"
