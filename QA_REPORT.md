# QA Report - Stock Advisor

## Basic Information
- **Project Name**: Stock Advisor (A Stock Trading Strategy System)
- **QA Reviewer**: qa-guardian
- **Report Date**: 2026-02-06
- **Last Updated**: 2026-02-06
- **Current Status**: Review Completed

---

## Design Document Review

### Review #1 - 2026-02-06
- **Review Result**: PASS with recommendations
- **Design Completeness**: Complete (DESIGN.md is comprehensive)

**Findings:**
- [x] Project goals clear and well-defined
- [x] Functional requirements complete and verifiable
- [x] Technical selection reasonable (React + FastAPI + Supabase)
- [x] Architecture design includes module division and data flow
- [x] Implementation plan has clear phasing
- [x] Acceptance criteria measurable

**Testing Strategy in Design:**
- [ ] Test scope definition - Missing
- [ ] Test type planning - Missing
- [ ] Test environment requirements - Partially defined
- [ ] Test data strategy - Missing
- [ ] Expected coverage goals - Missing
- [ ] Test acceptance criteria - Partially defined

**Recommendation:** Add a dedicated testing section to DESIGN.md

---

## Code Review Records

### Review #1 - 2026-02-06 (Post-Refactoring)

**Scope:** Backend services (strategy_service.py, stock.py, eastmoney_service.py, yahoo_service.py, ai_analysis_service.py) and Frontend components (HomeContent.tsx, TabSwitcher.tsx, RefreshAllButton.tsx, api.ts, types.ts)

**Code Quality Score:** 3.5/5

#### Issues Found

| Severity | File | Issue | Status |
|----------|------|-------|--------|
| CRITICAL | ai_analysis_service.py:15 | API Key hardcoded in source code | Pending |
| CRITICAL | glm_service.py:18 | API Key hardcoded in source code (duplicate) | Pending |
| MAJOR | api.ts:19-20 | Dead code: `aiRankingsCache` and `AI_RANKINGS_CACHE_MS` not used | Pending |
| MAJOR | api.ts / types.ts | Type inconsistency: `AIRankingItem` defined differently in two files | Pending |
| MINOR | api.ts:350 | `getAIRankings` function defined but never called | Pending |
| MINOR | types.ts:96 | `AIRankingItem.suggestion` uses string but api.ts uses `action` | Pending |

#### Detailed Analysis

**1. CRITICAL: API Key Exposure**

Location:
- `/backend/app/services/ai_analysis_service.py` line 15
- `/backend/app/services/glm_service.py` line 18

```python
GLM_API_KEY = "7fa0e9aeab364d0fa11ab05d831fc0e7.6GMxW2I2ZmSgNmlw"
```

**Risk:** API keys should NEVER be hardcoded in source code. If this repository is public or becomes public, the key will be exposed. Additionally, this key is duplicated in two files, making maintenance difficult.

**Recommended Fix:**
1. Move API key to environment variable
2. Update config.py to include `glm_api_key: str = ""`
3. Reference via `get_settings().glm_api_key`

**2. MAJOR: Dead Code in Frontend**

Location: `/src/lib/api.ts` lines 19-20

```typescript
let aiRankingsCache: { data: { count: number; rankings: AIRankingItem[] }; timestamp: number } | null = null;
const AI_RANKINGS_CACHE_MS = 5 * 60 * 1000; // 5 minutes cache
```

These variables are declared but never used in the codebase.

**3. MAJOR: Type Definition Inconsistency**

`AIRankingItem` is defined in two places with different structures:

**types.ts:**
```typescript
export interface AIRankingItem {
  // ... common fields ...
  suggestion: string;  // Uses 'suggestion'
}
```

**api.ts:**
```typescript
export interface AIRankingItem {
  // ... common fields ...
  action: string;  // Uses 'action'
  buy_price_low: number;
  buy_price_high: number;
  // ... more fields ...
}
```

This inconsistency could cause runtime errors if the types are used interchangeably.

---

## Build & Compilation Test

### Test #1 - 2026-02-06

**Test Type:** TypeScript Compilation + Next.js Build

**Commands Executed:**
```bash
npm run build
npx tsc --noEmit
```

**Results:**
- Build Status: PASS
- TypeScript Check: PASS (no type errors)
- Build Time: ~1.4 seconds

**Build Output:**
```
Route (app)
- / (Dynamic)
- /_not-found (Static)
- /search (Static)
- /stock/[code] (Dynamic)
```

---

## E2E API Test Results

### Test Execution #1 - 2026-02-06

**Test Environment:**
- Backend URL: https://stock-advisor-api-6vtb.onrender.com
- Frontend URL: https://stock-advisor.netlify.app
- Test Time: 2026-02-06 22:15 CST

#### TC001: Health Check - PASS
- **Endpoint**: GET /health
- **Response**: `{"status":"healthy"}`
- **HTTP Code**: 200
- **Response Time**: 0.87s
- **Status**: PASS

