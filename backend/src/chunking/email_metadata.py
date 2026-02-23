"""Email collection chunk metadata. Self-contained; no shared base class."""

from pydantic import BaseModel, Field


class EmailChunkMetadata(BaseModel):
    """Metadata for one chunk from an email. All fields in one place."""

    doc_id: str = Field(description="Source document ID")
    chunk_index: int = Field(ge=0, description="Zero-based index of chunk within document")
    source_type: str = Field(default="email", description="Source type")
    from_addr: str | None = Field(default=None, description="From address")
    to_addr: str | None = Field(default=None, description="To address(es)")
    subject: str | None = Field(default=None, description="Subject")
    date: str | None = Field(default=None, description="Date ISO string")
    message_id: str | None = Field(default=None, description="Message ID")
    content: str = Field(default="", description="Chunk text")
