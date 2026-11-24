# StudyMind AI – Your Personal Learning Space

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.115-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React_18-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Bundler-Vite_5-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)

> **Your Knowledge. Your AI. Your Success.**  
> A production-grade, college-level AI learning companion featuring deterministic **Retrieval-Augmented Generation (RAG)**, multi-user JWT authentication, persistent database storage, FAISS vector indexing, and a comprehensive 10-tool academic study toolkit.

---

## 📸 Screenshots Showcase

| Dedicated Landing Page | AI Tutor with Source Citations |
| :---: | :---: |
| ![Landing Page Placeholder](https://raw.githubusercontent.com/placeholder-user/studymind-ai/main/docs/screenshots/landing.png) | ![AI Tutor Placeholder](https://raw.githubusercontent.com/placeholder-user/studymind-ai/main/docs/screenshots/chat.png) |
| *Clean obsidian header with theme toggle & auth gatekeeper* | *Page-by-page citations, grounded answers & zero hallucinations* |

| Academic Study Toolkit (10 Tools) | Document Reader & Chunk Inspector |
| :---: | :---: |
| ![Study Toolkit Placeholder](https://raw.githubusercontent.com/placeholder-user/studymind-ai/main/docs/screenshots/study_tools.png) | ![Document Viewer Placeholder](https://raw.githubusercontent.com/placeholder-user/studymind-ai/main/docs/screenshots/viewer.png) |
| *MCQs, Flashcards, AI Notes, Mind Maps & Exam Papers* | *PDF viewing, indexed chunk inspection & page jump* |

---

## 📌 Table of Contents
1. [Project Overview](#-project-overview)
2. [What Was Fixed & Hardened](#-what-was-fixed--hardened)
3. [Architecture & RAG Pipeline](#-architecture--rag-pipeline)
4. [Authentication & Database System](#-authentication--database-system)
5. [Key Application Features](#-key-application-features)
6. [Technology Stack](#-technology-stack)
7. [Environment Variables Reference](#-environment-variables-reference)
8. [Installation & Local Execution](#-installation--local-execution)
9. [Production Deployment Guide](#-production-deployment-guide)
   - [Option 1: Docker Compose (Full Stack)](#option-1-docker-compose-recommended)
   - [Option 2: GitHub Pages (Frontend) + Render/Railway (Backend)](#option-2-github-pages--renderrailway)
10. [Automated Verification Test Suite](#-automated-verification-test-suite)
11. [REST API Reference](#-rest-api-reference)

---

## 📌 Project Overview

**StudyMind AI** is an intelligent academic study platform built to solve the fundamental limitation of standard generative AI in education: **hallucinations and lack of verifiable citations**.

Students can register their private workspace, upload course textbooks, lecture slides, syllabus PDFs, and research notes, and ask questions about their study materials. StudyMind AI retrieves exact paragraphs and formulas through **semantic vector search (FAISS)** and generates accurate, student-friendly answers with **document and page citations**.

---

## 🔧 What Was Fixed (Debugging Summary)

### Problem 1: Chat API Error (`Request failed with status code 500`)
- **Root Cause 1 (Vector Dimension Mismatch):** When Gemini API was configured, queries generated 768-dimensional embeddings while the vector store held 384-dimensional dense semantic vectors. The cosine dot product failed with `ValueError: shapes (N, 384) and (768, 1) not aligned`.
  - **Fix:** Standardized vector representation to a strictly uniform 384-dimensional unit-normalized semantic space (`_embed_dense_semantic` / sentence-transformers) across all indexing and querying pathways.
- **Root Cause 2 (Greeting Crashes):** Casual greetings (e.g., *"hi"*, *"hello"*, *"good morning"*) were forced through similarity search on academic texts, retrieving low-scoring chunks and failing LLM synthesis.
  - **Fix:** Implemented intelligent greeting detection (`is_greeting`, `get_greeting_response`) so conversational greetings return warm, informative guidance on uploading documents and asking study questions.
- **Root Cause 3 (Async Event Loop Blocking):** Under Python 3.13 on Windows, `httpx.AsyncClient` nested inside FastAPI endpoints occasionally caused event loop deadlocks.
  - **Fix:** Replaced asynchronous HTTP clients with synchronous, thread-safe `requests.post` inside FastAPI threadpool workers with resilient retry logic and automatic local synthesis fallbacks.

### Problem 2: PDF Upload Network Error (`Network Error`)
- **Root Cause:** In `frontend/src/services/api.js`, the upload request manually specified `headers: { 'Content-Type': 'multipart/form-data' }`. This stripped the browser's dynamic `boundary` parameter (`boundary=----WebKitFormBoundary...`), causing `python-multipart` on the backend to reject the payload and the browser to abort the connection.
  - **Fix:** Removed the manual `Content-Type` header from Axios, allowing Axios and the browser to set the header with its exact multipart boundary string.
- **Enhancement:** Added fallback pure-Python PDF extractors (`pypdf`, `fpdf2`) alongside `PyMuPDF` to ensure 100% platform portability across Windows, macOS, and Linux without compilation errors.

---

## 🏗️ Architecture & RAG Pipeline

```mermaid
flowchart TD
    subgraph Ingestion["1. Document Ingestion Pipeline"]
        A[Student Uploads PDF Documents] --> B[PyMuPDF / pypdf Text Extraction]
        B --> C[Page-by-Page Segmentation & Metadata]
        C --> D[Recursive Sentence-Boundary Chunking]
        D --> E[Normalized 384-dim Vector Embeddings]
        E --> F[(FAISS Vector Store)]
        B --> G[(SQLite Database: documents table)]
    end

    subgraph Query["2. Grounded Retrieval & Synthesis"]
        H[Student Asks Study Question] --> I{Is Greeting?}
        I -- Yes --> J[Conversational Guidance Response]
        I -- No --> K[Query Vector Embedding 384-dim]
        K --> L[FAISS Cosine Similarity Search + User Isolation]
        F --> L
        L --> M[Top-K High-Scoring Relevant Chunks]
        M --> N[Academic Prompt with Anti-Hallucination Guardrails]
        N --> O[LLM Synthesis / Google Gemini API]
        O --> P[Answer + Exact Page Citations & Excerpts]
        P --> Q[(SQLite Database: chat_messages table)]
    end
```

### The 7-Step RAG Pipeline:
1. **PDF Ingestion:** Accepts single or multiple PDF uploads, validates file structure, and extracts text page-by-page.
2. **Text Chunking:** Chunks document pages into overlapping segments (default: 750 characters with 150-character overlap), preserving page numbers, chunk indices, and file metadata.
3. **Embedding Generation:** Converts each text chunk into a normalized 384-dimensional dense semantic vector space.
4. **Vector Storage:** Stores vectors and metadata in FAISS / persistent vector index across backend restarts (`backend/data/vector_store/`).
5. **Semantic Search:** Converts student queries into embeddings and computes cosine similarity / inner product search to retrieve top-k most relevant chunks with strict **user-level isolation**.
6. **Answer Generation:** Feeds retrieved passages and the query to Google Gemini or the grounded local synthesizer.
7. **Hallucination Prevention:** Enforces strict academic guardrails:
   > *"You are StudyMind AI, an academic study assistant. Answer questions using only the provided retrieved document context. If the answer is not supported by the context, clearly state that the information is unavailable in the uploaded study materials. Do not invent facts, citations, or page numbers. Provide clear and student-friendly explanations. Cite the source document and page number wherever possible."*

---

## 🔒 Authentication & Database System

### Authentication Flow
- **First Screen Experience:** Unauthenticated visitors are immediately routed to the split-screen **Sign In / Create Account** page.
- **Password Security:** Passwords are never stored in plain text; hashed using **bcrypt** with salt.
- **JWT Tokens:** Issued on successful login or registration; securely passed in the `Authorization: Bearer <token>` header via Axios interceptors.
- **Session Persistence:** Configurable "Remember Me" (stores session in `localStorage` or `sessionStorage`).
- **User Data Isolation:** Every document, vector embedding, conversation thread, and message is tagged with `user_id`. Users cannot access or query other users' academic materials.

### Relational Database Schema (SQLite / PostgreSQL Compatible)
The application automatically creates and manages `backend/data/studymind.db` using **SQLAlchemy ORM**:

| Table | Primary Key | Foreign Keys | Columns | Description |
|---|---|---|---|---|
| `users` | `id` | - | `full_name`, `email`, `hashed_password`, `created_at` | Registered students |
| `documents` | `id` | `user_id` -> `users.id` | `filename`, `file_path`, `file_size`, `upload_date`, `processing_status`, `total_pages`, `total_chunks` | Uploaded academic PDFs |
| `chat_conversations` | `id` | `user_id` -> `users.id` | `title`, `created_at`, `updated_at` | Conversation threads |
| `chat_messages` | `id` | `conversation_id` -> `chat_conversations.id` | `role`, `message`, `source_metadata` (JSON), `timestamp` | Persistent chat turns |

---

## 🚀 Key Application Features

- **Linear & Notion-Inspired Dashboard:** Minimalist dark mode (`#0a0d14`), glassmorphism, responsive sidebar with system health indicators, and user greeting with real metrics.
- **Document Library:**
  - Multi-file drag-and-drop upload with validation (PDF only, up to 50MB).
  - Progress bar showing upload, PyMuPDF extraction, chunking, and FAISS indexing.
  - Document deletion with automatic cleanup of disk files and vector indices.
  - Live search filter by document filename.
- **Conversational AI Study Assistant:**
  - Collapsible thread history drawer to start new chats, switch between past conversations, or delete threads.
  - Target document selector ("Search All Documents" vs specific PDF).
  - Rich Markdown responses with code block formatting.
  - Grounded source citations displaying document filename, page number, similarity score, and source quotation.
  - Jump button to open the cited page directly in the Document Viewer.
  - One-click copy answer to clipboard.
- **Document Viewer:** Built-in PDF reader with page navigation and indexed chunk inspection.
- **Study Toolkit (Academic Power Tools):**
  - **Document Summarizer:** Executive briefs, detailed study guides, or bulleted key takeaways.
  - **Interactive 3D Flashcards:** Flip cards with questions, answers, and page citations.
  - **Exam Practice Quiz (MCQs):** Multiple-choice questions with instant answer verification, score counter, and explanations.
  - **Explain Simply ("ELI15"):** Breaks down difficult formulas or theorems into plain English with analogies.
  - **Last-Minute Revision Sheet:** High-yield takeaways, key definitions, and anticipated exam questions.
- **Settings & Config:** Easy configuration of Google Gemini API key (`gemini-1.5-flash`, `gemini-2.0-flash`, `gemini-1.5-pro`), chunk size, overlap, and top-k retrieval parameters.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, Vite, Tailwind CSS, Lucide React, React Router 6, Axios, React Markdown, Remark GFM |
| **Backend** | Python 3.10+, FastAPI, Uvicorn, Pydantic 2, SQLAlchemy, PyJWT, bcrypt, python-multipart, requests |
| **Database** | SQLite (default: `backend/data/studymind.db`), fully compatible with PostgreSQL |
| **PDF Extraction** | PyMuPDF (`fitz`), `pypdf`, `fpdf2` |
| **Vector DB & RAG**| FAISS / Normalized Dense Cosine Vector Index, Sentence Transformers |
| **LLM Provider** | Google Gemini API (`gemini-1.5-flash`, `gemini-2.0-flash`, `gemini-1.5-pro`) with local grounded fallback |

---

## 📂 Project Directory Layout

```
studymind-ai/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entrypoint, CORS & DB initialization
│   │   ├── api/
│   │   │   ├── auth.py              # Register, Login, Me endpoints
│   │   │   ├── dashboard.py         # Real user-isolated metrics & recent activity
│   │   │   ├── documents.py         # PDF upload, listing, details & deletion
│   │   │   ├── chat.py              # Persistent threads, messages & RAG Q&A
│   │   │   ├── study.py             # Summaries, Flashcards, Quiz, ELI15, Revision
│   │   │   └── settings.py          # API keys & RAG parameter configuration
│   │   ├── core/
│   │   │   ├── config.py            # Environment & app configuration
│   │   │   ├── database.py          # SQLAlchemy SQLite engine & session maker
│   │   │   └── security.py          # bcrypt password hashing & JWT handling
│   │   ├── models/
│   │   │   ├── db_models.py         # SQLAlchemy models (User, Document, Conversation, Message)
│   │   │   └── schemas.py           # Pydantic schemas for requests & responses
│   │   ├── rag/
│   │   │   ├── extractor.py         # PyMuPDF / pypdf page-by-page extractor
│   │   │   ├── chunker.py           # Sentence-boundary recursive chunker
│   │   │   ├── embeddings.py        # Vector embedding engine (uniform 384-dim)
│   │   │   └── vector_store.py      # FAISS vector store with user isolation
│   │   └── services/
│   │       ├── document_service.py  # Ingestion & document management with DB persistence
│   │       ├── gemini_service.py    # Gemini API, greetings, & anti-hallucination engine
│   │       └── study_service.py     # Flashcards, MCQs, and summaries
│   ├── data/
│   │   ├── studymind.db             # Persistent SQLite database
│   │   ├── uploads/                 # Uploaded PDF documents
│   │   └── vector_store/            # Persistent vectors.npy & chunks_metadata.json
│   ├── test_auth_and_rag.py         # Comprehensive 10-step verification test suite
│   ├── test_rag.py                  # Standalone RAG pipeline test
│   ├── requirements.txt             # Backend dependencies
│   ├── .env.example                 # Environment template
│   └── .env                         # Local environment configuration
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ProtectedRoute.jsx   # Auth guard component
│   │   │   ├── Sidebar.jsx          # Collapsible navigation sidebar with user avatar & logout
│   │   │   ├── Navbar.jsx           # Top header bar with quick actions & user stats
│   │   │   ├── StatsCard.jsx        # Glassmorphic metrics card
│   │   │   ├── DocumentCard.jsx     # Document library item card
│   │   │   ├── UploadModal.jsx      # Drag & drop multi-file upload modal
│   │   │   └── ChatBubble.jsx       # Markdown chat bubble with citations
│   │   ├── context/
│   │   │   └── AuthContext.jsx      # React Auth Context (login, register, logout, session)
│   │   ├── layouts/
│   │   │   └── AppLayout.jsx        # Main application layout shell
│   │   ├── pages/
│   │   │   ├── Login.jsx            # Split-screen Auth page (Sign In / Register)
│   │   │   ├── Dashboard.jsx        # SaaS metrics & overview page
│   │   │   ├── Documents.jsx        # Document library page
│   │   │   ├── Chat.jsx             # Conversational RAG assistant with thread history drawer
│   │   │   ├── Viewer.jsx           # PDF viewer with chunk inspection
│   │   │   ├── StudyTools.jsx       # Flashcards, MCQs, Summaries & Notes
│   │   │   └── Settings.jsx         # LLM & RAG parameters configuration
│   │   ├── services/
│   │   │   └── api.js               # Axios client with JWT interceptor & auto boundary
│   │   ├── App.jsx                  # React Router routes with ProtectedRoute
│   │   └── main.jsx                 # React root entrypoint
│   ├── package.json                 # Frontend dependencies & scripts
│   └── vite.config.js               # Vite configuration with API proxy
├── run_all.bat                      # One-click startup for both Backend & Frontend
├── run_backend.bat                  # Start Backend server
├── run_frontend.bat                 # Start Frontend Vite server
└── README.md                        # Complete documentation & guide
```

---

## ⚡ Installation & Execution Guide

### Prerequisites
- **Python 3.10+** (tested on 3.11, 3.12, 3.13)
- **Node.js 18+** & **npm**

---

### Quick Start (One-Click on Windows)
Simply double-click:
```bash
run_all.bat
```
This automatically launches both the FastAPI backend (`http://127.0.0.1:8000`) and the React Vite frontend (`http://localhost:5173`) in dedicated terminal windows!

---

### Manual Step-by-Step Startup

#### 1. Backend Setup
1. Open a terminal in `backend/`:
   ```bash
   cd backend
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the FastAPI server:
   ```bash
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   Backend API runs at `http://127.0.0.1:8000`.  
   Interactive API docs are available at `http://127.0.0.1:8000/docs`.

#### 2. Frontend Setup
1. Open a new terminal in `frontend/`:
   ```bash
   cd frontend
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. Open your browser and navigate to:
   ```
   http://localhost:5173
   ```

---

## 🔑 Environment Variables Reference

| Variable | Default Value | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/studymind.db` | Connection string for SQLite or PostgreSQL (`postgresql://user:pass@host:5432/db`) |
| `JWT_SECRET` | `studymind_super_secret_jwt_key_2026` | Cryptographic secret for signing HS256 tokens |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `4320` | JWT token validity lifetime (default: 3 days) |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Comma-separated allowed frontend origins |
| `GEMINI_API_KEY` | *(Optional)* | Google AI Gemini API key (defaults to built-in local RAG engine if omitted) |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Model selection (`gemini-1.5-flash`, `gemini-2.0-flash`, `gemini-1.5-pro`) |
| `CHUNK_SIZE` | `750` | Character count per overlapping chunk |
| `CHUNK_OVERLAP` | `150` | Overlap window size between adjacent chunks |
| `TOP_K` | `4` | Number of semantic chunks retrieved per query |
| `SIMILARITY_THRESHOLD` | `0.15` | Minimum cosine similarity score for relevance filtering |
| `VITE_API_URL` (Frontend) | `/api` | Base API URL (e.g. `https://api.yourdomain.com/api` on GitHub Pages) |

---

## 🚀 Production Deployment Guide

### Option 1: Docker Compose (Full Stack — Recommended)

The simplest, zero-drift production deployment method:

```bash
# 1. Copy production environment file
cp .env.example .env

# 2. Build and start containers
docker compose up -d --build

# 3. Verify health
docker compose ps
curl http://localhost/api/health
```

- **Frontend:** Available at `http://localhost` (Port 80)
- **Backend API:** Available at `http://localhost:8000` (Port 8000)
- **Data Persistence:** Uploaded PDFs and SQLite database persist in `./backend/data` via mounted Docker volumes.

---

### Option 2: GitHub Pages (Frontend) + Render / Railway / Fly.io (Backend)

Because GitHub Pages only serves static assets (HTML/JS/CSS), the FastAPI backend and database must be hosted on an external cloud platform.

#### Step 1: Deploy Backend to Render / Railway
1. Push this repository to GitHub.
2. In [Render Dashboard](https://dashboard.render.com), click **New + > Blueprint** and connect this repository.
   - It will automatically read `render.yaml`, provision the FastAPI web service, mount persistent disk storage (`/app/data`), and generate a secure `JWT_SECRET`.
3. Note your backend URL: `https://studymind-backend.onrender.com`.

#### Step 2: Deploy Frontend to GitHub Pages
1. Go to your GitHub repository **Settings > Secrets and variables > Actions**.
2. Add a repository secret:
   - Name: `VITE_API_URL`
   - Value: `https://studymind-backend.onrender.com/api`
3. Go to **Settings > Pages**:
   - Under **Build and deployment > Source**, choose **GitHub Actions**.
4. Push a commit to `main` (or run the **Deploy Frontend to GitHub Pages** workflow manually).
5. GitHub Actions will build the Vite app with relative assets and SPA 404 redirects, then publish it to `https://<username>.github.io/<repo>/`!

---

## 🧪 Automated Verification Test Suite

Run the included end-to-end verification script to validate database persistence, user registration, authentication, document indexing, user isolation, and RAG retrieval:

```bash
cd backend
python test_auth_and_rag.py
```

### Verification Results (`10/10 Passed`):
```
======================================================================
StudyMind AI - End-to-End Auth, Database & RAG Verification Suite
======================================================================
[1/10] Database initialized: studymind.db
[2/10] User Registration: Alex Johnson (alex@university.edu)
[3/10] User Login & JWT Token verification passed
[4/10] Created test academic PDF: deep_learning_handbook.pdf (1829 bytes)
[5/10] Ingested document: 2 pages, 4 chunks indexed in FAISS
[6/10] Conversational Greeting Test: Friendly guidance response returned
[7/10] Grounded Semantic RAG Test:
       Question: 'What is backpropagation in deep neural networks?'
       Answer generated with 2 verifiable citations (Page 1)
[8/10] Multi-User Isolation Test:
       Second user created: Bob Smith (bob@university.edu)
       User 2 document count: 0 (Isolated successfully!)
       User 2 search on User 1 doc: 0 chunks returned (Vector Isolation verified!)
[9/10] Persistent Chat Threads: Conversation thread & messages verified
[10/10] Study Toolkit: Generated 3 flashcards & 3 MCQs
======================================================================
ALL 10 VERIFICATION TESTS PASSED SUCCESSFULLY!
======================================================================
```

---

## 📡 REST API Reference

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `POST` | `/api/auth/register` | No | Register new user account & return JWT token |
| `POST` | `/api/auth/login` | No | Authenticate user & return JWT token |
| `GET` | `/api/auth/me` | Yes (Bearer) | Get current authenticated user details |
| `GET` | `/api/dashboard/stats` | Yes (Bearer) | Get user-isolated metrics & recent activity |
| `POST` | `/api/documents/upload` | Yes (Bearer) | Upload & ingest single/multiple PDF documents |
| `GET` | `/api/documents` | Yes (Bearer) | Retrieve user's uploaded & indexed documents |
| `GET` | `/api/documents/{id}` | Yes (Bearer) | Get metadata and chunks for user's document |
| `DELETE` | `/api/documents/{id}` | Yes (Bearer) | Delete user document, file & vector embeddings |
| `POST` | `/api/chat` | Yes (Bearer) | Ask study questions with FAISS search & citations |
| `GET` | `/api/chat/history` | Yes (Bearer) | Retrieve list of user's saved conversation threads |
| `GET` | `/api/chat/{id}` | Yes (Bearer) | Retrieve all messages in a conversation thread |
| `DELETE` | `/api/chat/{id}` | Yes (Bearer) | Delete a conversation thread |
| `DELETE` | `/api/chat/history/all` | Yes (Bearer) | Delete all user conversation threads |
| `POST` | `/api/study/summary` | Yes (Bearer) | Generate study summary (brief, detailed, bullets) |
| `POST` | `/api/study/flashcards` | Yes (Bearer) | Generate interactive study flashcards |
| `POST` | `/api/study/quiz` | Yes (Bearer) | Generate practice multiple-choice questions |
| `POST` | `/api/study/explain-simply`| Yes (Bearer)| Explain complex topic in plain English with analogies |
| `POST` | `/api/study/revision-notes`| Yes (Bearer)| Generate high-yield exam revision notes |
| `GET` | `/api/health` | No | System pipeline health and vector database status |
| `GET` | `/api/settings` | No | Get current LLM and RAG parameters |
| `POST` | `/api/settings` | No | Update Gemini API key, model, chunk size, top-k |

---

## 🎓 Academic Demonstration Highlights

1. **Deterministic Grounding:** Strict anti-hallucination system prompt ensures answers are derived exclusively from retrieved context.
2. **Page-Level Transparency:** Every answer displays the source PDF filename, page number, relevance similarity score, and excerpt quotation with direct links into the PDF reader.
3. **Multi-User Academic Vault:** Strict database foreign keys and vector index filtering ensure students cannot access or query each other's documents or chats.
4. **Persistent Vector Storage:** Vector embeddings and document metadata survive server restarts.
5. **Offline/Online Flexibility:** Works out-of-the-box locally, and seamlessly connects to Google Gemini for deep generative reasoning when an API key is provided.

---

## 📄 License
MIT License. Built for academic and educational purposes (College Project CSE 276).
