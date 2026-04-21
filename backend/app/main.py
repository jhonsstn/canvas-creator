from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router, _sweep_abandoned


@asynccontextmanager
async def lifespan(app: FastAPI):
    _sweep_abandoned()
    yield


app = FastAPI(title="Canvas Creator", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
