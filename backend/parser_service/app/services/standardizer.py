"""
Стандартизация JSON: преобразует внутренний формат парсера в целевой формат контракта API.
"""

import copy
import re
from typing import Dict, Any, List
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class JsonStandardizer:
    """
    Преобразует сырой JSON от парсера в стандартизированную структуру документа.
    """

    @staticmethod
    def transform(data: Dict[str, Any], file_name: str = "") -> Dict[str, Any]:
        """
        Преобразует входной JSON в единый формат документа.

        Args:
            data: Исходный JSON от парсера (может быть контейнером или сырым).
            file_name: Имя файла (для подстановки в источник).

        Returns:
            Стандартизированный JSON с полями document, quality, errors, status.
        """
        try:
            if "content" in data and "document_info" in data:
                container = copy.deepcopy(data)
                raw_content = container["content"]
                standardized_content = JsonStandardizer._transform_raw(raw_content, file_name)
                container["content"] = standardized_content
                if "metadata" not in container:
                    container["metadata"] = {}
                container["metadata"]["total_pages"] = standardized_content.get("document", {}).get("source", {}).get("page_count", 1)
                container["metadata"]["has_tables"] = any(
                    b.get("type") == "table"
                    for b in standardized_content.get("document", {}).get("block", [])
                )
                return container
            else:
                return JsonStandardizer._transform_raw(data, file_name)
        except Exception as e:
            logger.exception("Standardization failed: %s", e)
            # Возвращаем минимальную валидную структуру с ошибкой
            return {
                "document": {
                    "source": {"file_name": file_name, "page_count": 1},
                    "pages": [{"page": 1, "width": 595, "height": 842}],
                    "block": []
                },
                "quality": {"confidence": 0.0, "pages_processed": 0, "pages_failed": 1},
                "errors": [{"code": "STANDARDIZATION_ERROR", "message": str(e)}],
                "status": "failed"
            }

    @staticmethod
    def _transform_raw(raw_json: Dict[str, Any], file_name: str = "") -> Dict[str, Any]:
        """
        Внутренний метод преобразования сырого JSON (без контейнера).
        Безопасно извлекает поля, используя значения по умолчанию.
        """
        result = copy.deepcopy(raw_json) if raw_json else {}

        # Безопасное извлечение метаданных
        doc_meta = {}
        for key in ["author", "title", "creation date", "modification date", "file name"]:
            if key in result:
                doc_meta[key.replace(" ", "_")] = result.pop(key)

        total_pages = result.get("number of pages", 1)

        elements = result.get("kids", [])
        page_numbers = set()
        for el in elements:
            page_num = el.get("page number")
            if page_num is not None:
                page_numbers.add(page_num)

        dpi = settings.pdf_dpi
        width_px = int(210 * dpi / 25.4)
        height_px = int(297 * dpi / 25.4)
        pages = [{"page": p, "width": width_px, "height": height_px} for p in sorted(page_numbers)]
        if not pages:
            pages = [{"page": 1, "width": width_px, "height": height_px}]

        block = []
        for idx, el in enumerate(elements, start=1):
            # Безопасное получение bounding box
            bbox = el.get("bounding box")
            if not isinstance(bbox, list) or len(bbox) != 4:
                bbox = [0, 0, 0, 0]

            block_item = {
                "number": idx,
                "type": JsonStandardizer._map_type(el.get("type", "paragraph")),
                "page": el.get("page number", 1),
                "bbox": bbox,
            }

            # Шрифт
            font = {}
            if "font" in el or "font size" in el or "text color" in el:
                font["size"] = el.get("font size", 12.0)
                font["color"] = JsonStandardizer._color_to_hex(el.get("text color", "[0.0]"))
                font["bold"] = "Bold" in el.get("font", "")
                font["italic"] = "Italic" in el.get("font", "")
                font["underline"] = False
            if font:
                block_item["font"] = font

            t = block_item["type"]
            if t in ("paragraph", "headerFooter", "caption"):
                block_item["content"] = el.get("content", "")
            elif t == "heading":
                block_item["content"] = el.get("content", "")
                block_item["heading_level"] = el.get("heading level", 1)
            elif t == "list":
                block_item["numbering_style"] = el.get("numbering style", "unknown")
                items = el.get("list items", [])
                block_item["block"] = []
                for it in items:
                    block_item["block"].append({
                        "type": "paragraph",
                        "page": it.get("page number", block_item["page"]),
                        "bbox": it.get("bounding box", [0, 0, 0, 0]),
                        "content": it.get("content", ""),
                        "font": block_item.get("font", {})
                    })
            elif t == "image":
                block_item["image_key"] = el.get("image_key", el.get("source", "").replace("1d_images/", ""))
                if "width" in el:
                    block_item["width"] = el["width"]
                if "height" in el:
                    block_item["height"] = el["height"]
            elif t == "table":
                block_item["number_of_rows"] = el.get("number of rows", 0)
                block_item["number_of_columns"] = el.get("number of columns", 0)
                rows = []
                for r in el.get("rows", []):
                    row = {"type": "table row", "row_number": r.get("row number", 0), "cells": []}
                    for cell in r.get("cells", []):
                        cell_content = []
                        for kid in cell.get("kids", []):
                            cell_content.append({
                                "type": "paragraph",
                                "page": kid.get("page number", 1),
                                "bbox": kid.get("bounding box", [0, 0, 0, 0]),
                                "content": kid.get("content", ""),
                                "font": {}
                            })
                        row["cells"].append({
                            "type": "table cell",
                            "row_number": cell.get("row number", 0),
                            "column_number": cell.get("column number", 0),
                            "row_span": cell.get("row span", 1),
                            "column_span": cell.get("column span", 1),
                            "page": cell.get("page number", 1),
                            "bbox": cell.get("bounding box", [0, 0, 0, 0]),
                            "block": cell_content
                        })
                    rows.append(row)
                block_item["rows"] = rows
            elif t == "formula":
                block_item["latex"] = el.get("content", "")
                block_item["meaning"] = ""

            block.append(block_item)

        quality = {"confidence": 0.94, "pages_processed": total_pages, "pages_failed": 0}
        target = {
            "document": {
                "source": {
                    "file_name": file_name or doc_meta.get("file_name", ""),
                    "file_hash_sha256": result.get("file_hash_sha256", ""),
                    "page_count": total_pages,
                    "author": doc_meta.get("author"),
                    "title": doc_meta.get("title"),
                    "creation_date": doc_meta.get("creation_date"),
                    "modification_date": doc_meta.get("modification_date")
                },
                "pages": pages,
                "block": block
            },
            "quality": quality,
            "errors": [],
            "status": "completed",
            "metadata": {
                "total_pages": total_pages,
                "has_tables": any(b.get("type") == "table" for b in block)
            }
        }
        return target

    @staticmethod
    def _map_type(original_type: str) -> str:
        """Маппинг типов элементов из исходного JSON в стандартные типы."""
        mapping = {
            "paragraph": "paragraph",
            "heading": "heading",
            "headerFooter": "headerFooter",
            "list": "list",
            "table": "table",
            "image": "image",
            "caption": "caption",
            "formula": "formula"
        }
        return mapping.get(original_type, "paragraph")

    @staticmethod
    def _color_to_hex(color_str: str) -> str:
        """Преобразует строку цвета из формата "[R,G,B]" в HEX."""
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