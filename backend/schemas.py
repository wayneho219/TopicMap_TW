from pydantic import BaseModel
from typing import Optional


class StockSummary(BaseModel):
    id: str
    name: str
    price: float
    change: float
    changePercent: float
    volume: int


class RankedStock(BaseModel):
    rank: int
    id: str
    name: str
    price: float
    changePercent: float


class StockSearchResult(BaseModel):
    id: str
    name: str
    market: str
    industry: Optional[str]
    price: float
    change: float
    changePercent: float


class StockDetail(BaseModel):
    id: str
    name: str
    price: float
    change: float
    changePercent: float
    volume: int
    market: str
    industry: Optional[str]
    tags: list[str]
    status: str
    high: Optional[float]
    low: Optional[float]
    prevClose: Optional[float]
    open: Optional[float]


class IntradayPoint(BaseModel):
    time: str
    price: float
    volume: int
    pct: float


class SectorSummary(BaseModel):
    name: str
    changePercent: float
    advance: int
    decline: int
    totalVolume: int


class IndustrySummary(BaseModel):
    name: str
    topicCount: int
    advance: int
    decline: int
    changePercent: float
    totalVolume: int
    totalInvested: float


class IndustryTopic(BaseModel):
    name: str
    source: str
    changePercent: float
    stockCount: int


class TopicSummary(BaseModel):
    id: int
    name: str
    level: str
    parentId: Optional[int]
    totalInvested: Optional[float]
    articleCount: Optional[int]
    stockCount: Optional[int]


class TopicStock(BaseModel):
    id: str
    name: str
    price: float
    change: float
    changePercent: float
    volume: int
    articleCount: Optional[int]
    topicInvested: Optional[float]
