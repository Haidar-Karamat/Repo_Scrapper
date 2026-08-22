import re
from fastapi import APIRouter, HTTPException, Query
from app.scraper import (
    ScrapeRepoRequest,
    RepoSummaryResponse,
    FileContentResponse,
    LLMContextRequest,
    LLMContextResponse,
)
from app.github_service import github_service

router = APIRouter(prefix="/api/v1", tags=["Scraper"])


def parse_github_url(url: str) -> tuple[str, str]:
    pattern = r"github\.com/([^/]+)/([^/]+)"
    match = re.search(pattern, url)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid GitHub URL format.")
    owner, repo = match.group(1), match.group(2)
    repo = repo.replace(".git", "")
    return owner, repo


@router.post("/scrape/summary", response_model=RepoSummaryResponse)
async def scrape_repo_summary(payload: ScrapeRepoRequest):
    owner, repo = parse_github_url(payload.repo_url)
    try:
        meta = await github_service.get_repo_metadata(owner, repo)
        branch = payload.branch or meta["default_branch"]
        tree = await github_service.get_repo_tree(owner, repo, branch=branch)
        
        return RepoSummaryResponse(
            owner=owner,
            repo=repo,
            description=meta["description"],
            stars=meta["stars"],
            default_branch=branch,
            language=meta["language"],
            total_files=len(tree),
            tree=tree,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to scrape repository: {str(e)}")


@router.get("/scrape/file", response_model=FileContentResponse)
async def fetch_single_file(
    owner: str = Query(..., json_schema_extra={"example": "fastapi"}),
    repo: str = Query(..., json_schema_extra={"example": "fastapi"}),
    path: str = Query(..., json_schema_extra={"example": "README.md"}),
    branch: str = Query("main"),
):
    try:
        content = await github_service.get_file_content(owner, repo, path, branch)
        return FileContentResponse(owner=owner, repo=repo, path=path, content=content)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scrape/llm-context", response_model=LLMContextResponse)
async def generate_llm_context(payload: LLMContextRequest):
    """Scrapes files matching extension & size filters and packages them into a single formatted Markdown prompt for LLMs."""
    owner, repo = parse_github_url(payload.repo_url)
    try:
        meta = await github_service.get_repo_metadata(owner, repo)
        branch = payload.branch or meta["default_branch"]
        tree = await github_service.get_repo_tree(owner, repo, branch=branch)

        allowed_exts = tuple(ext.lower() for ext in payload.file_extensions) if payload.file_extensions else None
        max_bytes = payload.max_file_size_kb * 1024

        eligible_paths = []
        for item in tree:
            if item["type"] != "blob":
                continue
            if item["size"] > max_bytes:
                continue
            path = item["path"]
            if allowed_exts and not path.lower().endswith(allowed_exts):
                continue
            eligible_paths.append(path)

        selected_paths = eligible_paths[: payload.max_files]

        if not selected_paths:
            raise HTTPException(status_code=400, detail="No matching code files found for specified extension and size filters.")

        file_contents = await github_service.fetch_files_batch(owner, repo, selected_paths, branch=branch)

        prompt_parts = [
            f"# Repository Context: {owner}/{repo}",
            f"**Description**: {meta.get('description') or 'N/A'}",
            f"**Primary Language**: {meta.get('language') or 'N/A'} | **Stars**: {meta.get('stars', 0)}",
            "\n## File Tree Overview\n```text",
        ]
        for p in selected_paths:
            prompt_parts.append(f"- {p}")
        prompt_parts.append("```\n\n---\n\n## File Contents\n")

        for path, content in file_contents.items():
            ext = path.split(".")[-1] if "." in path else ""
            prompt_parts.append(f"### File: `{path}`\n```{ext}\n{content}\n```\n")

        formatted_prompt = "\n".join(prompt_parts)
        estimated_tokens = len(formatted_prompt) // 4  # Standard char-to-token approximation

        return LLMContextResponse(
            owner=owner,
            repo=repo,
            files_scraped=len(file_contents),
            estimated_tokens=estimated_tokens,
            formatted_prompt=formatted_prompt,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate LLM context: {str(e)}")