# PRD v2.0 Fixes Report

| Field | Value |
|-------|-------|
| Document | PRD_v2.0.md |
| Fix Date | 2026-02-09 |
| Fixed By | Product Orchestrator (PM) |
| QA Review Reference | QA_PRD_REVIEW.md |
| Issues Fixed | 4 Major (MAJOR-001 through MAJOR-004) |

---

## Fix Summary

All 4 Major issues identified by QA Guardian have been resolved. The PRD v2.0 has been updated in-place with new content integrated into the existing document structure.

---

## MAJOR-001: Missing Testing Strategy Section

**Problem**: PRD had no testing strategy. QA validation was allocated only 1 day in Phase 3, which is grossly insufficient for a financial information system.

**Fix Applied**:

Added **Section 13: Testing Strategy** with 9 subsections:

| Subsection | Content |
|------------|---------|
| 13.1 Test Types and Coverage Targets | 6 test types (unit, integration, AI quality, E2E, performance, compliance) with specific tools and frequency |
| 13.2 Unit Test Requirements | Per-service coverage targets (75%-90%), critical test cases for all indicator calculations |
| 13.3 Integration Test Requirements | Test scenarios for all 16+ API endpoints, mock data strategy using pytest fixtures + respx |
| 13.4 AI Output Validation | Structural validation rules (automated), content quality scoring rubric (weekly manual), template fallback validation |
| 13.5 E2E Test Scenarios | 5 Playwright test scripts: stock search, watchlist management, global refresh, historical review, device identity recovery |
| 13.6 Test Data Strategy | 7 standard test stocks covering all exchange types, mock data directory structure |
| 13.7 Performance Test Plan | 6 performance benchmarks with targets matching Section 12.3 |
| 13.8 Compliance Test Automation | 4 automated compliance checks running on every PR |
| 13.9 Testing Schedule | Phase-by-phase testing allocation, QA Guardian engagement points at 4 checkpoints |

**Key Changes**:
- Phase 3 QA validation expanded from 1 day to 3 days in the testing schedule
- QA Guardian now has 4 engagement checkpoints (Phase 0/1/2/3 exits) instead of just 1
- Testing is integrated throughout development (1 day testing per 2 days development) rather than being a final gate

**PRD Sections Modified**:
- Table of Contents: Added entry for Section 13
- New Section 13 (before Appendix A)

---

## MAJOR-002: Device Fingerprint Authentication is Unreliable

**Problem**: PRD conflated localStorage UUID with browser fingerprint. No recovery mechanism existed for watchlist data loss. This directly undermined the prediction tracking value proposition.

**Fix Applied**:

Added **Section 4.4.1: Device Identity Mechanism** with complete specification:

| Component | Detail |
|-----------|--------|
| Identity Clarification | Explicitly defined as a **UUID v4 stored in localStorage**, NOT a computed browser fingerprint. Documented what this means for data persistence. |
| Backup Code System [P0] | On first visit, display recovery code dialog. Settings page shows current device ID with copy button. |
| Recovery Flow | Settings page includes "Restore from Backup Code" input. System validates the UUID exists in database before restoring. |
| Data Export [P0] | JSON export of all watchlist stocks + metadata. Import function to restore from exported file. |
| Data Loss User Flow | Documented the complete flow: data loss detected -> new UUID generated -> user navigates to Settings -> Option A (backup code) / Option B (import JSON) / Option C (rebuild manually) |
| API Endpoints | Added 3 new endpoints: POST /device/validate, GET /device/export, POST /device/import |
| Future Enhancement | Email-based account linking noted as v2.1 item |

**Acceptance Criteria Updated**:
- Added: Backup code displayed on first visit and accessible from Settings
- Added: Recovery flow with valid backup code restores watchlist
- Added: Watchlist export to JSON includes all stocks and metadata
- Added: Watchlist import from JSON merges stocks into current device
- Changed: "device fingerprint" wording to "UUID stored in localStorage"

**PRD Sections Modified**:
- Section 4.4: New subsection 4.4.1 (Device Identity Mechanism)
- Section 4.4: Updated acceptance criteria (6 new criteria)
- Section 8.1: Added 3 new API endpoints to the endpoint table

---

## MAJOR-003: Curated Hot Stock List (60 Stocks) is Undefined

**Problem**: The recommendation pipeline references a "curated hot stock list" of ~60 stocks but never defines what it is, where it comes from, how it is maintained, or where it is stored.

**Fix Applied**:

Added **Section 4.3.1: Hot Stock Universe Definition** with complete specification:

