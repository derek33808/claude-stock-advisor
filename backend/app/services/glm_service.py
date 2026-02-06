"""
智谱 GLM 大模型服务
用于生成智能股票交易摘要
"""

import json
import urllib.request
import urllib.error
import time
from typing import Optional

# 导入 AI 模型状态管理和 API Key 获取函数
from app.services.ai_analysis_service import _ai_model_status, _get_glm_api_key


# GLM API 配置
GLM_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
GLM_MODEL = "glm-4-flash"  # 使用 flash 版本，速度快成本低
GLM_TIMEOUT = 30


def generate_ai_summary(
    name: str,
    code: str,
    price: float,
    change: float,
    score: int,
    suggestion: dict,
    indicators: dict,
    reasons: list,
) -> Optional[str]:
    """
    使用 GLM 大模型生成股票交易指导摘要

    Args:
        name: 股票名称
        code: 股票代码
        price: 当前价格
        change: 涨跌幅
        score: 综合评分
        suggestion: 交易建议
        indicators: 技术指标
        reasons: 推荐理由

    Returns:
        AI 生成的摘要文字，失败返回 None
    """

    # 构建 prompt
    prompt = f"""你是一位专业的股票分析师，请根据以下数据为投资者生成一段简洁的交易指导摘要。

## 股票信息
- 名称：{name}
- 代码：{code}
- 当前价格：¥{price:.2f}
- 今日涨跌：{'+' if change >= 0 else ''}{change:.2f}%
- 综合评分：{score}/100

## 交易建议
- 操作建议：{suggestion.get('action', '观望')}
- 建议买入区间：¥{suggestion.get('buy_price', {}).get('low', 0):.2f} - ¥{suggestion.get('buy_price', {}).get('high', 0):.2f}
- 止损价：¥{suggestion.get('stop_loss', 0):.2f}
- 止盈目标1：¥{suggestion.get('take_profit', {}).get('target1', 0):.2f}
- 止盈目标2：¥{suggestion.get('take_profit', {}).get('target2', 0):.2f}
- 风险等级：{suggestion.get('risk_level', '中')}
- 建议仓位：{suggestion.get('position_ratio', '10-15%')}
- 持有周期：{suggestion.get('holding_days', '5-15个交易日')}

## 技术指标
- MACD趋势：{indicators.get('macd', {}).get('trend', '未知')}
- RSI状态：{indicators.get('rsi', {}).get('level', '未知')}
- 均线排列：{indicators.get('ma', {}).get('alignment', '未知')}
- BOLL位置：{indicators.get('boll', {}).get('position', '未知')}

## 分析理由
{chr(10).join(['- ' + r for r in reasons[:5]])}

请生成一段200-300字的交易指导摘要，包含：
1. 当前行情简评
2. 技术面分析要点
3. 具体操作建议（买入点、止损、止盈）
4. 风险提示

要求：语言专业但易懂，使用 emoji 增强可读性，末尾加上免责声明。"""

    try:
        # 构建请求
        data = {
            "model": GLM_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位经验丰富的股票分析师，擅长用通俗易懂的语言为普通投资者提供交易指导。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500,
        }

        # 发送请求
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

        # 提取生成的内容
        if result.get("choices") and len(result["choices"]) > 0:
            content = result["choices"][0].get("message", {}).get("content", "")
            if content:
                _ai_model_status.clear_error()
                return content.strip()

        return None

    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode('utf-8')
        except:
            pass

        print(f"GLM API HTTP 错误 {e.code}: {error_body}")

        if e.code == 401:
            _ai_model_status.set_error("auth_failed", "API 认证失败，请检查 API Key")
        elif e.code == 429:
            if "quota" in error_body.lower() or "余额" in error_body:
                _ai_model_status.set_error("quota_exhausted", "API 配额已用尽，请充值或等待重置")
            else:
                _ai_model_status.set_error("rate_limited", "请求过于频繁，请稍后重试")
        elif e.code >= 500:
            _ai_model_status.set_error("unavailable", f"AI 模型服务暂时不可用 (HTTP {e.code})")
        return None

    except urllib.error.URLError as e:
        print(f"GLM API 网络错误: {e}")
        _ai_model_status.set_error("unavailable", "无法连接到 AI 模型服务")
        return None

    except Exception as e:
        print(f"GLM API 调用失败: {e}")
        return None


