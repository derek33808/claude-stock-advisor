# QA PRD Review Report - Stock Advisor PRD v2.0

| Field | Value |
|-------|-------|
| Document Reviewed | PRD_v2.0.md |
| Document Version | v2.0 (Final Draft) |
| Reviewer | QA Guardian |
| Review Date | 2026-02-09 |
| Review Status | Completed |

---

## 1. Review Summary

### 1.1 Overall Assessment

| Dimension | Score (out of 20) | Rating |
|-----------|-------------------|--------|
| Completeness | 17 | Excellent |
| Reasonableness | 15 | Good |
| Implementability | 14 | Good |
| Compliance | 18 | Excellent |
| User Experience | 16 | Very Good |
| Document Quality | 17 | Excellent |

**Total Score: 81 / 100**

**Overall Verdict: CONDITIONALLY APPROVED -- requires 4 Major issues to be resolved before entering architecture design phase.**

### 1.2 Issue Summary

| Severity | Count |
|----------|-------|
| Critical | 0 |
| Major | 4 |
| Minor | 8 |
| Nit | 5 |
| Total | 17 |

### 1.3 Key Findings

**Strengths:**
1. Exceptionally thorough document covering all major aspects of the product -- user personas, functional requirements, technical architecture, database design, API specifications, UI wireframes, compliance framework, and development roadmap.
2. The 5-dimensional AI analysis concept is well-defined with clear data sources for each dimension.
3. The compliance framework (Section 10) is comprehensive and demonstrates strong awareness of Chinese securities regulation -- one of the best aspects of this PRD.
4. Database design is detailed with proper indexing, views, and storage estimation.
5. API design includes complete request/response examples, error handling, and SSE for real-time progress.
6. Risk assessment (Appendix C) covers 10 risks with probability, impact, and mitigation -- thorough and realistic.

**Areas Requiring Attention:**
1. Device fingerprint authentication has significant reliability issues that are underestimated.
2. The curated hot stock list (60 stocks) for recommendations lacks a definition of how it is maintained and updated.
3. Several API data source integrations rely on undocumented/unofficial APIs with no contractual guarantees.
4. Testing strategy is completely absent from the PRD -- there is no section on test approach, test types, or quality assurance process.

---

## 2. Detailed Issue List

### 2.1 Major Issues (Must Fix Before Architecture Phase)

---

#### MAJOR-001: Missing Testing Strategy Section

**Location:** Entire document -- no Section 13 or equivalent for Testing Strategy

**Problem Description:**
The PRD contains 12 sections covering product, technical, and business aspects, but there is zero mention of a testing strategy. For a system that makes financial predictions and serves investment-related information, the absence of a testing plan is a significant gap. The document mentions "Comprehensive QA validation (launch qa-guardian)" as a single 1-day task in Phase 3 (line 2038), which is grossly insufficient.

**Impact:**
- Development team will lack guidance on what to test and how
- Critical financial calculation accuracy (technical indicators) may not be validated
- AI output quality may not be systematically evaluated
- Regression risks increase as the codebase grows from v1.0 to v2.0

**Recommended Fix:**
Add a new Section 13: Testing Strategy that includes:

```
13.1 Test Types and Coverage Targets
- Unit tests: All calculation services (indicator_service, composite_score), target > 80% coverage
- Integration tests: API endpoint tests with mock data sources
- AI Quality tests: GLM-4 output validation (format compliance, content quality scoring)
- E2E tests: Critical user flows (search -> analysis -> add watchlist -> refresh -> view history)
- Performance tests: Response time benchmarks per Section 12.3
- Compliance tests: Disclaimer presence, prohibited language absence

13.2 Test Data Strategy
- Define test stock codes for each scenario (main board, ChiNext, STAR, ETF, suspended, new listing)
- Define mock data for when external APIs are unavailable during testing

13.3 AI Output Validation
- Define acceptance criteria for GLM-4 responses (structure, length, language, recommendation format)
- Define fallback validation (template mode produces valid output)

13.4 Testing Schedule
- Unit tests: Continuous (every PR)
- Integration tests: End of each sprint
- E2E tests: End of each phase
- QA validation: Phase 3 (expanded from 1 day to 3 days)
```

**Severity:** Major -- testing strategy is a mandatory component for any production system, especially one involving financial data.

---

#### MAJOR-002: Device Fingerprint Authentication is Unreliable for Watchlist Persistence

**Location:** Section 4.4 (Feature 3: Watchlist Management), Section 7.2.1 (Watchlist Table), Appendix B (Technical Decision Log)

**Problem Description:**
The PRD acknowledges device fingerprint as the MVP authentication mechanism (Appendix B: "Good enough for MVP"), and Risk R9 acknowledges "Watchlist data loss (device fingerprint changes)" as Medium probability / Medium impact. However, the PRD does not adequately address the fact that:

1. Browser updates, private browsing mode, clearing cookies, and even minor OS updates can change device fingerprints.
2. The same user on mobile + desktop will have two separate watchlists with no way to merge.
3. The acceptance criterion "Watchlist persists across browser sessions (via device identifier stored in localStorage)" (line 400) conflates localStorage with device fingerprint -- these are different things. If the identifier is in localStorage, it can be cleared. If it is a fingerprint, it can change.
4. There is no recovery mechanism documented. If a user loses their watchlist, there is no way to retrieve it.

**Impact:**
- Users who build up watchlists and historical data may lose everything unexpectedly
- This directly undermines the core value of the Historical Review feature (Feature 5), which depends on persistent watchlist association
- User trust will be severely damaged, directly contradicting the product vision of building trust through prediction tracking

**Recommended Fix:**
1. Clarify exactly what "device fingerprint" means: is it a UUID generated and stored in localStorage, or is it a computed browser fingerprint? The PRD must be explicit.
2. If it is a localStorage UUID: Add a "Backup Code" feature where users can save/export a recovery code. Document this in the user flow.
3. Add an explicit user flow for "What happens when the device ID is lost" -- this is a P0 edge case for a P0 feature.
4. Consider a simple email-based recovery as a P1 item for v2.0 (not v2.1), given how critical watchlist persistence is to the prediction tracking value proposition.
5. Add a data export feature (CSV/JSON export of watchlist + history) as a P0 requirement.

