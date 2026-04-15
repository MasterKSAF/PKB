# Аналогичные решения и лучшие практики (OCR / Document AI / RAG)

Ниже — список найденных решений в открытых источниках (GitHub, Хабр) и краткий
разбор используемых подходов: извлечение текста и структуры, RAG, гибридный поиск,
оценка качества.

## 1) Практические пайплайны RAG по документам (Хабр)

- **RAG без LangChain, “чистый пайплайн” (PDF → OCR → embeddings → FAISS + BM25)**
  - Что полезно: явное разделение offline/online контуров; опыт борьбы с шумом
    OCR; гибрид FAISS + BM25 и аргументация, зачем нужны оба
    [Как гуманитарий… (Хабр)](https://habr.com/ru/articles/996144/).
  - Подходы:
    - OCR для сканов (Tesseract/Pillow/MuPDF/Fitz как элементы стека)
      [Как гуманитарий… (Хабр)](https://habr.com/ru/articles/996144/).
    - Индексация: FAISS + BM25 как дополняющие методы
      [Как гуманитарий… (Хабр)](https://habr.com/ru/articles/996144/).

- **RAG как “интерактивная база знаний” с акцентом на метаданные и разбиение по
  заголовкам**
  - Что полезно: практики работы с несколькими форматами, выделение заголовков
    регулярками/эвристиками, хранение метаданных и OCR для image-only PDF
    [Документный хаос? (Хабр)](https://habr.com/ru/articles/955768/).

- **RAG для поиска по нормативным документам (пример реализации)**
  - Что полезно: общее описание стадий RAG; акцент на цитировании источников и
    ограничениях контекстного окна LLM как мотивации к ретривалу
    [RAG‑технология… (Хабр)](https://habr.com/ru/articles/904418).

- **Обзор эволюции от OCR к “пониманию документа” (Document AI)**
  - Что полезно: мысль “документы — это структура (таблицы/графики), а не только
    плоский текст” и необходимость layout‑aware пайплайна для качественного RAG
    [От OCR до ADE… (Хабр)](https://habr.com/ru/articles/1008610/).

## 2) Open-source Document AI / OCR / layout (GitHub)

- **Docling** — конвертация документов (PDF/Office/HTML и др.) в унифицированное
  структурированное представление и экспорты (Markdown/JSON/HTML), включая OCR и
  разбор layout/таблиц
  [docling-project/docling](https://github.com/docling-project/docling).
  - Что полезно для нашего проекта:
    - выход в структурированную модель документа и экспорт в Markdown/JSON
      [docling-project/docling](https://github.com/docling-project/docling);
    - OCR и понимание страницы (reading order, layout, tables)
      [docling-project/docling](https://github.com/docling-project/docling).

- **LayoutParser** — toolkit для layout detection + интеграции OCR по регионам,
  полезен когда нужно выделять блоки (таблицы/колонки/шапки/штампы) и отдельно
  OCR‑ить их
  [Layout-Parser/layout-parser](http://github.com/Layout-Parser/layout-parser).

- **docTR** — end‑to‑end OCR библиотека (детекция текста + распознавание) с
  объектной моделью результата (страница/блок/строка/слово) и экспортом в JSON
  [mindee/doctr](https://github.com/mindee/doctr).

- **Unstructured** — ETL‑библиотека для извлечения элементов документа и
  подготовки данных под RAG (partitioning/chunking)
  [Unstructured-IO/unstructured](https://github.com/Unstructured-IO/unstructured).

## 3) Orchestration / RAG pipeline (GitHub)

- **Haystack** — модульный фреймворк оркестрации для production‑RAG (пайплайны,
  ретриверы, routing, интеграции)
  [deepset-ai/haystack](https://github.com/deepset-ai/haystack/).

## 4) Оценка качества RAG (evaluation)

- **RAGAS (пример интеграции с Haystack)** — подход к оценке RAG‑пайплайна через
  метрики качества (faithfulness, context precision и т. п.) и компонент
  `RagasEvaluator`
  [haystack.ipynb (RAGAS)](https://github.com/explodinggradients/ragas/blob/298b6827/docs/howtos/integrations/haystack.ipynb).

## 5) Что берём в “best practices” для судостроительной нормативки

1. **Hybrid retrieval**: BM25 для точных обозначений + vector search для “как/почему”
   вопросов (обосновано практикой в RAG‑пайплайнах) [Как гуманитарий… (Хабр)](https://habr.com/ru/articles/996144/).
2. **Layout-aware extraction** для нормативки с таблицами/структурой (иначе
   “смысл” теряется в плоском тексте) [От OCR до ADE… (Хабр)](https://habr.com/ru/articles/1008610/).
3. **Декомпозиция на offline/online контуры** и измеримость качества на каждом
   этапе (OCR качество, чанкинг, ретривал, генерация) [RAG‑технология… (Хабр)](https://habr.com/ru/articles/904418).
4. **Цитирование и трассируемость** как продуктовая фича “для инженера”:
   ссылки на страницу/раздел/версию документа [RAG‑технология… (Хабр)](https://habr.com/ru/articles/904418).

Sources:

- [Как гуманитарий за 2 месяца с нуля RAG систему построил, или Парсинг PDF по-хардкору / Хабр](https://habr.com/ru/articles/996144/)
- [Документный хаос? RAG-система придёт на помощь / Хабр](https://habr.com/ru/articles/955768/)
- [RAG-технология в действии: как создать интеллектуальную систему поиска по нормативным документам / Хабр](https://habr.com/ru/articles/904418)
- [От OCR до ADE: как машины научились не просто читать, а понимать документы / Хабр](https://habr.com/ru/articles/1008610/)
- [docling-project/docling](https://github.com/docling-project/docling)
- [Layout-Parser/layout-parser](http://github.com/Layout-Parser/layout-parser)
- [mindee/doctr](https://github.com/mindee/doctr)
- [Unstructured-IO/unstructured](https://github.com/Unstructured-IO/unstructured)
- [deepset-ai/haystack](https://github.com/deepset-ai/haystack/)
- [haystack.ipynb (RAGAS)](https://github.com/explodinggradients/ragas/blob/298b6827/docs/howtos/integrations/haystack.ipynb)
