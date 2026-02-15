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
    # 智谱 GLM-5（最新旗舰）
    "glm-5": {
        "provider": "zhipu",
        "api_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "api_key_field": "glm_api_key",
        "display_name": "GLM-5",
        "description": "最新旗舰模型，744B MoE，支持推理（付费）",
        "max_tokens": 4096,
        "timeout": 90,
        "free": False,
    },
    # 智谱 GLM-4.7 系列
    "glm-4.7": {
        "provider": "zhipu",
        "api_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "api_key_field": "glm_api_key",
        "display_name": "GLM-4.7",
        "description": "最新旗舰模型，能力最强（付费）",
        "max_tokens": 4096,
        "timeout": 60,
        "free": False,
    },
    "glm-4.7-flash": {
        "provider": "zhipu",
        "api_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "api_key_field": "glm_api_key",
        "display_name": "GLM-4.7-Flash",
        "description": "最新轻量模型，免费",
        "max_tokens": 4096,
        "timeout": 20,
        "free": True,
    },
    # 智谱 GLM-4 系列
    "glm-4-flash": {
        "provider": "zhipu",
        "api_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "api_key_field": "glm_api_key",
        "display_name": "GLM-4-Flash",
        "description": "上代轻量模型，免费",
        "max_tokens": 4096,
        "timeout": 15,
        "free": True,
    },
    "glm-4-air": {
        "provider": "zhipu",
        "api_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "api_key_field": "glm_api_key",
        "display_name": "GLM-4-Air",
        "description": "均衡模型（付费）",
        "max_tokens": 4096,
        "timeout": 20,
        "free": False,
    },
    "glm-4-plus": {
        "provider": "zhipu",
        "api_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "api_key_field": "glm_api_key",
        "display_name": "GLM-4-Plus",
        "description": "上代旗舰模型（付费）",
        "max_tokens": 4096,
        "timeout": 30,
        "free": False,
    },
    "glm-4-long": {
        "provider": "zhipu",
        "api_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "api_key_field": "glm_api_key",
        "display_name": "GLM-4-Long",
        "description": "长上下文模型，128K（付费）",
        "max_tokens": 4096,
        "timeout": 30,
        "free": False,
    },
    # DeepSeek 系列
    "deepseek-chat": {
        "provider": "deepseek",
        "api_url": "https://api.deepseek.com/chat/completions",
        "api_key_field": "deepseek_api_key",
        "display_name": "DeepSeek-V3",
        "description": "DeepSeek通用对话模型（付费）",
        "max_tokens": 4096,
        "timeout": 30,
        "free": False,
    },
    "deepseek-reasoner": {
        "provider": "deepseek",
        "api_url": "https://api.deepseek.com/chat/completions",
        "api_key_field": "deepseek_api_key",
        "display_name": "DeepSeek-R1",
        "description": "DeepSeek推理模型（付费）",
        "max_tokens": 4096,
        "timeout": 60,
        "free": False,
    },
}

# 默认模型
DEFAULT_MODEL = "glm-5"


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
                "free": config.get("free", False),
            })
    return models


def _get_api_key(model_id: str) -> str:
    """获取模型对应的 API Key"""
    config = MODEL_REGISTRY.get(model_id)
    if not config:
        return ""
    settings = get_settings()
    return getattr(settings, config["api_key_field"], "") or ""


async def _call_llm_once(
    config: Dict,
    api_key: str,
    model_id: str,
    data: Dict,
) -> Tuple[Optional[str], Optional[str]]:
    """单次 LLM 调用"""
    try:
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
                if "1113" in error_body or "余额" in error_body or "quota" in error_body.lower():
                    return None, "quota_exhausted"
                return None, "rate_limited"
            elif resp.status_code >= 500:
                return None, "unavailable"
            else:
                return None, "api_error"

        result = resp.json()

        if result.get("choices") and len(result["choices"]) > 0:
            message = result["choices"][0].get("message", {})
            content = message.get("content", "")
            # GLM-5 思考模式：content 可能为空，实际内容在 reasoning_content
            if not content and message.get("reasoning_content"):
                content = message["reasoning_content"]
            if content:
                return content.strip(), None

        # 调试：记录意外的空响应
        print(f"[LLM] {model_id} 返回200但无有效内容: {str(result)[:500]}")
        return None, None

    except asyncio.TimeoutError:
        print(f"[LLM] {model_id} 超时")
        return None, "timeout"

    except Exception as e:
        print(f"[LLM] {model_id} 调用失败: {e}")
        return None, "unknown"


async def call_llm(
    system_prompt: str,
    user_prompt: str,
    model_id: Optional[str] = None,
    max_tokens: int = 800,
    temperature: float = 0.7,
) -> Tuple[Optional[str], Optional[str]]:
    """
    统一大模型调用接口（含速率限制重试）
    """
    if not model_id or model_id not in MODEL_REGISTRY:
        model_id = DEFAULT_MODEL

    config = MODEL_REGISTRY[model_id]
    api_key = _get_api_key(model_id)

    if not api_key:
        print(f"[LLM] 模型 {model_id} 未配置 API Key")
        return None, "no_api_key"

    data = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    # GLM-5 倾向输出完整推理链，增大 token 并在 system prompt 中约束
    if model_id == "glm-5":
        data["max_tokens"] = max(max_tokens, 2048)
        data["messages"][0]["content"] += "\n\n重要：请直接给出结论性的回答，不要展示你的推理步骤、分析过程或思考链。"

    # 最多重试2次（速率限制时等待后重试）
    for attempt in range(3):
        content, error_type = await _call_llm_once(config, api_key, model_id, data)
        if error_type == "rate_limited" and attempt < 2:
            wait = 3 * (attempt + 1)
            print(f"[LLM] {model_id} 速率限制，{wait}秒后重试 ({attempt + 1}/2)")
            await asyncio.sleep(wait)
            continue
        return content, error_type

    return None, "rate_limited"
