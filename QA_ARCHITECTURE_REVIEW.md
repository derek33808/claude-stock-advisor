# QA Architecture Review - Stock Advisor v2.0

## Review Information

| Field | Value |
|-------|-------|
| **Document Reviewed** | ARCHITECTURE.md v1.0 (~2700 lines) |
| **Reviewer** | qa-guardian |
| **Review Date** | 2026-02-09 |
| **Reference PRD** | PRD_v2.0.md (91/100, QA Approved) |
| **Review Status** | APPROVED (Conditional) |
| **Overall Score** | **88 / 100** |

---

## 1. Review Summary

### 1.1 Overall Assessment

The ARCHITECTURE.md is a thorough, well-structured, and highly actionable technical document. At approximately 2700 lines, it covers the full system from high-level deployment topology to individual service method signatures, database schemas, caching strategies, and CI/CD pipelines. The document demonstrates strong systems thinking and mature engineering judgment, particularly in its rate limiting, circuit breaker, and fallback designs.

**Issue Counts:**

| Severity | Count | Status |
|----------|-------|--------|
| Critical | 0 | -- |
| Major | 3 | Must fix before development |
| Minor | 6 | Recommended fix |
| Nit | 5 | Optional improvement |
| FYI | 3 | Informational |

### 1.2 Score Breakdown

| Dimension | Score (1-10) | Weight | Weighted Score | Notes |
|-----------|-------------|--------|---------------|-------|
| PRD Consistency | 9 | 15% | 13.5 | Excellent feature mapping in Section 10 |
| Architecture Completeness | 9 | 15% | 13.5 | All layers covered; minor gaps noted |
| Technical Feasibility | 9 | 15% | 13.5 | Proven stack, pragmatic choices |
| Performance & Scalability | 8 | 10% | 8.0 | Good caching; Render free tier is a constraint |
| Security | 8 | 10% | 8.0 | Solid API key management; minor gaps |
| Reliability & Fault Tolerance | 9 | 10% | 9.0 | Excellent circuit breaker + fallback design |
| Testability | 8 | 10% | 8.0 | Good test structure; needs mock strategy detail |
| Maintainability | 9 | 10% | 9.0 | Clean module separation, DAO pattern |
| Deployment & DevOps | 8 | 5% | 4.0 | CI/CD defined; no staging environment |
| **Total** | | **100%** | **87.5 -> 88** | |

---

## 2. PRD Consistency Analysis

### 2.1 Feature Coverage Verification

| PRD Feature | PRD Section | Architecture Coverage | Verdict |
|-------------|-------------|----------------------|---------|
| AI Comprehensive Analysis (5 dims) | 4.2 | Section 2.2.1 + Section 10.1 | FULL |
| Daily Smart Recommendations | 4.3 | Section 2.2.10 + 2.5 + 10.2 | FULL |
| Hot Stock Universe | 4.3.1 | Section 2.2.10 + DB 4.1 | FULL |
| Watchlist Management | 4.4 | Section 2.2.5 + 10.3 | FULL |
| Device Identity (UUID) | 4.4.1 | Section 5.2 + Frontend 3.2 | FULL |
| Backup Code + Recovery | 4.4.1 | Section 5.2 + Frontend 3.1 | FULL |
| Export/Import JSON | 4.4.1 | Section 5.5 + 2.2.5 | FULL |
| Global Refresh (SSE) | 4.5 | Section 2.5 + 3.3 + 10.4 | FULL |
| Token Monitoring | 4.5 | Section 2.2.8 + 10.6 | FULL |
| Historical Review | 4.6 | Section 2.2.7 + 10.5 | FULL |
| Prediction Tracking (5-day) | 4.6 | Section 2.2.6 + 10.5 | FULL |
| Accuracy Statistics | 4.6 | Section 2.2.6 + DB views | FULL |
| Rate Limiting | 5.7 | Section 2.2.9 + 2.4.4 | FULL |
| Circuit Breaker | 5.7.4 | Section 2.4.5 | FULL |
| Compliance Framework | 10 | Section 8.2 (CI check) | FULL |
| News Integration | 4.2 Dim 4 | Section 2.2.2 | FULL |
| Fundamental Analysis | 4.2 Dim 3 | Section 2.2.3 | FULL |
| Industry Analysis | 4.2 Dim 5 | Section 2.2.4 | FULL |

**Verdict: 18/18 PRD features have corresponding architecture coverage. No feature gaps detected.**

### 2.2 Performance Target Alignment

| PRD Performance Target | Architecture Solution | Status |
|------------------------|----------------------|--------|
| Comprehensive analysis < 5s (uncached) | Parallel fetching (Section 6.2), time budget diagram | ALIGNED |
| Comprehensive analysis < 2s (cached) | L1 in-memory cache 30 min TTL | ALIGNED |
| Global refresh < 2 min for 20 stocks | Sequential processing ~3-5s/stock (Section 2.5) | ALIGNED |
| Home page load < 2s | Next.js SSG + CDN (Section 6.3) | ALIGNED* |
| Recommendation generation < 15 min | ~80s estimated (Section 5.7.6 in PRD) | ALIGNED |

*Note: PRD says "< 3s" for home page, Architecture Section 6.3 says "First paint < 1s". The home page also requires API data which adds to the perceived load time. Alignment is acceptable given CDN + skeleton loading.

### 2.3 Technology Stack Consistency

