"""
Registry Service Client with mock mode support.
Uses in-memory storage for mock data instead of static responses.
"""

from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.schemas.requests import (
    CheckUniquenessRequest,
    CreateDraftRequest,
    UpdateDocumentStatusRequest,
    UpdateDraftStatusRequest,
)
from app.services.base_client import ServiceClient


class RegistryServiceClient(ServiceClient):
    """Client for Registry Service."""

    # ------------------------------------------------------------------
    #  Immutable seed data — always available as fallback
    # ------------------------------------------------------------------

    _SEED_DRAFTS: Dict[int, Dict[str, Any]] = {
        1: {
            "draft_id": 1,
            "file_key": "drafts/1/file.pdf",
            "document_key": "doc-1",
            "status": "uploaded",
            "created_by": "user-1",
            "created_at": "2026-06-08T10:00:00Z",
            "updated_at": "2026-06-08T10:00:00Z",
        },
    }

    _SEED_DOCUMENTS: Dict[int, Dict[str, Any]] = {
        1: {
            "document_id": 1,
            "title": "Test Document",
            "status": "active",
        },
    }

    # ------------------------------------------------------------------
    #  Runtime storage — mutated by mock operations.
    #  Reads fall back to seed data when runtime has no entry.
    #  Deletes remove from runtime only (re-exposing seed).
    # ------------------------------------------------------------------

    _storage: Dict[str, Any] = {
        "drafts": {},  # runtime overrides
        "documents": {},
        "draft_seq": 1,
        "doc_seq": 1,
    }

    def __init__(self):
        super().__init__(
            service_name="registry",
            service_url=settings.services.REGISTRY_SERVICE_URL,
            mock_mode=settings.services.REGISTRY_SERVICE_MOCK,
        )

    # ------------------------------------------------------------------
    #  Storage helpers
    # ------------------------------------------------------------------

    @classmethod
    def _get_draft(cls, storage: dict, draft_id: int) -> Optional[dict]:
        """Get draft from runtime or fall back to seed."""
        draft = storage["drafts"].get(draft_id)
        if draft is not None:
            return draft
        return cls._SEED_DRAFTS.get(draft_id)

    @classmethod
    def _all_drafts(cls, storage: dict) -> List[dict]:
        """Merge seed + runtime drafts (runtime shadows seed)."""
        merged = dict(cls._SEED_DRAFTS)
        merged.update(storage["drafts"])
        return list(merged.values())

    @classmethod
    def _all_documents(cls, storage: dict) -> List[dict]:
        """Merge seed + runtime documents (runtime shadows seed)."""
        merged = dict(cls._SEED_DOCUMENTS)
        merged.update(storage["documents"])
        return list(merged.values())

    # ------------------------------------------------------------------
    #  Mock generator — routes method+endpoint to storage-backed handlers
    # ------------------------------------------------------------------

    async def _generate_mock(
        self, method: str, endpoint: str, default_mock: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        storage = type(self)._storage
        endpoint = endpoint.rstrip("/")
        parts = endpoint.split("/")
        # parts = ["", "registry", ...]

        # --- Drafts ---
        if endpoint == "/api/v1/registry/drafts":
            if method == "POST":
                return self._mock_create_draft(storage, kwargs.get("json", {}))
            return default_mock

        if (
            len(parts) >= 5
            and parts[1] == "api"
            and parts[2] == "v1"
            and parts[3] == "registry"
            and parts[4] == "drafts"
            and parts[5].isdigit()
        ):
            draft_id = int(parts[5])
            sub = parts[6] if len(parts) > 6 else None

            if sub is None:
                if method == "GET":
                    return self._mock_get_draft(storage, draft_id)
                elif method == "DELETE":
                    return self._mock_delete_draft(storage, draft_id)
                return default_mock

            if sub == "preview" and method == "GET":
                return self._mock_get_draft_preview(storage, draft_id)

            if sub == "status" and method == "PATCH":
                return self._mock_update_draft_status(
                    storage, draft_id, kwargs.get("json", {})
                )

            if sub == "metadata" and method == "PATCH":
                return self._mock_update_draft_metadata(
                    storage, draft_id, kwargs.get("json", {})
                )

        # --- Documents ---
        if endpoint == "/api/v1/registry/documents/check-uniqueness" and method == "POST":
            return self._mock_check_uniqueness(storage, kwargs.get("json", {}))

        if endpoint == "/api/v1/registry/documents":
            if method == "POST":
                return self._mock_create_document(storage, kwargs.get("json", {}))
            return default_mock

        if (
            len(parts) >= 5
            and parts[1] == "api"
            and parts[2] == "v1"
            and parts[3] == "registry"
            and parts[4] == "documents"
            and parts[5].isdigit()
        ):
            doc_id = int(parts[5])
            sub = parts[6] if len(parts) > 6 else None

            # --- Document status (RG-1: internal, only Orchestrator) ---
            if sub == "status" and method == "PATCH":
                return self._mock_update_document_status(
                    storage, doc_id, kwargs.get("json", {})
                )

            # --- Document sections for RAG Builder (RS-6/RS-7) ---
            if sub == "sections" and method == "GET":
                return self._mock_get_document_sections(storage, doc_id)

            # --- Document versions (internal: Orchestrator creates) ---
            if sub == "versions" and method == "POST":
                return self._mock_create_version(storage, doc_id, kwargs.get("json", {}))

            if sub is None:
                if method == "DELETE":
                    return self._mock_delete_document(storage, doc_id)
            return default_mock

        return default_mock

    # ------------------------------------------------------------------
    #  Draft mock handlers
    # ------------------------------------------------------------------

    @staticmethod
    def _mock_create_draft(storage: dict, body: dict) -> dict:
        storage["draft_seq"] += 1
        draft_id = storage["draft_seq"]
        now = "2026-06-08T10:00:00Z"
        draft: Dict[str, Any] = {
            "id": draft_id,
            "file_key": body.get("file_key", ""),
            "document_key": body.get("document_key", ""),
            "status": "uploaded",
            "created_by": body.get("created_by", ""),
            "created_at": now,
            "updated_at": now,
        }
        if body.get("file_hash_sha256"):
            draft["file_hash_sha256"] = body["file_hash_sha256"]
        if body.get("title_hash_sha256"):
            draft["title_hash_sha256"] = body["title_hash_sha256"]
        if body.get("title_key"):
            draft["title_key"] = body["title_key"]
        if body.get("metadata_fields"):
            draft["metadata_fields"] = body["metadata_fields"]
        storage["drafts"][draft_id] = draft
        return {"data": dict(draft)}

    @classmethod
    def _mock_get_draft(cls, storage: dict, draft_id: int) -> dict:
        draft = cls._get_draft(storage, draft_id)
        if draft is not None:
            return {"data": dict(draft)}
        return {"error": {"code": "NOT_FOUND", "message": f"Draft {draft_id} not found"}}

    @classmethod
    def _mock_get_draft_preview(cls, storage: dict, draft_id: int) -> dict:
        draft = cls._get_draft(storage, draft_id)
        if draft is None:
            return {"error": {"code": "NOT_FOUND", "message": f"Draft {draft_id} not found"}}
        # Use stored metadata_fields if available, otherwise fall back to hardcoded seed.
        # All metadata_fields keys are passed through so arbitrary JSON metadata
        # (e.g. udk_code) is preserved in the response.
        meta = draft.get("metadata_fields") or {}
        data = {
            "draft_id": draft_id,
            "doc_code": "ГОСТ 20868-81",
            "title": "Стойки установочные крепежные",
            "document_type": "normative",
            "year": "1981",
            "revision": None,
            "preview_not_supported": False,
            "total_pages": 3,
            "processed_pages": 3,
        }
        # Override with stored metadata_fields — preserves ALL keys (known + custom)
        data.update(meta)
        return {"data": data}



    @classmethod
    def _mock_update_draft_status(cls, storage: dict, draft_id: int, body: dict) -> dict:
        # If not in runtime, copy seed to runtime first so we can mutate it
        draft = storage["drafts"].get(draft_id)
        if draft is None:
            seed = cls._SEED_DRAFTS.get(draft_id)
            if seed is None:
                return {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Draft {draft_id} not found",
                    }
                }
            draft = dict(seed)
            storage["drafts"][draft_id] = draft

        status = body.get("status")
        draft["status"] = status
        if "document_id" in body:
            draft["document_id"] = body["document_id"]
        draft["updated_at"] = "2026-06-08T10:00:00Z"
        return {
            "data": {
                "draft_id": draft_id,
                "status": status,
                "document_id": body.get("document_id"),
                "updated_at": draft["updated_at"],
            }
        }

    @classmethod
    def _mock_update_draft_metadata(cls, storage: dict, draft_id: int, body: dict) -> dict:
        """Update draft metadata (PATCH /drafts/{id}/metadata)."""
        draft = storage["drafts"].get(draft_id)
        if draft is None:
            seed = cls._SEED_DRAFTS.get(draft_id)
            if seed is None:
                return {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Draft {draft_id} not found",
                    }
                }
            draft = dict(seed)
            storage["drafts"][draft_id] = draft

        preview_metadata = body.get("preview_metadata", {})
        metadata_overrides = body.get("metadata_overrides")

        # Merge preview_metadata into metadata_fields
        existing_meta = draft.get("metadata_fields") or {}
        existing_meta.update(preview_metadata)
        draft["metadata_fields"] = existing_meta

        if metadata_overrides is not None:
            draft["metadata_overrides"] = metadata_overrides

        draft["updated_at"] = "2026-06-08T10:00:00Z"
        return {
            "data": {
                "draft_id": draft_id,
                "status": draft.get("status", "uploaded"),
                "preview_metadata": preview_metadata,
                "updated_at": draft["updated_at"],
            }
        }

    @classmethod
    def _mock_delete_draft(cls, storage: dict, draft_id: int) -> dict:
        # Check existence in runtime OR seed
        exists = draft_id in storage["drafts"] or draft_id in cls._SEED_DRAFTS
        if not exists:
            return {
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Draft {draft_id} not found",
                }
            }
        # Remove runtime entry (seed re-exposed — pre-seeded entries are
        # logically indestructible, matching old mock behaviour)
        storage["drafts"].pop(draft_id, None)
        return {
            "data": {
                "draft_id": draft_id,
                "deleted": True,
                "deleted_at": "2026-06-08T10:00:00Z",
            }
        }

    # ------------------------------------------------------------------
    #  Document mock handlers
    # ------------------------------------------------------------------

    @staticmethod
    def _mock_create_document(storage: dict, body: dict) -> dict:
        storage["doc_seq"] += 1
        doc_id = storage["doc_seq"]
        is_new = not any(
            d.get("draft_id") == body.get("draft_id")
            for d in storage["documents"].values()
        )
        doc = {
            "document_id": doc_id,
            "version_id": doc_id * 10 + 1,
            "is_new_document": is_new,
            **body,
        }
        storage["documents"][doc_id] = doc
        return {"data": dict(doc)}

    @classmethod
    def _mock_update_document_status(cls, storage: dict, doc_id: int, body: dict) -> dict:
        """Mock for PATCH /registry/documents/{id}/status (RG-1)."""
        doc = storage["documents"].get(doc_id)
        if doc is None:
            seed = cls._SEED_DOCUMENTS.get(doc_id)
            if seed is None:
                return {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Document {doc_id} not found",
                    }
                }
            doc = dict(seed)
            storage["documents"][doc_id] = doc
        status = body.get("status")
        if status:
            doc["status"] = status
        if body.get("updated_by"):
            doc["updated_by"] = body["updated_by"]
        doc["updated_at"] = "2026-06-08T10:00:00Z"
        return {
            "data": {
                "document_id": doc_id,
                "status": doc["status"],
                "updated_at": doc["updated_at"],
            }
        }

    @classmethod
    def _mock_delete_document(cls, storage: dict, doc_id: int) -> dict:
        exists = doc_id in storage["documents"] or doc_id in cls._SEED_DOCUMENTS
        if not exists:
            return {
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Document {doc_id} not found",
                }
            }
        storage["documents"].pop(doc_id, None)
        return {"data": {"deleted": True, "document_id": doc_id}}

    @classmethod
    def _mock_get_document_sections(cls, storage: dict, doc_id: int) -> dict:
        """Mock for GET /registry/documents/{doc_id}/sections.

        Returns document metadata + sections[] as expected by RAG Builder.
        """
        doc = storage["documents"].get(doc_id)
        if doc is None and doc_id in cls._SEED_DOCUMENTS:
            doc = dict(cls._SEED_DOCUMENTS[doc_id])
        if doc is None:
            return {
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Document {doc_id} not found",
                }
            }
        # Return sections from stored doc body or generate mock sections
        sections = doc.get("sections", [])
        if not sections:
            sections = [
                {
                    "section_id": doc_id * 100 + 1,
                    "document_id": doc_id,
                    "parent_id": None,
                    "clause": "1",
                    "title": None,
                    "level": 1,
                    "path": "1",
                    "page": 1,
                    "type": "text",
                    "content": {
                        "text": f"Mock section content for document {doc_id}.",
                        "amendments": [],
                    },
                }
            ]
        return {
            "data": {
                "document": {
                    "id": doc_id,
                    "doc_code": doc.get("doc_code", ""),
                    "title": doc.get("title", ""),
                    "era": doc.get("era", "CURRENT"),
                    "validity_status": doc.get("status", "active"),
                },
                "sections": sections,
                "terminology": doc.get("terminology", []),
                "references": doc.get("references", []),
            }
        }

    @classmethod
    def _mock_create_version(cls, storage: dict, doc_id: int, body: dict) -> dict:
        """Mock for POST /registry/documents/{id}/versions."""
        from datetime import datetime, timezone

        storage["doc_seq"] = storage.get("doc_seq", 1000) + 1
        version_id = storage["doc_seq"]

        # Determine next version number
        existing_versions = [
            v for v in storage.get("versions", {}).values()
            if v.get("document_id") == doc_id
        ]
        version_number = max((v.get("version_number", 0) for v in existing_versions), default=0) + 1

        if "versions" not in storage:
            storage["versions"] = {}
        version = {
            "version_id": version_id,
            "document_id": doc_id,
            "version_number": version_number,
            "file_hash_sha256": body.get("file_hash_sha256", ""),
            "file_key": body.get("file_key", ""),
            "size_bytes": body.get("size_bytes", 0),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        storage["versions"][version_id] = version
        return {
            "data": {
                "document_id": doc_id,
                "version_id": version_id,
                "version_number": version_number,
                "file_hash_sha256": version["file_hash_sha256"],
                "is_duplicate_file": False,
                "created_at": version["created_at"],
            }
        }

    @classmethod
    def _mock_check_uniqueness(cls, storage: dict, body: dict) -> dict:
        title = body.get("title", "")
        is_duplicate = False
        if title:
            for d in cls._all_drafts(storage) + cls._all_documents(storage):
                if d.get("document_key") == title or d.get("file_key", "").find(title[:8]) >= 0:
                    is_duplicate = True
                    break
        return {
            "data": {
                "is_duplicate": is_duplicate,
                "is_duplicate_file": False,
                "candidates": [],
            }
        }

    # ------------------------------------------------------------------
    #  Public API — each delegates to self.call() which routes through
    #  _generate_mock in mock mode.  Signatures unchanged.
    # ------------------------------------------------------------------

    _mock_doc_seq: int = 1000

    async def create_document(self, document_data: dict) -> dict:
        """Create a new document in the registry.

        Returns document_id, version_id, is_new_document.
        """
        RegistryServiceClient._mock_doc_seq += 1
        doc_id = RegistryServiceClient._mock_doc_seq
        return await self.call(
            "POST",
            "/api/v1/registry/documents",
            mock_response={
                "data": {
                    "document_id": doc_id,
                    "version_id": doc_id * 10 + 1,
                    "is_new_document": True,
                    **document_data,
                }
            },
            json=document_data,
        )

    async def create_version(self, doc_id: int, version_data: dict) -> dict:
        """Create a new version of a document in the registry.

        Internal endpoint — only Orchestrator can call
        POST /registry/documents/{id}/versions.
        Returns document_id, version_id, version_number, is_duplicate_file.
        """
        return await self.call(
            "POST",
            f"/api/v1/registry/documents/{doc_id}/versions",
            mock_response={
                "data": {
                    "document_id": doc_id,
                    "version_id": doc_id * 100 + 1,
                    "version_number": 2,
                    "is_duplicate_file": False,
                    **version_data,
                }
            },
            json=version_data,
        )

    async def update_document_status(
        self,
        document_id: int,
        status: str,
        updated_by: Optional[str] = None,
    ) -> dict:
        """
        Update document status (RG-1).

        Internal endpoint — only Orchestrator can call PATCH /registry/documents/{id}/status.
        Used by Pipeline 2 to mark document status after indexation.
        """
        body = UpdateDocumentStatusRequest(
            status=status,
            updated_by=updated_by,
        )
        return await self.call(
            "PATCH",
            f"/api/v1/registry/documents/{document_id}/status",
            request_model=UpdateDocumentStatusRequest,
            mock_response={
                "data": {
                    "document_id": document_id,
                    "status": status,
                    "updated_at": "2026-06-08T10:00:00Z",
                }
            },
            json=body.model_dump(exclude_none=True),
        )

    async def delete_document(self, document_id: int) -> dict:
        """Delete a document from the registry."""
        return await self.call(
            "DELETE",
            f"/api/v1/registry/documents/{document_id}",
            mock_response={"data": {"deleted": True, "document_id": document_id}},
        )

    async def get_document_sections(self, document_id: int) -> dict:
        """Get document with sections for RAG Builder.

        GET /api/v1/registry/documents/{doc_id}/sections
        Returns document metadata + sections[] + terminology + references.
        """
        return await self.call(
            "GET",
            f"/api/v1/registry/documents/{document_id}/sections",
            mock_response={
                "data": {
                    "document": {
                        "id": document_id,
                        "doc_code": "",
                        "title": f"Document {document_id}",
                        "era": "CURRENT",
                        "validity_status": "active",
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
                            "content": {
                                "text": f"Mock section content for document {document_id}.",
                                "amendments": [],
                            },
                        }
                    ],
                    "terminology": [],
                    "references": [],
                }
            },
        )

    # --- Drafts ---

    async def create_draft(
        self,
        file_key: str,
        document_key: str,
        created_by: str,
        file_hash_sha256: Optional[str] = None,
        title_hash_sha256: Optional[str] = None,
        title_key: Optional[str] = None,
        metadata_fields: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """Create a draft in Registry. Returns draft_id."""
        body = CreateDraftRequest(
            file_key=file_key,
            document_key=document_key,
            created_by=created_by,
            file_hash_sha256=file_hash_sha256,
            title_hash_sha256=title_hash_sha256,
            title_key=title_key,
            metadata_fields=metadata_fields,
        )
        return await self.call(
            "POST",
            "/api/v1/registry/drafts",
            request_model=CreateDraftRequest,
            mock_response={
                "data": {
                    "id": 1,
                    "file_key": file_key,
                    "document_key": document_key,
                    "status": "uploaded",
                    "created_by": created_by,
                    "created_at": "2026-06-08T10:00:00Z",
                }
            },
            json=body.model_dump(exclude_none=True),
        )

    async def get_draft(self, draft_id: int) -> dict:
        """Get draft by ID."""
        return await self.call(
            "GET",
            f"/api/v1/registry/drafts/{draft_id}",
            mock_response={
                "data": {
                    "draft_id": draft_id,
                    "file_key": f"drafts/{draft_id}/file.pdf",
                    "document_key": f"doc-{draft_id}",
                    "status": "uploaded",
                    "created_by": "user-1",
                    "created_at": "2026-06-08T10:00:00Z",
                    "updated_at": "2026-06-08T10:00:00Z",
                }
            },
        )

    async def get_draft_preview(self, draft_id: int) -> dict:
        """Get preview metadata for a draft."""
        return await self.call(
            "GET",
            f"/api/v1/registry/drafts/{draft_id}/preview",
            mock_response={
                "data": {
                    "draft_id": draft_id,
                    "doc_code": "ГОСТ 20868-81",
                    "title": "Стойки установочные крепежные",
                    "document_type": "normative",
                    "year": "1981",
                    "revision": None,
                    "preview_not_supported": False,
                    "total_pages": 3,
                    "processed_pages": 3,
                }
            },
        )

    async def update_draft_status(
        self,
        draft_id: int,
        status: str,
        document_id: Optional[int] = None,
    ) -> dict:
        """Update draft status (and optionally set document_id)."""
        body = UpdateDraftStatusRequest(
            status=status,
            document_id=document_id,
        )
        return await self.call(
            "PATCH",
            f"/api/v1/registry/drafts/{draft_id}/status",
            request_model=UpdateDraftStatusRequest,
            mock_response={
                "data": {
                    "draft_id": draft_id,
                    "status": status,
                    "document_id": document_id,
                    "updated_at": "2026-06-08T10:00:00Z",
                }
            },
            json=body.model_dump(exclude_none=True),
        )

    async def delete_draft(self, draft_id: int) -> dict:
        """Delete a draft."""
        return await self.call(
            "DELETE",
            f"/api/v1/registry/drafts/{draft_id}",
            mock_response={
                "data": {
                    "draft_id": draft_id,
                    "deleted": True,
                    "deleted_at": "2026-06-08T10:00:00Z",
                }
            },
        )

    async def update_draft_metadata(self, draft_id: int, preview_metadata: dict, metadata_overrides: Optional[dict] = None, updated_by: str = "system") -> dict:
        """Update draft metadata (PATCH /api/v1/registry/drafts/{draft_id}/metadata)."""
        body = {
            "preview_metadata": preview_metadata,
            "metadata_overrides": metadata_overrides,
            "updated_by": updated_by,
        }
        return await self.call(
            "PATCH",
            f"/api/v1/registry/drafts/{draft_id}/metadata",
            mock_response={
                "data": {
                    "draft_id": draft_id,
                    "status": "uploaded",
                    "preview_metadata": preview_metadata,
                    "updated_at": "2026-06-08T10:00:00Z",
                }
            },
            json=body,
        )

    async def check_uniqueness(
        self,
        title: str,
        doc_code: Optional[str] = None,
        era: Optional[str] = None,
        source_type: Optional[str] = None,
        file_size_bytes: Optional[int] = None,
    ) -> dict:
        """Check document uniqueness (duplicate detection)."""
        body = CheckUniquenessRequest(
            title=title,
            doc_code=doc_code,
            era=era,
            source_type=source_type,
            file_size_bytes=file_size_bytes,
        )
        return await self.call(
            "POST",
            "/api/v1/registry/documents/check-uniqueness",
            request_model=CheckUniquenessRequest,
            mock_response={
                "data": {
                    "is_duplicate": False,
                    "is_duplicate_file": False,
                    "candidates": [],
                }
            },
            json=body.model_dump(exclude_none=True),
        )

    async def create_draft_snapshot(self, draft_id: int, metadata: dict) -> dict:
        """Save preview snapshot for a draft (P1F-4).

        Called on approve to 'freeze' preview_metadata in Registry.
        """
        return await self.call(
            "POST",
            f"/api/v1/registry/drafts/{draft_id}/snapshot",
            mock_response={
                "data": {
                    "draft_id": draft_id,
                    "snapshot_saved": True,
                }
            },
            json={"preview_metadata": metadata},
        )
