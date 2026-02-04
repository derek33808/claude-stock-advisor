# A股智能交易策略系统 - 开发进度

## 当前状态: 🔄 后端完成，部署测试中

**最后更新**: 2026-02-04 23:50

---

## 架构演进

### v1.0 (已废弃) - 纯静态方案
```
Next.js (SSG) → 静态 JSON → Render 部署
```
**问题**: 只能搜索预生成的 49 支推荐股票，无法实时查询任意股票

### v2.0 (当前) - 全栈分离方案
```
Netlify (前端) → Render (FastAPI) → Supabase (数据库)
                       ↓
                   AKShare (实时数据)
```
**优势**:
- ✅ 支持实时查询任意 A 股/ETF
- ✅ 推荐记录持久化存储
- ✅ 推荐跟踪与回溯
- ✅ 策略胜率统计
- ✅ 预留 AI 分析模块

---

## 今日完成 (2026-02-04)

### ✅ Supabase 项目创建
- [x] 创建项目: stock-advisor (Asia-Pacific 区域)
- [x] 创建数据库表:
  - recommendations (推荐记录)
  - market_overview (市场概览)
  - stock_cache (股票缓存)
  - recommendation_tracking (跟踪记录)
- [x] 创建索引优化查询
- [x] 获取 API 凭证

**Supabase 配置**:
```
项目: stock-advisor
URL: https://hntogkygloioqyexevac.supabase.co
```

### ✅ 后端项目完成

已创建文件:
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口 + CORS
│   ├── config.py            # Pydantic Settings
│   ├── api/
│   │   ├── __init__.py
│   │   ├── stock.py         # 股票查询 API
│   │   ├── recommendations.py # 推荐 API
│   │   └── stats.py         # 统计 API
│   ├── services/
│   │   ├── __init__.py
│   │   ├── akshare_service.py    # AKShare 数据获取
│   │   ├── indicator_service.py  # 技术指标计算
│   │   └── strategy_service.py   # 选股策略
│   ├── models/
│   │   └── schemas.py       # Pydantic 模型
│   └── db/
│       └── supabase.py      # Supabase 客户端
├── requirements.txt
├── .env                     # 环境变量 (gitignored)
├── .env.example
└── render.yaml              # Render 部署配置
```

**API 端点**:
- `GET /stock/{code}` - 股票完整分析 (实时)
- `GET /stock/{code}/kline` - K线数据
- `GET /stock/search` - 股票搜索
- `GET /recommendations` - 今日推荐
- `GET /recommendations/{date}` - 指定日期推荐
- `POST /recommendations/generate` - 手动生成推荐
- `GET /market/overview` - 市场概览
- `GET /stats/performance` - 策略表现统计

### ✅ 前端重构进行中

已完成:
- [x] 创建 API 服务层 (src/lib/api.ts)
- [x] 重构搜索页面 - 支持实时查询
  - 实时技术指标计算
  - 交易建议生成
  - 加载/错误状态处理
- [x] 创建前端环境配置 (.env.local)

待完成:
- [ ] 重构首页 (使用后端 recommendations API)
- [ ] 删除旧的静态数据依赖

---

## 下一步行动

1. **启动后端本地测试**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

2. **更新 Supabase anon key**
   - 从 Supabase 控制台复制 anon key
   - 更新 backend/.env 中的 SUPABASE_KEY

3. **测试 API**
   ```bash
   curl http://localhost:8000/stock/600519
   curl http://localhost:8000/market/overview
   ```

4. **启动前端**
   ```bash
   npm run dev
   # 访问 http://localhost:3000/search?code=600519
   ```

5. **部署**
   - 后端: 推送到 GitHub → Render 自动部署
   - 前端: 推送到 GitHub → Netlify 自动部署

---

## 环境配置

### Supabase
```
项目: stock-advisor
URL: https://hntogkygloioqyexevac.supabase.co
Key: (从控制台获取 anon key)
```

### Render (待部署)
```
后端服务: stock-advisor-api
URL: https://stock-advisor-api.onrender.com
```

### Netlify (待部署)
```
前端服务: stock-advisor
URL: https://stock-advisor.netlify.app
```

---

## 技术栈

### 后端
- Python 3.11+
- FastAPI 0.109.0
- AKShare 1.12.70 (A股数据)
- pandas + pandas-ta (技术指标)
- Supabase Python SDK

### 前端
- Next.js 15.1
- React 19
- TypeScript
- Tailwind CSS

### 部署
- Render (后端 + Cron Job)
- Netlify (前端静态托管)
- Supabase (PostgreSQL)

---

## 文档索引

| 文档 | 状态 | 说明 |
|-----|------|------|
| DESIGN.md | ✅ v2.0 | 完整产品设计文档 |
| PROGRESS.md | ✅ 维护中 | 开发进度跟踪 |
| QA_REPORT.md | ⏳ 待创建 | QA 审查报告 |
| SUMMARY.md | ⏳ 待创建 | 项目完成总结 |

---

*最后更新: 2026-02-04 23:50*