| PRD Specification | Architecture Specification | Match |
|-------------------|---------------------------|-------|
| Next.js 15 + React 18 | Next.js 16.x (existing) | MINOR DISCREPANCY |
| FastAPI 0.109 + Python 3.11 | FastAPI 0.109 + Python 3.11 | MATCH |
| Supabase PostgreSQL | Supabase PostgreSQL | MATCH |
| GLM-4 (Zhipu AI) | GLM-4 (Zhipu AI) | MATCH |
| Netlify + Render | Netlify + Render | MATCH |
| EastMoney + AKShare + Yahoo | EastMoney + AKShare + Yahoo | MATCH |

**Minor Discrepancy (Nit):** PRD Section 5.2 says "Next.js 15", Architecture Section 1.2 says "Next.js 16.x (existing)". This is likely because the existing codebase already uses Next.js 16. Not a real issue, but the PRD should be updated for consistency.

---

## 3. Problem Catalog

### 3.1 Major Issues (Must Fix Before Development)

#### MAJOR-001: No Trading Day Detection Implementation Detail

**Location:** Section 2.5 (Scheduled Jobs Design)

**Description:** The architecture states "Before executing Jobs 1-3, the job checks if today is a trading day using the trading calendar from AKShare" but provides no concrete implementation. The `akshare_service.py` mentions `get_trading_calendar()` that returns a list of dates, but there is no detail on:
- How the trading calendar is obtained (which AKShare function)
- How Chinese market holidays are handled
- What happens when AKShare is unavailable during calendar lookup
- How the calendar is cached (24h mentioned but no implementation pattern)
- Edge cases: the scheduler runs on UTC or CST time, but what timezone does AKShare return dates in?

**Impact:** If trading day detection fails silently, scheduled jobs would either run on non-trading days (wasting tokens, generating stale analysis) or fail to run on valid trading days (missing daily recommendations).

**Suggested Fix:** Add a dedicated `TradingCalendarService` with:
1. Specify the AKShare function: `akshare.tool_trade_date_hist_sina()` or similar
2. Cache the full-year calendar on startup with 24h refresh
3. Fallback: if AKShare unavailable, use a static calendar with Chinese holidays for current year
4. Method: `is_trading_day(date) -> bool` with timezone-aware logic (CST)
5. Log a warning if calendar is stale (> 48h since last refresh)

---

#### MAJOR-002: Render Free Tier Memory Constraint Not Addressed

**Location:** Section 1.3 (Deployment Architecture), Section 6.5 (Cold Start)

**Description:** The architecture specifies "512MB RAM" for the Render backend. However, the system now runs:
- FastAPI application
- APScheduler (in-process)
- In-memory TTL cache (up to 300 entries across 3 stores)
- Multiple httpx.AsyncClient connection pools
- AKShare library (which loads pandas, numpy internally)
- structlog
- Rate limiter state + circuit breaker state
- During Global Refresh: processing data for 20 stocks with concurrent data fetching

There is no memory budget analysis. With AKShare's pandas DataFrame operations for 60 stocks in the recommendation job, memory could spike significantly. If the process exceeds 512MB, Render will kill it, losing all in-memory cache and scheduler state.

**Impact:** Production outages during peak operations (daily recommendation generation, global refresh). The most memory-intensive operations (recommendation generation at 17:30 with 60 stock universe processing) are exactly when reliability matters most.

**Suggested Fix:**
1. Add a "Memory Budget Estimation" subsection with estimated memory consumption per component
2. Consider limiting TTLCache maxsize if memory is tight (currently 200+200+100 = 500 entries)
3. Add explicit memory monitoring via the `/health` endpoint (e.g., `psutil.Process().memory_info().rss`)
4. Define a memory threshold alert (e.g., 80% of 512MB = 410MB triggers warning)
5. Document the contingency plan: when to upgrade to paid tier (at what DAU/load)

---

#### MAJOR-003: SSE Connection Handling Incomplete

**Location:** Section 3.3 (SSE Client), Section 2.5 (Scheduled Jobs, Refresh endpoint)

**Description:** The SSE implementation for Global Refresh has several gaps:

1. **Backend cancellation**: The architecture shows AbortController on the frontend, but the backend has no mechanism to detect client disconnection. If the user closes the tab mid-refresh, the backend continues processing all remaining stocks, wasting tokens and API calls.

2. **Concurrent refresh protection**: Section 9.1 Risk TR-7 mentions "SSE endpoint tracks active refresh per device; rejects concurrent requests" but no implementation detail is provided. How is the active refresh tracked? In-memory dict? What happens if the process restarts mid-refresh?

3. **SSE reconnection**: The custom fetch-based SSE client (Section 3.3) does not handle network disconnection/reconnection. Unlike native EventSource, the fetch ReadableStream does not auto-reconnect. If the network drops mid-refresh, the user loses progress visibility.

4. **Timeout**: No timeout defined for the SSE connection. A slow refresh (e.g., GLM-4 is slow, taking 30s per stock) could keep the connection open for 10+ minutes.

**Impact:** Token waste on cancelled refreshes, poor user experience on network drops, potential for duplicate concurrent refreshes.

**Suggested Fix:**
1. Backend: Check `request.is_disconnected()` in FastAPI before processing each stock
2. Track active refreshes in a dict `{device_id: refresh_task}` with TTL; check on entry
3. Frontend: Add periodic heartbeat check and reconnection logic with state recovery
4. Set maximum SSE connection duration (e.g., 5 minutes) with graceful termination

---

### 3.2 Minor Issues (Recommended Fix)

#### MINOR-001: Next.js Version Discrepancy Between PRD and Architecture

**Location:** Section 1.2 (Technology Stack)

**Description:** PRD says "Next.js 15", Architecture says "Next.js 16.x (existing)". Also, the high-level diagram (Section 1.1) says "Next.js 15 (Static Export / SSG)" while the tech stack table says "Next.js 16.x". Internal inconsistency.

