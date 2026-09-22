import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.config import settings
from app.routers import chat, eligibility, meta, schemes
from app.services import ai_service, scheme_store


logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

log = logging.getLogger("jansaathi")


@asynccontextmanager
async def lifespan(_: FastAPI):
    log.info(ai_service.startup_report())
    log.info(
        "Loaded %d schemes",
        len(scheme_store.load_schemes())
    )
    yield


app = FastAPI(
    title="JanSaathi API",
    description="Multilingual assistant API for discovering Punjab government schemes.",
    version=__version__,
    lifespan=lifespan,
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "http://localhost:5173",
#         "http://127.0.0.1:5173",
#     ],
#     allow_credentials=True,
#     allow_methods=["GET", "POST", "OPTIONS"],
#     allow_headers=["*"],
# )


# ---------------------------------------------------------
# API ROUTES
# ---------------------------------------------------------

app.include_router(meta.router)
app.include_router(chat.router)
app.include_router(schemes.router)
app.include_router(eligibility.router)


# ---------------------------------------------------------
# FRONTEND - production only
# ---------------------------------------------------------

_static = Path(settings.static_dir)

if _static.is_dir() and (_static / "index.html").exists():
    app.mount(
        "/",
        StaticFiles(directory=_static, html=True),
        name="site",
    )

    log.info("Serving frontend from %s", _static)