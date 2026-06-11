from __future__ import annotations

from pathlib import Path

from mutationctl.models import MutationCommand, MutationTarget


class MutmutAdapter:
    tool_name = "mutmut"

    def build_command(self, target: MutationTarget, working_directory: str | Path) -> MutationCommand:
        return MutationCommand(
            "mutmut",
            "python",
            target.source_file,
            ["mutmut", "run", "--paths-to-mutate", target.source_file],
            1800,
            str(Path(working_directory)),
        )
