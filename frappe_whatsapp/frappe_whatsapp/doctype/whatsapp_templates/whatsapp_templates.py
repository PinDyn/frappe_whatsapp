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
                "type": button.button_type
            }
            
            if button.button_type == "QUICK_REPLY":
                button_data.update({
                    "text": button.button_text,
                    "payload": button.payload
                })
            elif button.button_type == "URL":
                button_data.update({
                    "text": button.button_text,
                    "url": button.url
                })
            elif button.button_type == "PHONE_NUMBER":
                button_data.update({
                    "text": button.button_text,
                    "phone_number": button.phone_number
                })
                
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
                    # Clear existing buttons first
                    if flags:
                        # Delete existing buttons for this template
                        frappe.db.sql("""
                            DELETE FROM `tabWhatsApp Template Buttons` 
                            WHERE parent = %s AND parenttype = 'WhatsApp Templates'
                        """, doc.name)
                    
                    # Add new buttons
                    for button in component.get("buttons", []):
                        button_doc = frappe.new_doc("WhatsApp Template Buttons")
                        button_doc.button_text = button.get("text", "")
                        button_doc.button_type = button.get("type", "")
                        
                        if button.get("type") == "QUICK_REPLY":
                            button_doc.payload = button.get("payload", "")
                        elif button.get("type") == "URL":
                            button_doc.url = button.get("url", "")
                        elif button.get("type") == "PHONE_NUMBER":
                            button_doc.phone_number = button.get("phone_number", "")
                        
                        button_doc.parent = doc.name
                        button_doc.parenttype = "WhatsApp Templates"
                        button_doc.parentfield = "buttons"
                        button_doc.idx = len(doc.buttons) + 1
                        button_doc.db_insert()

            # if document exists update else insert
            # used db_update and db_insert to ignore hooks
            if flags:
                doc.db_update()
            else:
                doc.db_insert()
            frappe.db.commit()

    except Exception as e:
        res = frappe.flags.integration_request.json()["error"]
        error_message = res.get("error_user_msg", res.get("message"))
        frappe.throw(
            msg=error_message,
            title=res.get("error_user_title", "Error"),
        )

    return "Successfully fetched templates from meta"
