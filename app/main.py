import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.api import api, views
from app.dependencies import get_database, get_scheduler


app_logger = logging.getLogger("app")
if not app_logger.handlers:
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
    )
    app_logger.addHandler(stream_handler)
app_logger.setLevel(logging.INFO)
app_logger.propagate = False

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

# import app.services.hardware as hardware # Placeholder for your GPIO setup

# --- 1. The Lifespan Manager ---
# This is where you handle Raspberry Pi hardware setup/teardown


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialise SQLite Database
    database = get_database()
    database.init()

    # Initialise scheduler to collect sensor data every minute
    scheduler = get_scheduler()
    scheduler.start()
    yield
    scheduler.stop()


# --- 2. App Initialization ---
app = FastAPI(title="Zoe", lifespan=lifespan)

# --- 3. Static Files & Templates ---
# This tells FastAPI where to find your CSS, Images, and JS
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# --- 4. Include Routers ---
# This pulls in the code from your other files
app.include_router(views.router)  # HTML pages
app.include_router(api.router)  # JSON API endpoints

# --- 5. Global Middleware (Optional) ---
# If you want to allow a specific local device to bypass CORS
# from fastapi.middleware.cors import CORSMiddleware
# app.add_middleware(CORSMiddleware, allow_origins=["*"])
