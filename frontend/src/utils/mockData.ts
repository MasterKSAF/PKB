export interface Citation {
  id: string;
  document: string;
  section: string;
  page: number;
  text: string;
  version: string;
  confidence?: number;
}

export type AnswerStatus = 'answered' | 'needs_clarification' | 'insufficient_data' | 'source_conflict';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  timestamp: string;
  status?: AnswerStatus;
  limitation?: string;
}

export interface Document {
  id: string;
  name: string;
  type: string;
  version: string;
  source: string;
  ocrStatus: 'Завершено' | 'В обработке' | 'Ошибка';
  indexStatus: 'Индексировано' | 'Ожидание';
  updatedAt: string;
}

export interface ParameterCheck {
  id: string;
  parameter: string;
  projectDocument: string;
  projectValue: string;
  projectPage: number;
  projectSection: string;
  projectText: string;
  projectVersion: string;
  nsiDocument: string;
  nsiRequirement: string;
  nsiPage: number;
  nsiSection: string;
  nsiText: string;
  nsiVersion: string;
  comment: string;
  status: 'OK' | 'WARNING' | 'ERROR';
}

export interface SystemMetrics {
  ocrQuality: number;
  retrievalQuality: number;
  answersWithSources: number;
  manualReviewQueue: number;
  searchLatency: number;
}

export interface EngineerRatingMetrics {
  ratedAnswers: number;
  usefulRate: number;
  flaggedForReview: number;
  unresolvedAfterReview: number;
  commonSignals: Array<{
    label: string;
    count: number;
  }>;
}

export interface QueryHistoryItem {
  id: string;
  user: string;
  query: string;
  answer: string;
  sources: number;
  status: AnswerStatus;
  createdAt: string;
}

export const MOCK_CITATIONS: Citation[] = [
  {
    id: 'c1',
    document: 'ГОСТ Р 54382-2011',
    section: 'Раздел 4.2.3 Конструктивные требования',
    page: 12,
    text: 'Толщина стального листа для корпусных конструкций должна определяться по расчетной нагрузке и применяемой группе конструкции. Для несущих элементов требуется отдельная проверка по актуальной версии нормы.',
    version: '2023.1',
    confidence: 0.91,
  },
  {
    id: 'c2',
    document: 'Спецификация КБ-122-04',
    section: 'Глава 2. Системы охлаждения',
    page: 45,
    text: 'Допустимый уровень вибрации насосного агрегата не должен превышать 0.8 мм/с в рабочем диапазоне частот.',
    version: 'Изд. 4',
    confidence: 0.86,
  },
];

export const MOCK_CHATS: ChatMessage[] = [
  {
    id: '1',
    role: 'user',
    content: 'Какие требования к толщине стальных листов для корпуса судна согласно ГОСТ?',
    timestamp: '10:00',
  },
  {
    id: '2',
    role: 'assistant',
    content:
      '1. Минимальная толщина листа не должна определяться отдельно от проекта, типа конструкции и расчетной нагрузки.\n' +
      '2. Для несущих элементов корпуса требуется сверка с актуальной редакцией нормы.\n' +
      '3. Перед применением значения нужно проверить проектную спецификацию и страницу первоисточника.',
    timestamp: '10:01',
    status: 'answered',
    limitation: 'Это не инженерный вердикт. Финальное решение принимает сотрудник после проверки первоисточника.',
    citations: [MOCK_CITATIONS[0], MOCK_CITATIONS[1]],
  },
];

export const MOCK_DOCUMENTS: Document[] = [
  {
    id: 'd1',
    name: 'Чертеж СЕВ-22-01',
    type: 'DWG',
    version: 'v1.4',
    source: 'Архив КБ',
    ocrStatus: 'Завершено',
    indexStatus: 'Индексировано',
    updatedAt: '2026-04-20',
  },
  {
    id: 'd2',
    name: 'Регламент сборки судна',
    type: 'PDF',
    version: 'v2.0',
    source: 'Нормативная база',
    ocrStatus: 'Завершено',
    indexStatus: 'Индексировано',
    updatedAt: '2026-04-18',
  },
  {
    id: 'd3',
    name: 'Отчет об испытаниях 2024',
    type: 'PDF',
    version: 'v1.1',
    source: 'Входящие',
    ocrStatus: 'В обработке',
    indexStatus: 'Ожидание',
    updatedAt: '2026-04-21',
  },
  {
    id: 'd4',
    name: 'Спецификация материала',
    type: 'XLSX',
    version: 'v3.2',
    source: 'Закупки',
    ocrStatus: 'Завершено',
    indexStatus: 'Индексировано',
    updatedAt: '2026-04-19',
  },
];

