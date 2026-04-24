"""Usage reports and HTML rendering.

Important: ingestion runs are executed both via API and via offline scripts.
The API repository is in-memory (MVP), so for cross-process visibility we also
support building usage reports from the filesystem event logs written under
`ARTIFACT_ROOT`.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC
from datetime import datetime
from pathlib import Path

from jinja2 import Template

from neuroassistant.api.schemas import RunResponse
from neuroassistant.api.schemas import UsageReport
from neuroassistant.repositories import InMemoryRepository
from neuroassistant.storage.artifacts import LocalArtifactStorage


def build_usage_report(repo: InMemoryRepository, latest_n: int = 20) -> UsageReport:
    documents = repo.list_documents()
    runs: list[RunResponse] = []
    for doc in documents:
        for run in repo.list_runs_for_document(doc.document_id):
            runs.append(RunResponse(**run.model_dump()))

    docs_by_status = Counter([d.status.value for d in documents])
    runs_by_status = Counter([r.status.value for r in runs])

    latest = sorted(runs, key=lambda r: r.created_at, reverse=True)[:latest_n]

    return UsageReport(
        documents_total=len(documents),
        runs_total=len(runs),
        documents_by_status=dict(docs_by_status),
        runs_by_status=dict(runs_by_status),
        latest_ingestions=latest,
    )


def build_usage_report_from_artifacts(
    storage: LocalArtifactStorage,
    latest_n: int = 20,
) -> UsageReport:
    events = _load_all_events(storage.root())
    runs = _events_to_runs(events)

    docs_by_status: Counter[str] = Counter()
    for r in runs.values():
        docs_by_status[r.status.value] += 1
    runs_by_status = Counter([r.status.value for r in runs.values()])

    latest = sorted(
        runs.values(),
        key=lambda r: r.created_at,
        reverse=True,
    )[:latest_n]

    return UsageReport(
        documents_total=len({r.document_id for r in runs.values()}),
        runs_total=len(runs),
        documents_by_status=dict(docs_by_status),
        runs_by_status=dict(runs_by_status),
        latest_ingestions=latest,
    )


def render_usage_html(report: UsageReport) -> str:
    template = Template(
        """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Ingestion usage report</title>
    <style>
      body { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial; margin: 24px; }
      .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
      .card { border: 1px solid #e5e7eb; border-radius: 10px; padding: 16px; }
      table { width: 100%; border-collapse: collapse; }
      th, td { text-align: left; padding: 8px; border-bottom: 1px solid #f3f4f6; font-size: 14px; }
      .muted { color: #6b7280; }
      code { background: #f3f4f6; padding: 2px 6px; border-radius: 6px; }
    </style>
  </head>
  <body>
    <h2>Ingestion usage report</h2>
    <p class="muted">
      Documents: <b>{{ report.documents_total }}</b>,
      Runs: <b>{{ report.runs_total }}</b>
    </p>

    <div class="grid">
      <div class="card">
        <h3>Documents by status</h3>
        <table>
          <thead><tr><th>Status</th><th>Count</th></tr></thead>
          <tbody>
          {% for status, count in report.documents_by_status.items() %}
            <tr><td><code>{{ status }}</code></td><td>{{ count }}</td></tr>
          {% endfor %}
          </tbody>
        </table>
      </div>

      <div class="card">
        <h3>Runs by status</h3>
        <table>
          <thead><tr><th>Status</th><th>Count</th></tr></thead>
          <tbody>
          {% for status, count in report.runs_by_status.items() %}
            <tr><td><code>{{ status }}</code></td><td>{{ count }}</td></tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
    </div>

    <div class="card" style="margin-top: 16px;">
      <h3>Latest ingestions</h3>
      <table>
        <thead>
          <tr>
            <th>Created</th>
            <th>Ingestion</th>
            <th>Document</th>
            <th>Status</th>
            <th>Errors</th>
          </tr>
        </thead>
        <tbody>
        {% for r in report.latest_ingestions %}
          <tr>
            <td class="muted">{{ r.created_at }}</td>
            <td><code>{{ r.ingestion_id }}</code></td>
            <td><code>{{ r.document_id }}</code></td>
            <td><code>{{ r.status }}</code></td>
            <td>{{ r.errors | length }}</td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
  </body>
</html>
"""
    )
    return template.render(report=report)


def _load_all_events(root: Path) -> list[dict]:
    if not root.exists():
        return []
    paths = list(root.glob("*/*/logs/events.jsonl"))
    out: list[dict] = []
    for path in paths:
        try:
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    out.append(json.loads(line))
        except OSError:
            continue
        except json.JSONDecodeError:
            continue
    return out


def _events_to_runs(events: list[dict]) -> dict[str, RunResponse]:
    # We model a RunResponse minimally from event logs so usage is non-empty
    # even when repository is empty (script-generated ingestions).
    by_ing: dict[str, list[dict]] = {}
    for e in events:
        ing = e.get("ingestion_id")
        if not ing:
            continue
        by_ing.setdefault(ing, []).append(e)

    runs: dict[str, RunResponse] = {}
    for ingestion_id, evs in by_ing.items():
        evs_sorted = sorted(
            evs,
            key=lambda x: x.get("timestamp") or "",
        )
        first = evs_sorted[0]
        document_id = first.get("document_id") or "unknown"
        created_at = _parse_ts(first.get("timestamp"))

        # Determine status: if any event failed -> failed; else succeeded at
        # preprocess -> completed; else use last stage status for best effort.
        failed = any(e.get("status") == "failed" for e in evs_sorted)
        if failed:
            status = "failed"
        else:
            status = "completed"

        errors = []
        for e in evs_sorted:
            err = e.get("error")
            if err:
                errors.append(err)

        runs[ingestion_id] = RunResponse(
            ingestion_id=ingestion_id,
            document_id=document_id,
            created_at=created_at,
            status=status,
            classification=None,
            errors=[],
            metrics={},
        )
    return runs


def _parse_ts(value: str | None) -> datetime:
    if not value:
        return datetime.now(UTC)
    try:
        # Examples contain 'Z' suffix
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.now(UTC)

