"""
Тест Docling pipeline с патчем _execute_pipeline (без валидации).
Использует PdfFormatOption из документации.
"""
import sys
import json
from pathlib import Path

import pikepdf
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption, ConversionResult
from docling.datamodel.document import InputDocument


def clean_and_convert(pdf_path: str, max_pages: int = 5):
    """Очищает PDF через pikepdf и парсит Docling-ом."""
    print("  Step 1: Cleaning PDF with pikepdf...", file=sys.stderr)

    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.do_cell_matching = True
    pipeline_options.accelerator_options.num_threads = 4

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    # Патчим _execute_pipeline — убираем проверку valid
    original_execute = converter._execute_pipeline

    def patched_execute(self, in_doc, raises_on_error=True):
        # Принудительно считаем документ валидным
        if not hasattr(in_doc, '_valid_override'):
            in_doc.valid = True
        pipeline = self._get_pipeline(in_doc.format)
        if pipeline is not None:
            conv_res = pipeline.execute(in_doc, raises_on_error=raises_on_error)
        else:
            if raises_on_error:
                raise Exception(f"No pipeline for {in_doc.file}")
            conv_res = ConversionResult(input=in_doc, status="failure")
        return conv_res

    converter._execute_pipeline = lambda in_doc, raises_on_error=True: patched_execute(
        converter, in_doc, raises_on_error
    )

    # Clean PDF
    with pikepdf.open(pdf_path) as pdf:
        cleaned_path = "temp_fixed.pdf"
        pdf.save(cleaned_path, linearize=True)

    print(f"  Step 2: Converting (max {max_pages} pages)...", file=sys.stderr)
    result = converter.convert(cleaned_path, max_num_pages=max_pages)
    doc = result.document
    print(f"  Done: {len(doc.pages)} pages", file=sys.stderr)
    return doc


if __name__ == "__main__":
    pdf_path = "pdf/2-020101-174-1.pdf"
    try:
        doc = clean_and_convert(pdf_path, max_pages=5)
        print(f"\nSuccess! Pages: {len(doc.pages)}", file=sys.stderr)
        for item, level in doc.iterate_items():
            label = getattr(item, "label", "")
            text = getattr(item, "text", "")[:80]
            print(f"  [{level}] {type(item).__name__}: {label} -> {text!r}", file=sys.stderr)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\nERROR: {e}", file=sys.stderr)
