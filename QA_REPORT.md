# QA Report - Stock Advisor v2.0

## Basic Information
- **Project Name**: Stock Advisor v2.0 (A Stock Trading Strategy System)
- **QA Reviewer**: qa-guardian
- **Report Date**: 2026-02-06 (Created)
- **Last Updated**: 2026-02-09 (P0/P1 Feature Code Review)
- **Current Status**: P0/P1 FEATURE CODE REVIEW COMPLETED

---

## FINAL QUALITY AUDIT - 2026-02-09

### Audit Scope

This final audit covers the complete v2.0 delivery:
- 10 backend service modules
- 5 API route files (17 endpoints)
- 14 E2E test cases
- 7 database tables
- Production deployment on Render
- All project documentation

---

## 1. Code Quality Assessment (Google 8-Dimension Framework)

### 1.1 Design (4/5)

**Strengths:**
- Clean separation of concerns: API routes -> Services -> Database (DAO pattern)
- Comprehensive analysis service (`comprehensive_analysis_service.py`) acts as an orchestrator, coordinating 5 dimensions via `asyncio.gather` for parallel data fetching
- Singleton pattern for Supabase client via `_SupabaseProxy` lazy initialization
- Config management via `pydantic-settings` with environment variable support
- Fallback strategy for data sources (EastMoney -> Yahoo Finance)
- AI fallback: GLM-4 API -> rule-based defaults (graceful degradation)

**Issues:**

| Severity | Location | Issue | Status |
|----------|----------|-------|--------|
| Major | `main.py:48,57` | Uses deprecated `@app.on_event("startup/shutdown")` pattern; FastAPI recommends `lifespan` context manager since v0.109 | Open |
| Minor | `main.py:90-158` | Debug endpoint `/debug/stock/{code}` exposed in production; should be behind a debug flag or removed | Open |
| Minor | `stock.py:15-23` | In-memory caches (`_ai_rankings_cache`, `_stock_analysis_cache`) will not persist across Render cold starts | Accepted (documented limitation) |

### 1.2 Functionality (4/5)

**Strengths:**
- All 14 E2E test cases pass (100%)
- 5-dimensional analysis returns complete data for all dimensions
- Watchlist CRUD operations work correctly with proper conflict handling (409 for duplicates)
- Token monitoring with daily reset and warning thresholds
- Proper error handling: 404 for invalid stocks, 422 for validation errors, 500 for internal errors
- Trading calendar integration prevents scheduled jobs on non-trading days

**Issues:**

| Severity | Location | Issue | Status |
|----------|----------|-------|--------|
| Minor | `comprehensive_analysis_service.py:50-54` | Synchronous functions (`eastmoney_service.get_realtime`, `get_history`) are called before async tasks, blocking the event loop | Open |
| Minor | `token_monitor_service.py` | Token usage is tracked in-memory only; resets on Render cold restarts; actual GLM API calls in `ai_analysis_service.py` do not call `token_monitor.log_usage()` | Open |
| Minor | `watchlist.py:13` | `name: str = None` should use `Optional[str] = None` for proper type annotation | Open |
| Nit | `comprehensive_analysis_service.py:278-293` | `_generate_trading_suggestion` has identical risk level for score >= 70 and score >= 50 (both return "medium") | Open |

### 1.3 Complexity (4/5)

**Strengths:**
- Most functions are under 50 lines
- Service layer is well-decomposed into single-responsibility modules
- Comprehensive analysis orchestrator cleanly delegates to sub-services

**Issues:**

| Severity | Location | Issue | Status |
|----------|----------|-------|--------|
| Minor | `stock.py:50-260` | `get_stock_analysis` function is 210 lines -- too long; formatting, caching, and AI logic should be extracted into helper functions | Open |
| Minor | `stock.py:393-519` | `get_ai_rankings` is 126 lines with deeply embedded logic; hot stock list should be externalized | Open |
| Nit | `ai_analysis_service.py` | JSON parsing with markdown code block stripping is duplicated 3 times (lines 210-218, 297-303, 397-402); should be a utility function | Open |

### 1.4 Tests (3/5)

**Strengths:**
- 14 E2E test cases covering 5 categories (basic API, v2.0 features, watchlist, error handling, performance)
- Well-structured test runner with categorized reporting
- Tests verify response structure, required fields, and status codes
- Edge cases tested: invalid stock codes, missing parameters

**Issues:**

| Severity | Location | Issue | Status |
|----------|----------|-------|--------|
| Major | Project-wide | No unit tests exist; only E2E tests against production API | Open |
| Major | Project-wide | No integration tests for individual services | Open |
| Major | `test_e2e_v2.py` | Tests run against production URL only; no local test environment configuration | Open |
| Minor | `test_e2e_v2.py:487-493` | Invalid stock code test accepts HTTP 500 as valid (line 487); 500 should not be expected behavior | Open |
| Minor | Project-wide | No test for scheduler jobs (daily_snapshot, evaluation_job) | Open |
| FYI | Project-wide | Test pyramid is inverted: 100% E2E, 0% unit, 0% integration | Open |