def generate_summary_with_fallback(
    name: str,
    code: str,
    price: float,
    change: float,
    score: int,
    suggestion: dict,
    indicators: dict,
    reasons: list,
) -> str:
    """
    生成摘要，AI 失败时使用模板兜底
    """
    # 先尝试 AI 生成
    ai_summary = generate_ai_summary(
        name, code, price, change, score,
        suggestion, indicators, reasons
    )

    if ai_summary:
        return ai_summary

    # AI 失败，使用模板生成
    return generate_template_summary(
        name, code, price, change, score,
        suggestion, indicators, reasons
    )


def generate_template_summary(
    name: str,
    code: str,
    price: float,
    change: float,
    score: int,
    suggestion: dict,
    indicators: dict,
    reasons: list,
) -> str:
    """
    模板生成摘要（兜底方案）
    """
    # 判断行情趋势
    if change > 2:
        trend = "强势上涨"
    elif change > 0:
        trend = "小幅上涨"
    elif change > -2:
        trend = "小幅下跌"
    else:
        trend = "明显下跌"

    # 评分评价
    if score >= 80:
        score_desc = "优秀"
        score_advice = "具备较好的投资价值"
    elif score >= 60:
        score_desc = "良好"
        score_advice = "可适当关注"
    elif score >= 40:
        score_desc = "一般"
        score_advice = "建议谨慎操作"
    else:
        score_desc = "较弱"
        score_advice = "建议观望为主"

    # 风险等级
    risk_map = {"low": "低", "medium": "中等", "high": "较高"}
    risk_level = risk_map.get(suggestion.get("risk_level", "medium"), "中等")

    # 获取建议数据
    action = suggestion.get("action", "观望")
    buy_low = suggestion.get("buy_price", {}).get("low", 0)
    buy_high = suggestion.get("buy_price", {}).get("high", 0)
    stop_loss = suggestion.get("stop_loss", 0)
    target1 = suggestion.get("take_profit", {}).get("target1", 0)
    target2 = suggestion.get("take_profit", {}).get("target2", 0)
    position = suggestion.get("position_ratio", "10-15%")
    holding = suggestion.get("holding_days", "5-15个交易日")

    # MACD 信号
    macd_trend = indicators.get("macd", {}).get("trend", "")
    macd_desc = ""
    if "金叉" in str(macd_trend):
        macd_desc = "MACD 出现金叉信号，短期看涨。"
    elif "死叉" in str(macd_trend):
        macd_desc = "MACD 出现死叉信号，注意风险。"

    # RSI 状态
    rsi_level = indicators.get("rsi", {}).get("level", "")
    rsi_desc = ""
    if rsi_level == "超买":
        rsi_desc = "RSI 处于超买区间，短期可能回调。"
    elif rsi_level == "超卖":
        rsi_desc = "RSI 处于超卖区间，可能存在反弹机会。"

    summary = f"""【{name}({code}) 交易指导】

📊 当前行情：现价 ¥{price:.2f}，今日{trend}（{'+' if change >= 0 else ''}{change:.2f}%）

⭐ 综合评分：{score}分（{score_desc}），{score_advice}。

📈 技术信号：{macd_desc}{rsi_desc}

💡 操作建议：{action}
• 建议买入区间：¥{buy_low:.2f} - ¥{buy_high:.2f}
• 止损价位：¥{stop_loss:.2f}（跌破即止损）
• 止盈目标：第一目标 ¥{target1:.2f}，第二目标 ¥{target2:.2f}
• 建议仓位：{position}
• 持有周期：{holding}

⚠️ 风险提示：当前风险等级为{risk_level}，请根据自身风险承受能力合理配置仓位。以上分析仅供参考，不构成投资建议，投资有风险，入市需谨慎。"""

    return summary
