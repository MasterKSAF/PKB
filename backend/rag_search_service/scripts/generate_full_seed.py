#!/usr/bin/env python3
"""
Генератор seed_data.sql с 20 чанками из 3 ГОСТов и реальными эмбеддингами.

Запуск:
    cd rag_search
    python scripts/generate_full_seed.py

Результат: обновлённый migrations/seed_data.sql
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────
# Конфигурация: пути
# ──────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ──────────────────────────────────────────────────────────────────────
# ДАННЫЕ: 3 документа (id = bigint), 14 секций (id = bigint), 20 чанков (id = bigint)
# ──────────────────────────────────────────────────────────────────────

DOCUMENTS = [
    {
        "id": 1,
        "doc_code": "ГОСТ 12.2.003-91",
        "title": "ССБТ. Оборудование производственное. Общие требования безопасности",
        "document_type": "normative",
        "adoption_date": "1991-01-01",
        "validity_status": "active",
        "era": "USSR",
    },
    {
        "id": 2,
        "doc_code": "ГОСТ 24705-81",
        "title": "Основные нормы взаимозаменяемости. Резьба метрическая. Допуски. Посадки с зазором",
        "document_type": "normative",
        "adoption_date": "1981-07-01",
        "validity_status": "active",
        "era": "USSR",
    },
    {
        "id": 3,
        "doc_code": "ГОСТ 5264-80",
        "title": "Ручная дуговая сварка. Соединения сварные. Основные типы, конструктивные элементы и размеры",
        "document_type": "normative",
        "adoption_date": "1980-01-01",
        "validity_status": "active",
        "era": "USSR",
    },
]

SECTIONS = [
    # ГОСТ 12.2.003-91 (id 1-5)
    {"id": 1, "doc_id": 1, "clause": "1", "title": "Область распространения", "level": 1, "path": "1", "page": 2, "type": "section", "content": None},
    {"id": 2, "doc_id": 1, "clause": "1.1", "title": "Общие положения", "level": 2, "path": "1.1", "page": 3, "type": "section", "content": None},
    {"id": 3, "doc_id": 1, "clause": "2", "title": "Требования безопасности к конструкции", "level": 1, "path": "2", "page": 5, "type": "section", "content": None},
    {"id": 4, "doc_id": 1, "clause": "2.1", "title": "Требования к движущимся частям", "level": 2, "path": "2.1", "page": 6, "type": "section", "content": None},
    {"id": 5, "doc_id": 1, "clause": "3", "title": "Требования к защитным ограждениям", "level": 1, "path": "3", "page": 9, "type": "section", "content": None},
    # ГОСТ 24705-81 (id 6-10)
    {"id": 6, "doc_id": 2, "clause": "1", "title": "Основные параметры резьбы", "level": 1, "path": "1", "page": 2, "type": "section", "content": None},
    {"id": 7, "doc_id": 2, "clause": "1.1", "title": "Номинальные диаметры и шаги", "level": 2, "path": "1.1", "page": 3, "type": "section", "content": None},
    {"id": 8, "doc_id": 2, "clause": "2", "title": "Допуски и посадки с зазором", "level": 1, "path": "2", "page": 8, "type": "section", "content": None},
    {"id": 9, "doc_id": 2, "clause": "2.1", "title": "Поля допусков", "level": 2, "path": "2.1", "page": 9, "type": "section", "content": None},
    {"id": 10, "doc_id": 2, "clause": "3", "title": "Контроль резьбы", "level": 1, "path": "3", "page": 14, "type": "section", "content": None},
    # ГОСТ 5264-80 (id 11-14)
    {"id": 11, "doc_id": 3, "clause": "1", "title": "Типы сварных соединений", "level": 1, "path": "1", "page": 2, "type": "section", "content": None},
    {"id": 12, "doc_id": 3, "clause": "1.1", "title": "Стыковые соединения", "level": 2, "path": "1.1", "page": 3, "type": "section", "content": None},
    {"id": 13, "doc_id": 3, "clause": "2", "title": "Конструктивные элементы", "level": 1, "path": "2", "page": 7, "type": "section", "content": None},
    {"id": 14, "doc_id": 3, "clause": "3", "title": "Требования к качеству сварных швов", "level": 1, "path": "3", "page": 11, "type": "section", "content": None},
]

CHUNKS = [
    # ── ГОСТ 12.2.003-91 (id 1-7) ──
    {
        "id": 1, "doc_id": 1, "section_id": 1,
        "content": "Настоящий стандарт распространяется на оборудование всех отраслей промышленности и устанавливает общие требования безопасности, предъявляемые к конструкции производственного оборудования.",
        "page": 2, "chunk_index": 0, "confidence": 0.95,
    },
    {
        "id": 2, "doc_id": "11111111-1111-1111-1111-111111111111", "section_id": 2,
        "content": "Оборудование должно быть безопасным при монтаже, эксплуатации и ремонте. Конструкция должна исключать возможность травмирования работающего при выполнении технологических операций.",
        "page": 3, "chunk_index": 0, "confidence": 0.94,
    },
    {
        "id": 3, "doc_id": "11111111-1111-1111-1111-111111111111", "section_id": 3,
        "content": "Движущиеся части оборудования, являющиеся возможным источником травмирования, должны быть ограждены или расположены так, чтобы исключалась возможность прикасания к ним работающего.",
        "page": 5, "chunk_index": 0, "confidence": 0.96,
    },
    {
        "id": 4, "doc_id": "11111111-1111-1111-1111-111111111111", "section_id": 4,
        "content": "Ограждения должны быть сблокированы с пусковыми устройствами, обеспечивающими остановку оборудования при снятии ограждения. Цвет ограждений должен соответствовать требованиям сигнальных цветов.",
        "page": 6, "chunk_index": 0, "confidence": 0.93,
    },
    {
        "id": 5, "doc_id": "11111111-1111-1111-1111-111111111111", "section_id": 4,
        "content": "Сигнальные цвета и знаки безопасности должны применяться для предупреждения об опасности. Красный сигнальный цвет применяется для запрещающих знаков и обозначения отключенного состояния оборудования.",
        "page": 7, "chunk_index": 1, "confidence": 0.92,
    },
    {
        "id": 6, "doc_id": "11111111-1111-1111-1111-111111111111", "section_id": 5,
        "content": "Защитные ограждения должны быть прочными, устойчивыми к внешним воздействиям и не создавать дополнительных опасностей. Конструкция ограждений должна обеспечивать возможность осмотра и смазки механизмов.",
        "page": 9, "chunk_index": 0, "confidence": 0.94,
    },
    {
        "id": 7, "doc_id": "11111111-1111-1111-1111-111111111111", "section_id": 5,
        "content": "Расстояние от ограждения до движущихся частей должно быть не менее 100 мм. Материал ограждений должен выбираться с учетом прочности и коррозионной стойкости в условиях эксплуатации.",
        "page": 10, "chunk_index": 1, "confidence": 0.91,
    },
    # ── ГОСТ 24705-81 (id 8-14) ──
    {
        "id": 8, "doc_id": 2, "section_id": 6,
        "content": "Метрическая резьба с крупным шагом применяется для соединений общего назначения. Диаметры от 1 до 600 мм. Допуски по среднему диаметру устанавливаются в зависимости от степени точности.",
        "page": 2, "chunk_index": 0, "confidence": 0.95,
    },
    {
        "id": 9, "doc_id": 2, "section_id": 7,
        "content": "Номинальные диаметры метрической резьбы устанавливаются в диапазоне от 1 до 600 мм. Для каждого диаметра предусмотрен основной шаг и несколько мелких шагов. Мелкие шаги применяются для резьб с повышенными требованиями к прочности.",
        "page": 3, "chunk_index": 0, "confidence": 0.94,
    },
    {
        "id": 10, "doc_id": 2, "section_id": 7,
        "content": "Для диаметров от 1 до 4 мм шаг резьбы составляет 0.25-0.7 мм. Для диаметров от 5 до 68 мм основной шаг составляет 0.8-6 мм. Для диаметров свыше 68 мм шаг резьбы устанавливается по специальной таблице.",
        "page": 4, "chunk_index": 1, "confidence": 0.93,
    },
    {
        "id": 11, "doc_id": 2, "section_id": 8,
        "content": "Посадки с зазором в метрической резьбе обеспечиваются выбором полей допусков. Для наружной резьбы установлены поля допусков: 4h, 6g, 6e, 8g. Для внутренней резьбы: 4H, 5H, 6H, 7H.",
        "page": 8, "chunk_index": 0, "confidence": 0.95,
    },
    {
        "id": 12, "doc_id": 2, "section_id": 9,
        "content": "Поле допуска 6H/6g является предпочтительным для резьбовых соединений общего назначения. Допуски на средний диаметр резьбы рассчитываются по формуле Td2 = K * (180 * P^(2/3) - 3.15 * P^(-1/2)).",
        "page": 9, "chunk_index": 0, "confidence": 0.94,
    },
    {
        "id": 13, "doc_id": 2, "section_id": 9,
        "content": "Степени точности для метрической резьбы: 4, 5, 6, 7, 8. Степень 6 является основной. Для ответственных соединений применяются степени 4 и 5. Для грубых соединений — степени 7 и 8.",
        "page": 10, "chunk_index": 1, "confidence": 0.93,
    },
    {
        "id": 14, "doc_id": 2, "section_id": 10,
        "content": "Контроль метрической резьбы осуществляется резьбовыми калибрами: проходными и непроходными. Проходной калибр должен свободно навинчиваться на контролируемую деталь. Непроходной калибр не должен навинчиваться более чем на 2-3 оборота.",
        "page": 14, "chunk_index": 0, "confidence": 0.95,
    },
    # ── ГОСТ 5264-80 (id 15-20) ──
    {
        "id": 15, "doc_id": 3, "section_id": 11,
        "content": "Настоящий стандарт устанавливает основные типы, конструктивные элементы и размеры сварных соединений при ручной дуговой сварке покрытыми электродами стальных конструкций.",
        "page": 2, "chunk_index": 0, "confidence": 0.95,
    },
    {
        "id": 16, "doc_id": 3, "section_id": 12,
        "content": "Стыковые соединения выполняются с разделкой кромок или без разделки в зависимости от толщины свариваемых деталей. При толщине до 4 мм разделка кромок не требуется. При толщине свыше 4 мм необходима V-образная или X-образная разделка.",
        "page": 3, "chunk_index": 0, "confidence": 0.94,
    },
    {
        "id": 17, "doc_id": 3, "section_id": 12,
        "content": "Угол разделки кромок при V-образной подготовке составляет 60±5 градусов. Притупление кромок — 1-2 мм. Зазор в стыке — 0-2 мм в зависимости от толщины свариваемых деталей.",
        "page": 4, "chunk_index": 1, "confidence": 0.93,
    },
    {
        "id": 18, "doc_id": 3, "section_id": 13,
        "content": "Угловые швы характеризуются катетом шва K. Минимальное значение катета углового шва составляет 3 мм. Выпуклость углового шва допускается не более 2 мм. Вогнутость углового шва допускается до 1.5 мм.",
        "page": 7, "chunk_index": 0, "confidence": 0.94,
    },
    {
        "id": 19, "doc_id": 3, "section_id": 13,
        "content": "Длина усиления стыкового шва должна быть не более 3 мм при толщине деталей до 10 мм и не более 4 мм при толщине свыше 10 мм. Ширина шва зависит от толщины свариваемых деталей и режима сварки.",
        "page": 8, "chunk_index": 1, "confidence": 0.92,
    },
    {
        "id": 20, "doc_id": 3, "section_id": 14,
        "content": "Сварные швы должны быть без трещин, непроваров, подрезов и шлаковых включений. Допускаются единичные поры диаметром не более 1 мм при количестве не более 3 на 100 мм длины шва.",
        "page": 11, "chunk_index": 0, "confidence": 0.95,
    },
]


# ──────────────────────────────────────────────────────────────────────
# ГЕНЕРАЦИЯ ЭМБЕДДИНГОВ
# ──────────────────────────────────────────────────────────────────────

def generate_embedding(text: str) -> list[float]:
    """Сгенерировать эмбеддинг через sentence-transformers (E5)."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("ERROR: Установите sentence-transformers: pip install sentence-transformers")
        sys.exit(1)

    model = SentenceTransformer("intfloat/multilingual-e5-large")
    prefixed = f"passage: {text}"
    embedding = model.encode(prefixed)
    return embedding.tolist()


