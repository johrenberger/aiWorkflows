from __future__ import annotations

from pathlib import Path

from mutationctl.models import MutationCommand, MutationTarget


class StrykerAdapter:
    tool_name = "stryker"

    def build_command(self, target: MutationTarget, working_directory: str | Path) -> MutationCommand:
        return MutationCommand(
            "stryker",
            "javascript",
            target.source_file,
            ["npx", "stryker", "run"],
            1800,
            str(Path(working_directory)),
        )
