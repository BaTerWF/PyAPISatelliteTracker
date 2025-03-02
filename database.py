import os
import psycopg2 as psdb
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from loguru import logger
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

# Настройки для подключения к базе данных
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:1234@localhost/staelite?options=-csearch_path%3Dsatelite"

# Создание базового класса для моделей
Base = declarative_base()

# Настройка соединения
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"options": "-csearch_path=public"})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    try:
        with engine.connect() as conn:
            conn.execute("CREATE SCHEMA IF NOT EXISTS satelite")
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise e


