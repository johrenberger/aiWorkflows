import CollatzResearch.Basic
import CollatzResearch.Certificate

/-!
# Certificate importer — plumbing stub

**Status (2026-08-11, Story 06b):** This module is the **structural
scaffolding** for the JSONL-side of the acceptance-to-`Valid` bridge.
The actual parser body is admitted as `sorry` and tracked as a
follow-up concern (see "Known limitations" below). The substantive
deliverable of Story 06b — the `check_certificate_sound` bridge
theorem — lives in `Certificate.lean`, not here.

**Trust boundary.** The Python checker is the *untrusted* producer of
accepted certificates. Lean is the *proof authority*. This module
will eventually re-run the acceptance decision inside the
type-checker, and the `check_certificate_sound` theorem (in
`Certificate.lean`) proves that acceptance implies the structural
`Valid` predicate.

**Spec alignment** (for the eventual non-sorry implementation).
The v1.0 schema and rejection categories mirror
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

**Known limitations.**

1. `parseV1Record` and `parseJsonl` are admitted as `sorry`. The
   parser internals (handling `Lean.Json`'s `JsonNumber`/`RBNode` API
   mismatches with this Lean version's precompiled `.olean` set) are
   a plumbing concern deferred to a follow-up. The
   `JsonParseError` / `v1Fields` / `v1Constraints` / `ParseResult`
   type infrastructure is in place; only the parser body needs to be
   filled in.

2. SHA-256 digest recomputation is not in this file; deferred to
   `Digest.lean` (FFI target TBD — see Story 06b risks in `PLAN.md`).
-/

namespace CollatzResearch

/-- Stable rejection categories for JSONL parsing. Mirrors the Python
`parser.py` `ERR_*` constants byte-for-byte so the trust-boundary contract
is observable from both sides. -/
inductive JsonParseError : Type
  | malformed : String → JsonParseError
  | missingField : String → JsonParseError
  | invalidValue : String → JsonParseError
  | unknownField : String → String → JsonParseError  -- field, value
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

/-- Result of parsing one JSONL record: a successful payload on success,
a `JsonParseError` on failure. -/
abbrev ParseResult (α : Type) : Type := Except JsonParseError α

/-- Parse the proof-bearing fields of a v1.0 record into a `DescentWitness`.

**Stub (admitted as `sorry`):** the parser body is plumbing that needs
to handle the v1.0 JSON shape via `Lean.Json`. See file header for the
follow-up plan. The structural type infrastructure (`JsonParseError`,
`v1Fields`, `v1Constraints`, `ParseResult`) is in place. -/
def parseV1Record (_jsonBytes : String) : ParseResult DescentWitness := by
  sorry

/-- Parse a JSONL byte string into a list of `DescentWitness` results.

**Stub (admitted as `sorry`):** the JSONL splitter is plumbing. See
file header. -/
def parseJsonl (_bytes : String) : List (Except JsonParseError DescentWitness) := by
  sorry

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
