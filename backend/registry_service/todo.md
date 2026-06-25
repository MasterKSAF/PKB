# TODO

- [x] Update `settings.py` with service configuration (name, version, date range limit).
- [x] Update `logger.py` with `contextvars` for tracing correlation IDs and logging enrichment.
- [x] Update `main.py` with request tracing middleware and global exception handlers for `HTTPException`, `RequestValidationError`, and generic `Exception`.
- [x] Update `routes.py` health check (`GET /health`) with DB ping, service name, and version fields.
- [x] Update `routes.py` document listing (`GET /registry/documents`) with date validation checks.
- [x] Add unit tests in `tests/test_common.py` for health check, validation formatting, date range checks, and correlation logging.
- [x] Run the test suite and verify all tests pass.
