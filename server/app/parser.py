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
            groq_client = Groq(api_key=api_key, timeout=2.5)
    return groq_client


def rule_based_cleaner(prompt: str) -> tuple[str, str]:
    """0ms offline keyword parser fallback for English & Hinglish prompts."""
    stop_words = {
        "top", "best", "give", "me", "show", "find", "a", "an", "the", "with", "for", "in", 
        "list", "high", "stars", "repos", "projects", "repositories", "code", "repo", "provide",
        "mujhe", "ke", "ka", "ki", "ko", "se", "sabse", "dikhao", "karo", "wale", "wala", "wali", 
        "chahiye", "badhiya", "ache", "achha", "dhund", "do", "hai", "kuch", "par", "mein", "batao", "lao"
    }
    tokens = re.findall(r'\b[\w\+\-]+\b', prompt.lower())
    clean_words = []
    
    for t in tokens:
        if t.isdigit() or t in stop_words:
            continue
        if t == "ml":
            clean_words.append("machine-learning")
        elif t == "ai":
            clean_words.append("artificial-intelligence")
        elif t in ("py", "python3"):
            clean_words.append("python")
        else:
            clean_words.append(t)

    clean_query = " ".join(clean_words).strip() or prompt.strip()
    return clean_query, "stars"


@lru_cache(maxsize=512)
def parse_query(prompt: str) -> tuple[str, str]:
    clean_prompt = prompt.strip()

    # Fast path for very short simple queries without conversational fillers
    words = clean_prompt.split()
    if len(words) <= 2 and not any(w in clean_prompt.lower() for w in ["mujhe", "best", "top", "chahiye", "provide", "karo", "dikhao"]):
        return clean_prompt, "stars"

    client = get_groq_client()
    if not client:
        return rule_based_cleaner(clean_prompt)

    system_prompt = (
    "You are a global multilingual AI assistant for GitHub repository search. "
    "The user can ask prompts in ANY language in the world (e.g. Spanish, French, Japanese, German, Chinese, Russian, Hindi, Hinglish, English). "
    "Translate the user's intent to English technical keywords and appropriate GitHub query filters. "
    "Strictly remove conversational verbs/fillers (e.g. 'por favor', 'karo', 'dikhao', 'provide', 'give', 'show', 'list', 'trouver', 'zeigen'). "
    "Output ONLY in the format: <english_query_keywords>|<sort_by (stars/forks/updated)>. "
    "Example: machine-learning language:python|stars"
)

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": clean_prompt}
            ],
            max_tokens=25,
            temperature=0.0
        )
        output = response.choices[0].message.content.strip()
        if "|" in output:
            parts = output.split("|")
            query = parts[0].strip()
            sort_by = parts[1].strip().lower()
            return query, sort_by
        return output, "stars"
    except Exception:
        return rule_based_cleaner(clean_prompt)