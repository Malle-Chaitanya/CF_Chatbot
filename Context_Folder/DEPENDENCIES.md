# Context Folder Dependencies

This document outlines all dependencies required for context-related functionality in the CloudFuze Chatbot application.

## Overview

The `Context_Folder` and context-related functionality handle document processing, context compression, and retrieval operations. This includes the `context_compressor.py` module and related context processing components.

---

## Python Dependencies

### Core Framework Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | >=0.119.1 | Web framework for API endpoints |
| `uvicorn` | >=0.30.0 | ASGI server for FastAPI |
| `python-multipart` | ==0.0.6 | Form data handling |
| `python-dotenv` | ==1.0.0 | Environment variable management |

### AI and Language Processing

| Package | Version | Purpose |
|---------|---------|---------|
| `langchain` | ==1.0.1 | Core LangChain framework |
| `langchain-openai` | ==1.0.1 | OpenAI integration for LangChain |
| `langchain-google-genai` | >=0.1.0 | Google Gemini support |
| `langchain-community` | ==0.4 | Community integrations |
| `langchain-core` | ==1.0.0 | Core LangChain components |
| `langchain-chroma` | ==1.0.0 | ChromaDB integration |
| `openai` | >=1.109.1 | OpenAI API client |
| `google-generativeai` | >=0.3.0 | Google Generative AI API |
| `langfuse` | ==2.51.2 | LLM observability and tracing |

### Transformers and Machine Learning

| Package | Version | Purpose |
|---------|---------|---------|
| `transformers` | >=4.41.0,<5.0.0 | HuggingFace transformers library |
| `huggingface-hub` | >=0.34.0,<1.0 | HuggingFace model hub access |
| `sentence-transformers` | >=2.7.0 | Sentence embeddings for retrieval |
| `scikit-learn` | >=1.4.0 | Machine learning utilities |
| `tiktoken` | >=0.7.0,<1.0.0 | Token counting for LLMs |

### Vector Database and Search

| Package | Version | Purpose |
|---------|---------|---------|
| `chromadb` | >=1.0.20 | Vector database for embeddings |
| `rank-bm25` | ==0.2.2 | BM25 sparse retrieval algorithm |

### Document Processing

| Package | Version | Purpose |
|---------|---------|---------|
| `PyPDF2` | ==3.0.1 | PDF parsing |
| `pdfplumber` | ==0.10.3 | Advanced PDF processing |
| `pymupdf4llm` | ==0.0.5 | PDF to LLM-friendly format |
| `python-docx` | ==1.1.0 | Word document processing |
| `docx2txt` | ==0.8 | Word document text extraction |
| `openpyxl` | ==3.1.2 | Excel file processing |
| `xlrd` | ==2.0.1 | Excel file reading |
| `unstructured[all-docs]` | ==0.11.8 | Advanced document parsing (HEAVY) |
| `markdown` | ==3.5.1 | Markdown processing |

### Database

| Package | Version | Purpose |
|---------|---------|---------|
| `motor` | ==3.3.2 | Async MongoDB driver |
| `pymongo` | ==4.5.0 | MongoDB Python driver |

### HTTP and Web Scraping

| Package | Version | Purpose |
|---------|---------|---------|
| `requests` | >=2.32.5 | HTTP library |
| `httpx` | >=0.27.0 | Async HTTP client |
| `beautifulsoup4` | ==4.12.2 | HTML parsing |

### Data Processing

| Package | Version | Purpose |
|---------|---------|---------|
| `pydantic` | >=2.7.4 | Data validation |
| `pandas` | ==2.3.3 | Data manipulation |

### Browser Automation (Optional)

| Package | Version | Purpose |
|---------|---------|---------|
| `selenium` | ==4.36.0 | Browser automation for SharePoint |
| `webdriver-manager` | ==4.0.2 | WebDriver management |

---

## Context-Specific Dependencies

### Context Compressor Module (`context_compressor.py`)

The context compressor uses the following dependencies:

- **langchain_core.documents**: For Document objects
- **app.llm_factory**: For LLM instance creation
- **LLM Provider**: Either OpenAI or Google Gemini (via langchain)

### Key Dependencies for Context Processing

1. **LLM Provider** (Required):
   - OpenAI API key (via `OPENAI_API_KEY` environment variable)
   - OR Google Gemini API key (via `GOOGLE_API_KEY` environment variable)

2. **Vector Database** (Required):
   - ChromaDB for storing and retrieving document embeddings

3. **Retrieval Components** (Required):
   - BM25 retriever for sparse retrieval
   - Sentence transformers for dense retrieval
   - Cross-encoder reranker for result ranking

---

## Frontend Dependencies

### Core Framework

