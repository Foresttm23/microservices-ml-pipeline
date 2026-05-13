import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from frontend.core.config import get_settings
from shared.core.logging import setup_logging

app = FastAPI()

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    settings = get_settings()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "gateway_url": settings.GATEWAY_CLIENT_URL,
            "gateway_ws_url": settings.GATEWAY_CLIENT_WS_URL,
        },
    )


def main():
    setup_logging()
    port = int(os.getenv("PORT", 8004))
    uvicorn.run("frontend.main:app", host="0.0.0.0", port=port, reload=True)


if __name__ == "__main__":
    main()
