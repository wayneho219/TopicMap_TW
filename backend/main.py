from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import stocks, market, topics, industries

app = FastAPI(title="TopicMap TW")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(stocks.router)
app.include_router(market.router)
app.include_router(topics.router)
app.include_router(industries.router)
