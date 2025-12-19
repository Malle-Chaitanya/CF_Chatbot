# CloudFuze Chatbot - End-to-End Workflow

This document provides a comprehensive, detailed explanation of the entire chatbot workflow from user interaction to response delivery.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Phase 1: User Authentication](#phase-1-user-authentication)
4. [Phase 2: Frontend Request](#phase-2-frontend-request)
5. [Phase 3: Backend Processing](#phase-3-backend-processing)
6. [Phase 4: Query Classification](#phase-4-query-classification)
7. [Phase 5: Document Retrieval](#phase-5-document-retrieval)
8. [Phase 6: Context Processing](#phase-6-context-processing)
9. [Phase 7: LLM Response Generation](#phase-7-llm-response-generation)
10. [Phase 8: Response Delivery](#phase-8-response-delivery)
11. [Phase 9: Session Management](#phase-9-session-management)
12. [Phase 10: Analytics & Tracking](#phase-10-analytics--tracking)
13. [Error Handling](#error-handling)
14. [Performance Considerations](#performance-considerations)

---

## Overview

The CloudFuze Chatbot is a RAG (Retrieval-Augmented Generation) system that:

1. **Authenticates** users via Microsoft OAuth
2. **Processes** user queries through intent classification
3. **Retrieves** relevant documents from multiple sources (SharePoint, Blog, PDFs, Emails)
4. **Reranks** documents using hybrid ranking (semantic + keyword)
5. **Compresses** context when needed
6. **Generates** responses using LLM (OpenAI GPT-4o-mini or Google Gemini)
7. **Streams** responses to frontend in real-time
8. **Tracks** analytics and user feedback

---

## Architecture Diagram

```
┌─────────────┐
│   User      │
│  Browser    │
└──────┬──────┘
       │
       │ 1. Login (Microsoft OAuth)
       ▼
┌─────────────────────────────────┐
│   Frontend (Next.js)            │
│   - Login Page                  │
│   - Chat Interface              │
│   - Dashboard                   │
└──────┬──────────────────────────┘
       │
       │ 2. POST /chat/stream
       │    Authorization: Bearer <token>
       ▼
┌─────────────────────────────────┐
│   Backend (FastAPI)             │
│   ┌──────────────────────────┐ │
│   │ 1. Authentication         │ │
│   │ 2. Event Tracking         │ │
│   │ 3. Query Classification   │ │
│   │ 4. Document Retrieval     │ │
│   │ 5. Reranking              │ │
│   │ 6. Context Compression     │ │
│   │ 7. LLM Generation         │ │
│   │ 8. Session Management     │ │
│   └──────────────────────────┘ │
└──────┬──────────────────────────┘
       │
       ├──► MongoDB (Sessions, Analytics)
       ├──► ChromaDB (Vector Store)
       ├──► Langfuse (Observability)
       └──► LLM Provider (OpenAI/Gemini)
```

---

## Phase 1: User Authentication

### Step 1.1: User Initiates Login

**Location**: `frontend/src/app/login/page.tsx`

1. User clicks "Sign in with Microsoft"
2. Frontend redirects to Microsoft OAuth endpoint
3. User authenticates with Microsoft account

### Step 1.2: OAuth Callback

**Location**: `app/endpoints.py` - `/auth/microsoft/callback`

1. Microsoft redirects back with authorization code
2. Backend exchanges code for access token
3. Backend fetches user info from Microsoft Graph API
4. Validates email domain (`@cloudfuze.com`)
5. Returns access token to frontend

### Step 1.3: Token Storage

**Location**: `frontend/src/lib/session-utils.ts`

1. Frontend stores access token in `localStorage`
2. Token used for all subsequent API calls
3. Token validated on every request

### Step 1.4: Request Authentication

**Location**: `app/auth.py` - `get_current_user()`

**Process**:
```python
1. Extract Bearer token from Authorization header
2. Verify token with Microsoft Graph API
3. Validate email domain (@cloudfuze.com)
4. Return user info: {user_id, email, name}
```

**Security Checks**:
- ✅ Token must be valid (not expired)
- ✅ Email must end with `@cloudfuze.com`
- ✅ User must exist in Microsoft Graph

---

## Phase 2: Frontend Request

### Step 2.1: User Sends Message

**Location**: `frontend/src/lib/chat-initialization.ts`

1. User types question in chat input
2. Frontend validates input (character limits)
3. Frontend creates/retrieves session ID
4. Frontend sends POST request to `/chat/stream`

### Step 2.2: Request Payload

```typescript
{
  question: "What is CloudFuze?",
  session_id: "cf.conversation.20251215.abc123"
}
```

### Step 2.3: Request Headers

```http
POST /chat/stream HTTP/1.1
Authorization: Bearer <microsoft_access_token>
Content-Type: application/json
```

---

## Phase 3: Backend Processing

### Step 3.1: Endpoint Entry Point

**Location**: `app/endpoints.py` - `/chat/stream`

**Initial Checks**:
1. ✅ Authentication validation (`require_auth` dependency)
2. ✅ Read-only session check (prevents editing others' chats)
3. ✅ Extract user info from verified token (not request body)

### Step 3.2: Extract Request Data

```python
question = data.get("question", "")
session_id = data.get("session_id", str(uuid.uuid4()))
user_id = auth_user["user_id"]      # From verified token
user_email = auth_user["email"]     # From verified token
user_name = auth_user["name"]       # From verified token
```

### Step 3.3: Event Tracking (Non-Blocking)

**Location**: `app/mongodb_memory.py` - `insert_message_event()`

**Process**:
1. Insert event into `message_events` collection
2. Store: `user_id`, `session_id`, `user_email`, `created_at`
3. **Non-blocking**: Errors don't break chat flow

**Purpose**: Analytics for dashboard (message counts, sessions, date-based filtering)

---

## Phase 4: Query Classification

### Step 4.1: Check for Corrected Response

**Location**: `app/endpoints.py` - `find_similar_corrected_response()`

**Process**:
1. Check if question matches a previously corrected response
2. If match found → return corrected answer immediately
3. Skip all retrieval and LLM processing

**Purpose**: Use human-corrected responses for known questions

### Step 4.2: Conversational Query Detection

**Location**: `app/endpoints.py` - `is_conversational_query()`

**Process**:
1. Check if query is a greeting ("hi", "hello", "thanks", "bye")
2. Check if query is conversational (not informational)
3. If conversational → handle directly with LLM (no retrieval)

**Conversational Path**:
```python
if is_conversational_query(question):
    # Use conversational prompt
    # No document retrieval
    # Direct LLM response
    # Temperature: 0.7 (more creative)
```

### Step 4.3: Intent Classification

**Location**: `app/endpoints.py` - `classify_intent()`

**Process**:
1. **Keyword Pre-filter**: Quick checks for common intents
   - "slack" + "teams" → `slack_teams_migration`
   - "pricing", "cost" → `pricing`
   - "certificate", "download" → `sharepoint_docs`

2. **LLM Classification**: For ambiguous queries
   - Uses LLM to classify into intent branches
   - Returns: `{intent, confidence, method}`

**Intent Branches**:
- `general_business` - General CloudFuze questions
- `slack_teams_migration` - Migration-specific
- `sharepoint_docs` - Documents, certificates
- `pricing` - Cost and pricing questions
- `troubleshooting` - Error/problem solving
- `email_conversations` - Email thread queries
- `other` - Default fallback

### Step 4.4: FAQ Event Tracking

**Location**: `app/mongodb_memory.py` - `insert_faq_event()`

**Process**:
1. Only for informational queries (not conversational)
2. Insert into `faq_events` collection
3. Store: `user_id`, `question`, `question_hash`, `created_at`
4. **Non-blocking**: Errors don't break chat flow

**Purpose**: Track frequently asked questions for analytics

---

## Phase 5: Document Retrieval

### Step 5.1: Query Expansion (Optional)

**Location**: `query_expander.py` - `QueryExpander.expand()`

**Condition**: `ENABLE_QUERY_EXPANSION = True`

**Process**:
1. Use LLM to generate query variations
2. Create synonyms and alternative phrasings
3. Expand query with intent-specific terms

**Example**:
```
Original: "CloudFuze pricing"
Expanded: ["CloudFuze cost", "CloudFuze subscription", "CloudFuze pricing plans"]
```

### Step 5.2: Perplexity-Style Retrieval (Option E)

**Location**: `app/endpoints.py` - `perplexity_style_retrieve()`

**Process**:
1. **Dense Retrieval** (Semantic Search):
   - Use ChromaDB vector similarity search
   - Retrieve top K documents (default: 40)
   - Uses sentence-transformers embeddings

2. **Sparse Retrieval** (BM25):
   - Use BM25 keyword matching
   - Retrieve top K documents (default: 40)
   - Uses `rank-bm25` library

3. **Combine Results**:
   - Merge dense + sparse results
   - Deduplicate by document content
   - Score normalization

4. **Reranking**:
   - Use cross-encoder reranker
   - Model: `cross-encoder/ms-marco-MiniLM-L-6-v2`
   - Final top K documents (default: 8)

**Retrieval Pipeline**:
```
Query
  ├─► Dense Retrieval (ChromaDB) → 40 docs
  ├─► Sparse Retrieval (BM25) → 40 docs
  ├─► Merge & Deduplicate
  └─► Rerank (Cross-Encoder) → 8 final docs
```

### Step 5.3: Branch-Specific Filtering (Legacy - Optional)

**Location**: `app/endpoints.py` - `retrieve_with_branch_filter()`

**Process**:
1. Retrieve documents from vectorstore
2. Filter by intent branch metadata tags
3. Apply source prioritization (SharePoint > Email > Blog)

**Source Prioritization**:
- SharePoint documents: 40% boost (score × 0.6)
- Email documents: 20% boost (score × 0.8)
- Blog documents: No boost

### Step 5.4: Hybrid Ranking

**Location**: `app/endpoints.py` - `hybrid_ranking()`

**Process**:
1. **Semantic Score**: From vector similarity (70% weight)
2. **Keyword Score**: From BM25/keyword matching (30% weight)
3. **Combined Score**: `alpha × semantic + (1-alpha) × keyword`

**Formula**:
```
final_score = 0.7 × semantic_score + 0.3 × keyword_score
```

### Step 5.5: Confidence-Based Fallback

**Location**: `app/endpoints.py` - `confidence_based_fallback()`

**Process**:
1. Check intent classification confidence
2. If confidence < threshold (e.g., 0.7):
   - Try alternative retrieval strategies
   - Expand search to "other" intent branch
   - Merge results with original

**Purpose**: Handle ambiguous queries that don't fit clear intent categories

### Step 5.6: Document Diversity

**Location**: `app/endpoints.py` - `calculate_document_diversity()`

**Process**:
1. Calculate diversity metrics:
   - Unique sources
   - Unique tags
   - Overall diversity score
2. Log diversity for debugging

**Purpose**: Ensure retrieved documents cover different aspects of the query

---

## Phase 6: Context Processing

### Step 6.1: Document Formatting

**Location**: `app/llm.py` - `format_docs()`

**Process**:
1. Extract document content and metadata
2. Add source tags: `[SOURCE: blog]`, `[SOURCE: sharepoint]`
3. Add special context for:
   - **SharePoint**: File name, folder path
   - **Email**: Subject, participants, date range
   - **Downloadable files**: Download URLs
   - **Videos**: Video URLs
   - **Blog posts**: Post URLs

**Example Format**:
```
[SOURCE: sharepoint]
File: Certificate.pdf
Folder: /Documents/Certificates

Content: ...
[DOWNLOAD LINK: Certificate.pdf - https://...]
```

### Step 6.2: Context Compression (Optional)

**Location**: `context_compressor.py` - `ContextCompressor.compress()`

**Condition**: `ENABLE_CONTEXT_COMPRESSION = True` AND context > max_chars

**Process**:
1. Check if total context exceeds `max_chars` (default: 8000)
2. If exceeds:
   - Use LLM to summarize context
   - Keep important details, steps, distinctions
   - Return compressed context
3. If within limit:
   - Return original context unchanged

**Purpose**: Reduce token usage while preserving important information

### Step 6.3: Context Assembly

**Process**:
1. Join formatted documents with `\n\n`
2. Create final context string
3. Prepare for LLM prompt

---

## Phase 7: LLM Response Generation

### Step 7.1: Prompt Construction

**Location**: `app/endpoints.py` - Chat prompt template

**System Prompt** (from `config.py`):
```
You are a CloudFuze AI assistant specializing in cloud migration services.
Answer questions based on the provided context.
Cite sources when referencing specific documents.
```

**User Prompt**:
```
Context: {formatted_context}

Question: {user_question}
```

### Step 7.2: LLM Selection

**Location**: `app/llm_factory.py` - `get_llm()`

**Configuration** (from `config.py`):
- `LLM_PROVIDER`: "openai" or "gemini"
- `OPENAI_API_KEY` or `GEMINI_API_KEY`

**Models**:
- **OpenAI**: `gpt-4o-mini` (default)
- **Google Gemini**: `gemini-2.5-flash-lite` (default)

**Parameters**:
- `temperature`: 0.1 (low for consistent responses)
- `max_tokens`: 1500
- `streaming`: True (for `/chat/stream`)

### Step 7.3: Response Generation

**Process**:
1. Invoke LLM with prompt
2. For streaming: Generate tokens incrementally
3. For non-streaming: Generate full response

**Streaming Flow**:
```
LLM → Token 1 → Frontend
     → Token 2 → Frontend
     → Token 3 → Frontend
     ...
     → Complete → Frontend
```

---

## Phase 8: Response Delivery

### Step 8.1: Streaming Response Format

**Location**: `app/endpoints.py` - `/chat/stream`

**SSE (Server-Sent Events) Format**:
```
data: {"type": "status", "status": "analyzing_query", "message": "Analyzing query"}

data: {"type": "status", "status": "retrieving_docs", "message": "Searching knowledge base"}

data: {"type": "status", "status": "reranking_docs", "message": "Found 8 documents, reranking for relevance"}

data: {"type": "thinking_complete"}

data: {"type": "token", "token": "Cloud"}

data: {"type": "token", "token": "Fuze"}

...

data: {"type": "done", "full_response": "...", "trace_id": "...", "recommended_questions": [...]}
```

### Step 8.2: Status Updates

**Status Types**:
- `analyzing_query` - Query classification
- `expanding_query` - Query expansion (if enabled)
- `retrieving_docs` - Document retrieval
- `reranking_docs` - Reranking documents
- `reading_sources` - Processing retrieved documents
- `thinking_complete` - Ready to stream response
- `token` - Individual response tokens
- `done` - Response complete

### Step 8.3: Recommended Questions

**Location**: `app/llm.py` - `generate_recommended_questions_from_docs()`

**Process**:
1. After response generation
2. Use LLM to generate 3-5 follow-up questions
3. Based on retrieved documents and response
4. Returned in `done` event

**Purpose**: Help users discover related information

### Step 8.4: Response Cleaning

**Location**: `app/helpers.py` - `strip_markdown()`, `preserve_markdown()`

**Process**:
1. Clean markdown formatting
2. Preserve important formatting (code blocks, lists)
3. Remove unnecessary markdown artifacts

---

## Phase 9: Session Management

### Step 9.1: Session Creation

**Location**: `app/mongodb_memory.py` - `save_session()`

**Process**:
1. Check if session exists
2. If new session:
   - Create session document
   - Store: `session_id`, `user_id`, `user_email`, `title`, `created_at`
3. If existing session:
   - Update session
   - Append messages to conversation

### Step 9.2: Conversation Storage

**Location**: `app/mongodb_memory.py` - `add_to_conversation()`

**Process**:
1. Add user message to conversation
2. Add assistant response to conversation
3. Store in MongoDB `chat_sessions` collection
4. Update `last_message_at` timestamp

**Conversation Format**:
```json
{
  "session_id": "cf.conversation.20251215.abc123",
  "user_id": "aad-12345",
  "messages": [
    {"role": "user", "content": "What is CloudFuze?"},
    {"role": "assistant", "content": "CloudFuze is..."}
  ],
  "updated_at": "2025-12-15T10:30:00Z"
}
```

### Step 9.3: User Activity Tracking

**Location**: `app/mongodb_memory.py` - `save_session()`

**Process**:
1. Update `user_activity` collection
2. Increment `total_messages`
3. Update `last_active` timestamp
4. Recalculate `avg_messages_per_session`

**Purpose**: Dashboard analytics (all-time statistics)

---

## Phase 10: Analytics & Tracking

### Step 10.1: Message Event Tracking

**Location**: `app/mongodb_memory.py` - `insert_message_event()`

**Collection**: `message_events`

**Stored Data**:
```json
{
  "user_id": "aad-12345",
  "session_id": "cf.conversation.20251215.abc123",
  "user_email": "user@cloudfuze.com",
  "created_at": "2025-12-15T10:30:00Z"
}
```

**Purpose**: Date-based analytics, session counting

### Step 10.2: FAQ Event Tracking

**Location**: `app/mongodb_memory.py` - `insert_faq_event()`

**Collection**: `faq_events`

**Stored Data**:
```json
{
  "user_id": "aad-12345",
  "question": "What is CloudFuze?",
  "question_hash": "a8f93c...",
  "user_email": "user@cloudfuze.com",
  "created_at": "2025-12-15T10:30:00Z"
}
```

**Purpose**: Track frequently asked questions

### Step 10.3: Langfuse Observability

**Location**: `app/langfuse_integration.py` - `langfuse_tracker.create_trace()`

**Process**:
1. Create trace for entire request
2. Log spans for:
   - Query processing
   - Document retrieval
   - LLM generation
3. Store metadata:
   - User info
   - Session info
   - Retrieval details
   - Response quality

**Purpose**: Debugging, performance monitoring, response quality tracking

### Step 10.4: Feedback Collection

**Location**: `app/endpoints.py` - `/feedback`

**Process**:
1. User provides feedback (thumbs up/down)
2. Store feedback in Langfuse
3. Link feedback to trace_id
4. Update response quality metrics

---

## Detailed Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER SENDS MESSAGE                           │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: AUTHENTICATION                                        │
│  - Verify Microsoft OAuth token                                 │
│  - Extract user info (user_id, email, name)                     │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 2: EVENT TRACKING                                        │
│  - Insert message_event (analytics)                             │
│  - Non-blocking (errors don't break flow)                       │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 3: QUERY CLASSIFICATION                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Check corrected response?                                 │  │
│  │  ├─ Yes → Return corrected answer (SKIP retrieval)       │  │
│  │  └─ No → Continue                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Is conversational query?                                  │  │
│  │  ├─ Yes → Direct LLM response (SKIP retrieval)          │  │
│  │  └─ No → Continue to retrieval                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Intent Classification                                     │  │
│  │  - Keyword pre-filter                                     │  │
│  │  - LLM classification (if ambiguous)                       │  │
│  │  - Returns: intent, confidence, method                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 4: DOCUMENT RETRIEVAL                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Query Expansion (Optional)                               │  │
│  │  - Generate query variations                             │  │
│  │  - Add intent-specific terms                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Perplexity-Style Retrieval                                │  │
│  │  1. Dense Retrieval (ChromaDB) → 40 docs                 │  │
│  │  2. Sparse Retrieval (BM25) → 40 docs                    │  │
│  │  3. Merge & Deduplicate                                  │  │
│  │  4. Rerank (Cross-Encoder) → 8 final docs                │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Source Prioritization                                    │  │
│  │  - SharePoint: 40% boost                                 │  │
│  │  - Email: 20% boost                                      │  │
│  │  - Blog: No boost                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Hybrid Ranking                                            │  │
│  │  - 70% semantic score                                    │  │
│  │  - 30% keyword score                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 5: CONTEXT PROCESSING                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Document Formatting                                      │  │
│  │  - Add source tags                                       │  │
│  │  - Add metadata (URLs, file names)                       │  │
│  │  - Format for LLM context                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Context Compression (Optional)                           │  │
│  │  - If context > 8000 chars                               │  │
│  │  - Use LLM to summarize                                  │  │
│  │  - Preserve important details                            │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 6: LLM RESPONSE GENERATION                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Prompt Construction                                      │  │
│  │  - System prompt (CloudFuze assistant)                   │  │
│  │  - Context (formatted documents)                         │  │
│  │  - User question                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ LLM Invocation                                           │  │
│  │  - Provider: OpenAI or Google Gemini                     │  │
│  │  - Model: gpt-4o-mini or gemini-2.5-flash-lite          │  │
│  │  - Temperature: 0.1 (consistent)                        │  │
│  │  - Streaming: Yes (for /chat/stream)                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 7: RESPONSE DELIVERY                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Streaming (SSE)                                          │  │
│  │  - Status updates                                         │  │
│  │  - Token-by-token response                               │  │
│  │  - Completion signal                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Recommended Questions                                     │  │
│  │  - Generate 3-5 follow-up questions                      │  │
│  │  - Based on retrieved docs                               │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 8: SESSION MANAGEMENT                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Save Conversation                                        │  │
│  │  - Add user message to session                           │  │
│  │  - Add assistant response to session                     │  │
│  │  - Update last_message_at                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Update User Activity                                      │  │
│  │  - Increment total_messages                               │  │
│  │  - Update last_active                                     │  │
│  │  - Recalculate avg_messages_per_session                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 9: ANALYTICS & TRACKING                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Langfuse Trace                                           │  │
│  │  - Log entire request flow                               │  │
│  │  - Store metadata                                        │  │
│  │  - Link to feedback                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ FAQ Event (if informational)                             │  │
│  │  - Insert into faq_events                                │  │
│  │  - For FAQ analytics                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Components

### 1. Authentication System

**Files**:
- `app/auth.py` - Authentication logic
- `app/endpoints.py` - `/auth/microsoft/callback`

**Flow**:
```
User → Microsoft OAuth → Backend → Verify Token → Return User Info
```

### 2. Query Processing

**Files**:
- `app/endpoints.py` - Query classification, expansion
- `query_expander.py` - Query expansion
- `app/helpers.py` - Query utilities

**Flow**:
```
Query → Classification → Expansion → Retrieval
```

### 3. Document Retrieval

**Files**:
- `app/vectorstore.py` - Vector store management
- `bm25_retriever.py` - BM25 sparse retrieval
- `reranker.py` - Cross-encoder reranking
- `app/endpoints.py` - Hybrid retrieval logic

**Flow**:
```
Query → Dense (ChromaDB) + Sparse (BM25) → Merge → Rerank → Final Docs
```

### 4. Context Processing

**Files**:
- `context_compressor.py` - Context compression
- `app/llm.py` - Document formatting

**Flow**:
```
Docs → Format → Compress (if needed) → Context String
```

### 5. LLM Integration

**Files**:
- `app/llm_factory.py` - LLM factory (OpenAI/Gemini)
- `app/llm.py` - LLM utilities
- `config.py` - LLM configuration

**Flow**:
```
Context + Query → LLM → Response
```

### 6. Session Management

**Files**:
- `app/mongodb_memory.py` - Session storage
- `app/endpoints.py` - Session handling

**Flow**:
```
Message → Save to Session → Update User Activity
```

### 7. Analytics

**Files**:
- `app/mongodb_memory.py` - Event tracking
- `app/langfuse_integration.py` - Observability

**Collections**:
- `message_events` - Message tracking
- `faq_events` - FAQ tracking
- `user_activity` - User statistics
- `chat_sessions` - Conversation history

---

## Data Flow

### Request Flow

```
Frontend
  │
  ├─► POST /chat/stream
  │   ├─► Authorization: Bearer <token>
  │   └─► Body: {question, session_id}
  │
  ▼
Backend (FastAPI)
  │
  ├─► Authentication Middleware
  │   └─► Verify Microsoft Token
  │
  ├─► Event Tracking (Non-blocking)
  │   └─► Insert message_event
  │
  ├─► Query Processing
  │   ├─► Check corrected response
  │   ├─► Check conversational
  │   ├─► Intent classification
  │   └─► Query expansion
  │
  ├─► Document Retrieval
  │   ├─► Dense retrieval (ChromaDB)
  │   ├─► Sparse retrieval (BM25)
  │   ├─► Merge & deduplicate
  │   └─► Rerank (Cross-encoder)
  │
  ├─► Context Processing
  │   ├─► Format documents
  │   └─► Compress (if needed)
  │
  ├─► LLM Generation
  │   ├─► Build prompt
  │   └─► Stream response
  │
  └─► Session Management
      ├─► Save conversation
      └─► Update user activity
```

### Response Flow

```
Backend
  │
  ├─► SSE Stream
  │   ├─► Status: "analyzing_query"
  │   ├─► Status: "retrieving_docs"
  │   ├─► Status: "reranking_docs"
  │   ├─► Status: "thinking_complete"
  │   ├─► Token: "Cloud"
  │   ├─► Token: "Fuze"
  │   ├─► ...
  │   └─► Done: {full_response, trace_id, recommended_questions}
  │
  ▼
Frontend
  │
  ├─► Display status updates
  ├─► Stream tokens to UI
  ├─► Show recommended questions
  └─► Store in session
```

---

## Error Handling

### Authentication Errors

**401 Unauthorized**:
- Invalid or expired token
- Missing Authorization header
- Response: Redirect to login

**403 Forbidden**:
- Non-CloudFuze email domain
- Response: Access denied message

### Processing Errors

**Vectorstore Not Available**:
- Fallback to default QA chain
- Log warning, continue processing

**LLM Errors**:
- Retry with exponential backoff
- Fallback to error message

**Retrieval Errors**:
- Confidence-based fallback
- Alternative retrieval strategies
- Never return empty results (always have fallback)

### Non-Blocking Errors

**Event Tracking Failures**:
- Log error
- Continue chat flow
- Don't break user experience

**Langfuse Failures**:
- Log warning
- Continue without observability
- Don't block response

---

## Performance Considerations

### Caching

1. **Vectorstore**: Loaded once at startup
2. **BM25 Index**: Built once, reused
3. **Reranker Model**: Loaded once, reused
4. **LLM Client**: Reused across requests

### Optimization

1. **Parallel Retrieval**: Dense + Sparse retrieval can run in parallel
2. **Streaming**: Reduces perceived latency
3. **Debouncing**: Frontend filters debounced (300ms)
4. **Non-blocking**: Analytics don't block chat flow

### Scalability

1. **MongoDB**: Handles session storage and analytics
2. **ChromaDB**: Efficient vector search
3. **Async Processing**: FastAPI async/await
4. **Connection Pooling**: Reused database connections

---

## Configuration Flags

### Feature Flags (from `config.py`)

| Flag | Purpose | Default |
|------|---------|---------|
| `ENABLE_INTENT_CLASSIFICATION` | Intent-based retrieval | `True` |
| `ENABLE_QUERY_EXPANSION` | Query expansion | `True` |
| `ENABLE_CONTEXT_COMPRESSION` | Context compression | `True` |
| `LLM_PROVIDER` | "openai" or "gemini" | "openai" |

### Retrieval Parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `DENSE_RETRIEVAL_K` | 40 | Documents from vector search |
| `BM25_RETRIEVAL_K` | 40 | Documents from BM25 |
| `FINAL_RETRIEVAL_K` | 8 | Final documents after reranking |
| `DENSE_WEIGHT` | 0.7 | Weight for semantic score |
| `BM25_WEIGHT` | 0.3 | Weight for keyword score |

---

## Example: Complete Request Flow

### User Query: "What is CloudFuze pricing?"

**Step-by-Step**:

1. **Frontend**: User types question, sends POST `/chat/stream`

2. **Authentication**: Verify Microsoft token → Extract user info

3. **Event Tracking**: Insert `message_event` → `message_events` collection

4. **Query Classification**:
   - Not corrected response
   - Not conversational
   - Intent: `pricing` (confidence: 0.85, method: keyword)

5. **Query Expansion**:
   - Original: "What is CloudFuze pricing?"
   - Expanded: ["CloudFuze cost", "CloudFuze subscription plans", "CloudFuze pricing"]

6. **Document Retrieval**:
   - Dense: 40 docs from ChromaDB
   - Sparse: 40 docs from BM25
   - Merge: 60 unique docs
   - Rerank: Top 8 docs

7. **Context Processing**:
   - Format: Add source tags, metadata
   - Compress: If > 8000 chars
   - Final context: 6000 chars

8. **LLM Generation**:
   - Prompt: System + Context + Question
   - Model: gpt-4o-mini
   - Temperature: 0.1
   - Response: "CloudFuze offers flexible pricing plans..."

9. **Streaming**:
   - Status: "analyzing_query"
   - Status: "retrieving_docs"
   - Status: "reranking_docs"
   - Status: "thinking_complete"
   - Tokens: "Cloud", "Fuze", "offers", ...
   - Done: Full response + trace_id + recommendations

10. **Session Management**:
    - Save user message
    - Save assistant response
    - Update user activity

11. **Analytics**:
    - Langfuse trace created
    - FAQ event inserted (if informational)

---

## Database Collections

### `message_events`
**Purpose**: Track every user message for date-based analytics

**Schema**:
```json
{
  "user_id": "aad-12345",
  "session_id": "cf.conversation.20251215.abc123",
  "user_email": "user@cloudfuze.com",
  "created_at": "2025-12-15T10:30:00Z"
}
```

### `faq_events`
**Purpose**: Track frequently asked questions

**Schema**:
```json
{
  "user_id": "aad-12345",
  "question": "What is CloudFuze?",
  "question_hash": "a8f93c...",
  "user_email": "user@cloudfuze.com",
  "created_at": "2025-12-15T10:30:00Z"
}
```

### `user_activity`
**Purpose**: Pre-aggregated user statistics (all-time)

**Schema**:
```json
{
  "user_id": "aad-12345",
  "user_email": "user@cloudfuze.com",
  "user_name": "User Name",
  "total_messages": 128,
  "total_sessions": 9,
  "avg_messages_per_session": 14.2,
  "last_active": "2025-12-15T10:30:00Z"
}
```

### `chat_sessions`
**Purpose**: Full conversation history

**Schema**:
```json
{
  "session_id": "cf.conversation.20251215.abc123",
  "user_id": "aad-12345",
  "user_email": "user@cloudfuze.com",
  "title": "CloudFuze pricing discussion",
  "messages": [
    {"role": "user", "content": "What is CloudFuze pricing?"},
    {"role": "assistant", "content": "CloudFuze offers..."}
  ],
  "created_at": "2025-12-15T10:00:00Z",
  "updated_at": "2025-12-15T10:30:00Z"
}
```

---

## API Endpoints

### Chat Endpoints

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/chat` | POST | Non-streaming chat | Full response JSON |
| `/chat/stream` | POST | Streaming chat | SSE stream |
| `/feedback` | POST | User feedback | Success confirmation |

### Authentication Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/microsoft/callback` | POST | OAuth callback |
| `/auth/verify` | GET | Token verification |

### Admin Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/admin/users/summary` | GET | All-time user statistics |
| `/admin/rankers` | GET | Date-based user rankers |
| `/admin/faqs` | GET | Frequently asked questions |

---

## Security Considerations

### Authentication

1. **Token Validation**: Every request validates Microsoft token
2. **Domain Restriction**: Only `@cloudfuze.com` emails allowed
3. **Token Expiration**: Tokens expire, require refresh
4. **Read-Only Sessions**: Cannot modify others' chats

### Data Protection

1. **User Info**: Extracted from verified token, not request body
2. **Session Isolation**: Users can only access their own sessions
3. **Admin Access**: Restricted to admin email allowlist

---

## Performance Metrics

### Typical Latencies

| Phase | Time | Notes |
|-------|------|-------|
| Authentication | < 100ms | Token verification |
| Query Classification | 200-500ms | LLM classification if needed |
| Document Retrieval | 500-1000ms | Dense + Sparse + Rerank |
| Context Processing | 100-300ms | Formatting + compression |
| LLM Generation | 2000-5000ms | Depends on response length |
| **Total** | **3-7 seconds** | End-to-end |

### Optimization Tips

1. **Caching**: Vectorstore, BM25 index cached
2. **Parallel Processing**: Dense + Sparse retrieval parallel
3. **Streaming**: Reduces perceived latency
4. **Non-blocking**: Analytics don't slow down responses

---

## Troubleshooting

### Common Issues

1. **No Documents Retrieved**:
   - Check vectorstore initialization
   - Verify documents are indexed
   - Check retrieval parameters

2. **Slow Responses**:
   - Check LLM provider status
   - Verify network connectivity
   - Check MongoDB connection

3. **Authentication Failures**:
   - Verify token is valid
   - Check email domain
   - Verify Microsoft Graph API access

4. **Streaming Issues**:
   - Check SSE connection
   - Verify frontend EventSource
   - Check network proxies

---

## Last Updated

- **Date**: December 2025
- **Project Version**: CF_Chatbot-V2
- **Documentation Version**: 1.0

---

## Notes

- All phases are designed to be **non-blocking** where possible
- Analytics failures **never break** the chat flow
- The system gracefully handles errors at every step
- Multiple fallback strategies ensure reliability

