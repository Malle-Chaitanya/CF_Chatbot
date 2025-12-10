# 🚀 Quick Setup Guide - Gemini Model Integration

## What's New?

Your chatbot now supports **Google Gemini 2.5 Flash Lite** alongside the original ChatGPT model! Switch between them with a single toggle.

---

## ⚡ Quick Start (2 Steps)

### Step 1: Get Your Gemini API Key
1. Go to: **https://aistudio.google.com/app/apikey**
2. Click **"Create API Key"**
3. Select/create a project
4. Copy your key

### Step 2: Update `.env` File
Add these two lines to your `.env` file:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-api-key-here
```

**That's it!** 🎉 Restart your application and you're using Gemini!

---

## 🔄 Switching Back to ChatGPT

Simply change your `.env`:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
```

---

## 📊 Comparison

| Feature | ChatGPT (gpt-4o-mini) | Gemini (2.5-flash-lite) |
|---------|----------------------|------------------------|
| **Cost** | $0.15/1M input | Free tier available |
| **Speed** | Very Fast | Very Fast |
| **Quality** | Excellent | Excellent |
| **Token Limit** | 128K | 1M |
| **Recommended** | Production | Cost-conscious / High-volume |

---

## 📝 What Changed?

**Files Modified** (all upgrades, no breaking changes):
- ✅ `config.py` - Added LLM provider configuration
- ✅ `app/llm_factory.py` - New LLM factory pattern
- ✅ `app/llm.py` - Uses factory function
- ✅ `app/endpoints.py` - Uses factory function (6 locations)
- ✅ `query_expander.py` - Uses factory function
- ✅ `context_compressor.py` - Uses factory function

**No breaking changes!** Existing code works as-is.

---

## 🔑 Environment Variables

### Required for Gemini:
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-key-here
```

### OR Required for OpenAI:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
```

### Optional (keeps existing defaults):
```env
# Everything else stays the same
MONGODB_URL=...
LANGFUSE_PUBLIC_KEY=...
# etc.
```

---

## 🧪 Test Your Setup

```bash
# Verify config is loaded
python -c "from config import LLM_PROVIDER; print(f'Using: {LLM_PROVIDER}')"

# Test LLM factory
python -c "from app.llm_factory import get_llm_provider_info; print(get_llm_provider_info())"
```

---

## 🛠️ Technical Details

### How It Works
```
Your App
    ↓
get_llm() factory function
    ↓
    ├─ OpenAI: Creates ChatOpenAI instance
    └─ Gemini: Creates ChatGoogleGenerativeAI instance
```

All chat operations automatically use the configured provider!

### Supported Parameters
The `get_llm()` function accepts:
- `model_name` - Override model (optional)
- `temperature` - 0 (deterministic) to 1 (creative)
- `streaming` - Enable streaming responses
- `max_tokens` - Maximum response length

---

## ✅ Verification Checklist

- [ ] Got your Gemini API key
- [ ] Added `LLM_PROVIDER=gemini` to `.env`
- [ ] Added `GEMINI_API_KEY=xxx` to `.env`
- [ ] Restarted your application
- [ ] Sent a test chat message
- [ ] Response received successfully ✨

---

## 🆘 Troubleshooting

### "GEMINI_API_KEY required"
→ Make sure `GEMINI_API_KEY` is set in `.env`

### "Invalid API key"
→ Your key might be wrong or revoked. Get a new one from: https://aistudio.google.com/app/apikey

### "ModuleNotFoundError: langchain_google_genai"
→ Install the dependency:
```bash
pip install langchain-google-genai
```

### Not using Gemini?
→ Check `LLM_PROVIDER` is exactly `"gemini"` (lowercase)

---

## 📚 Full Documentation

For detailed information, see:
- **LLM_PROVIDER_SWITCH.md** - Technical details
- **ENV_SETUP.md** - Complete environment setup guide

---

## 🎯 Next Steps

1. ✅ Get Gemini API key
2. ✅ Update `.env`
3. ✅ Restart app
4. ✅ Test with a chat message
5. ✅ Done!

**You're all set! Enjoy your new Gemini-powered chatbot!** 🚀

---

**Questions?** Check the documentation files or the implementation in `app/llm_factory.py`.

