from contextlib import asynccontextmanager
from pathlib import Path

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import db


ROOT = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.initialize_database()
    yield


app = FastAPI(title="FUDO Plus", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/products")
def products():
    try:
        return db.list_published_products()
    except (psycopg.Error, RuntimeError) as error:
        raise HTTPException(status_code=503, detail="El menú no está disponible por ahora.") from error


@app.get("/ready", include_in_schema=False)
def ready():
    try:
        db.database_is_ready()
    except (psycopg.Error, RuntimeError) as error:
        raise HTTPException(status_code=503, detail="Base de datos no disponible") from error
    return {"status": "ok"}
