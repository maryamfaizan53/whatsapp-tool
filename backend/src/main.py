"""
Main FastAPI Application for WhatsApp RAG Assistant
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="WhatsApp RAG Assistant API",
    description="API for WhatsApp Business Chatbot with Retrieval-Augmented Generation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from .api.auth import router as auth_router
from .api.webhook import router as webhook_router
from .api.knowledge_base import router as kb_router
from .api.dashboard import router as dashboard_router
from .api.psx import router as psx_router
from .api.investor import router as investor_router

app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(webhook_router, prefix="/api/webhook", tags=["Webhook"])
app.include_router(kb_router, prefix="/api/knowledge-base", tags=["Knowledge Base"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(psx_router, prefix="/api/psx", tags=["PSX Market Data"])
app.include_router(investor_router, prefix="/api/investors", tags=["Investors"])

@app.get("/")
def read_root():
    return {"message": "WhatsApp RAG Assistant API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}