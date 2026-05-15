from typing import List, Optional
from backend.repositories.market import MarketRepository
from backend.schemas import StockSummary, RankedStock, SectorSummary


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


def _to_stock_summary(r) -> StockSummary:
    return StockSummary(
        id=r['stock_code'],
        name=r['stock_name'],
        price=float(r['close_price']) if r['close_price'] else 0.0,
        change=_parse_float(r['change_val']),
        changePercent=_parse_float(r['change_pct']),
        volume=_parse_volume(r['volume']),
    )


class MarketService:
    def __init__(self, repo: Optional[MarketRepository] = None):
        self._repo = repo or MarketRepository()

    def get_hot(self, sort: str = 'volume', market: str = 'listed',
                stock_type: str = 'stock', limit: int = 10) -> List[StockSummary]:
        rows = self._repo.get_hot(sort, market, stock_type, limit)
        return [_to_stock_summary(r) for r in rows]

    def get_search_hot(self, stock_type: str = 'stock',
                       limit: int = 6) -> List[dict]:
        rows = self._repo.get_search_hot(stock_type, limit)
        return [
            {
                'id':            r['stock_code'],
                'name':          r['stock_name'],
                'price':         float(r['close_price']),
                'change':        _parse_float(r['change_val']),
                'changePercent': _parse_float(r['change_pct']),
            }
            for r in rows
        ]

    def get_recurring(self, limit: int = 15) -> List[RankedStock]:
        rows = self._repo.get_recurring(limit)
        return [
            RankedStock(
                rank=i + 1,
                id=r['stock_code'],
                name=r['stock_name'],
                price=float(r['close_price']),
                changePercent=_parse_float(r['change_pct']),
            )
            for i, r in enumerate(rows)
        ]

    def get_sectors(self, market: str = 'listed', sort: str = 'change',
                    order: str = 'desc') -> List[SectorSummary]:
        rows = self._repo.get_sectors(market, sort, order)
        return [
            SectorSummary(
                name=r['industry_name'],
                changePercent=round(r['avg_chg'] or 0, 2),
                advance=r['up'],
                decline=r['dn'],
                totalVolume=r['total_vol'] or 0,
            )
            for r in rows
        ]

    def get_sector_stocks(self, name: str, sort: str = 'change',
                          order: str = 'desc') -> List[StockSummary]:
        rows = self._repo.get_sector_stocks(name, sort, order)
        return [_to_stock_summary(r) for r in rows]

    def get_chain_stocks(self, name: str, sort: str = 'change',
                         order: str = 'desc') -> List[StockSummary]:
        codes = self._repo.get_chain_codes(name)
        rows = self._repo.get_stocks_by_codes(codes, sort, order)
        return [_to_stock_summary(r) for r in rows]
