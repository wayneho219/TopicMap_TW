from typing import List
from fastapi import APIRouter, Depends
from backend.services.industry import IndustryService
from backend.repositories.industry import IndustryRepository
from backend.schemas import IndustrySummary, StockSummary, IndustryTopic

router = APIRouter(prefix='/api/market', tags=['industries'])


def _svc() -> IndustryService:
    import backend.database as _db
    return IndustryService(IndustryRepository(_db.DB_PATH, _db.DB_CHAIN_PATH))


@router.get('/industries', response_model=List[IndustrySummary])
def get_industries(sort: str = 'change', order: str = 'desc',
                   svc: IndustryService = Depends(_svc)):
    return svc.get_industries(sort, order)


@router.get('/industry/{name}/stocks', response_model=List[StockSummary])
def get_industry_stocks(name: str, sort: str = 'change', order: str = 'desc',
                        svc: IndustryService = Depends(_svc)):
    return svc.get_industry_stocks(name, sort, order)


@router.get('/industry/{name}/topics', response_model=List[IndustryTopic])
def get_industry_topics(name: str, svc: IndustryService = Depends(_svc)):
    return svc.get_industry_topics(name)
