# ARCHITECTURE.md - Stock Advisor v2.0 System Architecture

| Field | Value |
|-------|-------|
| Document Version | v1.1 |
| Created | 2026-02-09 |
| Updated | 2026-02-09 |
| Author | System Architect |
| Status | Draft (Revised - QA Fixes Applied) |
| Based On | PRD v2.0 (91/100, QA Approved) |
| Project Location | `projects/software/stock-advisor/` |

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Backend Architecture Design](#2-backend-architecture-design)
3. [Frontend Architecture Design](#3-frontend-architecture-design)
4. [Database Architecture](#4-database-architecture)
5. [Security Architecture](#5-security-architecture)
6. [Performance Optimization Design](#6-performance-optimization-design)
7. [Monitoring and Logging](#7-monitoring-and-logging)
8. [Development and Deployment](#8-development-and-deployment)
9. [Technical Risks and Mitigations](#9-technical-risks-and-mitigations)
10. [PRD Feature Mapping](#10-prd-feature-mapping)

---

## 1. System Architecture Overview

### 1.1 High-Level Architecture Diagram

```
                        +---------------------------+
                        |     User Devices          |
                        |  Mobile / Desktop Browser |
                        +---------------------------+
                                    |
                                    | HTTPS
                                    v
        +---------------------------------------------------+
        |                  Netlify CDN                       |
        |  +---------------------------------------------+  |
        |  |  Next.js 15 (Static Export / SSG)           |  |
        |  |  React 18 + TypeScript + Tailwind CSS       |  |
        |  |                                             |  |
        |  |  Pages:                                     |  |
        |  |    / (Home - Recommendations + Watchlist)   |  |
        |  |    /stock/[code] (Comprehensive Analysis)   |  |
        |  |    /history/[code] (Historical Review)      |  |
        |  |    /settings (Device ID, Export/Import)     |  |
        |  |                                             |  |
        |  |  Client-Side State:                         |  |
        |  |    localStorage (device UUID)               |  |
        |  |    React Context (watchlist, token usage)   |  |
        |  |    In-memory cache (API responses, 3 min)   |  |
        |  +---------------------------------------------+  |
        +---------------------------------------------------+
                                    |
                          HTTPS REST API + SSE
                       X-Device-ID header on all requests
                                    |
                                    v
        +---------------------------------------------------+
        |              Render (Backend Server)               |
        |  +---------------------------------------------+  |
        |  |  FastAPI 0.109 + Python 3.11                |  |
        |  |                                             |  |
        |  |  +---------------------------------------+  |  |
        |  |  |          API Router Layer             |  |  |
        |  |  |  /api/v1/stock/*                      |  |  |
        |  |  |  /api/v1/watchlist/*                   |  |  |
        |  |  |  /api/v1/refresh/*                     |  |  |
        |  |  |  /api/v1/analysis/*                    |  |  |
        |  |  |  /api/v1/token/*                       |  |  |
        |  |  |  /api/v1/device/*                      |  |  |
        |  |  |  /api/v1/recommendations/*             |  |  |
        |  |  |  /api/v1/industry/*                    |  |  |
        |  |  +---------------------------------------+  |  |
        |  |                    |                        |  |
        |  |  +---------------------------------------+  |  |
        |  |  |         Service Layer                 |  |  |
        |  |  |  comprehensive_analysis_service       |  |  |
        |  |  |  news_service                         |  |  |
        |  |  |  fundamental_service                  |  |  |
        |  |  |  industry_service                     |  |  |
        |  |  |  watchlist_service                    |  |  |
        |  |  |  prediction_tracking_service          |  |  |
        |  |  |  analysis_history_service             |  |  |
        |  |  |  token_monitor_service                |  |  |
        |  |  |  rate_limiter_service                 |  |  |
        |  |  |  indicator_service (existing)         |  |  |
        |  |  |  strategy_service (existing)          |  |  |
        |  |  |  glm_service (existing, extended)     |  |  |
        |  |  +---------------------------------------+  |  |
        |  |                    |                        |  |
        |  |  +---------------------------------------+  |  |
        |  |  |      Data Access / Client Layer       |  |  |
        |  |  |  eastmoney_client (quotes, news)      |  |  |
        |  |  |  akshare_client (earnings, industry)  |  |  |
        |  |  |  yahoo_client (fallback)              |  |  |
        |  |  |  glm4_client (AI analysis)            |  |  |
        |  |  |  supabase_dao (all DB operations)     |  |  |
        |  |  +---------------------------------------+  |  |
        |  |                    |                        |  |
        |  |  +---------------------------------------+  |  |
        |  |  |     Infrastructure Layer              |  |  |
        |  |  |  in_memory_cache (TTLCache)           |  |  |
        |  |  |  rate_limiter (per-source semaphore)  |  |  |
        |  |  |  circuit_breaker (per-source)         |  |  |
        |  |  |  scheduler (APScheduler)              |  |  |
        |  |  +---------------------------------------+  |  |
        |  +---------------------------------------------+  |
        +---------------------------------------------------+
              |              |              |
              v              v              v
    +-----------+    +------------+   +----------------+
    | Supabase  |    |  AKShare   |   | External APIs  |
    | PostgreSQL|    |  (Python   |   |                |
    |           |    |   library) |   | EastMoney HTTP |
    | Tables:   |    +------------+   | EastMoney News |
    | watchlist |                      | GLM-4 (Zhipu) |
    | analysis  |                      | Yahoo Finance  |
    | prediction|                      +----------------+
    | tokens    |
    | news_cache|
    | industry  |
    | hot_stocks|
    +-----------+
```

### 1.2 Technology Stack Summary

| Layer | Technology | Version | Justification |
|-------|-----------|---------|---------------|
| **Frontend Framework** | Next.js | 16.x (existing) | Already deployed; SSG + client-side rendering; excellent DX |
| **UI Library** | React | 18.x | Existing; hooks, concurrent features |
| **Type System** | TypeScript | 5.x | Existing; catches errors at compile time |
| **Styling** | Tailwind CSS | 3.4.x | Existing; utility-first, mobile-responsive |
| **Backend Framework** | FastAPI | 0.109 | Existing; async native, auto-docs, type validation |
| **Language** | Python | 3.11 | Existing; rich data science ecosystem |
| **Database** | Supabase (PostgreSQL) | -- | Existing; free 500MB tier, real-time capabilities |
| **AI Model** | GLM-4 (Zhipu AI) | -- | Existing integration; strong Chinese NLP |
| **Market Data (Primary)** | EastMoney HTTP API | -- | Existing; comprehensive A-share coverage |
| **Financial Data** | AKShare | 1.18.x | Existing; open-source A-share data library |
| **Market Data (Fallback)** | Yahoo Finance (yfinance) | -- | Existing fallback for price data |
| **Technical Indicators** | ta (Python) | 0.11.0 | Existing; industry-standard calculations |
| **Frontend Hosting** | Netlify | -- | Existing; CDN, auto-deploy, free tier |
| **Backend Hosting** | Render | -- | Existing; auto-deploy, free tier |
| **Scheduler** | APScheduler | 3.10.x | **New**; lightweight in-process job scheduling |
| **Rate Limiting** | slowapi | 0.1.x | **New**; FastAPI rate limiting middleware |
| **HTTP Client** | httpx | 0.27.0 | Existing; async HTTP for external APIs |
| **Logging** | Python logging + structlog | -- | **New**; structured logging for observability |
| **Error Tracking** | Sentry (Python SDK) | -- | **New** (Phase 3); error monitoring and alerting |

**Technology Selection Rationale**: The architecture maximizes reuse of the existing v1.0 stack. No technology replacements are proposed because the current stack is well-suited for the workload. New additions (APScheduler, slowapi, structlog, Sentry) are lightweight libraries that integrate cleanly with FastAPI.

### 1.3 Deployment Architecture

```
+----------------------------------------------------------+
|                    Deployment Topology                     |
+----------------------------------------------------------+

  GitHub Repository (derek33808/stock-advisor)
       |
       | push to main
       v
  +----------------+        +------------------+
  | GitHub Actions |        | GitHub Actions   |
  | (CI Pipeline)  |        | (CI Pipeline)    |
  | - lint         |        | - pytest         |
  | - type check   |        | - coverage check |
  +----------------+        +------------------+
       |                           |
       v                           v
  +-----------+            +-------------+
  | Netlify   |            | Render      |
  | Auto-     |            | Auto-       |
  | Deploy    |            | Deploy      |
  | (frontend)|            | (backend)   |
  +-----------+            +-------------+
       |                         |
       v                         v
  +----------+          +----------------+
  | Netlify  |          | Render         |
  | CDN Edge |          | Web Service    |
  | (Global) |          | (Oregon, US)   |
  | HTTPS    |          | 512MB RAM      |
  +----------+          | Free Tier      |
                        +----------------+
                               |
                               v
                        +-----------+
                        | Supabase  |
                        | Cloud     |
                        | (US East) |
                        | 500MB     |
                        +-----------+
```

**Environment Configuration**:

| Environment | Frontend URL | Backend URL | Database | Purpose |
|-------------|-------------|-------------|----------|---------|
| Local Dev | `localhost:3000` | `localhost:8000` | Supabase (shared) | Development |
| Production | `*.netlify.app` | `*.onrender.com` | Supabase (shared) | Live users |

Note: A staging environment is deferred. The Supabase free tier provides only one project. Staging can be simulated by using a separate schema or table prefix if needed.

### 1.4 Data Flow Diagram

**Flow 1: Single Stock Comprehensive Analysis**

```
User enters code "600519"
        |
        v
[Frontend] Check in-memory cache (3 min TTL)
        |  (cache miss)
        v
[Frontend] GET /api/v1/stock/600519/comprehensive
        |  X-Device-ID: uuid-xxx
        v
[API Router] stock_router.get_comprehensive(code="600519")
        |
        v
[comprehensive_analysis_service.analyze(code)]
        |
        +---> Check in-memory cache (30 min TTL)
        |     (cache miss)
        |
        +---> [rate_limiter] acquire("eastmoney_quote")
        |     [eastmoney_client] GET real-time quote
        |
        +---> [rate_limiter] acquire("eastmoney_quote")
        |     [eastmoney_client] GET 60-day history
        |
        +---> [indicator_service] calculate_indicators(history_df)
        +---> [strategy_service] calculate_composite_score(indicators)
        |
        +---> [rate_limiter] acquire("akshare")    (parallel)
        |     [akshare_client] GET earnings data
        |
        +---> [rate_limiter] acquire("eastmoney_news")  (parallel)
        |     [news_service] GET recent news (7 days)
        |
        +---> [rate_limiter] acquire("akshare")    (parallel)
        |     [industry_service] GET industry data (cached per industry, 2h)
        |
        v
[comprehensive_analysis_service] Assemble prompt with all data
        |
        +---> [rate_limiter] acquire("glm4")
        |     [glm4_client] POST analysis prompt
        |     [token_monitor_service] log token usage
        |
        v
[comprehensive_analysis_service] Assemble response
        |
        +---> Store in in-memory cache (30 min)
        +---> Return ComprehensiveAnalysisResponse
        |
        v
[API Router] Return JSON response
        |
        v
[Frontend] Render 5-dimensional analysis page
```

**Flow 2: Global Refresh (SSE)**

```
User clicks "Refresh All"
        |
        v
[Frontend] POST /api/v1/refresh/all
        |  Body: { device_id: "uuid-xxx" }
        |  Accept: text/event-stream
        v
[API Router] refresh_router.refresh_all(device_id)
        |
        +---> Snapshot stock list (recommendations + watchlist)
        |     total = N_recs + N_watchlist
        |
        +---> SSE: { type: "start", total: T }
        |
        +---> For each stock (sequential, 1 at a time):
        |       |
        |       +---> comprehensive_analysis_service.analyze(code)
        |       |     (parallel data fetching within stock)
        |       |
        |       +---> SSE: { type: "progress", current: i, total: T, ... }
        |       +---> SSE: { type: "token_update", tokens_used: X, ... }
        |       |
        |       +---> Check token budget -> if exceeded, stop
        |
        +---> SSE: { type: "complete", total: T, succeeded: S, ... }
        |
        v
[Frontend] Update UI progressively via EventSource listener
```

**Flow 3: Daily Scheduled Jobs (17:30 CST)**

```
[APScheduler] Trigger at 17:30 CST (trading days only)
        |
        +---> Job 1: generate_daily_recommendations()
        |       |
        |       +---> Fetch hot_stock_universe (50-80 stocks)
        |       +---> Stage 1: Fetch quotes for all (rate-limited)
        |       +---> Stage 2: Technical screening (local calc)
        |       +---> Stage 3: Score and rank -> top 10
        |       +---> Stage 4: Full comprehensive analysis x10
        |       +---> Store in analysis_history (source="recommendation")
        |       +---> Create prediction_tracking entries
        |
        +---> Job 2: save_watchlist_snapshots()
        |       |
        |       +---> For each unique stock in all watchlists:
        |       +---> Run comprehensive analysis (reuse if cached from Job 1)
        |       +---> Store in analysis_history (source="watchlist")
        |       +---> Create prediction_tracking entries
        |
        +---> Job 3: evaluate_predictions()
                |
                +---> Query prediction_tracking WHERE evaluation_date = today
                +---> Fetch actual prices for each
                +---> Calculate direction_correct, range_correct, magnitude_error
                +---> Update prediction_tracking records
```

---

## 2. Backend Architecture Design

### 2.1 Module Decomposition

The backend follows a layered architecture with clear separation of concerns.

```
backend/
  app/
    __init__.py
    main.py                          # FastAPI application factory
    config.py                        # Settings (env vars)
    scheduler.py                     # APScheduler job definitions  [NEW]

    api/                             # API Router Layer
      __init__.py
      stock.py                       # /stock/* endpoints (existing, extended)
      recommendations.py             # /recommendations/* (existing, extended)
      stats.py                       # /stats/* (existing)
      watchlist.py                   # /watchlist/* endpoints          [NEW]
      refresh.py                     # /refresh/* endpoints (SSE)     [NEW]
      analysis_history.py            # /analysis/* endpoints          [NEW]
      token_usage.py                 # /token/* endpoints             [NEW]
      device.py                      # /device/* endpoints            [NEW]
      industry.py                    # /industry/* endpoints          [NEW]
      health.py                      # /health endpoint (extended)    [NEW]

    services/                        # Business Logic Layer
      __init__.py
      indicator_service.py           # Technical indicators (existing)
      strategy_service.py            # Composite scoring (existing)
      ai_analysis_service.py         # AI integration (existing, extended)
      eastmoney_service.py           # EastMoney client (existing, extended)
      akshare_service.py             # AKShare client (existing, extended)
      yahoo_service.py               # Yahoo fallback (existing)
      glm_service.py                 # GLM-4 client (existing, extended)
      sina_service.py                # Sina data (existing, may deprecate)

      news_service.py                # News data acquisition          [NEW]
      fundamental_service.py         # Earnings + financials          [NEW]
      industry_service.py            # Industry analysis              [NEW]
      comprehensive_analysis_service.py  # Orchestrator               [NEW]
      watchlist_service.py           # Watchlist CRUD                 [NEW]
      prediction_tracking_service.py # Prediction evaluation          [NEW]
      analysis_history_service.py    # History management             [NEW]
      token_monitor_service.py       # Token budget enforcement       [NEW]
      rate_limiter_service.py        # Rate limiting + circuit breaker [NEW]
      hot_stock_service.py           # Hot stock universe management  [NEW]
      trading_calendar_service.py    # Trading day detection + calendar [NEW]

    db/                              # Data Access Layer
      __init__.py
      supabase.py                    # Supabase client (existing, extended)
      dao.py                         # DAO pattern for all tables     [NEW]

    models/                          # Data Models
      __init__.py
      schemas.py                     # Pydantic models (existing, extended)

    infrastructure/                  # Cross-cutting Infrastructure    [NEW]
      __init__.py
      cache.py                       # In-memory TTL cache
      circuit_breaker.py             # Circuit breaker implementation
      rate_limiter.py                # Token bucket rate limiter

  tests/                             # Test Suite                     [NEW]
    __init__.py
    conftest.py                      # Shared fixtures
    fixtures/                        # Mock API response data
    unit/
      test_indicator_service.py
      test_strategy_service.py
      test_prediction_tracking.py
      test_token_monitor.py
      test_composite_score.py
    integration/
      test_stock_api.py
      test_watchlist_api.py
      test_refresh_api.py
      test_analysis_history_api.py
```

### 2.2 Service Detailed Design

#### 2.2.1 `comprehensive_analysis_service.py` -- Orchestrator

**Responsibility**: Coordinates all 5 analysis dimensions, assembles the GLM-4 prompt, validates AI output, and returns a unified response. This is the central service that ties together all data sources.

**Core Methods**:

```python
class ComprehensiveAnalysisService:

    async def analyze(
        self,
        code: str,
        force_refresh: bool = False
    ) -> ComprehensiveAnalysisResponse:
        """
        Main entry point. Returns full 5-dimensional analysis.
        Checks cache first (30 min TTL). On cache miss, fetches all
        dimensions in parallel where possible, calls GLM-4, caches result.
        """

    async def _fetch_all_dimensions(
        self,
        code: str
    ) -> DimensionData:
        """
        Parallel fetch of all data dimensions:
          Group A (parallel): quote + news
          Group B (parallel): earnings + announcements
          Group C (check cache): industry data
          Sequential: history -> indicators -> score
        Returns a DimensionData object with all raw data.
        """

    async def _generate_ai_summary(
        self,
        code: str,
        data: DimensionData
    ) -> AISummary:
        """
        Assembles the GLM-4 prompt from all dimensions,
        calls glm_service, validates response structure,
        falls back to template if AI unavailable.
        """

    def _build_template_fallback(
        self,
        data: DimensionData
    ) -> AISummary:
        """
        Template-based summary when GLM-4 is unavailable.
        Uses rule-based logic to generate recommendation
        from technical indicators and score.
        """

    def _assemble_response(
        self,
        code: str,
        data: DimensionData,
        ai_summary: AISummary
    ) -> ComprehensiveAnalysisResponse:
        """
        Combines all dimensions + AI summary into the final
        API response object. Adds disclaimer.
        """
```

**Dependencies**: `news_service`, `fundamental_service`, `industry_service`, `eastmoney_service`, `indicator_service`, `strategy_service`, `glm_service`, `token_monitor_service`, `rate_limiter_service`, `cache`

**Data Flow**:

```
analyze(code)
  |
  +-> cache.get(f"comprehensive:{code}")  -- hit? return cached
  |
  +-> _fetch_all_dimensions(code)
  |     |
  |     +-> eastmoney_service.get_realtime(code)        [parallel A]
  |     +-> news_service.get_recent_news(code)          [parallel A]
  |     +-> fundamental_service.get_earnings(code)      [parallel B]
  |     +-> fundamental_service.get_financials(code)    [parallel B]
  |     +-> eastmoney_service.get_history(code, 60)     [sequential]
  |     +-> indicator_service.calculate(history)        [sequential]
  |     +-> strategy_service.score(indicators)          [sequential]
  |     +-> industry_service.get_analysis(industry)     [cached/fetch]
  |
  +-> _generate_ai_summary(code, dimension_data)
  |     |
  |     +-> token_monitor_service.check_budget()
  |     +-> glm_service.analyze(prompt)  OR  _build_template_fallback()
  |     +-> token_monitor_service.log_usage(tokens)
  |
  +-> _assemble_response(code, dimension_data, ai_summary)
  +-> cache.set(f"comprehensive:{code}", response, ttl=1800)
  +-> return response
```

#### 2.2.2 `news_service.py` -- News Data Acquisition

**Responsibility**: Fetches stock-specific news from EastMoney News API. Handles deduplication, filtering, and caching. Returns top-N most relevant news items.

**Core Methods**:

```python
class NewsService:

    async def get_recent_news(
        self,
        code: str,
        days: int = 7,
        limit: int = 10
    ) -> list[NewsItem]:
        """
        Fetches recent news for a stock.
        1. Check DB cache (stock_news_cache, 1h TTL)
        2. On cache miss, fetch from EastMoney News API
        3. Filter: remove duplicates, ads, irrelevant items
        4. Store in DB cache
        5. Return top `limit` items
        """

    async def _fetch_from_eastmoney(
        self,
        code: str
    ) -> list[dict]:
        """
        HTTP call to EastMoney search API.
        Rate-limited via rate_limiter_service.
        Returns raw JSON response parsed into list of dicts.
        """

    def _filter_and_deduplicate(
        self,
        items: list[dict]
    ) -> list[NewsItem]:
        """
        Removes duplicate titles (fuzzy match),
        filters out ads and irrelevant content,
        extracts: title, source, publish_date, summary, url.
        """
```

**Dependencies**: `rate_limiter_service`, `dao` (stock_news_cache), `eastmoney_client`

#### 2.2.3 `fundamental_service.py` -- Earnings and Financials

**Responsibility**: Fetches company financial data via AKShare. Provides earnings reports, valuation metrics, profitability ratios, and growth indicators.

**Core Methods**:

```python
class FundamentalService:

    async def get_earnings(
        self,
        code: str,
        periods: int = 4
    ) -> list[EarningsReport]:
        """
        Fetches latest earnings reports via AKShare.
        Uses stock_financial_analysis_indicator.
        Cached for 24 hours (earnings data changes quarterly).
        """

    async def get_financials(
        self,
        code: str
    ) -> FinancialMetrics:
        """
        Returns valuation (PE, PB, PS), profitability (ROE, ROA,
        margins), growth (revenue YoY, profit YoY), and financial
        health (debt-to-equity, current ratio, cash flow).
        """

    async def get_company_info(
        self,
        code: str
    ) -> CompanyInfo:
        """
        Returns basic company information: name, industry (CSRC
        classification), market cap, business description.
        """
```

**Dependencies**: `rate_limiter_service`, `akshare_client`

#### 2.2.4 `industry_service.py` -- Industry Analysis

**Responsibility**: Fetches industry-level data including index performance, capital flow, peer comparison, and sector heat. Data is cached per industry (not per stock) for efficiency.

**Core Methods**:

```python
class IndustryService:

    async def get_analysis(
        self,
        industry_name: str
    ) -> IndustryAnalysis:
        """
        Returns comprehensive industry analysis.
        1. Check DB cache (industry_data_cache, 2h TTL)
        2. On cache miss, fetch all components
        3. Store in DB cache
        """

    async def get_index_performance(
        self,
        industry_name: str
    ) -> IndexPerformance:
        """
        Industry index data: current value, 1d/1w/1m/3m change.
        Source: AKShare stock_board_industry_index_em
        """

    async def get_peer_comparison(
        self,
        industry_name: str,
        limit: int = 5
    ) -> list[PeerStock]:
        """
        Top N stocks in the industry by market cap.
        Source: AKShare stock_board_industry_cons_em
        """

    async def get_capital_flow(
        self,
        industry_name: str
    ) -> CapitalFlow:
        """
        Industry net inflow/outflow.
        Source: AKShare stock_sector_fund_flow_rank
        """
```

**Dependencies**: `rate_limiter_service`, `akshare_client`, `dao` (industry_data_cache)

**Caching Strategy**: Industry data is shared across all stocks in the same industry. When stock A (industry: "baijiu") is analyzed, the industry data is cached. When stock B (same industry) is analyzed within 2 hours, the cached data is reused. This significantly reduces API calls during Global Refresh.

#### 2.2.5 `watchlist_service.py` -- Watchlist Management

**Responsibility**: CRUD operations for user watchlists. All operations are scoped to a device_id.

**Core Methods**:

```python
class WatchlistService:

    async def get_watchlist(
        self,
        device_id: str
    ) -> list[WatchlistStock]:
        """
        Returns all active watchlist stocks for a device.
        Includes latest analysis summary and prediction accuracy.
        """

    async def add_stock(
        self,
        device_id: str,
        code: str
    ) -> WatchlistAddResult:
        """
        Adds a stock to the watchlist.
        - Validates stock code exists
        - Checks max limit (50 stocks)
        - Handles duplicate gracefully (returns 200 if exists)
        - Saves current analysis snapshot as last_analysis
        """

    async def remove_stock(
        self,
        device_id: str,
        code: str
    ) -> WatchlistRemoveResult:
        """
        Soft-deletes stock from watchlist (sets is_active=false).
        Analysis history is preserved.
        """

    async def refresh_stock(
        self,
        device_id: str,
        code: str
    ) -> ComprehensiveAnalysisResponse:
        """
        Re-runs comprehensive analysis for a single watchlist stock.
        Updates last_analysis and last_refreshed_at in watchlist table.
        """

    async def validate_device(
        self,
        device_id: str
    ) -> DeviceValidationResult:
        """
        Checks if a device_id exists in the database.
        Returns stock count for that device.
        Used for backup code recovery.
        """

    async def export_data(
        self,
        device_id: str
    ) -> WatchlistExport:
        """
        Exports all watchlist stocks and metadata as JSON.
        """

    async def import_data(
        self,
        device_id: str,
        data: WatchlistExport
    ) -> ImportResult:
        """
        Imports watchlist from JSON export.
        Merges with existing stocks (no duplicates).
        """
```

**Dependencies**: `dao` (watchlist), `comprehensive_analysis_service`

#### 2.2.6 `prediction_tracking_service.py` -- Prediction Evaluation

**Responsibility**: Manages the prediction lifecycle: creation at analysis time, evaluation after 5 trading days, and accuracy statistics calculation.

**Core Methods**:

```python
class PredictionTrackingService:

    async def create_prediction(
        self,
        analysis_history_id: str,
        code: str,
        prediction_date: date,
        predicted_direction: str,
        predicted_change_low: float,
        predicted_change_high: float,
        predicted_confidence: str
    ) -> PredictionRecord:
        """
        Creates a new prediction tracking entry.
        Calculates evaluation_date = prediction_date + 5 trading days.
        Requires a trading calendar to compute correct evaluation date.
        """

    async def evaluate_due_predictions(self) -> EvaluationSummary:
        """
        Scheduled job: finds all predictions WHERE evaluation_date = today
        AND status = 'pending'. For each:
          1. Fetch actual closing price on evaluation_date
          2. Calculate actual_change_percent
          3. Determine direction_correct and range_correct
          4. Calculate magnitude_error
          5. Update record status to 'evaluated'
        Returns summary of evaluations performed.
        """

    async def get_accuracy_stats(
        self,
        code: str
    ) -> AccuracyStats:
        """
        Calculates prediction accuracy for a stock.
        Uses the prediction_accuracy_stats view in Supabase.
        Adds derived metrics: grade (A/B/C/D/F), insights.
        """

    def _calculate_evaluation_date(
        self,
        prediction_date: date
    ) -> date:
        """
        Returns prediction_date + 5 trading days.
        Uses a trading calendar (AKShare or static calendar).
        Handles Chinese market holidays.
        """

    def _calculate_grade(
        self,
        direction_accuracy: float,
        total_evaluated: int
    ) -> str:
        """
        Maps accuracy to letter grade.
        Only returns grade if total_evaluated >= 20.
        """
```

**Dependencies**: `dao` (prediction_tracking, analysis_history), `eastmoney_service` (for actual prices), trading calendar

#### 2.2.7 `analysis_history_service.py` -- History Management

**Responsibility**: Manages daily analysis snapshots and provides historical timeline data for the Historical Review page.

**Core Methods**:

```python
class AnalysisHistoryService:

    async def save_snapshot(
        self,
        code: str,
        analysis: ComprehensiveAnalysisResponse,
        source: str,  # "recommendation" or "watchlist"
        device_id: str | None = None
    ) -> AnalysisHistoryRecord:
        """
        Saves a complete analysis as a historical snapshot.
        Extracts prediction data and creates a prediction_tracking entry.
        Called by:
          - Daily recommendation generation (source="recommendation")
          - Daily watchlist snapshot job (source="watchlist")
          - Manual refresh (updates existing entry for today)
        """

    async def get_timeline(
        self,
        code: str,
        days: int = 30,
        device_id: str | None = None
    ) -> list[TimelineEntry]:
        """
        Returns historical analysis entries for a stock.
        If device_id provided, includes watchlist-specific entries.
        Each entry includes prediction vs actual comparison if evaluated.
        Ordered by analysis_date descending.
        """

    async def cleanup_old_records(
        self,
        retention_days: int = 90
    ) -> int:
        """
        Deletes analysis_history records older than retention_days.
        Preserves prediction_tracking records (they reference the deleted
        history but contain copied prediction data for independence).
        Returns count of deleted records.
        """
```

**Dependencies**: `dao` (analysis_history), `prediction_tracking_service`

#### 2.2.8 `token_monitor_service.py` -- Token Budget Enforcement

**Responsibility**: Tracks GLM-4 token consumption, enforces daily budget limits, and provides usage statistics.

**Core Methods**:

```python
class TokenMonitorService:

    DAILY_BUDGET: int = 500_000  # Configurable via env var
    WARNING_THRESHOLD: float = 0.8  # 80%

    async def check_budget(self) -> TokenBudgetStatus:
        """
        Returns current token usage status.
        If usage >= 100%, raises TokenBudgetExceeded.
        If usage >= 80%, sets alert_level = "warning".
        Uses in-memory counter (synced with DB periodically).
        """

    async def log_usage(
        self,
        request_type: str,
        stock_code: str,
        input_tokens: int,
        output_tokens: int,
        success: bool,
        response_time_ms: int,
        error_message: str | None = None
    ) -> None:
        """
        Logs a token usage record to token_usage_log table.
        Updates in-memory daily counter.
        """

    async def get_daily_usage(
        self,
        date: date | None = None
    ) -> DailyTokenUsage:
        """
        Returns aggregated token usage for a given date.
        Uses the daily_token_usage view.
        """

    def _sync_counter(self) -> None:
        """
        Periodically syncs in-memory counter with DB.
        Called every 5 minutes to avoid DB on every check.
        """
```

**Dependencies**: `dao` (token_usage_log)

#### 2.2.9 `rate_limiter_service.py` -- Rate Limiting and Circuit Breaker

**Responsibility**: Centralized rate limiting per external data source and circuit breaker pattern to prevent cascading failures.

**Core Methods**:

```python
class RateLimiterService:
    """
    Manages rate limiters and circuit breakers for all external data sources.
    Instantiated once at application startup.
    """

    def __init__(self):
        self.limiters = {
            "eastmoney_quote": TokenBucketLimiter(rate=5.0, burst=10),
            "eastmoney_news": TokenBucketLimiter(rate=3.0, burst=5),
            "akshare": TokenBucketLimiter(rate=3.0, burst=5),
            "glm4": TokenBucketLimiter(rate=1.0, burst=2),
            "yahoo": TokenBucketLimiter(rate=2.0, burst=3),
        }
        self.breakers = {
            "eastmoney_quote": CircuitBreaker(threshold=5, window=60, open_duration=300),
            "eastmoney_news": CircuitBreaker(threshold=5, window=60, open_duration=300),
            "akshare": CircuitBreaker(threshold=5, window=60, open_duration=300),
            "glm4": CircuitBreaker(threshold=3, window=60, open_duration=600),
            "yahoo": CircuitBreaker(threshold=5, window=60, open_duration=300),
        }

    async def acquire(
        self,
        source: str,
        priority: str = "MEDIUM"
    ) -> None:
        """
        Acquires a rate limit slot for the given source.
        Checks circuit breaker state first:
          - OPEN: raises CircuitBreakerOpen (caller uses fallback)
          - HALF-OPEN: allows single test request
          - CLOSED: proceeds normally
        Then acquires rate limiter slot (may wait).
        HIGH priority requests skip the queue.
        """

    def record_success(self, source: str) -> None:
        """Records successful call for circuit breaker tracking."""

    def record_failure(self, source: str) -> None:
        """Records failed call for circuit breaker tracking."""

    def get_status(self) -> dict[str, SourceStatus]:
        """Returns rate limiter and circuit breaker status for all sources."""
```

**Dependencies**: None (infrastructure-level service)

#### 2.2.10 `hot_stock_service.py` -- Hot Stock Universe

**Responsibility**: Manages the curated hot stock universe used for daily recommendation generation.

**Core Methods**:

```python
class HotStockService:

    async def get_active_universe(self) -> list[HotStock]:
        """
        Returns all active stocks in the hot stock universe.
        Source: hot_stock_universe table WHERE is_active = TRUE.
        """

    async def refresh_universe(self) -> UniverseRefreshResult:
        """
        Weekly job (Monday 09:00):
        1. Fetch sector leaders from EastMoney/AKShare
        2. Fetch top traded stocks by turnover
        3. Validate all inclusion criteria
        4. Add qualifying new stocks
        5. Deactivate stocks that no longer qualify
        6. Log all changes
        """

    async def seed_initial_universe(self) -> int:
        """
        One-time seeding for v2.0 launch.
        Selects top 10 by market cap from 6 key sectors.
        Returns count of stocks seeded.
        """
```

**Dependencies**: `rate_limiter_service`, `akshare_client`, `eastmoney_client`, `dao` (hot_stock_universe)

#### 2.2.11 `trading_calendar_service.py` -- Trading Day Detection

**Responsibility**: Provides trading day detection for all scheduled jobs and prediction evaluation date calculation. Maintains a cached trading calendar with a static fallback to ensure reliability even when AKShare is unavailable.

**Core Methods**:

```python
class TradingCalendarService:
    """
    Centralized trading calendar service.
    Initialized at application startup; caches the full-year calendar.
    All dates are in Asia/Shanghai (CST) timezone.
    """

    _calendar: set[date] = set()          # Set of trading dates for fast lookup
    _last_refresh: datetime | None = None  # When calendar was last refreshed
    _calendar_year: int = 0                # Year of the cached calendar

    STALE_THRESHOLD_HOURS: int = 48        # Warn if calendar older than 48h

    async def initialize(self) -> None:
        """
        Called on application startup.
        1. Try to load calendar from AKShare (primary source)
        2. If AKShare fails, load from static fallback file
        3. Log the calendar source and date count
        """

    async def refresh_calendar(self) -> CalendarRefreshResult:
        """
        Refreshes the trading calendar from AKShare.
        Called:
          - On startup (via initialize())
          - Daily at 08:00 CST (scheduled job)
          - Manually via /health recalibration (future)

        AKShare function: akshare.tool_trade_date_hist_sina()
        Returns all historical trading dates. We filter for the
        current year + next year (for December edge cases).

        On success: updates _calendar and _last_refresh.
        On failure: logs WARNING, keeps existing calendar.
        """

    def is_trading_day(self, target_date: date | None = None) -> bool:
        """
        Returns True if the given date is a trading day.
        If target_date is None, uses today in CST timezone.

        Logic:
          1. If calendar is empty (initialization failed), fall back
             to basic rule: weekday (Mon-Fri) = trading day
          2. Otherwise, check if date is in _calendar set (O(1) lookup)

        Note: This handles weekends AND Chinese market holidays
        (Spring Festival, National Day, Qingming, etc.)
        """

    def next_trading_day(self, from_date: date | None = None) -> date:
        """
        Returns the next trading day after from_date (exclusive).
        Used by prediction_tracking_service to calculate evaluation_date.

        If from_date is None, uses today in CST.
        Iterates forward up to 30 days to find next trading day.
        Raises TradingCalendarError if no trading day found in range.
        """

    def add_trading_days(self, from_date: date, count: int) -> date:
        """
        Returns the date that is `count` trading days after from_date.
        Used by prediction_tracking_service for 5-trading-day evaluation.

        Example: add_trading_days(Monday, 5) returns next Monday
                 (skipping weekends and holidays).
        """

    def is_stale(self) -> bool:
        """
        Returns True if the calendar hasn't been refreshed in
        STALE_THRESHOLD_HOURS. Used by /health endpoint for monitoring.
        """

    def _load_static_fallback(self) -> set[date]:
        """
        Loads trading calendar from static JSON file.
        File: data/trading_calendar_static.json
        Contains trading dates for 2024, 2025, 2026.

        The static file is generated once per year by running:
          python scripts/generate_trading_calendar.py

        Structure: { "2024": ["2024-01-02", ...], "2025": [...], "2026": [...] }
        """
```

**Static Fallback File**:

The file `data/trading_calendar_static.json` is committed to the repository and contains Chinese A-share market trading dates for 2024-2026. This ensures the system works even if AKShare is completely unavailable.

```json
// data/trading_calendar_static.json (structure)
{
  "generated_at": "2026-01-15",
  "source": "akshare.tool_trade_date_hist_sina()",
  "years": {
    "2024": ["2024-01-02", "2024-01-03", "..."],
    "2025": ["2025-01-02", "2025-01-03", "..."],
    "2026": ["2026-01-02", "2026-01-03", "..."]
  }
}
```

**Caching Strategy**:

| Aspect | Detail |
|--------|--------|
| Cache scope | Full-year trading dates (current year + next year) |
| Cache storage | In-memory `set[date]` for O(1) lookup |
| Refresh trigger | Daily at 08:00 CST + on startup |
| Stale detection | Warning logged if > 48 hours since last refresh |
| Fallback | Static JSON file with 2024-2026 trading dates |
| Calendar source | `akshare.tool_trade_date_hist_sina()` via `asyncio.to_thread()` |

**Timezone Handling**:

All date comparisons use `Asia/Shanghai` timezone. The APScheduler is already configured with `timezone="Asia/Shanghai"`. The `is_trading_day()` method converts `datetime.now()` to CST before extracting the date.

```python
from zoneinfo import ZoneInfo

CST = ZoneInfo("Asia/Shanghai")

def _today_cst(self) -> date:
    return datetime.now(CST).date()
```

**Dependencies**: `akshare_client` (for calendar fetch), static fallback file

**Integration Points**:
- `scheduler.py`: All jobs call `trading_calendar_service.is_trading_day()` at entry
- `prediction_tracking_service.py`: Calls `trading_calendar_service.add_trading_days()` for evaluation date
- `/health` endpoint: Reports `calendar_stale` status

### 2.3 Data Access Layer

#### 2.3.1 Supabase Connection Management

The existing `db/supabase.py` provides a singleton Supabase client. For v2.0, it is extended with connection pooling awareness.

```python
# db/supabase.py (extended)
from supabase import create_client, Client
from app.config import get_settings

_client: Client | None = None

def get_supabase() -> Client:
    """
    Returns singleton Supabase client.
    The supabase-py library manages HTTP connection pooling internally.
    """
    global _client
    if _client is None:
        settings = get_settings()
        _client = create_client(settings.supabase_url, settings.supabase_key)
    return _client
```

#### 2.3.2 DAO Pattern

A new `db/dao.py` module encapsulates all database operations, providing a clean interface between services and the database.

```python
# db/dao.py

class WatchlistDAO:
    """Data access for watchlist table."""

    async def get_by_device(self, device_id: str) -> list[dict]: ...
    async def add(self, device_id: str, code: str, name: str, industry: str) -> dict: ...
    async def remove(self, device_id: str, code: str) -> bool: ...
    async def update_analysis(self, device_id: str, code: str, analysis: dict) -> None: ...
    async def count_by_device(self, device_id: str) -> int: ...
    async def device_exists(self, device_id: str) -> bool: ...

class AnalysisHistoryDAO:
    """Data access for analysis_history table."""

    async def save(self, record: dict) -> dict: ...
    async def get_timeline(self, code: str, days: int, device_id: str | None) -> list[dict]: ...
    async def delete_older_than(self, days: int) -> int: ...

class PredictionTrackingDAO:
    """Data access for prediction_tracking table."""

    async def create(self, record: dict) -> dict: ...
    async def get_due(self, date: date) -> list[dict]: ...
    async def update_evaluation(self, id: str, results: dict) -> None: ...
    async def get_stats(self, code: str) -> dict: ...

class TokenUsageDAO:
    """Data access for token_usage_log table."""

    async def log(self, record: dict) -> None: ...
    async def get_daily_total(self, date: date) -> int: ...
    async def get_daily_summary(self, date: date) -> dict: ...

class NewsCacheDAO:
    """Data access for stock_news_cache table."""

    async def get(self, code: str) -> dict | None: ...
    async def upsert(self, code: str, news_items: list[dict], ttl_seconds: int) -> None: ...
    async def delete_expired(self) -> int: ...

class IndustryCacheDAO:
    """Data access for industry_data_cache table."""

    async def get(self, industry_name: str) -> dict | None: ...
    async def upsert(self, industry_name: str, data: dict, ttl_seconds: int) -> None: ...

class HotStockDAO:
    """Data access for hot_stock_universe table."""

    async def get_active(self) -> list[dict]: ...
    async def add(self, stock: dict) -> None: ...
    async def deactivate(self, code: str, reason: str) -> None: ...
    async def update_validation(self, code: str) -> None: ...
```

#### 2.3.3 Caching Strategy

The system uses a two-level cache:

**Level 1: In-Memory Cache (Python process)**

```python
# infrastructure/cache.py
from cachetools import TTLCache

class AppCache:
    """
    Application-level in-memory TTL cache.
    Thread-safe via cachetools. Survives across requests
    but is lost on process restart (acceptable for TTL data).
    """

    def __init__(self):
        self.stores = {
            "quote": TTLCache(maxsize=200, ttl=180),       # 3 min
            "indicators": TTLCache(maxsize=200, ttl=180),   # 3 min
            "comprehensive": TTLCache(maxsize=100, ttl=1800), # 30 min
        }

    def get(self, store: str, key: str) -> Any | None: ...
    def set(self, store: str, key: str, value: Any) -> None: ...
    def invalidate(self, store: str, key: str) -> None: ...
    def clear_store(self, store: str) -> None: ...
```

**Level 2: Database Cache (Supabase)**

| Table | Purpose | TTL | Eviction |
|-------|---------|-----|----------|
| `stock_news_cache` | News items per stock | 1 hour | `expires_at` column; periodic cleanup |
| `industry_data_cache` | Industry analysis per sector | 2 hours | `expires_at` column; periodic cleanup |
| `analysis_history` | Full analysis snapshots | 90 days | `cleanup_old_records()` job |

**Cache Decision Matrix**:

| Data Type | L1 (In-Memory) | L2 (Database) | Rationale |
|-----------|----------------|---------------|-----------|
| Real-time quote | 3 min | No | Highly volatile, small payload |
| Technical indicators | 3 min | No | Derived from quote, same lifecycle |
| Comprehensive analysis | 30 min | Yes (history) | Expensive to compute; DB stores for history |
| News items | No | 1 hour | Moderate size; shared across users |
| Industry data | No | 2 hours | Shared across stocks; moderate refresh rate |
| Earnings data | No | 24 hours | Changes quarterly; fetched via AKShare |
| Recommendations | No | Until regenerated | Generated once daily |

### 2.4 External API Integration

#### 2.4.1 EastMoney Client (`eastmoney_service.py` extended)

**Existing**: `get_stock_history()`, `get_stock_realtime()`, `get_history()`, `get_realtime()`

**New Methods**:

```python
# Added to existing eastmoney_service.py

async def get_stock_news(
    code: str,
    page_size: int = 10
) -> list[dict]:
    """
    Fetches stock-specific news from EastMoney search API.
    URL: https://search-api-web.eastmoney.com/search/jsonp
    Rate limited via rate_limiter_service ("eastmoney_news").
    Parses JSONP response to extract news items.
    """

async def get_stock_search(
    query: str,
    limit: int = 20
) -> list[dict]:
    """
    Search stocks by name or code.
    Existing functionality, but now rate-limited.
    """
```

**Error Handling**: All EastMoney calls are wrapped with:
1. Rate limiter acquisition (`rate_limiter_service.acquire("eastmoney_quote")`)
2. Circuit breaker check (raises `CircuitBreakerOpen` if tripped)
3. Retry logic (1 retry on timeout/5xx)
4. Fallback to Yahoo Finance for price data

#### 2.4.2 AKShare Client (`akshare_service.py` extended)

**Existing**: Basic integration for stock data.

**New Methods**:

```python
# Added to existing akshare_service.py

async def get_financial_indicators(code: str) -> dict:
    """
    Wraps akshare.stock_financial_analysis_indicator()
    Returns PE, PB, ROE, revenue growth, etc.
    Rate limited via rate_limiter_service ("akshare").
    """

async def get_announcements(code: str, days: int = 30) -> list[dict]:
    """
    Wraps akshare.stock_notice_report()
    Returns recent company announcements.
    """

async def get_industry_index(industry_name: str) -> dict:
    """
    Wraps akshare.stock_board_industry_index_em()
    Returns industry index value and performance.
    """

async def get_industry_constituents(industry_name: str) -> list[dict]:
    """
    Wraps akshare.stock_board_industry_cons_em()
    Returns list of stocks in the industry.
    """

async def get_sector_fund_flow() -> list[dict]:
    """
    Wraps akshare.stock_sector_fund_flow_rank()
    Returns capital flow data for all sectors.
    """

async def get_trading_calendar() -> list[date]:
    """
    Returns list of trading dates for the current year.
    Wraps akshare.tool_trade_date_hist_sina().
    Called by TradingCalendarService.refresh_calendar().
    See Section 2.2.11 for full calendar management design.
    """
```

**Important Note**: AKShare functions are synchronous (they use `requests` internally). All calls must be wrapped with `asyncio.to_thread()` to avoid blocking the FastAPI event loop.

```python
# Pattern for calling AKShare in async context
async def get_financial_indicators(code: str) -> dict:
    await rate_limiter_service.acquire("akshare")
    try:
        result = await asyncio.to_thread(
            akshare.stock_financial_analysis_indicator, symbol=code
        )
        rate_limiter_service.record_success("akshare")
        return result
    except Exception as e:
        rate_limiter_service.record_failure("akshare")
        raise
```

#### 2.4.3 GLM-4 Client (`glm_service.py` extended)

**Existing**: Basic prompt-response for AI analysis.

**Extended Prompt Architecture**:

```python
# Extended glm_service.py

SYSTEM_PROMPT = """你是一位专业的A股市场分析师。请基于提供的5个维度数据，
给出全面、客观的综合分析。注意：
1. 你的分析仅供参考，不构成投资建议
2. 必须使用中文回答
3. 必须使用"技术信号""分析结果"等术语，不要使用"投资建议""买入推荐"
4. 必须明确指出风险因素
5. 回答格式必须严格按照指定的JSON结构"""

async def comprehensive_analyze(
    code: str,
    technical_data: dict,
    fundamental_data: dict,
    earnings_data: dict,
    news_data: list[dict],
    industry_data: dict
) -> dict:
    """
    Sends structured 5-dimensional prompt to GLM-4.

    Token budget per call: ~2,800 (2,000 input + 800 output)

    Prompt structure:
      [System]: SYSTEM_PROMPT
      [Data Section 1]: Technical indicators and price data
      [Data Section 2]: Fundamental metrics
      [Data Section 3]: Earnings report highlights
      [Data Section 4]: Top 5 news items with summaries
      [Data Section 5]: Industry trend and peer comparison
      [Instruction]: Generate JSON response with required fields

    Response validation:
      - Must parse as valid JSON
      - Must contain all required fields
      - overall_recommendation must be one of: strong_buy/buy/hold/reduce/avoid
      - confidence must be one of: high/medium/low
      - If validation fails, retry once with simpler prompt
      - If retry fails, use template fallback
    """
```

#### 2.4.4 Request Queue and Rate Limiting Implementation

```
                          Incoming API Request
                                  |
                                  v
                    +---------------------------+
                    | Circuit Breaker Check     |
                    | State: CLOSED/OPEN/HALF   |
                    +---------------------------+
                         |              |
                      CLOSED          OPEN
                         |              |
                         v              v
                    +----------+   Return cached
                    | Token    |   data / fallback
                    | Bucket   |
                    | Rate     |
                    | Limiter  |
                    +----------+
                         |
                     (may wait for token)
                         |
                         v
                    +----------+
                    | Execute  |
                    | HTTP     |
                    | Request  |
                    +----------+
                         |
                    +----+----+
                    |         |
                 success    failure
                    |         |
                    v         v
               record()  record()
               success   failure
                    |         |
                    |    +----+----+
                    |    | Retry?  |
                    |    | (max 3) |
                    |    +---------+
                    |         |
                    v         v
                 Return    Exponential
                 result    backoff +
                           jitter
```

#### 2.4.5 Circuit Breaker State Machine

```python
# infrastructure/circuit_breaker.py

class CircuitBreaker:
    """
    Three-state circuit breaker per external data source.

    State transitions:

    CLOSED --[5 errors in 60s]--> OPEN
    OPEN   --[5 min elapsed]----> HALF_OPEN
    HALF_OPEN --[1 success]-----> CLOSED
    HALF_OPEN --[1 failure]-----> OPEN
    """

    def __init__(
        self,
        threshold: int = 5,      # errors to trip
        window: int = 60,        # seconds to track errors
        open_duration: int = 300  # seconds to stay open
    ): ...

    def allow_request(self) -> bool:
        """Returns True if request should proceed."""

    def record_success(self) -> None:
        """Records success. If HALF_OPEN, transitions to CLOSED."""

    def record_failure(self) -> None:
        """Records failure. May transition to OPEN."""

    @property
    def state(self) -> str:
        """Returns "CLOSED", "OPEN", or "HALF_OPEN"."""
```

### 2.5 Scheduled Jobs Design

The scheduler uses APScheduler (Advanced Python Scheduler) running in the same process as FastAPI. This is appropriate for a single-instance deployment on Render.

```python
# scheduler.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler()

def setup_scheduler():
    """Called on FastAPI startup event."""

    # Job 1: Daily Recommendations (17:30 CST, trading days)
    scheduler.add_job(
        generate_daily_recommendations,
        CronTrigger(hour=17, minute=30, timezone="Asia/Shanghai"),
        id="daily_recommendations",
        name="Generate daily stock recommendations",
        misfire_grace_time=3600,  # 1 hour grace period
    )

    # Job 2: Daily Watchlist Snapshots (17:35 CST, trading days)
    # Runs 5 minutes after recommendations to reuse cached data
    scheduler.add_job(
        save_watchlist_snapshots,
        CronTrigger(hour=17, minute=35, timezone="Asia/Shanghai"),
        id="watchlist_snapshots",
        name="Save daily watchlist analysis snapshots",
        misfire_grace_time=3600,
    )

    # Job 3: Prediction Evaluation (17:40 CST, trading days)
    scheduler.add_job(
        evaluate_predictions,
        CronTrigger(hour=17, minute=40, timezone="Asia/Shanghai"),
        id="prediction_evaluation",
        name="Evaluate 5-day predictions that are due today",
        misfire_grace_time=3600,
    )

    # Job 4: Hot Stock Universe Refresh (Monday 09:00 CST)
    scheduler.add_job(
        refresh_hot_stock_universe,
        CronTrigger(day_of_week="mon", hour=9, minute=0, timezone="Asia/Shanghai"),
        id="hot_stock_refresh",
        name="Weekly hot stock universe refresh",
        misfire_grace_time=7200,
    )

    # Job 5: Cache Cleanup (daily 03:00 CST)
    scheduler.add_job(
        cleanup_caches,
        CronTrigger(hour=3, minute=0, timezone="Asia/Shanghai"),
        id="cache_cleanup",
        name="Clean expired cache entries and old history records",
    )

    scheduler.start()
```

**Trading Day Detection via TradingCalendarService**:

Jobs 1-3 (daily recommendations, watchlist snapshots, prediction evaluation) must only run on trading days. Each job calls `TradingCalendarService.is_trading_day()` at the start and exits immediately if today is not a trading day.

```python
# Pattern used by all trading-day jobs
async def generate_daily_recommendations():
    if not trading_calendar_service.is_trading_day():
        logger.info("skip_job", job="daily_recommendations", reason="not_trading_day")
        return
    # ... proceed with job logic
```

Job 5 (`refresh_trading_calendar`) runs daily at 08:00 CST to refresh the calendar:

```python
# Added to scheduler.py
scheduler.add_job(
    trading_calendar_service.refresh_calendar,
    CronTrigger(hour=8, minute=0, timezone="Asia/Shanghai"),
    id="refresh_trading_calendar",
    name="Refresh trading calendar from AKShare",
    misfire_grace_time=7200,
)
```

**Calendar initialization on startup**:

```python
# In main.py lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    await trading_calendar_service.initialize()  # Load calendar before scheduler starts
    setup_scheduler()
    yield
    scheduler.shutdown()
```

**Misfire Handling**: Render free tier may restart the process, causing jobs to miss their scheduled time. The `misfire_grace_time` parameter ensures jobs still execute if the process restarts within the grace period. On restart, `trading_calendar_service.initialize()` re-loads the calendar (from AKShare or static fallback) before the scheduler processes any misfired jobs.

---

## 3. Frontend Architecture Design

### 3.1 Component Structure

```
src/
  app/                              # Next.js App Router pages
    layout.tsx                       # Root layout (existing, extended)
    page.tsx                         # Home page (existing, redesigned)
    globals.css                      # Global styles (existing)
    search/
      page.tsx                       # Search page (existing)
    stock/
      [code]/
        page.tsx                     # Stock detail (existing, redesigned for 5 dims)
        loading.tsx                  # Loading state (existing)
    history/                         # [NEW]
      [code]/
        page.tsx                     # Historical review page
    settings/                        # [NEW]
      page.tsx                       # Device ID, export/import, backup code

  components/
    # Layout Components
    Header.tsx                       # Header with logo, token badge     [NEW]
    TabBar.tsx                       # Recommendations / Watchlist / Search tabs [NEW]
    Footer.tsx                       # Disclaimer footer

    # Home Page Components
    HomeContent.tsx                  # Home page content (existing, extended)
    MarketHeader.tsx                 # Market overview banner (existing)
    TabSwitcher.tsx                  # Tab switching logic (existing, extended)

    # Stock Card Components
    StockCard.tsx                    # Stock card in list (existing, extended)
    RecommendationCard.tsx           # Recommendation-specific card      [NEW]
    WatchlistCard.tsx                # Watchlist-specific card with history/refresh [NEW]

    # Comprehensive Analysis Components
    StockDetailClient.tsx            # Detail page client component (existing, redesigned)
    AnalysisSummary.tsx              # AI comprehensive summary section  [NEW]
    TechnicalSection.tsx             # Technical analysis accordion      [NEW]
    FundamentalSection.tsx           # Fundamental analysis accordion    [NEW]
    NewsSection.tsx                  # Recent developments accordion     [NEW]
    IndustrySection.tsx              # Industry analysis accordion       [NEW]
    TradingSuggestion.tsx            # Trading plan display              [NEW]

    # Historical Review Components
    PredictionTimeline.tsx           # Timeline of past analyses         [NEW]
    AccuracyStats.tsx                # Prediction accuracy display       [NEW]
    AccuracyInsights.tsx             # AI-generated insights             [NEW]
    TimelineEntry.tsx                # Single timeline item              [NEW]

    # Refresh Components
    RefreshButton.tsx                # Single stock refresh (existing)
    RefreshAllButton.tsx             # Global refresh button (existing, extended)
    RefreshProgress.tsx              # SSE progress overlay              [NEW]
    ProgressBar.tsx                  # Progress bar (existing)

    # Watchlist Components
    WatchlistButton.tsx              # Add/remove from watchlist (existing, extended)
    WatchlistManager.tsx             # Watchlist list with sort/filter   [NEW]

    # Token Components
    TokenBadge.tsx                   # Token usage in header             [NEW]
    TokenWarning.tsx                 # Warning/limit reached banners     [NEW]

    # Settings Components
    BackupCodeDisplay.tsx            # Show/copy backup code             [NEW]
    DataExportImport.tsx             # Export/import watchlist            [NEW]
    RecoveryFlow.tsx                 # Backup code recovery              [NEW]

    # Common Components
    Disclaimer.tsx                   # Disclaimer text (existing)
    SearchBox.tsx                    # Stock search input (existing)
    ScoreBadge.tsx                   # Composite score circle            [NEW]
    LoadingSkeleton.tsx              # Skeleton loading states            [NEW]
    ErrorBoundary.tsx                # Error boundary wrapper             [NEW]

  lib/
    api.ts                           # API client (existing, extended)
    types.ts                         # TypeScript types (existing, extended)
    watchlist-context.tsx            # Watchlist React context (existing, extended)
    device-id.ts                     # Device UUID management            [NEW]
    sse-client.ts                    # SSE EventSource wrapper           [NEW]
    token-context.tsx                # Token usage React context         [NEW]
    cache.ts                         # Client-side response cache        [NEW]
    constants.ts                     # Shared constants                  [NEW]
```

### 3.2 State Management

The frontend uses React Context for global state and local component state for page-level concerns. No external state management library (Redux, Zustand) is needed given the application complexity.

**Global State (React Context)**:

```typescript
// lib/device-id.ts
export function getDeviceId(): string {
  let id = localStorage.getItem("stock_advisor_device_id");
  if (!id) {
    id = crypto.randomUUID();  // UUID v4
    localStorage.setItem("stock_advisor_device_id", id);
  }
  return id;
}

export function setDeviceId(id: string): void {
  localStorage.setItem("stock_advisor_device_id", id);
}

// lib/watchlist-context.tsx (extended)
interface WatchlistContextValue {
  stocks: WatchlistStock[];
  isLoading: boolean;
  addStock: (code: string) => Promise<void>;
  removeStock: (code: string) => Promise<void>;
  refreshStock: (code: string) => Promise<void>;
  refreshAll: () => void;       // Triggers SSE refresh
  isInWatchlist: (code: string) => boolean;
}

// lib/token-context.tsx [NEW]
interface TokenContextValue {
  usage: TokenUsage | null;     // { used, budget, percentage, alertLevel }
  isLoading: boolean;
  refresh: () => Promise<void>;
}
```

**Page State** (local `useState`/`useReducer`):

| Page | Local State |
|------|------------|
| Home (Recommendations tab) | `recommendations[]`, `isLoading`, `sortBy` |
| Home (Watchlist tab) | `sortBy`, `sortDirection` |
| Stock Detail | `analysis`, `isLoading`, `expandedSections[]` |
| Historical Review | `timeline[]`, `accuracy`, `isLoading` |
| Settings | `backupCode`, `isExporting`, `isImporting`, `recoveryInput` |

**State Flow Diagram**:

```
                    App (Root)
                       |
            +----------+----------+
            |                     |
    WatchlistProvider       TokenProvider
            |                     |
            +----------+----------+
                       |
                   Layout.tsx
                       |
              +--------+--------+
              |        |        |
          Header   TabBar   Content
          (token)  (tabs)   (pages)
              |
         TokenBadge
         (reads TokenContext)
```

### 3.3 API Call Layer

The existing `lib/api.ts` is extended with new endpoints and an SSE client.

```typescript
// lib/api.ts (extended)

// --- Existing functions (retained) ---
export async function getRecommendations(): Promise<RecommendationsResponse>;
export async function getStockAnalysis(code: string): Promise<StockAnalysis>;
export async function searchStocks(query: string): Promise<SearchResult[]>;
export async function getMarketOverview(): Promise<MarketOverview>;

// --- New functions ---

// Comprehensive Analysis (replaces getStockAnalysis for v2.0)
export async function getComprehensiveAnalysis(
  code: string,
  forceRefresh?: boolean
): Promise<ComprehensiveAnalysisResponse>;

// Watchlist
export async function getWatchlist(): Promise<WatchlistResponse>;
export async function addToWatchlist(code: string): Promise<void>;
export async function removeFromWatchlist(code: string): Promise<void>;
export async function refreshWatchlistStock(code: string): Promise<ComprehensiveAnalysisResponse>;

// Analysis History
export async function getAnalysisHistory(
  code: string,
  days?: number
): Promise<AnalysisHistoryResponse>;
export async function getAccuracyStats(
  code: string
): Promise<AccuracyStatsResponse>;

// Token Usage
export async function getTokenUsage(
  date?: string
): Promise<TokenUsageResponse>;

// Device Management
export async function validateDevice(
  deviceId: string
): Promise<DeviceValidationResponse>;
export async function exportWatchlist(): Promise<WatchlistExport>;
export async function importWatchlist(
  data: WatchlistExport
): Promise<ImportResult>;

// Industry
export async function getIndustryAnalysis(
  industryName: string
): Promise<IndustryAnalysisResponse>;

// News
export async function getStockNews(
  code: string,
  days?: number
): Promise<StockNewsResponse>;
```

**SSE Client for Global Refresh**:

```typescript
// lib/sse-client.ts [NEW]

export interface RefreshEvent {
  type: "start" | "progress" | "token_update" | "complete" | "error";
  data: any;
}

export function startGlobalRefresh(
  deviceId: string,
  onEvent: (event: RefreshEvent) => void,
  onError: (error: Error) => void
): AbortController {
  const controller = new AbortController();
  const url = `${API_BASE_URL}/refresh/all`;

  // Use fetch with ReadableStream for SSE (not EventSource,
  // because EventSource does not support POST with body)
  fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Device-ID": deviceId,
    },
    body: JSON.stringify({ device_id: deviceId }),
    signal: controller.signal,
  }).then(async (response) => {
    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = JSON.parse(line.substring(6));
          onEvent(data);
        }
      }
    }
  }).catch(onError);

  return controller;  // Caller can abort with controller.abort()
}
```

#### 3.3.1 SSE Connection Lifecycle Management

The Global Refresh SSE connection requires careful handling of disconnection, concurrency, reconnection, and interruption scenarios.

**Backend Disconnect Detection**:

The backend uses FastAPI's `request.is_disconnected()` to detect when the client has closed the connection. A heartbeat comment is sent every 15 seconds to keep the connection alive and detect dead clients.

```python
# api/refresh.py

@router.post("/all")
async def refresh_all(request: Request, body: RefreshRequest):
    device_id = body.device_id

    # 1. Concurrent refresh protection (see below)
    if _is_refresh_active(device_id):
        # Return current progress instead of starting new refresh
        return StreamingResponse(
            _resume_progress_stream(device_id),
            media_type="text/event-stream"
        )

    async def event_generator():
        _mark_refresh_active(device_id)
        try:
            stocks = await _get_refresh_stock_list(device_id)
            yield f"data: {json.dumps({'type': 'start', 'total': len(stocks)})}\n\n"

            for i, stock in enumerate(stocks):
                # Check client disconnect before each stock
                if await request.is_disconnected():
                    logger.info("client_disconnected", device_id=device_id, progress=f"{i}/{len(stocks)}")
                    break  # Stop processing, don't waste tokens

                # Process stock
                result = await comprehensive_analysis_service.analyze(stock.code, force_refresh=True)
                yield f"data: {json.dumps({'type': 'progress', 'current': i+1, 'total': len(stocks), 'code': stock.code, 'status': 'success'})}\n\n"

                # Heartbeat: send comment to keep connection alive
                if (i + 1) % 3 == 0:  # Every 3 stocks
                    yield ": heartbeat\n\n"

            yield f"data: {json.dumps({'type': 'complete', 'total': len(stocks)})}\n\n"
        finally:
            _mark_refresh_complete(device_id)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**Backend Heartbeat**:

```
SSE stream events:
  data: {"type": "start", ...}         -- Initial event
  data: {"type": "progress", ...}      -- Per-stock progress
  : heartbeat                          -- SSE comment (every 15s or every 3 stocks)
  data: {"type": "token_update", ...}  -- Token usage update
  data: {"type": "complete", ...}      -- Final event
```

The SSE comment (lines starting with `:`) is invisible to the application but keeps the HTTP connection alive, preventing proxies and CDNs from closing idle connections.

**Concurrent Refresh Protection**:

An in-memory dictionary tracks active refreshes per device. This prevents duplicate refreshes when a user clicks the refresh button multiple times.

```python
# api/refresh.py - Refresh state management

from dataclasses import dataclass
from datetime import datetime

@dataclass
class RefreshState:
    device_id: str
    started_at: datetime
    total_stocks: int
    completed_stocks: int
    status: str  # "in_progress", "completed", "failed"
    last_update: datetime

# In-memory refresh tracker (single-instance deployment)
_active_refreshes: dict[str, RefreshState] = {}
_REFRESH_TTL_SECONDS: int = 600  # Auto-expire after 10 minutes

def _is_refresh_active(device_id: str) -> bool:
    """
    Returns True if a refresh is currently in progress for this device.
    Also cleans up stale entries (older than TTL).
    """
    state = _active_refreshes.get(device_id)
    if state is None:
        return False
    if state.status != "in_progress":
        return False
    # Auto-expire stale refreshes
    if (datetime.now() - state.started_at).total_seconds() > _REFRESH_TTL_SECONDS:
        del _active_refreshes[device_id]
        return False
    return True

def _mark_refresh_active(device_id: str) -> None:
    _active_refreshes[device_id] = RefreshState(
        device_id=device_id,
        started_at=datetime.now(),
        total_stocks=0,
        completed_stocks=0,
        status="in_progress",
        last_update=datetime.now(),
    )

def _mark_refresh_complete(device_id: str) -> None:
    state = _active_refreshes.get(device_id)
    if state:
        state.status = "completed"
        state.last_update = datetime.now()

def _get_refresh_status(device_id: str) -> RefreshState | None:
    """Used by frontend reconnection to get current state."""
    return _active_refreshes.get(device_id)
```

**Frontend Concurrent Protection**:

The `RefreshAllButton.tsx` component disables itself during an active refresh and checks the backend status on mount:

```typescript
// components/RefreshAllButton.tsx
function RefreshAllButton() {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const controllerRef = useRef<AbortController | null>(null);

  // Disable button during refresh
  return (
    <button
      disabled={isRefreshing}
      onClick={handleRefresh}
      className={isRefreshing ? "opacity-50 cursor-not-allowed" : ""}
    >
      {isRefreshing ? "Refreshing..." : "Refresh All"}
    </button>
  );
}
```

**Frontend Network Reconnection**:

The SSE client handles network disconnection by detecting fetch errors and automatically reconnecting with state recovery:

```typescript
// lib/sse-client.ts (extended with reconnection)

export function startGlobalRefresh(
  deviceId: string,
  onEvent: (event: RefreshEvent) => void,
  onError: (error: Error) => void
): AbortController {
  const controller = new AbortController();
  let lastProgress = 0;  // Track last known progress for reconnection
  let reconnectAttempts = 0;
  const MAX_RECONNECT_ATTEMPTS = 3;
  const RECONNECT_DELAY_MS = 2000;

  async function connect() {
    try {
      const response = await fetch(`${API_BASE_URL}/refresh/all`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Device-ID": deviceId,
        },
        body: JSON.stringify({ device_id: deviceId }),
        signal: controller.signal,
      });

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      reconnectAttempts = 0;  // Reset on successful connection

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = JSON.parse(line.substring(6));
            if (data.type === "progress") {
              lastProgress = data.current;
            }
            onEvent(data);
          }
          // Ignore SSE comments (heartbeats)
        }
      }
    } catch (error) {
      if (controller.signal.aborted) return;  // User cancelled

      // Network error: attempt reconnection
      if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttempts++;
        onEvent({
          type: "reconnecting",
          data: { attempt: reconnectAttempts, lastProgress }
        });

        // Wait before reconnecting
        await new Promise(r => setTimeout(r, RECONNECT_DELAY_MS * reconnectAttempts));

        // Reconnect: the backend will return current progress if refresh is still active
        connect();
      } else {
        onError(new Error("Connection lost after 3 reconnection attempts"));
      }
    }
  }

  connect();
  return controller;
}
```

**Reconnection Status API Endpoint**:

A GET endpoint allows the frontend to check the current refresh status after reconnection:

```python
# api/refresh.py

@router.get("/status")
async def get_refresh_status(
    device_id: str = Header(alias="X-Device-ID")
) -> RefreshStatusResponse:
    """
    Returns current refresh status for the device.
    Used by frontend on reconnection to determine if refresh is still active.
    """
    state = _get_refresh_status(device_id)
    if state is None:
        return {"active": False}
    return {
        "active": state.status == "in_progress",
        "total": state.total_stocks,
        "completed": state.completed_stocks,
        "started_at": state.started_at.isoformat(),
    }
```

**Interruption Handling (User Closes Page)**:

When the user closes the page mid-refresh, the backend behavior is:

1. `request.is_disconnected()` returns `True` on the next stock processing attempt
2. The backend stops processing remaining stocks (saves tokens)
3. Stocks already processed retain their fresh analysis (idempotent)
4. The refresh state is marked as "completed" (partial completion)
5. If the user returns and starts a new refresh, only unprocessed stocks need refreshing (cache hit for recently-processed stocks within 30-min TTL)

**Maximum SSE Duration**:

The Global Refresh has an implicit timeout based on stock count: at ~5 seconds per stock and a maximum of ~40 stocks (20 recommended + 20 watchlist), the maximum duration is ~200 seconds (3.3 minutes). An explicit server-side timeout of 5 minutes is enforced:

```python
# In event_generator()
import asyncio

async def event_generator():
    start_time = datetime.now()
    MAX_DURATION_SECONDS = 300  # 5 minutes

    for i, stock in enumerate(stocks):
        elapsed = (datetime.now() - start_time).total_seconds()
        if elapsed > MAX_DURATION_SECONDS:
            yield f"data: {json.dumps({'type': 'timeout', 'processed': i, 'total': len(stocks)})}\n\n"
            break
        # ... process stock
```

**Request/Response Interceptor Pattern**:

All API calls go through `apiRequest<T>()` which handles:
1. **Device ID injection**: Automatically adds `X-Device-ID` header from `getDeviceId()`
2. **Backend wake-up**: Pings `/health` if backend may be sleeping (Render cold start)
3. **Timeout**: Default 60s, configurable per endpoint
4. **Retry**: 2 retries with exponential backoff for network errors
5. **Error mapping**: HTTP errors mapped to `ApiError` with Chinese error messages
6. **Response caching**: Client-side cache check before network call

---

## 4. Database Architecture

### 4.1 Entity-Relationship Diagram

```
+----------------------+       +------------------------+
| hot_stock_universe   |       |      watchlist         |
|----------------------|       |------------------------|
| id (PK)              |       | id (PK)                |
| code (UNIQUE)        |       | device_id              |
| name                 |       | code                   |
| industry             |       | name                   |
| market_cap           |       | industry               |
| avg_turnover_20d     |       | added_at               |
| listing_date         |       | last_analysis (JSONB)  |
| added_at             |       | last_refreshed_at      |
| last_validated_at    |       | is_active              |
| is_active            |       | notes                  |
| removal_reason       |       | UNIQUE(device_id,code) |
+----------------------+       +------------------------+
                                         |
                                         | device_id, code
                                         v
+----------------------+       +------------------------+
| stock_news_cache     |       |   analysis_history     |
|----------------------|       |------------------------|
| id (PK)              |       | id (PK)                |
| code (UNIQUE)        |       | code                   |
| news_items (JSONB)   |       | name                   |
| fetched_at           |       | analysis_date          |
| expires_at           |       | source                 |
+----------------------+       | device_id (nullable)   |
                               | price_at_analysis      |
+----------------------+       | change_percent         |
| industry_data_cache  |       | composite_score        |
|----------------------|       | technical_analysis(J)  |
| id (PK)              |       | fundamental_analysis(J)|
| industry_name(UNIQUE)|       | news_analysis (JSONB)  |
| industry_data (JSONB)|       | earnings_analysis(JSONB|
| fetched_at           |       | industry_analysis(JSONB|
| expires_at           |       | ai_comprehensive_summary|
+----------------------+       | predicted_direction    |
                               | predicted_change_low   |
                               | predicted_change_high  |
                               | predicted_confidence   |
                               | predicted_key_factors(J|
                               | suggestion_action      |
                               | buy/stop/take prices   |
                               | created_at             |
                               | UNIQUE(code,date,      |
                               |   source,device_id)    |
                               +------------------------+
                                         |
                                         | analysis_history_id (FK)
                                         v
                               +------------------------+
                               | prediction_tracking    |
                               |------------------------|
                               | id (PK)                |
                               | analysis_history_id(FK)|
                               | code                   |
                               | prediction_date        |
                               | evaluation_date        |
                               | predicted_direction    |
                               | predicted_change_low   |
                               | predicted_change_high  |
                               | predicted_confidence   |
                               | actual_price           |
                               | actual_change_percent  |
                               | actual_direction       |
                               | direction_correct      |
                               | range_correct          |
                               | magnitude_error        |
                               | status                 |
                               | evaluated_at           |
                               | created_at             |
                               +------------------------+

+------------------------+
| token_usage_log        |
|------------------------|
| id (PK)                |
| usage_date             |
| request_type           |
| stock_code             |
| input_tokens           |
| output_tokens          |
| total_tokens (computed)|
| model                  |
| success                |
| error_message          |
| response_time_ms       |
| created_at             |
+------------------------+

Views:
  daily_token_usage       -- Aggregates token_usage_log by date
  prediction_accuracy_stats -- Aggregates prediction_tracking by code
```

### 4.2 Index Strategy

| Table | Index | Columns | Purpose |
|-------|-------|---------|---------|
| watchlist | `idx_watchlist_device` | `device_id` | Fast lookup by device |
| watchlist | `idx_watchlist_active` | `device_id, is_active` | Active watchlist query |
| watchlist | `idx_watchlist_code` | `code` | Cross-device stock lookup |
| analysis_history | `idx_analysis_history_code_date` | `code, analysis_date` | Timeline query |
| analysis_history | `idx_analysis_history_date` | `analysis_date` | Date-range queries |
| analysis_history | `idx_analysis_history_device` | `device_id` | User-specific history |
| analysis_history | `idx_analysis_history_source` | `source` | Filter by source type |
| prediction_tracking | `idx_prediction_tracking_eval_date` | `evaluation_date, status` | Due predictions query |
| prediction_tracking | `idx_prediction_tracking_code` | `code` | Per-stock accuracy |
| prediction_tracking | `idx_prediction_tracking_status` | `status` | Status filtering |
| token_usage_log | `idx_token_usage_date` | `usage_date` | Daily aggregation |
| stock_news_cache | `idx_news_cache_expires` | `expires_at` | Cache cleanup |
| industry_data_cache | `idx_industry_cache_expires` | `expires_at` | Cache cleanup |
| hot_stock_universe | `idx_hot_universe_active` | `is_active` | Active universe query |

### 4.3 Query Optimization

**Most Frequent Queries and Their Optimization**:

| Query | Estimated Frequency | Optimization |
|-------|-------------------|--------------|
| Get watchlist by device_id (active) | Every page load | Composite index on `(device_id, is_active)` |
| Get analysis history by code (last 30 days) | Every history page view | Composite index on `(code, analysis_date)` + LIMIT |
| Get pending predictions due today | Once daily (scheduled) | Index on `(evaluation_date, status)` |
| Get daily token usage | Every API call (in-memory counter, periodic DB sync) | In-memory counter reduces DB hits to ~12/hour |
| Get cached news for stock | Every comprehensive analysis | UNIQUE index on `code` |
| Get cached industry data | Every comprehensive analysis | UNIQUE index on `industry_name` |

### 4.4 Data Retention and Cleanup

| Data Type | Retention | Cleanup Method | Frequency |
|-----------|----------|----------------|-----------|
| analysis_history | 90 days | `DELETE WHERE created_at < NOW() - INTERVAL '90 days'` | Daily at 03:00 |
| prediction_tracking | Indefinite | N/A (small rows, useful for long-term accuracy) | N/A |
| token_usage_log | 90 days | `DELETE WHERE usage_date < NOW() - INTERVAL '90 days'` | Daily at 03:00 |
| stock_news_cache | Auto (expires_at) | `DELETE WHERE expires_at < NOW()` | Daily at 03:00 |
| industry_data_cache | Auto (expires_at) | `DELETE WHERE expires_at < NOW()` | Daily at 03:00 |
| watchlist (is_active=false) | 30 days | `DELETE WHERE is_active=false AND updated_at < NOW() - 30 days` | Weekly |

**Storage Growth Estimate (Revised)**:

The PRD's storage estimate assumed 30 rows/day for analysis_history. At scale (500 DAU, 8 watchlist stocks each), a deduplicated approach is used:

| Scenario | analysis_history rows/day | Monthly Storage |
|----------|--------------------------|-----------------|
| Launch (50 DAU, 3 stocks each) | 10 (recs) + ~50 (unique watchlist stocks) = ~60 | ~9 MB |
| 90 days (500 DAU, 8 stocks each) | 10 (recs) + ~200 (unique watchlist stocks) = ~210 | ~31 MB |
| With 90-day retention | Max ~210 * 90 = ~18,900 rows | ~94 MB peak |

**Key Optimization**: Watchlist snapshots are saved per unique stock, not per user per stock. If 100 users all watch stock 600519, only one snapshot is saved. The analysis_history entry with `source="watchlist"` and `device_id=NULL` represents the shared snapshot. This keeps storage within the Supabase 500MB free tier.

---

## 5. Security Architecture

### 5.1 API Key Management

| Secret | Storage | Access Pattern |
|--------|---------|---------------|
| `SUPABASE_URL` | Render env var / `.env` | Backend only; never exposed to frontend |
| `SUPABASE_KEY` | Render env var / `.env` | Backend only; service role key |
| `GLM_API_KEY` | Render env var / `.env` | Backend only; used by glm_service |
| `NEXT_PUBLIC_API_URL` | Netlify env var / `.env.local` | Frontend; only the backend URL (not a secret) |
| `SENTRY_DSN` | Render env var | Backend only; error tracking |

**Security Rules**:
- No API keys in source code (enforced by CI check)
- `.env` files in `.gitignore` (verified)
- `.env.example` files contain placeholder values only
- Frontend never communicates directly with Supabase, GLM-4, or data sources

### 5.2 Device Identity Authentication

```
+---------------------+
|   First Visit       |
|                     |
| 1. Generate UUID v4 |
| 2. Store in         |
|    localStorage     |
| 3. Show backup code |
|    dialog           |
+---------------------+
         |
         v
+---------------------+
|   Every API Call     |
|                     |
| Header:             |
| X-Device-ID: uuid   |
|                     |
| Backend validates:  |
| - Is valid UUID     |
| - Creates device    |
|   record on first   |
|   watchlist action   |
+---------------------+
         |
         v
+---------------------+
|   Data Loss         |
|   Recovery          |
|                     |
| POST /device/       |
|   validate          |
| { device_id: "old"} |
|                     |
| If exists:          |
|  Replace current    |
|  localStorage UUID  |
|  with old UUID      |
+---------------------+
```

**Backend Validation Rules**:
- `X-Device-ID` header is required for `/watchlist/*`, `/device/*`, `/refresh/all` endpoints
- `X-Device-ID` is optional for `/stock/*`, `/recommendations`, `/analysis/*` endpoints
- Invalid or missing `X-Device-ID` on required endpoints returns `401 Unauthorized`
- No rate limiting per device in v2.0 (global rate limiting only)

### 5.3 CORS Configuration

```python
# Already configured in main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",           # Local development
        "https://stock-advisor.netlify.app",
        "https://claude-stock-advisor.netlify.app",
        "https://a-stock-advisor-cn.netlify.app",
        "https://my-stock-advisor.netlify.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],   # Allows X-Device-ID custom header
)
```

### 5.4 API Rate Limiting (Client-Facing)

In addition to internal rate limiting for external data sources, the backend implements client-facing rate limiting to prevent abuse.

```python
# Using slowapi middleware
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Global: 60 requests per minute per IP
# Comprehensive analysis: 10 per minute per IP
# Global refresh: 2 per minute per IP
# Recommendation generation: 1 per 10 minutes
```

### 5.5 Data Export/Import Security

- Export JSON files are plain text with no encryption (no sensitive data)
- Import validates JSON structure before processing
- Import uses `device_id` from the authenticated header, not from the JSON file
- Maximum import size: 1MB
- Stocks in import are validated against known stock codes

---

## 6. Performance Optimization Design

### 6.1 Cache Hierarchy

```
User Request
     |
     v
+----------------+  hit   +---------+
| Browser Cache  |------->| Return  |
| (3 min, API    |        | cached  |
|  responses in  |        +---------+
|  Map/memory)   |
+----------------+
     | miss
     v
+----------------+  hit   +---------+
| Backend L1     |------->| Return  |
| In-Memory Cache|        | cached  |
| (TTLCache)     |        +---------+
| 3-30 min       |
+----------------+
     | miss
     v
+----------------+  hit   +---------+
| Backend L2     |------->| Return  |
| DB Cache       |        | cached  |
| (news,industry)|        +---------+
| 1-24 hours     |
+----------------+
     | miss
     v
+----------------+
| External API   |
| Call (rate-    |
| limited)       |
+----------------+
```

### 6.2 Parallel Data Fetching

Within a single comprehensive analysis, data sources are fetched in parallel groups to minimize total latency.

```
Time  0s     1s     2s     3s     4s     5s
      |------|------|------|------|------|

Group A (parallel):
  EastMoney quote   [======]
  EastMoney news    [========]

Group B (parallel):
  AKShare earnings  [========]
  AKShare announce  [======]

Sequential (depends on quote):
  EastMoney history [==========]
  Indicators calc   [====]
  Score calc        [==]

Group C (check cache, fetch if miss):
  Industry data     [====] (often cached)

GLM-4 (after all data):
                              [========]

Total: ~4-5 seconds (uncached)
```

### 6.3 Frontend Optimization

| Optimization | Implementation | Impact |
|-------------|----------------|--------|
| **Static Generation** | Next.js SSG for layout, shell | First paint < 1s |
| **Lazy Loading** | Accordion sections collapsed by default; content loaded on expand | Reduces initial render payload |
| **Image Optimization** | No images in MVP (text-based UI) | N/A |
| **Bundle Splitting** | Next.js automatic code splitting per page | Smaller initial JS bundle |
| **API Response Cache** | Client-side Map with 3-min TTL | Avoids redundant network calls |
| **Skeleton Loading** | Shimmer placeholders during data fetch | Perceived performance improvement |
| **Progressive Enhancement** | Show cached data immediately, update when fresh data arrives | Instant perceived response |

### 6.4 Backend Optimization

| Optimization | Implementation | Impact |
|-------------|----------------|--------|
| **asyncio throughout** | All I/O uses `async/await`; AKShare calls wrapped in `to_thread` | Non-blocking request handling |
| **Connection pooling** | httpx.AsyncClient with connection pool for EastMoney | Reuse HTTP connections |
| **Shared industry cache** | Industry data cached per sector, shared across stocks | ~70% fewer industry API calls |
| **Smart Global Refresh** | Sequential stocks, parallel dimensions within each stock | Balanced throughput vs rate limits |
| **Token budget in-memory** | In-memory counter, DB sync every 5 min | DB query avoided on every AI call |
| **Batch prediction evaluation** | Single query for all due predictions, batch update | Efficient DB access |

### 6.5 Memory Budget Analysis (Render 512MB Constraint)

Render free tier provides 512MB RAM. The following analysis estimates memory consumption per component and defines mitigation strategies for peak scenarios.

#### 6.5.1 Component Memory Estimates

| Component | Estimated Memory | Notes |
|-----------|-----------------|-------|
| Python 3.11 runtime | ~25 MB | Base interpreter |
| FastAPI + Uvicorn | ~30 MB | ASGI server + routing + middleware |
| APScheduler | ~15 MB | In-process scheduler with job store |
| structlog + logging | ~5 MB | Logging infrastructure |
| slowapi (rate limiter) | ~5 MB | Middleware state |
| httpx.AsyncClient (3 pools) | ~15 MB | Connection pools for EastMoney, AKShare, GLM-4 |
| In-memory L1 cache (TTLCache) | ~50 MB max | 200 quote + 200 indicator + 100 comprehensive entries |
| Rate limiter state + circuit breakers | ~5 MB | Token buckets + breaker state for 5 sources |
| Trading calendar (in-memory set) | ~1 MB | ~250 dates per year, 2 years |
| **Baseline Total** | **~151 MB** | Before any request processing |

#### 6.5.2 Per-Request Memory Overhead

| Operation | Additional Memory | Duration |
|-----------|------------------|----------|
| Single comprehensive analysis | ~30 MB | pandas DataFrame (AKShare) + API responses; released after request |
| GLM-4 request/response payload | ~2 MB | Prompt + response JSON |
| News fetch + parse | ~3 MB | HTML parsing + dedup |
| Industry data fetch | ~5 MB | DataFrame + sector data |
| **Peak per-request** | **~40 MB** | Released after response sent |

#### 6.5.3 Peak Scenario Analysis

**Scenario A: Daily Recommendation Generation (17:30 CST)**

The most memory-intensive operation. Processes 50-80 stocks through a 4-stage pipeline.

```
Stage 1: Fetch quotes for all stocks
  - Processed in batches of 10
  - Peak: 10 concurrent quote fetches = ~10 MB
  - Each batch result released before next batch

Stage 2: Technical screening (local calculation)
  - pandas DataFrames for ~60 stocks
  - Peak: ~30 MB (10 DataFrames in memory at once, batched)

Stage 3: Score and rank
  - In-memory sort of ~60 score objects
  - Peak: ~2 MB

Stage 4: Full comprehensive analysis x 10
  - Sequential processing (1 at a time)
  - Peak: ~40 MB per stock (released between stocks)
```

**Peak memory during recommendation generation**:
- Baseline: 151 MB
- Active processing: ~70 MB (batch quote + screening + 1 analysis)
- **Total peak: ~221 MB** (well within 512 MB)

**Scenario B: Global Refresh (20 stocks, user-triggered)**

- Baseline: 151 MB
- Sequential processing: 1 stock at a time
- Per-stock overhead: ~40 MB (released between stocks)
- **Total peak: ~191 MB**

**Scenario C: Concurrent user requests during recommendation job**

Worst case: recommendation job running + 2 concurrent user analysis requests.

- Baseline: 151 MB
- Recommendation job active: ~70 MB
- 2 concurrent analyses: ~80 MB
- **Total peak: ~301 MB** (within 512 MB but approaching limit)

#### 6.5.4 Memory Budget Summary

```
+----------------------------------------------------------+
|                    512 MB Render Limit                     |
+----------------------------------------------------------+
|                                                            |
|  [===== 151 MB Baseline =====]                            |
|                                                            |
|  [=== 70 MB Peak Processing ===]                          |
|                                                            |
|  [== 80 MB Concurrent Users ==]                           |
|                                                            |
|  [= ~50 MB Safety Margin =]                              |
|                                                            |
|  Total Peak: ~301 MB / 512 MB = 59% utilization           |
|                                                            |
+----------------------------------------------------------+
```

#### 6.5.5 Mitigation Measures

| Measure | Implementation | Impact |
|---------|---------------|--------|
| **L1 cache size limit** | `TTLCache(maxsize=200)` for quotes/indicators, `TTLCache(maxsize=100)` for comprehensive | Caps cache memory at ~50 MB |
| **Batch processing in recommendations** | Process stocks in batches of 10 for Stage 1-2; release DataFrame after each batch | Prevents 60 simultaneous DataFrames |
| **Explicit DataFrame cleanup** | Call `del df` and `gc.collect()` after each AKShare operation in recommendation job | Releases pandas memory promptly |
| **Sequential Global Refresh** | Process 1 stock at a time (already designed) | Limits concurrent memory to 1 analysis |
| **Memory monitoring in /health** | Add `psutil.Process().memory_info().rss` to health endpoint | Real-time visibility |
| **Memory threshold alert** | Log WARNING when RSS > 410 MB (80% of 512 MB) | Early warning before OOM |

**Health endpoint memory reporting**:

```python
import psutil

@app.get("/health")
async def health_check():
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    return {
        # ... existing fields ...
        "memory": {
            "used_mb": round(memory_mb, 1),
            "limit_mb": 512,
            "percentage": round(memory_mb / 512 * 100, 1),
            "alert": "warning" if memory_mb > 410 else "normal"
        }
    }
```

**New dependency**: `psutil` added to `requirements.txt` for memory monitoring.

#### 6.5.6 Upgrade Path

If memory becomes a constraint at scale (>50 DAU with active Global Refresh usage):

| Trigger | Action | Cost |
|---------|--------|------|
| RSS consistently > 400 MB | Reduce L1 cache maxsize to 100/100/50 | Free |
| RSS spikes causing OOM kills | Upgrade to Render Starter Plan | $7/month (512 MB - 1 GB RAM) |
| > 100 DAU with heavy refresh | Upgrade to Render Standard Plan | $25/month (2 GB RAM) |

### 6.6 Cold Start Mitigation (Render Free Tier)

Render free tier spins down the backend after 15 minutes of inactivity. Cold start takes 30-60 seconds.

**Mitigation Strategy**:
1. Frontend pings `/health` on page load (existing behavior)
2. Frontend shows "Server is waking up..." message during cold start (existing)
3. 90-second timeout on initial health check (existing)
4. **New**: Scheduled jobs (APScheduler) keep the process alive during market hours (09:00-18:00 CST) -- the scheduler itself generates periodic activity
5. **Future (post-MVP)**: Upgrade to Render paid tier ($7/month) at 50 DAU milestone

---

## 7. Monitoring and Logging

### 7.1 Structured Logging

```python
# Using Python's built-in logging with structlog for structured output

import structlog

logger = structlog.get_logger()

# Log levels and their usage:
# DEBUG:   Detailed internal state (disabled in production)
# INFO:    Normal operations (API call completed, cache hit/miss)
# WARNING: Non-critical issues (rate limit approaching, fallback activated)
# ERROR:   Failed operations (API call failed, circuit breaker tripped)
# CRITICAL: System-level failures (DB connection lost, scheduler stopped)

# Example structured log output:
# {"event": "comprehensive_analysis", "code": "600519",
#  "cached": false, "duration_ms": 4200, "ai_tokens": 2800,
#  "dimensions_fetched": 5, "level": "info", "timestamp": "2026-02-09T17:30:00Z"}
```

**Log Categories**:

| Category | Log Fields | Purpose |
|----------|-----------|---------|
| API Request | method, path, status, duration_ms, device_id | Request tracing |
| External API | source, endpoint, status, duration_ms, cached | Data source monitoring |
| Rate Limiter | source, action (acquire/wait/reject), wait_ms | Rate limit visibility |
| Circuit Breaker | source, state_change (CLOSED->OPEN, etc.) | Fault tracking |
| Token Usage | request_type, stock_code, tokens, budget_remaining | Cost monitoring |
| Scheduler | job_name, status, duration_s, stocks_processed | Job execution tracking |
| Cache | store, key, action (hit/miss/set/evict) | Cache effectiveness |

### 7.2 Health Check Endpoint (Extended)

```python
# /health endpoint returns system health with component status

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "components": {
            "database": await check_supabase_connection(),
            "scheduler": scheduler.running,
            "circuit_breakers": {
                source: breaker.state
                for source, breaker in rate_limiter_service.breakers.items()
            },
            "token_budget": {
                "used": token_monitor.daily_used,
                "budget": token_monitor.DAILY_BUDGET,
                "percentage": round(token_monitor.daily_used / token_monitor.DAILY_BUDGET * 100, 1)
            }
        },
        "timestamp": datetime.now().isoformat()
    }
```

### 7.3 Error Tracking (Sentry)

Sentry is integrated in Phase 3 for production error tracking.

```python
# main.py (Phase 3 addition)
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=settings.sentry_dsn,
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,  # 10% of requests traced
    environment="production",
)
```

**Sentry Alerting Rules**:
- Alert on any 500 error
- Alert if error rate exceeds 5% in 5-minute window
- Alert if circuit breaker opens for any data source
- Alert if token budget exceeds 90%

### 7.4 External Uptime Monitoring

UptimeRobot (free tier) monitors:
- `/health` endpoint every 5 minutes
- Alert via email if endpoint is down for > 5 minutes
- Monthly uptime report for 99% target tracking

### 7.5 Data Source Availability Dashboard

The existing `data_source_log` table from v1.0 is extended. The `/health` endpoint exposes circuit breaker states, giving a real-time view of data source availability.

```
Data Source Health Dashboard (via /health response):

  EastMoney Quote:  [CLOSED]  -- Normal
  EastMoney News:   [CLOSED]  -- Normal
  AKShare:          [CLOSED]  -- Normal
  GLM-4:            [HALF_OPEN] -- Testing recovery
  Yahoo Finance:    [CLOSED]  -- Normal (standby)
```

---

## 8. Development and Deployment

### 8.1 Git Workflow

```
main (production)
  |
  +-- feature/comprehensive-analysis
  +-- feature/watchlist
  +-- feature/prediction-tracking
  +-- fix/rate-limiter-bug
  +-- chore/add-unit-tests
```

**Branch Rules**:
- `main` is the production branch; auto-deploys to Netlify and Render
- Feature branches created from `main`
- Pull requests required for all merges to `main`
- CI must pass before merge (lint + tests)
- Single developer workflow: feature branches are short-lived (1-3 days)

### 8.2 CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/ci.yml

name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  # Frontend checks
  frontend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm run lint
      - run: npx tsc --noEmit

  # Backend checks
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r backend/requirements.txt
      - run: pip install pytest pytest-cov pytest-asyncio respx
      - run: |
          cd backend
          python -m pytest tests/ \
            --cov=app \
            --cov-report=term-missing \
            --cov-fail-under=80

  # Compliance check
  compliance-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          # Check for prohibited language in frontend
          if grep -r "投资建议\|买入推荐\|保证收益\|专家意见" src/; then
            echo "FAIL: Prohibited language found in frontend"
            exit 1
          fi
          echo "PASS: No prohibited language found"
      - run: |
          # Check for hardcoded API keys
          if grep -rE "(sk-|glm_|supabase.*key.*=.*['\"])" --include="*.py" --include="*.ts" --include="*.tsx" .; then
            echo "FAIL: Possible hardcoded API key found"
            exit 1
          fi
          echo "PASS: No hardcoded keys found"
```

### 8.3 Environment Configuration

**Backend Environment Variables** (`.env`):

```bash
# Application
APP_NAME="Stock Advisor API"
DEBUG=false
ENVIRONMENT=production    # production | development

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGci...

# AI
GLM_API_KEY=xxx

# CORS
CORS_ORIGINS=["https://my-stock-advisor.netlify.app"]

# Token Budget
TOKEN_DAILY_BUDGET=500000

# Sentry (Phase 3)
SENTRY_DSN=https://xxx@sentry.io/xxx

# Rate Limiting
RATE_LIMIT_EASTMONEY_QUOTE=5    # requests per second
RATE_LIMIT_EASTMONEY_NEWS=3
RATE_LIMIT_AKSHARE=3
RATE_LIMIT_GLM4=1
RATE_LIMIT_YAHOO=2
```

**Frontend Environment Variables** (`.env.local`):

```bash
NEXT_PUBLIC_API_URL=https://stock-advisor-api-6vtb.onrender.com
```

### 8.4 Deployment Flow

```
Developer pushes to main
         |
         v
GitHub Actions CI runs
  - Frontend: lint + type check
  - Backend: pytest + coverage
  - Compliance: language scan + key scan
         |
    (all pass)
         |
    +----+----+
    |         |
    v         v
Netlify     Render
auto-       auto-
deploy      deploy
(2 min)     (5 min)
    |         |
    v         v
CDN edge   Web service
updated    restarted
```

### 8.5 New Dependencies to Add

**Backend** (`requirements.txt` additions):

```
# Scheduler
APScheduler==3.10.4

# Rate limiting middleware
slowapi==0.1.9

# Structured logging
structlog==24.1.0

# Cache utilities
cachetools==5.3.3

# Error tracking (Phase 3)
sentry-sdk[fastapi]==1.40.0

# Testing
pytest==8.0.0
pytest-asyncio==0.23.4
pytest-cov==4.1.0
respx==0.20.2
httpx==0.27.0

# Memory monitoring
psutil==5.9.8
```

**Frontend** (`package.json` additions):

```json
{
  "dependencies": {
    "uuid": "^9.0.0"
  },
  "devDependencies": {
    "@playwright/test": "^1.41.0"
  }
}
```

---

## 9. Technical Risks and Mitigations

### 9.1 Risk Register

| ID | Risk | Probability | Impact | Severity | Mitigation | Owner |
|----|------|-------------|--------|----------|------------|-------|
| TR-1 | EastMoney API changes or blocks IP | Medium | High | HIGH | Circuit breaker + Yahoo fallback + User-Agent rotation + rate limiting (Section 2.4) | Backend |
| TR-2 | GLM-4 quota exceeded or service unavailable | Medium | Medium | MEDIUM | Template fallback mode + token budget enforcement + in-memory analysis | Backend |
| TR-3 | Render cold start frustrates users | High | Medium | HIGH | Frontend wake-up flow + scheduler keeps process alive during market hours | Full-stack |
| TR-4 | Supabase 500MB storage limit reached | Low (with cleanup) | High | MEDIUM | 90-day retention + deduplicated snapshots + storage monitoring | Backend |
| TR-5 | APScheduler misses jobs on process restart | Medium | Medium | MEDIUM | `misfire_grace_time` + manual trigger endpoints + idempotent jobs | Backend |
| TR-6 | AKShare blocking call freezes event loop | Medium | High | HIGH | All AKShare calls wrapped in `asyncio.to_thread()` | Backend |
| TR-7 | Concurrent Global Refresh requests | Low | Low | LOW | In-memory `_active_refreshes` dict tracks per-device state; duplicate requests return current progress (Section 3.3.1) | Backend |
| TR-8 | localStorage cleared loses watchlist | Medium | High | HIGH | Backup code system + JSON export + recovery flow (PRD 4.4.1) | Frontend |
| TR-9 | AI output validation failure | Medium | Low | LOW | Strict JSON validation + retry + template fallback | Backend |
| TR-10 | Rate limit cascade during peak usage | Medium | Medium | MEDIUM | Priority queue (user > refresh > scheduled) + dynamic concurrency reduction | Backend |

### 9.2 Architecture Decision Records

#### ADR-001: In-Process Scheduler vs External Job Service

**Status**: Accepted

**Context**: The system needs scheduled jobs (daily recommendations, prediction evaluation). Options: (1) APScheduler in-process, (2) External service (Render cron job), (3) GitHub Actions scheduled workflow.

**Decision**: APScheduler in-process.

**Consequences**:
- Positive: No additional infrastructure; jobs have direct access to services and cache; simple deployment.
- Negative: Jobs lost if process restarts; single-instance only (cannot scale horizontally).
- Mitigation: `misfire_grace_time` handles restarts; horizontal scaling is not needed at MVP scale.

#### ADR-002: In-Memory Cache vs Redis

**Status**: Accepted

**Context**: The system needs a fast cache layer for API responses. Options: (1) Python in-memory (cachetools), (2) Redis (external service), (3) Supabase-only caching.

**Decision**: Python in-memory cache (cachetools).

**Consequences**:
- Positive: Zero additional infrastructure cost; zero latency; sufficient for single-instance deployment.
- Negative: Cache lost on process restart; not shared across instances.
- Mitigation: TTLs are short (3-30 min); losing cache only means a few extra API calls; DB cache (L2) survives restarts.

#### ADR-003: SSE vs WebSocket for Global Refresh

**Status**: Accepted (aligned with PRD)

**Context**: Global Refresh needs real-time progress updates. Options: (1) SSE, (2) WebSocket, (3) Polling.

**Decision**: SSE (Server-Sent Events).

**Consequences**:
- Positive: Simpler than WebSocket; one-way communication is sufficient; works through most proxies.
- Negative: POST + SSE requires fetch API (not native EventSource); slightly more complex client code.
- Mitigation: Custom SSE client using fetch ReadableStream (Section 3.3).

#### ADR-004: Deduplicated Watchlist Snapshots

**Status**: Accepted

**Context**: Daily snapshots for watchlist stocks could create N rows per user per stock. At 500 DAU with 8 stocks each, this is 4,000 rows/day.

**Decision**: Save one snapshot per unique stock (not per user per stock). Watchlist entries reference the shared snapshot.

**Consequences**:
- Positive: Storage reduced from 4,000 to ~200 rows/day; well within Supabase free tier.
- Negative: Cannot track per-user analysis history (all users see the same snapshot for a given stock on a given date).
- Mitigation: Acceptable for MVP; per-user differentiation is not a requirement in PRD v2.0.

---

## 10. PRD Feature Mapping

This section maps every PRD v2.0 feature to its implementation path in the architecture.

### 10.1 Feature 1: AI Comprehensive Analysis (PRD 4.2)

| PRD Requirement | Architecture Component | Implementation Path |
|----------------|----------------------|-------------------|
| 5-dimensional analysis | `comprehensive_analysis_service.py` | Orchestrates all 5 services in parallel |
| Technical indicators | `indicator_service.py` (existing) | Unchanged; extended with trend prediction |
| Fundamental data | `fundamental_service.py` (new) | AKShare integration |
| News data (7 days) | `news_service.py` (new) | EastMoney News API |
| Industry analysis | `industry_service.py` (new) | AKShare + EastMoney |
| AI comprehensive summary | `glm_service.py` (extended) | GLM-4 with 5-dim prompt |
| Composite score | `strategy_service.py` (existing) | Extended weighting |
| Response < 5s (uncached) | Parallel fetching + cache | Architecture Section 6.2 |
| Response < 2s (cached) | In-memory L1 cache (30 min) | Architecture Section 6.1 |
| Template fallback | `comprehensive_analysis_service._build_template_fallback()` | Rule-based summary |
| API endpoint | `GET /api/v1/stock/{code}/comprehensive` | `api/stock.py` |

### 10.2 Feature 2: Daily Smart Recommendations (PRD 4.3)

| PRD Requirement | Architecture Component | Implementation Path |
|----------------|----------------------|-------------------|
| Hot stock universe (50-80) | `hot_stock_service.py` + `hot_stock_universe` table | Weekly refresh job |
| 4-stage pipeline | `scheduler.py` -> `generate_daily_recommendations()` | APScheduler at 17:30 |
| Technical screening | `strategy_service.py` | MACD/RSI/MA/Volume filters |
| Top 10 selection | Scoring + ranking in recommendation job | Composite score > 60, top 10 |
| Full analysis per stock | `comprehensive_analysis_service.analyze()` x 10 | Reuses Feature 1 |
| 17:30 CST timing | APScheduler CronTrigger | `scheduler.py` |
| Token usage logged | `token_monitor_service.log_usage()` | Per GLM-4 call |
| API endpoint | `GET /api/v1/recommendations` | `api/recommendations.py` (extended) |

### 10.3 Feature 3: Watchlist Management (PRD 4.4)

| PRD Requirement | Architecture Component | Implementation Path |
|----------------|----------------------|-------------------|
| Add/remove/refresh | `watchlist_service.py` | CRUD operations |
| Device identity (UUID) | `lib/device-id.ts` + `X-Device-ID` header | Frontend generates, backend validates |
| Backup code system | `api/device.py` + `BackupCodeDisplay.tsx` | Display UUID, recovery flow |
| Export/import JSON | `watchlist_service.export_data()` / `import_data()` | `api/device.py` endpoints |
| Max 50 stocks | `watchlist_service.add_stock()` limit check | Database count + enforce |
| Idempotent add | `watchlist_service.add_stock()` returns 200 if exists | UNIQUE constraint handling |
| API endpoints | `/watchlist`, `/watchlist/add`, `/watchlist/remove` | `api/watchlist.py` |

### 10.4 Feature 4: Global Refresh (PRD 4.5)

| PRD Requirement | Architecture Component | Implementation Path |
|----------------|----------------------|-------------------|
| Refresh all stocks | `api/refresh.py` SSE endpoint | POST /refresh/all |
| Progress bar (SSE) | `sse-client.ts` + `RefreshProgress.tsx` | EventSource via fetch |
| Token tracking | `token_monitor_service` events in SSE stream | `token_update` events |
| < 2 min for 20 stocks | Rate-limited sequential processing | 1 stock at a time, parallel dims |
| Cancel mid-process | `AbortController` in frontend, check signal in backend | Graceful stop |
| Partial results | Each stock committed individually | Already-refreshed stocks retained |

### 10.5 Feature 5: Historical Review + Prediction Tracking (PRD 4.6)

| PRD Requirement | Architecture Component | Implementation Path |
|----------------|----------------------|-------------------|
| Daily 17:30 snapshot | `scheduler.py` -> `save_watchlist_snapshots()` | APScheduler job |
| 5-day evaluation | `prediction_tracking_service.evaluate_due_predictions()` | APScheduler job at 17:40 |
| Trading calendar | `akshare_service.get_trading_calendar()` | AKShare + cache |
| Timeline view | `api/analysis_history.py` + `PredictionTimeline.tsx` | GET /analysis/history/{code} |
| Accuracy stats | `prediction_tracking_service.get_accuracy_stats()` | GET /analysis/accuracy/{code} |
| Direction accuracy | `prediction_tracking` table, `direction_correct` field | Automated calculation |
| Range accuracy | `prediction_tracking` table, `range_correct` field | Automated calculation |
| Grade (A/B/C) | `prediction_tracking_service._calculate_grade()` | Derived from accuracy % |
| Minimum sample size | Grade shown only when `total_evaluated >= 20` | Service logic |
| 90-day retention | `analysis_history_service.cleanup_old_records()` | Daily cleanup job |

### 10.6 Token Monitoring (PRD 4.5, 5.4)

| PRD Requirement | Architecture Component | Implementation Path |
|----------------|----------------------|-------------------|
| Track usage | `token_monitor_service.log_usage()` | Every GLM-4 call |
| Display in header | `TokenBadge.tsx` + `token-context.tsx` | GET /token/usage |
| 80% warning | `TokenWarning.tsx` yellow banner | `alert_level: "warning"` |
| 100% hard stop | `token_monitor_service.check_budget()` raises exception | Template fallback activates |
| Budget: 500K/day | `TOKEN_DAILY_BUDGET` env var | Configurable |

### 10.7 Rate Limiting and Backpressure (PRD 5.7)

| PRD Requirement | Architecture Component | Implementation Path |
|----------------|----------------------|-------------------|
| Per-source rate limits | `rate_limiter_service.py` | Token bucket per source |
| Priority queue | `rate_limiter_service.acquire(priority)` | HIGH/MEDIUM/LOW |
| Exponential backoff | `infrastructure/rate_limiter.py` | 2^attempt + jitter |
| Circuit breaker | `infrastructure/circuit_breaker.py` | Per-source, 3-state |
| Global Refresh optimization | Sequential stocks, parallel dims | Architecture Section 2.5 |

### 10.8 Testing Strategy (PRD Section 13)

| PRD Requirement | Architecture Component | Implementation Path |
|----------------|----------------------|-------------------|
| Unit tests > 80% | `tests/unit/` | pytest + pytest-cov |
| Integration tests | `tests/integration/` | pytest + httpx + respx |
| E2E tests (5 scenarios) | Playwright test suite | E2E-001 through E2E-005 |
| AI quality validation | Custom validation in glm_service | Structural + content scoring |
| Compliance automation | CI pipeline compliance check | GitHub Actions job |
| Mock data | `tests/fixtures/` | Frozen API responses |

---

## Appendix A: Pydantic Models (Key Schemas)

```python
# models/schemas.py (key additions for v2.0)

class ComprehensiveAnalysisResponse(BaseModel):
    code: str
    name: str
    exchange: str
    analysis_timestamp: datetime
    composite_score: int
    basic_info: BasicInfo
    technical_analysis: TechnicalAnalysis
    fundamental_analysis: FundamentalAnalysis | None
    recent_developments: RecentDevelopments
    industry_analysis: IndustryAnalysis | None
    ai_comprehensive_summary: AISummary
    trading_suggestion: TradingSuggestion
    disclaimer: str

class AISummary(BaseModel):
    overall_recommendation: Literal["strong_buy", "buy", "hold", "reduce", "avoid"]
    confidence: Literal["high", "medium", "low"]
    positive_factors: list[str]
    risk_factors: list[str]
    price_prediction_5d: PricePrediction
    full_text: str

class WatchlistStock(BaseModel):
    code: str
    name: str
    industry: str | None
    added_at: datetime
    last_refreshed_at: datetime | None
    current_price: float | None
    change_percent: float | None
    composite_score: int | None
    recommendation: str | None
    last_analysis_summary: str | None
    prediction_accuracy: PredictionAccuracy | None

class TimelineEntry(BaseModel):
    analysis_date: date
    composite_score: int
    recommendation: str
    predicted_direction: str
    predicted_change: PriceRange
    confidence: str
    price_at_analysis: float
    actual_result: ActualResult | None
    evaluation_status: Literal["pending", "evaluated", "skipped"]
    evaluation_date: date | None
    key_factors: list[str]

class TokenUsageResponse(BaseModel):
    date: date
    total_tokens: int
    input_tokens: int
    output_tokens: int
    daily_budget: int
    usage_percentage: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    alert_level: Literal["normal", "warning", "critical"]
```

## Appendix B: New Backend Dependencies Summary

| Package | Version | Purpose | Phase |
|---------|---------|---------|-------|
| APScheduler | 3.10.x | Scheduled jobs (recommendations, snapshots, evaluation) | Phase 1 |
| slowapi | 0.1.x | Client-facing API rate limiting | Phase 0 |
| structlog | 24.x | Structured logging | Phase 0 |
| cachetools | 5.3.x | In-memory TTL cache | Phase 1 |
| sentry-sdk | 1.40.x | Error tracking (production) | Phase 3 |
| pytest | 8.x | Unit and integration testing | Phase 0 |
| pytest-asyncio | 0.23.x | Async test support | Phase 0 |
| pytest-cov | 4.x | Code coverage reporting | Phase 0 |
| respx | 0.20.x | HTTP request mocking for tests | Phase 0 |
| psutil | 5.9.x | Process memory monitoring for /health | Phase 0 |

## Appendix C: Configuration Reference

| Config Key | Default | Environment Variable | Description |
|-----------|---------|---------------------|-------------|
| `app_name` | "Stock Advisor API" | `APP_NAME` | Application name |
| `debug` | `false` | `DEBUG` | Debug mode |
| `supabase_url` | -- | `SUPABASE_URL` | Supabase project URL |
| `supabase_key` | -- | `SUPABASE_KEY` | Supabase service role key |
| `glm_api_key` | -- | `GLM_API_KEY` | Zhipu AI API key |
| `token_daily_budget` | `500000` | `TOKEN_DAILY_BUDGET` | Daily token budget |
| `token_warning_threshold` | `0.8` | `TOKEN_WARNING_THRESHOLD` | Warning at 80% |
| `sentry_dsn` | -- | `SENTRY_DSN` | Sentry error tracking DSN |
| `cors_origins` | `[localhost:3000, *.netlify.app]` | `CORS_ORIGINS` | Allowed CORS origins |
| `rate_limit_eastmoney_quote` | `5` | `RATE_LIMIT_EASTMONEY_QUOTE` | EastMoney quote rate/sec |
| `rate_limit_eastmoney_news` | `3` | `RATE_LIMIT_EASTMONEY_NEWS` | EastMoney news rate/sec |
| `rate_limit_akshare` | `3` | `RATE_LIMIT_AKSHARE` | AKShare rate/sec |
| `rate_limit_glm4` | `1` | `RATE_LIMIT_GLM4` | GLM-4 rate/sec |
| `rate_limit_yahoo` | `2` | `RATE_LIMIT_YAHOO` | Yahoo Finance rate/sec |
| `history_retention_days` | `90` | `HISTORY_RETENTION_DAYS` | Analysis history retention |

---

*End of ARCHITECTURE.md v1.1 (QA Major Issue Fixes Applied)*

*This document is the authoritative technical architecture specification for Stock Advisor v2.0. It is designed to be directly actionable for implementation.*

*Maintained by: System Architect*
*Review cycle: Before each development phase begins*
