from fastapi import APIRouter, HTTPException, Response
from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
import uuid

from app.config import settings
from app.models.user import LoginRequest, RegisterRequest, AuthResponse, UserResponse

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory store for hackathon demo (replace with DynamoDB in production)
USERS_DB: dict[str, dict] = {}
# Pre-seed a demo user
USERS_DB["demo@university.ac.kr"] = {
    "id": "user_demo_001",
    "email": "demo@university.ac.kr",
    "password_hash": pwd_context.hash("demo1234"),
    "university": "서울대학교",
    "provider": "email",
    "createdAt": "2024-01-01T00:00:00Z",
}


def create_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


@router.post("/login")
async def login(request: LoginRequest, response: Response):
    user = USERS_DB.get(request.email)
    if not user or not pwd_context.verify(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail={
            "error": "AUTH_FAILED",
            "message": "이메일 또는 비밀번호가 올바르지 않습니다."
        })

    token = create_token(user["id"])
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=settings.JWT_EXPIRE_HOURS * 3600,
    )

    return AuthResponse(
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            university=user["university"],
            provider=user["provider"],
            createdAt=user["createdAt"],
        ),
        token=token,
    )


@router.post("/register")
async def register(request: RegisterRequest):
    if request.password != request.passwordConfirm:
        raise HTTPException(status_code=422, detail={
            "error": "VALIDATION_ERROR",
            "message": "비밀번호가 일치하지 않습니다.",
            "details": {"passwordConfirm": "비밀번호가 일치하지 않습니다."}
        })

    if request.email in USERS_DB:
        raise HTTPException(status_code=409, detail={
            "error": "DUPLICATE_EMAIL",
            "message": "이미 등록된 이메일입니다."
        })

    user_id = f"user_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()

    USERS_DB[request.email] = {
        "id": user_id,
        "email": request.email,
        "password_hash": pwd_context.hash(request.password),
        "university": request.university,
        "provider": "email",
        "createdAt": now,
    }

    return {"message": "회원가입이 완료되었습니다.", "userId": user_id}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("auth_token")
    return {"message": "로그아웃되었습니다."}


@router.get("/me")
async def get_me():
    # Simplified for demo - in production, extract from JWT cookie
    demo_user = USERS_DB.get("demo@university.ac.kr")
    if demo_user:
        return UserResponse(
            id=demo_user["id"],
            email=demo_user["email"],
            university=demo_user["university"],
            provider=demo_user["provider"],
            createdAt=demo_user["createdAt"],
        )
    raise HTTPException(status_code=401, detail={"message": "인증이 필요합니다."})
