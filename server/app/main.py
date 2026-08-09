from fastapi import FastAPI, Query, HTTPException
from app.models import SearchResponse
from app.parser import parse_query  
from app.github_client import GitHubClient
from app.endpoints import router as scraper_router

app = FastAPI(
    title="Repo Scrapper API",
    description="Production-ready FastAPI backend with Hybrid AI Query Parsing for GitHub extraction",
    version="1.0.0",
)

app.include_router(scraper_router)


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

    query, sort_by = parse_query(prompt)

    client = GitHubClient()
    results = client.search_repositories(query=query, sort=sort_by, limit=limit)

    return SearchResponse(
        query_used=query,
        sort_by=sort_by,
        total_found=len(results),
        results=results
    )