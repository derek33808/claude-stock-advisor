"""
AI 智能分析服务
使用 GLM 大模型进行公司分析、基本面分析和智能评分
全部使用 httpx 异步调用 + asyncio.gather 并行化
"""

import json
import asyncio
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from cachetools import TTLCache
from app.config import get_settings
from app.http_client import get_client


# GLM API 配置
GLM_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
GLM_MODEL = "glm-4-flash"
GLM_TIMEOUT = 15

# AI 分析结果缓存：同一天同一股票复用（最多100条，TTL 4小时）
_ai_analysis_cache: TTLCache = TTLCache(maxsize=100, ttl=14400)

def _get_glm_api_key() -> str:
    """从环境变量获取 GLM API Key"""
    settings = get_settings()
    return settings.glm_api_key or ""


# AI 模型状态跟踪
class AIModelStatus:
    """AI 模型状态管理"""
    def __init__(self):
        self.available = True
        self.last_error = None
        self.last_error_time = None
        self.error_code = None  # 'unavailable', 'quota_exhausted', 'auth_failed'
        self.error_message = None

    def set_error(self, code: str, message: str):
        self.available = False
        self.error_code = code
        self.error_message = message
        self.last_error_time = datetime.now()

    def clear_error(self):
        self.available = True
        self.error_code = None
        self.error_message = None

    def get_status(self) -> Dict:
        return {
            "available": self.available,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None
        }


# 全局 AI 模型状态
_ai_model_status = AIModelStatus()


def get_ai_model_status() -> Dict:
    """获取 AI 模型状态"""
    return _ai_model_status.get_status()


async def call_glm_api(system_prompt: str, user_prompt: str, max_tokens: int = 800) -> Tuple[Optional[str], Optional[str]]:
    """
    调用 GLM API（异步）

    Args:
        system_prompt: 系统提示词
        user_prompt: 用户提示词
        max_tokens: 最大生成 token 数

    Returns:
        Tuple of (content, error_type)
    """
    global _ai_model_status

    try:
        data = {
            "model": GLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": max_tokens,
        }

        client = get_client()
        resp = await client.post(
            GLM_API_URL,
            json=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {_get_glm_api_key()}",
            },
            timeout=GLM_TIMEOUT,
        )

        if resp.status_code != 200:
            error_body = resp.text
            error_msg = error_body
            try:
                error_json = json.loads(error_body)
                error_msg = error_json.get("error", {}).get("message", error_body)
            except Exception:
                pass

            print(f"GLM API HTTP 错误 {resp.status_code}: {error_msg}")

            if resp.status_code == 401:
                _ai_model_status.set_error("auth_failed", "API 认证失败，请检查 API Key")
                return None, "auth_failed"
            elif resp.status_code == 429:
                if "quota" in error_body.lower() or "余额" in error_body:
                    _ai_model_status.set_error("quota_exhausted", "API 配额已用尽，请充值或等待重置")
                    return None, "quota_exhausted"
                else:
                    _ai_model_status.set_error("rate_limited", "请求过于频繁，请稍后重试")
                    return None, "rate_limited"
            elif resp.status_code >= 500:
                _ai_model_status.set_error("unavailable", f"AI 模型服务暂时不可用 (HTTP {resp.status_code})")
                return None, "unavailable"
            else:
                _ai_model_status.set_error("api_error", f"API 错误: {error_msg}")
                return None, "api_error"

        result = resp.json()

        if result.get("choices") and len(result["choices"]) > 0:
            content = result["choices"][0].get("message", {}).get("content", "")
            if content:
                _ai_model_status.clear_error()
                return content.strip(), None

        return None, None

    except asyncio.TimeoutError:
        print("GLM API 超时")
        _ai_model_status.set_error("timeout", "AI 模型响应超时，请稍后重试")
        return None, "timeout"

    except Exception as e:
        print(f"GLM API 调用失败: {e}")
        _ai_model_status.set_error("unknown", f"未知错误: {str(e)}")
        return None, "unknown"


async def generate_company_analysis(
    name: str,
    code: str,
    industry: str,
    price: float,
    market_cap: float,
) -> Dict:
    """生成公司分析报告（异步）"""
    system_prompt = """你是一位资深的股票分析师，专注于A股市场研究。
请根据提供的股票信息，生成专业的公司分析报告。
要求：
1. 内容要专业、客观
2. 分析要有逻辑性
3. 使用中文回复
4. 返回 JSON 格式"""

    user_prompt = f"""请分析以下股票的公司情况：

股票名称：{name}
股票代码：{code}
所属行业：{industry}
当前价格：¥{price:.2f}
市值：{market_cap:.2f}亿元

请返回以下 JSON 格式的分析结果：
{{
    "company_profile": "公司简介（50字以内）",
    "main_business": "主营业务描述（80字以内）",
    "competitive_advantage": "核心竞争优势（80字以内）",
    "industry_position": "行业地位（如：龙头、领先、中游等）",
    "growth_potential": "成长潜力评估（高/中/低）",
    "risk_factors": ["风险因素1", "风险因素2"]
}}

只返回 JSON，不要其他内容。"""

    content, error_type = await call_glm_api(system_prompt, user_prompt, 600)

    if content:
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())
        except json.JSONDecodeError:
            pass

    return generate_default_company_analysis(name, industry)


