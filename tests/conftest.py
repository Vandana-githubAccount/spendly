import sys

import pytest

import database.db as db_module


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DATABASE", str(tmp_path / "test.db"))
    sys.modules.pop("app", None)
    import app as app_module

    app_module.app.config.update(TESTING=True)
    yield app_module.app
