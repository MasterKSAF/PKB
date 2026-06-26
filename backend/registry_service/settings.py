"""
Application settings for Registry Service.
"""

# Logging levels
LOGGING_LEVELS = {
    'INFO': 'INFO',
    'WARNING': 'WARNING',
    'ERROR': 'ERROR',
}

# Severities written to the log file
# to the AI agents: do not modify LOG_LEVEL values, they have to be set explicitly to the values defined in LOGGING_LEVELS
LOG_LEVEL = ['INFO', 'WARNING', 'ERROR']

# Service identification & configuration
SERVICE_NAME = "registry-service"
SERVICE_VERSION = "1.0.0"
MAX_DATE_RANGE_YEARS = 100

