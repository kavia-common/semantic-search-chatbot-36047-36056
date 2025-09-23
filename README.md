# semantic-search-chatbot-36047-36056

Backend Django API (RAG + FAISS)
- Endpoints
  - GET /api/health/ — Health check
  - POST /api/documents/upload/ — multipart form with title, file
  - GET /api/documents/ — list documents
  - GET /api/documents/{id}/ — get document with chunk count
  - POST /api/chat/ — body: { query: string, session_id?: number, top_k?: number }
  - GET /api/chat/sessions/ — list chat sessions
  - GET /api/chat/sessions/{id}/ — session details

Quick start
1) Create virtualenv, install requirements:
   pip install -r backend_django/requirements.txt
2) Create .env from example and set Postgres if needed.
3) Run migrations:
   python backend_django/manage.py migrate
4) Start server:
   python backend_django/manage.py runserver 0.0.0.0:8000
5) Open API docs at /docs

Notes
- FAISS index stored at FAISS_INDEX_PATH. Use management command to rebuild:
  python backend_django/manage.py rebuild_faiss
- Embeddings via sentence-transformers/all-MiniLM-L6-v2.
- This backend is prepared to be used by a React frontend.