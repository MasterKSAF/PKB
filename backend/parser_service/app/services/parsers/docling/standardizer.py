"""
Стандартизация JSON: преобразует внутренний формат парсера в целевой формат контракта API.
Теперь поддерживает разные схемы через наследование.
"""
import copy
import re
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import logging
from datetime import datetime, timezone, timedelta

PDF_DPI = 72  # копия settings.pdf_dpi из parser_service

logger = logging.getLogger(__name__)


class BaseStandardizer(ABC):
    """Базовый интерфейс стандартизатора."""

    @abstractmethod
    def transform(self, data: Dict[str, Any], file_name: str = "") -> Dict[str, Any]:
        """Преобразует входной JSON в стандартизированную структуру."""
        pass


class JsonStandardizer(BaseStandardizer):
    """Стандартизатор для схемы raw_ocr_v4 (текущая реализация)."""

    @staticmethod
    def _normalize_bbox(bbox: List[float]) -> List[float]:
        """
        Нормализует bounding box: приводит отрицательные координаты к 0,
        убеждается, что x2 > x1 и y2 > y1.
        """
        if not bbox or len(bbox) != 4:
            return [0, 0, 0, 0]

        x1, y1, x2, y2 = bbox

        # Приводим отрицательные к 0
        x1 = max(0.0, x1)
        y1 = max(0.0, y1)
        x2 = max(0.0, x2)
        y2 = max(0.0, y2)

        # Если x2 <= x1, меняем местами или устанавливаем минимальную ширину
        if x2 <= x1:
            x2 = x1 + 1.0  # минимальная ширина 1 пиксель

        if y2 <= y1:
            y2 = y1 + 1.0

        return [float(x1), float(y1), float(x2), float(y2)]

    def transform(self, data: Dict[str, Any], file_name: str = "") -> Dict[str, Any]:
        """
        Преобразует входной JSON в стандартизированную структуру.
        """
        logger.debug("Starting standardization for file %s", file_name)
        try:
            if "content" in data and "document_info" in data:
                container = copy.deepcopy(data)
                raw_content = container["content"]
                standardized_content = self._transform_raw(raw_content, file_name)
                container["content"] = standardized_content
                if "metadata" not in container:
                    container["metadata"] = {}
                container["metadata"]["total_pages"] = (
                    standardized_content.get("document", {})
                    .get("source", {})
                    .get("page_count", 1)
                )
                container["metadata"]["has_tables"] = any(
                    b.get("type") == "table"
                    for b in standardized_content.get("document", {}).get("block", [])
                )
                logger.debug("Standardization completed for file %s", file_name)
                return container
            else:
                result = self._transform_raw(data, file_name)
                logger.debug("Standardization completed for file %s (raw)", file_name)
                return result
        except Exception as e:
            logger.exception("Standardization failed for file %s", file_name)
            return {
                "document": {
                    "source": {"file_name": file_name, "page_count": 1},
                    "pages": [{"page": 1, "width": 595, "height": 842}],
                    "block": [],
                },
                "quality": {
                    "confidence": 0.0,
                    "pages_processed": 0,
                    "pages_failed": 1,
                    "per_page": [{"page": 1, "status": "failed", "error": "STANDARDIZATION_ERROR"}],
                    "notifications": [],
                },
                "errors": [{"code": "STANDARDIZATION_ERROR", "message": str(e)}],
                "status": "failed",
            }

    def _transform_raw(self, raw_json: Dict[str, Any], file_name: str = "") -> Dict[str, Any]:
        """Внутренний метод преобразования сырого JSON (без контейнера)."""
        result = copy.deepcopy(raw_json) if raw_json else {}

        # Извлекаем метаданные документа
        doc_meta = {}
        for key in ["author", "title", "creation date", "modification date", "file name"]:
            if key in result:
                doc_meta[key.replace(" ", "_")] = result.pop(key)

        total_pages = result.get("number of pages", 1)
        file_hash = result.get("file_hash_sha256", "")

        # Строим страницы
        elements = result.get("kids", [])
        page_numbers = set()
        for el in elements:
            page_num = el.get("page number")
            if page_num is not None:
                page_numbers.add(page_num)

        dpi = PDF_DPI
        width_px = int(210 * dpi / 25.4)
        height_px = int(297 * dpi / 25.4)
        pages = [{"page": p, "width": width_px, "height": height_px} for p in sorted(page_numbers)]
        if not pages:
            pages = [{"page": 1, "width": width_px, "height": height_px}]

        # Формируем блоки
        block = []
        for idx, el in enumerate(elements, start=1):
            bbox = el.get("bounding box")
            if not isinstance(bbox, list) or len(bbox) != 4:
                bbox = [0, 0, 0, 0]
            else:
                # Нормализуем координаты
                bbox = self._normalize_bbox(bbox)

            block_item = {
                "number": idx,
                "type": self._map_type(el.get("type", "paragraph")),
                "page": el.get("page number", 1),
                "bbox": bbox,
            }

            # Шрифт
            font = {}
            if "font" in el or "font size" in el or "text color" in el:
                font["size"] = el.get("font size", 12.0)
                font["color"] = self._color_to_hex(el.get("text color", "[0.0]"))
                font["bold"] = "Bold" in el.get("font", "")
                font["italic"] = "Italic" in el.get("font", "")
                font["underline"] = False
            if font:
                block_item["font"] = font

            t = block_item["type"]

            # Обработка типов
            if t in ("paragraph", "headerFooter", "caption"):
                block_item["content"] = el.get("content", "")
                if t == "caption":
                    linked = el.get("linked number")
                    if linked is not None:
                        block_item["linked_number"] = linked

            elif t == "heading":
                block_item["content"] = el.get("content", "")
                block_item["heading_level"] = el.get("heading level", 1)

            elif t == "list":
                block_item["numbering_style"] = el.get("numbering style", "unknown")
                items = el.get("list items", [])
                block_item["block"] = []
                for it in items:
                    item_font = {}
                    if "font size" in it or "text color" in it:
                        item_font["size"] = it.get("font size", 12.0)
                        item_font["color"] = self._color_to_hex(it.get("text color", "[0.0]"))
                        item_font["bold"] = "Bold" in it.get("font", "")
                        item_font["italic"] = "Italic" in it.get("font", "")
                        item_font["underline"] = False
                    block_item["block"].append(
                        {
                            "type": "paragraph",
                            "page": it.get("page number", block_item["page"]),
                            "bbox": self._normalize_bbox(it.get("bounding box", [0, 0, 0, 0])),
                            "content": it.get("content", ""),
                            "font": item_font if item_font else block_item.get("font", {}),
                        }
                    )

            elif t == "text_block":
                children = el.get("block") or el.get("kids", [])
                block_item["block"] = []
                for child in children:
                    child_font = {}
                    if "font size" in child or "text color" in child:
                        child_font["size"] = child.get("font size", 12.0)
                        child_font["color"] = self._color_to_hex(child.get("text color", "[0.0]"))
                        child_font["bold"] = "Bold" in child.get("font", "")
                        child_font["italic"] = "Italic" in child.get("font", "")
                        child_font["underline"] = False
                    block_item["block"].append(
                        {
                            "content": child.get("content", ""),
                            "font": child_font if child_font else block_item.get("font", {}),
                        }
                    )
                # Удаляем font на верхнем уровне, так как он не нужен для text_block
                block_item.pop("font", None)

            elif t == "image":
                block_item["image_key"] = el.get(
                    "image_key", el.get("source", "").replace("1d_images/", "")
                )
                if "width" in el:
                    block_item["width"] = el["width"]
                if "height" in el:
                    block_item["height"] = el["height"]

            elif t == "formula":
                block_item["latex"] = el.get("content", "")
                block_item["meaning"] = el.get("meaning", "")
                if "image_key" in el:
                    block_item["image_key"] = el["image_key"]

            elif t == "table":
                block_item["number_of_rows"] = el.get("number of rows", 0)
                block_item["number_of_columns"] = el.get("number of columns", 0)
                if "content" in el and el["content"]:
                    block_item["content"] = el["content"]

                if "caption" in el:
                    cap = el["caption"]
                    block_item["caption"] = {
                        "type": "caption",
                        "page": cap.get("page number", block_item["page"]),
                        "bbox": self._normalize_bbox(cap.get("bounding box", [0, 0, 0, 0])),
                        "linked_number": cap.get("linked number", idx),
                        "content": cap.get("content", ""),
                        "font": {},
                    }
                    cap_font = {}
                    if "font size" in cap or "text color" in cap:
                        cap_font["size"] = cap.get("font size", 9.0)
                        cap_font["color"] = self._color_to_hex(cap.get("text color", "[0.0]"))
                        cap_font["bold"] = "Bold" in cap.get("font", "")
                        cap_font["italic"] = "Italic" in cap.get("font", "")
                        cap_font["underline"] = False
                    if cap_font:
                        block_item["caption"]["font"] = cap_font

                rows = []
                for r in el.get("rows", []):
                    row = {"type": "table row", "row_number": r.get("row number", 0), "cells": []}
                    for cell in r.get("cells", []):
                        cell_content = []
                        for kid in cell.get("kids", []):
                            cell_font = {}
                            if "font size" in kid or "text color" in kid:
                                cell_font["size"] = kid.get("font size", 9.0)
                                cell_font["color"] = self._color_to_hex(kid.get("text color", "[0.0]"))
                                cell_font["bold"] = "Bold" in kid.get("font", "")
                                cell_font["italic"] = "Italic" in kid.get("font", "")
                                cell_font["underline"] = False
                            cell_content.append(
                                {"content": kid.get("content", ""), "font": cell_font if cell_font else {}}
                            )
                        row["cells"].append(
                            {
                                "type": "table cell",
                                "row_number": cell.get("row number", 0),
                                "column_number": cell.get("column number", 0),
                                "row_span": cell.get("row span", 1),
                                "column_span": cell.get("column span", 1),
                                "page": cell.get("page number", 1),
                                "bbox": self._normalize_bbox(cell.get("bounding box", [0, 0, 0, 0])),
                                "block": cell_content,
                            }
                        )
                    rows.append(row)
                block_item["rows"] = rows

                if "footnotes" in el:
                    block_item["footnotes"] = []
                    for fn in el["footnotes"]:
                        fn_font = {}
                        if "font size" in fn or "text color" in fn:
                            fn_font["size"] = fn.get("font size", 8.0)
                            fn_font["color"] = self._color_to_hex(fn.get("text color", "[0.0]"))
                            fn_font["bold"] = "Bold" in fn.get("font", "")
                            fn_font["italic"] = "Italic" in fn.get("font", "")
                            fn_font["underline"] = False
                        block_item["footnotes"].append(
                            {
                                "bbox": self._normalize_bbox(fn.get("bounding box", [0, 0, 0, 0])),
                                "content": fn.get("content", ""),
                                "font": fn_font if fn_font else {},
                            }
                        )

            block.append(block_item)

        # Формируем quality
        per_page = []
        for page_num in sorted(page_numbers) if page_numbers else [1]:
            per_page.append({"page": page_num, "status": "ok", "confidence": 0.94})
        pages_failed = 0

        quality = {
            "confidence": 0.94,
            "pages_processed": total_pages,
            "pages_failed": pages_failed,
            "per_page": per_page,
            "notifications": [],
        }

        # Преобразуем даты
        creation_date = self._convert_pdf_date(doc_meta.get("creation_date"))
        modification_date = self._convert_pdf_date(doc_meta.get("modification_date"))

        target = {
            "document": {
                "source": {
                    "file_name": file_name or doc_meta.get("file_name", ""),
                    "file_hash_sha256": file_hash,
                    "page_count": total_pages,
                    "author": doc_meta.get("author"),
                    "title": doc_meta.get("title"),
                    "creation_date": creation_date,
                    "modification_date": modification_date,
                },
                "pages": pages,
                "block": block,
            },
            "quality": quality,
            "errors": [],
            "status": "completed",
            "metadata": {
                "total_pages": total_pages,
                "has_tables": any(b.get("type") == "table" for b in block),
            },
        }
        return target

    @staticmethod
    def _map_type(original_type: str) -> str:
        mapping = {
            "paragraph": "paragraph",
            "heading": "heading",
            "headerFooter": "headerFooter",
            "list": "list",
            "table": "table",
            "image": "image",
            "caption": "caption",
            "formula": "formula",
            "text_block": "text_block",
        }
        return mapping.get(original_type, "paragraph")

    @staticmethod
    def _color_to_hex(color_str: str) -> str:
        if not color_str or color_str == "[0.0]":
            return "#000000"
        numbers = re.findall(r"[-+]?\d*\.?\d+", color_str)
        if len(numbers) >= 3:
            try:
                r = int(round(float(numbers[0]) * 255))
                g = int(round(float(numbers[1]) * 255))
                b = int(round(float(numbers[2]) * 255))
                r = max(0, min(255, r))
                g = max(0, min(255, g))
                b = max(0, min(255, b))
                return f"#{r:02x}{g:02x}{b:02x}"
            except (ValueError, IndexError):
                return "#000000"
        return "#000000"

    @staticmethod
    def _convert_pdf_date(date_str: Optional[str]) -> Optional[str]:
        """
        Преобразует дату из PDF-формата (D:YYYYMMDDHHmmSS[+/-]HH'mm' или с Z) в ISO 8601 с Z (UTC).
        Если не удаётся распарсить, возвращает None.
        """
        if not date_str:
            return None

        patterns = [
            r"D:(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})([+-]\d{2})'(\d{2})'",  # с часовым поясом
            r"D:(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})([+-]\d{2})(\d{2})",   # без кавычек
            r"D:(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})Z",                    # Z
            r"D:(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})",                    # без пояса
        ]

        for pat in patterns:
            match = re.match(pat, date_str)
            if match:
                groups = match.groups()
                year, month, day, hour, minute, second = map(int, groups[:6])
                dt = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
                if len(groups) >= 8:
                    offset_sign = groups[6]
                    offset_hours = int(groups[7]) if len(groups) >= 8 else 0
                    offset_minutes = int(groups[8]) if len(groups) == 9 else 0
                    if offset_sign == "-":
                        dt = dt + timedelta(hours=offset_hours, minutes=offset_minutes)
                    elif offset_sign == "+":
                        dt = dt - timedelta(hours=offset_hours, minutes=offset_minutes)
                return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Если ничего не подошло, пробуем просто убрать "D:" и попытаться как обычную дату
        cleaned = re.sub(r"^D:", "", date_str)
        try:
            dt = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            logger.warning("Could not parse date: %s", date_str)
            return None