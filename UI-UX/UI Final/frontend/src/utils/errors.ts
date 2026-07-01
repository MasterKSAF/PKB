const firstText = (...values: unknown[]): string => {
  for (const value of values) {
    if (typeof value === 'string' && value.trim()) return value.trim();
  }
  return '';
};

const isTechnicalMessage = (message: string) =>
  !message ||
  /^request failed with status code \d+$/i.test(message) ||
  /^internal server error$/i.test(message) ||
  /^network error$/i.test(message);

export const getUserFacingApiError = (
  error: any,
  fallback = 'Не удалось выполнить операцию.',
): string => {
  const status = Number(error?.response?.status ?? 0);
  const payload = error?.response?.data;
  const detail = payload?.detail;
  const nestedError = detail?.error ?? payload?.error;
  const code = firstText(nestedError?.code, detail?.code, payload?.code, error?.code);
  const requestId = firstText(
    nestedError?.details?.request_id,
    detail?.request_id,
    payload?.request_id,
    payload?.details?.request_id,
  );
  const serverMessage = firstText(
    nestedError?.message,
    detail?.message,
    typeof detail === 'string' ? detail : '',
    payload?.message,
    typeof payload === 'string' ? payload : '',
    error?.message,
  );

  let message = serverMessage;

  if (code.includes('DUPLICATE')) {
    message = 'Такой документ уже загружен или находится в обработке.';
  } else if (status === 401) {
    message = 'Сессия истекла. Войдите в систему повторно.';
  } else if (status === 403) {
    message = 'У вас недостаточно прав для выполнения этой операции.';
  } else if (status === 404 && isTechnicalMessage(message)) {
    message = 'Запрошенный объект не найден. Обновите страницу и повторите попытку.';
  } else if (status === 409 && isTechnicalMessage(message)) {
    message = 'Операцию нельзя выполнить в текущем состоянии документа. Обновите данные и повторите попытку.';
  } else if (status === 422 && isTechnicalMessage(message)) {
    message = 'Сервер отклонил введённые данные. Проверьте заполненные поля.';
  } else if (status >= 500) {
    message = 'Сервер не смог выполнить операцию. Данные сохранены, повторите попытку позже.';
  } else if (!error?.response && error?.code === 'ECONNABORTED') {
    message = 'Сервер не ответил вовремя. Повторите попытку.';
  } else if (!error?.response && isTechnicalMessage(message)) {
    message = 'Нет связи с сервером. Проверьте подключение и повторите попытку.';
  } else if (isTechnicalMessage(message)) {
    message = fallback;
  }

  return requestId ? `${message} Код обращения: ${requestId}.` : message;
};