### 1.5 Naming (4/5)

**Strengths:**
- Service files clearly named by responsibility (e.g., `watchlist_service.py`, `token_monitor_service.py`)
- Function names are descriptive: `generate_comprehensive_analysis`, `calculate_trading_suggestion`
- API route paths follow REST conventions: `/watchlist/add`, `/watchlist/check/{code}`

**Issues:**

| Severity | Location | Issue | Status |
|----------|----------|-------|--------|
| Nit | `ai_analysis_service.py:19` | Private function `_get_glm_api_key` is imported by `glm_service.py`; underscore prefix implies private | Open |
| Nit | `ai_analysis_service.py:56` | `_ai_model_status` is a "private" module-level instance but imported externally by `glm_service.py` | Open |

### 1.6 Comments (4/5)

**Strengths:**
- All service files have module-level docstrings explaining purpose
- Function signatures include Args/Returns documentation
- Scheduler jobs have clear descriptions of execution schedule and conditions

**Issues:**

| Severity | Location | Issue | Status |
|----------|----------|-------|--------|
| Nit | `stock.py:158` | Comment `# Trigger deployment` at end of `main.py` is leftover from a deployment trigger commit | Open |
| Nit | `comprehensive_analysis_service.py:108,119,145,169,192` | Multiple `ai_comment: ''` fields with comment "will be generated by AI" but AI generation was disabled | Open |

### 1.7 Style (5/5)

**Strengths:**
- Consistent Python code style throughout
- Proper use of type hints in most service functions
- FastAPI router patterns consistent across all API files
- Consistent error handling pattern with try/except blocks

### 1.8 Documentation (4/5)

**Strengths:**
- Comprehensive DESIGN.md covering architecture, data model, API design, and strategies
- DELIVERY_SUMMARY.md provides complete delivery checklist
- Swagger/ReDoc auto-generated at `/docs` and `/redoc`
- PROGRESS.md maintained throughout development lifecycle

**Issues:**

| Severity | Location | Issue | Status |
|----------|----------|-------|--------|
| Major | `SUMMARY.md` | Still describes project as "design and planning complete, ready for development" -- does not reflect v2.0 development/deployment completion | Open |
| Minor | `PROGRESS.md` | Header says "Paused - v2.0 E2E testing complete, deployment issues found" but deployment issues were resolved; status is stale | Open |
| Minor | `QA_REPORT.md` | Was outdated (reflected v1.0 state); now updated with this final audit | Fixed |

---

## 2. Security Assessment (OWASP)

### 2.1 Resolved Security Issues

| ID | Issue | Status | Evidence |
|----|-------|--------|----------|
| SEC-001 | API Key hardcoded in `ai_analysis_service.py` | RESOLVED | Key now loaded via `get_settings().glm_api_key` from environment variables |
| SEC-002 | API Key hardcoded in `glm_service.py` | RESOLVED | `glm_service.py` imports `_get_glm_api_key()` from `ai_analysis_service.py` |

### 2.2 Remaining Security Observations

| Severity | Issue | Risk Level | Recommendation |
|----------|-------|------------|----------------|
| Minor | No API rate limiting on public endpoints | Medium | Add `slowapi` middleware (already in architecture plan but not implemented) |
| Minor | No authentication on watchlist endpoints; `default_user` hardcoded | Low | Acceptable for MVP; noted for Phase 2 |
| Minor | CORS allows specific origins but includes `allow_methods=["*"]` and `allow_headers=["*"]` | Low | Tighten to specific methods/headers needed |
| FYI | Debug endpoint `/debug/stock/{code}` is publicly accessible | Low | Consider removing or gating behind config flag |
| FYI | Supabase key in environment could be the `anon` key (public) or `service_role` key (private); verify correct key type | Low | Verify in Render dashboard |

---

## 3. E2E Test Verification

### 3.1 Test Results (as reported by tester)

