from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from loguru import logger
import requests
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from sgp4.api import Satrec
from astropy.time import Time as AstroPyTime
from astropy.coordinates import TEME, ITRS, CartesianRepresentation
from astropy import units as u
from database import Database
from TLE import get_orbit_and_position
from typing import List
from fastapi import Query

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

db = Database(pg_host, pg_database, pg_user, pg_password, pg_port)
TLE_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"

app = FastAPI()
logger.add("satellites_log.log", level="DEBUG", encoding="utf-8")


@app.get("/")
def read_root(request: Request):
    return html.TemplateResponse("main.html", {"request": request})


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

@app.get("/get_all_satelite")
async def get_all_satelite():
    result = db.get_all_satellites()
    return result

@app.get("/get_orbit_data")
async def get_orbit_data(norad_ids: List[str] = Query(...)):
    try:
        # Получаем TLE-данные для списка NORAD ID
        satellite_tle = db.get_tle_by_norad(norad_ids)  # Передаем список NORAD ID
        if not satellite_tle:
            raise HTTPException(status_code=404, detail="Satellites not found")

        orbit_data_list = []

        # Для каждого NORAD ID извлекаем данные TLE и орбитальные параметры
        for norad_id in norad_ids:
            if norad_id not in satellite_tle:
                continue  # Пропускаем если спутник не найден

            tle_line1, tle_line2 = satellite_tle[norad_id]
            current_time = datetime.utcnow()

            # Вычисляем орбитальные данные
            orbit_data = get_orbit_and_position(tle_line1, tle_line2, current_time)
            orbit_data_list.append({
                "norad_id": norad_id,
                "orbit_data": orbit_data
            })

        return JSONResponse(content={"satellites": orbit_data_list})
    except Exception as e:
        logger.error(f"Error fetching orbit data for NORAD IDs {norad_ids}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching orbit data: {str(e)}")



@app.post("/remove_orbit_data/{norad_id}")
async def remove_orbit_data(norad_id: str):
    # Если требуется специфическая логика на сервере
    logger.info(f"Removing orbit data for NORAD ID {norad_id}")
    return {"status": "success", "norad_id": norad_id}

@app.get("/display_maps", response_class=HTMLResponse)
async def display_maps(request: Request):
    return html.TemplateResponse("index.html", {"request": request})
