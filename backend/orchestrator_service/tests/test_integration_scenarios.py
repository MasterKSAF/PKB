"""
Integration scenario tests — end-to-end pipeline flows.

Tests complete business scenarios matching the pipeline documentation:
  - Pipeline 1: Upload → Preview → Decide → Status → Approve
  - Pipeline 2: Status indexation → indexed
  - Pipeline 3: Search + Ask
  - Validation chain: Compare → Result → Batch → Checks → Export
  - Version management: Upload version → List versions
  - Cross-pipeline scenario: Full Pipeline 1 → 2 → 3
"""

from datetime import datetime

from fastapi.testclient import TestClient


class TestPipeline1FormationScenario:
    """End-to-end Pipeline 1: document formation flow."""

    def test_full_upload_to_approve_flow(self, client: TestClient, auth_header: dict):
        """Upload → List → Get → Status → Approve."""
        # 1. Upload document
        upload_resp = client.post(
            "/api/v1/documents/",
            files={"file": ("test.pdf", b"%PDF-1.4 test", "application/pdf")},
            data={
                "source_type": "GOST",
                "title": "Тестовый документ",
                "doc_code": "ГОСТ 1234-56",
            },
            headers=auth_header,
        )
        assert upload_resp.status_code == 202
        upload_data = upload_resp.json()
        assert upload_data["status"] == "uploaded"
        task_id = upload_data["task_id"]
        file_hash = upload_data["file_hash_sha256"]

        # 2. List documents to verify it appears
        list_resp = client.get("/api/v1/documents/", headers=auth_header)
        assert list_resp.status_code == 200
        list_data = list_resp.json()
        assert "items" in list_data
        assert "summary" in list_data
        assert "meta" in list_data

        # 3. Start preview
        preview_resp = client.post(
            f"/api/v1/documents/tasks/{task_id}/preview",
            headers=auth_header,
        )
        assert preview_resp.status_code == 202
        preview_data = preview_resp.json()
        assert preview_data["status"] == "previewing"
        assert "estimated_completion" in preview_data

        # 4. Get preview status (via task)
        preview_status_resp = client.get(
            f"/api/v1/documents/tasks/{task_id}/preview/status",
            params={"longpoll": 10},
            headers=auth_header,
        )
        assert preview_status_resp.status_code == 200
        ps_data = preview_status_resp.json()
        assert "status" in ps_data
        assert "preview" in ps_data
        assert "duplicates" in ps_data
        assert "decision_required" in ps_data

        # Preview metadata checks
        preview = ps_data["preview"]
        assert "doc_code" in preview
        assert "title" in preview
        assert "document_type" in preview
        assert "year" in preview

        # 5. Decide to proceed
        decide_resp = client.post(
            f"/api/v1/documents/tasks/{task_id}/decide",
            json={"action": "proceed", "comment": "Одобрено"},
            headers=auth_header,
        )
        assert decide_resp.status_code == 202
        decide_data = decide_resp.json()
        assert "document_id" in decide_data
        assert decide_data["status"] == "proceeding"
        doc_id = decide_data["document_id"]

        # 6. Get document details
        get_resp = client.get(f"/api/v1/documents/{doc_id}", headers=auth_header)
        assert get_resp.status_code == 200
        get_data = get_resp.json()
        assert get_data["document_id"] == doc_id

        # 7. Get document status (FSM-aware)
        status_resp = client.get(
            f"/api/v1/documents/{doc_id}/status",
            params={"longpoll": 15},
            headers=auth_header,
        )
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        assert "status" in status_data
        assert "steps" in status_data
        steps = status_data["steps"]
        assert "pipeline" in steps
        assert "formation" in steps["pipeline"]
        assert "indexation" in steps["pipeline"]

        # 8. Approve document
        approve_resp = client.post(
            f"/api/v1/documents/{doc_id}/approve",
            json={"force": True, "comment": "Утверждаю"},
            headers=auth_header,
        )
        assert approve_resp.status_code == 202
        approve_data = approve_resp.json()
        assert approve_data["status"] == "approved"
        assert "promotion_task_id" in approve_data
        assert "approved_by" in approve_data
        assert "approved_at" in approve_data

        # 9. Get document history
        history_resp = client.get(
            f"/api/v1/documents/{doc_id}/history",
            headers=auth_header,
        )
        assert history_resp.status_code == 200
        history_data = history_resp.json()
        assert "history" in history_data
        assert "meta" in history_data

        # 10. Verify file hash consistency
        assert "file_hash_sha256" in upload_data

    def test_duplicate_detection_flow(self, client: TestClient, auth_header: dict):
        """Upload → Preview → Stop as duplicate."""
        upload_resp = client.post(
            "/api/v1/documents/",
            files={"file": ("dup.pdf", b"duplicate content", "application/pdf")},
            data={"source_type": "GOST", "title": "Дубликат"},
            headers=auth_header,
        )
        task_id = upload_resp.json()["task_id"]

        # Simulate browse to decide: stop_duplicate
        decide_resp = client.post(
            f"/api/v1/documents/tasks/{task_id}/decide",
            json={"action": "stop_duplicate", "comment": "Это дубликат"},
            headers=auth_header,
        )
        assert decide_resp.status_code == 202
        data = decide_resp.json()
        assert data["status"] == "stopped"
        assert "дубликат" in data["message"].lower() or \
               "duplicate" in data["message"].lower()


