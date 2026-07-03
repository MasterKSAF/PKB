from convertor_validator_service_lama.models.contracts import DryRunResponse, PipelineStep


def build_dry_run_response() -> DryRunResponse:
    steps = [
        PipelineStep(name="llama_parse_source_pdf", description="LlamaParse processes the original source PDF."),
        PipelineStep(name="store_parse_job_id", description="Store parse_job_id and raw parser artifacts."),
        PipelineStep(name="llama_extract_by_parse_job_id", description="Run LlamaExtract passes by parse_job_id.", uses_parse_job_id=True),
        PipelineStep(name="python_validator_assembler", description="Build rich_document_package.json and apply corrections in Python.", uses_parse_job_id=True)
    ]
    return DryRunResponse(planned_steps=steps)
