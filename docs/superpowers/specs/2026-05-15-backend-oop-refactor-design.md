# Backend OOP Refactor Design

**Date:** 2026-05-15
**Scope:** `backend/` — 835-line monolithic `main.py` → 3-layer OOP architecture
**Constraint:** All API paths and response shapes remain unchanged; frontend requires zero changes.

---

## Motivation

`backend/main.py` is 835 lines with 17 endpoints, no classes, and DB queries embedded directly in route handlers. The refactor introduces a Router / Service / Repository separation and Pydantic response schemas to make the codebase testable, extensible, and demonstrably object-oriented.

---

## Target Directory Structure

```
backend/
├── __init__.py
├── main.py              ← app creation, middleware, router registration only
├── schemas.py           ← all Pydantic response models
├── database.py          ← DB connection context manager + path constants
├── repositories/
│   ├── __init__.py
│   ├── market.py        ← MarketRepository
│   ├── stock.py         ← StockRepository
│   ├── topic.py         ← TopicRepository
│   └── industry.py      ← IndustryRepository
├── services/
│   ├── __init__.py
│   ├── market.py        ← MarketService
│   ├── stock.py         ← StockService
│   ├── topic.py         ← TopicService
│   └── industry.py      ← IndustryService
└── routers/
    ├── __init__.py
    ├── market.py        ← /api/market/* routes
    ├── stocks.py        ← /api/stocks/* routes
    ├── topics.py        ← /api/topics/* routes
    └── industries.py    ← /api/market/industries + /api/market/industry/* routes
```

---

## Layer Responsibilities

### Router
- Declares the FastAPI route and query parameters
- Calls the relevant service method
- Returns a Pydantic response model
- No DB access, no business logic

### Service
- Receives typed inputs; returns Pydantic models
- Orchestrates one or more repository calls
- Handles business logic: data combination, formatting, derived fields
- Raises `HTTPException` when a resource is not found

### Repository
- Accepts a `db_path: str` in `__init__`
- Opens and closes DB connections internally (context manager via `database.py`)
- Returns raw `sqlite3.Row` objects or lists thereof
- No business logic, no HTTP concerns

### schemas.py
- One Pydantic model per distinct response shape
- All fields explicitly typed
- Used as `response_model=` in every route decorator

### database.py
- Defines `DB_PATH` and `DB_CHAIN_PATH` constants (single source of truth)
- Provides a `get_connection(path)` context manager that sets `row_factory = sqlite3.Row`

---

## Domain → Endpoint Mapping

| Domain | Repository | Service | Router file | Endpoints |
|--------|-----------|---------|-------------|-----------|
| Market | `MarketRepository` | `MarketService` | `routers/market.py` | `GET /api/market/hot`, `/search_hot`, `/recurring/tw`, `/sectors`, `/sector/{name}/stocks`, `/chain/{name}/stocks` |
| Stocks | `StockRepository` | `StockService` | `routers/stocks.py` | `GET /api/stocks/prices`, `/search`, `/{id}`, `/{id}/topics`, `/{id}/intraday` |
| Topics | `TopicRepository` | `TopicService` | `routers/topics.py` | `GET /api/topics`, `/topics/{name}/children`, `/topics/{name}/stocks` |
| Industries | `IndustryRepository` | `IndustryService` | `routers/industries.py` | `GET /api/market/industries`, `/industry/{name}/stocks`, `/industry/{name}/topics` |

---

## Key Interfaces

```python
# database.py
DB_PATH = ...
DB_CHAIN_PATH = ...

@contextmanager
def get_connection(path: str) -> Generator[sqlite3.Connection, None, None]: ...

# repositories/stock.py
class StockRepository:
    def __init__(self, db_path: str = DB_PATH): ...
    def find_by_id(self, stock_id: str) -> sqlite3.Row | None: ...
    def search(self, q: str, limit: int = 20) -> list[sqlite3.Row]: ...
    def get_prices(self, codes: list[str]) -> list[sqlite3.Row]: ...
    def get_topics(self, stock_id: str) -> list[sqlite3.Row]: ...

# services/stock.py
class StockService:
    def __init__(self, repo: StockRepository = Depends(...)): ...
    def get_stock(self, stock_id: str) -> StockDetail: ...
    def search(self, q: str) -> list[StockSummary]: ...

# routers/stocks.py
router = APIRouter(prefix="/api/stocks", tags=["stocks"])

@router.get("/{stock_id}", response_model=StockDetail)
def get_stock(stock_id: str, svc: StockService = Depends(get_stock_service)): ...
```

---

## Dependency Injection

Services are injected into routes via FastAPI `Depends`. Each domain has a factory function:

```python
def get_stock_service() -> StockService:
    return StockService(StockRepository())
```

This keeps repositories swappable and units independently testable.

---

## Helper Migration

Existing module-level helpers in `main.py` are relocated as follows:

| Helper | Destination |
|--------|-------------|
| `_parse_float`, `_parse_volume` | `database.py` or `schemas.py` validators |
| `_tags`, `_type_filter`, `_sort_expr` | relevant Repository or Service class (private methods) |
| `_stock_rows_to_list`, `_topic_row` | relevant Service class |
| `SORT_MAP`, `MARKET_MAP`, `MARKET_LABEL`, `YAHOO_SUFFIX` | relevant Repository / Service as class-level constants |

---

## Compatibility Guarantees

- **API paths:** unchanged
- **Response field names and types:** unchanged (verified by existing tests)
- **Existing tests:** `tests/test_backend.py`, `tests/test_industries_api.py`, `tests/test_topics_api.py` continue to pass without modification to test assertions — only import paths may need updating

---

## Out of Scope

- Async (`async def`) routes — not introduced in this refactor
- Authentication / middleware changes
- New endpoints or changed response fields
- Frontend changes
