# .env Configuration Examples

## Example 1: Using Gemini 2.5 Flash Lite (Recommended ⭐)

```env
# ============================================================================
# LLM PROVIDER CONFIGURATION
# ============================================================================
LLM_PROVIDER=gemini

# Google Gemini API Key (Free tier available!)
GEMINI_API_KEY=AIzaSyBXxxx_your_actual_key_here_xxx

# ============================================================================
# MICROSOFT OAUTH CONFIGURATION
# ============================================================================
MICROSOFT_CLIENT_ID=your-client-id-here
MICROSOFT_CLIENT_SECRET=your-client-secret-here
MICROSOFT_TENANT=cloudfuze.com

# ============================================================================
# LANGFUSE CONFIGURATION (Observability)
# ============================================================================
LANGFUSE_PUBLIC_KEY=your-langfuse-public-key
LANGFUSE_SECRET_KEY=your-langfuse-secret-key
LANGFUSE_HOST=https://cloud.langfuse.com

# ============================================================================
# MONGODB CONFIGURATION
# ============================================================================
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=slack2teams
MONGODB_CHAT_COLLECTION=chat_histories

# ============================================================================
# DATA SOURCE CONFIGURATION
# ============================================================================
INITIALIZE_VECTORSTORE=false
ENABLE_WEB_SOURCE=false
ENABLE_PDF_SOURCE=false
ENABLE_EXCEL_SOURCE=false
ENABLE_DOC_SOURCE=false
ENABLE_SHAREPOINT_SOURCE=false
ENABLE_OUTLOOK_SOURCE=false

# ============================================================================
# OTHER CONFIGURATION
# ============================================================================
JSON_MEMORY_FILE=data/chat_history.json
NEXT_PUBLIC_API_URL=http://127.0.0.1:8002
```

**Cost**: ~$0.10 per 10,000 messages (or FREE on free tier!)  
**Quality**: ⭐⭐⭐⭐⭐ Excellent  
**Speed**: ⚡⚡⚡ Very Fast

---

## Example 2: Using OpenAI GPT-4o Mini (Original)

```env
# ============================================================================
# LLM PROVIDER CONFIGURATION
# ============================================================================
LLM_PROVIDER=openai

# OpenAI API Key (starts with "sk-")
OPENAI_API_KEY=sk-proj-xxx_your_actual_key_here_xxx

# ============================================================================
# MICROSOFT OAUTH CONFIGURATION
# ============================================================================
MICROSOFT_CLIENT_ID=your-client-id-here
MICROSOFT_CLIENT_SECRET=your-client-secret-here
MICROSOFT_TENANT=cloudfuze.com

# ============================================================================
# LANGFUSE CONFIGURATION (Observability)
# ============================================================================
LANGFUSE_PUBLIC_KEY=your-langfuse-public-key
LANGFUSE_SECRET_KEY=your-langfuse-secret-key
LANGFUSE_HOST=https://cloud.langfuse.com

# ============================================================================
# MONGODB CONFIGURATION
# ============================================================================
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=slack2teams
MONGODB_CHAT_COLLECTION=chat_histories

# ============================================================================
# DATA SOURCE CONFIGURATION
# ============================================================================
INITIALIZE_VECTORSTORE=false
ENABLE_WEB_SOURCE=false
ENABLE_PDF_SOURCE=false
ENABLE_EXCEL_SOURCE=false
ENABLE_DOC_SOURCE=false
ENABLE_SHAREPOINT_SOURCE=false
ENABLE_OUTLOOK_SOURCE=false

# ============================================================================
# OTHER CONFIGURATION
# ============================================================================
JSON_MEMORY_FILE=data/chat_history.json
NEXT_PUBLIC_API_URL=http://127.0.0.1:8002
```

**Cost**: ~$2.10 per 10,000 messages  
**Quality**: ⭐⭐⭐⭐⭐ Excellent  
**Speed**: ⚡⚡⚡ Very Fast

---

## Example 3: Full Production Configuration (with all sources enabled)

