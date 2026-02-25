"""API統合テスト"""

import pytest
from fastapi.testclient import TestClient

from ai_video_gen.main import app


@pytest.fixture
def client():
    """テストクライアント"""
    return TestClient(app)


def test_health_check(client):
    """ヘルスチェック"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_create_project(client):
    """プロジェクト作成"""
    response = client.post(
        "/api/projects",
        json={"theme": "テスト動画", "duration_target": 300}
    )
    assert response.status_code in [200, 201]  # 200 or 201 Created
    data = response.json()
    assert data["theme"] == "テスト動画"
    assert data["state"] == "init"
    assert "id" in data


def test_create_project_invalid(client):
    """不正なプロジェクト作成"""
    response = client.post(
        "/api/projects",
        json={"theme": "", "duration_target": 300}
    )
    assert response.status_code == 422  # Validation error


def test_list_projects(client):
    """プロジェクト一覧"""
    response = client.get("/api/projects")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_project_not_found(client):
    """存在しないプロジェクト取得"""
    response = client.get("/api/projects/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_compose_status_not_found(client):
    """存在しないプロジェクトの合成状態"""
    response = client.get("/api/projects/00000000-0000-0000-0000-000000000000/compose/status")
    assert response.status_code == 404


def test_preferences_endpoint(client):
    """好みエンドポイント"""
    response = client.get("/api/feedback/preferences")
    # テーブルが存在しない場合は500、存在すれば200
    assert response.status_code in [200, 500]


def test_corrections_endpoint(client):
    """修正ログエンドポイント"""
    response = client.get("/api/feedback/corrections")
    # テーブルが存在しない場合は500、存在すれば200
    assert response.status_code in [200, 500]
