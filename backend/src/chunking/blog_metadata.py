"""Blog collection chunk metadata. Self-contained; no shared base class."""

from pydantic import BaseModel, Field


class BlogChunkMetadata(BaseModel):
    """Metadata for one chunk from a blog post. All fields in one place."""

    doc_id: str = Field(description="Source document ID (e.g. slug from URL)")
    chunk_index: int = Field(ge=0, description="Zero-based index of chunk within document")
    chunk_role: str = Field(default="content", description="content or summary")
    heading_path: str | None = Field(default=None, description="Section path e.g. Step-by-Step Migration > Steps 1-2")
    doc_title: str | None = Field(default=None, description="Post title")
    url: str | None = Field(default=None, description="Canonical blog URL")
    author: str | None = Field(default=None, description="Author name")
    published_date: str | None = Field(default=None, description="ISO date or datetime")
    tags: list[str] = Field(default_factory=list, description="Tags")
    category: str | None = Field(default=None, description="Category")
    migration_source: str | None = Field(default=None, description="e.g. Egnyte")
    migration_destination: str | None = Field(default=None, description="e.g. Microsoft 365")
    migration_combination: str | None = Field(default=None, description="Source to destination e.g. Egnyte to Microsoft 365")
    migration_type: str | None = Field(default=None, description="(Legacy) e.g. External Shares")
    content: str = Field(default="", description="Chunk text")
    token_count: int | None = Field(default=None, ge=0, description="Token count")
    start_char: int | None = Field(default=None, ge=0, description="Start character offset in source")
    end_char: int | None = Field(default=None, ge=0, description="End character offset in source")
    source_type: str = Field(default="blog", description="Source type")