```env
# ============================================================================
# LLM PROVIDER CONFIGURATION
# ============================================================================
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSyBXxxx_your_key_xxx

# ============================================================================
# MICROSOFT OAUTH CONFIGURATION
# ============================================================================
MICROSOFT_CLIENT_ID=your-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
MICROSOFT_TENANT=cloudfuze.com

# ============================================================================
# LANGFUSE CONFIGURATION (Observability)
# ============================================================================
LANGFUSE_PUBLIC_KEY=your-langfuse-public-key
LANGFUSE_SECRET_KEY=your-langfuse-secret-key
LANGFUSE_HOST=https://cloud.langfuse.com

# ============================================================================
# MONGODB CONFIGURATION
# ============================================================================
MONGODB_URL=mongodb://your-production-mongodb-url
MONGODB_DATABASE=slack2teams
MONGODB_CHAT_COLLECTION=chat_histories

# ============================================================================
# DATA SOURCE CONFIGURATION - ALL ENABLED
# ============================================================================
INITIALIZE_VECTORSTORE=true

# Web Sources
ENABLE_WEB_SOURCE=true
WEB_SOURCE_URL=https://cloudfuze.com/wp-json/wp/v2/posts?per_page=100

# PDF Sources
ENABLE_PDF_SOURCE=true
PDF_SOURCE_DIR=./pdfs

# Excel Sources
ENABLE_EXCEL_SOURCE=true
EXCEL_SOURCE_DIR=./excel

# Doc Sources
ENABLE_DOC_SOURCE=true
DOC_SOURCE_DIR=./docs

# SharePoint Configuration
ENABLE_SHAREPOINT_SOURCE=true
SHAREPOINT_SITE_URL=https://cloudfuzecom.sharepoint.com/sites/DOC360
SHAREPOINT_START_PAGE=
SHAREPOINT_MAX_DEPTH=999
SHAREPOINT_EXCLUDE_FILES=true

# Outlook Email Configuration
ENABLE_OUTLOOK_SOURCE=true
OUTLOOK_USER_EMAIL=your-email@cloudfuze.com
OUTLOOK_FOLDER_NAME=Inbox
OUTLOOK_MAX_EMAILS=500
OUTLOOK_DATE_FILTER=last_3_months

# ============================================================================
# CHUNKING & PROCESSING CONFIGURATION
# ============================================================================
CHUNK_TARGET_TOKENS=800
CHUNK_OVERLAP_TOKENS=200
CHUNK_MIN_TOKENS=150
ENABLE_DEDUPLICATION=true
DEDUP_THRESHOLD=0.85
ENABLE_UNSTRUCTURED=true
ENABLE_OCR=true
OCR_LANGUAGE=eng
GRAPH_DB_PATH=./data/graph_relations.db
ENABLE_GRAPH_STORAGE=true

# ============================================================================
# RETRIEVAL CONFIGURATION (Option E - Perplexity-style)
# ============================================================================
ENABLE_INTENT_CLASSIFICATION=true
ENABLE_QUERY_EXPANSION=true
ENABLE_CONTEXT_COMPRESSION=true

# Retrieval parameters
DENSE_RETRIEVAL_K=40
BM25_RETRIEVAL_K=40
FINAL_RETRIEVAL_K=8

# Hybrid scoring weights
DENSE_WEIGHT=0.5
BM25_WEIGHT=0.3
RERANKER_WEIGHT=0.8

# ============================================================================
# OTHER CONFIGURATION
# ============================================================================
JSON_MEMORY_FILE=data/chat_history.json
NEXT_PUBLIC_API_URL=https://ai.cloudfuze.com
BLOG_START_PAGE=1
```

---

## Example 4: Development Configuration (with local services)

```env
# ============================================================================
# LLM PROVIDER CONFIGURATION
# ============================================================================
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSyBXxxx_your_dev_key_xxx

# ============================================================================
# MICROSOFT OAUTH CONFIGURATION
# ============================================================================
MICROSOFT_CLIENT_ID=dev-client-id
MICROSOFT_CLIENT_SECRET=dev-client-secret
MICROSOFT_TENANT=cloudfuze.com

# ============================================================================
# LANGFUSE CONFIGURATION - Using Local Langfuse
# ============================================================================
LANGFUSE_PUBLIC_KEY=dev-public-key
LANGFUSE_SECRET_KEY=dev-secret-key
LANGFUSE_HOST=http://localhost:3000

# ============================================================================
# MONGODB CONFIGURATION - Local MongoDB
# ============================================================================
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=slack2teams_dev
MONGODB_CHAT_COLLECTION=chat_histories

# ============================================================================
# DATA SOURCE CONFIGURATION - Minimal for dev
# ============================================================================
INITIALIZE_VECTORSTORE=false
ENABLE_WEB_SOURCE=false
ENABLE_PDF_SOURCE=true
ENABLE_EXCEL_SOURCE=false
ENABLE_DOC_SOURCE=true
ENABLE_SHAREPOINT_SOURCE=true
ENABLE_OUTLOOK_SOURCE=false

PDF_SOURCE_DIR=./pdfs
DOC_SOURCE_DIR=./docs

SHAREPOINT_SITE_URL=https://cloudfuzecom.sharepoint.com/sites/DOC360
SHAREPOINT_MAX_DEPTH=999

# ============================================================================
# RETRIEVAL CONFIGURATION - Dev settings
# ============================================================================
ENABLE_INTENT_CLASSIFICATION=false
ENABLE_QUERY_EXPANSION=true
ENABLE_CONTEXT_COMPRESSION=true

DENSE_RETRIEVAL_K=40
BM25_RETRIEVAL_K=40
FINAL_RETRIEVAL_K=8

# ============================================================================
# OTHER CONFIGURATION
# ============================================================================
JSON_MEMORY_FILE=data/chat_history_dev.json
NEXT_PUBLIC_API_URL=http://127.0.0.1:8002
```

---

## Minimal Configuration (Bare Minimum)

