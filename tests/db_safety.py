"""Safety guard: the tests empty EVERY table, so before they do, make sure
they are connected to the throw-away test database and never to the real
one named in .streamlit/secrets.toml.

Host names and database names are compared; nothing secret is printed.
"""

import tomllib
from pathlib import Path

from psycopg2.extensions import parse_dsn

PROJECT_SECRETS = Path(__file__).resolve().parents[1] / ".streamlit" / "secrets.toml"
HOME_SECRETS = Path.home() / ".streamlit" / "secrets.toml"

_LOCAL_HOSTS = {"", "localhost", "127.0.0.1", "::1"}


def _normal_host(host):
    host = (host or "").lower().strip()
    if host in _LOCAL_HOSTS:
        return "localhost"
    # Neon: "ep-x-pooler.region..." and "ep-x.region..." are the SAME
    # database, reached through the pooler or directly.
    first, _, rest = host.partition(".")
    return first.removesuffix("-pooler") + ("." + rest if rest else "")


def target_from_dsn(dsn):
    """(host, database name) from a URL or 'host=... dbname=...' string."""
    params = parse_dsn(dsn)
    return _normal_host(params.get("host")), params.get("dbname", "")


def live_target(connection):
    """(host, database name) the open connection is really using."""
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT current_database();")
        dbname = cursor.fetchone()[0]
    finally:
        cursor.close()
    return _normal_host(connection.info.host), dbname


def production_targets(secrets_files=(PROJECT_SECRETS, HOME_SECRETS)):
    """(host, database name) of every real database named in secrets.toml."""
    targets = []
    for path in secrets_files:
        if not Path(path).is_file():
            continue
        with open(path, "rb") as handle:
            data = tomllib.load(handle)
        if data.get("DATABASE_URL"):
            targets.append(target_from_dsn(str(data["DATABASE_URL"])))
        elif data.get("DB_NAME"):
            targets.append((_normal_host(data.get("DB_HOST")),
                            str(data["DB_NAME"])))
    return targets


def problem_with_target(live, test_database_url, production):
    """None if it is safe to empty the tables, otherwise the reason."""
    if live != target_from_dsn(test_database_url):
        return ("The tests are connected to a different database than "
                "TEST_DATABASE_URL.")
    if live in production:
        return ("TEST_DATABASE_URL points at the real database named in "
                "secrets.toml.")
    return None
