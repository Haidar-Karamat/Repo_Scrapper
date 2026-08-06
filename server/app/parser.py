from typing import Tuple, Dict, Set
import re

class QueryParser():

    LANG_GROUPS: Dict[Tuple[str, ...], str] = {
        ("python", "py", "fastapi", "django", "flask", "pytorch", "tensorflow"): "python",
        ("javascript", "js", "react", "vue", "angular", "node", "express", "nextjs"): "javascript",
        ("typescript", "ts", "nest", "next"): "typescript",
        ("java", "spring", "springboot", "maven"): "java",
        ("go", "golang", "gin", "fiber"): "go",
        ("cpp", "c++", "c"): "c++",
        ("csharp", "c#", "dotnet", "aspnet"): "c#",
        ("rust", "rs", "actix"): "rust",
        ("ruby", "rails", "rb"): "ruby",
        ("php", "laravel", "symfony"): "php",
    }

    LANG_MAP: Dict[str, str] = {
        keyword: lang 
        for keywords, lang in LANG_GROUPS.items() 
        for keyword in keywords
    }

    SORT_MAP: Dict[str, str] = {
        "latest": "updated",
        "recent": "updated",
        "new": "updated",
        "best": "stars",
        "popular": "stars",
        "top": "stars",
    }

    STOPWORDS: Set[str] = {
        "find", "top", "the", "a", "an", "show", "me", "need", "want",
        "get", "for", "with", "project", "repo", "repository", "code",
        "looking", "search", "template", "boilerplate", "batao", "chahiye"
    }

    @classmethod
    def parse(cls, prompt: str) -> Tuple[str, str]:
        """
        Parses raw prompt string into a clean GitHub search query and sort parameter.
        Example: "find top fastapi boilerplate" -> ("boilerplate language:python", "stars")
        """
        # Tokenize lowercase words
        tokens = re.findall(r'\b[\w\+\-]+\b', prompt.lower())
        
        detected_lang = None
        sort_by = "stars"  # Default sorting
        filtered_keywords = []

        for token in tokens:
            # 1. Detect framework/language
            if not detected_lang and token in cls.LANG_MAP:
                detected_lang = cls.LANG_MAP[token]
                # If the token itself is a framework (e.g. fastapi), keep it as a keyword too
                if token not in ("python", "javascript", "js", "ts", "java", "go"):
                    filtered_keywords.append(token)
                continue

            # 2. Detect sort order
            if token in cls.SORT_MAP:
                sort_by = cls.SORT_MAP[token]
                continue

            # 3. Filter out noise words
            if token not in cls.STOPWORDS:
                filtered_keywords.append(token)

        # Build final search query string
        query = " ".join(filtered_keywords)
        if detected_lang:
            query += f" language:{detected_lang}"

        return query.strip(), sort_by