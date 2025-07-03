# WhatsApp Template Buttons Feature

This feature adds support for WhatsApp template buttons with custom payloads to the frappe_whatsapp app.

## Features Added

1. **WhatsApp Template Buttons Doctype**: A new doctype to define buttons with their payloads
2. **Button Support in Templates**: WhatsApp templates can now include up to 3 buttons
3. **Button Types Supported**:
   - **QUICK_REPLY**: Buttons that send a custom payload when clicked
   - **URL**: Buttons that open a URL when clicked
   - **PHONE_NUMBER**: Buttons that initiate a phone call

## How to Use

### 1. Create Button Definitions

1. Go to **WhatsApp Template Buttons** doctype
2. Create a new button with:
   - **Button Text**: The text displayed on the button
   - **Button Type**: Choose from QUICK_REPLY, URL, or PHONE_NUMBER
   - **Payload/URL/Phone Number**: Required field based on button type

### 2. Add Buttons to Templates

1. Go to **WhatsApp Templates**
2. Create or edit a template
3. In the "Template Buttons" section, add the buttons you created
4. Save the template - it will be automatically submitted to Meta for approval

### 3. Send Messages with Buttons

When you send a WhatsApp message using a template that has buttons, the buttons will automatically be included in the message.

## Button Types and Payloads

### Quick Reply Buttons
- **Purpose**: Send a predefined payload when clicked
- **Use Case**: Customer support, order status, etc.
- **Example Payload**: `"order_status_123"`, `"support_request"`

### URL Buttons
- **Purpose**: Open a web page when clicked
- **Use Case**: Product catalogs, order tracking, etc.
- **Example URL**: `"https://yourstore.com/track-order"`

### Phone Number Buttons
- **Purpose**: Initiate a phone call when clicked
- **Use Case**: Customer support, sales inquiries
- **Example**: `"+1234567890"`

## Receiving Button Clicks

When a user clicks a button, the webhook will receive the button click as an incoming message of type "button". The webhook handler already processes these and stores them in the WhatsApp Message doctype.

## Technical Implementation

### New Doctypes
- `WhatsApp Template Buttons`: Stores button definitions
- Updated `WhatsApp Templates`: Now includes a table field for buttons

### Modified Files
- `whatsapp_templates.py`: Added button component generation
- `whatsapp_message.py`: Added button support in outgoing messages

### API Integration
The buttons are sent to Meta's WhatsApp API in the correct format:
```json
{
  "type": "button",
  "sub_type": "quick_reply",
  "index": 0,
  "parameters": [
    {
      "type": "QUICK_REPLY",
      "text": "Button Text",
      "payload": "custom_payload"
    }
  ]
}
```

## Limitations

- Maximum 3 buttons per template (WhatsApp API limitation)
- Buttons must be approved by Meta along with the template
- Only certain template categories support buttons

## Migration

To apply these changes to your existing installation:

```bash
bench migrate
```

This will automatically create the new doctype and update existing templates. 