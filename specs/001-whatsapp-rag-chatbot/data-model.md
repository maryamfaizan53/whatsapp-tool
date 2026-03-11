# Data Model: WhatsApp RAG Chatbot SaaS Platform

## Core Entities

### Business
- **business_id**: UUID (primary key)
- **name**: String (business name)
- **email**: String (admin contact)
- **whatsapp_phone_number_id**: String (Meta's phone number ID)
- **whatsapp_access_token**: EncryptedString (securely stored API token)
- **webhook_url**: String (configured webhook endpoint)
- **created_at**: DateTime
- **updated_at**: DateTime
- **is_active**: Boolean
- **subscription_tier**: String (pricing tier)

### KnowledgeBase
- **kb_id**: UUID (primary key)
- **business_id**: UUID (foreign key to Business)
- **name**: String (knowledge base name)
- **description**: Text (optional description)
- **source_type**: Enum ('website', 'documents', 'manual')
- **source_url**: String (if website crawling)
- **vector_index_name**: String (name of vector DB index)
- **last_indexed_at**: DateTime
- **document_count**: Integer
- **status**: Enum ('active', 'indexing', 'error')

### Document
- **doc_id**: UUID (primary key)
- **kb_id**: UUID (foreign key to KnowledgeBase)
- **filename**: String (original filename)
- **source_url**: String (URL if crawled from website)
- **content_hash**: String (to detect changes)
- **indexed_chunks**: Integer (number of indexed chunks)
- **upload_date**: DateTime
- **status**: Enum ('uploaded', 'processing', 'indexed', 'failed')

### Conversation
- **conv_id**: UUID (primary key)
- **business_id**: UUID (foreign key to Business)
- **customer_whatsapp_id**: String (customer's WhatsApp ID)
- **started_at**: DateTime
- **last_message_at**: DateTime
- **status**: Enum ('active', 'closed', 'transferred')
- **language_code**: String (detected language)

### Message
- **msg_id**: UUID (primary key)
- **conv_id**: UUID (foreign key to Conversation)
- **sender_type**: Enum ('customer', 'business', 'system')
- **content**: Text (message content)
- **media_url**: String (URL to voice/image media if applicable)
- **message_type**: Enum ('text', 'voice', 'image', 'template')
- **timestamp**: DateTime
- **processed_by_rag**: Boolean (whether RAG was used)
- **confidence_score**: Float (RAG response confidence)

### WidgetConfiguration
- **widget_id**: UUID (primary key)
- **business_id**: UUID (foreign key to Business)
- **position**: Enum ('bottom-right', 'bottom-left', 'top-right', 'top-left')
- **color_scheme**: String (hex color)
- **icon_type**: String (icon identifier)
- **pre_filled_message**: String (default message text)
- **is_enabled**: Boolean
- **custom_css**: Text (custom styling)
- **created_at**: DateTime
- **updated_at**: DateTime

## Relationships
- Business 1:* KnowledgeBase
- KnowledgeBase 1:* Document
- Business 1:* Conversation
- Conversation 1:* Message
- Business 1:* WidgetConfiguration