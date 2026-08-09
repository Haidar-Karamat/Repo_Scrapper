import os
import re
import json
import logging
import requests
from itertools import cycle
from typing import Tuple, Dict, Set, List
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(usecwd=True), override=True)

logger = logging.getLogger("uvicorn.error")


class APIKeyRotator:
    """Manages API Keys with Round-Robin Rotation and Failover."""

    def __init__(self, env_prefix: str = "GROK_API_KEY"):
        self.env_prefix = env_prefix
        self.keys: List[str] = []
        self._cycle = None
        self._reload_keys()

    def _reload_keys(self):
        # Force re-scan of environment variables
        load_dotenv(find_dotenv(usecwd=True), override=True)
        found_keys = []

        # 1. Numbered keys: GROK_API_KEY_1, GROK_API_KEY_2, etc.
        for i in range(1, 10):
            key = os.getenv(f"{self.env_prefix}_{i}")
            if key and key.strip() and not key.startswith("my_"):
                found_keys.append(key.strip())

        # 2. Comma-separated keys: GROK_API_KEYS
        csv_keys = os.getenv(f"{self.env_prefix}S")
        if csv_keys:
            for k in csv_keys.split(","):
                clean_k = k.strip()
                if clean_k and not clean_k.startswith("my_") and clean_k not in found_keys:
                    found_keys.append(clean_k)

        # 3. Single key fallback: GROK_API_KEY or XAI_API_KEY
        single_key = os.getenv(self.env_prefix) or os.getenv("XAI_API_KEY")
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


grok_rotator = APIKeyRotator("GROK_API_KEY")


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
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        system_instruction = (
            "You are an expert GitHub Query Optimizer. "
            "Convert user natural language input into a structured GitHub Search API query object. "
            "Output ONLY a raw JSON object with these keys:\n"
            '- "query": Clean, concise search keywords (e.g. "claude harness", "system design")\n'
            '- "sort": Exactly one of "stars", "forks", or "updated"\n'
            "Return ONLY valid raw JSON, no markdown syntax or extra text."
        )

        payload = {
            "model": "grok-2-latest",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"User Prompt: {prompt}"}
            ],
            "temperature": 0.1
        }

        response = requests.post(url, headers=headers, json=payload, timeout=6)
        response.raise_for_status()

        raw_text = response.json()["choices"][0]["message"]["content"].strip()
        
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
                print(f"🤖 [Grok AI Key #{idx}] Transformed '{prompt}' -> Query: '{query}', Sort: '{sort_by}'")
                return query, sort_by
            except Exception as e:
                print(f"⚠️ [Grok AI Key #{idx} Failed] Reason: {e}")

    # Fallback Execution
    query, sort_by = RuleBasedQueryParser.parse(prompt)
    print(f"⚙️ [Rule Parser Fallback] Transformed '{prompt}' -> Query: '{query}', Sort: '{sort_by}'")
    return query, sort_by