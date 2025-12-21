import pytest


@pytest.fixture(autouse=True)
def no_user_site(monkeypatch):
    monkeypatch.delenv("PYTHONPATH", raising=False)
