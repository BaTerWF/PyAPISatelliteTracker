from fastapi import FastAPI, HTTPException, Request, Depends, Query, Cookie
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from loguru import logger
import requests
from dotenv import load_dotenv
import os
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session

# Local imports
from TLE import get_orbit_and_position
from ayth import auth_router
from database import get_db
from models import Satellite, User, AuthToken, UserSatellite

# Initialize FastAPI
app = FastAPI()
app.include_router(auth_router, prefix="/auth")

# Configuration
templates = Jinja2Templates(directory="html")
load_dotenv("config.env")
TLE_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"

# Logger setup
logger.add("satellites_log.log", level="DEBUG", encoding="utf-8")


@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    try:
        from database import create_tables
        create_tables()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# Ваши существующие эндпоинты
@app.get("/", response_class=HTMLResponse)
async def main_page(request: Request):
    return templates.TemplateResponse("main.html", {"request": request})


@app.get("/fetch_tle")
async def fetch_tle(db: Session = Depends(get_db)):
    """Fetch and update TLE data from external source"""
    try:
        response = requests.get(TLE_URL)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error loading TLE data")

        tle_data = response.text.splitlines()
        for i in range(0, len(tle_data), 3):
            if i + 2 >= len(tle_data):
                break

            satellite_name = tle_data[i].strip()
            line1 = tle_data[i + 1].strip()
            line2 = tle_data[i + 2].strip()
            norad_id = line2.split()[1]

            # Upsert satellite data
            satellite = db.query(Satellite).filter(Satellite.norad_id == norad_id).first()
            if not satellite:
                satellite = Satellite(
                    norad_id=norad_id,
                    name=satellite_name,
                    tle_line1=line1,
                    tle_line2=line2
                )
                db.add(satellite)
            else:
                satellite.tle_line1 = line1
                satellite.tle_line2 = line2
                satellite.updated_at = datetime.utcnow()

            db.commit()

        return {"status": "TLE data updated successfully"}

    except Exception as e:
        logger.error(f"TLE update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/track_satellite/{norad_id}")
async def track_satellite(
    norad_id: str,
    db: Session = Depends(get_db),
    auth_token: str = Cookie(None, alias="auth_token")
):
    """Track satellite for authenticated user"""
    if not auth_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).join(AuthToken).filter(
        AuthToken.token == auth_token,
        AuthToken.expires_at > datetime.utcnow()
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    satellite = db.query(Satellite).filter(Satellite.norad_id == norad_id).first()
    if not satellite:
        raise HTTPException(status_code=404, detail="Satellite not found")

    # Проверяем существующую связь
    existing = db.query(UserSatellite).filter_by(
        user_id=user.id,
        norad_id=norad_id
    ).first()

    if not existing:
        new_tracking = UserSatellite(
            user_id=user.id,
            norad_id=norad_id,
            created_at=datetime.utcnow()
        )
        db.add(new_tracking)
        db.commit()

    return {"status": f"Tracking satellite {norad_id}"}

@app.get("/get_all_satellites")
async def get_all_satellites(db: Session = Depends(get_db)):
    """
    Получение списка всех спутников из базы данных
    """
    try:
        satellites = db.query(Satellite).all()
        return [
            {
                "norad_id": sat.norad_id,
                "name": sat.name,
                "tle_line1": sat.tle_line1,
                "tle_line2": sat.tle_line2,
                "updated_at": sat.updated_at.isoformat()
            }
            for sat in satellites
        ]
    except Exception as e:
        logger.error(f"Error fetching satellites: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/my_satellites")
async def get_my_satellites(
        db: Session = Depends(get_db),
        auth_token: str = Cookie(None, alias="auth_token")
):
    """Get tracked satellites for authenticated user"""
    user = db.query(User).join(AuthToken).filter(AuthToken.token == auth_token).first()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return {
        "tracked_satellites": [
            {
                "norad_id": sat.norad_id,
                "name": sat.name,
                "last_update": sat.updated_at.isoformat()
            }
            for sat in user.satellites
        ]
    }


@app.get("/orbit_data")
async def get_orbit_data(
        norad_ids: str = Query(..., description="Comma-separated NORAD IDs"),
        db: Session = Depends(get_db),
        auth_token: str = Cookie(None, alias="auth_token")
):
    try:
        if not auth_token:
            raise HTTPException(status_code=401, detail="Not authenticated")

        # Получаем список NORAD ID
        norad_list = norad_ids.split(',')

        satellites_data = []
        for norad_id in norad_list:
            satellite = db.query(Satellite).filter(Satellite.norad_id == norad_id).first()
            if not satellite:
                continue

            try:
                orbit_data = get_orbit_and_position(
                    satellite.tle_line1,
                    satellite.tle_line2,
                    datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error processing {norad_id}: {str(e)}")
                continue

            satellites_data.append({
                "norad_id": satellite.norad_id,
                "name": satellite.name,
                "orbit_data": orbit_data
            })

        return {"satellites": satellites_data}

    except Exception as e:
        logger.error(f"Error in orbit_data endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/satellite/{norad_id}")
async def get_single_satellite(
    norad_id: str,
    db: Session = Depends(get_db),
    auth_token: str = Cookie(None, alias="auth_token")
):
    if not auth_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    satellite = db.query(Satellite).filter(Satellite.norad_id == norad_id).first()
    if not satellite:
        raise HTTPException(status_code=404, detail="Satellite not found")

    try:
        orbit_data = get_orbit_and_position(
            satellite.tle_line1,
            satellite.tle_line2,
            datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Error processing {norad_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error calculating orbit")

    return {
        "norad_id": satellite.norad_id,
        "name": satellite.name,
        "orbit_data": orbit_data,
        "position": orbit_data.get("position", {})
    }

@app.post("/untrack_satellite/{norad_id}")
async def untrack_satellite(
    norad_id: str,
    db: Session = Depends(get_db),
    auth_token: str = Cookie(None, alias="auth_token")
):
    if not auth_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).join(AuthToken).filter(
        AuthToken.token == auth_token,
        AuthToken.expires_at > datetime.utcnow()
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Удаляем связь пользователя со спутником
    tracking = db.query(UserSatellite).filter_by(
        user_id=user.id,
        norad_id=norad_id
    ).first()

    if tracking:
        db.delete(tracking)
        db.commit()

    return {"status": f"Stopped tracking satellite {norad_id}"}


@app.get("/display_maps", response_class=HTMLResponse)
async def display_maps(request: Request):
    """Map display endpoint"""
    return templates.TemplateResponse("index.html", {"request": request})