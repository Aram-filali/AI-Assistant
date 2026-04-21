# 📖 Project Navigation Guide for Code Review

Welcome! This guide helps you navigate the codebase efficiently. Start here to understand the structure.

---

## 🚀 Quick Navigation

### For First-Time Reviewers
1. **Start Here**: [README.md](README.md) - Project overview & features
2. **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md) - System design & data flow
3. **Deployment**: [PRODUCTION_DEPLOYMENT_PLAN_RAILWAY_VERCEL.md](PRODUCTION_DEPLOYMENT_PLAN_RAILWAY_VERCEL.md) - Production setup

### For Security Review
1. [SECURITY.md](SECURITY.md) - Security features & vulnerability handling
2. [backend/app/api/auth.py](backend/app/api/auth.py) - Authentication logic
3. [backend/app/core/auth.py](backend/app/core/auth.py) - JWT token management
4. [backend/tests/test_security_performance.py](backend/tests/test_security_performance.py) - Security tests

### For Code Quality
1. [CONTRIBUTING.md](CONTRIBUTING.md) - Code standards & PR guidelines
2. [TEST_COVERAGE_REPORT.md](COVERAGE_REPORT_FINAL.md) - Test results (160/160 passing ✅)
3. [backend/pytest.ini](backend/pytest.ini) - Test configuration
4. [.github/CODEOWNERS](.github/CODEOWNERS) - Code ownership

---

## 📁 Key Files by Category

### 🎯 Core Business Logic

| File | Purpose | Key Insights |
|------|---------|--------------|
| [backend/app/services/rag_service.py](backend/app/services/rag_service.py) | RAG pipeline orchestration | Load → Split → Embed → Index → Retrieve → Generate |
| [backend/app/services/chat_service.py](backend/app/services/chat_service.py) | Hybrid chat (RAG + standard) | Automatic mode selection based on KB presence |
| [backend/app/services/action_service.py](backend/app/services/action_service.py) | Custom actions execution | Extensible action framework |
| [backend/app/core/rag/](backend/app/core/rag/) | RAG components | Modular pipeline pieces |

### 🔐 Authentication & Security

| File | Purpose | Key Insights |
|------|---------|--------------|
| [backend/app/api/auth.py](backend/app/api/auth.py) | Auth endpoints | Register, Login, JWT generation |
| [backend/app/core/auth.py](backend/app/core/auth.py) | Auth utilities | Token creation/verification |
| [backend/app/main.py](backend/app/main.py) | App setup | CORS, middleware, route registration |
| [SECURITY.md](SECURITY.md) | Security policies | Best practices & incident response |

### 💾 Data Models

| File | Purpose | Key Insights |
|------|---------|--------------|
| [backend/app/models/user.py](backend/app/models/user.py) | User model | Accounts, roles, authentication |
| [backend/app/models/knowledge.py](backend/app/models/knowledge.py) | KB entities | Knowledge bases & documents |
| [backend/app/models/conversation.py](backend/app/models/conversation.py) | Chat sessions | Conversations with KB linkage |
| [backend/app/models/message.py](backend/app/models/message.py) | Messages | Chat history with roles |

### 🌐 API Endpoints

| File | Purpose | Endpoints |
|------|---------|-----------|
| [backend/app/api/auth.py](backend/app/api/auth.py) | Authentication | `/auth/register`, `/auth/login`, `/auth/me` |
| [backend/app/api/chat.py](backend/app/api/chat.py) | Chat | `/chat/conversations`, `/chat/messages` |
| [backend/app/api/knowledge.py](backend/app/api/knowledge.py) | Knowledge base | `/knowledge/bases`, `/knowledge/*/documents` |
| [backend/app/api/admin.py](backend/app/api/admin.py) | Admin | `/admin/users`, `/admin/stats` |

### 🎨 Frontend Components

| File | Purpose | Key Insights |
|------|---------|--------------|
| [frontend/app/page.tsx](frontend/app/page.tsx) | Landing page | Public face of the application |
| [frontend/app/components/ChatWidget.tsx](frontend/app/components/ChatWidget.tsx) | Chat interface | Real-time messaging UI |
| [frontend/app/components/Navbar.tsx](frontend/app/components/Navbar.tsx) | Navigation | Route & user menu |
| [frontend/lib/api.ts](frontend/lib/api.ts) | API client | Centralized HTTP wrapper |

### 🧪 Testing & Quality

