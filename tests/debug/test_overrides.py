from unittest.mock import MagicMock

from app.api.v1.deps import get_current_user
from app.main import app


def override():
    return MagicMock()


app.dependency_overrides[get_current_user] = override
print(app.dependency_overrides)
