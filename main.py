from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from loguru import logger
import requests
from dotenv import load_dotenv
import os
from database import Database
from TLE import TLEConverter
from skyfield.api import load, EarthSatellite
from astropy.time import Time
from astropy.coordinates import EarthLocation, GCRS, ITRS
from astropy import units as u
import numpy as np
from datetime import datetime, timedelta

html = Jinja2Templates(directory="html")
load_dotenv("config.env")
pg_host = os.getenv("PG_HOST")
pg_port = os.getenv("PG_PORT")
pg_user = os.getenv("PG_USER")
pg_password = os.getenv("PG_PASSWORD")
pg_database = os.getenv("PG_DB")
if not pg_host:
    raise Exception("PG_HOST env not set")
if not pg_user:
    raise Exception("PG_USER env not set")
if not pg_password:
    raise Exception("PG_PASSWORD env not set")
if not pg_database:
    pg_database = 'postgres'
if not pg_port:
    pg_port = '5432'

#поменяйте конфиг и больше его не коммитте
db = Database(pg_host, pg_database, pg_user, pg_password, pg_port)
TLE_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"

app = FastAPI()
logger.add("stalites_log.log", level="DEBUG", encoding="utf-8")

@app.get("/")
def read_root():
    return {"message": "First endpoint"}


@app.get("/fetch_tle")
def fetch_tle():

    try:
        response = requests.get(TLE_URL)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Ошибка загрузки данных TLE")

        tle_data = response.text.splitlines()
        for i in range(0, len(tle_data), 3):
            satellite_name = tle_data[i].strip()
            line1 = tle_data[i+1].strip()
            line2 = tle_data[i+2].strip()

            db.insert_tle(satellite_name, line1, line2)

        return {"status": "Данные успешно загружены и сохранены"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@app.get("/get_satellite")
async def get_tle(satelliteName:str = None, noradID:str = None):
    result = db.get_tle_by_name_or_norad(satelliteName=satelliteName)
    return result

@app.get("/convert_TLE")
async def convert(satelliteName: str = None, noradID: str = None, Time = 1, step_minutes = 5):
    satelliteTle = await get_tle(satelliteName=satelliteName, noradID=noradID)
    tle_line1 = satelliteTle['line1']
    tle_line2 = satelliteTle['line2']
    converter = TLEConverter(tle_line1, tle_line2)
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(hours=int(Time))
    orbit_data = converter.calculate_orbit(start_time, end_time, step_minutes=int(step_minutes))
    TrackSatelite = []
    for coord in orbit_data:
        TrackSatelite.append({"lat": coord[0], "lon": coord[1], "alt": coord[2]})
    print(TrackSatelite)

    return TrackSatelite

@app.get("/display_maps", response_class=HTMLResponse)
async def display_maps(request: Request):
    return html.TemplateResponse("index.html", {"request": request})


