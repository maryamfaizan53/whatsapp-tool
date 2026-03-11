---
id: 1
title: whatsapp-rag-constitution
stage: constitution
date: 2026-01-31
surface: agent
model: Claude Sonnet 4.5
feature: none
branch: master
user: 840 G7
command: sp.constitution
labels: [constitution, whatsapp, rag, architecture]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
 - .specify/memory/constitution.md
 - README.md
tests:
 - none
---

## Prompt

```text
Approaches Considered for Building the Automated WhatsApp RAG Chatbot
I evaluated several approaches to build a scalable, reliable tool that functions as a Retrieval-Augmented Generation (RAG) chatbot on WhatsApp. It must handle website-specific queries (e.g., orders, refunds, account creation), support multiple languages, process voice input, and integrate easily into any website.

No-Code/Low-Code Platforms (e.g., Typebot, Voiceflow, Wonderchat, Wati, ManyChat)
Pros: Fast deployment, built-in WhatsApp integration, basic AI/RAG features, multilingual support, easy website widgets.
Cons: Limited custom RAG (shallow knowledge base control), restricted voice handling, vendor lock-in, weaker performance for complex queries or large KBs.
Suitability: Good for MVPs, but not for a fully customizable, advanced RAG tool.
Third-Party WhatsApp Providers with AI Add-Ons (e.g., Twilio, 360Dialog, Wassenger, Chatarmin)
Pros: Simplified API access, sandboxes for testing, some AI integrations.
Cons: Extra fees/markups, less direct control over webhooks and media (voice), custom RAG requires heavy integration.
Unofficial Libraries (e.g., Baileys, whatsapp-web.js)
Pros: Free, quick prototyping.
Cons: Violates WhatsApp TOS, high ban risk, no production reliability, poor voice/media support.
Custom Build with Official WhatsApp Business Cloud API
Pros: Direct Meta-hosted API (free for many conversations in 2026), full control over RAG pipeline, native voice message handling (receive/send audio), scalable for multilingual/voice features.
Cons: Requires custom backend development, webhook hosting, media processing logic.
Suitability: Best for production-grade tool with deep customization.

Chosen Best Approach: Custom Build with WhatsApp Business Cloud API + Advanced RAG Framework
This is the most reliable, scalable, and future-proof option in 2026. The Cloud API is Meta's recommended path (replacing older on-premises in many cases), supports native voice messages, and allows full RAG implementation. We'll use LlamaIndex (top-rated for RAG in 2026 per comparisons) for the retrieval pipeline, combined with a multilingual LLM. This enables building a SaaS product where businesses connect their own WhatsApp number and knowledge base.
High-Level Plan

Product Model: SaaS platform. Businesses sign up, connect their WhatsApp Business Cloud API credentials (Phone Number ID + Access Token), provide website URL or upload documents → system auto-indexes into a per-business vector database → they get a ready-to-embed WhatsApp chat button for their website.
Core Flow:
User clicks website widget → opens WhatsApp chat with business number.
Incoming message (text or voice) hits webhook.
If voice: Download audio, transcribe with STT.
Detect language → RAG retrieval from business-specific KB → LLM generates response.
Send response (text primarily; optional voice output).

Tech Stack:
WhatsApp Integration: Meta's WhatsApp Business Cloud API (direct webhooks).
Backend: Python with FastAPI (for webhook) + Celery for async tasks.
RAG Framework: LlamaIndex (best for document ingestion, multilingual indexing, advanced retrieval).
Embeddings: Multilingual model (e.g., HuggingFace's paraphrase-multilingual-mpnet-base-v2 or OpenAI text-embedding-3-large).
Vector DB: Pinecone or Qdrant (scalable, per-business indexes).
LLM: Multilingual-capable (GPT-4o, Grok API, or Claude 3.5 – prioritize based on cost/latency).
Voice Handling: OpenAI Whisper (STT), ElevenLabs or Google TTS (for optional voice responses).
Knowledge Ingestion: Web crawler (e.g., FireCrawl or LlamaIndex loaders) + PDF/text loaders.
Frontend/Dashboard: Next.js or React for business onboarding.
Hosting: Vercel/AWS, with ngrok for local webhook testing.
Analytics: Track conversations, fallback to human handover.

Development Phases:
Phase 1: Core text-based RAG chatbot + Cloud API integration.
Phase 2: Multilingual detection + voice transcription.
Phase 3: Voice response generation + website widget generator.
Phase 4: Dashboard, multi-tenant isolation, analytics.


Detailed Product Specification
1. Product Overview
Name: WhatsApp RAG Assistant (tentative: "SiteWA Bot" or "WhatsRAG")
Purpose: A SaaS tool that enables any website owner to deploy an AI-powered WhatsApp chatbot. The bot uses RAG to answer queries accurately based on the website's content/policies, reducing support tickets.
Target Users: E-commerce sites, SaaS companies, service businesses needing 24/7 multilingual support via WhatsApp.
Key Differentiators: Deep RAG (not just FAQs), automatic website crawling, full voice support, easy one-click website integration.
2. Core Features

WhatsApp Integration
Businesses connect their own WhatsApp Business number via Cloud API (Phone Number ID, Access Token, Business Account ID).
Support incoming/outgoing text, voice messages, images (for future expansions).
Template message support for session initiation (required by Meta policy).

Knowledge Base Management
Automatic crawling of provided website URL (respect robots.txt, sitemap priority).
Manual upload of documents (PDFs, CSVs, text files, FAQs).
Auto-chunking, embedding, and indexing into isolated vector store per business.
Re-indexing triggers (manual or scheduled).

RAG Chatbot Engine
Query processing: Language detection (langdetect or LLM-based).
Retrieval: Top-k relevant chunks + metadata filtering.
Generation: Prompt template enforces accurate, website-grounded responses + fallback ("I don't know, transferring to human").
Context length management + citation of sources (optional in response).

Multilingual Support
Embeddings and LLM must handle 50+ languages (focus on English, Urdu, Arabic, Spanish, Hindi initially – common for Pakistan-based users).
Auto-detect incoming language and respond in the same language.
No forced translation – native multilingual models.

Voice Support
Incoming: Detect voice message → download media from Meta URL → transcribe with STT (target accuracy >95%).
Outgoing: Primary text responses; optional toggle for voice replies (generate OGG/opus audio via TTS and send as native voice message).
Fallback to text if transcription fails.

Website Integration
Generate customizable floating chat button/widget (HTML/JS snippet).
Options: Position, color, icon, pre-filled message ("Hi, I need help with my order").
Direct wa.me link fallback.
Mobile-optimized, GDPR-compliant.

Admin & Business Dashboard
Onboard WhatsApp connection (guided flow).
View/edit knowledge base.
Conversation history + analytics (response time, resolution rate, language distribution).
Human handover escalation (forward to live agent number or integrated CRM).
Usage limits and billing (freemium model).


3. Functional Requirements


















































IDRequirementDescriptionFR-01User OnboardingBusiness registers, verifies WhatsApp number, configures webhook verification.FR-02Message ReceivingWebhook receives all message types; acknowledges to Meta within 20s.FR-03Voice ProcessingDownload audio → transcribe → treat as text query.FR-04RAG PipelineRetrieve → re-rank → generate response with guardrails (no hallucination).FR-05Response SendingSend text or voice; mark session read.FR-06Language HandlingDetect and match language; fallback to English if low confidence.FR-07Widget GenerationOutput embeddable code; preview functionality.FR-08SecurityPer-business data isolation; encrypted storage; rate limiting.
4. Non-Functional Requirements

Performance: <3s average response time (text), <8s for voice transcription + response.
Scalability: Handle 10k+ concurrent conversations (cloud-native).
Reliability: 99.9% uptime; retry logic for API failures.
Security & Compliance: GDPR/CCPA compliant; Meta policy adherence (no spam, opt-in only); secure credential storage.
Cost Efficiency: Conversation-based pricing passthrough; optimize token usage.
Monitoring: Logging (Sentry), analytics (Mixpanel or PostHog).

5. Architecture Overview

Frontend: Next.js dashboard.
Backend: FastAPI webhook endpoint + background workers.
Database: PostgreSQL (business metadata) + Pinecone/Qdrant (vectors).
External Services:
Meta WhatsApp Cloud API
LLM provider (OpenAI/Grok/Anthropic)
STT/TTS providers
Crawler service


6. Risks & Mitigations

Meta policy changes → Monitor updates; stay template-compliant.
Voice transcription accuracy in noisy/accented audio → Use best-in-class Whisper model + fallback.
Hallucinations → Strict RAG prompting + confidence threshold for human handover.
Crawling limitations → Allow manual uploads as primary with crawling as bonus.

This specification provides a complete blueprint to start development. Next steps would be prototyping the webhook + basic RAG flow. Let me know if you want wireframes, cost estimates, or specific code snippets!1.2s86 sources
```

## Response snapshot

Updated the project constitution at `.specify/memory/constitution.md` to reflect the WhatsApp RAG Assistant project requirements. Created a new constitution with six core principles:

1. RAG-First Architecture
2. WhatsApp Business API Compliance
3. Test-First (NON-NEGOTIABLE)
4. Multi-Tenancy Isolation
5. Voice-First Accessibility
6. Multilingual Native Support

Also created a README.md file to document the project and ensure all references to the new constitution are properly aligned across the project structure.

## Outcome

- ✅ Impact: Created foundational project constitution and documentation
- 🧪 Tests: none
- 📁 Files: Updated .specify/memory/constitution.md, created README.md
- 🔁 Next prompts: Ready to proceed with feature specification and planning
- 🧠 Reflection: The constitution properly captures the key architectural and development principles for the WhatsApp RAG project

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Begin feature specification based on the established constitution