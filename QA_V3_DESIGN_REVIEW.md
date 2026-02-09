# Stock Advisor v3.0 Design Review Report

## Review Information

- **Document Reviewed**: `DESIGN_V3_CACHE_AND_QA.md`
- **Reviewer**: qa-guardian
- **Review Date**: 2026-02-09
- **Review Type**: Design Phase Review (pre-development)
- **Review Status**: CONDITIONALLY APPROVED -- requires 4 issues to be resolved before development

---

## 1. Completeness Assessment

| Checklist Item | Status | Notes |
|----------------|--------|-------|
| Project objectives clear | PASS | Two clear objectives: intelligent caching + AI Q&A |
| Functional requirements complete and verifiable | PASS | Detailed API specs, data flow, UI mockups |
| Technology choices justified | PASS | Supabase for persistent cache (free tier), GLM-4 for Q&A -- both aligned with existing stack |
| Architecture includes module breakdown and data flow | PASS | 3-layer cache diagram, data flow per API clearly defined |
| Implementation plan has clear phases | PASS | 4 phases (A/B/C/D) with dependency mapping |
| Acceptance criteria measurable | PASS | Section 7 has concrete before/after metrics (e.g., 15-30s -> <1s) |
| Risk analysis present | PASS | Section 6 covers technical risks, constraints, UX tradeoffs |
| File change list included | PASS | Section 8 lists all new/modified files |

**Completeness Score: 8/8 -- All required sections present.**

---

## 2. Testing Strategy Assessment

| Checklist Item | Status | Notes |
|----------------|--------|-------|
| Test scope defined | PARTIAL | Phase D mentions E2E + performance tests but scope is vague |
| Test types planned | WARN | Only E2E and performance mentioned; no unit or integration test plan |
| Test environment requirements | MISSING | No local test environment setup described |
| Test data strategy | MISSING | No mention of test data fixtures, mock data for cache scenarios |
| Coverage targets | MISSING | No coverage goals defined |
| Test acceptance criteria | PARTIAL | Phase D says "E2E test" but no pass criteria |

**Testing Strategy Score: 2/6 -- Significant gaps.**

**Mandatory Improvement**: The design document must add a Testing Strategy section before development begins. Specifically:

1. Define unit tests for `cache_service.py` (cache hit/miss/expiry logic) and `chat_service.py` (prompt building, quota enforcement, similar question matching).
2. Define integration tests for Supabase cache read/write operations.
3. Define E2E test cases for each new API endpoint with expected response structures.
4. Specify how to test cache expiration logic without waiting real hours (time mocking strategy).
5. Specify test data: which stock codes, what cache states (empty, valid, expired, stale).

---

## 3. Design Quality Review (8-Dimension Framework Applied to Design)

### 3.1 Architecture Design: 4.5/5

**Strengths:**
- The 3-layer cache architecture (Memory -> Supabase -> Data Source) is a well-established pattern. The decision to put only 30-second realtime prices in memory and everything else in Supabase is the correct call given Render's 512MB limit and cold-start behavior.
- Decoupling "data fetch" from "data display" is the right principle. The `refresh=true/false` parameter gives users explicit control.
- The batch realtime API (`ulist.np`) is already proven in the codebase for market indices. Extending it to individual stocks is low-risk.
- The `cache_info` response field providing transparency to the frontend is a good design choice.

**Issues:**

| ID | Severity | Description |
|----|----------|-------------|
| DR-D001 | Major | **Cache warm job runs serially for all stocks.** Section 2.5.1 shows `for code in codes: await generate_and_cache_analysis(code)`. If there are 30 stocks (10 recommended + 20 watchlist), each taking 15-30s, the job will run 450-900 seconds (7.5-15 minutes). This overlaps with the 17:30 `daily_snapshot` job and potentially the 18:00 `evaluation_job`. The design should specify concurrency limits (e.g., `asyncio.Semaphore(3)`) and handle the overlap scenario. |
| DR-D002 | Minor | **No migration plan for existing `stock_cache` table.** Section 2.3.1 says the new `stock_analysis_cache` "replaces" the existing `stock_cache` table, but there is no migration step. What happens to existing data? When is the old table dropped? This should be explicit. |
| DR-D003 | Minor | **No cache invalidation on data source failure.** If the cache warm job partially fails (e.g., 5 of 30 stocks fail), those 5 stocks will serve stale data until the next day's warm job. The design should specify whether to mark failed entries or serve stale data with a warning. |

