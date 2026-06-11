from __future__ import annotations

from pathlib import Path

from mutationctl.models import MutationCommand, MutationTarget


class PitAdapter:
    tool_name = "pit"

    def build_command(self, target: MutationTarget, working_directory: str | Path) -> MutationCommand:
        return MutationCommand(
            "pit",
            "java",
            target.source_file,
            ["mvn", "org.pitest:pitest-maven:mutationCoverage"],
            1800,
            str(Path(working_directory)),
        )
