# Architecture

Python may produce candidates; Lean independently checks formal statements. No Lean proof may depend on Python, solver output, or an experiment artifact.

| Layer | Responsibility | Trust level |
| --- | --- | --- |
| `python/` | Search and serialization | Untrusted |
| `schemas/` | Interchange contracts | Reviewed specification |
| `Lean/` | Definitions and theorems | Trusted after kernel checking |
| `experiments/` | Candidate generation | Untrusted evidence |

The initial certificate records one finite trajectory endpoint. A future importer must recompute semantics rather than trust a supplied target.
