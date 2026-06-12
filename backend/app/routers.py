from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db, logger
from app.models import Issue, IssuePriority, IssueStatus, Project, User
from app.schemas import (
    IssueCreate,
    IssueResponse,
    IssueUpdate,
    LoginRequest,
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.security import create_access_token, get_current_user, hash_password, verify_password

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "Email is already registered"},
        )

    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info("User registered: %s (id=%s)", user.email, user.id)
    return user


@auth_router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        logger.info("Failed login attempt for email: %s", payload.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid email or password"},
        )

    token = create_access_token(subject=str(user.id))
    logger.info("User logged in: %s (id=%s)", user.email, user.id)
    return TokenResponse(access_token=token)


@auth_router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
   
    logger.info("User logged out: %s (id=%s)", current_user.email, current_user.id)
    return {"message": "Logged out successfully"}


@auth_router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@auth_router.get("/users", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List all users — used by the frontend to populate assignee dropdowns."""
    return db.query(User).order_by(User.name).all()


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

projects_router = APIRouter(prefix="/projects", tags=["projects"])


def _get_owned_project_or_404(project_id: int, db: Session, current_user: User) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "Project not found"})
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "You do not have access to this project"},
        )
    return project


@projects_router.get("", response_model=list[ProjectListResponse])
def list_projects(
    include_archived: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Project).filter(Project.owner_id == current_user.id)
    if not include_archived:
        query = query.filter(Project.is_archived.is_(False))

    projects = query.order_by(Project.created_at.desc()).all()

    results = []
    for project in projects:
        issue_count = db.query(func.count(Issue.id)).filter(Issue.project_id == project.id).scalar()
        results.append(
            ProjectListResponse(
                id=project.id,
                name=project.name,
                description=project.description,
                created_at=project.created_at,
                is_archived=project.is_archived,
                owner_id=project.owner_id,
                issue_count=issue_count or 0,
            )
        )
    return results


@projects_router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = (
        db.query(Project)
        .filter(Project.owner_id == current_user.id, Project.name == payload.name)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "Project name already exists"},
        )

    project = Project(name=payload.name, description=payload.description, owner_id=current_user.id)
    db.add(project)
    db.commit()
    db.refresh(project)

    logger.info("Project created: %s (id=%s) by user_id=%s", project.name, project.id, current_user.id)
    return project


@projects_router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _get_owned_project_or_404(project_id, db, current_user)


@projects_router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_owned_project_or_404(project_id, db, current_user)

    if payload.name is not None and payload.name != project.name:
        existing = (
            db.query(Project)
            .filter(
                Project.owner_id == current_user.id,
                Project.name == payload.name,
                Project.id != project.id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "Project name already exists"},
            )
        project.name = payload.name

    if payload.description is not None:
        project.description = payload.description

    db.commit()
    db.refresh(project)
    logger.info("Project updated: %s (id=%s)", project.name, project.id)
    return project


@projects_router.post("/{project_id}/archive", response_model=ProjectResponse)
def archive_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = _get_owned_project_or_404(project_id, db, current_user)
    project.is_archived = True
    db.commit()
    db.refresh(project)
    logger.info("Project archived: %s (id=%s)", project.name, project.id)
    return project


@projects_router.post("/{project_id}/unarchive", response_model=ProjectResponse)
def unarchive_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = _get_owned_project_or_404(project_id, db, current_user)
    project.is_archived = False
    db.commit()
    db.refresh(project)
    logger.info("Project unarchived: %s (id=%s)", project.name, project.id)
    return project


# ---------------------------------------------------------------------------
# Issues
# ---------------------------------------------------------------------------

issues_router = APIRouter(prefix="/issues", tags=["issues"])


def _get_accessible_issue_or_404(issue_id: int, db: Session, current_user: User) -> Issue:
    issue = db.get(Issue, issue_id)
    if issue is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "Issue not found"})
    if issue.project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "You do not have access to this issue"},
        )
    return issue


@issues_router.get("", response_model=list[IssueResponse])
def list_issues(
    project_id: int | None = None,
    search: str | None = Query(default=None, description="Search by issue title"),
    status_filter: IssueStatus | None = Query(default=None, alias="status"),
    priority: IssuePriority | None = None,
    assignee_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Issue).join(Project).filter(Project.owner_id == current_user.id)

    if project_id is not None:
        query = query.filter(Issue.project_id == project_id)
    if search:
        query = query.filter(Issue.title.ilike(f"%{search}%"))
    if status_filter is not None:
        query = query.filter(Issue.status == status_filter)
    if priority is not None:
        query = query.filter(Issue.priority == priority)
    if assignee_id is not None:
        query = query.filter(Issue.assignee_id == assignee_id)

    return query.order_by(Issue.created_at.desc()).all()


@issues_router.post("", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
def create_issue(payload: IssueCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _get_owned_project_or_404(payload.project_id, db, current_user)

    if payload.assignee_id is not None and db.get(User, payload.assignee_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Assignee does not exist"},
        )

    issue = Issue(
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        status=payload.status,
        project_id=payload.project_id,
        assignee_id=payload.assignee_id,
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)

    logger.info("Issue created: '%s' (id=%s) in project_id=%s", issue.title, issue.id, issue.project_id)
    return issue


@issues_router.get("/{issue_id}", response_model=IssueResponse)
def get_issue(issue_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _get_accessible_issue_or_404(issue_id, db, current_user)


@issues_router.patch("/{issue_id}", response_model=IssueResponse)
def update_issue(
    issue_id: int,
    payload: IssueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    issue = _get_accessible_issue_or_404(issue_id, db, current_user)

    if payload.assignee_id is not None and db.get(User, payload.assignee_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Assignee does not exist"},
        )

    update_data = payload.model_dump(exclude_unset=True)
    old_status = issue.status

    for field, value in update_data.items():
        setattr(issue, field, value)

    db.commit()
    db.refresh(issue)

    if "status" in update_data and update_data["status"] != old_status:
        logger.info("Issue status changed: '%s' (id=%s) %s -> %s", issue.title, issue.id, old_status, issue.status)
    else:
        logger.info("Issue updated: '%s' (id=%s)", issue.title, issue.id)

    return issue


@issues_router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_issue(issue_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    issue = _get_accessible_issue_or_404(issue_id, db, current_user)
    title, iid = issue.title, issue.id
    db.delete(issue)
    db.commit()
    logger.info("Issue deleted: '%s' (id=%s)", title, iid)
    return None


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@dashboard_router.get("/stats")
def get_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_projects = (
        db.query(func.count(Project.id))
        .filter(Project.owner_id == current_user.id, Project.is_archived.is_(False))
        .scalar()
    ) or 0

    total_issues = (
        db.query(func.count(Issue.id)).join(Project).filter(Project.owner_id == current_user.id).scalar()
    ) or 0

    open_issues = (
        db.query(func.count(Issue.id))
        .join(Project)
        .filter(Project.owner_id == current_user.id, Issue.status != IssueStatus.DONE)
        .scalar()
    ) or 0

    completed_issues = (
        db.query(func.count(Issue.id))
        .join(Project)
        .filter(Project.owner_id == current_user.id, Issue.status == IssueStatus.DONE)
        .scalar()
    ) or 0

    return {
        "total_projects": total_projects,
        "total_issues": total_issues,
        "open_issues": open_issues,
        "completed_issues": completed_issues,
    }
