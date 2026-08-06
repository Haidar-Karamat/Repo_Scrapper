from typing import List, Optional
from pydantic import BaseModel, Field


class ScrapeRepoRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = None


class FileItem(BaseModel):
    path: str
    type: str
    size: int


class RepoSummaryResponse(BaseModel):
    owner: str
    repo: str
    description: Optional[str]
    stars: int
    default_branch: str
    language: Optional[str]
    total_files: int
    tree: List[FileItem]


class FileContentResponse(BaseModel):
    owner: str
    repo: str
    path: str
    content: str


class LLMContextRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = None
    file_extensions: Optional[List[str]] = Field(
        default=[".py", ".js", ".ts", ".jsx", ".tsx", ".md", ".json", ".yaml", ".yml", ".go", ".rs"],
        description="Filter by file extensions. Pass empty list to include all extensions."
    )
    max_file_size_kb: int = Field(default=100, ge=1, le=1000, description="Max size per file in KB")
    max_files: int = Field(default=30, ge=1, le=100, description="Max number of files to fetch")


class LLMContextResponse(BaseModel):
    owner: str
    repo: str
    files_scraped: int
    estimated_tokens: int
    formatted_prompt: str