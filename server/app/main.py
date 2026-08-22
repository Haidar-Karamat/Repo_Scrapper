from fastapi import FastAPI, Query, HTTPException
from cachetools import TTLCache
from app.models import SearchResponse
from app.parser import parse_query  
from app.github_client import GitHubClient

app = FastAPI(
    title="Repo Scrapper API",
    description="High-performance GitHub search parser",
    version="1.3.2"
)

# Cache 500 queries for 15 minutes
search_cache = TTLCache(maxsize=500, ttl=900)
client = GitHubClient()

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "repo-scrapper-backend"}

@app.get("/api/v1/search", response_model=SearchResponse)
def search(
    prompt: str = Query(..., description="Natural language search prompt"),
    limit: int = Query(default=10, ge=1, le=50)
):
    clean_prompt = prompt.strip()
    if not clean_prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    cache_key = f"{clean_prompt.lower()}:{limit}"
    if cache_key in search_cache:
        return search_cache[cache_key]

    query, sort_by = parse_query(clean_prompt)
    results = client.search_repositories(query=query, sort=sort_by, limit=limit)

    response = SearchResponse(
        query_used=query,
        sort_by=sort_by,
        total_found=len(results),
        results=results
    )
    
    search_cache[cache_key] = response
    return response