#### TC002: Market Overview - PASS
- **Endpoint**: GET /api/v1/market/overview
- **Response**: `{"sh_index":4065.58,"sh_change":-0.25,"sz_index":13906.73,"sz_change":-0.33,"sentiment":"中性"}`
- **HTTP Code**: 200
- **Response Time**: 5.82s
- **Validation**: All required fields present (sh_index, sz_index, sentiment)
- **Status**: PASS

#### TC003: Recommendations List - FAIL
- **Endpoint**: GET /api/v1/recommendations
- **Expected**: Maximum 10 stocks
- **Actual**: Only 5 stocks returned
- **HTTP Code**: 200
- **Response Time**: 5.47s
- **Issue**: Recommendations count is 5, not 10 as expected per recent changes
- **Status**: FAIL
- **Severity**: MAJOR

**Details:**
The API returned only 5 recommended stocks:
1. 002873 - 新天药业 (Score: 80)
2. 600009 - 上海机场 (Score: 80)
3. 002415 - 海康威视 (Score: 80)
4. 000333 - 美的集团 (Score: 80)
5. 600519 - 贵州茅台 (Score: 75)

**Root Cause Analysis:**
The database (Supabase) stores the recommendations. The stored data from the last generation only contains 5 stocks. The `strategy_service.generate_daily_recommendations(top_n=10)` function is called with top_n=10, but the database may have been populated before this change.

**Resolution Required:**
- Trigger a new recommendation generation via POST /api/v1/recommendations/generate
- Or update the database records

#### TC004: Stock Search - FAIL
- **Endpoint**: GET /api/v1/stock/search?q=茅台
- **Expected**: Search results with 600519
- **Actual**: 404 error - "无法获取股票 search 的数据，请检查代码是否正确"
- **HTTP Code**: 404
- **Status**: FAIL
- **Severity**: CRITICAL

**Root Cause Analysis:**
FastAPI route priority issue. The route `/stock/{code}` is defined BEFORE `/stock/search`, so "search" is interpreted as a stock code parameter.

**Code Location:** `/backend/app/api/stock.py`
- Line 26: `@router.get("/stock/{code}")` - This catches all requests including `/stock/search`
- Line 300: `@router.get("/stock/search")` - Never reached

**Resolution Required:**
Move the `/stock/search` route BEFORE `/stock/{code}` route, or use a different URL pattern like `/stocks/search`.

#### TC005: Stock Details - PASS (with issues)
- **Endpoint**: GET /api/v1/stock/600519?ai_analysis=true&refresh=true
- **HTTP Code**: 200
- **Response Time**: ~3s (cached)

**Validation Results:**
| Field | Expected | Actual | Status |
|-------|----------|--------|--------|
| code | 600519 | 600519 | PASS |
| name | 贵州茅台 | 贵州茅台 | PASS |
| price | Numeric | 1515.01 | PASS |
| change | Numeric | 8.14 | PASS |
| prev_close | Numeric | None/Missing | WARN |
| indicators | Present | Present | PASS |
| suggestion | Present | Present | PASS |
| ai_analysis | Present | Present (when requested) | PASS |

**Issues Found:**
1. `prev_close` field returns `None` in API response despite being set in code
2. Without `ai_analysis=true` parameter, `ai_analysis` is not included in cached responses

#### TC006: Change Calculation Validation - UNABLE TO VERIFY
- **Issue**: `prev_close` returns `None`, cannot verify calculation
- **Expected Formula**: `change = (price - prev_close) / prev_close * 100`
- **Status**: BLOCKED
- **Note**: The eastmoney_service.py correctly returns prev_close, but it may be lost somewhere in the response chain

#### TC007: TypeScript Build - PASS
- **Command**: `npx tsc --noEmit`
- **Result**: No type errors
- **Status**: PASS

### E2E Test Summary

| Test Case | Status | Severity |
|-----------|--------|----------|
| TC001: Health Check | PASS | - |
| TC002: Market Overview | PASS | - |
| TC003: Recommendations (10 stocks) | FAIL | MAJOR |
| TC004: Stock Search | FAIL | CRITICAL |
| TC005: Stock Details | PASS (with warnings) | - |
| TC006: Change Calculation | BLOCKED | WARN |
| TC007: TypeScript Build | PASS | - |

**Pass Rate:** 4/7 (57%)
**Critical Issues Found:** 1 (Stock Search API broken)
**Major Issues Found:** 1 (Recommendations count mismatch)

---

## Architecture Analysis

### Positive Findings

1. **Clean Separation of Concerns**
   - Frontend: React + Next.js for UI
   - Backend: FastAPI for API services
   - Database: Supabase for persistence
   - Data Sources: EastMoney + Yahoo Finance with automatic fallback

