# ARCHITECTURE.md v1.0 -> v1.1 Fix Report

| Field | Value |
|-------|-------|
| Document | ARCHITECTURE.md |
| Version | v1.0 -> v1.1 |
| QA Review Score | 88/100 (Conditional Approval) |
| Issues Fixed | 3 Major (MAJOR-001, MAJOR-002, MAJOR-003) |
| Author | System Architect |
| Date | 2026-02-09 |

---

## Fix Summary

| Issue ID | Issue | Fix Applied | Sections Modified |
|----------|-------|-------------|-------------------|
| MAJOR-001 | No TradingCalendarService implementation detail | Added full service design with AKShare + static fallback | 2.1, 2.2.11 (new), 2.4.2, 2.5 |
| MAJOR-002 | Render free tier 512MB memory constraint not addressed | Added comprehensive memory budget analysis | 6.5 (new), 6.6 (renumbered), Appendix B, Section 8.5 |
| MAJOR-003 | SSE connection handling incomplete | Added disconnect detection, concurrency protection, reconnection, interruption handling | 3.3.1 (new), 9.1 (TR-7 updated) |

---

## MAJOR-001: TradingCalendarService Implementation Detail

### Problem

All scheduled jobs depend on trading day detection, but the architecture had no concrete implementation. Missing details included:
- Which AKShare function to use
- How to handle Chinese market holidays
- What happens when AKShare is unavailable
- Timezone handling (CST)
- Cache strategy for the calendar

### Fix Applied

**New Section 2.2.11**: `trading_calendar_service.py` -- Trading Day Detection

Added a complete service design including:

1. **Primary source**: `akshare.tool_trade_date_hist_sina()` wrapped in `asyncio.to_thread()`
2. **Static fallback**: `data/trading_calendar_static.json` with 2024-2026 trading dates committed to the repo
3. **Caching**: Full-year calendar stored as `set[date]` in memory for O(1) lookup
4. **Query interfaces**:
   - `is_trading_day(date) -> bool` -- used by all scheduled jobs
   - `next_trading_day(date) -> date` -- used by prediction evaluation
   - `add_trading_days(date, count) -> date` -- used for 5-trading-day calculation
5. **Daily refresh**: Scheduled job at 08:00 CST refreshes calendar from AKShare
6. **Stale detection**: Warning logged if calendar > 48 hours old; exposed in `/health`
7. **Timezone**: All dates in `Asia/Shanghai` using `zoneinfo.ZoneInfo`

**Updated Section 2.5**: Scheduled Jobs Design

- Added explicit pattern showing how each job calls `trading_calendar_service.is_trading_day()`
- Added calendar refresh job (Job 5) at 08:00 CST
- Added initialization sequence in `main.py` lifespan (calendar loads before scheduler starts)
- Updated misfire handling to note that calendar is re-loaded on restart

**Updated Section 2.4.2**: AKShare Client

- Updated `get_trading_calendar()` docstring to reference Section 2.2.11

**Updated Section 2.1**: Module Decomposition

- Added `trading_calendar_service.py` to the services directory listing

### Sections Modified

- Section 2.1 (Module Decomposition): Added file listing
- Section 2.2.11 (new): Full TradingCalendarService design (~120 lines)
- Section 2.4.2 (AKShare Client): Updated docstring
- Section 2.5 (Scheduled Jobs): Added usage pattern, calendar refresh job, initialization

---

## MAJOR-002: Render Free Tier Memory Budget Analysis

### Problem

Render free tier provides only 512MB RAM. The system runs FastAPI + APScheduler + caches + AKShare (pandas/numpy) but had no memory budget analysis. Peak operations (recommendation generation with 60 stocks) could spike memory significantly.

### Fix Applied

**New Section 6.5**: Memory Budget Analysis (Render 512MB Constraint)

Added comprehensive analysis with 6 subsections:

1. **6.5.1 Component Memory Estimates**: Itemized baseline memory for each component (total: ~151 MB)
2. **6.5.2 Per-Request Memory Overhead**: Memory cost per comprehensive analysis (~40 MB, released after response)
3. **6.5.3 Peak Scenario Analysis**: Three scenarios analyzed:
   - Scenario A: Recommendation generation (peak ~221 MB)
   - Scenario B: Global Refresh (peak ~191 MB)
   - Scenario C: Concurrent operations (peak ~301 MB, 59% of 512 MB)
4. **6.5.4 Memory Budget Summary**: Visual budget diagram showing utilization
5. **6.5.5 Mitigation Measures**:
   - L1 cache maxsize capped at 200/200/100 entries
   - Batch processing (10 stocks/batch) in recommendation generation
   - Explicit `del df` + `gc.collect()` after AKShare operations
   - `psutil.Process().memory_info().rss` monitoring in `/health` endpoint
   - 410 MB (80%) threshold for WARNING logs
