from fastapi import APIRouter, Depends
from backend.services.stock import StockService
from backend.repositories.stock import StockRepository
from backend.schemas import (
    StockSummary, StockSearchResult, StockDetail,
    TopicSummary, IntradayPoint
)

router = APIRouter(prefix='/api/stocks', tags=['stocks'])


def _svc() -> StockService:
    import backend.database as _db
    return StockService(StockRepository(_db.DB_PATH))


@router.get('/prices', response_model=list[StockSummary])
def get_stock_prices(ids: str = '', svc: StockService = Depends(_svc)):
    codes = [c.strip() for c in ids.split(',') if c.strip()]
    return svc.get_prices(codes)


@router.get('/search', response_model=list[StockSearchResult])
def search_stocks(q: str = '', svc: StockService = Depends(_svc)):
    return svc.search(q)


@router.get('/{stock_id}/topics', response_model=list[TopicSummary])
def get_stock_topics(stock_id: str, svc: StockService = Depends(_svc)):
    return svc.get_topics(stock_id)


@router.get('/{stock_id}/intraday', response_model=list[IntradayPoint])
def get_intraday(stock_id: str, svc: StockService = Depends(_svc)):
    return svc.get_intraday(stock_id)


@router.get('/{stock_id}', response_model=StockDetail)
def get_stock(stock_id: str, svc: StockService = Depends(_svc)):
    return svc.get_stock(stock_id)
