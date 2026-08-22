import os
import re
import json
import logging
import requests
from itertools import cycle
from typing import Tuple, Dict, Set, List, Optional
from dotenv import load_dotenv, find_dotenv

# Load .env file
load_dotenv(find_dotenv(usecwd=True), override=True)

logger = logging.getLogger("uvicorn.error")


class APIKeyRotator:
    """Manages API Keys with Round-Robin Rotation and Failover."""

    def __init__(self, env_prefix: str = "GROQ_API_KEY"):
        self.env_prefix = env_prefix
        self.keys: List[str] = []
        self._cycle = None
        self._reload_keys()

    def _reload_keys(self):
        load_dotenv(find_dotenv(usecwd=True), override=True)
        found_keys = []

        # Scan numbered keys (GROQ_API_KEY_1 to GROQ_API_KEY_9)
        for i in range(1, 10):
            key = os.getenv(f"{self.env_prefix}_{i}")
            if key and key.strip() and not key.startswith("my_"):
                found_keys.append(key.strip())

        # Scan CSV keys (GROQ_API_KEYS)
        csv_keys = os.getenv(f"{self.env_prefix}S")
        if csv_keys:
            for k in csv_keys.split(","):
                clean_k = k.strip()
                if clean_k and not clean_k.startswith("my_") and clean_k not in found_keys:
                    found_keys.append(clean_k)

        # Single key fallback (GROQ_API_KEY)
        single_key = os.getenv(self.env_prefix)
        if single_key and single_key.strip() and not single_key.startswith("my_") and single_key.strip() not in found_keys:
            found_keys.append(single_key.strip())

        if found_keys != self.keys:
            self.keys = found_keys
            self._cycle = cycle(self.keys) if self.keys else None

    def get_ordered_keys(self) -> List[str]:
        if not self.keys:
            self._reload_keys()

        if not self.keys or not self._cycle:
            return []

        primary_key = next(self._cycle)
        return [primary_key] + [k for k in self.keys if k != primary_key]


# Initialize Rotator
grok_rotator = APIKeyRotator("GROQ_API_KEY")


class DynamicModelManager:
    """Auto-discovers and caches the fastest, most stable model available on the account."""

    _cached_model: Optional[str] = None

    # Priority list ranked by speed, reliability, and structured query generation
    PREFERRED_MODELS: List[str] = [
        "qwen/qwen3.6-27b",
        "groq/compound-mini",
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b",
        "allam-2-7b",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
    ]

    # Models that must never be selected for chat/completion
    EXCLUDE_KEYWORDS: Set[str] = {
        "whisper",
        "prompt-guard",
        "safeguard",
        "orpheus",
        "embedding",
        "vision",
    }

    @classmethod
    def get_best_model(cls, api_key: str) -> str:
        if cls._cached_model:
            return cls._cached_model

        try:
            url = "https://api.groq.com/openai/v1/models"
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()

            available_models = {
                item["id"] for item in response.json().get("data", [])
            }

            # 1. Match against preferred ordered models
            for preferred in cls.PREFERRED_MODELS:
                if preferred in available_models:
                    cls._cached_model = preferred
                    print(f"🎯 [Model Auto-Select] Picked preferred model: '{preferred}'")
                    return cls._cached_model

            # 2. Dynamic fallback: filter out audio/guardrail models
            valid_chat_models = [
                m for m in available_models
                if not any(ex in m.lower() for ex in cls.EXCLUDE_KEYWORDS)
            ]

            if valid_chat_models:
                cls._cached_model = valid_chat_models[0]
                print(f"🎯 [Model Auto-Select] Fallback model selected: '{cls._cached_model}'")
                return cls._cached_model

        except Exception as e:
            print(f"⚠️ [Model Auto-Select Warning] Could not fetch models dynamically: {e}")

        # Static fallback if network call fails
        return "qwen/qwen3.6-27b"