**Suggested Fix:** Verify the actual version in the existing codebase and make both documents consistent.

---

#### MINOR-002: No Error Response Schema Standardization

**Location:** Throughout API endpoints (Sections 3.3, 5.2, implied in routes)

**Description:** The architecture defines error responses for the comprehensive analysis endpoint (400, 404, 503) but does not define a standardized error response schema across all endpoints. Different endpoints may return different error structures.

**Suggested Fix:** Define a global `ErrorResponse` Pydantic model:
```python
class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    code: str | None = None  # machine-readable error code
```
Apply it to all endpoints with FastAPI exception handlers.

---

#### MINOR-003: Watchlist Snapshot Deduplication Has User Experience Trade-off

**Location:** Section 4.4 (Data Retention), ADR-004

**Description:** ADR-004 decides to save one snapshot per unique stock, not per user. This means if User A has stock 600519 in their watchlist and User B also has it, they see the same snapshot. This is documented as an acceptable trade-off, but it creates a subtle UX issue: if User A manually refreshes stock 600519 at 14:00, and the system takes the daily snapshot at 17:30, User A will see two entries in their timeline (14:00 manual + 17:30 scheduled), but only the 17:30 snapshot is shared.

**Impact:** Potential confusion in timeline view. The architecture does not clarify whether manual refreshes create separate `analysis_history` entries or update the daily entry.

**Suggested Fix:** Clarify in Section 2.2.7 `save_snapshot()` whether manual refreshes update the existing daily entry or create a separate entry. Document the expected timeline behavior explicitly.

---

#### MINOR-004: No Graceful Degradation UI Components

**Location:** Section 3.1 (Frontend Component Structure)

**Description:** The frontend component structure lists `ErrorBoundary.tsx` but does not define partial rendering behavior. When one dimension fails (e.g., industry data unavailable), the architecture says "show available data, flag unavailable" (in alignment with PRD). However, there is no component for displaying partial/degraded state per dimension (e.g., a `DimensionUnavailable.tsx` placeholder).

**Suggested Fix:** Add a `DimensionUnavailable.tsx` component to the component list, used inside each accordion section when its data source fails. Include a standard message pattern and retry button.

---

#### MINOR-005: Database Migration Lacks Versioning Strategy

**Location:** Section 4.1 (Database Architecture), referenced migration plan from PRD 7.3

**Description:** The migration plan lists steps (create tables, views, indexes) but does not specify a migration versioning tool. Supabase supports SQL migrations, and the existing v1.0 tables are already in place. Without a migration tool, there is risk of:
- Running migrations out of order
- Not being able to roll back cleanly
- Losing track of what has been applied

**Suggested Fix:** Either use Supabase CLI migrations (`supabase migration new`) or maintain a numbered SQL migration directory (`db/migrations/001_create_watchlist.sql`, etc.). Document the chosen approach.

---

#### MINOR-006: Frontend Test Strategy Underspecified

**Location:** Section 10.8 (Testing Strategy Mapping)

**Description:** The architecture maps testing to backend pytest extensively but frontend testing is limited to "Playwright test suite" for E2E. There is no mention of:
- React component unit tests (Jest + Testing Library)
- API client mock tests
- State management tests (Context providers)

The frontend has 30+ components (many new), and relying solely on E2E tests for frontend validation creates a testing gap.

**Suggested Fix:** Add a frontend unit testing section specifying:
1. Jest + React Testing Library for component tests
2. Priority components to test: `StockDetailClient`, `RefreshProgress`, `WatchlistManager`, `TokenBadge`
3. Coverage target: > 60% for `lib/` utilities, > 50% for critical components

---

### 3.3 Nit Issues (Optional Improvement)

#### NIT-001: Diagram Text Inconsistency in Section 1.1

The high-level architecture diagram shows "Next.js 15 (Static Export / SSG)" but SSG is not the same as Static Export. Next.js Static Export produces a fully static site (no server), while SSG pre-renders at build time but can still have server-side features. The existing deployment uses Netlify (static hosting), so "Static Export" is more accurate. Clarify which mode is used.

#### NIT-002: Cache TTLs Documented in Multiple Places

Cache TTL values are documented in Section 2.3.3 (Cache Decision Matrix), Section 6.1 (Cache Hierarchy), and inline in service descriptions. If TTLs change, they need to be updated in 3 places. Consider defining TTLs as constants in `config.py` and referencing the config in the architecture document.

#### NIT-003: `rate_limiter_service.py` vs `infrastructure/rate_limiter.py`

The architecture defines both `rate_limiter_service.py` (Section 2.2.9) and `infrastructure/rate_limiter.py` (Section 2.1 module listing). The relationship is clear (service wraps infrastructure), but the naming could cause confusion. Consider renaming `infrastructure/rate_limiter.py` to `infrastructure/token_bucket.py` to differentiate from the service-level `rate_limiter_service.py`.

#### NIT-004: CORS Configuration Hardcodes Multiple Netlify Domains

Section 5.3 lists 4 specific Netlify app URLs. If the deployment domain changes, this requires a code change. Consider using a wildcard pattern or loading CORS origins from environment variables (the `CORS_ORIGINS` env var is mentioned in Section 8.3 but the code sample in 5.3 uses hardcoded values).

#### NIT-005: Appendix A Pydantic Models Missing Some Types

