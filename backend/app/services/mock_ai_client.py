import json
import re

from openai import OpenAI

from app.core.config import settings
from app.services.character_filter import (
    canonicalize_character_list,
    filter_scene_character_names,
    normalize_speaker,
)


def extract_characters_json(text: str) -> str:
    ai_result = _extract_characters_with_ai(text)
    if ai_result is not None:
        return ai_result
    raise RuntimeError("AI character extraction requires LLM_API_KEY, LLM_BASE_URL and LLM_MODEL.")


def _extract_characters_with_ai(text: str) -> str | None:
    if not (settings.llm_api_key and settings.llm_base_url and settings.llm_model):
        return None

    prompt = "\n".join(
        [
            "\u4f60\u662f\u5c0f\u8bf4\u7ed3\u6784\u5316\u89e3\u6790\u5668\u3002",
            "",
            "\u4efb\u52a1\uff1a\u53ea\u62bd\u53d6\u771f\u5b9e\u4eba\u7269\uff0c\u4e0d\u8981\u62bd\u53d6\u52a8\u4f5c\u3001\u4ee3\u8bcd\u3001\u8bed\u6c14\u8bcd\u3001\u53e5\u5b50\u7247\u6bb5\u3002",
            "",
            "\u9519\u8bef\u793a\u4f8b\uff1a",
            "\u53ef\u4ee5\uff1a\u4e0d\u662f\u4eba\u7269",
            "\u4f60\u8bf4\uff1a\u4e0d\u662f\u4eba\u7269",
            "\u4ed6\u8bf4\uff1a\u4e0d\u662f\u4eba\u7269",
            "\u9648\u5e9c\u5c39\u70b9\uff1a\u9519\u8bef\uff0c\u5e94\u4e3a\u9648\u5e9c\u5c39",
            "\u8bb8\u4e03\u5b89\u611f\u89c9\uff1a\u9519\u8bef\uff0c\u5e94\u4e3a\u8bb8\u4e03\u5b89",
            "",
            "\u4eba\u7269\u540d\u5224\u65ad\u6807\u51c6\uff1a",
            "1. \u5fc5\u987b\u662f\u5c0f\u8bf4\u4e2d\u7684\u771f\u5b9e\u4eba\u7269\u3001\u79f0\u8c13\u4eba\u7269\u6216\u7ec4\u7ec7\u804c\u52a1\u4eba\u7269\u3002",
            "2. \u4e0d\u80fd\u662f\u52a8\u4f5c\u77ed\u8bed\u3002",
            "3. \u4e0d\u80fd\u662f\u4ee3\u8bcd\u3002",
            "4. \u4e0d\u80fd\u662f\u666e\u901a\u8bcd\u3002",
            "5. \u5982\u679c\u540c\u4e00\u4e2a\u4eba\u7269\u6709\u591a\u4e2a\u79f0\u547c\uff0c\u8bf7\u5408\u5e76\u4e3a aliases\u3002",
            "6. alias \u6620\u5c04\uff1a\u9648\u5e9c\u5c39=\u9648\u6c49\u5149\uff1b\u9ec4\u88d9\u5c11\u5973=\u91c7\u8587=\u891a\u91c7\u8587\uff1b\u4e8c\u53d4=\u8bb8\u5e73\u5fd7\uff1b\u8bb8\u5bb6\u4e8c\u90ce=\u8bb8\u65b0\u5e74\u3002",
            "",
            "\u8bf7\u4e25\u683c\u8f93\u51fa JSON\uff1a",
            "{\"characters\":[{\"canonicalName\":\"\u8bb8\u4e03\u5b89\",\"aliases\":[\"\u8bb8\u4e03\u5b89\",\"\u5b81\u5bb4\"],\"role\":\"\u4e3b\u89d2\",\"evidence\":\"\u539f\u6587\u4e2d\u80fd\u8bc1\u660e\u4ed6\u662f\u4eba\u7269\u7684\u4e00\u53e5\u8bdd\",\"confidence\":0.95}]}",
            "",
            "\u4e0d\u8981\u8f93\u51fa\u89e3\u91ca\u3002",
            "\u4e0d\u8981\u521b\u9020\u539f\u6587\u4e2d\u4e0d\u5b58\u5728\u7684\u4eba\u7269\u3002",
            "\u4e0d\u8981\u628a\u201c\u53ef\u4ee5\u201d\u201c\u4f60\u8bf4\u201d\u201c\u4ed6\u8bf4\u201d\u201c\u9648\u5e9c\u5c39\u70b9\u201d\u8bc6\u522b\u6210\u4eba\u7269\u3002",
            "",
            "\u539f\u6587\uff1a",
            text[:12000],
        ]
    )

    try:
        client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            timeout=settings.llm_timeout_seconds,
        )
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "\u4f60\u662f\u5c0f\u8bf4\u4eba\u7269\u8bc6\u522b\u52a9\u624b\uff0c\u5fc5\u987b\u53ea\u8f93\u51fa\u5408\u6cd5 JSON\uff0c\u4e0d\u8981 Markdown\u3002",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        content = response.choices[0].message.content
        parsed = json.loads(content or "{}")
    except Exception:
        return None

    if not isinstance(parsed, dict) or not isinstance(parsed.get("characters"), list):
        return None
    return json.dumps(parsed, ensure_ascii=False)


