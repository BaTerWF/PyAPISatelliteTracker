from fastapi import FastAPI, UploadFile, Form, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, JSONResponse,FileResponse
from database import Database
from dotenv import load_dotenv
import os

app = FastAPI()

load_dotenv("config.env")
pg_host = os.getenv("PG_HOST")
pg_port = os.getenv("PG_PORT")
pg_user = os.getenv("PG_USER")
pg_password = os.getenv("PG_PASSWORD")
pg_database = os.getenv("PG_DB")
db = Database()
@app.get("/")
def read_root():
    return {"message": "Welcome to FastAPI project with Database"}