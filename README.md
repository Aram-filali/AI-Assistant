# 🤖 AI Sales & Support Assistant

> Assistant intelligent pour automatiser les interactions commerciales et support client avec RAG (Retrieval-Augmented Generation)

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)
![Next.js](https://img.shields.io/badge/Next.js-14.1-black.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)
![Redis](https://img.shields.io/badge/Redis-7-red.svg)

---

## 📋 Vue d'Ensemble

Système d'assistant IA qui combine :
- **RAG (Retrieval-Augmented Generation)** : Réponses basées sur votre base de connaissances
- **Actions Automatiques** : Envoi d'emails, création de tickets, mise à jour CRM
- **Support 24/7** : Disponibilité permanente pour prospects et clients
- **Qualification Intelligente** : Scoring automatique des leads

---

## 🏗️ Architecture
```
┌─────────────────────────────────────────────────┐
│            Frontend (Next.js 14)                │
│  • Interface Chat                               │
│  • Dashboard Admin                              │
│  • Analytics                                    │
└────────────────┬────────────────────────────────┘
                 │ REST API / WebSocket
                 ▼
┌─────────────────────────────────────────────────┐
│          Backend (FastAPI)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │   RAG    │  │  Actions │  │   Chat   │     │
│  │  Engine  │  │  Engine  │  │ Service  │     │
│  └──────────┘  └──────────┘  └──────────┘     │
└──────┬──────────────┬─────────────┬────────────┘
       │              │             │
       ▼              ▼             ▼
┌──────────┐   ┌──────────┐  ┌─────────────┐
│PostgreSQL│   │  Redis   │  │   OpenAI    │
│    16    │   │    7     │  │  GPT-4 API  │
└──────────┘   └──────────┘  └─────────────┘
```

---

## 🚀 Quick Start

### Prérequis

- Docker Desktop
- Python 3.11+
- Node.js 18+
- Git

### Installation
```bash
# 1. Cloner le repo
git clone https://github.com/VOTRE_USERNAME/ai-sales-assistant.git
cd ai-sales-assistant

# 2. Démarrer PostgreSQL + Redis (Docker)
./manage.sh start

# 3. Backend Setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Éditer .env avec vos clés API

# 4. Migrations
alembic upgrade head

# 5. Démarrer Backend
uvicorn app.main:app --reload

# 6. Frontend Setup (nouveau terminal)
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

### Accès

- **Frontend** : http://localhost:3000
- **Backend API** : http://localhost:8000
- **API Docs** : http://localhost:8000/docs
- **pgAdmin** : http://localhost:5050 (si démarré avec `./manage.sh start-tools`)

---

## 📁 Structure du Projet
```
ai-sales-assistant/
├── backend/                  # API FastAPI
│   ├── app/
│   │   ├── api/             # Endpoints REST
│   │   ├── core/            # Config, database, security
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   └── main.py          # Application entry point
│   ├── alembic/             # Database migrations
│   ├── scripts/             # Utilitaires
│   ├── tests/               # Tests unitaires
│   └── requirements.txt     # Python dependencies
│
├── frontend/                # Application Next.js
│   ├── src/
│   │   ├── app/            # Pages (App Router)
│   │   ├── components/     # Composants React
│   │   ├── lib/            # Utilitaires
│   │   └── hooks/          # Custom hooks
│   └── package.json        # Node dependencies
│
├── data/                    # Données runtime
│   ├── documents/          # Documents indexés
│   ├── faiss_index/        # Index vectoriels
│   └── logs/               # Logs application
│
├── docker-compose.yml      # Services Docker
├── manage.sh               # Script de gestion
└── README.md              # Ce fichier
```

---

## 🛠️ Commandes Utiles

### Docker (Database)
```bash
./manage.sh start          # Démarrer PostgreSQL + Redis
./manage.sh stop           # Arrêter les services
./manage.sh status         # Voir le statut
./manage.sh logs           # Voir les logs
./manage.sh psql           # Se connecter à PostgreSQL
./manage.sh redis          # Se connecter à Redis
./manage.sh backup         # Backup de la DB
./manage.sh reset          # Reset complet (⚠️ supprime data)
```

### Backend
```bash
# Migrations
alembic revision --autogenerate -m "Description"
alembic upgrade head
alembic downgrade -1

# Tests
pytest
pytest --cov=app tests/

# Linter
black app/
ruff check app/
```

### Frontend
```bash
npm run dev        # Dev server
npm run build      # Production build
npm run lint       # ESLint
```

---

## 🔑 Variables d'Environnement

### Backend (.env)
```env
# OpenAI
OPENAI_API_KEY=sk-...

# Database (Docker)
DATABASE_URL=postgresql+asyncpg://ai_sales_user:ai_sales_2024_secure@localhost:5432/ai_sales_db

# Redis (Docker)
REDIS_URL=redis://:redis_password_2024@localhost:6379/0

# Email (Resend)
RESEND_API_KEY=re_...

# Security
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 📚 Documentation

- [Documentation Technique Complète](./docs/TECHNICAL.md)
- [Guide d'Architecture](./docs/ARCHITECTURE.md)
- [API Reference](http://localhost:8000/docs) (une fois lancé)

---

## 🧪 Tests
```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

---

## 🤝 Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amazing-feature`)
3. Commit (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing-feature`)
5. Ouvrir une Pull Request

---

## 📝 Roadmap

- [x] Setup projet et Docker
- [x] Modèles de données
- [ ] Système RAG complet
- [ ] API Chat fonctionnelle
- [ ] Interface utilisateur
- [ ] Actions automatiques
- [ ] Dashboard analytics
- [ ] Tests end-to-end
- [ ] Déploiement production

---

## 📄 License

MIT License - voir [LICENSE](LICENSE)

---

## 👨‍💻 Auteur

**Votre Nom**
- GitHub: [@votre-username](https://github.com/votre-username)
- Email: votre.email@example.com

---

## 🙏 Remerciements

- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/)
- [OpenAI](https://openai.com/)
- [LangChain](https://python.langchain.com/)

---

**⭐ Star ce repo si vous le trouvez utile !**