**Severity:** Major -- directly impacts the core value proposition (prediction tracking requires persistent identity).

---

#### MAJOR-003: Curated Hot Stock List (60 Stocks) is Undefined

**Location:** Section 4.3 (Feature 2: Daily Smart Recommendations), line 335-336

**Problem Description:**
The recommendation pipeline Stage 1 states: "Universe Selection (~60 stocks from curated hot stock list)". However, the PRD does not define:

1. What is this "curated hot stock list"? Who curates it? How often is it updated?
2. What criteria determine inclusion in the list?
3. Is it a static list or dynamically generated?
4. Where is it stored? (Not in the database design.)
5. What happens when a stock in the list is delisted, suspended, or undergoes a name change?

This is a critical gap because the entire daily recommendation feature depends on this list as its starting universe. If the list is stale, the recommendations become meaningless.

**Impact:**
- Development team cannot implement the recommendation pipeline without knowing where the stock universe comes from
- If the list is static and manually maintained, it will become stale quickly
- If the list is dynamic, the criteria and data source must be specified

**Recommended Fix:**
Add a subsection under 4.3 defining the stock universe:

```
Hot Stock Universe Definition:
- Source: EastMoney sector hot stock lists + AKShare industry leaders
- Size: 50-80 stocks, refreshed weekly
- Inclusion criteria:
  - Market cap > 5B RMB
  - Average daily turnover > 100M RMB (past 20 days)
  - Not ST, not suspended, listed > 1 year
  - Distributed across at least 5 industries
- Storage: `hot_stock_universe` table in Supabase
- Update mechanism: Weekly automated refresh + manual override capability
- Fallback: If the universe refresh fails, use last known good list
```

Also add a corresponding database table definition in Section 7.2.

**Severity:** Major -- blocks implementation of a P0 feature.

---

#### MAJOR-004: No API Rate Limiting Design for External Data Sources

**Location:** Section 5 (Technical Architecture), Section 6 (Data Strategy)

**Problem Description:**
The PRD mentions request throttling in Risk R1 mitigation ("Request throttling max 10/sec") and "Rate limiting middleware (slowapi)" in Phase 0 tasks, but there is no systematic rate limiting design for the multiple external data sources used. Specifically:

1. Feature 1 (Comprehensive Analysis) requires 10+ sequential external API calls per stock (lines 731-741). For Global Refresh of 20 stocks, that is 200+ external API calls within 2 minutes.
2. The Global Refresh feature allows 3 concurrent stock analyses (line 415). Each analysis makes 10+ calls. That means 30+ concurrent external API calls.
3. EastMoney APIs have no documented rate limits (they are unofficial). AKShare wraps multiple sources with unknown limits.
4. There is no request queuing, backoff strategy, or circuit breaker pattern documented.
5. The Daily Recommendation generation processes 60 stocks in Stage 1-2 (data fetch + indicators), then 10 stocks with full analysis. The total external API call volume for a single recommendation run is not estimated.

**Impact:**
- IP blocking from EastMoney (Risk R1) becomes much more likely than "Medium" probability
- Global Refresh could trigger rate limiting from multiple data sources simultaneously
- Users may experience cascading failures during peak usage
- The 2-minute target for Global Refresh (20 stocks) may be unreachable if rate limiting kicks in

**Recommended Fix:**
Add a Section 5.7: Rate Limiting and Backpressure Strategy:

```
5.7.1 External API Call Budget
- EastMoney: max 5 requests/second (conservative)
- AKShare: max 3 requests/second per function
- GLM-4: per API quota (document current quota)
- Yahoo Finance: max 2 requests/second

5.7.2 Request Queue Architecture
- Implement a centralized request queue per data source
- Priority levels: user-initiated (high) > refresh (medium) > scheduled (low)
- Backoff strategy: exponential backoff with jitter on 429/rate limit responses
- Circuit breaker: if a source returns 5+ errors in 60 seconds, open circuit for 5 minutes

5.7.3 Global Refresh Rate Optimization
- Sequential stock processing with parallel dimension fetching within each stock
- Estimated call volume: 20 stocks x 10 calls = 200 calls over 2 minutes = ~1.7 calls/second (safe)
- If rate limited: reduce concurrency from 3 to 1, extend timeout
```

**Severity:** Major -- architectural gap that could cause the system to be blocked by data providers.

---

### 2.2 Minor Issues (Should Fix, Non-Blocking)

---

#### MINOR-001: Inconsistent Recommendation Language in PRD

**Location:** Section 4.2 (line 300), Section 10.4 (line 1914-1923)

**Problem Description:**
Section 4.2 defines the AI output as including: "Provides a clear recommendation: Strong Buy / Buy / Hold / Reduce / Avoid" (line 300). However, Section 10.4 (Language Guidelines) explicitly prohibits the use of language like "buy recommendation" and requires using terms like "technical signal" and "reference information" instead.

Additionally, the API response example (line 1234) uses `"overall_recommendation": "buy"` and the trading suggestion uses `"action": "buy"`. These directly conflict with the compliance framework.

**Recommended Fix:**
Align the terminology throughout the document. Replace:
- "recommendation" with "signal" or "analysis result"
- "Strong Buy / Buy / Hold / Reduce / Avoid" with "Strong Positive Signal / Positive Signal / Neutral / Cautious Signal / Negative Signal"
- API field name `overall_recommendation` with `overall_signal` or `analysis_conclusion`
- API field name `suggestion_action` with `signal_type`

---

#### MINOR-002: Prediction Accuracy Target of >55% Needs Statistical Context

**Location:** Section 1.5 (Key Metrics), Section 12.4

