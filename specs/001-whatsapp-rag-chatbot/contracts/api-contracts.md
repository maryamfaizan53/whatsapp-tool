# API Contracts: WhatsApp RAG Chatbot SaaS Platform

## Authentication API

### POST /api/auth/login
Authenticate business user
- Request: `{ email: string, password: string }`
- Response: `{ access_token: string, user: User }`

### POST /api/auth/register
Register new business
- Request: `{ email: string, password: string, business_name: string }`
- Response: `{ access_token: string, user: User }`

## WhatsApp Integration API

### POST /api/webhook/whatsapp
Webhook endpoint for receiving WhatsApp messages
- Headers: `X-Hub-Signature-256: string` (for verification)
- Request: `{ object: string, entry: Array<Entry> }`
- Response: `{ success: boolean }`

### GET /api/webhook/whatsapp
Verify webhook endpoint (challenge-response)
- Query: `hub.challenge: string`
- Response: `challenge: string`

## Knowledge Base API

### GET /api/knowledge-base
Get business knowledge bases
- Response: `{ knowledge_bases: KnowledgeBase[] }`

### POST /api/knowledge-base
Create new knowledge base
- Request: `{ name: string, description: string, source_type: string, source_url?: string }`
- Response: `{ knowledge_base: KnowledgeBase }`

### POST /api/knowledge-base/{kb_id}/crawl
Crawl website for knowledge base
- Request: `{ url: string }`
- Response: `{ status: string, message: string }`

### POST /api/knowledge-base/{kb_id}/upload
Upload documents to knowledge base
- Request: FormData with files
- Response: `{ uploaded_files: string[] }`

### POST /api/knowledge-base/{kb_id}/index
Trigger re-indexing of knowledge base
- Response: `{ status: string, message: string }`

## Widget Configuration API

### GET /api/widget-config
Get business widget configuration
- Response: `{ widget_config: WidgetConfiguration }`

### PUT /api/widget-config
Update widget configuration
- Request: `{ position: string, color_scheme: string, icon_type: string, pre_filled_message: string, is_enabled: boolean }`
- Response: `{ widget_config: WidgetConfiguration }`

### GET /api/widget-config/generate
Generate embeddable widget code
- Response: `{ html_code: string, js_code: string }`

## Dashboard Analytics API

### GET /api/analytics/conversations
Get conversation statistics
- Response: `{ total_conversations: number, avg_response_time: number, languages_used: Object, resolution_rate: number }`

### GET /api/conversations
Get conversation history
- Response: `{ conversations: Conversation[] }`

### GET /api/conversations/{conv_id}/messages
Get messages for specific conversation
- Response: `{ messages: Message[] }`