class RuleBasedQueryParser:
    """Offline/Instant regex fallback engine."""

    LANG_GROUPS: Dict[Tuple[str, ...], str] = {
        ("python", "py", "fastapi", "django", "flask", "pytorch", "tensorflow"): "python",
        ("javascript", "js", "react", "vue", "angular", "node", "express", "nextjs"): "javascript",
        ("typescript", "ts", "nest", "next"): "typescript",
        ("java", "spring", "springboot", "maven"): "java",
        ("go", "golang", "gin", "fiber"): "go",
        ("cpp", "c++", "c"): "c++",
        ("csharp", "c#", "dotnet", "aspnet"): "c#",
        ("rust", "rs", "actix"): "rust",
    }

    LANG_MAP: Dict[str, str] = {
        keyword: lang
        for keywords, lang in LANG_GROUPS.items()
        for keyword in keywords
    }

    SORT_MAP: Dict[str, str] = {
        "latest": "updated", "recent": "updated", "new": "updated",
        "best": "stars", "popular": "stars", "top": "stars",
    }

    STOPWORDS: Set[str] = {
        "find", "top", "the", "a", "an", "show", "me", "need", "want",
        "get", "for", "with", "project", "repo", "repository", "code",
        "looking", "search", "template", "boilerplate", "batao", "chahiye",
        "prompt", "current", "prompt-top", "prompt-repo", "of", "in", "on", "about",
        "best", "list", "latest", "recent", "repos", "repositories"
    }

    @classmethod
    def parse(cls, prompt: str) -> Tuple[str, str]:
        tokens = re.findall(r'\b[\w\+\-]+\b', prompt.lower())
        detected_lang = None
        sort_by = "stars"
        filtered_keywords = []

        for token in tokens:
            if token.isdigit():
                continue

            if not detected_lang and token in cls.LANG_MAP:
                detected_lang = cls.LANG_MAP[token]
                if token not in ("python", "javascript", "js", "ts", "java", "go"):
                    filtered_keywords.append(token)
                continue

            if token in cls.SORT_MAP:
                sort_by = cls.SORT_MAP[token]
                continue

            if token not in cls.STOPWORDS:
                filtered_keywords.append(token)

        query = " ".join(filtered_keywords).strip()
        if detected_lang:
            query = f"{query} language:{detected_lang}".strip() if query else f"language:{detected_lang}"

        return query or prompt, sort_by


class LLMQueryParser:
    @staticmethod
    def parse_with_key(prompt: str, api_key: str) -> Tuple[str, str]:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Auto-detect optimal model
        active_model = DynamicModelManager.get_best_model(api_key)

        system_instruction = (
            "You are an expert GitHub Query Optimizer. "
            "Convert user natural language input into a structured GitHub Search API query object. "
            "Output ONLY a raw JSON object with keys:\n"
            '- "query": Clean, concise search keywords (e.g. "claude harness", "system design")\n'
            '- "sort": Exactly one of "stars", "forks", or "updated"\n'
            "Return valid raw JSON only, without markdown fences or extra explanations."
        )

        payload = {
            "model": active_model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"User Prompt: {prompt}"}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1
        }

        response = requests.post(url, headers=headers, json=payload, timeout=8)
        response.raise_for_status()

        raw = response.json()
        raw_text = raw["choices"][0]["message"]["content"].strip()

        # Regex fallback for clean extraction
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            raw_text = json_match.group(0)

        parsed_json = json.loads(raw_text)
        return parsed_json.get("query", prompt), parsed_json.get("sort", "stars")


def parse_query(prompt: str) -> Tuple[str, str]:
    keys_to_try = grok_rotator.get_ordered_keys()

    if keys_to_try:
        for idx, key in enumerate(keys_to_try, start=1):
            try:
                query, sort_by = LLMQueryParser.parse_with_key(prompt, key)
                print(f"🤖 [Groq Key #{idx}] Transformed '{prompt}' -> Query: '{query}', Sort: '{sort_by}'")
                return query, sort_by
            except Exception as e:
                print(f"⚠️ [Groq Key #{idx} Failed] Reason: {e}")

    query, sort_by = RuleBasedQueryParser.parse(prompt)
    print(f"⚙️ [Rule Parser Fallback] Transformed '{prompt}' -> Query: '{query}', Sort: '{sort_by}'")
    return query, sort_by


def validate_keys():
    keys = grok_rotator.get_ordered_keys()
    if not keys:
        print("❌ No API keys found in environment.")
        return

    # Auto-resolve best model using the first available key
    selected_model = DynamicModelManager.get_best_model(keys[0])
    print(f"🚀 Using Model: '{selected_model}'\n")

    for idx, key in enumerate(keys, start=1):
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": selected_model,
                "messages": [
                    {"role": "user", "content": "Ping"}
                ]
            }
            response = requests.post(url, headers=headers, json=payload, timeout=8)
            response.raise_for_status()
            print(f"✅ [Key #{idx}] Active and Working! (Status: {response.status_code})")
        except requests.exceptions.HTTPError as http_err:
            print(f"❌ [Key #{idx}] HTTP Error: {http_err.response.status_code} - {http_err.response.text}")
        except Exception as e:
            print(f"❌ [Key #{idx}] Error: {e}")


if __name__ == "__main__":
    validate_keys()
    print("\n--- Test Query Run ---")
    q, s = parse_query("find top fast api repos for machine learning")
    print(f"Final Output -> Query: {q} | Sort: {s}")