| File | Purpose | Coverage |
|------|---------|----------|
| [backend/tests/test_rag.py](backend/tests/test_rag.py) | RAG pipeline tests | 44/44 passing ✅ |
| [backend/tests/test_models_*.py](backend/tests/) | Model layer tests | 37/37 passing ✅ |
| [backend/tests/test_integration_api.py](backend/tests/test_integration_api.py) | API integration tests | 54/54 passing ✅ |
| [backend/tests/test_security_performance.py](backend/tests/test_security_performance.py) | Security & perf tests | 25/25 passing ✅ |

### 📦 Configuration & Infrastructure

| File | Purpose | Usage |
|------|---------|-------|
| [backend/.env.example](backend/.env.example) | Backend config template | Copy to `.env` for development |
| [frontend/.env.example](frontend/.env.example) | Frontend config template | Copy to `.env.local` for development |
| [docker-compose.yml](docker-compose.yml) | Local dev environment | `docker-compose up` |
| [backend/requirements.txt](backend/requirements.txt) | Python dependencies | Core packages & versions |
| [frontend/package.json](frontend/package.json) | Node.js dependencies | React, Next.js, utilities |

---

## 🎓 Understanding the Architecture

### Data Flow for Chat with RAG

```
User Types Message
    ↓
[Frontend] ChatWidget.tsx sends via lib/api.ts
    ↓
[Backend] app/api/chat.py receives POST
    ↓
[Service] chat_service.py determines mode
    ↓
IF Knowledge Base linked:
    [RAG Service] rag_service.py:
    - Semantic search in FAISS
    - Multi-tenant filtering
    - Retrieved chunks passed to LLM
ELSE:
    Standard chat with LLM only
    ↓
[Database] Message saved to messages table
    ↓
[Frontend] Response displayed with sources
```

### Multi-Tenant Isolation

Every database query is filtered by `user_id`:

```python
# Example from chat.py
await db.execute(
    select(Conversation)
    .filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id  # ← Always present
    )
)
```

This ensures:
- Users only see their own conversations
- Documents only appear in their KBs
- No data leakage between tenants

---

## 🔍 Code Review Checklist

When reviewing code, check for:

### Security ✅
- [ ] Multi-tenant filtering present (`user_id` in WHERE clause)
- [ ] Password hashed before storage (PBKDF2)
- [ ] No hardcoded secrets
- [ ] Input validated (Pydantic schemas)
- [ ] SQL injection prevention (parameterized queries)

### Performance ✅
- [ ] Eager loading used (selectinload, joinedload)
- [ ] Indexes on FK columns & search filters
- [ ] Async/await throughout
- [ ] No N+1 queries
- [ ] Caching where appropriate

### Code Quality ✅
- [ ] Type hints present (Python & TypeScript)
- [ ] Comments explain "why", not "what"
- [ ] Docstrings on public functions
- [ ] Tests provided for new code
- [ ] Error handling comprehensive

---

## 📊 Project Metrics

```
Backend:
├─ Python Files: 50+
├─ Lines of Code: ~8,000
├─ Test Coverage: 160/160 passing (100% ✅)
└─ API Endpoints: 30+

Frontend:
├─ TypeScript Files: 20+
├─ Components: 10+ reusable
├─ Pages: 5+ main routes
└─ Bundle Size: <200KB (optimized)

Tests:
├─ Unit Tests: 80+
├─ Integration Tests: 54+
├─ Security Tests: 25+
└─ Total: 160+ passing ✅
```

---

## 🚀 Getting Started with Development

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
pytest tests/ -v
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with API_URL=http://localhost:8000
npm run dev
```

### Running Tests
```bash
# All tests
pytest backend/tests/ -v

# Coverage report
pytest backend/tests/ --cov=backend/app --cov-report=html

# Specific test file
pytest backend/tests/test_rag.py -v
```

---

## 💡 Key Architectural Decisions

1. **Async-First**: All I/O operations are async for scalability
2. **Service Layer**: Business logic separated from routers
3. **Multi-Tenant**: User_id filtering on all queries for isolation
4. **RAG Pipeline**: Modular components for flexibility
5. **Hybrid Chat**: Automatic RAG detection based on KB presence
6. **Factory Pattern for Tests**: Reusable test data generation

---

## 📞 Getting Help

- **Questions**: Check [README.md](README.md) FAQ section
- **Architecture**: Read [ARCHITECTURE.md](ARCHITECTURE.md)
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)
- **Security**: Review [SECURITY.md](SECURITY.md)
- **Setup Issues**: Check [PRODUCTION_DEPLOYMENT_PLAN_RAILWAY_VERCEL.md](PRODUCTION_DEPLOYMENT_PLAN_RAILWAY_VERCEL.md)

---

**Last Updated**: April 2026  
**Status**: ✅ Production Ready  
**Test Results**: 160/160 passing  
**Code Quality**: Industry standards maintained
