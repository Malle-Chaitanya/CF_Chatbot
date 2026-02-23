"""Jira collection chunk metadata. Self-contained; no shared base class."""

from pydantic import BaseModel, Field


class JiraChunkMetadata(BaseModel):
    """Metadata for one chunk from a Jira ticket. All fields in one place.
    doc_id = ticket_key (parent identity). No parent_ticket_key.
    """

    # Required for weaviate_writer
    doc_id: str = Field(description="Source document ID (ticket_key)")
    chunk_index: int = Field(ge=0, description="Zero-based index of chunk within document")
    source_type: str = Field(default="jira", description="Source type")

    # Collection name for grounding and hybrid search
    collection: str = Field(default="JiraTickets", description="Collection name for grounding and hybrid search")

    # Parent metadata (scalar only; stored on every chunk)
    ticket_key: str = Field(description="Issue key e.g. PRI-9796")
    project_key: str | None = Field(default=None, description="Project key e.g. PRI")
    issue_type: str | None = Field(default=None, description="e.g. Task, Bug")
    priority: str | None = Field(default=None, description="e.g. Medium, Highest")
    status: str | None = Field(default=None, description="e.g. Resolved")
    combination: str = Field(description="Migration combination (required), e.g. Slack to Chat, Dropbox - Onedrive")
    assignee: str | None = Field(default=None, description="Assignee display name")
    reporter: str | None = Field(default=None, description="Reporter display name")
    doc_title: str | None = Field(default=None, description="Ticket summary/title")
    created: str | None = Field(default=None, description="Created date ISO string")
    updated: str | None = Field(default=None, description="Updated date ISO string")
    resolved: str | None = Field(default=None, description="Resolved date ISO string")

    # Child/section fields
    section: str | None = Field(
        default=None,
        description="summary | description | root_cause | fix_description | comment",
    )
    ticket_chunk_type: str | None = Field(
        default=None,
        description="summary | problem | resolution",
    )
    total_chunks: int | None = Field(default=None, ge=0, description="Total chunks for this ticket")
    comment_index: int | None = Field(default=None, ge=1, description="1-based comment index; only for section=comment")
    # When a section (description, root_cause, fix_description) is split into subchunks:
    section_part_index: int | None = Field(default=None, ge=1, description="1-based index of this part within the section")
    section_part_total: int | None = Field(default=None, ge=1, description="Total parts for this section (when split)")
    # When a comment body is split into subchunks (ordering for retrieval):
    comment_part_index: int | None = Field(default=None, ge=1, description="1-based index of this part within the comment")
    comment_part_total: int | None = Field(default=None, ge=1, description="Total parts for this comment (when split)")

    # Ticket-level flags (for filtering: ticket has at least one resolution/root_cause section)
    ticket_has_resolution: bool | None = Field(default=None, description="Ticket contains resolution section(s)")
    ticket_has_root_cause: bool | None = Field(default=None, description="Ticket contains root_cause section")

    # Schema consistency; writer sets stored value from chunk text
    content: str = Field(default="", description="Chunk text")