def extract_scenes_json(chapters: list[dict], characters: list[dict]) -> str:
    known_names = [item.get("name") for item in characters if item.get("name")]
    scenes = []
    scene_index = 1
    for chapter in chapters:
        chunks = _scene_chunks(chapter["content"])
        for chunk in chunks:
            raw_names = [name for name in known_names if name in chunk]
            names_in_scene = filter_scene_character_names(raw_names, characters)
            scenes.append(
                {
                    "id": f"scene_{scene_index:03d}",
                    "chapter": chapter["title"],
                    "title": _guess_scene_title(chunk, scene_index),
                    "location": _guess_location(chunk),
                    "time": _guess_time(chunk),
                    "atmosphere": _guess_atmosphere(chunk),
                    "characters": names_in_scene,
                    "summary": _summarize(chunk),
                    "source_text": chunk,
                }
            )
            scene_index += 1
    return json.dumps({"scenes": scenes}, ensure_ascii=False)


def generate_scene_content_json(scene: dict, characters: list[dict]) -> str:
    names = [item.get("name") for item in characters if item.get("name")]
    sentences = _sentences(scene.get("source_text", ""))
    content = []
    for sentence in sentences[:10]:
        quote = _extract_quote(sentence)
        if quote:
            speaker = normalize_speaker(_guess_speaker(sentence, names), characters)
            content.append(
                {
                    "type": "dialogue",
                    "speaker": speaker or "\u65c1\u767d",
                    "emotion": _guess_emotion(sentence),
                    "text": quote,
                    "source_text": sentence,
                    "confidence": 0.82 if speaker else 0.55,
                    "need_review": speaker is None,
                }
            )
            continue

        actor = next((name for name in names if name in sentence), None)
        content.append(
            {
                "type": "action" if actor else "narration",
                "actor": actor,
                "text": sentence,
                "source_text": sentence,
                "confidence": 0.78 if actor else 0.7,
                "need_review": False if actor else True,
            }
        )

    if not content and scene.get("source_text"):
        content.append(
            {
                "type": "narration",
                "text": scene["source_text"][:180],
                "source_text": scene["source_text"][:180],
                "confidence": 0.6,
                "need_review": True,
            }
        )
    return json.dumps({"content": content}, ensure_ascii=False)