### 3.2 Functionality Design: 4/5

**Strengths:**
- The `/stock/{code}/quick` lightweight endpoint is a smart addition for list views.
- AI Q&A with pre-set question templates significantly lowers the barrier to entry.
- The 10-question-per-day limit is a pragmatic cost control measure.
- The similar question matching (keyword overlap > 70%) is simple and avoids introducing additional ML dependencies.

**Issues:**

| ID | Severity | Description |
|----|----------|-------------|
| DR-F001 | Major | **`is_cache_valid` for `realtime_quote` returns `True` unconditionally outside trading hours.** This means if the last known price was cached at 14:30 on Friday, and a user checks at 09:00 on Monday (before market open), they see Friday's 14:30 price with no staleness indicator because the function says "valid." The logic should check if the cache was generated during the most recent completed trading session. Furthermore, the function does not handle the scenario where the market opens at 09:30 -- between 09:00 and 09:30 on a trading day, should the previous day's close be considered "valid" or should the system indicate that fresh data will be available at 09:30? |
| DR-F002 | Major | **Holiday handling in cache validity is incomplete.** `is_trading_hours(now)` and `get_last_trading_day(now)` are referenced in the pseudo-code but neither is defined. The existing `TradingCalendarService` has `is_trading_day()` but not `is_trading_hours()`. The `_generate_simple_calendar()` fallback only excludes weekends, not Chinese national holidays (Spring Festival, National Day, etc.). A cache validity function that depends on an incomplete trading calendar will produce incorrect results during holiday periods -- data from before a week-long holiday would be served as "fresh." |
| DR-F003 | Minor | **AI Q&A `user_id` is `default_user` hardcoded.** The chat API accepts `user_id` in the request body, but the current system has no authentication. The 10-question-per-day limit can be trivially bypassed by changing the `user_id` string. This is acceptable for MVP but should be documented as a known limitation. |
| DR-F004 | Minor | **Similar question matching by keyword overlap is fragile.** "What is the company's latest earnings?" and "What were the latest earnings of the company?" have ~100% keyword overlap with different word order, which is fine. But "How is the stock doing?" and "Is the stock doing well?" may score below 70%. The design should acknowledge this limitation and state that false negatives (calling GLM when a cached answer exists) are acceptable since the cost is bounded by the daily quota. |
| DR-F005 | Nit | **The `risk` template is listed in the frontend quick questions (Section 3.6.1) but not defined in the backend prompt templates (Section 3.4.2).** The `build_chat_prompt` function handles `financial`, `news`, `comparison`, and `technical` -- but not `risk`. Either add the backend template or remove it from the frontend. |

### 3.3 Performance and Resource Design: 4/5

**Strengths:**
- Memory budget analysis is detailed and reasonable. Moving the cache to Supabase is the key insight.
- Token cost analysis shows the caching mechanism actually offsets the Q&A cost, resulting in near-zero net increase.
- Supabase storage estimate (<5MB/month) is well within the 500MB free tier.

**Issues:**

| ID | Severity | Description |
|----|----------|-------------|
| DR-P001 | Major | **Memory budget underestimates peak usage during cache warm.** Section 2.7 estimates 280MB total with a 40MB peak for the scheduler processing 20 stocks simultaneously. However, Section 2.5.1 shows serial processing, not parallel. If changed to parallel (to fix DR-D001), memory could spike. More importantly, the current `comprehensive_analysis_service.py` loads pandas DataFrames (~2MB each) and makes synchronous HTTP calls. With 3 concurrent analyses, peak could reach 80-100MB additional. The estimate should account for the actual implementation pattern, not just dictionary sizes. The stated "55% usage" has insufficient safety margin if the actual peak is higher. Recommend staying below 70% (360MB) with verified measurements post-implementation. |
| DR-P002 | Minor | **Supabase read latency not benchmarked.** The design assumes Supabase reads are "<1 second" but the free tier database is likely in a US region (or wherever Supabase provisioned it). If the backend is on Render (also US), latency should be low. But this assumption should be verified. If Supabase is slow, the entire "<1 second cache hit" promise breaks. |
| DR-P003 | Nit | **`stock_chat_history` has no cleanup strategy.** At 100 records/day, that is 36,500 records/year at ~36MB. Not a problem for the 500MB limit, but the table will grow indefinitely. Consider adding a retention policy (e.g., delete records older than 90 days) or mention this as future work. |

