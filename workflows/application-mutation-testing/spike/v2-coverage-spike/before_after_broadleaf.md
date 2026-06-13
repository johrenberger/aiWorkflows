# Open 4 (Broadleaf edition): Before/After Comparison on BroadleafCommerce

**Date:** 2026-06-13
**Target:** `johrenberger/BroadleafCommerce` @ `bb978302` (HEAD)
**Stack:** Java 17 (built with 21), Spring 6.2.18, Spring Boot 3.5.14, Hibernate 5.6.15, ~3790 inventory items, ~2801 v2-eligible source files
**Status:** integration works on Java; end-to-end smoke complete. Real mutation run (PIT) not attempted in this session.

## What was run

1. v2 against Broadleaf (no `--generate-coverage`):
   ```bash
   test-factory scan     --repo /tmp/BroadleafCommerce --out /tmp/v2-broadleaf-out
   test-factory coverage --repo /tmp/BroadleafCommerce --out /tmp/v2-broadleaf-out
   test-factory score    --repo /tmp/BroadleafCommerce --out /tmp/v2-broadleaf-out
   ```
   Result: `analysis-artifacts/risk_scores.json` with **2,801 records** (all source files; v2 still excludes `is_test=true` files from risk scoring).

2. mutation's `ingest_coverage()` against that artifact:
   ```
   evidence_path: /tmp/v2-broadleaf-out/risk_scores.json
   status: PASS
   file count: 2801
   v2-sourced: 2801
   files with real complexity: 2801
   ingest time: 0.02s
   ```

3. mutation's `select_targets()` with and without v2 input:

### Baseline (no v2 input — all fallback)

```
admin/broadleaf-open-admin-platform/.../FormBuilderServiceImpl.java                 score= 64.00  (fallback)
common/.../demo/CompositeAutoImportSampleDaoImpl.java                              score= 64.00  (fallback)
common/.../payment/CreditCardTypeChecksumUtility.java                              score= 64.00  (fallback)
common/.../util/dao/DynamicDaoHelperImpl.java                                      score= 64.00  (fallback)
core/.../search/service/SearchServiceImpl.java                                     score= 64.00  (fallback)
admin/.../FormBuilderServiceImpl.java (more)                                       score= 63.94  (fallback)
core/.../payment/service/PaymentInfoServiceImpl.java                               score= 63.50  (fallback)
core/.../profile/web/.../CustomerPhoneController.java                              score= 63.06  (fallback)
admin/.../request/SearchServiceImpl.java (admin)                                   score= 62.44  (fallback)
admin/.../service/...                                                             score= 61.30  (fallback)
```

10 targets. **6 distinct scores.** **Score ceiling at 64.00** (4 of 10 are at the cap — flat).

### With v2 input

```
admin/.../FormBuilderServiceImpl.java (high-cx, v2 risk=1601)                     score=106.50  [v2-cx]
admin/.../FormBuilderServiceImpl.java (high-cx, v2 risk=1421)                     score= 91.50  [v2-cx]
admin/.../FormBuilderServiceImpl.java                                              score= 80.50  [v2-cx]
admin/.../FormBuilderServiceImpl.java                                              score= 73.25  [v2-cx]
admin/.../FormBuilderServiceImpl.java                                              score= 70.75  [v2-cx]
admin/.../FormBuilderServiceImpl.java                                              score= 67.50  [v2-cx]
admin/.../FormBuilderServiceImpl.java                                              score= 67.25  [v2-cx]
common/.../extensibility/jpa/copy/DirectCopyTransformers.java                      score= 66.25  [v2-cx]
core/.../order/service/OrderServiceImpl.java                                       score= 66.25  [v2-cx]
admin/.../FormBuilderServiceImpl.java (more)                                       score= 63.50  [v2-cx]
```

10 targets. **9 distinct scores.** **Score range 63.50–106.50** (no flat cap).

## Comparison

| Metric                                | Baseline | With v2 | Δ |
|---------------------------------------|---------:|--------:|---|
| Distinct scores in top 10            |        6 |       9 | +50% |
| Score ceiling                         |    64.00 |  106.50 | +66% |
| Top score                             |    64.00 |  106.50 | +66% |
| Targets at score cap (flat)           |     4/10 |    0/10 | -100% |
| Overlap with baseline                 |        — |      1/10 |    — |
| Selection time                        |    0.86s |   0.29s | 3× faster |

## What this tells us

1. **v2's complexity lifts the score ceiling dramatically.** Without v2, the
   `complexity_score(source)` fallback is bounded (all four baseline #1s hit
   64.00). With v2, the top target (FormBuilderServiceImpl, complexity=298)
   scores 106.50 — the difference is purely from v2's per-file complexity
   value being plumbed into the model.

2. **The ranking reshuffles dramatically** — only 1 of 10 targets overlap.
   That's the expected shape when v2 has real per-file data: the
   `complexity` term dominates, so high-cx files jump up.

3. **7 of 10 v2-aware top targets are in `FormBuilderServiceImpl.java`**
   (and friends in `broadleaf-open-admin-platform/`). v2's top 5 by
   `risk_score` are all from this same file: 1601, 1421, 1175, 1052, 1028
   (complexity 298, 238, 194, 141, 155). The file is enormous (likely a
   central class with many inheritance hierarchies); mutation testing
   here would yield **a lot of work** — and v2 is correctly flagging it.

4. **v2-aware selection is 3× faster** (0.29s vs 0.86s) because the v2
   records carry the complexity directly and skip the file-system walks
   the fallback path does.

5. **Real line coverage is still missing.** v2 ran without
   `--generate-coverage`; we don't know which Broadleaf files are
   actually exercised by tests. With real line coverage, scores would
   shift again (low-coverage files would rank higher for mutation
   targeting). To get real coverage, we need to run `mvn test` on at
   least one module.

## Reproduction

```bash
# 1. v2 emits the artifact (no Java needed)
test-factory scan     --repo /tmp/BroadleafCommerce --out /tmp/v2-broadleaf-out
test-factory coverage --repo /tmp/BroadleafCommerce --out /tmp/v2-broadleaf-out
test-factory score    --repo /tmp/BroadleafCommerce --out /tmp/v2-broadleaf-out

# 2. mutation consumes it (one-liner)
PYTHONPATH=src python3 -c "
from mutationctl.coverage.ingest import ingest_coverage
from mutationctl.targeting.selector import select_targets

result = ingest_coverage(
    '/tmp/BroadleafCommerce',
    v2_artifact_path='/tmp/v2-broadleaf-out/risk_scores.json',
)
selection = select_targets(
    '/tmp/BroadleafCommerce', 'java', 'pitest',
    coverage_files=result.files, max_target_files=10,
)
for t in selection.selected:
    print(f'  {t.source_file}  score={t.score:.2f}  {t.rationale}')
"
```

## Sandbox limits hit

- No Java/Maven in PATH (found at `/data/jdk21/...` and `/data/maven/...`)
- No PIT configured (would need plugin + config + 1+ hours to run)
- 7.8 GiB RAM, 53 GiB disk — tight for a full Spring+Solr+Hibernate test run
- Prior session's `/tmp/broadleaf-ws/` had only repo-discovery (no test run)

**The integration is proven on a real Java codebase.** A real mutation
run (with PIT) is a follow-up; it requires significant setup time and
is best done in a CI environment with more resources.
