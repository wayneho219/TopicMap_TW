from typing import List
from backend.repositories.industry import IndustryRepository
from backend.schemas import StockSummary, IndustrySummary, IndustryTopic


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


class IndustryService:
    def __init__(self, repo: IndustryRepository = None):
        self._repo = repo or IndustryRepository()

    def get_industries(self, sort: str = 'change',
                       order: str = 'desc') -> List[IndustrySummary]:
        rows, industry_codes = self._repo.get_industries(sort, order)
        all_codes = list({c for codes in industry_codes.values() for c in codes})
        nlp_counts = self._repo.get_nlp_counts(all_codes, industry_codes)
        chain_counts = self._repo.get_chain_counts(all_codes, industry_codes)
        return [
            IndustrySummary(
                name=r['industry_name'],
                topicCount=chain_counts.get(r['industry_name'], 0)
                           + nlp_counts.get(r['industry_name'], 0),
                advance=r['up'],
                decline=r['dn'],
                changePercent=round(r['avg_chg'] or 0, 2),
                totalVolume=r['total_vol'] or 0,
                totalInvested=0.0,
            )
            for r in rows
        ]

    def get_industry_stocks(self, name: str, sort: str = 'change',
                            order: str = 'desc') -> List[StockSummary]:
        rows = self._repo.get_industry_stocks(name, sort, order)
        return [
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

    def get_industry_topics(self, name: str) -> List[IndustryTopic]:
        industry_codes = self._repo.get_industry_stock_codes(name)
        if not industry_codes:
            return []

        nlp_rows = self._repo.get_nlp_topics_for_codes(industry_codes)
        nlp_names = {r['id']: r['name'] for r in nlp_rows}
        nlp_stock_cnt = {r['id']: r['stock_count'] for r in nlp_rows}
        nlp_stock_map = self._repo.get_nlp_stock_map(list(nlp_names.keys()))

        all_price_codes = list(
            set(industry_codes) | {c for s in nlp_stock_map.values() for c in s}
        )
        price_map = self._repo.get_price_map(all_price_codes)
        chain_topics = self._repo.get_chain_topics_for_codes(industry_codes)

        results: List[IndustryTopic] = []

        for chain_topic, codes in chain_topics.items():
            changes = [price_map[c] for c in codes if c in price_map]
            avg_chg = round(sum(changes) / len(changes), 2) if changes else 0.0
            results.append(IndustryTopic(
                name=chain_topic,
                source='tpex',
                changePercent=avg_chg,
                stockCount=len(codes),
            ))

        for tid, tname in nlp_names.items():
            codes = nlp_stock_map.get(tid, set())
            changes = [price_map[c] for c in codes if c in price_map]
            avg_chg = round(sum(changes) / len(changes), 2) if changes else 0.0
            results.append(IndustryTopic(
                name=tname,
                source='nlp',
                changePercent=avg_chg,
                stockCount=nlp_stock_cnt.get(tid, len(codes)),
            ))

        results.sort(key=lambda x: abs(x.changePercent), reverse=True)
        return results
