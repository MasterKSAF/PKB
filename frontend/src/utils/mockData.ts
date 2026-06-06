export interface Citation {
  id: string;
  documentId?: string;
  document: string;
  section: string;
  page: number;
  text: string;
  version: string;
  confidence?: number;
  pagePreviewUrl?: string;
  documentUrl?: string;
  contentType?: string;
}

export type AnswerStatus =
  | 'answered'
  | 'needs_clarification'
  | 'insufficient_data'
  | 'source_conflict'
  | 'out_of_scope'
  | 'not_found'
  | 'backend_error';

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
  project: string;
  topic: string;
  session: string;
  query: string;
  answer: string;
  sources: number;
  status: AnswerStatus;
  createdAt: string;
  messages: ChatMessage[];
}

export interface AdminUser {
  id: string;
  name: string;
  position: string;
  login: string;
  role: 'Пользователь' | 'Администратор знаний' | 'Системный администратор';
  access: string;
  status: 'Активен' | 'Ожидает настройки' | 'Отключен';
  lastSeen: string;
}

export interface ProcessingLogItem {
  id: string;
  time: string;
  document: string;
  stage: 'Загрузка' | 'OCR' | 'Parsing' | 'Indexing' | 'Answer generation';
  event: string;
  retryStatus: 'Не требуется' | 'Запланирована' | 'Выполнена' | 'Ошибка';
  visibility: 'Инженер' | 'Администратор';
}

export interface KnowledgeSection {
  id: string;
  title: string;
  description: string;
  documents: number;
  updatedAt: string;
  status: 'Готово' | 'В обработке' | 'Нужна проверка';
}

