"""Статические mock-ответы для заглушки RAG/LLM."""
import itertools

_ANSWERED = {
    "status": "answered",
    "answer_items": [
        {
            "number": 1,
            "text": (
                "Согласно Правилам классификации и постройки морских судов (Часть II, стр. 42), "
                "минимальная толщина обшивки ледового пояса для класса Arc4 составляет не менее 12 мм. "
                "Расчёт выполняется с учётом района эксплуатации, материала и ледовой нагрузки."
            ),
            "citations": [
                {
                    "citation_id": "cit-001",
                    "document_id": "doc-norm-001",
                    "document_title": "Правила классификации и постройки морских судов, Часть II",
                    "section": "Корпус",
                    "page": 42,
                    "fragment": "Для ледового класса Arc4 толщина обшивки ледового пояса должна быть не менее 12 мм.",
                    "page_preview_url": "/documents/doc-norm-001/pages/42/preview",
                    "document_url": "/documents/doc-norm-001/file",
                },
                {
                    "citation_id": "cit-002",
                    "document_id": "doc-norm-002",
                    "document_title": "НСИ ПКБ, версия 2026",
                    "section": "Нормативные требования",
                    "page": 17,
                    "fragment": "Класс Arc4: толщина листов — не менее 12 мм при стали категории Е.",
                    "page_preview_url": "/documents/doc-norm-002/pages/17/preview",
                    "document_url": "/documents/doc-norm-002/file",
                },
            ],
        }
    ],
    "latency_ms": 1420,
}

_NEEDS_CLARIFICATION = {
    "status": "needs_clarification",
    "message": "Уточните проект, район корпуса и тип судна для точного ответа.",
    "missing_fields": ["project_id", "hull_area", "vessel_type"],
    "answer_items": [],
    "latency_ms": 680,
}

_SOURCE_CONFLICT = {
    "status": "source_conflict",
    "message": "Найдены разные требования в двух редакциях нормативного документа.",
    "conflicts": [
        {
            "document_id": "doc-norm-001",
            "document_title": "НСИ, редакция 2024",
            "page": 45,
            "value": "8 мм",
        },
        {
            "document_id": "doc-norm-003",
            "document_title": "НСИ, редакция 2026",
            "page": 47,
            "value": "10 мм",
        },
    ],
    "answer_items": [],
    "latency_ms": 890,
}

_CYCLE = itertools.cycle([_ANSWERED, _ANSWERED, _NEEDS_CLARIFICATION, _ANSWERED, _SOURCE_CONFLICT])


def next_chat_response() -> dict:
    return next(_CYCLE).copy()


SEARCH_RESULTS = [
    {
        "section_id": 420042,
        "document_id": "doc-norm-001",
        "document_title": "Правила РС, часть I",
        "page": 42,
        "content": "Для ледового класса Arc4 толщина обшивки ледового пояса должна быть не менее 12 мм.",
        "score": 0.94,
        "document_type": "normative",
        "matched_subquery": None,
    },
    {
        "section_id": 420017,
        "document_id": "doc-norm-002",
        "document_title": "НСИ ПКБ 2026",
        "page": 17,
        "content": "Класс Arc4: нормативная толщина — не менее 12 мм при стали категории Е.",
        "score": 0.87,
        "document_type": "normative",
        "matched_subquery": None,
    },
]

ASK_RESPONSE = {
    "normalized_question": "Требования к толщине обшивки ледового пояса для класса Arc4",
    "answer": (
        "Согласно Правилам РС и НСИ ПКБ 2026, для ледового класса Arc4 минимальная толщина обшивки "
        "ледового пояса составляет 12 мм при использовании стали категории Е. "
        "При других категориях стали расчёт выполняется индивидуально."
    ),
    "sources": [
        {
            "document_id": "doc-norm-001",
            "document_title": "Правила РС, часть I",
            "page_number": 42,
            "fragment_id": "frg-042",
            "text": "Для ледового класса Arc4 толщина обшивки ледового пояса должна быть не менее 12 мм.",
            "score": 0.94,
        }
    ],
    "disclaimer": "Результат носит информационный характер и подлежит обязательной инженерной проверке.",
    "processing_time_ms": 4200,
    "model_used": "mock-rag-v1",
}
