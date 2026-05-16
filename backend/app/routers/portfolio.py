from fastapi import APIRouter
from datetime import datetime, timezone
import uuid

from app.ai.bedrock_client import bedrock_client
from app.ai.prompts import portfolio_gen
from app.models.portfolio import GeneratePortfolioRequest, GeneratedPortfolioResponse
from app.routers.projects import PROJECTS_DB, RECORDS_DB
from app.routers.ai import _format_records

router = APIRouter()

# In-memory store
PORTFOLIO_DB: list[dict] = []


@router.get("/generated")
async def list_generated(content_type: str = None, sort: str = "createdAt"):
    results = PORTFOLIO_DB
    if content_type:
        results = [r for r in results if r["contentType"] == content_type]
    results = sorted(results, key=lambda r: r["createdAt"], reverse=True)
    return {"results": results}


@router.post("/generate")
async def generate_portfolio(request: GeneratePortfolioRequest):
    """AI 포트폴리오 생성 - Bedrock Claude 호출"""
    # Gather project data
    project_ids = request.projectIds or list(PROJECTS_DB.keys())
    projects_data = []
    all_records = []

    for pid in project_ids:
        project = PROJECTS_DB.get(pid)
        if project:
            projects_data.append(project)
            all_records.extend(RECORDS_DB.get(pid, []))

    if not projects_data:
        return {"error": "NO_PROJECTS", "message": "프로젝트를 찾을 수 없습니다."}

    # Use first project for now (MVP)
    project = projects_data[0]
    records = RECORDS_DB.get(project["id"], [])
    records_text = _format_records(records)

    try:
        prompt = portfolio_gen.PROMPT_TEMPLATE.format(
            title=project["title"],
            start_date=project["period"]["start"],
            end_date=project["period"]["end"],
            roles=", ".join(project["roles"]),
            tech_stack=", ".join(project["techStack"]),
            records_summary=records_text,
            inferred_roles=str(project.get("aiInferredRoles", project["roles"])),
            extracted_tech=", ".join(project.get("aiExtractedTech", project["techStack"])),
            job_category=request.jobCategory,
        )

        result = await bedrock_client.invoke_json(prompt, portfolio_gen.SYSTEM)

        now = datetime.now(timezone.utc).isoformat()
        generated_items = []

        # Portfolio
        if "portfolio" in result:
            item = _create_portfolio_item(
                content_type="포트폴리오",
                job_category=request.jobCategory,
                content=result["portfolio"]["content"],
                achievements=result["portfolio"].get("achievements", []),
                alternatives=result.get("alternatives", []),
                source_ids=project_ids,
                created_at=now,
            )
            generated_items.append(item)

        # Self-introduction
        if "self_introduction" in result:
            item = _create_portfolio_item(
                content_type="자기소개서",
                job_category=request.jobCategory,
                content=result["self_introduction"]["content"],
                achievements=result["self_introduction"].get("achievements", []),
                alternatives=[],
                source_ids=project_ids,
                created_at=now,
            )
            generated_items.append(item)

        # LinkedIn
        if "linkedin" in result:
            item = _create_portfolio_item(
                content_type="링크드인 소개글",
                job_category=request.jobCategory,
                content=result["linkedin"]["content"][:300],  # 300 char limit
                achievements=result["linkedin"].get("achievements", []),
                alternatives=[],
                source_ids=project_ids,
                created_at=now,
            )
            generated_items.append(item)

        return {"results": generated_items, "count": len(generated_items)}

    except Exception as e:
        # Fallback demo response if Bedrock not configured
        now = datetime.now(timezone.utc).isoformat()
        fallback_items = [
            _create_portfolio_item(
                content_type="포트폴리오",
                job_category=request.jobCategory,
                content=f"[{request.jobCategory}] {project['title']} 프로젝트에서 {', '.join(project['roles'])} 역할을 수행했습니다. {', '.join(project['techStack'])}을 활용하여 프로젝트를 진행했습니다.",
                achievements=[f"{project['title']} 프로젝트 수행"],
                alternatives=[],
                source_ids=project_ids,
                created_at=now,
            ),
        ]
        return {"results": fallback_items, "count": 1, "_fallback": True, "_error": str(e)}


@router.post("/{portfolio_id}/save")
async def save_portfolio(portfolio_id: str):
    for item in PORTFOLIO_DB:
        if item["id"] == portfolio_id:
            item["isSaved"] = True
            return {"success": True}
    return {"success": False}


def _create_portfolio_item(
    content_type: str, job_category: str, content: str,
    achievements: list, alternatives: list, source_ids: list, created_at: str
) -> dict:
    item = {
        "id": f"port_{uuid.uuid4().hex[:8]}",
        "contentType": content_type,
        "jobCategory": job_category,
        "content": content,
        "achievements": achievements,
        "alternatives": alternatives,
        "sourceProjectIds": source_ids,
        "isSaved": False,
        "createdAt": created_at,
    }
    PORTFOLIO_DB.append(item)
    return item
