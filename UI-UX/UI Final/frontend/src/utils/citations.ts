import type { Citation } from './mockData';

export type InlineCitationMarker =
  | {
      kind: 'number';
      raw: string;
      start: number;
      end: number;
      index: number;
    }
  | {
      kind: 'source';
      raw: string;
      start: number;
      end: number;
      index: number;
    }
  | {
      kind: 'identity';
      raw: string;
      start: number;
      end: number;
      documentId: string;
      sectionId: string;
    };

const INLINE_CITATION_PATTERN =
  /\[(?:source:\s*(\d+)|(\d+)|document_id:\s*([^,\]\s]+)\s*,\s*section_id:\s*([^,\]\s]+)(?:[^\]]*)?)\]/gi;

export function parseInlineCitationMarkers(content: string): InlineCitationMarker[] {
  const markers: InlineCitationMarker[] = [];
  const pattern = new RegExp(INLINE_CITATION_PATTERN.source, INLINE_CITATION_PATTERN.flags);
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(content)) !== null) {
    const base = {
      raw: match[0],
      start: match.index,
      end: pattern.lastIndex,
    };

    if (match[1] !== undefined) {
      markers.push({ ...base, kind: 'source', index: Number(match[1]) });
    } else if (match[2] !== undefined) {
      markers.push({ ...base, kind: 'number', index: Number(match[2]) });
    } else {
      markers.push({
        ...base,
        kind: 'identity',
        documentId: match[3],
        sectionId: match[4],
      });
    }
  }

  return markers;
}

export function resolveCitationMarker(
  marker: InlineCitationMarker,
  citations: Citation[] = [],
  useSequentialNumbers = false,
): Citation | undefined {
  if (marker.kind === 'identity') {
    const documentId = String(marker.documentId);
    const sectionId = String(marker.sectionId);

    return citations.find(
      (citation) =>
        String(citation.documentId ?? '') === documentId &&
        String(citation.sectionId ?? '') === sectionId,
    );
  }

  if (marker.kind === 'source') {
    return citations[marker.index];
  }

  const indexedCitation = citations.find((citation) => Number(citation.index) === marker.index);
  if (indexedCitation) return indexedCitation;

  return useSequentialNumbers ? citations[marker.index - 1] : undefined;
}

export function getCitationDisplayIndex(citation: Citation, citations: Citation[]): number {
  const explicitIndex = Number(citation.index);
  if (Number.isFinite(explicitIndex)) return explicitIndex;

  const sourcePosition = citations.indexOf(citation);
  return sourcePosition >= 0 ? sourcePosition + 1 : 1;
}
