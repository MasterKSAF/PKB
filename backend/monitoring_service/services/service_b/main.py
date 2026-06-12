import os
import logging
from fastapi import FastAPI, HTTPException
from telemetry_lib.telemetry import setup_observability, instrument_fastapi
import uvicorn

app = FastAPI()
service_name = "service-b"
otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "signoz-otel-collector:4317")

tracer_provider, meter_provider, _ = setup_observability(service_name, otlp_endpoint=otlp_endpoint)
instrument_fastapi(app, tracer_provider)

log = logging.getLogger(service_name)

MAPPING = {1: "а", 2: "б", 4: "г", 5: "д"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/map")
async def map_number(payload: dict):
    number = payload.get("value")
    log.debug(f"Received mapping request for {number}")

    if number not in MAPPING:
        log.error(f"Number {number} not in mapping (causes exception)")
        raise HTTPException(status_code=400, detail="No mapping for this number")

    letter = MAPPING[number]
    log.info(f"Mapped {number} -> {letter}")
    return {"letter": letter}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)