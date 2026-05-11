"""
Integration Service Client with mock mode support.
"""
from typing import Any, Dict, List, Optional
from app.services.base_client import ServiceClient
from app.core.config import settings


class IntegrationServiceClient(ServiceClient):
    """Client for Integration Service."""
    
    def __init__(self):
        super().__init__(
            service_name="integration",
            service_url=settings.services.INTEGRATION_SERVICE_URL,
            mock_mode=settings.services.INTEGRATION_SERVICE_MOCK
        )
    
    async def _generate_mock(
        self,
        method: str,
        endpoint: str,
        default_mock: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate mock integration responses."""
        if endpoint == "/files/upload" and method == "POST":
            return {
                "file_id": "file-mock-xyz",
                "filename": "uploaded_file.pdf",
                "size": 1048576,
                "mime_type": "application/pdf",
                "url": "/files/file-mock-xyz",
                "uploaded_at": "2026-05-05T10:00:00Z"
            }
        
        if endpoint.startswith("/files/") and endpoint.endswith("/info") and method == "GET":
            file_id = endpoint.split("/")[-2]
            return {
                "file_id": file_id,
                "filename": "document.pdf",
                "size": 2048576,
                "mime_type": "application/pdf",
                "url": f"/files/{file_id}",
                "uploaded_at": "2026-05-05T10:00:00Z"
            }
        
        if endpoint.startswith("/files/") and method == "GET":
            # Binary file response - return metadata for mock
            return {
                "file_id": endpoint.split("/")[-1],
                "content_type": "application/pdf",
                "size": 2048576,
                "is_binary": True
            }
        
        if endpoint.startswith("/files/") and method == "DELETE":
            return {
                "file_id": endpoint.split("/")[-1],
                "deleted_at": "2026-05-05T10:30:00Z"
            }
        
        if endpoint == "/meridian/export" and method == "POST":
            request_data = kwargs.get("json", {})
            return {
                "export_id": "exp-mock-001",
                "external_id": "mer-mock-12345",
                "status": "sent",
                "sent_at": "2026-05-05T12:00:00Z",
                "response_message": "Принято"
            }
        
        if endpoint == "/external/status" and method == "GET":
            return {
                "systems": [
                    {
                        "api_name": "meridian",
                        "status": "available",
                        "last_checked": "2026-05-05T12:05:00Z",
                        "latency_ms": 230
                    }
                ]
            }
        
        return default_mock
    
    async def upload_file(
        self,
        file_data: bytes,
        filename: str,
        related_document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload file to storage."""
        files = {"file": (filename, file_data)}
        data = {}
        if related_document_id:
            data["related_document_id"] = related_document_id
        
        return await self.call(
            "POST",
            "/files/upload",
            mock_response={},
            files=files,
            data=data
        )
    
    async def get_file(self, file_id: str) -> Dict[str, Any]:
        """Get file metadata or binary content."""
        return await self.call(
            "GET",
            f"/files/{file_id}",
            mock_response={}
        )
    
    async def delete_file(self, file_id: str) -> Dict[str, Any]:
        """Delete file from storage."""
        return await self.call(
            "DELETE",
            f"/files/{file_id}",
            mock_response={}
        )
    
    async def export_to_meridian(
        self,
        document_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export data to Meridian system."""
        return await self.call(
            "POST",
            "/meridian/export",
            mock_response={},
            json={"document_id": document_id, "data": data}
        )
    
    async def get_external_systems_status(self) -> Dict[str, Any]:
        """Get status of external systems."""
        return await self.call(
            "GET",
            "/external/status",
            mock_response={"systems": []}
        )
