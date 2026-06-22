from __future__ import annotations

import ast
import json
import logging
import re
import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Callable

import httpx
from openai import APIStatusError, OpenAI
from pydantic import ValidationError

from app.core.config import settings
from app.models.project import Project
from app.schemas.screenplay import ScreenplayDocument


DETAIL_LEVELS = {"brief", "standard", "detailed"}
FAST_LOCAL_ANALYSIS_CHAR_LIMIT = 12_000
AI_CHAPTER_PROMPT_CHAR_LIMIT = 1_600
OMITTED_REASONS = {
    "brief": "已省略非关键细节、重复心理描写和背景解释。",
    "standard": "已压缩支线细节和重复背景说明，保留主要场景、冲突和关键对白。",
    "detailed": "尽量保留原文主要场景和对白，仅压缩重复说明和难以剧本化的背景叙述。",
}

logger = logging.getLogger(__name__)
_last_llm_raw_response: str | None = None
_llm_config_override: ContextVar[dict[str, Any] | None] = ContextVar("llm_config_override", default=None)


class AIParseError(RuntimeError):
    """Raised when AI parsing or validation fails."""


class SafeJsonParseError(ValueError):
    """Raised when an LLM response cannot be parsed into a JSON object."""

    def __init__(self, message: str, raw_response: str, cleaned_response: str = "") -> None:
        super().__init__(message)
        self.raw_response = raw_response
        self.cleaned_response = cleaned_response


@dataclass(frozen=True)
class LLMResult:
    provider: str
    content: dict[str, Any]
    fallback_reason: str | None = None


@contextmanager
def llm_config_context(config: dict[str, Any] | None):
    token = _llm_config_override.set(config or None)
    try:
        yield
    finally:
        _llm_config_override.reset(token)


def build_user_llm_config(user: Any | None) -> dict[str, Any] | None:
    if user is None:
        return None

    provider = str(getattr(user, "llm_provider", None) or settings.llm_provider or "openai_compatible").strip()
    base_url = str(getattr(user, "llm_base_url", None) or "").strip()
    api_key = str(getattr(user, "llm_api_key", None) or "").strip()
    model = str(getattr(user, "llm_model", None) or "").strip()

    if not base_url or not model:
        return None
    if provider.lower() != "ollama" and not api_key:
        return None

    return {
        "provider": provider,
        "base_url": base_url,
        "api_key": api_key,
        "model": model,
        "timeout_seconds": settings.llm_timeout_seconds,
    }


def is_user_llm_configured(user: Any | None) -> bool:
    return build_user_llm_config(user) is not None


def call_model_text(prompt: str, *, system_prompt: str = "你是一个简洁可靠的中文助手。") -> str:
    _require_llm_config()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    if _effective_llm_provider() == "ollama":
        return _ollama_text_content(messages, max_tokens=512)

    client = OpenAI(
        api_key=_effective_llm_api_key(),
        base_url=_effective_llm_base_url(),
        timeout=_effective_llm_timeout_seconds(),
    )
    response = _create_chat_completion_with_policy(
        client,
        {
            "model": _effective_llm_model(),
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 512,
        },
        purpose="profile_llm_test",
    )
    return response.choices[0].message.content or ""


def analyze_project(project: Project) -> LLMResult:
    _require_llm_config()
    source_chars = sum(len(chapter.content or "") for chapter in project.chapters)
    logger.info(
        "AI analysis started project_id=%s text_chars=%s chapters=%s real_ai=%s mock_fallback=%s",
        getattr(project, "id", None),
        source_chars,
        len(project.chapters),
        True,
        False,
    )

    if source_chars > FAST_LOCAL_ANALYSIS_CHAR_LIMIT:
        fallback_reason = "小说正文较长，已使用本地快速解析，避免 AI 长时间等待。"
        content = _local_project_analysis(project)
    else:
        result = _call_deepseek(
            _project_analysis_prompt(project),
            timeout_seconds=min(settings.llm_timeout_seconds, 12),
        )
        if _is_valid_project_analysis(result):
            content = _normalize_project_analysis(result)
            fallback_reason = None
        else:
            fallback_reason = "AI 返回超时或格式不完整，已使用本地快速解析兜底。"
            content = _local_project_analysis(project)

    if fallback_reason:
        logger.warning(
            "AI analysis fallback project_id=%s reason=%s",
            getattr(project, "id", None),
            fallback_reason,
        )

    chapter_results = content["chapter_analyses"]
    scene_count = sum(len(item.get("analysis", {}).get("events", []) or []) for item in chapter_results)
    logger.info(
        "AI analysis completed project_id=%s characters=%s locations=%s scenes=%s mock_fallback=%s",
        getattr(project, "id", None),
        len(content["characters"]),
        len(content["locations"]),
        scene_count,
        fallback_reason is not None,
    )
    return LLMResult(provider=settings.llm_provider, content=content, fallback_reason=fallback_reason)


ProgressCallback = Callable[[str, int], None]


def generate_screenplay(
    project: Project,
    analysis: dict[str, Any] | None = None,
    progress_callback: ProgressCallback | None = None,
) -> LLMResult:
    _require_llm_config()
    generation_settings = _project_generation_settings(project)
    detail_level = _detail_level(generation_settings)
    if analysis is None:
        raise AIParseError("AI 解析失败，请重试：请先完成第 2 步 AI 解析。")
    source_analysis = analysis
    if not _is_valid_global_analysis(source_analysis):
        raise AIParseError("AI 解析失败，请重试：缺少可用的人物或地点解析结果。")
    logger.info(
        "AI screenplay generation started project_id=%s detail_level=%s analysis_characters=%s analysis_locations=%s mock_fallback=%s",
        getattr(project, "id", None),
        detail_level,
        len(source_analysis.get("characters", []) or []),
        len(source_analysis.get("locations", []) or []),
        False,
    )

    result = _generate_screenplay_in_stages(
        project,
        source_analysis,
        generation_settings,
        detail_level,
        progress_callback=progress_callback,
    )

    errors = _validate_screenplay_result(result)
    if errors:
        _print_llm_failure("screenplay_generation", "剧本 Schema 校验失败：" + "；".join(errors))
        raise AIParseError("AI 解析失败，请重试：" + "；".join(errors))

    scene_count = sum(len(chapter.get("scenes", []) or []) for chapter in result.get("script", {}).get("chapters", []) or [])
    logger.info(
        "AI screenplay generation completed project_id=%s scenes=%s mock_fallback=%s",
        getattr(project, "id", None),
        scene_count,
        False,
    )
    return LLMResult(provider=settings.llm_provider, content=result)


def _require_llm_config() -> None:
    provider = _effective_llm_provider()
    if provider == "ollama":
        if not (_effective_llm_base_url() and _effective_llm_model()):
            raise AIParseError("本地 Ollama 未配置，请检查 OLLAMA_BASE_URL 和 OLLAMA_MODEL。")
        return

    if not (_effective_llm_api_key() and _effective_llm_base_url() and _effective_llm_model()):
        raise AIParseError("AI 服务未配置，请检查 API Key、Base URL 或模型配置。")


def get_last_llm_raw_response() -> str | None:
    return _last_llm_raw_response


def clear_last_llm_raw_response() -> None:
    global _last_llm_raw_response
    _last_llm_raw_response = None


def _print_llm_failure(purpose: str, message: str) -> None:
    raw = (get_last_llm_raw_response() or "").strip()
    raw_head = raw[:4000] if raw else "<empty>"
    print(
        f"LLM {purpose} failed: {message}\n"
        f"LLM {purpose} raw/error first 4000 chars:\n{raw_head}",
        flush=True,
    )
    logger.error(
        "LLM %s failed: %s raw/error head=%r",
        purpose,
        message,
        raw_head,
    )


def _call_deepseek(
    prompt: str,
    timeout_seconds: int | None = None,
    max_tokens: int = 4096,
    purpose: str = "llm_call",
) -> dict[str, Any] | None:
    if _effective_llm_provider() == "ollama":
        return _call_ollama(prompt, timeout_seconds=timeout_seconds, max_tokens=max_tokens, purpose=purpose)

    global _last_llm_raw_response
    _last_llm_raw_response = None
    content = ""
    try:
        client = OpenAI(
            api_key=_effective_llm_api_key(),
            base_url=_effective_llm_base_url(),
            timeout=timeout_seconds or _effective_llm_timeout_seconds(),
        )
        request = _deepseek_request_payload(prompt, max_tokens=max_tokens)
        response = _create_chat_completion_with_policy(client, request, purpose=purpose)
        content = response.choices[0].message.content
        _last_llm_raw_response = content
        if not content:
            return None
        try:
            parsed = safe_json_parse(content, purpose=purpose)
        except SafeJsonParseError as parse_exc:
            print(
                f"LLM {purpose} JSON parse failed, attempting JSON repair: {parse_exc}",
                flush=True,
            )
            logger.warning("LLM %s JSON parse failed, attempting repair: %s", purpose, parse_exc)
            repaired_content = _repair_json_response(
                client,
                content,
                str(parse_exc),
                timeout_seconds=timeout_seconds,
                max_tokens=max_tokens,
                purpose=purpose,
            )
            _last_llm_raw_response = repaired_content
            parsed = safe_json_parse(repaired_content, purpose=f"{purpose}_repair")
    except AIParseError:
        raise
    except Exception as exc:
        _last_llm_raw_response = _llm_exception_debug_text(exc)
        print(f"LLM {purpose} raw/error head: {_last_llm_raw_response[:4000]}", flush=True)
        logger.warning("LLM call failed: %s", exc)
        return None
    if isinstance(parsed, dict):
        return parsed
    logger.warning("LLM returned non-JSON content head=%r", (content or "")[:1000])
    print(f"LLM {purpose} invalid JSON raw response head: {(content or '')[:4000]}", flush=True)
    return None


