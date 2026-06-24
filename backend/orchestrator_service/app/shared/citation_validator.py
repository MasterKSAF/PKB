"""
Citation format validator for LLM responses (P3S-4).

Validates that citations in LLM responses follow the [source:N] format.
Supports retry mechanism with fallback.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Regex for [source:N] format — matches [source:1], [source:42], etc.
SOURCE_PATTERN = re.compile(r'\[source:(\d+)\]')

# Fallback: citation ranges like [source:1-3]
SOURCE_RANGE_PATTERN = re.compile(r'\[source:(\d+)-(\d+)\]')

# Catch-all: any citation-like pattern regardless of case — for detection
CITATION_LIKE_PATTERN = re.compile(r'\[[Ss][Oo][Uu][Rr][Cc][Ee]:[^\]]*\]')


def validate_citation_format(text: Optional[str]) -> bool:
    """Check that all citation markers in text follow [source:N] format.
    
    Returns True if all citations are valid, False otherwise.
    """
    if not text:
        return True

    # Find ALL citation-like patterns (case-insensitive)
    all_citations = CITATION_LIKE_PATTERN.findall(text)
    if not all_citations:
        return True

    # Each citation must match the canonical lowercase format
    for citation in all_citations:
        if SOURCE_PATTERN.match(citation):
            # Valid single [source:N]
            idx_str = SOURCE_PATTERN.match(citation).group(1)
            try:
                idx = int(idx_str)
                if idx < 0:
                    logger.warning(f"Citation index out of range: {idx}")
                    return False
            except ValueError:
                return False
        elif SOURCE_RANGE_PATTERN.match(citation):
            # Valid range [source:N-M]
            pass
        else:
            # Invalid format
            logger.warning(f"Invalid citation format: {citation}")
            return False
    
    return True


def extract_source_indices(text: str) -> list[int]:
    """Extract all source indices from citation markers.
    
    Returns sorted list of unique source indices.
    """
    indices: set[int] = set()
    
    # Single indices
    for match in SOURCE_PATTERN.finditer(text):
        indices.add(int(match.group(1)))
    
    # Ranges
    for match in SOURCE_RANGE_PATTERN.finditer(text):
        start, end = int(match.group(1)), int(match.group(2))
        indices.update(range(start, end + 1))
    
    return sorted(indices)


def fix_citation_format(text: str) -> str:
    """Attempt to fix common citation format issues.
    
    - [source: N] → [source:N]
    - [Source:N] → [source:N]
    - [source: N, M] → [source:N], [source:M]
    """
    if not text:
        return text
    
    # Fix: [source: N] → [source:N] (space after colon)
    text = re.sub(r'\[source:\s+(\d+)\]', r'[source:\1]', text)
    
    # Fix: [Source:N], [SOURCE:N] → [source:N] (case)
    text = re.sub(r'\[[Ss][Oo][Uu][Rr][Cc][Ee]:(\d+)\]', r'[source:\1]', text)
    
    # Fix: [source:N M] → [source:N], [source:M] (space instead of comma)
    text = re.sub(r'\[source:(\d+)\s+(\d+)\]', r'[source:\1], [source:\2]', text)
    
    return text


def validate_with_retry(
    text: str,
    max_retries: int = 2,
) -> tuple[bool, str, bool]:
    """Validate citation format with retry + fallback.
    
    Args:
        text: The LLM response text to validate.
        max_retries: Maximum number of fix attempts (default: 2).
    
    Returns:
        Tuple of (is_valid, processed_text, was_fixed).
    """
    if not text:
        return True, text, False
    
    current_text = text
    was_fixed = False
    
    for attempt in range(max_retries + 1):
        if validate_citation_format(current_text):
            return True, current_text, was_fixed
        
        # Try to fix
        fixed = fix_citation_format(current_text)
        if fixed != current_text:
            current_text = fixed
            was_fixed = True
            continue
        
        # Cannot fix further — fallback
        break
    
    # Fallback: strip invalid citations
    cleaned = re.sub(r'\[source:[^\]]*\]', '', current_text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    logger.warning(
        f"Citation validation failed after {max_retries} retries, "
        f"invalid citations stripped"
    )
    
    return False, cleaned, True
