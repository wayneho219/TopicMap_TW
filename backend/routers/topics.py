from typing import List
from fastapi import APIRouter, Depends
from backend.services.topic import TopicService
from backend.repositories.topic import TopicRepository
from backend.schemas import TopicSummary, TopicStock

router = APIRouter(prefix='/api/topics', tags=['topics'])


def _svc() -> TopicService:
    import backend.database as _db
    return TopicService(TopicRepository(_db.DB_PATH))


@router.get('', response_model=List[TopicSummary])
def get_topics(level: str = 'medium', svc: TopicService = Depends(_svc)):
    return svc.get_topics(level)


@router.get('/{name}/children', response_model=List[TopicSummary])
def get_topic_children(name: str, svc: TopicService = Depends(_svc)):
    return svc.get_children(name)


@router.get('/{name}/stocks', response_model=List[TopicStock])
def get_topic_stocks(name: str, level: str = 'medium',
                     sort: str = 'heat', order: str = 'desc',
                     svc: TopicService = Depends(_svc)):
    return svc.get_topic_stocks(name, level, sort, order)
