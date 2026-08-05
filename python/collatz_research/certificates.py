"""Certificate data structures. Validation does not confer proof status."""
from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class DescentCertificate:
    schema_version: str
    start: int
    steps: int
    target: int

    def as_dict(self) -> dict[str, int | str]:
        return asdict(self)
