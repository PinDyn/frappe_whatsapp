# WhatsApp Carousel Integration for Frappe

This document explains how to use the integrated carousel functionality in the `frappe_whatsapp` app.

## Overview

The carousel integration provides a complete workflow for:
1. **Uploading media files** to WhatsApp using the Resumable Upload API
2. **Creating carousel templates** with multiple cards, images, and buttons
3. **Checking template status** and approval
4. **Sending carousel messages** to recipients

## Prerequisites

1. **WhatsApp Business API Setup**: Ensure you have:
   - WhatsApp Business Account
   - App ID
   - Business Account ID
   - Phone Number ID
   - Access Token

2. **Frappe WhatsApp Settings**: Configure the following fields in `WhatsApp Settings`:
   - `token`: Your WhatsApp access token
   - `app_id`: Your WhatsApp App ID
   - `business_id`: Your Business Account ID
   - `phone_id`: Your Phone Number ID

## File Structure

```
frappe_whatsapp/
├── frappe_whatsapp/
│   └── utils/
│       └── carousel_utils.py          # Core carousel functionality
├── integrated_carousel_manager.py     # Integrated workflow manager
├── example_carousel_workflow.py       # Example usage
└── carousel_data/                     # Data storage (auto-created)
    ├── uploads.json                   # Uploaded media records
    └── templates.json                 # Created templates
```

## Core Components

### 1. Carousel Utils (`carousel_utils.py`)

The core utility functions for building carousel payloads and uploading media:

#### Key Functions:

- `upload_attach_to_whatsapp()`: Uploads Frappe file attachments to WhatsApp
- `build_carousel_payload()`: Builds complete carousel template payload
- `build_card_payload()`: Builds individual card payloads
- `build_header_component()`: Builds header components with images/videos
- `build_body_component()`: Builds body text components
- `build_buttons_component()`: Builds button components

#### Usage Example:

```python
from frappe_whatsapp.frappe_whatsapp.utils.carousel_utils import upload_attach_to_whatsapp

# Upload a file from Frappe attach field
handle = upload_attach_to_whatsapp("/files/my_image.jpg")
print(f"Uploaded handle: {handle}")
```

### 2. Integrated Carousel Manager (`integrated_carousel_manager.py`)

A comprehensive manager class that handles the complete workflow:

#### Key Methods:

- `upload_media()`: Upload files to WhatsApp
- `create_carousel_template()`: Create carousel templates
- `check_template_status()`: Check template approval status
- `send_carousel_message()`: Send carousel messages
- `list_uploads()`: List all uploaded media
- `list_templates()`: List all created templates

#### Usage Example:

```python
from integrated_carousel_manager import IntegratedCarouselManager

# Initialize manager
manager = IntegratedCarouselManager()

# Upload media
result = manager.upload_media("/path/to/image.jpg")
handle = result["asset_handle"]

# Create template
cards_data = [
    {
        "image_handle": handle,
        "body_text": "Welcome to our product!",
        "buttons": [
            {"type": "quick_reply", "text": "Learn More"}
        ]
    }
]
template_result = manager.create_carousel_template("My Template", cards_data)

# Check status
status = manager.check_template_status("My Template")

# Send message (if approved)
if status["status"] == "APPROVED":
    manager.send_carousel_message("My Template", "1234567890")
```

## Command Line Usage

The integrated manager can be used from the command line:

### Upload Media
```bash
python integrated_carousel_manager.py --action upload --file /path/to/image.jpg
```

### Create Template
```bash
python integrated_carousel_manager.py --action create --template "My Template" --cards cards.json
```

### Check Status
```bash
python integrated_carousel_manager.py --action status --template "My Template"
```

### Send Message
```bash
python integrated_carousel_manager.py --action send --template "My Template" --to "1234567890"
```

### List Uploads/Templates
```bash
python integrated_carousel_manager.py --action list-uploads
python integrated_carousel_manager.py --action list-templates
```