**Test Date**: 2026-02-09
**Test Environment**: Production (https://stock-advisor-api-6vtb.onrender.com)
**Total Tests**: 14 | **Passed**: 14 | **Failed**: 0 | **Pass Rate**: 100%

| Category | Tests | Pass Rate |
|----------|-------|-----------|
| Basic API | 3/3 | 100% |
| v2.0 New Features | 4/4 | 100% |
| Watchlist | 4/4 | 100% |
| Error Handling | 2/2 | 100% |
| Performance | 1/1 | 100% |

### 3.2 Test Coverage Analysis

**Covered:**
- Health check and root endpoint
- Single stock query (legacy API)
- 5-dimensional comprehensive analysis
- News retrieval
- Token usage and statistics
- Watchlist full CRUD lifecycle (add -> list -> check -> remove)
- Invalid stock code handling
- Missing parameter validation
- Cold start performance

**NOT Covered (Gaps):**
- Stock search endpoint (`/stocks/search`) -- not tested in E2E
- AI rankings endpoint (`/rankings/ai`) -- not tested
- K-line data endpoint (`/stock/{code}/kline`) -- not tested
- AI analysis endpoint (`/stock/{code}/ai-analysis`) -- not tested
- Recommendations endpoints (`/recommendations`, `/recommendations/generate`) -- not tested in v2.0 E2E
- Market overview endpoint (`/market/overview`) -- not tested in v2.0 E2E
- Statistics endpoint (`/stats/performance`) -- not tested in v2.0 E2E
- Industry analysis endpoint (`/industry/{name}/analysis`) -- not tested
- Refresh endpoints (`/refresh/all`, `/refresh/status`) -- not tested
- Prefetch endpoint (`/stocks/prefetch`) -- not tested
- Scheduler jobs -- not testable via E2E

**Coverage Assessment**: E2E tests cover approximately 8 of 17+ endpoints (47% endpoint coverage). Core v2.0 features (comprehensive analysis, watchlist, token monitoring) are well tested, but many legacy and supporting endpoints lack v2.0 E2E coverage.

---

## 4. Deployment Verification

### 4.1 Deployment Status

| Component | Status | URL |
|-----------|--------|-----|
| Backend API | Running | https://stock-advisor-api-6vtb.onrender.com |
| API Docs | Running | https://stock-advisor-api-6vtb.onrender.com/docs |
| Database | Running | Supabase (7 tables + indexes) |
| Frontend | Running | https://my-stock-advisor.netlify.app |

### 4.2 Deployment Observations

| Area | Status | Notes |
|------|--------|-------|
| Render deployment | Stable | Deployed via GitHub auto-deploy; 3 fix iterations (573205b, 254bb34, 82b60b8) |
| Database migration | Complete | 7 tables created with proper indexes |
| Environment variables | Configured | SUPABASE_URL, SUPABASE_KEY, GLM_API_KEY set in Render |
| Cold start | Acceptable | 5.75s (Free Tier limitation, documented) |
| Hot response times | Good | 0.59s - 0.75s average |

---

## 5. Documentation Completeness Audit

| Document | Exists | Current | Notes |
|----------|--------|---------|-------|
| DESIGN.md | Yes | Partially outdated | Original v1.0 design; PRD_v2.0.md is the authority |
| PROGRESS.md | Yes | Stale header | Header shows "paused" but issues were resolved |
| QA_REPORT.md | Yes | Updated | This document (final audit) |
| DELIVERY_SUMMARY.md | Yes | Current | Complete delivery summary |
| SUMMARY.md | Yes | Outdated | Describes "design complete, ready for development" -- does not reflect actual v2.0 completion |
| PRD_v2.0.md | Yes | Current | Authoritative product requirements |
| ARCHITECTURE.md | Yes | Current | v1.1, QA approved |
| TEST_CASES.md | Yes | Partially outdated | 75+ cases from v1.0; v2.0 test_e2e_v2.py is the current E2E suite |

---

## 6. Quality Metrics Dashboard

### 6.1 Core Metrics

| Metric | Target | Current | Status | Trend |
|--------|--------|---------|--------|-------|
| E2E Test Pass Rate | 100% | 100% (14/14) | PASS | Improved from 57% to 100% |
| Unit Test Coverage | > 70% | 0% | FAIL | No change |
| Critical Bugs | 0 | 0 | PASS | Resolved from 2 |
| Major Bugs | 0 | 0 | PASS | Resolved from 2 |
| API Key Security | Resolved | Resolved | PASS | Fixed |
| Documentation Completeness | 100% | 80% | WARN | SUMMARY.md needs update |
| Build Success | Pass | Pass | PASS | Stable |

### 6.2 Test Pyramid Health

| Test Type | Target Ratio | Current Ratio | Count | Status |
|-----------|-------------|---------------|-------|--------|
| Unit Tests | 70% | 0% | 0 | FAIL |
| Integration Tests | 20% | 0% | 0 | FAIL |
| E2E Tests | 10% | 100% | 14 | WARN (inverted pyramid) |

### 6.3 Quality Gates

| Gate | Condition | Current | Pass |
|------|-----------|---------|------|
| E2E Pass Rate | 100% pass | 100% | YES |
| P0 Tests | All pass | 3/3 pass | YES |
| Critical Bugs | 0 open | 0 open | YES |
| Major Bugs | 0 open | 0 open | YES |
| Security Issues | 0 critical | 0 critical | YES |
| API Key Security | Not hardcoded | Environment variables | YES |
| Production Deployment | Running | Running | YES |
| Unit Test Coverage | >= 70% | 0% | NO |

---

## 7. Code Review Summary (8-Dimension Scores)

| Dimension | Score | Weight | Weighted | Assessment |
|-----------|-------|--------|----------|------------|
| Design | 4/5 | High | Good architecture, minor deprecation issues |
| Functionality | 4/5 | High | All features work, minor gaps in token tracking |
| Complexity | 4/5 | High | Most code is clean; 2 oversized functions |
| Tests | 3/5 | High | E2E complete but no unit/integration tests |
| Naming | 4/5 | Medium | Clear and consistent naming conventions |
| Comments | 4/5 | Medium | Good documentation, minor stale comments |
| Style | 5/5 | Low | Consistent code style |
| Documentation | 4/5 | Medium | Comprehensive but SUMMARY.md is outdated |

**Total Score: 32/40 = 80%**

---

## 8. Risk and Issue Tracking

### 8.1 Resolved Issues (from previous QA cycles)

| ID | Type | Description | Resolution |
|----|------|-------------|------------|
| SEC-001 | Security | API Key hardcoded in ai_analysis_service.py | Moved to environment variable |
| SEC-002 | Security | API Key hardcoded in glm_service.py | Uses shared `_get_glm_api_key()` |
| BUG-001 | Bug | Stock search API 404 (route priority) | Moved to `/stocks/search` |
| BUG-002 | Bug | Only 5 recommendations instead of 10 | Regenerated |
| DEF-001 | Deployment | v2.0 code not deployed to Render | Deployed and verified |
| DEF-002 | Deployment | Database tables not created | 7 tables migrated |

### 8.2 Open Issues (Non-Blocking)

| ID | Type | Description | Severity | Priority | Recommendation |
|----|------|-------------|----------|----------|----------------|
| QA-F-001 | Testing | No unit tests exist | Major | P1 | Add pytest unit tests for indicator_service, strategy_service |
| QA-F-002 | Testing | Inverted test pyramid (100% E2E, 0% unit) | Major | P1 | Target 70% unit / 20% integration / 10% E2E |
| QA-F-003 | Testing | E2E covers only 47% of endpoints | Minor | P2 | Add tests for search, rankings, kline, industry |
| QA-F-004 | Code | `get_stock_analysis` function is 210 lines | Minor | P2 | Extract formatting and caching logic |
| QA-F-005 | Code | JSON markdown stripping duplicated 3x | Nit | P3 | Extract to utility function |
| QA-F-006 | Code | Deprecated `on_event` startup/shutdown | Minor | P2 | Migrate to FastAPI `lifespan` |
| QA-F-007 | Code | Token monitor not integrated with actual GLM calls | Minor | P2 | Call `token_monitor.log_usage()` in `call_glm_api` |
| QA-F-008 | Docs | SUMMARY.md still says "design complete, ready for development" | Major | P1 | Update to reflect v2.0 completion |
| QA-F-009 | Docs | PROGRESS.md header shows "paused" status | Minor | P1 | Update to "completed" |
| QA-F-010 | Code | Debug endpoint exposed in production | Minor | P2 | Gate behind `settings.debug` flag |
| QA-F-011 | Code | No API rate limiting implemented | Minor | P2 | Add slowapi middleware |

---

## 9. Final Quality Assessment

### 9.1 Overall Score: 7.5/10

**Quality Dimension Ratings:**

| Dimension | Score | Change from v1.0 QA | Notes |
|-----------|-------|---------------------|-------|
| Functionality | 4.5/5 | +1.5 | All v2.0 features working in production |
| Code Quality | 3.5/5 | +0.5 | Security issues resolved; some complexity remains |
| Test Coverage | 2.5/5 | +1.5 | E2E complete but no unit/integration tests |
| Documentation | 4/5 | +0 | Good overall but SUMMARY.md outdated |
| Security | 4/5 | +2 | API key issue resolved; minor items remain |
| Performance | 4.5/5 | N/A (new) | All targets met; cold start acceptable for free tier |
| Architecture | 4/5 | N/A (new) | Clean separation; good fault tolerance design |

### 9.2 Comparison with Previous QA Reports

| Metric | QA #1 (Feb 6) | QA #2 (Feb 8) | Final (Feb 9) |
|--------|---------------|---------------|---------------|
| Overall Score | 5/10 | 6/10 | **7.5/10** |
| E2E Pass Rate | 57% (4/7) | 61% (14/23) | **100% (14/14)** |
| Critical Bugs | 2 | 2 | **0** |
| Security Issues | 2 Critical | 2 Critical | **0 Critical** |
| Release Status | NOT RECOMMENDED | NOT RECOMMENDED | **CONDITIONAL PASS** |

### 9.3 Release Recommendation: CONDITIONAL PASS

**Verdict**: The project is approved for delivery as a working MVP with documented limitations.

**Conditions met (MUST):**
- [x] All P0 E2E tests pass (100%)
- [x] No Critical or Major bugs blocking core functionality
- [x] API key security issue resolved
- [x] Production deployment stable
- [x] Database migration complete
- [x] Core v2.0 features operational (5D analysis, watchlist, token monitoring)

**Conditions NOT met (SHOULD -- non-blocking for MVP):**
- [ ] Unit test coverage >= 70% (currently 0%)
- [ ] SUMMARY.md updated to reflect v2.0 completion
- [ ] PROGRESS.md header updated to completed status

**Rationale for Conditional Pass:**
The system functions correctly in production with all 14 E2E tests passing. The core value proposition (5-dimensional stock analysis, watchlist management, token monitoring) works as designed. The primary gap is the complete absence of unit and integration tests, which creates technical debt and risks for future maintenance. However, this does not block the current delivery since the E2E tests validate end-user functionality.

### 9.4 Recommended Immediate Actions (P0/P1)

1. **[P1] Update SUMMARY.md** to accurately reflect v2.0 completion status
2. **[P1] Update PROGRESS.md** header to show "Completed" instead of "Paused"
3. **[P1] Add unit tests** for core services (indicator_service, strategy_service) to begin building the test pyramid

### 9.5 Recommended Follow-up Actions (P2/P3)

4. **[P2] Add integration tests** for database operations
5. **[P2] Expand E2E coverage** to remaining endpoints (search, rankings, kline, industry)
6. **[P2] Refactor** `get_stock_analysis` (210 lines) into smaller functions
7. **[P2] Integrate token monitoring** with actual GLM API calls
8. **[P2] Add rate limiting** via slowapi middleware
9. **[P3] Migrate** from deprecated `on_event` to `lifespan` context manager
10. **[P3] Extract** JSON parsing utility to reduce code duplication

---

## 10. Delivery Acceptance Checklist

| Item | Status | Evidence |
|------|--------|----------|
| Core functionality works | PASS | 14/14 E2E tests |
| Production deployment stable | PASS | API responding at production URL |
| Database properly configured | PASS | 7 tables migrated with indexes |
| No Critical/Major bugs | PASS | All resolved |
| No security vulnerabilities | PASS | API key moved to env vars |
| E2E tests documented and passing | PASS | test_e2e_v2.py, 100% pass rate |
| API documentation available | PASS | /docs and /redoc endpoints |
| Design documentation complete | PASS | DESIGN.md, PRD_v2.0.md, ARCHITECTURE.md |
| Unit test coverage adequate | FAIL | 0% coverage |
| SUMMARY.md up to date | FAIL | Reflects design phase, not completion |

**Final Decision: APPROVED FOR DELIVERY (with documented technical debt)**

---

---

## 11. P0/P1 Feature Code Review - 2026-02-09

### Review Scope

Code review for three newly completed features:
- **Task #39** [P0]: History Tracking Frontend (HistoryClient.tsx, history page, api.ts additions, StockDetailClient.tsx)
- **Task #40** [P1]: Recommendation Auto-Scheduling (scheduler.py - daily_recommendations_job)
- **Task #41** [P1]: Global Refresh Extension (refresh.py, RefreshAllButton.tsx)

### 8-Dimension Scores (Feature-Specific)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Design | 4/5 | Good separation; SSE pattern appropriate for long-running refresh |
| Functionality | 3/5 | Critical: API_BASE_URL not exported; SSE parse unprotected; scheduler no timezone |
| Complexity | 4/5 | HistoryClient 311 lines acceptable; refresh generator slightly complex |
| Tests | 1/5 | Zero tests for any new feature (~700 new LOC) |
| Naming | 4/5 | Clear conventions; Chinese comments helpful for domain context |
| Comments | 4/5 | Good docstrings on scheduler jobs and endpoints |
| Style | 4/5 | Consistent Tailwind and Python patterns |
| Documentation | 3/5 | API functions documented; PROGRESS.md not updated |

**Feature Review Total: 27/40 = 67.5%**

### Critical Issues (Block Release)

| ID | File | Line | Description |
|----|------|------|-------------|
| CR4-C001 | `src/lib/api.ts` | 6 | `API_BASE_URL` declared as `const` (not `export const`) but imported by `RefreshAllButton.tsx:4`. Build will fail or import resolves to `undefined`. Fix: add `export` keyword. |
| CR4-C002 | `src/components/RefreshAllButton.tsx` | 59 | `JSON.parse(line.slice(6))` has no try-catch. SSE chunks can be split across reads, yielding incomplete JSON. This will crash the component with uncaught exception. Fix: wrap in try-catch and implement SSE buffer logic. |

### Major Issues (Must Fix)

| ID | File | Line | Description |
|----|------|------|-------------|
| CR4-M001 | `backend/app/scheduler.py` | 22,59,107 | No `timezone` parameter on cron jobs. Render servers default to UTC; jobs would fire at UTC 17:00 (Beijing 01:00 AM), useless for A-stock market. Fix: add `timezone='Asia/Shanghai'`. |
| CR4-M002 | `backend/app/api/refresh.py` | 23,54-58 | `_active_refreshes` dict is not thread/async-safe. Race condition: two concurrent requests can both pass the `if user_id in` check. Fix: use `asyncio.Lock()`. |
| CR4-M003 | `backend/app/scheduler.py` | all | Uses `print()` for logging. No log levels, timestamps, or ability to filter. Fix: use `logging.getLogger(__name__)`. |
| CR4-M004 | `src/components/HistoryClient.tsx` | 52-53 | `loadData` defined as regular function but missing from `useEffect` deps. React anti-pattern. Fix: wrap with `useCallback`. |
| CR4-M005 | `src/components/RefreshAllButton.tsx` | 40-88 | No `AbortController` cleanup for SSE fetch. Component unmount during streaming causes setState on unmounted component. Fix: add AbortController. |
| CR4-M006 | Project-wide | - | Zero test coverage for 700+ new lines of code. |

### Minor Issues

| ID | File | Line | Description |
|----|------|------|-------------|
| CR4-m001 | `src/components/HistoryClient.tsx` | 12-32 | `HistoryRecord` interface duplicates inline type from `api.ts:394-416`. Maintenance risk. |
| CR4-m002 | `src/lib/api.ts` | 405 | `analysis_content: any` bypasses type safety. |
| CR4-m003 | `api.ts:388,426`, `RefreshAllButton.tsx:29` | - | `'default_user'` hardcoded in 3 places. |
| CR4-m004 | `src/components/RefreshAllButton.tsx` | 81 | `window.location.reload()` is poor SPA UX. |
| CR4-m005 | `backend/app/api/refresh.py` | 97 | `len(recommendations)` will throw if `recommendations` is `None`. |

### Nit Issues

| ID | File | Description |
|----|------|-------------|
| CR4-n001 | `refresh.py:131` | Failed stocks don't increment `tasks_completed`; progress never reaches 100% if any fail. |
| CR4-n002 | `refresh.py:124` | SSE heartbeat comment not documented for frontend. |
| CR4-n003 | `api.ts:389` | Magic number `30` for default days. |

### Review Verdict: CONDITIONALLY APPROVED

**Must fix before next deployment:** CR4-C001, CR4-C002, CR4-M001

**Must fix within current sprint:** CR4-M002 through CR4-M006

### Positive Highlights

1. `Promise.all` parallel loading in HistoryClient (line 61) with graceful degradation via `.catch(() => null)`
2. Trading day check in all scheduler jobs prevents wasted API calls
3. SSE heartbeat mechanism prevents connection timeout
4. Per-stock error tolerance in both scheduler and refresh endpoint
5. Clean history UI with evaluation status badges (correct/incorrect predictions)

---

---

## 12. Performance Optimization Code Review - 2026-02-10

### Review Scope

Code review for major performance optimization across 22 files:
- **Backend (13 files)**: urllib -> httpx async migration, asyncio.gather parallelization, TTLCache caching, event loop antipattern removal
- **Frontend (9 files)**: Skeleton loading, SSR timeout/degradation, differentiated timeouts, double-wake removal, SSE robustness, anti-duplicate loading, effect dependency fixes

### Review Summary

| Level | Count | Description |
|-------|-------|-------------|
| Critical | 2 | Must fix before deployment |
| Major | 3 | Recommend fix, not blocking |
| Minor | 4 | Code quality improvements |
| PASS | 13 | Review passed |

**Overall Assessment**: High quality optimization. Async migration is correct, parallelization is well designed. 2 Critical issues need fixing.

---

### Critical Issues

#### CR5-C001: `main.py` debug endpoint missing `await` on async functions

**File**: `backend/app/main.py:111-146`
**Problem**: `/debug/stock/{code}` endpoint calls `eastmoney_service.get_stock_history()`, `get_stock_realtime()`, `get_history()`, `get_realtime()` — all converted to `async` in this optimization — **without `await`**.

```python
# Line 111-112 (and similar at 141-146)
df_em = eastmoney_service.get_stock_history(code, days=60)  # Missing await!
rt_em = eastmoney_service.get_stock_realtime(code)           # Missing await!
```

**Impact**: Returns coroutine objects instead of data. `df_em is not None` always True (coroutine != None), `len(df_em)` throws TypeError. Debug endpoint completely broken.

**Fix**: Add `await` to all 6 async calls in the debug endpoint.

#### CR5-C002: `refresh.py` SSE loses per-stock progress events after parallelization

**File**: `backend/app/api/refresh.py:95-123`
**Problem**: `asyncio.gather` runs all stock refreshes in parallel but only yields a single progress event after ALL stocks complete. The SSE stream goes silent during the entire stock refresh phase.

```python
# All stocks refresh in parallel...
refresh_results = await asyncio.gather(
    *[_refresh_one(c) for c in codes]
)
# ...only ONE yield happens here, after all are done
```

**Impact**: Frontend `RefreshAllButton.tsx` receives no intermediate progress during stock refresh. Progress bar appears stuck between recommendations completion and final 100%.

**Fix Options**:
1. Use `asyncio.Queue` in `_refresh_one` to push progress events, drain queue in generator
2. Use `asyncio.as_completed` to yield as each stock finishes
3. Accept this as a tradeoff of parallelization (simpler but worse UX)

---

### Major Issues

#### CR5-M001: `chat_service.py` synchronous DB calls block event loop

**File**: `backend/app/services/chat_service.py:125-139, 142-175, 229-255, 258-272`
**Problem**: `get_remaining_quota()`, `find_similar_answer()`, `save_chat_history()`, `get_chat_history()` are synchronous functions with Supabase SDK blocking I/O. Called directly within `async def ask_question()`.

**Impact**: Blocks event loop during DB queries. Low impact at current traffic but violates async best practices.

**Fix**: Wrap with `await asyncio.to_thread()` or convert to async.

#### CR5-M002: `cache_service.py` all functions synchronous, blocking in async handlers

**File**: `backend/app/services/cache_service.py` (called by `stock.py`)
**Problem**: `get_cached_analysis()`, `save_analysis_cache()`, `get_cached_analyses_batch()` etc. all use synchronous Supabase SDK calls. Called directly in async API handlers.

**Impact**: Same as M001. Acceptable short-term for MVP traffic levels.

#### CR5-M003: `db/supabase.py` async def functions with no actual await

**File**: `backend/app/db/supabase.py:29-258`
**Problem**: All functions declared `async def` but contain only synchronous Supabase SDK calls. No `await` inside any function body. Pre-existing issue, not introduced by this optimization.

**Impact**: Misleading — functions appear async but still block. Works because callers can `await` them (returns coroutine that immediately resolves).

---

### Minor Issues

#### CR5-m001: `StockChatPanel.tsx` useEffect missing `loadHistory` dependency

**File**: `src/components/StockChatPanel.tsx:30-34`
```tsx
useEffect(() => {
  if (expanded) { loadHistory(); }
}, [expanded, code]);  // loadHistory not in deps
```
**Impact**: Functionally fine but violates React exhaustive-deps rule.

#### CR5-m002: `http_client.py` lazy singleton without lock

**File**: `backend/app/http_client.py:23-33`
**Problem**: `get_client()` has no lock on global `_client` initialization. Safe under asyncio single-threaded model, but fragile if `asyncio.to_thread` is used.

**Suggestion**: Pre-create in FastAPI startup event.

#### CR5-m003: `_get_stock_cache_ttl()` defined but never used

**File**: `backend/app/api/stock.py:26-30`
**Problem**: Dead code. TTLCache TTL is fixed at creation time (180s), function would need to rebuild the cache to change TTL.

#### CR5-m004: ETF price precision inconsistency between APIs

**File**: `backend/app/services/eastmoney_service.py`
**Problem**: `get_batch_realtime()` returns ETF prices with 3 decimals (`round(price, 3)`), while `get_stock_realtime()` returns 2 decimals (`round(price, 2)`).

**Impact**: Same ETF shows different price precision depending on API path.

---

### PASS - Files that passed review

#### Backend (11 PASS)

| # | File | Notes |
|---|------|-------|
| 1 | `requirements.txt` | cachetools 5.3.2 + httpx 0.27.0 versions appropriate, no conflicts |
| 2 | `http_client.py` | Shared AsyncClient with connection pooling (20 max, 10 keepalive), proper shutdown |
| 3 | `main.py` (lifecycle) | `close_client()` correctly awaited in shutdown event |
| 4 | `eastmoney_service.py` | Full async migration correct. Retry with `await asyncio.sleep(0.3)`. Yahoo fallback uses `asyncio.to_thread` for sync wrapper. Batch API via `ulist.np` single HTTP call |
| 5 | `glm_service.py` | Async httpx POST correct, error status handling preserved |
| 6 | `ai_analysis_service.py` | `asyncio.gather` for parallel company + fundamental analysis, serial AI recommendation. TTLCache(100, 14400) appropriate |
| 7 | `news_service.py` | Simple async migration, correct |
| 8 | `fundamental_service.py` | Simple async migration, correct |
| 9 | `comprehensive_analysis_service.py` | 5-dimension parallel: `create_task` + `gather` pattern correct |
| 10 | `scheduler.py` | Removed `asyncio.new_event_loop()` antipattern. Now uses `AsyncIOScheduler` + direct `gather` + `Semaphore(3)`. Deadline check prevents runaway jobs |
| 11 | `stock.py` | 3-layer cache (L1 memory TTL -> L2 Supabase -> L3 live) correct. `Semaphore(5)` for batch analysis. `asyncio.gather` for parallel history+realtime and summary+AI analysis |

#### Frontend (8 PASS)

| # | File | Notes |
|---|------|-------|
| 1 | `loading.tsx` | Skeleton matches page layout structure |
| 2 | `page.tsx` | 15s AbortController timeout on SSR fetch, graceful degradation to "connecting" page |
| 3 | `api.ts` | Differentiated timeouts: recommendations 15s/1 retry, stock 30s/1 retry, rankings 120s/0 retry. Backend wake check integrated |
| 4 | `StockDetailClient.tsx` | Removed redundant `wakeUpBackend()` call — `apiRequest` handles it internally. `useMemo` for cache hint |
| 5 | `RefreshAllButton.tsx` | SSE buffer handling with `lines.pop()` for incomplete chunks. `JSON.parse` wrapped in try-catch (fixed from CR4-C002). `router.refresh()` replaces `window.location.reload()` (fixed from CR4-m004) |
| 6 | `HomeContent.tsx` | `useMemo(watchlistKey)` prevents re-render cascade. `prefetchedRef` prevents duplicate prefetch. `useCallback(loadWatchlistStocks)` stable reference |
| 7 | `ProgressBar.tsx` | Logarithmic progress (500ms interval, max 95%). Clean and performant |
| 8 | `MarketHeader.tsx` | No changes from optimization; code is clean |

---

### API Compatibility Check

| Endpoint | Signature | Response Format | Result |
|----------|-----------|----------------|--------|
| GET /api/v1/stock/{code} | No change | No change | PASS |
| GET /api/v1/stocks/search | No change | No change | PASS |
| GET /api/v1/stocks/batch | No change | No change | PASS |
| POST /api/v1/stocks/prefetch | No change | No change | PASS |
| GET /api/v1/stock/{code}/kline | No change | No change | PASS |
| GET /api/v1/stock/{code}/ai-analysis | No change | No change | PASS |
| GET /api/v1/rankings/ai | No change | No change | PASS |
| POST /api/v1/refresh/all | No change | SSE format same, timing changed (see CR5-C002) | WARN |
| POST /api/v1/stock/{code}/chat | No change | No change | PASS |

### Import Completeness Check

| File | New Imports | Status |
|------|-----------|--------|
| `eastmoney_service.py` | `from app.http_client import get_client` | OK |
| `glm_service.py` | `from app.http_client import get_client` | OK |
| `ai_analysis_service.py` | `from cachetools import TTLCache`, `from app.http_client import get_client` | OK |
| `news_service.py` | `from app.http_client import get_client` | OK |
| `fundamental_service.py` | `from app.http_client import get_client` | OK |
| `chat_service.py` | `from app.http_client import get_client` | OK |
| `stock.py` | `from cachetools import TTLCache` | OK |
| `refresh.py` | `import asyncio` | OK |
| `main.py` | `from app.http_client import close_client` | OK |

### Parallel Safety Assessment

| Location | Pattern | Safe? | Notes |
|----------|---------|-------|-------|
| `stock.py:118-121` | `asyncio.gather(get_history, get_realtime)` | YES | Independent I/O operations |
| `stock.py:251-272` | `asyncio.gather(summary_task, ai_task)` | YES | Independent AI calls |
| `stock.py:381-416` | `Semaphore(5) + gather` for batch analysis | YES | Semaphore limits concurrent analysis |
| `stock.py:589-646` | `Semaphore(5) + gather` for AI rankings | YES | Semaphore limits concurrent analysis |
| `ai_analysis_service.py:430-433` | `gather(company, fundamental)` | YES | Independent AI calls |
| `refresh.py:96-117` | `Semaphore(3) + gather` for stock refresh | YES | asyncio single-threaded; `nonlocal completed_count` safe |
| `scheduler.py:103-119` | `Semaphore(3) + gather` for cache warm | YES | Same pattern as refresh |
| `comprehensive_analysis_service.py:35-48` | `create_task + gather` for 5 dimensions | YES | Independent data fetches |

### Cache Consistency Check

| Cache | Type | TTL | Max Size | Behavior |
|-------|------|-----|----------|----------|
| `_ai_analysis_cache` (ai_analysis_service) | TTLCache | 4 hours | 100 | Same-day same-stock reuse; auto-eviction |
| `_stock_analysis_cache` (stock.py) | TTLCache | 3 min | 200 | Per-stock per-ai_analysis key; auto-eviction |
| `_ai_rankings_cache` (stock.py) | TTLCache | 30 min | 1 | Single key "rankings"; auto-eviction |
| `stockCache` (api.ts frontend) | Map | 3 min (manual) | Unbounded | Manual TTL check; no eviction |

All TTLCache instances correctly replace previous `dict` caches with automatic expiration.

---

### Priority Fix List

1. **Immediate (Critical)**:
   - CR5-C001: Add `await` to 6 calls in `main.py` debug endpoint
   - CR5-C002: Decide on SSE progress strategy for parallel refresh

2. **Next Version (Major)**:
   - CR5-M001: Wrap chat_service sync DB calls
   - CR5-M002: Wrap cache_service sync DB calls
   - CR5-M003: Migrate to async Supabase client (long-term)

3. **When Available (Minor)**:
   - CR5-m001 ~ CR5-m004: Code quality details

---

### Review Verdict: CONDITIONALLY APPROVED

**Must fix before deployment**: CR5-C001 (debug endpoint missing await)

**Can defer**: CR5-C002 (SSE progress UX degradation — functional, just less responsive)

**Not blocking**: All Major and Minor issues

---

*QA Report generated by qa-guardian*
*Report Version: 5.0 (Performance Optimization Code Review)*
*Last Updated: 2026-02-10*
