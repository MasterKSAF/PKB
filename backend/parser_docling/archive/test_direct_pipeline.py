"""
Тест: StandardPdfPipeline.execute() с InputDocument + page_range=(1,1).
"""
import sys, time
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import InputDocument
from docling.backend.docling_parse_v2_backend import DoclingParseV2DocumentBackend
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.settings import DocumentLimits
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline


pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False
pipeline_options.do_table_structure = True
pipeline_options.table_structure_options.do_cell_matching = True
pipeline_options.accelerator_options.num_threads = 4

pipeline = StandardPdfPipeline(pipeline_options=pipeline_options)

pdf_path = "pdf/2-020101-174-1.pdf"

limits = DocumentLimits(page_range=(1, 1))
in_doc = InputDocument(
    path_or_stream=Path(pdf_path),
    format=InputFormat.PDF,
    backend=DoclingParseV2DocumentBackend,
    limits=limits,
)
print(f"valid={in_doc.valid}, pages={in_doc.page_count}, limits={limits}", file=sys.stderr, flush=True)

if not in_doc.valid:
    print("Document not valid", file=sys.stderr)
    sys.exit(1)

print("Running pipeline.execute()...", file=sys.stderr, flush=True)
t0 = time.time()
result = pipeline.execute(in_doc, raises_on_error=False)
elapsed = time.time() - t0
print(f"Elapsed: {elapsed:.1f}s, Status: {result.status}", file=sys.stderr, flush=True)

if result.document:
    doc = result.document
    print(f"Pages: {len(doc.pages)}", file=sys.stderr)
    for item, level in doc.iterate_items():
        label = getattr(item, "label", "")
        text = getattr(item, "text", "")[:100]
        print(f"  [{level}] {type(item).__name__}: {label} -> {text!r}", file=sys.stderr)
else:
    if hasattr(result, 'errors') and result.errors:
        print("Errors:", result.errors, file=sys.stderr)