**Problem Description:**
The PRD sets a target of >55% direction accuracy at 30 days and >60% at 90 days. However:
1. No statistical significance testing is mentioned. With 10 recommendations/day for 30 days, we have ~200 evaluated predictions after 35 days. At n=200, the 95% confidence interval for a true 50% rate is approximately 43%-57%. A measured 55% could easily be within the confidence interval of random chance.
2. No benchmark comparison is defined. What is the baseline accuracy of random selection? Of simple moving average strategies?
3. The "Improvement Suggestions" feature (Section 4.6, line 517-523) references "over-optimistic on tech stocks" and similar insights, but the sample size for per-sector accuracy will be extremely small in the early days.

**Recommended Fix:**
1. Add a note that accuracy metrics are only meaningful after a minimum of 100 evaluated predictions per stock or 500 total evaluations.
2. Define a baseline comparison: "Direction accuracy must exceed 50% + 2 standard deviations given sample size."
3. Add a minimum sample size threshold before displaying accuracy statistics to users (e.g., "Accuracy stats shown only after 20+ evaluated predictions").

---

#### MINOR-003: "Trading Day" Definition Missing

**Location:** Section 4.3 (line 359), Section 4.6

**Problem Description:**
The PRD references "trading days" extensively but does not define:
1. How the system determines if a given day is a trading day (Chinese market has unique holidays, half-days, and makeup trading days).
2. Where the trading calendar data comes from.
3. How the "5 trading days later" evaluation date is calculated -- this requires an accurate trading calendar.

**Recommended Fix:**
Add to Section 6 (Data Strategy):
- Trading calendar source: AKShare `tool_trade_date_hist_sina()` or maintain a static calendar updated annually
- Define handling for: Chinese holidays (Spring Festival, National Day, Qingming, etc.), makeup Saturday trading days, and unexpected market closures

---

#### MINOR-004: Storage Estimation Underestimates Growth

**Location:** Section 7.4

**Problem Description:**
The storage estimation assumes 30 rows/day for analysis_history (10 recs + 20 watchlist). However:
1. If the product reaches 500 DAU at 90 days (per Section 1.5) with 8 watchlist stocks each, the watchlist snapshots alone would be 4,000/day, not 20.
2. The estimation does not account for multiple users having the same stock, meaning the same stock may have multiple watchlist-source snapshots.
3. At 4,000 rows/day x 5KB = 20MB/day = 600MB/month, which would exceed the Supabase 500MB free tier within a month of reaching the 90-day DAU target.

**Recommended Fix:**
1. Revise storage estimation with growth projections tied to DAU targets.
2. Add a data archival strategy: snapshots older than 90 days are archived or aggregated.
3. Plan for Supabase paid tier upgrade or self-hosted PostgreSQL at the 500 DAU milestone.
4. Consider storing one snapshot per stock per day (not per user per stock per day) and linking watchlist entries to a shared snapshot.

---

#### MINOR-005: No Monitoring/Alerting Strategy

**Location:** Entire document

**Problem Description:**
The PRD defines token monitoring but has no broader system monitoring strategy:
1. No health check endpoint defined in Section 8 API Design
2. No uptime monitoring plan despite "99% uptime during market hours" target (Section 12.4)
3. No error alerting mechanism (how does the team know when things break?)
4. No logging strategy beyond token usage logging

**Recommended Fix:**
Add a Section 5.8: Monitoring and Alerting:
- `/health` endpoint returning service status
- External uptime monitor (e.g., UptimeRobot, free tier)
- Error notification channel (e.g., email/Slack alert on 5xx error rate > 5%)
- Structured logging format for all services
- Dashboard for key metrics (DAU, API response times, error rates)

---

#### MINOR-006: Concurrent Watchlist Modification Race Condition

**Location:** Section 4.4, Section 7.2.1, Section 8.2.6-8.2.7

**Problem Description:**
The watchlist uses a UNIQUE(device_id, code) constraint, but the PRD does not address:
1. What happens if a user clicks "Add to Watchlist" twice quickly (race condition on POST /watchlist/add)
2. What happens if a global refresh is running while the user removes a stock from the watchlist
3. The Global Refresh processes stocks from both recommendations and watchlist -- if the watchlist changes mid-refresh, is the behavior defined?

**Recommended Fix:**
Add a note in the API design about idempotency:
- POST /watchlist/add should be idempotent (return 200 if already exists instead of 409, or handle gracefully on the frontend)
- Global Refresh should snapshot the stock list at the start and process that snapshot, ignoring mid-refresh changes
- Add optimistic locking or version field to watchlist entries

---

#### MINOR-007: ETF Handling is Underspecified

**Location:** Section 4.2 (line 312, 325)

**Problem Description:**
The PRD mentions ETF support in the acceptance criteria (line 312: "Accepts any valid A-share code (SH/SZ main board, SME, ChiNext, STAR, ETFs)") and edge cases (line 325: "ETF: Technical analysis and basic info available"). However:
1. ETFs do not have earnings reports, PE ratios, ROE, or most fundamental metrics. The fundamental_analysis section of the response would be mostly empty.
2. ETFs do not have a single industry classification. The industry_analysis section may not apply.
3. The recommendation pipeline (Feature 2) includes ETFs in the universe but the scoring algorithm uses fundamental metrics that ETFs lack.
4. The API response schema (Section 8.2.1) does not define which fields are nullable for ETFs.

**Recommended Fix:**
1. Define a separate response template for ETFs that replaces fundamental_analysis with fund-level data (NAV, tracking error, AUM, top holdings).
2. Replace industry_analysis with sector exposure analysis for ETFs.
3. Clarify whether ETFs are included in or excluded from the daily recommendation universe.
4. Mark nullable fields in the API response schema.

---

#### MINOR-008: Phase 0 Duration May Be Insufficient

**Location:** Section 11.2

