from __future__ import annotations

SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS runs (
        run_id TEXT PRIMARY KEY,
        repo_url TEXT,
        repo_path TEXT,
        branch TEXT,
        mode TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        config_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS repo_metadata (
        run_id TEXT PRIMARY KEY,
        repo_url TEXT,
        repo_path TEXT NOT NULL,
        branch TEXT NOT NULL,
        commit_sha TEXT NOT NULL,
        is_dirty INTEGER NOT NULL,
        captured_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS commands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        command_json TEXT NOT NULL,
        exit_code INTEGER,
        duration_seconds REAL NOT NULL,
        status TEXT NOT NULL,
        stdout_path TEXT,
        stderr_path TEXT,
        timed_out INTEGER NOT NULL DEFAULT 0
    )
    """,
    "CREATE TABLE IF NOT EXISTS tool_detection (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS coverage_summaries (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS targets (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS mutation_results (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS surviving_mutants (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS survivor_packets (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS survivor_classifications (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS llm_requests (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS llm_responses (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS llm_validation_results (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS patch_proposals (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS patch_safety_results (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS patch_apply_results (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS patch_revert_results (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS weakening_findings (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS focused_test_results (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS validation_gate_results (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS validation_summaries (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS mutation_recheck_plans (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS mutation_recheck_results (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS remaining_survivors (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS git_status (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS branch_plans (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS commit_plans (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS commit_gate_results (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS commit_execution_results (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS workflow_run_results (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS final_summaries (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS real_tool_policies (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS real_tool_decisions (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS real_tool_results (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
    "CREATE TABLE IF NOT EXISTS validation_results (id INTEGER PRIMARY KEY AUTOINCREMENT, gate_name TEXT, status TEXT, details TEXT)",
    """
    CREATE TABLE IF NOT EXISTS ledger_tasks (
        task_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        status TEXT NOT NULL,
        details TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS blockers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL,
        status TEXT NOT NULL,
        reason TEXT NOT NULL,
        evidence TEXT NOT NULL
    )
    """,
    "CREATE TABLE IF NOT EXISTS commits (id INTEGER PRIMARY KEY AUTOINCREMENT, payload_json TEXT DEFAULT '{}')",
]
