from typing import Optional
from fastapi import HTTPException
from backend.repositories.stock import StockRepository
from backend.schemas import (
    StockSummary, StockSearchResult, StockDetail,
    TopicSummary, IntradayPoint
)

MARKET_LABEL = {
    'TWSE_LISTED':   '上市',
    'TPEX_OTC':      '上櫃',
    'TPEX_EMERGING': '興櫃',
}


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


def _tags(market: str) -> list[str]:
    label = MARKET_LABEL.get(market, market)
    return [label, '可現沖'] if market == 'TWSE_LISTED' else [label]


class StockService:
    def __init__(self, repo: Optional[StockRepository] = None):
        self._repo = repo or StockRepository()

    def get_prices(self, codes: list[str]) -> list[StockSummary]:
        rows = self._repo.get_prices(codes)
        order_map = {c: i for i, c in enumerate(codes)}
        result = [
            StockSummary(
                id=r['stock_code'],
                name=r['stock_name'],
                price=float(r['close_price']) if r['close_price'] else 0.0,
                change=_parse_float(r['change_val']),
                changePercent=_parse_float(r['change_pct']),
                volume=_parse_volume(r['volume']),
            )
            for r in rows
        ]
        result.sort(key=lambda x: order_map.get(x.id, 999))
        return result

    def search(self, q: str) -> list[StockSearchResult]:
        rows = self._repo.search(q)
        return [
            StockSearchResult(
                id=r['stock_code'],
                name=r['stock_name'],
                market=r['market'],
                industry=r['industry_name'],
                price=float(r['close_price']) if r['close_price'] is not None else 0.0,
                change=_parse_float(r['change_val']),
                changePercent=_parse_float(r['change_pct']),
            )
            for r in rows
        ]

    def get_stock(self, stock_id: str) -> StockDetail:
        row = self._repo.find_by_id(stock_id)
        if row is None:
            raise HTTPException(status_code=404, detail='Stock not found')
        close = float(row['close_price']) if row['close_price'] is not None else 0.0
        change = _parse_float(row['change_val'])
        prev_close = round(close - change, 2) if close and change else None

        def _opt(val):
            return float(val) if val is not None else None

        return StockDetail(
            id=row['stock_code'],
            name=row['stock_name'],
            price=close,
            change=change,
            changePercent=_parse_float(row['change_pct']),
            volume=_parse_volume(row['volume']),
            market=row['market'],
            industry=row['industry_name'],
            tags=_tags(row['market']),
            status='已收盤',
            high=_opt(row['high_price']),
            low=_opt(row['low_price']),
            prevClose=prev_close,
            open=_opt(row['open_price']),
        )

    def get_topics(self, stock_id: str) -> list[TopicSummary]:
        rows = self._repo.get_topics(stock_id)
        return [
            TopicSummary(
                id=r['id'],
                name=r['name'],
                level=r['level'],
                parentId=r['parent_id'],
                totalInvested=r['total_invested'],
                articleCount=r['article_count'],
                stockCount=r['stock_count'],
            )
            for r in rows
        ]

    def get_intraday(self, stock_id: str) -> list[IntradayPoint]:
        meta = self._repo.get_intraday_meta(stock_id)
        if meta is None:
            raise HTTPException(status_code=404, detail='Stock not found')
        try:
            points = self._repo.fetch_yahoo_intraday(stock_id, meta['market'])
        except Exception as e:
            raise HTTPException(status_code=502, detail=f'Failed to fetch: {e}')
        if not points:
            raise HTTPException(status_code=404, detail='No intraday data')
        return [IntradayPoint(**p) for p in points]
