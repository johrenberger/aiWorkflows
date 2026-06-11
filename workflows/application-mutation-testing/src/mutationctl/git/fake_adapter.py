from __future__ import annotations

import hashlib

from mutationctl.models import CommitExecutionResult, CommitPlan


class FakeGitAdapter:
    def execute_commit(self, plan: CommitPlan) -> CommitExecutionResult:
        identity = f"{plan.proposed_branch}|{plan.commit_message}|{'|'.join(plan.files_to_commit)}"
        sha = f"fake-{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:12]}"
        return CommitExecutionResult("PASS", True, sha, plan.proposed_branch, plan.commit_message, plan.evidence)
