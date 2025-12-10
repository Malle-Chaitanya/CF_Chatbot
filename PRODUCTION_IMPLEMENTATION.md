# Production Implementation - Quick Reference

## Changes Required for Production Deployment

### 1. Environment Variables

Create `.env.production` in the project root:

```env
# Frontend
NEXT_PUBLIC_API_BASE_URL=https://api.cloudfuze.com
NEXT_PUBLIC_APP_URL=https://app.cloudfuze.com

# Backend
MONGODB_URI=mongodb+srv://username:password@cluster0.mongodb.net/chatdb
API_PORT=8000
ENVIRONMENT=production
```

### 2. Update getApiBase() Function

**File**: `frontend/src/lib/chat-initialization.ts`

Find and update the `getApiBase()` function:

```typescript
function getApiBase(): string {
  if (typeof window === 'undefined') return '';
  
  // Use environment variable if available, otherwise use origin
  if (process.env.NEXT_PUBLIC_API_BASE_URL) {
    return process.env.NEXT_PUBLIC_API_BASE_URL;
  }
  
  // Fallback for development or same-domain setup
  return window.location.origin;
}
```

### 3. CORS Configuration

**File**: `server.py`

Update the CORS middleware:

```python
from fastapi.middleware.cors import CORSMiddleware
import os

# Get allowed origins from environment
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**.env file**:
```env
ALLOWED_ORIGINS=https://app.cloudfuze.com,https://www.cloudfuze.com
```

### 4. Share URL Generation

**No code changes needed!** The share URL generation automatically uses the correct domain:

```typescript
// This automatically becomes https://app.cloudfuze.com/chat/shared/... in production
const shareUrl = `${window.location.origin}/chat/shared/${share_token}`;
```

### 5. MongoDB Atlas Configuration

**In backend environment**:

```bash
export MONGODB_URI="mongodb+srv://username:password@cluster0.mongodb.net/chatdb?retryWrites=true&w=majority"
```

**In code** - `app/mongodb_memory.py`:

```python
import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGODB_URI)
database = client.chatdb
```

### 6. Rate Limiting (Optional but Recommended)

**File**: `server.py`

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

**File**: `app/endpoints.py`

```python
from fastapi import request
from app.main import app

@router.post("/chat/share/{session_id}")
@app.state.limiter.limit("10/minute")
async def share_chat_session(
    request: Request,
    session_id: str,
    auth_user: dict = Depends(require_auth)
):
    # ... existing code ...
```

### 7. Security Headers

**File**: `server.py`

```python
from fastapi.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

### 8. Logging Configuration

**File**: `server.py`

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            'app.log',
            maxBytes=10485760,  # 10MB
            backupCount=5
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

### 9. Docker Setup (if using containers)

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URI=mongodb://mongo:27017/chatdb
      - ALLOWED_ORIGINS=https://app.cloudfuze.com
      - ENVIRONMENT=production
    depends_on:
      - mongo
  
  mongo:
    image: mongo:6
    volumes:
      - mongo_data:/data/db
    environment:
      - MONGO_INITDB_DATABASE=chatdb

volumes:
  mongo_data:
```

### 10. Deployment Commands

#### Using Vercel (Frontend)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod

# Set environment variables in Vercel dashboard
# NEXT_PUBLIC_API_BASE_URL: https://api.cloudfuze.com
# NEXT_PUBLIC_APP_URL: https://app.cloudfuze.com
```

#### Using AWS (Backend)

```bash
# Build Docker image
docker build -t chatbot-api:latest .

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

docker tag chatbot-api:latest <account>.dkr.ecr.us-east-1.amazonaws.com/chatbot-api:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/chatbot-api:latest

# Deploy to ECS
aws ecs update-service --cluster chatbot-cluster --service chatbot-api --force-new-deployment
```

---

## Testing Production Setup Locally

Before deploying, test production configuration locally:

```bash
# Set environment variables
export NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
export ALLOWED_ORIGINS=http://localhost:3000

# Start backend
python server.py

# In another terminal, start frontend
cd frontend
npm run dev
```

---

## Verifying Share Functionality in Production

1. **Generate a share link**:
   ```
   https://app.cloudfuze.com → Click Share button
   ```

2. **Copy link**:
   ```
   Link should be copied: https://app.cloudfuze.com/chat/shared/{token}
   ```

3. **Test link from different browser/incognito**:
   ```
   Open https://app.cloudfuze.com/chat/shared/{token}
   Should prompt for login
   Should show chat in read-only mode
   ```

4. **Test "Continue Thread"**:
   ```
   Click "Continue in this thread"
   Should create copy in your chats
   Should be editable
   ```

---

## Monitoring Production

### Key Metrics to Check

1. **Share endpoint response time**: Target < 2 seconds
2. **Share link success rate**: Target > 99%
3. **Authentication failures**: Should be near 0 after users log in
4. **Database connection errors**: Should be 0

### Logs to Monitor

```bash
# Watch API logs
tail -f app.log | grep SHARE

# Watch error logs
tail -f app.log | grep ERROR

# Monitor database
mongostat
```

---

## Troubleshooting Checklist

| Issue | Solution |
|-------|----------|
| Share link returns 404 | Check MongoDB connection, verify token in DB |
| "Authentication required" on share | Verify Bearer token validity |
| CORS error | Check ALLOWED_ORIGINS environment variable |
| Clipboard not working | Check browser console, fallback should show toast |
| Chat not loading on share link | Verify API URL is correct, check backend logs |
| Slow share creation | Check database indexes, consider caching |

---

## Summary

**Minimal changes required for production:**
1. Update `getApiBase()` function
2. Set 3 environment variables
3. Configure CORS
4. Set up HTTPS
5. Configure MongoDB Atlas

**Everything else works as-is!** The implementation is production-ready.

