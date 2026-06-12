"""Pydantic request/response schemas for auth, projects, and issues."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.database import settings
from app.models import IssuePriority, IssueStatus


def _not_blank(value: str, field_name: str = "Field") -> str:
    if not value or not value.strip():
        raise ValueError(f"{field_name} must not be blank")
    return value.strip()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        return _not_blank(v, "Name")

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < settings.PASSWORD_MIN_LENGTH:
            raise ValueError(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

class ProjectCreate(BaseModel):
    name: str
    description: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        return _not_blank(v, "Project name")


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return _not_blank(v, "Project name")


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    is_archived: bool
    created_at: datetime
    owner: UserResponse


class ProjectListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    is_archived: bool
    created_at: datetime
    owner_id: int
    issue_count: int = 0


# ---------------------------------------------------------------------------
# Issues
# ---------------------------------------------------------------------------

class IssueCreate(BaseModel):
    title: str
    description: str | None = None
    priority: IssuePriority = IssuePriority.MEDIUM
    status: IssueStatus = IssueStatus.TODO
    project_id: int
    assignee_id: int | None = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        return _not_blank(v, "Issue title")


class IssueUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: IssuePriority | None = None
    status: IssueStatus | None = None
    assignee_id: int | None = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return _not_blank(v, "Issue title")


class IssueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    priority: IssuePriority
    status: IssueStatus
    created_at: datetime
    updated_at: datetime
    project_id: int
    assignee: UserResponse | None