def _name_candidates(text: str) -> list[str]:
    patterns = [
        r"[\u4e00-\u9fff]{2,7}(?=(?:\u8bf4|\u9053|\u95ee|\u7b54|\u558a|\u53eb|\u7b11|\u770b|\u671b|\u77a5|\u5410|\u70b9|\u611f\u89c9|[\uff1a:]))",
        r"(?:\u540d\u53eb|\u59d3\u540d|\u5524\u4f5c|叫做)\s*([\u4e00-\u9fff]{2,5})",
        r"[\u4e00-\u9fff]{2,5}(?:\u5e9c\u5c39|\u5c11\u5973|\u4e8c\u53d4|\u4e8c\u90ce|\u5927\u4eba|\u59d1\u5a18|\u516c\u5b50)",
    ]
    names: list[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            candidate = match.group(1) if match.groups() else match.group(0)
            if candidate not in names:
                names.append(candidate)
    return names


def _scene_chunks(text: str) -> list[str]:
    paragraphs = [item.strip() for item in re.split(r"\n\s*\n", text) if item.strip()]
    if not paragraphs:
        paragraphs = [text.strip()] if text.strip() else []

    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(current) + len(paragraph) > 900 and current:
            chunks.append(current.strip())
            current = paragraph
        else:
            current = f"{current}\n{paragraph}".strip()
    if current:
        chunks.append(current)
    return chunks[:12]


def _guess_scene_title(text: str, index: int) -> str:
    first_sentence = _sentences(text)
    if first_sentence:
        return first_sentence[0][:16]
    return f"\u573a\u666f {index:03d}"


def _guess_location(text: str) -> str:
    for marker in ["\u5df7\u53e3", "\u623f\u95f4", "\u5ba2\u5385", "\u8857\u4e0a", "\u95e8\u53e3", "\u8f66\u7ad9", "\u5b66\u6821", "\u533b\u9662", "\u529e\u516c\u5ba4", "\u96e8\u91cc"]:
        if marker in text:
            return marker
    return "\u672a\u660e\u786e\u5730\u70b9"


def _guess_time(text: str) -> str:
    for marker in ["\u6e05\u6668", "\u65e9\u6668", "\u4e0a\u5348", "\u4e2d\u5348", "\u4e0b\u5348", "\u508d\u665a", "\u591c\u665a", "\u6df1\u591c", "\u96e8\u591c"]:
        if marker in text:
            return marker
    return "\u672a\u660e\u786e\u65f6\u95f4"


def _guess_atmosphere(text: str) -> str:
    if any(word in text for word in ["\u7d27\u5f20", "\u6c89\u9ed8", "\u51b7", "\u96e8", "\u9ed1"]):
        return "\u7d27\u5f20"
    if any(word in text for word in ["\u7b11", "\u6e29\u67d4", "\u6696"]):
        return "\u6e29\u548c"
    return "\u5e73\u9759"


def _summarize(text: str) -> str:
    sentences = _sentences(text)
    return (sentences[0] if sentences else text[:80]).strip()


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[\u3002\uff01\uff1f!?])\s*|\n+", text)
    return [part.strip() for part in parts if part.strip()]


def _extract_quote(sentence: str) -> str | None:
    match = re.search(r"[\u201c\u2018\"](.+?)[\u201d\u2019\"]", sentence)
    if match:
        return match.group(1).strip()
    colon_match = re.search(r"[\uff1a:]\s*(.+)$", sentence)
    return colon_match.group(1).strip() if colon_match else None


def _guess_speaker(sentence: str, names: list[str]) -> str | None:
    before_quote = re.split(r"[\u201c\u2018\"\uff1a:]", sentence, maxsplit=1)[0]
    return next((name for name in names if name in before_quote), None)


def _guess_emotion(sentence: str) -> str:
    if any(word in sentence for word in ["\u60ca", "\u6123", "\u6014"]):
        return "\u60ca\u8bb6"
    if any(word in sentence for word in ["\u7b11", "\u6e29\u67d4"]):
        return "\u6e29\u548c"
    if any(word in sentence for word in ["\u558a", "\u6012", "\u51b7"]):
        return "\u7d27\u5f20"
    return "\u5e73\u9759"
