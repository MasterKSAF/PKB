import { describe, expect, it } from 'vitest';
import { mapGatewayDraftRecordToUi } from '../KnowledgeProcessing';

describe('Gateway draft mapper', () => {
  it('uses document_key when the backend does not return a title or filename', () => {
    const draft = mapGatewayDraftRecordToUi({
      draft_id: 17,
      document_key: 'sha256-document-key',
      status: 'uploaded',
    });

    expect(draft.id).toBe('17');
    expect(draft.gatewayDraftId).toBe('17');
    expect(draft.title).toBe('sha256-document-key');
    expect(draft.fileName).toBe('sha256-document-key');
  });

  it('uses file_key before falling back to the numeric id', () => {
    const draft = mapGatewayDraftRecordToUi({
      id: 18,
      file_key: 'drafts/18/source.pdf',
      status: 'uploaded',
    });

    expect(draft.gatewayDraftId).toBe('18');
    expect(draft.title).toBe('drafts/18/source.pdf');
  });

  it('normalizes backend metadata values to strings before they reach form fields', () => {
    const draft = mapGatewayDraftRecordToUi({
      draft_id: 19,
      title: 'ГОСТ 123',
      status: 'review_required',
      year: 2026,
      mks_oks_code: 47.02,
      okstu_code: 12000,
      issuing_body: 42,
      valid_from: 20260101,
      preview_metadata: {
        year: 2025,
      },
    });

    expect(draft.year).toBe('2026');
    expect(draft.mksOksCode).toBe('47.02');
    expect(draft.okstuCode).toBe('12000');
    expect(draft.issuingBody).toBe('42');
    expect(draft.validFrom).toBe('20260101');
  });
});
