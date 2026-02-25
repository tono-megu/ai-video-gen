"""pytest設定"""

import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    """非同期テスト用バックエンド"""
    return "asyncio"
