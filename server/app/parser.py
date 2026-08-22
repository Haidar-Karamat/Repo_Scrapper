import os
import re
from functools import lru_cache
from groq import Groq

groq_client = None

def get_groq_client():
    global groq_client
    if groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if api_key and not api_key.startswith("your_"):
            groq_client = Groq(api_key=api_key, timeout=4.0)
    return groq_client


UNIVERSAL_SYSTEM_PROMPT = """You are a deterministic search-intent compiler for developer repositories.

Input: User query in ANY human language, dialect, or mixed vernacular.
Output Contract: <english_technical_keywords>|<sort_by>

OPERATIONAL RULES:
1. SEMANTIC TRANSLATION: Translate core technical concepts into standard English developer terminology (e.g., framework names, paradigms, infrastructure components).
2. NOISE PRUNING: Discard all grammatical padding, greetings, conversational verbs, subjective adjectives (e.g., 'best', 'top', 'awesome'), and politeness markers regardless of the source language.
3. ENTITY ISOLATION: Keep only actionable technical entities (programming languages, libraries, platforms, design patterns).
4. SORT RESOLUTION: Infer target sorting criteria strictly from intent:
   - Popularity / Reputation -> 'stars' (Default)
   - Reusability / Template / Forks -> 'forks'
   - Recency / Active maintenance -> 'updated'
5. OUTPUT CONSTRAINTS: Return ONLY the formatted string without explanations, Markdown formatting, or quotes."""


@lru_cache(maxsize=1024)
def parse_query(prompt: str) -> tuple[str, str]:
    clean_prompt = prompt.strip()
    if not clean_prompt:
        return "", "stars"

    client = get_groq_client()
    if not client:
        # Fallback if AI service is completely unavailable
        fallback_query = re.sub(r'[^\w\s\-\.]', '', clean_prompt)
        return fallback_query, "stars"

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": UNIVERSAL_SYSTEM_PROMPT},
                {"role": "user", "content": clean_prompt}
            ],
            max_tokens=30,
            temperature=0.0
        )
        
        raw_output = response.choices[0].message.content.strip()
        
        # Clean any accidental wrapping characters
        raw_output = raw_output.replace("`", "").replace('"', '').replace("'", "")
        
        if "|" in raw_output:
            parts = raw_output.split("|")
            query = parts[0].strip()
            sort_by = parts[1].strip().lower()
            if sort_by not in ("stars", "forks", "updated"):
                sort_by = "stars"
            return query or clean_prompt, sort_by
            
        return raw_output, "stars"
        
    except Exception:
        fallback_query = re.sub(r'[^\w\s\-\.]', '', clean_prompt)
        return fallback_query, "stars"