from __future__ import annotations

from typing import Protocol

from mutationctl.models import MutationCommand, MutationTarget


class MutationAdapter(Protocol):
    tool_name: str

    def build_command(self, target: MutationTarget, working_directory) -> MutationCommand:
        ...
