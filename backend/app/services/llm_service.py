"""
统一大模型调用服务
支持多个模型提供商：智谱GLM、DeepSeek等
所有提供商使用 OpenAI 兼容的 API 格式
"""

import asyncio
from typing import Optional, Dict, List, Tuple
from app.config import get_settings
from app.http_client import get_client


# 模型配置注册表
MODEL_REGISTRY: Dict[str, Dict] = {
    # 智谱 GLM 系列
    "glm-4-flash": {
        "provider": "zhipu",
        "api_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "api_key_field": "glm_api_key",
        "display_name": "GLM-4-Flash",
        "description": "智谱轻量模型，速度最快",
        "max_tokens": 4096,
        "timeout": 15,
    },
    "glm-4-air": {
        "provider": "zhipu",
        "api_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "api_key_field": "glm_api_key",
        "display_name": "GLM-4-Air",
        "description": "智谱均衡模型，性价比高",
        "max_tokens": 4096,
        "timeout": 20,
    },
    "glm-4-plus": {
        "provider": "zhipu",
        "api_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "api_key_field": "glm_api_key",
        "display_name": "GLM-4-Plus",
        "description": "智谱旗舰模型，分析能力最强",
        "max_tokens": 4096,
        "timeout": 30,
    },
    "glm-4-long": {
        "provider": "zhipu",
        "api_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "api_key_field": "glm_api_key",
        "display_name": "GLM-4-Long",
        "description": "智谱长上下文模型，支持128K",
        "max_tokens": 4096,
        "timeout": 30,
    },
    # DeepSeek 系列
    "deepseek-chat": {
        "provider": "deepseek",
        "api_url": "https://api.deepseek.com/chat/completions",
        "api_key_field": "deepseek_api_key",
        "display_name": "DeepSeek-V3",
        "description": "DeepSeek通用对话模型",
        "max_tokens": 4096,
        "timeout": 30,
    },
    "deepseek-reasoner": {
        "provider": "deepseek",
        "api_url": "https://api.deepseek.com/chat/completions",
        "api_key_field": "deepseek_api_key",
        "display_name": "DeepSeek-R1",
        "description": "DeepSeek推理模型，深度分析",
        "max_tokens": 4096,
        "timeout": 60,
    },
}

# 默认模型
DEFAULT_MODEL = "glm-4-flash"


def get_available_models() -> List[Dict]:
    """获取所有可用模型列表（只返回配置了 API Key 的）"""
    settings = get_settings()
    models = []
    for model_id, config in MODEL_REGISTRY.items():
        api_key = getattr(settings, config["api_key_field"], "")
        if api_key:
            models.append({
                "id": model_id,
                "provider": config["provider"],
                "name": config["display_name"],
                "description": config["description"],
            })
    return models


def _get_api_key(model_id: str) -> str:
    """获取模型对应的 API Key"""
    config = MODEL_REGISTRY.get(model_id)
    if not config:
        return ""
    settings = get_settings()
    return getattr(settings, config["api_key_field"], "") or ""


async def call_llm(
    system_prompt: str,
    user_prompt: str,
    model_id: Optional[str] = None,
    max_tokens: int = 800,
    temperature: float = 0.7,
) -> Tuple[Optional[str], Optional[str]]:
    """
    统一大模型调用接口

    Args:
        system_prompt: 系统提示词
        user_prompt: 用户提示词
        model_id: 模型ID（为空则使用默认模型）
        max_tokens: 最大生成 token 数
        temperature: 温度参数

    Returns:
        Tuple of (content, error_type)
    """
    if not model_id or model_id not in MODEL_REGISTRY:
        model_id = DEFAULT_MODEL

    config = MODEL_REGISTRY[model_id]
    api_key = _get_api_key(model_id)

    if not api_key:
        print(f"[LLM] 模型 {model_id} 未配置 API Key")
        return None, "no_api_key"

    try:
        data = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        client = get_client()
        resp = await client.post(
            config["api_url"],
            json=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            timeout=config["timeout"],
        )

        if resp.status_code != 200:
            error_body = resp.text
            print(f"[LLM] {model_id} API HTTP {resp.status_code}: {error_body[:200]}")

            if resp.status_code == 401:
                return None, "auth_failed"
            elif resp.status_code == 429:
                # 区分限流和余额不足
                if "1113" in error_body or "余额" in error_body or "quota" in error_body.lower():
                    return None, "quota_exhausted"
                return None, "rate_limited"
            elif resp.status_code >= 500:
                return None, "unavailable"
            else:
                return None, "api_error"

        result = resp.json()

        if result.get("choices") and len(result["choices"]) > 0:
            content = result["choices"][0].get("message", {}).get("content", "")
            if content:
                return content.strip(), None

        return None, None

    except asyncio.TimeoutError:
        print(f"[LLM] {model_id} 超时")
        return None, "timeout"

    except Exception as e:
        print(f"[LLM] {model_id} 调用失败: {e}")
        return None, "unknown"
