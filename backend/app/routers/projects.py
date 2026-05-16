from fastapi import APIRouter
from datetime import datetime, timezone
import uuid

from app.models.project import (
    CreateProjectRequest, CreateMeetingRequest, CreateTaskRequest,
    CreateTroubleshootingRequest, CreateRetrospectiveRequest, ProjectResponse,
)

router = APIRouter()

# In-memory store for hackathon demo
PROJECTS_DB: dict[str, dict] = {}
RECORDS_DB: dict[str, list] = {}

# Pre-seed demo data
_demo_project_id = "proj_001"
PROJECTS_DB[_demo_project_id] = {
    "id": _demo_project_id,
    "title": "노인식품 개발 캡스톤디자인 경진대회 우수상",
    "status": "진행중",
    "period": {"start": "2024-03-01", "end": "2024-06-30"},
    "roles": ["팀장", "기획", "데이터 분석"],
    "techStack": ["Python", "Pandas", "Figma"],
    "completeness": 65,
    "aiInferredRoles": [],
    "aiExtractedTech": [],
    "recordCounts": {"meetings": 2, "tasks": 3, "troubleshooting": 1, "retrospectives": 1, "attachments": 0},
    "createdAt": "2024-03-01T00:00:00Z",
    "updatedAt": "2024-06-15T00:00:00Z",
}
RECORDS_DB[_demo_project_id] = [
    {"id": "rec_1", "type": "meeting", "title": "1차 기획 회의", "content": "프로젝트 방향성 논의 및 역할 분담", "date": "2024-03-05"},
    {"id": "rec_2", "type": "meeting", "title": "데이터 분석 결과 공유", "content": "크롤링한 식품 리뷰 데이터 분석 결과 발표", "date": "2024-04-10"},
    {"id": "rec_3", "type": "task", "description": "노인식품 시장 데이터 크롤링 및 전처리", "status": "완료", "date": "2024-03-15"},
    {"id": "rec_4", "type": "task", "description": "프로토타입 UI 설계 (Figma)", "status": "진행중", "date": "2024-05-01"},
    {"id": "rec_5", "type": "troubleshooting", "problem": "크롤링 데이터에 중복 리뷰 다수 포함", "solution": "TF-IDF 기반 유사도 측정으로 중복 제거, 15% 데이터 정제", "date": "2024-04-05"},
    {"id": "rec_6", "type": "retrospective", "content": "데이터 분석 단계에서 초기 가설 설정의 중요성을 깨달았다.", "date": "2024-05-15"},
]


@router.get("")
async def list_projects(status: str = None, sort: str = "updatedAt", search: str = None):
    projects = list(PROJECTS_DB.values())

    if status and status != "all":
        projects = [p for p in projects if p["status"] == status]

    if search:
        q = search.lower()
        projects = [p for p in projects if
                    q in p["title"].lower() or
                    any(q in r.lower() for r in p["roles"]) or
                    any(q in t.lower() for t in p["techStack"])]

    projects.sort(key=lambda p: p.get("updatedAt", ""), reverse=True)
    return {"projects": projects, "total": len(projects)}


@router.post("")
async def create_project(request: CreateProjectRequest):
    project_id = f"proj_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()

    project = {
        "id": project_id,
        "title": request.title,
        "status": "진행중",
        "period": {"start": request.startDate, "end": request.endDate},
        "roles": request.roles,
        "techStack": request.techStack,
        "completeness": 0,
        "aiInferredRoles": [],
        "aiExtractedTech": [],
        "recordCounts": {"meetings": 0, "tasks": 0, "troubleshooting": 0, "retrospectives": 0, "attachments": 0},
        "createdAt": now,
        "updatedAt": now,
    }

    PROJECTS_DB[project_id] = project
    RECORDS_DB[project_id] = []
    return project


@router.get("/{project_id}")
async def get_project(project_id: str):
    project = PROJECTS_DB.get(project_id)
    if not project:
        return {"error": "NOT_FOUND", "message": "프로젝트를 찾을 수 없습니다."}
    records = RECORDS_DB.get(project_id, [])
    return {"project": project, "records": records}


@router.post("/{project_id}/meetings")
async def add_meeting(project_id: str, request: CreateMeetingRequest):
    record = {
        "id": f"rec_{uuid.uuid4().hex[:8]}",
        "type": "meeting",
        "title": request.title,
        "content": request.content,
        "date": request.date,
    }
    RECORDS_DB.setdefault(project_id, []).append(record)
    _update_record_counts(project_id)
    return record


@router.post("/{project_id}/tasks")
async def add_task(project_id: str, request: CreateTaskRequest):
    record = {
        "id": f"rec_{uuid.uuid4().hex[:8]}",
        "type": "task",
        "description": request.description,
        "status": request.status,
        "date": request.date,
    }
    RECORDS_DB.setdefault(project_id, []).append(record)
    _update_record_counts(project_id)
    return record


@router.post("/{project_id}/troubleshooting")
async def add_troubleshooting(project_id: str, request: CreateTroubleshootingRequest):
    record = {
        "id": f"rec_{uuid.uuid4().hex[:8]}",
        "type": "troubleshooting",
        "problem": request.problem,
        "solution": request.solution,
        "date": request.date,
    }
    RECORDS_DB.setdefault(project_id, []).append(record)
    _update_record_counts(project_id)
    return record


@router.post("/{project_id}/retrospective")
async def add_retrospective(project_id: str, request: CreateRetrospectiveRequest):
    record = {
        "id": f"rec_{uuid.uuid4().hex[:8]}",
        "type": "retrospective",
        "content": request.content,
        "date": request.date,
    }
    RECORDS_DB.setdefault(project_id, []).append(record)
    _update_record_counts(project_id)
    return record


def _update_record_counts(project_id: str):
    records = RECORDS_DB.get(project_id, [])
    project = PROJECTS_DB.get(project_id)
    if not project:
        return

    counts = {"meetings": 0, "tasks": 0, "troubleshooting": 0, "retrospectives": 0, "attachments": 0}
    type_map = {"meeting": "meetings", "task": "tasks", "troubleshooting": "troubleshooting", "retrospective": "retrospectives", "attachment": "attachments"}

    for r in records:
        key = type_map.get(r["type"])
        if key:
            counts[key] += 1

    project["recordCounts"] = counts

    # Calculate completeness (each type with at least 1 record = 20%)
    filled = sum(1 for v in counts.values() if v > 0)
    project["completeness"] = min(100, filled * 20)
    project["updatedAt"] = datetime.now(timezone.utc).isoformat()
