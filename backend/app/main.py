import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routes.candidates import router as candidates_router
from .config import get_llm_provider
from .services import email_sender


app = FastAPI(title="TraqCheck API", version="0.1.0")

_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
allow_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", _default_origins).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "llm_provider": get_llm_provider() or "none (fallback mode)",
        "email_transport": email_sender.active_transport() or "none (log-only)",
    }


app.include_router(candidates_router)
