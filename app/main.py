from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import api, views
from app.hardware.bme280 import BME280
from app.hardware.sparkfun import Sparkfun
from app.hardware.tsl2591 import TSL2591
from app.services.database import Database
from app.services.scheduler import Scheduler
from app.services.sensor_service import SensorService

# import app.services.hardware as hardware # Placeholder for your GPIO setup

# --- 1. The Lifespan Manager ---
# This is where you handle Raspberry Pi hardware setup/teardown


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialise SQLite Database
    database = Database()
    database.init()

    # Initialise hardware and sensor service.
    bme280, tsl2591, sparkfun = BME280(), TSL2591(), Sparkfun()
    sensor_service = SensorService(bme280, tsl2591, sparkfun)

    # Initialise scheduler to collect sensor data every minute
    scheduler = Scheduler(sensor_service, database)
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
