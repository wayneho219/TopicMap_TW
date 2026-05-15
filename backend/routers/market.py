from fastapi import APIRouter, Depends
from backend.services.market import MarketService
from backend.schemas import StockSummary, RankedStock, SectorSummary
from typing import List

router = APIRouter(prefix='/api/market', tags=['market'])


def _svc() -> MarketService:
    return MarketService()


@router.get('/hot', response_model=List[StockSummary])
def get_market_hot(sort: str = 'volume', market: str = 'listed',
                   stock_type: str = 'stock', limit: int = 10,
                   svc: MarketService = Depends(_svc)):
    return svc.get_hot(sort, market, stock_type, limit)


@router.get('/search_hot')
def get_search_hot(stock_type: str = 'stock', limit: int = 6,
                   svc: MarketService = Depends(_svc)):
    return svc.get_search_hot(stock_type, limit)


@router.get('/recurring/tw', response_model=List[RankedStock])
def get_recurring_tw(limit: int = 15, svc: MarketService = Depends(_svc)):
    return svc.get_recurring(limit)


@router.get('/sectors', response_model=List[SectorSummary])
def get_sectors(market: str = 'listed', sort: str = 'change',
                order: str = 'desc', svc: MarketService = Depends(_svc)):
    return svc.get_sectors(market, sort, order)


@router.get('/sector/{name}/stocks', response_model=List[StockSummary])
def get_sector_stocks(name: str, sort: str = 'change', order: str = 'desc',
                      svc: MarketService = Depends(_svc)):
    return svc.get_sector_stocks(name, sort, order)


@router.get('/chain/{name}/stocks', response_model=List[StockSummary])
def get_chain_stocks(name: str, sort: str = 'change', order: str = 'desc',
                     svc: MarketService = Depends(_svc)):
    return svc.get_chain_stocks(name, sort, order)
