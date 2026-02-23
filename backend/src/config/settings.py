"""Application settings loaded from environment (Pydantic BaseSettings)."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Backend settings from env vars. Copy .env.example to .env and set values."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Weaviate
    weaviate_url: str = Field(default="http://localhost:8081", description="Weaviate HTTP URL")
    embedding_model: str = Field(default="text-embedding-3-small", description="OpenAI embedding model")
    embedding_dimension: int = Field(default=1536, ge=1, description="Vector dimension from embedding model (e.g. 1536 for text-embedding-3-small)")

    # OpenAI
    openai_api_key: str = Field(default="", description="OpenAI API key for embeddings and optional LLM")

    # Chunking (global defaults; blog uses its own when source_type=blog)
    chunk_target_tokens: int = Field(default=512, ge=1, description="Target chunk size in tokens")
    chunk_overlap_tokens: int = Field(default=64, ge=0, description="Overlap between chunks in tokens")
    # Blog-only chunking (from .env: BLOG_CHUNK_TARGET_TOKENS, BLOG_CHUNK_OVERLAP_TOKENS)
    blog_chunk_target_tokens: int = Field(default=512, ge=1, description="Blog chunk target size in tokens")
    blog_chunk_overlap_tokens: int = Field(default=64, ge=0, description="Blog chunk overlap in tokens")

    # Retrieval
    retrieval_top_k: int = Field(default=10, ge=1, le=100, description="Number of chunks to retrieve")
    # Hybrid search: alpha = weight of vector (semantic). 1.0 = pure vector, 0.0 = pure keyword (BM25), 0.7 = 70% semantic + 30% keyword
    retrieval_hybrid_alpha: float = Field(default=0.7, ge=0.0, le=1.0, description="Hybrid search alpha: 1=vector only, 0=BM25 only, 0.7=70%% semantic + 30%% keyword")

    # LLM
    llm_model: str = Field(default="gpt-4o-mini", description="LLM model for query answering")
    llm_temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="LLM temperature")

    # Debug: log full RAG context for grounding checks (Option A). Set LOG_FULL_CONTEXT=true to log every request.
    log_full_context: bool = Field(default=False, description="If True, write full context sent to LLM to rag_context_debug.log on every chat request")

    # Optional LangSmith
    langchain_tracing_v2: bool = Field(default=False, description="Enable LangSmith tracing")
    langchain_api_key: str = Field(default="", description="LangSmith API key")
    langchain_project: str = Field(default="rag-phase1", description="LangSmith project name")

    # Parent-document expansion
    enable_parent_doc_expansion: bool = Field(default=False, description="Expand retrieval with parent documents")

    # Microsoft OAuth (for frontend Sign in with Microsoft)
    microsoft_client_id: str = Field(default="", description="Azure AD app (client) ID")
    microsoft_client_secret: str = Field(default="", description="Azure AD client secret")
    microsoft_tenant: str = Field(default="common", description="Tenant ID or domain (e.g. cloudfuze.com)")
    microsoft_allowed_domain: str = Field(default="", description="If set, only allow emails ending with this domain (e.g. cloudfuze.com)")

    # Jira (for API-based ingestion; .env: JIRA_SERVER, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEYS)
    enable_jira_source: bool = Field(default=True, description="Enable Jira ingestion. Set false to skip Jira when running ingest.")
    jira_server: str = Field(default="", description="Jira base URL e.g. https://cf2020.atlassian.net")
    jira_email: str = Field(default="", description="Jira user email for API auth")
    jira_api_token: str = Field(default="", description="Jira API token (Atlassian)")
    jira_project_keys: str = Field(default="PRI", description="Comma-separated project keys e.g. PRI,PROJ")
    jira_field_combination: str = Field(default="", description="Optional custom field ID for Combination e.g. customfield_10050")
    jira_field_root_cause: str = Field(default="", description="Optional custom field ID for Root Cause")
    jira_field_fix_description: str = Field(default="", description="Optional custom field ID for Fix Description")
    # Jira ingest: filter by status, updated date (past N months), and max tickets per run. From .env.
    jira_ingest_statuses: str = Field(default="Resolved,Closed", description="Comma-separated statuses to fetch (e.g. Resolved,Closed). Only these tickets are ingested.")
    jira_ingest_past_months: int = Field(default=2, ge=0, description="Only tickets updated in the past N months (0 = no date filter).")
    jira_ingest_max_tickets: int = Field(default=1000, ge=0, description="Max tickets to ingest this run (0 = no limit).")

    # Vectorstore and blog-from-web ingestion
    initialize_vectorstore: bool = Field(default=False, description="When true, run vectorstore init / blog ingestion if enabled")
    enable_web_source: bool = Field(default=False, description="Enable blog ingestion from WordPress URL when initializing")
    web_source_url: str = Field(default="", description="WordPress REST API URL for posts (e.g. .../wp/v2/posts?per_page=100)")
    web_start_page: int = Field(default=1, ge=1, description="First page number for pagination")
    web_max_pages: int = Field(default=100, ge=1, description="Max number of pages to fetch")


def get_settings() -> Settings:
    """Return application settings (singleton-style; create once per process)."""
    return Settings()
