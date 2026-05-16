from fastapi import APIRouter
from datetime import datetime, timezone
import uuid

router = APIRouter()

# In-memory store
TEAM_POSTS_DB: list[dict] = [
    {
        "id": "team_001",
        "authorId": "user_001",
        "authorName": "김민수",
        "description": "AI 기반 헬스케어 앱 개발 프로젝트. 프론트엔드와 디자이너를 모집합니다.",
        "requiredRoles": ["프론트엔드", "UI/UX 디자이너"],
        "techStack": ["React Native", "TypeScript", "Firebase"],
        "projectStatus": "진행중",
        "recruitStatus": "모집중",
        "applicantCount": 3,
        "maxPositions": 5,
        "createdAt": "2024-06-10T00:00:00Z",
    },
]


@router.get("/posts")
async def list_posts(page: int = 1, limit: int = 20, role: str = None, tech: str = None, search: str = None):
    posts = TEAM_POSTS_DB

    if role:
        posts = [p for p in posts if role in p["requiredRoles"]]
    if tech:
        posts = [p for p in posts if tech in p["techStack"]]
    if search:
        q = search.lower()
        posts = [p for p in posts if q in p["description"].lower() or
                 any(q in r.lower() for r in p["requiredRoles"]) or
                 any(q in t.lower() for t in p["techStack"])]

    posts = sorted(posts, key=lambda p: p["createdAt"], reverse=True)
    start = (page - 1) * limit
    return {"posts": posts[start:start + limit], "total": len(posts), "page": page}


@router.post("/posts")
async def create_post(description: str, requiredRoles: list[str], techStack: list[str], maxPositions: int = 5):
    post = {
        "id": f"team_{uuid.uuid4().hex[:8]}",
        "authorId": "user_demo_001",
        "authorName": "데모 사용자",
        "description": description,
        "requiredRoles": requiredRoles,
        "techStack": techStack,
        "projectStatus": "진행중",
        "recruitStatus": "모집중",
        "applicantCount": 0,
        "maxPositions": maxPositions,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    TEAM_POSTS_DB.append(post)
    return post


@router.post("/posts/{post_id}/apply")
async def apply_to_post(post_id: str):
    for post in TEAM_POSTS_DB:
        if post["id"] == post_id:
            if post["applicantCount"] >= post["maxPositions"]:
                return {"error": "FULL", "message": "모집이 마감되었습니다."}
            post["applicantCount"] += 1
            return {"success": True, "message": "지원이 완료되었습니다."}
    return {"error": "NOT_FOUND"}


@router.post("/posts/{post_id}/bookmark")
async def bookmark_post(post_id: str):
    return {"success": True, "message": "관심 목록에 추가되었습니다."}
