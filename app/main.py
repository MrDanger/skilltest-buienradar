from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.routes import router as api_router
from app.core.config import get_settings
from app.db.init_db import init_db
from app.db.session import get_db
from app.services.scheduler import ingestion_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    del app
    init_db()
    yield
    ingestion_scheduler.shutdown()


settings = get_settings()
app = FastAPI(title=settings.project_name, lifespan=lifespan)

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

app.include_router(api_router)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    del db
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "default_interval": settings.scheduler_default_interval_minutes},
    )
