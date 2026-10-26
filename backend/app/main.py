import os
from urllib.parse import quote_plus

import psycopg
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()


def database_url() -> str:
    user = quote_plus(os.environ["POSTGRES_USER"])
    password = quote_plus(os.environ["POSTGRES_PASSWORD"])
    host = os.environ.get("POSTGRES_HOST", "localhost")
    database = quote_plus(os.environ["POSTGRES_DB"])
    return f"postgresql://{user}:{password}@{host}:5432/{database}"


@app.get("/api/health")
def health():
    try:
        with psycopg.connect(database_url(), connect_timeout=3) as conn:
            conn.execute("select 1")
    except psycopg.Error:
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return {"status": "ok"}