def _call_ollama(
    prompt: str,
    timeout_seconds: int | None = None,
    max_tokens: int = 4096,
    purpose: str = "llm_call",
) -> dict[str, Any] | None:
    global _last_llm_raw_response
    _last_llm_raw_response = None
    request = _deepseek_request_payload(prompt, max_tokens=max_tokens)
    content = ""

    try:
        content = _ollama_chat_content(
            request["messages"],
            timeout_seconds=timeout_seconds,
            max_tokens=max_tokens,
        )
        _last_llm_raw_response = content
        if not content:
            return None

        try:
            parsed = safe_json_parse(content, purpose=purpose)
        except SafeJsonParseError as parse_exc:
            print(
                f"LLM {purpose} JSON parse failed, attempting Ollama JSON repair: {parse_exc}",
                flush=True,
            )
            logger.warning("LLM %s JSON parse failed, attempting Ollama repair: %s", purpose, parse_exc)
            repaired_content = _ollama_repair_json_response(
                content,
                str(parse_exc),
                timeout_seconds=timeout_seconds,
                max_tokens=max_tokens,
            )
            _last_llm_raw_response = repaired_content
            parsed = safe_json_parse(repaired_content, purpose=f"{purpose}_repair")
    except AIParseError:
        raise
    except Exception as exc:
        _last_llm_raw_response = _llm_exception_debug_text(exc)
        print(f"LLM {purpose} raw/error head: {_last_llm_raw_response[:4000]}", flush=True)
        logger.warning("Ollama LLM call failed: %s", exc)
        return None

    if isinstance(parsed, dict):
        return parsed

    logger.warning("Ollama returned non-JSON content head=%r", (content or "")[:1000])
    print(f"LLM {purpose} invalid JSON raw response head: {(content or '')[:4000]}", flush=True)
    return None


def _ollama_chat_content(
    messages: list[dict[str, str]],
    timeout_seconds: int | None = None,
    max_tokens: int = 4096,
) -> str:
    base_url = (_override_value("base_url") or settings.ollama_base_url or "http://127.0.0.1:11434").rstrip("/")
    if base_url.endswith("/v1"):
        base_url = base_url[:-3]
    payload = {
        "model": _effective_llm_model(),
        "messages": messages,
        "stream": False,
        "think": False,
        "format": "json",
        "options": {
            "temperature": 0.1,
            "num_predict": max_tokens,
        },
    }
    response = httpx.post(
        f"{base_url}/api/chat",
        json=payload,
        timeout=timeout_seconds or _effective_llm_timeout_seconds(),
    )
    response.raise_for_status()
    data = response.json()
    message = data.get("message") or {}
    return str(message.get("content") or "")


def _ollama_text_content(
    messages: list[dict[str, str]],
    timeout_seconds: int | None = None,
    max_tokens: int = 512,
) -> str:
    base_url = (_override_value("base_url") or settings.ollama_base_url or "http://127.0.0.1:11434").rstrip("/")
    if base_url.endswith("/v1"):
        base_url = base_url[:-3]
    payload = {
        "model": _effective_llm_model(),
        "messages": messages,
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0.2,
            "num_predict": max_tokens,
        },
    }
    response = httpx.post(
        f"{base_url}/api/chat",
        json=payload,
        timeout=timeout_seconds or _effective_llm_timeout_seconds(),
    )
    response.raise_for_status()
    data = response.json()
    message = data.get("message") or {}
    return str(message.get("content") or "")


def _ollama_repair_json_response(
    raw_content: str,
    parse_error: str,
    timeout_seconds: int | None = None,
    max_tokens: int = 4096,
) -> str:
    prompt = "\n".join(
        [
            "只修复 JSON 格式，不要改内容。",
            "不要新增字段，不要删除字段，不要解释。",
            "只返回一个合法 JSON 对象。",
            f"JSON 解析错误：{parse_error}",
            "需要修复的原始内容：",
            raw_content,
        ]
    )
    request = _deepseek_request_payload(prompt, max_tokens=max_tokens)
    repaired = _ollama_chat_content(
        request["messages"],
        timeout_seconds=timeout_seconds,
        max_tokens=max_tokens,
    )
    print(f"LLM repaired JSON response head: {repaired[:1000]}", flush=True)
    return repaired


def _llm_exception_debug_text(exc: Exception) -> str:
    parts = [
        "LLM 请求异常，未收到可解析的模型响应。",
        f"{type(exc).__name__}: {exc}",
    ]
    cause = getattr(exc, "__cause__", None)
    if cause is not None:
        parts.append(f"cause={type(cause).__name__}: {cause}")
    context = getattr(exc, "__context__", None)
    if context is not None and context is not cause:
        parts.append(f"context={type(context).__name__}: {context}")
    response = getattr(exc, "response", None)
    response_text = getattr(response, "text", None)
    if response_text:
        parts.append(f"response_text={response_text}")
    return "\n".join(parts)


def _deepseek_request_payload(prompt: str, max_tokens: int = 4096) -> dict[str, Any]:
    json_user_prompt = "\n".join(
        [
            "请严格输出 json。",
            "只返回 json 对象。",
            "不要 Markdown。",
            "不要解释。",
            "不要 ```json 代码块。",
            prompt,
        ]
    )
    payload: dict[str, Any] = {
        "model": _effective_llm_model(),
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是小说结构化解析器。必须只返回 json 对象。"
                    "不要 Markdown，不要解释，不要 ```json 代码块。"
                ),
            },
            {"role": "user", "content": json_user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": max_tokens,
    }
    if _should_use_json_response_format():
        payload["response_format"] = {"type": "json_object"}
    return payload


def _effective_llm_model() -> str:
    override_model = _override_value("model")
    if override_model:
        return override_model

    if _effective_llm_provider() == "ollama":
        return settings.llm_model or settings.ollama_model or "qwen3.5:9b"

    model = settings.llm_model or "deepseek-chat"
    if "deepseek" in model.lower() and "reasoner" in model.lower():
        return "deepseek-chat"
    return model


def _effective_llm_provider() -> str:
    return (_override_value("provider") or settings.llm_provider or "openai_compatible").strip().lower()


def _effective_llm_base_url() -> str:
    if _effective_llm_provider() == "ollama":
        base_url = (_override_value("base_url") or settings.llm_base_url or settings.ollama_base_url or "http://127.0.0.1:11434").strip()
        base_url = base_url.rstrip("/")
        if not base_url.endswith("/v1"):
            base_url = f"{base_url}/v1"
        return base_url

    return (_override_value("base_url") or settings.llm_base_url or "").strip()


def _effective_llm_api_key() -> str:
    if _effective_llm_provider() == "ollama":
        return _override_value("api_key") or settings.llm_api_key or "ollama"
    return _override_value("api_key") or settings.llm_api_key


def _effective_llm_timeout_seconds() -> int:
    value = _override_value("timeout_seconds")
    if value is None:
        return settings.llm_timeout_seconds
    try:
        return int(value)
    except (TypeError, ValueError):
        return settings.llm_timeout_seconds


def _override_value(key: str) -> Any:
    config = _llm_config_override.get()
    if not config:
        return None
    value = config.get(key)
    if isinstance(value, str):
        value = value.strip()
    return value or None


def _should_use_json_response_format() -> bool:
    provider = _effective_llm_provider()
    model = _effective_llm_model().lower()
    base_url = _effective_llm_base_url().lower()
    return provider == "openai_compatible" and ("deepseek" in model or "deepseek" in base_url)


def _create_chat_completion_with_policy(client: OpenAI, request: dict[str, Any], *, purpose: str):
    max_retries = min(settings.llm_max_retries, 1)
    attempt = 0
    while True:
        try:
            return _create_chat_completion(client, request)
        except APIStatusError as exc:
            status_code = getattr(exc, "status_code", None)
            message = _api_status_error_message(exc)
            _last_error = f"LLM API error status={status_code}: {message}"
            print(f"LLM {purpose} API error: {_last_error}", flush=True)
            logger.warning("LLM %s API error status=%s: %s", purpose, status_code, message)

            if status_code == 402:
                raise AIParseError("DeepSeek 账户余额不足，请充值或更换 API Key。") from exc
            if status_code in {401, 403}:
                raise AIParseError(f"LLM API 鉴权失败或无权限（HTTP {status_code}）：{message}") from exc
            if status_code == 429 and attempt < max_retries:
                attempt += 1
                wait_seconds = _retry_after_seconds(exc) or 1.5
                print(f"LLM {purpose} rate limited, retrying in {wait_seconds:.1f}s", flush=True)
                time.sleep(wait_seconds)
                continue
            if status_code is not None and 500 <= status_code < 600 and attempt < max_retries:
                attempt += 1
                wait_seconds = _retry_after_seconds(exc) or 1.5
                print(f"LLM {purpose} server error, retrying in {wait_seconds:.1f}s", flush=True)
                time.sleep(wait_seconds)
                continue
            raise AIParseError(f"LLM API 请求失败（HTTP {status_code}）：{message}") from exc


def _api_status_error_message(exc: APIStatusError) -> str:
    response = getattr(exc, "response", None)
    response_text = getattr(response, "text", None)
    if response_text:
        return str(response_text)[:1000]
    return str(exc)


def _retry_after_seconds(exc: APIStatusError) -> float | None:
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None)
    if not headers:
        return None
    value = headers.get("retry-after") if hasattr(headers, "get") else None
    if not value:
        return None
    try:
        return max(0.0, min(float(value), 30.0))
    except ValueError:
        return None


