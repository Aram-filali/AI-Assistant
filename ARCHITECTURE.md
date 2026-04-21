# Architecture Overview

## System Design

The AI Sales Assistant is built on a **modular, scalable architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND LAYER                           │
│                     (Next.js + React)                        │
│  ┌────────────────┐  ┌────────────┐  ┌──────────────┐      │
│  │ Auth Pages     │  │ Dashboard  │  │ Chat Widget  │      │
│  └────────────────┘  └────────────┘  └──────────────┘      │
│                API Client (lib/api.ts)                      │
└──────────────────────────┬───────────────────────────────────┘
                          │ HTTPS
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     API GATEWAY LAYER                        │
│                     (FastAPI + Uvicorn)                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Router Layer (app/api/)                  │   │
│  │  ┌──────────┐ ┌─────────┐ ┌──────────────┐         │   │
│  │  │ Auth     │ │ Chat    │ │ Knowledge    │        │   │
│  │  │ Router   │ │ Router  │ │ Base Router  │        │   │
│  │  └──────────┘ └─────────┘ └──────────────┘         │   │
│  └─────────────────┬───────────────────────────────────┘   │
│                    ▼                                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │       Service Layer (app/services/)                │   │
│  │  ┌──────────────┐  ┌──────────────┐                │   │
│  │  │ RAG Service  │  │ Chat Service │                │   │
│  │  │- Load        │  │- Message     │                │   │
│  │  │- Split       │  │- History     │                │   │
│  │  │- Embed       │  │- Generation  │                │   │
│  │  │- Index       │  │- Hybrid Mode │                │   │
│  │  │- Retrieve    │  │- Fallback    │                │   │
│  │  │- Generate    │  └──────────────┘                │   │
│  │  └──────────────┘                                  │   │
│  └─────────────────┬───────────────────────────────────┘   │
└────────────────────┼─────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  PostgreSQL  │ │    Redis     │ │  OpenAI API  │
│   Database   │ │    Cache     │ │  (LLM)       │
└──────────────┘ └──────────────┘ └──────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────┐
│  FAISS Vector Database (In-Memory Index)            │
│  - Document embeddings                              │
│  - Semantic search capability                       │
│  - Multi-tenant isolation via metadata              │
└──────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Frontend (Next.js 14)

**Purpose**: User interface for authenticated users and public chat  
**Key Features**:
- Server-side components for performance
- Client-side state management (React Context)
- Protected routes with auth checks
- API client with JWT token injection

**Directory Structure**:
```
frontend/
├── app/
│   ├── (auth)/               # Protected routes
│   │   └── dashboard/        # Main user dashboard
│   ├── components/           # Reusable React components
│   │   ├── ChatWidget.tsx   # Chat interface
│   │   ├── Navbar.tsx       # Navigation
│   │   └── FeatureCard.tsx  # Card component
│   ├── layout.tsx           # Root layout with providers
│   └── page.tsx             # Landing page
├── lib/
│   ├── api.ts               # Centralized API client
│   └── store.ts             # Global state management
└── public/                  # Static assets
```

### 2. Backend API (FastAPI)

**Purpose**: RESTful API for frontend + webhook handlers  
**Architecture**: Layered (Routers → Services → Models)  
**Key Features**:
- Async-first architecture
- Request/response validation (Pydantic schemas)
- JWT authentication & authorization
- Multi-tenant data isolation
- Comprehensive error handling & logging

**Directory Structure**:
```
backend/app/
├── api/                     # API Routers
│   ├── auth.py             # Authentication (register, login, me)
│   ├── chat.py             # Chat (messages, conversations)
│   ├── knowledge.py        # Knowledge base (CRUD + documents)
│   ├── actions.py          # Custom actions
│   └── admin.py            # Admin operations
├── core/
│   ├── config.py           # Settings from environment
│   ├── database.py         # DB connection & session management
│   ├── auth.py             # JWT utilities
│   └── rag/                # RAG pipeline components
│       ├── document_loader.py   # PDF/DOCX extraction
│       ├── text_splitter.py     # Chunking strategy
│       ├── embedder.py          # Sentence Transformers
│       ├── faiss_manager.py     # Vector database
│       ├── retriever.py         # Semantic search
│       └── generator.py         # LLM response generation
├── models/                 # SQLAlchemy ORM
│   ├── user.py
│   ├── knowledge.py        # KB + Documents
│   ├── conversation.py
│   ├── message.py
│   └── action.py
├── schemas/                # Pydantic request/response
│   ├── user.py
│   ├── chat.py
│   ├── knowledge.py
│   └── action.py
├── services/               # Business logic
│   ├── rag_service.py      # RAG pipeline orchestration
│   ├── chat_service.py     # Chat logic (hybrid mode)
│   ├── action_service.py   # Custom actions
│   └── lead_service.py     # Lead management
├── utils/                  # Helper functions
│   ├── validators.py
│   └── email.py
└── main.py                 # FastAPI app entry point
```

