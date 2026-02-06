# E2E Test Plan - Stock Advisor

## Basic Information
- **Project Name**: Stock Advisor (A Stock Trading Strategy System)
- **Plan Created**: 2026-02-06
- **Plan Author**: qa-guardian
- **Expected Completion**: 2026-02-06

---

## 1. Test Scope

### Included
- [x] Backend API - Health Check
- [x] Backend API - Market Overview
- [x] Backend API - Recommendations (verify top 10)
- [x] Backend API - Stock Search
- [x] Backend API - Stock Details with AI Analysis
- [x] Data Validation - Change calculation
- [x] Data Validation - Stock count (10 stocks)
- [x] TypeScript Static Analysis

### Excluded
- Frontend visual testing (no Playwright setup)
- Load testing
- Security penetration testing
- Database direct access testing

---

## 2. Test Types and Estimates

| Test Type | Test Cases | Estimated Time | Priority |
|-----------|-----------|----------------|----------|
| API Health Check | 2 | 2 min | P0 |
| API Functional Tests | 5 | 10 min | P0 |
| Data Validation | 3 | 5 min | P0 |
| TypeScript Check | 1 | 1 min | P1 |

**Total**: 11 test cases, ~18 minutes

---

## 3. Execution Order

1. [x] Backend health check (wake up from cold start)
2. [ ] Market overview API test
3. [ ] Recommendations API test (verify 10 stocks)
4. [ ] Stock search API test
5. [ ] Stock details API test (verify AI analysis)
6. [ ] Data validation (change calculation)
7. [ ] TypeScript static analysis

---

## 4. Pass Criteria

| Metric | Target |
|--------|--------|
| P0 Test Pass Rate | 100% |
| P1 Test Pass Rate | >= 90% |
| API Response Time | < 60s (first request), < 5s (cached) |
| Critical Bugs | 0 |

---

## 5. Resources and Dependencies

- **Backend URL**: https://stock-advisor-api-6vtb.onrender.com
- **Frontend URL**: https://stock-advisor.netlify.app
- **Test Data**: Real market data from EastMoney/Yahoo Finance
- **External Dependencies**: Render (backend hosting), Netlify (frontend hosting)

---

## 6. Progress Tracking

| Phase | Status | Start Time | End Time | Executor |
|-------|--------|------------|----------|----------|
| Health Check | Pending | | | qa-guardian |
| API Tests | Pending | | | qa-guardian |
| Data Validation | Pending | | | qa-guardian |
| TypeScript Check | Pending | | | qa-guardian |
| QA Review | Pending | | | qa-guardian |

---

## 7. Risks and Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Backend cold start timeout | High | Medium | Wait up to 90s, retry |
| Market data unavailable (weekend) | Low | Medium | Use cached data or mock |
| Rate limiting | Low | Low | Add delays between requests |

---

## Test Cases

### TC001: Health Check
- **Endpoint**: GET /health
- **Expected**: `{"status": "healthy"}`
- **Timeout**: 90s (cold start)

### TC002: Market Overview
- **Endpoint**: GET /api/v1/market/overview
- **Expected**: sh_index, sz_index, sentiment fields present
- **Validation**: Numeric values for indices

### TC003: Recommendations List
- **Endpoint**: GET /api/v1/recommendations
- **Expected**: Maximum 10 stocks in recommendations array
- **Validation**: Each stock has code, name, price, change, score, ai_analysis

### TC004: Stock Search
- **Endpoint**: GET /api/v1/stock/search?q=茅台
- **Expected**: Results containing stock with code 600519
- **Validation**: Results array not empty

### TC005: Stock Details
- **Endpoint**: GET /api/v1/stock/600519
- **Expected**: Full analysis with indicators, suggestion, ai_analysis
- **Validation**:
  - indicators.macd present
  - suggestion.action present
  - ai_analysis field present (when ai_analysis=true)

### TC006: Change Calculation
- **Validation**: change = (price - prev_close) / prev_close * 100
- **Tolerance**: 0.1%

### TC007: TypeScript Build
- **Command**: npx tsc --noEmit
- **Expected**: No type errors

---

*Test Plan Version: 1.0*
*Created by: qa-guardian*
