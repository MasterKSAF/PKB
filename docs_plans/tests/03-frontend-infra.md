# Frontend — инфраструктура тестов

**Директория:** `UI-UX/UI Final/frontend/`

Требуется донастройка `package.json` и `vite.config.ts` для поддержки тестирования.

---

## 1. Добавить devDependencies в `package.json`

```json
"devDependencies": {
  "vitest": "^3.0.0",
  "@testing-library/react": "^16.0.0",
  "@testing-library/jest-dom": "^6.0.0",
  "@testing-library/user-event": "^14.0.0",
  "jsdom": "^25.0.0",
  "msw": "^2.0.0"
}
```

---

## 2. Добавить секцию `test` в `vite.config.ts`

```ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  // ... существующий конфиг
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    css: true,
  },
});
```

---

## 3. Создать `src/test/setup.ts` (~40 строк)

```ts
import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

afterEach(() => {
  cleanup();
});

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});
```

---

## 4. Создать `src/test/mocks/handlers.ts` (~100 строк)

MSW handlers для всех API:

```ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  // Auth
  http.post('/api/v1/auth/token', () => HttpResponse.json({
    access_token: 'test-token',
    refresh_token: 'test-refresh',
    token_type: 'bearer',
    expires_in: 3600,
  })),
  
  // Health
  http.get('/api/v1/system/health', () => HttpResponse.json({
    status: 'ok', version: '1.2.0', services: {}, timestamp: '...',
  })),

  // Chat sessions
  http.get('/api/v1/chat/sessions', () => HttpResponse.json({
    sessions: [{ id: 1, topic: 'Test', messages: [] }],
    meta: { total: 1, page: 1, page_size: 50 },
  })),

  // Documents
  http.get('/api/v1/documents', () => HttpResponse.json({
    items: [], summary: { total: 0 },
    meta: { total: 0, page: 1, page_size: 50 },
  })),

  // Drafts
  http.post('/api/v1/drafts', () => HttpResponse.json({
    draft_id: 1, task_id: 'task-1', status: 'uploaded',
  }, { status: 202 })),

  http.get('/api/v1/drafts', () => HttpResponse.json({
    items: [], meta: { total: 0, page: 1, page_size: 50 },
  })),

  // Registry
  http.get('/api/v1/registry/classifiers', () => HttpResponse.json({
    data: [], meta: { total: 0, page: 1, page_size: 50 },
  })),

  // Metrics
  http.get('/api/v1/monitor/metrics', () => HttpResponse.json({
    control: {}, answers: {}, logs: [],
  })),

  // Admin
  http.get('/api/v1/admin/users', () => HttpResponse.json({
    users: [], meta: { total: 0, page: 1, page_size: 50 },
  })),
  
  http.get('/api/v1/admin/audit', () => HttpResponse.json({
    events: [], meta: { total: 0, page: 1, page_size: 50 },
  })),

  // Fallback для всех остальных запросов
  http.all('*', () => HttpResponse.json({ error: 'not found' }, { status: 404 })),
];
```
