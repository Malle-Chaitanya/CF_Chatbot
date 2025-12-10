# Environment Configuration Guide

This document explains how to configure the LLM provider for your chatbot.

## Quick Start

The chatbot now supports **two LLM providers**:

1. **OpenAI** (ChatGPT - gpt-4o-mini) - Original provider
2. **Google Gemini** (gemini-2.5-flash-lite) - New provider

### Switching Between Providers

Add this to your `.env` file:

```env
# Choose between "openai" or "gemini"
LLM_PROVIDER=gemini
```

---

## Configuration by Provider

### Option 1: Using OpenAI (ChatGPT)

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-api-key
```

Get your OpenAI API key from: https://platform.openai.com/api-keys

---

### Option 2: Using Google Gemini (Recommended for Cost)

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-google-ai-studio-api-key
```

Get your Gemini API key from: https://aistudio.google.com/app/apikey

---

## Complete .env Configuration

Here's a complete example of your `.env` file:

```env
# ============================================================================
# LLM PROVIDER (Required) - Choose: "openai" or "gemini"
# ============================================================================
LLM_PROVIDER=gemini

# ============================================================================
# OPENAI API KEY (Required if LLM_PROVIDER=openai)
# ============================================================================
OPENAI_API_KEY=sk-your-key-here

# ============================================================================
# GOOGLE GEMINI API KEY (Required if LLM_PROVIDER=gemini)
# ============================================================================
GEMINI_API_KEY=your-gemini-key-here

# ============================================================================
# MICROSOFT OAUTH CONFIGURATION (Required)
# ============================================================================
MICROSOFT_CLIENT_ID=your-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
MICROSOFT_TENANT=cloudfuze.com

# ============================================================================
# LANGFUSE CONFIGURATION (Required for Observability)
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
# REST OF YOUR CONFIGURATION...
# ============================================================================
# ... (other environment variables)
```

---

## How It Works

The chatbot uses a **factory pattern** to automatically select the right LLM based on the `LLM_PROVIDER` setting:

### Architecture

```
┌─────────────────────────────────────────────────┐
│         config.py (Configuration)               │
│  - LLM_PROVIDER toggle (openai/gemini)         │
│  - API keys loading                             │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│    app/llm_factory.py (LLM Factory)            │
│  - get_llm() function                           │
│  - Returns ChatOpenAI or ChatGoogleGenerativeAI │
└────────────────┬────────────────────────────────┘
                 │
        ┌────────┴──────────┐
        ▼                   ▼
   ┌─────────────┐    ┌───────────────┐
   │ ChatOpenAI  │    │ ChatGemini    │
   │ (gpt-4o-   │    │ (gemini-2.5-  │
   │  mini)      │    │  flash-lite)  │
   └─────────────┘    └───────────────┘
```

### Where LLM is Used

All these components use the factory function and respect your `LLM_PROVIDER` setting:

- ✅ `app/endpoints.py` - Chat endpoint, streaming responses, conversational queries
- ✅ `app/llm.py` - Q&A chain setup, recommended questions generation
- ✅ `query_expander.py` - Query expansion for better retrieval
- ✅ `context_compressor.py` - Context compression and summarization

---

## Model Details

### OpenAI (gpt-4o-mini)
- **Model**: `gpt-4o-mini`
- **Cost**: ~0.15/1M input tokens, 0.60/1M output tokens
- **Speed**: Very fast
- **Quality**: Excellent
- **Get Key**: https://platform.openai.com/api-keys

### Google Gemini (gemini-2.5-flash-lite)
- **Model**: `gemini-2.5-flash-lite`
- **Cost**: Free tier available, very affordable at scale
- **Speed**: Very fast
- **Quality**: Excellent
- **Get Key**: https://aistudio.google.com/app/apikey

---

## Troubleshooting

### Error: "OPENAI_API_KEY environment variable is required"
- You're using `LLM_PROVIDER=openai` but haven't set `OPENAI_API_KEY`
- Set `OPENAI_API_KEY` in your `.env` file

### Error: "GEMINI_API_KEY environment variable is required"
- You're using `LLM_PROVIDER=gemini` but haven't set `GEMINI_API_KEY`
- Set `GEMINI_API_KEY` in your `.env` file

### Error: "LLM_PROVIDER must be either 'openai' or 'gemini'"
- You set `LLM_PROVIDER` to an invalid value
- Must be exactly `"openai"` or `"gemini"` (case-insensitive)

### Error: "Unknown LLM provider"
- Something went wrong with the configuration
- Check that your `LLM_PROVIDER` is valid

---

## Switching Providers at Runtime

To switch between providers, simply:

1. Update the `LLM_PROVIDER` value in your `.env` file
2. Set the corresponding API key (`OPENAI_API_KEY` or `GEMINI_API_KEY`)
3. Restart your application

The change will be applied immediately to all new chat requests.

---

## Performance Comparison

| Aspect | OpenAI (gpt-4o-mini) | Gemini (2.5-flash-lite) |
|--------|---------------------|------------------------|
| Speed | ⚡⚡⚡ | ⚡⚡⚡ |
| Quality | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Cost | 💰💰 | 💰 |
| Latency | Low | Low |
| Token Limits | 128K | 1M |

---

## Examples

### Example 1: Using Gemini (Current Setup)
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSyBXxxx...your-key-here
```

### Example 2: Using OpenAI
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-xxx...your-key-here
```

### Example 3: Switching from OpenAI to Gemini
Just change the .env file:
```diff
- LLM_PROVIDER=openai
+ LLM_PROVIDER=gemini

- OPENAI_API_KEY=sk-...
+ GEMINI_API_KEY=AIzaSy...
```

---

## Next Steps

1. Get your API key (OpenAI or Gemini)
2. Set `LLM_PROVIDER` in your `.env`
3. Set the corresponding API key
4. Restart your application
5. Test by sending a message in the chat!

---

Need help? Check the configuration files:
- `config.py` - Main configuration loader
- `app/llm_factory.py` - LLM factory implementation
- `app/endpoints.py` - Chat endpoints
- `app/llm.py` - LLM chain setup

