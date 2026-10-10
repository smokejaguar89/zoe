import logging
from contextlib import asynccontextmanager
import sys

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import api, views
from app.config import STATIC_DIR
from app.dependencies import get_database, get_scheduler

logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG if you need more verbosity
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

app_logger = logging.getLogger("app")

# Prevent APScheduler from being too noisy (optional but recommended)
logging.getLogger("apscheduler").setLevel(logging.WARNING)

# import app.services.hardware as hardware # Placeholder for your GPIO setup

# --- 1. The Lifespan Manager ---
# This is where you handle Raspberry Pi hardware setup/teardown


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialise SQLite Database
    app_logger.info("Starting up Zoe...")
    database = get_database()
    database.init()

    # Start the scheduler on this event loop: sensor readings every 15
    # minutes and images on the cron schedule
    scheduler = get_scheduler()
    scheduler.start()
    yield
    scheduler.stop()


# --- 2. App Initialization ---
app = FastAPI(title="Zoe", lifespan=lifespan)

# --- 3. Static Files & Templates ---
# This tells FastAPI where to find your CSS, Images, and JS
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# --- 4. Include Routers ---
# This pulls in the code from your other files
app.include_router(views.router)  # HTML pages
app.include_router(api.router)  # JSON API endpoints

# --- 5. Global Middleware (Optional) ---
# If you want to allow a specific local device to bypass CORS
# from fastapi.middleware.cors import CORSMiddleware
# app.add_middleware(CORSMiddleware, allow_origins=["*"])
