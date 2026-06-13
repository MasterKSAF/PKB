import os
import logging
from fastapi import FastAPI, HTTPException
from telemetry_lib.telemetry import setup_observability, instrument_fastapi
import uvicorn

app = FastAPI()
service_name = "service-a"
otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "signoz-otel-collector:4317")

tracer_provider, meter_provider, _ = setup_observability(service_name, otlp_endpoint=otlp_endpoint)
instrument_fastapi(app, tracer_provider)

log = logging.getLogger(service_name)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/check")
async def check_number(payload: dict):
    number = payload.get("value")
    log.debug(f"Received number: {number}")
    
    if not (1 <= number <= 5):
        log.exception(f"Number out of range [1,5]: {number}")
        raise HTTPException(status_code=400, detail="Number out of range")
    
    status = "yes" if number % 2 == 0 else "no"
    log.info(f"Check {number}: {status}")
    return {"status": status}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)