| Package | Version | Purpose |
|---------|---------|---------|
| `next` | 16.0.3 | React framework |
| `react` | 19.2.0 | React library |
| `react-dom` | 19.2.0 | React DOM rendering |
| `typescript` | ^5 | TypeScript support |

### UI Components

| Package | Version | Purpose |
|---------|---------|---------|
| `@radix-ui/react-slot` | ^1.1.1 | UI component primitives |
| `class-variance-authority` | ^0.7.1 | Component variant management |
| `clsx` | ^2.1.1 | Conditional class names |
| `tailwind-merge` | ^2.5.5 | Tailwind CSS class merging |
| `tailwindcss` | ^4 | CSS framework |

### Data Visualization

| Package | Version | Purpose |
|---------|---------|---------|
| `recharts` | ^2.10.3 | Chart library for dashboard |

### Utilities

| Package | Version | Purpose |
|---------|---------|---------|
| `axios` | ^1.7.9 | HTTP client |
| `marked` | ^17.0.0 | Markdown rendering |
| `framer-motion` | ^11.11.17 | Animation library |

### Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `eslint` | ^9 | Code linting |
| `eslint-config-next` | 16.0.3 | Next.js ESLint config |
| `@tailwindcss/postcss` | ^4 | PostCSS plugin for Tailwind |

---

## Installation

### Backend Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# For production (lightweight, without sentence-transformers)
pip install -r requirements.prod.light.txt

# For production (with reranking support)
pip install -r requirements.prod.txt
```

### Frontend Dependencies

```bash
cd frontend
npm install
```

---

## Critical Version Constraints

### Transformers Compatibility

⚠️ **IMPORTANT**: The following versions must be compatible:

- `transformers>=4.41.0,<5.0.0`
- `huggingface-hub>=0.34.0,<1.0`
- `sentence-transformers>=2.7.0`

These versions are verified to work together. Upgrading beyond these ranges may cause compatibility issues.

### LangChain Compatibility

All LangChain packages should be version 1.0.x for compatibility:

- `langchain==1.0.1`
- `langchain-core==1.0.0`
- `langchain-community==0.4`
- `langchain-chroma==1.0.0`

---

## Environment Variables Required

### LLM Provider Configuration

```bash
# OpenAI (if using OpenAI)
OPENAI_API_KEY=your_openai_api_key

# Google Gemini (if using Google)
GOOGLE_API_KEY=your_google_api_key
```

### Database Configuration

```bash
# MongoDB Connection
MONGODB_URI=mongodb://localhost:27017/your_database
# OR for MongoDB Atlas
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/database
```

### Other Configuration

```bash
# Langfuse (optional, for observability)
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_SECRET_KEY=your_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com
```

---

## Build Time Considerations

### Heavy Dependencies

The following packages significantly increase build time:

1. **unstructured[all-docs]** (10-15 minutes)
   - Advanced document processing
   - Only needed for document ingestion

2. **sentence-transformers** (5+ minutes)
   - Pulls NVIDIA CUDA dependencies (~5GB)
   - Required for dense retrieval and reranking
   - Can be excluded in lightweight deployments

### Lightweight Deployment

For faster builds, use `requirements.prod.light.txt` which excludes:
- `sentence-transformers` (reranking will be skipped)
- `unstructured[all-docs]` (basic document processing only)

---

## Dependency Usage in Context Processing

### Context Compressor Flow

1. **Document Retrieval**:
   - Uses `chromadb` for vector search
   - Uses `rank-bm25` for sparse retrieval
   - Uses `sentence-transformers` for embeddings

2. **Context Compression**:
   - Uses LLM (OpenAI or Gemini) via `langchain`
   - Uses `tiktoken` for token counting
   - Uses `langchain_core.documents` for document handling

3. **Reranking**:
   - Uses `sentence-transformers` cross-encoder models
   - Uses `scikit-learn` for similarity calculations

---

## Troubleshooting

### Common Issues

1. **Import Errors**:
   - Ensure all packages are installed: `pip install -r requirements.txt`
   - Check Python version (3.8+ required)

2. **Version Conflicts**:
   - Use exact versions specified in `requirements.txt`
   - Avoid upgrading transformers/huggingface-hub beyond specified ranges

3. **Build Timeouts**:
   - Use `requirements.prod.light.txt` for faster builds
   - Consider pre-building Docker images

4. **Memory Issues**:
   - `sentence-transformers` requires significant RAM
   - Consider using GPU for better performance

---

## Last Updated

- **Date**: December 2025
- **Project Version**: CF_Chatbot-V2
- **Python Version**: 3.8+
- **Node Version**: 18+

---

## Notes

- The `Context_Folder` directory is currently empty but reserved for context-related data files
- Context processing happens in `context_compressor.py` at the root level
- All context-related dependencies are listed in `requirements.txt`