`BasicInfo`, `TechnicalAnalysis`, `FundamentalAnalysis`, `RecentDevelopments`, `IndustryAnalysis`, `TradingSuggestion`, `PricePrediction`, `PriceRange`, `ActualResult`, `PredictionAccuracy` are referenced in the Appendix A schemas but their definitions are not provided. While these can be inferred, including them would make the document more self-contained.

---

### 3.4 FYI Notes (Informational)

#### FYI-001: Render Free Tier Will Cause Scheduler Reliability Issues

Render free tier spins down after 15 minutes of inactivity. The architecture acknowledges this (Section 6.5) and mitigates with scheduler activity during market hours. However, if no user visits the site for 15 minutes during market hours AND no scheduled job is due, the process will spin down. This means:
- The 17:30 recommendation job might miss its window if the process spun down at 17:15
- `misfire_grace_time=3600` helps but adds unpredictability

This is a known limitation and upgrading to the paid tier at 50 DAU is the correct mitigation. No action needed now, but it should be tracked as a risk.

#### FYI-002: AKShare Library Stability

AKShare is an open-source library that wraps multiple Chinese financial data sources. Its API can change between versions. The architecture pins the version (1.18.x) which is good. However, the underlying data sources that AKShare wraps (Sina, EastMoney, etc.) can change their HTML/API structure, breaking AKShare even without a version update.

Monitoring AKShare's GitHub issues before each release is recommended.

#### FYI-003: Supabase Free Tier Connection Limits

Supabase free tier limits concurrent connections. The architecture uses a singleton client (Section 2.3.1), which is correct. However, during peak operations (recommendation generation + user requests), the number of concurrent queries could approach limits. The `supabase-py` library manages this internally, but it should be monitored in production.

---

## 4. Highlights and Best Practices

The architecture document demonstrates several excellent engineering practices:

### 4.1 Outstanding Design Decisions

1. **Circuit Breaker Pattern Per Data Source (Section 2.4.5):** Each external data source has an independent circuit breaker with well-defined state transitions. This prevents a single failing data source from cascading to the entire system. The 3-state model (CLOSED/OPEN/HALF_OPEN) is industry-standard and correctly configured.

2. **Two-Level Cache Strategy (Section 2.3.3):** The cache decision matrix clearly distinguishes which data belongs in L1 (in-memory, short TTL, volatile) vs L2 (database, longer TTL, persistent). This balances performance with resilience to process restarts.

3. **ADR Documentation (Section 9.2):** Four Architecture Decision Records document the reasoning behind key choices (in-process scheduler, in-memory cache, SSE, deduplicated snapshots). This is excellent engineering practice that future developers will appreciate.

4. **Parallel Fetching Within Sequential Processing (Section 6.2):** The approach of processing stocks sequentially but fetching data dimensions in parallel within each stock is a pragmatic balance between throughput and rate limit safety.

5. **Token Budget Design (Section 2.2.8):** The in-memory counter with periodic DB sync is smart -- it avoids a DB query on every AI call while maintaining durability through periodic persistence.

6. **Compliance CI Check (Section 8.2):** Automated scanning for prohibited language ("投资建议", "保证收益") in CI is a proactive compliance measure that prevents accidental regulatory violations.

7. **PRD Feature Mapping Table (Section 10):** Systematically mapping every PRD requirement to its implementation path ensures nothing is lost in translation. This is a best practice we should apply to all future projects.

8. **DAO Pattern (Section 2.3.2):** Clean separation between services and database operations makes the code testable and maintainable. Each table has its own DAO with a clear interface.

### 4.2 Document Quality

- **Well-structured:** 10 major sections with clear hierarchy
- **Actionable:** Method signatures, data flow diagrams, and timing diagrams allow direct implementation
- **Complete code samples:** Python and TypeScript code snippets are syntactically correct and illustrative
- **Configuration reference (Appendix C):** All environment variables documented with defaults
- **Dependency list (Appendix B):** Pinned versions with phase mapping

---

## 5. Testability Assessment

### 5.1 Backend Testability

| Aspect | Assessment | Score (1-5) |
|--------|-----------|-------------|
| Module isolation | Services have clear boundaries and injectable dependencies | 5 |
| External dependency mockability | All external calls go through clients (eastmoney_client, akshare_client, glm4_client) that can be mocked | 5 |
| Database testability | DAO pattern allows mocking all DB operations | 4 |
| Cache testability | AppCache is a simple class that can be replaced with a test double | 4 |
| Scheduler testability | Jobs are regular async functions that can be called directly | 4 |
| Test infrastructure | pytest + respx + httpx for mocking HTTP, conftest.py with fixtures | 4 |
| **Average** | | **4.3** |

### 5.2 Frontend Testability

| Aspect | Assessment | Score (1-5) |
|--------|-----------|-------------|
| Component isolation | React components are well-decomposed | 4 |
| State management testability | React Context is testable with providers in tests | 3 |
| API mock ability | api.ts functions can be mocked with jest.mock | 4 |
| E2E coverage plan | 5 user flows defined in PRD Section 13 | 4 |
| Unit test plan | Not defined in architecture (see MINOR-006) | 2 |
| **Average** | | **3.4** |

### 5.3 Test Strategy Alignment with QA Requirements

| QA Requirement | Architecture Support | Status |
|---------------|---------------------|--------|
| Unit test coverage > 80% | Test directory structure defined, pytest-cov configured for 80% | SUPPORTED |
| Integration test for all endpoints | 16 endpoints listed, test scenarios described in PRD 13.3 | SUPPORTED |
| E2E test for 5 core flows | Playwright in dependencies, flows defined in PRD 13.5 | SUPPORTED |
| AI quality validation | Custom validation in glm_service mentioned | PARTIALLY SUPPORTED |
| Mock data strategy | `tests/fixtures/` directory defined | SUPPORTED |
| CI integration | GitHub Actions pipeline with coverage gate | SUPPORTED |
| Compliance testing | Automated language scan in CI | SUPPORTED |

