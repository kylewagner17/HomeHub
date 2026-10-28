import os

# Local dev: avoid requiring Postgres for pytest. GitHub Actions sets CI=true and DATABASE_URL.
if os.getenv("CI") != "true":
    os.environ["DATABASE_URL"] = "sqlite+pysqlite://"

import pytest
from fastapi.testclient import TestClient

from homehub.db.base import Base
from homehub.main import app, engine


@pytest.fixture(autouse=True)
def reset_database():
    from homehub.modules.auth import models as auth_models  # noqa: F401
    from homehub.modules.families import models as families_models  # noqa: F401
    from homehub.modules.groceries import models as groceries_models  # noqa: F401
    from homehub.modules.sync import models as sync_models  # noqa: F401

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
