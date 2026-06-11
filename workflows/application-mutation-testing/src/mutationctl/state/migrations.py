from __future__ import annotations

import sqlite3

from mutationctl.state.schema import SCHEMA_STATEMENTS


def apply_migrations(connection: sqlite3.Connection) -> None:
    for statement in SCHEMA_STATEMENTS:
        connection.execute(statement)
    connection.commit()
