# Carousel Template Implementation Plan

## Overview
Implement WhatsApp Carousel templates support in the frappe_whatsapp app, allowing users to create and send interactive carousel messages with multiple cards.

## 1. Database Schema Changes

### A. WhatsApp Templates Doctype
```json
{
  "fieldname": "template_type",
  "fieldtype": "Select",
  "label": "Template Type",
  "options": "Template\nCarousel",
  "default": "Template"
}
```

### B. New Carousel Cards Doctype
```json
{
  "doctype": "WhatsApp Carousel Cards",
  "istable": 1,
  "fields": [
    {
      "fieldname": "card_index",
      "fieldtype": "Int",
      "label": "Card Index",
      "reqd": 1
    },
    {
      "fieldname": "header_type",
      "fieldtype": "Select",
      "label": "Header Type",
      "options": "IMAGE\nVIDEO\nTEXT",
      "reqd": 1
    },
    {
      "fieldname": "header_content",
      "fieldtype": "Data",
      "label": "Header Content",
      "description": "URL for media or text content"
    },
    {
      "fieldname": "body_text",
      "fieldtype": "Text",
      "label": "Body Text",
      "description": "Card body text with variables like {{1}}, {{2}}"
    }
  ]
}
```

### C. Carousel Parameters Doctype
```json
{
  "doctype": "WhatsApp Carousel Parameters",
  "istable": 1,
  "fields": [
    {
      "fieldname": "parameter_type",
      "fieldtype": "Select",
      "label": "Parameter Type",
      "options": "body_variable\ncard_header\ncard_body",
      "reqd": 1
    },
    {
      "fieldname": "variable_name",
      "fieldtype": "Data",
      "label": "Variable Name",
      "description": "e.g., {{1}}, {{2}} for body or card-specific variables"
    },
    {
      "fieldname": "field_name",
      "fieldtype": "Data",
      "label": "Field Name",
      "description": "Document field to use for replacement"
    },
    {
      "fieldname": "card_index",
      "fieldtype": "Int",
      "label": "Card Index",
      "description": "For card-specific parameters (optional)"
    }
  ]
}
```

## 2. Template Creation Flow

### A. Template Type Selection
- User selects "Carousel" as template type
- UI shows carousel-specific fields
- Card builder interface appears

### B. Carousel Configuration
- Main body text (appears above carousel)
- Number of cards (1-10, WhatsApp limit)
- Card configuration for each card

### C. Card Builder
- Header type selection (Image/Video/Text)
- Media upload for headers
- Body text with variable support
- Button configuration per card

## 3. Message Sending Implementation

### A. Carousel Payload Structure
```json
{
  "messaging_product": "whatsapp",
  "to": "phone_number",
  "type": "template",
  "template": {
    "name": "template_name",
    "language": {"code": "en"},
    "components": [
      {
        "type": "carousel",
        "cards": [
          {
            "card_index": 0,
            "components": [
              {
                "type": "header",
                "parameters": [
                  {
                    "type": "image",
                    "image": {"link": "url"}
                  }
                ]
              },
              {
                "type": "body",
                "parameters": [
                  {"type": "text", "text": "replaced_value"}
                ]
              }
            ]
          }
        ]
      }
    ]
  }
}
```

### B. Dynamic Parameter Replacement
- Body text variables ({{1}}, {{2}}, etc.)
- Card-specific header content
- Card-specific body text
- Button parameters per card

## 4. Implementation Steps

### Phase 1: Database Schema ✅ COMPLETED
1. ✅ Update WhatsApp Templates doctype
2. ✅ Create WhatsApp Carousel Cards doctype
3. ✅ Create WhatsApp Carousel Parameters doctype
4. ✅ Update WhatsApp Notification doctype

### Phase 2: Template Creation
1. Update template creation UI
2. Implement carousel template builder
3. Add media upload functionality
4. Implement template validation

### Phase 3: Template Fetching
1. Update fetch() function for carousels
2. Parse carousel components from Meta
3. Store carousel data in local database

### Phase 4: Message Sending ✅ COMPLETED
1. ✅ Implement carousel payload generation
2. ✅ Add dynamic parameter replacement
3. ✅ Handle carousel-specific buttons
4. ✅ Test with Meta API

### Phase 5: UI/UX
1. Create carousel template form
2. Add card builder interface
3. Implement drag-and-drop functionality
4. Add preview functionality

## 5. Technical Considerations

### A. API Limitations
- Maximum 10 cards per carousel
- Media size limits (5MB images, 16MB videos)
- Supported media formats
- Variable limits per template

### B. Performance
- Efficient carousel data storage
- Optimized parameter replacement
- Caching for frequently used templates

### C. Error Handling
- Template validation
- Media upload error handling
- API error responses
- Fallback mechanisms

## 6. Testing Strategy

### A. Unit Tests
- Template creation validation
- Parameter replacement logic
- Payload generation
- Error handling

### B. Integration Tests
- Meta API integration
- Template fetching
- Message sending
- Media upload

### C. User Acceptance Tests
- Template creation workflow
- Message sending workflow
- Error scenarios
- Performance testing 