**Problem Description:**
Phase 0 (Stabilization) is allocated 1 week and includes 10 tasks ranging from "10 min" to "1 day". The total effort sums to approximately 3.5-4 workdays. However:
1. "Add unit tests for indicator calculations" (estimated 1 day) is likely underestimated given the number of indicators (MACD, RSI, KDJ, BOLL, MA, ATR, Volume Ratio).
2. "Set up GitHub Actions CI" includes both lint and test pipelines, which typically takes more than 0.5 day for a Next.js + Python monorepo.
3. There is no buffer for unexpected issues during stabilization.

**Recommended Fix:**
Either extend Phase 0 to 1.5 weeks, or reduce scope by moving CI setup to Phase 1 Sprint 1 (can run in parallel with new development).

---

### 2.3 Nit Issues (Optional Improvements)

---

#### NIT-001: Inconsistent Terminology -- "Stock Code" vs "Code"

Throughout the document, the stock identifier is variously called "stock code", "code", "A-share code", and "6-digit number". The API uses `code` as the parameter name but some descriptions say "stock code".

**Recommendation:** Standardize on "stock code" in prose and `code` in API parameters. Add to Appendix A glossary.

---

#### NIT-002: Missing "Sort by" Options for Recommendation List

Section 9.2 shows the Recommendations tab but does not offer sort options. The Watchlist tab (Section 9.3) has sort by [Most Recent] [Score] [Change%], but recommendations do not. Users may want to sort the 10 recommendations by score, sector, or risk level.

**Recommendation:** Add sort options to the Recommendations tab or note that the default sort (by score descending) is the only option.

---

#### NIT-003: API Versioning Mentioned But Not Enforced

The API base URL includes `/api/v1` (line 1086), which implies version support, but there is no discussion of API versioning strategy, backward compatibility, or deprecation policy.

**Recommendation:** Add a brief note: "API version v1 is the launch version. No backward-compatible guarantees during beta. Version bumps will be communicated to frontend via forced update mechanism."

---

#### NIT-004: Appendix B Missing Entry for Database Choice

The Technical Decision Log (Appendix B) does not include the decision to continue with Supabase PostgreSQL, despite the significant new storage requirements. Given the storage concern in MINOR-004, this decision should be explicitly documented with alternatives considered (e.g., Neon, PlanetScale, self-hosted).

---

#### NIT-005: Section 9.8 Breakpoint Values May Not Match Tailwind Defaults

The responsive breakpoints (line 1830-1835) use 375px, 767px, 768px, 1023px, 1024px. Tailwind CSS default breakpoints are sm:640px, md:768px, lg:1024px. The PRD should either align with Tailwind defaults or note that custom breakpoints will be configured.

**Recommendation:** Align with Tailwind defaults or add a note about custom breakpoint configuration in tailwind.config.js.

---

## 3. Completeness Checklist

### 3.1 Functional Requirements Completeness

| Requirement | Defined | Clear | Testable | Notes |
|-------------|---------|-------|----------|-------|
| AI Comprehensive Analysis (5 dimensions) | YES | YES | YES | Well-defined with acceptance criteria |
| Daily Smart Recommendations | YES | PARTIAL | YES | Missing hot stock universe definition (MAJOR-003) |
| Watchlist Management | YES | YES | YES | Auth concern (MAJOR-002) |
| Global Refresh | YES | YES | YES | Rate limiting concern (MAJOR-004) |
| Historical Review + Prediction Tracking | YES | YES | YES | Good detail |
| Token Monitoring | YES | YES | YES | Good detail |
| Edge Cases | YES | YES | PARTIAL | ETF handling underspecified (MINOR-007) |
| Error Handling | YES | YES | YES | Section 5.6 covers all failure modes |

### 3.2 Technical Architecture Completeness

| Component | Defined | Notes |
|-----------|---------|-------|
| Architecture Overview | YES | Clear diagram with all layers |
| Technology Stack | YES | With justification for each choice |
| Service Layer | YES | 7 new services well-defined |
| AI Integration | YES | Prompt structure, token budget, cost control |
| Caching Strategy | YES | Per data type with TTL |
| Error Handling | YES | Per failure mode |
| Rate Limiting | NO | Missing (MAJOR-004) |
| Monitoring | NO | Missing (MINOR-005) |
| Testing | NO | Missing (MAJOR-001) |

### 3.3 Database Design Completeness

| Aspect | Covered | Notes |
|--------|---------|-------|
| Table Definitions | YES | 6 new tables with complete DDL |
| Indexes | YES | Appropriate indexes on query patterns |
| Views | YES | Aggregation views for token usage and accuracy |
| Migration Plan | YES | Simple 4-step plan with rollback |
| Storage Estimation | PARTIAL | Underestimates growth (MINOR-004) |
| Data Archival | NO | No archival strategy |
| Backup/Recovery | NO | Relies on Supabase default |

### 3.4 API Design Completeness

| Aspect | Covered | Notes |
|--------|---------|-------|
| Endpoint List | YES | 16 endpoints with methods and descriptions |
| Request/Response Specs | YES | Complete JSON examples for all new endpoints |
| Error Responses | YES | Status codes and error bodies defined |
| Authentication | PARTIAL | Device ID via header, but mechanism underspecified |
| Rate Limiting | NO | No client-facing rate limit headers |
| Pagination | NO | History endpoint may need pagination for large datasets |
| CORS | NO | Not mentioned, but required for Netlify -> Render |

### 3.5 Development Roadmap Completeness

| Aspect | Covered | Notes |
|--------|---------|-------|
| Phase Definition | YES | 4 phases over 7 weeks |
| Sprint-level Tasks | YES | Individual tasks with effort estimates |
| Dependencies | YES | Task dependencies noted |
| Exit Criteria | YES | Per phase |
| Milestones | YES | 4 milestones with success criteria |
| Resource Allocation | NO | Assumes single developer? Not stated. |
| Buffer/Contingency | NO | No slack in timeline |

---

## 4. Reasonableness Assessment

### 4.1 Technical Choices

