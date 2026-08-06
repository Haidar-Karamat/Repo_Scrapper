from pydantic import BaseModel
from typing import Optional, List


class RepoItem(BaseModel):
    name: str
    full_name: str
    owner: str
    description: Optional[str] = "No description provided."
    stars: int
    forks: int
    languages: List[str]
    clone_url: str
    default_branch: str
    topics: List[str]


class SearchResponse(BaseModel):  
    query_used: str
    sort_by: str
    total_found: int
    results: List[RepoItem]