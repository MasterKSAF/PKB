# -*- coding: utf-8 -*-
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "okb_mvp_12_week_plan_presentation.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)

W, H = 1280, 720

pdfmetrics.registerFont(TTFont("Arial", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf"))

BG = colors.HexColor("#EDF4F6")
INK = colors.HexColor("#132630")
MUTED = colors.HexColor("#556B75")
GREEN = colors.HexColor("#1C5A67")
GOLD = colors.HexColor("#A5844C")
BLUE = colors.HexColor("#355D79")
RED = colors.HexColor("#8C5B4B")
PAPER = colors.HexColor("#FBFDFD")
LINE = colors.HexColor("#C9D7DD")


c = canvas.Canvas(str(OUT), pagesize=(W, H))
c.setTitle("OKB MVP plan")


def title(text, subtitle=None):
    c.setFillColor(BG)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(GREEN)
    c.rect(0, H - 86, W, 86, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Arial-Bold", 30)
    c.drawString(54, H - 54, text)
    if subtitle:
        c.setFont("Arial", 13)
        c.setFillColor(colors.HexColor("#DDE8ED"))
        c.drawRightString(W - 54, H - 54, subtitle)


def footer(n):
    c.setFillColor(MUTED)
    c.setFont("Arial", 10)
    c.drawString(54, 24, "Нейроассистент по инженерным документам ПКБ")
    c.drawRightString(W - 54, 24, f"{n}/3")


def paragraph(text, x, y, width, font="Arial", size=14, leading=19, color=INK):
    c.setFont(font, size)
    c.setFillColor(color)
    lines = []
    for part in str(text).split("\n"):
        lines.extend(simpleSplit(part, font, size, width) or [""])
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def bullet(text, x, y, width, color=INK, size=14, leading=19):
    c.setFillColor(GOLD)
    c.circle(x + 5, y + 5, 4, stroke=0, fill=1)
    return paragraph(text, x + 18, y, width - 18, size=size, leading=leading, color=color)


def card(x, y, w, h, heading, body, accent=GREEN):
    c.setFillColor(PAPER)
    c.roundRect(x, y, w, h, 14, stroke=0, fill=1)
    c.setStrokeColor(LINE)
    c.roundRect(x, y, w, h, 14, stroke=1, fill=0)
    c.setFillColor(accent)
    c.roundRect(x, y + h - 12, w, 12, 6, stroke=0, fill=1)
    c.setFillColor(INK)
    c.setFont("Arial-Bold", 16)
    c.drawString(x + 18, y + h - 38, heading)
    if body:
        paragraph(body, x + 18, y + h - 64, w - 36, size=12.5, leading=16, color=MUTED)


def pipeline_box(x, y, w, h, num, heading, items, accent=GREEN):
    c.setFillColor(PAPER)
    c.roundRect(x, y, w, h, 14, stroke=0, fill=1)
    c.setStrokeColor(LINE)
    c.roundRect(x, y, w, h, 14, stroke=1, fill=0)
    c.setFillColor(accent)
    c.roundRect(x, y + h - 12, w, 12, 6, stroke=0, fill=1)
    c.circle(x + 30, y + h - 40, 16, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Arial-Bold", 13)
    c.drawCentredString(x + 30, y + h - 45, str(num))
    c.setFillColor(INK)
    c.setFont("Arial-Bold", 14.5)
    c.drawString(x + 55, y + h - 46, heading)
    yy = y + h - 72
    for idx, item in enumerate(items, start=1):
        c.setFillColor(GOLD)
        c.setFont("Arial-Bold", 10)
        c.drawString(x + 18, yy, f"{idx}.")
        yy = paragraph(item, x + 38, yy, w - 56, size=10.7, leading=14, color=MUTED)
        yy -= 5


def slide_1():
    title("MVP: 12 недель / ~240 часов", "план по ТЗ + фактическая база знаний")

    c.setFillColor(INK)
    c.setFont("Arial-Bold", 21)
    c.drawString(54, 592, "Фазы разработки")
    c.setFont("Arial", 13)
    c.setFillColor(MUTED)
    c.drawString(
        54,
        568,
        "Цель: за 3 месяца собрать MVP для OCR, RAG-поиска, цитирования источников и базовой подсветки расхождений.",
    )

    c.setFillColor(BG)
    c.rect(50, 548, 1180, 32, stroke=0, fill=1)
    c.setFillColor(PAPER)
    c.roundRect(54, 526, 640, 50, 12, stroke=0, fill=1)
    c.setStrokeColor(LINE)
    c.roundRect(54, 526, 640, 50, 12, stroke=1, fill=0)
    c.setFillColor(BLUE)
    c.roundRect(54, 566, 640, 10, 6, stroke=0, fill=1)
    c.setFillColor(INK)
    c.setFont("Arial-Bold", 12.8)
    c.drawString(72, 548, "Цель MVP")
    paragraph(
        "За 3 месяца собрать MVP для OCR, RAG-поиска, цитирования источников и базовой подсветки расхождений.",
        148,
        548,
        526,
        size=12.4,
        leading=13,
        color=MUTED,
    )

    phases = [
        ("1", "Подготовка", "1 нед", "20 ч", GREEN),
        ("2", "Ingestion + OCR", "2 нед", "40 ч", BLUE),
        ("3", "RAG", "2 нед", "40 ч", BLUE),
        ("4", "Диалог", "1 нед", "24 ч", GOLD),
        ("5", "Проверка решений", "2 нед", "40 ч", RED),
        ("6", "Интеграции", "1 нед", "20 ч", GREEN),
        ("7", "Frontend", "3 нед", "60 ч", BLUE),
        ("8", "Деплой", "1 нед", "16 ч", GREEN),
        ("9", "Тестирование", "2 нед", "32 ч", GOLD),
    ]

    x0, y0 = 54, 488
    row_h = 42
    col = [52, 285, 105, 86]
    headers = ["#", "Фаза", "Срок", "Часы"]
    c.setFillColor(GREEN)
    c.roundRect(x0, y0, sum(col), 38, 10, stroke=0, fill=1)
    c.setFont("Arial-Bold", 13)
    c.setFillColor(colors.white)
    x = x0 + 16
    for header, width in zip(headers, col):
        c.drawString(x, y0 + 13, header)
        x += width

    y = y0 - row_h
    for i, (num, name, duration, hours, accent) in enumerate(phases):
        c.setFillColor(PAPER if i % 2 == 0 else colors.HexColor("#F1E8D8"))
        c.roundRect(x0, y, sum(col), 36, 8, stroke=0, fill=1)
        c.setFillColor(accent)
        c.circle(x0 + 27, y + 18, 11, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Arial-Bold", 11)
        c.drawCentredString(x0 + 27, y + 14, num)
        c.setFillColor(INK)
        c.setFont("Arial-Bold", 13)
        c.drawString(x0 + col[0] + 16, y + 12, name)
        c.setFont("Arial", 13)
        c.setFillColor(MUTED)
        c.drawString(x0 + col[0] + col[1] + 16, y + 12, duration)
        c.drawString(x0 + col[0] + col[1] + col[2] + 16, y + 12, hours)
        y -= row_h

    card(620, 407, 285, 121, "База уже собрана", "234 файла, ~543 MB, ~17k PDF-страниц, ~43 млн символов извлечённого текста.", GREEN)
    card(930, 407, 285, 121, "Ограничения набора", "Есть сканы/low-text PDF для OCR, 7 DWG требуют CAD-конвертации, 1 legacy DOC требует конвертер.", RED)
    card(
        620,
        245,
        595,
        116,
        "Ключевой принцип",
        "ИИ работает как инструмент поиска, извлечения и структурирования. Все ответы трассируются до документа и страницы; финальное решение остаётся за инженером.",
        BLUE,
    )
    card(
        620,
        110,
        595,
        94,
        "Контрольный результат",
        "Рабочая демо-цепочка: импорт документов -> OCR/parsing -> индекс -> поиск/RAG -> цитата -> просмотр страницы -> подсветка возможного расхождения.",
        GOLD,
    )
    footer(1)
    c.showPage()


def slide_2():
    title("Собранные документы и пайплайны MVP", "как содержание ложится в архитектуру")

    pipeline_box(
        54,
        466,
        360,
        152,
        1,
        "Собираем и описываем документы",
        [
            "Загружаем файлы из RKO, GDrive, реестров XLSX и внутренних папок.",
            "Сохраняем источник, версию, тип документа, путь и дату получения.",
            "Отмечаем дубли и разные версии одного документа.",
        ],
        GREEN,
    )
    pipeline_box(
        460,
        466,
        360,
        152,
        2,
        "Извлекаем содержание",
        [
            "Читаем текст из PDF, DOCX, XLSX, RTF и TXT.",
            "Страницы без текста отправляем на OCR.",
            "Таблицы, спецификации, штампы и страницы сохраняем отдельно.",
        ],
        BLUE,
    )
    pipeline_box(
        866,
        466,
        360,
        152,
        3,
        "Готовим поиск",
        [
            "Делим документы на фрагменты удобного размера.",
            "У каждого фрагмента остаётся ссылка на документ и страницу.",
            "Строим индекс для поиска по нормам, терминам и параметрам.",
        ],
        GOLD,
    )
    pipeline_box(
        54,
        264,
        360,
        162,
        4,
        "Отвечаем на запрос инженера",
        [
            "Инженер задаёт вопрос обычным языком.",
            "Находим подходящие фрагменты в правилах, ГОСТах и проектных документах.",
            "Показываем краткий вывод, страницу и текст источника.",
        ],
        GREEN,
    )
    pipeline_box(
        460,
        264,
        360,
        162,
        5,
        "Сверяем выбранные параметры",
        [
            "Берём требование из нормы и значение из чертежа или спецификации.",
            "Сравниваем только первые согласованные сценарии.",
            "Показываем результат как подсказку для инженерной проверки.",
        ],
        RED,
    )
    pipeline_box(
        866,
        264,
        360,
        162,
        6,
        "Показываем проверяемый результат",
        [
            "Вывод не должен быть «ответом без доказательств».",
            "В карточке должны быть источник, страница, фрагмент и статус.",
            "Инженер быстро открывает первоисточник и принимает решение.",
        ],
        BLUE,
    )

    c.setStrokeColor(GREEN)
    c.setLineWidth(3)
    for x1, y1, x2, y2 in [
        (414, 542, 460, 542),
        (820, 542, 866, 542),
        (234, 466, 234, 426),
        (414, 345, 460, 345),
        (820, 345, 866, 345),
    ]:
        c.line(x1, y1, x2, y2)
        c.setFillColor(GREEN)
        c.circle(x2, y2, 4, stroke=0, fill=1)

    c.setFillColor(INK)
    c.setFont("Arial-Bold", 20)
    c.drawString(70, 202, "Смысл пайплайна")
    paragraph(
        "Главное — не просто загрузить документы, а сохранить проверяемую цепочку: источник -> документ -> страница -> фрагмент -> ответ. Тогда инженер видит основание вывода и может быстро проверить его по первоисточнику.",
        70,
        172,
        1120,
        size=15,
        leading=21,
        color=MUTED,
    )
    footer(2)
    c.showPage()


def slide_3():
    title("Что нужно уточнить у заказчика", "простые вопросы перед стартом MVP")

    cols = [
        (
            "Какие документы главные?",
            [
                "В наборе документов есть правила разных лет и отдельные извещения об изменениях. Нужно подтвердить, какие версии считаются рабочими.",
                "Важно понять, должен ли ассистент показывать извещение отдельно или уже учитывать его как изменение к правилу.",
                "Если это не уточнить, система может сослаться на старую или не ту редакцию документа.",
            ],
            GREEN,
        ),
        (
            "Как проверить, что MVP полезен?",
            [
                "Нужны 20-30 реальных вопросов инженеров: что они обычно ищут в правилах, ГОСТах, чертежах и спецификациях.",
                "По каждому вопросу желательно знать правильный документ и страницу, чтобы объективно проверить качество поиска.",
                "Без такого набора приёмка будет субъективной: «кажется нашёл» вместо измеримого результата.",
            ],
            BLUE,
        ),
        (
            "Что сверяем первым?",
            [
                "Нужно выбрать первые 3-5 практических сценариев: например толщина листа, марка материала, ледовый класс, масса, обозначение детали.",
                "Важно определить, какой документ считать источником проверяемого значения: чертёж, спецификацию или альбом типовых конструкций.",
                "На MVP система должна подсвечивать возможное расхождение, а не выдавать финальный инженерный вердикт.",
            ],
            RED,
        ),
        (
            "Что можно хранить и читать?",
            [
                "Нужно подтвердить, какие документы можно хранить внутри системы, а какие можно только индексировать или открывать по ссылке.",
                "В наборе документов есть DWG. Нужно решить, входят ли они в MVP, или на первом этапе работаем только с PDF-выгрузками чертежей.",
                "Если DWG нужны сразу, потребуется способ конвертации в PDF/DXF/SVG и отдельный контур обработки.",
            ],
            GOLD,
        ),
    ]

    for idx, (head, items, accent) in enumerate(cols):
        x = 54 + idx * 306
        y = 150
        card(x, y, 278, 440, head, "", accent)
        yy = 505
        for item in items:
            yy = bullet(item, x + 20, yy, 238, size=12.2, leading=17)
            yy -= 12

    c.setFillColor(GREEN)
    c.roundRect(54, 70, 1172, 54, 14, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Arial-Bold", 16)
    c.drawString(
        78,
        93,
        "На следующей встрече лучше попросить: список главных документов, 20-30 типовых вопросов и 3-5 первых сценариев сверки.",
    )
    footer(3)
    c.showPage()


def pipeline_box_extended(x, y, w, h, num, heading, items, accent=GREEN, result=None):
    c.setFillColor(PAPER)
    c.roundRect(x, y, w, h, 14, stroke=0, fill=1)
    c.setStrokeColor(LINE)
    c.roundRect(x, y, w, h, 14, stroke=1, fill=0)
    c.setFillColor(accent)
    c.roundRect(x, y + h - 13, w, 13, 6, stroke=0, fill=1)
    c.circle(x + 31, y + h - 43, 17, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Arial-Bold", 13.5)
    c.drawCentredString(x + 31, y + h - 48, str(num))
    c.setFillColor(INK)
    c.setFont("Arial-Bold", 14.7)
    c.drawString(x + 58, y + h - 48, heading)

    yy = y + h - 76
    for idx, item in enumerate(items, start=1):
        c.setFillColor(GOLD)
        c.setFont("Arial-Bold", 11.2)
        c.drawString(x + 18, yy, f"{idx}.")
        yy = paragraph(item, x + 40, yy, w - 58, size=11.25, leading=14.3, color=MUTED)
        yy -= 3.7

    if result:
        c.setStrokeColor(LINE)
        c.setLineWidth(1)
        c.line(x + 18, y + 35, x + w - 18, y + 35)
        c.setFillColor(accent)
        c.setFont("Arial-Bold", 10.8)
        c.drawString(x + 18, y + 17, "Результат:")
        paragraph(result, x + 82, y + 17, w - 100, size=10.8, leading=12.5, color=INK)


def slide_2():
    title("Пайплайны MVP: от документов к проверяемому ответу", "более подробная рабочая схема")

    w, h = 376, 258
    xs = [54, 452, 850]
    top_y, bottom_y = 368, 82

    pipeline_box_extended(
        xs[0],
        top_y,
        w,
        h,
        1,
        "Собираем документы",
        [
            "Загружаем файлы из РКО, GDrive, реестров XLSX и внутренних папок.",
            "Для каждого файла сохраняем источник, ссылку, путь, дату и тип документа.",
            "Отдельно отмечаем правила, ГОСТы, чертежи, спецификации и служебные таблицы.",
            "Находим дубли, старые редакции и похожие названия, чтобы не смешивать версии.",
        ],
        GREEN,
        "реестр документов и список пробелов по доступам/файлам.",
    )
    pipeline_box_extended(
        xs[1],
        top_y,
        w,
        h,
        2,
        "Извлекаем содержание",
        [
            "Читаем текст из PDF, DOCX, XLSX, RTF и TXT без ручного копирования.",
            "Страницы без текстового слоя отправляем на OCR и помечаем качество распознавания.",
            "Таблицы, спецификации, штампы и номера страниц сохраняем отдельными блоками.",
            "Для DWG фиксируем необходимость конвертации в PDF, DXF или другой читаемый формат.",
        ],
        BLUE,
        "извлеченный текст, таблицы и отчет по проблемным файлам.",
    )
    pipeline_box_extended(
        xs[2],
        top_y,
        w,
        h,
        3,
        "Готовим поиск",
        [
            "Делим документы на фрагменты так, чтобы не терялись пункты, таблицы и заголовки.",
            "К каждому фрагменту привязываем документ, страницу, раздел и исходный файл.",
            "Строим индекс для поиска по нормам, терминам, обозначениям и числовым параметрам.",
            "Разводим типы источников: правила, ГОСТы, проектные документы и справочники.",
        ],
        GOLD,
        "поисковый индекс с привязкой к источникам и страницам.",
    )
    pipeline_box_extended(
        xs[0],
        bottom_y,
        w,
        h,
        4,
        "Ведем диалог и уточняем ответ",
        [
            "Инженер задает вопрос обычным языком, без точного названия документа.",
            "Если запрос широкий, ассистент предлагает уточнить объект, раздел или параметр.",
            "Поиск подбирает наиболее близкие фрагменты из правил, ГОСТов и проектных документов.",
            "Ответ формируется так, чтобы быть максимально точным и опираться на найденные источники.",
        ],
        GREEN,
        "уточненный ответ с цитатами и ссылками на источники.",
    )
    pipeline_box_extended(
        xs[1],
        bottom_y,
        w,
        h,
        5,
        "Сверяем параметры",
        [
            "Берем требование из нормы и значение из чертежа, спецификации или таблицы.",
            "На MVP выбираем только первые согласованные сценарии, например толщину или материал.",
            "Фиксируем единицы измерения, допуски и контекст, чтобы не сравнить разные вещи.",
            "Показываем результат как подсказку: совпадает, не совпадает или нужно уточнение.",
        ],
        RED,
        "карточка сверки с двумя источниками и статусом проверки.",
    )
    pipeline_box_extended(
        xs[2],
        bottom_y,
        w,
        h,
        6,
        "Показываем результат",
        [
            "На экране должна быть не просто фраза, а карточка с доказательной цепочкой.",
            "В карточке показываем источник, страницу, фрагмент текста, статус и дату версии.",
            "Можно быстро открыть первоисточник и проверить место, откуда взят вывод.",
            "Спорные места собираем в список для ручной проверки и улучшения набора примеров.",
        ],
        BLUE,
        "проверяемый экран MVP и журнал спорных мест для доработки.",
    )

    footer(2)
    c.showPage()


def question_box(x, y, w, h, num, heading, items, result, accent=GREEN):
    c.setFillColor(PAPER)
    c.roundRect(x, y, w, h, 14, stroke=0, fill=1)
    c.setStrokeColor(LINE)
    c.roundRect(x, y, w, h, 14, stroke=1, fill=0)
    c.setFillColor(accent)
    c.roundRect(x, y + h - 12, w, 12, 6, stroke=0, fill=1)
    c.circle(x + 28, y + h - 38, 15, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Arial-Bold", 12.5)
    c.drawCentredString(x + 28, y + h - 43, str(num))
    c.setFillColor(INK)
    c.setFont("Arial-Bold", 13.5)
    c.drawString(x + 52, y + h - 43, heading)

    yy = y + h - 68
    for item in items:
        yy = bullet(item, x + 18, yy, w - 36, size=10.5, leading=13.4)
        yy -= 3

    c.setStrokeColor(LINE)
    c.setLineWidth(1)
    c.line(x + 18, y + 34, x + w - 18, y + 34)
    c.setFillColor(accent)
    c.setFont("Arial-Bold", 10.4)
    c.drawString(x + 18, y + 16, "Нужно получить:")
    paragraph(result, x + 108, y + 16, w - 126, size=10.4, leading=12, color=INK)


def slide_3():
    title("Что уточнить у заказчика перед стартом MVP", "чем конкретнее ответы, тем меньше риск переделок")

    w, h = 376, 242
    xs = [54, 452, 850]
    top_y, bottom_y = 384, 104

    question_box(
        xs[0],
        top_y,
        w,
        h,
        1,
        "Документы и версии",
        [
            "Какие документы точно входят в MVP: РКО, РС, ГОСТы, чертежи, спецификации?",
            "Какие редакции считать рабочими, а какие оставить только как архив?",
            "Как учитывать извещения об изменениях: отдельно или как часть правила?",
            "Есть ли документы, которых пока нет в наборе, но они критичны для проверки?",
        ],
        "утвержденный перечень документов и правила работы с версиями.",
        GREEN,
    )
    question_box(
        xs[1],
        top_y,
        w,
        h,
        2,
        "Доступы и ограничения",
        [
            "Что можно хранить внутри решения, а что можно только индексировать или открывать ссылкой?",
            "Можно ли использовать скачанные файлы РКО/РС в демонстрационном контуре?",
            "Где должен находиться MVP: локально, в контуре заказчика или во внешнем облаке?",
            "Есть ли требования по NDA, журналированию действий и разграничению доступа?",
        ],
        "понятные правила хранения, доступа и использования документов.",
        BLUE,
    )
    question_box(
        xs[2],
        top_y,
        w,
        h,
        3,
        "Пользователи и сценарии",
        [
            "Кто первый пользователь: конструктор, нормоконтролер, инженер проекта, руководитель?",
            "Какие 20-30 вопросов инженеры чаще всего задают по этим документам?",
            "Какие 3-5 сценариев сверки выбрать первыми: материал, толщина, класс, масса, обозначение?",
            "Что для пользователя важнее: быстро найти страницу, получить краткий вывод или собрать отчет?",
        ],
        "приоритетный список пользовательских сценариев для MVP.",
        GOLD,
    )
    question_box(
        xs[0],
        bottom_y,
        w,
        h,
        4,
        "Качество и приемка",
        [
            "Какие вопросы войдут в тестовый набор и кто подтвердит правильные ответы?",
            "Что считаем успешным поиском: нужная страница в топ-3, точная цитата или краткий вывод?",
            "Как обрабатывать случаи, когда ответ не найден или найдено несколько противоречивых мест?",
            "Какие ошибки критичны для приемки, а какие можно оставить как ограничения MVP?",
        ],
        "измеримые критерии приемки и тестовый набор вопросов.",
        RED,
    )
    question_box(
        xs[1],
        bottom_y,
        w,
        h,
        5,
        "Интерфейс и интеграции",
        [
            "Где инженер должен открывать первоисточник: в браузере, PDF-viewer, сетевой папке или PDM?",
            "Нужны ли роли пользователей: просмотр, загрузка документов, подтверждение спорных мест?",
            "Нужно ли подключать внутренние папки, SharePoint/Drive, PDM, СЭД или реестры XLSX?",
            "Нужен ли экспорт результата проверки в PDF, Excel или карточку задачи?",
        ],
        "схема экранов, ролей и необходимых интеграций.",
        GREEN,
    )
    question_box(
        xs[2],
        bottom_y,
        w,
        h,
        6,
        "Обновление и поддержка",
        [
            "Кто будет добавлять новые документы и подтверждать, что база обновлена корректно?",
            "Как часто обновлять правила, ГОСТы, проектные документы и внутренние реестры?",
            "Кто разбирает спорные ответы и помечает правильный источник для следующей версии?",
            "Какие логи и отчеты нужны: запросы, найденные источники, ошибки OCR, качество ответов?",
        ],
        "регламент обновления базы и обработки обратной связи.",
        BLUE,
    )

    footer(3)
    c.showPage()


def dry_question_box(x, y, w, h, num, heading, items, accent=GREEN):
    c.setFillColor(PAPER)
    c.roundRect(x, y, w, h, 14, stroke=0, fill=1)
    c.setStrokeColor(LINE)
    c.roundRect(x, y, w, h, 14, stroke=1, fill=0)
    c.setFillColor(accent)
    c.roundRect(x, y + h - 10, w, 10, 6, stroke=0, fill=1)
    c.circle(x + 24, y + h - 32, 13, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Arial-Bold", 11.5)
    c.drawCentredString(x + 24, y + h - 36, str(num))
    c.setFillColor(INK)
    c.setFont("Arial-Bold", 13.2)
    c.drawString(x + 46, y + h - 37, heading)

    yy = y + h - 62
    for item in items:
        yy = bullet(item, x + 18, yy, w - 36, size=10.8, leading=13.3, color=MUTED)
        yy -= 2


def slide_3():
    title("Вопросы К Заказчику Перед Стартом", "один рабочий лист")

    c.setFillColor(MUTED)
    c.setFont("Arial", 12.8)
    c.drawString(
        54,
        608,
        "Ниже не финальные решения, а список вопросов, которые стоит закрыть до начала MVP.",
    )

    w, h = 572, 132
    left_x, right_x = 54, 654
    ys = [448, 290, 132]

    dry_question_box(
        left_x,
        ys[0],
        w,
        h,
        1,
        "Документы",
        [
            "Какие документы берем в первую очередь?",
            "Где лежат актуальные версии?",
            "Что считать рабочей редакцией?",
            "Что пока не берем в MVP?",
        ],
        GREEN,
    )
    dry_question_box(
        right_x,
        ys[0],
        w,
        h,
        2,
        "Пользователь и запросы",
        [
            "Кто будет первым пользователем?",
            "Какие 10-20 вопросов он задает чаще всего?",
            "Что важнее: найти страницу, цитату или краткий ответ?",
            "Нужны ли уточняющие вопросы в диалоге?",
        ],
        BLUE,
    )
    dry_question_box(
        left_x,
        ys[1],
        w,
        h,
        3,
        "Проверка результата",
        [
            "Какие 3-5 сверок делаем первыми?",
            "Кто подтверждает, что ответ правильный?",
            "Что делать, если найдено несколько мест?",
            "Какие ошибки допустимы на старте, а какие нет?",
        ],
        RED,
    )
    dry_question_box(
        right_x,
        ys[1],
        w,
        h,
        4,
        "Доступы и контур",
        [
            "Можно ли хранить документы внутри решения?",
            "Где должен жить MVP: локально или в контуре заказчика?",
            "Есть ли ограничения по NDA и ролям?",
            "Какие источники можно подключать сразу?",
        ],
        GOLD,
    )
    dry_question_box(
        left_x,
        ys[2],
        w,
        h,
        5,
        "Интерфейс",
        [
            "Как пользователь открывает первоисточник?",
            "Нужен ли экспорт в PDF или Excel?",
            "Нужны ли роли: просмотр, загрузка, подтверждение?",
            "Нужен ли список спорных мест для ручной проверки?",
        ],
        GREEN,
    )
    dry_question_box(
        right_x,
        ys[2],
        w,
        h,
        6,
        "Обновление базы",
        [
            "Кто добавляет новые документы?",
            "Как часто обновлять правила и проектные файлы?",
            "Кто разбирает спорные ответы?",
            "Какие логи и отчеты нужны на старте?",
        ],
        BLUE,
    )

    c.setFillColor(PAPER)
    c.roundRect(54, 58, 1172, 42, 12, stroke=0, fill=1)
    c.setStrokeColor(LINE)
    c.roundRect(54, 58, 1172, 42, 12, stroke=1, fill=0)
    c.setFillColor(INK)
    c.setFont("Arial-Bold", 12.6)
    c.drawString(72, 74, "Что хочется получить после встречи:")
    c.setFont("Arial", 12.4)
    c.setFillColor(MUTED)
    c.drawString(
        322,
        74,
        "список документов, список типовых вопросов, первые сценарии сверки, правила доступа и критерии приемки.",
    )

    footer(3)
    c.showPage()


def vision_step(x, y, w, h, num, heading, body, accent=GREEN):
    c.setFillColor(PAPER)
    c.roundRect(x, y, w, h, 14, stroke=0, fill=1)
    c.setStrokeColor(LINE)
    c.roundRect(x, y, w, h, 14, stroke=1, fill=0)
    c.setFillColor(accent)
    c.roundRect(x, y + h - 10, w, 10, 6, stroke=0, fill=1)
    c.circle(x + 26, y + h - 32, 14, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Arial-Bold", 12)
    c.drawCentredString(x + 26, y + h - 36, str(num))
    c.setFillColor(INK)
    c.setFont("Arial-Bold", 13.2)
    c.drawString(x + 48, y + h - 36, heading)
    paragraph(body, x + 18, y + h - 60, w - 36, size=11.1, leading=14, color=MUTED)


def compact_box(x, y, w, h, heading, items, accent=BLUE):
    c.setFillColor(PAPER)
    c.roundRect(x, y, w, h, 14, stroke=0, fill=1)
    c.setStrokeColor(LINE)
    c.roundRect(x, y, w, h, 14, stroke=1, fill=0)
    c.setFillColor(accent)
    c.roundRect(x, y + h - 10, w, 10, 6, stroke=0, fill=1)
    c.setFillColor(INK)
    c.setFont("Arial-Bold", 14)
    c.drawString(x + 18, y + h - 30, heading)
    yy = y + h - 56
    for item in items:
        yy = bullet(item, x + 18, yy, w - 36, size=11, leading=13.8, color=MUTED)
        yy -= 3


def slide_3():
    title("Видение Процесса MVP", "упрощенная схема по ТЗ")

    c.setFillColor(MUTED)
    c.setFont("Arial", 12.8)
    c.drawString(
        54,
        608,
        "Упрощенно: от запроса инженера до проверяемого ответа с привязкой к источнику.",
    )

    c.setFillColor(INK)
    c.setFont("Arial-Bold", 18)
    c.drawString(54, 568, "Как должен работать контур")

    step_y = 430
    step_w = 215
    step_h = 96
    xs = [54, 289, 524, 759, 994]
    steps = [
        ("Запрос", "Инженер задает вопрос или выбирает типовую проверку.", GREEN),
        ("Поиск", "Находим нужные правила, ГОСТы, чертежи и фрагменты.", BLUE),
        ("Ответ", "Собираем ответ только из найденных источников.", GOLD),
        ("Основание", "Показываем документ, страницу, фрагмент и статус.", RED),
        ("Проверка", "Инженер смотрит первоисточник и принимает решение.", GREEN),
    ]

    for idx, (x, (heading, body, accent)) in enumerate(zip(xs, steps), start=1):
        vision_step(x, step_y, step_w, step_h, idx, heading, body, accent)

    c.setStrokeColor(GREEN)
    c.setLineWidth(3)
    for x1, x2 in [(269, 289), (504, 524), (739, 759), (974, 994)]:
        y = step_y + 54
        c.line(x1, y, x2, y)
        c.setFillColor(GREEN)
        c.circle(x2, y, 4, stroke=0, fill=1)

    compact_box(
        54,
        202,
        560,
        146,
        "Что входит в MVP по ТЗ",
        [
            "Импорт документов, OCR и извлечение текста.",
            "Поиск и RAG по правилам, ГОСТам и проектным документам.",
            "Короткий ответ с обязательной привязкой к источнику.",
            "Первые сценарии базовой сверки параметров.",
        ],
        GREEN,
    )
    compact_box(
        666,
        202,
        560,
        146,
        "Что не входит в MVP по ТЗ",
        [
            "Финальное инженерное решение вместо инженера.",
            "Полноценные расчетные модули по прочности и гидростатике.",
            "Нативный разбор CAD-геометрии без отдельного контура конвертации.",
            "Автоматическая экспертиза без проверки по первоисточнику.",
        ],
        BLUE,
    )

    c.setFillColor(PAPER)
    c.roundRect(54, 86, 1172, 54, 12, stroke=0, fill=1)
    c.setStrokeColor(LINE)
    c.roundRect(54, 86, 1172, 54, 12, stroke=1, fill=0)
    c.setFillColor(INK)
    c.setFont("Arial-Bold", 13.2)
    c.drawString(72, 108, "Смысл MVP")
    paragraph(
        "По ТЗ сначала делаем рабочий контур поиска, цитирования и базовой сверки. Он помогает инженеру, а не подменяет его решение.",
        72,
        92,
        1128,
        size=11.9,
        leading=14,
        color=MUTED,
    )

    footer(3)
    c.showPage()


def slide_1():
    title("MVP: 12 недель / ~240 часов", "план по ТЗ + фактическая база знаний")

    c.setFillColor(INK)
    c.setFont("Arial-Bold", 21)
    c.drawString(54, 592, "Фазы разработки")

    c.setFillColor(colors.HexColor("#E3EDF1"))
    c.roundRect(54, 544, 980, 28, 8, stroke=0, fill=1)
    c.setFillColor(BLUE)
    c.roundRect(54, 544, 10, 28, 5, stroke=0, fill=1)
    c.setFillColor(INK)
    c.setFont("Arial-Bold", 13)
    c.drawString(
        76,
        552,
        "Цель: за 3 месяца собрать MVP для OCR, RAG-поиска, цитирования источников и базовой подсветки расхождений.",
    )

    phases = [
        ("1", "Подготовка", "1 нед", "20 ч", GREEN),
        ("2", "Ingestion + OCR", "2 нед", "40 ч", BLUE),
        ("3", "RAG", "2 нед", "40 ч", BLUE),
        ("4", "Диалог", "1 нед", "24 ч", GOLD),
        ("5", "Проверка решений", "2 нед", "40 ч", RED),
        ("6", "Интеграции", "1 нед", "20 ч", GREEN),
        ("7", "Frontend", "3 нед", "60 ч", BLUE),
        ("8", "Деплой", "1 нед", "16 ч", GREEN),
        ("9", "Тестирование", "2 нед", "32 ч", GOLD),
    ]

    x0, y0 = 54, 488
    row_h = 42
    col = [52, 285, 105, 86]
    headers = ["#", "Фаза", "Срок", "Часы"]
    c.setFillColor(GREEN)
    c.roundRect(x0, y0, sum(col), 38, 10, stroke=0, fill=1)
    c.setFont("Arial-Bold", 13)
    c.setFillColor(colors.white)
    x = x0 + 16
    for header, width in zip(headers, col):
        c.drawString(x, y0 + 13, header)
        x += width

    y = y0 - row_h
    for i, (num, name, duration, hours, accent) in enumerate(phases):
        c.setFillColor(PAPER if i % 2 == 0 else colors.HexColor("#F1E8D8"))
        c.roundRect(x0, y, sum(col), 36, 8, stroke=0, fill=1)
        c.setFillColor(accent)
        c.circle(x0 + 27, y + 18, 11, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Arial-Bold", 11)
        c.drawCentredString(x0 + 27, y + 14, num)
        c.setFillColor(INK)
        c.setFont("Arial-Bold", 13)
        c.drawString(x0 + col[0] + 16, y + 12, name)
        c.setFont("Arial", 13)
        c.setFillColor(MUTED)
        c.drawString(x0 + col[0] + col[1] + 16, y + 12, duration)
        c.drawString(x0 + col[0] + col[1] + col[2] + 16, y + 12, hours)
        y -= row_h

    card(620, 407, 285, 121, "База уже собрана", "234 файла, ~543 MB, ~17k PDF-страниц, ~43 млн символов извлечённого текста.", GREEN)
    card(930, 407, 285, 121, "Ограничения набора", "Есть сканы/low-text PDF для OCR, 7 DWG требуют CAD-конвертации, 1 legacy DOC требует конвертер.", RED)
    card(
        620,
        245,
        595,
        116,
        "Ключевой принцип",
        "ИИ работает как инструмент поиска, извлечения и структурирования. Все ответы трассируются до документа и страницы; финальное решение остаётся за инженером.",
        BLUE,
    )
    card(
        620,
        110,
        595,
        94,
        "Контрольный результат",
        "Рабочая демо-цепочка: импорт документов -> OCR/parsing -> индекс -> поиск/RAG -> цитата -> просмотр страницы -> подсветка возможного расхождения.",
        GOLD,
    )
    footer(1)
    c.showPage()


def slide_2():
    title("Пайплайны MVP: от документа к проверяемому ответу", "рабочая схема с более конкретными формулировками")

    w, h = 376, 258
    xs = [54, 452, 850]
    top_y, bottom_y = 368, 82

    pipeline_box_extended(
        xs[0],
        top_y,
        w,
        h,
        1,
        "Реестр и состав документов",
        [
            "Собираем файлы из РКО, Drive, XLSX-реестров и внутренних папок в единый перечень.",
            "Для каждого файла фиксируем источник, путь, тип документа, дату получения и рабочую версию.",
            "Отдельно помечаем правила, ГОСТы, чертежи, спецификации и служебные таблицы.",
            "Находим дубли и спорные версии, чтобы не смешивать старые и актуальные редакции.",
        ],
        GREEN,
        "реестр документов, список дублей и список пробелов по доступам или отсутствующим файлам.",
    )
    pipeline_box_extended(
        xs[1],
        top_y,
        w,
        h,
        2,
        "Извлечение текста и таблиц",
        [
            "Читаем текст из PDF, DOCX, XLSX, RTF и TXT без ручной перекладки файлов.",
            "Страницы без текстового слоя отправляем на OCR и помечаем качество распознавания.",
            "Таблицы, штампы, номера страниц и спецификации сохраняем отдельными блоками.",
            "Для DWG на этом этапе фиксируем, что нужен отдельный контур конвертации.",
        ],
        BLUE,
        "извлеченный текст, таблицы и отчет по файлам, которые читаются плохо или требуют конвертации.",
    )
    pipeline_box_extended(
        xs[2],
        top_y,
        w,
        h,
        3,
        "Индекс и RAG-поиск",
        [
            "Делим документы на фрагменты так, чтобы не терялись заголовки, пункты и таблицы.",
            "К каждому фрагменту привязываем документ, страницу, раздел и исходный файл.",
            "Строим индекс для поиска по нормам, терминам, обозначениям и числовым параметрам.",
            "Разводим типы источников: правила, ГОСТы, проектные документы и справочные материалы.",
        ],
        GOLD,
        "поисковый индекс, из которого можно поднять нужный фрагмент вместе с источником и страницей.",
    )
    pipeline_box_extended(
        xs[0],
        bottom_y,
        w,
        h,
        4,
        "Диалог и подбор ответа",
        [
            "Инженер задает вопрос обычным языком, без точного названия документа.",
            "Если запрос широкий, ассистент просит уточнить объект, раздел, параметр или тип проверки.",
            "Поиск подбирает наиболее близкие фрагменты из правил, ГОСТов и проектных документов.",
            "Ответ собирается только по найденным источникам, а не как свободное рассуждение модели.",
        ],
        GREEN,
        "ответ с цитатами, ссылками на источник и понятной логикой, почему выбраны именно эти фрагменты.",
    )
    pipeline_box_extended(
        xs[1],
        bottom_y,
        w,
        h,
        5,
        "Сверка параметров по источникам",
        [
            "Берем требование из нормы и значение из чертежа, спецификации или таблицы.",
            "На MVP выбираем только первые согласованные сценарии: например материал, толщину, класс или массу.",
            "Сопоставляем единицы измерения, допуски и контекст, чтобы не сравнивать разные вещи.",
            "Результат показываем как подсказку: совпадает, не совпадает или нужно уточнение.",
        ],
        RED,
        "карточка сверки с двумя источниками, найденными значениями и статусом проверки.",
    )
    pipeline_box_extended(
        xs[2],
        bottom_y,
        w,
        h,
        6,
        "Экран результата и проверка",
        [
            "На экране показываем не только ответ, но и доказательную цепочку до первоисточника.",
            "В карточке есть документ, страница, фрагмент текста, статус и версия документа.",
            "Инженер может быстро открыть первоисточник и проверить место, откуда взят вывод.",
            "Спорные случаи попадают в журнал для ручной проверки и улучшения следующих версий.",
        ],
        BLUE,
        "проверяемый экран MVP и журнал спорных мест, которые помогают дообучать и уточнять систему.",
    )

    footer(2)
    c.showPage()


slide_1()
slide_2()
slide_3()
c.save()
print(OUT)