| Choice | Assessment | Concern |
|--------|-----------|---------|
| Next.js 15 + React 18 | Reasonable | Existing stack, good for the use case |
| FastAPI + Python 3.11 | Reasonable | Good for data processing and AI integration |
| Supabase PostgreSQL | Reasonable for MVP | Storage growth concern at scale (MINOR-004) |
| GLM-4 (Zhipu AI) | Reasonable | Chinese language support, cost-effective |
| EastMoney (undocumented API) | Risky | No SLA, no documentation, could break anytime |
| AKShare | Reasonable | Popular open-source library, active maintenance |
| SSE for Global Refresh | Good | Simpler than WebSocket, fits the use case |
| Device fingerprint for auth | Risky for MVP | Acceptable short-term but undermines prediction tracking value |

### 4.2 Time Estimates

| Phase | Estimated | Assessment |
|-------|-----------|-----------|
| Phase 0: Stabilization | 1 week | Tight -- may need 1.5 weeks (MINOR-008) |
| Phase 1: Core Features | 3 weeks | Aggressive but achievable for experienced developer |
| Phase 2: History/Tracking | 2 weeks | Reasonable |
| Phase 3: Polish/Launch | 1 week | Tight -- QA needs more than 1 day |
| Total: 7 weeks | | Should budget 8-9 weeks with buffer |

### 4.3 Token Cost Analysis

| Metric | PRD Estimate | Assessment |
|--------|-------------|-----------|
| Tokens per analysis | ~2,800 | Reasonable, may be slightly low (news items can be verbose) |
| Daily total | ~224,000 | Reasonable for initial usage |
| Daily budget | 500,000 | Provides 2.2x headroom -- good |
| GLM-4 cost | Not stated | The PRD should state the current price per token and monthly cost estimate |

**Missing:** The PRD does not state the actual monetary cost of 500,000 tokens/day on GLM-4, or the monthly budget. This should be added for budget planning.

---

## 5. Compliance Assessment

### 5.1 Regulatory Compliance

| Requirement | Status | Notes |
|-------------|--------|-------|
| No "investment advice" claims | PARTIAL | Section 10 is excellent but Section 4.2 uses "recommendation" language (MINOR-001) |
| Disclaimers on every page | YES | Three types of disclaimers defined |
| No guaranteed returns | YES | Explicitly prohibited |
| No advisory license claims | YES | Explicitly stated |
| Prediction tracking disclaimers | YES | Specific disclaimer for accuracy pages |
| Sample size shown with accuracy | YES | Required in Section 10.5 |
| Language guidelines | YES | Comprehensive do/don't table |

### 5.2 Compliance Risk

The PRD does a very good job on compliance overall. The main risk is the inconsistency between Section 10 (compliance framework) and other sections that use terms like "recommendation", "buy", "Strong Buy" which could be interpreted as investment advice. This needs alignment (MINOR-001).

---

## 6. Improvement Recommendations

### 6.1 Must-Fix Items (Blocking Architecture Phase)

| ID | Issue | Owner | Priority |
|----|-------|-------|----------|
| MAJOR-001 | Add Testing Strategy section | PM | P0 |
| MAJOR-002 | Clarify and strengthen device identity + recovery | PM | P0 |
| MAJOR-003 | Define curated hot stock list source and maintenance | PM | P0 |
| MAJOR-004 | Add rate limiting and backpressure design | PM + Architect | P0 |

### 6.2 Should-Fix Items (Before Development Starts)

| ID | Issue | Owner | Priority |
|----|-------|-------|----------|
| MINOR-001 | Align compliance language throughout document | PM | P1 |
| MINOR-002 | Add statistical context for accuracy targets | PM | P1 |
| MINOR-003 | Define trading calendar source and handling | PM | P1 |
| MINOR-004 | Revise storage estimation with growth model | PM + Architect | P1 |
| MINOR-005 | Add monitoring and alerting strategy | Architect | P1 |
| MINOR-006 | Address concurrent modification scenarios | Architect | P1 |
| MINOR-007 | Define ETF-specific response handling | PM | P1 |
| MINOR-008 | Review Phase 0 duration estimate | PM | P2 |

### 6.3 Items Requiring Clarification

| Question | Section | Why It Matters |
|----------|---------|---------------|
| Is the team one developer or multiple? | Section 11 | Affects timeline feasibility |
| What is the actual GLM-4 monetary cost per day? | Section 5.4 | Budget planning |
| Does the existing v1.0 backend stay running during v2.0 development? | Section 11.2 | Deployment strategy |
| How will the v2.0 migration be handled for existing users? | Section 7.3 | User experience continuity |
| Is CORS already configured between Netlify and Render? | Section 5 | Could be a blocking issue |

### 6.4 Items to Add

| Item | Reason |
|------|--------|
| Section 13: Testing Strategy | Mandatory for quality assurance |
| Section 5.7: Rate Limiting Design | Prevents data source blocking |
| Section 5.8: Monitoring Strategy | Required for production readiness |
| Subsection 6.7: Trading Calendar | Required for prediction evaluation |
| Subsection 4.3.x: Hot Stock Universe Definition | Required for recommendation pipeline |
| API: /health endpoint | Required for monitoring |
| API: Pagination for history endpoint | Required for long-term data access |
| GLM-4 monetary cost estimate | Required for budget planning |

---

## 7. Review Conclusion

### 7.1 Verdict: CONDITIONALLY APPROVED

The PRD v2.0 is a well-crafted, comprehensive document that demonstrates strong product thinking and thorough technical planning. The 5-dimensional AI analysis concept is innovative and well-specified. The compliance framework is notably strong. The database design, API specifications, and UI wireframes provide sufficient detail for development to begin.

However, **4 Major issues must be resolved** before proceeding to the architecture design phase:

