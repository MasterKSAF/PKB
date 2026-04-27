import axios from 'axios';
import {
  MOCK_CHECKS,
  MOCK_CHATS,
  MOCK_CITATIONS,
  MOCK_DOCUMENTS,
  MOCK_HISTORY,
  MOCK_METRICS,
  type ChatMessage,
} from './mockData';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 5000,
});

function needsClarification(query: string) {
  const normalized = query.toLowerCase();
  const broadWords = ['толщина', 'материал', 'соответствует', 'проверить', 'норма'];
  const hasBroadIntent = broadWords.some((word) => normalized.includes(word));
  const hasContext =
    normalized.includes('проект') ||
    normalized.includes('21900') ||
    normalized.includes('версия') ||
    normalized.includes('раздел') ||
    normalized.includes('чертеж');

  return hasBroadIntent && !hasContext;
}

export const chatApi = {
  send: async (query: string): Promise<ChatMessage> => {
    if (needsClarification(query)) {
      await new Promise((resolve) => setTimeout(resolve, 500));

      return {
        id: Math.random().toString(36).slice(2),
        role: 'assistant',
        content:
          'Нужно уточнить контекст, чтобы не дать слишком общий ответ. Укажите проект, тип конструкции, версию НСИ или конкретный документ, по которому нужно выполнить проверку.',
        status: 'needs_clarification',
        limitation:
          'По ТЗ ассистент не должен угадывать недостающие параметры. Сначала уточняем контекст, затем ищем источники и формируем ответ.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
    }

    try {
      const response = await apiClient.post('/chat', { q: query });
      return response.data;
    } catch {
      await new Promise((resolve) => setTimeout(resolve, 1200));

      return {
        id: Math.random().toString(36).slice(2),
        role: 'assistant',
        content:
          `1. По запросу "${query}" найдены релевантные фрагменты в базе знаний.\n` +
          '2. Ответ сформирован только по документам, которые попали в подборку источников.\n' +
          '3. Перед применением результата нужно открыть источник и сверить страницу, раздел и редакцию документа.',
        status: 'answered',
        citations: MOCK_CITATIONS,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
    }
  },
};

export const searchApi = {
  query: async (q: string) => {
    try {
      const response = await apiClient.get('/search', { params: { q } });
      return response.data;
    } catch {
      return MOCK_DOCUMENTS.map((doc) => ({
        ...doc,
        relevance: 0.92,
        fragment:
          'Найденный фрагмент в документе: описание технических требований и связанных параметров проекта.',
      }));
    }
  },
};

export const documentsApi = {
  list: async () => {
    try {
      const response = await apiClient.get('/documents');
      return response.data;
    } catch {
      return MOCK_DOCUMENTS;
    }
  },
};

export const checksApi = {
  get: async () => {
    try {
      const response = await apiClient.get('/checks');
      return response.data;
    } catch {
      return MOCK_CHECKS;
    }
  },
};

export const historyApi = {
  get: async () => {
    try {
      const response = await apiClient.get('/history');
      return response.data;
    } catch {
      return MOCK_HISTORY;
    }
  },
};

export const metricsApi = {
  get: async () => {
    try {
      const response = await apiClient.get('/metrics');
      return response.data;
    } catch {
      return MOCK_METRICS;
    }
  },
};

export const feedbackApi = {
  send: async (payload: { useful: boolean; comment: string }) => {
    try {
      await apiClient.post('/feedback', payload);
      return { ok: true };
    } catch {
      return { ok: true, demo: true };
    }
  },
};

export const initialChatMessages = MOCK_CHATS;