2. **Robust Fallback Mechanism**
   - EastMoney -> Yahoo Finance fallback for data reliability
   - Default analysis generation when AI fails

3. **Good Error Handling**
   - API error classes properly defined
   - User-friendly error messages

4. **Caching Strategy**
   - Backend: 30-minute AI rankings cache, 3-minute stock analysis cache
   - Frontend: Wake-up mechanism for Render cold start

### Areas for Improvement

1. **Security**
   - API keys must be moved to environment variables
   - Consider implementing rate limiting

2. **Code Maintainability**
   - Remove dead code
   - Consolidate duplicate type definitions
   - Single source of truth for AIRankingItem interface

3. **Testing Coverage**
   - No unit tests found
   - No integration tests found
   - No E2E tests found

---

## Quality Metrics Summary

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| E2E API Test Pass Rate | 100% | 57% (4/7) | FAIL |
| Test Coverage | 80% | 0% | FAIL |
| Bug Fix Rate | 100% | N/A | N/A |
| Code Review Pass Rate | 100% | N/A | N/A |
| Documentation Completeness | 100% | 85% | WARN |
| TypeScript Build | Pass | Pass | PASS |
| Critical Security Issues | 0 | 2 | FAIL |
| Critical Bug Issues | 0 | 1 | FAIL |
| Major Bug Issues | 0 | 1 | FAIL |

---

## Risk and Issue Tracking

| ID | Type | Description | Severity | Status | Resolution |
|----|------|-------------|----------|--------|------------|
| SEC001 | Security | API Key hardcoded in ai_analysis_service.py | CRITICAL | Open | Move to env var |
| SEC002 | Security | API Key hardcoded in glm_service.py | CRITICAL | Open | Move to env var |
| BUG001 | Bug | Stock search API returns 404 (route priority issue) | CRITICAL | Open | Reorder routes in stock.py |
| BUG002 | Bug | Recommendations returns 5 stocks instead of 10 | MAJOR | Open | Regenerate recommendations |
| BUG003 | Bug | prev_close field missing from API response | MINOR | Open | Debug response chain |
| CODE001 | Code Quality | Dead code: aiRankingsCache unused | MAJOR | Open | Remove or use |
| CODE002 | Code Quality | Type inconsistency AIRankingItem | MAJOR | Open | Consolidate types |
| TEST001 | Testing | No test coverage | MAJOR | Open | Add tests |

---

## Recommendations

### Immediate Actions (P0)
1. **Move API keys to environment variables**
   - Create GLM_API_KEY in .env
   - Update ai_analysis_service.py and glm_service.py to use env var
   - Update config.py to load the new config

### Short-term Actions (P1)
2. **Clean up dead code**
   - Remove or properly implement aiRankingsCache
   - Remove unused AI_RANKINGS_CACHE_MS

3. **Fix type definitions**
   - Keep single AIRankingItem definition in types.ts
   - Update api.ts to import from types.ts

### Medium-term Actions (P2)
4. **Add test coverage**
   - Unit tests for indicator calculations
   - Integration tests for API endpoints
   - E2E tests for critical user flows

5. **Update DESIGN.md**
   - Add testing strategy section
   - Add deployment documentation

---

## Final Quality Assessment

### Overall Score: 5/10

**Quality Dimension Ratings:**
- Functionality: 3/5 - Critical API bug (search broken), partial feature regression (5 vs 10 stocks)
- Code Quality: 3/5 - Has security issues and dead code
- Test Coverage: 1/5 - No automated tests found
- Documentation: 4/5 - Good design doc, missing test strategy
- Security: 2/5 - Critical API key exposure issue

### Release Recommendation: NOT RECOMMENDED

**Blocking Issues:**
1. CRITICAL: Stock search API is completely broken (route priority bug)
2. CRITICAL: API keys hardcoded in source code (security risk)
3. MAJOR: Recommendations only returns 5 stocks, not 10 as specified

**Conditions for Release:**
1. MUST fix stock search route priority issue (`/stock/search` before `/stock/{code}`)
2. MUST fix API key exposure (move to environment variables)
3. MUST regenerate recommendations to include 10 stocks
4. SHOULD remove dead code
5. SHOULD fix type inconsistencies

**Next Steps:**
1. **Immediate (P0):**
   - Fix route priority in `/backend/app/api/stock.py` - move search route before dynamic route
   - Move API keys to environment variables
   - Regenerate recommendations via POST /api/v1/recommendations/generate

2. **Short-term (P1):**
   - Clean up dead code in frontend
   - Consolidate type definitions
   - Debug prev_close field

3. **Medium-term (P2):**
   - Add automated test coverage
   - Update DESIGN.md with testing strategy

---

## Appendix: Test Plan Reference

See `TEST_PLAN.md` for detailed test plan and test case specifications.

---

*QA Report generated by qa-guardian*
*Report Version: 1.1*
*Last Updated: 2026-02-06*
