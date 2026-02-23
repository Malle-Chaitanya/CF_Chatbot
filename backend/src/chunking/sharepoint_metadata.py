"""SharePoint collection chunk metadata. Self-contained; no shared base class."""

from pydantic import BaseModel, Field


class SharePointChunkMetadata(BaseModel):
    """Metadata for one chunk from a SharePoint file (PDF, DOCX, Excel). All fields in one place."""

    doc_id: str = Field(description="Source document ID")
    chunk_index: int = Field(ge=0, description="Zero-based index of chunk within document")
    source_type: str = Field(default="sharepoint", description="Source type")
    doc_type: str = Field(description="pdf, docx, or excel")
    title: str = Field(description="File name / title")
    folder_path: str | None = Field(default=None, description="Folder path in SharePoint")
    sheet_name: str | None = Field(default=None, description="Sheet name for Excel; null for PDF/DOCX")
    content: str = Field(default="", description="Chunk text")
    start_char: int | None = Field(default=None, ge=0, description="Start character offset in source")
    end_char: int | None = Field(default=None, ge=0, description="End character offset in source")
    doc_title: str | None = Field(default=None, description="Document title")
    last_modified: str | None = Field(default=None, description="Last modified date ISO string")