class TestPipeline2IndexationScenario:
    """End-to-end Pipeline 2: document indexation flow."""

    def test_status_shows_indexation_step(self, client: TestClient, auth_header: dict):
        """Status response should contain indexation pipeline info."""
        status_resp = client.get(
            "/api/v1/documents/doc-8a3f2b/status",
            headers=auth_header,
        )
        assert status_resp.status_code == 200
        data = status_resp.json()
        pipeline = data["steps"]["pipeline"]
        assert "indexation" in pipeline
        indexation = pipeline["indexation"]
        assert "status" in indexation
        assert "rag_indexing" in indexation

    def test_indexation_status_values(self, client: TestClient, auth_header: dict):
        """Indexation status should be valid FSM state."""
        status_resp = client.get(
            "/api/v1/documents/doc-8a3f2b/status",
            headers=auth_header,
        )
        data = status_resp.json()
        rag = data["steps"]["pipeline"]["indexation"]["rag_indexing"]
        valid_states = {"pending", "in_progress", "completed", "failed"}
        assert rag["status"] in valid_states


class TestPipeline3SearchScenario:
    """End-to-end Pipeline 3: search and ask flow."""

    def test_search_and_ask_full_flow(self, client: TestClient, auth_header: dict):
        """Search → Ask with complete response validation."""
        # 1. POST search
        search_resp = client.post(
            "/api/v1/documents/search",
            json={
                "query": "толщина обшивки ледового пояса",
                "top_k": 5,
                "filters": {"document_type": ["normative"]},
            },
            headers=auth_header,
        )
        assert search_resp.status_code == 200
        search_data = search_resp.json()
        assert search_data["query"] == "толщина обшивки ледового пояса"
        assert "items" in search_data
        assert "total_found" in search_data
        assert "processing_time_ms" in search_data

        # Verify search results structure
        for item in search_data["items"]:
            for field in ("fragment_id", "document_id", "document_title",
                          "document_type", "page", "fragment", "score"):
                assert field in item, f"Missing field: {field}"
            assert 0.0 <= item["score"] <= 1.0

        # 2. GET quick search
        quick_resp = client.get(
            "/api/v1/documents/search",
            params={"q": "ледовый пояс", "limit": 3},
            headers=auth_header,
        )
        assert quick_resp.status_code == 200

        # 3. Ask question
        ask_resp = client.post(
            "/api/v1/ask",
            json={
                "question": "Какая минимальная толщина обшивки для ледового пояса?",
                "document_ids": ["doc-norm-001"],
                "options": {"temperature": 0.3},
            },
            headers=auth_header,
        )
        assert ask_resp.status_code == 200
        ask_data = ask_resp.json()
        assert ask_data["question"] == "Какая минимальная толщина обшивки для ледового пояса?"
        assert "answer" in ask_data
        assert len(ask_data["answer"]) > 0
        assert "sources" in ask_data
        assert "model_used" in ask_data
        assert "processing_time_ms" in ask_data

        # Verify sources structure
        for src in ask_data["sources"]:
            for field in ("document_id", "document_title", "page_number",
                          "fragment_id", "text", "score"):
                assert field in src, f"Missing field: {field}"


