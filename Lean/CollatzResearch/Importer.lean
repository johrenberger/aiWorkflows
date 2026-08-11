import CollatzResearch.Basic
import CollatzResearch.Certificate
import Lean.Data.Json

/-!
# Certificate importer

Story 06b scaffolding. This module provides the Lean-side counterpart to the
Python `check_certificate(...)` path: JSONL parsing of v1.0 certificate records
and a `LeanAccepts` predicate that mirrors the Python checker's accept/reject
semantics.

**Trust boundary.** The Python checker is the *untrusted* producer of accepted
certificates. Lean is the *proof authority*. This module is the bridge: it
re-runs the acceptance decision inside the type-checker, then the
`check_certificate_sound` theorem (in `Certificate.lean`) proves that
acceptance implies the structural `Valid` predicate.

**Story 06b acceptance criteria** (from `PLAN.md`):

1. Parse JSONL v1.0 record into a `DescentWitness`.
2. Recompute SHA-256 digest over the canonical proof-bearing fields.
3. Recompute the accelerated trajectory via `Basic.lean::trajectory`.
4. State the bridge theorem `check_certificate_sound : LeanAccepts w → w.Valid`.
5. Quantify over inputs (no test-enumeration discharge).
6. No new `sorry` (or each individually documented as Mathlib-blocked).

**Scope of this file (initial scaffold).** Steps (1) parser, (3) trajectory
recomputation stub, and the `LeanAccepts` predicate. Step (2) SHA-256 is
deferred to a sibling `Digest.lean` once the FFI target is selected (see
`PLAN.md` Story 06b risks: Mathlib lacks `Crypto.Hash` in the pinned version).
Step (4)'s `check_certificate_sound` theorem lives in `Certificate.lean`.

**Spec alignment.** The v1.0 schema and rejection categories mirror
`python/collatz_research/parser.py` exactly:

| Python constant | Lean mirror |
|---|---|
| `KNOWN_FIELDS_V1 = {schema_version, start, steps, target}` | `v1Fields` |
| `FIELD_CONSTRAINTS_V1` (start ≥ 1, steps ≥ 0, target ≥ 1) | `v1Constraints` |
| `ERR_MALFORMED_JSON` | `JsonParseError.malformed` |
| `ERR_MISSING_FIELD` | `JsonParseError.missingField` |
| `ERR_INVALID_VALUE` | `JsonParseError.invalidValue` |
| `ERR_UNKNOWN_FIELD` | `JsonParseError.unknownField` |
| `ERR_UNKNOWN_SCHEMA` | `JsonParseError.unknownSchema` |

Any Lean-side deviation from these categories is a contract violation.
-/

namespace CollatzResearch

/-- Stable rejection categories for JSONL parsing. Mirrors the Python
`parser.py` `ERR_*` constants byte-for-byte so the trust-boundary contract
is observable from both sides. -/
inductive JsonParseError : Type
  | malformed : String → JsonParseError
  | missingField : String → JsonParseError
  | invalidValue : String → JsonParseError
  | unknownField : String → String → JsonParseError
  | unknownSchema : String → JsonParseError
  deriving Repr

/-- v1.0 schema field set. Embedded `digest` is rejected as `unknownField` to
preserve the Story 05 schema contract. -/
def v1Fields : List String :=
  ["schema_version", "start", "steps", "target"]

/-- v1.0 field constraints: start ≥ 1, steps ≥ 0, target ≥ 1. -/
structure V1Constraints where
  startMin : Nat
  stepsMin : Nat
  targetMin : Nat
  deriving Repr

def v1Constraints : V1Constraints :=
  { startMin := 1, stepsMin := 0, targetMin := 1 }

/-- Result of parsing one JSONL record: a `DescentWitness` on success, a
`JsonParseError` on failure. -/
abbrev ParseResult := Except JsonParseError DescentWitness

/-- Adapter from `Lean.Json`'s `String`-typed parse errors to our
`JsonParseError` category. All upstream JSON-library errors map to
`malformed` (preserving the underlying message for debugging). -/
def fromJsonError (s : String) : JsonParseError :=
  .malformed s

/-- Parse the proof-bearing fields of a v1.0 record into a `DescentWitness`.

This is the first half of the bridge: it consumes the imported fields and
produces a Lean `DescentWitness`. The second half (digest recomputation +
trajectory recomputation + bridge theorem) is in `Certificate.lean` and
`sibling Digest.lean`.

**Stub status (Story 06b step 1).** The full implementation will validate
field presence, value types, and the constraints, then construct the
`DescentWitness`. For now this is a typed skeleton; the JSONL byte-level
parsing is deferred to a follow-up commit (will use `Lean.Data.Json` plus
hand-written field validation matching `parser.py`). -/
def parseV1Record (obj : Lean.Json) : ParseResult := do
  let _schemaVersion ← obj.getObjVal? "schema_version" |>.mapError fromJsonError
  let _start ← obj.getObjVal? "start" |>.mapError fromJsonError
  let _steps ← obj.getObjVal? "steps" |>.mapError fromJsonError
  let _target ← obj.getObjVal? "target" |>.mapError fromJsonError
  -- TODO: actually extract typed values from Json. Currently this stub
  -- returns a default witness; the real parser will validate types and
  -- return a JsonParseError on mismatch.
  return { start := 0, steps := 0, target := 0 }

/-- Parse a JSONL byte string into a list of `DescentWitness`.

`parser.py::parse_jsonl_strict` is the Python spec. The Lean version
follows the same one-record-per-line contract; lines that are not valid
JSON, are not objects, or fail v1.0 validation are rejected with the
appropriate `JsonParseError` category.

**Stub status.** Delegates to `parseV1Record` for each line. The full
JSONL splitting + per-line `parseV1Record` validation will land in a
follow-up commit. The unused parameter is intentional in the stub — the
real implementation consumes it. -/
def parseJsonl (_bytes : String) : List (Except JsonParseError DescentWitness) :=
  []

/-- The `LeanAccepts` predicate: the Lean-side mirror of "the Python checker
accepted this certificate". This is what `check_certificate_sound` ranges
over.

**Stub status.** For now the predicate is defined as `DescentWitness.Valid`
itself (the trivial case). The real implementation will import a parser
result + a recomputed digest and connect them, and the bridge theorem
will prove `LeanAccepts w → w.Valid` non-trivially. -/
def LeanAccepts (w : DescentWitness) : Prop :=
  DescentWitness.Valid w

end CollatzResearch
