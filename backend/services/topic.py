from typing import List
from fastapi import HTTPException
from backend.repositories.topic import TopicRepository
from backend.schemas import TopicSummary, TopicStock


def _parse_float(val) -> float:
    if val is None:
        return 0.0
    try:
        return float(str(val).replace('+', '').replace('%', ''))
    except ValueError:
        return 0.0


def _parse_volume(val) -> int:
    if val is None:
        return 0
    try:
        return int(float(str(val)))
    except ValueError:
        return 0


def _to_topic_summary(r) -> TopicSummary:
    return TopicSummary(
        id=r['id'],
        name=r['name'],
        level=r['level'],
        parentId=r['parent_id'],
        totalInvested=r['total_invested'],
        articleCount=r['article_count'],
        stockCount=r['stock_count'],
    )


class TopicService:
    def __init__(self, repo: TopicRepository = None):
        self._repo = repo or TopicRepository()

    def get_topics(self, level: str = 'medium') -> List[TopicSummary]:
        if level not in ('medium', 'fine'):
            raise HTTPException(status_code=400, detail='level must be medium or fine')
        return [_to_topic_summary(r) for r in self._repo.get_by_level(level)]

    def get_children(self, name: str) -> List[TopicSummary]:
        parent = self._repo.find_medium_by_name(name)
        if parent is None:
            raise HTTPException(status_code=404, detail=f'Topic "{name}" not found')
        return [_to_topic_summary(r) for r in self._repo.get_children(parent['id'])]

    def get_topic_stocks(self, name: str, level: str = 'medium',
                         sort: str = 'heat', order: str = 'desc') -> List[TopicStock]:
        if level not in ('medium', 'fine'):
            raise HTTPException(status_code=400, detail='level must be medium or fine')
        topic = self._repo.find_by_name_and_level(name, level)
        if topic is None:
            raise HTTPException(status_code=404,
                                detail=f'Topic "{name}" not found at level {level}')
        rows = self._repo.get_topic_stocks(topic['id'], sort, order)
        return [
            TopicStock(
                id=r['stock_code'],
                name=r['stock_name'],
                price=float(r['close_price']),
                change=_parse_float(r['change_val']),
                changePercent=_parse_float(r['change_pct']),
                volume=_parse_volume(r['volume']),
                articleCount=r['article_count'],
                topicInvested=r['total_invested'],
            )
            for r in rows
        ]
