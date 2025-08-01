# Copyright (c) 2022, Shridhar Patil and contributors
# For license information, please see license.txt
import json
import frappe
from frappe.model.document import Document
from frappe.integrations.utils import make_post_request
from ...utils.button_utils import get_template_buttons_with_dynamic_values


class WhatsAppMessage(Document):
    """Send whats app messages."""

    def before_insert(self):
        """Send message."""
        if self.type == "Outgoing" and self.message_type != "Template":
            if self.attach and not self.attach.startswith("http"):
                link = frappe.utils.get_url() + "/" + self.attach
            else:
                link = self.attach

            data = {
                "messaging_product": "whatsapp",
                "to": self.format_number(self.to),
                "type": self.content_type,
            }
            if self.is_reply and self.reply_to_message_id:
                data["context"] = {"message_id": self.reply_to_message_id}
            if self.content_type in ["document", "image", "video"]:
                data[self.content_type.lower()] = {
                    "link": link,
                    "caption": self.message,
                }
            elif self.content_type == "reaction":
                data["reaction"] = {
                    "message_id": self.reply_to_message_id,
                    "emoji": self.message,
                }
            elif self.content_type == "text":
                data["text"] = {"preview_url": True, "body": self.message}

            elif self.content_type == "audio":
                data["text"] = {"link": link}

            try:
                self.notify(data)
                self.status = "Success"
            except Exception as e:
                self.status = "Failed"
                frappe.throw(f"Failed to send message {str(e)}")
        elif self.type == "Outgoing" and self.message_type == "Template" and not self.message_id:
            self.send_template()

    def send_template(self):
        """Send template."""
        template = frappe.get_doc("WhatsApp Templates", self.template)
        data = {
            "messaging_product": "whatsapp",
            "to": self.format_number(self.to),
            "type": "template",
            "template": {
                "name": template.actual_name or template.template_name,
                "language": {"code": template.language_code},
                "components": [],
            },
        }

        if template.sample_values:
            field_names = template.field_names.split(",") if template.field_names else template.sample_values.split(",")
            parameters = []
            template_parameters = []

            if self.flags.custom_ref_doc:
                custom_values = self.flags.custom_ref_doc
                for field_name in field_names:
                    value = custom_values.get(field_name.strip())
                    parameters.append({"type": "text", "text": value})
                    template_parameters.append(value)                    

            else:
                ref_doc = frappe.get_doc(self.reference_doctype, self.reference_name)
                for field_name in field_names:
                    value = ref_doc.get_formatted(field_name.strip())

                    parameters.append({"type": "text", "text": value})
                    template_parameters.append(value)


            self.template_parameters = json.dumps(template_parameters)

            data["template"]["components"].append(
                {
                    "type": "body",
                    "parameters": parameters,
                }
            )

        if template.header_type and template.sample:
            if template.header_type == 'IMAGE':
                if template.sample.startswith("http"):
                    url = f'{template.sample}'
                else:
                    url = f'{frappe.utils.get_url()}{template.sample}'
                data['template']['components'].append({
                    "type": "header",
                    "parameters": [{
                        "type": "image",
                        "image": {
                            "link": url
                        }
                    }]
                })

        # Add buttons if template has them
        if template.buttons:
            button_component = self.get_template_buttons_component(template)
            if button_component:
                data["template"]["components"].append(button_component)

        self.notify(data)

    def notify(self, data):
        """Notify."""
        settings = frappe.get_doc(
            "WhatsApp Settings",
            "WhatsApp Settings",
        )
        token = settings.get_password("token")

        headers = {
            "authorization": f"Bearer {token}",
            "content-type": "application/json",
        }
        try:
            response = make_post_request(
                f"{settings.url}/{settings.version}/{settings.phone_id}/messages",
                headers=headers,
                data=json.dumps(data),
            )
            self.message_id = response["messages"][0]["id"]

        except Exception as e:
            res = frappe.flags.integration_request.json()["error"]
            error_message = res.get("Error", res.get("message"))
            frappe.get_doc(
                {
                    "doctype": "WhatsApp Notification Log",
                    "template": "Text Message",
                    "meta_data": frappe.flags.integration_request.json(),
                }
            ).insert(ignore_permissions=True)

            frappe.throw(msg=error_message, title=res.get("error_user_title", "Error"))

    def format_number(self, number):
        """Format number."""
        if number.startswith("+"):
            number = number[1 : len(number)]

        return number

    def get_template_buttons_component(self, template):
        """Get buttons component for template message."""
        if not template.buttons or len(template.buttons) > 3:
            return None
            
        buttons = []
        for button in template.buttons:
            button_data = {
                "type": button.button_type,
                "text": button.button_text
            }
            
            # According to WhatsApp API docs, when sending template messages:
            # - QUICK_REPLY buttons should include the payload
            # - URL buttons should include the URL
            # - PHONE_NUMBER buttons should include the phone_number
            # - COPY_CODE buttons should include the example
            
            if button.button_type == "QUICK_REPLY" and button.payload:
                button_data["payload"] = button.payload
            elif button.button_type == "URL" and button.url:
                button_data["url"] = button.url
            elif button.button_type == "PHONE_NUMBER" and button.phone_number:
                button_data["phone_number"] = button.phone_number
            elif button.button_type == "COPY_CODE" and button.copy_code_example:
                button_data["example"] = [button.copy_code_example]
            elif button.button_type == "FLOW" and button.flow_id:
                # For FLOW buttons, we need flow_token from notification parameters
                # The flow_id is already configured in the template
                pass
                
            buttons.append(button_data)
            
        return {
            "type": "BUTTONS",
            "buttons": buttons
        }


def on_doctype_update():
    frappe.db.add_index("WhatsApp Message", ["reference_doctype", "reference_name"])


@frappe.whitelist()
def send_template(to, reference_doctype, reference_name, template):
    try:
        doc = frappe.get_doc({
            "doctype": "WhatsApp Message",
            "to": to,
            "type": "Outgoing",
            "message_type": "Template",
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
            "content_type": "text",
            "template": template
        })

        doc.save()
    except Exception as e:
        raise e