1. **MAJOR-001**: A testing strategy must be added -- this is non-negotiable for a financial information system.
2. **MAJOR-002**: The device identity mechanism must be clarified and strengthened -- the prediction tracking value proposition depends on persistent identity.
3. **MAJOR-003**: The hot stock universe must be defined -- the recommendation pipeline cannot be implemented without it.
4. **MAJOR-004**: Rate limiting design must be added -- without it, the system risks being blocked by data providers.

### 7.2 Next Steps

| Step | Owner | Deadline |
|------|-------|----------|
| 1. PM resolves 4 Major issues | PM (Product Orchestrator) | Before architecture design starts |
| 2. PM addresses Minor issues (at least MINOR-001 through MINOR-005) | PM | Before development starts |
| 3. QA re-reviews updated PRD sections | QA Guardian | After PM fixes |
| 4. Architecture design begins | Architect | After QA approval |

### 7.3 Quality Gate Status

| Gate | Status |
|------|--------|
| PRD Completeness | CONDITIONAL PASS -- 4 sections need addition |
| PRD Correctness | PASS -- no factual errors found |
| PRD Feasibility | CONDITIONAL PASS -- rate limiting design needed |
| PRD Compliance | PASS -- strong compliance framework with minor language alignment needed |
| PRD Testability | FAIL -- no testing strategy defined |

**When all 4 Major issues are resolved, QA will re-review and issue final approval to proceed to architecture design.**

---

*Report generated by: QA Guardian*
*Review methodology: 6-dimensional PRD review framework (Completeness, Reasonableness, Implementability, Compliance, User Experience, Document Quality)*
*Review duration: Full document review (2185 lines)*

---

## 8. Re-Review After Fixes (2026-02-09)

### 8.1 Fix Verification

---

#### MAJOR-001 Fix: PASS

**New Section**: Section 13 - Testing Strategy (lines 2451-2685, approximately 235 lines)

**Assessment**: The PM has added an exceptionally comprehensive testing strategy that significantly exceeds the minimum recommendation from the original review. Specifically:

- **13.1 Test Types and Coverage Targets**: Defines 6 test types (Unit, Integration, AI Quality, E2E, Performance, Compliance) with specific coverage targets, execution frequency, and tooling. This is well-structured and actionable.
- **13.2 Unit Test Requirements**: Lists 9 priority services with individual coverage targets (75%-90%). Includes specific critical test cases for indicator calculations with known datasets and tolerance levels (0.1%). This level of detail allows developers to write tests without ambiguity.
- **13.3 Integration Test Requirements**: Covers all 16 API endpoints with multiple test scenarios per endpoint (happy path, error cases, edge cases). Defines mock data strategy using `pytest fixtures` + `respx`. Well done.
- **13.4 AI Output Validation**: Distinguishes between structural validation (automated, every call) and content quality scoring (weekly sampling). The quality rubric with 5 dimensions and minimum scores is a strong approach for LLM output evaluation.
- **13.5 E2E Test Scenarios**: Defines 5 concrete Playwright test scenarios covering the critical user journeys. E2E-005 (Device Identity Recovery) directly validates the MAJOR-002 fix.
- **13.6 Test Data Strategy**: Defines 7 standard test stocks covering all market types (SH main board, SZ main board, ChiNext, STAR, ETF) plus scenario-specific test setups. Mock data directory structure is specified.
- **13.7 Performance Test Plan**: Covers 6 performance scenarios with specific targets and measurement methods.
- **13.8 Compliance Test Automation**: 4 automated compliance checks integrated into CI pipeline -- this is exactly what a financial information system needs.
- **13.9 Testing Schedule**: Phase-by-phase test activities with clear time allocation. QA Guardian engagement points are well-defined at 4 checkpoints. Notably, Phase 3 QA expanded from 1 day to 3 days as originally recommended.

**Verdict**: This is one of the most thorough testing strategies I have seen in a PRD. It addresses every concern raised in the original MAJOR-001 finding and goes well beyond the minimum recommendation. PASS.

---

#### MAJOR-002 Fix: PASS

**New Section**: Section 4.4.1 - Device Identity Mechanism (lines 453-532, approximately 80 lines)

**Assessment**: The PM has thoroughly addressed the device identity concern:

1. **Clarification of mechanism**: The PRD now explicitly states the identifier is a "locally-generated UUID v4", NOT a computed browser fingerprint. This was the primary source of confusion in the original review. The distinction is clearly explained with a "What This Means" section that covers all implications (localStorage clearing, cross-device behavior, incognito mode).

2. **Backup Code System [P0]**: A complete backup/recovery system is defined including:
   - First-visit backup code display dialog
   - Settings page with persistent "Copy" button for the current device ID
   - Recovery flow via backup code entry
   - JSON export/import of watchlist data

3. **User flow for data loss**: A clear step-by-step recovery flow is documented covering three scenarios: backup code recovery, JSON import recovery, and manual rebuild.

4. **API endpoints**: Three new endpoints (`/device/validate`, `/device/export`, `/device/import`) are defined for the recovery mechanism.

5. **Export format**: The JSON export schema is specified with a concrete example.

6. **Future enhancement**: Email-based account linking noted for v2.1 as a permanent solution.

7. **Updated acceptance criteria**: The acceptance criteria now include 9 items covering backup code display, recovery flow, export/import functionality, and backward compatibility.

**Minor Residual Issues** (non-blocking):
- Line 669 still says "device fingerprint sufficient" in the deferred features table -- should be updated to "device UUID" for consistency with Section 4.4.1.
- Line 1146 in the database DDL has comment `-- Device fingerprint (MVP auth)` -- should be `-- Device UUID (MVP auth)`.
- Line 2707 in Appendix B still says "Device fingerprint" -- should be "Device UUID/localStorage".
- Line 2725 (Risk R9) still says "device fingerprint changes" -- should be updated given the mechanism is now a UUID.

These are terminology consistency nits, not functional issues. The mechanism itself is well-designed and addresses the original concern. PASS.

---

#### MAJOR-003 Fix: PASS