class TestValidationScenario:
    """End-to-end validation flow."""

    def test_full_validation_flow(self, client: TestClient, auth_header: dict):
        """Compare → Get Result → Batch → Checks → Export."""
        # 1. Start comparison
        compare_resp = client.post(
            "/api/v1/validate/compare",
            json={
                "normative_query": "Толщина обшивки ≥ 12 мм",
                "project_document_id": "doc-proj-001",
            },
            headers=auth_header,
        )
        assert compare_resp.status_code == 202
        compare_data = compare_resp.json()
        assert "comparison_id" in compare_data
        assert compare_data["status"] == "processing"
        comparison_id = compare_data["comparison_id"]

        # 2. Get comparison result
        result_resp = client.get(
            f"/api/v1/validate/compare/{comparison_id}",
            headers=auth_header,
        )
        assert result_resp.status_code == 200
        result_data = result_resp.json()
        assert result_data["comparison_id"] == comparison_id
        assert "normative_block" in result_data
        assert "project_block" in result_data
        assert "match_status" in result_data
        assert "details" in result_data
        assert "sources" in result_data
        assert "disclaimer" in result_data
        assert "processing_time_ms" in result_data

        # 3. Batch compare
        batch_resp = client.post(
            "/api/v1/validate/compare/batch",
            json=[
                {"normative": "Толщина ≥ 12 мм", "project": "Толщина = 14 мм"},
                {"normative": "Длина ≥ 5 м", "project": "Длина = 4.5 м"},
            ],
            headers=auth_header,
        )
        assert batch_resp.status_code == 200
        batch_data = batch_resp.json()
        assert "batch_id" in batch_data
        assert "comparisons" in batch_data
        assert "total_pairs" in batch_data
        assert batch_data["total_pairs"] == 2

        # 4. Start check run
        check_resp = client.post(
            "/api/v1/validate/checks",
            headers=auth_header,
        )
        assert check_resp.status_code == 201
        check_data = check_resp.json()
        check_run_id = check_data["check_run_id"]
        assert "summary" in check_data
        assert "items" in check_data

        # 5. Get check run status
        status_resp = client.get(
            f"/api/v1/validate/checks/{check_run_id}",
            headers=auth_header,
        )
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        assert status_data["check_run_id"] == check_run_id
        assert "progress_percent" in status_data
        assert "created_at" in status_data
        assert "updated_at" in status_data

        # 6. Export check run
        export_resp = client.get(
            f"/api/v1/validate/checks/{check_run_id}/export",
            headers=auth_header,
        )
        assert export_resp.status_code == 200
        export_data = export_resp.json()
        assert export_data["check_run_id"] == check_run_id
        assert "export_url" in export_data
        assert "format" in export_data