### 3.4 API Design: 4.5/5

**Strengths:**
- Backward-compatible changes to existing APIs (adding `refresh` parameter with `false` default).
- Clear separation between `/stock/{code}` (full analysis) and `/stock/{code}/quick` (lightweight).
- Batch quotes API (`/quotes/batch`) is a significant improvement over serial calls.
- Chat history API is simple and appropriate.

**Issues:**

| ID | Severity | Description |
|----|----------|-------------|
| DR-A001 | Minor | **`POST /cache/warm` has no authentication or rate limiting.** Anyone who discovers this endpoint can trigger expensive cache warming operations, causing heavy API calls to EastMoney and GLM-4. At minimum, this should have an API key or be restricted to internal scheduler calls only (not exposed as a public endpoint). |
| DR-A002 | Minor | **`GET /stock/{code}/quick` response does not include `change_percent`.** The response shows `"change": 2.35` but the field name is ambiguous -- is this percentage or absolute value? The existing API uses `change` for percentage. Ensure naming consistency and consider adding both `change_amount` and `change_percent` for clarity. |
| DR-A003 | Nit | **Chat API `POST /stock/{code}/chat` returns `remaining_quota` but does not specify the reset time.** The user sees "8/10 remaining" but does not know when the quota resets. Consider adding `quota_resets_at` or a human-readable message. |

### 3.5 Data Model Design: 4/5

**Strengths:**
- `stock_analysis_cache` as a single-row-per-stock upsert model is simple and effective.
- Separate timestamp columns for different data types (`quote_updated_at`, `ai_updated_at`, `full_analysis_updated_at`) allows fine-grained cache validity checks.
- `stock_kline_cache` with composite primary key `(code, trade_date)` is correct and efficient.

**Issues:**

