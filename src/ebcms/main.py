from fastapi import FastAPI

from ebcms.api.routes import auth, clients, operations, reports, rules, trades
from ebcms.config import get_settings
from ebcms.database import init_db

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.9.0",
    description="Authenticated brokerage calculation, trade ingestion, rule management, audit, and reporting APIs.",
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(clients.router)
app.include_router(operations.router)
app.include_router(rules.router)
app.include_router(trades.router)
app.include_router(reports.router)
