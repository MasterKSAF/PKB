"""
Registry Service Client with mock mode support.
"""

from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.services.base_client import ServiceClient


class RegistryServiceClient(ServiceClient):
    """Client for Registry Service (classifiers, terminology, documents)."""

    def __init__(self):
        super().__init__(
            service_name="registry",
            service_url=settings.services.REGISTRY_SERVICE_URL,
            mock_mode=settings.services.REGISTRY_SERVICE_MOCK,
        )

    async def _generate_mock(
        self, method: str, endpoint: str, default_mock: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """Generate mock registry responses."""
        # --- Classifiers ---
        if endpoint == "/classifiers" and method == "GET":
            return {
                "data": [
                    {
                        "code": "01",
                        "parent_code": None,
                        "full_name": "Судостроение",
                        "doc_type": "normative",
                        "jurisdiction": "RF",
                        "language": "ru",
                        "oks_code": "01.040.47",
                        "is_thematic": False,
                        "created_at": "2025-12-01T08:00:00Z",
                        "updated_at": "2025-12-01T08:00:00Z",
                    }
                ],
                "meta": {"total": 1, "page": 1, "page_size": 50},
            }

        if endpoint == "/classifiers/tree" and method == "GET":
            return {
                "data": [
                    {
                        "code": "01",
                        "full_name": "Судостроение",
                        "doc_type": "normative",
                        "oks_code": "01.040.47",
                        "is_thematic": False,
                        "children": [],
                    }
                ],
                "meta": {"total": 1, "max_depth_reached": 5},
            }

        if (
            endpoint.startswith("/classifiers/")
            and method == "GET"
            and "tree" not in endpoint
        ):
            code = endpoint.split("/")[-1]
            return {
                "data": {
                    "code": code,
                    "parent_code": None,
                    "full_name": f"Узел {code}",
                    "doc_type": "normative",
                    "jurisdiction": "RF",
                    "language": "ru",
                    "oks_code": "01.040.47",
                    "is_thematic": False,
                    "created_at": "2025-12-01T08:00:00Z",
                    "updated_at": "2025-12-01T08:00:00Z",
                }
            }

        if endpoint == "/classifiers" and method == "POST":
            request_data = kwargs.get("json", {})
            return {
                "data": {
                    "code": request_data.get("code", "new-code"),
                    "parent_code": request_data.get("parent_code"),
                    "full_name": request_data.get("full_name", "Новый узел"),
                    "doc_type": request_data.get("doc_type", "normative"),
                    "jurisdiction": request_data.get("jurisdiction", "RF"),
                    "language": request_data.get("language", "ru"),
                    "oks_code": request_data.get("oks_code"),
                    "is_thematic": request_data.get("is_thematic", False),
                    "created_at": "2026-05-05T10:00:00Z",
                    "updated_at": "2026-05-05T10:00:00Z",
                }
            }

        if endpoint.startswith("/classifiers/") and method == "DELETE":
            code = endpoint.split("/")[-1]
            return {
                "data": {
                    "code": code,
                    "deleted": True,
                    "deleted_at": "2026-05-05T10:30:00Z",
                }
            }

        if endpoint == "/classifiers/import" and method == "POST":
            return {"data": {"inserted": 5, "updated": 2, "errors": []}}

        # --- Terminology ---
        if endpoint == "/terminology" and method == "GET":
            return {
                "data": [
                    {
                        "term_id": "t-mock-001",
                        "term": "обшивка",
                        "normalized_term": "обшивка",
                        "context": "Конструкция корпуса",
                        "source": "Правила РС",
                        "created_at": "2025-12-01T08:00:00Z",
                    }
                ],
                "meta": {"total": 1, "page": 1, "page_size": 50},
            }

        if endpoint.startswith("/terminology/") and method == "GET":
            term_id = endpoint.split("/")[-1]
            return {
                "data": {
                    "term_id": term_id,
                    "term": "обшивка",
                    "normalized_term": "обшивка",
                    "context": "Конструкция корпуса",
                    "source": "Правила РС",
                    "created_at": "2025-12-01T08:00:00Z",
                }
            }

        if endpoint == "/terminology" and method == "POST":
            request_data = kwargs.get("json", {})
            return {
                "data": {
                    "term_id": "t-mock-new",
                    "term": request_data.get("term", ""),
                    "normalized_term": request_data.get("normalized_term", ""),
                    "context": request_data.get("context", ""),
                    "source": request_data.get("source", ""),
                    "created_at": "2026-05-05T10:00:00Z",
                }
            }

        if endpoint.startswith("/terminology/") and method == "DELETE":
            return {
                "data": {
                    "term_id": endpoint.split("/")[-1],
                    "deleted": True,
                    "deleted_at": "2026-05-05T10:30:00Z",
                }
            }

        if endpoint == "/terminology/normalize" and method == "POST":
            request_data = kwargs.get("json", {})
            return {
                "data": {
                    "original": request_data.get("term", ""),
                    "normalized": request_data.get("term", "").lower(),
                    "found": True,
                }
            }

        # --- Registry Documents ---
        if endpoint == "/documents" and method == "GET":
            return {
                "data": [
                    {
                        "doc_id": 1,
                        "title": "Правила РС часть I",
                        "doc_number": "РС-001-2023",
                        "classifier_code": "01",
                        "classifier_name": "Судостроение",
                        "status": "active",
                        "source": "Российский морской регистр",
                        "notes": "",
                        "created_at": "2025-12-01T08:00:00Z",
                        "updated_at": "2025-12-01T08:00:00Z",
                    }
                ],
                "meta": {"total": 1, "page": 1, "page_size": 50},
            }

        if endpoint.startswith("/documents/") and method == "GET":
            doc_id = endpoint.split("/")[-1]
            return {
                "data": {
                    "doc_id": int(doc_id) if doc_id.isdigit() else 1,
                    "title": "Правила РС часть I",
                    "doc_number": "РС-001-2023",
                    "classifier_code": "01",
                    "classifier_name": "Судостроение",
                    "status": "active",
                    "source": "Российский морской регистр",
                    "notes": "",
                    "created_at": "2025-12-01T08:00:00Z",
                    "updated_at": "2025-12-01T08:00:00Z",
                }
            }

        if endpoint == "/documents" and method == "POST":
            request_data = kwargs.get("json", {})
            return {
                "data": {
                    "doc_id": 999,
                    "title": request_data.get("title", ""),
                    "doc_number": request_data.get("doc_number", ""),
                    "classifier_code": request_data.get("classifier_code", ""),
                    "status": request_data.get("status", "draft"),
                    "source": request_data.get("source", ""),
                    "notes": request_data.get("notes", ""),
                    "created_at": "2026-05-05T10:00:00Z",
                    "updated_at": "2026-05-05T10:00:00Z",
                }
            }

        if endpoint.startswith("/documents/") and method == "DELETE":
            return {
                "data": {
                    "doc_id": endpoint.split("/")[-1],
                    "deleted": True,
                    "deleted_at": "2026-05-05T10:30:00Z",
                }
            }

        # --- Common ---
        if endpoint == "/common/statistics" and method == "GET":
            return {
                "data": {
                    "classifiers_total": 150,
                    "terminology_total": 1200,
                    "documents_total": 45,
                    "documents_by_status": {
                        "draft": 5,
                        "active": 30,
                        "obsolete": 8,
                        "need_to_buy": 1,
                        "searching": 1,
                    },
                }
            }

        if endpoint == "/common/enums" and method == "GET":
            return {
                "data": {
                    "doc_type": [
                        "normative",
                        "archival_scan",
                        "drawing",
                        "specification",
                    ],
                    "jurisdiction": ["RF", "international"],
                    "language": ["ru", "en"],
                    "document_status": [
                        "draft",
                        "active",
                        "obsolete",
                        "need_to_buy",
                        "searching",
                    ],
                    "context": ["construction", "materials", "welding", "pipeline"],
                    "file_document_type": ["pdf", "png", "jpg", "tiff"],
                    "file_document_status": [
                        "queued",
                        "processing",
                        "completed",
                        "failed",
                    ],
                    "check_result_status": ["ok", "warning", "error"],
                    "match_status": [
                        "match",
                        "possible_discrepancy",
                        "not_found_in_project",
                        "not_found_in_norm",
                        "insufficient_data",
                    ],
                    "ocr_engine": ["paddleocr", "tesseract"],
                    "chat_status": ["active", "archived"],
                }
            }

        return default_mock

    # --- Classifiers ---

    async def list_classifiers(
        self,
        page: int = 1,
        page_size: int = 50,
        doc_type: Optional[str] = None,
        parent_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List classifier nodes (flat)."""
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if doc_type:
            params["doc_type"] = doc_type
        if parent_code:
            params["parent_code"] = parent_code
        return await self.call(
            "GET",
            "/classifiers",
            mock_response={
                "data": [],
                "meta": {"total": 0, "page": 1, "page_size": 50},
            },
            params=params,
        )

    async def get_classifier_tree(
        self, root_code: Optional[str] = None, max_depth: int = 5
    ) -> Dict[str, Any]:
        """Get classifier tree (hierarchical)."""
        params: Dict[str, Any] = {}
        if root_code:
            params["root_code"] = root_code
        params["max_depth"] = max_depth
        return await self.call(
            "GET",
            "/classifiers/tree",
            mock_response={
                "data": [],
                "meta": {"total": 0, "max_depth_reached": max_depth},
            },
            params=params,
        )

    async def get_classifier(self, code: str) -> Dict[str, Any]:
        """Get a single classifier node."""
        return await self.call(
            "GET", f"/classifiers/{code}", mock_response={"data": {}}
        )

    async def create_classifier(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a classifier node."""
        return await self.call(
            "POST", "/classifiers", mock_response={"data": {}}, json=data
        )

    async def update_classifier(
        self, code: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a classifier node."""
        return await self.call(
            "PUT", f"/classifiers/{code}", mock_response={"data": {}}, json=data
        )

    async def patch_classifier(self, code: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Partially update a classifier node."""
        return await self.call(
            "PATCH", f"/classifiers/{code}", mock_response={"data": {}}, json=data
        )

    async def delete_classifier(self, code: str) -> Dict[str, Any]:
        """Delete a classifier node."""
        return await self.call(
            "DELETE", f"/classifiers/{code}", mock_response={"data": {}}
        )

    async def import_classifiers(self, nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Import classifier nodes in bulk."""
        return await self.call(
            "POST",
            "/classifiers/import",
            mock_response={"data": {"inserted": 0, "updated": 0, "errors": []}},
            json={"nodes": nodes},
        )

    # --- Terminology ---

    async def list_terminology(
        self, page: int = 1, page_size: int = 50, search: Optional[str] = None
    ) -> Dict[str, Any]:
        """List terminology entries."""
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if search:
            params["search"] = search
        return await self.call(
            "GET",
            "/terminology",
            mock_response={
                "data": [],
                "meta": {"total": 0, "page": 1, "page_size": 50},
            },
            params=params,
        )

    async def get_term(self, term_id: str) -> Dict[str, Any]:
        """Get a terminology entry."""
        return await self.call(
            "GET", f"/terminology/{term_id}", mock_response={"data": {}}
        )

    async def create_term(
        self,
        term: str,
        normalized_term: Optional[str] = None,
        context: Optional[str] = None,
        source: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a terminology entry."""
        body = {"term": term}
        if normalized_term:
            body["normalized_term"] = normalized_term
        if context:
            body["context"] = context
        if source:
            body["source"] = source
        return await self.call(
            "POST", "/terminology", mock_response={"data": {}}, json=body
        )

    async def update_term(self, term_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a terminology entry."""
        return await self.call(
            "PUT", f"/terminology/{term_id}", mock_response={"data": {}}, json=data
        )

    async def delete_term(self, term_id: str) -> Dict[str, Any]:
        """Delete a terminology entry."""
        return await self.call(
            "DELETE", f"/terminology/{term_id}", mock_response={"data": {}}
        )

    async def normalize_term(self, term: str) -> Dict[str, Any]:
        """Find normalized form of a term."""
        return await self.call(
            "POST",
            "/terminology/normalize",
            mock_response={
                "data": {"original": term, "normalized": term.lower(), "found": True}
            },
            json={"term": term},
        )

    async def import_terms(self, terms: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Import terminology entries in bulk."""
        return await self.call(
            "POST",
            "/terminology/import",
            mock_response={"data": {"inserted": 0, "updated": 0, "errors": []}},
            json={"terms": terms},
        )

    # --- Registry Documents ---

    async def list_registry_documents(
        self,
        page: int = 1,
        page_size: int = 50,
        classifier_code: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List registry documents."""
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if classifier_code:
            params["classifier_code"] = classifier_code
        if status:
            params["status"] = status
        if search:
            params["search"] = search
        return await self.call(
            "GET",
            "/documents",
            mock_response={
                "data": [],
                "meta": {"total": 0, "page": 1, "page_size": 50},
            },
            params=params,
        )

    async def get_registry_document(self, doc_id: str) -> Dict[str, Any]:
        """Get a registry document."""
        return await self.call(
            "GET", f"/documents/{doc_id}", mock_response={"data": {}}
        )

    async def create_registry_document(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a registry document."""
        return await self.call(
            "POST", "/documents", mock_response={"data": {}}, json=data
        )

    async def update_registry_document(
        self, doc_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a registry document."""
        return await self.call(
            "PUT", f"/documents/{doc_id}", mock_response={"data": {}}, json=data
        )

    async def update_registry_document_status(
        self, doc_id: str, status: str
    ) -> Dict[str, Any]:
        """Update registry document status."""
        return await self.call(
            "PATCH",
            f"/documents/{doc_id}/status",
            mock_response={"data": {}},
            json={"status": status},
        )

    async def delete_registry_document(self, doc_id: str) -> Dict[str, Any]:
        """Delete a registry document."""
        return await self.call(
            "DELETE", f"/documents/{doc_id}", mock_response={"data": {}}
        )

    async def export_registry_documents(
        self, format: str = "xlsx", classifier_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Export registry documents."""
        params: Dict[str, Any] = {"format": format}
        if classifier_code:
            params["classifier_code"] = classifier_code
        return await self.call(
            "GET",
            "/documents/export",
            mock_response={"data": {"url": "/exports/registry/documents.xlsx"}},
            params=params,
        )

    async def import_registry_documents(
        self, documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Import registry documents in bulk."""
        return await self.call(
            "POST",
            "/documents/import",
            mock_response={"data": {"inserted": 0, "updated": 0, "errors": []}},
            json={"documents": documents},
        )

    # --- Common ---

    async def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return await self.call("GET", "/common/statistics", mock_response={"data": {}})

    async def get_enums(self) -> Dict[str, Any]:
        """Get valid enum values."""
        return await self.call("GET", "/common/enums", mock_response={"data": {}})