class TestVersionManagementScenario:
    """End-to-end version management flow."""

    def test_upload_and_list_versions(self, client: TestClient, auth_header: dict):
        """Upload original → Upload new version → List versions."""
        doc_id = "doc-8a3f2b"  # Known document from mock data

        # 1. Upload new version
        version_resp = client.post(
            f"/api/v1/documents/{doc_id}/versions",
            files={"file": ("v2.pdf", b"%PDF-1.4 version 2", "application/pdf")},
            headers=auth_header,
        )
        assert version_resp.status_code == 202
        version_data = version_resp.json()
        assert version_data["document_id"] == doc_id
        assert version_data["status"] == "uploaded"
        assert "version_id" in version_data
        assert "task_id" in version_data
        assert "file_hash_sha256" in version_data

        # 2. List versions
        list_resp = client.get(
            f"/api/v1/documents/{doc_id}/versions",
            headers=auth_header,
        )
        assert list_resp.status_code == 200
        list_data = list_resp.json()
        assert list_data["document_id"] == doc_id
        assert "versions" in list_data
        assert "meta" in list_data
        assert list_data["meta"]["total"] > 0

        # Verify version item structure
        for ver in list_data["versions"]:
            for field in ("version_id", "version_number", "format_code",
                          "format_label", "file_key", "file_hash_sha256",
                          "size_bytes", "uploaded_at", "uploaded_by"):
                assert field in ver, f"Missing field: {field}"


class TestCrossPipelineIntegration:
    """Cross-pipeline integration — Pipeline 1 → 2 → 3."""

    def test_document_lifecycle_status_transitions(self, client: TestClient, auth_header: dict):
        """Verify status response reflects all pipeline stages."""
        doc_id = "doc-8a3f2b"

        # Get status — verifies both Pipeline 1 and Pipeline 2
        status_resp = client.get(
            f"/api/v1/documents/{doc_id}/status",
            params={"longpoll": 15},
            headers=auth_header,
        )
        assert status_resp.status_code == 200
        data = status_resp.json()

        pipeline = data["steps"]["pipeline"]
        formation = pipeline["formation"]
        indexation = pipeline["indexation"]

        # Pipeline 1 checks
        assert formation["status"] in ("completed", "in_progress", "pending", "failed")
        if "preview" in formation:
            assert "ocr_parser" in formation["preview"]
            assert "converter_validator" in formation["preview"]
            assert "decision" in formation["preview"]

        # Pipeline 2 checks
        assert indexation["status"] in ("completed", "in_progress", "pending", "failed")
        assert indexation["rag_indexing"]["status"] in ("pending", "in_progress", "completed", "failed")

    def test_soft_delete_affects_document(self, client: TestClient, auth_header: dict):
        """Delete document and verify response."""
        doc_id = "doc-8a3f2b"

        delete_resp = client.delete(
            f"/api/v1/documents/{doc_id}",
            headers=auth_header,
        )
        assert delete_resp.status_code == 200
        delete_data = delete_resp.json()
        assert delete_data["document_id"] == doc_id
        assert "deleted_at" in delete_data

    def test_reprocess_document_flow(self, client: TestClient, auth_header: dict):
        """Reprocess document with different modes."""
        doc_id = "doc-8a3f2b"

        # Test all supported reprocess modes
        for mode in ("full", "ocr_only", "validation_only", "reindex", "chunking_only"):
            resp = client.post(
                f"/api/v1/documents/{doc_id}/reprocess",
                json={"mode": mode},
                headers=auth_header,
            )
            assert resp.status_code == 202
            data = resp.json()
            assert data["mode"] == mode
            assert data["status"] == "reprocessing_queued"
            assert "task_id" in data

    def test_document_errors_and_parameters(self, client: TestClient, auth_header: dict):
        """Get document processing errors and extracted parameters."""
        doc_id = "doc-8a3f2b"

        # Errors with filter
        err_resp = client.get(
            f"/api/v1/documents/{doc_id}/errors",
            params={"stage": "ocr", "severity": "warning"},
            headers=auth_header,
        )
        assert err_resp.status_code == 200
        err_data = err_resp.json()
        assert "errors" in err_data
        assert "meta" in err_data

        # Parameters
        param_resp = client.get(
            f"/api/v1/documents/{doc_id}/parameters",
            headers=auth_header,
        )
        assert param_resp.status_code == 200
        param_data = param_resp.json()
        assert param_data["document_id"] == doc_id
        assert "parameters" in param_data
        assert "total" in param_data
        assert param_data["total"] >= 0