### 3. Database (PostgreSQL)

**Purpose**: Persistent data storage with ACID guarantees

**Schema**:
```sql
-- Users (Authentication)
table users {
  id UUID PRIMARY KEY
  email VARCHAR UNIQUE
  hashed_password VARCHAR
  full_name VARCHAR
  role ENUM (admin, user)  -- Role-based access
  is_active BOOLEAN
  created_at TIMESTAMP
}

-- Knowledge Bases (User's document collections)
table knowledge_bases {
  id UUID PRIMARY KEY
  user_id UUID FOREIGN KEY -> users
  name VARCHAR
  description TEXT
  created_at TIMESTAMP
}

-- Documents (Individual files)
table knowledge_documents {
  id UUID PRIMARY KEY
  knowledge_base_id UUID FOREIGN KEY -> knowledge_bases
  filename VARCHAR
  file_path VARCHAR
  file_type VARCHAR
  chunk_count INTEGER
  created_at TIMESTAMP
}

-- Conversations (Chat sessions)
table conversations {
  id UUID PRIMARY KEY
  user_id UUID FOREIGN KEY -> users
  knowledge_base_id UUID NULLABLE FOREIGN KEY -> knowledge_bases
  title VARCHAR
  metadata JSONB
  status ENUM
  created_at TIMESTAMP
}

-- Messages (Chat history)
table messages {
  id UUID PRIMARY KEY
  conversation_id UUID FOREIGN KEY -> conversations
  role ENUM (user, assistant)
  content TEXT
  metadata JSONB
  created_at TIMESTAMP
}
```

**Indexing Strategy**:
```sql
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_documents_kb_id ON knowledge_documents(knowledge_base_id);
-- Multi-tenant isolation indexes
CREATE INDEX idx_conversations_user_kb ON conversations(user_id, knowledge_base_id);
```

### 4. Vector Database (FAISS)

**Purpose**: Fast semantic search over document embeddings  
**Storage**: In-memory with periodic disk persistence  
**Integration**: SQLAlchemy metadata for document tracking

**Workflow**:
```
Document → Text Splitter → Sentence Transformers → Embeddings (384-dim)
                                                        ↓
                                                   FAISS Index
                                                        ↓
                          Query → Embedding → Top-K Search → Results
```

### 5. RAG Pipeline

**The complete flow**:

```
1. INGESTION (User uploads document)
   ├─ Load: Extract text from PDF/DOCX/URLs
   ├─ Split: Chunk into semantic pieces (512 tokens each)
   ├─ Embed: Generate vectors (SentenceTransformer)
   ├─ Index: Add to FAISS with metadata
   └─ Persist: Save to disk for production

2. RETRIEVAL (User asks question)
   ├─ Embed: Convert question to vector
   ├─ Search: Find K-nearest neighbors in FAISS (top_k=5)
   ├─ Filter: Multi-tenant isolation (only user's KB chunks)
   └─ Return: Top chunks with metadata

3. GENERATION (Generate answer)
   ├─ Context: Combine retrieved chunks + conversation history
   ├─ Prompt: Include in system prompt for GPT-4
   ├─ Generate: Call OpenAI API with context
   └─ Stream: Return response to frontend

4. STORAGE
   └─ Save: Store user message + assistant response in DB
```

---

## Data Flow

### Chat with Knowledge Base (RAG Mode)

