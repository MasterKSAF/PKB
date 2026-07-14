import subprocess, json

r = subprocess.run(["docker", "exec", "pkb-orchestrator", "python", "-c", """
from app.core.config import settings
print("OCR_ENABLED:", settings.services.OCR_ENABLED)
print("PARSER_FALLBACK_TO_OCR:", settings.services.PARSER_FALLBACK_TO_OCR)
print("AUTO_APPROVE_ENABLED:", getattr(settings.pipeline, "AUTO_APPROVE_ENABLED", "?"))
print("QUALITY_OPERATOR_CONFIDENCE_BELOW:", getattr(settings.pipeline, "QUALITY_OPERATOR_CONFIDENCE_BELOW", "?"))
print("QUALITY_REPROCESS_CONFIDENCE_BELOW:", getattr(settings.pipeline, "QUALITY_REPROCESS_CONFIDENCE_BELOW", "?"))
print("AUTO_APPROVE_MAX_CRITICAL:", getattr(settings.pipeline, "AUTO_APPROVE_MAX_CRITICAL", "?"))
print("AUTO_APPROVE_MAX_WARNING:", getattr(settings.pipeline, "AUTO_APPROVE_MAX_WARNING", "?"))
"""], capture_output=True, text=True)
print(r.stdout)
print(r.stderr[:500] if r.stderr else "")
