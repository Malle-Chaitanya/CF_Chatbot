# RAG + Frontend (CloudFuze-style UI)

This repo uses the **exact** frontend from the Slack2teams-2-confident-chatbot project. The RAG backend implements the endpoints the frontend expects.

## Run backend

From repo root (with Weaviate and `.env` configured):

```bash
python scripts/run_api.py
```

API runs at **http://localhost:8000**.

## Run frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:3000** and proxies API calls to the backend via `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000` (see `frontend/.env.local`).

## Sign in with Microsoft

If your `.env` (repo root) has Microsoft OAuth credentials, **Sign in with Microsoft** on the login page works:

- `MICROSOFT_CLIENT_ID` – Azure AD app (client) ID  
- `MICROSOFT_CLIENT_SECRET` – Azure AD client secret  
- `MICROSOFT_TENANT` – tenant ID or domain (e.g. `cloudfuze.com`)  
- Optional: `MICROSOFT_ALLOWED_DOMAIN` – if set, only emails ending with this domain are allowed (e.g. `cloudfuze.com`).

The backend serves `GET /auth/config` (client_id, tenant) and `POST /auth/microsoft/callback` (exchange code for token, get user from Graph, set session cookie).

## Dev login (no Microsoft)

To use the app without Microsoft OAuth:

1. Open **http://localhost:3000/dev-login.html**
2. Click **Sign in (dev)**. This calls the RAG backend `POST /auth/dev-login`, sets the user in localStorage, and redirects to `/chat/new`.
3. Use the chat; messages go to `POST /chat/stream` (RAG: Weaviate retrieval + LLM streaming).

## Backend endpoints used by the frontend

| Endpoint | Purpose |
|----------|---------|
| `POST /chat/stream` | RAG chat (retrieve + LLM, SSE stream) |
| `POST /chat/sessions/save` | Session save (no-op; frontend uses localStorage) |
| `GET /api/suggested-questions/` | Suggested questions for empty state |
| `GET /auth/config` | OAuth config (for login page) |
| `POST /auth/dev-login` | Dev login (sets cookie, returns user) |
| `POST /auth/logout` | Logout |
| `GET /user/profile` | User profile (e.g. needs_onboarding) |
| `GET /chat/sessions/all` | Session list (empty in RAG mode) |
| `GET /chat/history/{user_id}` | History (empty in RAG mode) |

## Customizing the RAG system prompt

Edit `backend/src/api/chat_service.py`: change `RAG_SYSTEM_PROMPT` to your full CloudFuze expert prompt if needed.
