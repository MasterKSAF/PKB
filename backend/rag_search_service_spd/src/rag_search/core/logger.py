# src/rag_search/core/logger.py

import logging

if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

logger = logging.getLogger("rag_search")
logger.setLevel(logging.INFO)