```
User Message
    ↓
[Frontend] Send via API
    ↓
[Backend] Receive in chat.py endpoint
    ↓
[Chat Service] Load conversation + history
    ↓
[RAG Service] Semantic search in FAISS
    ↓
[Filter] Multi-tenant isolation applied
    ↓
[LLM] GPT-4 with context window:
      - Conversation history
      - Retrieved document chunks
      - System prompt
    ↓
[Response] AI-generated answer with sources
    ↓
[Persist] Save to messages table
    ↓
[Frontend] Display with source citations
```

### Chat without Knowledge Base (Standard Mode)

```
User Message
    ↓
[Backend] No KB linked
    ↓
[Chat Service] Skip RAG, use direct LLM
    ↓
[LLM] GPT-4 with only conversation history
    ↓
[Response] General conversation
    ↓
[Persist] Save to DB
    ↓
[Frontend] Display
```

---

## Security Architecture

### Multi-Tenant Isolation

Every database query includes user_id filter:
```python
# Example: Users can only see their own conversations
await db.execute(
    select(Conversation)
    .filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id  # ← Always present
    )
)
```

### Authentication Flow

```
Login Request
    ↓
[Backend] Verify password (PBKDF2-SHA256)
    ↓
[JWT Token] Generated with user ID + payload
    ↓
[Response] Return token to frontend
    ↓
[Frontend] Store in localStorage
    ↓
[Subsequent Requests] Include "Authorization: Bearer {token}"
    ↓
[Backend] Verify JWT signature + expiration
    ↓
[Authorize] Extract user_id from token → use for filtering
```

### RAGAS (Retrieval Augmented Generation Assessment)

- **Faithfulness**: Verify answers are grounded in documents
- **Relevance**: Ensure retrieved chunks match query intent
- **Harmlessness**: Filter dangerous prompts before LLM
- **Source Attribution**: Always cite document source

---

## Deployment Architecture

### Development (Local)

```
Docker Compose:
├─ Backend     → localhost:8000
├─ Frontend    → localhost:3000
├─ PostgreSQL  → localhost:5432
└─ Redis       → localhost:6379
```

### Production (Railway + Vercel)

```
Frontend:
└─ Vercel CDN → 

Backend:
├─ Railway Instance → 
├─ PostgreSQL (Railway) → Managed by Railway
├─ Redis (Railway) → Managed by Railway
└─ FAISS Index → On-disk in container

External:
└─ OpenAI API → GPT-4 access (using openrouter service)
```

---

## Performance Optimization

### Database

- **Indexes**: On `user_id`, `conversation_id`, join columns
- **Eager Loading**: Use `selectinload()` to prevent N+1 queries
- **Connection Pooling**: Async SQLAlchemy with pool_size=20
- **Query Profiling**: Log slow queries (>1s)

### RAG Pipeline

- **Caching**: Redis for frequently accessed chunks
- **Batch Processing**: Embed documents in batches (32)
- **FAISS Optimization**: GPU acceleration option available
- **Lazy Loading**: Load large indices on-demand

### Frontend

- **Code Splitting**: Next.js automatic route splitting
- **Image Optimization**: Next.js Image component
- **CSS-in-JS**: Tailwind for efficient styling
- **API Caching**: HTTP caching headers where appropriate

---

## Monitoring & Observability

### Logging

- **Backend**: Structured logging (JSON format)
  - Auth events (login, token expiration)
  - RAG operations (retrieval quality)
  - Errors (full traceback)
  
- **Frontend**: Browser console only (no PII)

### Metrics

Track:
- API response times
- RAG retrieval quality (relevance scores)
- Chat response latency
- Document processing speed
- Concurrent user count

### Error Tracking

- **Sentry**: For unhandled exceptions
- **Health Checks**: `/health` endpoint for load balancers
- **Alerting**: High error rates, DB connection failures

---

## Future Scaling

### Horizontal
- Multiple backend instances with load balancer
- Database read replicas for analytics
- Distributed FAISS indices per KB

### Vertical
- GPU acceleration for embeddings
- Batch processing for document indexing
- Async task queue (Celery) for background jobs

### Architectural
- GraphQL for complex queries
- WebSocket for real-time updates
- Message queues (RabbitMQ) for async operations
- Microservices split (RAG ingestion separate from chat)

---

**Last Updated**: April 2026  
**Architecture Type**: Monolith → Microservices Ready  
**Scaling Status**: Ready for 1K+ concurrent users with optimizations
