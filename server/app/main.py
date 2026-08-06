from fastapi import FastAPI, Query, HTTPException
from .models import SearchResponse
from .parser import QueryParser
from .github_client import GitHubClient

app = FastAPI(title="Repo Scrapper API", version="1.0.0")

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "repo-scrapper-backend"}

@app.get("/api/v1/search", response_model=SearchResponse)
def search(
    prompt: str = Query(..., description="Natural language search prompt"),
    limit: int = Query(default=10, ge=1, le=50)
):
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    # 1. Parse natural prompt into github query & sort preference
    query, sort_by = QueryParser.parse(prompt)

    # 2. Fetch repos from GitHub API
    client = GitHubClient()
    results = client.search_repositories(query=query, sort=sort_by, limit=limit)

    # 3. Return structured response
    return SearchResponse(
        query_used=query,
        sort_by=sort_by,
        total_found=len(results),
        results=results
    )