export const MOCK_CHECKS: ParameterCheck[] = [
  {
    id: 'ch1',
    parameter: 'Максимальная скорость судна',
    projectDocument: 'Проект 223-М. Основные характеристики',
    projectValue: '32 узла',
    projectPage: 18,
    projectSection: 'Раздел 5. Основные характеристики',
    projectText: 'В проектной документации для судна зафиксирована максимальная скорость 32 узла в штатном режиме эксплуатации.',
    projectVersion: 'Проект v2.4',
    nsiDocument: 'ТЗ-2024. Эксплуатационные требования',
    nsiRequirement: 'Не менее 32 узлов',
    nsiPage: 12,
    nsiSection: 'Раздел 3. Эксплуатационные требования',
    nsiText: 'Максимальная скорость судна должна составлять не менее 32 узлов при штатном режиме эксплуатации.',
    nsiVersion: 'Изд. 2',
    comment: 'Параметр проекта соответствует требованию НСИ.',
    status: 'OK',
  },
  {
    id: 'ch2',
    parameter: 'Масса двигателя',
    projectDocument: 'Чертеж силовой установки. Лист сборки',
    projectValue: '4750 кг',
    projectPage: 22,
    projectSection: 'Примечания по агрегату',
    projectText: 'На чертеже сборки для узла указана масса двигателя 4750 кг.',
    projectVersion: 'Проект v1.9',
    nsiDocument: 'Каталог двигателя. Базовая комплектация',
    nsiRequirement: '4500 кг',
    nsiPage: 7,
    nsiSection: 'Таблица масс',
    nsiText: 'Масса двигателя в базовой комплектации составляет 4500 кг.',
    nsiVersion: 'Изд. 4',
    comment: 'Значение в проекте выше нормативно-справочного значения. Требуется проверка версии агрегата или состава комплектации.',
    status: 'ERROR',
  },
  {
    id: 'ch3',
    parameter: 'Марка стали для конструктивного элемента',
    projectDocument: 'Заявка на материал для корпуса',
    projectValue: '10ХСНД-2',
    projectPage: 4,
    projectSection: 'Примечание к заявке',
    projectText: 'В заявке на закупку материала указано обозначение 10ХСНД-2.',
    projectVersion: 'Заявка 04-2026',
    nsiDocument: 'ГОСТ-123. Допустимые марки стали',
    nsiRequirement: '10ХСНД',
    nsiPage: 33,
    nsiSection: 'Таблица 7. Марки стали',
    nsiText: 'Для данной группы конструкций указана сталь 10ХСНД.',
    nsiVersion: '2024.3',
    comment: 'Обозначение в проекте похоже на модификацию марки. Нужна инженерная проверка эквивалентности.',
    status: 'WARNING',
  },
];

export const MOCK_HISTORY: QueryHistoryItem[] = [
  {
    id: 'h1',
    user: 'Инженер-конструктор',
    query: 'Какая минимальная толщина листа для корпуса?',
    answer: 'Требуется уточнить проект, тип конструкции и актуальную редакцию нормы.',
    sources: 1,
    status: 'needs_clarification',
    createdAt: '2026-04-23 10:14',
  },
  {
    id: 'h2',
    user: 'Инженер-конструктор',
    query: 'Найди регламент сварки Т-образных швов',
    answer: 'Найдены разделы регламента и проектной спецификации, требуется проверка версии.',
    sources: 2,
    status: 'answered',
    createdAt: '2026-04-23 10:21',
  },
  {
    id: 'h3',
    user: 'Администратор знаний',
    query: 'Какие документы не прошли OCR?',
    answer: 'Найден один документ в обработке и один ожидающий индексации.',
    sources: 0,
    status: 'answered',
    createdAt: '2026-04-23 10:38',
  },
];

export const MOCK_METRICS: SystemMetrics = {
  ocrQuality: 98.4,
  retrievalQuality: 92.1,
  answersWithSources: 95.8,
  manualReviewQueue: 12,
  searchLatency: 1.4,
};

export const MOCK_ENGINEER_RATINGS: EngineerRatingMetrics = {
  ratedAnswers: 128,
  usefulRate: 84,
  flaggedForReview: 7,
  unresolvedAfterReview: 3,
  commonSignals: [
    { label: 'нужна сверка версии', count: 9 },
    { label: 'не хватает точной страницы', count: 6 },
    { label: 'ответ слишком общий', count: 4 },
  ],
};
