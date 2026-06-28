import { describe, expect, it } from 'vitest';
import type { Citation } from '../mockData';
import {
  getCitationDisplayIndex,
  parseInlineCitationMarkers,
  resolveCitationMarker,
} from '../citations';

const citations: Citation[] = [
  {
    id: 'source-1',
    index: 1,
    documentId: '42',
    sectionId: '7',
    document: 'ГОСТ 42',
    section: '3.1',
    page: 5,
    text: 'Первый фрагмент',
    version: '1',
  },
  {
    id: 'source-2',
    index: 2,
    documentId: '42',
    sectionId: '8',
    document: 'ГОСТ 42',
    section: '3.2',
    page: 6,
    text: 'Второй фрагмент',
    version: '1',
  },
];

describe('inline citation markers', () => {
  it('parses documented, transitional and legacy numeric formats', () => {
    const markers = parseInlineCitationMarkers(
      'Текст [document_id:42, section_id:7 §3.1, стр. 5], затем [source:1] и [2].',
    );

    expect(markers).toMatchObject([
      { kind: 'identity', documentId: '42', sectionId: '7' },
      { kind: 'source', index: 1 },
      { kind: 'number', index: 2 },
    ]);
  });

  it('resolves document and section identifiers without confusing sections of one document', () => {
    const [marker] = parseInlineCitationMarkers('[document_id:42, section_id:8]');

    expect(resolveCitationMarker(marker, citations)?.id).toBe('source-2');
  });

  it('resolves source markers as zero-based positions and numeric markers by citation index', () => {
    const [sourceMarker, numericMarker] = parseInlineCitationMarkers('[source:0] [2]');

    expect(resolveCitationMarker(sourceMarker, citations)?.id).toBe('source-1');
    expect(resolveCitationMarker(numericMarker, citations)?.id).toBe('source-2');
  });

  it('uses the structured citation index for the visible link number', () => {
    expect(getCitationDisplayIndex(citations[1], citations)).toBe(2);
  });
});
