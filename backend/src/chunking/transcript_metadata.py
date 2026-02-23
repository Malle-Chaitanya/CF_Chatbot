"""Transcripts collection chunk metadata. Self-contained; no shared base class."""

from pydantic import BaseModel, Field


class TranscriptChunkMetadata(BaseModel):
    """Metadata for one chunk from a transcript file. All fields in one place."""

    doc_id: str = Field(description="Source document ID")
    chunk_index: int = Field(ge=0, description="Zero-based index of chunk within document")
    source_type: str = Field(default="Transcripts", description="Source type")
    file_name: str = Field(description="Transcript file name")
    included_persons: str | list[str] | None = Field(default=None, description="Speakers / customers (string or list)")
    content: str = Field(default="", description="Chunk text")
