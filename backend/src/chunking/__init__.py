# Chunking package: chunk key + per-collection metadata (no shared base class)
from .metadata import generate_chunk_key
from .token_chunker import chunk_document
from .blog_section_chunker import chunk_blog_by_sections, parse_blog_sections
from .blog_metadata import BlogChunkMetadata
from .sharepoint_metadata import SharePointChunkMetadata
from .jira_metadata import JiraChunkMetadata
from .transcript_metadata import TranscriptChunkMetadata
from .email_metadata import EmailChunkMetadata

__all__ = [
    "generate_chunk_key",
    "chunk_document",
    "chunk_blog_by_sections",
    "parse_blog_sections",
    "BlogChunkMetadata",
    "SharePointChunkMetadata",
    "JiraChunkMetadata",
    "TranscriptChunkMetadata",
    "EmailChunkMetadata",
]
