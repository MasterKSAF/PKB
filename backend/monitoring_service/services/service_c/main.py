import os
import logging
from fastapi import FastAPI
from telemetry_lib.telemetry import setup_observability, instrument_fastapi
import uvicorn
import asyncio
import random
import httpx

app = FastAPI()
service_name = "service-c"
otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "signoz-otel-collector:4317")

tracer_provider, meter_provider, log = setup_observability(service_name, otlp_endpoint=otlp_endpoint)
instrument_fastapi(app, tracer_provider)

meter = meter_provider.get_meter(service_name)
task_counter = meter.create_counter("generation_tasks_total", description="Total generation cycles")
success_counter = meter.create_counter("successful_chains_total", description="Successful A->B chains")
error_counter = meter.create_counter("errors_total", description="Errors during chain")

SERVICE_A_URL = os.getenv("SERVICE_A_URL", "http://service_a:8000")
SERVICE_B_URL = os.getenv("SERVICE_B_URL", "http://service_b:8001")

http_client = httpx.AsyncClient(timeout=5.0)

async def periodic_generator():
    while True:
        delay = random.uniform(5, 15)
        await asyncio.sleep(delay)
        number = random.randint(1, 10)
        log.info(f"Generated number: {number}")
        task_counter.add(1)

        try:
            resp_a = await http_client.post(f"{SERVICE_A_URL}/check", json={"value": number})
            resp_a.raise_for_status()
            status = resp_a.json().get("status")
            log.info(f"Service A returned status: {status}")

            if status == "yes":
                resp_b = await http_client.post(f"{SERVICE_B_URL}/map", json={"value": number})
                resp_b.raise_for_status()
                letter = resp_b.json().get("letter")
                log.info(f"Service B returned letter: {letter} for number {number}")
                success_counter.add(1)
            else:
                log.info(f"Number {number} is odd, not sending to B")

        except httpx.HTTPStatusError as e:
            log.error(f"HTTP error in chain: {e.response.status_code} - {e.response.text}")
            error_counter.add(1, {"error_stage": "A_or_B"})
        except Exception as e:
            log.error(f"Exception in chain: {str(e)}")
            error_counter.add(1, {"error_stage": "general"})

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(periodic_generator())

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.on_event("shutdown")
async def shutdown_event():
    await http_client.aclose()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)