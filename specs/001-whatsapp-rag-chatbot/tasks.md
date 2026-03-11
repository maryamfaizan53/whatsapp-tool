---
description: "Task list template for feature implementation"
---

# Tasks: WhatsApp RAG Chatbot SaaS Platform

**Input**: Design documents from `/specs/001-whatsapp-rag-chatbot/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
  ============================================================================
  IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

  The /sp.tasks command MUST replace these with actual tasks based on:
  - User stories from spec.md (with their priorities P1, P2, P3...)
  - Feature requirements from plan.md
  - Entities from data-model.md
  - Endpoints from contracts/

  Tasks MUST be organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment

  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan
- [X] T002 Initialize Python project with FastAPI dependencies in backend/
- [ ] T003 [P] Configure linting and formatting tools in backend/
- [X] T004 Initialize Next.js project with dependencies in frontend/
- [ ] T005 [P] Configure ESLint and Prettier in frontend/

---

## Phase 2: Foundational (Blocking Primitives)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T006 Setup database schema and migrations framework in backend/src/db/
- [ ] T007 [P] Implement JWT authentication framework in backend/src/auth/
- [ ] T008 [P] Setup API routing and middleware structure in backend/src/api/
- [ ] T009 Create base models/entities that all stories depend on in backend/src/models/
- [ ] T010 Configure error handling and logging infrastructure in backend/src/utils/
- [ ] T011 Setup environment configuration management in backend/src/config/
- [ ] T012 [P] Setup multitenancy isolation framework in backend/src/utils/multitenancy.py
- [ ] T013 Initialize frontend authentication and state management in frontend/src/lib/

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Business Onboarding and WhatsApp Connection (Priority: P1) 🎯 MVP

**Goal**: Enable business owner to sign up for the platform, connect their WhatsApp Business Cloud API credentials, and establish webhook connection.

**Independent Test**: Can be fully tested by completing the onboarding flow with valid WhatsApp credentials and verifying webhook connectivity. Delivers the core value of connecting business WhatsApp to the RAG system.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T014 [P] [US1] Contract test for authentication endpoints in backend/tests/contract/test_auth.py
- [ ] T015 [P] [US1] Integration test for business registration flow in backend/tests/integration/test_onboarding.py

### Implementation for User Story 1

- [ ] T016 [P] [US1] Create Business model in backend/src/models/business.py
- [ ] T017 [P] [US1] Create WidgetConfiguration model in backend/src/models/widget_config.py
- [ ] T018 [US1] Implement authentication service in backend/src/services/auth_service.py
- [ ] T019 [US1] Implement business registration endpoint in backend/src/api/auth.py
- [ ] T020 [US1] Implement WhatsApp credentials validation in backend/src/services/whatsapp_service.py
- [ ] T021 [US1] Implement webhook configuration endpoint in backend/src/api/webhook.py
- [ ] T022 [US1] Add webhook verification logic in backend/src/api/webhook.py
- [ ] T023 [US1] Create onboarding UI components in frontend/src/components/onboarding/
- [ ] T024 [US1] Implement onboarding wizard in frontend/src/pages/onboarding/
- [ ] T025 [US1] Add WhatsApp connection form in frontend/src/pages/dashboard/settings/
- [ ] T026 [US1] Add validation and error handling for onboarding
- [ ] T027 [US1] Add logging for onboarding operations

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Knowledge Base Creation and Management (Priority: P1)

**Goal**: Allow business to provide website URL for automatic crawling OR upload documents to create a knowledge base that gets processed and indexed for RAG retrieval.

**Independent Test**: Can be fully tested by uploading documents or providing a website URL and verifying that content is properly indexed and retrievable. Delivers the core value of having accurate, website-specific knowledge for responses.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US2] Contract test for knowledge base endpoints in backend/tests/contract/test_kb.py
- [ ] T029 [P] [US2] Integration test for document upload and indexing in backend/tests/integration/test_knowledge_base.py

### Implementation for User Story 2

- [ ] T030 [P] [US2] Create KnowledgeBase model in backend/src/models/knowledge_base.py
- [ ] T031 [P] [US2] Create Document model in backend/src/models/document.py
- [ ] T032 [US2] Implement knowledge base service in backend/src/services/knowledge_base_service.py
- [ ] T033 [US2] Implement website crawler using LlamaIndex in backend/src/services/crawler_service.py
- [ ] T034 [US2] Implement document upload handler in backend/src/api/knowledge_base.py
- [ ] T035 [US2] Implement indexing pipeline using LlamaIndex in backend/src/services/indexing_service.py
- [ ] T036 [US2] Implement vector database integration (Pinecone/Qdrant) in backend/src/db/vector_store.py
- [ ] T037 [US2] Create knowledge base UI in frontend/src/pages/knowledge-base/
- [ ] T038 [US2] Implement document upload component in frontend/src/components/knowledge-base/
- [ ] T039 [US2] Add URL crawling form in frontend/src/components/knowledge-base/
- [ ] T040 [US2] Integrate with User Story 1 components for business association

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - WhatsApp Message Processing and Response (Priority: P1)

**Goal**: Process incoming WhatsApp messages (text or voice) through the RAG pipeline and send accurate responses back to customers.

**Independent Test**: Can be fully tested by sending various messages to the WhatsApp number and verifying accurate, contextually appropriate responses are generated. Delivers the core value of automated customer support.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T041 [P] [US3] Contract test for webhook endpoint in backend/tests/contract/test_webhook.py
- [ ] T042 [P] [US3] Integration test for RAG pipeline in backend/tests/integration/test_rag.py

### Implementation for User Story 3

- [ ] T043 [P] [US3] Create Conversation model in backend/src/models/conversation.py
- [ ] T044 [P] [US3] Create Message model in backend/src/models/message.py
- [ ] T045 [US3] Implement webhook message parsing in backend/src/api/webhook.py
- [ ] T046 [US3] Implement RAG service using LlamaIndex in backend/src/services/rag_service.py
- [ ] T047 [US3] Implement voice processing service with OpenAI Whisper in backend/src/services/voice_service.py
- [ ] T048 [US3] Implement language detection service in backend/src/services/language_service.py
- [ ] T049 [US3] Implement response generation with LLM in backend/src/services/llm_service.py
- [ ] T050 [US3] Implement WhatsApp message sending in backend/src/services/whatsapp_service.py
- [ ] T051 [US3] Add conversation history tracking in backend/src/services/conversation_service.py
- [ ] T052 [US3] Create conversation UI in frontend/src/pages/conversations/
- [ ] T053 [US3] Add real-time message display in frontend/src/components/conversations/

**Checkpoint**: At this point, User Stories 1, 2 AND 3 should all work independently

---

## Phase 6: User Story 4 - Website Widget Generation (Priority: P2)

**Goal**: Allow business to customize and generate an embeddable WhatsApp chat widget for their website.

**Independent Test**: Can be fully tested by generating the widget code and embedding it on a test site to verify it properly links to the business WhatsApp number.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T054 [P] [US4] Contract test for widget configuration endpoints in backend/tests/contract/test_widget.py
- [ ] T055 [P] [US4] Integration test for widget code generation in backend/tests/integration/test_widget.py

### Implementation for User Story 4

- [ ] T056 [P] [US4] Update WidgetConfiguration model with additional fields in backend/src/models/widget_config.py
- [ ] T057 [US4] Implement widget configuration service in backend/src/services/widget_service.py
- [ ] T058 [US4] Implement widget code generation in backend/src/api/widget.py
- [ ] T059 [US4] Create widget builder UI in frontend/src/pages/widget-builder/
- [ ] T060 [US4] Implement widget preview component in frontend/src/components/widget/
- [ ] T061 [US4] Add embed code generator in frontend/src/components/widget/
- [ ] T062 [US4] Integrate with User Story 1 components for dashboard access

**Checkpoint**: All user stories should now be independently functional

---

[Add more user story phases as needed, following the same pattern]

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T063 [P] Documentation updates in docs/
- [ ] T064 Code cleanup and refactoring
- [ ] T065 Performance optimization across all stories
- [ ] T066 [P] Additional unit tests (if requested) in backend/tests/unit/
- [ ] T067 Security hardening
- [ ] T068 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for authentication endpoints in backend/tests/contract/test_auth.py"
Task: "Integration test for business registration flow in backend/tests/integration/test_onboarding.py"

# Launch all models for User Story 1 together:
Task: "Create Business model in backend/src/models/business.py"
Task: "Create WidgetConfiguration model in backend/src/models/widget_config.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence