import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { apiClient, chatApi, documentsApi, draftsApi, historyApi, tasksApi } from '../http';
import { useUIStore } from '../../store/uiStore';

const apiBase = 'http://127.0.0.1:8080/api/v1';

const server = setupServer();

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => {
  vi.restoreAllMocks();
  server.resetHandlers();
});
afterAll(() => server.close());

beforeEach(() => {
  window.localStorage.clear();
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

  it('sends Authorization on draft preview pipeline requests', async () => {
    window.localStorage.setItem('pkb_gateway_access_token_v2', 'test-access-token');
    let authorization: string | null = null;

    server.use(
      http.post(`${apiBase}/drafts/21/preview`, ({ request }) => {
        authorization = request.headers.get('authorization');
        return HttpResponse.json({ task_id: 21, status: 'processing' }, { status: 202 });
      }),
    );

    await expect(draftsApi.startPreview('21')).resolves.toMatchObject({ task_id: 21 });
    expect(authorization).toBe('Bearer test-access-token');
  });

  it('omits nonnumeric project ids when creating chat sessions', async () => {
    const post = vi.spyOn(apiClient, 'post').mockResolvedValue({
      data: { session_id: 7, title: 'Новый чат' },
    });

    await chatApi.createSession('Новый чат', 'Рабочие диалоги');

    expect(post).toHaveBeenCalledWith('/chat/sessions', {
      title: 'Новый чат',
      document_ids: [],
    });
  });

  it('rejects local chat ids before updating Gateway sessions', async () => {
    const put = vi.spyOn(apiClient, 'put');

    await expect(chatApi.updateSession('chat-Рабочие диалоги-1782752390714', { title: 'Тест' })).rejects.toThrow(
      'Gateway session id is missing or not numeric.',
    );

    expect(put).not.toHaveBeenCalled();
  });

  it('does not create a Gateway chat session implicitly when sending a message', async () => {
    const post = vi.spyOn(apiClient, 'post');

    await expect(chatApi.send('проверка')).rejects.toThrow('Сначала создайте или выберите чат');

    expect(post).not.toHaveBeenCalled();
  });

  it('treats Query Service not_found as a final chat status', async () => {
    useUIStore.getState().setCurrentGatewaySessionId('12');

    server.use(
      http.post(`${apiBase}/chat/sessions/12/messages`, () => HttpResponse.json({ message_id: 91 })),
      http.get(`${apiBase}/chat/sessions/12/messages/91`, () =>
        HttpResponse.json({
          message_id: 91,
          status: 'not_found',
          message: 'По запросу ничего не найдено.',
        }),
      ),
    );

    await expect(chatApi.send('неизвестный запрос')).resolves.toMatchObject({
      status: 'failed',
      content: 'По запросу ничего не найдено.',
    });
  });

  it('keeps task converter errors visible in processing logs', async () => {
    server.use(
      http.get(`${apiBase}/tasks/27/status`, () =>
        HttpResponse.json({
          task_id: 27,
          draft_id: 11,
          status: 'failed',
          pipeline_stage: 'converter',
          progress_percent: 72,
          error_code: 'CONVERTER_ERROR',
          error_message: "Client error '422 Unprocessable Content' for url 'http://converter-validator:8086/api/v1/converter/convert'",
        }),
      ),
    );

    const logs = await tasksApi.status('27');

    expect(logs[0].event).toContain('CONVERTER_ERROR');
    expect(logs[0].event).toContain('422 Unprocessable Content');
  });

  it('maps task status detail for draft processing UI', async () => {
    server.use(
      http.get(`${apiBase}/tasks/28/status`, () =>
        HttpResponse.json({
          task_id: 28,
          draft_id: 12,
          status: 'active',
          pipeline_stage: 'preview',
          progress_percent: 65,
          steps: [
            { step_name: 'upload', service_name: 'orchestrator', status: 'completed' },
            { step_name: 'preview_ocr', service_name: 'ocr', status: 'running' },
          ],
        }),
      ),
    );

    await expect(tasksApi.detail('28')).resolves.toMatchObject({
      taskId: '28',
      draftId: '12',
      status: 'active',
      pipelineStage: 'preview',
      progressPercent: 65,
      steps: [
        { stepName: 'upload', serviceName: 'orchestrator', status: 'completed' },
        { stepName: 'preview_ocr', serviceName: 'ocr', status: 'running' },
      ],
    });
  });
});