**New Section**: Section 4.3.1 - Hot Stock Universe Definition (lines 334-395, approximately 62 lines)

**Assessment**: The PM has provided a complete and implementable definition:

1. **Universe composition**: Target size (50-80 stocks), data sources (EastMoney sector hot lists + AKShare industry leaders + top traded stocks by turnover) are clearly specified.

2. **Inclusion criteria**: 5 specific, measurable criteria in a well-formatted table -- market cap (>5B RMB), daily turnover (>100M RMB 20-day avg), listing age (>1 year), ST/suspension status, and industry diversification (>=5 sectors). Each criterion includes a rationale. This is directly implementable.

3. **Exclusion rules**: Explicitly listed (ST, suspended, <1 year, low liquidity, B-shares).

4. **Database schema**: A complete `hot_stock_universe` table DDL is provided with appropriate fields (code, name, industry, market_cap, avg_turnover, listing_date, added_at, last_validated_at, is_active, removal_reason) and proper indexes.

5. **Update mechanism**: Weekly refresh on Monday 09:00, 5-step update process, manual override capability, fallback to last known good list, and change logging for audit trail.

6. **Initial seeding strategy**: Practical approach -- top 10 stocks from 6 key sectors, validated against inclusion criteria, manually reviewed.

7. **Pipeline reference**: Line 395 updates the pipeline Stage 1 to explicitly reference the `hot_stock_universe` table.

**Minor Residual Issue** (non-blocking):
- The `hot_stock_universe` table DDL is defined in Section 4.3.1 but is NOT repeated in Section 7.2 (Database Design). The formal database schema section (7.2) lists tables 7.2.1 through 7.2.7 but does not include `hot_stock_universe`. This should be added as Section 7.2.8 or referenced with a cross-link to Section 4.3.1 for completeness.

Despite this minor cross-referencing gap, the definition itself is complete and fully implementable. PASS.

---

#### MAJOR-004 Fix: PASS

**New Section**: Section 5.7 - Rate Limiting and Backpressure Strategy (lines 842-1025, approximately 184 lines)

**Assessment**: This is the most extensive fix of the four, and the PM has delivered an architecturally sound design:

1. **External API Call Budget (5.7.1)**: Conservative rate limits per data source in a clear table format -- EastMoney quotes (5 req/s), EastMoney news (3 req/s), AKShare (3 req/s), GLM-4 (~60 RPM), Yahoo Finance (2 req/s). Includes burst limits and notes on each source. This gives the development team concrete numbers to implement.

2. **Request Queue Architecture (5.7.2)**: Centralized queue per data source using `asyncio.Semaphore` with a clear architecture diagram showing the routing pattern. Three priority levels (HIGH/MEDIUM/LOW) with clear examples for each. The conceptual Python implementation (`DataSourceRateLimiter` class) provides a good starting point.

3. **Backoff and Retry Strategy (5.7.3)**: Well-structured table mapping HTTP response codes to specific actions -- 429 (exponential backoff), 403 (switch to fallback, 5-min cooldown), 5xx (single retry), timeout (single retry), invalid data (no retry, use cache). Exponential backoff formula is explicitly defined (2^attempt + jitter, max 3 retries).

4. **Circuit Breaker Pattern (5.7.4)**: Three-state circuit breaker (CLOSED/OPEN/HALF-OPEN) with per-source configuration. Error thresholds (5 errors/60s for most, 3/60s for GLM-4), open duration (5 min, 10 min for GLM-4), and specific fallback behavior for each source when the circuit is open. This is a proper resilience pattern.

5. **Global Refresh Rate Optimization (5.7.5)**: The most detailed subsection. Includes:
   - Complete call volume estimation table (9 calls per stock, ~138 total for 20 stocks)
   - Processing pipeline description with parallel/sequential grouping
   - Per-source timing calculation showing the 20-stock refresh fits within the 2-minute target
   - Concurrency control (default 1, max 3, with dynamic reduction on rate limiting)
   - Rate limit adaptation logic with clear response actions

6. **Daily Recommendation Rate Budget (5.7.6)**: Estimates ~210 total API calls for the daily recommendation job taking ~80 seconds. Notes it runs during off-peak hours.

**Verdict**: This section demonstrates strong architectural thinking. The combination of rate limiting, backoff, circuit breaker, and dynamic adaptation provides a robust defense against data source blocking. The call volume estimations give the team confidence that the 2-minute Global Refresh target is achievable. PASS.

---

### 8.2 Integration Quality Check

#### New content consistency with existing document:

