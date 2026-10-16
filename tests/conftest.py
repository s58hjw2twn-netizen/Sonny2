"""Keep the automated suite free of model API charges, even in a keyed shell."""
import pytest


@pytest.fixture(autouse=True)
def no_paid_model_credentials(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
