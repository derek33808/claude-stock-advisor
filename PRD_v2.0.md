# Stock Advisor PRD v2.0 - A股智能交易策略系统

| Field | Value |
|-------|-------|
| Document Version | v2.0 |
| Created | 2026-02-08 |
| Author | Product Orchestrator |
| Status | Final Draft |
| Project Location | `projects/software/stock-advisor/` |
| Supersedes | PRD.md v1.0, DESIGN.md v2.0 |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Vision and Positioning](#2-product-vision-and-positioning)
3. [User Research](#3-user-research)
4. [Functional Requirements](#4-functional-requirements)
5. [Technical Architecture](#5-technical-architecture)
6. [Data Strategy](#6-data-strategy)
7. [Database Design](#7-database-design)
8. [API Design](#8-api-design)
9. [UI/UX Design](#9-uiux-design)
10. [Compliance Framework](#10-compliance-framework)
11. [Development Roadmap](#11-development-roadmap)
12. [Success Metrics](#12-success-metrics)
13. [Testing Strategy](#13-testing-strategy)

---

## 1. Executive Summary

### 1.1 Vision

Build a free, intelligent A-share trading strategy advisory tool that provides individual investors with **multi-dimensional AI analysis** combining technical indicators, fundamental data, real-time news, earnings reports, and industry analysis -- all synthesized into actionable insights accessible via a mobile-friendly web interface.

### 1.2 Problem Statement

Individual A-share investors face four core challenges:

1. **Information fragmentation**: Investors must visit 5+ different platforms to gather technical data, financial reports, news, industry analysis, and analyst opinions. There is no single tool that synthesizes all dimensions for a given stock.
2. **Time constraints**: Working professionals cannot dedicate hours to daily stock screening, reading earnings reports, tracking industry trends, and monitoring news flow.
3. **Lack of accountability**: Most stock tips from social media, WeChat groups, and paid advisory services have no transparent track record. Investors cannot verify whether recommendations actually perform well over time.
4. **No systematic learning loop**: Investors repeat the same mistakes because they have no tool to review their past analysis against actual outcomes.

### 1.3 Solution

Stock Advisor v2.0 provides:

- **AI Comprehensive Analysis**: Enter any A-share code, receive a multi-dimensional analysis in 3-5 seconds covering technical indicators, fundamentals, recent news, earnings, and industry positioning
- **Daily Smart Recommendations**: 10 curated stocks every trading day at 17:30, each with full AI comprehensive analysis
- **Watchlist Management**: Add stocks you own or are tracking, with full AI analysis and one-click refresh
- **Global Refresh**: Update all analysis (recommendations + watchlist) with a single action, with progress tracking and token cost monitoring
- **Historical Review with Prediction Tracking**: Automatically save daily analysis snapshots, compare predictions against actual results after 5 trading days, and display accuracy statistics

### 1.4 Core Differentiators vs PRD v1.0

| Dimension | PRD v1.0 | PRD v2.0 |
|-----------|----------|----------|
| Analysis Depth | Technical indicators only + basic AI summary | 5-dimensional analysis (technical + fundamental + news + earnings + industry) |
| News Integration | Not included | Real-time news (7 days), earnings reports, major announcements |
| Industry Analysis | Not included | Industry trends, policy impact, peer comparison, capital flow |
| User Portfolio | Not included | Watchlist with full analysis and refresh |
| Prediction Tracking | Basic recommendation history | Automated 5-day prediction vs actual comparison with accuracy stats |
| Token Cost Control | Not considered | Real-time token usage monitoring with alert thresholds |
| K-Line Chart | Planned for v1.1 | Deferred (too complex for current scope) |

### 1.5 Key Metrics (North Stars)

| Metric | Target (30 days post-launch) | Target (90 days) |
|--------|------------------------------|-------------------|
| Daily Active Users (DAU) | 50 | 500 |
| Stock Queries per Day | 200 | 2,000 |
| Watchlist Additions per User | 3 | 8 |
| Prediction Accuracy Rate | > 55% | > 60% |
| Average Session Duration | > 5 min | > 8 min |
| Returning Users (D7 retention) | > 35% | > 50% |

---

## 2. Product Vision and Positioning

### 2.1 Product Definition

Stock Advisor v2.0 is a **free, web-based A-share comprehensive analysis platform** that combines quantitative technical analysis with AI-powered fundamental, news, and industry analysis to give individual investors a 360-degree view of any stock in seconds.

**What Stock Advisor IS:**
- A multi-dimensional data aggregation and analysis tool
- A technical indicator calculator with trend prediction
- An AI-powered news and earnings report interpreter
- An industry positioning and peer comparison tool
- A transparent prediction tracking system with accountability

**What Stock Advisor is NOT:**
- An investment advisory service (no advisory license)
- A trading platform (no order execution)
- A guaranteed profit system (no performance guarantees)
- A replacement for professional financial advice

### 2.2 Differentiation Strategy

| Dimension | Broker Apps (Tonghuashun) | Paid Advisory | Stock Advisor v2.0 |
|-----------|--------------------------|---------------|---------------------|
| Price | Free | 500-5000 RMB/month | Free |
| Technical Analysis | Raw indicators, user interprets | Analyst reports (delayed) | Automated interpretation with actionable suggestions |
| News Analysis | News feed (user reads manually) | Analyst summaries | AI synthesized impact analysis per stock |
| Earnings Analysis | Raw financial tables | Quarterly reports | AI interpreted key metrics with trend analysis |
| Industry Context | Sector indices | Occasional industry reports | Real-time industry trends, peer comparison, capital flow |
| Prediction Tracking | None | Opaque track record | Transparent 5-day prediction vs actual comparison |
| Watchlist Intelligence | Price alerts only | N/A | Full AI analysis with one-click refresh |
| Accessibility | Complex interfaces | Reports via WeChat/email | Mobile-first web app, instant access |

### 2.3 Positioning Statement

For individual A-share investors who want a quick, comprehensive understanding of any stock without visiting multiple platforms, Stock Advisor is a free web tool that synthesizes technical analysis, earnings data, news flow, and industry trends into a single AI-powered analysis in under 5 seconds, and uniquely tracks its own prediction accuracy to build user trust.

---

## 3. User Research

### 3.1 Primary Persona: "The Informed Part-Timer"

| Attribute | Detail |
|-----------|--------|
| Name | Li Wei (Archetype) |
| Age | 28-45 |
| Occupation | Tech professional, middle management, small business owner |
| Investment Experience | 2-5 years, understands basic technical analysis concepts |
| Portfolio Size | 50,000 - 500,000 RMB |
| Daily Time for Investing | 10-30 minutes |
| Current Behavior | Checks Tonghuashun for prices, reads Xueqiu for discussion, occasionally checks Dongfang Caifu for news. Has 5-15 stocks in mental watchlist. Makes 2-3 trades per week. |
| Pain Points | Cannot screen 5000+ stocks daily; misses important earnings reports and announcements; does not have time to research industry trends; relies on tips from colleagues/WeChat groups with no accountability |
| Goals | Find 2-3 good entry opportunities per week; understand the full picture before buying; manage risk with clear stop-loss levels; learn from past decisions |
| Technology | Uses smartphone primarily, occasionally laptop; comfortable with web apps |
| Key Question | "Is this stock worth buying right now, and why?" |

### 3.2 User Scenarios

**Scenario 1: Morning Quick Check (5 minutes)**
```
Li Wei opens Stock Advisor during commute.
-> Views today's 10 recommended stocks
-> Taps on one that catches his eye (e.g., a semiconductor stock)
-> Reads: technical signals bullish, latest earnings beat expectations,
   industry benefiting from government subsidies, peer comparison favorable
-> Notes the buy price range and stop loss
-> Adds to watchlist for monitoring
-> Total time: 4 minutes
```

**Scenario 2: Pre-Trade Research (10 minutes)**
```
Li Wei hears about a stock from a colleague during lunch.
-> Opens Stock Advisor, enters the stock code
-> AI analysis generates in 3 seconds
-> Reads comprehensive analysis:
   - Technical: MACD about to golden cross, RSI healthy
   - Fundamentals: PE below industry average, revenue growing 15% YoY
   - Recent News: Company signed major contract 3 days ago
   - Earnings: Latest quarterly report shows profit up 20%
   - Industry: Sector is in uptrend, policy support expected
-> Decides to place a limit order at the suggested buy range
-> Total time: 8 minutes
```

**Scenario 3: Weekend Review (15 minutes)**
```
Li Wei reviews his investment performance on Saturday morning.
-> Opens watchlist, sees all his holdings with current analysis
-> Clicks "Historical Review" on a stock he bought 2 weeks ago
-> Sees timeline: Day 1 prediction "bullish, target 15% upside"
-> Sees Day 5 actual result: stock up 8%, prediction partially correct
-> Reviews accuracy statistics: his watchlist predictions 62% accurate
-> Adjusts his strategy based on patterns
-> Total time: 12 minutes
```

**Scenario 4: Earnings Season Deep Dive (10 minutes)**
```
It is earnings season. Li Wei wants to check if any of his stocks reported.
-> Opens watchlist, clicks "Refresh All"
-> Progress bar shows 8/12 stocks refreshed
-> Three stocks have new earnings data flagged
-> Reads AI interpretation of one earnings report:
   "Revenue beat consensus by 12%, but margin compressed due to
   raw material costs. Forward guidance cautious. Mixed signal."
-> Decides to hold but tighten stop loss
-> Total time: 10 minutes
```

### 3.3 Key User Flows

**Flow 1: Single Stock Analysis**
```
Home -> Enter stock code -> Loading (3-5s) -> View 5-dimensional AI analysis
     -> Read technical signals -> Read news impact -> Read earnings summary
     -> Read industry context -> Note trading suggestion -> [Add to Watchlist]
```

**Flow 2: Daily Recommendation Browse**
```
Home -> View 10 recommended stocks (cards) -> Tap for detail
     -> Full AI analysis -> [Add to Watchlist] or [Dismiss]
```

**Flow 3: Watchlist Management**
```
Home -> Watchlist tab -> View all watchlist stocks with analysis
     -> [Refresh Single] or [Refresh All] -> Updated analysis
     -> [Remove from Watchlist]
```

**Flow 4: Historical Review**
```
Watchlist -> Select stock -> History tab -> View timeline of past analyses
         -> View prediction vs actual comparison -> View accuracy stats
         -> Adjust investment thesis
```

**Flow 5: Global Refresh**
```
Home -> Click "Refresh All" -> Progress bar (1-2 min)
     -> Token usage indicator -> All stocks updated
     -> [View token usage summary]
```

---

## 4. Functional Requirements

### 4.1 Priority Framework

- **P0 (Must-Have)**: Required for v2.0 launch. System cannot deliver its core value without these.
- **P1 (Should-Have)**: Significantly improves user experience. Target for v2.1.
- **P2 (Nice-to-Have)**: Differentiators for future growth.

### 4.2 Feature 1: AI Comprehensive Analysis [P0]

**Description**: User enters any A-share stock code and receives a multi-dimensional AI analysis in 3-5 seconds that synthesizes 5 analysis dimensions into a coherent investment thesis.

**Input**: Stock code (6-digit number, e.g., 600519, 000001, 512930)

**Output -- 5 Analysis Dimensions**:

#### Dimension 1: K-Line Technical Analysis + Trend Prediction

| Data Point | Source | Details |
|------------|--------|---------|
| Technical Indicators | Calculated from 60-day history | MACD (DIF/DEA/histogram + signal), RSI (value + level), MA (5/10/20/60 + alignment), KDJ (K/D/J), BOLL (upper/mid/lower + position), ATR, Volume Ratio |
| Trend Prediction | AI (GLM-4) | Short-term (1-5 days) and medium-term (5-20 days) trend prediction based on technical patterns |
| Trading Suggestion | Algorithm + AI | Action (buy/hold/sell/wait), buy price range, stop loss, take profit 1 & 2, holding period, position size, risk level |
| Composite Score | Weighted calculation | 0-100 score: technical 40%, pattern 30%, momentum 20%, volume 10% |

#### Dimension 2: Company Basic Information

| Data Point | Source | Details |
|------------|--------|---------|
| Company Name | Data API | Full Chinese name |
| Stock Code | Input | With exchange prefix (SH/SZ) |
| Industry | Data API | CSRC industry classification |
| Market Cap | Data API | Total and circulating market cap |
| Business Description | AI (GLM-4) | 2-3 sentence description of core business |
| Key Products | AI (GLM-4) | Main revenue-driving products/services |

#### Dimension 3: Fundamental Analysis

| Data Point | Source | Details |
|------------|--------|---------|
| Valuation Metrics | AKShare / EastMoney | PE (TTM), PB, PS ratios with industry comparison |
| Profitability | AKShare | ROE, ROA, gross margin, net margin |
| Growth | AKShare | Revenue YoY, profit YoY, 3-year CAGR |
| Financial Health | AKShare | Debt-to-equity ratio, current ratio, cash flow |
| AI Interpretation | GLM-4 | 3-5 sentence interpretation of financial position |

#### Dimension 4: Recent Developments (Core Differentiator)

| Data Point | Source | Time Range | Details |
|------------|--------|------------|---------|
| Latest Earnings | AKShare | Most recent quarter | Revenue, net profit, YoY change, key highlights |
| Important News | EastMoney News API | Last 7 days | Top 5 most relevant news items with AI impact assessment |
| Major Announcements | AKShare | Last 30 days | Dividends, share issuance, restructuring, executive changes |
| AI News Impact | GLM-4 | Synthesized | Overall sentiment (positive/neutral/negative), key factors, risk alerts |

#### Dimension 5: Industry Analysis (Core Differentiator)

| Data Point | Source | Details |
|------------|--------|---------|
| Industry Trend | Industry index data | Industry index performance (1-week, 1-month, 3-month change) |
| Policy Impact | AI (GLM-4) + News | Government policies affecting the industry, regulatory changes |
| Peer Comparison | AKShare | Top 5 industry leaders: name, market cap, PE, revenue growth, stock performance |
| Industry Capital Flow | EastMoney | Net capital inflow/outflow for the industry sector |
| Industry Heat | Calculated | Relative trading volume and attention vs. market average |
| AI Industry Summary | GLM-4 | 3-5 sentence summary of industry outlook and stock's position within it |

**AI Comprehensive Summary**:

After all 5 dimensions are gathered, GLM-4 generates a unified summary that:
- Synthesizes all 5 dimensions into a coherent investment thesis
- Highlights the top 3 positive factors and top 3 risk factors
- Provides a clear recommendation: Strong Buy / Buy / Hold / Reduce / Avoid
- Includes confidence level: High / Medium / Low
- Gives a specific prediction: expected price range in 5 trading days

**Performance Requirements**:
| Scenario | Target Response Time |
|----------|---------------------|
| Cached data (within 30 minutes) | < 2 seconds |
| Fresh data, all dimensions | 3-5 seconds |
| AI service degraded (fallback mode) | < 3 seconds (partial analysis) |

**Acceptance Criteria**:
- [ ] Accepts any valid A-share code (SH/SZ main board, SME, ChiNext, STAR, ETFs)
- [ ] Returns all 5 dimensions with no critical null fields
- [ ] AI comprehensive summary integrates all available dimensions
- [ ] Gracefully handles missing data for any single dimension (show available data, flag unavailable)
- [ ] Works when AI is unavailable (template fallback for summary, raw data still displayed)
- [ ] Technical indicators match manual calculation within 0.1% tolerance
- [ ] News data is from the last 7 days (not stale)
- [ ] Earnings data reflects the most recently filed report

**Edge Cases**:
- Stock suspended: Show last available data with "suspended" status, skip real-time quote
- Market closed: Show last closing data with "market closed" indicator
- New stock (< 60 days history): Show available data with "insufficient technical history" warning; fundamental and news analysis still available
- ETF: Technical analysis and basic info available; fundamental analysis shows fund-level data; news shows ETF-related news
- No recent news: Display "No significant news in the past 7 days" with positive framing
- Earnings report not yet filed for current quarter: Show last available quarter with date label

### 4.3 Feature 2: Daily Smart Recommendations [P0]

**Description**: System automatically generates 10 recommended stocks every trading day at 17:30 CST. Each recommendation includes the full AI comprehensive analysis (identical to Feature 1 output).

#### 4.3.1 Hot Stock Universe Definition

The recommendation pipeline draws candidates from a curated "Hot Stock Universe" that is maintained as follows:

**Universe Composition**:
- **Target Size**: 50-80 stocks at any given time
- **Source**: Combination of EastMoney sector hot stock lists (`stock_board_industry_index_em`) + AKShare industry leaders (`stock_board_industry_cons_em`) + top traded stocks by turnover

**Inclusion Criteria** (all must be met):
| Criterion | Threshold | Rationale |
|-----------|-----------|-----------|
| Market Cap | > 5 billion RMB | Ensures sufficient liquidity and analyst coverage |
| Average Daily Turnover | > 100 million RMB (20-day average) | Ensures tradability for retail investors |
| Listing Age | > 1 year (> 250 trading days) | Ensures sufficient technical history |
| Status | Not ST, not *ST, not suspended | Avoids high-risk/untradable stocks |
| Industry Coverage | At least 5 distinct CSRC industry sectors represented | Ensures diversification across sectors |

**Exclusion Rules**:
- ST or *ST stocks (special treatment for financial distress)
- Stocks suspended from trading
- Stocks listed less than 1 year (insufficient historical data for technical analysis)
- Stocks with average daily turnover below 100M RMB (low liquidity risk)
- B-shares (only A-shares are in scope)

**Storage**: `hot_stock_universe` table in Supabase:
```sql
CREATE TABLE hot_stock_universe (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(10) NOT NULL UNIQUE,      -- Stock code
    name VARCHAR(50) NOT NULL,             -- Stock name
    industry VARCHAR(50),                  -- CSRC industry classification
    market_cap DECIMAL(15,2),              -- Market cap in RMB
    avg_turnover_20d DECIMAL(15,2),        -- 20-day average daily turnover
    listing_date DATE,                     -- IPO date
    added_at TIMESTAMPTZ DEFAULT NOW(),    -- When added to universe
    last_validated_at TIMESTAMPTZ,         -- Last validation check
    is_active BOOLEAN DEFAULT TRUE,        -- Soft delete for removed stocks
    removal_reason VARCHAR(100)            -- Why removed (if inactive)
);

CREATE INDEX idx_hot_universe_active ON hot_stock_universe(is_active);
CREATE INDEX idx_hot_universe_industry ON hot_stock_universe(industry);
```

**Update Mechanism**:
| Aspect | Detail |
|--------|--------|
| Refresh Frequency | Weekly (every Monday at 09:00 before market open) |
| Update Process | 1) Fetch current sector leaders from EastMoney/AKShare; 2) Validate all inclusion criteria; 3) Add qualifying new stocks; 4) Remove stocks that no longer meet criteria; 5) Log all changes |
| Manual Override | Admin can manually add/remove stocks via direct database update |
| Fallback | If weekly refresh fails, use last known good list (staleness alert if > 2 weeks old) |
| Change Logging | All additions/removals logged with timestamp and reason for audit trail |

**Initial Seeding Strategy** (for v2.0 launch):
1. Select top 10 stocks by market cap from each of 6 key sectors (banking, tech, consumer, healthcare, energy, manufacturing) = ~60 stocks
2. Validate all meet inclusion criteria
3. Manually review and adjust for known problematic stocks
4. Store in `hot_stock_universe` table

**Recommendation Generation Pipeline**:
```
Stage 1: Universe Selection (~60 stocks from hot_stock_universe table)
  -> Excludes ST/suspended/new listings
  -> Requires market cap > 1B RMB
  -> Requires daily turnover > 50M RMB

Stage 2: Technical Screening (at least 1 strategy must trigger)
  -> MACD golden cross or approaching golden cross
  -> RSI oversold bounce (recovering from < 30)
  -> MA bullish alignment (MA5 > MA10 > MA20)
  -> Volume-price confirmation (price up + volume > 1.5x average)

Stage 3: Scoring and Ranking
  -> Calculate composite score for each qualifying stock
  -> Composite score > 60 to qualify
  -> Sort by score descending
  -> Select top 10

Stage 4: AI Comprehensive Analysis (for each of the 10)
  -> Run full 5-dimensional analysis (same as Feature 1)
  -> Generate comprehensive AI summary
  -> Store complete analysis in database
  -> Fallback to technical-only if AI is unavailable for some stocks
```

**Timing**: 17:30 CST on trading days (Monday-Friday, excluding holidays)

**Output**: 10 stocks, each with:
- Complete 5-dimensional AI analysis
- Specific entry/exit levels
- 5-day price prediction
- Risk assessment

**Acceptance Criteria**:
- [ ] Produces exactly 10 recommendations on trading days (or fewer if insufficient candidates)
- [ ] Each recommendation includes the complete 5-dimensional analysis
- [ ] All recommendations stored in database with date stamp
- [ ] No duplicate stocks in the same day's list
- [ ] Generation completes within 15 minutes (including AI analysis for 10 stocks)
- [ ] Token usage logged for each generation run
- [ ] Handles API failures gracefully (partial results acceptable, logged)

### 4.4 Feature 3: Watchlist Management [P0]

**Description**: Users can maintain a personal watchlist of stocks they own or are monitoring. Each watchlist stock displays the same comprehensive AI analysis as recommendations.

**Functionality**:

| Action | Trigger | Behavior |
|--------|---------|----------|
| Add to Watchlist | Click "Add to Watchlist" button on any stock analysis | Stock added with current analysis snapshot saved |
| View Watchlist | Navigate to Watchlist tab on home page | Display all watchlist stocks with latest analysis |
| Refresh Single Stock | Click refresh icon on individual stock card | Re-run 5-dimensional analysis for that stock |
| Remove from Watchlist | Click "Remove" button on stock card | Stock removed, history preserved |

**Data Storage**:
- Watchlist is stored server-side (Supabase) with a user identifier
- Each watchlist entry stores: stock code, add date, last analysis snapshot, last refresh timestamp

#### 4.4.1 Device Identity Mechanism

The MVP authentication uses a **locally-generated UUID** (not a computed browser fingerprint). This is a critical distinction:

**How It Works**:
1. On first visit, the frontend generates a UUID v4 (e.g., `a1b2c3d4-e5f6-7890-abcd-ef1234567890`)
2. The UUID is stored in `localStorage` under the key `stock_advisor_device_id`
3. All API requests include this UUID in the `X-Device-ID` header
4. The server uses this UUID to associate watchlist entries and analysis history with the user

**What This Means**:
- The identifier is a **random UUID stored in localStorage**, NOT a computed browser fingerprint
- If the user clears their browser data (localStorage), the UUID is lost
- The same user on different devices/browsers will have separate watchlists
- Private/incognito mode creates a temporary session that is lost when the window closes

**Data Loss Prevention -- Backup Code System [P0]**:

Since the UUID can be lost when localStorage is cleared, the system provides a backup mechanism:

| Feature | Description |
|---------|-------------|
| **Backup Code Generation** | On first visit (UUID creation), display a one-time "Your Recovery Code" dialog showing the UUID. User can copy/save it. |
| **Recovery Code Display** | Settings page shows the current device ID with a "Copy" button at all times |
| **Recovery Flow** | Settings page includes "Restore from Backup Code" input field. User pastes their UUID, system validates it exists in the database, and replaces the current localStorage UUID |
| **Export/Import** | Settings page provides "Export Watchlist (JSON)" button that downloads all watchlist stocks + their analysis history as a JSON file. "Import Watchlist" button to restore from exported file |

**Data Loss Recovery User Flow**:
```
User clears browser data -> Returns to Stock Advisor
  -> System generates new UUID (empty watchlist)
  -> User notices watchlist is empty
  -> User navigates to Settings
  -> Option A: Enters saved backup code -> Watchlist restored
  -> Option B: Imports previously exported JSON file -> Watchlist restored
  -> Option C: No backup available -> Must rebuild watchlist manually
```

**Watchlist Data Export [P0]**:
```
Export format (JSON):
{
  "exported_at": "2026-02-08T10:00:00Z",
  "device_id": "a1b2c3d4-...",
  "stocks": [
    {
      "code": "600519",
      "name": "贵州茅台",
      "added_at": "2026-02-01T10:00:00Z",
      "notes": ""
    }
  ],
  "analysis_history_count": 25
}
```

**API Endpoint for Recovery**:
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/device/validate` | POST | Check if a device_id exists in the database (returns stock count) |
| `/device/export` | GET | Export watchlist data as JSON (requires X-Device-ID header) |
| `/device/import` | POST | Import watchlist from JSON export (merges with current device) |

**Future Enhancement (v2.1)**: Add optional email-based account linking. User enters email, receives a magic link, and the email becomes a persistent identifier that survives device changes. The UUID-based system remains as the default for anonymous users.

**Display Requirements**:
- Watchlist stocks show identical detail level to recommendations
- Each stock card shows: name, code, current price, change%, composite score, AI recommendation, last refreshed timestamp
- Stocks sorted by: most recently added first (default), or by score, or by change%

**Acceptance Criteria**:
- [ ] User can add any stock from analysis page or recommendation list
- [ ] Watchlist persists across browser sessions (via UUID stored in localStorage)
- [ ] Backup code displayed on first visit and accessible from Settings page
- [ ] Recovery flow: entering a valid backup code restores watchlist access
- [ ] Watchlist export to JSON includes all stocks and metadata
- [ ] Watchlist import from JSON merges stocks into current device
- [ ] Watchlist displays full AI analysis for each stock
- [ ] Single-stock refresh completes within 5 seconds
- [ ] Remove action preserves historical analysis records
- [ ] Maximum 50 stocks per watchlist (with clear message when limit reached)

### 4.5 Feature 4: Global Refresh [P0]

**Description**: A single action that re-generates fresh AI comprehensive analysis for all stocks in both recommendations and watchlist.

**Behavior**:
```
User clicks "Refresh All"
  -> System counts total stocks: N (recommendations) + M (watchlist) = T
  -> Progress bar appears: "Refreshing 0/T stocks..."
  -> System processes stocks sequentially or in small batches (3 concurrent)
  -> Progress bar updates: "Refreshing 5/T stocks... (estimated 45 seconds remaining)"
  -> Token usage counter increments in real-time
  -> On completion: "All T stocks refreshed. Token usage: X/Y (Z% of daily limit)"
  -> If token limit approaching (> 80%): Warning banner appears
  -> If token limit exceeded: Stops processing, notifies user
```

**Token Monitoring**:

| Metric | Display Location | Alert Threshold |
|--------|-----------------|-----------------|
| Tokens used today | Header area, always visible | N/A |
| Daily token budget | Settings / info panel | N/A |
| Usage percentage | Progress bar tooltip | 80% = yellow warning |
| Token limit reached | Modal dialog | 100% = stop processing |
| Estimated cost per refresh | Refresh confirmation dialog | N/A |

**Performance Requirements**:
- Total refresh time for 20 stocks (10 recs + 10 watchlist): < 2 minutes
- Progress updates every 3 seconds minimum
- Partial completion is acceptable: if process fails mid-way, successfully refreshed stocks retain new data

**Acceptance Criteria**:
- [ ] Refreshes all recommendation and watchlist stocks in a single action
- [ ] Progress bar shows real-time progress (X/Y stocks completed)
- [ ] Estimated time remaining displayed
- [ ] Token usage tracked and displayed
- [ ] Warning displayed when token usage exceeds 80% of daily limit
- [ ] Processing stops gracefully when token limit reached
- [ ] Partial results preserved if process is interrupted
- [ ] User can cancel mid-process (already-refreshed stocks keep new data)

### 4.6 Feature 5: Watchlist Historical Review with Prediction Tracking [P0 -- Core Highlight]

**Description**: The system automatically saves a snapshot of every watchlist stock analysis daily at 17:30 (alongside recommendation generation). After 5 trading days, it compares the prediction made at analysis time against actual price movement, calculates prediction accuracy, and presents historical data in a timeline format.

**Automatic Daily Snapshot**:
```
Every trading day at 17:30:
  For each stock in any user's watchlist:
    1. Save current 5-dimensional analysis as a snapshot
    2. Record the prediction: {
         predicted_direction: "bullish" / "neutral" / "bearish",
         predicted_price_range: { low: X, high: Y },
         predicted_change_percent: Z%,
         confidence: "high" / "medium" / "low",
         key_factors: ["factor1", "factor2", "factor3"]
       }
    3. Set evaluation_date = current_date + 5 trading days
```

**5-Day Prediction Evaluation**:
```
On each trading day, check for snapshots where evaluation_date = today:
  For each such snapshot:
    1. Fetch actual price on evaluation_date
    2. Calculate actual_change_percent = (actual_price - predicted_price) / predicted_price * 100
    3. Determine accuracy:
       - Direction correct? (predicted bullish AND actual price up = correct)
       - Price range hit? (actual price within predicted range = correct)
       - Magnitude accuracy = 1 - abs(predicted_change - actual_change) / max(abs(predicted_change), 1)
    4. Update snapshot with actual results
    5. Recalculate running accuracy statistics
```

**Display -- Historical Review Page**:

**Section A: Timeline View**
```
Stock: 600519 Guizhou Moutai

[Timeline bar showing dates]

2026-02-01 | Score: 78 | Prediction: Bullish +3-5%
  -> Actual (5 days later): +4.2% [CORRECT]
  -> Key factors: MACD golden cross, strong earnings

2026-02-05 | Score: 72 | Prediction: Neutral 0-2%
  -> Actual (5 days later): -1.5% [PARTIALLY CORRECT - direction neutral range]
  -> Key factors: Industry downturn offset company strength

2026-02-10 | Score: 65 | Prediction: Bearish -2-5%
  -> Pending evaluation (2026-02-17)
  -> Key factors: RSI overbought, negative news
```

**Section B: Prediction Accuracy Statistics**
```
Accuracy Report for: 600519 (Last 30 days)

Direction Accuracy:    68% (17/25 predictions)
Price Range Accuracy:  52% (13/25 predictions)
Average Error:         2.3 percentage points

Best Prediction:  2026-01-20 (predicted +5%, actual +5.8%)
Worst Prediction: 2026-01-15 (predicted +3%, actual -4.2%)

Overall Grade: B+ (Reliable for directional calls)
```

**Section C: Improvement Suggestions**
```
Based on historical analysis patterns:
- The system tends to be over-optimistic on tech stocks (adjust for sector bias)
- Predictions during earnings season are less accurate (higher uncertainty)
- Short-term (1-3 day) predictions are more accurate than 5-day predictions
- Consider reducing position size when confidence is "low"
```

**Acceptance Criteria**:
- [ ] Analysis snapshot saved automatically at 17:30 for every watchlist stock
- [ ] 5-day evaluation executes automatically and updates prediction record
- [ ] Timeline displays all historical analyses for a given stock
- [ ] Each timeline entry shows: date, score, prediction, actual result, accuracy
- [ ] Accuracy statistics calculated and displayed: direction accuracy, range accuracy, average error
- [ ] Pending evaluations clearly marked with evaluation date
- [ ] At least 30 days of history retained per stock
- [ ] Historical data survives stock removal from watchlist (archived, viewable)

### 4.7 Deferred Features (Not in v2.0 Scope)

| Feature | Reason for Deferral | Target Version |
|---------|--------------------|--------------------|
| K-Line Interactive Chart | Too complex to implement well; existing tools serve this need | v3.0 |
| User Authentication | Not needed for MVP; device fingerprint sufficient | v2.1 |
| Full Market Screening (5000+ stocks) | Requires background job architecture | v3.0 |
| Push Notifications | Requires auth system + notification infrastructure | v3.0 |
| Multi-Timeframe Analysis | Scope creep risk; daily timeframe sufficient for target user | v2.1 |
| Backtesting Module | Useful but not required for core value delivery | v3.0 |

---

## 5. Technical Architecture

### 5.1 Architecture Overview

```
                         User (Mobile / Desktop Browser)
                                     |
                                     v
                     +-------------------------------+
                     |        Netlify CDN            |
                     |   Next.js 15 + React 18 + TS  |
                     |   Static site + client-side   |
                     +-------------------------------+
                                     |
                               HTTPS API calls
                                     |
                                     v
                     +-------------------------------+
                     |        Render (Backend)       |
                     |     FastAPI + Python 3.11     |
                     |                               |
                     |  +-------------------------+  |
                     |  | API Layer               |  |
                     |  | /stock/comprehensive    |  |
                     |  | /watchlist              |  |
                     |  | /analysis/history       |  |
                     |  | /refresh/all            |  |
                     |  | /industry               |  |
                     |  +-------------------------+  |
                     |  | Service Layer           |  |
                     |  | comprehensive_analysis  |  |
                     |  | news_service            |  |
                     |  | industry_service        |  |
                     |  | fundamental_service     |  |
                     |  | watchlist_service        |  |
                     |  | prediction_tracking     |  |
                     |  | token_monitor           |  |
                     |  | indicator_service       |  |
                     |  | strategy_service        |  |
                     |  +-------------------------+  |
                     |  | Caching Layer           |  |
                     |  | In-memory (3-30 min)    |  |
                     |  | DB-backed (news/industry)|  |
                     |  +-------------------------+  |
                     +-------------------------------+
                          |       |        |
                          v       v        v
               +-----------+ +---------+ +----------------+
               | Supabase  | | AKShare | | External APIs  |
               | PostgreSQL| | Library | | - EastMoney    |
               | - watchlist|          | | - EastMoney News|
               | - history | +---------+ | - GLM-4 API   |
               | - tracking|             | - Yahoo (FB)   |
               | - tokens  |             +----------------+
               +-----------+
```

### 5.2 Technology Stack

| Layer | Technology | Justification |
|-------|-----------|---------------|
| **Frontend** | Next.js 15 + React 18 + TypeScript + Tailwind CSS | Existing stack, SSG + client-side rendering, mobile-first |
| **Backend** | FastAPI 0.109 + Python 3.11 | Existing stack, async support, auto-docs, type validation |
| **Database** | Supabase (PostgreSQL) | Existing stack, free tier (500MB), real-time capabilities |
| **AI Model** | GLM-4 (Zhipu AI) | Existing integration, strong Chinese language analysis, cost-effective |
| **Market Data** | EastMoney HTTP API (primary) | Real-time quotes, historical OHLCV, comprehensive coverage |
| **Data Fallback** | Yahoo Finance (yfinance) | Backup for when EastMoney is unavailable |
| **Financial Data** | AKShare | Earnings reports, financial indicators, announcements |
| **News Data** | EastMoney News API | Stock-specific news feed, 7-day window |
| **Industry Data** | AKShare + EastMoney | Industry indices, capital flow, peer data |
| **Technical Indicators** | ta (Python library) | Industry-standard indicator calculations |
| **Hosting (Frontend)** | Netlify | CDN, auto-deploy, generous free tier |
| **Hosting (Backend)** | Render | Auto-deploy from GitHub, sufficient for MVP |

### 5.3 New Services to Build

| Service | Purpose | Dependencies |
|---------|---------|-------------|
| `comprehensive_analysis_service.py` | Orchestrates all 5 analysis dimensions into a single response | All data services + GLM-4 |
| `news_service.py` | Fetches and caches stock-specific news from EastMoney | EastMoney News API |
| `fundamental_service.py` | Fetches earnings reports and financial metrics | AKShare |
| `industry_service.py` | Fetches industry data, peer comparisons, capital flow | AKShare + EastMoney |
| `watchlist_service.py` | CRUD operations for user watchlists | Supabase |
| `prediction_tracking_service.py` | Saves predictions, evaluates after 5 days, calculates accuracy | Supabase |
| `token_monitor_service.py` | Tracks GLM-4 token usage, enforces daily limits, alerts | Supabase |

### 5.4 AI Integration Design

**GLM-4 Prompt Architecture**:

The comprehensive analysis uses a structured prompt that includes all gathered data:

```
Prompt Structure:
  [System Role]: You are a professional A-share market analyst...
  [Stock Data]: Code, Name, Industry, Market Cap, Current Price...
  [Technical Data]: MACD, RSI, KDJ, MA, BOLL, ATR values and signals...
  [Fundamental Data]: PE, PB, ROE, revenue growth, profit growth...
  [Earnings Data]: Latest quarterly results, key metrics, YoY changes...
  [News Data]: Top 5 recent news items with titles and summaries...
  [Industry Data]: Industry index trend, peer performance, capital flow...
  [Instruction]: Provide a comprehensive analysis covering:
    1. Technical trend prediction (1-5 day and 5-20 day outlook)
    2. Earnings interpretation (key takeaways, quality assessment)
    3. News impact analysis (positive/negative/neutral, key risks)
    4. Industry positioning (competitive advantages, sector tailwinds/headwinds)
    5. Comprehensive recommendation with confidence level
    6. 5-day price prediction (expected range)
    7. Top 3 positive factors and top 3 risk factors
```

**Token Budget per Analysis**:
| Component | Estimated Tokens (Input) | Estimated Tokens (Output) |
|-----------|--------------------------|---------------------------|
| System prompt + instructions | ~500 | - |
| Technical data | ~300 | - |
| Fundamental data | ~200 | - |
| Earnings data | ~200 | - |
| News data (5 items) | ~500 | - |
| Industry data | ~300 | - |
| AI response | - | ~800 |
| **Total per stock** | **~2,000** | **~800** |
| **Total per full analysis** | **~2,800 tokens** | |

**Daily Token Budget Calculation**:
| Activity | Stocks | Tokens per Stock | Total Tokens |
|----------|--------|-------------------|--------------|
| Daily recommendations (17:30) | 10 | 2,800 | 28,000 |
| Watchlist snapshots (17:30) | ~20 (estimate) | 2,800 | 56,000 |
| On-demand queries (user) | ~50 (estimate) | 2,800 | 140,000 |
| **Daily total** | | | **~224,000** |

**Token Cost Control Strategy**:
1. Cache AI responses for 30 minutes (identical queries reuse cached response)
2. Daily token budget: 500,000 tokens (configurable)
3. Alert at 80% usage (400,000 tokens)
4. Stop AI analysis at 100% (fallback to template-based analysis)
5. Log every API call with token count for monitoring
6. Use shorter prompts for watchlist snapshots (exclude redundant context)

### 5.5 Caching Strategy

| Data Type | Cache Location | TTL | Invalidation |
|-----------|---------------|-----|--------------|
| Stock real-time quote | In-memory | 3 minutes | Time-based |
| Technical indicators | In-memory | 3 minutes | With quote |
| AI comprehensive analysis | In-memory + DB | 30 minutes | Time-based |
| News data | DB (stock_news_cache) | 1 hour | Time-based |
| Industry data | DB (industry_data_cache) | 2 hours | Time-based |
| Earnings data | DB (via AKShare) | 24 hours | Time-based |
| Daily recommendations | DB | Until next generation | Manual |
| Watchlist analysis | DB | Until refresh | Manual |

### 5.6 Error Handling Strategy

| Failure Mode | User Impact | Handling |
|-------------|-------------|----------|
| EastMoney API down | No real-time quotes | Fallback to Yahoo Finance; show cached data with timestamp |
| AKShare unavailable | No earnings/financial data | Show "Financial data temporarily unavailable"; other dimensions still shown |
| GLM-4 API down | No AI analysis | Template-based fallback; show raw data with manual interpretation guide |
| GLM-4 rate limited | Slow/no AI analysis | Queue requests; show cached analysis; warn user |
| News API fails | No news section | Show "News data temporarily unavailable"; other dimensions still shown |
| Supabase down | No watchlist/history | In-memory fallback for current session; log for later sync |
| Token limit reached | No new AI analysis | Show cached analysis; template fallback; clear message to user |

### 5.7 Rate Limiting and Backpressure Strategy

External data sources have undocumented or implicit rate limits. To prevent IP blocking and cascading failures, the system implements a centralized rate limiting and backpressure mechanism.

#### 5.7.1 External API Call Budget

| Data Source | Estimated Safe Rate | Max Burst | Notes |
|-------------|-------------------|-----------|-------|
| EastMoney HTTP API (quotes, history) | 5 requests/second | 10 requests/second for < 5 sec | Undocumented; conservative estimate based on community experience |
| EastMoney News API | 3 requests/second | 5 requests/second for < 3 sec | Separate endpoint, separate rate limit |
| AKShare (Python library) | 3 requests/second per function | 5 requests/second | Library wraps multiple sources; each underlying source has its own limit |
| GLM-4 (Zhipu AI) API | Per API quota (currently ~60 RPM on free tier) | N/A | Token-based limiting handled by token_monitor_service |
| Yahoo Finance (yfinance) | 2 requests/second | 3 requests/second | Aggressive rate limiting; used only as fallback |

#### 5.7.2 Request Queue Architecture

The system implements a **centralized request queue per data source** using Python's `asyncio.Semaphore` and a custom rate limiter:

```
Request Queue Design:

                      User Request
                           |
                           v
                  +------------------+
                  | Request Router   |
                  | (determines      |
                  |  data source)    |
                  +------------------+
                    |    |    |    |
                    v    v    v    v
              +------+ +------+ +------+ +------+
              |EastM | |AKSh  | |GLM-4 | |Yahoo |
              |Queue | |Queue | |Queue | |Queue |
              |5/sec | |3/sec | |quota | |2/sec |
              +------+ +------+ +------+ +------+
                    |    |    |    |
                    v    v    v    v
              External API Calls (with retry logic)
```

**Priority Levels** (higher priority requests are processed first):
| Priority | Request Type | Example |
|----------|-------------|---------|
| HIGH | User-initiated single stock query | User enters a stock code and clicks search |
| MEDIUM | User-initiated refresh (single or global) | User clicks "Refresh" or "Refresh All" |
| LOW | Scheduled background tasks | Daily recommendation generation, daily snapshots |

**Implementation**:
```python
# Rate limiter per data source (conceptual)
class DataSourceRateLimiter:
    def __init__(self, name: str, max_per_second: float, burst_limit: int):
        self.semaphore = asyncio.Semaphore(burst_limit)
        self.rate = max_per_second
        self.name = name

    async def acquire(self, priority: str = "MEDIUM"):
        # Priority queue: HIGH requests skip ahead
        # Rate limiting: enforce max_per_second using token bucket
        # Logging: record wait time for monitoring
        pass

# Configured rate limiters
rate_limiters = {
    "eastmoney_quote": DataSourceRateLimiter("eastmoney_quote", 5, 10),
    "eastmoney_news": DataSourceRateLimiter("eastmoney_news", 3, 5),
    "akshare": DataSourceRateLimiter("akshare", 3, 5),
    "glm4": DataSourceRateLimiter("glm4", 1, 2),  # ~60 RPM
    "yahoo": DataSourceRateLimiter("yahoo", 2, 3),
}
```

#### 5.7.3 Backoff and Retry Strategy

| Response Code | Interpretation | Action |
|---------------|---------------|--------|
| HTTP 429 (Too Many Requests) | Rate limited by source | Exponential backoff: wait 2^attempt * 1s + random jitter (0-1s). Max 3 retries. |
| HTTP 403 (Forbidden) | Possible IP block | Switch to fallback source immediately. Alert for investigation. No retry to same source for 5 minutes. |
| HTTP 5xx (Server Error) | Source temporarily down | Retry once after 2 seconds. If still failing, use cached data or skip dimension. |
| Connection Timeout (>10s) | Network issue or overloaded source | Retry once after 3 seconds. If still failing, use cached data. |
| HTTP 200 but empty/invalid | Source returning bad data | Log warning. Use cached data if available. Do not retry (likely a data issue, not transient). |

**Exponential Backoff Implementation**:
```
Attempt 1: Wait 2 seconds + jitter(0-1s)
Attempt 2: Wait 4 seconds + jitter(0-1s)
Attempt 3: Wait 8 seconds + jitter(0-1s)
After 3 failures: Give up, use fallback/cache, log error
```

#### 5.7.4 Circuit Breaker Pattern

Each external data source has an independent circuit breaker to prevent cascading failures:

| State | Condition | Behavior |
|-------|-----------|----------|
| **CLOSED** (normal) | Error rate < 50% in last 60 seconds | Requests pass through normally |
| **OPEN** (tripped) | 5+ errors within 60 seconds from the same source | All requests to this source immediately return cached data or fallback. No actual API calls made. |
| **HALF-OPEN** (testing) | After 5 minutes in OPEN state | Allow 1 test request through. If successful, move to CLOSED. If failed, return to OPEN for another 5 minutes. |

**Circuit Breaker Configuration**:
| Data Source | Error Threshold | Open Duration | Fallback When Open |
|-------------|----------------|---------------|-------------------|
| EastMoney Quote | 5 errors / 60s | 5 minutes | Yahoo Finance or cached data |
| EastMoney News | 5 errors / 60s | 5 minutes | "News temporarily unavailable" message |
| AKShare | 5 errors / 60s | 5 minutes | Cached data or "Data temporarily unavailable" |
| GLM-4 | 3 errors / 60s | 10 minutes | Template-based analysis (no AI) |
| Yahoo Finance | 5 errors / 60s | 5 minutes | Cached data only |

#### 5.7.5 Global Refresh Rate Optimization

Global Refresh is the most API-intensive operation. Estimated call volume:

**Call Volume Estimation for Global Refresh (20 stocks)**:
| Step | Calls per Stock | Total Calls (20 stocks) | Target Source |
|------|----------------|------------------------|---------------|
| Real-time quote | 1 | 20 | EastMoney |
| 60-day historical data | 1 | 20 | EastMoney |
| Latest earnings | 1 | 20 | AKShare |
| Recent news (7 days) | 1 | 20 | EastMoney News |
| Announcements | 1 | 20 | AKShare |
| Industry index | 1 | ~6 (cached per industry) | AKShare |
| Industry capital flow | 1 | ~6 (cached per industry) | AKShare |
| Peer comparison | 1 | ~6 (cached per industry) | AKShare |
| GLM-4 analysis | 1 | 20 | GLM-4 |
| **Total** | **~9** | **~138** | |

**Processing Strategy**:
```
Global Refresh Processing Pipeline:

1. Snapshot stock list at start (ignore mid-refresh watchlist changes)
2. Process stocks sequentially (1 at a time by default)
   - Within each stock: fetch dimensions in parallel where possible
     - Parallel Group A: EastMoney quote + EastMoney news (same source, but different endpoints)
     - Parallel Group B: AKShare earnings + AKShare announcements
     - Sequential: Industry data (shared cache, fetch only if expired)
     - Sequential: GLM-4 analysis (after all data gathered)
3. Rate limiting applied per source:
   - EastMoney: ~5 calls/stock, at 5 req/s = ~1 second per stock
   - AKShare: ~3 calls/stock, at 3 req/s = ~1 second per stock
   - GLM-4: 1 call/stock, at ~1 req/s = ~1 second per stock
4. Estimated per-stock time: ~3-5 seconds (parallel fetching + GLM-4)
5. Total for 20 stocks: ~60-100 seconds (within 2-minute target)
```

**Concurrency Control**:
- Default: Process 1 stock at a time (safest for rate limits)
- If measured rate limit headroom exists: Increase to 2 concurrent stocks
- Never exceed 3 concurrent stocks (risk of hitting EastMoney limits)
- If rate limited during refresh: Automatically reduce concurrency to 1 and increase inter-request delay

**Rate Limit Adaptation**:
```
If HTTP 429 received during Global Refresh:
  -> Reduce concurrency to 1
  -> Double inter-request delay (e.g., from 200ms to 400ms)
  -> Extend estimated time remaining
  -> Continue processing (do not abort)
  -> Log rate limit event for tuning

If circuit breaker opens during Global Refresh:
  -> Skip the affected dimension for remaining stocks
  -> Mark affected stocks as "partial refresh"
  -> Notify user: "X stocks refreshed with partial data due to data source issues"
```

#### 5.7.6 Daily Recommendation Generation Rate Budget

The daily recommendation job at 17:30 has the highest total API call volume:

| Stage | Stocks | Calls per Stock | Total Calls | Duration (estimated) |
|-------|--------|----------------|-------------|---------------------|
| Stage 1: Universe fetch (quotes) | 60 | 1 | 60 | ~12 seconds (at 5/s) |
| Stage 1: Universe fetch (history) | 60 | 1 | 60 | ~12 seconds (at 5/s) |
| Stage 2: Technical screening | 60 | 0 (local calc) | 0 | ~5 seconds |
| Stage 3: Scoring | ~20 | 0 (local calc) | 0 | ~2 seconds |
| Stage 4: Full analysis (top 10) | 10 | ~9 | ~90 | ~50 seconds |
| **Total** | | | **~210** | **~80 seconds** |

This is well within safe rate limits when processed sequentially. The job runs during off-peak hours (17:30, after market close) when user-initiated requests are lower.

---

## 6. Data Strategy

### 6.1 Data Sources

| Source | Data Type | Integration Method | Reliability | Cost | Rate Limit |
|--------|-----------|-------------------|-------------|------|------------|
| **EastMoney HTTP API** | Real-time quotes, historical OHLCV, stock list, search | Direct HTTP (undocumented) | Medium | Free | ~10 req/sec safe |
| **EastMoney News API** | Stock-specific news, market news | Direct HTTP | Medium | Free | ~5 req/sec safe |
| **AKShare** | Earnings reports, financial indicators, announcements, industry data | Python library | Medium-High | Free | Library-limited |
| **Yahoo Finance** | Historical OHLCV (fallback) | yfinance library | Medium | Free | Rate-limited |
| **GLM-4 (Zhipu AI)** | AI text analysis, comprehensive summary | REST API | High | Free tier + paid | API quota |

### 6.2 Data Acquisition per Feature

**For Feature 1 (Comprehensive Analysis)**:
```
Step 1: Fetch real-time quote         -> EastMoney API
Step 2: Fetch 60-day historical data  -> EastMoney API (or Yahoo fallback)
Step 3: Calculate technical indicators -> Local computation (ta library)
Step 4: Fetch latest earnings report   -> AKShare: stock_financial_analysis_indicator
Step 5: Fetch recent news (7 days)     -> EastMoney News API
Step 6: Fetch announcements (30 days)  -> AKShare: stock_notice_report
Step 7: Fetch industry index data      -> AKShare: stock_board_industry_index_em
Step 8: Fetch industry capital flow    -> AKShare: stock_individual_fund_flow
Step 9: Fetch peer comparison data     -> AKShare: stock_board_industry_cons_em
Step 10: Send all data to GLM-4       -> Zhipu AI API
Step 11: Cache results                 -> In-memory + Supabase
```

**For Feature 2 (Daily Recommendations)**:
```
Step 1: Fetch data for ~60 curated stocks -> EastMoney API (batched)
Step 2: Calculate indicators for all      -> Local computation
Step 3: Apply strategy filters            -> Local computation
Step 4: Score and rank                    -> Local computation
Step 5: Select top 10                     -> Local computation
Step 6: Run comprehensive analysis x10    -> Steps 1-11 from Feature 1
Step 7: Store all results                 -> Supabase
```

### 6.3 AKShare Key Interfaces

| Data Need | AKShare Function | Parameters | Returns |
|-----------|-----------------|------------|---------|
| Latest Earnings | `stock_financial_analysis_indicator` | symbol="600519" | PE, PB, ROE, revenue growth, etc. |
| Announcements | `stock_notice_report` | symbol="600519" | Title, date, type, content summary |
| Industry Index | `stock_board_industry_index_em` | symbol="白酒" | Index value, change%, components |
| Industry Capital Flow | `stock_sector_fund_flow_rank` | indicator="今日", sector_type="行业资金流" | Net inflow, rank |
| Industry Constituents | `stock_board_industry_cons_em` | symbol="白酒" | List of stocks in the industry |
| Financial Statements | `stock_financial_report_sina` | stock="600519", symbol="资产负债表" | Balance sheet items |

### 6.4 News Data Acquisition

**EastMoney News API Endpoint**:
```
URL: https://search-api-web.eastmoney.com/search/jsonp
Parameters:
  - cb: jQuery callback
  - param: {"uid":"","keyword":"600519","type":["cmsArticleWebOld"],"client":"web",
            "clientType":"web","clientVersion":"curr","param":
            {"cmsArticleWebOld":{"searchScope":"default","sort":"default",
             "pageIndex":1,"pageSize":10,"preTag":"","postTag":""}}}

Alternative URL (simpler):
  https://guba.eastmoney.com/interface/GetData
  Parameters: code=600519, type=1, count=10
```

**News Processing Pipeline**:
```
1. Fetch raw news items (10 items per stock, last 7 days)
2. Filter: Remove duplicate titles, remove ads
3. Extract: Title, publish date, source, summary
4. Cache: Store in stock_news_cache table (1 hour TTL)
5. Pass to GLM-4: Include top 5 most relevant items in AI prompt
```

### 6.5 Data Freshness Requirements

| Data Type | Maximum Staleness | Refresh Trigger |
|-----------|-------------------|-----------------|
| Real-time quote | 3 minutes during market hours | User query or auto-refresh |
| Technical indicators | 3 minutes (derived from quote) | With quote refresh |
| News | 1 hour | User query or scheduled |
| Earnings report | 24 hours | Daily check at 17:30 |
| Announcements | 6 hours | User query |
| Industry data | 2 hours | User query or scheduled |
| AI analysis | 30 minutes | User query or manual refresh |

### 6.6 Data Source Risk Mitigation

| Risk | Probability | Mitigation |
|------|-------------|------------|
| EastMoney blocks IP | Medium | Request throttling (max 10/sec), User-Agent rotation, fallback to Yahoo |
| AKShare API changes | Low | Pin AKShare version, monitor for breaking changes |
| News API returns empty | Medium | Fallback message "No recent news available" |
| GLM-4 quota exceeded | Medium | Token monitoring, daily budget enforcement, template fallback |
| Data inconsistency (different sources disagree) | Low | Use EastMoney as primary truth for price data |

---

## 7. Database Design

### 7.1 Overview

The database extends the existing Supabase PostgreSQL schema with new tables for watchlist, analysis history, prediction tracking, token monitoring, and data caching.

### 7.2 New Table Definitions

```sql
-- ============================================================
-- PRD v2.0: New Tables
-- ============================================================

-- --------------------------------------------------------
-- 7.2.1: Watchlist (User's tracked stocks)
-- --------------------------------------------------------
CREATE TABLE watchlist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(100) NOT NULL,           -- Device fingerprint (MVP auth)
    code VARCHAR(10) NOT NULL,                 -- Stock code
    name VARCHAR(50),                          -- Stock name
    industry VARCHAR(50),                      -- Industry
    added_at TIMESTAMPTZ DEFAULT NOW(),        -- When user added this stock
    last_analysis JSONB,                       -- Latest comprehensive analysis snapshot
    last_refreshed_at TIMESTAMPTZ,             -- When analysis was last refreshed
    is_active BOOLEAN DEFAULT TRUE,            -- Soft delete flag
    notes TEXT,                                -- User notes (future feature)

    UNIQUE(device_id, code)
);

CREATE INDEX idx_watchlist_device ON watchlist(device_id);
CREATE INDEX idx_watchlist_code ON watchlist(code);
CREATE INDEX idx_watchlist_active ON watchlist(device_id, is_active);


-- --------------------------------------------------------
-- 7.2.2: Analysis History (Daily snapshots for tracking)
-- --------------------------------------------------------
CREATE TABLE analysis_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(10) NOT NULL,                 -- Stock code
    name VARCHAR(50),                          -- Stock name
    analysis_date DATE NOT NULL,               -- Date of analysis
    source VARCHAR(20) NOT NULL,               -- 'recommendation' or 'watchlist'
    device_id VARCHAR(100),                    -- NULL for recommendations, set for watchlist

    -- Price data at time of analysis
    price_at_analysis DECIMAL(10,2),           -- Closing price on analysis date
    change_percent DECIMAL(5,2),               -- Change % on analysis date

    -- Composite score
    composite_score INTEGER,                   -- 0-100 score

    -- Full analysis snapshot (JSONB for flexibility)
    technical_analysis JSONB,                  -- Technical indicators + signals
    fundamental_analysis JSONB,                -- PE, PB, ROE, growth metrics
    news_analysis JSONB,                       -- Top news items + AI impact assessment
    earnings_analysis JSONB,                   -- Latest earnings summary
    industry_analysis JSONB,                   -- Industry trend + peer comparison
    ai_comprehensive_summary TEXT,             -- GLM-4 generated summary

    -- Prediction data
    predicted_direction VARCHAR(20),           -- 'bullish', 'neutral', 'bearish'
    predicted_change_low DECIMAL(5,2),         -- Predicted % change lower bound
    predicted_change_high DECIMAL(5,2),        -- Predicted % change upper bound
    predicted_confidence VARCHAR(20),          -- 'high', 'medium', 'low'
    predicted_key_factors JSONB,               -- Array of key factor strings

    -- Trading suggestion
    suggestion_action VARCHAR(20),             -- 'strong_buy', 'buy', 'hold', 'reduce', 'avoid'
    buy_price_low DECIMAL(10,2),
    buy_price_high DECIMAL(10,2),
    stop_loss DECIMAL(10,2),
    take_profit_1 DECIMAL(10,2),
    take_profit_2 DECIMAL(10,2),

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(code, analysis_date, source, COALESCE(device_id, 'system'))
);

CREATE INDEX idx_analysis_history_code_date ON analysis_history(code, analysis_date);
CREATE INDEX idx_analysis_history_date ON analysis_history(analysis_date);
CREATE INDEX idx_analysis_history_device ON analysis_history(device_id);
CREATE INDEX idx_analysis_history_source ON analysis_history(source);


-- --------------------------------------------------------
-- 7.2.3: Prediction Tracking (5-day evaluation records)
-- --------------------------------------------------------
CREATE TABLE prediction_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_history_id UUID REFERENCES analysis_history(id),
    code VARCHAR(10) NOT NULL,                 -- Stock code
    prediction_date DATE NOT NULL,             -- Date prediction was made
    evaluation_date DATE NOT NULL,             -- Date to evaluate (prediction_date + 5 trading days)

    -- Prediction (copied from analysis_history for convenience)
    predicted_direction VARCHAR(20),           -- 'bullish', 'neutral', 'bearish'
    predicted_change_low DECIMAL(5,2),
    predicted_change_high DECIMAL(5,2),
    predicted_confidence VARCHAR(20),

    -- Actual results (filled on evaluation_date)
    actual_price DECIMAL(10,2),                -- Actual closing price on evaluation_date
    actual_change_percent DECIMAL(5,2),        -- Actual % change from prediction_date
    actual_direction VARCHAR(20),              -- Derived: 'bullish' if up, 'bearish' if down

    -- Accuracy metrics (calculated on evaluation)
    direction_correct BOOLEAN,                 -- Was the direction prediction correct?
    range_correct BOOLEAN,                     -- Was actual change within predicted range?
    magnitude_error DECIMAL(5,2),              -- abs(predicted_midpoint - actual_change)

    -- Status
    status VARCHAR(20) DEFAULT 'pending',      -- 'pending', 'evaluated', 'skipped' (suspended stock, etc.)
    evaluated_at TIMESTAMPTZ,                  -- When evaluation was performed

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_prediction_tracking_eval_date ON prediction_tracking(evaluation_date, status);
CREATE INDEX idx_prediction_tracking_code ON prediction_tracking(code);
CREATE INDEX idx_prediction_tracking_status ON prediction_tracking(status);


-- --------------------------------------------------------
-- 7.2.4: Token Usage Log (AI cost monitoring)
-- --------------------------------------------------------
CREATE TABLE token_usage_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usage_date DATE NOT NULL,                  -- Date of usage
    request_type VARCHAR(50) NOT NULL,         -- 'comprehensive_analysis', 'recommendation', 'watchlist_snapshot', 'on_demand'
    stock_code VARCHAR(10),                    -- Which stock
    input_tokens INTEGER NOT NULL DEFAULT 0,   -- Tokens sent to GLM-4
    output_tokens INTEGER NOT NULL DEFAULT 0,  -- Tokens received from GLM-4
    total_tokens INTEGER GENERATED ALWAYS AS (input_tokens + output_tokens) STORED,
    model VARCHAR(50) DEFAULT 'glm-4',         -- Model used
    success BOOLEAN DEFAULT TRUE,              -- Whether the API call succeeded
    error_message TEXT,                        -- Error details if failed
    response_time_ms INTEGER,                  -- API response time
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_token_usage_date ON token_usage_log(usage_date);
CREATE INDEX idx_token_usage_type ON token_usage_log(request_type);

-- Daily usage aggregation view
CREATE VIEW daily_token_usage AS
SELECT
    usage_date,
    COUNT(*) AS total_requests,
    SUM(total_tokens) AS total_tokens,
    SUM(input_tokens) AS total_input_tokens,
    SUM(output_tokens) AS total_output_tokens,
    COUNT(*) FILTER (WHERE success = TRUE) AS successful_requests,
    COUNT(*) FILTER (WHERE success = FALSE) AS failed_requests,
    AVG(response_time_ms) AS avg_response_time_ms
FROM token_usage_log
GROUP BY usage_date;


-- --------------------------------------------------------
-- 7.2.5: Stock News Cache (reduce API calls)
-- --------------------------------------------------------
CREATE TABLE stock_news_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(10) NOT NULL,                 -- Stock code
    news_items JSONB NOT NULL,                 -- Array of news items
    -- Each item: { title, source, publish_date, summary, url, sentiment }
    fetched_at TIMESTAMPTZ DEFAULT NOW(),       -- When data was fetched
    expires_at TIMESTAMPTZ NOT NULL,            -- Cache expiration time

    UNIQUE(code)
);

CREATE INDEX idx_news_cache_code ON stock_news_cache(code);
CREATE INDEX idx_news_cache_expires ON stock_news_cache(expires_at);


-- --------------------------------------------------------
-- 7.2.6: Industry Data Cache (reduce API calls)
-- --------------------------------------------------------
CREATE TABLE industry_data_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    industry_name VARCHAR(100) NOT NULL,       -- Industry name (CSRC classification)
    industry_data JSONB NOT NULL,              -- Industry analysis data
    -- Contains: {
    --   index_value, index_change_1w, index_change_1m, index_change_3m,
    --   top_stocks: [{ code, name, market_cap, pe, revenue_growth, price_change }],
    --   capital_flow: { net_inflow, rank },
    --   heat_score: 0-100,
    --   policy_factors: ["factor1", "factor2"]
    -- }
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,

    UNIQUE(industry_name)
);

CREATE INDEX idx_industry_cache_name ON industry_data_cache(industry_name);
CREATE INDEX idx_industry_cache_expires ON industry_data_cache(expires_at);


-- --------------------------------------------------------
-- 7.2.7: Prediction Accuracy Statistics (materialized view)
-- --------------------------------------------------------
CREATE VIEW prediction_accuracy_stats AS
SELECT
    code,
    COUNT(*) FILTER (WHERE status = 'evaluated') AS total_evaluated,
    COUNT(*) FILTER (WHERE direction_correct = TRUE) AS direction_correct_count,
    ROUND(
        COUNT(*) FILTER (WHERE direction_correct = TRUE)::DECIMAL /
        NULLIF(COUNT(*) FILTER (WHERE status = 'evaluated'), 0) * 100,
        1
    ) AS direction_accuracy_percent,
    COUNT(*) FILTER (WHERE range_correct = TRUE) AS range_correct_count,
    ROUND(
        COUNT(*) FILTER (WHERE range_correct = TRUE)::DECIMAL /
        NULLIF(COUNT(*) FILTER (WHERE status = 'evaluated'), 0) * 100,
        1
    ) AS range_accuracy_percent,
    ROUND(AVG(magnitude_error), 2) AS avg_magnitude_error,
    COUNT(*) FILTER (WHERE status = 'pending') AS pending_count
FROM prediction_tracking
GROUP BY code;


-- ============================================================
-- Existing Tables (from PRD v1.0, retained)
-- ============================================================

-- recommendations          -- Daily stock recommendations (existing)
-- recommendation_tracking  -- Price tracking for recommendations (existing)
-- stock_cache              -- Stock data cache (existing)
-- market_overview          -- Market indices (existing)
-- ai_analysis              -- AI analysis cache (existing, will be extended)
-- data_source_log          -- Data source health monitoring (from PRD v1.0)
```

### 7.3 Database Migration Plan

| Step | Action | Risk | Rollback |
|------|--------|------|----------|
| 1 | Create new tables (watchlist, analysis_history, prediction_tracking, token_usage_log, stock_news_cache, industry_data_cache) | Low | DROP TABLE |
| 2 | Create views (daily_token_usage, prediction_accuracy_stats) | Low | DROP VIEW |
| 3 | Add indexes | Low | DROP INDEX |
| 4 | Verify existing tables remain functional | Medium | N/A (read-only verification) |

### 7.4 Storage Estimation

| Table | Rows per Day | Row Size (est.) | Monthly Storage |
|-------|-------------|-----------------|-----------------|
| analysis_history | 30 (10 recs + 20 watchlist) | ~5 KB | ~4.5 MB |
| prediction_tracking | 30 | ~0.5 KB | ~450 KB |
| token_usage_log | 80 (all API calls) | ~0.3 KB | ~720 KB |
| stock_news_cache | 100 (unique stocks) | ~3 KB | ~300 KB (overwritten) |
| industry_data_cache | 30 (industries) | ~5 KB | ~150 KB (overwritten) |
| watchlist | 200 (all users) | ~3 KB | ~600 KB (growing slowly) |
| **Monthly total (new tables)** | | | **~6.7 MB** |

Supabase free tier allows 500MB. Current usage estimated at ~50MB. New tables add ~80MB/year. Well within limits for 2+ years.

---

## 8. API Design

### 8.1 API Overview

Base URL: `https://stock-advisor-api-6vtb.onrender.com/api/v1`

| Endpoint | Method | Description | Priority |
|----------|--------|-------------|----------|
| `/stock/{code}/comprehensive` | GET | Full 5-dimensional analysis | P0 |
| `/stock/{code}/news` | GET | Recent news for a stock | P0 |
| `/stock/{code}/earnings` | GET | Latest earnings data | P0 |
| `/industry/{industry_name}/analysis` | GET | Industry analysis | P0 |
| `/watchlist` | GET | Get user's watchlist | P0 |
| `/watchlist/add` | POST | Add stock to watchlist | P0 |
| `/watchlist/remove` | POST | Remove stock from watchlist | P0 |
| `/watchlist/refresh/{code}` | POST | Refresh single watchlist stock | P0 |
| `/refresh/all` | POST | Refresh all stocks (SSE stream) | P0 |
| `/analysis/history/{code}` | GET | Historical analysis timeline | P0 |
| `/analysis/accuracy/{code}` | GET | Prediction accuracy stats | P0 |
| `/token/usage` | GET | Token usage statistics | P0 |
| `/device/validate` | POST | Validate a device ID exists in database | P0 |
| `/device/export` | GET | Export watchlist data as JSON | P0 |
| `/device/import` | POST | Import watchlist from JSON export | P0 |
| `/recommendations` | GET | Today's recommendations | P0 (existing) |
| `/recommendations/generate` | POST | Trigger recommendation generation | P0 (existing) |
| `/stock/{code}` | GET | Basic stock analysis | P0 (existing) |
| `/market/overview` | GET | Market indices | P0 (existing) |

### 8.2 Endpoint Specifications

#### 8.2.1 GET `/stock/{code}/comprehensive`

**Description**: Returns the complete 5-dimensional AI analysis for a given stock.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| code | path | Yes | 6-digit stock code (e.g., 600519) |
| force_refresh | query | No | If true, bypass cache (default: false) |

**Response** (200 OK):
```json
{
  "code": "600519",
  "name": "贵州茅台",
  "exchange": "SH",
  "analysis_timestamp": "2026-02-08T15:30:00Z",
  "composite_score": 78,

  "basic_info": {
    "industry": "白酒",
    "market_cap": 2160000000000,
    "circulating_cap": 2160000000000,
    "business_description": "中国领先的高端白酒生产商...",
    "key_products": ["飞天茅台", "茅台王子酒", "茅台迎宾酒"]
  },

  "technical_analysis": {
    "price": 1720.00,
    "change_percent": 2.35,
    "open": 1695.00,
    "high": 1725.00,
    "low": 1690.00,
    "prev_close": 1680.50,
    "volume": 12500000,
    "turnover": 21400000000,
    "indicators": {
      "macd": { "dif": 15.2, "dea": 12.8, "histogram": 4.8, "signal": "golden_cross" },
      "rsi": { "rsi6": 55, "rsi12": 52, "rsi24": 50, "level": "neutral" },
      "ma": { "ma5": 1700, "ma10": 1680, "ma20": 1650, "ma60": 1600, "alignment": "bullish" },
      "kdj": { "k": 65, "d": 58, "j": 79 },
      "boll": { "upper": 1780, "mid": 1700, "lower": 1620, "position": "mid_to_upper" },
      "atr": 28.5,
      "volume_ratio": 1.35
    },
    "trend_prediction": {
      "short_term": "bullish",
      "medium_term": "neutral_to_bullish",
      "support_levels": [1680, 1650],
      "resistance_levels": [1750, 1800]
    }
  },

  "fundamental_analysis": {
    "pe_ttm": 28.5,
    "pb": 9.2,
    "ps": 14.8,
    "roe": 25.3,
    "roa": 18.7,
    "gross_margin": 91.5,
    "net_margin": 52.3,
    "revenue_yoy": 15.2,
    "profit_yoy": 18.6,
    "debt_to_equity": 0.23,
    "industry_pe_avg": 32.1,
    "ai_interpretation": "估值低于行业平均水平，盈利能力行业领先..."
  },

  "recent_developments": {
    "latest_earnings": {
      "report_period": "2025-Q3",
      "revenue": 108000000000,
      "net_profit": 56500000000,
      "revenue_yoy": 15.2,
      "profit_yoy": 18.6,
      "highlights": ["营收超预期", "毛利率保持稳定", "现金流充沛"]
    },
    "news": [
      {
        "title": "贵州茅台获机构大幅增持",
        "source": "证券时报",
        "publish_date": "2026-02-07",
        "summary": "多家基金机构在近期调仓中增持茅台...",
        "sentiment": "positive"
      },
      {
        "title": "白酒行业春节销售数据出炉",
        "source": "中国证券报",
        "publish_date": "2026-02-06",
        "summary": "春节期间高端白酒销售同比增长12%...",
        "sentiment": "positive"
      }
    ],
    "announcements": [
      {
        "title": "关于2025年度利润分配预案的公告",
        "date": "2026-01-25",
        "type": "dividend"
      }
    ],
    "ai_news_impact": "近期消息面整体偏正面，机构增持和春节销售数据为股价提供支撑..."
  },

  "industry_analysis": {
    "industry_name": "白酒",
    "index_performance": {
      "change_1w": 2.1,
      "change_1m": 5.8,
      "change_3m": -1.2
    },
    "peer_comparison": [
      { "code": "000858", "name": "五粮液", "market_cap": 680000000000, "pe": 22.3, "change_1m": 4.2 },
      { "code": "000568", "name": "泸州老窖", "market_cap": 320000000000, "pe": 20.1, "change_1m": 3.8 },
      { "code": "002304", "name": "洋河股份", "market_cap": 210000000000, "pe": 18.5, "change_1m": 2.1 }
    ],
    "capital_flow": {
      "net_inflow_today": 850000000,
      "net_inflow_5d": 2300000000,
      "rank_in_sector": 1
    },
    "industry_heat": 72,
    "ai_industry_summary": "白酒行业整体处于估值修复阶段，龙头企业受益于消费升级和春节效应..."
  },

  "ai_comprehensive_summary": {
    "overall_recommendation": "buy",
    "confidence": "high",
    "positive_factors": [
      "MACD金叉确认，短期技术面看涨",
      "最新季报显示盈利超预期增长18.6%",
      "春节销售数据利好，机构持续增持"
    ],
    "risk_factors": [
      "估值虽低于行业均值但绝对PE仍偏高",
      "白酒行业长期面临消费习惯变化挑战",
      "宏观经济不确定性可能影响高端消费"
    ],
    "price_prediction_5d": {
      "direction": "bullish",
      "range_low": 1700,
      "range_high": 1780,
      "expected_change_percent": { "low": 1.2, "high": 3.5 }
    },
    "full_text": "综合技术面、基本面、消息面和行业分析，贵州茅台当前处于技术面多头格局中..."
  },

  "trading_suggestion": {
    "action": "buy",
    "buy_price_low": 1690,
    "buy_price_high": 1710,
    "stop_loss": 1645,
    "take_profit_1": 1780,
    "take_profit_2": 1850,
    "position_size": "10-15%",
    "holding_period": "5-15 trading days",
    "risk_level": "medium"
  },

  "disclaimer": "本分析由系统基于技术指标和AI模型自动生成，仅供参考，不构成投资建议。"
}
```

**Error Responses**:
| Status | Body | Condition |
|--------|------|-----------|
| 400 | `{"error": "Invalid stock code format"}` | Non-6-digit input |
| 404 | `{"error": "Stock not found"}` | Valid format but no such stock |
| 503 | `{"error": "Data source temporarily unavailable", "partial": {...}}` | External API failure, partial data returned |

#### 8.2.2 GET `/stock/{code}/news`

**Description**: Returns recent news items for a stock.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| code | path | Yes | 6-digit stock code |
| days | query | No | Number of days to look back (default: 7, max: 30) |
| limit | query | No | Max news items to return (default: 10, max: 20) |

**Response** (200 OK):
```json
{
  "code": "600519",
  "news": [
    {
      "title": "...",
      "source": "证券时报",
      "publish_date": "2026-02-07T14:30:00Z",
      "summary": "...",
      "url": "https://...",
      "sentiment": "positive"
    }
  ],
  "total_count": 15,
  "fetched_at": "2026-02-08T10:00:00Z"
}
```

#### 8.2.3 GET `/stock/{code}/earnings`

**Description**: Returns the latest earnings report data for a stock.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| code | path | Yes | 6-digit stock code |
| periods | query | No | Number of quarters to return (default: 4, max: 8) |

**Response** (200 OK):
```json
{
  "code": "600519",
  "earnings": [
    {
      "period": "2025-Q3",
      "revenue": 108000000000,
      "net_profit": 56500000000,
      "revenue_yoy": 15.2,
      "profit_yoy": 18.6,
      "eps": 44.98,
      "roe": 25.3,
      "gross_margin": 91.5,
      "operating_cash_flow": 42000000000
    }
  ]
}
```

#### 8.2.4 GET `/industry/{industry_name}/analysis`

**Description**: Returns industry-level analysis including trends, capital flow, and peer comparison.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| industry_name | path | Yes | Industry name in Chinese (e.g., "白酒") |

**Response** (200 OK):
```json
{
  "industry_name": "白酒",
  "index_performance": {
    "current_value": 12580.5,
    "change_1d": 0.85,
    "change_1w": 2.1,
    "change_1m": 5.8,
    "change_3m": -1.2
  },
  "top_stocks": [
    { "code": "600519", "name": "贵州茅台", "market_cap": 2160000000000, "pe": 28.5, "price_change_1m": 6.2 }
  ],
  "capital_flow": {
    "net_inflow_today": 3200000000,
    "trend_5d": "inflow_increasing"
  },
  "heat_score": 72,
  "policy_factors": ["春节消费旺季", "消费刺激政策预期"],
  "fetched_at": "2026-02-08T10:00:00Z"
}
```

#### 8.2.5 GET `/watchlist`

**Description**: Returns the user's watchlist with latest analysis for each stock.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| device_id | header (X-Device-ID) | Yes | Device fingerprint |

**Response** (200 OK):
```json
{
  "stocks": [
    {
      "code": "600519",
      "name": "贵州茅台",
      "industry": "白酒",
      "added_at": "2026-02-01T10:00:00Z",
      "last_refreshed_at": "2026-02-08T09:30:00Z",
      "current_price": 1720.00,
      "change_percent": 2.35,
      "composite_score": 78,
      "recommendation": "buy",
      "last_analysis_summary": "综合分析看好...",
      "prediction_accuracy": {
        "direction_accuracy": 68.0,
        "total_evaluated": 25
      }
    }
  ],
  "total_count": 5
}
```

#### 8.2.6 POST `/watchlist/add`

**Description**: Adds a stock to the user's watchlist with initial analysis.

**Request Body**:
```json
{
  "code": "600519",
  "device_id": "abc123"
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "message": "600519 added to watchlist",
  "watchlist_count": 6
}
```

**Error Responses**:
| Status | Body | Condition |
|--------|------|-----------|
| 400 | `{"error": "Invalid stock code"}` | Invalid code |
| 409 | `{"error": "Stock already in watchlist"}` | Duplicate |
| 429 | `{"error": "Watchlist limit reached (50 stocks)"}` | Max limit |

#### 8.2.7 POST `/watchlist/remove`

**Request Body**:
```json
{
  "code": "600519",
  "device_id": "abc123"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "600519 removed from watchlist",
  "watchlist_count": 4
}
```

#### 8.2.8 POST `/refresh/all`

**Description**: Triggers a full refresh of all recommendations and watchlist stocks. Returns a Server-Sent Events (SSE) stream for real-time progress updates.

**Request Body**:
```json
{
  "device_id": "abc123"
}
```

**Response** (200 OK, Content-Type: text/event-stream):
```
data: {"type": "start", "total": 18, "recommendations": 10, "watchlist": 8}

data: {"type": "progress", "current": 1, "total": 18, "stock": "600519", "name": "贵州茅台", "status": "completed"}

data: {"type": "progress", "current": 2, "total": 18, "stock": "000001", "name": "平安银行", "status": "completed"}

data: {"type": "token_update", "tokens_used": 5600, "daily_budget": 500000, "percentage": 1.12}

data: {"type": "progress", "current": 3, "total": 18, "stock": "300750", "name": "宁德时代", "status": "failed", "error": "News API timeout"}

...

data: {"type": "complete", "total": 18, "succeeded": 17, "failed": 1, "tokens_used": 50400, "elapsed_seconds": 85}
```

#### 8.2.9 GET `/analysis/history/{code}`

**Description**: Returns the historical analysis timeline for a stock.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| code | path | Yes | 6-digit stock code |
| days | query | No | Number of days to look back (default: 30, max: 90) |
| device_id | header | No | If provided, includes watchlist-specific history |

**Response** (200 OK):
```json
{
  "code": "600519",
  "name": "贵州茅台",
  "history": [
    {
      "analysis_date": "2026-02-08",
      "composite_score": 78,
      "recommendation": "buy",
      "predicted_direction": "bullish",
      "predicted_change": { "low": 1.2, "high": 3.5 },
      "confidence": "high",
      "price_at_analysis": 1720.00,
      "actual_result": null,
      "evaluation_status": "pending",
      "evaluation_date": "2026-02-15",
      "key_factors": ["MACD金叉", "季报超预期", "机构增持"]
    },
    {
      "analysis_date": "2026-02-01",
      "composite_score": 72,
      "recommendation": "hold",
      "predicted_direction": "neutral",
      "predicted_change": { "low": -1.0, "high": 2.0 },
      "confidence": "medium",
      "price_at_analysis": 1680.00,
      "actual_result": {
        "actual_price": 1720.00,
        "actual_change_percent": 2.38,
        "direction_correct": true,
        "range_correct": false
      },
      "evaluation_status": "evaluated",
      "key_factors": ["均线多头排列", "行业回暖"]
    }
  ]
}
```

#### 8.2.10 GET `/analysis/accuracy/{code}`

**Description**: Returns prediction accuracy statistics for a stock.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| code | path | Yes | 6-digit stock code |

**Response** (200 OK):
```json
{
  "code": "600519",
  "name": "贵州茅台",
  "accuracy": {
    "total_evaluated": 25,
    "pending": 5,
    "direction_accuracy": 68.0,
    "range_accuracy": 52.0,
    "avg_magnitude_error": 2.3,
    "best_prediction": {
      "date": "2026-01-20",
      "predicted_change": 5.0,
      "actual_change": 5.8
    },
    "worst_prediction": {
      "date": "2026-01-15",
      "predicted_change": 3.0,
      "actual_change": -4.2
    },
    "grade": "B+",
    "insights": [
      "方向判断准确率高于随机水平",
      "在行业利好时预测准确度更高",
      "建议关注中等信心度的预测"
    ]
  }
}
```

#### 8.2.11 GET `/token/usage`

**Description**: Returns token usage statistics.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| date | query | No | Specific date (default: today) |

**Response** (200 OK):
```json
{
  "date": "2026-02-08",
  "total_tokens": 156000,
  "input_tokens": 112000,
  "output_tokens": 44000,
  "daily_budget": 500000,
  "usage_percentage": 31.2,
  "total_requests": 56,
  "successful_requests": 54,
  "failed_requests": 2,
  "avg_response_time_ms": 2850,
  "alert_level": "normal"
}
```

---

## 9. UI/UX Design

### 9.1 Page Structure

```
App Layout:
+--------------------------------------------------+
| Header: Logo + "A股智能分析" + Token Usage Badge  |
+--------------------------------------------------+
| Tab Bar: [推荐股] [自选股] [搜索]                  |
+--------------------------------------------------+
| Content Area (varies by tab)                      |
|                                                    |
|                                                    |
|                                                    |
+--------------------------------------------------+
| Footer: Disclaimer + Version                      |
+--------------------------------------------------+
```

### 9.2 Home Page -- Recommendations Tab (Default)

```
+--------------------------------------------------+
| Market Overview Banner                            |
| 上证: 3,245.67 +1.2%  深证: 10,876.54 +0.8%     |
+--------------------------------------------------+
| [Refresh All]  Token Usage: 156K/500K (31%)      |
+--------------------------------------------------+
| Today's Top 10 Recommendations (2026-02-08)      |
|                                                    |
| +----------------------------------------------+ |
| | #1  600519 贵州茅台        Score: 78  [+自选] | |
| | 白酒 | 1720.00 +2.35%                        | |
| | AI: 综合看好，MACD金叉+季报超预期             | |
| | Rec: Buy | Target: 1780-1850 | Risk: Medium  | |
| +----------------------------------------------+ |
|                                                    |
| +----------------------------------------------+ |
| | #2  300750 宁德时代        Score: 75  [+自选] | |
| | 电池 | 198.50 +3.12%                         | |
| | AI: 新能源政策利好，行业资金流入               | |
| | Rec: Buy | Target: 215-230 | Risk: Medium    | |
| +----------------------------------------------+ |
|                                                    |
| ... (8 more cards) ...                            |
+--------------------------------------------------+
```

### 9.3 Watchlist Tab

```
+--------------------------------------------------+
| My Watchlist (8 stocks)           [Refresh All]   |
+--------------------------------------------------+
| Sort: [Most Recent] [Score] [Change%]            |
+--------------------------------------------------+
|                                                    |
| +----------------------------------------------+ |
| | 600519 贵州茅台    Score: 78       [Refresh]  | |
| | 1720.00 +2.35%  |  AI: Buy (High Confidence) | |
| | Last refreshed: 10 min ago                    | |
| | Prediction Accuracy: 68% (25 evaluated)       | |
| | [View History] [Remove]                       | |
| +----------------------------------------------+ |
|                                                    |
| +----------------------------------------------+ |
| | 000333 美的集团    Score: 65       [Refresh]  | |
| | 58.20 -0.85%   |  AI: Hold (Medium)          | |
| | Last refreshed: 2 hours ago                   | |
| | Prediction Accuracy: 55% (18 evaluated)       | |
| | [View History] [Remove]                       | |
| +----------------------------------------------+ |
|                                                    |
| ... more stocks ...                               |
+--------------------------------------------------+
```

### 9.4 Stock Detail Page (Comprehensive Analysis)

```
+--------------------------------------------------+
| [Back]  600519 贵州茅台  Score: 78/100  [+自选]  |
+--------------------------------------------------+
| 1,720.00  +40.50 (+2.35%)                        |
| 白酒 | 市值: 2.16万亿                             |
+--------------------------------------------------+
|                                                    |
| === AI Comprehensive Summary ===                  |
| +----------------------------------------------+ |
| | Recommendation: BUY (High Confidence)         | |
| |                                                | |
| | Positive Factors:                              | |
| | 1. MACD金叉确认，短期技术面看涨               | |
| | 2. 最新季报盈利超预期增长18.6%                 | |
| | 3. 春节销售数据利好，机构持续增持              | |
| |                                                | |
| | Risk Factors:                                  | |
| | 1. 绝对PE偏高                                  | |
| | 2. 白酒行业面临消费习惯变化                    | |
| | 3. 宏观经济不确定性                            | |
| |                                                | |
| | 5-Day Prediction: +1.2% to +3.5% (Bullish)   | |
| +----------------------------------------------+ |
|                                                    |
| === Sections (Expandable Accordions) ===          |
|                                                    |
| [v] Technical Analysis                            |
|     MACD: Golden Cross | RSI: 55 (Neutral)       |
|     MA: Bullish Alignment | KDJ: 65/58/79        |
|     Trading Plan: Buy 1690-1710 | SL 1645        |
|     TP1: 1780 | TP2: 1850                        |
|                                                    |
| [v] Fundamental Analysis                          |
|     PE: 28.5 (Industry avg: 32.1)                |
|     ROE: 25.3% | Revenue YoY: +15.2%            |
|     AI: "估值低于行业均值，盈利能力领先..."       |
|                                                    |
| [v] Recent Developments                           |
|     Latest Earnings (2025-Q3):                    |
|       Revenue: 1080亿 (+15.2% YoY)               |
|       Net Profit: 565亿 (+18.6% YoY)             |
|     Recent News:                                  |
|       [Positive] 机构大幅增持 - 2/7              |
|       [Positive] 春节销售数据利好 - 2/6          |
|     Announcements:                                |
|       利润分配预案公告 - 1/25                     |
|                                                    |
| [v] Industry Analysis                             |
|     白酒行业: 1周 +2.1% | 1月 +5.8%             |
|     Peer Comparison:                              |
|       五粮液 PE:22.3 | 泸州老窖 PE:20.1          |
|     Capital Flow: 净流入 8.5亿 (行业第1)          |
|     AI: "行业处于估值修复阶段..."                 |
|                                                    |
| === Disclaimer ===                                |
| 本分析由系统自动生成，仅供参考，不构成投资建议。    |
+--------------------------------------------------+
```

### 9.5 Historical Review Page

```
+--------------------------------------------------+
| [Back]  600519 贵州茅台 - Historical Review       |
+--------------------------------------------------+
|                                                    |
| === Accuracy Summary ===                          |
| +----------------------------------------------+ |
| | Direction Accuracy: 68%  |  Range: 52%       | |
| | Avg Error: 2.3 ppts     |  Grade: B+        | |
| | Evaluated: 25  |  Pending: 5                 | |
| +----------------------------------------------+ |
|                                                    |
| === Timeline ===                                  |
|                                                    |
| 2026-02-08  Score: 78  |  Bullish +1.2% to +3.5%|
| [Pending - Evaluates on 2026-02-15]              |
| Key: MACD金叉, 季报超预期, 机构增持              |
| ------------------------------------------------ |
|                                                    |
| 2026-02-01  Score: 72  |  Neutral -1.0% to +2.0% |
| Actual: +2.38%  Direction: CORRECT  Range: MISS  |
| Key: 均线多头排列, 行业回暖                       |
| ------------------------------------------------ |
|                                                    |
| 2026-01-25  Score: 70  |  Bullish +2.0% to +5.0% |
| Actual: +3.15%  Direction: CORRECT  Range: CORRECT|
| Key: RSI超卖反弹, 分红预案利好                    |
| ------------------------------------------------ |
|                                                    |
| ... more entries ...                              |
|                                                    |
| === AI Insights ===                               |
| - 方向判断准确率高于随机水平                       |
| - 行业利好时预测准确度更高                         |
| - 盈亏比建议关注中等信心度预测                     |
+--------------------------------------------------+
```

### 9.6 Global Refresh Progress

```
+--------------------------------------------------+
| Refreshing All Stocks...                          |
|                                                    |
| [===========............] 12/18 stocks (67%)      |
|                                                    |
| Current: 300750 宁德时代...                       |
| Estimated time remaining: 35 seconds              |
|                                                    |
| Completed:                                        |
|   600519 贵州茅台     [OK]                        |
|   000001 平安银行     [OK]                        |
|   300750 宁德时代     [Processing...]             |
|                                                    |
| Token Usage: 33,600 / 500,000 (6.7%)             |
|                                                    |
| [Cancel Refresh]                                  |
+--------------------------------------------------+
```

### 9.7 Token Usage Warning States

**Normal (< 80%)**:
```
Token: 156K/500K (31%) [Green badge in header]
```

**Warning (80-99%)**:
```
+--------------------------------------------------+
| [Warning Banner - Yellow]                         |
| Token usage at 82%. AI analysis may be limited    |
| for remaining queries today.                      |
+--------------------------------------------------+
```

**Limit Reached (100%)**:
```
+--------------------------------------------------+
| [Alert Banner - Red]                              |
| Daily AI token limit reached. Analysis will use   |
| template mode (no AI insights) until tomorrow.    |
| Technical indicators and price data still         |
| available.                                        |
+--------------------------------------------------+
```

### 9.8 Mobile Responsiveness

| Breakpoint | Layout Adjustments |
|------------|-------------------|
| < 375px | Single column, cards full width, smaller font |
| 375-767px | Single column, standard mobile cards |
| 768-1023px | Two-column card grid |
| >= 1024px | Three-column card grid, sidebar for watchlist |

### 9.9 Interaction Patterns

| Interaction | Behavior |
|-------------|----------|
| Tap stock card | Navigate to full comprehensive analysis page |
| Tap "+自选" button | Add to watchlist, button changes to checkmark |
| Tap "Refresh" icon | Spin animation, re-fetch analysis for that stock |
| Tap "Refresh All" | Show progress overlay (9.6) |
| Swipe left on watchlist card | Reveal "Remove" button |
| Pull to refresh (mobile) | Refresh current view's data |
| Tap section accordion | Expand/collapse analysis dimension |
| Tap timeline entry | Expand to show full prediction vs actual detail |

---

## 10. Compliance Framework

### 10.1 Regulatory Context

In China, providing investment advisory services requires a license from the China Securities Regulatory Commission (CSRC). Stock Advisor must position itself as an **information tool and data analysis platform**, not an advisory service.

### 10.2 Compliance Positioning

| Activity | Permitted | Prohibited |
|----------|-----------|------------|
| Displaying calculated technical indicators | YES | - |
| Showing factual market data and financial reports | YES | - |
| Presenting AI-generated analysis as "reference information" | YES (with disclaimers) | - |
| Displaying prediction accuracy statistics | YES (factual record) | - |
| Tracking and displaying historical system signals | YES | - |
| Claiming to provide "investment advice" | - | NO |
| Guaranteeing returns or profits | - | NO |
| Soliciting investment decisions | - | NO |
| Charging for advisory services without license | - | NO |
| Displaying live trading orders or portfolio management | - | NO |
| Claiming AI predictions are reliable | - | NO |

### 10.3 Required Disclaimers

**Site-Wide Disclaimer** (footer of every page, in Chinese and English):

```
免责声明:

1. 本系统提供的所有信息、分析、预测和建议仅供参考，不构成任何形式的投资建议。

2. 股票市场存在风险，过往业绩和预测准确率不代表未来表现。投资者应根据自身
   财务状况、风险承受能力和投资目标，独立做出投资决策。

3. 本系统的选股策略基于历史数据和技术分析，AI分析基于大语言模型，均无法
   保证未来收益，投资者可能面临本金损失的风险。

4. 本系统不提供证券投资咨询服务，不具备证券投资咨询资格。

5. 预测准确率统计仅反映系统历史信号的事后对比结果，不应被理解为对未来
   预测能力的保证。

6. 技术指标、评分系统和AI分析均为计算工具，仅供参考，不代表专业分析
   意见或建议。

7. 使用本系统即表示您已阅读、理解并同意以上声明。
```

**Per-Analysis Disclaimer** (bottom of every stock analysis):
```
本分析由系统基于技术指标和AI模型自动生成，仅供参考，不构成买入或卖出建议。
请独立判断并自行承担投资风险。
```

**Prediction Tracking Disclaimer** (on history/accuracy pages):
```
预测准确率基于历史数据的事后统计，反映系统信号的方向一致性，不代表
未来预测能力的保证。过往准确率不应作为投资决策的依据。
```

### 10.4 Language Guidelines

| Use | Do Not Use |
|-----|------------|
| "分析结果" (analysis result) | "投资建议" (investment advice) |
| "技术信号" (technical signal) | "买入推荐" (buy recommendation) |
| "参考信息" (reference information) | "专家意见" (expert opinion) |
| "策略回测" (strategy backtest) | "保证收益" (guaranteed returns) |
| "历史表现" (historical performance) | "预期利润" (expected profits) |
| "观察" or "关注" (observe/watch) | "必须买入" (must buy) |
| "系统信号" (system signal) | "确定涨" (definitely goes up) |
| "预测参考" (prediction reference) | "精准预测" (precise prediction) |

### 10.5 Prediction Tracking Compliance Notes

The prediction tracking feature requires extra compliance care:

1. **Never display accuracy as a marketing claim**: Accuracy stats are informational, not promotional
2. **Always show sample size**: "68% accuracy" must always show "(17/25 evaluated)" alongside
3. **Time-limit claims**: Stats should be shown for specific periods (e.g., "last 30 days"), not cumulative all-time
4. **Include uncertainty**: Show confidence intervals where possible
5. **Prominent disclaimers**: Accuracy page must have its own dedicated disclaimer

---

## 11. Development Roadmap

### 11.1 Phase Overview

| Phase | Name | Duration | Goal |
|-------|------|----------|------|
| 0 | Stabilization | 1 week | Fix critical bugs from v1.0, prepare codebase for v2.0 |
| 1 | Core v2.0 Features | 3 weeks | Build comprehensive analysis, watchlist, refresh |
| 2 | History & Tracking | 2 weeks | Build prediction tracking, historical review, accuracy stats |
| 3 | Polish & Launch | 1 week | UI polish, performance optimization, QA validation |

**Total estimated timeline: 7 weeks**

### 11.2 Phase 0: Stabilization (Week 1)

**Goal**: Fix all critical bugs, remove dead code, add basic tests, prepare codebase.

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Deploy search route fix to Render | P0 | 10 min | Pending |
| Verify and remove any hardcoded API keys | P0 | 30 min | In Progress |
| Regenerate recommendations (10 stocks) | P0 | 5 min | Pending |
| Fix prev_close null issue | P1 | 2 hours | Open |
| Remove dead frontend code (aiRankingsCache) | P1 | 15 min | Open |
| Consolidate AIRankingItem type definitions | P1 | 30 min | Open |
| Add unit tests for indicator calculations | P0 | 1 day | Open |
| Review all UI text for compliance language | P0 | 2 hours | Open |
| Add rate limiting middleware (slowapi) | P1 | 2 hours | Open |
| Set up GitHub Actions CI (lint + test) | P1 | 0.5 day | Open |

**Exit Criteria**: All P0 bugs fixed, unit tests passing, CI pipeline running.

### 11.3 Phase 1: Core v2.0 Features (Weeks 2-4)

**Sprint 1 (Week 2): Data Sources + Backend Services**

| Task | Priority | Effort | Dependencies |
|------|----------|--------|-------------|
| Create news_service.py (EastMoney news API integration) | P0 | 2 days | None |
| Create fundamental_service.py (AKShare earnings + financials) | P0 | 2 days | None |
| Create industry_service.py (AKShare industry data) | P0 | 2 days | None |
| Create token_monitor_service.py | P0 | 1 day | None |
| Set up new database tables (watchlist, caches, token_usage) | P0 | 0.5 day | None |

**Sprint 2 (Week 3): Comprehensive Analysis + Watchlist**

| Task | Priority | Effort | Dependencies |
|------|----------|--------|-------------|
| Create comprehensive_analysis_service.py (orchestrator) | P0 | 2 days | All data services |
| Expand GLM-4 prompt for 5-dimensional analysis | P0 | 1 day | Comprehensive service |
| Create watchlist_service.py (CRUD operations) | P0 | 1 day | Database tables |
| Build API endpoints: /stock/{code}/comprehensive | P0 | 1 day | Comprehensive service |
| Build API endpoints: /watchlist/* | P0 | 1 day | Watchlist service |
| Build API endpoint: /stock/{code}/news | P0 | 0.5 day | News service |
| Build API endpoint: /industry/{name}/analysis | P0 | 0.5 day | Industry service |

**Sprint 3 (Week 4): Frontend + Global Refresh**

| Task | Priority | Effort | Dependencies |
|------|----------|--------|-------------|
| Redesign stock detail page for 5-dimensional analysis | P0 | 2 days | Comprehensive API |
| Build watchlist tab and stock cards | P0 | 2 days | Watchlist API |
| Build global refresh with SSE progress | P0 | 1.5 days | Refresh API |
| Build token usage display in header | P0 | 0.5 day | Token API |
| Update recommendation cards with new analysis depth | P0 | 1 day | Comprehensive API |
| Update daily recommendation generation to use comprehensive analysis | P0 | 1 day | Comprehensive service |

**Exit Criteria**: Comprehensive analysis working for any stock. Watchlist functional. Global refresh with progress bar working. Token monitoring active.

### 11.4 Phase 2: History & Tracking (Weeks 5-6)

**Sprint 4 (Week 5): Prediction Tracking System**

| Task | Priority | Effort | Dependencies |
|------|----------|--------|-------------|
| Create prediction_tracking_service.py | P0 | 2 days | Database tables |
| Create analysis_history_service.py | P0 | 1.5 days | Database tables |
| Build daily snapshot job (17:30 auto-save) | P0 | 1 day | Prediction service |
| Build 5-day evaluation job | P0 | 1.5 days | Prediction service |
| Build API endpoints: /analysis/history/{code} | P0 | 0.5 day | History service |
| Build API endpoint: /analysis/accuracy/{code} | P0 | 0.5 day | Prediction service |

**Sprint 5 (Week 6): History Frontend**

| Task | Priority | Effort | Dependencies |
|------|----------|--------|-------------|
| Build historical review page (timeline view) | P0 | 2 days | History API |
| Build prediction accuracy display | P0 | 1.5 days | Accuracy API |
| Build accuracy insights section | P1 | 1 day | Accuracy API |
| Add "View History" button to watchlist cards | P0 | 0.5 day | History page |
| Integration testing: full flow from analysis to evaluation | P0 | 1 day | All services |

**Exit Criteria**: Analysis history saved daily. 5-day evaluation running. Timeline and accuracy views functional.

### 11.5 Phase 3: Polish & Launch (Week 7)

| Task | Priority | Effort |
|------|----------|--------|
| UI polish: consistent styling, loading states, error states | P0 | 2 days |
| Mobile responsiveness testing and fixes | P0 | 1 day |
| Performance optimization (lazy loading, caching verification) | P1 | 1 day |
| Comprehensive QA validation (launch qa-guardian) | P0 | 1 day |
| Final compliance review (disclaimers, language) | P0 | 0.5 day |
| Update all documentation (DESIGN.md, PROGRESS.md) | P0 | 0.5 day |
| Deploy to production and verify | P0 | 0.5 day |

**Exit Criteria**: QA sign-off. All compliance requirements met. Mobile-responsive. Performance targets met. Documentation current.

### 11.6 Milestone Summary

| Milestone | Target Date | Deliverable | Success Criteria |
|-----------|-------------|-------------|------------------|
| M0 | Week 1 end | Stable v1.0 codebase | All P0 bugs fixed, CI running |
| M1 | Week 4 end | Core v2.0 features | Comprehensive analysis, watchlist, refresh working |
| M2 | Week 6 end | History & tracking | Prediction tracking, accuracy stats functional |
| M3 | Week 7 end | v2.0 launch-ready | QA approved, all acceptance criteria met |

---

## 12. Success Metrics

### 12.1 Launch Readiness Checklist

**P0 -- Must Complete (Blocking Launch)**:
- [ ] Comprehensive analysis returns all 5 dimensions for test stocks (600519, 000001, 300750, 000333, 512930)
- [ ] Daily recommendations generate 10 stocks with full analysis at 17:30
- [ ] Watchlist: add, remove, refresh single, and display all functional
- [ ] Global refresh completes for 20 stocks within 2 minutes with progress bar
- [ ] Token monitoring tracks usage and displays warnings at 80%
- [ ] Historical analysis snapshots saved daily at 17:30
- [ ] 5-day prediction evaluation runs automatically
- [ ] Timeline view shows historical analysis with prediction vs actual
- [ ] Accuracy statistics calculated and displayed correctly
- [ ] All disclaimers present on every page
- [ ] Mobile-responsive on iPhone SE, iPhone 14, iPad, Desktop
- [ ] Error handling for all failure modes (data unavailable, AI down, market closed)
- [ ] No hardcoded API keys in codebase

**P1 -- Should Complete (Non-blocking)**:
- [ ] Rate limiting enabled
- [ ] CI pipeline running on all PRs
- [ ] Unit test coverage > 70% for services
- [ ] Performance: comprehensive analysis < 5 seconds cached
- [ ] Token cost per day stays within budget

### 12.2 Feature Acceptance Matrix

| Feature | Test Method | Acceptance Criteria | Status |
|---------|-----------|---------------------|--------|
| Comprehensive Analysis | API test + visual | All 5 dimensions returned, AI summary coherent, < 5s cached | Not started |
| Daily Recommendations | Scheduled job test | 10 stocks at 17:30, each with full analysis | Not started |
| Watchlist | E2E test | Add/remove/refresh working, persists across sessions | Not started |
| Global Refresh | E2E test | Progress bar, token tracking, completes < 2 min for 20 stocks | Not started |
| Historical Review | API test + visual | Timeline shows past analyses, prediction vs actual displayed | Not started |
| Prediction Accuracy | API test | Direction accuracy calculated, stats match manual verification | Not started |
| Token Monitoring | API test | Usage tracked, warnings displayed at 80%, stops at 100% | Not started |
| News Integration | API test | Returns news from last 7 days, no stale data | Not started |
| Industry Analysis | API test | Industry trend, peer comparison, capital flow returned | Not started |
| Compliance | Visual audit | All disclaimers present, no prohibited language | Not started |

### 12.3 Performance Acceptance

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| Comprehensive analysis (cached) | < 2 seconds | API timing |
| Comprehensive analysis (uncached) | < 5 seconds | API timing |
| Home page load | < 3 seconds | Lighthouse |
| Global refresh (20 stocks) | < 2 minutes | End-to-end timing |
| Recommendation generation (10 stocks) | < 15 minutes | Server logs |
| API error rate | < 1% | Monitoring |
| Token cost per day | < 500,000 tokens | Token usage log |

### 12.4 Post-Launch Success Criteria (30 Days)

| Metric | Target | How to Measure |
|--------|--------|---------------|
| DAU | 50 | Server access logs / analytics |
| Stocks analyzed per day | 200 | API call logs |
| Watchlist stocks per user | 3 average | Database query |
| Prediction direction accuracy | > 55% | prediction_tracking table |
| Returning users (D7) | > 35% | Analytics |
| Critical bugs reported | < 3 | User feedback |
| System uptime (market hours) | > 99% | Health check monitoring |
| Token budget adherence | < 100% daily | Token usage log |

### 12.5 Post-Launch Success Criteria (90 Days)

| Metric | Target | How to Measure |
|--------|--------|---------------|
| DAU | 500 | Analytics |
| Prediction direction accuracy | > 60% | prediction_tracking table |
| Returning users (D7) | > 50% | Analytics |
| Average session duration | > 8 minutes | Analytics |
| Watchlist stocks per user | 8 average | Database query |
| User-initiated refreshes per day | 100 | API logs |
| Historical review page views per user per week | 2 | Analytics |

---

## 13. Testing Strategy

Testing is a continuous activity integrated into every development phase, not a single gate at the end. For a system that generates financial analysis and tracks prediction accuracy, testing must cover data correctness, AI output quality, compliance requirements, and user experience.

### 13.1 Test Types and Coverage Targets

| Test Type | Scope | Coverage Target | Execution Frequency | Tool |
|-----------|-------|----------------|--------------------|----|
| Unit Tests | Individual functions and services | > 80% line coverage for all service files | Every commit (CI) | pytest |
| Integration Tests | API endpoints with mock data sources | 100% of API endpoints | Every PR merge (CI) | pytest + httpx |
| AI Quality Tests | GLM-4 output validation | 100% of AI response fields | End of each sprint | Custom validation scripts |
| E2E Tests | Critical user flows | 5 core user journeys | End of each phase | Playwright |
| Performance Tests | API response times, page load | All targets in Section 12.3 | End of each phase | pytest-benchmark + Lighthouse |
| Compliance Tests | Disclaimer presence, prohibited language | 100% of pages and API responses | Every PR merge (CI) + manual audit | Custom scripts + manual review |

### 13.2 Unit Test Requirements

**Priority services for unit testing** (ordered by criticality):

| Service | Key Functions to Test | Min Coverage |
|---------|----------------------|-------------|
| `indicator_service.py` | MACD, RSI, KDJ, BOLL, MA, ATR, Volume Ratio calculations | > 90% |
| `composite_score` (strategy_service) | Weighted score calculation, edge cases (missing indicators) | > 90% |
| `prediction_tracking_service.py` | Direction accuracy, range accuracy, magnitude error calculation | > 85% |
| `token_monitor_service.py` | Token counting, budget enforcement, alert thresholds | > 85% |
| `comprehensive_analysis_service.py` | Dimension orchestration, fallback handling, caching logic | > 80% |
| `watchlist_service.py` | CRUD operations, limit enforcement, device_id validation | > 80% |
| `news_service.py` | News parsing, deduplication, sentiment extraction | > 75% |
| `fundamental_service.py` | Financial metric extraction, YoY calculation | > 75% |
| `industry_service.py` | Industry data aggregation, peer comparison | > 75% |

**Critical Test Cases for Indicator Calculations**:
```
- MACD: Verify DIF, DEA, histogram values against known dataset (e.g., 600519 2025-12 data)
- RSI: Test boundary conditions (RSI=0, RSI=100, RSI at 30/70 thresholds)
- KDJ: Verify K, D, J values and overbought/oversold signal generation
- BOLL: Verify upper/mid/lower bands and position classification
- MA: Test 5/10/20/60 day averages and bullish/bearish alignment detection
- ATR: Verify calculation matches ta library output within 0.1% tolerance
- Composite Score: Test with all indicators present, with some missing, with all missing
```

### 13.3 Integration Test Requirements

All 16 API endpoints must have integration tests with mock external data sources:

| Endpoint | Test Scenarios |
|----------|---------------|
| `GET /stock/{code}/comprehensive` | Valid stock, invalid code (400), nonexistent stock (404), external API failure (503 with partial data), cached vs uncached response |
| `GET /stock/{code}/news` | Normal response, no news available, news API down, expired cache |
| `GET /stock/{code}/earnings` | Normal response, no earnings data, multiple quarters |
| `GET /industry/{name}/analysis` | Valid industry, unknown industry, cached response |
| `GET /watchlist` | Empty watchlist, populated watchlist, invalid device_id |
| `POST /watchlist/add` | Normal add, duplicate stock (409), max limit reached (429), invalid code |
| `POST /watchlist/remove` | Normal remove, stock not in watchlist |
| `POST /watchlist/refresh/{code}` | Normal refresh, stock not in watchlist |
| `POST /refresh/all` | SSE stream correctness, partial failure handling, token limit mid-refresh |
| `GET /analysis/history/{code}` | Normal history, empty history, with/without device_id |
| `GET /analysis/accuracy/{code}` | Normal stats, no evaluated predictions yet, all pending |
| `GET /token/usage` | Normal usage, zero usage, budget exceeded |
| `POST /device/validate` | Valid device_id, nonexistent device_id |
| `GET /device/export` | Normal export, empty watchlist |
| `POST /device/import` | Normal import, merge with existing stocks, invalid format |

**Mock Data Strategy**:
- All external API responses are mocked using `pytest fixtures` + `respx` (for HTTP) or `unittest.mock` (for AKShare)
- Mock data files stored in `tests/fixtures/` directory
- Each mock file represents a known stock's real response, sanitized for testing

### 13.4 AI Output Validation

GLM-4 output must be validated for structure, content quality, and compliance:

**Structural Validation** (automated, every AI call):
| Field | Validation Rule | Action on Failure |
|-------|----------------|-------------------|
| `ai_comprehensive_summary.full_text` | Non-empty, 100-800 characters | Log warning, use template fallback |
| `ai_comprehensive_summary.overall_recommendation` | One of: strong_buy, buy, hold, reduce, avoid | Default to "hold" |
| `ai_comprehensive_summary.confidence` | One of: high, medium, low | Default to "low" |
| `ai_comprehensive_summary.positive_factors` | Array with 1-5 items, each < 100 chars | Use empty array |
| `ai_comprehensive_summary.risk_factors` | Array with 1-5 items, each < 100 chars | Use empty array |
| `ai_comprehensive_summary.price_prediction_5d` | Has direction, range_low, range_high; range_low < range_high | Skip prediction |
| Language | Response is in Chinese | Log warning, still display |

**Content Quality Scoring** (weekly sampling, manual + automated):
| Quality Dimension | Scoring Criteria | Min Acceptable Score |
|-------------------|-----------------|---------------------|
| Relevance | Analysis references the correct stock, industry, and recent events | 4/5 |
| Coherence | Summary logically follows from the 5 data dimensions provided | 4/5 |
| Specificity | Analysis mentions specific numbers (PE, growth rates, price levels) rather than vague statements | 3/5 |
| Compliance | No prohibited language (per Section 10.4), includes hedging phrases | 5/5 (mandatory) |
| Actionability | Trading suggestion includes specific price levels and risk assessment | 3/5 |

**Quality Validation Process**:
1. Weekly: Sample 10 random AI analyses from the past week
2. Run automated compliance check (prohibited language detection)
3. Manually score 5 of the 10 on the quality rubric above
4. If average quality score < 3.5/5: Review and adjust GLM-4 prompt
5. Document results in QA_REPORT.md

**Template Fallback Validation**:
- When AI is unavailable, the template mode must produce valid output
- Test: Mock GLM-4 as unavailable, verify template response structure matches AI response structure
- Test: Template response passes all structural validation rules above

### 13.5 E2E Test Scenarios (Playwright)

5 critical user journeys must be automated using Playwright:

**E2E-001: Stock Search and Analysis**
```
1. Navigate to home page
2. Enter stock code "600519" in search
3. Wait for comprehensive analysis to load (< 5 seconds)
4. Verify all 5 analysis sections are present
5. Verify disclaimer is visible
6. Verify composite score is displayed (0-100 range)
```

**E2E-002: Watchlist Management**
```
1. Navigate to home page
2. Search for stock "600519"
3. Click "Add to Watchlist"
4. Navigate to Watchlist tab
5. Verify stock appears in watchlist
6. Click "Refresh" on the stock
7. Verify analysis updates (last_refreshed timestamp changes)
8. Click "Remove"
9. Verify stock no longer in active watchlist
```

**E2E-003: Global Refresh with Progress**
```
1. Add 3 stocks to watchlist
2. Click "Refresh All"
3. Verify progress bar appears
4. Wait for completion
5. Verify all stocks show updated analysis
6. Verify token usage counter updated
```

**E2E-004: Historical Review and Accuracy**
```
1. Navigate to a stock with existing history (seeded test data)
2. Click "View History"
3. Verify timeline entries are displayed in chronological order
4. Verify evaluated predictions show actual results
5. Verify accuracy statistics are calculated correctly
6. Verify prediction tracking disclaimer is visible
```

**E2E-005: Device Identity Recovery**
```
1. Add stocks to watchlist
2. Note the device backup code from Settings
3. Clear localStorage (simulate data loss)
4. Refresh page -- verify watchlist is empty (new UUID)
5. Navigate to Settings
6. Enter backup code
7. Verify watchlist is restored
```

### 13.6 Test Data Strategy

**Standard Test Stocks** (used across all test types):

| Stock Code | Name | Type | Why Selected |
|-----------|------|------|-------------|
| 600519 | Guizhou Moutai | SH Main Board | Blue chip, always has data, high liquidity |
| 000001 | Ping An Bank | SZ Main Board | Banking sector representative |
| 300750 | CATL | ChiNext | Growth stock, tech sector |
| 000333 | Midea Group | SZ Main Board | Consumer sector, stable fundamentals |
| 512930 | CSI Financial ETF | ETF | Test ETF-specific handling |
| 688981 | SMIC | STAR Market | STAR market representative |
| 600000 | Pudong Development Bank | SH Main Board | Additional banking test case |

**Test Data for Specific Scenarios**:
| Scenario | Test Setup |
|----------|-----------|
| Suspended stock | Use a known suspended stock code (updated periodically) |
| New listing (< 60 days) | Use a recently IPO'd stock (updated periodically) |
| ST stock | Use a known ST stock code (updated periodically) |
| No recent news | Use a low-profile stock with minimal news coverage |
| High volatility | Use a stock with > 5% daily change in recent history |

**Mock Data for External API Testing**:
- Directory: `tests/fixtures/`
- Files: `eastmoney_quote_600519.json`, `akshare_earnings_600519.json`, `eastmoney_news_600519.json`, etc.
- Generated from real API responses, frozen at a known point in time
- Updated quarterly to ensure mock data remains representative

### 13.7 Performance Test Plan

| Test | Method | Target | Frequency |
|------|--------|--------|-----------|
| Comprehensive analysis (cached) | pytest-benchmark: call API with pre-cached data | < 2 seconds | End of Phase 1, 3 |
| Comprehensive analysis (uncached) | pytest-benchmark: call API with fresh data | < 5 seconds | End of Phase 1, 3 |
| Home page load (mobile 3G) | Lighthouse: throttled to Fast 3G | < 3 seconds, Performance score > 70 | End of Phase 3 |
| Global refresh (20 stocks) | End-to-end timer: trigger refresh, measure completion | < 2 minutes | End of Phase 1, 3 |
| Recommendation generation | Server timer: trigger generation, measure completion | < 15 minutes | End of Phase 1, 2 |
| Concurrent users (10 simultaneous) | Load test: 10 concurrent comprehensive analysis requests | All complete < 10 seconds, no 5xx errors | End of Phase 3 |

### 13.8 Compliance Test Automation

Automated checks run on every PR:

| Check | Implementation | Pass Criteria |
|-------|---------------|--------------|
| Disclaimer presence | Parse all page templates; verify disclaimer text exists | Every page renders disclaimer |
| Prohibited language scan | Regex scan of all frontend text and API response templates for words from Section 10.4 "Do Not Use" column | Zero matches for prohibited terms |
| API response compliance | Check that API responses include `disclaimer` field | All analysis endpoints include disclaimer |
| Accuracy display validation | Check that all accuracy statistics are accompanied by sample size | No accuracy % shown without (N/M) notation |

### 13.9 Testing Schedule

| Phase | Test Activities | Duration |
|-------|----------------|----------|
| **Phase 0 (Week 1)** | Write unit tests for existing indicator_service and strategy_service. Set up pytest + CI pipeline. | Continuous throughout week |
| **Phase 1, Sprint 1 (Week 2)** | Unit tests for new data services (news, fundamental, industry). Integration test fixtures. | 1 day testing per 2 days development |
| **Phase 1, Sprint 2 (Week 3)** | Integration tests for comprehensive analysis API. Unit tests for watchlist service. | 1 day testing per 2 days development |
| **Phase 1, Sprint 3 (Week 4)** | E2E tests (E2E-001 through E2E-003). Performance test (cached/uncached analysis). | 1.5 days dedicated testing |
| **Phase 2, Sprint 4 (Week 5)** | Unit tests for prediction tracking. Integration tests for history/accuracy APIs. | 1 day testing per 2 days development |
| **Phase 2, Sprint 5 (Week 6)** | E2E tests (E2E-004, E2E-005). AI quality validation (first sample). | 1.5 days dedicated testing |
| **Phase 3 (Week 7)** | Full regression suite. Performance tests (all targets). Compliance audit. QA Guardian validation. | 3 days (expanded from original 1 day) |

**QA Guardian Engagement Points**:
| Checkpoint | Trigger | Scope |
|------------|---------|-------|
| Phase 0 exit | All Phase 0 tasks complete | Code quality review, CI pipeline verification |
| Phase 1 exit | Sprint 3 complete | Feature validation (analysis, watchlist, refresh) |
| Phase 2 exit | Sprint 5 complete | Prediction tracking validation, accuracy calculation verification |
| Phase 3 / Pre-Launch | Final QA | Full product validation, compliance audit, performance verification |

---

## Appendix A: Glossary

| Term | Definition |
|------|-----------|
| Comprehensive Analysis | The full 5-dimensional AI analysis combining technical, fundamental, news, earnings, and industry data |
| Watchlist | User's personal list of tracked stocks |
| Global Refresh | Action to re-generate analysis for all recommendations and watchlist stocks |
| Prediction Tracking | System that compares 5-day predictions against actual results |
| Token Budget | Daily limit on GLM-4 API token consumption |
| Composite Score | 0-100 weighted score combining multiple analysis dimensions |
| Direction Accuracy | Percentage of predictions where the predicted direction (up/down) matched actual |
| Range Accuracy | Percentage of predictions where actual price change fell within predicted range |

## Appendix B: Technical Decision Log

| Decision | Options Considered | Choice | Rationale |
|----------|-------------------|--------|-----------|
| News data source | 1) AKShare news 2) EastMoney News API 3) Sina Finance | EastMoney News API | Best coverage for A-shares, real-time, free, already integrated ecosystem |
| Earnings data source | 1) AKShare 2) Tushare 3) Wind | AKShare | Free, comprehensive, already in tech stack, no registration required |
| Industry data source | 1) AKShare + EastMoney 2) Tushare Pro 3) Wind | AKShare + EastMoney | Combined coverage, free, existing integration |
| Watchlist auth (MVP) | 1) Full auth system 2) Device fingerprint 3) Local storage only | Device fingerprint | Good enough for MVP, no auth complexity, server-side persistence |
| Prediction evaluation window | 1) 3 days 2) 5 days 3) 10 days | 5 trading days | Balance between too short (noise) and too long (irrelevant) |
| K-Line chart | 1) Build with lightweight-charts 2) Use TradingView widget 3) Defer | Defer | Too complex for current scope, not core to AI analysis value prop |
| Global refresh transport | 1) Polling 2) SSE 3) WebSocket | SSE (Server-Sent Events) | Simpler than WebSocket, sufficient for one-way progress updates |
| Token budget enforcement | 1) Hard stop 2) Degraded mode 3) Alert only | Hard stop + template fallback | Prevents unexpected costs, template mode still provides value |

## Appendix C: Risk Assessment

| ID | Risk | Probability | Impact | Severity | Mitigation |
|----|------|-------------|--------|----------|------------|
| R1 | EastMoney blocks IP or changes API | Medium | High | HIGH | Yahoo fallback; request throttling; User-Agent rotation |
| R2 | GLM-4 API becomes paid or rate-limited | Medium | Medium | MEDIUM | Template fallback; token budget enforcement; evaluate alternatives |
| R3 | Render cold start deters first-time users | High | Medium | HIGH | Wake-up mechanism; plan paid upgrade at 50 DAU |
| R4 | Prediction accuracy is poor (< 50%) | Medium | High | HIGH | Transparent tracking; continuous strategy improvement; manage expectations |
| R5 | Regulatory concern about prediction display | Low | Critical | HIGH | Strict disclaimers; never claim advisory role; accuracy stats are factual records |
| R6 | AKShare library breaking changes | Low | Medium | MEDIUM | Pin version; monitor releases; test before upgrade |
| R7 | Token costs exceed budget | Medium | Low | MEDIUM | Daily budget enforcement; monitoring; caching |
| R8 | News API returns irrelevant or spam content | Medium | Low | LOW | Content filtering; relevance scoring; manual review samples |
| R9 | Watchlist data loss (device fingerprint changes) | Medium | Medium | MEDIUM | Provide export option; consider simple login for v2.1 |
| R10 | Comprehensive analysis too slow (> 10 seconds) | Medium | Medium | MEDIUM | Parallel data fetching; aggressive caching; progressive loading |

---

*End of PRD v2.0*

*This document supersedes PRD.md v1.0 and DESIGN.md v2.0 as the authoritative product specification.*

*Maintained by: Product Orchestrator*
*Review cycle: At the start of each development phase*
