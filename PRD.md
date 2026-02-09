# Stock Advisor PRD (Product Requirements Document)

**A Stock Intelligent Trading Strategy System**

| Field | Value |
|-------|-------|
| Document Version | v1.0 |
| Created | 2026-02-08 |
| Author | Product Orchestrator |
| Status | Draft - Pending Review |
| Project Location | `projects/software/stock-advisor/` |
| Based On | DESIGN.md v2.0 (2026-02-04) audit + codebase review |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current State Audit](#2-current-state-audit)
3. [Product Vision and Positioning](#3-product-vision-and-positioning)
4. [Market Analysis](#4-market-analysis)
5. [User Research](#5-user-research)
6. [Functional Requirements](#6-functional-requirements)
7. [Non-Functional Requirements](#7-non-functional-requirements)
8. [Technical Architecture](#8-technical-architecture)
9. [Data Strategy](#9-data-strategy)
10. [Compliance and Legal Framework](#10-compliance-and-legal-framework)
11. [Testing Strategy](#11-testing-strategy)
12. [Development Roadmap](#12-development-roadmap)
13. [Risk Assessment](#13-risk-assessment)
14. [Success Metrics and Acceptance Criteria](#14-success-metrics-and-acceptance-criteria)
15. [Appendix: Design Audit Findings](#15-appendix-design-audit-findings)

---

## 1. Executive Summary

### 1.1 Vision

Build a free, intelligent A-share trading strategy advisory tool that empowers individual investors with institutional-grade technical analysis, AI-augmented insights, and transparent performance tracking -- all accessible via a mobile-friendly web interface.

### 1.2 Problem Statement

Individual A-share investors face three core challenges:

1. **Information asymmetry**: Retail investors lack the analytical tools available to institutions. They rely on fragmented information from social media, forums, and broker apps that often lack rigor.
2. **Time constraints**: Many investors (especially working professionals) cannot dedicate hours to daily stock screening, technical analysis, and market monitoring.
3. **Emotional decision-making**: Without systematic frameworks, investors frequently buy high and sell low, driven by fear and greed rather than data.

### 1.3 Solution

Stock Advisor provides:

- **Instant technical analysis** for any A-share or ETF -- enter a code, receive a complete analysis in under 5 seconds
- **Daily automated screening** -- the system runs quantitative strategies every trading day and surfaces the top candidates
- **Transparent performance tracking** -- every recommendation is tracked, with win rate, average return, and profit/loss ratio publicly visible
- **AI-powered insights** -- GLM-4 provides fundamental analysis, company overviews, and natural-language trading guidance

### 1.4 Core Value Proposition

| For | Who | Our Product | That | Unlike |
|-----|-----|-------------|------|--------|
| Individual A-share investors | Want quick, data-driven stock analysis | Provides real-time technical analysis + AI insights + transparent tracking | Reduces analysis time from hours to seconds and adds accountability via historical tracking | Free brokerage apps that provide only raw data without actionable recommendations; and paid advisory services that are expensive and opaque |

### 1.5 Key Metrics (North Stars)

| Metric | Target (30 days post-launch) | Target (90 days) |
|--------|------------------------------|-------------------|
| Daily Active Users (DAU) | 50 | 500 |
| Stock Queries per Day | 200 | 2,000 |
| Recommendation Win Rate | > 55% | > 60% |
| Average Session Duration | > 3 min | > 5 min |
| Returning Users (D7 retention) | > 30% | > 40% |

---

## 2. Current State Audit

### 2.1 What Has Been Built

The project has reached a testing phase with the following components deployed:

| Component | Technology | Deployment | Status |
|-----------|-----------|------------|--------|
| Frontend | Next.js 15 + React 18 + TypeScript + Tailwind | Netlify (my-stock-advisor.netlify.app) | Running |
| Backend | FastAPI 0.109 + Python 3.11 | Render (stock-advisor-api-6vtb.onrender.com) | Running |
| Database | PostgreSQL via Supabase | Supabase Cloud | Running |
| AI Analysis | GLM-4 (Zhipu AI) | API calls from backend | Running |
| Data Sources | EastMoney API (primary) + Yahoo Finance (fallback) | Direct HTTP calls | Running |

### 2.2 Implemented Features

- Single stock query with full technical analysis (MACD, RSI, KDJ, MA, BOLL, ATR)
- Trading suggestions (buy price range, stop loss, take profit levels)
- AI-powered company overview and fundamental analysis via GLM-4
- AI intelligent ranking of ~30 pre-defined hot stocks
- Daily recommendation generation (stored in Supabase)
- Market overview (Shanghai/Shenzhen indices)
- Stock search (route fix pending deployment)
- Backend wake-up mechanism for Render cold start
- Mobile-responsive frontend

### 2.3 Critical Issues Found in Audit

| ID | Severity | Issue | Current Status |
|----|----------|-------|----------------|
| SEC-001 | CRITICAL | GLM API key hardcoded in `ai_analysis_service.py` and `glm_service.py` | Claimed resolved via env var, but code review shows hardcoded fallback remains |
| BUG-001 | CRITICAL | Stock search returns 404 -- route conflict between `/stock/{code}` and `/stock/search` | Code fix applied (moved to `/stocks/search`), pending Render deployment |
| BUG-002 | MAJOR | Recommendations return only 5 stocks instead of 10 | Database has stale data; needs regeneration |
| BUG-003 | MINOR | `prev_close` field returns null in API responses | Under investigation |
| CODE-001 | MAJOR | Dead code in frontend (`aiRankingsCache` unused) | Open |
| CODE-002 | MAJOR | Duplicate/inconsistent `AIRankingItem` type definitions in `api.ts` vs `types.ts` | Open |
| TEST-001 | MAJOR | Zero automated test coverage (no unit, integration, or E2E tests) | 75+ test cases documented but none automated |
| ARCH-001 | MAJOR | Render free tier cold start takes 57 seconds -- unacceptable UX for first-time visitors | Mitigated by wake-up mechanism, but still painful |

### 2.4 Issues Found in Original DESIGN.md

**Strengths of the original design:**
- Clear feature breakdown with user flows
- Detailed database schema
- Well-defined API contract
- Strategy logic documented with Python pseudocode
- Compliance disclaimer included

**Weaknesses identified:**

1. **Product positioning is too broad**: The document mixes "helping beginners learn" with "serving busy professionals" -- these are fundamentally different use cases requiring different UX approaches.

2. **User personas lack depth**: Three user types are listed as a table without scenarios, motivation chains, or behavioral patterns. No user journey maps.

3. **No market context**: No competitor analysis, no differentiation strategy, no market sizing. The reader cannot assess whether this product has a viable niche.

4. **Compliance treatment is superficial**: A single disclaimer block does not constitute a compliance strategy. Financial software in China must consider CSRC regulations, anti-fraud obligations, and the distinction between "information service" vs "investment advisory."

5. **Testing strategy completely absent**: The QA Report independently identified this gap. No test plan, no coverage targets, no automation framework.

6. **Data source risk unaddressed**: The system relies entirely on EastMoney's undocumented HTTP API with Yahoo Finance as fallback. Neither is a contracted, stable data source. No rate limiting, no terms-of-service compliance analysis.

7. **AI dependency not risk-assessed**: GLM-4 API could become unavailable, rate-limited, or change pricing. The system's behavior when AI is unavailable is handled but not documented in the design.

8. **Performance targets are inadequate**: "< 5 seconds for stock query" is the only performance target. No targets for cold start, concurrent users, data freshness, or cache invalidation.

9. **Scoring system lacks validation**: The 0-100 scoring system has no backtesting data to prove it correlates with actual stock performance. Displaying scores without validation creates false confidence.

10. **Roadmap is unrealistic**: Phase 1 MVP in 2 weeks, Phase 2 AI in 2 more weeks, Phase 3 optimization in 1 week -- total 5 weeks for a full-stack financial application with AI. The project is already past this timeline and not yet stable.

11. **No error handling UX**: The design describes happy paths only. What does the user see when data is unavailable? When AI fails? When the market is closed?

12. **No monitoring or alerting strategy**: No plan for how to detect issues in production, track system health, or receive alerts when something breaks.

---

## 3. Product Vision and Positioning

### 3.1 Product Definition

Stock Advisor is a **free, web-based A-share technical analysis tool** that provides individual investors with automated stock screening, real-time technical analysis, AI-powered insights, and transparent recommendation tracking.

**What Stock Advisor IS:**
- A data presentation and analysis tool
- A technical indicator calculator and visualizer
- An AI-assisted information aggregator
- A transparent record of system-generated signals

**What Stock Advisor is NOT:**
- An investment advisory service (no advisory license)
- A trading platform (no order execution)
- A guaranteed profit system (no performance guarantees)
- A replacement for professional financial advice

### 3.2 Differentiation Strategy

| Dimension | Broker Apps (e.g., Tonghuashun) | Paid Advisory Services | Stock Advisor |
|-----------|------|------|------|
| Price | Free | 500-5000 RMB/month | Free |
| Technical Analysis | Raw indicators, user interprets | Analyst reports | Automated interpretation with actionable suggestions |
| Recommendations | None (compliance) | Opaque track record | Transparent, auditable history with performance stats |
| AI Analysis | Basic news summaries | Human analysts | GLM-4 powered company analysis and fundamental review |
| Accessibility | Complex interfaces | Reports via WeChat/email | Mobile-first web app, instant access |
| Target Audience | All investors | High-net-worth | Individual investors wanting a quick analytical edge |

### 3.3 Positioning Statement

For individual A-share investors who want quick, data-driven analysis without paying for advisory services, Stock Advisor is a free web tool that combines quantitative screening with AI insights and transparent tracking, unlike brokerage apps that only show raw data or paid services that lack accountability.

---

## 4. Market Analysis

### 4.1 Market Context

- A-share market has approximately 220 million individual investor accounts (CSRC data)
- Individual investors account for roughly 60% of trading volume
- Most retail investors underperform the market index over 3-year periods
- Growing demand for quantitative and AI-assisted tools among tech-savvy younger investors
- Regulatory environment is tightening around unlicensed investment advisory

### 4.2 Competitive Landscape

| Category | Examples | Strengths | Weaknesses |
|----------|----------|-----------|------------|
| **Brokerage Apps** | Tonghuashun, Dongfang Caifu | Massive user base, official data feeds, trading integration | Overwhelming complexity, no personalized recommendations |
| **Quantitative Platforms** | JoinQuant, RiceQuant, Tushare | Backtesting, custom strategies, professional grade | Steep learning curve, requires programming knowledge |
| **Social Trading** | Xueqiu (Snowball) | Community insights, portfolio sharing | Noise, survivorship bias, no systematic analysis |
| **Paid Advisory** | Various WeChat groups, subscription services | Personal attention | Expensive, often unlicensed, opaque performance |
| **AI Stock Tools** | Various emerging tools | Novel AI analysis | Unproven, often overpromise |

### 4.3 Our Niche

Stock Advisor targets the gap between "raw data apps" and "expensive advisory services" -- specifically:
- Investors who can read a stock chart but want automated scanning
- Professionals who have 5-10 minutes per day for market review
- Users who value transparency and want to see historical recommendation accuracy

---

## 5. User Research

### 5.1 Primary Persona: "The Informed Part-Timer"

| Attribute | Detail |
|-----------|--------|
| Name | Li Wei (Archetype) |
| Age | 28-45 |
| Occupation | Tech professional, middle management, small business owner |
| Investment Experience | 2-5 years, understands basic technical analysis concepts |
| Portfolio Size | 50,000 - 500,000 RMB |
| Daily Time for Investing | 10-30 minutes |
| Pain Points | Cannot screen 5000+ stocks daily; misses entry/exit points due to work; relies on tips from colleagues/WeChat groups with no accountability |
| Goals | Find 2-3 good entry opportunities per week; manage risk with clear stop-loss levels; improve win rate over time |
| Technology | Uses smartphone primarily, occasionally laptop; comfortable with web apps |
| Current Tools | Brokerage app for trading, Xueqiu for discussion, occasionally Tonghuashun for charts |

### 5.2 Secondary Persona: "The Curious Learner"

| Attribute | Detail |
|-----------|--------|
| Name | Zhang Min (Archetype) |
| Age | 22-30 |
| Investment Experience | < 2 years, learning technical analysis |
| Portfolio Size | 10,000 - 100,000 RMB |
| Pain Points | Information overload, does not know how to interpret indicators, afraid of making costly mistakes |
| Goals | Learn by seeing how strategies work on real data; build confidence before committing larger capital |
| Technology | Smartphone-first, very comfortable with web apps |

### 5.3 User Journey Map (Primary Persona)

```
Scenario: Li Wei checks the market during lunch break

1. DISCOVER
   - Sees Stock Advisor shared in a WeChat group or Xueqiu post
   - Opens the web link on phone

2. FIRST VISIT (Critical moment)
   - Sees market overview (Shanghai/Shenzhen indices)
   - Sees today's recommended stocks with scores
   - Notices the disclaimer and risk warning
   - Thinks: "Let me check a stock I already own"

3. SEARCH & ANALYZE
   - Types stock code (e.g., 600519) in search box
   - Gets full analysis in 3-5 seconds
   - Reviews technical indicators, AI analysis, and trading suggestion
   - Compares buy/sell levels with current position

4. EXPLORE RECOMMENDATIONS
   - Scrolls through today's Top 10 recommendations
   - Taps on an interesting stock to see detailed analysis
   - Notes the buy price range and stop loss level

5. VALIDATE TRUST (Critical for retention)
   - Checks historical recommendation performance
   - Sees win rate, average return, profit/loss ratio
   - Thinks: "The track record is reasonable and transparent"

6. RETURN DAILY
   - Bookmarks the site
   - Checks daily recommendations each morning
   - Queries stocks before making trading decisions
```

### 5.4 Key User Flows

**Flow 1: Stock Query**
```
Home Page -> Enter stock code -> View analysis -> Read AI summary -> Note trading levels
```

**Flow 2: Daily Check**
```
Home Page -> View market overview -> Browse today's recommendations -> Tap for details
```

**Flow 3: Performance Validation**
```
Home Page -> Navigate to history/stats -> View win rate and performance -> Build trust
```

---

## 6. Functional Requirements

### 6.1 Priority Framework

- **P0 (Must-Have)**: Required for launch. System cannot provide value without these.
- **P1 (Should-Have)**: Significantly improves user experience. Target for v1.1.
- **P2 (Nice-to-Have)**: Differentiators for growth. Target for v2.0.

### 6.2 P0: Core Features (Required for Launch)

#### F1: Real-Time Stock Analysis

**Description**: User enters any A-share stock code or ETF code and receives a comprehensive technical analysis within 5 seconds (cached) or 15 seconds (uncached).

**Input**: Stock code (6-digit number, e.g., 600519, 000001, 512930)

**Output**:
| Section | Content | Notes |
|---------|---------|-------|
| Basic Info | Name, code, industry, market cap | From real-time data source |
| Price Data | Current price, change%, open, high, low, prev_close, volume, turnover | Real-time or 15-min delayed |
| Technical Indicators | MACD (DIF/DEA/histogram + signal), RSI (value + level), MA (5/10/20/60 + alignment), KDJ (K/D/J), BOLL (upper/mid/lower + position), ATR, volume ratio | Calculated from 60-day history |
| Trading Suggestion | Action (buy/hold/sell/wait), buy price range, stop loss, take profit 1 & 2, holding period, position size, risk level | Algorithm-generated |
| Summary | Natural language trading guidance | AI-generated (GLM-4) with template fallback |
| Score | 0-100 composite score | Weighted: technical 40%, pattern 30%, momentum 20%, volume 10% |

**Acceptance Criteria**:
- [ ] Accepts any valid A-share code (SH/SZ main board, SME board, ChiNext, STAR, and ETFs)
- [ ] Returns complete analysis within 5 seconds for cached data, 15 seconds for uncached
- [ ] Gracefully handles invalid codes with clear error message
- [ ] Technical indicators match manual calculation within 0.1% tolerance
- [ ] Trading suggestion includes all required fields (no null values for critical fields)
- [ ] Works when AI is unavailable (template fallback for summary)

**Edge Cases**:
- Stock is suspended: Show last available data with "suspended" status
- Market is closed: Show last closing data with "market closed" indicator
- New stock (< 60 days of history): Show available data with "insufficient history" warning
- ETF vs stock: Both should work, clearly labeled

#### F2: Daily Smart Recommendations

**Description**: System automatically screens the full A-share market daily and produces a ranked list of top 10 candidates based on quantitative strategies.

**Screening Pipeline**:
```
Stage 1: Universe Selection (~60 stocks from curated list)
  -> Excludes ST/suspended/new listings
  -> Requires market cap > 1B RMB
  -> Requires daily turnover > 50M RMB

Stage 2: Strategy Filtering (at least 1 must trigger)
  -> MACD golden cross or approaching
  -> RSI oversold bounce
  -> MA bullish alignment
  -> Volume-price confirmation

Stage 3: Scoring and Ranking
  -> Composite score > 60 to qualify
  -> Sorted by score descending
  -> Top 10 selected

Stage 4: AI Enrichment (best-effort)
  -> GLM-4 fundamental analysis for each recommendation
  -> Fallback to technical-only if AI unavailable
```

**Output**: List of 10 recommended stocks, each with:
- Full technical analysis (same as F1 output)
- AI fundamental analysis (when available)
- Specific entry/exit levels
- Risk assessment

**Timing**: Generated after market close (17:30 CST on trading days)

**Acceptance Criteria**:
- [ ] Produces exactly 10 recommendations on trading days (or fewer if insufficient candidates pass screening)
- [ ] Each recommendation includes complete analysis with entry/exit levels
- [ ] Recommendations are stored in database with date stamp
- [ ] No duplicate stocks in the same day's list
- [ ] Screening logic is deterministic and reproducible
- [ ] Generation completes within 10 minutes

**Known Limitation (Current)**: The screening universe is limited to ~60 curated stocks (from `STOCK_LIST` in `eastmoney_service.py`), not the full A-share market. This is acceptable for MVP but should expand in future versions.

#### F3: Recommendation History and Performance Tracking

**Description**: Every recommendation is stored permanently and tracked daily to build a transparent performance record.

**Tracking Logic**:
- After recommendation date, track daily closing price
- Status transitions: `holding` -> `stop_loss` (if price falls below stop loss) or `take_profit` (if price reaches target 1 or target 2) or `expired` (if holding period exceeded)
- Calculate: individual return per recommendation, aggregate win rate, average return, profit/loss ratio

**Display**:
| Metric | Calculation |
|--------|------------|
| Win Rate | (take_profit count) / (take_profit + stop_loss count) |
| Average Return | Mean of (exit_price - entry_price) / entry_price for closed positions |
| Profit/Loss Ratio | Average winning trade return / Average losing trade return |
| Total Recommendations | Count of all recommendations in period |
| Active Positions | Count of holding status recommendations |

**Acceptance Criteria**:
- [ ] All recommendations are persisted in Supabase with unique (date, code) constraint
- [ ] Performance statistics are calculated correctly
- [ ] Historical data is queryable by date range
- [ ] Stats page shows 30-day rolling performance by default
- [ ] Individual recommendation tracking shows daily price progression

#### F4: Market Overview

**Description**: Show the current state of major market indices as context for all analysis.

**Data**:
- Shanghai Composite Index (value + change%)
- Shenzhen Component Index (value + change%)
- Market sentiment indicator (bullish/neutral/bearish)

**Acceptance Criteria**:
- [ ] Displays on home page above recommendations
- [ ] Refreshes each time user visits the page
- [ ] Shows "market closed" state outside trading hours

#### F5: Web Interface

**Description**: Mobile-first, responsive web application with clean design.

**Pages**:

| Page | Path | Content | Priority |
|------|------|---------|----------|
| Home | `/` | Market overview + search box + today's recommendations + disclaimer | P0 |
| Stock Detail | `/stock/[code]` | Full analysis for a single stock | P0 |
| Search Results | `/search` | Search results page | P0 |

**UI Requirements**:
- Mobile-first design (375px minimum width)
- Clear visual hierarchy: market overview > search > recommendations
- Color coding for up (red in China market convention) and down (green) price movements
- Loading states for all async operations
- Error states with retry actions
- Disclaimer visible without scrolling on first visit

**Acceptance Criteria**:
- [ ] Renders correctly on iPhone SE, iPhone 14, iPad, and desktop (1440px)
- [ ] First Contentful Paint < 2 seconds
- [ ] Interactive within 3 seconds on 4G network
- [ ] All async operations show loading indicators
- [ ] Error states provide actionable guidance (retry button, alternative actions)

#### F6: Risk Disclaimers

**Description**: Legally compliant risk warnings and disclaimers integrated throughout the UX.

**Placement Requirements**:
- Home page: Banner disclaimer visible without scrolling
- Every stock analysis page: Risk warning section
- Every recommendation: Individual risk level indicator
- Footer: Full legal disclaimer on every page

**Acceptance Criteria**:
- [ ] Disclaimer text is reviewed for legal accuracy (see Section 10)
- [ ] Risk warnings cannot be dismissed permanently (always visible)
- [ ] Every trading suggestion includes a risk level assessment
- [ ] No language that could be construed as a guarantee of profit

### 6.3 P1: Enhancement Features (v1.1)

#### F7: AI Intelligent Ranking

**Description**: Ranks ~30 hot stocks by an AI-augmented composite score that combines technical analysis with AI sentiment analysis.

**Current State**: Implemented and deployed at `/rankings/ai`. Uses a curated list of 30 stocks, calculates technical scores, and applies an AI ranking boost.

**Improvements Needed**:
- Expand to 50+ stocks
- Add sector-level analysis
- Show ranking changes from previous day

#### F8: Advanced Search

**Description**: Search stocks by name (Chinese characters) or code, with autocomplete suggestions.

**Current State**: Backend endpoint exists at `/stocks/search` (pending deployment). Frontend search page exists.

**Improvements Needed**:
- Add fuzzy matching for Chinese names
- Add industry/sector filtering
- Show recent search history (local storage)

#### F9: K-Line Chart

**Description**: Interactive candlestick chart for each stock showing price action with technical indicator overlays.

**Current State**: K-line data API exists (`/stock/{code}/kline`). No frontend chart component yet.

**Requirements**:
- 60-day candlestick chart
- Volume bars below price chart
- MA overlay (5/10/20/60)
- Buy/sell signal markers
- Mobile-friendly touch interactions (pinch to zoom, swipe to scroll)

#### F10: Statistics Dashboard

**Description**: Dedicated page showing historical recommendation performance with charts and filters.

**Path**: `/stats`

**Content**:
- Rolling 30-day performance summary
- Monthly win rate trend chart
- Best/worst performing recommendations
- Sector distribution of recommendations

### 6.4 P2: Future Features (v2.0)

#### F11: Full Market Screening

Expand from ~60 curated stocks to scanning the entire A-share market (~5000 stocks). Requires:
- Background job architecture (current synchronous approach will not scale)
- Parallel data fetching with rate limiting
- Incremental scanning (not all stocks every day)

#### F12: User Accounts and Watchlists

Allow users to create accounts, save favorite stocks, and receive notifications. Requires:
- Authentication system (WeChat login preferred)
- User preferences storage
- Push notification infrastructure

#### F13: Backtesting Module

Allow users to see how the scoring/recommendation system would have performed over historical periods (3 months, 6 months, 1 year).

#### F14: Multi-Timeframe Analysis

Support weekly and monthly chart analysis in addition to daily.

#### F15: News and Sentiment Analysis

Integrate financial news feeds and use NLP to assess sentiment for recommended stocks.

---

## 7. Non-Functional Requirements

### 7.1 Performance

| Metric | Target | Current | Gap |
|--------|--------|---------|-----|
| Stock query (cached) | < 2 seconds | 0.61s | Met |
| Stock query (uncached) | < 15 seconds | 10.63s | Met |
| First page load | < 3 seconds | ~2s (after wake) | Met |
| Cold start (Render) | < 30 seconds | 57 seconds | NOT MET |
| Recommendation generation | < 10 minutes | ~5 minutes | Met |
| Concurrent users | 50 simultaneous | Unknown (untested) | Untested |
| API availability | > 99% during market hours | Dependent on Render/Supabase | Untested |

**Cold Start Mitigation Strategy**:
The Render free tier cold start is a fundamental UX problem. Options:
1. (Current) Frontend wake-up mechanism with progress indicator -- acceptable for MVP
2. (Recommended for v1.1) Upgrade to Render paid plan ($7/month) for always-on instances
3. (Alternative) Migrate backend to a platform without cold start (e.g., Vercel serverless, fly.io)

### 7.2 Security

| Requirement | Priority | Status |
|-------------|----------|--------|
| No API keys in source code | P0 | CRITICAL: Hardcoded key found |
| HTTPS for all communications | P0 | Met (Netlify + Render both use HTTPS) |
| CORS restricted to known origins | P0 | Met (whitelist in config.py) |
| Rate limiting on API | P1 | NOT IMPLEMENTED |
| Input validation on all endpoints | P0 | Partially implemented |
| No user authentication data stored (MVP) | P0 | Met (no auth system) |

### 7.3 Reliability

| Requirement | Target |
|-------------|--------|
| Data source failover | Primary (EastMoney) -> Fallback (Yahoo Finance) |
| AI service degradation | GLM-4 unavailable -> template-based fallback |
| Database unavailability | Recommendation history unavailable, real-time queries still work |
| Graceful error handling | All errors return user-friendly messages with retry guidance |

### 7.4 Scalability

For MVP (free tier), the system supports approximately:
- 100 API requests per minute (Render free tier limits)
- 500MB database storage (Supabase free tier)
- 100GB bandwidth per month (Netlify free tier)

This is sufficient for the initial launch target of ~50 DAU. Scaling plan is covered in the roadmap.

### 7.5 Accessibility

| Requirement | Priority |
|-------------|----------|
| Semantic HTML structure | P1 |
| Color contrast ratio > 4.5:1 | P1 |
| Screen reader compatible basic navigation | P2 |
| Keyboard navigation for all interactive elements | P2 |

---

## 8. Technical Architecture

### 8.1 Architecture Overview

```
                        User (Mobile/Desktop Browser)
                                    |
                                    v
                    +-------------------------------+
                    |       Netlify CDN             |
                    |  Next.js 15 + React 18 + TS  |
                    |  Static site + client-side    |
                    +-------------------------------+
                                    |
                              HTTPS API calls
                                    |
                                    v
                    +-------------------------------+
                    |       Render (Backend)        |
                    |    FastAPI + Python 3.11      |
                    |                               |
                    |  +-------------------------+  |
                    |  | API Layer (Routes)      |  |
                    |  | /stock, /recommendations|  |
                    |  | /stats, /rankings       |  |
                    |  +-------------------------+  |
                    |  | Service Layer           |  |
                    |  | indicator_service       |  |
                    |  | strategy_service        |  |
                    |  | ai_analysis_service     |  |
                    |  | eastmoney_service       |  |
                    |  | yahoo_service (fallback)|  |
                    |  | glm_service (AI)        |  |
                    |  +-------------------------+  |
                    |  | Caching Layer           |  |
                    |  | In-memory (3-30 min)    |  |
                    |  +-------------------------+  |
                    +-------------------------------+
                         |              |
                         v              v
              +--------------+  +---------------+
              |   Supabase   |  |  External APIs|
              |  PostgreSQL  |  |  - EastMoney  |
              |  - recs      |  |  - Yahoo Fin  |
              |  - tracking  |  |  - GLM-4 API  |
              |  - cache     |  +---------------+
              +--------------+
```

### 8.2 Technology Stack Assessment

| Layer | Current Choice | Assessment | Recommendation |
|-------|---------------|------------|----------------|
| Frontend Framework | Next.js 15 + React 18 | Appropriate. SSG + client-side rendering fits the use case. | Keep |
| Frontend Styling | Tailwind CSS | Good choice for rapid prototyping and mobile-first design. | Keep |
| Backend Framework | FastAPI | Excellent choice. Async support, auto-docs, type validation. | Keep |
| Database | Supabase (PostgreSQL) | Good for MVP. Free tier generous (500MB, 50K rows/month). | Keep for MVP, evaluate scaling later |
| Data Source | EastMoney HTTP API (undocumented) | RISK: Undocumented, no SLA, could break without notice. | Keep for MVP, add monitoring, plan migration to licensed API |
| Data Fallback | Yahoo Finance (yfinance library) | Good fallback, but A-share data quality varies. | Keep as fallback |
| AI Model | GLM-4 (Zhipu AI) | Good for Chinese language analysis. Free tier limits unknown. | Keep, add quota monitoring |
| Hosting (Frontend) | Netlify | Good free tier, excellent CDN. | Keep |
| Hosting (Backend) | Render | RISK: Cold start problem. Otherwise good for MVP. | Keep for MVP, plan upgrade |
| Technical Indicators | pandas-ta / ta library | Industry standard. Calculation accuracy verified. | Keep |

### 8.3 Architecture Concerns and Improvements

**Concern 1: In-Memory Caching**
Current caching is in-memory on the Render instance. This means:
- Cache is lost on every deployment or cold start
- No cache sharing if scaling to multiple instances
- No persistent cache for expensive AI rankings

**Recommendation**: Acceptable for MVP single-instance. For v1.1, consider Redis or Supabase-based caching.

**Concern 2: Synchronous Data Fetching in Rankings**
The AI rankings endpoint fetches data for 30 stocks sequentially. This is slow and blocks the event loop.

**Recommendation**: Implement async concurrent fetching with `asyncio.gather()` or a background task queue.

**Concern 3: No Request Rate Limiting**
Any user can make unlimited API requests, which could:
- Exhaust the GLM-4 API quota
- Overload the EastMoney API (risk of IP ban)
- Exhaust Render free tier resources

**Recommendation**: Add rate limiting middleware (e.g., `slowapi` for FastAPI) with:
- 60 requests per minute per IP for stock queries
- 5 requests per minute per IP for AI analysis
- 1 request per 5 minutes per IP for recommendation generation

### 8.4 Frontend Architecture

```
src/
  app/
    page.tsx              # Home page (market overview + search + recommendations)
    layout.tsx            # Root layout with metadata
    globals.css           # Global styles
    search/page.tsx       # Search results page
    stock/[code]/page.tsx # Stock detail page
  components/
    HomeContent.tsx       # Home page client component (main logic)
    MarketHeader.tsx      # Market indices display
    SearchBox.tsx         # Stock code/name search input
    StockCard.tsx         # Stock recommendation card
    StockDetailClient.tsx # Stock detail page content
    Disclaimer.tsx        # Legal disclaimer component
    TabSwitcher.tsx       # Recommendations/AI Rankings tab
    RefreshButton.tsx     # Single refresh button
    RefreshAllButton.tsx  # Bulk refresh button
    ProgressBar.tsx       # Loading progress indicator
    WatchlistButton.tsx   # Add to watchlist (future)
  lib/
    api.ts               # API client with retry, caching, wake-up logic
    types.ts             # TypeScript type definitions (NEEDS CONSOLIDATION)
```

---

## 9. Data Strategy

### 9.1 Data Sources

| Source | Data Type | Reliability | Cost | Risk |
|--------|-----------|-------------|------|------|
| EastMoney HTTP API | Real-time quotes, historical OHLCV, stock list, search | Medium -- undocumented, no SLA | Free | Could block IP, change endpoints, or add CAPTCHA at any time |
| Yahoo Finance (yfinance) | Historical OHLCV, basic fundamentals | Medium -- occasionally rate-limited for A-shares | Free | A-share data quality is inconsistent |
| GLM-4 (Zhipu AI) | AI text analysis | Medium -- API-based | Free tier (limited) | Quota limits, pricing changes |

### 9.2 Data Freshness

| Data Type | Update Frequency | Cache Duration |
|-----------|-----------------|----------------|
| Stock real-time quote | On each query | 3 minutes |
| Stock historical OHLCV | Daily after market close | Until next trading day |
| Technical indicators | On each query (derived from history) | 3 minutes (with quote) |
| AI analysis | On each query | 30 minutes |
| Daily recommendations | Once daily at 17:30 | Until next generation |
| Market overview | On each query | 3 minutes |
| AI rankings | On query or refresh | 30 minutes |

### 9.3 Data Source Mitigation Plan

Since EastMoney is an undocumented API, the following mitigations are required:

1. **Request throttling**: Max 10 requests per second to EastMoney to avoid IP blocking
2. **User-Agent rotation**: Rotate browser-like User-Agent strings
3. **Response validation**: Validate all EastMoney responses before use; treat malformed responses as errors
4. **Fallback chain**: EastMoney -> Yahoo Finance -> cached data -> error message
5. **Monitoring**: Log all data source failures, track failure rate trends
6. **Alternative evaluation**: Continuously evaluate licensed data providers (Tushare Pro, Wind, Choice) for v2.0

### 9.4 Database Schema

The current schema (as documented in DESIGN.md) is well-designed. One refinement recommended:

**Add a `data_source_log` table** for monitoring data source health:

```sql
CREATE TABLE data_source_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(50) NOT NULL,          -- 'eastmoney', 'yahoo', 'glm4'
    endpoint VARCHAR(200),                -- specific API endpoint
    status VARCHAR(20) NOT NULL,          -- 'success', 'error', 'timeout'
    response_time_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_data_source_log_source_time ON data_source_log(source, created_at);
```

---

## 10. Compliance and Legal Framework

### 10.1 Regulatory Context

In China, providing investment advisory services requires a license from the China Securities Regulatory Commission (CSRC). Stock Advisor must carefully position itself as an **information tool**, not an **advisory service**.

### 10.2 Compliance Positioning

| Activity | Permitted | Prohibited |
|----------|-----------|------------|
| Displaying technical indicator calculations | YES | - |
| Showing factual market data | YES | - |
| Providing educational explanations of strategies | YES | - |
| Displaying AI-generated analysis as "reference information" | YES (with disclaimers) | - |
| Tracking historical system-generated signals | YES | - |
| Claiming to provide "investment advice" | - | NO |
| Guaranteeing returns or profits | - | NO |
| Soliciting investment decisions | - | NO |
| Charging for advisory services without license | - | NO |
| Displaying live trading orders or portfolio management | - | NO |

### 10.3 Required Disclaimers

**Site-Wide Disclaimer** (footer of every page):

```
Disclaimer:

1. All information, analysis, and suggestions provided by this system are for reference
   only and do not constitute investment advice of any kind.

2. The stock market carries risk. Past performance does not guarantee future results.
   Investors should make independent investment decisions based on their own financial
   situation, risk tolerance, and investment objectives.

3. The stock screening strategies in this system are based on historical data and
   technical analysis. They cannot guarantee future returns, and investors may face
   the risk of principal loss.

4. This system does not provide securities investment advisory services and does not
   hold a securities investment advisory qualification.

5. Technical indicators and scoring systems are computational tools for reference only.
   They do not represent professional analysis opinions or recommendations.

6. By using this system, you acknowledge that you have read, understood, and agreed to
   the above statements.
```

**Per-Recommendation Disclaimer** (on each stock card/detail):

```
This analysis is system-generated based on technical indicators and is for reference
only. It does not constitute a buy or sell recommendation. Please make your own
investment decisions and manage risk accordingly.
```

### 10.4 Language Guidelines

| Use | Do Not Use |
|-----|------------|
| "Analysis result" | "Investment advice" |
| "Technical signal" | "Buy recommendation" |
| "Reference information" | "Expert opinion" |
| "Strategy backtesting" | "Guaranteed returns" |
| "Historical performance" | "Expected profits" |
| "Observation" or "Watch" | "Must buy" |

### 10.5 Compliance Review Checklist

- [ ] All UI text reviewed for compliance with the above language guidelines
- [ ] Disclaimer visible on every page
- [ ] No guarantees of profit anywhere in the system
- [ ] "Suggestion" labels clearly framed as technical signals, not advice
- [ ] Terms of Service page created
- [ ] Privacy Policy page created (even though no user data is collected in MVP)

---

## 11. Testing Strategy

### 11.1 Testing Philosophy

This is a **financial data application**. Incorrect calculations or misleading information can cause real financial harm. Testing rigor must be higher than a typical CRUD application.

### 11.2 Test Pyramid

```
                    /\
                   /  \
                  / E2E \          5 critical user journeys
                 /--------\
                /Integration\      API endpoint tests + data source tests
               /--------------\
              /   Unit Tests    \  Indicator calculations + strategy logic
             /--------------------\
```

### 11.3 Test Categories

#### Unit Tests (P0 -- Required Before Launch)

| Area | Scope | Target Coverage |
|------|-------|----------------|
| Technical Indicators | MACD, RSI, KDJ, MA, BOLL, ATR calculations | 95% |
| Trading Suggestion | Buy price, stop loss, take profit calculations | 95% |
| Scoring System | Composite score calculation | 90% |
| Strategy Logic | Golden cross, RSI bounce, MA alignment, volume-price | 90% |
| Data Transformation | API response formatting, type conversions | 85% |

**Framework**: pytest (backend), Jest (frontend)

#### Integration Tests (P1 -- Required for v1.1)

| Area | Scope | Notes |
|------|-------|-------|
| API Endpoints | All FastAPI routes with real-like data | Mock external services |
| Data Source Failover | EastMoney failure -> Yahoo fallback | Simulate network failures |
| AI Fallback | GLM-4 failure -> template fallback | Simulate API timeout |
| Database Operations | CRUD for recommendations and tracking | Test against Supabase test schema |
| Cache Behavior | Cache hit/miss/expiration/invalidation | Verify timing logic |

#### E2E Tests (P1 -- Required for v1.1)

| Flow | Steps | Tool |
|------|-------|------|
| Stock Query | Open home -> Enter code -> View analysis | Playwright |
| Daily Recommendations | Open home -> View recommendations -> Click detail | Playwright |
| Search Flow | Open home -> Search by name -> View results -> Click stock | Playwright |
| Error Handling | Enter invalid code -> See error -> Retry | Playwright |
| Mobile Responsiveness | All flows on 375px viewport | Playwright |

#### Performance Tests (P2)

| Test | Target |
|------|--------|
| Concurrent stock queries | 10 simultaneous queries complete within 20 seconds each |
| Recommendation generation under load | Completes within 15 minutes even with parallel queries |
| Frontend load test | 50 simultaneous page loads, all render within 5 seconds |

### 11.4 Test Data Strategy

- **Stock data**: Use a fixed set of 5 well-known stocks (600519, 000001, 300750, 000333, 512930) for all tests
- **Historical data**: Create fixtures with known indicator values for verification
- **AI responses**: Mock GLM-4 responses with representative examples

### 11.5 Test Automation Plan

| Phase | Action | Timeline |
|-------|--------|----------|
| Now | Add unit tests for indicator_service.py and strategy_service.py | Sprint 1 |
| v1.1 | Add API integration tests with mocked services | Sprint 2 |
| v1.1 | Set up Playwright E2E tests for critical flows | Sprint 2 |
| v2.0 | Add performance tests | Sprint 4 |
| Ongoing | Run tests on every PR via GitHub Actions | Sprint 2 onward |

---

## 12. Development Roadmap

### 12.1 Phase 0: Stabilization (Current -- 1 Week)

**Goal**: Fix all critical bugs and achieve release-ready quality.

| Task | Priority | Effort | Owner | Status |
|------|----------|--------|-------|--------|
| Deploy search route fix to Render | P0 | 10 min | DevOps | Pending |
| Verify and remove hardcoded API key | P0 | 30 min | Backend | In progress |
| Regenerate recommendations (10 stocks) | P0 | 5 min | Operations | Pending |
| Investigate and fix `prev_close` null issue | P1 | 2 hours | Backend | Open |
| Remove dead code in frontend (`aiRankingsCache`) | P1 | 15 min | Frontend | Open |
| Consolidate `AIRankingItem` type definitions | P1 | 30 min | Frontend | Open |
| Add unit tests for indicator calculations | P0 | 1 day | Testing | Open |
| Review all UI text for compliance language | P0 | 2 hours | Product | Open |
| Add rate limiting middleware | P1 | 2 hours | Backend | Open |

**Exit Criteria**: All P0 bugs fixed, unit tests for indicators passing, QA sign-off.

### 12.2 Phase 1: Soft Launch (Weeks 2-3)

**Goal**: Release to a small group of users (friends, colleagues, WeChat group) and gather feedback.

| Task | Priority | Effort |
|------|----------|--------|
| Complete performance tracking feature (tracking logic + stats calculation) | P0 | 3 days |
| Add K-line chart component (lightweight, e.g., lightweight-charts) | P1 | 2 days |
| Improve search with Chinese name fuzzy matching | P1 | 1 day |
| Add "last updated" timestamp to all data displays | P0 | 0.5 day |
| Add "market closed" state to home page | P0 | 0.5 day |
| Create proper error pages (404, 500, timeout) | P0 | 1 day |
| Set up GitHub Actions CI (lint + test + build) | P1 | 0.5 day |
| Integrate Playwright E2E tests for critical flows | P1 | 2 days |
| User feedback collection mechanism (simple form/link) | P1 | 0.5 day |

**Exit Criteria**: 10+ users testing for 1 week, core feedback collected, no critical bugs.

### 12.3 Phase 2: Public Launch (Weeks 4-6)

**Goal**: Open to public, establish daily usage pattern, validate recommendation accuracy.

| Task | Priority | Effort |
|------|----------|--------|
| Statistics dashboard page (`/stats`) | P1 | 3 days |
| Recommendation history page (`/history`) | P1 | 2 days |
| Expand stock screening universe to 100+ stocks | P1 | 2 days |
| Upgrade Render to paid plan (if traffic warrants) | P1 | 1 hour |
| SEO optimization (meta tags, structured data) | P1 | 1 day |
| Add basic analytics (page views, popular queries) | P2 | 1 day |
| Performance optimization (lazy loading, code splitting) | P2 | 2 days |
| Share functionality (generate image for WeChat sharing) | P2 | 2 days |

**Exit Criteria**: 50+ DAU, recommendation system running 30+ days with published performance stats.

### 12.4 Phase 3: Growth and Enhancement (Weeks 7-12)

**Goal**: Improve product quality, add differentiating features, grow user base.

| Feature | Priority | Effort |
|---------|----------|--------|
| Full market screening (5000+ stocks, background job) | P1 | 1 week |
| Backtesting module (historical strategy performance) | P2 | 1 week |
| Multi-timeframe analysis (weekly, monthly) | P2 | 3 days |
| News sentiment integration | P2 | 1 week |
| User accounts and watchlists | P2 | 1 week |
| Push notifications (WeChat mini-program or PWA) | P2 | 1 week |
| Evaluate licensed data source migration | P1 | 2 days |

---

## 13. Risk Assessment

### 13.1 Risk Matrix

| ID | Risk | Probability | Impact | Severity | Mitigation |
|----|------|-------------|--------|----------|------------|
| R1 | EastMoney blocks our IP or changes API | Medium | High | HIGH | Yahoo fallback; monitor for changes; evaluate licensed alternatives |
| R2 | GLM-4 API becomes paid-only or unavailable | Medium | Medium | MEDIUM | Template fallback already implemented; evaluate alternative LLMs |
| R3 | Render cold start deters first-time users | High | Medium | HIGH | Wake-up mechanism exists; plan paid upgrade at 50 DAU |
| R4 | Recommendation accuracy is poor (< 50% win rate) | Medium | High | HIGH | Transparent tracking builds trust even if win rate is moderate; improve strategies based on data |
| R5 | Regulatory action for resembling advisory service | Low | Critical | HIGH | Strict compliance language; no advisory claims; clear disclaimers |
| R6 | API key exposure leads to GLM-4 quota abuse | High (if not fixed) | Medium | HIGH | IMMEDIATE: Move to env variable, rotate key |
| R7 | No users adopt the product | Medium | Medium | MEDIUM | Soft launch with known community; iterate based on feedback |
| R8 | AKShare/EastMoney data is inaccurate | Low | High | MEDIUM | Cross-validate with Yahoo Finance; display data source timestamp |
| R9 | Supabase free tier limits hit | Low | Medium | LOW | Monitor usage; upgrade plan when needed ($25/month) |
| R10 | Technical debt accumulates (no tests, dead code) | High | Medium | HIGH | Phase 0 stabilization; CI enforcement; test coverage targets |

### 13.2 Top 3 Risks Requiring Immediate Action

1. **R6 (API Key Exposure)**: Action within 24 hours. Rotate key, ensure env variable is used, verify no hardcoded fallback in production.

2. **R3 (Cold Start UX)**: Monitor user drop-off during cold start. If >30% abandon rate, upgrade Render within 1 week.

3. **R10 (Technical Debt)**: Phase 0 stabilization must complete before any new feature work. Enforce this as a blocking gate.

---

## 14. Success Metrics and Acceptance Criteria

### 14.1 Launch Readiness Checklist

**P0 -- Must Complete (Blocking)**:
- [ ] All critical bugs fixed (BUG-001, SEC-001)
- [ ] Unit tests for indicator calculations passing
- [ ] Compliance language review completed
- [ ] Full disclaimer visible on every page
- [ ] Mobile responsiveness verified on 3 device sizes
- [ ] API response format consistent (no null critical fields)
- [ ] Error handling for all failure modes (data unavailable, AI down, market closed)
- [ ] Recommendations generate successfully with 10 stocks

**P1 -- Should Complete (Non-blocking)**:
- [ ] Rate limiting enabled
- [ ] Dead code removed
- [ ] Type definitions consolidated
- [ ] Performance tracking functional
- [ ] Stats page showing historical data

### 14.2 Feature Acceptance Matrix

| Feature | Acceptance Criteria | Test Method | Status |
|---------|--------------------|-----------  |--------|
| Stock Query | Returns full analysis for 600519, 000001, 300750, 000333, 512930 within 15s each | API test | Partial pass |
| Recommendations | Returns 10 stocks with all required fields, no nulls | API test | Needs regeneration |
| Market Overview | Returns both indices with numeric values | API test | Pass |
| Search | Returns results for "600519", "maotai", and "ETF" queries | API test | Pending deployment |
| AI Analysis | Returns structured analysis or graceful fallback | API test | Pass |
| Mobile UI | Renders correctly on 375px viewport | Visual test | Pass |
| Disclaimer | Visible on home, stock detail, and every recommendation | Visual test | Needs audit |

### 14.3 Performance Acceptance

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| Stock query (cached) | < 2s | API timing |
| Stock query (uncached) | < 15s | API timing |
| Home page load | < 3s | Lighthouse |
| Recommendation generation | < 10 min | Server logs |
| API error rate | < 1% | Monitoring |

### 14.4 Post-Launch Success Criteria (30 Days)

| Metric | Target | How to Measure |
|--------|--------|---------------|
| DAU | 50 | Analytics or server logs |
| Recommendation win rate | > 55% | Database tracking |
| Returning users (D7) | > 30% | Analytics |
| Critical bugs reported | < 3 | User feedback |
| System uptime (market hours) | > 99% | Health check monitoring |

---

## 15. Appendix: Design Audit Findings

### 15.1 Summary of Issues in Original DESIGN.md

| Category | Finding | Severity | Resolution in this PRD |
|----------|---------|----------|----------------------|
| Product Positioning | Too broad, mixes different user types | Medium | Section 3: Focused positioning statement; Section 5: Distinct personas |
| Market Analysis | Completely absent | High | Section 4: Market context, competitive landscape, niche definition |
| User Research | Surface-level personas without journeys | Medium | Section 5: Detailed personas, journey map, user flows |
| Compliance | Single disclaimer block, no strategy | High | Section 10: Full compliance framework with language guidelines |
| Testing | Entirely absent from design | Critical | Section 11: Complete testing strategy with pyramid, categories, data plan |
| Data Source Risk | Not addressed | High | Section 9.3: Mitigation plan for undocumented API dependency |
| Performance | Single metric (5s query) | Medium | Section 7.1: Comprehensive performance targets with gap analysis |
| Architecture | Well-documented but missing risk analysis | Medium | Section 8.3: Architecture concerns and improvement recommendations |
| Scoring Validation | No backtesting to validate scoring | High | Section 12 Phase 3: Backtesting module planned; transparent tracking in Phase 0-1 |
| Roadmap | Unrealistic 5-week timeline | High | Section 12: Revised phased roadmap with realistic estimates |
| Error UX | Only happy paths designed | Medium | Section 6: Edge cases and error states in acceptance criteria |
| Monitoring | Not mentioned | Medium | Section 9.4: Data source logging; Section 14: monitoring metrics |

### 15.2 Code Quality Issues (From QA Report + Code Audit)

| Issue | File | Severity | Recommended Fix |
|-------|------|----------|----------------|
| Hardcoded API key | `ai_analysis_service.py:15`, `glm_service.py:18` | CRITICAL | Move to env variable, rotate key |
| Route conflict (fixed but undeployed) | `stock.py` (original) | CRITICAL | Already fixed to `/stocks/search`, deploy to Render |
| Dead code | `api.ts:19-20` (aiRankingsCache) | MAJOR | Remove unused variables |
| Duplicate types | `api.ts` vs `types.ts` (AIRankingItem) | MAJOR | Single source of truth in types.ts |
| Bare except clauses | `strategy_service.py` (multiple) | MINOR | Catch specific exceptions, log errors |
| Debug endpoint in production | `main.py:57` (`/debug/stock/{code}`) | MINOR | Remove or gate behind debug flag |
| Version mismatch | `main.py:37` returns "2.0.0", title says "2.1.0" | MINOR | Centralize version string |

### 15.3 Actual vs Documented Architecture Differences

| Aspect | DESIGN.md Says | Reality |
|--------|---------------|---------|
| Data source | AKShare | EastMoney HTTP API (AKShare abandoned) |
| AI model | Not specified for Phase 1 | GLM-4 already integrated |
| Frontend framework | React + TypeScript | Next.js 15 + React 18 + TypeScript |
| Recommendation count | Top 5 | Code says top 10, database has 5 |
| AI rankings | Not in design | Implemented at `/rankings/ai` |
| Stock universe | Full market scan | ~60 curated stocks only |
| Technical indicator library | pandas-ta | ta (Python) |

**Recommendation**: Keep the DESIGN.md as a historical document. This PRD supersedes it as the authoritative product specification. The DESIGN.md should be updated with a header noting "Superseded by PRD.md as of 2026-02-08."

---

*End of PRD Document*

*This document is maintained by the Product Orchestrator and should be reviewed and updated at the start of each development phase.*