def _create_chat_completion(client: OpenAI, request: dict[str, Any]):
    try:
        return client.chat.completions.create(**request)
    except Exception as exc:
        message = str(exc).lower()
        fallback_request = dict(request)
        changed = False
        if "response_format" in fallback_request and "response_format" in message:
            logger.warning("LLM response_format unsupported, retrying without response_format: %s", exc)
            print(f"LLM response_format unsupported, retrying without response_format: {exc}", flush=True)
            fallback_request.pop("response_format", None)
            changed = True
        if int(fallback_request.get("max_tokens") or 0) > 4096 and (
            "max_tokens" in message or "maximum" in message or "token" in message
        ):
            logger.warning("LLM max_tokens unsupported, retrying with max_tokens=4096: %s", exc)
            print(f"LLM max_tokens unsupported, retrying with max_tokens=4096: {exc}", flush=True)
            fallback_request["max_tokens"] = 4096
            changed = True
        if not changed:
            raise
        return client.chat.completions.create(**fallback_request)


def _repair_json_response(
    client: OpenAI,
    raw_content: str,
    parse_error: str,
    timeout_seconds: int | None = None,
    max_tokens: int = 4096,
    purpose: str = "llm_call",
) -> str:
    prompt = "\n".join(
        [
            "只修复 JSON 格式，不要改内容。",
            "不要新增字段，不要删减字段，不要解释。",
            "只返回一个合法 JSON 对象。",
            f"JSON 解析错误：{parse_error}",
            "需要修复的原始内容：",
            raw_content,
        ]
    )
    request = _deepseek_request_payload(prompt, max_tokens=max_tokens)
    response = _create_chat_completion_with_policy(client, request, purpose=f"{purpose}_repair")
    repaired = response.choices[0].message.content or ""
    print(f"LLM {purpose} repaired JSON response head: {repaired[:1000]}", flush=True)
    return repaired


def extract_json_from_text(content: str) -> dict[str, Any] | None:
    try:
        return safe_json_parse(content, purpose="extract_json_from_text")
    except SafeJsonParseError:
        return None


def safe_json_parse(content: str, *, purpose: str = "llm_call") -> dict[str, Any]:
    if not isinstance(content, str) or not content.strip():
        raise SafeJsonParseError("empty response", content or "")

    cleaned = content.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        cleaned = fenced.group(1).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end <= start:
        message = "no JSON object found between first { and last }"
        _log_json_parse_failure(purpose, message, content, cleaned)
        raise SafeJsonParseError(message, content, cleaned)

    candidate = cleaned[start : end + 1]
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        message = f"json.loads failed at line {exc.lineno} column {exc.colno}: {exc.msg}"
        _log_json_parse_failure(purpose, message, content, candidate)
        raise SafeJsonParseError(message, content, candidate) from exc

    if not isinstance(parsed, dict):
        message = f"parsed JSON root must be object, got {type(parsed).__name__}"
        _log_json_parse_failure(purpose, message, content, candidate)
        raise SafeJsonParseError(message, content, candidate)
    return parsed


def _log_json_parse_failure(purpose: str, message: str, raw: str, cleaned: str) -> None:
    print(
        f"LLM {purpose} safe_json_parse failed: {message}\n"
        f"LLM {purpose} raw response first 4000 chars:\n{(raw or '')[:4000]}\n"
        f"LLM {purpose} extracted candidate first 4000 chars:\n{(cleaned or '')[:4000]}",
        flush=True,
    )
    logger.error(
        "LLM %s safe_json_parse failed: %s raw=%r cleaned=%r",
        purpose,
        message,
        (raw or "")[:8000],
        (cleaned or "")[:8000],
    )


