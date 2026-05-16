from pydantic import BaseModel
from typing import Optional


class CreateProjectRequest(BaseModel):
    title: str
    startDate: str
    endDate: str
    roles: list[str]
    techStack: list[str] = []


class CreateMeetingRequest(BaseModel):
    title: str
    content: str
    date: str


class CreateTaskRequest(BaseModel):
    description: str
    status: str = "시작전"
    date: str


class CreateTroubleshootingRequest(BaseModel):
    problem: str
    solution: str
    date: str


class CreateRetrospectiveRequest(BaseModel):
    content: str
    date: str


class ProjectResponse(BaseModel):
    id: str
    title: str
    status: str
    period: dict
    roles: list[str]
    techStack: list[str]
    completeness: int
    aiInferredRoles: list[dict] = []
    aiExtractedTech: list[str] = []
    recordCounts: dict = {}
    createdAt: str
    updatedAt: str