---

## 6. Security Assessment

| Security Dimension | Assessment | Score (1-5) |
|-------------------|-----------|-------------|
| API key management | Keys in env vars only, CI scan for hardcoded keys | 5 |
| Device identity | UUID in localStorage, not a computed fingerprint | 4 |
| CORS configuration | Explicit origin list, custom header allowed | 4 |
| Input validation | Pydantic models for all request/response schemas | 4 |
| Rate limiting | slowapi for client-facing, custom for external APIs | 4 |
| Data export security | No encryption but no sensitive data; import validates structure | 3 |
| SQL injection | Supabase client uses parameterized queries | 4 |
| XSS prevention | React auto-escapes; no dangerouslySetInnerHTML usage indicated | 4 |
| **Average** | | **4.0** |

**Notable:** The architecture correctly identifies that the frontend never communicates directly with Supabase, GLM-4, or data sources -- all external access is proxied through the backend. This is a security best practice.

---

## 7. Risk Assessment

### 7.1 Architecture Risk Summary

The risk register (Section 9.1) identifies 10 risks, which is thorough. However, a few risks are missing:

| Missing Risk | Probability | Impact | Suggested Mitigation |
|-------------|-------------|--------|---------------------|
| AKShare `to_thread` blocks ThreadPoolExecutor | Medium | High | Set explicit max_workers; monitor thread count |
| Supabase free tier connection limit during peak | Low | High | Connection pooling awareness; monitor concurrent queries |
| Frontend bundle size growth with 30+ new components | Medium | Low | Monitor bundle size in CI; use dynamic imports |

### 7.2 Single Points of Failure

| Component | Single Point? | Mitigation Documented? |
|-----------|--------------|----------------------|
| Render backend instance | Yes (single instance) | Partially (cold start, no HA plan) |
| Supabase database | Yes (single project) | No (Supabase has built-in HA, not documented) |
| In-memory cache | Yes (process-bound) | Yes (short TTLs, L2 cache survives restarts) |
| APScheduler | Yes (in-process) | Yes (misfire_grace_time + manual triggers) |

---

## 8. Improvement Suggestions

### 8.1 Required Actions (Blocking Development Start)

| ID | Action | Owner | Priority |
|----|--------|-------|----------|
| ACT-01 | Add TradingCalendarService implementation detail (MAJOR-001) | Architect | P0 |
| ACT-02 | Add memory budget analysis for Render 512MB (MAJOR-002) | Architect | P0 |
| ACT-03 | Add SSE disconnect detection and concurrent refresh protection detail (MAJOR-003) | Architect | P0 |

### 8.2 Recommended Actions (Before Phase 1 Complete)

| ID | Action | Owner | Priority |
|----|--------|-------|----------|
| ACT-04 | Standardize error response schema across all endpoints (MINOR-002) | Architect | P1 |
| ACT-05 | Clarify manual refresh vs daily snapshot behavior in timeline (MINOR-003) | Architect | P1 |
| ACT-06 | Add frontend unit test strategy (MINOR-006) | Architect | P1 |
| ACT-07 | Define database migration versioning approach (MINOR-005) | Architect | P1 |
| ACT-08 | Add graceful degradation UI component (MINOR-004) | Architect | P2 |
| ACT-09 | Reconcile Next.js version between PRD and Architecture (MINOR-001) | PM/Architect | P2 |

---

## 9. Review Conclusion

### 9.1 Verdict: APPROVED (Conditional)

The ARCHITECTURE.md scores **88/100**, exceeding the 85-point threshold for approval. The document is comprehensive, well-organized, and demonstrates mature systems design thinking.

**Conditions for full approval (must be addressed before development begins):**

1. **MAJOR-001:** Add TradingCalendarService implementation detail with fallback strategy
2. **MAJOR-002:** Add memory budget analysis for the 512MB Render constraint
3. **MAJOR-003:** Add SSE connection lifecycle management details

These three issues can be addressed with targeted additions (estimated ~50-100 lines of additional content) without restructuring the document.

### 9.2 Development Readiness Assessment

| Gate | Status | Notes |
|------|--------|-------|
| PRD feature coverage | PASS | 18/18 features mapped |
| Technology stack validated | PASS | All technologies proven and in use |
| Database schema complete | PASS | 7 new tables + 2 views fully defined |
| API contract defined | PASS | 16 endpoints with request/response specs |
| Caching strategy defined | PASS | Two-level cache with clear decision matrix |
| Error handling designed | PASS | Per-source fallbacks documented |
| Testing infrastructure planned | PASS (with gaps) | Backend strong, frontend needs unit test plan |
| CI/CD pipeline defined | PASS | GitHub Actions + Netlify/Render auto-deploy |
| Security model defined | PASS | API keys, CORS, rate limiting, device identity |
| Risk register complete | PASS (with additions) | 10 risks + 3 suggested additions |

### 9.3 Next Steps

1. **Architect** resolves MAJOR-001, MAJOR-002, MAJOR-003 (estimated: 2-4 hours)
2. **QA** verifies fixes and grants full approval
3. **Development** begins with Phase 0 (Stabilization)
4. **QA** monitors development via PROGRESS.md and conducts code reviews at phase boundaries

---

*Review completed by: qa-guardian*
*Review methodology: 8-dimension framework + PRD traceability analysis + security/performance audit*
*Total review duration: Full document review (~2700 lines architecture + ~2500 lines PRD)*

