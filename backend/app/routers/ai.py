from fastapi import APIRouter
from datetime import datetime, timezone
import uuid

from app.ai.bedrock_client import bedrock_client
from app.ai.prompts import role_inference, gap_detection
from app.routers.projects import PROJECTS_DB, RECORDS_DB

router = APIRouter()

# In-memory recommendations store
RECOMMENDATIONS_DB: list[dict] = []


@router.get("/recommendations")
async def get_recommendations(limit: int = 5):
    sorted_recs = sorted(RECOMMENDATIONS_DB, key=lambda r: r["createdAt"], reverse=True)
    return {"recommendations": sorted_recs[:limit]}


@router.put("/recommendations/{rec_id}/read")
async def mark_read(rec_id: str):
    for rec in RECOMMENDATIONS_DB:
        if rec["id"] == rec_id:
            rec["isRead"] = True
            return {"success": True}
    return {"success": False}


@router.get("/project/{project_id}/insights")
async def get_project_insights(project_id: str):
    """AI 분석: 역할 추론 + 기술 추출 + 요약 + 제안"""
    project = PROJECTS_DB.get(project_id)
    if not project:
        return {"error": "NOT_FOUND"}

    records = RECORDS_DB.get(project_id, [])
    if not records:
        return {
            "inferredRoles": [],
            "extractedTech": [],
            "summary": "기록이 없어 분석할 수 없습니다. 프로젝트 활동을 기록해주세요.",
            "suggestions": ["첫 번째 회의록을 추가해보세요."],
        }

    # Format records for prompt
    records_text = _format_records(records)

    try:
        prompt = role_inference.PROMPT_TEMPLATE.format(
            title=project["title"],
            start_date=project["period"]["start"],
            end_date=project["period"]["end"],
            roles=", ".join(project["roles"]),
            records=records_text,
        )

        result = await bedrock_client.invoke_json(prompt, role_inference.SYSTEM)

        # Update project with AI results
        project["aiInferredRoles"] = result.get("inferred_roles", [])
        project["aiExtractedTech"] = result.get("extracted_tech", [])

        return {
            "inferredRoles": result.get("inferred_roles", []),
            "extractedTech": result.get("extracted_tech", []),
            "summary": result.get("summary", ""),
            "suggestions": _generate_suggestions(project, records),
        }
    except Exception as e:
        # Fallback for demo if Bedrock is not configured
        return {
            "inferredRoles": [{"role": project["roles"][0] if project["roles"] else "개발", "level": "주도", "evidence": ["활동 기록 분석"], "confidence": 0.8}],
            "extractedTech": project["techStack"][:5],
            "summary": f"'{project['title']}' 프로젝트에서 {', '.join(project['roles'])} 역할을 수행 중입니다.",
            "suggestions": _generate_suggestions(project, records),
            "_fallback": True,
            "_error": str(e),
        }


@router.post("/analyze/{project_id}")
async def trigger_analysis(project_id: str):
    """수동 분석 트리거 - 기록 부족 탐지 + 추천 생성"""
    project = PROJECTS_DB.get(project_id)
    if not project:
        return {"error": "NOT_FOUND"}

    records = RECORDS_DB.get(project_id, [])
    suggestions = _generate_suggestions(project, records)

    # Create recommendations
    now = datetime.now(timezone.utc).isoformat()
    for suggestion in suggestions:
        rec = {
            "id": f"rec_{uuid.uuid4().hex[:8]}",
            "type": suggestion.get("type", "action_suggestion"),
            "message": suggestion.get("message", ""),
            "projectId": project_id,
            "projectTitle": project["title"],
            "isRead": False,
            "createdAt": now,
        }
        RECOMMENDATIONS_DB.append(rec)

    return {"analysisId": f"analysis_{uuid.uuid4().hex[:8]}", "suggestionsCount": len(suggestions)}


def _format_records(records: list) -> str:
    lines = []
    for r in records:
        if r["type"] == "meeting":
            lines.append(f"[회의] {r.get('date', '')} - {r.get('title', '')}: {r.get('content', '')}")
        elif r["type"] == "task":
            lines.append(f"[업무] {r.get('date', '')} - {r.get('description', '')} (상태: {r.get('status', '')})")
        elif r["type"] == "troubleshooting":
            lines.append(f"[트러블슈팅] {r.get('date', '')} - 문제: {r.get('problem', '')} / 해결: {r.get('solution', '')}")
        elif r["type"] == "retrospective":
            lines.append(f"[회고] {r.get('date', '')} - {r.get('content', '')}")
    return "\n".join(lines)


def _generate_suggestions(project: dict, records: list) -> list:
    suggestions = []
    counts = project.get("recordCounts", {})

    if counts.get("meetings", 0) == 0:
        suggestions.append({"type": "record_gap", "message": f"'{project['title']}'에 회의록이 없습니다. 팀 회의 내용을 기록해보세요."})
    if counts.get("tasks", 0) == 0:
        suggestions.append({"type": "record_gap", "message": f"'{project['title']}'에 담당 업무 기록이 없습니다. 본인의 업무를 기록해보세요."})
    if counts.get("troubleshooting", 0) == 0:
        suggestions.append({"type": "record_gap", "message": "트러블슈팅 기록이 없습니다. 문제 해결 경험은 포트폴리오에서 높은 가치를 가집니다."})
    if counts.get("retrospectives", 0) == 0:
        suggestions.append({"type": "record_gap", "message": "회고가 없습니다. 프로젝트를 돌아보며 배운 점을 기록하세요."})

    if project.get("completeness", 0) >= 50 and not suggestions:
        suggestions.append({"type": "action_suggestion", "message": "성과 수치를 추가하면 포트폴리오 품질이 높아집니다. (예: 처리 건수, 개선율)"})

    return suggestions
