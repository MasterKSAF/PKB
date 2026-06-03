"""
Gateway Service — единая точка входа для веб-интерфейса.
Объединяет все микросервисы на порту 8081.
Явно проксирует запросы к нужным сервисам.
"""
import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(
    title="PKB Neuroassistant Gateway",
    version="1.0.0",
    description="Единый шлюз для веб-интерфейса"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Адреса внутренних сервисов
AUTH_SERVICE = "http://127.0.0.1:8082"
QUERY_SERVICE = "http://127.0.0.1:8083"
REGISTRY_SERVICE = "http://127.0.0.1:8084"
ORCH_SERVICE = "http://127.0.0.1:8081"  

# Общий прокси-метод
async def proxy_request(service_url: str, request: Request):
    path = request.url.path.replace("/api/v1", "", 1) if request.url.path.startswith("/api/v1") else request.url.path
    url = f"{service_url}/api/v1{path}" if not path.startswith("/api/v1") else f"{service_url}{path}"
    params = dict(request.query_params)
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")}
    body = await request.body()
    async with httpx.AsyncClient() as client:
        resp = await client.request(
            method=request.method,
            url=url,
            params=params,
            headers=headers,
            content=body,
        )
    return JSONResponse(
        status_code=resp.status_code,
        content=resp.json() if resp.status_code != 204 else None,
        headers=dict(resp.headers),
    )

# ── Auth: /api/v1/auth/*, /api/v1/admin/*, /api/v1/internal/*
@app.api_route("/api/v1/auth/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_auth(path: str, request: Request):
    return await proxy_request(AUTH_SERVICE, request)

@app.api_route("/api/v1/admin/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_admin(path: str, request: Request):
    return await proxy_request(AUTH_SERVICE, request)

@app.api_route("/api/v1/internal/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_internal(path: str, request: Request):
    return await proxy_request(AUTH_SERVICE, request)

# ── Query: /api/v1/chat/*, /api/v1/text/*
@app.api_route("/api/v1/chat/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_chat(path: str, request: Request):
    return await proxy_request(QUERY_SERVICE, request)

@app.api_route("/api/v1/text/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_text(path: str, request: Request):
    return await proxy_request(QUERY_SERVICE, request)

# ── Registry: /api/v1/classifiers/*, /api/v1/terminology/*, /api/v1/documents (реестр), /api/v1/stats, /api/v1/enums
@app.api_route("/api/v1/classifiers/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_classifiers(path: str, request: Request):
    return await proxy_request(REGISTRY_SERVICE, request)

@app.api_route("/api/v1/terminology/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_terminology(path: str, request: Request):
    return await proxy_request(REGISTRY_SERVICE, request)

@app.get("/api/v1/stats")
async def proxy_stats(request: Request):
    return await proxy_request(REGISTRY_SERVICE, request)

@app.get("/api/v1/enums")
async def proxy_enums(request: Request):
    return await proxy_request(REGISTRY_SERVICE, request)

# ── Orchestrator: /api/v1/documents/* (публичные), /api/v1/search, /api/v1/monitor/*, /api/v1/system/*
@app.api_route("/api/v1/documents/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_documents(path: str, request: Request):
    return await proxy_request(ORCH_SERVICE, request)

@app.api_route("/api/v1/search/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_search(path: str, request: Request):
    return await proxy_request(ORCH_SERVICE, request)

@app.api_route("/api/v1/monitor/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_monitor(path: str, request: Request):
    return await proxy_request(ORCH_SERVICE, request)

@app.api_route("/api/v1/system/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_system(path: str, request: Request):
    return await proxy_request(ORCH_SERVICE, request)

# Health
@app.get("/health")
async def health():
    return {"status": "ok", "service": "gateway", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)