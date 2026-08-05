import json
from pathlib import Path

from collatz_research.certificates import DescentCertificate
from jsonschema import validate


def test_descent_certificate_matches_schema() -> None:
    schema_path = Path(__file__).parents[1] / "schemas" / "descent-certificate-v1.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validate(DescentCertificate("1.0", 3, 1, 5).as_dict(), schema)
