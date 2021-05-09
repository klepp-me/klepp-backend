import os

import pytest
from fastapi.testclient import TestClient
from pydantic import Field

from app import main
from app.core.config import Settings, load_settings


def get_settings_override():
    test_db = Field(..., env='DATABASE_TEST_URL')
    print(test_db)
    return Settings(testing=1, database_url=test_db)


@pytest.fixture(scope='module')
def test_app():
    # set up
    main.app.dependency_overrides[load_settings] = get_settings_override
    with TestClient(main.app) as test_client:

        # testing
        yield test_client

    # tear down


def test_lol(test_app):
    print('hehe')