| Check | Result | Notes |
|-------|--------|-------|
| Section 13 referenced in Table of Contents | YES | Line 29: "13. Testing Strategy" |
| Section 4.3.1 flows naturally from 4.3 | YES | Placed immediately after Feature 2 description, before the recommendation pipeline |
| Section 4.4.1 flows naturally from 4.4 | YES | Placed at the start of watchlist feature, before display requirements |
| Section 5.7 placed correctly in technical architecture | YES | Between Section 5.6 (Error Handling) and Section 6 (Data Strategy) |
| New API endpoints (/device/*) appear in Section 8 | YES | Verified at line 1414 |
| hot_stock_universe table in Section 7.2 database design | NO | Table DDL defined in 4.3.1 but missing from the formal database design section 7.2 |
| Stale "device fingerprint" references updated | PARTIAL | Section 4.4.1 clarified mechanism, but lines 669, 1146, 2707, 2725 still use old terminology |
| Appendix B updated for new decisions | NO | No new entries in Appendix B for rate limiting strategy, device UUID clarification, or hot stock universe design |
| Risk R9 updated to reflect new backup mechanism | PARTIAL | R9 still says "device fingerprint changes" but mitigation now matches ("Provide export option") |

#### Were new issues introduced by the fixes?

| Potential Issue | Severity | Notes |
|----------------|----------|-------|
| Terminology inconsistency: "device fingerprint" in 4 locations vs "device UUID" in Section 4.4.1 | Nit | Non-blocking; readers of Section 4.4.1 will understand the correct mechanism |
| hot_stock_universe table missing from Section 7.2 | Minor | Cross-reference gap; DDL exists in 4.3.1 and is complete |
| Appendix B missing entries for new design decisions | Nit | Technical decision log should document rate limiting strategy, device UUID choice, and hot stock universe design |
| Section 13 AI validation field still uses `overall_recommendation` (line 2528) | Nit | MINOR-001 (compliance language) is still outstanding; this is a pre-existing issue, not newly introduced |

**Conclusion**: No new Major or Critical issues were introduced by the fixes. The integration quality is good overall with minor terminology consistency issues remaining.

---

### 8.3 Updated Scoring

| Dimension | Original | New Score | Change | Justification |
|-----------|----------|-----------|--------|---------------|
| Completeness | 17 | 19 | +2 | Addition of Testing Strategy (Section 13) and Hot Stock Universe Definition (Section 4.3.1) fills the two largest completeness gaps. The only remaining gap is the cross-reference of hot_stock_universe in Section 7.2. |
| Reasonableness | 15 | 17 | +2 | Rate limiting design (Section 5.7) with call volume estimation validates that the 2-minute Global Refresh and daily recommendation targets are achievable. Device UUID mechanism is realistic and well-scoped for MVP. |
| Implementability | 14 | 18 | +4 | Largest improvement. Rate limiting architecture with concrete numbers, circuit breaker patterns, and Python implementation skeleton provides clear development guidance. Hot stock universe criteria are directly translatable to code. Test data strategy gives developers concrete stocks and fixtures to work with. |
| Compliance | 18 | 18 | 0 | Compliance framework was already strong. MINOR-001 (terminology alignment) remains outstanding but was not in scope for this fix cycle. |
| User Experience | 16 | 17 | +1 | Device backup code system and export/import feature directly address the "surprise data loss" scenario that threatened user trust. Recovery flow is clearly documented. |
| Document Quality | 17 | 18 | +1 | New sections are well-structured, use consistent formatting (tables, code blocks, diagrams), and include concrete examples. Minor deduction for cross-reference gap and stale terminology in 4 locations. |
| **Total** | **81** | **91** | **+10** | |

---

### 8.4 Final Verdict

**APPROVED**

The PRD v2.0 has been approved for the architecture design phase. All 4 Major issues have been resolved to a satisfactory level:

- MAJOR-001 (Testing Strategy): PASS -- Section 13 is comprehensive, covering 6 test types, 9 priority services, all 16 API endpoints, 5 E2E scenarios, AI quality validation, and a phase-by-phase testing schedule.
- MAJOR-002 (Device Identity): PASS -- Section 4.4.1 clarifies the mechanism (UUID, not fingerprint), adds backup code system and JSON export/import as P0 features, and documents the complete recovery flow.
- MAJOR-003 (Hot Stock Universe): PASS -- Section 4.3.1 defines the universe with measurable inclusion criteria, complete database schema, weekly refresh mechanism, and initial seeding strategy.
- MAJOR-004 (Rate Limiting): PASS -- Section 5.7 provides a full rate limiting architecture with per-source budgets, request queuing, exponential backoff, circuit breaker pattern, and call volume estimation.

**Score: 91/100** -- exceeds the 85-point threshold for architecture phase approval.

---

### 8.5 Remaining Issues (Non-Blocking)

The following issues remain open. They should be addressed before development begins but do NOT block the architecture design phase:

| ID | Severity | Description | Recommended Timing |
|----|----------|-------------|-------------------|
| MINOR-001 | Minor | Compliance language inconsistency ("recommendation" vs "signal") throughout document | Before Phase 1 Sprint 1 |
| MINOR-002 | Minor | Prediction accuracy targets need statistical context (sample size thresholds) | Before Phase 2 |
| MINOR-003 | Minor | Trading calendar source and holiday handling not defined | Before Phase 1 Sprint 1 |
| MINOR-004 | Minor | Storage estimation underestimates growth at 500 DAU scale | Before Phase 2 |
| MINOR-005 | Minor | No monitoring/alerting strategy beyond token monitoring | Before Phase 3 |
| MINOR-006 | Minor | Concurrent watchlist modification race conditions | Before Phase 1 Sprint 2 |
| MINOR-007 | Minor | ETF handling underspecified for fundamentals and industry | Before Phase 1 Sprint 1 |
| MINOR-008 | Minor | Phase 0 duration may be tight | Noted for schedule management |
| NIT-NEW-001 | Nit | Stale "device fingerprint" references at lines 669, 1146, 2707, 2725 | Next PRD update |
| NIT-NEW-002 | Nit | hot_stock_universe table DDL missing from Section 7.2 (exists in 4.3.1) | Next PRD update |
| NIT-NEW-003 | Nit | Appendix B missing entries for rate limiting, device UUID, and hot stock universe decisions | Next PRD update |
| NIT-001 through NIT-005 | Nit | Original nit issues from first review (terminology, sort options, API versioning, DB choice log, Tailwind breakpoints) | As convenient |

---

### 8.6 Recommendation

**The PRD v2.0 is approved to proceed to the architecture design phase.**

The architecture design should:
1. Use Section 5.7 (Rate Limiting and Backpressure Strategy) as the foundation for the backend service architecture
2. Incorporate the `hot_stock_universe` table from Section 4.3.1 into the formal database schema
3. Use Section 13 (Testing Strategy) to establish the CI/CD pipeline requirements from Phase 0
4. Ensure the device identity mechanism from Section 4.4.1 is reflected in the API authentication layer design

The remaining Minor and Nit issues should be tracked in the project backlog and resolved progressively during development.

---

*Re-review conducted by: QA Guardian*
*Re-review date: 2026-02-09*
*Scope: Verification of 4 Major issue fixes + integration quality + updated scoring*
*Document version reviewed: PRD v2.0 (post-fix, ~2735 lines)*
