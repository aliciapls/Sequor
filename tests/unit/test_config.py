"""Test configuration loading from .env."""

import os

from sequor.config import Settings


def test_settings_loads_defaults():
    s = Settings(_env_file=None, database_url="postgresql://localhost/test")
    assert s.app_env == "development"
    assert s.debug is True
    assert s.log_level == "INFO"
    assert s.default_escalation_sla_hours == 4
    assert s.default_confidence_threshold == 0.90


def test_ollama_defaults():
    s = Settings(_env_file=None, database_url="postgresql://localhost/test")
    assert s.ollama_base_url == "http://localhost:11434"
    assert s.llm_model == "llama3.1"
    assert s.embedding_model == "nomic-embed-text"


def test_settings_reads_env_vars():
    os.environ["APP_ENV"] = "production"
    os.environ["DEBUG"] = "false"
    os.environ["LLM_MODEL"] = "llama3.1:8b"
    try:
        s = Settings(_env_file=None, database_url="postgresql://localhost/test")
        assert s.app_env == "production"
        assert s.debug is False
        assert s.llm_model == "llama3.1:8b"
    finally:
        del os.environ["APP_ENV"]
        del os.environ["DEBUG"]
        del os.environ["LLM_MODEL"]


def test_package_version():
    from sequor import __version__

    assert __version__ == "0.1.0"
