from __future__ import annotations

from typing import Protocol

from mutationctl.models import CommitExecutionResult, CommitPlan


class GitAdapter(Protocol):
    def execute_commit(self, plan: CommitPlan) -> CommitExecutionResult:
        ...