6. **6.5.6 Upgrade Path**: Cost breakdown for Render Starter ($7/month) and Standard ($25/month) plans

**Renumbered Section 6.6**: Cold Start Mitigation (was 6.5)

**Updated Appendix B**: Added `psutil 5.9.x` dependency

**Updated Section 8.5**: Added `psutil==5.9.8` to requirements.txt listing

### Sections Modified

- Section 6.5 (new): Memory Budget Analysis (~100 lines)
- Section 6.6 (renumbered from 6.5): Cold Start Mitigation
- Appendix B: Added psutil dependency
- Section 8.5: Added psutil to requirements.txt

---

## MAJOR-003: SSE Connection Handling

### Problem

The SSE implementation for Global Refresh had several gaps:
- No backend disconnect detection
- No concurrent refresh protection detail
- No network reconnection logic
- No timeout handling
- No state management for in-progress refreshes

### Fix Applied

**New Section 3.3.1**: SSE Connection Lifecycle Management

Added comprehensive connection handling covering all four scenarios:

1. **Backend Disconnect Detection**:
   - `request.is_disconnected()` checked before each stock processing
   - Heartbeat SSE comments (`: heartbeat`) every 3 stocks to keep connection alive
   - On disconnect: stop processing, save tokens, mark refresh complete

2. **Concurrent Refresh Protection**:
   - Backend: In-memory `_active_refreshes: dict[str, RefreshState]` tracks per-device state
   - `_is_refresh_active(device_id)` checks with auto-expiry (10 min TTL)
   - Duplicate refresh request returns current progress stream instead of starting new one
   - Frontend: `RefreshAllButton` disables during active refresh (`disabled` prop)

3. **Frontend Network Reconnection**:
   - Reconnection logic with 3 attempts and exponential backoff (2s, 4s, 6s)
   - `lastProgress` tracking for state recovery on reconnect
   - `reconnecting` event type sent to UI for user feedback
   - New backend endpoint `GET /refresh/status` for reconnection state check

4. **Interruption Handling (User Closes Page)**:
   - Backend detects disconnect and stops processing (saves tokens)
   - Already-processed stocks retain fresh analysis (idempotent)
   - Refresh state marked "completed" (partial)
   - On return: new refresh benefits from cached results (30-min TTL)

5. **Maximum SSE Duration**:
   - 5-minute server-side timeout enforced
   - `timeout` event sent to client with progress count
   - Implicit limit: ~40 stocks x 5s = ~200s (3.3 min)

**Updated Section 9.1**: Risk Register

- TR-7 updated to reference `_active_refreshes` dict and Section 3.3.1

### Sections Modified

- Section 3.3.1 (new): SSE Connection Lifecycle Management (~200 lines)
- Section 9.1: TR-7 mitigation text updated

---

## Changes Summary

| Metric | Value |
|--------|-------|
| Lines added (estimated) | ~420 |
| New sections | 3 (2.2.11, 3.3.1, 6.5) |
| Modified sections | 7 (2.1, 2.4.2, 2.5, 6.6, 8.5, 9.1, Appendix B) |
| New dependencies | 1 (psutil) |
| New API endpoints | 1 (GET /refresh/status) |
| New static files | 1 (data/trading_calendar_static.json) |
| Document version | v1.0 -> v1.1 |

---

## Verification Checklist

- [x] MAJOR-001: TradingCalendarService has primary source (AKShare) + static fallback
- [x] MAJOR-001: Cache strategy defined (full-year in-memory set)
- [x] MAJOR-001: Query interfaces defined (is_trading_day, next_trading_day, add_trading_days)
- [x] MAJOR-001: All scheduled jobs reference TradingCalendarService
- [x] MAJOR-001: Timezone handling specified (Asia/Shanghai)
- [x] MAJOR-002: Component memory estimates provided
- [x] MAJOR-002: Peak scenario analysis for 3 scenarios
- [x] MAJOR-002: Mitigation measures (cache limits, batching, gc, monitoring)
- [x] MAJOR-002: Memory monitoring via /health endpoint
- [x] MAJOR-002: Upgrade path defined (Render Starter/Standard)
- [x] MAJOR-003: Backend disconnect detection via request.is_disconnected()
- [x] MAJOR-003: Heartbeat mechanism (SSE comments every 3 stocks)
- [x] MAJOR-003: Concurrent protection (in-memory dict with TTL)
- [x] MAJOR-003: Frontend button disabling during refresh
- [x] MAJOR-003: Network reconnection with 3 attempts + backoff
- [x] MAJOR-003: Interruption handling (partial completion is safe)
- [x] MAJOR-003: Maximum SSE duration (5 minutes)
- [x] MAJOR-003: Refresh status API endpoint for reconnection

---

*Fix report completed by: System Architect*
*Ready for QA re-review*