| Component | Detail |
|-----------|--------|
| Universe Composition | 50-80 stocks from EastMoney sector hot lists + AKShare industry leaders + top traded stocks |
| Inclusion Criteria | 5 criteria: market cap > 5B, avg turnover > 100M (20d), listing age > 1 year, not ST/suspended, at least 5 industries |
| Exclusion Rules | ST/*ST, suspended, < 1 year listed, < 100M turnover, B-shares |
| Database Table | New `hot_stock_universe` table with complete DDL (code, name, industry, market_cap, avg_turnover, listing_date, validation tracking) |
| Update Mechanism | Weekly refresh (Monday 09:00), automated process with manual override capability, change logging |
| Fallback | If refresh fails, use last known good list with staleness alert if > 2 weeks old |
| Initial Seeding | Top 10 stocks by market cap from 6 key sectors = ~60 stocks, manually reviewed |

**PRD Sections Modified**:
- Section 4.3: New subsection 4.3.1 (before the pipeline description)
- Section 4.3: Pipeline Stage 1 updated to reference `hot_stock_universe table` instead of vague "curated hot stock list"

---

## MAJOR-004: No API Rate Limiting Design for External Data Sources

**Problem**: Global Refresh of 20 stocks requires 200+ external API calls but there was no rate limiting design, no request queuing, no backoff strategy, and no circuit breaker pattern.

**Fix Applied**:

Added **Section 5.7: Rate Limiting and Backpressure Strategy** with 6 subsections:

| Subsection | Content |
|------------|---------|
| 5.7.1 External API Call Budget | Per-source safe rates: EastMoney 5/s, EastMoney News 3/s, AKShare 3/s, GLM-4 ~60 RPM, Yahoo 2/s |
| 5.7.2 Request Queue Architecture | Centralized queue per data source with priority levels (HIGH/MEDIUM/LOW). Conceptual Python implementation using asyncio.Semaphore. |
| 5.7.3 Backoff and Retry Strategy | Per-response-code handling: 429 -> exponential backoff (2/4/8s + jitter, max 3 retries), 403 -> switch to fallback, 5xx -> retry once, timeout -> retry once |
| 5.7.4 Circuit Breaker Pattern | Three states (CLOSED/OPEN/HALF-OPEN) per data source. Configurable thresholds: 5 errors/60s triggers OPEN, 5 min cooldown, 1 test request in HALF-OPEN |
| 5.7.5 Global Refresh Rate Optimization | Detailed call volume estimation (138 total calls for 20 stocks), processing strategy (sequential stocks, parallel dimensions within stock), concurrency control (default 1, max 3), rate limit adaptation |
| 5.7.6 Daily Recommendation Generation Rate Budget | Call volume estimation for 17:30 job (~210 calls, ~80 seconds), confirming it is within safe rate limits |

**Key Design Decisions**:
- Global Refresh processes stocks sequentially by default (safest for rate limits)
- Within each stock, data dimensions are fetched in parallel where possible
- Industry data is cached per industry (not per stock), reducing duplicate calls from ~20 to ~6
- Estimated total time for 20-stock Global Refresh: 60-100 seconds (within 2-minute target)
- Circuit breakers prevent cascading failures when a data source goes down
- Rate limit adaptation: if 429 received, automatically reduce concurrency and increase delays

**PRD Sections Modified**:
- Section 5: New subsection 5.7 (between Error Handling and Data Strategy)

---

## Cross-Cutting Changes

### API Endpoint Count
- Original: 16 endpoints
- Added: 3 new device recovery endpoints (`/device/validate`, `/device/export`, `/device/import`)
- New total: 19 endpoints

### Database Tables
- Original: 6 new tables + 2 views
- Added: 1 new table (`hot_stock_universe`)
- New total: 7 new tables + 2 views

---

## Verification Checklist

| MAJOR Issue | Status | New Content Location |
|-------------|--------|---------------------|
| MAJOR-001: Testing Strategy | FIXED | Section 13 (13.1 through 13.9) |
| MAJOR-002: Device Identity | FIXED | Section 4.4.1, Section 8.1 (API table) |
| MAJOR-003: Hot Stock Universe | FIXED | Section 4.3.1 |
| MAJOR-004: Rate Limiting | FIXED | Section 5.7 (5.7.1 through 5.7.6) |

---

## Next Steps

1. **QA Guardian re-review**: Submit updated PRD v2.0 for re-review by QA Guardian
2. **Target score**: > 85/100 (up from 81/100)
3. **Expected improvements**:
   - Completeness: +2 points (testing strategy + hot stock definition)
   - Implementability: +3 points (rate limiting design + device identity clarification)
   - Testability gate: PASS (was FAIL)
4. **After QA approval**: Proceed to architecture design phase

---

*Report generated by: Product Orchestrator*
*Date: 2026-02-09*