export interface ProcessingQueueItem {
  id: string;
  document: string;
  stage: 'OCR' | 'Индексация' | 'Разбор таблиц';
  progress: number;
  status: 'в очереди' | 'в работе' | 'ошибка';
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

export const MOCK_CHAT_THREADS: Record<string, ChatMessage[]> = {
  'chat-hull': MOCK_CHATS,
  'chat-materials': [
    {
      id: 'materials-u1',
      role: 'user',
      content: 'Какие материалы нужно сверить перед применением в корпусных конструкциях?',
      timestamp: '10:08',
    },
    {
      id: 'materials-a1',
      role: 'assistant',
      content:
        '1. Перед применением нужно сверить марку стали с проектной спецификацией и действующей редакцией НСИ.\n' +
        '2. Для материалов с модификациями обозначения требуется отдельная инженерная проверка эквивалентности.\n' +
        '3. В карточке источника нужно открыть документ и страницу, где указана применяемость материала.',
      timestamp: '10:09',
      status: 'answered',
      citations: [MOCK_CITATIONS[0]],
    },
  ],
  'chat-pumps': [
    {
      id: 'pumps-u1',
      role: 'user',
      content: 'Проверь требования по насосным агрегатам для проекта 22220.',
      timestamp: '11:20',
    },
    {
      id: 'pumps-a1',
      role: 'assistant',
      content:
        '1. По насосным агрегатам найдены требования к вибрации и рабочему диапазону частот.\n' +
        '2. Перед применением нужно проверить версию спецификации и фактическую комплектацию агрегата.',
      timestamp: '11:21',
      status: 'answered',
      citations: [MOCK_CITATIONS[1]],
    },
  ],
  'chat-cooling': [
    {
      id: 'cooling-u1',
      role: 'user',
      content: 'Что нужно уточнить по системе охлаждения?',
      timestamp: '11:34',
    },
    {
      id: 'cooling-a1',
      role: 'assistant',
      content:
        'Нужно уточнить состав системы, проектную стадию и документ, по которому выполняется сверка. Без этого система не должна подставлять случайный источник.',
      timestamp: '11:35',
      status: 'needs_clarification',
    },
  ],
  'chat-ocr': [
    {
      id: 'ocr-u1',
      role: 'user',
      content: 'Какие документы требуют повторного OCR?',
      timestamp: '12:06',
    },
    {
      id: 'ocr-a1',
      role: 'assistant',
      content:
        '1. В демонстрационном наборе есть документы с незавершенным OCR и ожиданием индексации.\n' +
        '2. Реальный список должен возвращать Gateway после обработки документов.',
      timestamp: '12:07',
      status: 'answered',
      citations: [MOCK_CITATIONS[0]],
    },
  ],
};

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

export const MOCK_KNOWLEDGE_SECTIONS: KnowledgeSection[] = [
  {
    id: 'kb-hull',
    title: 'Корпус',
    description: 'Конструкции корпуса, прочность, обшивка, набор, водонепроницаемость.',
    documents: 34,
    updatedAt: '2026-05-21',
    status: 'Готово',
  },
  {
    id: 'kb-machinery',
    title: 'Энергетика',
    description: 'Главные и вспомогательные механизмы, двигатели, насосы, агрегаты.',
    documents: 27,
    updatedAt: '2026-05-20',
    status: 'В обработке',
  },
  {
    id: 'kb-electrical',
    title: 'Электрика',
    description: 'Электрооборудование, кабельные сети, питание, аварийные системы.',
    documents: 22,
    updatedAt: '2026-05-19',
    status: 'Готово',
  },
  {
    id: 'kb-piping',
    title: 'Трубопроводы',
    description: 'Судовые системы, трубопроводы, арматура, насосные магистрали.',
    documents: 19,
    updatedAt: '2026-05-18',
    status: 'Готово',
  },
  {
    id: 'kb-ventilation',
    title: 'Вентиляция',
    description: 'Вентиляция, кондиционирование, дымоудаление, воздуховоды.',
    documents: 14,
    updatedAt: '2026-05-18',
    status: 'Готово',
  },
  {
    id: 'kb-automation',
    title: 'Автоматика',
    description: 'АСУ, датчики, сигнализация, блокировки, дистанционное управление.',
    documents: 16,
    updatedAt: '2026-05-17',
    status: 'В обработке',
  },
  {
    id: 'kb-navigation',
    title: 'Навигация и связь',
    description: 'Радиосвязь, навигационное оборудование, мостик, сигнализация.',
    documents: 13,
    updatedAt: '2026-05-17',
    status: 'Готово',
  },
  {
    id: 'kb-fire',
    title: 'Пожарная безопасность',
    description: 'Пожаротушение, обнаружение пожара, изоляция, эвакуация.',
    documents: 18,
    updatedAt: '2026-05-16',
    status: 'Готово',
  },
  {
    id: 'kb-lifesaving',
    title: 'Спасательные средства',
    description: 'Шлюпки, плоты, индивидуальные средства, размещение и нормы.',
    documents: 11,
    updatedAt: '2026-05-16',
    status: 'Готово',
  },
  {
    id: 'kb-materials',
    title: 'Материалы',
    description: 'Стали, сплавы, покрытия, сварочные материалы, сертификаты.',
    documents: 21,
    updatedAt: '2026-05-15',
    status: 'Нужна проверка',
  },
  {
    id: 'kb-welding',
    title: 'Сварка',
    description: 'Технологии сварки, контроль швов, допуски, испытания.',
    documents: 17,
    updatedAt: '2026-05-15',
    status: 'Готово',
  },
  {
    id: 'kb-environment',
    title: 'Экология',
    description: 'Балласт, сточные воды, выбросы, предотвращение загрязнений.',
    documents: 10,
    updatedAt: '2026-05-14',
    status: 'Готово',
  },
];

export const MOCK_HISTORY: QueryHistoryItem[] = [
  {
    id: 'h1',
    user: 'Алексей Морозов',
    project: 'Проект 223-М',
    topic: 'Корпус',
    session: 'Толщина листа корпуса',
    query: 'Какая минимальная толщина листа для корпуса?',
    answer: 'Требуется уточнить проект, тип конструкции и актуальную редакцию нормы.',
    sources: 1,
    status: 'needs_clarification',
    createdAt: '2026-04-23 10:14',
    messages: [
      {
        id: 'h1-u1',
        role: 'user',
        content: 'Какая минимальная толщина листа для корпуса?',
        timestamp: '10:14',
      },
      {
        id: 'h1-a1',
        role: 'assistant',
        content: 'Уточните проект, район корпуса и тип конструкции. Без этих данных нельзя корректно выбрать требование НСИ.',
        timestamp: '10:15',
        status: 'needs_clarification',
        citations: [MOCK_CITATIONS[0]],
      },
    ],
  },
  {
    id: 'h2',
    user: 'Алексей Морозов',
    project: 'Проект 223-М',
    topic: 'Сварка',
    session: 'Регламент сварки',
    query: 'Найди регламент сварки Т-образных швов',
    answer: 'Найдены разделы регламента и проектной спецификации, требуется проверка версии.',
    sources: 2,
    status: 'answered',
    createdAt: '2026-04-23 10:21',
    messages: [
      {
        id: 'h2-u1',
        role: 'user',
        content: 'Найди регламент сварки Т-образных швов',
        timestamp: '10:21',
      },
      {
        id: 'h2-a1',
        role: 'assistant',
        content:
          '1. Для Т-образных швов нужно проверить актуальную редакцию регламента сварки.\n' +
          '2. Проектная спецификация должна совпадать с версией регламента, указанной в НСИ.',
        timestamp: '10:22',
        status: 'answered',
        citations: [MOCK_CITATIONS[0], MOCK_CITATIONS[1]],
      },
    ],
  },
  {
    id: 'h3',
    user: 'Ольга Волкова',
    project: 'База НСИ',
    topic: 'OCR',
    session: 'Контроль обработки документов',
    query: 'Какие документы не прошли OCR?',
    answer: 'Найден один документ в обработке и один ожидающий индексации.',
    sources: 0,
    status: 'answered',
    createdAt: '2026-04-23 10:38',
    messages: [
      {
        id: 'h3-u1',
        role: 'user',
        content: 'Какие документы не прошли OCR?',
        timestamp: '10:38',
      },
      {
        id: 'h3-a1',
        role: 'assistant',
        content: 'Найден один документ в обработке и один документ, который ожидает индексации после повторного OCR.',
        timestamp: '10:39',
        status: 'answered',
      },
    ],
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

export const MOCK_ADMIN_USERS: AdminUser[] = [
  {
    id: 'u1',
    name: 'Алексей Морозов',
    position: 'Инженер-конструктор',
    login: 'a.morozov',
    role: 'Пользователь',
    access: 'Чат, поиск, своя история',
    status: 'Активен',
    lastSeen: '2026-04-29 10:12',
  },
  {
    id: 'u2',
    name: 'Мария Соколова',
    position: 'Инженер-проектировщик',
    login: 'm.sokolova',
    role: 'Пользователь',
    access: 'Чат, поиск, своя история',
    status: 'Активен',
    lastSeen: '2026-04-29 09:44',
  },
  {
    id: 'u3',
    name: 'Ольга Волкова',
    position: 'Администратор базы НСИ',
    login: 'o.volkova',
    role: 'Администратор знаний',
    access: 'База знаний, поиск, история, QA, OCR-артефакты, журналы обработки',
    status: 'Активен',
    lastSeen: '2026-04-29 09:20',
  },
  {
    id: 'u4',
    name: 'Дмитрий Смирнов',
    position: 'Системный администратор',
    login: 'd.smirnov',
    role: 'Системный администратор',
    access: 'Все вкладки, роли, права, полный журнал',
    status: 'Ожидает настройки',
    lastSeen: '2026-04-28 18:05',
  },
];

export const MOCK_PROCESSING_LOGS: ProcessingLogItem[] = [
  {
    id: 'log1',
    time: '12:34:02',
    document: 'Правила РС. Часть I',
    stage: 'OCR',
    event: 'Страница 45 распознана с пониженной уверенностью, требуется повторная обработка.',
    retryStatus: 'Запланирована',
    visibility: 'Администратор',
  },
  {
    id: 'log2',
    time: '12:35:11',
    document: 'Спецификация 21900M2.362135.0903',
    stage: 'Parsing',
    event: 'Таблица параметров извлечена, структура сохранена в карточке документа.',
    retryStatus: 'Не требуется',
    visibility: 'Инженер',
  },
  {
    id: 'log3',
    time: '12:36:20',
    document: 'ГОСТ 2.103-2013',
    stage: 'Indexing',
    event: 'Индекс обновлен после повторной обработки документа.',
    retryStatus: 'Выполнена',
    visibility: 'Инженер',
  },
  {
    id: 'log4',
    time: '12:38:47',
    document: 'Архивный скан РКО',
    stage: 'OCR',
    event: 'Не удалось прочитать 3 страницы из-за качества скана.',
    retryStatus: 'Ошибка',
    visibility: 'Администратор',
  },
];
