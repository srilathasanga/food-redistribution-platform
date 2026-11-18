"""The tests must never touch the real database.

These need no database. They use a FAKE secrets.toml in a temporary
folder, never the real one.
"""

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from tests.db_safety import (
    problem_with_target,
    production_targets,
    target_from_dsn,
)

pytestmark = pytest.mark.no_database

PROJECT = Path(__file__).resolve().parents[1]
FAKE_REAL_DB = "postgresql://owner:secret@ep-real-1.example.neon.tech/ministry"
FAKE_TEST_DB = "postgresql://postgres:pw@localhost:5432/food_test"


def test_test_database_url_wins_over_secrets_toml(tmp_path):
    (tmp_path / ".streamlit").mkdir()
    (tmp_path / ".streamlit" / "secrets.toml").write_text(
        f'DATABASE_URL = "{FAKE_REAL_DB}"\n', encoding="utf-8"
    )
    script = textwrap.dedent(f"""
        import os
        import streamlit as st
        from app.config import get_setting
        from app.database import _connect_kwargs

        # Reading any secret makes Streamlit copy secrets.toml into the
        # environment. Prove the danger really happens here...
        get_setting("DB_POOL_SIZE", "10")
        "anything" in st.secrets
        assert os.environ["DATABASE_URL"] == {FAKE_REAL_DB!r}, "no overwrite"

        # ...and that the app still uses the test database.
        assert get_setting("DATABASE_URL") == {FAKE_TEST_DB!r}
        assert _connect_kwargs()["dsn"] == {FAKE_TEST_DB!r}
        print("TEST DATABASE WINS")
    """)
    env = {
        key: value for key, value in os.environ.items()
        if key not in ("DATABASE_URL", "TEST_DATABASE_URL")
    }
    env.update({
        # What conftest.py does when TEST_DATABASE_URL is set.
        "DATABASE_URL": FAKE_TEST_DB,
        "PYTHONPATH": str(PROJECT),
        # Keep Streamlit away from any real ~/.streamlit/secrets.toml.
        "HOME": str(tmp_path),
        "USERPROFILE": str(tmp_path),
    })
    result = subprocess.run(
        [sys.executable, "-c", script], cwd=tmp_path, env=env,
        capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    assert "TEST DATABASE WINS" in result.stdout


def test_runtime_setting_changes_still_work(monkeypatch):
    from app.config import get_setting

    import app.config

    # A setting that did not exist at start-up.
    monkeypatch.setenv("SAFETY_TEST_SETTING", "changed-by-test")
    assert get_setting("SAFETY_TEST_SETTING") == "changed-by-test"

    # A setting that existed at start-up (e.g. from .env) and a test
    # then changes on purpose, like test_ui.py does with ADMIN_EMAILS.
    monkeypatch.setitem(app.config._STARTUP_ENV, "SAFETY_TEST_2", "start")
    monkeypatch.setenv("SAFETY_TEST_2", "changed-by-test")
    assert get_setting("SAFETY_TEST_2") == "changed-by-test"

    # Unchanged since start-up: the start-up value.
    monkeypatch.setenv("SAFETY_TEST_2", "start")
    assert get_setting("SAFETY_TEST_2") == "start"


def test_guard_refuses_a_different_database():
    live = target_from_dsn("postgresql://u:p@other-host/other_db")
    assert problem_with_target(live, FAKE_TEST_DB, [])


def test_guard_refuses_the_real_database_even_via_neon_pooler():
    pooled = "postgresql://owner:x@ep-real-1-pooler.example.neon.tech/ministry"
    live = target_from_dsn(pooled)
    real = [target_from_dsn(FAKE_REAL_DB)]
    assert problem_with_target(live, pooled, real)


def test_guard_allows_the_test_database():
    live = target_from_dsn("host=127.0.0.1 dbname=food_test user=postgres")
    real = [target_from_dsn(FAKE_REAL_DB)]
    assert problem_with_target(live, FAKE_TEST_DB, real) is None


def test_guard_reads_real_database_from_secrets_file(tmp_path):
    secrets = tmp_path / "secrets.toml"
    secrets.write_text(f'DATABASE_URL = "{FAKE_REAL_DB}"\n', encoding="utf-8")
    assert production_targets([secrets, tmp_path / "missing.toml"]) == [
        ("ep-real-1.example.neon.tech", "ministry")
    ]