This is the smallest valid `.env` file:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSyBXxxx_your_key_xxx
MICROSOFT_CLIENT_ID=your-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
LANGFUSE_PUBLIC_KEY=your-public-key
LANGFUSE_SECRET_KEY=your-secret-key
```

Everything else has sensible defaults!

---

## How to Get Each Key

### Gemini API Key
1. Visit: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Select your Google Cloud project (or create new)
4. Copy the generated key
5. Format: `AIzaSy...` (no quotes needed)

### OpenAI API Key
1. Visit: https://platform.openai.com/api-keys
2. Login or create account
3. Click "Create new secret key"
4. Copy the key (save it securely, can't view again)
5. Format: `sk-proj-...` (no quotes needed)

### Microsoft OAuth
1. Go to Azure portal: https://portal.azure.com
2. Register an app in Azure AD
3. Create a client secret
4. Copy Client ID and Secret

### Langfuse Keys
1. Visit: https://cloud.langfuse.com
2. Create account or login
3. Go to API keys section
4. Copy public and secret keys

---

## Key Points

✅ **No Quotes Needed** - Don't use quotes around API keys  
✅ **Case Sensitive** - `LLM_PROVIDER=gemini` is different from `LLM_PROVIDER=Gemini`  
✅ **Whitespace** - Avoid spaces around the `=` sign  
✅ **Security** - Never commit `.env` to version control  
✅ **Restart Required** - Changes take effect after restart  

---

## Switching Between Providers

### From Gemini to OpenAI

**Before**:
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSyBXxxx...
```

**After**:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-xxx...
```

**Then**: Restart your application

### From OpenAI to Gemini

**Before**:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-xxx...
```

**After**:
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSyBXxxx...
```

**Then**: Restart your application

---

## Validation

Before running your application, validate:

```bash
# Check LLM_PROVIDER is set
grep "LLM_PROVIDER" .env

# Check API key is set
grep "GEMINI_API_KEY\|OPENAI_API_KEY" .env

# Check key format
grep "^GEMINI_API_KEY=AIzaSy" .env
grep "^OPENAI_API_KEY=sk-" .env
```

---

## Common Mistakes

❌ **Quotes around values**:
```env
LLM_PROVIDER="gemini"  # ❌ Wrong
LLM_PROVIDER=gemini    # ✅ Correct
```

❌ **Spaces around equals**:
```env
LLM_PROVIDER = gemini  # ❌ Wrong (space = value includes space)
LLM_PROVIDER=gemini    # ✅ Correct
```

❌ **Wrong case**:
```env
llm_provider=gemini    # ❌ Wrong (env vars are case-sensitive)
LLM_PROVIDER=gemini    # ✅ Correct
```

❌ **Typos in values**:
```env
LLM_PROVIDER=geminni   # ❌ Wrong (typo)
LLM_PROVIDER=gemini    # ✅ Correct
```

---

## Testing Configuration

### Method 1: Check logs
Start your app and look for:
```
LLM_PROVIDER: gemini
Using Gemini API...
```

### Method 2: Python check
```python
from config import LLM_PROVIDER, GEMINI_API_KEY
print(f"Provider: {LLM_PROVIDER}")
print(f"Has key: {bool(GEMINI_API_KEY)}")
```

### Method 3: API call test
```python
from app.llm_factory import get_llm_provider_info
print(get_llm_provider_info())
# Output: {'provider': 'gemini', 'model': 'gemini-2.5-flash-lite', ...}
```

---

## Environment File Location

Save your `.env` file in the **project root**:

```
chatbot/
├── .env              ← Put it here!
├── config.py
├── app/
├── requirements.txt
└── ...
```

**NOT** in subdirectories like `app/.env` or `backend/.env`

---

## Troubleshooting

### "GEMINI_API_KEY required"
**Cause**: Variable not in `.env` or has wrong name  
**Fix**: Add `GEMINI_API_KEY=your-key` to `.env`

### "LLM_PROVIDER must be either 'openai' or 'gemini'"
**Cause**: Typo in provider name  
**Fix**: Check spelling - must be exactly `openai` or `gemini`

### "Invalid API key"
**Cause**: Wrong key or revoked  
**Fix**: Get new key from provider website

### Key not being read
**Cause**: Application not restarted  
**Fix**: Restart your application after changing `.env`

---

## Summary Table

| Setting | Gemini Value | OpenAI Value |
|---------|--------------|--------------|
| `LLM_PROVIDER` | `gemini` | `openai` |
| API Key Var | `GEMINI_API_KEY` | `OPENAI_API_KEY` |
| Key Prefix | `AIzaSy...` | `sk-proj-...` |
| Model Used | `gemini-2.5-flash-lite` | `gpt-4o-mini` |
| Cost/10K msg | ~$0.10 | ~$2.10 |

---

## Quick Decision Guide

**Choose Gemini if**:
- 💰 Cost is a concern
- 📊 Handling large volumes
- ⚡ Need fast responses
- 🆓 Want to use free tier

**Choose OpenAI if**:
- 🔒 Maximum quality assurance
- 🏢 Enterprise deployment
- 💼 Budget not a concern
- 📈 Scaling to millions of requests

---

## Next Steps

1. Copy one of the example configurations above
2. Fill in your actual API keys
3. Save as `.env` in project root
4. Restart your application
5. Test with a chat message
6. Done! ✅

---

**Happy configuring!** 🎉

