"""Mark tests/ inside fixtures/ as non-collectable. The fixtures are sample
repos for adapter detection tests; their `tests/` subdirs are NOT test
modules for the v2 suite itself. The hand-rolled pytest.py shim used to
skip them via a string check on path parts, but the real pytest needs
this hook (pytest's official `collect_ignore_glob` mechanism, supported
in conftest.py since pytest 6)."""
collect_ignore_glob = ["sample-repo/**/test_*.py", "sample-repo/**/*.py"]
