# Test Pattern: Wrapped-Commit for DB Exception Paths

**When to use:** Testing exception-handler code in endpoints that use a real database (SQLAlchemy, SQLModel, Django ORM) without faking the whole session stack.

**Source:** `pytest-fastapi-crud-example` PR #4 (2026-06-07) — `app/user.py` IntegrityError → 409 and OperationalError → 500 paths.

## The problem

You want to verify that an endpoint's `except IntegrityError: return 409` branch is hit. You have three choices:

1. **Mock the whole `db`** with `MagicMock()` — high-coupling, brittle, doesn't actually test the real code path.
2. **`mock.patch` the targeted method** (e.g. `Session.commit`) and `return None` — **breaks the test setup**, because setup operations (the `INSERT` to create the row) also need a working commit, and your mock swallows it.
3. **Wrap, don't replace.** Patch the method, but **delegate to the real method** for the calls you want to succeed. Only raise on the targeted call.

Option 3 is the wrapped-commit pattern.

## The pattern

```python
import sqlalchemy.orm.session as _sqla_session
from unittest.mock import patch
from sqlalchemy.exc import IntegrityError, OperationalError

# Save the real method before patching.
_real_commit = _sqla_session.Session.commit

def test_update_user_returns_409_on_duplicate_id(test_client, user_payload):
    counter = {"n": 0}

    def wrapped_commit(self, *args, **kwargs):
        counter["n"] += 1
        if counter["n"] == 2:  # the update's commit (the one we want to fail)
            raise IntegrityError("UPDATE", {}, Exception("duplicate key"))
        return _real_commit(self, *args, **kwargs)  # delegate to real commit

    with patch("sqlalchemy.orm.session.Session.commit", wrapped_commit):
        # Setup: real commit (1st call)
        r1 = test_client.post(f"/api/users/", json=user_payload)
        assert r1.status_code == 201

        # Targeted: wrapped commit raises IntegrityError (2nd call)
        r2 = test_client.patch(
            f"/api/users/{user_payload['id']}",
            json={"first_name": "NewName"},
        )
    assert r2.status_code == 409
```

## Why it works

- **External boundary, not internals.** The DB is an external dependency. Wrapping the commit treats it as a fault-injection point — the production code path is otherwise unchanged.
- **Minimal coupling.** No `MagicMock` of the whole session, no spec lists, no `autospec=True` chains. Just one method.
- **Deterministic counter.** A simple `counter` selects which call to fail. Reliable across test orderings.
- **Setup integrity preserved.** Setup operations (create the user) hit the real DB and actually persist. Without this, downstream operations that read the row (e.g. PATCH-then-GET) silently see stale state.

## The anti-pattern (what not to do)

```python
# ❌ This breaks: the create's commit returns None (no-op),
# data is never persisted, refresh fails, post returns 500 (not 201).
def bad_wrapped_commit(self, *args, **kwargs):
    if counter["n"] == 2:
        raise IntegrityError(...)
    return None  # ← no-op, breaks the real flow
```

Symptoms: 500 instead of 201 on setup, 202 instead of 409 on the targeted call, or `sqlalchemy.exc.InvalidRequestError: This Session's transaction has been rolled back`.

## Variations

- **OperationalError (500 path):** Same pattern, raise `OperationalError("COMMIT", {}, Exception("conn lost"))` on the targeted call.
- **Multiple endpoints, single test:** Use a different counter threshold per endpoint, or split into separate tests (preferred — keeps test isolation clear).
- **Mocking `db.add` or `db.query`** instead of commit: useful when the failure is mid-transaction (before commit), e.g. `IntegrityError` on flush. Same wrap-vs-replace principle applies.

## When NOT to use

- If the production code's exception handler is "trivial" (e.g. just re-raises), don't write the test. The test is for **observable behavior** (status code, body), not for "we have a try/except."
- If the failure is **in setup itself** (you can't set up the test scenario without the failure), use a different fixture strategy — e.g. a `pytest` parametrize with a fixture that returns a session in a known-bad state.
- If the spec rule "Avoid over-mocking internals" requires the failure to come from a real signal (e.g. actual SQL constraint violation), **prefer that**. The wrap-and-raise approach is for when no real signal can trigger the path.
