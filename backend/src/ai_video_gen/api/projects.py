"""プロジェクトCRUD API"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status

from ai_video_gen.models import Project, ProjectCreate, ProjectState, ProjectUpdate
from ai_video_gen.services.supabase import get_supabase_client

router = APIRouter()


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(project: ProjectCreate) -> Project:
    """新規プロジェクト作成"""
    try:
        client = get_supabase_client()
        now = datetime.now(timezone.utc)

        data = {
            "id": str(uuid4()),
            "theme": project.theme,
            "state": ProjectState.INIT.value,
            "duration_target": project.duration_target,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        result = client.table("projects").insert(data).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="プロジェクト作成に失敗しました")

        return Project(**result.data[0], sections=[])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[Project])
async def list_projects() -> list[Project]:
    """プロジェクト一覧取得"""
    try:
        client = get_supabase_client()
        result = client.table("projects").select("*").order("created_at", desc=True).execute()

        projects = []
        for p in result.data:
            projects.append(Project(**p, sections=[]))

        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: UUID) -> Project:
    """プロジェクト詳細取得"""
    try:
        client = get_supabase_client()

        # プロジェクト取得
        result = client.table("projects").select("*").eq("id", str(project_id)).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")

        # セクション取得
        sections_result = (
            client.table("sections")
            .select("*")
            .eq("project_id", str(project_id))
            .order("section_index")
            .execute()
        )

        return Project(**result.data[0], sections=sections_result.data or [])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{project_id}", response_model=Project)
async def update_project(project_id: UUID, update: ProjectUpdate) -> Project:
    """プロジェクト更新"""
    try:
        client = get_supabase_client()

        # 更新データを構築
        data = update.model_dump(exclude_unset=True)
        if "state" in data and data["state"]:
            data["state"] = data["state"].value
        data["updated_at"] = datetime.now(timezone.utc).isoformat()

        result = (
            client.table("projects")
            .update(data)
            .eq("id", str(project_id))
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")

        return Project(**result.data[0], sections=[])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: UUID) -> None:
    """プロジェクト削除"""
    try:
        client = get_supabase_client()

        result = (
            client.table("projects")
            .delete()
            .eq("id", str(project_id))
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
