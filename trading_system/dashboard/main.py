import os
from pathlib import Path

import httpx
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

BOT_URL = os.getenv("BOT_URL", "http://127.0.0.1:8000")
app = FastAPI(title="Trading Dashboard")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def _auth_header(request: Request) -> dict[str, str]:
    token = request.cookies.get("dashboard_token", "")
    return {"Authorization": f"Bearer {token}"} if token else {}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "dashboard"}


@app.get("/metrics")
async def metrics() -> HTMLResponse:
    return HTMLResponse(generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("login.html", {"request": request, "error": ""})


@app.post("/login")
async def login(request: Request, token: str = Form("")) -> HTMLResponse | RedirectResponse:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(f"{BOT_URL}/health")
        if response.status_code != 200:
            return templates.TemplateResponse("login.html", {"request": request, "error": "Bot unavailable"})
    redirect = RedirectResponse(url="/", status_code=303)
    redirect.set_cookie("dashboard_token", token, httponly=True, samesite="strict")
    return redirect


@app.post("/logout")
async def logout() -> RedirectResponse:
    redirect = RedirectResponse(url="/login", status_code=303)
    redirect.delete_cookie("dashboard_token")
    return redirect


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse | RedirectResponse:
    headers = _auth_header(request)
    if not headers:
        return RedirectResponse(url="/login", status_code=303)
    async with httpx.AsyncClient(timeout=10) as client:
        controls_response = await client.get(f"{BOT_URL}/controls", headers=headers)
        audit_response = await client.get(f"{BOT_URL}/audit", headers=headers)
    if controls_response.status_code != 200:
        return RedirectResponse(url="/login", status_code=303)
    controls = controls_response.json()
    audit = audit_response.json() if audit_response.status_code == 200 else []
    return templates.TemplateResponse(
        "index.html", {"request": request, "controls": controls, "audit": audit}
    )


@app.post("/controls")
async def controls(
    request: Request,
    tactical_earnings_enabled: bool = Form(False),
    drift_enabled: bool = Form(False),
    wheel_enabled: bool = Form(False),
    risk_mode: str = Form("normal"),
    kill_switch: bool = Form(False),
    whitelist: str = Form(""),
    blacklist: str = Form(""),
) -> RedirectResponse:
    payload = {
        "tactical_earnings_enabled": tactical_earnings_enabled,
        "drift_enabled": drift_enabled,
        "wheel_enabled": wheel_enabled,
        "risk_mode": risk_mode,
        "kill_switch": kill_switch,
        "whitelist": [x.strip().upper() for x in whitelist.split(",") if x.strip()],
        "blacklist": [x.strip().upper() for x in blacklist.split(",") if x.strip()],
    }
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(f"{BOT_URL}/controls", json=payload, headers=_auth_header(request))
    return RedirectResponse(url="/", status_code=303)


@app.post("/run-cycle")
async def run_cycle(request: Request) -> RedirectResponse:
    async with httpx.AsyncClient(timeout=20) as client:
        await client.post(f"{BOT_URL}/run-cycle", headers=_auth_header(request))
    return RedirectResponse(url="/", status_code=303)
