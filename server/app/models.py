
from pydantic import BaseModel
from typing import List, Optional

class Repository(BaseModel):
    name: str
    full_name: Optional[str] = ""
    description: Optional[str] = "No description provided."
    html_url: Optional[str] = ""
    clone_url: Optional[str] = ""
    owner: Optional[str] = ""
    stars: Optional[int] = 0
    forks: Optional[int] = 0
    language: Optional[str] = "N/A"
    default_branch: Optional[str] = "main"
    topics: Optional[List[str]] = []

class SearchResponse(BaseModel):
    query_used: str
    sort_by: str
    total_found: int
    results: List[Repository]