---

## 3. Re-Review After Fixes (2026-02-09)

### 3.0 Review Context

**Document:** ARCHITECTURE.md v1.1 (~3100 lines, +420 lines from v1.0)
**Fix Report:** ARCHITECTURE_FIXES.md
**Sections Reviewed:** 2.1, 2.2.11 (new), 2.4.2, 2.5, 3.3.1 (new), 6.5 (new), 6.6, 8.5, 9.1, Appendix B
**Review Focus:** Verify 3 Major issue fixes, check for regressions, update scoring

---

### 3.1 Fix Verification

#### MAJOR-001 Fix: TradingCalendarService -- PASS

**Section 2.2.11 Review:**

The new `TradingCalendarService` design is thorough and well-integrated. Specific verification:

| Requirement (from original issue) | Implementation | Verdict |
|-----------------------------------|---------------|---------|
| Which AKShare function to use | `akshare.tool_trade_date_hist_sina()` specified | PASS |
| Chinese market holiday handling | Full-year trading dates in `set[date]`; holidays implicitly excluded | PASS |
| AKShare unavailable fallback | Static JSON file (`data/trading_calendar_static.json`) with 2024-2026 dates | PASS |
| Cache strategy | In-memory `set[date]` for O(1) lookup; daily refresh at 08:00 CST | PASS |
| Timezone handling | `Asia/Shanghai` via `zoneinfo.ZoneInfo`; `_today_cst()` helper method | PASS |
| Stale detection | 48-hour threshold; exposed in `/health` endpoint | PASS |
| Query interfaces | `is_trading_day()`, `next_trading_day()`, `add_trading_days()` -- all three meet functional requirements | PASS |

**Integration verification:**
- Section 2.1 updated with `trading_calendar_service.py` in module listing (line 385) -- PASS
- Section 2.5 updated with explicit job pattern showing `is_trading_day()` call -- PASS
- Calendar refresh job added as a scheduled job at 08:00 CST -- PASS
- Initialization sequence in `main.py` lifespan ensures calendar loads before scheduler starts -- PASS
- Integration points documented (scheduler, prediction_tracking, /health) -- PASS

**Design quality assessment:**
- The static fallback file is a pragmatic and reliable approach. Committing it to the repo ensures availability even without network access.
- The `_load_static_fallback()` method with clear file structure documentation makes maintenance straightforward.
- The basic weekday rule as an ultimate fallback (if calendar is empty) is a sensible defense-in-depth approach.
- Edge case handling: `next_trading_day()` iterates up to 30 days forward, which covers extended holiday periods (e.g., Spring Festival + National Day combined would never exceed 14 days).

**One minor observation (Nit):** The text below the scheduler code says "Job 5 (`refresh_trading_calendar`) runs daily at 08:00 CST" but in the scheduler code block, Job 5 is labeled as "Cache Cleanup (daily 03:00 CST)". The calendar refresh job should be labeled as Job 6 to avoid numbering confusion. This is cosmetic and does not affect functionality.

**Verdict: MAJOR-001 is fully resolved.**

---

#### MAJOR-002 Fix: Memory Budget Analysis -- PASS

**Section 6.5 Review:**

The memory budget analysis is comprehensive and demonstrates disciplined systems thinking. Specific verification:

| Requirement (from original issue) | Implementation | Verdict |
|-----------------------------------|---------------|---------|
| Memory budget estimation per component | Table in 6.5.1 with 10 components totaling ~151 MB baseline | PASS |
| Peak scenario analysis | 3 scenarios: recommendations (221 MB), global refresh (191 MB), concurrent (301 MB) | PASS |
| TTLCache maxsize consideration | Capped at 200/200/100 entries, ~50 MB max | PASS |
| Memory monitoring via /health | `psutil.Process().memory_info().rss` with response schema | PASS |
| Memory threshold alert | 410 MB (80% of 512 MB) triggers WARNING log | PASS |
| Upgrade contingency plan | Render Starter ($7/month) and Standard ($25/month) with clear triggers | PASS |

**Analysis quality assessment:**

1. **Baseline estimate (151 MB):** The component-level breakdown is reasonable. Python 3.11 runtime at ~25 MB is typical. FastAPI + Uvicorn at ~30 MB is slightly conservative but acceptable. The L1 cache estimate of ~50 MB for 500 entries is a reasonable worst-case upper bound.

2. **Scenario A (Recommendation Generation, 221 MB peak):** The batch processing strategy (10 stocks per batch) is key to controlling memory. Processing in batches of 10 with explicit DataFrame cleanup (`del df` + `gc.collect()`) prevents accumulation. The 221 MB estimate is credible at 43% utilization.

3. **Scenario B (Global Refresh, 191 MB peak):** Sequential 1-stock-at-a-time processing naturally limits memory. The 191 MB estimate at 37% utilization leaves substantial headroom.

4. **Scenario C (Concurrent operations, 301 MB peak):** This worst-case scenario at 59% utilization still leaves ~211 MB of headroom. The analysis correctly identifies this as the critical case but demonstrates it is within safe limits.

5. **Mitigation measures:** The 6-item mitigation table is actionable. The `psutil` health endpoint code sample is directly implementable.

6. **Upgrade path:** Clear triggers with costs make the decision framework transparent. The tiered approach (reduce cache first, then upgrade) is cost-conscious.

**One observation (Nit):** The Render Starter Plan is listed as "$7/month (512 MB - 1 GB RAM)" but the table says "Upgrade to Render Starter Plan" at the "RSS spikes causing OOM kills" trigger. The specific RAM amount for Starter Plan should be stated explicitly (e.g., "1 GB RAM" or "512 MB to 1 GB depending on configuration") to avoid ambiguity during the upgrade decision.