def generate_default_company_analysis(name: str, industry: str) -> Dict:
    """生成默认的公司分析（AI 失败时兜底）"""
    return {
        "company_profile": f"{name}是{industry}行业的知名企业",
        "main_business": f"主要从事{industry}相关产品的研发、生产和销售",
        "competitive_advantage": "具有一定的品牌影响力和市场份额",
        "industry_position": "行业参与者",
        "growth_potential": "中",
        "risk_factors": ["行业竞争加剧", "宏观经济波动"]
    }


async def generate_fundamental_analysis(
    name: str,
    code: str,
    price: float,
    change: float,
    market_cap: float,
    indicators: Dict,
) -> Dict:
    """生成基本面分析（异步）"""
    system_prompt = """你是一位资深的股票分析师，擅长基本面分析。
请根据提供的股票信息，生成专业的基本面分析报告。
要求返回 JSON 格式。"""

    ma = indicators.get("ma", {})
    rsi = indicators.get("rsi", {})
    volume = indicators.get("volume", {})

    user_prompt = f"""请对以下股票进行基本面分析：

股票名称：{name}
股票代码：{code}
当前价格：¥{price:.2f}
今日涨跌：{'+' if change >= 0 else ''}{change:.2f}%
市值：{market_cap:.2f}亿元

技术面参考：
- 均线趋势：{ma.get('trend', '未知')}
- RSI状态：{rsi.get('status', '未知')}（RSI6={rsi.get('rsi6', 50)}）
- 成交量：{volume.get('status', '正常')}

请返回以下 JSON 格式：
{{
    "valuation_level": "估值水平（低估/合理/高估）",
    "valuation_reason": "估值判断理由（50字以内）",
    "profitability": "盈利能力评估（强/中/弱）",
    "financial_health": "财务健康度（优秀/良好/一般/较差）",
    "dividend_policy": "分红情况（慷慨/稳定/较少/无）",
    "investment_value": "投资价值评分（1-10分）",
    "analysis_summary": "基本面分析总结（100字以内）"
}}

只返回 JSON，不要其他内容。"""

    content, error_type = await call_glm_api(system_prompt, user_prompt, 500)

    if content:
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())
        except json.JSONDecodeError:
            pass

    return generate_default_fundamental_analysis(price, change, market_cap)


def generate_default_fundamental_analysis(price: float, change: float, market_cap: float) -> Dict:
    """生成默认的基本面分析"""
    if market_cap > 5000:
        valuation = "合理"
        val_reason = "大市值蓝筹股，估值相对稳定"
    elif market_cap > 500:
        valuation = "合理"
        val_reason = "中等市值，估值需结合业绩判断"
    else:
        valuation = "需关注"
        val_reason = "小市值股票，估值波动较大"

    return {
        "valuation_level": valuation,
        "valuation_reason": val_reason,
        "profitability": "中",
        "financial_health": "良好",
        "dividend_policy": "稳定",
        "investment_value": 6,
        "analysis_summary": "该股票基本面整体稳健，建议结合技术面和市场情绪综合判断。"
    }


