import axios from 'axios';
import {
  MOCK_CHECKS,
  MOCK_CHATS,
  MOCK_CITATIONS,
  MOCK_DOCUMENTS,
  MOCK_HISTORY,
  MOCK_KNOWLEDGE_SECTIONS,
  MOCK_METRICS,
  type ChatMessage,
} from './mockData';
import { useUIStore } from '../store/uiStore';

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

function shouldShowNoKnowledgeResult(query: string) {
  const normalized = query.toLowerCase();
  const noKnowledgeMarkers = [
    'ничего не найдено',
    'нет данных',
    'не найден',
    'несуществ',
  ];

  return noKnowledgeMarkers.some((marker) => normalized.includes(marker));
}

function shouldShowOutOfScopeResult(query: string) {
  const normalized = query.toLowerCase();
  const outOfScopeMarkers = ['погода', 'температура на улице', 'курс валют', 'который час', 'сколько времени', 'текущее время'];

  return outOfScopeMarkers.some((marker) => normalized.includes(marker));
}

function isDemoMode() {
  return useUIStore.getState().workMode === 'demo';
}

function backendUnavailableMessage(): ChatMessage {
  return {
    id: Math.random().toString(36).slice(2),
    role: 'assistant',
    content: 'Backend недоступен. Повторите запрос позже или переключитесь в demo-режим для просмотра демонстрационных сценариев.',
    status: 'backend_error',
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  };
}

function notFoundMessage(query: string): ChatMessage {
  return {
    id: Math.random().toString(36).slice(2),
    role: 'assistant',
    content: `В базе знаний не найдено подтвержденных фрагментов по запросу «${query}». Попробуйте уточнить формулировку, проект, раздел или документ.`,
    status: 'not_found',
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  };
}

function outOfScopeMessage(query: string): ChatMessage {
  return {
    id: Math.random().toString(36).slice(2),
    role: 'assistant',
    content: `Запрос «${query}» не относится к инженерным документам, НСИ или проектной проверке. Задайте вопрос в рамках базы знаний проекта, и система выполнит поиск по источникам.`,
    status: 'out_of_scope',
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  };
}

async function demoChatMessage(query: string): Promise<ChatMessage> {
  await new Promise((resolve) => setTimeout(resolve, 900));

  if (needsClarification(query)) {
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

  if (shouldShowOutOfScopeResult(query)) {
    return outOfScopeMessage(query);
  }

  if (shouldShowNoKnowledgeResult(query)) {
    return notFoundMessage(query);
  }

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

function demoSearchResults(q: string) {
  if (shouldShowNoKnowledgeResult(q) || shouldShowOutOfScopeResult(q)) {
    return [];
  }

  return MOCK_DOCUMENTS.map((doc, index) => ({
    ...doc,
    section: MOCK_KNOWLEDGE_SECTIONS[index % MOCK_KNOWLEDGE_SECTIONS.length].title,
    relevance: 0.92,
    fragment:
      'Найденный фрагмент в документе: описание технических требований и связанных параметров проекта.',
  }));
}

export const chatApi = {
  send: async (query: string): Promise<ChatMessage> => {
    const demoMode = isDemoMode();

    if (demoMode) {
      useUIStore.getState().setApiStatus('demo');
      return demoChatMessage(query);
    }

    try {
      const response = await apiClient.post('/chat', { q: query });
      useUIStore.getState().setApiStatus('online');
      return response.data;
    } catch {
      useUIStore.getState().setApiStatus(demoMode ? 'demo' : 'offline');

      if (!demoMode) {
        return backendUnavailableMessage();
      }

      return backendUnavailableMessage();
    }
  },
};

export const searchApi = {
  query: async (q: string) => {
    const demoMode = isDemoMode();

    if (demoMode) {
      useUIStore.getState().setApiStatus('demo');
      return demoSearchResults(q);
    }

    try {
      const response = await apiClient.get('/search', { params: { q } });
      useUIStore.getState().setApiStatus('online');
      return response.data;
    } catch {
      useUIStore.getState().setApiStatus(demoMode ? 'demo' : 'offline');

      throw new Error('Backend недоступен');
    }
  },
};

export const documentsApi = {
  list: async () => {
    if (isDemoMode()) return MOCK_DOCUMENTS;

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
    if (isDemoMode()) return MOCK_CHECKS;

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
    if (isDemoMode()) return MOCK_HISTORY;

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
    if (isDemoMode()) return MOCK_METRICS;

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
