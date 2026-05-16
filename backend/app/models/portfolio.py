from pydantic import BaseModel


class GeneratePortfolioRequest(BaseModel):
    jobCategory: str
    projectIds: list[str] = []


class GeneratedPortfolioResponse(BaseModel):
    id: str
    contentType: str
    jobCategory: str
    content: str
    achievements: list[str] = []
    alternatives: list[dict] = []
    sourceProjectIds: list[str] = []
    isSaved: bool = False
    createdAt: str
