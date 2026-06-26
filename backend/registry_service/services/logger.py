import datetime
from typing import Optional

from settings import LOG_LEVEL

LOG_FILE = 'service.log'


import os
from typing import Any

def log_payload(payload: Optional[Any] = None) -> Optional[Any]:
    """
    Return request payload for log data, or None if missing or empty.
    Masks PII fields specified in LOG_PII_FIELDS (defaults to password, access_token, refresh_token) with '***'.
    """
    if not payload:
        return None

    # Get PII fields to mask
    pii_fields_raw = os.getenv('LOG_PII_FIELDS', 'password, access_token, refresh_token')
    pii_fields = {f.strip() for f in pii_fields_raw.split(',') if f.strip()}

    def mask_value(val: Any) -> Any:
        if isinstance(val, dict):
            return {k: ('***' if k in pii_fields else mask_value(v)) for k, v in val.items()}
        elif isinstance(val, list):
            return [mask_value(item) for item in val]
        return val

    try:
        # Handle Pydantic models if passed directly
        if hasattr(payload, 'model_dump'):
            payload = payload.model_dump()
        elif hasattr(payload, 'dict'):
            payload = payload.dict()

        masked = mask_value(payload)
        return masked or None
    except Exception:
        return None



from contextvars import ContextVar
import json
from settings import SERVICE_NAME

# ContextVars for request tracing
request_id_var = ContextVar("request_id", default=None)
trace_id_var = ContextVar("trace_id", default=None)
span_id_var = ContextVar("span_id", default=None)
draft_id_var = ContextVar("draft_id", default=None)
document_id_var = ContextVar("document_id", default=None)
version_id_var = ContextVar("version_id", default=None)
user_id_var = ContextVar("user_id", default=None)

# Extra HTTP Context (optional, set by middleware)
path_var = ContextVar("path", default=None)
method_var = ContextVar("method", default=None)
status_var = ContextVar("status", default=None)
latency_ms_var = ContextVar("latency_ms", default=None)


def log_event(severity: str, endpoint: str, query_string: Optional[str] = None, data: Optional[dict] = None, error: Optional[str] = None) -> None:
    """
    Logs an event for monitoring purposes.

    Args:
        severity (str): Log level (e.g., 'INFO', 'WARNING', 'ERROR').
        endpoint (str): The API endpoint or service function name.
        query_string (str, optional): The query string or parameters. Defaults to None.
        data (dict, optional): The request or relevant data as a dictionary. Defaults to None.
        error (str, optional): Error message if any.
    """
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if data is not None and not isinstance(data, dict):
        raise TypeError("data argument must be a dictionary or None")

    # Read correlation IDs
    req_id = request_id_var.get()
    tr_id = trace_id_var.get()
    sp_id = span_id_var.get()
    dr_id = draft_id_var.get()
    doc_id = document_id_var.get()
    ver_id = version_id_var.get()
    usr_id = user_id_var.get()

    # Read HTTP context if set by middleware, else fallback to log_event args
    current_path = path_var.get() or endpoint
    current_method = method_var.get()
    current_status = status_var.get()
    current_latency = latency_ms_var.get()

    # Build extra payload
    extra_dict = {}
    if query_string:
        extra_dict['query_string'] = query_string
    if data:
        extra_dict['data'] = data
    if dr_id:
        extra_dict['draft_id'] = dr_id
    if doc_id:
        extra_dict['document_id'] = doc_id
    if ver_id:
        extra_dict['version_id'] = ver_id

    log_entry = {
        'timestamp': timestamp,
        'level': severity.upper(),
        'service': SERVICE_NAME.replace("-service", ""),  # "registry"
        'trace_id': tr_id,
        'span_id': sp_id,
        'request_id': req_id,
        'user_id': usr_id,
        'path': current_path,
        'method': current_method,
        'status': current_status,
        'latency_ms': current_latency,
        'message': error if error else f"Event at {endpoint}",
        'error_code': None,
        'error_message': error,
        'extra': extra_dict
    }

    # Write to file only if severity level is configured in LOG_LEVEL
    if severity in LOG_LEVEL:
        def log_serializer(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            return str(obj)

        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{json.dumps(log_entry, default=log_serializer, ensure_ascii=False)}\n")