def format_vector(embedding: list[float]) -> str:
    """Форматировать вектор как pgvector-литерал."""
    values = ",".join(f"{v:.6f}" for v in embedding)
    return f"'[{values}]'::vector(1024)"


# ──────────────────────────────────────────────────────────────────────
# ГЕНЕРАЦИЯ SQL
# ──────────────────────────────────────────────────────────────────────

def generate_sql() -> str:
    lines = []
    lines.append("-- =============================================================================")
    lines.append("-- Тестовые данные: 3 ГОСТа, 20 чанков с реальными эмбеддингами")
    lines.append("-- Сгенерировано scripts/generate_full_seed.py")
    lines.append("-- =============================================================================")
    lines.append("")

    # Документы (id = bigint)
    lines.append("-- Документы")
    lines.append("INSERT INTO registry.documents (id, doc_code, title, document_type, adoption_date, validity_status, era) VALUES")
    doc_values = []
    for d in DOCUMENTS:
        doc_values.append(
            f"    ('{d['id']}', '{d['doc_code']}', '{d['title']}', "
            f"'{d['document_type']}', '{d['adoption_date']}', "
            f"'{d['validity_status']}', '{d['era']}')"
        )
    lines.append(",\n".join(doc_values))
    lines.append("ON CONFLICT (id) DO NOTHING;")
    lines.append("")

    # Секции (id = bigint, serial)
    lines.append("-- Секции документов (id = bigint)")
    lines.append("INSERT INTO registry.document_sections (id, document_id, clause, title, level, path, page, type, content) VALUES")
    sec_values = []
    for s in SECTIONS:
        content_val = "'{}'::jsonb" if s['content'] is None else f"'{json.dumps(s['content'])}'::jsonb"
        sec_values.append(
            f"    ({s['id']}, '{s['doc_id']}', '{s['clause']}', "
            f"'{s['title']}', {s['level']}, '{s['path']}', {s['page']}, "
            f"'{s['type']}', {content_val})"
        )
    lines.append(",\n".join(sec_values))
    lines.append("ON CONFLICT (id) DO NOTHING;")
    lines.append("")

    # Чанки (id = bigint, serial)
    lines.append("-- Чанки (20 шт, id = bigint, embedding размерности 1024)")
    lines.append("INSERT INTO rag.document_chunks (id, document_id, section_id, content, page, chunk_index, confidence, embedding) VALUES")

    chunk_values = []
    for i, c in enumerate(CHUNKS):
        section_id = str(c['section_id']) if c['section_id'] else "NULL"
        confidence = f"{c['confidence']:.2f}"

        print(f"  Генерация эмбеддинга [{i+1}/{len(CHUNKS)}]: {c['content'][:50]}...")
        emb = generate_embedding(c["content"])
        vec = format_vector(emb)

        chunk_values.append(
            f"    ({c['id']},\n"
            f"     '{c['doc_id']}',\n"
            f"     {section_id},\n"
            f"     '{c['content']}',\n"
            f"     {c['page']}, {c['chunk_index']}, {confidence},\n"
            f"     {vec})"
        )

    lines.append(",\n".join(chunk_values))
    lines.append("ON CONFLICT (id) DO NOTHING;")
    lines.append("")

    return "\n".join(lines)


def main():
    print("=" * 60)
    print("Генерация seed_data.sql: 3 ГОСТа, 20 чанков, реальные эмбеддинги")
    print("=" * 60)

    seed_file = PROJECT_ROOT / "migrations" / "seed_data.sql"
    print(f"\nГенерация эмбеддингов для {len(CHUNKS)} чанков...\n")

    sql = generate_sql()

    seed_file.write_text(sql, encoding="utf-8")
    print(f"\n✅ Готово! Файл {seed_file} записан.")
    print(f"   Документов: {len(DOCUMENTS)}")
    print(f"   Секций: {len(SECTIONS)}")
    print(f"   Чанков: {len(CHUNKS)}")


if __name__ == "__main__":
    main()