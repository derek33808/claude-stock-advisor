"""
AI 智能分析服务
使用 GLM 大模型进行公司分析、基本面分析和智能评分
"""

import json
import urllib.request
import urllib.error
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from app.config import get_settings


# GLM API 配置
GLM_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
GLM_MODEL = "glm-4-flash"
GLM_TIMEOUT = 45

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


def call_glm_api(system_prompt: str, user_prompt: str, max_tokens: int = 800) -> Tuple[Optional[str], Optional[str]]:
    """
    调用 GLM API

    Args:
        system_prompt: 系统提示词
        user_prompt: 用户提示词
        max_tokens: 最大生成 token 数

    Returns:
        Tuple of (content, error_type)
        - content: 生成的文本，失败返回 None
        - error_type: 错误类型 ('unavailable', 'quota_exhausted', 'auth_failed', None)
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

        req = urllib.request.Request(
            GLM_API_URL,
            data=json.dumps(data).encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {_get_glm_api_key()}",
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=GLM_TIMEOUT) as response:
            result = json.loads(response.read().decode('utf-8'))

        if result.get("choices") and len(result["choices"]) > 0:
            content = result["choices"][0].get("message", {}).get("content", "")
            if content:
                # 成功调用，清除错误状态
                _ai_model_status.clear_error()
                return content.strip(), None

        return None, None

    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode('utf-8')
            error_json = json.loads(error_body)
            error_msg = error_json.get("error", {}).get("message", str(e))
        except:
            error_msg = str(e)

        print(f"GLM API HTTP 错误 {e.code}: {error_msg}")

        if e.code == 401:
            _ai_model_status.set_error("auth_failed", "API 认证失败，请检查 API Key")
            return None, "auth_failed"
        elif e.code == 429:
            # 解析具体的配额错误
            if "quota" in error_body.lower() or "余额" in error_body:
                _ai_model_status.set_error("quota_exhausted", "API 配额已用尽，请充值或等待重置")
                return None, "quota_exhausted"
            else:
                _ai_model_status.set_error("rate_limited", "请求过于频繁，请稍后重试")
                return None, "rate_limited"
        elif e.code >= 500:
            _ai_model_status.set_error("unavailable", f"AI 模型服务暂时不可用 (HTTP {e.code})")
            return None, "unavailable"
        else:
            _ai_model_status.set_error("api_error", f"API 错误: {error_msg}")
            return None, "api_error"

    except urllib.error.URLError as e:
        print(f"GLM API 网络错误: {e}")
        _ai_model_status.set_error("unavailable", "无法连接到 AI 模型服务，请检查网络")
        return None, "unavailable"

    except TimeoutError:
        print("GLM API 超时")
        _ai_model_status.set_error("timeout", "AI 模型响应超时，请稍后重试")
        return None, "timeout"

    except Exception as e:
        print(f"GLM API 调用失败: {e}")
        _ai_model_status.set_error("unknown", f"未知错误: {str(e)}")
        return None, "unknown"


def generate_company_analysis(
    name: str,
    code: str,
    industry: str,
    price: float,
    market_cap: float,
) -> Dict:
    """
    生成公司分析报告

    Args:
        name: 股票名称
        code: 股票代码
        industry: 所属行业
        price: 当前价格
        market_cap: 市值（亿）

    Returns:
        公司分析结果
    """
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

    content, error_type = call_glm_api(system_prompt, user_prompt, 600)

    if content:
        try:
            # 尝试解析 JSON
            # 处理可能的 markdown 代码块
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())
        except json.JSONDecodeError:
            pass

    # 返回默认分析
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


def generate_fundamental_analysis(
    name: str,
    code: str,
    price: float,
    change: float,
    market_cap: float,
    indicators: Dict,
) -> Dict:
    """
    生成基本面分析

    Args:
        name: 股票名称
        code: 股票代码
        price: 当前价格
        change: 涨跌幅
        market_cap: 市值
        indicators: 技术指标

    Returns:
        基本面分析结果
    """
    system_prompt = """你是一位资深的股票分析师，擅长基本面分析。
请根据提供的股票信息，生成专业的基本面分析报告。
要求返回 JSON 格式。"""

    # 提取关键技术数据
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

    content, error_type = call_glm_api(system_prompt, user_prompt, 500)

    if content:
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())
        except json.JSONDecodeError:
            pass

    # 返回默认分析
    return generate_default_fundamental_analysis(price, change, market_cap)


def generate_default_fundamental_analysis(price: float, change: float, market_cap: float) -> Dict:
    """生成默认的基本面分析"""
    # 根据市值判断估值
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


def generate_ai_score_and_recommendation(
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
    """
    生成 AI 智能评分和投资建议

    Returns:
        AI 评分和建议
    """
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

    content, error_type = call_glm_api(system_prompt, user_prompt, 500)

    if content:
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            parsed = json.loads(content.strip())
            # 确保 ai_score 在合理范围
            if "ai_score" in parsed:
                parsed["ai_score"] = max(0, min(100, int(parsed["ai_score"])))
            return parsed
        except (json.JSONDecodeError, ValueError):
            pass

    # 返回默认建议
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


def get_full_ai_analysis(
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

    Returns:
        包含公司分析、基本面分析、AI评分的完整分析结果
    """
    # 1. 公司分析
    company_analysis = generate_company_analysis(
        name, code, industry, price, market_cap
    )

    # 2. 基本面分析
    fundamental_analysis = generate_fundamental_analysis(
        name, code, price, change, market_cap, indicators
    )

    # 3. AI 智能评分和建议
    ai_recommendation = generate_ai_score_and_recommendation(
        name, code, price, change, score,
        indicators, suggestion,
        company_analysis, fundamental_analysis
    )

    return {
        "company": company_analysis,
        "fundamental": fundamental_analysis,
        "ai_recommendation": ai_recommendation,
        "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def calculate_ai_ranking_score(
    technical_score: int,
    ai_score: int,
    change: float,
    volume_status: str,
    ma_trend: str,
) -> int:
    """
    计算 AI 排名分数（用于股票排名）

    Args:
        technical_score: 技术评分
        ai_score: AI 评分
        change: 涨跌幅
        volume_status: 成交量状态
        ma_trend: 均线趋势

    Returns:
        排名分数（0-100）
    """
    # 基础分数：技术评分和AI评分的加权平均
    base_score = technical_score * 0.4 + ai_score * 0.6

    # 涨跌幅调整（适度上涨加分，暴涨扣分）
    if 0 < change <= 3:
        base_score += 5
    elif 3 < change <= 7:
        base_score += 3
    elif change > 7:
        base_score -= 5  # 涨幅过大风险增加
    elif -3 < change < 0:
        base_score += 2  # 小幅回调可能是买点
    elif change <= -5:
        base_score -= 10

    # 成交量调整
    if volume_status == "温和放量":
        base_score += 5
    elif volume_status == "放量":
        base_score += 3
    elif volume_status == "缩量":
        base_score -= 3

    # 均线趋势调整
    if ma_trend == "多头排列":
        base_score += 10
    elif ma_trend == "多头回调":
        base_score += 5
    elif ma_trend == "空头排列":
        base_score -= 10
    elif ma_trend == "空头反弹":
        base_score -= 5

    return max(0, min(100, int(base_score)))