def _parse_json_object(content: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass

    cleaned = content.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        cleaned = fenced.group(1).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end <= start:
        return None

    try:
        parsed = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _project_analysis_prompt(project: Project) -> str:
    template = {
        "chapter_analyses": [
            {
                "chapter_number": 1,
                "source_title": "章节标题",
                "analysis": {
                    "chapter_title": "章节标题",
                    "characters": [
                        {"name": "人物名", "aliases": [], "role": "角色", "description": "", "evidence": ""}
                    ],
                    "locations": [{"name": "地点名", "description": "", "evidence": ""}],
                    "organizations": [{"name": "组织名", "description": "", "evidence": ""}],
                    "events": [
                        {
                            "title": "事件标题",
                            "summary": "事件摘要",
                            "characters": ["人物名"],
                            "location": "地点名",
                            "evidence": "",
                        }
                    ],
                    "dialogues": [
                        {
                            "speaker": "人物名",
                            "line": "对白",
                            "line_type": "dialogue",
                            "emotion": "neutral",
                            "evidence": "",
                        }
                    ],
                },
            }
        ],
        "characters": [{"id": "char_001", "name": "人物名", "aliases": [], "role": "角色", "description": ""}],
        "locations": [{"id": "loc_001", "name": "地点名", "description": ""}],
        "organizations": [{"id": "org_001", "name": "组织名", "description": ""}],
        "alias_map": [{"alias": "别名", "canonical": "人物名", "evidence": "", "confidence": 0.95}],
        "themes": [],
        "conflicts": [],
    }
    chapters = [
        {
            "number": chapter.number,
            "title": chapter.title,
            "content": _prompt_chapter_text(chapter.content),
        }
        for chapter in project.chapters
    ]
    return "\n".join(
        [
            "你是小说结构化解析器。",
            "请一次性完成整本小说的结构化解析，避免逐章多轮往返。",
            "必须严格返回 JSON 对象，不要输出解释、Markdown 或代码块。",
            "",
            "要求：",
            "1. chapter_analyses 必须包含每个输入章节的解析。",
            "2. characters 和 locations 是全局合并后的实体，必须带 id 和 name。",
            "3. 不要把动作短语、地点、组织、普通名词识别成人物。",
            "4. 对白 line_type 只能是 dialogue、monologue 或 narration。",
            "5. 无法确认说话人时 speaker 为 null。",
            "",
            "返回 JSON 必须符合这个结构：",
            json.dumps(template, ensure_ascii=False),
            "",
            f"小说标题：{project.title}",
            f"作者：{project.author or '未知'}",
            "章节：",
            json.dumps(chapters, ensure_ascii=False),
        ]
    )


def _prompt_chapter_text(text: str) -> str:
    compact = re.sub(r"\s+", "\n", text or "").strip()
    if len(compact) <= AI_CHAPTER_PROMPT_CHAR_LIMIT:
        return compact
    head_length = int(AI_CHAPTER_PROMPT_CHAR_LIMIT * 0.75)
    tail_length = AI_CHAPTER_PROMPT_CHAR_LIMIT - head_length
    return f"{compact[:head_length]}\n...[中间内容已压缩]...\n{compact[-tail_length:]}"


def _chapter_analysis_prompt(chapter_number: int, chapter_title: str, chapter_text: str) -> str:
    template = {
        "chapter_title": "",
        "characters": [
            {
                "name": "",
                "aliases": [],
                "role": "",
                "description": "",
                "evidence": "",
            }
        ],
        "locations": [
            {
                "name": "",
                "description": "",
                "evidence": "",
            }
        ],
        "organizations": [
            {
                "name": "",
                "description": "",
                "evidence": "",
            }
        ],
        "events": [
            {
                "title": "",
                "summary": "",
                "characters": [],
                "location": "",
                "evidence": "",
            }
        ],
        "dialogues": [
            {
                "speaker": "",
                "line": "",
                "line_type": "dialogue",
                "emotion": "",
                "evidence": "",
            }
        ],
    }
    return "\n".join(
        [
            "你是小说结构化解析器。",
            "",
            "请从当前章节文本中识别人物、地点、组织、剧情事件和对白。",
            "",
            "要求：",
            "1. 只识别真实人物，不要把动作短语、地点、组织、普通名词识别成人物。",
            "2. 如果出现“陈某反驳道”“中年男人回道”“少女淡淡道”这类表达，请理解真正说话人，不要把动作词并入人物名。",
            "3. 地点、组织、人物必须区分清楚。",
            "4. 如果同一人物有多个称呼，请放入 aliases。",
            "5. 对白尽量保留原文。",
            "6. 心理活动标记为 monologue。",
            "7. 旁白叙述标记为 narration。",
            "8. 不确定说话人时 speaker 为 null。",
            "9. 严格返回 JSON，不要输出解释。",
            "",
            "返回 JSON 必须符合这个结构：",
            json.dumps(template, ensure_ascii=False),
            "",
            f"章节编号：{chapter_number}",
            f"章节标题：{chapter_title}",
            "章节文本：",
            chapter_text,
        ]
    )


def _global_merge_prompt(project: Project, chapter_results: list[dict[str, Any]]) -> str:
    template = {
        "characters": [
            {
                "id": "char_001",
                "name": "",
                "aliases": [],
                "role": "",
                "description": "",
            }
        ],
        "locations": [
            {
                "id": "loc_001",
                "name": "",
                "description": "",
            }
        ],
        "organizations": [
            {
                "id": "org_001",
                "name": "",
                "description": "",
            }
        ],
        "alias_map": [
            {
                "alias": "",
                "canonical": "",
                "evidence": "",
                "confidence": 0.95,
            }
        ],
        "themes": [],
        "conflicts": [],
    }
    return "\n".join(
        [
            "请对所有章节解析结果做全局实体合并。",
            "要求：",
            "1. 合并同一人物的不同称呼。",
            "2. 合并同一地点的不同称呼。",
            "3. 不允许 characters 和 locations 重复。",
            "4. 不允许把地点、组织、普通物品放进 characters。",
            "5. 不允许写死任何当前测试小说的人名和地点，只能依据输入证据。",
            "6. 严格返回 JSON，不要输出解释。",
            "",
            "返回 JSON 必须符合这个结构：",
            json.dumps(template, ensure_ascii=False),
            "",
            f"小说标题：{project.title}",
            f"作者：{project.author or '未知'}",
            "章节解析结果：",
            json.dumps(chapter_results, ensure_ascii=False),
        ]
    )


def _generate_screenplay_in_stages(
    project: Project,
    analysis: dict[str, Any],
    generation_settings: dict[str, Any],
    detail_level: str,
    progress_callback: ProgressCallback | None = None,
) -> dict[str, Any]:
    if progress_callback:
        progress_callback("正在整理剧本人物、地点和改编说明", 42)
    metadata = _call_deepseek(
        _screenplay_metadata_prompt(project, analysis, generation_settings, detail_level),
        max_tokens=2048,
        purpose="screenplay_metadata",
    )
    if not isinstance(metadata, dict):
        _print_llm_failure("screenplay_metadata", "metadata JSON generation failed; using analysis fallback.")
        metadata = _screenplay_metadata_from_analysis(analysis, detail_level)
    if progress_callback:
        progress_callback("剧本元数据已准备，开始生成章节", 48)

    document = _screenplay_json_template(project, generation_settings, detail_level)
    script = document["script"]
    script["characters"] = _normalize_script_characters(metadata.get("characters"), analysis)
    script["locations"] = _normalize_script_locations(metadata.get("locations"), analysis)
    script["organizations"] = _normalize_script_organizations(metadata.get("organizations"), analysis)
    script["world_settings"] = _normalize_script_world_settings(metadata.get("world_settings"))
    script["adaptation_notes"] = _normalize_adaptation_notes(
        metadata.get("adaptation_notes"),
        analysis,
        script["adaptation_notes"],
    )
    _split_world_settings_from_locations(script)

    character_ids = {item["id"] for item in script["characters"]}
    location_ids = {item["id"] for item in script["locations"]}
    default_location_id = script["locations"][0]["id"]
    chapters = []
    failed_chapters = []

    sorted_chapters = sorted(project.chapters, key=lambda item: item.number)
    total_chapters = len(sorted_chapters) or 1
    for chapter_index, chapter in enumerate(sorted_chapters, start=1):
        chapter_analysis = _analysis_for_chapter(analysis, chapter.number)
        if progress_callback:
            progress_callback(
                f"正在生成第 {chapter_index}/{total_chapters} 章：{chapter.title}",
                50 + round((chapter_index - 1) / total_chapters * 35),
            )
        try:
            generated = _call_deepseek(
                _screenplay_chapter_prompt(
                    project,
                    chapter,
                    chapter_analysis,
                    script["characters"],
                    script["locations"],
                    generation_settings,
                    detail_level,
                ),
                max_tokens=3072,
                purpose=f"screenplay_chapter_{chapter.number}",
            )
            chapter_payload = _normalize_generated_chapter(
                chapter,
                generated,
                chapter_analysis,
                character_ids,
                location_ids,
                default_location_id,
            )
        except Exception as exc:  # keep later chapters moving
            print(f"LLM screenplay chapter {chapter.number} failed, continuing: {exc}", flush=True)
            logger.exception("LLM screenplay chapter %s failed", chapter.number)
            chapter_payload = _failed_chapter_payload(chapter, default_location_id, str(exc))

        if chapter_payload.get("generation_status") == "failed":
            failed_chapters.append(
                {
                    "number": chapter.number,
                    "title": chapter.title,
                    "error": chapter_payload.get("generation_error") or "chapter generation failed",
                }
            )
        chapters.append(chapter_payload)
        if progress_callback:
            progress_callback(
                f"已完成第 {chapter_index}/{total_chapters} 章：{chapter.title}",
                50 + round(chapter_index / total_chapters * 35),
            )

    script["chapters"] = chapters
    script["metadata"]["coverage"]["generated_scenes"] = sum(len(chapter.get("scenes", []) or []) for chapter in chapters)
    script["metadata"]["coverage"]["preserved_dialogues"] = sum(
        len(scene.get("dialogue", []) or [])
        for chapter in chapters
        for scene in chapter.get("scenes", []) or []
    )
    if failed_chapters:
        failed_summary = "Failed chapters: " + "; ".join(
            f"{item['number']} {item['title']}: {item['error']}" for item in failed_chapters
        )
        script["adaptation_notes"]["omissions"].append(failed_summary)

    if progress_callback:
        progress_callback("正在汇总覆盖率并校验剧本结构", 88)
    _finalize_screenplay_document(document, generation_settings, analysis, detail_level)
    return document


def _screenplay_metadata_prompt(
    project: Project,
    analysis: dict[str, Any],
    generation_settings: dict[str, Any],
    detail_level: str,
) -> str:
    template = {
        "characters": [{"id": "char_001", "name": "人物名", "role": "角色", "gender": "unknown", "age": None, "description": ""}],
        "locations": [{"id": "loc_001", "name": "地点名", "description": ""}],
        "organizations": [{"id": "org_001", "name": "组织名", "description": ""}],
        "world_settings": [{"id": "world_001", "name": "世界观地点或设定", "description": ""}],
        "adaptation_notes": {
            "themes": [],
            "conflicts": [{"type": "个人困境", "description": "角色目标与阻碍", "characters": ["char_001"]}],
            "omissions": [],
            "template_rules": [],
        },
    }
    return "\n".join(
        [
            "Generate screenplay metadata only. Do not generate chapters, scenes, or dialogue.",
            "Return one JSON object only.",
            "Use the existing analysis as source truth. Preserve entity ids when possible.",
            "characters must contain id, name, role, gender, age, description.",
            "Do not use generic role='角色'. Infer concrete roles such as 主角、堂弟、叔父、府尹、打更人、司天监术士、狱卒.",
            "character descriptions must be 30-60 Chinese characters and explain relationship/function in the story.",
            "locations must contain only actual scene locations where action happens.",
            "Put worldview-only places into world_settings, not locations.",
            "adaptation_notes.conflicts must be an array of objects: {type, description, characters}. characters must use character ids.",
            "locations and organizations must contain id, name, description.",
            f"Project title: {project.title}",
            f"Author: {project.author or ''}",
            f"detail_level: {detail_level}",
            f"generation_settings: {json.dumps(generation_settings, ensure_ascii=False)}",
            "Required JSON shape:",
            json.dumps(template, ensure_ascii=False),
            "Existing analysis:",
            json.dumps(
                {
                    "characters": analysis.get("characters", []),
                    "locations": analysis.get("locations", []),
                    "organizations": analysis.get("organizations", []),
                    "themes": analysis.get("themes", []),
                    "conflicts": analysis.get("conflicts", []),
                },
                ensure_ascii=False,
            ),
        ]
    )


def _screenplay_metadata_from_analysis(analysis: dict[str, Any], detail_level: str) -> dict[str, Any]:
    conflicts = analysis.get("conflicts") if isinstance(analysis.get("conflicts"), list) else []
    omissions = [
        "剧本元数据由第 2 步解析结果兜底生成；AI metadata JSON 未通过解析。",
        OMITTED_REASONS[detail_level],
    ]
    return {
        "characters": analysis.get("characters", []),
        "locations": analysis.get("locations", []),
        "organizations": analysis.get("organizations", []),
        "world_settings": [],
        "adaptation_notes": {
            "themes": analysis.get("themes", []),
            "conflicts": conflicts,
            "omissions": omissions,
            "template_rules": [],
        },
    }


def _screenplay_chapter_prompt(
    project: Project,
    chapter,
    chapter_analysis: dict[str, Any],
    characters: list[dict[str, Any]],
    locations: list[dict[str, Any]],
    generation_settings: dict[str, Any],
    detail_level: str,
) -> str:
    template = {
        "chapter": {
            "id": f"ch_{chapter.number:03d}",
            "title": chapter.title,
            "source_chapter_numbers": [chapter.number],
            "summary": "章节摘要",
            "scenes": [
                {
                    "id": f"sc_{chapter.number:03d}_001",
                    "title": "场景标题",
                    "location_id": "loc_001",
                    "time": "时间",
                    "characters": ["char_001"],
                    "synopsis": "场景概要",
                    "source_range": {
                        "chapter": chapter.number,
                        "start_hint": "原文起始短句",
                        "end_hint": "原文结束短句",
                    },
                    "stage_directions": ["舞台或镜头调度"],
                    "dialogue": [
                        {
                            "speaker_id": "char_001",
                            "speaker_name": "人物名",
                            "line": "台词",
                            "emotion": "neutral",
                            "line_type": "dialogue",
                        }
                    ],
                }
            ],
        }
    }
    return "\n".join(
        [
            "Generate screenplay scenes for exactly one source chapter.",
            "Return one JSON object only. Do not include metadata or other chapters.",
            "Every location_id must be from allowed_locations. Every character id must be from allowed_characters.",
            "dialogue.speaker_id must be null when speaker is uncertain.",
            "line_type must be dialogue or monologue. Do not put narration into dialogue.",
            "Move narration, exposition, and descriptive prose into stage_directions.",
            "Keep only 4-8 key character dialogue lines per scene. Do not copy source paragraphs line by line.",
            "dialogue.speaker_name must match the allowed character name for dialogue.speaker_id.",
            "Do not invent template filler dialogue. Prefer concise source dialogue from chapter_analysis.",
            f"Project title: {project.title}",
            f"Source chapter number: {chapter.number}",
            f"Source chapter title: {chapter.title}",
            f"detail_level: {detail_level}",
            f"generation_settings: {json.dumps(generation_settings, ensure_ascii=False)}",
            "Required JSON shape:",
            json.dumps(template, ensure_ascii=False),
            "allowed_characters:",
            json.dumps(characters, ensure_ascii=False),
            "allowed_locations:",
            json.dumps(locations, ensure_ascii=False),
            "chapter_analysis:",
            json.dumps(chapter_analysis, ensure_ascii=False),
            "source_excerpt:",
            _prompt_excerpt(chapter.content, AI_CHAPTER_PROMPT_CHAR_LIMIT),
        ]
    )


def _normalize_script_characters(items: Any, analysis: dict[str, Any]) -> list[dict[str, Any]]:
    source = items if isinstance(items, list) and items else analysis.get("characters", [])
    characters = []
    for index, item in enumerate(source or [], start=1):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        characters.append(
            {
                "id": str(item.get("id") or f"char_{index:03d}"),
                "name": name,
                "role": str(item.get("role") or "角色"),
                "gender": str(item.get("gender") or "unknown"),
                "age": item.get("age") if isinstance(item.get("age"), int) else None,
                "description": str(item.get("description") or f"{name}。"),
            }
        )
    return characters or [
        {
            "id": "char_001",
            "name": "旁白",
            "role": "narrator",
            "gender": "unknown",
            "age": None,
            "description": "用于无法确认说话人的旁白。",
        }
    ]


def _normalize_script_locations(items: Any, analysis: dict[str, Any]) -> list[dict[str, Any]]:
    source = items if isinstance(items, list) and items else analysis.get("locations", [])
    locations = []
    for index, item in enumerate(source or [], start=1):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        locations.append(
            {
                "id": str(item.get("id") or f"loc_{index:03d}"),
                "name": name,
                "description": str(item.get("description") or f"{name}。"),
            }
        )
    return locations or [{"id": "loc_001", "name": "未明确地点", "description": "原文未明确地点。"}]


def _normalize_script_organizations(items: Any, analysis: dict[str, Any]) -> list[dict[str, Any]]:
    source = items if isinstance(items, list) else analysis.get("organizations", [])
    organizations = []
    for index, item in enumerate(source or [], start=1):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        organizations.append(
            {
                "id": str(item.get("id") or f"org_{index:03d}"),
                "name": name,
                "description": str(item.get("description") or f"{name}。"),
            }
        )
    return organizations


def _normalize_script_world_settings(items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    settings_items = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        settings_items.append(
            {
                "id": str(item.get("id") or f"world_{index:03d}"),
                "name": name,
                "description": str(item.get("description") or "世界观背景设定。").strip(),
            }
        )
    return settings_items


def _normalize_adaptation_notes(items: Any, analysis: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    data = items if isinstance(items, dict) else {}
    return {
        "themes": _list_of_strings(data.get("themes")) or _list_of_strings(analysis.get("themes")),
        "conflicts": _list_of_strings(data.get("conflicts")) or _list_of_strings(analysis.get("conflicts")),
        "omissions": _list_of_strings(data.get("omissions")) or list(defaults.get("omissions") or []),
        "template_rules": _list_of_strings(data.get("template_rules")) or list(defaults.get("template_rules") or []),
    }


def _analysis_for_chapter(analysis: dict[str, Any], chapter_number: int) -> dict[str, Any]:
    for item in analysis.get("chapter_analyses") or []:
        if not isinstance(item, dict):
            continue
        if item.get("chapter_number") == chapter_number:
            chapter_analysis = item.get("analysis")
            return chapter_analysis if isinstance(chapter_analysis, dict) else {}
    return {}


def _normalize_generated_chapter(
    source_chapter,
    generated: Any,
    chapter_analysis: dict[str, Any],
    character_ids: set[str],
    location_ids: set[str],
    default_location_id: str,
) -> dict[str, Any]:
    if not isinstance(generated, dict):
        return _failed_chapter_payload(source_chapter, default_location_id, "LLM did not return a JSON object.")

    payload = generated.get("chapter") if isinstance(generated.get("chapter"), dict) else generated
    raw_scenes = payload.get("scenes") if isinstance(payload, dict) else None
    if not isinstance(raw_scenes, list) or not raw_scenes:
        return _failed_chapter_payload(source_chapter, default_location_id, "LLM chapter response has no scenes.")

    scenes = [
        _normalize_scene(
            source_chapter.number,
            index,
            scene,
            character_ids,
            location_ids,
            default_location_id,
        )
        for index, scene in enumerate(raw_scenes, start=1)
        if isinstance(scene, dict)
    ]
    scenes = [scene for scene in scenes if scene is not None]
    if not scenes:
        return _failed_chapter_payload(source_chapter, default_location_id, "LLM chapter scenes were unusable.")

    return {
        "id": str(payload.get("id") or f"ch_{source_chapter.number:03d}"),
        "title": str(payload.get("title") or source_chapter.title or f"Chapter {source_chapter.number}"),
        "source_chapter_numbers": [source_chapter.number],
        "summary": str(payload.get("summary") or chapter_analysis.get("chapter_title") or _compact_text(source_chapter.content, 120)),
        "scenes": scenes,
    }


def _normalize_scene(
    chapter_number: int,
    scene_number: int,
    scene: dict[str, Any],
    character_ids: set[str],
    location_ids: set[str],
    default_location_id: str,
) -> dict[str, Any] | None:
    title = str(scene.get("title") or f"Scene {scene_number}").strip()
    synopsis = str(scene.get("synopsis") or scene.get("summary") or title).strip()
    if not title or not synopsis:
        return None
    location_id = str(scene.get("location_id") or "").strip()
    if location_id not in location_ids:
        location_id = default_location_id
    scene_characters = [
        str(item).strip()
        for item in scene.get("characters") or []
        if str(item).strip() in character_ids
    ]
    dialogue = [
        _normalize_dialogue_for_script(line, character_ids)
        for line in scene.get("dialogue") or []
        if isinstance(line, dict)
    ]
    dialogue = [line for line in dialogue if line is not None]
    source_range = scene.get("source_range") if isinstance(scene.get("source_range"), dict) else {}
    return {
        "id": str(scene.get("id") or f"sc_{chapter_number:03d}_{scene_number:03d}"),
        "title": title,
        "location_id": location_id,
        "time": str(scene.get("time") or "未明确时间"),
        "characters": _unique(scene_characters),
        "synopsis": synopsis,
        "source_range": {
            "chapter": chapter_number,
            "start_hint": str(source_range.get("start_hint") or synopsis[:40]),
            "end_hint": str(source_range.get("end_hint") or synopsis[-40:]),
        },
        "stage_directions": _list_of_strings(scene.get("stage_directions")) or [synopsis],
        "dialogue": dialogue,
    }


def _normalize_dialogue_for_script(line: dict[str, Any], character_ids: set[str]) -> dict[str, Any] | None:
    text = str(line.get("line") or "").strip()
    if not text:
        return None
    speaker_id = line.get("speaker_id")
    speaker_id = str(speaker_id).strip() if speaker_id is not None else None
    if speaker_id not in character_ids:
        speaker_id = None
    line_type = str(line.get("line_type") or "dialogue").strip().lower()
    if line_type not in {"dialogue", "monologue", "narration"}:
        line_type = "dialogue"
    return {
        "speaker_id": speaker_id,
        "speaker_name": str(line.get("speaker_name") or ("旁白" if speaker_id is None else speaker_id)),
        "line": text,
        "emotion": str(line.get("emotion") or "neutral"),
        "line_type": line_type,
    }


def _failed_chapter_payload(source_chapter, default_location_id: str, error: str) -> dict[str, Any]:
    message = f"第 {source_chapter.number} 章生成失败：{error}"
    return {
        "id": f"ch_{source_chapter.number:03d}",
        "title": source_chapter.title or f"Chapter {source_chapter.number}",
        "source_chapter_numbers": [source_chapter.number],
        "summary": message,
        "generation_status": "failed",
        "generation_error": error,
        "scenes": [
            {
                "id": f"sc_{source_chapter.number:03d}_failed",
                "title": "生成失败",
                "location_id": default_location_id,
                "time": "未明确时间",
                "characters": [],
                "synopsis": message,
                "source_range": {
                    "chapter": source_chapter.number,
                    "start_hint": _compact_text(source_chapter.content, 40),
                    "end_hint": _compact_text((source_chapter.content or "")[-120:], 40),
                },
                "stage_directions": [message],
                "dialogue": [],
            }
        ],
    }


def _list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _finalize_screenplay_document(
    document: dict[str, Any],
    generation_settings: dict[str, Any],
    analysis: dict[str, Any],
    detail_level: str,
) -> None:
    script = document.get("script") if isinstance(document.get("script"), dict) else {}
    _fix_metadata_consistency(script, generation_settings)
    _improve_character_profiles(script, analysis)
    _normalize_conflict_notes(script, analysis)
    _split_world_settings_from_locations(script)
    _fix_dialogues_and_scene_refs(script, detail_level)
    _recalculate_screenplay_coverage(script, detail_level)


def _fix_metadata_consistency(script: dict[str, Any], generation_settings: dict[str, Any]) -> None:
    metadata = script.get("metadata") if isinstance(script.get("metadata"), dict) else {}
    profile = _template_profile_for_generation_settings(
        {
            **generation_settings,
            "templateId": metadata.get("template_id") or generation_settings.get("templateId"),
            "scriptType": generation_settings.get("scriptType") or metadata.get("script_type"),
        }
    )
    metadata["target_format"] = profile["target_format"]
    metadata["template_id"] = profile["id"]
    metadata["script_type"] = profile["script_type"]
    script["metadata"] = metadata


def _improve_character_profiles(script: dict[str, Any], analysis: dict[str, Any]) -> None:
    source_by_name = {
        str(item.get("name") or "").strip(): item
        for item in (analysis.get("characters") or [])
        if isinstance(item, dict) and str(item.get("name") or "").strip()
    }
    characters = []
    seen_ids = set()
    for index, item in enumerate(script.get("characters") or [], start=1):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        character_id = str(item.get("id") or f"char_{index:03d}").strip()
        if character_id in seen_ids:
            character_id = f"char_{index:03d}"
        seen_ids.add(character_id)
        source = source_by_name.get(name, {})
        role = _infer_character_role(name, item, source)
        description = _character_description(name, role, item, source)
        characters.append(
            {
                **item,
                "id": character_id,
                "name": name,
                "role": role,
                "gender": str(item.get("gender") or source.get("gender") or "unknown"),
                "age": item.get("age") if isinstance(item.get("age"), int) else source.get("age") if isinstance(source.get("age"), int) else None,
                "description": description,
            }
        )
    if characters:
        script["characters"] = characters


def _infer_character_role(name: str, item: dict[str, Any], source: dict[str, Any]) -> str:
    raw_role = str(item.get("role") or source.get("role") or "").strip()
    text = " ".join(
        str(value)
        for value in (
            name,
            raw_role,
            item.get("description"),
            source.get("description"),
            source.get("evidence"),
        )
        if value
    )
    if raw_role and raw_role not in {"角色", "人物", "未知", "unknown"}:
        return raw_role
    role_rules = [
        ("主角", ("许七安", "主角", "穿越")),
        ("堂弟", ("许新年", "堂弟")),
        ("叔父", ("许平志", "叔父", "二叔")),
        ("府尹", ("府尹", "陈府尹", "陈汉光")),
        ("打更人", ("打更人", "宋廷风", "朱广孝")),
        ("司天监术士", ("司天监", "术士", "炼金")),
        ("狱卒", ("狱卒", "牢头", "监牢")),
        ("犯人", ("囚犯", "犯人", "入狱")),
        ("家人", ("婶婶", "姨", "许家")),
    ]
    for role, keywords in role_rules:
        if any(keyword in text for keyword in keywords):
            return role
    return "剧情人物"


def _character_description(name: str, role: str, item: dict[str, Any], source: dict[str, Any]) -> str:
    raw = str(item.get("description") or source.get("description") or source.get("evidence") or "").strip()
    generic_markers = ("分块解析识别的人物", "角色", "人物", "未明确")
    if raw and not any(marker in raw for marker in generic_markers) and len(raw) >= 18:
        return _clip_sentence(raw, 60)
    descriptions = {
        "主角": f"{name}是改编主线核心，卷入案件与牢狱困境，推动调查、脱罪和成长线展开。",
        "堂弟": f"{name}与主角同属许家，是家族关系和案件压力的重要连接人物。",
        "叔父": f"{name}是许家长辈，承担家庭责任，也推动主角面对现实困境。",
        "府尹": f"{name}代表官府审理力量，影响案件走向并制造审讯压力。",
        "打更人": f"{name}关联打更人体系，是案件调查和外部势力介入的重要角色。",
        "司天监术士": f"{name}代表司天监术法线索，为案件提供技术与世界观支撑。",
        "狱卒": f"{name}负责监牢秩序，推动牢狱场景中的信息传递和冲突。",
    }
    return descriptions.get(role, f"{name}在剧情中承担{role}功能，参与主要冲突并推动关键场景发展。")


def _normalize_conflict_notes(script: dict[str, Any], analysis: dict[str, Any]) -> None:
    notes = script.get("adaptation_notes") if isinstance(script.get("adaptation_notes"), dict) else {}
    characters = script.get("characters") if isinstance(script.get("characters"), list) else []
    name_to_id = {str(item.get("name")): str(item.get("id")) for item in characters if isinstance(item, dict) and item.get("id")}
    valid_ids = {str(item.get("id")) for item in characters if isinstance(item, dict) and item.get("id")}
    conflicts = notes.get("conflicts")
    if not conflicts:
        conflicts = analysis.get("conflicts") or []
    normalized = []
    for item in conflicts if isinstance(conflicts, list) else [conflicts]:
        conflict = _coerce_conflict_object(item)
        if not conflict:
            continue
        character_ids = []
        for value in conflict.get("characters") or []:
            marker = str(value).strip()
            if marker in valid_ids:
                character_ids.append(marker)
            elif marker in name_to_id:
                character_ids.append(name_to_id[marker])
        normalized.append(
            {
                "type": str(conflict.get("type") or "剧情冲突").strip() or "剧情冲突",
                "description": _clip_sentence(str(conflict.get("description") or "").strip(), 80),
                "characters": _unique(character_ids),
            }
        )
    notes["conflicts"] = normalized
    script["adaptation_notes"] = notes


def _coerce_conflict_object(item: Any) -> dict[str, Any] | None:
    if isinstance(item, dict):
        description = str(item.get("description") or item.get("summary") or item.get("content") or "").strip()
        if not description and len(item) == 1:
            description = str(next(iter(item.values()))).strip()
        if not description:
            return None
        return {
            "type": item.get("type") or item.get("category") or "剧情冲突",
            "description": description,
            "characters": item.get("characters") or [],
        }
    text = str(item or "").strip()
    if not text:
        return None
    parsed = None
    if text.startswith("{") and text.endswith("}"):
        for parser in (json.loads, ast.literal_eval):
            try:
                parsed = parser(text)
                break
            except Exception:
                parsed = None
    if isinstance(parsed, dict):
        return _coerce_conflict_object(parsed)
    conflict_type = "个人困境" if any(keyword in text for keyword in ("入狱", "流放", "困境", "脱罪")) else "剧情冲突"
    return {"type": conflict_type, "description": text, "characters": []}


def _split_world_settings_from_locations(script: dict[str, Any]) -> None:
    locations = [item for item in script.get("locations") or [] if isinstance(item, dict)]
    if not locations:
        return
    world_settings = [item for item in locations if _is_world_setting_location(item)]
    actual_locations = [item for item in locations if not _is_world_setting_location(item)]
    if not actual_locations:
        actual_locations = [{"id": "loc_001", "name": "未明确地点", "description": "原文未明确具体发生场景。"}]
    actual_ids = {str(item.get("id")) for item in actual_locations if item.get("id")}
    default_location_id = str(actual_locations[0].get("id") or "loc_001")
    for chapter in script.get("chapters") or []:
        if not isinstance(chapter, dict):
            continue
        for scene in chapter.get("scenes") or []:
            if isinstance(scene, dict) and str(scene.get("location_id")) not in actual_ids:
                scene["location_id"] = default_location_id
    script["locations"] = actual_locations
    if world_settings:
        existing_world_settings = [
            item
            for item in script.get("world_settings") or []
            if isinstance(item, dict) and str(item.get("name") or "").strip()
        ]
        script["world_settings"] = _unique_dicts(existing_world_settings + [
            {
                "id": str(item.get("id") or f"world_{index:03d}"),
                "name": str(item.get("name") or "").strip(),
                "description": str(item.get("description") or "世界观背景设定。").strip(),
            }
            for index, item in enumerate(world_settings, start=1)
            if str(item.get("name") or "").strip()
        ], "name")


def _is_world_setting_location(item: dict[str, Any]) -> bool:
    name = str(item.get("name") or "").strip()
    description = str(item.get("description") or "").strip()
    text = f"{name} {description}"
    explicit_world_places = ("万妖国", "南疆十万大山")
    world_keywords = ("世界观", "天下", "诸国", "大陆", "王朝疆域")
    return any(keyword in text for keyword in explicit_world_places + world_keywords)


def _fix_dialogues_and_scene_refs(script: dict[str, Any], detail_level: str) -> None:
    characters = [item for item in script.get("characters") or [] if isinstance(item, dict)]
    char_by_id = {str(item.get("id")): item for item in characters if item.get("id")}
    id_by_name = {str(item.get("name")): str(item.get("id")) for item in characters if item.get("id") and item.get("name")}
    max_dialogues = {"brief": 4, "standard": 6, "detailed": 8}.get(detail_level, 6)
    for chapter in script.get("chapters") or []:
        if not isinstance(chapter, dict):
            continue
        for scene in chapter.get("scenes") or []:
            if not isinstance(scene, dict):
                continue
            stage_directions = _list_of_strings(scene.get("stage_directions"))
            scene_characters = [
                str(value).strip()
                for value in scene.get("characters") or []
                if str(value).strip() in char_by_id
            ]
            normalized_dialogue = []
            for line in scene.get("dialogue") or []:
                if not isinstance(line, dict):
                    continue
                fixed = _fix_dialogue_line(line, char_by_id, id_by_name)
                if fixed is None:
                    narration = str(line.get("line") or "").strip()
                    if narration:
                        stage_directions.append(_clip_sentence(narration, 90))
                    continue
                normalized_dialogue.append(fixed)
                if fixed["speaker_id"]:
                    scene_characters.append(fixed["speaker_id"])
            scene["stage_directions"] = _unique(stage_directions) or [str(scene.get("synopsis") or "场景动作延续。")]
            scene["dialogue"] = _select_key_dialogues(normalized_dialogue, max_dialogues)
            scene["characters"] = _unique(scene_characters)


def _fix_dialogue_line(
    line: dict[str, Any],
    char_by_id: dict[str, dict[str, Any]],
    id_by_name: dict[str, str],
) -> dict[str, Any] | None:
    text = str(line.get("line") or "").strip()
    if not text:
        return None
    line_type = str(line.get("line_type") or "dialogue").strip().lower()
    speaker_id = str(line.get("speaker_id") or "").strip()
    speaker_name = str(line.get("speaker_name") or "").strip()
    if speaker_id not in char_by_id and speaker_name in id_by_name:
        speaker_id = id_by_name[speaker_name]
    if speaker_id not in char_by_id:
        return None
    if line_type == "narration":
        return None
    if line_type not in {"dialogue", "monologue"}:
        line_type = "dialogue"
    return {
        "speaker_id": speaker_id,
        "speaker_name": str(char_by_id[speaker_id].get("name") or speaker_name or speaker_id),
        "line": _clip_sentence(text, 88),
        "emotion": str(line.get("emotion") or "neutral"),
        "line_type": line_type,
    }


def _select_key_dialogues(dialogues: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    selected = []
    seen = set()
    for line in dialogues:
        text = str(line.get("line") or "").strip()
        marker = (line.get("speaker_id"), text)
        if not text or marker in seen:
            continue
        seen.add(marker)
        selected.append(line)
        if len(selected) >= limit:
            break
    return selected


def _recalculate_screenplay_coverage(script: dict[str, Any], detail_level: str) -> None:
    metadata = script.get("metadata") if isinstance(script.get("metadata"), dict) else {}
    coverage = metadata.get("coverage") if isinstance(metadata.get("coverage"), dict) else {}
    chapters = [chapter for chapter in script.get("chapters") or [] if isinstance(chapter, dict)]
    scenes = [
        scene
        for chapter in chapters
        for scene in (chapter.get("scenes") or [])
        if isinstance(scene, dict)
    ]
    coverage["source_chapters"] = metadata.get("total_chapters") or len(chapters)
    coverage["generated_scenes"] = len(scenes)
    coverage["preserved_dialogues"] = sum(
        1
        for scene in scenes
        for line in (scene.get("dialogue") or [])
        if isinstance(line, dict)
        and line.get("speaker_id")
        and str(line.get("line_type") or "dialogue") in {"dialogue", "monologue"}
    )
    coverage["adaptation_mode"] = detail_level
    coverage["omitted_reason"] = OMITTED_REASONS[detail_level]
    metadata["coverage"] = coverage
    script["metadata"] = metadata


def _clip_sentence(text: str, limit: int) -> str:
    compact = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(compact) <= limit:
        return compact
    clipped = compact[:limit].rstrip("，。；、,.!！?？")
    return clipped + "…"


def _screenplay_prompt(
    project: Project,
    analysis: dict[str, Any],
    generation_settings: dict[str, Any],
    detail_level: str,
) -> str:
    template = _template_profile(generation_settings.get("templateId"))
    screenplay_template = _screenplay_json_template(project, generation_settings, detail_level)
    return "\n".join(
        [
            "请基于全局 characters、locations 和章节解析结果生成剧本结构。",
            "后端不会替你识别人名、地点、场景或对白归属，所以你必须在本次输出中保证引用正确。",
            "",
            "生成要求：",
            "1. 顶层必须是 JSON 对象，包含 script 字段；不要输出 YAML、Markdown 或解释。",
            "2. scene title 由你总结，不要直接截断原文。",
            "3. scene.characters 必须来自全局 characters 的 id。",
            "4. scene.location_id 必须来自全局 locations 的 id。",
            "5. dialogue.speaker_id 必须来自全局 characters 的 id，无法确认则为 null，speaker_name 为“旁白”。",
            "6. 尽量使用原文真实对白。",
            "7. 心理描写可以转为 monologue。",
            "8. 旁白叙述可以转为 narration。",
            "9. 不要生成模板化假对白。",
            f"10. detail_level={detail_level}；brief 为概要剧本，standard 为标准剧本，detailed 为详细剧本。",
            "",
            f"模板：{template['name']} target_format={template['target_format']}",
            f"生成设置：{json.dumps(generation_settings, ensure_ascii=False)}",
            "",
            "返回 JSON 必须符合这个结构：",
            json.dumps(screenplay_template, ensure_ascii=False),
            "",
            "全局解析结果：",
            json.dumps(_analysis_for_prompt(analysis), ensure_ascii=False),
            "",
            "原文章节：",
            json.dumps(_chapters_for_prompt(project), ensure_ascii=False),
        ]
    )


def _screenplay_json_template(
    project: Project,
    generation_settings: dict[str, Any] | None = None,
    detail_level: str = "standard",
) -> dict[str, Any]:
    template = _template_profile_for_generation_settings(generation_settings or {})
    return {
        "script": {
            "schema_version": "1.0",
            "metadata": {
                "title": project.title,
                "original_novel": project.title,
                "author": project.author,
                "language": "zh-CN",
                "target_format": template["target_format"],
                "template_id": template["id"],
                "script_type": template["script_type"],
                "adaptation_style": (generation_settings or {}).get("adaptationStyle"),
                "total_chapters": len(project.chapters),
                "adaptation_mode": detail_level,
                "omitted_reason": OMITTED_REASONS[detail_level],
                "coverage": {
                    "source_chapters": len(project.chapters),
                    "generated_scenes": 0,
                    "preserved_dialogues": 0,
                    "adaptation_mode": detail_level,
                    "omitted_reason": OMITTED_REASONS[detail_level],
                },
            },
            "characters": [],
            "locations": [],
            "organizations": [],
            "chapters": [
                {
                    "id": "ch_001",
                    "title": "章节标题",
                    "source_chapter_numbers": [1],
                    "summary": "章节摘要",
                    "scenes": [
                        {
                            "id": "sc_001_001",
                            "title": "场景标题",
                            "location_id": "loc_001",
                            "time": "时间",
                            "characters": ["char_001"],
                            "synopsis": "场景概要",
                            "source_range": {
                                "chapter": 1,
                                "start_hint": "原文起始短句",
                                "end_hint": "原文结束短句",
                            },
                            "stage_directions": ["舞台或镜头调度"],
                            "dialogue": [
                                {
                                    "speaker_id": "char_001",
                                    "speaker_name": "人物名",
                                    "line": "原文对白或改编对白",
                                    "emotion": "neutral",
                                    "line_type": "dialogue",
                                }
                            ],
                        }
                    ],
                }
            ],
            "adaptation_notes": {
                "themes": [],
                "conflicts": [],
                "omissions": [OMITTED_REASONS[detail_level]],
                "template_rules": template["rules"],
            },
        }
    }


def _is_valid_chapter_analysis(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    required_lists = ("characters", "locations", "events", "dialogues")
    if not all(isinstance(data.get(key), list) for key in required_lists):
        return False
    for line in data.get("dialogues", []):
        if not isinstance(line, dict):
            return False
        if line.get("line_type") not in {"dialogue", "monologue", "narration"}:
            return False
    return True


def _is_valid_global_analysis(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    characters = data.get("characters")
    locations = data.get("locations")
    if not isinstance(characters, list) or not isinstance(locations, list):
        return False
    if not characters or not locations:
        return False
    if not all(isinstance(item, dict) and item.get("id") and item.get("name") for item in characters):
        return False
    if not all(isinstance(item, dict) and item.get("id") and item.get("name") for item in locations):
        return False
    character_names = {item["name"] for item in characters}
    location_names = {item["name"] for item in locations}
    return character_names.isdisjoint(location_names)


def _is_valid_project_analysis(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    chapter_analyses = data.get("chapter_analyses")
    if not isinstance(chapter_analyses, list) or not chapter_analyses:
        return False
    for item in chapter_analyses:
        if not isinstance(item, dict) or not _is_valid_chapter_analysis(item.get("analysis")):
            return False
    return _is_valid_global_analysis(data)


def _normalize_project_analysis(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": "ai",
        "chapter_analyses": data.get("chapter_analyses", []),
        "characters": data.get("characters", []),
        "locations": data.get("locations", []),
        "organizations": data.get("organizations", []),
        "alias_map": data.get("alias_map", []),
        "candidate_aliases": data.get("alias_map", []),
        "themes": data.get("themes", []),
        "conflicts": data.get("conflicts", []),
    }


def _local_project_analysis(project: Project) -> dict[str, Any]:
    chapter_analyses = []
    character_names: list[str] = []
    location_names: list[str] = []
    organizations: list[dict[str, Any]] = []

    for chapter in project.chapters:
        analysis = _local_chapter_analysis(chapter.number, chapter.title, chapter.content)
        chapter_analyses.append(
            {
                "chapter_number": chapter.number,
                "source_title": chapter.title,
                "analysis": analysis,
            }
        )
        character_names.extend(item["name"] for item in analysis["characters"])
        location_names.extend(item["name"] for item in analysis["locations"])
        organizations.extend(analysis.get("organizations", []))

    characters = [
        {
            "id": f"char_{index:03d}",
            "name": name,
            "aliases": [],
            "role": "角色",
            "description": "本地快速解析识别的人物。",
        }
        for index, name in enumerate(_unique(character_names) or ["旁白"], start=1)
    ]
    locations = [
        {
            "id": f"loc_{index:03d}",
            "name": name,
            "description": "本地快速解析识别的地点。",
        }
        for index, name in enumerate(_unique(location_names) or ["未明确地点"], start=1)
    ]
    return {
        "source": "local_fallback",
        "chapter_analyses": chapter_analyses,
        "characters": characters,
        "locations": locations,
        "organizations": [
            {
                "id": f"org_{index:03d}",
                "name": item["name"],
                "description": item.get("description") or "本地快速解析识别的组织。",
            }
            for index, item in enumerate(_unique_dicts(organizations, "name"), start=1)
        ],
        "alias_map": [],
        "candidate_aliases": [],
        "themes": ["小说改编", "人物冲突"],
        "conflicts": ["主角目标与外部阻碍之间的冲突"],
    }


def _local_chapter_analysis(chapter_number: int, title: str, content: str) -> dict[str, Any]:
    speakers = _extract_speakers(content)
    fallback_names = _extract_likely_names(content)
    characters = _unique(speakers + fallback_names)[:12]
    locations = _extract_locations(content)[:8]
    dialogues = _extract_dialogues(content)
    summary = _compact_text(content, 90)
    event_characters = characters[:4]
    event_location = locations[0] if locations else "未明确地点"
    return {
        "chapter_title": title,
        "characters": [
            {
                "name": name,
                "aliases": [],
                "role": "角色",
                "description": f"第 {chapter_number} 章出现的人物。",
                "evidence": name,
            }
            for name in characters
        ],
        "locations": [
            {
                "name": location,
                "description": f"第 {chapter_number} 章出现的地点。",
                "evidence": location,
            }
            for location in locations
        ],
        "organizations": [],
        "events": [
            {
                "title": title,
                "summary": summary,
                "characters": event_characters,
                "location": event_location,
                "evidence": _compact_text(content, 40),
            }
        ],
        "dialogues": dialogues,
    }


def _extract_dialogues(text: str) -> list[dict[str, Any]]:
    dialogues = []
    patterns = [
        re.compile(r"(?P<speaker>[\u4e00-\u9fffA-Za-z0-9_]{1,8})(?:说道|说|道|问道|答道|喊道|喝道|低声道|沉声道|笑道|怒道)[:：]?[“\"](?P<line>[^”\"]{1,120})[”\"]"),
        re.compile(r"[“\"](?P<line>[^”\"]{1,120})[”\"](?P<speaker>[\u4e00-\u9fffA-Za-z0-9_]{1,8})(?:说道|说|道|问道|答道|喊道|喝道|低声道|沉声道|笑道|怒道)"),
    ]
    for pattern in patterns:
        for match in pattern.finditer(text):
            speaker = _clean_name(match.group("speaker"))
            line = match.group("line").strip()
            if not speaker or not line:
                continue
            dialogues.append(
                {
                    "speaker": speaker,
                    "line": line,
                    "line_type": "dialogue",
                    "emotion": "neutral",
                    "evidence": line[:40],
                }
            )
    if not dialogues:
        dialogues.append(
            {
                "speaker": None,
                "line": _compact_text(text, 80),
                "line_type": "narration",
                "emotion": "neutral",
                "evidence": _compact_text(text, 40),
            }
        )
    return dialogues[:20]


def _extract_speakers(text: str) -> list[str]:
    names = []
    for pattern in [
        r"([\u4e00-\u9fffA-Za-z0-9_]{1,8})(?:说道|说|道|问道|答道|喊道|喝道|低声道|沉声道|笑道|怒道)",
        r"[“\"][^”\"]{1,120}[”\"]([\u4e00-\u9fffA-Za-z0-9_]{1,8})(?:说道|说|道|问道|答道|喊道|喝道|低声道|沉声道|笑道|怒道)",
    ]:
        names.extend(_clean_name(match) for match in re.findall(pattern, text))
    return [name for name in names if name]


def _extract_likely_names(text: str) -> list[str]:
    candidates = re.findall(r"[\u4e00-\u9fff]{2,4}", text)
    stop_words = {
        "第一章",
        "第二章",
        "第三章",
        "第四章",
        "第五章",
        "第六章",
        "一个",
        "他们",
        "我们",
        "这里",
        "那里",
        "没有",
        "什么",
        "时候",
        "自己",
        "众人",
    }
    names = []
    for item in candidates:
        if item in stop_words or item.startswith("第"):
            continue
        if any(suffix in item for suffix in ("府", "街", "城", "院", "监", "司", "堂", "桥", "河")):
            continue
        names.append(item)
    return names[:12]


def _extract_locations(text: str) -> list[str]:
    locations = []
    for match in re.findall(r"[\u4e00-\u9fff]{2,8}(?:府|街|城|院|监|司|堂|桥|河|客栈|书院|衙门|监牢|皇宫|山|门)", text):
        if not match.startswith("第"):
            locations.append(match)
    return _unique(locations)


def _clean_name(value: str | None) -> str | None:
    if not value:
        return None
    name = re.sub(r"[，。！？、：；“”\"'（）()\s]", "", value)
    name = re.sub(r"^(?:忽然|只见|却见|这时|随后|于是|但是|因为|如果|那个|这个)", "", name)
    if len(name) < 2 or len(name) > 8:
        return None
    if any(word in name for word in ("众人", "声音", "时候", "什么", "这里", "那里")):
        return None
    return name


def _compact_text(text: str, limit: int) -> str:
    compact = re.sub(r"\s+", "", text or "")
    return compact[:limit] if compact else "本章围绕主要人物与事件展开。"


def _unique(values: list[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _unique_dicts(values: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    result = []
    seen = set()
    for value in values:
        marker = value.get(key)
        if marker and marker not in seen:
            seen.add(marker)
            result.append(value)
    return result


def _validate_screenplay_result(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    try:
        document = ScreenplayDocument.model_validate(data)
    except (ValidationError, ValueError) as exc:
        return [f"剧本 Schema 校验失败：{exc}"]

    if not document.script.characters:
        errors.append("characters 不能为空。")
    if not document.script.locations:
        errors.append("locations 不能为空。")

    character_ids = {character.id for character in document.script.characters}
    location_ids = {location.id for location in document.script.locations}
    for chapter in document.script.chapters:
        for scene in chapter.scenes:
            if scene.location_id not in location_ids:
                errors.append(f"scene {scene.id} 的 location_id 不存在。")
            for character_id in scene.characters:
                if character_id not in character_ids:
                    errors.append(f"scene {scene.id} 引用了不存在的人物 {character_id}。")
            for line in scene.dialogue:
                if line.speaker_id is not None and line.speaker_id not in character_ids:
                    errors.append(f"scene {scene.id} 的对白引用了不存在的 speaker_id {line.speaker_id}。")
    return errors


def _project_generation_settings(project: Project) -> dict[str, Any]:
    raw = getattr(project, "generation_settings_json", None)
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _detail_level(settings_data: dict[str, Any]) -> str:
    value = str(settings_data.get("detail_level") or settings_data.get("detailLevel") or "standard")
    return value if value in DETAIL_LEVELS else "standard"


def _template_profile(template_id: str | None) -> dict[str, Any]:
    profiles = {
        "tv-drama": {
            "id": "tv-drama",
            "name": "影视剧剧本模板",
            "target_format": "screenplay",
            "script_type": "影视剧",
            "rules": ["由 AI 完成场景拆分", "由 AI 完成对白归属", "由后端校验引用关系"],
        },
        "short-drama": {
            "id": "short-drama",
            "name": "短剧剧本模板",
            "target_format": "short_drama",
            "script_type": "短剧",
            "rules": ["由 AI 强化冲突和钩子", "由 AI 保留关键对白", "由后端校验引用关系"],
        },
        "stage-play": {
            "id": "stage-play",
            "name": "话剧剧本模板",
            "target_format": "stage_play",
            "script_type": "话剧",
            "rules": ["由 AI 生成舞台调度", "由 AI 处理入场退场", "由后端校验引用关系"],
        },
        "storyboard": {
            "id": "storyboard",
            "name": "分镜剧本模板",
            "target_format": "storyboard",
            "script_type": "分镜剧本",
            "rules": ["由 AI 生成镜头化场景", "由 AI 标注画面重点", "由后端校验引用关系"],
        },
        "audio-drama": {
            "id": "audio-drama",
            "name": "广播剧剧本模板",
            "target_format": "audio_drama",
            "script_type": "广播剧",
            "rules": ["由 AI 强化声音调度", "由 AI 区分旁白和对白", "由后端校验引用关系"],
        },
    }
    return profiles.get(template_id or "tv-drama", profiles["tv-drama"])


def _template_profile_for_generation_settings(generation_settings: dict[str, Any]) -> dict[str, Any]:
    script_type = str(generation_settings.get("scriptType") or "").strip()
    template_id = str(generation_settings.get("templateId") or "").strip()
    if script_type == "短剧":
        template_id = "short-drama"
    return _template_profile(template_id or None)


def _analysis_for_prompt(analysis: dict[str, Any]) -> dict[str, Any]:
    return {
        "characters": analysis.get("characters", []),
        "locations": analysis.get("locations", []),
        "organizations": analysis.get("organizations", []),
        "alias_map": analysis.get("alias_map") or analysis.get("candidate_aliases", []),
        "chapter_analyses": analysis.get("chapter_analyses", []),
        "themes": analysis.get("themes", []),
        "conflicts": analysis.get("conflicts", []),
    }


def _chapters_for_prompt(project: Project) -> list[dict[str, Any]]:
    return [
        {
            "number": chapter.number,
            "title": chapter.title,
            "content_excerpt": _prompt_excerpt(chapter.content, AI_CHAPTER_PROMPT_CHAR_LIMIT),
        }
        for chapter in project.chapters
    ]


def _prompt_excerpt(text: str, limit: int) -> str:
    compact = re.sub(r"\s+", "\n", (text or "").strip())
    if len(compact) <= limit:
        return compact
    half = max(1, limit // 2)
    return f"{compact[:half]}\n...\n{compact[-half:]}"