| ID | Severity | Description |
|----|----------|-------------|
| DR-DB001 | Major | **`stock_analysis_cache` stores denormalized AI results as JSONB, but the cache validity check only uses `full_analysis_updated_at`.** The design shows AI results cached for 4 hours and K-line data cached for the full day. But the table has a single `full_analysis_updated_at` column that seems to represent the last complete analysis. If a user requests `refresh=true` and only the AI analysis needs refreshing (because K-line data is still valid from today), does the system re-fetch everything or only the AI portion? The design does not specify partial cache refresh. This could lead to unnecessary EastMoney API calls when only the AI cache has expired. |
| DR-DB002 | Minor | **`stock_kline_cache` will accumulate historical data indefinitely.** 50 stocks x 60 trading days = 3,000 rows initially. But as the system runs, older K-line data is never deleted. After a year: 50 stocks x 250 trading days = 12,500 rows. This is manageable but a cleanup strategy (drop data older than 90 trading days) should be mentioned. |
| DR-DB003 | Minor | **No index on `stock_chat_history.user_id` alone.** The composite index `idx_sch_code_user` covers `(code, user_id)`, but the daily quota check needs to query by `user_id` only (count today's questions for the user across all stocks). This query would not efficiently use the composite index. Add a separate index on `(user_id, created_at)`. |

---

## 4. Focused Risk Analysis (Per User Request)

### 4.1 Cache Consistency (Database Cache vs. Realtime Data)

**Risk Level: MEDIUM**

The design acknowledges this in Section 6.3 ("sacrifice some freshness for speed"). The mitigation (showing cache age in the UI, providing manual refresh) is appropriate.

**Unaddressed Scenarios:**
1. **Race condition during cache warm:** If a user requests `/stock/{code}?refresh=true` while the 17:10 cache warm job is processing the same stock, both will write to `stock_analysis_cache`. The last write wins, which is acceptable for an upsert, but the user may see briefly inconsistent data if the warm job's write overwrites their fresh request with slightly older data.
2. **Stale AI analysis after significant price movement:** If a stock gaps up 8% at market open, the 4-hour-old AI analysis from the previous evening may contain contradictory advice. The design should consider invalidating AI cache when price change exceeds a threshold (e.g., > 5% from cached price).

### 4.2 EastMoney Batch API Reliability

**Risk Level: LOW**

The `ulist.np` endpoint is already used in production for market indices (`get_market_indices()`). Extending it to individual stocks changes only the `secids` parameter, not the endpoint itself. The `fields` parameter selects the return columns.

**Residual Risks:**
1. The response format for individual stocks via `ulist.np` may differ slightly from the single-stock `qt/stock/get` endpoint (different field numbering or precision). This needs verification during implementation.
2. The batch endpoint may have an undocumented limit on the number of `secids`. Testing with 30+ stocks at once should be part of the implementation validation.
3. The design correctly mentions keeping "per-stock fallback" as a backup.

### 4.3 Render 512MB Memory Safety Margin

**Risk Level: MEDIUM-HIGH**

The design claims 55% usage (280MB/512MB), leaving a 45% margin. However:

| Component | Design Estimate | Realistic Estimate | Difference |
|-----------|----------------|-------------------|------------|
| Python base + FastAPI + libs | 175MB | 180-200MB | Could be higher with all imported services |
| pandas/numpy per stock | 2MB | 2-5MB (with intermediate copies) | DataFrame operations create temporary copies |
| Cache warm peak (20 stocks serial) | 40MB | 60-80MB (if any parallelism introduced) | Underestimated |
| Concurrent user requests | Not estimated | 20-50MB per concurrent request | Missing from analysis |
| **Total Realistic Peak** | **280MB** | **320-380MB** | **62-74% usage** |

At 74% usage, a single memory spike (e.g., a large DataFrame or garbage collection delay) could trigger OOM. **Recommendation:** Add memory monitoring (`psutil.Process().memory_info().rss`) with a circuit breaker that rejects new cache warm items if memory exceeds 400MB (78%).

### 4.4 AI Q&A Token Cost Control

**Risk Level: LOW**

The analysis is sound:
- Single Q&A: ~850 tokens at ~0.17 RMB
- Daily cap: 50 Q&A x 850 = 42,500 tokens (~8.5 RMB/day)
- Cache reduction offsets: saving ~40K tokens/day from reduced AI analysis calls
- Net impact: approximately neutral

**Minor Concern:** The design says GLM-4-flash pricing is "0.1 RMB per 1K tokens" for both input and output. This should be verified against the current zhipuai.cn pricing page, as LLM pricing changes frequently. If prices have increased, the cost model needs updating.

### 4.5 Cache Expiration Edge Cases (Trading/Non-Trading/Holiday)

**Risk Level: HIGH**

This is the most significant design gap. The `is_cache_valid` pseudo-code in Section 2.2.2 depends on three undefined functions:
- `is_trading_hours(now)` -- not implemented in the current codebase
- `get_last_trading_day(now)` -- not a method on the existing `TradingCalendarService`
- The existing `TradingCalendarService._generate_simple_calendar()` fallback does NOT handle Chinese national holidays

**Specific Failure Scenarios:**

| Scenario | Expected Behavior | Likely Actual Behavior | Impact |
|----------|-------------------|----------------------|--------|
| Spring Festival (7 days off) | Cache warm does not run; last trading day's data served with "X days old" notice | `is_trading_day()` returns False correctly if static calendar loaded; but `_generate_simple_calendar` fallback treats weekdays as trading days, so cache warm would run on holidays and fail (no market data) | Scheduler errors, no fresh cache |
| Market holiday (single day, e.g., Qingming) | Skip cache warm | Same as above -- depends on calendar file | May or may not work |
| Monday 09:00 (pre-market) | Show Friday's close, indicate "pre-market" | `is_trading_hours` undefined; `is_cache_valid` for realtime returns `True` (non-trading hours branch) | Appears correct price but no staleness indicator |
| Trading day 12:00 (lunch break) | Show last price from 11:30, valid | `is_trading_hours` would need to handle the lunch break 11:30-13:00 | If lunch break is not handled, cache may be considered "expired" during lunch |

**Mandatory Requirement:** Before implementing `is_cache_valid`, the following must be defined:
1. `is_trading_hours()` must handle: pre-market (before 09:30), morning session (09:30-11:30), lunch break (11:30-13:00), afternoon session (13:00-15:00), post-market (after 15:00).
2. `get_last_trading_day()` must be added to `TradingCalendarService`.
3. The static trading calendar file must be verified to contain 2026 data with correct Chinese holidays.
4. The fallback `_generate_simple_calendar` should be documented as a degraded mode that will cause cache warm failures on holidays.

### 4.6 Frontend User Experience (Cache vs. Realtime Perception)

**Risk Level: LOW**

The design handles this well:
- Clear visual distinction: gray badge for cached data, green for fresh
- "Price is realtime | Analysis is cached" text separation
- Manual refresh button with progress indicator
- Cache age displayed in human-readable format

**Minor Suggestion:** Consider adding a subtle pulsing animation to the "realtime" price during trading hours to reinforce that the price updates are live, even if the analysis section is cached.

---

## 5. Issues Summary

### Critical (0) -- None

### Major (5) -- Must resolve before development

| ID | Category | Summary | Recommendation |
|----|----------|---------|----------------|
| DR-D001 | Architecture | Cache warm job runs serially; 30 stocks = 7.5-15 min; overlaps with subsequent scheduler jobs | Add concurrency control (Semaphore), estimate total runtime, stagger scheduler times accordingly |
| DR-F001 | Functionality | Realtime quote cache returns "valid" unconditionally outside trading hours with no staleness indicator | Redesign to check if cache is from the most recent trading session; add pre-market/post-market states |
| DR-F002 | Functionality | `is_trading_hours()` and `get_last_trading_day()` are undefined; holiday handling incomplete | Define these functions explicitly; verify 2026 static calendar; document fallback behavior |
| DR-P001 | Performance | Memory budget underestimates peak; concurrent requests not accounted for | Re-estimate with concurrent request overhead; add memory circuit breaker at 400MB |
| DR-DB001 | Data Model | No partial cache refresh strategy; AI expiry (4h) forces full re-analysis including unnecessary K-line re-fetch | Define separate refresh paths: quote-only, AI-only, full-refresh |

### Minor (9)

| ID | Category | Summary |
|----|----------|---------|
| DR-D002 | Architecture | No migration plan for existing `stock_cache` table |
| DR-D003 | Architecture | No handling of partially failed cache warm (stale entries not marked) |
| DR-F003 | Functionality | `user_id` hardcoded; daily quota trivially bypassable |
| DR-F004 | Functionality | Keyword overlap matching has false negative risk (acknowledged as acceptable) |
| DR-A001 | API | `/cache/warm` endpoint has no authentication |
| DR-A002 | API | `/stock/{code}/quick` response field `change` is ambiguous |
| DR-P002 | Performance | Supabase read latency assumption not benchmarked |
| DR-DB002 | Data Model | `stock_kline_cache` has no cleanup/retention policy |
| DR-DB003 | Data Model | Missing index on `(user_id, created_at)` for daily quota check |

### Nit (3)

| ID | Category | Summary |
|----|----------|---------|
| DR-F005 | Functionality | `risk` template in frontend but not in backend prompt builder |
| DR-A003 | API | Chat quota response lacks reset time information |
| DR-P003 | Performance | `stock_chat_history` has no retention/cleanup policy |

---

## 6. Testing Strategy Gaps (Must Address Before Development)

The design document (Phase D) allocates only 2-3 hours for testing. Given the v2.0 QA report findings -- which identified an inverted test pyramid (0% unit tests, 0% integration tests, 100% E2E) -- v3.0 must not repeat this pattern.

**Required Test Plan Additions:**

| Test Type | Target Count | Priority | Scope |
|-----------|-------------|----------|-------|
| Unit Tests | 15-20 | P0 | `cache_service.py` (cache hit/miss/expiry for each data type, trading hours logic), `chat_service.py` (prompt building, quota check, similar question matching) |
| Integration Tests | 5-8 | P1 | Supabase cache CRUD operations, batch quote API parsing, cache warm + read sequence |
| E2E Tests | 8-10 | P0 | New endpoints: `/stock/{code}` with cache, `/stock/{code}/quick`, `/quotes/batch`, `/cache/warm`, `/stock/{code}/chat`, `/stock/{code}/chat/history`; Cache hit vs. miss behavior |
| Performance Tests | 3 | P2 | Cache hit response time < 1s, batch quote response time < 2s, memory usage during cache warm |

**Critical Testing Need:** Cache expiration logic must be testable with mocked time. The design should specify using `freezegun` or similar library to test cache validity across trading day boundaries without waiting real hours.

---

## 7. Positive Highlights

1. **Excellent problem diagnosis.** Section 1.1 provides exact timing breakdown per API call with code references. This level of precision demonstrates thorough understanding of the current system's bottlenecks.

2. **Pragmatic technology choices.** Using Supabase (already in the stack) for persistent caching rather than introducing Redis avoids additional infrastructure complexity and cost.

3. **Token cost modeling is rigorous.** The analysis showing that caching actually offsets Q&A costs is compelling and well-documented.

4. **Backward-compatible API changes.** Adding `refresh=false` as a default parameter to existing endpoints means existing frontend code continues to work without modification during incremental rollout.

5. **User experience transparency.** The `cache_info` response object and visual indicators (gray/green badges) give users control and understanding of data freshness.

6. **Phased implementation with clear dependencies.** The 4-phase plan with explicit dependency arrows (e.g., C7 depends on C6 and A5) allows for realistic scheduling.

7. **Batch API optimization is a significant win.** Replacing 10 serial HTTP calls with 1 batch call for the recommendations page is a 5-10x improvement that benefits all users immediately.

---

## 8. Review Verdict

### Score: 82/100

| Dimension | Score | Weight | Notes |
|-----------|-------|--------|-------|
| Completeness | 9/10 | High | All sections present; testing strategy weak |
| Technical Feasibility | 8/10 | High | Sound architecture; cache expiration edge cases need work |
| Risk Coverage | 7/10 | High | Good risk table but holiday/calendar gap is significant |
| Implementation Plan | 9/10 | Medium | Clear phases, dependencies, and time estimates |
| API Design | 9/10 | Medium | Clean, backward-compatible, well-documented |
| Data Model | 8/10 | Medium | Effective but needs partial refresh and cleanup policies |
| UX Consideration | 9/10 | Medium | Excellent transparency and user control |
| Testing Strategy | 5/10 | High | Minimal; must be expanded significantly |

### Decision: CONDITIONALLY APPROVED

**Conditions for approval (must resolve before development begins):**

1. **[MUST] Resolve DR-F001 + DR-F002:** Define `is_trading_hours()` and `get_last_trading_day()` with complete specifications covering pre-market, lunch break, post-market, weekends, and Chinese national holidays. Verify 2026 static trading calendar file exists and is correct.

2. **[MUST] Resolve DR-D001:** Specify the cache warm job's concurrency strategy and total estimated runtime. Adjust scheduler timing if overlap with `daily_snapshot` is likely.

3. **[MUST] Resolve DR-DB001:** Define partial cache refresh paths (quote-only vs. AI-only vs. full) to avoid unnecessary API calls.

4. **[MUST] Add Testing Strategy:** Expand Phase D to include unit tests for cache service and chat service, with mocked time for cache expiration testing.

**Recommended but non-blocking:**
- Address Minor issues DR-D002, DR-A001, DR-DB003 during implementation.
- Nit issues can be addressed at developer discretion.

---

## 9. Relationship to Existing v2.0 QA Issues

Several v2.0 QA issues from `QA_REPORT.md` are directly relevant to v3.0:

| v2.0 Issue | v3.0 Impact | Action Needed |
|------------|-------------|---------------|
| QA-F-001: No unit tests | v3.0 must not repeat this. Add unit tests for new services. | Include in v3.0 test plan |
| QA-F-002: Inverted test pyramid | v3.0 adds more E2E-only testing if not corrected | Require unit tests before E2E |
| CR4-M001: No timezone on scheduler | v3.0 adds a new scheduler job (cache_warm) that also needs `timezone='Asia/Shanghai'` | Carry forward to v3.0 implementation |
| CR4-M003: Uses `print()` for logging | New cache_service and chat_service should use proper logging from the start | Include as implementation requirement |
| QA-F-007: Token monitor not integrated | v3.0 chat service should call `token_monitor.log_usage()` | Include in chat_service design |

---

*Report generated by qa-guardian*
*Review version: 1.0*
*Date: 2026-02-09*
