"""
MockRegistryClient — mock for RegistryServiceClient with FSM validation.

Matches real Registry behaviour (routes.py:2226):
  - update_draft_status: raises 409 if current status is 'approved' or 'discarded'
  - update_draft_metadata: no FSM check (as per real Registry)
  - create_document: always succeeds
  - get_draft / get_draft_preview: return configurable test data

Usage in tests:
    mock_reg = MockRegistryClient()
    mock_reg._ensure_draft(100, status="uploaded")
    with patch("app.core.pipeline.orchestrator.RegistryServiceClient", return_value=mock_reg):
        ...
    assert mock_reg._drafts[100]["status"] == "approved"
"""

from typing import Optional


class MockRegistryClient:
    """Mock Registry client — validates FSM transitions like real Registry."""

    def __init__(self):
        self._drafts: dict[int, dict] = {}
        self._doc_seq: int = 1000
        # Track all method calls for test assertions
        self.call_log: list[tuple[str, dict]] = []

    # ------------------------------------------------------------------
    #  Internal helpers
    # ------------------------------------------------------------------

    def _ensure_draft(self, draft_id: int, status: str = "uploaded") -> dict:
        """Get or create a minimal draft record."""
        if draft_id not in self._drafts:
            self._drafts[draft_id] = {
                "id": draft_id,
                "draft_id": draft_id,
                "file_key": f"drafts/{draft_id}/file.pdf",
                "document_key": f"doc-{draft_id}",
                "status": status,
                "file_hash_sha256": None,
                "title_key": f"Draft {draft_id}",
                "created_by": "user-1",
                "created_at": "2026-06-08T10:00:00Z",
                "updated_at": "2026-06-08T10:00:00Z",
            }
        return self._drafts[draft_id]

    def _log_call(self, method: str, **kwargs):
        self.call_log.append((method, kwargs))

    # ------------------------------------------------------------------
    #  Draft API
    # ------------------------------------------------------------------

    async def get_draft(self, draft_id: int) -> dict:
        """Get draft by ID."""
        self._log_call("get_draft", draft_id=draft_id)
        draft = self._ensure_draft(draft_id)
        return {"data": dict(draft)}  # return a copy

    async def get_draft_preview(self, draft_id: int) -> dict:
        """Get preview metadata for a draft."""
        self._log_call("get_draft_preview", draft_id=draft_id)
        draft = self._ensure_draft(draft_id)
        return {
            "data": {
                "draft_id": draft_id,
                "title": f"Test Draft {draft_id}",
                "doc_code": f"TEST-{draft_id}",
                "source_type": "GOST",
                "year": "2024",
                "era": "CURRENT",
                "jurisdiction": "RU",
                "issuing_body": "Test Body",
                "preview_not_supported": False,
                "total_pages": 3,
                "processed_pages": 3,
                "preview_md": f"# Test Draft {draft_id}\n\nContent",
            }
        }

    async def update_draft_status(
        self,
        draft_id: int,
        status: str,
        document_id: Optional[int] = None,
        **kwargs,
    ) -> dict:
        """Update draft status — validates FSM like real Registry.

        Real Registry (routes.py:2226):
          if draft.status in ('approved', 'discarded') -> HTTPException(409)
        """
        self._log_call(
            "update_draft_status",
            draft_id=draft_id,
            status=status,
            document_id=document_id,
            **kwargs,
        )
        draft = self._ensure_draft(draft_id)

        # FSM check: reject if already in a final state
        if draft["status"] in ("approved", "discarded"):
            raise RuntimeError(
                f"409: DRAFT_ALREADY_DECIDED: "
                f"Draft {draft_id} is already in a final state ({draft['status']})"
            )

        previous_status = draft["status"]
        draft["status"] = status
        if document_id is not None:
            draft["document_id"] = document_id
        return {
            "data": {
                "id": draft_id,
                "status": status,
                "previous_status": previous_status,
                "updated_at": "2026-06-08T10:00:00Z",
            }
        }

    async def update_draft_metadata(self, draft_id: int, **kwargs) -> dict:
        """Update draft metadata — no FSM check (matches real Registry)."""
        self._log_call("update_draft_metadata", draft_id=draft_id, kwargs=kwargs)
        draft = self._ensure_draft(draft_id)
        return {
            "data": {
                "id": draft_id,
                "status": draft["status"],
                "preview_metadata": kwargs.get("preview_metadata"),
                "updated_at": "2026-06-08T10:00:00Z",
            }
        }

    async def create_draft_snapshot(self, draft_id: int, metadata: dict) -> dict:
        """Save preview snapshot for a draft (always succeeds)."""
        self._log_call("create_draft_snapshot", draft_id=draft_id, metadata=metadata)
        return {
            "data": {
                "draft_id": draft_id,
                "snapshot_saved": True,
            }
        }

    # ------------------------------------------------------------------
    #  Document API
    # ------------------------------------------------------------------

    async def create_document(self, document_data: dict) -> dict:
        """Create a document in the registry."""
        self._log_call("create_document", document_data=document_data)
        self._doc_seq += 1
        doc_id = self._doc_seq
        return {
            "data": {
                "document_id": doc_id,
                "version_id": doc_id * 10 + 1,
                "is_new_document": True,
                **document_data,
            }
        }

    async def get_document_sections(self, document_id: int) -> dict:
        """Get document sections."""
        self._log_call("get_document_sections", document_id=document_id)
        return {
            "data": {
                "document": {
                    "id": document_id,
                    "doc_code": f"DOC-{document_id}",
                    "title": f"Document {document_id}",
                },
                "sections": [
                    {
                        "section_id": document_id * 100 + 1,
                        "document_id": document_id,
                        "parent_id": None,
                        "clause": "1",
                        "title": None,
                        "level": 1,
                        "path": "1",
                        "page": 1,
                        "type": "text",
                        "content": {"text": f"Mock section content for document {document_id}."},
                    }
                ],
                "terminology": [],
                "references": [],
            }
        }

    async def update_document_status(self, document_id: int, status: str) -> dict:
        """Update document status."""
        self._log_call("update_document_status", document_id=document_id, status=status)
        return {"data": {"document_id": document_id, "status": status}}

    # ------------------------------------------------------------------
    #  Lifecycle
    # ------------------------------------------------------------------

    async def close(self):
        """No-op for mock."""
        pass

    def assert_draft_status(self, draft_id: int, expected_status: str) -> None:
        """Assert that a draft reached the expected status."""
        draft = self._drafts.get(draft_id)
        assert draft is not None, f"Draft {draft_id} not found in mock state"
        assert draft["status"] == expected_status, (
            f"Draft {draft_id} expected status '{expected_status}', "
            f"got '{draft['status']}'"
        )
