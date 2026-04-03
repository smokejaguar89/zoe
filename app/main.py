from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.api import api, views
from app.hardware.bme280_driver import BME280Driver
from app.hardware.sparkfun_driver import SparkfunDriver
from app.hardware.tsl2591_driver import TSL2591Driver
from app.db.database import Database
from app.scheduler.scheduler import Scheduler
from app.clients.gemini_client import GeminiClient
from app.services.image_generation_service import ImageGenerationService
from app.services.sensor_service import SensorService

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

# import app.services.hardware as hardware # Placeholder for your GPIO setup

# --- 1. The Lifespan Manager ---
# This is where you handle Raspberry Pi hardware setup/teardown


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialise SQLite Database
    database = Database()
    database.init()

    # Initialise hardware and sensor service.
    bme280 = BME280Driver()
    tsl2591 = TSL2591Driver()
    sparkfun = SparkfunDriver()
    sensor_service = SensorService(bme280, tsl2591, sparkfun)
    gemini_client = GeminiClient()
    image_generation_service = ImageGenerationService(
        sensor_service=sensor_service,
        image_client=gemini_client,
        database=database,
    )

    # Initialise scheduler to collect sensor data every minute
    scheduler = Scheduler(sensor_service, database, image_generation_service)
    scheduler.start()
    yield
    scheduler.stop()

# --- 2. App Initialization ---
app = FastAPI(
    title="Pi Sensor Hub",
    lifespan=lifespan
)

# --- 3. Static Files & Templates ---
# This tells FastAPI where to find your CSS, Images, and JS
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# --- 4. Include Routers ---
# This pulls in the code from your other files
app.include_router(views.router)      # HTML pages
app.include_router(api.router)    # JSON API endpoints

# --- 5. Global Middleware (Optional) ---
# If you want to allow a specific local device to bypass CORS
# from fastapi.middleware.cors import CORSMiddleware
# app.add_middleware(CORSMiddleware, allow_origins=["*"])
