from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine, ensure_schema
from app.models import Base
from app.routes import courses, groups, modules, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await ensure_schema(conn)
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)
app.include_router(users.router, prefix="/api")
app.include_router(groups.router, prefix="/api")
app.include_router(courses.router, prefix="/api")
app.include_router(modules.router, prefix="/api")


@app.get("/api/health")
async def health():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("select 1"))
    except SQLAlchemyError:
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return {"status": "ok"}
