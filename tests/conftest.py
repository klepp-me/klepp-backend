import pytest
from fastapi.testclient import TestClient
from tortoise.contrib.fastapi import register_tortoise

from app import main
from core.config import settings
from main import create_application


@pytest.fixture(scope='module')
def test_client():
    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture(scope='module')
def test_client_with_db():
    # set up
    app = create_application()
    register_tortoise(
        app,
        db_url=settings.DATABASE_URL,
        modules={'models': ['app.models.tortoise']},
        generate_schemas=True,
        add_exception_handlers=True,
    )
    with TestClient(app) as test_client:
        yield test_client