class TestMonitorAndHealthScenario:
    """Monitor and health check flow."""

    def test_health_and_metrics_flow(self, client: TestClient, auth_header: dict):
        """Health check → Monitor metrics."""
        # 1. Health check (public)
        health_resp = client.get("/api/v1/system/health")
        assert health_resp.status_code == 200
        health_data = health_resp.json()
        assert health_data["status"] == "ok"
        assert "services" in health_data
        assert "database" in health_data
        assert "search_index" in health_data
        assert "ocr_queue" in health_data
        assert "storage" in health_data

        # Verify all required services are present
        expected_services = {"auth", "rag_builder", "rag_search", "ocr", "validation", "integration"}
        assert set(health_data["services"].keys()) == expected_services

        # 2. Monitor metrics (protected)
        metrics_resp = client.get(
            "/api/v1/monitor/metrics",
            headers=auth_header,
        )
        assert metrics_resp.status_code == 200
        metrics_data = metrics_resp.json()
        assert "control_metrics" in metrics_data
        assert "answer_metrics" in metrics_data
        assert "logs" in metrics_data

        # Verify metrics ranges
        cm = metrics_data["control_metrics"]
        assert 0.0 <= cm["ocr_quality"] <= 1.0
        assert 0.0 <= cm["retrieval_quality"] <= 1.0
        assert 0.0 <= cm["answers_with_sources"] <= 1.0
        assert cm["avg_latency_ms"] > 0

        am = metrics_data["answer_metrics"]
        assert 0.0 <= am["useful_rate"] <= 1.0
        assert am["rated_answers"] >= 0
        assert am["flagged_for_review"] >= 0
        assert am["open_questions"] >= 0


class TestDocumentPagesScenario:
    """Document pages access flow."""

    def test_full_pages_scenario(self, client: TestClient, auth_header: dict):
        """List pages → View page → Get page text → Preview."""
        doc_id = "doc-8a3f2b"

        # 1. List pages
        pages_resp = client.get(
            f"/api/v1/documents/{doc_id}/pages",
            headers=auth_header,
        )
        assert pages_resp.status_code == 200
        pages_data = pages_resp.json()
        assert "pages" in pages_data
        assert "pages_total" in pages_data
        assert "meta" in pages_data

        # 2. Get page view
        view_resp = client.get(
            f"/api/v1/documents/{doc_id}/pages/1",
            headers=auth_header,
        )
        assert view_resp.status_code == 200

        # 3. Get page text
        text_resp = client.get(
            f"/api/v1/documents/{doc_id}/pages/1/text",
            headers=auth_header,
        )
        assert text_resp.status_code == 200
        text_data = text_resp.json()
        assert "blocks" in text_data
        assert "width" in text_data
        assert "height" in text_data
        for block in text_data["blocks"]:
            assert "number" in block
            assert "type" in block
            assert "bbox" in block
            assert "content" in block

        # 4. Get page preview
        preview_resp = client.get(
            f"/api/v1/documents/{doc_id}/pages/1/preview",
            headers=auth_header,
        )
        assert preview_resp.status_code == 200
        preview_data = preview_resp.json()
        assert "image_url" in preview_data
        assert "blocks" in preview_data
        assert "text_layer" in preview_data


class TestQueueScenario:
    """Document processing queue flow."""

    def test_queue_with_pagination(self, client: TestClient, auth_header: dict):
        """Get queue with pagination parameters."""
        # Default queue
        queue_resp = client.get(
            "/api/v1/documents/queue",
            headers=auth_header,
        )
        assert queue_resp.status_code == 200
        queue_data = queue_resp.json()
        assert "queue" in queue_data
        assert "meta" in queue_data

        # With pagination
        queue_resp = client.get(
            "/api/v1/documents/queue",
            params={"page": 1, "page_size": 10},
            headers=auth_header,
        )
        assert queue_resp.status_code == 200

        # Verify queue item structure
        if queue_data["queue"]:
            item = queue_data["queue"][0]
            for field in ("document_id", "title", "status", "progress_percent",
                          "current_step", "steps", "user_id", "created_at"):
                assert field in item, f"Missing field: {field}"