async def generate_ai_score_and_recommendation(
    name: str,
    code: str,
    price: float,
    change: float,
    score: int,
    indicators: Dict,
    suggestion: Dict,
    company_analysis: Dict,
    fundamental_analysis: Dict,
) -> Dict:
    """生成 AI 智能评分和投资建议（异步）"""
    system_prompt = """你是一位专业的投资顾问，请综合技术面、基本面分析，给出最终的投资建议。
要求返回 JSON 格式。"""

    macd = indicators.get("macd", {})
    rsi = indicators.get("rsi", {})
    ma = indicators.get("ma", {})

    user_prompt = f"""请对以下股票给出综合投资建议：

【基本信息】
股票：{name}（{code}）
价格：¥{price:.2f}，涨跌：{'+' if change >= 0 else ''}{change:.2f}%
技术评分：{score}/100

【技术面】
- MACD：{macd.get('signal', '未知')}
- RSI：{rsi.get('status', '未知')}
- 均线：{ma.get('trend', '未知')}
- 操作建议：{suggestion.get('action', '观望')}

【公司分析】
- 行业地位：{company_analysis.get('industry_position', '未知')}
- 成长潜力：{company_analysis.get('growth_potential', '未知')}

【基本面】
- 估值：{fundamental_analysis.get('valuation_level', '未知')}
- 盈利能力：{fundamental_analysis.get('profitability', '未知')}
- 投资价值：{fundamental_analysis.get('investment_value', 5)}/10

请返回以下 JSON 格式：
{{
    "ai_score": 85,
    "ai_rating": "推荐等级（强烈推荐/推荐/中性/谨慎/回避）",
    "confidence": "置信度（高/中/低）",
    "time_horizon": "建议持有周期",
    "key_points": ["核心观点1", "核心观点2", "核心观点3"],
    "ai_summary": "AI智能分析总结（150字以内，专业且易懂）"
}}

只返回 JSON，不要其他内容。"""

    content, error_type = await call_glm_api(system_prompt, user_prompt, 500)

    if content:
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            parsed = json.loads(content.strip())
            if "ai_score" in parsed:
                parsed["ai_score"] = max(0, min(100, int(parsed["ai_score"])))
            return parsed
        except (json.JSONDecodeError, ValueError):
            pass

    return generate_default_ai_recommendation(score, suggestion)


def generate_default_ai_recommendation(score: int, suggestion: Dict) -> Dict:
    """生成默认的 AI 建议"""
    action = suggestion.get("action", "观望")

    if score >= 70:
        rating = "推荐"
        confidence = "中"
    elif score >= 50:
        rating = "中性"
        confidence = "中"
    else:
        rating = "谨慎"
        confidence = "低"

    if action == "买入":
        rating = "推荐"
    elif action == "回避":
        rating = "谨慎"

    return {
        "ai_score": score,
        "ai_rating": rating,
        "confidence": confidence,
        "time_horizon": "短中期（1-3个月）",
        "key_points": [
            "技术面信号需关注",
            "建议控制仓位",
            "注意止损止盈"
        ],
        "ai_summary": f"综合技术面和基本面分析，该股票当前{rating}操作。建议根据个人风险承受能力合理配置仓位，注意设置止损止盈点位。"
    }


async def get_full_ai_analysis(
    name: str,
    code: str,
    industry: str,
    price: float,
    change: float,
    market_cap: float,
    score: int,
    indicators: Dict,
    suggestion: Dict,
) -> Dict:
    """
    获取完整的 AI 智能分析
    - 步骤1和步骤2并行执行（公司分析 + 基本面分析）
    - 步骤3串行执行（依赖步骤1和2的结果）
    - 缓存同一天同一股票的结果

    Returns:
        包含公司分析、基本面分析、AI评分的完整分析结果
    """
    # 检查缓存
    today = datetime.now().strftime("%Y-%m-%d")
    cache_key = f"{code}_{today}"
    if cache_key in _ai_analysis_cache:
        return _ai_analysis_cache[cache_key]

    # 1 & 2. 公司分析 + 基本面分析 并行执行
    company_analysis, fundamental_analysis = await asyncio.gather(
        generate_company_analysis(name, code, industry, price, market_cap),
        generate_fundamental_analysis(name, code, price, change, market_cap, indicators),
    )

    # 3. AI 智能评分和建议（依赖上面两个结果，串行）
    ai_recommendation = await generate_ai_score_and_recommendation(
        name, code, price, change, score,
        indicators, suggestion,
        company_analysis, fundamental_analysis
    )

    result = {
        "company": company_analysis,
        "fundamental": fundamental_analysis,
        "ai_recommendation": ai_recommendation,
        "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # 写入缓存
    _ai_analysis_cache[cache_key] = result

    return result


def calculate_ai_ranking_score(
    technical_score: int,
    ai_score: int,
    change: float,
    volume_status: str,
    ma_trend: str,
) -> int:
    """
    计算 AI 排名分数（用于股票排名）
    """
    base_score = technical_score * 0.4 + ai_score * 0.6

    if 0 < change <= 3:
        base_score += 5
    elif 3 < change <= 7:
        base_score += 3
    elif change > 7:
        base_score -= 5
    elif -3 < change < 0:
        base_score += 2
    elif change <= -5:
        base_score -= 10

    if volume_status == "温和放量":
        base_score += 5
    elif volume_status == "放量":
        base_score += 3
    elif volume_status == "缩量":
        base_score -= 3

    if ma_trend == "多头排列":
        base_score += 10
    elif ma_trend == "多头回调":
        base_score += 5
    elif ma_trend == "空头排列":
        base_score -= 10
    elif ma_trend == "空头反弹":
        base_score -= 5

    return max(0, min(100, int(base_score)))