**Dependency verification:** `psutil==5.9.8` confirmed added to requirements.txt listing (line 3006) and Appendix B (line 3282). Consistent and correct.

**Verdict: MAJOR-002 is fully resolved.**

---

#### MAJOR-003 Fix: SSE Connection Lifecycle -- PASS

**Section 3.3.1 Review:**

The SSE connection lifecycle management is the most substantial fix (~200 lines) and addresses all four gaps identified in the original review. Specific verification:

| Requirement (from original issue) | Implementation | Verdict |
|-----------------------------------|---------------|---------|
| Backend disconnect detection | `request.is_disconnected()` checked before each stock | PASS |
| Concurrent refresh protection | In-memory `_active_refreshes` dict with RefreshState dataclass + 10-min TTL auto-expiry | PASS |
| SSE reconnection | 3 attempts with exponential backoff (2s, 4s, 6s) + `lastProgress` state tracking | PASS |
| Timeout handling | 5-minute server-side timeout with `timeout` event type | PASS |

**Detailed design quality assessment:**

1. **Backend Disconnect Detection:**
   - `request.is_disconnected()` checked before each stock processing -- correct placement.
   - On disconnect: breaks the loop, saving tokens for remaining stocks -- good resource conservation.
   - The `finally` block calls `_mark_refresh_complete()` ensuring state cleanup regardless of exit path -- robust.

2. **Concurrent Refresh Protection:**
   - `RefreshState` dataclass captures device_id, timestamps, progress, and status -- complete state model.
   - `_is_refresh_active()` performs auto-expiry check (10-min TTL) -- prevents orphaned states from blocking future refreshes.
   - Duplicate request returns current progress stream via `_resume_progress_stream()` rather than an error -- good UX.
   - Frontend button disabling prevents most duplicate requests at the UI level -- defense in depth.

3. **Frontend Reconnection:**
   - 3 attempts with exponential backoff (2s, 4s, 6s) is appropriate for a user-facing feature -- not too aggressive, not too slow.
   - `lastProgress` tracking enables state recovery on reconnect -- essential for UX continuity.
   - `reconnecting` event type allows UI to show reconnection feedback -- good user communication.
   - After max attempts, throws error with clear message -- graceful failure.

4. **Reconnection Status API:**
   - `GET /refresh/status` endpoint returns active status with progress -- enables frontend to determine refresh state on reconnection.
   - Returns `{"active": False}` when no refresh is active -- clean default.

5. **Interruption Handling:**
   - Clearly documented 5-step behavior for user page close -- complete lifecycle.
   - Idempotent property (already-processed stocks retain fresh data) is correctly identified -- no data loss.
   - Cache TTL (30 min) provides automatic "resume" benefit on re-entry -- clever use of existing caching.

6. **Maximum Duration:**
   - 5-minute explicit timeout with `timeout` event type -- prevents runaway connections.
   - Implicit limit calculation (~40 stocks x 5s = 200s) provides a sanity check against the 5-min explicit timeout -- consistent.

**Risk Register Update:** TR-7 correctly updated to reference `_active_refreshes` dict and Section 3.3.1 -- PASS.

**One minor observation (Nit):** The text description says "A heartbeat comment is sent every 15 seconds" but the code implementation sends it "every 3 stocks" (`if (i + 1) % 3 == 0`). These are different mechanisms -- stock-count-based vs time-based. At ~5 seconds per stock, every 3 stocks equals ~15 seconds, so the effect is similar. However, the document should be consistent: either describe it as "every 3 stocks" (matching the code) or implement a time-based heartbeat (matching the text). This is a documentation accuracy issue, not a functional concern.

**Another observation (Nit):** The new `GET /refresh/status` endpoint is not explicitly listed in the API Router Layer diagram in Section 1.1. The wildcard `/api/v1/refresh/*` implicitly covers it, but the endpoint count in the document (originally "16 endpoints") should be updated to reflect this addition.

**Verdict: MAJOR-003 is fully resolved.**

---

### 3.2 Regression and Integration Check

**Did the fixes introduce new problems or contradictions?**

| Check | Result | Notes |
|-------|--------|-------|
| Section numbering consistency | Minor issue | Job numbering conflict (two "Job 5" entries) -- cosmetic only |
| Heartbeat description vs code | Minor inconsistency | Text says "every 15s", code says "every 3 stocks" -- functionally equivalent |
| New endpoint not in router list | Minor omission | `GET /refresh/status` not reflected in Section 1.1 endpoint count |
| Section 6.5/6.6 renumbering | PASS | Clean renumbering, no broken references |
| New dependency (psutil) tracking | PASS | Added to requirements.txt (8.5) and Appendix B |
| Cross-references between sections | PASS | Section 2.2.11 <-> 2.5 <-> scheduler references are consistent |
| TradingCalendarService <-> AKShare client | PASS | Section 2.4.2 docstring references Section 2.2.11 |
| Memory budget <-> cache design | PASS | TTLCache maxsize (200/200/100) matches Section 2.3.3 values |
| SSE lifecycle <-> Risk Register | PASS | TR-7 updated to reference Section 3.3.1 |

**No new Major or Critical issues introduced by the fixes.**

**New Nit issues identified during re-review:** 3 (NIT-006 through NIT-008)

- **NIT-006:** Job numbering conflict -- two jobs labeled "Job 5" in Section 2.5. Calendar refresh should be Job 6.
- **NIT-007:** Heartbeat description says "every 15 seconds" but code implements "every 3 stocks". Should use consistent language.
- **NIT-008:** Endpoint count should be updated from 16 to 17 to include `GET /refresh/status`.

