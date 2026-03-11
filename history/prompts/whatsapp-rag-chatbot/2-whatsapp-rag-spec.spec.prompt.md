---
id: 2
title: whatsapp-rag-spec
stage: spec
date: 2026-01-31
surface: agent
model: Claude Sonnet 4.5
feature: whatsapp-rag-chatbot
branch: 001-whatsapp-rag-chatbot
user: 840 G7
command: sp.specify
labels: [specification, whatsapp, rag, saas, chatbot]
links:
  spec: specs/001-whatsapp-rag-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/001-whatsapp-rag-chatbot/spec.md
 - specs/001-whatsapp-rag-chatbot/checklists/requirements.md
tests:
 - none
---

## Prompt

```text
Software Requirements Specification (SRS) for WhatsApp RAG Chatbot SaaS Platform
Project Name: WhatsRAG (WhatsApp Retrieval-Augmented Generation Assistant)
Version: 1.0
Date: January 31, 2026
Author: Grok AI (assisted specification)
Client/Stakeholder: Maryam (Project Initiator)
Status: Draft for Review
1. Introduction
1.1 Purpose
This document defines the complete software requirements for WhatsRAG, a SaaS platform that enables website owners to deploy an AI-powered WhatsApp chatbot. The chatbot uses Retrieval-Augmented Generation (RAG) to provide accurate, website-specific answers to customer queries (e.g., orders, refunds, account creation) via WhatsApp. It supports multilingual conversations and voice input, with seamless integration into any website via an embeddable widget.
The system aims to reduce support workload, improve response time, and provide 24/7 automated assistance while maintaining high accuracy through grounded RAG responses.
1.2 Scope
In Scope:

Onboarding of businesses with their WhatsApp Business Cloud API credentials.
Automatic ingestion and indexing of website content/documents into a per-business knowledge base.
Real-time processing of incoming WhatsApp messages (text and voice).
Multilingual detection and response generation using RAG.
Generation of customizable website chat widgets.
Basic analytics and conversation history.

Out of Scope (for MVP)**:

Live agent handover integration with external CRMs (e.g., Zendesk).
Advanced analytics (sentiment analysis, custom dashboards).
Payment processing for SaaS billing.
Mobile app for business management.

1.3 Definitions and Acronyms

RAG: Retrieval-Augmented Generation
WhatsApp Business Cloud API: Meta's hosted API for WhatsApp Business messaging
STT: Speech-to-Text
TTS: Text-to-Speech
KB: Knowledge Base
LLM: Large Language Model
Webhook: Server endpoint that receives real-time messages from Meta

1.4 References

Meta WhatsApp Business Cloud API Documentation (2026 version)
LlamaIndex Documentation
OpenAI/Grok API Guidelines
GDPR/CCPA Compliance Guidelines

1.5 Overview
The rest of this document describes system overview, functional and non-functional requirements, architecture constraints, and supporting information.
2. Overall Description
2.1 Product Perspective
WhatsRAG is a new SaaS product addressing the gap between generic chatbots and website-specific support on WhatsApp, the dominant messaging platform in markets like Pakistan, India, and Latin America. It combines official WhatsApp integration with advanced RAG to ensure responses are accurate and grounded in the business's own content.
2.2 Product Functions

Business onboarding and WhatsApp connection
Knowledge base creation (crawling + uploads)
Message processing pipeline (receive → transcribe if voice → detect language → retrieve → generate → send)
Website widget generation
Conversation management and analytics

2.3 User Classes and Characteristics

























User ClassDescriptionCharacteristicsBusiness Owner/AdminWebsite owners who configure the botTechnical to non-technical; need easy dashboardEnd CustomerWebsite visitors using WhatsApp chatMultilingual; may use voice; mobile-firstSystem AdministratorPlatform maintainerHandles scaling, monitoring
2.4 Operating Environment

Server: Cloud-hosted (AWS/Vercel/DigitalOcean)
Client: Modern web browsers (Chrome, Safari, Firefox) for dashboard; WhatsApp mobile/web apps for end users
WhatsApp: Official apps supporting voice messages

2.5 Design and Implementation Constraints

Must use WhatsApp Business Cloud API (no unofficial libraries)
Python-based backend (FastAPI)
RAG framework: LlamaIndex
Vector database: Pinecone or Qdrant
Multilingual embeddings/LLM required

2.6 Assumptions and Dependencies

Businesses have approved WhatsApp Business accounts
Meta API remains free for conversational messages
Third-party APIs (LLM, STT/TTS) are available and billed separately

3. Specific Requirements
3.1 External Interface Requirements
3.1.1 User Interfaces

Responsive web dashboard (Next.js/React) for business onboarding, KB management, analytics
Customizable floating WhatsApp widget (HTML/JS) for websites

3.1.2 Hardware Interfaces
None
3.1.3 Software Interfaces

Meta WhatsApp Cloud API (REST webhooks)
LLM provider API (e.g., Grok/OpenAI)
Vector DB API
STT/TTS APIs

3.1.4 Communication Interfaces

HTTPS webhooks
Secure WebSocket optional for real-time dashboard updates

3.2 Functional Requirements













































































IDCategoryRequirement DescriptionPriorityFR01OnboardingSystem shall allow business signup and secure storage of WhatsApp credentials (Phone ID, Token)HighFR02Knowledge Base IngestionSystem shall crawl provided website URL and/or accept document uploads to build indexed KBHighFR03Webhook HandlingSystem shall receive and acknowledge WhatsApp messages within 20 secondsHighFR04Voice ProcessingSystem shall detect voice messages, download audio, and transcribe using STT (>95% target accuracy)HighFR05Language DetectionSystem shall detect incoming message language and respond in the same languageHighFR06RAG PipelineSystem shall retrieve relevant chunks, re-rank, and generate grounded response using LLMHighFR07Response DeliverySystem shall send text responses; optional voice responses via TTSMediumFR08Widget GenerationSystem shall generate embeddable HTML/JS code for website chat buttonHighFR09Conversation HistorySystem shall store and display conversation logs per businessMediumFR10AnalyticsSystem shall provide basic metrics (conversations, languages, resolution rate)MediumFR11SecuritySystem shall isolate data per business; encrypt sensitive dataHigh
3.3 Non-Functional Requirements



























































IDCategoryRequirementMetric/TargetNFR01PerformanceEnd-to-end response time<3s text, <8s voiceNFR02ScalabilitySupport concurrent conversations10,000+NFR03AvailabilitySystem uptime99.9%NFR04SecurityCompliance with GDPR/CCPA; secure credential handlingFull complianceNFR05ReliabilityMessage delivery with retry logic99% success rateNFR06UsabilityDashboard intuitive for non-technical usersCompletion of tasks in <5 minNFR07MaintainabilityCode modular; logging and monitoringEasy deployment/updatesNFR08Cost EfficiencyOptimize token usage; pass-through conversation costsMinimize overhead
4. Supporting Information
4.1 Architecture Overview
Multi-tenant SaaS with:

Frontend: Next.js dashboard
Backend: FastAPI + Celery workers
Databases: PostgreSQL (metadata) + Vector DB (per-business indexes)
External: Meta API, LLM, STT/TTS

4.2 Data Flow

Customer → WhatsApp → Meta → Webhook → Backend
Backend → (Transcribe if voice) → Language Detect → Retrieve → LLM Generate → Send via Meta API

4.3 Risks

Meta policy changes: Mitigate by monitoring and template compliance
Transcription accuracy: Use best STT model + text fallback
Hallucinations: Strict prompting + confidence-based handover

This SRS serves as the complete requirements baseline. Next steps: Review and approve, then proceed to detailed design and prototyping.
```

## Response snapshot

Created a comprehensive feature specification for the WhatsApp RAG Chatbot SaaS Platform (WhatsRAG). The specification includes:

- Four prioritized user stories covering onboarding, knowledge base management, message processing, and widget generation
- Twelve functional requirements defining core system capabilities
- Four key entities representing the main data structures
- Six measurable success criteria with specific metrics
- Identified edge cases for system resilience

The specification follows the template structure and focuses on user value without implementation details, making it suitable for stakeholder review and subsequent planning.

## Outcome

- ✅ Impact: Created complete feature specification aligned with user requirements
- 🧪 Tests: none
- 📁 Files: Created spec.md and requirements checklist
- 🔁 Next prompts: Ready for planning phase with /sp.plan
- 🧠 Reflection: Specification captures all key aspects of the WhatsApp RAG platform

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Proceed to planning phase