## Template Structure

Carousel templates consist of multiple cards, each with:

### Card Components:
1. **Header** (optional): Image or video
2. **Body**: Text content (supports variables like `{{1}}`, `{{2}}`)
3. **Buttons** (required): Up to 2 buttons per card

### Button Types:
- `quick_reply`: Simple text button with payload
- `url`: Button that opens a URL
- `phone_number`: Button that calls a phone number
- `copy_code`: Button that copies text to clipboard
- `flow`: Button that triggers a flow

### Example Cards JSON:
```json
[
  {
    "image_handle": "uploaded_image_handle",
    "body_text": "Welcome {{1}}! Check out our {{2}} offer.",
    "buttons": [
      {
        "type": "quick_reply",
        "text": "Learn More",
        "payload": "learn_more"
      },
      {
        "type": "url",
        "text": "Visit Website",
        "url": "https://example.com"
      }
    ]
  }
]
```

## Integration with Frappe UI

### 1. Template Creation Form

The carousel functionality is integrated into the `WhatsApp Templates` doctype:

1. Create a new WhatsApp Template
2. Set `template_type` to "Carousel"
3. Add carousel cards with:
   - Header type (Image/Video/None)
   - Header content (attach field)
   - Body text
   - Buttons
4. Use "Create Template" button to submit to WhatsApp
5. Use "Update Template" button to modify existing templates

### 2. Message Sending

Carousel messages can be sent through:
- The WhatsApp Templates form
- Programmatic API calls
- Integration with other Frappe modules

## Error Handling

The integration includes comprehensive error handling:

1. **Upload Errors**: Network issues, invalid files, API errors
2. **Template Errors**: Invalid structure, missing required fields
3. **Status Errors**: Template not found, approval issues
4. **Send Errors**: Invalid phone numbers, template not approved

All errors are logged and provide detailed information for debugging.

## Best Practices

### 1. Media Uploads
- Use appropriate image formats (JPEG, PNG)
- Keep file sizes reasonable (< 5MB for images)
- Use descriptive file names
- Handle upload failures gracefully

### 2. Template Design
- Keep body text concise (≤ 160 characters)
- Use clear, actionable button text
- Test templates thoroughly before production
- Follow WhatsApp's content policies

### 3. Message Sending
- Always check template approval status
- Validate phone numbers before sending
- Handle delivery failures
- Monitor message delivery status

## Troubleshooting

### Common Issues:

1. **"App ID not found"**: Check WhatsApp Settings configuration
2. **"Upload failed"**: Verify file exists and is accessible
3. **"Template creation failed"**: Check template structure and required fields
4. **"Template not approved"**: Wait for Meta approval or check content
5. **"Message sending failed"**: Verify phone number format and template status

### Debug Mode:

Enable detailed logging by setting:
```python
import frappe
frappe.logger().setLevel("DEBUG")
```

## API Reference

### WhatsApp Business API Endpoints Used:

- **Media Upload**: `POST /v23.0/{app_id}/uploads`
- **Template Creation**: `POST /v23.0/{business_id}/message_templates`
- **Template Status**: `GET /v23.0/{template_id}`
- **Message Sending**: `POST /v23.0/{phone_id}/messages`

### Frappe Integration Points:

- **File Management**: Uses Frappe's File doctype for attachments
- **Settings**: Uses WhatsApp Settings for configuration
- **Templates**: Uses WhatsApp Templates doctype
- **Messages**: Uses WhatsApp Messages doctype

## Support

For issues and questions:
1. Check the error logs in Frappe
2. Verify WhatsApp API credentials
3. Test with the example workflow script
4. Review Meta's WhatsApp Business API documentation

## Changelog

- **v1.0**: Initial carousel implementation
- **v1.1**: Added integrated manager and command-line tools
- **v1.2**: Improved error handling and logging
- **v1.3**: Added UI integration and form handling 