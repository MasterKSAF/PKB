import datetime
from typing import Any, Optional

LOG_FILE = 'service.log'


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
    log_entry = {
        'timestamp': timestamp,
        'severity': severity,
        'endpoint': endpoint,
        'query_string': query_string,
        'data': data,
        'error': error
    }
    # Simple file append; in production, use structured logging or external monitoring
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{log_entry}\n")
