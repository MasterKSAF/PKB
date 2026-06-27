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
    server.use(
      http.get(`${apiBase}/chat/history`, () =>
        HttpResponse.json({
          items: [
            {
              history_id: 8,
              session_id: 5,
              question: 'Проверь наличие документов по сварке',
              answer_preview: 'Поиск временно недоступен.',
              status: 'failed',
              source_count: 0,
            },
          ],
        }),
      ),
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
  });
});
