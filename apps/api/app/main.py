from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.routers import auth, crm, quotations, services, territories
from app.seeds.bootstrap import seed_database

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        await seed_database(session)
    yield


app = FastAPI(
    title="Revive My Drive API",
    version="0.1.0",
    description="Regional business operating system — Phase 1 foundation",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

prefix = "/api/v1"
app.include_router(auth.router, prefix=prefix)
app.include_router(territories.router, prefix=prefix)
app.include_router(services.router, prefix=prefix)
app.include_router(crm.router, prefix=prefix)
app.include_router(quotations.router, prefix=prefix)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}