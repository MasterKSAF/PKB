import { describe, expect, it } from 'vitest';
import { getUserFacingApiError } from '../errors';

describe('getUserFacingApiError', () => {
  it('hides technical Axios messages for server errors', () => {
    expect(
      getUserFacingApiError({
        message: 'Request failed with status code 500',
        response: { status: 500, data: 'Internal Server Error' },
      }),
    ).toBe('Сервер не смог выполнить операцию. Данные сохранены, повторите попытку позже.');
  });

  it('shows duplicate conflicts in user terms', () => {
    expect(
      getUserFacingApiError({
        response: {
          status: 409,
          data: {
            detail: {
              error: {
                code: 'DUPLICATE_DOCUMENT',
                message: 'Document already exists',
              },
            },
          },
        },
      }),
    ).toBe('Такой документ уже загружен или находится в обработке.');
  });

  it('keeps a request id for support', () => {
    expect(
      getUserFacingApiError({
        response: {
          status: 500,
          data: {
            error: {
              code: 'INTERNAL_ERROR',
              message: 'Внутренняя ошибка сервера',
              details: { request_id: 'req-123' },
            },
          },
        },
      }),
    ).toContain('Код обращения: req-123.');
  });
});
