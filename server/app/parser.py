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
    """0ms offline keyword parser fallback."""
    stop_words = {
        "top", "best", "give", "me", "show", "find", "a", "an", "the", "with", "for", "in", 
        "list", "high", "stars", "repos", "projects", "repositories", "code", "repo",
        "mujhe", "ke", "ka", "ki", "ko", "se", "sabse", "dikhao", "karo", "wale", "wala", 
        "chahiye", "badhiya", "ache", "achha", "dhund", "do", "hai", "kuch", "par", "mein"
    }
    tokens = re.findall(r'\b[\w\+\-]+\b', prompt.lower())
    clean_words = [t for t in tokens if not t.isdigit() and t not in stop_words]
    clean_query = " ".join(clean_words).strip() or prompt.strip()
    return clean_query, "stars"

@lru_cache(maxsize=512)
def parse_query(prompt: str) -> tuple[str, str]:
    clean_prompt = prompt.strip()
    
    words = clean_prompt.split()
    if len(words) <= 2 and not any(w in clean_prompt.lower() for w in ["mujhe", "best", "top", "chahiye"]):
        return clean_prompt, "stars"

    client = get_groq_client()
    if not client:
        return rule_based_cleaner(clean_prompt)

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "Extract GitHub search query and sort. Output format: <query>|<stars/forks/updated>. No extra text."
                },
                {"role": "user", "content": clean_prompt}
            ],
            max_tokens=25,
            temperature=0.0
        )
        output = response.choices[0].message.content.strip()
        if "|" in output:
            parts = output.split("|")
            return parts[0].strip(), parts[1].strip().lower()
        return output, "stars"
    except Exception:
        return rule_based_cleaner(clean_prompt)