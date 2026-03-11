# Quickstart Guide: WhatsApp RAG Chatbot SaaS Platform

## Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 13+
- Pinecone or Qdrant account
- Meta Developer Account with WhatsApp Business Cloud API access

## Setup Instructions

### 1. Environment Setup
```bash
# Clone the repository
git clone <repo-url>
cd whatsapp-rag-platform

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install
```

### 2. Environment Variables
Create `.env` files in both backend and frontend:

**Backend (.env):**
```env
DATABASE_URL=postgresql://user:password@localhost/whatsrag
PINECONE_API_KEY=your_pinecone_key
OPENAI_API_KEY=your_openai_key
WHATSAPP_ACCESS_TOKEN=your_meta_app_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
JWT_SECRET=your_jwt_secret
ENCRYPTION_KEY=your_encryption_key
```

**Frontend (.env.local):**
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3000
```

### 3. Database Setup
```bash
# Run database migrations
cd backend
python -m alembic upgrade head
```

### 4. Running the Application
```bash
# Terminal 1: Start backend
cd backend
uvicorn src.main:app --reload --port 8000

# Terminal 2: Start frontend
cd frontend
npm run dev
```

### 5. Initial Setup
1. Navigate to http://localhost:3000
2. Sign up as a new business user
3. Connect your WhatsApp Business Cloud API credentials
4. Configure your knowledge base (upload documents or provide website URL)
5. Generate and embed your WhatsApp widget on your website

### 6. Testing the Flow
1. Send a message to your WhatsApp number
2. Verify the webhook receives the message
3. Check that the RAG system processes and responds appropriately
4. Verify the conversation appears in the dashboard

## Common Issues
- **Webhook not receiving messages**: Ensure your server is accessible from the internet (use ngrok for local testing)
- **API authentication errors**: Verify your WhatsApp access token and phone number ID
- **RAG responses inaccurate**: Check that your knowledge base is properly indexed