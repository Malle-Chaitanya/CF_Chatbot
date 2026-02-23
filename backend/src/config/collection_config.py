"""Weaviate collection (class) names and registry. Schema created per collection in init_schema.py."""

# Per-collection class names (Weaviate)
BLOG_COLLECTION_NAME = "BlogChunk"
SHAREPOINT_COLLECTION_NAME = "SharePointChunk"
JIRA_COLLECTION_NAME = "JiraChunk"
TRANSCRIPT_COLLECTION_NAME = "TranscriptChunk"
EMAIL_COLLECTION_NAME = "EmailChunk"

# Optional second SharePoint site; same schema, different filter or class name
SHAREPOINT2_COLLECTION_NAME = "SharePoint2Chunk"

# Legacy (Phase 1 single class); prefer per-collection names above
DEFAULT_COLLECTION_NAME = "DocumentChunk"

# Registry: collection key -> (Weaviate class name, metadata model)
# Used by init_schema and ingest to resolve --collection <name>
COLLECTION_REGISTRY: dict[str, tuple[str, str]] = {
    "blog": (BLOG_COLLECTION_NAME, "chunking.blog_metadata.BlogChunkMetadata"),
    "sharepoint": (SHAREPOINT_COLLECTION_NAME, "chunking.sharepoint_metadata.SharePointChunkMetadata"),
    "jira": (JIRA_COLLECTION_NAME, "chunking.jira_metadata.JiraChunkMetadata"),
    "transcripts": (TRANSCRIPT_COLLECTION_NAME, "chunking.transcript_metadata.TranscriptChunkMetadata"),
    "email": (EMAIL_COLLECTION_NAME, "chunking.email_metadata.EmailChunkMetadata"),
    "sharepoint2": (SHAREPOINT2_COLLECTION_NAME, "chunking.sharepoint_metadata.SharePointChunkMetadata"),
}
