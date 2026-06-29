import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { apiClient, documentsApi, draftsApi, historyApi } from '../http';
import { useUIStore } from '../../store/uiStore';

const apiBase = 'http://127.0.0.1:8080/api/v1';

const server = setupServer();

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

beforeEach(() => {
  useUIStore.setState(useUIStore.getInitialState(), true);
  useUIStore.getState().setWorkMode('prod');
});

describe('live Gateway response contracts', () => {
  it('keeps failed chat history records failed', async () => {
    const failedSession = {
      session_id: 5,
      title: 'Рабочий чат',
      status: 'failed',
      messages: [
        {
          message_id: 80,
          role: 'user',
          content: 'Проверь наличие документов по сварке',
          created_at: '2026-06-29T10:00:00Z',
        },
        {
          message_id: 81,
          role: 'assistant',
          content: 'Поиск временно недоступен.',
          status: 'failed',
          created_at: '2026-06-29T10:00:01Z',
          sources: [],
        },
      ],
    };

    server.use(
      http.get(`${apiBase}/chat/sessions`, () =>
        HttpResponse.json({
          sessions: [failedSession],
        }),
      ),
      http.get(`${apiBase}/chat/sessions/5`, () => HttpResponse.json(failedSession)),
    );

    const history = await historyApi.get();

    expect(history).toHaveLength(1);
    expect(history[0].status).toBe('failed');
    expect(history[0].sources).toBe(0);
  });

  it('reads document pages from the documented data.pages envelope', async () => {
    server.use(
      http.get(`${apiBase}/documents/4/pages`, () =>
        HttpResponse.json({
          data: {
            document_id: 4,
            pages_total: 1,
            pages: [{ page: 1, has_text_layer: true }],
          },
        }),
      ),
    );

    await expect(documentsApi.pages('4')).resolves.toEqual([{ page: 1, has_text_layer: true }]);
  });

  it('lets the browser generate a valid multipart boundary for draft upload', async () => {
    const post = vi.spyOn(apiClient, 'post').mockResolvedValue({
      data: { draft_id: 21, status: 'uploaded' },
    });

    const response = await draftsApi.create(new File(['test'], 'document.pdf', { type: 'application/pdf' }));
    const [, form, config] = post.mock.calls[0];

    expect(response.draft_id).toBe(21);
    expect(form).toBeInstanceOf(FormData);
    expect((form as FormData).get('file')).toBeInstanceOf(File);
    expect(config?.headers).not.toHaveProperty('Content-Type');
    expect(config?.timeout).toBe(120_000);
  });
});