---

### 3.3 Updated Scoring

The scoring uses the same dimensions and weights as the original review. Changes reflect improvements from the three fixes.

| Dimension | Weight | Original (1-10) | New (1-10) | Change | Justification |
|-----------|--------|-----------------|------------|--------|---------------|
| PRD Consistency | 15% | 9 | 9 | -- | No change; all PRD features were already fully mapped |
| Architecture Completeness | 15% | 9 | 10 | +1 | TradingCalendarService fills the last significant gap; all components now have implementation detail |
| Technical Feasibility | 15% | 9 | 9 | -- | No change; already strong |
| Performance & Scalability | 10% | 8 | 9 | +1 | Memory budget analysis addresses the key constraint; batch processing and monitoring provide confidence |
| Security | 10% | 8 | 8 | -- | No change from fixes |
| Reliability & Fault Tolerance | 10% | 9 | 10 | +1 | SSE lifecycle management closes all reliability gaps for the streaming feature |
| Testability | 10% | 8 | 8 | -- | No change; frontend test gap (MINOR-006) still exists |
| Maintainability | 10% | 9 | 9 | -- | No change; already strong |
| Deployment & DevOps | 5% | 8 | 9 | +1 | Memory monitoring in /health + upgrade path provide operational clarity |

**Weighted Score Calculation:**

| Dimension | Weight | Score | Weighted |
|-----------|--------|-------|----------|
| PRD Consistency | 15% | 9 | 13.5 |
| Architecture Completeness | 15% | 10 | 15.0 |
| Technical Feasibility | 15% | 9 | 13.5 |
| Performance & Scalability | 10% | 9 | 9.0 |
| Security | 10% | 8 | 8.0 |
| Reliability & Fault Tolerance | 10% | 10 | 10.0 |
| Testability | 10% | 8 | 8.0 |
| Maintainability | 10% | 9 | 9.0 |
| Deployment & DevOps | 5% | 9 | 4.5 |
| **Total** | **100%** | | **90.5 -> 91** |

**Score improvement: 88 -> 91 (+3 points)**

---

### 3.4 Remaining Issues Summary

#### Issues Resolved by This Fix

| ID | Issue | Status |
|----|-------|--------|
| MAJOR-001 | No TradingCalendarService implementation detail | RESOLVED |
| MAJOR-002 | Render free tier memory constraint not addressed | RESOLVED |
| MAJOR-003 | SSE connection handling incomplete | RESOLVED |

#### Issues Still Open (from original review, non-blocking)

| ID | Severity | Issue | Recommendation |
|----|----------|-------|----------------|
| MINOR-001 | Minor | Next.js version discrepancy (15 vs 16) | Fix during development |
| MINOR-002 | Minor | No standardized error response schema | Fix in Phase 1 |
| MINOR-003 | Minor | Watchlist snapshot dedup UX unclear | Clarify during implementation |
| MINOR-004 | Minor | No graceful degradation UI component | Add during frontend development |
| MINOR-005 | Minor | Database migration versioning not defined | Define before Phase 0 migration |
| MINOR-006 | Minor | Frontend test strategy underspecified | Define before Phase 2 |
| NIT-001 | Nit | Next.js "SSG" vs "Static Export" terminology | Optional |
| NIT-002 | Nit | Cache TTLs documented in multiple places | Optional |
| NIT-003 | Nit | rate_limiter_service vs infrastructure naming | Optional |
| NIT-004 | Nit | CORS hardcoded domains | Optional |
| NIT-005 | Nit | Appendix A missing some Pydantic model definitions | Optional |
| NIT-006 | Nit (new) | Job numbering conflict (two "Job 5") | Fix during development |
| NIT-007 | Nit (new) | Heartbeat description inconsistency (15s vs 3 stocks) | Fix in document |
| NIT-008 | Nit (new) | Endpoint count should be 17, not 16 | Fix in document |

**No Critical or Major issues remain.**

---

### 3.5 Final Verdict

**APPROVED**

The ARCHITECTURE.md v1.1 scores **91/100**, exceeding the 90-point approval threshold. All three Major issues have been resolved with thorough, well-designed solutions that integrate cleanly with the existing architecture.

**Key improvements in v1.1:**
- TradingCalendarService provides reliable trading day detection with a dual-source strategy (AKShare primary + static fallback), proper timezone handling, and clean integration with all scheduled jobs.
- Memory budget analysis demonstrates that the system operates within Render's 512 MB constraint with a worst-case utilization of 59%, along with concrete mitigation measures and a clear upgrade path.
- SSE connection lifecycle management covers all four previously-missing scenarios (disconnect detection, concurrent protection, reconnection, interruption handling) with production-quality code patterns.

**Remaining items (6 Minor + 8 Nit) are non-blocking and can be addressed during development.**

### 3.6 Recommendation

The architecture document is ready for development. The team should proceed with:

1. **Immediate:** Begin Phase 0 (Stabilization) development
2. **During development:** Address MINOR-001 through MINOR-006 at the relevant phase boundaries
3. **Before Phase 2:** Define the frontend unit test strategy (MINOR-006) to ensure adequate test coverage for 30+ new components
4. **Post-MVP:** Monitor memory usage in production and follow the upgrade path defined in Section 6.5.6 if needed

**Development can begin immediately.**

---

*Re-review completed by: qa-guardian*
*Date: 2026-02-09*
*Document version reviewed: ARCHITECTURE.md v1.1*
*Verdict: APPROVED (91/100)*
